"""HTTP server entry point for the business team."""

import re
import sys
from pathlib import Path

from agent_framework import Role, ChatMessage

from vanda_team import config as _config  # Loads .env
from vanda_team.agents import AGENT_METADATA, get_or_create_agents, get_or_create_workflow, BaseTeamAgent

# Constants
NAME_TO_KEY = {
    "claire": "strategy",
    "marc": "architect", 
    "sophie": "analyst",
    "hugo": "builder",
    "nina": "reviewer"
}

def extract_response_text(response):
    """Extract text from agent response."""
    response_text = ""
    if hasattr(response, "messages") and response.messages:
        for msg in response.messages:
            if hasattr(msg, "text") and msg.text:
                response_text += msg.text + " "
    return response_text.strip()

def create_agent_result(agent_key, response_text):
    """Create result dict for agent response."""
    estimated_tokens = max(1, len(response_text) // 4) if response_text else 0
    metadata = AGENT_METADATA.get(agent_key, {})
    label = agent_key
    if metadata:
        label = f"{metadata.get('name', agent_key)} ({metadata.get('role', agent_key)})"
    
    return {
        "output": response_text or "Request processed",
        "agent": agent_key,
        "agent_label": label,
        "agent_meta": metadata,
        "agent_avatar": metadata.get("avatar_url"),
        "tokens_estimated": estimated_tokens,
        "status": "complete",
    }

async def run_agent_with_messages(agent_key, messages_for_agent, agents):
    """Run an agent with given messages."""
    response = await agents[agent_key].run(messages_for_agent)
    response_text = extract_response_text(response)
    
    return create_agent_result(agent_key, response_text)


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

                # Determine which agents should respond initially
                initial_responders = [key for key, agent in agents.items() if agent.should_respond(chat_messages)]
                if not initial_responders:
                    initial_responders = ["assistant"]

                import asyncio
                
                async def run_agent(agent_key):
                    return await run_agent_with_messages(agent_key, chat_messages, agents)
                
                # Run initial responders
                results = await asyncio.gather(*[run_agent(key) for key in initial_responders])
                active_results = [r for r in results if r.get("output", "").strip().upper() != "PASS"]
                
                # Check if assistant responded and mentioned other agents
                assistant_result = next((r for r in active_results if r["agent"] == "assistant"), None)
                if assistant_result:
                    assistant_text = assistant_result.get("output", "")
                    # Add assistant response to messages for potential additional responders
                    extended_messages = chat_messages + [ChatMessage(role=Role.ASSISTANT, text=assistant_text)]
                    
                    # Find additional agents that should respond now
                    additional_responders = [key for key, agent in agents.items() 
                                           if agent.should_respond(extended_messages) and key not in initial_responders]
                    
                    if additional_responders:
                        additional_results = await asyncio.gather(*[run_agent_with_messages(key, extended_messages, agents) 
                                                                   for key in additional_responders])
                        for r in additional_results:
                            if r.get("output", "").strip().upper() != "PASS":
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


__all__ = ["main"]
