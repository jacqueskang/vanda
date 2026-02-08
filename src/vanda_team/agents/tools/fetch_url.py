from agent_framework._tools import ai_function as tool
from langchain_community.tools import RequestsGetTool
from langchain_community.utilities import RequestsWrapper

_requests_get = RequestsGetTool(
    allow_dangerous_requests=True,
    requests_wrapper=RequestsWrapper(),
)


@tool
def strategy_fetch_url(url: str) -> str:
    """Fetch public data from a URL for analysis."""
    try:
        result = _requests_get.run(url)
        return str(result) if result is not None else "No content found"
    except Exception as e:
        return f"Fetch error: {str(e)}"
