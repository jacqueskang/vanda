"""VandaTeam class for managing the business team agents."""

import logging
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

    logger = logging.getLogger(__name__)

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
        response = await self.agents[agent_key].run_with_context(messages)
        response_text = self.extract_response_text(response)
        return self.create_agent_result(agent_key, response_text)

    async def determine_responders(
        self, messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """Determine which agents should respond using the router agent.

        The router analyzes the chat history and determines which agents are relevant
        to the current message based on context and expertise areas.

        Supports structured collaboration with roles: propose -> critique -> evaluate.
        Max 3 agent turns.

        Args:
            messages: List of chat messages to evaluate.

        Returns:
            List of agent response dictionaries.
        """

        # Use the router agent to determine which agents should respond
        agent_roles = await self.router.analyze_and_route(messages)
        self.logger.debug(
            "Router recommended agents with roles: %s",
            agent_roles,
        )

        # Max 3 turns for collaboration
        max_turns = 3

        active_results = []
        current_messages = messages

        # Build role context for the first turn
        if len(agent_roles) > 1:
            role_context = self._build_role_context(agent_roles)
            current_messages = current_messages + [
                ChatMessage(
                    role=Role.SYSTEM,
                    text=f"Collaboration sequence: {role_context}. Each agent should build on previous responses."
                )
            ]

        # Run agents in sequence (one agent per turn, max 3 turns)
        for turn in range(max_turns):
            if turn >= len(agent_roles):
                break

            agent_spec = agent_roles[turn]
            agent_key = agent_spec.get("key")
            role = agent_spec.get("role", "respond")

            if agent_key not in self.agents:
                continue

            # Add role context to prompt
            turn_messages = self._add_role_context(current_messages, role, turn + 1, len(agent_roles))

            result = await self.run_agent_with_messages(agent_key, turn_messages)

            # Add role info to result
            result["role"] = role
            result["turn"] = turn + 1
            active_results.append(result)

            # Add this response to the conversation for context
            agent_name = self.agents[agent_key].name
            current_messages = current_messages + [
                ChatMessage(
                    role=Role.ASSISTANT,
                    text=f"[{agent_name} ({role})]: {result['output']}"
                )
            ]

        return active_results

    async def determine_responders_stream(
        self, messages: List[ChatMessage]
    ):
        """Streaming version of determine_responders - yields each result as it completes.

        Args:
            messages: List of chat messages to evaluate.

        Yields:
            Agent response dictionaries as they complete.
        """
        import asyncio

        # Use the router agent to determine which agents should respond
        agent_roles = await self.router.analyze_and_route(messages)
        self.logger.debug(
            "Router recommended agents with roles: %s",
            agent_roles,
        )

        max_turns = min(3, len(agent_roles))
        current_messages = messages

        # Build role context for collaboration
        if len(agent_roles) > 1:
            role_context = self._build_role_context(agent_roles)
            current_messages = current_messages + [
                ChatMessage(
                    role=Role.SYSTEM,
                    text=f"Collaboration sequence: {role_context}. Each agent should build on previous responses."
                )
            ]

        # Run agents and yield each result as it completes
        for turn in range(max_turns):
            agent_spec = agent_roles[turn]
            agent_key = agent_spec.get("key")
            role = agent_spec.get("role", "respond")

            if agent_key not in self.agents:
                continue

            turn_messages = self._add_role_context(current_messages, role, turn + 1, len(agent_roles))

            result = await self.run_agent_with_messages(agent_key, turn_messages)
            result["role"] = role
            result["turn"] = turn + 1

            yield result

            # Small delay between agents to make discussion visible
            if turn < max_turns - 1:
                self.logger.debug(f"Agent {agent_key} done, waiting before next agent...")
                await asyncio.sleep(1.0)

            # Add response to context for next agent
            agent_name = self.agents[agent_key].name
            current_messages = current_messages + [
                ChatMessage(
                    role=Role.ASSISTANT,
                    text=f"[{agent_name} ({role})]: {result['output']}"
                )
            ]

    def _build_role_context(self, agent_roles: List[Dict[str, str]]) -> str:
        """Build a description of the collaboration sequence.

        Args:
            agent_roles: List of agent specs with 'key' and 'role'.

        Returns:
            Human-readable collaboration sequence.
        """
        parts = []
        for spec in agent_roles:
            key = spec.get("key", "")
            role = spec.get("role", "respond")
            agent_name = self.agents.get(key, None)
            name = agent_name.name if agent_name else key
            parts.append(f"{name} ({role})")
        return " -> ".join(parts)

    def _add_role_context(
        self, messages: List[ChatMessage], role: str, turn: int, total: int
    ) -> List[ChatMessage]:
        """Add role context to messages for a specific turn.

        Args:
            messages: Original messages.
            role: Current agent's role (propose/critique/evaluate/respond).
            turn: Current turn number.
            total: Total number of agents in sequence.

        Returns:
            Messages with role context added.
        """
        role_guidance = {
            "propose": "Make your initial proposal or suggestion. Be specific and actionable.",
            "critique": "Evaluate the proposal critically. Identify issues, gaps, or improvements needed.",
            "evaluate": "Review and provide final assessment. Consider feasibility, risks, and benefits.",
            "respond": "Provide a direct, helpful answer to the user's question.",
        }
        guidance = role_guidance.get(role, role_guidance["respond"])

        context_msg = ChatMessage(
            role=Role.SYSTEM,
            text=f"Your role: {role} (turn {turn}/{total}). {guidance}"
        )
        return messages + [context_msg]

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
