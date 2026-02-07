# 🚀 Quick Start Guide

## What You've Built

A **multi-agent AI system** that helps you develop your AI-hiring platform business. You now have 5 specialized AI agents working together:

- **Strategy Agent** - Analyzes market opportunities
- **Technical Architect** - Designs the system
- **Business Analyst** - Creates product roadmaps
- **Builder Agent** - Generates code
- **Reviewer Agent** - Polishes and validates output

## Setup (2 minutes)

### Step 1: Get GitHub Token
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: "vanda-ai-business"
4. **No special permissions needed** - just create the token
5. Copy the token (looks like: `ghp_xxxxxxxxxxxxx`)

### Step 2: Configure Token
Edit `c:\Users\jkang\repos\vanda\.env`:

```env
GITHUB_TOKEN=ghp_your_token_here
```

Replace `ghp_your_token_here` with your actual token.

### Step 3: Verify Setup
```bash
cd c:\Users\jkang\repos\vanda
.\venv\Scripts\activate
python verify_setup.py
```

You should see all ✅ checks pass.

## Run the Business Team

### Option A: From Terminal (Simple)
```bash
cd c:\Users\jkang\repos\vanda
.\venv\Scripts\activate
python business_team.py
```

Wait for:
```
Application startup complete
Uvicorn running on http://127.0.0.1:8087
```

### Option B: From VS Code (Debug)
1. Open `c:\Users\jkang\repos\vanda` in VS Code
2. Press `F5` to start debugging
3. Server will start on port 8087

## Ask Questions to Your Team

Once the server is running, use any of these methods:

### Method 1: Using PowerShell
```powershell
$body = @{
    messages = @(
        @{
            role = "user"
            text = "What are the main challenges in building an AI-hiring platform?"
        }
    )
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://127.0.0.1:8087/chat" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body
```

### Method 2: Using cURL (Bash)
```bash
curl -X POST http://127.0.0.1:8087/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "text": "What should be our MVP features for the AI-hiring platform?"
      }
    ]
  }'
```

### Method 3: Using Python
```python
import requests

response = requests.post(
    "http://127.0.0.1:8087/chat",
    json={
        "messages": [
            {
                "role": "user",
                "text": "Create a business and technical plan for our AI-hiring platform"
            }
        ]
    }
)

print(response.json())
```

## Example Questions to Ask

- "What are the biggest business challenges for an AI-hiring platform?"
- "Design the technical architecture for our platform"
- "What should our MVP include?"
- "Generate code samples for the API endpoints"
- "Review the plan and provide a final summary"
- "Should we build this as a SaaS or open-source?"

## Project Structure

```
vanda/
├── business_team.py          # Main multi-agent system
├── verify_setup.py           # Setup verification
├── requirements.txt          # Python dependencies
├── .env                      # Configuration (add your token!)
├── README.md                 # Full documentation
├── QUICKSTART.md            # This file
└── .vscode/               
    ├── launch.json           # Debug configuration
    └── tasks.json            # VS Code tasks
```

## Troubleshooting

### "GitHub token not found"
- Make sure you edited `.env` and added your token
- Token should start with `ghp_`
- Save the file and restart the server

### "Port 8087 already in use"
Edit `.env` and change:
```env
AGENT_SERVER_PORT=8088
```

### "ModuleNotFoundError: No module named 'agent_framework'"
Run:
```bash
.\venv\Scripts\activate
pip install -r requirements.txt
```

### "Connection refused"
- Make sure the server is running (check terminal output)
- Server should say "Uvicorn running on http://127.0.0.1:8087"

## Next Steps

1. **Ask the team questions** about your business
2. **Iterate** based on their feedback
3. **Extract insights** from the responses
4. **Customize agents** by editing their instructions in `business_team.py`
5. **Scale up** by adding more specialized agents

## Customize Your Agents

Open `business_team.py` and find the agent creation section (around line 200). Each `client.create_agent()` has an `instructions` parameter. Edit these to specialize the agents for your needs.

For example, to add a Data Science Agent:
```python
data_agent = client.create_agent(
    name="DataScienceAgent",
    instructions="""You are a data scientist expert...""",
)
```

Then add it to the workflow:
```python
workflow = (
    WorkflowBuilder()
    .set_start_executor(strategy)
    .add_edge(strategy, architect)
    .add_edge(architect, analyst)
    .add_edge(analyst, data_agent)  # Add here
    .add_edge(data_agent, builder)
    .add_edge(builder, reviewer)
    .build()
)
```

## Need Help?

- Agent Framework: https://github.com/microsoft/agent-framework
- GitHub Models: https://github.com/marketplace/models
- Azure AI: https://learn.microsoft.com/en-us/azure/ai-studio/

---

**You're all set! Your AI business team is ready. Let's build something great! 🎉**
