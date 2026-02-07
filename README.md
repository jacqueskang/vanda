# AI-Powered Business Team

A multi-agent AI system that helps you develop a business platform where AI agents can hire humans for services.

## Overview

This project creates a team of specialized AI agents that work together to:

1. **Strategy Agent** - Analyzes market opportunities and business strategy
2. **Technical Architect Agent** - Designs the system architecture and technology stack
3. **Business Analyst Agent** - Creates product roadmaps and requirements
4. **Builder Agent** - Generates code and implementation guidance
5. **Reviewer Agent** - Reviews and refines all output

Each agent has expertise in their domain and they collaborate through a workflow to produce comprehensive analysis and recommendations.

## Quick Start

### Prerequisites

- Python 3.10+
- GitHub account with a Personal Access Token (for free model access) OR Microsoft Foundry project

### Setup

1. **Clone and navigate to the repository:**
   ```bash
   cd c:\Users\jkang\repos\vanda
   ```

2. **Create a Python virtual environment:**
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your model:**

   **Option A: Using GitHub Models (Free, Recommended for Start)**
   - Get a GitHub Personal Access Token: https://github.com/settings/tokens
   - Update `.env` file:
     ```env
     MODEL_ENDPOINT=https://models.github.ai/inference/
     MODEL_NAME=openai/gpt-4o-mini
     GITHUB_TOKEN=your_token_here
     ```

   **Option B: Using Microsoft Foundry Models**
   - Set up a Microsoft Foundry project in Azure AI Studio
   - Update `.env` file with your Foundry endpoint and deployment name
   - Use Azure CLI to authenticate: `az login`

5. **Run the agent server:**
   ```bash
   python business_team.py
   ```

   You should see output like:
   ```
   Application startup complete
   Uvicorn running on http://127.0.0.1:8087
   ```

### Using the Agent

Once the server is running, you can interact with it:

**Using cURL:**
```bash
curl -X POST http://127.0.0.1:8087/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "text": "Create a comprehensive business and technical plan for an AI-hiring platform"
      }
    ]
  }'
```

**Using Python:**
```python
import requests
import json

response = requests.post(
    "http://127.0.0.1:8087/chat",
    json={
        "messages": [
            {
                "role": "user",
                "text": "What are the key features we need for MVP?"
            }
        ]
    }
)
print(response.json())
```

## Development

### Debugging

For interactive debugging with VS Code:

1. Install debug tools:
   ```bash
   pip install debugpy agent-dev-cli --pre
   ```

2. Press `F5` in VS Code to start debugging (requires `.vscode/launch.json` configuration)

### Project Structure

```
vanda/
├── business_team.py       # Main multi-agent workflow
├── requirements.txt       # Python dependencies
├── .env                   # Configuration (add your tokens here)
├── README.md              # This file
└── .vscode/
    ├── launch.json        # Debug configuration
    └── tasks.json         # Build tasks
```

## How It Works

1. **User Input**: Send a request to the HTTP server with your business question
2. **Strategy Phase**: Strategy Agent analyzes the market opportunity
3. **Architecture Phase**: Technical Architect designs the system
4. **Analysis Phase**: Business Analyst creates requirements and roadmap
5. **Development Phase**: Builder Agent provides implementation guidance
6. **Review Phase**: Reviewer Agent polishes and finalizes the output

Each agent receives the conversation history and builds upon the previous agent's insights.

## Models

This project uses **gpt-4o-mini** by default (via GitHub Models) which provides:
- Good reasoning capability for complex tasks
- Fast response times
- Low cost
- Free trial access

For production, consider upgrading to:
- **gpt-4.1** (better reasoning for complex architecture decisions)
- **claude-opus-4-5** (excellent for strategic thinking)

## Troubleshooting

### "No module named 'agent_framework'"
```bash
pip install -r requirements.txt
```

### "GITHUB_TOKEN not found"
Update your `.env` file with your GitHub Personal Access Token from https://github.com/settings/tokens

### Port 8087 already in use
Edit `.env` and change `AGENT_SERVER_PORT=8087` to a different port, then update client requests accordingly.

### Authentication errors
- For GitHub models: Ensure your token is valid and has no expiration
- For Foundry models: Run `az login` to authenticate with Azure

## Next Steps

1. **Ask the team questions** about your business idea
2. **Iterate** - refine requirements based on feedback
3. **Extract artifacts** - use generated plans, architecture docs, and code samples
4. **Scale up** - add more agents or specialize existing ones
5. **Connect to real systems** - integrate with your actual development workflow

## Resources

- [Microsoft Agent Framework Documentation](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [GitHub Models Documentation](https://github.com/marketplace/models)

## License

This project is provided as an example. Feel free to modify and extend it for your needs.
