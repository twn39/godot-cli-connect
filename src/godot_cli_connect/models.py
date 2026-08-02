"""
Structured data response models for godot-cli-connect operations
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List


@dataclass
class OperationResult:
    """Standard operation response container."""

    status: str  # "success", "error", "failure", "syntax_errors_found"
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Converts result container into a clean dictionary."""
        d = asdict(self)
        if not self.errors:
            d.pop("errors", None)
        if not self.data:
            d.pop("data", None)
        if not self.message:
            d.pop("message", None)
        return d
