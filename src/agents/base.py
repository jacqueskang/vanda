"""Base team agent class with shared properties and methods."""

import abc
import os
from dataclasses import dataclass
from typing import Union, List
from agent_framework import ChatAgent, Executor
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient
from azure.identity.aio import DefaultAzureCredential
from agent_framework import ChatMessage


@dataclass
class AgentMetadata:
    """Metadata for team agents."""

    key: str
    name: str
    gender: str
    role: str
    avatar_url: str
    model_name: str


class BaseAgent(Executor, abc.ABC):
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

    def __init__(self, agent: ChatAgent):
        self.agent = agent
        self.id = self.key

    @classmethod
    async def create(cls) -> "BaseAgent":
        """Factory method to create a fully initialized agent instance.

        This handles ChatAgent creation and wrapping it in the team agent.
        """
        # Initialize model client
        client = await cls._get_model_client()
        instructions = cls.build_instructions()

        # Create ChatAgent with or without tools
        if cls.tools:
            chat_agent = client.create_agent(
                name=f"{cls.__name__}",
                instructions=instructions,
                tools=cls.tools,
            )
        else:
            chat_agent = client.create_agent(
                name=f"{cls.__name__}",
                instructions=instructions,
            )

        return cls(chat_agent)

    @abc.abstractmethod
    def should_respond(self, messages: List[ChatMessage]) -> bool:
        """Determine if this agent should respond based on message content."""
        pass

    @classmethod
    def metadata(cls) -> AgentMetadata:
        return AgentMetadata(
            key=cls.key,
            name=cls.name,
            gender=cls.gender,
            role=cls.role_title,
            avatar_url=cls.avatar_url,
            model_name=cls.model_name,
        )

    @classmethod
    async def _get_model_client(cls) -> Union[AzureOpenAIChatClient, OpenAIChatClient]:
        """Initialize the model client based on configuration."""
        model_endpoint = os.getenv(
            "MODEL_ENDPOINT", "https://models.github.ai/inference/"
        ).strip()
        model_name_env = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
        model_name = (cls.model_name or model_name_env).strip()
        github_token = (os.getenv("GITHUB_TOKEN", "") or "").strip()

        if "models.github.ai" in model_endpoint or model_endpoint.startswith(
            "https://models"
        ):
            if not github_token:
                raise ValueError(
                    "GitHub token not found. Please:\n"
                    "1. Create a token at: https://github.com/settings/tokens\n"
                    "2. Set GITHUB_TOKEN in .env file\n"
                    "3. Re-run this script"
                )

            openai_client: OpenAIChatClient = OpenAIChatClient(
                base_url=model_endpoint,
                model_id=model_name,
                api_key=github_token,
            )
            return openai_client

        credential = DefaultAzureCredential()
        endpoint = model_endpoint
        deployment = model_name

        if not endpoint or endpoint.startswith("https://models"):
            raise ValueError(
                "Azure Foundry endpoint not configured. Please:\n"
                "1. Set up an Azure AI Foundry project\n"
                "2. Update MODEL_ENDPOINT in .env\n"
                "3. Update MODEL_NAME in .env"
            )

        client: AzureOpenAIChatClient = AzureOpenAIChatClient(
            endpoint=endpoint,
            deployment_name=deployment,
            ad_token_provider=lambda: credential.get_token(  # type: ignore
                "https://cognitiveservices.azure.com/.default"
            ).token,
        )

        return client

    @classmethod
    def build_instructions(cls) -> str:
        """Build instructions dynamically from class properties."""
        focus_text = "\n".join(
            f"{i+1}. {area}" for i, area in enumerate(cls.focus_areas)
        )

        instructions = f"{cls.TEAM_MISSION}\n\n"
        instructions += f"You are {cls.name}, {cls.role_description}\n\n"
        instructions += f"PERSONALITY: {cls.personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n"

        if cls.tools:
            tools_text = "You have access to the following tools:\n"
            for tool in cls.tools:
                tool_name = getattr(tool, "name", str(tool))
                tool_desc = getattr(tool, "description", "")
                tools_text += f"- {tool_name}"
                if tool_desc:
                    tools_text += f": {tool_desc}"
                tools_text += "\n"
            tools_text += "\nUse these tools when needed."
            instructions += f"\n{tools_text}\n"

        instructions += (
            "\nKeep responses short and high-signal (3-6 bullets or 1-2 short "
            "paragraphs)."
        )
        return instructions
