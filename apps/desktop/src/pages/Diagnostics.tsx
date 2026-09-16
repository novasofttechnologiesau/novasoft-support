import type { DiagnosticPack } from "@novasoft/shared";
import { DIAGNOSTIC_PACK_LABELS } from "@novasoft/shared";
import { useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { SeverityBadge } from "../components/Badge";
import { PrivacyNoticeModal } from "../components/PrivacyNoticeModal";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { tauriCommands } from "../lib/tauri";

const PACKS: { pack: DiagnosticPack; collects: string[] }[] = [
  {
    pack: "device_health_basic",
    collects: ["Computer name & username", "Windows version, uptime", "CPU/RAM/disk usage", "Last boot time"],
  },
  {
    pack: "network_basic",
    collects: ["Active adapter & IP", "Gateway & DNS servers", "Ping/DNS/internet reachability", "VPN adapter detection"],
  },
  {
    pack: "printer_basic",
    collects: ["Default printer", "Print Spooler service status", "Recent print errors"],
  },
  {
    pack: "onedrive_basic",
    collects: ["Whether OneDrive is running", "Whether a OneDrive sync folder exists"],
  },
  {
    pack: "outlook_basic",
    collects: ["Whether Outlook is running"],
  },
];

async function runPack(pack: DiagnosticPack) {
  switch (pack) {
    case "device_health_basic":
      return tauriCommands.getDeviceHealth();
    case "network_basic":
      return tauriCommands.getNetworkDiagnostics();
    case "printer_basic":
      return tauriCommands.getPrinterDiagnostics();
    case "onedrive_basic":
      return tauriCommands.getOneDriveDiagnostics();
    case "outlook_basic":
      return tauriCommands.getOutlookDiagnostics();
  }
}

export function DiagnosticsPage() {
  const { device } = useAuth();
  const [pendingPack, setPendingPack] = useState<DiagnosticPack | null>(null);
  const [running, setRunning] = useState<DiagnosticPack | null>(null);
  const [lastResult, setLastResult] = useState<Awaited<ReturnType<typeof runPack>> | null>(null);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function confirmRun() {
    if (!pendingPack) return;
    const pack = pendingPack;
    setPendingPack(null);
    setRunning(pack);
    setSaved(false);
    setError(null);
    try {
      const report = await runPack(pack);
      setLastResult(report);

      if (device) {
        await api.post("/diagnostics/runs", {
          device_id: device.id,
          diagnostic_pack: report.diagnostic_pack,
          severity: report.severity,
          result: report.results,
        });
        setSaved(true);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Diagnostic run failed");
    } finally {
      setRunning(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Diagnostics</h1>
        <p className="text-sm text-nova-muted">Run a safe, read-only diagnostic check on this device.</p>
      </div>

      <div className="grid grid-cols-2 gap-4">
        {PACKS.map(({ pack, collects }) => (
          <Card key={pack} title={DIAGNOSTIC_PACK_LABELS[pack]}>
            <ul className="mb-4 space-y-1 text-xs text-nova-muted">
              {collects.map((c) => (
                <li key={c}>• {c}</li>
              ))}
            </ul>
            <Button variant="secondary" onClick={() => setPendingPack(pack)} disabled={running !== null}>
              {running === pack ? "Running…" : "Run Diagnostics"}
            </Button>
          </Card>
        ))}
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      {lastResult && (
        <Card
          title={`Result: ${DIAGNOSTIC_PACK_LABELS[lastResult.diagnostic_pack as DiagnosticPack]}`}
          action={<SeverityBadge severity={lastResult.severity} />}
        >
          {saved && <p className="mb-2 text-xs text-emerald-400">✓ Saved to your diagnostic history.</p>}
          <pre className="overflow-x-auto rounded bg-nova-bg p-3 text-xs text-nova-muted">
            {JSON.stringify(lastResult.results, null, 2)}
          </pre>
        </Card>
      )}

      {pendingPack && (
        <PrivacyNoticeModal
          packLabel={DIAGNOSTIC_PACK_LABELS[pendingPack]}
          onConfirm={confirmRun}
          onCancel={() => setPendingPack(null)}
        />
      )}
    </div>
  );
}
