import logging
import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approved_action import ApprovedAction
from app.models.device import Device
from app.models.diagnostic import DiagnosticResult, DiagnosticRun
from app.models.knowledge_article import KnowledgeArticle
from app.models.ticket import Ticket
from app.models.user import User
from app.schemas.ai_triage import AITriageResponse
from app.services.ai.context import TriageContext
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock_provider import MockAIProvider

logger = logging.getLogger(__name__)


async def _build_context(db: AsyncSession, ticket: Ticket) -> TriageContext:
    requester = await db.get(User, ticket.requester_id)
    device = await db.get(Device, ticket.device_id) if ticket.device_id else None

    diag_result = await db.execute(
        select(DiagnosticResult, DiagnosticRun)
        .join(DiagnosticRun, DiagnosticResult.diagnostic_run_id == DiagnosticRun.id)
        .where(DiagnosticRun.ticket_id == ticket.id)
        .order_by(DiagnosticResult.created_at.desc())
    )
    diagnostic_results = [
        {
            "diagnostic_pack": run.diagnostic_pack.value,
            "severity": result.severity.value,
            "results": result.result_json,
        }
        for result, run in diag_result.all()
    ]

    related_result = await db.execute(
        select(Ticket)
        .where(
            Ticket.requester_id == ticket.requester_id,
            Ticket.id != ticket.id,
            Ticket.category == ticket.category,
        )
        .order_by(Ticket.created_at.desc())
        .limit(5)
    )
    related_tickets = [
        {"title": t.title, "status": t.status.value, "ai_summary": t.ai_summary}
        for t in related_result.scalars().all()
    ]

    kb_result = await db.execute(
        select(KnowledgeArticle).where(
            KnowledgeArticle.category == ticket.category,
            or_(KnowledgeArticle.client_id.is_(None), KnowledgeArticle.client_id == ticket.client_id),
        ).limit(5)
    )
    knowledge_articles = [
        {"title": a.title, "body": a.body} for a in kb_result.scalars().all()
    ]

    actions_result = await db.execute(select(ApprovedAction).where(ApprovedAction.enabled.is_(True)))
    approved_actions = [
        {
            "name": a.name,
            "risk_level": a.risk_level.value,
            "requires_approval": a.requires_approval,
        }
        for a in actions_result.scalars().all()
    ]

    return TriageContext(
        ticket_title=ticket.title,
        ticket_description=ticket.description,
        ticket_category=ticket.category.value,
        ticket_priority=ticket.priority.value,
        device_name=device.device_name if device else None,
        requester_name=requester.full_name if requester else "The user",
        diagnostic_results=diagnostic_results,
        related_tickets=related_tickets,
        knowledge_articles=knowledge_articles,
        approved_actions=approved_actions,
    )


class AITriageService:
    """Orchestration layer the API routes call. Matches the spec's interface:
    triage_ticket / summarize_ticket / suggest_actions / draft_user_reply -- all operating
    on a ticket_id, all backed by the same underlying triage generation."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._provider = get_ai_provider()

    async def _generate(self, ticket_id: uuid.UUID) -> AITriageResponse:
        ticket = await self._db.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"Ticket {ticket_id} not found")
        context = await _build_context(self._db, ticket)
        try:
            return await self._provider.generate_triage(context)
        except Exception:
            logger.warning("AI provider failed; using mock triage (exception details withheld)")
            return await MockAIProvider().generate_triage(context)

    async def triage_ticket(self, ticket_id: uuid.UUID) -> AITriageResponse:
        return await self._generate(ticket_id)

    async def summarize_ticket(self, ticket_id: uuid.UUID) -> str:
        result = await self._generate(ticket_id)
        return result.summary

    async def suggest_actions(self, ticket_id: uuid.UUID) -> list:
        result = await self._generate(ticket_id)
        return result.recommended_actions

    async def draft_user_reply(self, ticket_id: uuid.UUID) -> str | None:
        result = await self._generate(ticket_id)
        return result.user_reply_draft
