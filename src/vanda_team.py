"""VandaTeam class for managing the business team agents."""

from dataclasses import asdict
from typing import Dict, List, Any, Optional, Type

from agent_framework import Role, ChatMessage

from agents import (
    BaseAgent,
    AgentMetadata,
    StrategyAgent,
    TechnicalArchitectAgent,
    BusinessAnalystAgent,
    BuilderAgent,
    ReviewerAgent,
    AssistantAgent,
)


class VandaTeam:
    """Manages the Vanda AI business team and agent interactions."""

    AGENT_CLASSES: list[Type[BaseAgent]] = [
        StrategyAgent,
        TechnicalArchitectAgent,
        BusinessAnalystAgent,
        BuilderAgent,
        ReviewerAgent,
        AssistantAgent,
    ]

    def __init__(self, agents: Dict[str, BaseAgent]):
        """Initialize the team with a dictionary of agents.

        Args:
            agents: Dictionary mapping agent keys to agent instances.
        """
        self.agents = agents

    @classmethod
    async def create(cls) -> "VandaTeam":
        """Create a fully initialized VandaTeam instance.

        Returns:
            VandaTeam: Initialized team with all agents ready.
        """
        agents = {}
        for agent_class in cls.AGENT_CLASSES:
            agents[agent_class.key] = await agent_class.create()
        return cls(agents)

    @staticmethod
    def extract_response_text(response: Any) -> str:
        """Extract text from agent response.

        Args:
            response: Agent response object.

        Returns:
            str: Extracted text content.
        """
        response_text = ""
        if hasattr(response, "messages") and response.messages:
            for msg in response.messages:
                if hasattr(msg, "text") and msg.text:
                    response_text += msg.text + " "
        return response_text.strip()

    @staticmethod
    def create_agent_result(agent_key: str, response_text: str) -> Dict[str, Any]:
        """Create result dict for agent response.

        Args:
            agent_key: Key identifying the agent.
            response_text: Response text from the agent.

        Returns:
            Dict containing formatted agent response data.
        """
        estimated_tokens = max(1, len(response_text) // 4) if response_text else 0
        metadata: Optional[AgentMetadata] = None
        for agent_class in VandaTeam.AGENT_CLASSES:
            if agent_class.key == agent_key:
                metadata = agent_class.metadata()
                break
        label = agent_key
        if metadata:
            label = f"{metadata.name} ({metadata.role})"

        return {
            "output": response_text or "Request processed",
            "agent": agent_key,
            "agent_label": label,
            "agent_meta": asdict(metadata) if metadata else None,
            "agent_avatar": metadata.avatar_url if metadata else None,
            "tokens_estimated": estimated_tokens,
            "status": "complete",
        }

    async def run_agent_with_messages(
        self, agent_key: str, messages: List[ChatMessage]
    ) -> Dict[str, Any]:
        """Run an agent with given messages.

        Args:
            agent_key: Key identifying which agent to run.
            messages: List of chat messages for context.

        Returns:
            Dict containing agent response data.
        """
        response = await self.agents[agent_key].agent.run(messages)
        response_text = self.extract_response_text(response)
        return self.create_agent_result(agent_key, response_text)

    async def determine_responders(
        self, messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """Determine which agents should respond to the given messages in a chain.

        Args:
            messages: List of chat messages to evaluate.

        Returns:
            List of agent response dictionaries.
        """
        active_results = []
        current_messages = messages
        responded_agents = set()

        while True:
            # Find agents that should respond but haven't yet
            potential_responders = [
                key
                for key, agent in self.agents.items()
                if agent.should_respond(current_messages)
                and key not in responded_agents
            ]

            if not potential_responders:
                break

            # Run the first potential responder (to avoid conflicts, run one at a time)
            responder_key = potential_responders[0]

            result = await self.run_agent_with_messages(responder_key, current_messages)

            if result.get("output", "").strip().upper() != "PASS":
                active_results.append(result)
                responded_agents.add(responder_key)

                # Add this response to the conversation for potential further responses
                current_messages = current_messages + [
                    ChatMessage(role=Role.ASSISTANT, text=result["output"])
                ]

        return active_results

    def get_agents_list(self) -> List[Dict[str, Any]]:
        """Get list of available agents with their metadata.

        Returns:
            List of dicts containing agent information.
        """
        return [
            {
                "key": key,
                "name": agent.name,
                "role": agent.role_title,
                "avatar": agent.avatar_url,
                "description": "",
            }
            for key, agent in self.agents.items()
        ]
