"""GitHub Issues tool for managing product backlogs."""

import os
import json
from typing import Any, Dict
from agent_framework._tools import ai_function as tool

from .approval import require_tool_approval, summarize_text
from .context import get_agent_context

try:
    import requests  # type: ignore[import-untyped]
except ImportError:
    requests = None

DEFAULT_GITHUB_REPO = "team-vanda/vanda-project"


def _get_github_headers() -> Dict[str, str]:
    """Get GitHub API headers with authentication.

    Token requirement:
    - Current executing agent's token (ANALYST_GITHUB_TOKEN, ARCHITECT_GITHUB_TOKEN, etc.)
    """
    # Check current agent's token first
    current_agent = get_agent_context()
    if current_agent:
        token_var = f"{current_agent.upper()}_GITHUB_TOKEN"
        token = os.getenv(token_var)
        if token:
            return {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github.v3+json",
            }

    raise ValueError(
        "No agent-specific GitHub token found for the current agent. "
        "Set {AGENT_KEY}_GITHUB_TOKEN (e.g., ANALYST_GITHUB_TOKEN)."
    )


@tool
def create_backlog_item(
    title: str, description: str, labels: str = "", priority: str = "medium"
) -> str:
    """Create a new backlog item (GitHub issue) for product planning.

    Args:
        title: Brief title of the backlog item
        description: Detailed description including user stories and acceptance criteria
        labels: Comma-separated labels (e.g., "feature,phase1,epic")
        priority: Priority level (low, medium, high, critical)

    Returns:
        JSON string with issue details including issue number and URL
    """
    approved, message = require_tool_approval(
        tool_name="create_backlog_item",
        summary=summarize_text("Create GitHub issue", title),
        arguments={
            "title": title,
            "description": description,
            "labels": labels,
            "priority": priority,
        },
    )
    if not approved:
        return message
    try:
        import requests

        repo = os.getenv("GITHUB_REPO", DEFAULT_GITHUB_REPO)

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = _get_github_headers()

        # Build labels list
        issue_labels = []
        if labels:
            issue_labels.extend([label.strip() for label in labels.split(",")])
        if priority:
            issue_labels.append(f"priority-{priority}")

        payload = {
            "title": title,
            "body": description,
            "labels": issue_labels,
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        issue = response.json()
        return json.dumps(
            {
                "success": True,
                "issue_number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
                "state": issue["state"],
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def list_backlog(filter_labels: str = "", state: str = "open") -> str:
    """List product backlog items (GitHub issues) for the project.

    Args:
        filter_labels: Comma-separated labels to filter by (e.g., "feature,phase1")
        state: Filter by state (open, closed, all)

    Returns:
        JSON string with list of backlog items
    """
    approved, message = require_tool_approval(
        tool_name="list_backlog",
        summary=summarize_text(
            "List GitHub issues", f"labels={filter_labels}, state={state}"
        ),
        arguments={"filter_labels": filter_labels, "state": state},
    )
    if not approved:
        return message
    try:
        import requests

        repo = os.getenv("GITHUB_REPO", DEFAULT_GITHUB_REPO)

        url = f"https://api.github.com/repos/{repo}/issues"
        headers = _get_github_headers()

        params = {
            "state": state,
            "per_page": 50,
            "sort": "updated",
            "direction": "desc",
        }

        if filter_labels:
            params["labels"] = filter_labels

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        issues = response.json()
        backlog_items = [
            {
                "number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "labels": [label["name"] for label in issue["labels"]],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "url": issue["html_url"],
            }
            for issue in issues
        ]

        return json.dumps(
            {"success": True, "total": len(backlog_items), "items": backlog_items}
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def update_backlog_item(
    issue_number: int,
    title: str = "",
    description: str = "",
    labels: str = "",
    state: str = "",
) -> str:
    """Update an existing backlog item (GitHub issue).

    Args:
        issue_number: The issue number to update
        title: New title (optional)
        description: New description (optional)
        labels: Comma-separated labels (optional)
        state: New state - "open" or "closed" (optional)

    Returns:
        JSON string with updated issue details
    """
    approved, message = require_tool_approval(
        tool_name="update_backlog_item",
        summary=summarize_text("Update GitHub issue", f"#{issue_number}"),
        arguments={
            "issue_number": issue_number,
            "title": title,
            "description": description,
            "labels": labels,
            "state": state,
        },
    )
    if not approved:
        return message
    try:
        import requests

        repo = os.getenv("GITHUB_REPO", DEFAULT_GITHUB_REPO)

        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        headers = _get_github_headers()

        payload: Dict[str, Any] = {}
        if title:
            payload["title"] = title
        if description:
            payload["body"] = description
        if labels:
            payload["labels"] = [label.strip() for label in labels.split(",")]
        if state:
            payload["state"] = state

        response = requests.patch(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()

        issue = response.json()
        return json.dumps(
            {
                "success": True,
                "issue_number": issue["number"],
                "title": issue["title"],
                "state": issue["state"],
                "url": issue["html_url"],
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})


@tool
def get_backlog_item(issue_number: int) -> str:
    """Get details of a specific backlog item (GitHub issue).

    Args:
        issue_number: The issue number to retrieve

    Returns:
        JSON string with full issue details
    """
    approved, message = require_tool_approval(
        tool_name="get_backlog_item",
        summary=summarize_text("Get GitHub issue", f"#{issue_number}"),
        arguments={"issue_number": issue_number},
    )
    if not approved:
        return message
    try:
        import requests

        repo = os.getenv("GITHUB_REPO", DEFAULT_GITHUB_REPO)

        url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
        headers = _get_github_headers()

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        issue = response.json()
        return json.dumps(
            {
                "success": True,
                "number": issue["number"],
                "title": issue["title"],
                "body": issue["body"],
                "state": issue["state"],
                "labels": [label["name"] for label in issue["labels"]],
                "created_at": issue["created_at"],
                "updated_at": issue["updated_at"],
                "url": issue["html_url"],
            }
        )
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})
