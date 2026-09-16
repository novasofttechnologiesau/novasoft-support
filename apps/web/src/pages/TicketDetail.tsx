import type {
  ActionRun,
  AITriageResult,
  AuditLog,
  Device,
  DiagnosticRun,
  Ticket,
  TicketAttachment,
  TicketMessage,
  User,
} from "@novasoft/shared";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PriorityBadge, RiskBadge, StatusBadge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const { user } = useAuth();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [attachments, setAttachments] = useState<TicketAttachment[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticRun[]>([]);
  const [triage, setTriage] = useState<AITriageResult | null>(null);
  const [actionRuns, setActionRuns] = useState<ActionRun[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [devices, setDevices] = useState<Device[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [newComment, setNewComment] = useState("");
  const [isInternal, setIsInternal] = useState(false);

  const load = useCallback(async () => {
    if (!ticketId) return;
    try {
      const [t, m, a, d, actions, u, dev] = await Promise.all([
        api.get<Ticket>(`/tickets/${ticketId}`),
        api.get<TicketMessage[]>(`/tickets/${ticketId}/messages`),
        api.get<TicketAttachment[]>(`/tickets/${ticketId}/attachments`),
        api.get<DiagnosticRun[]>(`/tickets/${ticketId}/diagnostics`),
        api.get<ActionRun[]>(`/tickets/${ticketId}/actions`),
        api.get<User[]>("/users").catch(() => []),
        api.get<Device[]>("/devices").catch(() => []),
      ]);
      setTicket(t);
      setMessages(m);
      setAttachments(a);
      setDiagnostics(d);
      setActionRuns(actions);
      setUsers(u);
      setDevices(dev);

      try {
        setTriage(await api.get<AITriageResult>(`/tickets/${ticketId}/ai-triage`));
      } catch {
        setTriage(null);
      }

      if (user?.role === "admin") {
        const logs = await api.get<AuditLog[]>("/audit-logs");
        const relevantIds = new Set([ticketId, ...d.map((r) => r.id), ...actions.map((r) => r.id)]);
        setAuditLogs(logs.filter((l) => l.entity_id && relevantIds.has(l.entity_id)));
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load ticket");
    }
  }, [ticketId, user?.role]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!ticket) return <p className="text-sm text-nova-muted">Loading ticket…</p>;

  const requester = users.find((u) => u.id === ticket.requester_id);
  const device = devices.find((d) => d.id === ticket.device_id);
  const userVisibleMessages = messages.filter((m) => !m.is_internal);
  const internalNotes = messages.filter((m) => m.is_internal);

  async function updateStatus(status: string) {
    setBusy("status");
    try {
      const updated = await api.patch<Ticket>(`/tickets/${ticketId}`, { status });
      setTicket(updated);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to update status");
    } finally {
      setBusy(null);
    }
  }

  async function postComment() {
    if (!newComment.trim()) return;
    setBusy("comment");
    try {
      await api.post(`/tickets/${ticketId}/messages`, { body: newComment, is_internal: isInternal });
      setNewComment("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add comment");
    } finally {
      setBusy(null);
    }
  }

  async function runTriage() {
    setBusy("triage");
    try {
      const result = await api.post<AITriageResult>(`/ai/triage/${ticketId}`);
      setTriage(result);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "AI triage failed");
    } finally {
      setBusy(null);
    }
  }

  async function requestAction(actionName: string) {
    if (!ticket || !ticket.device_id) return;
    setBusy(actionName);
    try {
      await api.post(`/actions/run`, {
        ticket_id: ticket.id,
        device_id: ticket.device_id,
        action_name: actionName,
        ai_suggested: true,
      });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to request action");
    } finally {
      setBusy(null);
    }
  }

  async function approveAction(actionRunId: string) {
    setBusy(actionRunId);
    try {
      await api.post(`/actions/${actionRunId}/approve`);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to approve action");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-semibold">{ticket.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <StatusBadge status={ticket.status} />
            <PriorityBadge priority={ticket.priority} />
            <span className="text-sm capitalize text-nova-muted">{ticket.category.replace(/_/g, " ")}</span>
          </div>
        </div>
        <select
          value={ticket.status}
          disabled={busy === "status"}
          onChange={(e) => updateStatus(e.target.value)}
          className="rounded-lg border border-nova-border bg-nova-card px-3 py-2 text-sm"
        >
          {["new", "awaiting_diagnostics", "ai_triaged", "waiting_for_technician", "in_progress", "waiting_for_user", "resolved", "closed"].map(
            (s) => (
              <option key={s} value={s}>
                {s.replace(/_/g, " ")}
              </option>
            ),
          )}
        </select>
      </div>

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-6">
          <Card title="Description">
            <p className="whitespace-pre-wrap text-sm text-nova-text">{ticket.description}</p>
          </Card>

          {attachments.length > 0 && (
            <Card title="Attachments">
              <ul className="space-y-1 text-sm">
                {attachments.map((a) => (
                  <li key={a.id} className="text-nova-text">
                    📎 {a.original_file_name} <span className="text-nova-muted">({Math.round(a.size_bytes / 1024)} KB)</span>
                  </li>
                ))}
              </ul>
            </Card>
          )}

          <Card title="Conversation">
            <div className="space-y-3">
              {userVisibleMessages.map((m) => (
                <div key={m.id} className="rounded-lg bg-nova-surface p-3 text-sm">
                  <div className="mb-1 text-xs text-nova-muted">{new Date(m.created_at).toLocaleString()}</div>
                  {m.body}
                </div>
              ))}
              {userVisibleMessages.length === 0 && <p className="text-sm text-nova-muted">No messages yet.</p>}
            </div>
            <div className="mt-4 space-y-2">
              <textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Write a reply…"
                className="w-full rounded-lg border border-nova-border bg-nova-surface p-2.5 text-sm outline-none focus:border-nova-accent"
                rows={3}
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-xs text-nova-muted">
                  <input type="checkbox" checked={isInternal} onChange={(e) => setIsInternal(e.target.checked)} />
                  Internal note (not visible to user)
                </label>
                <Button onClick={postComment} disabled={busy === "comment"}>
                  {busy === "comment" ? "Posting…" : "Post"}
                </Button>
              </div>
            </div>
          </Card>

          {internalNotes.length > 0 && (
            <Card title="Internal Technician Notes">
              <div className="space-y-3">
                {internalNotes.map((m) => (
                  <div key={m.id} className="rounded-lg border border-amber-500/20 bg-amber-500/5 p-3 text-sm">
                    <div className="mb-1 text-xs text-nova-muted">{new Date(m.created_at).toLocaleString()}</div>
                    {m.body}
                  </div>
                ))}
              </div>
            </Card>
          )}

          <Card title="Diagnostic History">
            <div className="space-y-3">
              {diagnostics.map((run) => (
                <div key={run.id} className="rounded-lg bg-nova-surface p-3 text-sm">
                  <div className="mb-1 flex items-center justify-between">
                    <span className="font-medium capitalize">{run.diagnostic_pack.replace(/_/g, " ")}</span>
                    <span className="text-xs text-nova-muted">
                      {run.completed_at ? new Date(run.completed_at).toLocaleString() : ""}
                    </span>
                  </div>
                  {run.results.map((r) => (
                    <pre key={r.id} className="mt-1 overflow-x-auto rounded bg-nova-bg p-2 text-xs text-nova-muted">
                      {JSON.stringify(r.result_json, null, 2)}
                    </pre>
                  ))}
                </div>
              ))}
              {diagnostics.length === 0 && <p className="text-sm text-nova-muted">No diagnostics have been run yet.</p>}
            </div>
          </Card>

          {auditLogs.length > 0 && (
            <Card title="Audit Log">
              <ul className="space-y-1 text-xs text-nova-muted">
                {auditLogs.map((l) => (
                  <li key={l.id}>
                    {new Date(l.created_at).toLocaleString()} — <span className="text-nova-text">{l.action}</span> ({l.entity_type})
                  </li>
                ))}
              </ul>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card title="Requester &amp; Device">
            <dl className="space-y-2 text-sm">
              <div>
                <dt className="text-xs text-nova-muted">Requester</dt>
                <dd>{requester?.full_name ?? "Unknown"}</dd>
              </div>
              <div>
                <dt className="text-xs text-nova-muted">Device</dt>
                <dd>{device?.device_name ?? "None"}</dd>
              </div>
            </dl>
          </Card>

          <Card
            title="AI Triage"
            action={
              <Button variant="secondary" onClick={runTriage} disabled={busy === "triage"}>
                {busy === "triage" ? "Running…" : triage ? "Re-run" : "Run AI Triage"}
              </Button>
            }
          >
            {triage ? (
              <div className="space-y-3 text-sm">
                <p className="text-nova-text">{triage.summary}</p>
                <div>
                  <div className="text-xs text-nova-muted">Likely cause</div>
                  <div>{triage.likely_cause}</div>
                </div>
                <div className="flex items-center gap-2">
                  <RiskBadge risk={triage.risk_level} />
                  <span className="text-xs text-nova-muted">Confidence {Math.round(triage.confidence * 100)}%</span>
                </div>
                {triage.escalate && (
                  <p className="rounded-lg border border-red-500/30 bg-red-500/10 p-2 text-xs text-red-400">
                    Escalation recommended
                  </p>
                )}
                {triage.recommended_actions_json.length > 0 && (
                  <div>
                    <div className="mb-1 text-xs text-nova-muted">Recommended actions</div>
                    <div className="space-y-2">
                      {triage.recommended_actions_json.map((a) => (
                        <div key={a.action} className="rounded-lg bg-nova-surface p-2">
                          <div className="flex items-center justify-between">
                            <span className="font-medium">{a.action}</span>
                            <Button
                              variant="secondary"
                              className="!px-2 !py-1 text-xs"
                              onClick={() => requestAction(a.action)}
                              disabled={busy === a.action}
                            >
                              {busy === a.action ? "…" : "Run"}
                            </Button>
                          </div>
                          <p className="mt-1 text-xs text-nova-muted">{a.reason}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {triage.user_reply_draft && (
                  <div>
                    <div className="text-xs text-nova-muted">Draft reply to user</div>
                    <p className="italic text-nova-text">{triage.user_reply_draft}</p>
                  </div>
                )}
                {triage.technician_notes && (
                  <div>
                    <div className="text-xs text-nova-muted">Technician notes</div>
                    <p>{triage.technician_notes}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-nova-muted">No AI triage has been run for this ticket yet.</p>
            )}
          </Card>

          <Card title="Approved Actions History">
            <div className="space-y-2">
              {actionRuns.map((run) => (
                <div key={run.id} className="rounded-lg bg-nova-surface p-2.5 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{run.action_name}</span>
                    <span className="text-xs capitalize text-nova-muted">{run.status}</span>
                  </div>
                  <div className="mt-1 flex items-center justify-between text-xs text-nova-muted">
                    <span>{run.ai_suggested ? "AI suggested" : "Manually run"} · approval: {run.approval_status}</span>
                    {run.approval_status === "pending" && (
                      <Button
                        variant="secondary"
                        className="!px-2 !py-1"
                        onClick={() => approveAction(run.id)}
                        disabled={busy === run.id}
                      >
                        Approve
                      </Button>
                    )}
                  </div>
                </div>
              ))}
              {actionRuns.length === 0 && <p className="text-sm text-nova-muted">No actions have been run yet.</p>}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
