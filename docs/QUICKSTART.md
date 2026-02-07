# Quick Start

## 1) Install

```bash
cd c:\Users\jkang\repos\vanda
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## 2) Configure

Edit .env:
```env
MODEL_ENDPOINT=https://models.github.ai/inference/
MODEL_NAME=openai/gpt-4o-mini
GITHUB_TOKEN=your_token_here
```

## 3) Run

```bash
python scripts/run.py
```

Web UI: http://127.0.0.1:8088/
API: http://127.0.0.1:8088/chat

## 4) Ask a question

```bash
curl -X POST http://127.0.0.1:8088/chat \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "text": "What is our MVP?"}]}'
```
