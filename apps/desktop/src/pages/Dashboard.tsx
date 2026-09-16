import type { Ticket } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PriorityBadge, StatusBadge } from "../components/Badge";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";

export function DashboardPage() {
  const { user, device } = useAuth();
  const [tickets, setTickets] = useState<Ticket[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Ticket[]>("/tickets")
      .then(setTickets)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Failed to load tickets"));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Welcome, {user?.full_name?.split(" ")[0]}</h1>
        <p className="text-sm text-nova-muted">
          Signed in as {user?.email} · Device: {device?.device_name ?? "registering…"}
        </p>
      </div>

      <div className="flex gap-3">
        <Link to="/new-ticket">
          <Button>+ New Ticket</Button>
        </Link>
        <Link to="/diagnostics">
          <Button variant="secondary">Run Diagnostics</Button>
        </Link>
      </div>

      {error && <p className="text-sm text-red-400">{error}</p>}

      <Card title="Your Tickets">
        <div className="space-y-2">
          {tickets?.map((t) => (
            <Link
              key={t.id}
              to={`/tickets/${t.id}`}
              className="flex items-center justify-between rounded-lg bg-nova-surface p-3 text-sm hover:bg-nova-border/40"
            >
              <div>
                <div className="font-medium">{t.title}</div>
                <div className="text-xs capitalize text-nova-muted">{t.category.replace(/_/g, " ")}</div>
              </div>
              <div className="flex items-center gap-2">
                <PriorityBadge priority={t.priority} />
                <StatusBadge status={t.status} />
              </div>
            </Link>
          ))}
          {tickets && tickets.length === 0 && <p className="text-sm text-nova-muted">You haven't submitted any tickets yet.</p>}
        </div>
      </Card>
    </div>
  );
}
