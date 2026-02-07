# Architecture (Short)

## Flow

User -> Strategy -> Architect -> Analyst -> Builder -> Reviewer -> Response

## Core Modules

- src/vanda_team/agents.py: agent roles + workflow
- src/vanda_team/model_client.py: model client
- src/vanda_team/tools_strategy.py: research tools
- src/vanda_team/tools_github.py: GitHub tools
- src/vanda_team/server.py: HTTP server

## Endpoints

- POST /chat: main request
- GET /health: health check

## Entry Points

- scripts/run.py: web UI + API
- scripts/business_team.py: API only
