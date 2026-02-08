# Architecture (Short)

## Flow

User -> Strategy -> Architect -> Analyst -> Builder -> Reviewer -> Response

## Core Modules

- src/agents.py: agent roles + workflow
- src/model_client.py: model client
- src/tools_strategy.py: research tools
- src/tools_github.py: GitHub tools
- src/server.py: HTTP server

## Endpoints

- POST /chat: main request
- GET /health: health check

## Entry Points

- scripts/run.py: web UI + API
- scripts/business_team.py: API only
