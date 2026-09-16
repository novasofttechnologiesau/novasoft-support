from dataclasses import dataclass, field
from typing import Any


@dataclass
class TriageContext:
    """Everything the AI is allowed to see for one triage pass. Built by the API layer
    from trusted DB rows only -- never includes raw file contents or credentials."""

    ticket_title: str
    ticket_description: str
    ticket_category: str
    ticket_priority: str
    device_name: str | None
    requester_name: str
    diagnostic_results: list[dict[str, Any]] = field(default_factory=list)
    related_tickets: list[dict[str, Any]] = field(default_factory=list)
    knowledge_articles: list[dict[str, Any]] = field(default_factory=list)
    approved_actions: list[dict[str, Any]] = field(default_factory=list)
