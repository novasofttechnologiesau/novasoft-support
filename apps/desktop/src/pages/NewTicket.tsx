import type { DiagnosticPack, Severity, Ticket, TicketCategory, TicketPriority } from "@novasoft/shared";
import { DIAGNOSTIC_PACK_LABELS, TICKET_CATEGORIES, TICKET_PRIORITIES } from "@novasoft/shared";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { PrivacyNoticeModal } from "../components/PrivacyNoticeModal";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { tauriCommands } from "../lib/tauri";

const SUGGESTED_PACK: Partial<Record<TicketCategory, DiagnosticPack>> = {
  printer_issue: "printer_basic",
  network_issue: "network_basic",
  onedrive_issue: "onedrive_basic",
  email_issue: "outlook_basic",
  slow_computer: "device_health_basic",
  hardware_issue: "device_health_basic",
};

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

export function NewTicketPage() {
  const { device } = useAuth();
  const navigate = useNavigate();

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState<TicketCategory>("printer_issue");
  const [priority, setPriority] = useState<TicketPriority>("normal");
  const [file, setFile] = useState<File | null>(null);

  const [showPrivacyNotice, setShowPrivacyNotice] = useState(false);
  const [diagnosticAttached, setDiagnosticAttached] = useState<{ pack: DiagnosticPack; result: unknown; severity: Severity } | null>(
    null,
  );
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const suggestedPack = SUGGESTED_PACK[category];

  async function confirmRunDiagnostics() {
    setShowPrivacyNotice(false);
    if (!suggestedPack) return;
    const report = await runPack(suggestedPack);
    setDiagnosticAttached({ pack: suggestedPack, result: report.results, severity: report.severity as Severity });
  }

  async function handleSubmit() {
    if (!title.trim() || !description.trim() || !device) return;
    setSubmitting(true);
    setError(null);
    try {
      const ticket = await api.post<Ticket>("/tickets", {
        title,
        description,
        category,
        priority,
        device_id: device.id,
      });

      if (diagnosticAttached) {
        await api.post("/diagnostics/runs", {
          device_id: device.id,
          ticket_id: ticket.id,
          diagnostic_pack: diagnosticAttached.pack,
          severity: diagnosticAttached.severity,
          result: diagnosticAttached.result,
        });
      }

      if (file) {
        const form = new FormData();
        form.append("file", file);
        await api.postForm(`/tickets/${ticket.id}/attachments`, form);
      }

      navigate(`/tickets/${ticket.id}`);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to submit ticket");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">New Support Ticket</h1>

      <Card>
        <div className="space-y-4">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Category</label>
            <select
              value={category}
              onChange={(e) => {
                setCategory(e.target.value as TicketCategory);
                setDiagnosticAttached(null);
              }}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
            >
              {TICKET_CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Urgency</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value as TicketPriority)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
            >
              {TICKET_PRIORITIES.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Title</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              placeholder="Short summary of the issue"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Describe the issue</label>
            <textarea
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              placeholder="The printer is not working."
            />
          </div>

          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Attach a screenshot or file (optional)</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              className="w-full text-sm text-nova-muted"
            />
          </div>

          {suggestedPack && (
            <div className="rounded-lg border border-nova-border bg-nova-surface p-3">
              {diagnosticAttached ? (
                <p className="text-sm text-emerald-400">
                  ✓ {DIAGNOSTIC_PACK_LABELS[diagnosticAttached.pack]} diagnostics attached.
                </p>
              ) : (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-nova-text">
                    Want to run <strong>{DIAGNOSTIC_PACK_LABELS[suggestedPack]}</strong> diagnostics? This can help us
                    resolve your issue faster.
                  </p>
                  <Button variant="secondary" onClick={() => setShowPrivacyNotice(true)}>
                    Run Diagnostics
                  </Button>
                </div>
              )}
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}

          <Button onClick={handleSubmit} disabled={submitting || !title.trim() || !description.trim()} className="w-full justify-center">
            {submitting ? "Submitting…" : "Submit Ticket"}
          </Button>
        </div>
      </Card>

      {showPrivacyNotice && suggestedPack && (
        <PrivacyNoticeModal
          packLabel={DIAGNOSTIC_PACK_LABELS[suggestedPack]}
          onConfirm={confirmRunDiagnostics}
          onCancel={() => setShowPrivacyNotice(false)}
        />
      )}
    </div>
  );
}
