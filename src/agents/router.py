"""Router Agent: analyzes chat and determines which agents should respond."""

import json
from typing import Dict, List, Any

from agent_framework import ChatAgent, ChatMessage

from .base import BaseAgent


class RouterAgent(BaseAgent):
    """Router Agent: analyzes context and routes to appropriate agents."""

    def __init__(self, agent: ChatAgent, config: Dict[str, Any]) -> None:
        """Initialize the router agent.

        Args:
            agent: The ChatAgent instance.
            config: Configuration dictionary for the agent.
        """
        super().__init__(agent, config)
        self.team_agents: Dict[str, BaseAgent] = {}

    def set_team_agents(self, agents: Dict[str, BaseAgent]) -> None:
        """Set the team agents for dynamic routing configuration.

        Args:
            agents: Dictionary of agent key to BaseAgent instances.
        """
        self.team_agents = agents

    async def analyze_and_route(self, messages: List[ChatMessage]) -> List[str]:
        """Analyze chat history and determine which agents should respond.

        Uses LLM-based analysis to determine appropriate agents based on context
        and conversation content. Automatically learns agent names, roles, and
        expertise areas from the team composition.

        Args:
            messages: List of chat messages to analyze.

        Returns:
            List of agent keys that should respond to this message.
        """
        # Build the routing analysis prompt
        routing_prompt = self._build_routing_prompt(messages)

        # Create a temporary message for analysis
        analysis_messages = [ChatMessage(role="user", text=routing_prompt)]

        # Run the router agent to get recommendations
        response = await self.agent.run(analysis_messages)
        response_text = self._extract_response_text(response)

        # Parse the response to get agent keys
        agent_keys = self._parse_agent_recommendations(response_text)

        # Default to assistant if no agents are recommended
        if not agent_keys:
            agent_keys = ["assistant"]

        return agent_keys

    def _build_routing_prompt(self, messages: List[ChatMessage]) -> str:
        """Build the prompt for routing analysis.

        Dynamically builds team member descriptions from actual team agents.

        Args:
            messages: List of chat messages.

        Returns:
            Formatted prompt for routing analysis.
        """
        # Get the last message or recent context
        context = "\n".join(
            [
                f"{msg.role}: {getattr(msg, 'text', str(msg))}"
                for msg in messages[-5:]  # Last 5 messages for context
            ]
        )

        # Dynamically build team member descriptions from team_agents
        team_description = self._build_team_description()

        routing_instructions = f"""You are a message router for a business team. Analyze the conversation
and determine which team members should respond next.

TEAM MEMBERS:
{team_description}

CONVERSATION CONTEXT:
{context}

Based on the conversation, which team members should respond? Return ONLY a JSON object with this format:
{{"agent_keys": ["key1", "key2"]}}

Rules:
- Return only agent keys that are relevant to the message
- Multiple agents can respond for multidisciplinary questions
- If unsure, default to 'assistant'
- Return empty array if you're really unsure"""

        return routing_instructions

    def _build_team_description(self) -> str:
        """Build dynamic team description from team agents.

        Returns:
            str: Formatted team member descriptions.
        """
        descriptions = []
        for key, agent in self.team_agents.items():
            desc = f"- {agent.name} ({agent.role_title}, key='{key}'): "
            if agent.focus_areas:
                desc += ", ".join(agent.focus_areas[:2])
            descriptions.append(desc)

        return "\n".join(descriptions)

    @staticmethod
    def _extract_response_text(response: Any) -> str:
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
                    response_text += msg.text
        return response_text.strip()

    @staticmethod
    def _parse_agent_recommendations(response_text: str) -> List[str]:
        """Parse agent recommendations from LLM response.

        Args:
            response_text: Response text from the router LLM.

        Returns:
            List of agent keys recommended.
        """
        try:
            # Try to extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                agent_keys = data.get("agent_keys", [])
                if isinstance(agent_keys, list):
                    return agent_keys
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: check if response mentions agent names
        agent_keys = []
        response_lower = response_text.lower()
        agent_name_map = {
            "claire": "strategy",
            "marc": "architect",
            "sophie": "analyst",
            "hugo": "builder",
            "nina": "reviewer",
            "emma": "assistant",
        }

        for name, key in agent_name_map.items():
            if name in response_lower:
                agent_keys.append(key)

        return agent_keys if agent_keys else ["assistant"]
