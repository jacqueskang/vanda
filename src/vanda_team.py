"""VandaTeam class for managing the business team agents."""

from dataclasses import asdict
from typing import Dict, List, Any, Optional

from agent_framework import Role, ChatMessage

from agents import (
    BaseAgent,
    AgentMetadata,
    AgentLoader,
    RouterAgent,
)


class VandaTeam:
    """Manages the Vanda AI business team and agent interactions."""

    def __init__(self, agents: Dict[str, BaseAgent], router: RouterAgent):
        """Initialize the team with a dictionary of agents.

        Args:
            agents: Dictionary mapping agent keys to agent instances.
            router: Router agent for determining which agents should respond.
        """
        self.agents = agents
        self.router = router

    @classmethod
    async def create(cls) -> "VandaTeam":
        """Create a fully initialized VandaTeam instance.

        Returns:
            VandaTeam: Initialized team with all agents ready.
        """
        # Load all agents from YAML configuration
        agents = await AgentLoader.load_all()

        # Extract router from agents (it's loaded like any other agent)
        router = agents.pop("router")

        # Create team instance
        team = cls(agents, router)  # type: ignore[arg-type]

        # Configure router with team reference for dynamic routing
        router.set_team(team)  # type: ignore

        return team

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

    def create_agent_result(self, agent_key: str, response_text: str) -> Dict[str, Any]:
        """Create result dict for agent response.

        Args:
            agent_key: Key identifying the agent.
            response_text: Response text from the agent.

        Returns:
            Dict containing formatted agent response data.
        """
        estimated_tokens = max(1, len(response_text) // 4) if response_text else 0
        metadata: Optional[AgentMetadata] = None

        # Get metadata from the agent instance
        if agent_key in self.agents:
            metadata = self.agents[agent_key].metadata()

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
        """Determine which agents should respond using the router agent.

        The router analyzes the chat history and determines which agents are relevant
        to the current message based on context and expertise areas.

        Args:
            messages: List of chat messages to evaluate.

        Returns:
            List of agent response dictionaries.
        """
        # Use the router agent to determine which agents should respond
        router_recommendations = await self.router.analyze_and_route(messages)

        active_results = []
        current_messages = messages

        # Run recommended agents in order
        for agent_key in router_recommendations:
            if agent_key not in self.agents:
                continue

            result = await self.run_agent_with_messages(agent_key, current_messages)

            # Add successful response to results
            active_results.append(result)

            # Add this response to the conversation for context
            current_messages = current_messages + [
                ChatMessage(role=Role.ASSISTANT, text=result["output"])
            ]

        return active_results

    def get_team_description(self) -> str:
        """Build team description from agents for routing context.

        Returns:
            str: Formatted team member descriptions.
        """
        descriptions = []
        for key, agent in self.agents.items():
            desc = f"- {agent.name} ({agent.role_title}, key='{key}'): "
            if agent.role_description:
                desc += agent.role_description
            descriptions.append(desc)

        return "\n".join(descriptions)

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
