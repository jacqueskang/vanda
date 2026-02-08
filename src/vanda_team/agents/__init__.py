"""AI Business Team - Multi-agent coordinator system."""

from typing import Dict

from .analyst import BusinessAnalystAgent
from .architect import TechnicalArchitectAgent
from .assistant import CEOAssistantAgent
from .base import BaseAgent, AgentMetadata
from .builder import BuilderAgent
from .reviewer import ReviewerAgent
from .strategy import StrategyAgent

AGENT_CLASSES = [
    StrategyAgent,
    TechnicalArchitectAgent,
    BusinessAnalystAgent,
    BuilderAgent,
    ReviewerAgent,
    CEOAssistantAgent,
]

AGENT_METADATA: Dict[str, AgentMetadata] = {
    agent_class.key: agent_class.metadata() for agent_class in AGENT_CLASSES
}


async def create_all_team_agents() -> Dict[str, BaseAgent]:
    """Create fully initialized team agent instances."""
    agents = {}
    for agent_class in AGENT_CLASSES:
        agents[agent_class.key] = await agent_class.create()
    return agents


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
