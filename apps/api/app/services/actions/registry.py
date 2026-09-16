"""The complete allowlist of actions the AI or a user/technician may ever trigger.

This is the single source of truth for action safety. Nothing outside this module may
execute a system-level action. Actions are either:
  - executed_by="device": the Tauri desktop app runs a hardcoded local command and reports
    the result back (restart_print_spooler, flush_dns, restart_onedrive, the collect_* packs)
  - executed_by="server": the backend itself performs the (non-system) action, e.g. escalating
    a ticket is just a state change + audit log entry, no device access needed.

`implemented=False` entries exist so the approval framework, UI, and audit trail are fully
designed end-to-end, but they have no working handler yet -- attempting to run one returns a
"not implemented" error rather than silently no-op'ing.
"""

from dataclasses import dataclass

from app.models.enums import RiskLevel, UserRole


@dataclass(frozen=True)
class ActionDefinition:
    name: str
    description: str
    risk_level: RiskLevel
    requires_approval: bool
    allowed_roles: tuple[UserRole, ...]
    executed_by: str  # "device" | "server"
    implemented: bool


ACTION_REGISTRY: dict[str, ActionDefinition] = {
    # --- Initial low-risk approved actions (Phase 4) ---
    "restart_print_spooler": ActionDefinition(
        name="restart_print_spooler",
        description="Stops and restarts the Windows Print Spooler service.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "flush_dns": ActionDefinition(
        name="flush_dns",
        description="Clears the local DNS resolver cache.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "restart_onedrive": ActionDefinition(
        name="restart_onedrive",
        description="Restarts the OneDrive sync client process.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "collect_network_diagnostics": ActionDefinition(
        name="collect_network_diagnostics",
        description="Runs the Network Basic read-only diagnostic pack.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "collect_printer_diagnostics": ActionDefinition(
        name="collect_printer_diagnostics",
        description="Runs the Printer Basic read-only diagnostic pack.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "collect_device_health": ActionDefinition(
        name="collect_device_health",
        description="Runs the Device Health Basic read-only diagnostic pack.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "escalate_ticket": ActionDefinition(
        name="escalate_ticket",
        description="Flags a ticket as needing human technician attention.",
        risk_level=RiskLevel.low,
        requires_approval=False,
        allowed_roles=(UserRole.end_user, UserRole.technician, UserRole.admin),
        executed_by="server",
        implemented=True,
    ),
    # --- Actions that require technician approval (system design only for MVP) ---
    "clear_print_queue": ActionDefinition(
        name="clear_print_queue",
        description="Clears all pending jobs from a printer's queue.",
        risk_level=RiskLevel.medium,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "restart_computer": ActionDefinition(
        name="restart_computer",
        description="Restarts the user's computer.",
        risk_level=RiskLevel.high,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "reset_network_adapter": ActionDefinition(
        name="reset_network_adapter",
        description="Disables and re-enables the active network adapter.",
        risk_level=RiskLevel.medium,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "reinstall_printer": ActionDefinition(
        name="reinstall_printer",
        description="Removes and reinstalls a printer driver/queue.",
        risk_level=RiskLevel.medium,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "kill_process": ActionDefinition(
        name="kill_process",
        description="Terminates a specific, named, non-system process.",
        risk_level=RiskLevel.medium,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
    "change_default_printer": ActionDefinition(
        name="change_default_printer",
        description="Changes the user's default printer.",
        risk_level=RiskLevel.medium,
        requires_approval=True,
        allowed_roles=(UserRole.technician, UserRole.admin),
        executed_by="device",
        implemented=False,
    ),
}

# Never automated in the MVP, and never added to ACTION_REGISTRY under any circumstance:
# delete user files, modify registry, change permissions, change passwords, disable security
# tools, change firewall rules, run arbitrary PowerShell, remote shell access, remote desktop
# control, export sensitive files, modify BitLocker/security settings.


def get_action(name: str) -> ActionDefinition | None:
    return ACTION_REGISTRY.get(name)
