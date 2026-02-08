from agent_framework._tools import ai_function as tool
from langchain_community.tools import DuckDuckGoSearchRun

from .approval import require_tool_approval, summarize_text

_ddg_search = DuckDuckGoSearchRun()


@tool
def web_search(query: str) -> str:
    """Search the web for market, competitor, and trend information."""
    approved, message = require_tool_approval(
        tool_name="web_search",
        summary=summarize_text("Search the web for", query),
        arguments={"query": query},
    )
    if not approved:
        return message
    try:
        result = _ddg_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Search error: {str(e)}"
