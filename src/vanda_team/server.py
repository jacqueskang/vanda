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
from vanda_team.agents import AGENT_METADATA, TEAM_MISSION, get_or_create_agents


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
        workflow, _client = await get_or_create_workflow()

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

        agents, router = await get_or_create_agents()

        root_dir = Path(__file__).resolve().parents[2]
        ui_file = root_dir / "web" / "web_ui.html"

        async def chat_handler(request):
            """Handle chat requests."""
            try:
                data = await request.json()
                messages = data.get("messages", [])
                requested_agents = data.get("agents", None)  # Can be None or list of agent keys

                chat_messages = []
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

                        chat_messages.append(
                            ChatMessage(
                                role=role_value,
                                text=msg.get("text", ""),
                            )
                        )
                    else:
                        chat_messages.append(msg)

                # If specific agents were requested, use them; otherwise, use router
                if requested_agents and isinstance(requested_agents, list) and len(requested_agents) > 0:
                    # Use requested agents
                    selected_agents = [a for a in requested_agents if a in agents]
                    print(f"[DEBUG] Requested agents: {requested_agents}")
                    print(f"[DEBUG] Available agents: {list(agents.keys())}")
                    print(f"[DEBUG] Selected agents: {selected_agents}")
                    if not selected_agents:
                        selected_agents = ["strategy"]
                        print(f"[DEBUG] No valid agents found, defaulting to strategy")
                else:
                    # Route to best agent
                    router_prompt = (
                        f"{TEAM_MISSION} "
                        "Pick the best agent for this request. "
                        "Respond with one word: strategy, architect, analyst, builder, reviewer."
                    )
                    router_messages = [
                        ChatMessage(role=Role.SYSTEM, text=router_prompt),
                    ] + chat_messages

                    route_response = await router.run(router_messages)
                    choice = "strategy"
                    if hasattr(route_response, "messages") and route_response.messages:
                        last = route_response.messages[-1]
                        if hasattr(last, "text") and last.text:
                            choice = last.text.strip().lower()

                    if choice not in agents:
                        choice = "strategy"
                    
                    selected_agents = [choice]

                # Run all selected agents in parallel
                import asyncio
                
                async def run_agent(agent_key):
                    mission_message = ChatMessage(role=Role.SYSTEM, text=TEAM_MISSION)
                    response = await agents[agent_key].run([mission_message] + chat_messages)
                    
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
                
                # Run all agents in parallel
                results = await asyncio.gather(*[run_agent(agent_key) for agent_key in selected_agents])
                
                # Return single or multiple responses
                if len(results) == 1:
                    return JSONResponse(results[0])
                else:
                    return JSONResponse({
                        "responses": results,
                        "status": "complete",
                        "agent_count": len(results)
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

        async def ui_handler(request):
            if ui_file.exists():
                return FileResponse(ui_file)
            return PlainTextResponse("web_ui.html not found", status_code=404)

        app = Starlette(
            routes=[
                Route("/", ui_handler, methods=["GET"]),
                Route("/web_ui.html", ui_handler, methods=["GET"]),
                Route("/health", health_handler, methods=["GET"]),
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
