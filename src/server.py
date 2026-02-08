"""HTTP server entry point for the business team."""

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Dict, List, Any, Optional

from agent_framework import Role, ChatMessage

from agents import (
    AGENT_METADATA,
    AgentMetadata,
    create_all_team_agents,
)

# Constants
NAME_TO_KEY = {
    "claire": "strategy",
    "marc": "architect",
    "sophie": "analyst",
    "hugo": "builder",
    "nina": "reviewer",
}


def extract_response_text(response: Any) -> str:
    """Extract text from agent response."""
    response_text = ""
    if hasattr(response, "messages") and response.messages:
        for msg in response.messages:
            if hasattr(msg, "text") and msg.text:
                response_text += msg.text + " "
    return response_text.strip()


def create_agent_result(agent_key: str, response_text: str) -> Dict[str, Any]:
    """Create result dict for agent response."""
    estimated_tokens = max(1, len(response_text) // 4) if response_text else 0
    metadata: Optional[AgentMetadata] = AGENT_METADATA.get(agent_key, None)
    label = agent_key
    if metadata:
        label = f"{metadata.name} ({metadata.role})"

    return {
        "output": response_text or "Request processed",
        "agent": agent_key,
        "agent_label": label,
        "agent_meta": asdict(metadata) if metadata else None,
        "agent_avatar": metadata.avatar_url if metadata else None,
        "tokens_estimated": estimated_tokens,
        "status": "complete",
    }


async def run_agent_with_messages(
    agent_key: str, messages_for_agent: List[ChatMessage], agents: Dict[str, Any]
) -> Dict[str, Any]:
    """Run an agent with given messages."""
    response = await agents[agent_key].agent.run(messages_for_agent)
    response_text = extract_response_text(response)

    return create_agent_result(agent_key, response_text)


async def determine_responders(
    messages: List[ChatMessage], agents: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Determine which agents should respond to the given messages in a chain."""
    active_results = []
    current_messages = messages
    responded_agents = set()

    while True:
        # Find agents that should respond but haven't yet
        potential_responders = [
            key
            for key, agent in agents.items()
            if agent.should_respond(current_messages) and key not in responded_agents
        ]

        if not potential_responders:
            break

        # Run the first potential responder (to avoid conflicts, run one at a time)
        responder_key = potential_responders[0]

        result = await run_agent_with_messages(responder_key, current_messages, agents)

        if result.get("output", "").strip().upper() != "PASS":
            active_results.append(result)
            responded_agents.add(responder_key)

            # Add this response to the conversation for potential further responses
            current_messages = current_messages + [
                ChatMessage(role=Role.ASSISTANT, text=result["output"])
            ]

    return active_results


async def main() -> None:
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

        agents = await create_all_team_agents()

        root_dir = Path(__file__).resolve().parents[1]
        ui_file = root_dir / "web" / "web_ui.html"

        async def chat_handler(request: Any) -> Any:
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

                # Determine and run responders
                active_results = await determine_responders(chat_messages, agents)

                # Return single or multiple responses

                if len(active_results) == 1:
                    return JSONResponse(active_results[0])
                else:
                    return JSONResponse(
                        {
                            "responses": active_results,
                            "status": "complete",
                            "agent_count": len(active_results),
                        }
                    )

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

        async def health_handler(request: Any) -> Any:
            return JSONResponse({"status": "ok"})

        async def agents_handler(request: Any) -> Any:
            """Return list of available agents."""
            agents_list = [
                {
                    "key": meta.key,
                    "name": meta.name,
                    "role": meta.role,
                    "avatar": meta.avatar_url,
                    "description": "",
                }
                for meta in AGENT_METADATA.values()
            ]
            return JSONResponse({"agents": agents_list})

        async def ui_handler(request: Any) -> Any:
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
