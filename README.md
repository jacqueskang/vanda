# Vanda AI Business Team

A multi-agent system that helps you plan and build an AI-hiring platform. Five agents collaborate in sequence: Strategy, Architect, Analyst, Builder, Reviewer.

## Quick Start

```bash
cd c:\Users\jkang\repos\vanda
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

Set your model in .env:
```env
MODEL_ENDPOINT=https://models.github.ai/inference/
MODEL_NAME=openai/gpt-4o-mini
GITHUB_TOKEN=your_token_here
```

Run the stack:
```bash
python scripts/run.py
```

Web UI: http://127.0.0.1:8088/
API: http://127.0.0.1:8088/chat

## Project Layout

```
vanda/
├── src/     # Core package
├── scripts/            # Entry points
├── web/                # Web UI assets
├── docs/               # Short docs
├── logs/               # Runtime logs
├── requirements.txt
└── .env
```

## Docs

- Quick start: docs/QUICKSTART.md
- Architecture: docs/ARCHITECTURE.md
- Setup checklist: docs/SETUP_CHECKLIST.md

## API Example

```bash
curl -X POST http://127.0.0.1:8088/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "text": "Design the MVP."}]}'
```
