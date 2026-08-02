"""
Structured data response models for godot-cli-connect operations.

Canonical agent-facing shape is a **flat dict**:
  {"status": "success"|"error"|..., "message"?: str, "errors"?: list, ...payload}

`OperationResult` is the typed constructor; call ``to_flat_dict()`` (or use
``ok()`` / ``err()``) before returning from operations or printing JSON.
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from dataclasses import asdict, dataclass, field
from typing import Any, Union

ResultDict = dict[str, Any]
ResultLike = Union["OperationResult", Mapping[str, Any]]

SUCCESS_STATUSES = frozenset({"success"})


@dataclass
class OperationResult:
    """Standard operation response container."""

    status: str  # "success", "error", "failure", "syntax_errors_found", ...
    message: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Nested dict form (status/message/data/errors). Prefer ``to_flat_dict`` for CLI/JSON."""
        d = asdict(self)
        if not self.errors:
            d.pop("errors", None)
        if not self.data:
            d.pop("data", None)
        if not self.message:
            d.pop("message", None)
        return d

    def to_flat_dict(self) -> ResultDict:
        """
        Agent-friendly flat payload: status + message/errors + data keys at top level.
        Matches the historical dict return convention used across operations.
        """
        out: ResultDict = {"status": self.status}
        if self.message:
            out["message"] = self.message
        if self.errors:
            out["errors"] = list(self.errors)
        out.update(self.data)
        return out


def ok(message: str = "", **data: Any) -> ResultDict:
    """Build a successful flat result dict."""
    return OperationResult(status="success", message=message, data=dict(data)).to_flat_dict()


def err(
    message: str,
    *,
    status: str = "error",
    errors: list[str] | None = None,
    **data: Any,
) -> ResultDict:
    """Build a failed flat result dict."""
    return OperationResult(
        status=status,
        message=message,
        data=dict(data),
        errors=list(errors or []),
    ).to_flat_dict()


def as_result_dict(result: ResultLike) -> ResultDict:
    """Normalize OperationResult or mapping to a flat dict."""
    if isinstance(result, OperationResult):
        return result.to_flat_dict()
    if isinstance(result, MutableMapping):
        return dict(result)
    return dict(result)


def is_success(result: ResultLike) -> bool:
    """True when status is a success status."""
    if isinstance(result, OperationResult):
        return result.status in SUCCESS_STATUSES
    return str(result.get("status", "")) in SUCCESS_STATUSES
