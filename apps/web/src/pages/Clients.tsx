import type { Client } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";

export function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [name, setName] = useState("");
  const [contactEmail, setContactEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setClients(await api.get<Client[]>("/clients"));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function createClient() {
    if (!name.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/clients", { name, contact_email: contactEmail || null });
      setName("");
      setContactEmail("");
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create client");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Clients</h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2 p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nova-border text-left text-xs uppercase tracking-wide text-nova-muted">
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Contact Email</th>
                <th className="px-5 py-3 font-medium">Type</th>
              </tr>
            </thead>
            <tbody>
              {clients.map((c) => (
                <tr key={c.id} className="border-b border-nova-border last:border-0 hover:bg-nova-surface/60">
                  <td className="px-5 py-3 font-medium">{c.name}</td>
                  <td className="px-5 py-3 text-nova-muted">{c.contact_email ?? "—"}</td>
                  <td className="px-5 py-3 text-nova-muted">{c.is_internal ? "Internal (NovaSoft staff)" : "Client"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Add Client">
          <div className="space-y-3">
            <input
              placeholder="Client name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
            />
            <input
              placeholder="Contact email"
              value={contactEmail}
              onChange={(e) => setContactEmail(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
            />
            <Button onClick={createClient} disabled={submitting} className="w-full justify-center">
              {submitting ? "Creating…" : "Create client"}
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
