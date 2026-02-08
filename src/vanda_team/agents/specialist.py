"""Base class for specialist agents that only respond when mentioned."""

import re
from typing import List
from agent_framework import ChatMessage, ChatAgent
from vanda_team.agents.base import BaseTeamAgent


class BaseSpecialistAgent(BaseTeamAgent):
    """Base class for specialist agents that only respond when mentioned."""

    # Specialist agents only respond when explicitly mentioned
    specialist_instructions: str = (
        "\n\nIMPORTANT: You should ONLY respond if you are explicitly mentioned by name in the "
        "message. If you are not mentioned, respond with exactly: 'PASS'\n"
        "When you ARE mentioned, provide a helpful, focused response in your area of expertise."
    )

    def should_respond(self, messages: List[ChatMessage]) -> bool:
        """Specialist agents respond only when mentioned by name."""
        for msg in messages:
            if hasattr(msg, "text"):
                mentions = re.findall(r"@(\w+)", msg.text, re.IGNORECASE)
                for mention in mentions:
                    if mention.lower() == self.name.lower():
                        return True
        return False

    @classmethod
    async def create_agent(cls) -> ChatAgent:
        """Create an agent instance with specialist instructions."""
        # Get the right client based on model_name
        model_name = cls.model_name.strip() if cls.model_name else ""
        client = await cls.get_model_client(model_name if model_name else None)

        # Build instructions
        if cls.tools:
            instructions = cls.build_instructions_with_tools()
        else:
            instructions = cls.build_instructions()

        # Add specialist instructions
        instructions += cls.specialist_instructions

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
