"""AI Business Team - Multi-agent coordinator system."""

from typing import Dict, Optional
from agent_framework import ChatAgent, WorkflowBuilder

from .analyst import BusinessAnalystAgent
from .architect import TechnicalArchitectAgent
from .assistant import CEOAssistantAgent
from .base import BaseAgent, AgentMetadata
from .builder import BuilderAgent
from .reviewer import ReviewerAgent
from .strategy import StrategyAgent

AGENT_METADATA: Dict[str, AgentMetadata] = {
    StrategyAgent.key: StrategyAgent.metadata(),
    TechnicalArchitectAgent.key: TechnicalArchitectAgent.metadata(),
    BusinessAnalystAgent.key: BusinessAnalystAgent.metadata(),
    BuilderAgent.key: BuilderAgent.metadata(),
    ReviewerAgent.key: ReviewerAgent.metadata(),
    CEOAssistantAgent.key: CEOAssistantAgent.metadata(),
}

_team_agents_cache: Optional[Dict[str, BaseAgent]] = None
_workflow_cache: Optional[object] = None


async def create_all_team_agents() -> Dict[str, BaseAgent]:
    """Create fully initialized team agent instances (cached for performance)."""
    global _team_agents_cache

    if _team_agents_cache is not None:
        return _team_agents_cache

    strategy_agent = await StrategyAgent.create()
    architect_agent = await TechnicalArchitectAgent.create()
    analyst_agent = await BusinessAnalystAgent.create()
    builder_agent = await BuilderAgent.create()
    reviewer_agent = await ReviewerAgent.create()
    assistant_agent = await CEOAssistantAgent.create()

    _team_agents_cache = {
        "strategy": strategy_agent,
        "architect": architect_agent,
        "analyst": analyst_agent,
        "builder": builder_agent,
        "reviewer": reviewer_agent,
        "assistant": assistant_agent,
    }

    return _team_agents_cache


async def get_or_create_agents() -> Dict[str, ChatAgent]:
    """Get or create the agent map (cached for performance).

    Deprecated: Use create_all_team_agents() instead for the new unified approach.
    This function remains for backward compatibility.
    """
    team_agents = await create_all_team_agents()
    return {k: v.agent for k, v in team_agents.items()}


async def get_or_create_workflow() -> object:
    """Get or create the multi-agent workflow (cached for performance)."""
    global _workflow_cache

    if _workflow_cache is not None:
        return _workflow_cache

    print("[*] Initializing AI agent team...")

    print("[*] Creating specialized agents...")

    strategy = await StrategyAgent.create()

    architect = await TechnicalArchitectAgent.create()

    analyst = await BusinessAnalystAgent.create()

    builder = await BuilderAgent.create()

    reviewer = await ReviewerAgent.create()

    print("[-] Building multi-agent workflow...")

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
    return workflow


__all__ = [
    "BaseAgent",
    "AgentMetadata",
    "StrategyAgent",
    "TechnicalArchitectAgent",
    "BusinessAnalystAgent",
    "BuilderAgent",
    "ReviewerAgent",
    "CEOAssistantAgent",
    "create_all_team_agents",
    "get_or_create_workflow",
    "get_or_create_agents",
    "AGENT_METADATA",
]
