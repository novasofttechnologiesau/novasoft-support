import { PrivacyNoticeModal } from "../components/PrivacyNoticeModal";
import { useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { useAuth } from "../lib/auth";
import type { DeviceHealthResults, DiagnosticReport } from "../lib/tauri";
import { tauriCommands } from "../lib/tauri";

export function MyDevicePage() {
  const { device } = useAuth();
  const [health, setHealth] = useState<DiagnosticReport<DeviceHealthResults> | null>(null);
  const [loading, setLoading] = useState(false);
  const [consent, setConsent] = useState(false);

  async function refresh() {
    setConsent(false);
    setLoading(true);
    try {
      setHealth(await tauriCommands.getDeviceHealth());
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">My Device</h1>
      {consent && <PrivacyNoticeModal packLabel="Device health" onConfirm={refresh} onCancel={() => setConsent(false)} />}

      <Card title="Registered Device">
        <dl className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-xs text-nova-muted">Device name</dt>
            <dd>{device?.device_name ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-nova-muted">Hostname</dt>
            <dd>{device?.hostname ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-nova-muted">OS Version</dt>
            <dd>{device?.os_version ?? "—"}</dd>
          </div>
          <div>
            <dt className="text-xs text-nova-muted">Registered</dt>
            <dd>{device ? new Date(device.created_at).toLocaleDateString() : "—"}</dd>
          </div>
        </dl>
      </Card>

      <Card title="Live Snapshot" action={<Button variant="secondary" onClick={() => setConsent(true)} disabled={loading}>{loading ? "Checking…" : "Refresh"}</Button>}>
        {health ? (
          <dl className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-xs text-nova-muted">CPU usage</dt>
              <dd>{health.results.cpu_usage_percent.toFixed(1)}%</dd>
            </div>
            <div>
              <dt className="text-xs text-nova-muted">RAM usage</dt>
              <dd>{health.results.ram_usage_percent.toFixed(1)}%</dd>
            </div>
            <div>
              <dt className="text-xs text-nova-muted">Disk usage</dt>
              <dd>{health.results.disk_usage_percent?.toFixed(1) ?? "—"}%</dd>
            </div>
            <div>
              <dt className="text-xs text-nova-muted">Uptime</dt>
              <dd>{Math.floor(health.results.uptime_seconds / 3600)}h</dd>
            </div>
          </dl>
        ) : (
          <p className="text-sm text-nova-muted">Click Refresh to check current device health.</p>
        )}
      </Card>
    </div>
  );
}
