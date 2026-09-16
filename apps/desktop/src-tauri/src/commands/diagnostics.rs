//! Read-only diagnostic packs. Every command here is hardcoded and parameterless -- there is
//! no generic "run a diagnostic" command, and nothing here accepts a caller-supplied command
//! string. See docs/diagnostics.md for exactly what each pack collects (and does not collect).

use serde::Serialize;
use std::net::ToSocketAddrs;
use std::time::Duration;
use sysinfo::{Disks, System};

use crate::sysutil::run_fixed_command;
use crate::types::{device_name, now_iso, DiagnosticReport};

// ---------------------------------------------------------------------------
// Device Health Basic
// ---------------------------------------------------------------------------

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct DeviceHealthResults {
    computer_name: String,
    current_username: String,
    windows_version: String,
    uptime_seconds: u64,
    cpu_usage_percent: f32,
    ram_usage_percent: f32,
    disk_usage_percent: Option<f32>,
    battery_status: Option<String>,
    pending_reboot: Option<bool>,
    antivirus_status: Option<String>,
    last_boot_time: String,
    unavailable_fields: Vec<String>,
}

fn current_username() -> String {
    std::env::var("USERNAME")
        .or_else(|_| std::env::var("USER"))
        .unwrap_or_else(|_| "unknown".to_string())
}

fn windows_version_string() -> String {
    if cfg!(target_os = "windows") {
        run_fixed_command("cmd", &["/C", "ver"])
            .map(|s| s.trim().to_string())
            .unwrap_or_else(|e| format!("Unknown (could not read version: {e})"))
    } else {
        format!("Not applicable -- running a {} development build", std::env::consts::OS)
    }
}

#[tauri::command]
pub fn get_device_health() -> DiagnosticReport<DeviceHealthResults> {
    let mut sys = System::new_all();
    sys.refresh_cpu_usage();
    std::thread::sleep(Duration::from_millis(200));
    sys.refresh_cpu_usage();
    sys.refresh_memory();

    let ram_usage_percent = if sys.total_memory() > 0 {
        (sys.used_memory() as f32 / sys.total_memory() as f32) * 100.0
    } else {
        0.0
    };

    let disks = Disks::new_with_refreshed_list();
    let (total_space, available_space) = disks
        .iter()
        .fold((0u64, 0u64), |(t, a), d| (t + d.total_space(), a + d.available_space()));
    let disk_usage_percent = if total_space > 0 {
        Some(((total_space - available_space) as f32 / total_space as f32) * 100.0)
    } else {
        None
    };

    let boot_time = System::boot_time();
    let last_boot_time = chrono::DateTime::from_timestamp(boot_time as i64, 0)
        .map(|dt| dt.to_rfc3339())
        .unwrap_or_else(|| "Unknown".to_string());

    let mut unavailable = vec![];
    unavailable.push("battery_status (not implemented in this MVP build)".to_string());
    unavailable.push("pending_reboot (not implemented in this MVP build)".to_string());
    unavailable.push("antivirus_status (not implemented in this MVP build)".to_string());

    let results = DeviceHealthResults {
        computer_name: device_name(),
        current_username: current_username(),
        windows_version: windows_version_string(),
        uptime_seconds: System::uptime(),
        cpu_usage_percent: sys.global_cpu_usage(),
        ram_usage_percent,
        disk_usage_percent,
        battery_status: None,
        pending_reboot: None,
        antivirus_status: None,
        last_boot_time,
        unavailable_fields: unavailable,
    };

    let severity = if disk_usage_percent.unwrap_or(0.0) > 90.0 || ram_usage_percent > 90.0 {
        "warning"
    } else {
        "ok"
    };

    DiagnosticReport {
        diagnostic_pack: "device_health_basic",
        device_name: device_name(),
        timestamp: now_iso(),
        results,
        severity,
    }
}

// ---------------------------------------------------------------------------
// Network Basic
// ---------------------------------------------------------------------------

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct NetworkResults {
    active_adapter: Option<String>,
    ip_address: Option<String>,
    gateway: Option<String>,
    dns_servers: Vec<String>,
    can_ping_gateway: Option<bool>,
    can_resolve_dns: bool,
    can_reach_internet: bool,
    wifi_signal_strength: Option<String>,
    vpn_adapter_detected: bool,
    recent_network_errors: Option<String>,
}

fn ping_host(host: &str) -> bool {
    let args: Vec<&str> = if cfg!(target_os = "windows") {
        vec!["-n", "1", "-w", "1500", host]
    } else {
        vec!["-c", "1", "-W", "1500", host]
    };
    command_succeeds("ping", &args)
}

fn command_succeeds(program: &str, args: &[&str]) -> bool {
    std::process::Command::new(program)
        .args(args)
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map(|s| s.success())
        .unwrap_or(false)
}

fn can_resolve_dns() -> bool {
    ("microsoft.com", 443).to_socket_addrs().is_ok()
}

fn dns_servers_from_resolv_conf() -> Vec<String> {
    std::fs::read_to_string("/etc/resolv.conf")
        .map(|contents| {
            contents
                .lines()
                .filter_map(|line| line.strip_prefix("nameserver "))
                .map(|s| s.trim().to_string())
                .collect()
        })
        .unwrap_or_default()
}

#[tauri::command]
pub fn get_network_diagnostics() -> DiagnosticReport<NetworkResults> {
    let default_iface = default_net::get_default_interface().ok();

    let active_adapter = default_iface.as_ref().map(|i| i.name.clone());
    let ip_address = default_iface
        .as_ref()
        .and_then(|i| i.ipv4.first())
        .map(|net| net.addr.to_string());
    let gateway = default_iface
        .as_ref()
        .and_then(|i| i.gateway.as_ref())
        .map(|g| g.ip_addr.to_string());

    let dns_servers = if cfg!(target_os = "windows") {
        Vec::new() // TODO: parse `ipconfig /all` output for "DNS Servers" lines.
    } else {
        dns_servers_from_resolv_conf()
    };

    let can_ping_gateway = gateway.as_deref().map(ping_host);
    let can_reach_internet = ping_host("1.1.1.1");
    let resolves_dns = can_resolve_dns();

    let vpn_adapter_detected = default_net::get_interfaces().iter().any(|i| {
        let name = i.name.to_lowercase();
        ["tun", "tap", "ppp", "wg", "vpn"].iter().any(|kw| name.contains(kw))
    });

    let results = NetworkResults {
        active_adapter,
        ip_address,
        gateway,
        dns_servers,
        can_ping_gateway,
        can_resolve_dns: resolves_dns,
        can_reach_internet,
        wifi_signal_strength: None, // TODO: platform-specific Wi-Fi RSSI API.
        vpn_adapter_detected,
        recent_network_errors: None, // TODO: Windows Event Log query.
    };

    let severity = if !can_reach_internet {
        "critical"
    } else if !can_ping_gateway.unwrap_or(true) || !resolves_dns {
        "warning"
    } else {
        "ok"
    };

    DiagnosticReport {
        diagnostic_pack: "network_basic",
        device_name: device_name(),
        timestamp: now_iso(),
        results,
        severity,
    }
}

// ---------------------------------------------------------------------------
// Printer Basic
// ---------------------------------------------------------------------------

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct PrinterResults {
    default_printer: Option<String>,
    installed_printers: Vec<String>,
    queue_count: Option<u32>,
    spooler_status: String,
    recent_print_errors: Option<String>,
    printer_online: Option<bool>,
    printer_ip_reachable: Option<bool>,
}

fn spooler_status() -> String {
    if cfg!(target_os = "windows") {
        run_fixed_command("sc", &["query", "Spooler"])
            .ok()
            .and_then(|out| {
                out.lines()
                    .find(|l| l.contains("STATE"))
                    .map(|l| l.trim().to_string())
            })
            .map(|line| {
                if line.contains("RUNNING") {
                    "Running".to_string()
                } else if line.contains("STOPPED") {
                    "Stopped".to_string()
                } else {
                    line
                }
            })
            .unwrap_or_else(|| "Unknown".to_string())
    } else {
        "Not applicable -- no Print Spooler service on this OS".to_string()
    }
}

fn default_printer() -> Option<String> {
    if cfg!(target_os = "windows") {
        run_fixed_command(
            "powershell",
            &[
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                "(Get-CimInstance -ClassName Win32_Printer -Filter 'Default=true').Name",
            ],
        )
        .ok()
        .map(|s| s.trim().to_string())
        .filter(|s| !s.is_empty())
    } else {
        None
    }
}

#[tauri::command]
pub fn get_printer_diagnostics() -> DiagnosticReport<PrinterResults> {
    let status = spooler_status();
    let results = PrinterResults {
        default_printer: default_printer(),
        installed_printers: Vec::new(), // TODO: enumerate via Win32 print spooler APIs.
        queue_count: None,              // TODO: enumerate print jobs for the default printer.
        spooler_status: status.clone(),
        recent_print_errors: None, // TODO: Windows Event Log query.
        printer_online: None,      // TODO: needs a printer IP/port to probe.
        printer_ip_reachable: None,
    };

    let severity = if status == "Stopped" { "warning" } else { "ok" };

    DiagnosticReport {
        diagnostic_pack: "printer_basic",
        device_name: device_name(),
        timestamp: now_iso(),
        results,
        severity,
    }
}

// ---------------------------------------------------------------------------
// OneDrive Basic
// ---------------------------------------------------------------------------

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct OneDriveResults {
    process_running: bool,
    sync_folder_detected: bool,
    sync_status: Option<String>,
    recent_errors: Option<String>,
}

fn process_running(name_fragment: &str) -> bool {
    let mut sys = System::new_all();
    sys.refresh_processes(sysinfo::ProcessesToUpdate::All, true);
    sys.processes()
        .values()
        .any(|p| p.name().to_string_lossy().to_lowercase().contains(name_fragment))
}

fn onedrive_folder_exists() -> bool {
    dirs_home()
        .map(|home| home.join("OneDrive").exists())
        .unwrap_or(false)
}

fn dirs_home() -> Option<std::path::PathBuf> {
    std::env::var_os("USERPROFILE")
        .or_else(|| std::env::var_os("HOME"))
        .map(std::path::PathBuf::from)
}

#[tauri::command]
pub fn get_onedrive_diagnostics() -> DiagnosticReport<OneDriveResults> {
    let running = process_running("onedrive");
    let folder_detected = onedrive_folder_exists();

    let results = OneDriveResults {
        process_running: running,
        sync_folder_detected: folder_detected,
        sync_status: None, // TODO: read OneDrive's own status API/registry.
        recent_errors: None,
    };

    let severity = if folder_detected && !running { "warning" } else { "ok" };

    DiagnosticReport {
        diagnostic_pack: "onedrive_basic",
        device_name: device_name(),
        timestamp: now_iso(),
        results,
        severity,
    }
}

// ---------------------------------------------------------------------------
// Outlook Basic
// ---------------------------------------------------------------------------

#[derive(Serialize)]
#[serde(rename_all = "snake_case")]
pub struct OutlookResults {
    installed: Option<bool>,
    running: bool,
    recent_crash_events: Option<String>,
    profile_detected: Option<bool>,
    ost_pst_size_mb: Option<u64>,
}

#[tauri::command]
pub fn get_outlook_diagnostics() -> DiagnosticReport<OutlookResults> {
    let running = process_running("outlook");

    let results = OutlookResults {
        installed: None, // TODO: check registry (Windows) / installed application list.
        running,
        recent_crash_events: None, // TODO: Windows Event Log query.
        profile_detected: None,    // TODO: read Outlook profile registry key.
        ost_pst_size_mb: None,     // TODO: locate profile's data files and stat() them.
    };

    DiagnosticReport {
        diagnostic_pack: "outlook_basic",
        device_name: device_name(),
        timestamp: now_iso(),
        results,
        severity: "ok",
    }
}
