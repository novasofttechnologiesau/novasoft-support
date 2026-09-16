# Diagnostic scope in v0.1.0

Five read-only packs are available in the native shell after UI consent. Browser previews
return simulated data. Network checks contact the configured gateway, ping 1.1.1.1 and resolve
microsoft.com, so a network diagnostic is not entirely offline. The operating-system username
and local network details are diagnostic data; do not publish real reports in issues.

The field descriptions below describe the implementation. Windows-specific behavior remains
unverified on real Windows hardware for this release. Native repairs are excluded.

# Diagnostic Packs

All packs are read-only and return structured JSON in this shape:

```json
{
  "diagnostic_pack": "printer_basic",
  "device_name": "RECEPTION-PC-01",
  "timestamp": "2026-07-03T10:30:00+10:00",
  "results": { "...": "pack-specific fields" },
  "severity": "ok | info | warning | critical"
}
```

Each pack is implemented as a single hardcoded `#[tauri::command]` in
`apps/desktop/src-tauri/src/commands/diagnostics.rs`. None of them accept parameters from the
caller. Fields that aren't implemented yet are always `null`/empty (never fabricated) --
`device_health_basic` additionally lists them explicitly in `unavailable_fields` so the AI
layer and technicians know to ask for more information rather than assume a false negative.

## Device Health Basic (`device_health_basic`)

| Field | Real on all OSes? | Notes |
|---|---|---|
| `computer_name` | Yes | via `sysinfo` |
| `current_username` | Yes | `$USERNAME`/`$USER` |
| `windows_version` | Windows only | `cmd /C ver`; non-Windows reports "not applicable" |
| `uptime_seconds` | Yes | via `sysinfo` |
| `cpu_usage_percent` | Yes | via `sysinfo` |
| `ram_usage_percent` | Yes | via `sysinfo` |
| `disk_usage_percent` | Yes | aggregated across all mounted disks |
| `last_boot_time` | Yes | via `sysinfo` |
| `battery_status` | Not implemented | requires a platform battery API; always `null` |
| `pending_reboot` | Not implemented | requires a Windows registry check; always `null` |
| `antivirus_status` | Not implemented | requires a WMI Security Center query; always `null` |

## Network Basic (`network_basic`)

| Field | Real on all OSes? | Notes |
|---|---|---|
| `active_adapter`, `ip_address`, `gateway` | Yes | via the `default-net` crate |
| `dns_servers` | Unix real / Windows TODO | parsed from `/etc/resolv.conf`; Windows parsing of `ipconfig /all` not implemented yet |
| `can_ping_gateway`, `can_reach_internet` | Yes | a single fixed-count `ping` to the gateway and to `1.1.1.1` |
| `can_resolve_dns` | Yes | resolves a fixed hostname via the OS resolver |
| `vpn_adapter_detected` | Yes | heuristic: any interface name containing tun/tap/ppp/wg/vpn |
| `wifi_signal_strength` | Not implemented | needs a platform-specific Wi-Fi API; always `null` |
| `recent_network_errors` | Not implemented | needs a Windows Event Log query; always `null` |

## Printer Basic (`printer_basic`)

| Field | Real on all OSes? | Notes |
|---|---|---|
| `spooler_status` | Windows only | `sc query Spooler`; non-Windows reports "not applicable" |
| `default_printer` | Windows only | fixed PowerShell `Get-CimInstance Win32_Printer` query |
| `installed_printers` | Not implemented | requires Win32 print spooler enumeration APIs; always `[]` |
| `queue_count` | Not implemented | requires enumerating print jobs; always `null` |
| `recent_print_errors` | Not implemented | needs a Windows Event Log query; always `null` |
| `printer_online`, `printer_ip_reachable` | Not implemented | needs a printer IP, which isn't collected yet; always `null` |

## OneDrive Basic (`onedrive_basic`)

| Field | Real on all OSes? | Notes |
|---|---|---|
| `process_running` | Yes | process-list scan for a name containing "onedrive" |
| `sync_folder_detected` | Yes | checks for `~/OneDrive` (or `%USERPROFILE%\OneDrive`) |
| `sync_status`, `recent_errors` | Not implemented | needs OneDrive's own status API/registry; always `null` |

## Outlook Basic (`outlook_basic`)

| Field | Real on all OSes? | Notes |
|---|---|---|
| `running` | Yes | process-list scan for a name containing "outlook" |
| `installed` | Not implemented | needs a registry/installed-app check; always `null` |
| `recent_crash_events` | Not implemented | needs a Windows Event Log query; always `null` |
| `profile_detected`, `ost_pst_size_mb` | Not implemented | needs the Outlook profile registry key; always `null` |

## What diagnostics never collect

Personal documents, browser history, passwords, authentication tokens, email contents, full
file listings, private message contents. See `security.md` for the privacy notice shown to
the user before any pack runs.

## Verifying on real Windows

This project was developed on macOS. Cross-platform fields above (marked "Yes") were
compiled and exercised for real on macOS via `cargo check` and `tauri dev`. The
Windows-specific branches (`sc query`, `net stop/start spooler`, `ipconfig /flushdns`, the
PowerShell printer query) compile (they're plain `std::process::Command` calls with fixed
strings) but have **not** been run against a real Windows Print Spooler/service host yet --
verify these on an actual Windows machine before relying on them in front of a real user.
