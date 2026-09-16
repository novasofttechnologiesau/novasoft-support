import type { AuditLog } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<AuditLog[]>("/audit-logs")
      .then(setLogs)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load audit logs"));
  }, []);

  return (
    <div>
      <h1 className="mb-6 text-xl font-semibold">Audit Logs</h1>
      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}
      <Card className="p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-nova-border text-left text-xs uppercase tracking-wide text-nova-muted">
              <th className="px-5 py-3 font-medium">Time</th>
              <th className="px-5 py-3 font-medium">Action</th>
              <th className="px-5 py-3 font-medium">Entity</th>
              <th className="px-5 py-3 font-medium">Metadata</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((l) => (
              <tr key={l.id} className="border-b border-nova-border last:border-0 hover:bg-nova-surface/60">
                <td className="px-5 py-3 text-nova-muted">{new Date(l.created_at).toLocaleString()}</td>
                <td className="px-5 py-3 font-medium">{l.action}</td>
                <td className="px-5 py-3 text-nova-muted">
                  {l.entity_type} {l.entity_id ? `#${l.entity_id.slice(0, 8)}` : ""}
                </td>
                <td className="px-5 py-3 font-mono text-xs text-nova-muted">{JSON.stringify(l.metadata_json)}</td>
              </tr>
            ))}
            {logs.length === 0 && (
              <tr>
                <td colSpan={4} className="px-5 py-10 text-center text-nova-muted">
                  No audit log entries yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
