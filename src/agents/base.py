"""Base team agent class with shared properties and methods."""

import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, Union
from agent_framework import ChatAgent, Executor
from agent_framework.azure import AzureOpenAIChatClient
from agent_framework.openai import OpenAIChatClient
from azure.identity.aio import DefaultAzureCredential


@dataclass
class AgentMetadata:
    """Metadata for team agents."""

    key: str
    name: str
    gender: str
    role: str
    avatar_url: str
    model_name: str


class BaseAgent(Executor):
    """Configurable agent with properties driven by config dict."""

    # Team mission (shared across all agents)
    TEAM_MISSION: str = (
        "Mission: Build a profitable platform where AI agents can hire and manage human services. "
        "Short-term market focus: France. Long-term market focus: worldwide. Maximize revenue and "
        "sustainable unit economics. All guidance should align to this objective. Be brief and focus "
        "only on the most important points."
    )

    logger = logging.getLogger(__name__)

    def __init__(self, agent: ChatAgent, config: Dict[str, Any]):
        """Initialize agent with ChatAgent and configuration dict.

        Args:
            agent: The ChatAgent instance.
            config: Configuration dictionary containing agent properties.
        """
        self.agent = agent
        self.config = config

        # Set properties from config
        self.key = config.get("key", "")
        self.name = config.get("name", "")
        self.gender = config.get("gender", "")
        self.role_title = config.get("role_title", "")
        self.avatar_url = config.get("avatar_url", "")
        self.model_name = config.get("model_name", "")
        self.role_description = config.get("role_description", "")
        self.personality = config.get("personality", "")
        self.focus_areas = config.get("focus_areas", [])
        self.tools = config.get("tools", [])

        self.id = self.key

    @classmethod
    async def create(cls, config: Dict[str, Any]) -> "BaseAgent":
        """Factory method to create a fully initialized agent instance.

        Args:
            config: Configuration dictionary for the agent.

        Returns:
            BaseAgent: Initialized agent instance.
        """
        # Initialize model client
        model_name = config.get("model_name", "")
        client = await cls._get_model_client(model_name)
        instructions = cls._build_instructions_from_config(config)

        # Resolve tools from tool names in config
        tools = cls._resolve_tools(config.get("tools", []))

        # Create ChatAgent with or without tools
        if tools:
            chat_agent = client.create_agent(
                name=config.get("name", "Agent"),
                instructions=instructions,
                tools=tools,
            )
        else:
            chat_agent = client.create_agent(
                name=config.get("name", "Agent"),
                instructions=instructions,
            )

        return cls(chat_agent, config)

    def metadata(self) -> AgentMetadata:
        """Return metadata for this agent.

        Returns:
            AgentMetadata: Agent metadata.
        """
        return AgentMetadata(
            key=self.key,
            name=self.name,
            gender=self.gender,
            role=self.role_title,
            avatar_url=self.avatar_url,
            model_name=self.model_name,
        )

    async def run_with_context(self, messages: list[Any]) -> Any:
        """Run the agent with context set for tool execution.

        This ensures that when tools are called, they know which agent is executing.

        Args:
            messages: List of chat messages to process.

        Returns:
            Agent response.
        """
        from .tools.context import set_agent_context

        # Debug logging: show messages sent to this agent
        self.logger.debug(
            "Agent '%s' (%s) receiving %s messages",
            self.name,
            self.key,
            len(messages),
        )
        for i, msg in enumerate(
            messages[-5:], start=max(0, len(messages) - 5)
        ):  # Show last 5
            msg_text = getattr(msg, "text", str(msg))[:100]  # First 100 chars
            self.logger.debug(
                "[%s] %s: %s...",
                i,
                getattr(msg, "role", "unknown"),
                msg_text,
            )

        # Set the agent context before running
        set_agent_context(self.key)
        # Run the agent
        response = await self.agent.run(messages)

        # Debug logging: show agent response
        response_text = ""
        if hasattr(response, "messages") and response.messages:
            for msg in response.messages:
                if hasattr(msg, "text") and msg.text:
                    response_text += msg.text
        self.logger.debug(
            "Agent '%s' response: %s...",
            self.name,
            response_text[:100],
        )

        return response

    @staticmethod
    async def _get_model_client(
        model_name: str = "",
    ) -> Union[AzureOpenAIChatClient, OpenAIChatClient]:
        """Initialize the model client based on configuration.

        Args:
            model_name: Override model name from config. If empty, uses env var.

        Returns:
            Union[AzureOpenAIChatClient, OpenAIChatClient]: Initialized model client.
        """
        model_endpoint = os.getenv(
            "MODEL_ENDPOINT", "https://models.github.ai/inference/"
        ).strip()
        model_name_env = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
        final_model_name = (model_name or model_name_env).strip()
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
                model_id=final_model_name,
                api_key=github_token,
            )
            return openai_client

        credential = DefaultAzureCredential()
        endpoint = model_endpoint
        deployment = final_model_name

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
    def _build_instructions_from_config(cls, config: Dict[str, Any]) -> str:
        """Build instructions from config dictionary.

        Args:
            config: Configuration dictionary for the agent.

        Returns:
            str: Built instructions string.
        """
        name = config.get("name", "")
        role_description = config.get("role_description", "")
        personality = config.get("personality", "")
        focus_areas = config.get("focus_areas", [])

        focus_text = "\n".join(f"{i+1}. {area}" for i, area in enumerate(focus_areas))

        instructions = f"{cls.TEAM_MISSION}\n\n"
        instructions += f"You are {name}, {role_description}\n\n"
        instructions += f"PERSONALITY: {personality}\n\n"
        instructions += f"FOCUS AREAS:\n{focus_text}\n"

        # Note: Tools are listed in the prompt, but actual tool objects are passed separately
        tools_list = config.get("tools", [])
        if tools_list:
            tools_text = "You have access to the following tools:\n"
            # If tools are strings (tool names), just list them
            if isinstance(tools_list, list) and len(tools_list) > 0:
                if isinstance(tools_list[0], str):
                    for tool_name in tools_list:
                        tools_text += f"- {tool_name}\n"
                else:
                    # If they are objects, try to get name/description
                    for tool in tools_list:
                        tool_name = getattr(tool, "name", str(tool))
                        tool_desc = getattr(tool, "description", "")
                        tools_text += f"- {tool_name}"
                        if tool_desc:
                            tools_text += f": {tool_desc}"
                        tools_text += "\n"
            tools_text += "\nUse these tools when needed."
            tools_text += " Before calling any tool, ask the user for approval and wait for explicit confirmation."
            instructions += f"\n{tools_text}\n"

        instructions += (
            "\nKeep responses short and high-signal (3-6 bullets or 1-2 short "
            "paragraphs)."
        )
        return instructions

    @staticmethod
    def _resolve_tools(tool_names):  # type: ignore
        """Resolve tool names to actual tool objects.

        Args:
            tool_names: List of tool names or tool objects.

        Returns:
            list: Resolved tool objects.
        """
        from . import tools as tools_module

        resolved_tools = []
        for tool in tool_names:
            # If it's already an object, keep it
            if not isinstance(tool, str):
                resolved_tools.append(tool)
            else:
                # Try to import the tool by name
                if hasattr(tools_module, tool):
                    tool_obj = getattr(tools_module, tool)
                    resolved_tools.append(tool_obj)
        return resolved_tools
