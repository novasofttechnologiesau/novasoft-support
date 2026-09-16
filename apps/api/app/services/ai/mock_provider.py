from app.schemas.ai_triage import AITriageResponse, RecommendedAction
from app.services.ai.base import AIProvider
from app.services.ai.context import TriageContext


class MockAIProvider(AIProvider):
    """Deterministic, offline stand-in for a real LLM. Used automatically whenever no AI
    provider is configured (or a real provider call fails), so the product works end-to-end
    with zero external dependencies."""

    async def generate_triage(self, context: TriageContext) -> AITriageResponse:
        if not context.diagnostic_results:
            return AITriageResponse(
                summary=f"User reported: {context.ticket_title}.",
                likely_cause="Not enough information yet -- no diagnostics have been run.",
                confidence=0.2,
                risk_level="low",
                recommended_actions=[],
                technician_notes="Ask the user to run the relevant diagnostic pack before triage.",
                user_reply_draft=(
                    "Thanks for the report. Could you run a quick diagnostic check from the "
                    "NovaSoft Support app so we can pinpoint the cause?"
                ),
                escalate=False,
                missing_information=["diagnostic_results"],
            )

        if context.ticket_category == "printer_issue":
            spooler_result = next(
                (
                    d
                    for d in context.diagnostic_results
                    if d.get("results", {}).get("spooler_status") == "Stopped"
                ),
                None,
            )
            if spooler_result:
                return AITriageResponse(
                    summary=f"{context.requester_name} cannot print from {context.device_name or 'their device'}.",
                    likely_cause="Print Spooler service is stopped.",
                    confidence=0.91,
                    risk_level="low",
                    recommended_actions=[
                        RecommendedAction(
                            action="restart_print_spooler",
                            requires_approval=False,
                            reason="Spooler is stopped; restarting it is a low-risk, reversible fix.",
                        )
                    ],
                    technician_notes="Printer diagnostics show the spooler service stopped. Issue appears local to the workstation.",
                    user_reply_draft=(
                        "It looks like your computer's print service has stopped. I'm going to "
                        "restart the print service and check if printing resumes."
                    ),
                    escalate=False,
                )
            return AITriageResponse(
                summary=f"{context.requester_name} is reporting a printer issue.",
                likely_cause="Printer diagnostics did not show a stopped spooler; cause is unclear from available data.",
                confidence=0.4,
                risk_level="low",
                recommended_actions=[
                    RecommendedAction(
                        action="collect_printer_diagnostics",
                        requires_approval=False,
                        reason="Need a fresh printer diagnostic pack to narrow down the cause.",
                    )
                ],
                technician_notes="Consider checking printer connectivity and queue manually.",
                user_reply_draft="We're looking into your printer issue and may ask you to run one more check.",
                escalate=False,
            )

        if context.ticket_category == "network_issue":
            return AITriageResponse(
                summary=f"{context.requester_name} is reporting a network/internet issue.",
                likely_cause="Network diagnostics indicate connectivity or DNS resolution problems.",
                confidence=0.6,
                risk_level="low",
                recommended_actions=[
                    RecommendedAction(
                        action="flush_dns",
                        requires_approval=False,
                        reason="A DNS flush is a safe first step for resolution-related network issues.",
                    )
                ],
                technician_notes="Review the network_basic diagnostic pack for gateway/DNS reachability details.",
                user_reply_draft="We're going to refresh your network settings and check if that resolves the issue.",
                escalate=False,
            )

        if context.ticket_category == "onedrive_issue":
            return AITriageResponse(
                summary=f"{context.requester_name} is reporting a OneDrive sync issue.",
                likely_cause="OneDrive process may not be running or is stuck syncing.",
                confidence=0.55,
                risk_level="low",
                recommended_actions=[
                    RecommendedAction(
                        action="restart_onedrive",
                        requires_approval=False,
                        reason="Restarting OneDrive is a safe, reversible first step for sync issues.",
                    )
                ],
                technician_notes="Confirm OneDrive diagnostics before and after the restart.",
                user_reply_draft="We're restarting your OneDrive sync client to see if that clears the issue.",
                escalate=False,
            )

        return AITriageResponse(
            summary=f"{context.requester_name} reported: {context.ticket_title}.",
            likely_cause="Cause is not yet clear from the available diagnostics for this category.",
            confidence=0.3,
            risk_level="medium",
            recommended_actions=[],
            technician_notes="No automated recommendation available for this category; manual review needed.",
            user_reply_draft="Thanks for letting us know -- a technician will review your ticket shortly.",
            escalate=True,
        )
