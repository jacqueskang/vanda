from agent_framework._tools import ai_function as tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

from .approval import require_tool_approval, summarize_text

_wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())  # type: ignore


@tool
def wikipedia_lookup(query: str) -> str:
    """Lookup background information on Wikipedia."""
    approved, message = require_tool_approval(
        tool_name="wikipedia_lookup",
        summary=summarize_text("Lookup Wikipedia for", query),
        arguments={"query": query},
    )
    if not approved:
        return message
    try:
        result = _wiki_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"
