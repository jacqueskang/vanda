"""Router Agent: analyzes chat and determines which agents should respond."""

import json
import logging
from typing import Dict, List, Any, Optional

from agent_framework import ChatAgent, ChatMessage

from .base import BaseAgent


class RouterAgent(BaseAgent):
    """Router Agent: analyzes context and routes to appropriate agents."""

    logger = logging.getLogger(__name__)

    def __init__(self, agent: ChatAgent, config: Dict[str, Any]) -> None:
        """Initialize the router agent.

        Args:
            agent: The ChatAgent instance.
            config: Configuration dictionary for the agent.
        """
        super().__init__(agent, config)
        self.team: Any = None

    def set_team(self, team: Any) -> None:
        """Set the team reference for dynamic routing configuration.

        Args:
            team: VandaTeam instance for accessing team context.
        """
        self.team = team

    async def analyze_and_route(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """Analyze chat history and determine which agents should respond.

        Uses LLM-based analysis to determine appropriate agents based on context
        and conversation content. Automatically learns agent names, roles, and
        expertise areas from the team composition.

        Args:
            messages: List of chat messages to analyze.

        Returns:
            List of dicts with 'key' and 'role' for each agent to respond.
        """
        # If the last message explicitly mentions agents, prioritize those
        last_message_text = self._get_last_message_text(messages)
        mentioned_agent_keys = self._extract_mentioned_agents(last_message_text)
        if mentioned_agent_keys:
            self.logger.debug(
                "Router: Explicitly mentioned agents: %s",
                mentioned_agent_keys,
            )
            # Convert to role format
            return [{"key": k, "role": "respond"} for k in mentioned_agent_keys]

        # Detect last agent who responded for context continuity
        last_agent_key = self._get_last_responding_agent(messages)
        self.logger.debug("Router: Last responding agent: %s", last_agent_key)

        # Build the routing analysis prompt with full history
        routing_prompt = self._build_routing_prompt(messages, last_agent_key)

        # Create a temporary message for analysis
        analysis_messages = [ChatMessage(role="user", text=routing_prompt)]

        # Run the router agent to get recommendations
        response = await self.run_with_context(analysis_messages)
        response_text = self._extract_response_text(response)

        # Parse the response to get agent roles
        agent_roles = self._parse_agent_roles(response_text)

        # Default to assistant if no agents are recommended
        if not agent_roles:
            agent_roles = [{"key": "assistant", "role": "respond"}]

        # Limit to max 3 agents
        if len(agent_roles) > 3:
            agent_roles = agent_roles[:3]

        return agent_roles

    def _build_routing_prompt(
        self, messages: List[ChatMessage], last_agent_key: Optional[str] = None
    ) -> str:
        """Build the prompt for routing analysis.

        Dynamically builds team member descriptions from actual team agents.

        Args:
            messages: List of chat messages (recent conversation history).
            last_agent_key: Key of the last agent who responded (for continuity).

        Returns:
            Formatted prompt for routing analysis.
        """
        # Get the last 10 messages for context with agent identification
        formatted_messages = []
        for msg in messages[-10:]:
            msg_text = getattr(msg, "text", str(msg))
            role = str(msg.role)

            # Extract agent name from [AgentName]: prefix if present
            if role.lower() in ("assistant", "ASSISTANT") and msg_text.startswith("["):
                end_bracket = msg_text.find("]")
                if end_bracket > 0:
                    # Format as "AgentName (assistant): message"
                    formatted_messages.append(
                        msg_text.replace("]: ", " (assistant): ", 1)
                    )
                    continue

            formatted_messages.append(f"{role}: {msg_text}")

        context = "\n".join(formatted_messages)

        # Dynamically build team member descriptions from team_agents
        team_description = self.team.get_team_description()

        # Add context about last responding agent
        last_agent_note = ""
        if last_agent_key:
            agent = self.team.agents.get(last_agent_key)
            if agent:
                last_agent_note = (
                    f"\n\nNOTE: The last agent to respond was {agent.name} "
                    f"(key='{last_agent_key}'). Consider prioritizing them "
                    f"if the conversation is continuing on the same topic."
                )

        routing_instructions = f"""You are a message router for a business team. Analyze the conversation
and determine which team members should respond, and in what sequence/role.

TEAM MEMBERS:
{team_description}{last_agent_note}

CONVERSATION HISTORY (RECENT CONTEXT):
{context}

Based on the conversation, which team members should respond? Assign roles to enable structured collaboration:
- "propose": Agent makes initial proposal or suggestion
- "critique": Agent evaluates or critiques the proposal
- "evaluate": Agent reviews and provides final assessment
- "respond": Agent gives a direct answer

Return ONLY a JSON object with this format (max 3 agents):
{{"agents": [{{"key": "agent_key", "role": "propose"}}, {{"key": "agent_key", "role": "critique"}}]}}

Rules:
- Assign clear roles to enable collaboration (propose -> critique -> evaluate)
- Order agents in the sequence they should speak
- Use "respond" role for simple questions that don't need collaboration
- If unsure, default to a single agent with "respond" role
"""

        return routing_instructions

    @staticmethod
    def _get_last_message_text(messages: List[ChatMessage]) -> str:
        """Get the last message text from the conversation.

        Args:
            messages: List of chat messages.

        Returns:
            str: Last message text content.
        """
        if not messages:
            return ""
        last_msg = messages[-1]
        return getattr(last_msg, "text", str(last_msg)) or ""

    def _get_last_responding_agent(self, messages: List[ChatMessage]) -> Optional[str]:
        """Identify the last agent who responded in the conversation.

        Args:
            messages: List of chat messages.

        Returns:
            Optional[str]: Key of the last agent who responded, or None.
        """
        # Iterate backwards through messages to find the last assistant response
        for msg in reversed(messages):
            if msg.role == "assistant" or msg.role == "ASSISTANT":
                # Try to identify which agent this was from
                msg_text = getattr(msg, "text", "")
                if msg_text:
                    # Check for agent name prefix format: [AgentName]:
                    if msg_text.startswith("["):
                        end_bracket = msg_text.find("]")
                        if end_bracket > 0:
                            agent_name = msg_text[1:end_bracket]
                            # Find agent by name
                            for key, agent in self.team.agents.items():
                                if agent.name.lower() == agent_name.lower():
                                    return str(key)

                    # Fallback: check if agent name appears in message
                    for key, agent in self.team.agents.items():
                        if agent.name.lower() in msg_text.lower()[:100]:
                            return str(key)
        return None

    @staticmethod
    def _should_continue_with_last_agent(message_text: str) -> bool:
        """Determine if the conversation should continue with the last agent.

        Args:
            message_text: Text of the current user message.

        Returns:
            bool: True if this seems like a continuation of the previous topic.
        """
        # Continuation indicators
        continuation_patterns = [
            "yes",
            "no",
            "thanks",
            "thank you",
            "ok",
            "okay",
            "what about",
            "how about",
            "more",
            "continue",
            "go on",
            "and",
            "also",
            "additionally",
            "furthermore",
            "can you",
            "could you",
            "please",
            "?",
        ]

        message_lower = message_text.lower().strip()

        # Short messages are often continuations
        if len(message_lower.split()) <= 5:
            return True

        # Check for continuation patterns
        for pattern in continuation_patterns:
            if pattern in message_lower:
                return True

        return False

    @staticmethod
    def _extract_mentioned_agents(message_text: str) -> List[str]:
        """Extract explicitly mentioned agents from the last message.

        Args:
            message_text: Text of the last user message.

        Returns:
            List[str]: Agent keys in the order they appear in the message.
        """
        if not message_text:
            return []

        text_lower = message_text.lower()
        agent_name_map = {
            "claire": "strategy",
            "marc": "architect",
            "sophie": "analyst",
            "hugo": "builder",
            "nina": "reviewer",
            "emma": "assistant",
        }

        matches: List[tuple[int, str]] = []
        for name, key in agent_name_map.items():
            for token in (f"@{name}", name):
                index = text_lower.find(token)
                if index != -1:
                    matches.append((index, key))

        if not matches:
            return []

        matches.sort(key=lambda item: item[0])
        ordered_keys = []
        for _, key in matches:
            if key not in ordered_keys:
                ordered_keys.append(key)

        return ordered_keys

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
    def _parse_agent_roles(response_text: str) -> List[Dict[str, str]]:
        """Parse agent roles from LLM response.

        Args:
            response_text: Response text from the router LLM.

        Returns:
            List of dicts with 'key' and 'role' (propose/critique/evaluate/respond).
        """
        import re

        try:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                data = json.loads(json_str)
                agents = data.get("agents", [])
                if isinstance(agents, list) and agents:
                    validated = []
                    for a in agents:
                        if isinstance(a, dict):
                            key = a.get("key", "")
                            role = a.get("role", "respond")
                            if key:
                                validated.append({"key": key, "role": role})
                    if validated:
                        return validated
        except (json.JSONDecodeError, ValueError):
            pass

        # Fallback: try to extract agent names and infer propose role
        agent_keys = RouterAgent._parse_agent_recommendations_fallback(response_text)
        return [{"key": k, "role": "respond"} for k in agent_keys]

    @staticmethod
    def _parse_agent_recommendations_fallback(response_text: str) -> List[str]:
        """Parse agent recommendations from LLM response (fallback).

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
