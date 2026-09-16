import type { ActionRun, AITriageResult, DiagnosticRun, Ticket, TicketAttachment, TicketMessage } from "@novasoft/shared";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { PriorityBadge, StatusBadge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";

const DEVICE_ACTION_RUNNERS: Record<string, () => Promise<{ success: boolean; message: string }>> = {};

export function TicketDetailPage() {
  const { ticketId } = useParams<{ ticketId: string }>();

  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [messages, setMessages] = useState<TicketMessage[]>([]);
  const [attachments, setAttachments] = useState<TicketAttachment[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticRun[]>([]);
  const [triage, setTriage] = useState<AITriageResult | null>(null);
  const [actionRuns, setActionRuns] = useState<ActionRun[]>([]);
  const [newComment, setNewComment] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!ticketId) return;
    try {
      const [t, m, a, d, actions] = await Promise.all([
        api.get<Ticket>(`/tickets/${ticketId}`),
        api.get<TicketMessage[]>(`/tickets/${ticketId}/messages`),
        api.get<TicketAttachment[]>(`/tickets/${ticketId}/attachments`),
        api.get<DiagnosticRun[]>(`/tickets/${ticketId}/diagnostics`),
        api.get<ActionRun[]>(`/tickets/${ticketId}/actions`),
      ]);
      setTicket(t);
      setMessages(m);
      setAttachments(a);
      setDiagnostics(d);
      setActionRuns(actions);
      try {
        setTriage(await api.get<AITriageResult>(`/tickets/${ticketId}/ai-triage`));
      } catch {
        setTriage(null);
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to load ticket");
    }
  }, [ticketId]);

  useEffect(() => {
    load();
  }, [load]);

  if (error) return <p className="text-sm text-red-400">{error}</p>;
  if (!ticket) return <p className="text-sm text-nova-muted">Loading ticket…</p>;

  async function postComment() {
    if (!newComment.trim()) return;
    setBusy("comment");
    try {
      await api.post(`/tickets/${ticketId}/messages`, { body: newComment, is_internal: false });
      setNewComment("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to add comment");
    } finally {
      setBusy(null);
    }
  }

  async function runFix(actionName: string) {
    if (!ticket?.device_id) return;
    setBusy(actionName);
    try {
      const run = await api.post<ActionRun>("/actions/run", {
        ticket_id: ticket.id,
        device_id: ticket.device_id,
        action_name: actionName,
        ai_suggested: true,
      });

      if (run.status === "approved") {
        const runner = DEVICE_ACTION_RUNNERS[actionName];
        const result = runner ? await runner() : { success: false, message: "This action has no local handler yet." };
        await api.post(`/actions/${run.id}/complete`, {
          status: result.success ? "completed" : "failed",
          output: { message: result.message },
          error_message: result.success ? null : result.message,
        });
      }
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to run action");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">{ticket.title}</h1>
        <div className="mt-2 flex items-center gap-2">
          <StatusBadge status={ticket.status} />
          <PriorityBadge priority={ticket.priority} />
          <span className="text-sm capitalize text-nova-muted">{ticket.category.replace(/_/g, " ")}</span>
        </div>
      </div>

      <Card title="Description">
        <p className="whitespace-pre-wrap text-sm">{ticket.description}</p>
      </Card>

      {attachments.length > 0 && (
        <Card title="Attachments">
          <ul className="space-y-1 text-sm">
            {attachments.map((a) => (
              <li key={a.id}>📎 {a.original_file_name}</li>
            ))}
          </ul>
        </Card>
      )}

      {triage && (
        <Card title="Update from NovaSoft Support">
          <p className="text-sm text-nova-text">{triage.user_reply_draft ?? triage.summary}</p>
          {triage.recommended_actions_json.length > 0 && (
            <div className="mt-4 space-y-2">
              {triage.recommended_actions_json.map((a) => {
                const relatedRun = actionRuns.find((r) => r.action_name === a.action);
                const alreadyDone = relatedRun && ["completed", "failed"].includes(relatedRun.status);
                return (
                  <div key={a.action} className="rounded-lg bg-nova-surface p-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{a.action.replace(/_/g, " ")}</span>
                      {!alreadyDone && DEVICE_ACTION_RUNNERS[a.action] && (
                        <Button variant="secondary" className="!px-2 !py-1 text-xs" onClick={() => runFix(a.action)} disabled={busy === a.action}>
                          {busy === a.action ? "Running…" : "Run this fix"}
                        </Button>
                      )}
                      {alreadyDone && <span className="text-xs capitalize text-nova-muted">{relatedRun?.status}</span>}
                    </div>
                    <p className="mt-1 text-xs text-nova-muted">{a.reason}</p>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      )}

      {diagnostics.length > 0 && (
        <Card title="Diagnostic History">
          <div className="space-y-2">
            {diagnostics.map((run) => (
              <div key={run.id} className="rounded-lg bg-nova-surface p-3 text-sm">
                <span className="font-medium capitalize">{run.diagnostic_pack.replace(/_/g, " ")}</span>
              </div>
            ))}
          </div>
        </Card>
      )}

      <Card title="Conversation">
        <div className="space-y-3">
          {messages.map((m) => (
            <div key={m.id} className="rounded-lg bg-nova-surface p-3 text-sm">
              <div className="mb-1 text-xs text-nova-muted">{new Date(m.created_at).toLocaleString()}</div>
              {m.body}
            </div>
          ))}
          {messages.length === 0 && <p className="text-sm text-nova-muted">No messages yet.</p>}
        </div>
        <div className="mt-4 space-y-2">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Add a comment…"
            className="w-full rounded-lg border border-nova-border bg-nova-surface p-2.5 text-sm"
            rows={3}
          />
          <Button onClick={postComment} disabled={busy === "comment"}>
            {busy === "comment" ? "Posting…" : "Post comment"}
          </Button>
        </div>
      </Card>
    </div>
  );
}
