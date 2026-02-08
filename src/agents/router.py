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

        # Dynamically build team members description from team agents
        team_members_description = self._build_team_members_description()

        prompt = (
            "You are a message router. Analyze the conversation and determine "
            "which specialized team members should respond. Only recommend "
            "specialists when truly needed - the assistant is the default fallback "
            "for all other cases.\n\n"
            "Team Members and Their Expertise:\n"
            f"{team_members_description}\n\n"
            "ROUTING GUIDELINES:\n"
            "- TECHNICAL (architecture, design, tech stacks, language viability) "
            "→ architect\n"
            "- MARKET/STRATEGY (competitive analysis, growth, positioning) "
            "→ strategy\n"
            "- PRODUCT/REQUIREMENTS (features, roadmaps, specifications) → analyst\n"
            "- IMPLEMENTATION/CODE (coding, building, solutions) → builder\n"
            "- QUALITY/REVIEW (testing, validation, QA) → reviewer\n\n"
            "FALLBACK TO ASSISTANT:\n"
            "Return empty agents list for: greetings, general questions, or anything "
            "that doesn't require a specialist. The assistant will automatically handle "
            "as fallback.\n\n"
            f"Recent Conversation:\n{context}\n\n"
            "DECISION RULES:\n"
            "1. Only recommend specialists for their specific domains\n"
            "2. For multi-domain questions, recommend all relevant specialists\n"
            "3. If question doesn't fit specialist domains, return empty list "
            "(assistant is fallback)\n"
            "4. Return empty list for: greetings, small talk, general knowledge\n\n"
            "Return ONLY a JSON object:\n"
            '{"agents": ["key1", "key2"], "reasoning": "brief explanation"}\n\n'
            "Examples:\n"
            '- "Is C# obsolete?" → {"agents": ["architect"], '
            '"reasoning": "Technical question about language viability"}\n'
            '- "What\'s our competitive advantage?" → {"agents": ["strategy"], '
            '"reasoning": "Market and competitive positioning"}\n'
            '- "Hello, how are you?" → {"agents": [], '
            '"reasoning": "Greeting - assistant will handle as fallback"}\n'
            '- "What\'s the weather?" → {"agents": [], '
            '"reasoning": "General knowledge - assistant will handle as fallback"}\n\n'
            "Return ONLY valid JSON, no other text."
        )
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
