import type { Ticket } from "@novasoft/shared";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Card } from "../components/Card";
import { PriorityBadge, StatusBadge } from "../components/Badge";
import { api } from "../lib/api";

export function TicketQueuePage() {
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("all");

  useEffect(() => {
    api
      .get<Ticket[]>("/tickets")
      .then(setTickets)
      .catch((e) => setError(e.message));
  }, []);

  const filtered = useMemo(() => {
    if (!tickets) return [];
    if (statusFilter === "all") return tickets;
    return tickets.filter((t) => t.status === statusFilter);
  }, [tickets, statusFilter]);

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Ticket Queue</h1>
          <p className="text-sm text-nova-muted">All support tickets across clients.</p>
        </div>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-lg border border-nova-border bg-nova-card px-3 py-2 text-sm"
        >
          <option value="all">All statuses</option>
          <option value="new">New</option>
          <option value="awaiting_diagnostics">Awaiting diagnostics</option>
          <option value="ai_triaged">AI triaged</option>
          <option value="waiting_for_technician">Waiting for technician</option>
          <option value="in_progress">In progress</option>
          <option value="waiting_for_user">Waiting for user</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {error && <p className="mb-4 text-sm text-red-400">{error}</p>}

      <Card className="p-0">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-nova-border text-left text-xs uppercase tracking-wide text-nova-muted">
              <th className="px-5 py-3 font-medium">Title</th>
              <th className="px-5 py-3 font-medium">Category</th>
              <th className="px-5 py-3 font-medium">Priority</th>
              <th className="px-5 py-3 font-medium">Status</th>
              <th className="px-5 py-3 font-medium">Created</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((ticket) => (
              <tr key={ticket.id} className="border-b border-nova-border last:border-0 hover:bg-nova-surface/60">
                <td className="px-5 py-3">
                  <Link to={`/tickets/${ticket.id}`} className="font-medium text-nova-text hover:text-nova-accent">
                    {ticket.title}
                  </Link>
                </td>
                <td className="px-5 py-3 capitalize text-nova-muted">{ticket.category.replace(/_/g, " ")}</td>
                <td className="px-5 py-3">
                  <PriorityBadge priority={ticket.priority} />
                </td>
                <td className="px-5 py-3">
                  <StatusBadge status={ticket.status} />
                </td>
                <td className="px-5 py-3 text-nova-muted">{new Date(ticket.created_at).toLocaleString()}</td>
              </tr>
            ))}
            {tickets && filtered.length === 0 && (
              <tr>
                <td colSpan={5} className="px-5 py-10 text-center text-nova-muted">
                  No tickets match this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
