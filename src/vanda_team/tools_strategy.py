"""StrategyAgent research tools (LangChain-based)."""

from agent_framework._tools import ai_function as tool
from langchain_community.tools import (
    DuckDuckGoSearchRun,
    WikipediaQueryRun,
    RequestsGetTool,
)
from langchain_community.utilities import WikipediaAPIWrapper, RequestsWrapper

_ddg_search = DuckDuckGoSearchRun()
_wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(wiki_client=None))
_requests_get = RequestsGetTool(
    allow_dangerous_requests=True,
    requests_wrapper=RequestsWrapper(),
)


@tool
def strategy_web_search(query: str) -> str:
    """Search the web for market, competitor, and trend information."""
    try:
        return _ddg_search.run(query)
    except Exception as e:
        return f"Search error: {str(e)}"


@tool
def strategy_wikipedia_lookup(query: str) -> str:
    """Lookup background information on Wikipedia."""
    try:
        return _wiki_search.run(query)
    except Exception as e:
        return f"Wikipedia error: {str(e)}"


@tool
def strategy_fetch_url(url: str) -> str:
    """Fetch public data from a URL for analysis."""
    try:
        return _requests_get.run(url)
    except Exception as e:
        return f"Fetch error: {str(e)}"


__all__ = [
    "strategy_web_search",
    "strategy_wikipedia_lookup",
    "strategy_fetch_url",
]
