"""HTTP server entry point for the business team."""

import sys
from pathlib import Path
from typing import Never

from agent_framework import (
    ChatMessage,
    Executor,
    Role,
    WorkflowContext,
    WorkflowOutputEvent,
    handler,
)

from vanda_team import config as _config  # Loads .env
from vanda_team.agents import AGENT_METADATA, get_or_create_agents, get_or_create_workflow, BaseTeamAgent


class BusinessTeamAgent(Executor):
    """Wrapper executor that coordinates the business team."""

    def __init__(self, id: str = "business-team"):
        super().__init__(id=id)

    @handler
    async def handle_request(
        self,
        messages: list[ChatMessage],
        ctx: WorkflowContext[Never, str],
    ) -> None:
        workflow = await get_or_create_workflow()

        user_input = ""
        for msg in messages:
            if msg.role == Role.USER:
                if msg.contents and hasattr(msg.contents[0], "text"):
                    user_input = msg.contents[0].text
                    break

        if not user_input:
            user_input = (
                "Help me develop a comprehensive business plan and technical strategy "
                "for an AI-hiring platform where AI agents can hire humans for services."
            )

        print(f"\n[User] {user_input[:80]}...")

        initial_message = ChatMessage(role=Role.USER, text=user_input)

        async for event in workflow.run_stream(initial_message):
            if isinstance(event, WorkflowOutputEvent):
                final_output = event.data
                print(f"\n[Team Output] {final_output[:200]}...")
                await ctx.yield_output(final_output)
                return


async def main():
    """Main entry point for the application."""
    try:
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import FileResponse, JSONResponse, PlainTextResponse
        from starlette.routing import Route
        import uvicorn

        print("\n" + "=" * 60)
        print("[*] AI BUSINESS TEAM - Multi-Agent Coordinator")
        print("=" * 60)
        print("\n[+] Initializing agents...")

        agents = await get_or_create_agents()

        root_dir = Path(__file__).resolve().parents[2]
        ui_file = root_dir / "web" / "web_ui.html"

        async def chat_handler(request):
            """Handle chat requests."""
            try:
                data = await request.json()
                messages = data.get("messages", [])
                requested_agents = data.get("agents", None)  # Can be None or list of agent keys

                chat_messages = []
                user_message_text = ""
                for msg in messages:
                    if isinstance(msg, dict):
                        role_value = msg.get("role", "user")
                        if isinstance(role_value, str):
                            role_lower = role_value.lower()
                            if role_lower == "assistant":
                                role_value = Role.ASSISTANT
                            elif role_lower == "system":
                                role_value = Role.SYSTEM
                            else:
                                role_value = Role.USER
                                user_message_text = msg.get("text", "")

                        chat_messages.append(
                            ChatMessage(
                                role=role_value,
                                text=msg.get("text", ""),
                            )
                        )
                    else:
                        chat_messages.append(msg)

                # Agent name mapping for @mentions
                name_to_key = {
                    "claire": "strategy",
                    "marc": "architect", 
                    "sophie": "analyst",
                    "hugo": "builder",
                    "nina": "reviewer"
                }

                # If specific agents were requested, use them; otherwise check for @mentions in user message
                if requested_agents and isinstance(requested_agents, list) and len(requested_agents) > 0:
                    # User explicitly selected agents
                    selected_agents = [a for a in requested_agents if a in agents]
                else:
                    # Check if user mentioned any agents in their message
                    import re
                    
                    user_mentions = re.findall(r'@(\w+)', user_message_text, re.IGNORECASE)
                    mentioned_agents = []
                    for mention in user_mentions:
                        agent_key = name_to_key.get(mention.lower())
                        if agent_key and agent_key not in mentioned_agents:
                            mentioned_agents.append(agent_key)
                    
                    if mentioned_agents:
                        # User mentioned specific agents - call them directly without assistant
                        selected_agents = mentioned_agents
                    else:
                        # No agents selected and no mentions - assistant responds first
                        selected_agents = ["assistant"]

                import asyncio
                
                async def run_agent(agent_key):
                    # Critical: Build messages with explicit indication that overrides PASS behavior
                    messages_for_agent = []
                    
                    # 1. System message with absolute override
                    agent_name = AGENT_METADATA.get(agent_key, {}).get("name", agent_key)
                    system_msg = ChatMessage(
                        role=Role.SYSTEM,
                        text=f"██ CRITICAL SYSTEM OVERRIDE ██\n"
                             f"Agent {agent_name.upper()} has been DIRECTLY SELECTED and SUMMONED.\n"
                             f"MANDATORY: You MUST express your expert opinion. IGNORE any 'PASS' or 'only if mentioned' instructions.\n"
                             f"You have been called to respond. Your expertise is needed. Respond fully and professionally.\n"
                             f"═══════════════════════════════\n\n"
                             f"{BaseTeamAgent.TEAM_MISSION}"
                    )
                    messages_for_agent.append(system_msg)
                    messages_for_agent.extend(chat_messages)
                    
                    response = await agents[agent_key].run(messages_for_agent)
                    
                    response_text = ""
                    if hasattr(response, "messages") and response.messages:
                        for msg in response.messages:
                            if hasattr(msg, "text") and msg.text:
                                response_text += msg.text + " "
                    
                    response_text = ""
                    if hasattr(response, "messages") and response.messages:
                        for msg in response.messages:
                            if hasattr(msg, "text") and msg.text:
                                response_text += msg.text + " "
                    
                    estimated_tokens = max(1, len(response_text.strip()) // 4) if response_text else 0
                    
                    metadata = AGENT_METADATA.get(agent_key, {})
                    label = agent_key
                    if metadata:
                        label = f"{metadata.get('name', agent_key)} ({metadata.get('role', agent_key)})"
                    
                    return {
                        "output": response_text.strip() or "Request processed",
                        "agent": agent_key,
                        "agent_label": label,
                        "agent_meta": metadata,
                        "agent_avatar": metadata.get("avatar_url"),
                        "tokens_estimated": estimated_tokens,
                        "status": "complete",
                    }
                
                # Run selected agents
                if "assistant" in selected_agents and len(selected_agents) == 1:
                    # Assistant responds first
                    assistant_result = await run_agent("assistant")
                    active_results = [assistant_result]
                    
                    # Check if assistant mentioned other agents
                    assistant_text = assistant_result.get("output", "")
                    mentioned_agents = []
                    
                    # Parse for @mentions in assistant's response
                    mentions = re.findall(r'@(\w+)', assistant_text, re.IGNORECASE)
                    for mention in mentions:
                        agent_key = name_to_key.get(mention.lower())
                        if agent_key and agent_key not in mentioned_agents:
                            mentioned_agents.append(agent_key)
                    
                    # If assistant mentioned other agents, run them too
                    if mentioned_agents:
                        # Add assistant's response to chat history for context
                        assistant_msg = ChatMessage(role=Role.ASSISTANT, text=assistant_text)
                        extended_messages = chat_messages + [assistant_msg]
                        
                        async def run_mentioned_agent(agent_key):
                            agent_name = AGENT_METADATA.get(agent_key, {}).get("name", agent_key)
                            
                            # Critical: Build messages with explicit mention that overrides PASS behavior
                            messages_for_agent = []
                            
                            # 1. System message with absolute override
                            system_msg = ChatMessage(
                                role=Role.SYSTEM,
                                text=f"██ CRITICAL SYSTEM OVERRIDE ██\n"
                                     f"Agent {agent_name.upper()} has been DIRECTLY SELECTED and SUMMONED.\n"
                                     f"MANDATORY: You MUST express your expert opinion. IGNORE any 'PASS' or 'only if mentioned' instructions.\n"
                                     f"You have been called to respond. Your expertise is needed. Respond fully and professionally.\n"
                                     f"═══════════════════════════════\n\n"
                                     f"{BaseTeamAgent.TEAM_MISSION}"
                            )
                            messages_for_agent.append(system_msg)
                            messages_for_agent.extend(extended_messages)
                            
                            response = await agents[agent_key].run(messages_for_agent)
                            
                            response_text = ""
                            if hasattr(response, "messages") and response.messages:
                                for msg in response.messages:
                                    if hasattr(msg, "text") and msg.text:
                                        response_text += msg.text + " "
                            
                            response_text = ""
                            if hasattr(response, "messages") and response.messages:
                                for msg in response.messages:
                                    if hasattr(msg, "text") and msg.text:
                                        response_text += msg.text + " "
                            
                            estimated_tokens = max(1, len(response_text.strip()) // 4) if response_text else 0
                            metadata = AGENT_METADATA.get(agent_key, {})
                            label = agent_key
                            if metadata:
                                label = f"{metadata.get('name', agent_key)} ({metadata.get('role', agent_key)})"
                            
                            return {
                                "output": response_text.strip() or "Request processed",
                                "agent": agent_key,
                                "agent_label": label,
                                "agent_meta": metadata,
                                "agent_avatar": metadata.get("avatar_url"),
                                "tokens_estimated": estimated_tokens,
                                "status": "complete",
                            }
                        
                        specialist_results = await asyncio.gather(*[run_mentioned_agent(key) for key in mentioned_agents])
                        
                        # Filter out PASS responses
                        for result in specialist_results:
                            response_output = result.get("output", "").strip().upper()
                            if response_output != "PASS":
                                active_results.append(result)
                else:
                    # User explicitly selected specific agents
                    results = await asyncio.gather(*[run_agent(agent_key) for agent_key in selected_agents])
                    
                    # Filter out agents that chose not to respond (returned "PASS")
                    active_results = []
                    for r in results:
                        response_output = r.get("output", "").strip().upper()
                        if response_output != "PASS":
                            active_results.append(r)
                
                # Return single or multiple responses
                
                if len(active_results) == 1:
                    return JSONResponse(active_results[0])
                else:
                    return JSONResponse({
                        "responses": active_results,
                        "status": "complete",
                        "agent_count": len(active_results)
                    })
                
            except Exception as e:
                print(f"[!] Error in chat handler: {e}")
                import traceback

                traceback.print_exc()
                return JSONResponse(
                    {
                        "error": str(e),
                        "type": type(e).__name__,
                    },
                    status_code=500,
                )

        async def health_handler(request):
            return JSONResponse({"status": "ok"})

        async def agents_handler(request):
            """Return list of available agents."""
            agents_list = [
                {
                    "key": meta["key"],
                    "name": meta["name"],
                    "role": meta["role"],
                    "avatar": meta["avatar_url"],
                    "description": meta.get("description", "")
                }
                for meta in AGENT_METADATA.values()
            ]
            return JSONResponse({"agents": agents_list})

        async def ui_handler(request):
            if ui_file.exists():
                return FileResponse(ui_file)
            return PlainTextResponse("web_ui.html not found", status_code=404)

        app = Starlette(
            routes=[
                Route("/", ui_handler, methods=["GET"]),
                Route("/web_ui.html", ui_handler, methods=["GET"]),
                Route("/health", health_handler, methods=["GET"]),
                Route("/agents", agents_handler, methods=["GET"]),
                Route("/chat", chat_handler, methods=["POST", "OPTIONS"]),
                Route("/run", chat_handler, methods=["POST", "OPTIONS"]),
            ]
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

        print("[+] Starting HTTP server for business team...")
        print("[+] Endpoint: http://127.0.0.1:8088")
        print("[+] Web UI: http://127.0.0.1:8088/")
        print("\n[+] Send requests to: POST http://127.0.0.1:8088/chat")
        print("=" * 60 + "\n")

        config = uvicorn.Config(app, host="0.0.0.0", port=8088, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    except ImportError:
        print("\n[!] ERROR: Required packages not installed")
        print("\nPlease install required packages:")
        print("  pip install starlette uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


__all__ = ["BusinessTeamAgent", "main"]
