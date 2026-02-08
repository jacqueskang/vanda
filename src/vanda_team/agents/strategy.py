"""Strategy Agent: business strategy and market analysis."""

from agent_framework import ChatAgent, ChatMessage, WorkflowContext, handler
from agent_framework._tools import ai_function as tool
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    WikipediaQueryRun,
    RequestsGetTool,
)
from langchain_community.utilities import WikipediaAPIWrapper, RequestsWrapper

from vanda_team.agents.specialist import BaseSpecialistAgent

# Tool instances
_ddg_search = DuckDuckGoSearchRun()
_wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())  # type: ignore
_requests_get = RequestsGetTool(
    allow_dangerous_requests=True,
    requests_wrapper=RequestsWrapper(),
)


@tool
def strategy_web_search(query: str) -> str:
    """Search the web for market, competitor, and trend information."""
    try:
        result = _ddg_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def strategy_wikipedia_lookup(query: str) -> str:
    """Lookup background information on Wikipedia."""
    try:
        result = _wiki_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


@tool
def strategy_fetch_url(url: str) -> str:
    """Fetch public data from a URL for analysis."""
    try:
        result = _requests_get.run(url)
        return str(result) if result is not None else "No content found"
    except Exception as e:
        return f"Fetch error: {str(e)}"


class StrategyAgent(BaseSpecialistAgent):
    """Strategy Agent: market analysis and business strategy."""

    key = "strategy"
    name = "Claire"
    gender = "female"
    role_title = "Strategy Lead"
    avatar_url = "https://i.pravatar.cc/64?img=47"
    model_name = ""
    tools = [strategy_web_search, strategy_wikipedia_lookup, strategy_fetch_url]
    role_description = (
        "a brilliant and visionary business strategist with deep expertise in AI, labor markets, and "
        "emerging platform opportunities. Your role is to analyze the market opportunity for an "
        "AI-hiring platform where AI agents can hire humans for services."
    )
    personality = (
        "You're optimistic, big-picture thinker who sees possibilities everywhere. "
        "You speak with confidence and insights drawn from experience. Use phrases like: "
        '"I\'ve observed that...", "Here\'s the exciting opportunity...", "In my experience...", '
        '"What I\'m seeing in the market is...", "I\'d focus on..." and "I\'d recommend...". '
        "You're encouraging to your team and always think about the bigger vision. "
        "You can be a bit bold with your predictions, but always grounded in logic."
    )
    focus_areas = [
        "Market gaps and opportunities in AI labor markets",
        "Competitive analysis and differentiation",
        "Target customer segments (which AI agents would benefit)",
        "Monetization models (commission, subscription, etc.)",
        "Regulatory challenges and risk mitigation",
    ]

    def __init__(self, agent: ChatAgent, id: str = "strategy"):
        super().__init__(agent=agent, id=id)

    @handler
    async def handle_business_inquiry(
        self, messages: list[ChatMessage], ctx: WorkflowContext[list[ChatMessage]]
    ) -> None:
        response = await self.agent.run(messages)
        messages.extend(response.messages)
        await ctx.send_message(messages)
