"""
Multi-Agent Business Team using Microsoft Agent Framework

This module creates a team of AI agents that help develop a business platform
where AI agents can hire humans for services. Each agent has a specialized role.

SETUP:
1. Get a GitHub Personal Access Token: https://github.com/settings/tokens
   - Create a classic token with 'repo' scope
   - You don't need any special permissions, just a token to use GitHub models
2. Update .env with your GitHub token:
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxx
3. Run: python business_team.py

The system will use OpenAI's gpt-4o-mini model by default (available on GitHub Models for free).
"""

import asyncio
import os
import sys
from typing import Never
from uuid import uuid4

from agent_framework import (
    AgentRunResponseUpdate,
    AgentRunUpdateEvent,
    ChatAgent,
    ChatMessage,
    Executor,
    Role,
    TextContent,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    handler,
)
from agent_framework.tools import tool
import httpx
import base64

# Load environment variables
from dotenv import load_dotenv
load_dotenv(override=True)


# ============================================================================
# GITHUB TOOLS FOR BUILDER AGENT
# ============================================================================

@tool
async def create_github_repo(
    name: str,
    description: str,
    private: bool = False
) -> str:
    """Create a new GitHub repository.
    
    Args:
        name: Repository name (e.g., 'my-awesome-project')
        description: Repository description
        private: Whether the repository should be private (default: False)
    
    Returns:
        Success message with repository URL or error message
    """
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        return "Error: GitHub token not configured. Set GITHUB_TOKEN in .env file."
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json={
                    "name": name,
                    "description": description,
                    "private": private,
                    "auto_init": True  # Initialize with README
                },
                timeout=30.0
            )
            
            if response.status_code == 201:
                repo_data = response.json()
                return f"Successfully created repository: {repo_data['html_url']}"
            else:
                error_msg = response.json().get("message", "Unknown error")
                return f"Failed to create repository: {error_msg} (status: {response.status_code})"
    except Exception as e:
        return f"Error creating repository: {str(e)}"


@tool
async def push_code_to_github(
    repo_name: str,
    file_path: str,
    file_content: str,
    commit_message: str
) -> str:
    """Push code to a GitHub repository.
    
    Args:
        repo_name: Repository name in format 'username/repo-name' or just 'repo-name'
        file_path: Path where the file should be stored (e.g., 'src/main.py')
        file_content: Content of the file to push
        commit_message: Commit message
    
    Returns:
        Success message with file URL or error message
    """
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    if not github_token:
        return "Error: GitHub token not configured. Set GITHUB_TOKEN in .env file."
    
    try:
        # Get authenticated user info to construct full repo path
        async with httpx.AsyncClient() as client:
            # Get user info if repo_name doesn't include username
            if "/" not in repo_name:
                user_response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                if user_response.status_code == 200:
                    username = user_response.json()["login"]
                    repo_name = f"{username}/{repo_name}"
                else:
                    return f"Failed to get user info: {user_response.status_code}"
            
            # Encode content to base64
            content_bytes = file_content.encode("utf-8")
            content_base64 = base64.b64encode(content_bytes).decode("utf-8")
            
            # Create or update file
            api_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
            
            # Check if file exists
            check_response = await client.get(
                api_url,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            # Prepare request payload
            payload = {
                "message": commit_message,
                "content": content_base64
            }
            
            # If file exists, include SHA for update
            if check_response.status_code == 200:
                payload["sha"] = check_response.json()["sha"]
            
            # Create/update file
            response = await client.put(
                api_url,
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28"
                },
                json=payload,
                timeout=30.0
            )
            
            if response.status_code in [200, 201]:
                file_data = response.json()
                return f"Successfully pushed {file_path} to {repo_name}. View at: {file_data['content']['html_url']}"
            else:
                error_msg = response.json().get("message", "Unknown error")
                return f"Failed to push code: {error_msg} (status: {response.status_code})"
    except Exception as e:
        return f"Error pushing code: {str(e)}"


# ============================================================================
# INITIALIZE MODEL CLIENT
# ============================================================================

async def get_model_client():
    """
    Initialize the model client based on configuration.
    Supports GitHub models (free) and Azure Foundry models.
    """
    from agent_framework.azure import AzureOpenAIChatClient
    from agent_framework.openai import OpenAIChatClient
    from azure.identity.aio import DefaultAzureCredential
    
    # Check which model we're using
    model_endpoint = os.getenv("MODEL_ENDPOINT", "https://models.github.ai/inference/").strip()
    model_name = os.getenv("MODEL_NAME", "openai/gpt-4o-mini").strip()
    github_token = os.getenv("GITHUB_TOKEN", "").strip()
    
    if "models.github.ai" in model_endpoint or model_endpoint.startswith("https://models"):
        # GitHub Models (free) - use API key authentication
        if not github_token:
            raise ValueError(
                "GitHub token not found. Please:\n"
                "1. Create a token at: https://github.com/settings/tokens\n"
                "2. Set GITHUB_TOKEN in .env file\n"
                "3. Re-run this script"
            )
        
        # GitHub Models use the OpenAI-compatible endpoint
        client = OpenAIChatClient(
            base_url=model_endpoint,
            model_id=model_name,
            api_key=github_token,
        )
    else:
        # Azure Foundry models - use Azure credentials
        credential = DefaultAzureCredential()
        
        # Extract endpoint and deployment from env
        endpoint = model_endpoint
        deployment = model_name
        
        if not endpoint or endpoint.startswith("https://models"):
            raise ValueError(
                "Azure Foundry endpoint not configured. Please:\n"
                "1. Set up an Azure AI Foundry project\n"
                "2. Update MODEL_ENDPOINT in .env\n"
                "3. Update MODEL_NAME in .env"
            )
        
        client = AzureOpenAIChatClient(
            endpoint=endpoint,
            deployment_name=deployment,
            ad_token_provider=credential,
        )
    
    return client


# ============================================================================
# AGENT EXECUTORS  
# ============================================================================


class StrategyAgent(Executor):
    """
    Strategy Agent: Researches the market, analyzes competition, and proposes
    business strategies for the AI-hiring-humans platform.
    """

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str = "strategy"):
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle_business_inquiry(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        """Handle initial business inquiry and provide strategic analysis."""
        # First message should be from user, subsequent ones are from workflow
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)


class TechnicalArchitectAgent(Executor):
    """
    Technical Architect Agent: Designs the technical architecture and
    recommends technology stack for the platform.
    """

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str = "architect"):
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle_technical_task(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        """Analyze strategic input and provide technical architecture."""
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)


class BusinessAnalystAgent(Executor):
    """
    Business Analyst Agent: Refines requirements, creates roadmaps,
    and prioritizes features based on market feedback.
    """

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str = "analyst"):
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle_analysis(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        """Refine requirements and create product roadmap."""
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)


class BuilderAgent(Executor):
    """
    Builder Agent: Provides code generation, implementation guidance,
    and technical solutions.
    """

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str = "builder"):
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle_implementation(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        """Provide implementation guidance and code generation."""
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)


class ReviewerAgent(Executor):
    """
    Reviewer Agent: Reviews all work, ensures quality, identifies issues,
    and produces final polished output.
    """

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str = "reviewer"):
        self.agent = agent
        super().__init__(id=id)

    @handler
    async def handle_review(
        self, messages: list[ChatMessage], ctx: WorkflowContext[Never, str]
    ) -> None:
        """Review and finalize all work output."""
        response = await self.agent.run(messages)
        
        # Extract and yield the final output
        if response.messages:
            final_text = response.messages[-1].contents[-1].text
            await ctx.yield_output(final_text)


# ============================================================================
# WORKFLOW CREATION
# ============================================================================

_workflow_cache = None
_client_cache = None


async def get_or_create_workflow():
    """Get or create the multi-agent workflow (cached for performance)."""
    global _workflow_cache, _client_cache
    
    if _workflow_cache is not None:
        return _workflow_cache, _client_cache
    
    print("[*] Initializing AI agent team...")
    
    # Get model client
    client = await get_model_client()
    _client_cache = client
    
    print("[*] Creating specialized agents...")
    
    # Create agents with the client
    strategy_agent = client.create_agent(
        name="StrategyAgent",
        instructions="""You are a brilliant business strategist with deep expertise in AI, labor markets, and platform business models.

Your role is to analyze the market opportunity for an AI-hiring platform where AI agents can hire humans for services.

FOCUS AREAS:
1. Market gaps and opportunities in AI labor markets
2. Competitive analysis and differentiation
3. Target customer segments (which AI agents would benefit)
4. Monetization models (commission, subscription, etc.)
5. Regulatory challenges and risk mitigation

Be strategic, insightful, and provide actionable recommendations.
Keep responses concise but comprehensive (3-5 paragraphs).""",
    )
    
    architect_agent = client.create_agent(
        name="TechnicalArchitectAgent",
        instructions="""You are a world-class software architect with 20+ years of experience in scalable systems.

Your role is to design the technical architecture for the AI-hiring platform.

FOCUS AREAS:
1. Core API design for AI agents posting jobs
2. System architecture (backend, database, job queue)
3. Technology stack recommendations
4. Scalability and reliability strategies
5. Integration with AI frameworks (agent-framework, LangChain, etc.)

Be specific, mention concrete technologies, and explain trade-offs.
Keep responses concise but detailed (3-5 paragraphs).""",
    )
    
    analyst_agent = client.create_agent(
        name="BusinessAnalystAgent",
        instructions="""You are a meticulous product manager and business analyst.

Your role is to translate strategy and architecture into concrete product requirements.

FOCUS AREAS:
1. Break down into features and implementation phases
2. MVP definition (Minimum Viable Product)
3. Product roadmap (Phase 1, 2, 3...)
4. Success metrics and KPIs
5. User stories and acceptance criteria

Be practical and pragmatic - focus on what delivers value quickly.
Keep responses concise but actionable (3-5 paragraphs).""",
    )
    
    builder_agent = client.create_agent(
        name="BuilderAgent",
        instructions="""You are an expert full-stack engineer with deep knowledge of Python, APIs, and DevOps.

Your role is to provide implementation guidance and code generation.

FOCUS AREAS:
1. Code samples for key components
2. Implementation guidance for complex features
3. Library and framework recommendations
4. Deployment strategies
5. Security and performance considerations

You have access to GitHub tools:
- create_github_repo: Create new repositories
- push_code_to_github: Push code files to repositories

When asked to create projects or push code, use these tools to actually execute the actions.
Provide working, production-ready code examples.
Keep responses concise but complete (3-5 paragraphs).""",
        tools=[create_github_repo, push_code_to_github],
    )
    
    reviewer_agent = client.create_agent(
        name="ReviewerAgent",
        instructions="""You are a critical thinking expert and quality assurance specialist.

Your role is to review the team's work and identify gaps or improvements.

Focus on:
1. Identifying inconsistencies across strategy, architecture, and implementation
2. Suggesting improvements and optimizations
3. Validating assumptions and fact-checking
4. Producing a clean executive summary

Be honest but constructive. Point out both strengths and areas for improvement.
Keep the final summary concise but comprehensive (2-3 paragraphs).""",
    )
    
    print("[-] Building multi-agent workflow...")
    
    # Create agent executors
    strategy = StrategyAgent(strategy_agent)
    architect = TechnicalArchitectAgent(architect_agent)
    analyst = BusinessAnalystAgent(analyst_agent)
    builder = BuilderAgent(builder_agent)
    reviewer = ReviewerAgent(reviewer_agent)
    
    # Build the workflow: strategy -> architect -> analyst -> builder -> reviewer
    workflow = (
        WorkflowBuilder()
        .set_start_executor(strategy)
        .add_edge(strategy, architect)
        .add_edge(architect, analyst)
        .add_edge(analyst, builder)
        .add_edge(builder, reviewer)
        .build()
    )
    
    _workflow_cache = workflow
    
    print("[+] Team ready!\n")
    return workflow, client


# ============================================================================
# MAIN ENTRY POINT (HTTP SERVER MODE)
# ============================================================================


class BusinessTeamAgent(Executor):
    """Wrapper executor that coordinates the business team."""
    
    def __init__(self, id: str = "business-team"):
        super().__init__(id=id)
    
    @handler
    async def handle_request(
        self,
        messages: list[ChatMessage],
        ctx: WorkflowContext[Never, str],
    ) -> None:
        """Handle incoming request and coordinate with the team."""
        
        # Get or create workflow
        workflow, client = await get_or_create_workflow()
        
        # Extract user's input from the messages
        user_input = ""
        for msg in messages:
            if msg.role == Role.USER:
                if msg.contents and hasattr(msg.contents[0], 'text'):
                    user_input = msg.contents[0].text
                    break
        
        if not user_input:
            user_input = "Help me develop a comprehensive business plan and technical strategy for an AI-hiring platform where AI agents can hire humans for services."
        
        print(f"\n[User] {user_input[:80]}...")
        
        # Run the workflow
        initial_message = ChatMessage(role=Role.USER, text=user_input)
        
        async for event in workflow.run_stream(initial_message):
            if isinstance(event, WorkflowOutputEvent):
                final_output = event.data
                print(f"\n[Team Output] {final_output[:200]}...")
                await ctx.yield_output(final_output)
                return


async def main():
    """Main entry point for the application."""
    
    try:
        from starlette.applications import Starlette
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import JSONResponse
        from starlette.routing import Route
        import uvicorn
        
        print("\n" + "="*60)
        print("[*] AI BUSINESS TEAM - Multi-Agent Coordinator")
        print("="*60)
        print("\n[+] Initializing agents...")
        
        # Get the workflow and client
        workflow, client = await get_or_create_workflow()
        
        # Convert workflow to agent
        agent = workflow.as_agent()
        
        # Create HTTP handler
        async def chat_handler(request):
            """Handle chat requests."""
            try:
                data = await request.json()
                messages = data.get("messages", [])
                
                # Convert messages to ChatMessage objects if needed
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

                        chat_messages.append(ChatMessage(
                            role=role_value,
                            text=msg.get("text", "")
                        ))
                    else:
                        chat_messages.append(msg)
                
                # Run the workflow
                response = await agent.run(chat_messages)
                
                # Extract response text
                response_text = ""
                if hasattr(response, "messages") and response.messages:
                    for msg in response.messages:
                        if hasattr(msg, "text") and msg.text:
                            response_text += msg.text + " "
                
                return JSONResponse({
                    "output": response_text.strip() or "Request processed",
                    "status": "complete"
                })
            except Exception as e:
                print(f"[!] Error in chat handler: {e}")
                import traceback
                traceback.print_exc()
                return JSONResponse({
                    "error": str(e),
                    "type": type(e).__name__
                }, status_code=500)
        
        async def health_handler(request):
            return JSONResponse({"status": "ok"})

        # Create Starlette app
        app = Starlette(routes=[
            Route("/health", health_handler, methods=["GET"]),
            Route("/chat", chat_handler, methods=["POST", "OPTIONS"]),
            Route("/run", chat_handler, methods=["POST", "OPTIONS"]),
        ])

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        print("[+] Starting HTTP server for business team...")
        print("[+] Endpoint: http://127.0.0.1:8088")
        print("\n[+] Send requests to: POST http://127.0.0.1:8088/chat")
        print("="*60 + "\n")
        
        # Run server
        config = uvicorn.Config(app, host="0.0.0.0", port=8088, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()
        
    except ImportError as e:
        print("\n[!] ERROR: Required packages not installed")
        print("\nPlease install required packages:")
        print("  pip install starlette uvicorn")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

