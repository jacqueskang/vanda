"""AI Business Team - Multi-agent coordinator system."""

from typing import Never

from agent_framework import (
    ChatMessage,
    Role,
    WorkflowBuilder,
    WorkflowContext,
    WorkflowOutputEvent,
    handler,
)

from vanda_team.model_client import get_model_client
from vanda_team.tools_strategy import (
    strategy_fetch_url,
    strategy_web_search,
    strategy_wikipedia_lookup,
)

from .analyst import BusinessAnalystAgent
from .architect import TechnicalArchitectAgent
from .assistant import CEOAssistantAgent
from .base import BaseTeamAgent
from .builder import BuilderAgent
from .reviewer import ReviewerAgent
from .strategy import StrategyAgent


TEAM_MISSION = (
    "Mission: Build a profitable platform where AI agents can hire and manage human services. "
    "Short-term market focus: France. Long-term market focus: worldwide. "
    "Maximize revenue and sustainable unit economics. All guidance should align to this objective. "
    "Be brief and focus only on the most important points."
)

AGENT_METADATA = {
    StrategyAgent.key: StrategyAgent.metadata(),
    TechnicalArchitectAgent.key: TechnicalArchitectAgent.metadata(),
    BusinessAnalystAgent.key: BusinessAnalystAgent.metadata(),
    BuilderAgent.key: BuilderAgent.metadata(),
    ReviewerAgent.key: ReviewerAgent.metadata(),
    CEOAssistantAgent.key: CEOAssistantAgent.metadata(),
}

_workflow_cache = None
_client_cache = None
_agents_cache = None


async def get_or_create_agents():
    """Get or create the agent map (cached for performance)."""
    global _agents_cache, _client_cache

    if _agents_cache is not None:
        return _agents_cache

    client = await get_model_client()
    _client_cache = client

    # Specialist agents only respond when explicitly mentioned
    specialist_instructions = (
        "\n\nIMPORTANT: You should ONLY respond if you are explicitly mentioned by name in the message. "
        "If you are not mentioned, respond with exactly: 'PASS'\n"
        "When you ARE mentioned, provide a helpful, focused response in your area of expertise."
    )

    strategy_agent = client.create_agent(
        name="StrategyAgent",
        instructions=StrategyAgent.build_instructions_with_tools(TEAM_MISSION) + specialist_instructions,
        tools=[strategy_web_search, strategy_wikipedia_lookup, strategy_fetch_url],
    )

    architect_agent = client.create_agent(
        name="TechnicalArchitectAgent",
        instructions=TechnicalArchitectAgent.build_instructions(TEAM_MISSION) + specialist_instructions,
    )

    analyst_agent = client.create_agent(
        name="BusinessAnalystAgent",
        instructions=BusinessAnalystAgent.build_instructions(TEAM_MISSION) + specialist_instructions,
    )

    builder_agent = client.create_agent(
        name="BuilderAgent",
        instructions=BuilderAgent.build_instructions(TEAM_MISSION) + specialist_instructions,
    )

    reviewer_agent = client.create_agent(
        name="ReviewerAgent",
        instructions=ReviewerAgent.build_instructions(TEAM_MISSION) + specialist_instructions,
    )

    # CEO Assistant never passes - always available to help
    assistant_agent = client.create_agent(
        name="CEOAssistantAgent",
        instructions=CEOAssistantAgent.build_instructions(TEAM_MISSION),
    )

    _agents_cache = {
        "strategy": strategy_agent,
        "architect": architect_agent,
        "analyst": analyst_agent,
        "builder": builder_agent,
        "reviewer": reviewer_agent,
        "assistant": assistant_agent,
    }

    return _agents_cache


async def get_or_create_workflow():
    """Get or create the multi-agent workflow (cached for performance)."""
    global _workflow_cache, _client_cache

    if _workflow_cache is not None:
        return _workflow_cache, _client_cache

    print("[*] Initializing AI agent team...")

    client = await get_model_client()
    _client_cache = client

    print("[*] Creating specialized agents...")

    strategy_agent = client.create_agent(
        name="StrategyAgent",
        instructions=StrategyAgent.build_instructions_with_tools(TEAM_MISSION),
        tools=[strategy_web_search, strategy_wikipedia_lookup, strategy_fetch_url],
    )

    architect_agent = client.create_agent(
        name="TechnicalArchitectAgent",
        instructions=TechnicalArchitectAgent.build_instructions(TEAM_MISSION),
    )

    analyst_agent = client.create_agent(
        name="BusinessAnalystAgent",
        instructions=BusinessAnalystAgent.build_instructions(TEAM_MISSION),
    )

    builder_agent = client.create_agent(
        name="BuilderAgent",
        instructions=BuilderAgent.build_instructions(TEAM_MISSION),
    )

    reviewer_agent = client.create_agent(
        name="ReviewerAgent",
        instructions=ReviewerAgent.build_instructions(TEAM_MISSION),
    )

    print("[-] Building multi-agent workflow...")

    strategy = StrategyAgent(strategy_agent)
    architect = TechnicalArchitectAgent(architect_agent)
    analyst = BusinessAnalystAgent(analyst_agent)
    builder = BuilderAgent(builder_agent)
    reviewer = ReviewerAgent(reviewer_agent)

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


__all__ = [
    "BaseTeamAgent",
    "StrategyAgent",
    "TechnicalArchitectAgent",
    "BusinessAnalystAgent",
    "BuilderAgent",
    "ReviewerAgent",
    "CEOAssistantAgent",
    "get_or_create_workflow",
    "get_or_create_agents",
    "TEAM_MISSION",
    "AGENT_METADATA",
]
