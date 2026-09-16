import enum


class UserRole(str, enum.Enum):
    end_user = "end_user"
    technician = "technician"
    admin = "admin"


class TicketCategory(str, enum.Enum):
    printer_issue = "printer_issue"
    network_issue = "network_issue"
    email_issue = "email_issue"
    m365_issue = "m365_issue"
    onedrive_issue = "onedrive_issue"
    teams_issue = "teams_issue"
    slow_computer = "slow_computer"
    login_issue = "login_issue"
    software_issue = "software_issue"
    hardware_issue = "hardware_issue"
    other = "other"


class TicketPriority(str, enum.Enum):
    low = "low"
    normal = "normal"
    high = "high"
    critical = "critical"


class TicketStatus(str, enum.Enum):
    new = "new"
    awaiting_diagnostics = "awaiting_diagnostics"
    ai_triaged = "ai_triaged"
    waiting_for_technician = "waiting_for_technician"
    in_progress = "in_progress"
    waiting_for_user = "waiting_for_user"
    resolved = "resolved"
    closed = "closed"


class DiagnosticPack(str, enum.Enum):
    device_health_basic = "device_health_basic"
    network_basic = "network_basic"
    printer_basic = "printer_basic"
    onedrive_basic = "onedrive_basic"
    outlook_basic = "outlook_basic"


class DiagnosticRunStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Severity(str, enum.Enum):
    ok = "ok"
    info = "info"
    warning = "warning"
    critical = "critical"


class RiskLevel(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ApprovalStatus(str, enum.Enum):
    not_required = "not_required"
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class ActionRunStatus(str, enum.Enum):
    blocked = "blocked"
    approved = "approved"
    running = "running"
    completed = "completed"
    failed = "failed"
    rejected = "rejected"
