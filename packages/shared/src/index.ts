// Shared types mirroring apps/api/app/schemas/*.py. Keep these in sync by hand for now --
// see docs/setup.md for the plan to generate this from the OpenAPI schema later.

export type UserRole = "end_user" | "technician" | "admin";

export type TicketCategory =
  | "printer_issue"
  | "network_issue"
  | "email_issue"
  | "m365_issue"
  | "onedrive_issue"
  | "teams_issue"
  | "slow_computer"
  | "login_issue"
  | "software_issue"
  | "hardware_issue"
  | "other";

export type TicketPriority = "low" | "normal" | "high" | "critical";

export type TicketStatus =
  | "new"
  | "awaiting_diagnostics"
  | "ai_triaged"
  | "waiting_for_technician"
  | "in_progress"
  | "waiting_for_user"
  | "resolved"
  | "closed";

export type DiagnosticPack =
  | "device_health_basic"
  | "network_basic"
  | "printer_basic"
  | "onedrive_basic"
  | "outlook_basic";

export type DiagnosticRunStatus = "pending" | "running" | "completed" | "failed";

export type Severity = "ok" | "info" | "warning" | "critical";

export type RiskLevel = "low" | "medium" | "high";

export type ApprovalStatus = "not_required" | "pending" | "approved" | "rejected";

export type ActionRunStatus = "blocked" | "approved" | "running" | "completed" | "failed" | "rejected";

export interface Client {
  id: string;
  name: string;
  contact_email: string | null;
  is_active: boolean;
  is_internal: boolean;
  created_at: string;
  updated_at: string;
}

export interface User {
  id: string;
  client_id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Device {
  id: string;
  client_id: string;
  owner_user_id: string | null;
  device_name: string;
  hostname: string | null;
  os_version: string | null;
  last_seen_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  client_id: string;
  requester_id: string;
  assigned_to_id: string | null;
  device_id: string | null;
  title: string;
  description: string;
  category: TicketCategory;
  priority: TicketPriority;
  status: TicketStatus;
  ai_summary: string | null;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
}

export interface TicketMessage {
  id: string;
  ticket_id: string;
  author_user_id: string;
  body: string;
  is_internal: boolean;
  created_at: string;
}

export interface TicketAttachment {
  id: string;
  ticket_id: string;
  uploaded_by_user_id: string;
  original_file_name: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface DiagnosticResult {
  id: string;
  diagnostic_run_id: string;
  result_json: Record<string, unknown>;
  severity: Severity;
  created_at: string;
}

export interface DiagnosticRun {
  id: string;
  client_id: string;
  ticket_id: string | null;
  device_id: string;
  diagnostic_pack: DiagnosticPack;
  status: DiagnosticRunStatus;
  started_at: string | null;
  completed_at: string | null;
  created_by_user_id: string;
  results: DiagnosticResult[];
}

export interface RecommendedAction {
  action: string;
  requires_approval: boolean;
  reason: string;
}

export interface AITriageResult {
  id: string;
  ticket_id: string;
  summary: string;
  likely_cause: string;
  confidence: number;
  risk_level: RiskLevel;
  recommended_actions_json: RecommendedAction[];
  technician_notes: string | null;
  user_reply_draft: string | null;
  escalate: boolean;
  created_at: string;
}

export interface ApprovedAction {
  id: string;
  name: string;
  description: string;
  risk_level: RiskLevel;
  requires_approval: boolean;
  enabled: boolean;
}

export interface ActionRun {
  id: string;
  ticket_id: string;
  device_id: string;
  action_name: string;
  requested_by_user_id: string;
  approved_by_user_id: string | null;
  approval_status: ApprovalStatus;
  status: ActionRunStatus;
  ai_suggested: boolean;
  input_json: Record<string, unknown>;
  output_json: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface KnowledgeArticle {
  id: string;
  client_id: string | null;
  title: string;
  body: string;
  category: TicketCategory | null;
  created_by_user_id: string;
  created_at: string;
  updated_at: string;
}

export interface AuditLog {
  id: string;
  client_id: string | null;
  actor_user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string | null;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export const TICKET_CATEGORIES: { value: TicketCategory; label: string }[] = [
  { value: "printer_issue", label: "Printer issue" },
  { value: "network_issue", label: "Internet/network issue" },
  { value: "email_issue", label: "Email/Outlook issue" },
  { value: "m365_issue", label: "Microsoft 365 issue" },
  { value: "onedrive_issue", label: "OneDrive issue" },
  { value: "teams_issue", label: "Teams issue" },
  { value: "slow_computer", label: "Slow computer" },
  { value: "login_issue", label: "Login/password issue" },
  { value: "software_issue", label: "Software issue" },
  { value: "hardware_issue", label: "Hardware issue" },
  { value: "other", label: "Other" },
];

export const TICKET_PRIORITIES: { value: TicketPriority; label: string }[] = [
  { value: "low", label: "Low" },
  { value: "normal", label: "Normal" },
  { value: "high", label: "High" },
  { value: "critical", label: "Critical" },
];

export const TICKET_STATUS_LABELS: Record<TicketStatus, string> = {
  new: "New",
  awaiting_diagnostics: "Awaiting diagnostics",
  ai_triaged: "AI triaged",
  waiting_for_technician: "Waiting for technician",
  in_progress: "In progress",
  waiting_for_user: "Waiting for user",
  resolved: "Resolved",
  closed: "Closed",
};

export const DIAGNOSTIC_PACK_LABELS: Record<DiagnosticPack, string> = {
  device_health_basic: "Device Health Basic",
  network_basic: "Network Basic",
  printer_basic: "Printer Basic",
  onedrive_basic: "OneDrive Basic",
  outlook_basic: "Outlook Basic",
};

export const DIAGNOSTICS_PRIVACY_NOTICE =
  "NovaSoft Support will collect basic technical information from your device to help " +
  "diagnose this issue. This may include your device name, OS username, Windows version, network status, " +
  "printer status, disk space, running support-related services, and recent relevant error " +
  "logs. NovaSoft Support will not collect your personal files, browser history, passwords, " +
  "or private document contents.";
