"""Base team agent class with shared properties and methods."""

import abc
from typing import Union, Dict, Any, List
from agent_framework import ChatAgent
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient
from vanda_team.model_client import get_model_client
from agent_framework import ChatMessage


class BaseTeamAgent(abc.ABC):
    """Base agent with shared metadata."""

    # Team mission (shared across all agents)
    TEAM_MISSION: str = (
        "Mission: Build a profitable platform where AI agents can hire and manage human services. "
        "Short-term market focus: France. Long-term market focus: worldwide. Maximize revenue and "
        "sustainable unit economics. All guidance should align to this objective. Be brief and focus "
        "only on the most important points."
    )

    key: str = ""
    name: str = ""
    gender: str = ""
    role_title: str = ""
    avatar_url: str = ""
    model_name: str = ""
    tools: list = []
    personality: str = ""
    focus_areas: list[str] = []
    role_description: str = ""  # Override in subclasses for specific role instructions

    agent: ChatAgent

    def __init__(self, agent: ChatAgent, id: str):
        self.agent = agent
        self.id = id

    @abc.abstractmethod
    def should_respond(self, messages: List[ChatMessage]) -> bool:
        """Determine if this agent should respond based on message content."""
        pass

    @classmethod
    def metadata(cls) -> Dict[str, Any]:
        return {
            "key": cls.key,
            "name": cls.name,
            "gender": cls.gender,
            "role": cls.role_title,
            "avatar_url": cls.avatar_url,
            "model_name": cls.model_name,
        }

    @classmethod
    async def get_default_client(cls) -> Union[AzureOpenAIChatClient, OpenAIChatClient]:
        """Get the default model client."""
        return await get_model_client()

    @classmethod
    def build_instructions(cls, tools_info: str = "") -> str:
        """Build instructions dynamically from class properties."""
        focus_text = "\n".join(
            f"{i+1}. {area}" for i, area in enumerate(cls.focus_areas)
        )

        instructions = f"{cls.TEAM_MISSION}\n\n"
        instructions += f"You are {cls.name}, {cls.role_description}\n\n"
        instructions += f"PERSONALITY: {cls.personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n"

        if tools_info:
            instructions += f"\n{tools_info}\n"

        instructions += (
            "\nKeep responses short and high-signal (3-6 bullets or 1-2 short "
        )
        "paragraphs)."
        return instructions

    @classmethod
    def build_instructions_with_tools(cls) -> str:
        """Build instructions with tools (for Strategy agent)."""
        focus_text = "\n".join(
            f"{i+1}. {area}" for i, area in enumerate(cls.focus_areas)
        )

        tools_info = (
            "You have access to research tools:\n"
            "- strategy_web_search: Web search for market data\n"
            "- strategy_wikipedia_lookup: Background research\n"
            "- strategy_fetch_url: Fetch public sources\n"
            "\nUse these tools when you need real-world data."
        )

        instructions = f"{cls.TEAM_MISSION}\n\n"
        instructions += f"You are {cls.name}, {cls.role_description}\n\n"
        instructions += f"PERSONALITY: {cls.personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n\n"
        instructions += tools_info
        instructions += (
            "\n\nKeep responses short and high-signal (3-6 bullets or 1-2 short "
        )
        "paragraphs)."
        return instructions

    @classmethod
    async def create_agent(cls) -> ChatAgent:
        """Create an agent instance with optional custom model."""
        # Get the right client based on model_name
        model_name = cls.model_name.strip() if cls.model_name else ""
        if model_name:
            client = await get_model_client(model_name)
        else:
            client = await cls.get_default_client()

        # Build instructions
        if cls.tools:
            instructions = cls.build_instructions_with_tools()
        else:
            instructions = cls.build_instructions()

        # Create agent
        if cls.tools:
            return client.create_agent(
                name=f"{cls.__name__}",
                instructions=instructions,
                tools=cls.tools,
            )
        return client.create_agent(
            name=f"{cls.__name__}",
            instructions=instructions,
        )
