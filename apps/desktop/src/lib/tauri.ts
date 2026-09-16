import { invoke } from "@tauri-apps/api/core";

// True when running inside the actual Tauri desktop shell. False when this app is loaded in a
// plain browser tab (e.g. `npm run dev` opened directly, or a preview tool) -- in that case we
// fall back to clearly-labeled mock data so the UI can still be exercised without native APIs.
export const isTauri = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

export interface DiagnosticReport<T> {
  diagnostic_pack: string;
  device_name: string;
  timestamp: string;
  results: T;
  severity: "ok" | "info" | "warning" | "critical";
}

export interface ActionResult {
  action: string;
  success: boolean;
  message: string;
  timestamp: string;
}

export interface DeviceHealthResults {
  computer_name: string;
  current_username: string;
  windows_version: string;
  uptime_seconds: number;
  cpu_usage_percent: number;
  ram_usage_percent: number;
  disk_usage_percent: number | null;
  battery_status: string | null;
  pending_reboot: boolean | null;
  antivirus_status: string | null;
  last_boot_time: string;
  unavailable_fields: string[];
}

export interface NetworkResults {
  active_adapter: string | null;
  ip_address: string | null;
  gateway: string | null;
  dns_servers: string[];
  can_ping_gateway: boolean | null;
  can_resolve_dns: boolean;
  can_reach_internet: boolean;
  wifi_signal_strength: string | null;
  vpn_adapter_detected: boolean;
  recent_network_errors: string | null;
}

export interface PrinterResults {
  default_printer: string | null;
  installed_printers: string[];
  queue_count: number | null;
  spooler_status: string;
  recent_print_errors: string | null;
  printer_online: boolean | null;
  printer_ip_reachable: boolean | null;
}

export interface OneDriveResults {
  process_running: boolean;
  sync_folder_detected: boolean;
  sync_status: string | null;
  recent_errors: string | null;
}

export interface OutlookResults {
  installed: boolean | null;
  running: boolean;
  recent_crash_events: string | null;
  profile_detected: boolean | null;
  ost_pst_size_mb: number | null;
}

async function call<T>(command: string, mock: () => T): Promise<T> {
  if (!isTauri) {
    // eslint-disable-next-line no-console
    console.warn(`[dev preview] '${command}' mocked -- not running inside the NovaSoft Support desktop shell`);
    await new Promise((r) => setTimeout(r, 300));
    return mock();
  }
  return invoke<T>(command);
}

const nowIso = () => new Date().toISOString();

export const tauriCommands = {
  getDeviceHealth: () =>
    call<DiagnosticReport<DeviceHealthResults>>("get_device_health", () => ({
      diagnostic_pack: "device_health_basic",
      device_name: "DEV-PREVIEW-PC",
      timestamp: nowIso(),
      severity: "ok",
      results: {
        computer_name: "DEV-PREVIEW-PC",
        current_username: "preview-user",
        windows_version: "Not applicable (browser preview)",
        uptime_seconds: 3600,
        cpu_usage_percent: 12.5,
        ram_usage_percent: 41.2,
        disk_usage_percent: 55.0,
        battery_status: null,
        pending_reboot: null,
        antivirus_status: null,
        last_boot_time: nowIso(),
        unavailable_fields: ["battery_status", "pending_reboot", "antivirus_status"],
      },
    })),

  getNetworkDiagnostics: () =>
    call<DiagnosticReport<NetworkResults>>("get_network_diagnostics", () => ({
      diagnostic_pack: "network_basic",
      device_name: "DEV-PREVIEW-PC",
      timestamp: nowIso(),
      severity: "ok",
      results: {
        active_adapter: "en0 (preview)",
        ip_address: "192.168.1.42",
        gateway: "192.168.1.1",
        dns_servers: ["1.1.1.1", "8.8.8.8"],
        can_ping_gateway: true,
        can_resolve_dns: true,
        can_reach_internet: true,
        wifi_signal_strength: null,
        vpn_adapter_detected: false,
        recent_network_errors: null,
      },
    })),

  getPrinterDiagnostics: () =>
    call<DiagnosticReport<PrinterResults>>("get_printer_diagnostics", () => ({
      diagnostic_pack: "printer_basic",
      device_name: "DEV-PREVIEW-PC",
      timestamp: nowIso(),
      severity: "warning",
      results: {
        default_printer: "Kyocera Main Office (preview)",
        installed_printers: [],
        queue_count: null,
        spooler_status: "Stopped",
        recent_print_errors: "Print Spooler service terminated unexpectedly",
        printer_online: null,
        printer_ip_reachable: null,
      },
    })),

  getOneDriveDiagnostics: () =>
    call<DiagnosticReport<OneDriveResults>>("get_onedrive_diagnostics", () => ({
      diagnostic_pack: "onedrive_basic",
      device_name: "DEV-PREVIEW-PC",
      timestamp: nowIso(),
      severity: "ok",
      results: {
        process_running: true,
        sync_folder_detected: true,
        sync_status: null,
        recent_errors: null,
      },
    })),

  getOutlookDiagnostics: () =>
    call<DiagnosticReport<OutlookResults>>("get_outlook_diagnostics", () => ({
      diagnostic_pack: "outlook_basic",
      device_name: "DEV-PREVIEW-PC",
      timestamp: nowIso(),
      severity: "ok",
      results: {
        installed: null,
        running: false,
        recent_crash_events: null,
        profile_detected: null,
        ost_pst_size_mb: null,
      },
    })),

};
