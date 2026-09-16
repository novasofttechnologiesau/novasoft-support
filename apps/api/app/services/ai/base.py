import re
from abc import ABC, abstractmethod

from app.schemas.ai_triage import AITriageResponse
from app.services.ai.context import TriageContext

# Verbatim safety system prompt -- do not edit ad hoc. Any change here is a security-relevant
# change and must be reviewed like one.
AI_SYSTEM_PROMPT = """You are NovaSoft Support AI, an IT support triage assistant. Your job is to \
analyse support tickets and diagnostic results. You may summarise issues, identify likely causes, \
recommend safe next steps, draft user replies, and suggest approved actions.

You must not request or execute arbitrary commands.

You must not suggest deleting files, changing passwords, modifying security settings, disabling \
antivirus, editing the registry, changing firewall rules, or accessing private files unless a \
human technician explicitly approves and the action exists in the approved action allowlist.

You must only recommend actions from the approved action list provided to you.

If the diagnostic information is insufficient, say what extra information is needed.

If confidence is low, recommend escalation to a human technician.

Return structured JSON only."""

_SECRET_PATTERNS = [
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+)"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*\S+"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._-]+"),
]


def redact_secrets(text: str) -> str:
    """Best-effort redaction of secret-shaped substrings before anything is sent to an AI
    provider. Diagnostic packs should never collect secrets in the first place -- this is a
    defence-in-depth backstop, not the primary control."""
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


class AIProvider(ABC):
    """Every provider (mock, DeepSeek, future providers) implements this single method.
    Providers never touch the database directly -- the caller builds a TriageContext from
    trusted rows and the provider returns a structured, schema-validated response."""

    @abstractmethod
    async def generate_triage(self, context: TriageContext) -> AITriageResponse: ...
