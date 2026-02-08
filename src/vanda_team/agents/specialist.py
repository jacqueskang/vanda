"""Base class for specialist agents that only respond when mentioned."""

import re
from typing import List
from agent_framework import ChatMessage
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
    def build_instructions(cls) -> str:
        """Build instructions with specialist requirements."""
        instructions = super().build_instructions()
        return instructions + cls.specialist_instructions
