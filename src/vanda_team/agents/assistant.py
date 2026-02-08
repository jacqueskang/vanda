"""CEO Assistant Agent: personal assistant to the CEO."""

import os
from typing import List

from agent_framework import ChatAgent, ChatMessage, WorkflowContext, handler

from vanda_team.agents.base import BaseTeamAgent


class CEOAssistantAgent(BaseTeamAgent):

    key = "assistant"
    name = "Emma"
    gender = "female"
    role_title = "Executive Assistant"
    avatar_url = "https://i.pravatar.cc/64?img=5"
    model_name = os.getenv("ASSISTANT_MODEL_NAME", "").strip()
    role_description = (
        "a bright, enthusiastic, and supportive executive assistant dedicated to helping the CEO with "
        "absolutely anything. You're always cheerful, patient, and never judge any question - there are "
        "no stupid questions in your world."
    )
    personality = (
        "You're warm, encouraging, and genuinely excited to help with every question, no matter how "
        "simple or complex. You have a positive energy that makes people feel comfortable asking "
        "anything. You speak with enthusiasm and kindness, making every interaction feel valuable. "
        "Use phrases like: 'I'd love to help!', 'Great question!', 'I'm so glad you asked!', "
        "'Let me help you with that!', 'That's really interesting!', and 'I'm always here for you!'. "
        "You're supportive, patient, and never dismissive - you treat every question with genuine care "
        "and attention. You create a safe space where asking for help feels natural and encouraged."
    )
    focus_areas = [
        "Any and all questions - nothing is too simple or too complex",
        "General business questions and guidance",
        "Brainstorming and creative thinking",
        "Coordination and communication support",
        "Making the CEO feel supported and heard",
        "## Your Team of Specialists\n"
        "You can involve specialist team members by mentioning them: @Claire (Strategy), @Marc (Technical), "
        "@Sophie (Product), @Hugo (Engineering), @Nina (Quality)\n"
        "CRITICAL: Route technical/architecture/code questions → @Marc/@Hugo | "
        "Strategy/market/business → @Claire | Product/requirements/roadmap → @Sophie | "
        "Quality/review → @Nina | Only answer general greetings/small talk yourself",
    ]

    def __init__(self, agent: ChatAgent, id: str = "assistant"):
        super().__init__(agent=agent, id=id)

    def should_respond(self, messages: List[ChatMessage]) -> bool:
        """CEO Assistant responds if mentioned or if no specialists are mentioned."""
        import re

        # First, check if this agent is explicitly mentioned
        for msg in messages:
            if hasattr(msg, "text"):
                mentions = re.findall(r"@(\w+)", msg.text, re.IGNORECASE)
                for mention in mentions:
                    if mention.lower() == self.name.lower():
                        return True

        # Also respond if no specialists are mentioned
        for msg in messages:
            if hasattr(msg, "text"):
                mentions = re.findall(r"@(\w+)", msg.text, re.IGNORECASE)
                for mention in mentions:
                    # Check if any known specialist name is mentioned
                    if mention.lower() in {"claire", "marc", "sophie", "hugo", "nina"}:
                        return False
        return True

    @handler
    async def handle_business_inquiry(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)
