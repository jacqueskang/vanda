"""Shared context helpers for agent tool execution."""

import contextvars

_current_agent_context: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_agent", default=""
)


def set_agent_context(agent_key: str) -> None:
    """Set the current executing agent context."""
    _current_agent_context.set(agent_key)


def get_agent_context() -> str:
    """Get the current executing agent context."""
    return _current_agent_context.get()
