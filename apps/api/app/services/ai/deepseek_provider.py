import json

from openai import AsyncOpenAI

from app.schemas.ai_triage import AITriageResponse
from app.services.ai.base import AI_SYSTEM_PROMPT, AIProvider, redact_secrets
from app.services.ai.context import TriageContext

DEEPSEEK_BASE_URL = "https://api.deepseek.com"


def _build_user_prompt(context: TriageContext) -> str:
    payload = {
        "ticket": {
            "title": context.ticket_title,
            "description": redact_secrets(context.ticket_description),
            "category": context.ticket_category,
            "priority": context.ticket_priority,
        },
        "requester_name": "The requester",
        "device_name": "Registered device" if context.device_name else None,
        "diagnostic_results": context.diagnostic_results,
        "related_previous_tickets": context.related_tickets,
        "knowledge_base_articles": context.knowledge_articles,
        "approved_actions_allowlist": context.approved_actions,
    }
    def redact(value):
        if isinstance(value, str):
            return redact_secrets(value)
        if isinstance(value, dict):
            return {redact_secrets(str(k)): ("[REDACTED]" if any(term in str(k).lower() for term in ("password", "secret", "token", "api_key", "username", "ip_address", "gateway", "dns_servers")) else redact(v)) for k, v in value.items()}
        if isinstance(value, list):
            return [redact(v) for v in value]
        return value
    payload = redact(payload)
    return (
        "Analyse the following support ticket and return ONLY a JSON object with keys: "
        "summary, likely_cause, confidence (0-1), risk_level (low|medium|high), "
        "recommended_actions (list of {action, requires_approval, reason} where `action` "
        "MUST be one of the names in approved_actions_allowlist), technician_notes, "
        "user_reply_draft, escalate (bool), missing_information (list of strings).\n\n"
        f"DATA:\n{json.dumps(payload, default=str)}"
    )


class DeepSeekAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)
        self._model = model

    async def generate_triage(self, context: TriageContext) -> AITriageResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": AI_SYSTEM_PROMPT},
                {"role": "user", "content": _build_user_prompt(context)},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        raw = response.choices[0].message.content or "{}"
        data = json.loads(raw)
        return AITriageResponse.model_validate(data)
