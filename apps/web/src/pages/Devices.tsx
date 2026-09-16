import type { Device } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { api } from "../lib/api";

export function DevicesPage() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Device[]>("/devices")
      .then(setDevices)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold">Devices</h1>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      <Card className="p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-nova-border text-left text-xs uppercase tracking-wide text-nova-muted">
              <th className="px-5 py-3 font-medium">Device Name</th>
              <th className="px-5 py-3 font-medium">Hostname</th>
              <th className="px-5 py-3 font-medium">OS Version</th>
              <th className="px-5 py-3 font-medium">Last Seen</th>
            </tr>
          </thead>
          <tbody>
            {devices.map((d) => (
              <tr key={d.id} className="border-b border-nova-border last:border-0 hover:bg-nova-surface/60">
                <td className="px-5 py-3 font-medium">{d.device_name}</td>
                <td className="px-5 py-3 text-nova-muted">{d.hostname ?? "—"}</td>
                <td className="px-5 py-3 text-nova-muted">{d.os_version ?? "—"}</td>
                <td className="px-5 py-3 text-nova-muted">{d.last_seen_at ? new Date(d.last_seen_at).toLocaleString() : "Never"}</td>
              </tr>
            ))}
            {devices.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-nova-muted">
                  No devices registered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
