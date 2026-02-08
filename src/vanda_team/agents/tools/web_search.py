from agent_framework._tools import ai_function as tool
from langchain_community.tools import DuckDuckGoSearchRun

_ddg_search = DuckDuckGoSearchRun()


@tool
def strategy_web_search(query: str) -> str:
    """Search the web for market, competitor, and trend information."""
    try:
        result = _ddg_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"
