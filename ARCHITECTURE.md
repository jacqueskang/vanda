# Architecture & Design

## System Overview

The Business Team is a **multi-agent workflow system** built with Microsoft Agent Framework. It coordinates 5 specialized AI agents to help develop your AI-hiring platform business.

```
User Input
    ↓
Strategy Agent (Market Analysis)
    ↓
Technical Architect (System Design)
    ↓
Business Analyst (Requirements & Roadmap)
    ↓
Builder Agent (Implementation Guidance)
    ↓
Reviewer Agent (Quality & Polish)
    ↓
Final Output
```

## Agent Roles

### 1. Strategy Agent
**Input:** User's initial business question/challenge
**Output:** Market analysis and strategic recommendations

**Expertise:**
- Market opportunity analysis
- Competitive landscape
- Target customer segments
- Business risks and mitigation
- Monetization models

**Example Output:**
- Market gap identification
- Competitor analysis
- Customer persona recommendations
- Key success factors

---

### 2. Technical Architect Agent
**Input:** Strategic objectives from Strategy Agent
**Output:** Technical architecture and technology recommendations

**Expertise:**
- System design and architecture
- Technology stack selection
- API design
- Scalability planning
- Integration with AI frameworks

**Example Output:**
- System architecture diagram (text)
- Technology recommendations
- Scaling strategies
- Integration points for AI agents

---

### 3. Business Analyst Agent
**Input:** Strategic and architectural perspectives
**Output:** Concrete requirements and product roadmap

**Expertise:**
- Product management
- Requirements gathering
- Roadmap creation
- Feature prioritization
- Success metrics definition

**Example Output:**
- MVP feature list
- Implementation phases
- User stories
- KPIs and success metrics
- Technical requirements

---

### 4. Builder Agent
**Input:** Requirements and architectural guidance
**Output:** Code samples and implementation guidance

**Expertise:**
- Full-stack engineering
- Code generation
- API implementation
- Database design
- DevOps and deployment

**Example Output:**
- Python/Node.js code samples
- Database schema recommendations
- API endpoint examples
- Deployment strategies
- Docker configuration examples

---

### 5. Reviewer Agent
**Input:** All previous agent outputs
**Output:** Final polish and executive summary

**Expertise:**
- Quality assurance
- Gap identification
- Consistency checking
- Executive communication
- Final recommendations

**Example Output:**
- Consolidated executive summary
- Key highlights and recommendations
- Risk assessment
- Next immediate steps
- Stakeholder-ready document

---

## Workflow Architecture

### WorkflowBuilder Pattern
```python
workflow = (
    WorkflowBuilder()
    .set_start_executor(strategy)           # Entry point
    .add_edge(strategy, architect)          # Pass to next
    .add_edge(architect, analyst)           # And so on...
    .add_edge(analyst, builder)
    .add_edge(builder, reviewer)
    .build()
)
```

### Message Flow
Each agent:
1. Receives complete conversation history from previous agents
2. Runs its specialized AI model
3. Adds new insights to the conversation
4. Passes enriched conversation to next agent

### Output Format
- **Strategy Output:** 3-5 paragraphs of strategic analysis
- **Architecture Output:** Technical diagrams and recommendations
- **Analysis Output:** Structured roadmap and requirements
- **Builder Output:** Code samples and guides
- **Reviewer Output:** Executive summary (2-3 paragraphs)

---

## Technology Stack

### Core Framework
- **Microsoft Agent Framework** - Multi-agent orchestration
- **Python 3.13+** - Runtime
- **Async/Await** - Concurrent agent execution

### AI Models
- **OpenAI GPT-4o-mini** (default via GitHub Models)
- Can use: gpt-4.1, Claude Opus 4.5, or others

### Infrastructure
- **Uvicorn** - HTTP server
- **Starlette** - Web framework
- **Azure Identity** - Authentication
- **dotenv** - Configuration management

### Development
- **debugpy** - Remote debugging
- **agent-dev-cli** - Agent development tools

---

## Data Flow

```
HTTP Request (User Input)
    ↓
BusinessTeamAgent.handle_request()
    ↓
Workflow.run_stream(initial_message)
    ↓
[Agent 1] → ChatMessage[] → [Agent 2] → ... → [Agent 5]
    ↓
ctx.yield_output(final_text)
    ↓
HTTP Response (Final Output)
```

---

## Extensibility

### Adding New Agents

1. Create a new Executor class:
```python
class DataScienceAgent(Executor):
    agent: ChatAgent
    
    def __init__(self, agent: ChatAgent, id: str = "data-scientist"):
        self.agent = agent
        super().__init__(id=id)
    
    @handler
    async def handle_analysis(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)
```

2. Create agent with instructions:
```python
data_agent = client.create_agent(
    name="DataScienceAgent",
    instructions="You are a data science expert...",
)
```

3. Add to workflow:
```python
worker = DataScienceAgent(data_agent)
workflow = (
    WorkflowBuilder()
    .set_start_executor(strategy)
    .add_edge(strategy, architect)
    .add_edge(architect, data_agent)  # New position
    .add_edge(data_agent, analyst)
    # ... rest of edges
    .build()
)
```

### Customizing Agent Behavior

Edit agent instructions in `business_team.py`:
```python
strategy_agent = client.create_agent(
    name="StrategyAgent",
    instructions="YOUR CUSTOM INSTRUCTIONS HERE",
)
```

### Using Different Models

Update `.env`:
```env
# GitHub Models (free)
MODEL_NAME=openai/gpt-4o-mini
# or
MODEL_NAME=meta/llama-3.3-70b-instruct

# Azure Foundry Models (better performance)
MODEL_ENDPOINT=https://your-project.inference.ml.azure.com/
MODEL_NAME=gpt-4o
```

---

## API Specification

### POST /chat

**Request:**
```json
{
  "messages": [
    {
      "role": "user",
      "text": "Your question here"
    }
  ]
}
```

**Response:**
```json
{
  "response": "Final output from the reviewer agent...",
  "status": "complete"
}
```

---

## Performance Considerations

### Sequential Processing
- Agents run one after another (not in parallel)
- Each agent sees full conversation history
- Total time = sum of individual agent times

### Expected Latencies (per agent)
- Strategy Agent: 30-60 seconds
- Technical Architect: 40-70 seconds
- Business Analyst: 40-70 seconds
- Builder Agent: 50-90 seconds (generates code)
- Reviewer Agent: 30-60 seconds

**Total: ~3-5 minutes** for complete workflow

### Optimization Options
1. Use faster models (gpt-4o-mini instead of gpt-4)
2. Run agents in parallel (advanced architecture)
3. Use smaller context windows
4. Cache agent instructions

---

## Security & Best Practices

### Token Management
- Keep GitHub token in `.env` (never commit!)
- `.env` is in `.gitignore`
- Rotate tokens periodically

### Rate Limiting
- GitHub Models: Rate limited based on plan
- Foundry: Rate limited based on quota

### Cost Management
- GitHub Models: Free tier available
- Foundry: Pay-per-request pricing
- Monitor token usage

### Error Handling
- All handlers have try-catch blocks
- Graceful fallback on agent failures
- Clear error messages for debugging

---

## Debugging

### Enable Debug Mode
Press `F5` in VS Code to start with debugger attached.

### Check Logs
```bash
# Terminal shows all agent interactions
# Look for:
# - 👤 User: [...user input...]
# - ExecutorInvokedEvent: [agent name]
# - 📋 Final Team Output: [...output...]
```

### Test Individual Agent
```python
# In Python REPL
import asyncio
from business_team import get_or_create_workflow

workflow, client = asyncio.run(get_or_create_workflow())
# Now you can test individual agents
```

---

## Limitations & Future Improvements

### Current Limitations
- Sequential processing (could be parallel)
- No persistent storage of results
- No user authentication
- No rate limiting on server side

### Future Enhancements
- Parallel agent execution for speed
- Database for storing conversation history
- User authentication & multi-tenant
- Caching for repeated queries
- Agent refinement based on feedback
- Integration with real development tools

---

## References

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Azure AI Foundry](https://learn.microsoft.com/en-us/azure/ai-studio/)
- [GitHub Models](https://github.com/marketplace/models)
- [OpenAI API](https://platform.openai.com/docs)

---

**Your AI business team is ready to work! 🚀**
