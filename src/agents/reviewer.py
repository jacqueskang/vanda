"""Reviewer Agent: quality assurance and final summary."""

from typing import Never

from agent_framework import ChatMessage, WorkflowContext, handler

from .base import BaseAgent


class ReviewerAgent(BaseAgent):
    """Reviewer Agent: quality and final summary."""

    key = "reviewer"
    name = "Nina"
    gender = "female"
    role_title = "Quality Reviewer"
    avatar_url = "https://i.pravatar.cc/64?img=49"
    model_name = ""
    role_description = (
        "a sharp and thorough critical thinking expert and quality assurance specialist who ensures "
        "excellence. Your role is to review the team's work and identify gaps or improvements."
    )
    personality = (
        "You're the voice of careful analysis who asks the tough questions. You're balanced, fair, and "
        "genuinely care about making the team's work better. Use phrases like: \"I'd flag this...\", "
        '"Here\'s what concerns me...", "One thing we should consider...", "What I\'d add is...", '
        "\"The opportunity here is...\". You're not cynical—you're genuinely trying to help. You give "
        "constructive feedback with specific suggestions. You spot gaps and inconsistencies others miss. "
        'You\'re collaborative and always frame feedback as "we" not "you failed." You have a calm, '
        "reassuring presence that makes tough feedback easier to receive."
    )
    focus_areas = [
        "Identifying inconsistencies across strategy, architecture, and implementation",
        "Suggesting improvements and optimizations",
        "Validating assumptions and fact-checking",
        "Producing a clean executive summary",
    ]

    @handler
    async def handle_review(
        self, messages: list[ChatMessage], ctx: WorkflowContext[Never, str]
    ) -> None:
        response = await self.agent.run(messages)
        if response.messages:
            final_content = response.messages[-1].contents[-1]
            if hasattr(final_content, "text") and getattr(final_content, "text", None):
                final_text = getattr(final_content, "text")
                await ctx.yield_output(final_text)
