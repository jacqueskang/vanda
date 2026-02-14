"""HTTP server entry point for the business team."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any

import json
from agent_framework import Role, ChatMessage

from vanda_team import VandaTeam
from agents.tools.approval import register_tool_approval

# Constants
NAME_TO_KEY = {
    "claire": "strategy",
    "marc": "architect",
    "sophie": "analyst",
    "hugo": "builder",
    "nina": "reviewer",
}


async def main() -> None:
    """Main entry point for the application."""
    try:
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
        from starlette.routing import Mount, Route
        from starlette.staticfiles import StaticFiles
        import uvicorn

        logging_config = uvicorn.config.LOGGING_CONFIG.copy()
        logging_config["loggers"] = logging_config.get("loggers", {}).copy()
        logging_config["loggers"]["uvicorn.access"] = {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False,
        }
        for logger_name in ("agents", "vanda_team", "server"):
            logging_config["loggers"][logger_name] = {
                "handlers": ["default"],
                "level": "DEBUG",
                "propagate": False,
            }
        logging.config.dictConfig(logging_config)

        print("\n" + "=" * 60)
        print("[*] AI BUSINESS TEAM - Multi-Agent Coordinator")
        print("=" * 60)
        print("\n[+] Initializing agents...")

        team = await VandaTeam.create()

        root_dir = Path(__file__).resolve().parents[1]
        ui_file = root_dir / "web" / "index.html"

        async def chat_handler(request: Any) -> Any:
            """Handle chat requests."""
            try:
                data = await request.json()
                messages = data.get("messages", [])

                chat_messages = []
                last_user_text = ""
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

                        if role_value == Role.USER:
                            last_user_text = msg.get("text", "") or ""

                        chat_messages.append(
                            ChatMessage(
                                role=role_value,
                                text=msg.get("text", ""),
                            )
                        )
                    else:
                        chat_messages.append(msg)

                decision = register_tool_approval(last_user_text)
                if decision:
                    if decision.action == "approve":
                        chat_messages.append(
                            ChatMessage(
                                role=Role.SYSTEM,
                                text=(
                                    "User approved tool request "
                                    f"{decision.request_id}. Proceed with the tool call."
                                ),
                            )
                        )
                    else:
                        chat_messages.append(
                            ChatMessage(
                                role=Role.SYSTEM,
                                text=(
                                    "User denied tool request "
                                    f"{decision.request_id}. Do not call that tool unless a new approval is requested."
                                ),
                            )
                        )

                # Determine and run responders
                active_results = await team.determine_responders(chat_messages)

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

        async def chat_stream_handler(request: Any) -> Any:
            """Handle streaming chat requests - placeholder."""
            return JSONResponse({"error": "Stream endpoint disabled"})

        async def health_handler(request: Any) -> Any:
            return JSONResponse({"status": "ok"})

        async def agents_handler(request: Any) -> Any:
            """Return list of available agents."""
            agents_list = team.get_agents_list()
            return JSONResponse({"agents": agents_list})

        async def ui_handler(request: Any) -> Any:
            if ui_file.exists():
                return FileResponse(ui_file)
            return PlainTextResponse("index.html not found", status_code=404)

        # Get the web directory path
        web_dir = root_dir / "web"

        app = Starlette(
            routes=[
                Route("/", ui_handler, methods=["GET"]),
                Route("/index.html", ui_handler, methods=["GET"]),
                Route("/health", health_handler, methods=["GET"]),
                Route("/agents", agents_handler, methods=["GET"]),
                Route("/chat", chat_handler, methods=["POST", "OPTIONS"]),
                Route("/chat/stream", chat_stream_handler, methods=["POST", "OPTIONS"]),
                Route("/run", chat_handler, methods=["POST", "OPTIONS"]),
                Mount("/", StaticFiles(directory=str(web_dir)), name="static"),
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

        config = uvicorn.Config(
            app,
            host="0.0.0.0",
            port=8088,
            log_level="info",
            access_log=False,
        )
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
