"""AI Business Team - Multi-agent coordinator system."""

from typing import Dict

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


async def create_all_team_agents() -> Dict[str, BaseAgent]:
    """Create fully initialized team agent instances."""
    strategy_agent = await StrategyAgent.create()
    architect_agent = await TechnicalArchitectAgent.create()
    analyst_agent = await BusinessAnalystAgent.create()
    builder_agent = await BuilderAgent.create()
    reviewer_agent = await ReviewerAgent.create()
    assistant_agent = await CEOAssistantAgent.create()

    return {
        "strategy": strategy_agent,
        "architect": architect_agent,
        "analyst": analyst_agent,
        "builder": builder_agent,
        "reviewer": reviewer_agent,
        "assistant": assistant_agent,
    }


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
    "AGENT_METADATA",
]
