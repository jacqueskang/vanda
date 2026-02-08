"""Tool approval gating for agent tool execution."""

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple
import json
import threading
import time
import uuid


@dataclass(frozen=True)
class ToolApprovalRequest:
    """Represents a pending tool approval request."""

    request_id: str
    tool_name: str
    summary: str
    arguments: Dict[str, Any]
    created_at: float


@dataclass(frozen=True)
class ToolApprovalDecision:
    """Represents a user decision about a tool request."""

    action: str
    request_id: str


class ToolApprovalManager:
    """Manages tool approval requests and decisions."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._pending: Optional[ToolApprovalRequest] = None
        self._approved_id: Optional[str] = None

    def ensure_approval(
        self, tool_name: str, summary: str, arguments: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Ensure a tool has been approved before execution."""
        with self._lock:
            if self._approved_id and self._pending:
                if self._pending.request_id == self._approved_id:
                    self._approved_id = None
                    self._pending = None
                    return True, ""
                self._approved_id = None

            if self._pending:
                return False, _format_request_message(self._pending)

            request = ToolApprovalRequest(
                request_id=_create_request_id(),
                tool_name=tool_name,
                summary=summary or tool_name,
                arguments=arguments,
                created_at=time.time(),
            )
            self._pending = request
            return False, _format_request_message(request)

    def register_user_decision(
        self, message_text: str
    ) -> Optional[ToolApprovalDecision]:
        """Register a user approval or denial message."""
        normalized = (message_text or "").strip().lower()
        if not normalized:
            return None

        tokens = normalized.split()
        if not tokens or tokens[0] not in ("approve", "deny"):
            return None

        request_id = tokens[1] if len(tokens) > 1 else None

        with self._lock:
            if not self._pending:
                return None
            if request_id and request_id != self._pending.request_id:
                return None

            decision = ToolApprovalDecision(
                action=tokens[0], request_id=self._pending.request_id
            )

            if tokens[0] == "approve":
                self._approved_id = self._pending.request_id
                return decision

            self._pending = None
            self._approved_id = None
            return decision


_APPROVAL_MANAGER = ToolApprovalManager()


def require_tool_approval(
    tool_name: str, summary: str, arguments: Dict[str, Any]
) -> Tuple[bool, str]:
    """Request approval for a tool and return whether it is approved."""
    return _APPROVAL_MANAGER.ensure_approval(tool_name, summary, arguments)


def register_tool_approval(message_text: str) -> Optional[ToolApprovalDecision]:
    """Register user approval/denial text from a chat message."""
    return _APPROVAL_MANAGER.register_user_decision(message_text)


def summarize_text(action: str, text: str, limit: int = 160) -> str:
    """Build a short, readable summary for tool approvals."""
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) > limit:
        cleaned = f"{cleaned[: max(0, limit - 3)]}..."
    return f"{action}: {cleaned}" if cleaned else action


def _create_request_id() -> str:
    return uuid.uuid4().hex[:8]


def _format_request_message(request: ToolApprovalRequest) -> str:
    args_text = _format_arguments(request.arguments)
    return (
        "Approval required before using a tool.\n"
        f"Tool: {request.tool_name}\n"
        f"Summary: {request.summary}\n"
        f"Args: {args_text}\n"
        f"Reply with: approve {request.request_id} or deny {request.request_id}"
    )


def _format_arguments(arguments: Dict[str, Any]) -> str:
    try:
        rendered = json.dumps(arguments, ensure_ascii=True)
    except TypeError:
        rendered = str(arguments)

    max_len = 240
    if len(rendered) > max_len:
        rendered = f"{rendered[: max_len - 3]}..."
    return rendered
