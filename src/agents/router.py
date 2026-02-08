"""Router Agent: analyzes chat and determines which agents should respond."""

import json
from typing import Dict, List

from agent_framework import ChatMessage

from .base import BaseAgent


class RouterAgent(BaseAgent):
    """Router Agent: analyzes context and routes to appropriate agents."""

    key = "router"
    name = "Router"
    gender = "neutral"
    role_title = "Message Router"
    avatar_url = ""
    model_name = ""
    role_description = (
        "an intelligent message router that analyzes conversations and determines "
        "which team members should respond."
    )
    personality = (
        "You are precise, analytical, and objective. You analyze context without bias."
    )
    focus_areas = [
        "Analyze conversation context and topics",
        "Route messages to appropriate specialists",
        "Understanding the domain of each team member",
    ]

    def __init__(self, agent) -> None:  # type: ignore
        """Initialize the router agent.

        Args:
            agent: The ChatAgent instance.
        """
        super().__init__(agent)
        self.team_agents: Dict[str, BaseAgent] = {}

    def set_team_agents(self, agents: Dict[str, BaseAgent]) -> None:
        """Set the team agents for dynamic routing configuration.

        Args:
            agents: Dictionary of agent key to BaseAgent instances.
        """
        self.team_agents = agents

    async def analyze_and_route(self, messages: List[ChatMessage]) -> List[str]:
        """Analyze chat history and determine which agents should respond.

        If the last message explicitly mentions any agents by name, route to them directly.
        Otherwise, use LLM-based analysis to determine appropriate agents.

        Args:
            messages: List of chat messages to analyze.

        Returns:
            List of agent keys that should respond to this message.
        """
        # Check if the last message mentions specific agents
        if messages:
            last_message_text = getattr(messages[-1], "text", "")
            mentioned_agents = self._extract_mentioned_agents(last_message_text)
            if mentioned_agents:
                return mentioned_agents

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

    def _extract_mentioned_agents(self, text: str) -> List[str]:
        """Extract agent names mentioned in the text using @ notation.

        Dynamically builds mapping from actual team agents.

        Args:
            text: Text to search for agent mentions.

        Returns:
            List of agent keys that are mentioned.
        """
        import re

        # Dynamically build agent name to key mapping from team agents
        agent_name_to_key = {}
        for agent_key, agent in self.team_agents.items():
            agent_name = agent.name.lower() if agent.name else ""
            if agent_name:
                agent_name_to_key[agent_name] = agent_key

        # Find all @mentions in the text
        mentions = re.findall(r"@(\w+)", text, re.IGNORECASE)

        # Convert mentions to agent keys
        mentioned_agents: List[str] = []
        for mention in mentions:
            found_agent_key: str | None = agent_name_to_key.get(mention.lower())
            if found_agent_key:
                if found_agent_key not in mentioned_agents:
                    mentioned_agents.append(found_agent_key)

        return mentioned_agents

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

        # Dynamically build team members description from team agents
        team_members_description = self._build_team_members_description()

        prompt = f"""Analyze the following conversation and determine which team members should respond.

Team Members and Their Expertise:
{team_members_description}

Recent Conversation:
{context}

Based on the conversation, which team members should respond? Return ONLY a JSON object with this exact format:
{{
  "agents": ["key1", "key2"],
  "reasoning": "brief explanation"
}}

Example:
{{"agents": ["architect", "builder"], "reasoning": "Technical architecture and implementation guidance needed"}}

If no specialized response is needed, return:
{{"agents": [], "reasoning": "General conversation or current team members can handle"}}

Return ONLY valid JSON, no other text."""

        return prompt

    def _build_team_members_description(self) -> str:
        """Build team members description from actual team agents.

        Returns:
            Formatted string describing all team members and their expertise.
        """
        descriptions = []

        for agent_key, agent in self.team_agents.items():
            # Skip the router itself
            if agent_key == "router":
                continue

            # Get agent details
            agent_name = agent.name or agent_key
            agent_role = agent.role_title
            agent_focus = agent.focus_areas

            # Build focus areas string
            focus_text = ", ".join(agent_focus) if agent_focus else "General support"

            # Format the description
            description = f"- {agent_key} ({agent_name}): {agent_role} - {focus_text}"
            descriptions.append(description)

        return (
            "\n".join(descriptions) if descriptions else "- assistant: General support"
        )

    def _extract_response_text(self, response: object) -> str:
        """Extract text from agent response.

        Args:
            response: Agent response object.

        Returns:
            Extracted text content.
        """
        response_text = ""
        if hasattr(response, "messages") and response.messages:
            for msg in response.messages:
                if hasattr(msg, "text") and msg.text:
                    response_text += msg.text + " "
        return response_text.strip()

    def _parse_agent_recommendations(self, response_text: str) -> List[str]:
        """Parse agent recommendations from response.

        Validates recommendations against actual team agents.

        Args:
            response_text: Text response containing JSON recommendations.

        Returns:
            List of agent keys to respond.
        """
        try:
            # Try to extract JSON from the response
            import re

            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                agents = data.get("agents", [])
                # Validate against actual team agents
                valid_agent_keys = set(self.team_agents.keys())
                valid_agents = [agent for agent in agents if agent in valid_agent_keys]
                return valid_agents
        except (json.JSONDecodeError, AttributeError):
            pass

        return []

    def should_respond(self, messages: List[ChatMessage]) -> bool:
        """Router agent does not respond to messages directly."""
        return False
