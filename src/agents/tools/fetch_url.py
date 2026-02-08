from agent_framework._tools import ai_function as tool
from langchain_community.tools import RequestsGetTool
from langchain_community.utilities import RequestsWrapper

from .approval import require_tool_approval, summarize_text

_requests_get = RequestsGetTool(
    allow_dangerous_requests=True,
    requests_wrapper=RequestsWrapper(),
)


@tool
def fetch_url(url: str) -> str:
    """Fetch public data from a URL for analysis."""
    approved, message = require_tool_approval(
        tool_name="fetch_url",
        summary=summarize_text("Fetch URL", url),
        arguments={"url": url},
    )
    if not approved:
        return message
    try:
        result = _requests_get.run(url)
        return str(result) if result is not None else "No content found"
    except Exception as e:
        return f"Fetch error: {str(e)}"
