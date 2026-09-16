import type { RiskLevel, TicketPriority, TicketStatus } from "@novasoft/shared";
import { TICKET_STATUS_LABELS } from "@novasoft/shared";

const STATUS_STYLES: Record<TicketStatus, string> = {
  new: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  awaiting_diagnostics: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  ai_triaged: "bg-violet-500/15 text-violet-400 border-violet-500/30",
  waiting_for_technician: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  in_progress: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  waiting_for_user: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  resolved: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  closed: "bg-nova-border/40 text-nova-muted border-nova-border",
};

export function StatusBadge({ status }: { status: TicketStatus }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLES[status]}`}>
      {TICKET_STATUS_LABELS[status]}
    </span>
  );
}

const PRIORITY_STYLES: Record<TicketPriority, string> = {
  low: "bg-nova-border/40 text-nova-muted border-nova-border",
  normal: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  high: "bg-orange-500/15 text-orange-400 border-orange-500/30",
  critical: "bg-red-500/15 text-red-400 border-red-500/30",
}

export function PriorityBadge({ priority }: { priority: TicketPriority }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${PRIORITY_STYLES[priority]}`}>
      {priority}
    </span>
  );
}

const RISK_STYLES: Record<RiskLevel, string> = {
  low: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30",
  medium: "bg-amber-500/15 text-amber-400 border-amber-500/30",
  high: "bg-red-500/15 text-red-400 border-red-500/30",
};

export function RiskBadge({ risk }: { risk: RiskLevel }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${RISK_STYLES[risk]}`}>
      {risk} risk
    </span>
  );
}
