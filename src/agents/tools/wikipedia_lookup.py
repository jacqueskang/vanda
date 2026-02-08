from agent_framework._tools import ai_function as tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

_wiki_search = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())  # type: ignore


@tool
def wikipedia_lookup(query: str) -> str:
    """Lookup background information on Wikipedia."""
    try:
        result = _wiki_search.run(query)
        return str(result) if result is not None else "No results found"
    except Exception as e:
        return f"Wikipedia error: {str(e)}"
