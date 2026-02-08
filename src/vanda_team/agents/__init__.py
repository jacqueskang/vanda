"""AI Business Team - Multi-agent coordinator system."""

from typing import Dict, Any
from agent_framework import ChatAgent, WorkflowBuilder

from .analyst import BusinessAnalystAgent
from .architect import TechnicalArchitectAgent
from .assistant import CEOAssistantAgent
from .base import BaseTeamAgent
from .builder import BuilderAgent
from .reviewer import ReviewerAgent
from .strategy import StrategyAgent

AGENT_METADATA = {
    StrategyAgent.key: StrategyAgent.metadata(),
    TechnicalArchitectAgent.key: TechnicalArchitectAgent.metadata(),
    BusinessAnalystAgent.key: BusinessAnalystAgent.metadata(),
    BuilderAgent.key: BuilderAgent.metadata(),
    ReviewerAgent.key: ReviewerAgent.metadata(),
    CEOAssistantAgent.key: CEOAssistantAgent.metadata(),
}

_workflow_cache = None
_agents_cache = None


async def get_or_create_agents() -> Dict[str, ChatAgent]:
    """Get or create the agent map (cached for performance)."""
    global _agents_cache

    if _agents_cache is not None:
        return _agents_cache

    strategy_agent = await StrategyAgent.create_agent()
    architect_agent = await TechnicalArchitectAgent.create_agent()
    analyst_agent = await BusinessAnalystAgent.create_agent()
    builder_agent = await BuilderAgent.create_agent()
    reviewer_agent = await ReviewerAgent.create_agent()
    assistant_agent = await CEOAssistantAgent.create_agent()

    _agents_cache = {
        "strategy": strategy_agent,
        "architect": architect_agent,
        "analyst": analyst_agent,
        "builder": builder_agent,
        "reviewer": reviewer_agent,
        "assistant": assistant_agent,
    }

    return _agents_cache


async def get_or_create_workflow() -> Any:
    """Get or create the multi-agent workflow (cached for performance)."""
    global _workflow_cache

    if _workflow_cache is not None:
        return _workflow_cache

    print("[*] Initializing AI agent team...")

    print("[*] Creating specialized agents...")

    strategy_agent = await StrategyAgent.create_agent()

    architect_agent = await TechnicalArchitectAgent.create_agent()

    analyst_agent = await BusinessAnalystAgent.create_agent()

    builder_agent = await BuilderAgent.create_agent()

    reviewer_agent = await ReviewerAgent.create_agent()

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
    return workflow


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
    "AGENT_METADATA",
]
