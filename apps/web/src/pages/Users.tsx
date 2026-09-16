import type { Client, User, UserRole } from "@novasoft/shared";
import { useEffect, useState } from "react";
import { Button } from "../components/Button";
import { Card } from "../components/Card";
import { ApiError, api } from "../lib/api";
import { useAuth } from "../lib/auth";

const EMPTY_FORM = { client_id: "", email: "", password: "", full_name: "", role: "end_user" as UserRole };

export function UsersPage() {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    const [u, c] = await Promise.all([api.get<User[]>("/users"), api.get<Client[]>("/clients")]);
    setUsers(u);
    setClients(c);
    if (!form.client_id && c.length > 0) setForm((f) => ({ ...f, client_id: c[0].id }));
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function createUser() {
    setSubmitting(true);
    setError(null);
    try {
      await api.post("/users", form);
      setForm({ ...EMPTY_FORM, client_id: form.client_id });
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Failed to create user");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Users</h1>
      {error && <p className="text-sm text-red-400">{error}</p>}

      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2 p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-nova-border text-left text-xs uppercase tracking-wide text-nova-muted">
                <th className="px-5 py-3 font-medium">Name</th>
                <th className="px-5 py-3 font-medium">Email</th>
                <th className="px-5 py-3 font-medium">Role</th>
                <th className="px-5 py-3 font-medium">Active</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-nova-border last:border-0 hover:bg-nova-surface/60">
                  <td className="px-5 py-3 font-medium">{u.full_name}</td>
                  <td className="px-5 py-3 text-nova-muted">{u.email}</td>
                  <td className="px-5 py-3 capitalize text-nova-muted">{u.role.replace("_", " ")}</td>
                  <td className="px-5 py-3">{u.is_active ? "Yes" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        {currentUser?.role === "admin" && (
          <Card title="Create User">
            <div className="space-y-3">
              <select
                value={form.client_id}
                onChange={(e) => setForm({ ...form, client_id: e.target.value })}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              >
                {clients.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
              <input
                placeholder="Full name"
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              />
              <input
                placeholder="Email"
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              />
              <input
                placeholder="Password"
                type="password"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              />
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value as UserRole })}
                className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm"
              >
                <option value="end_user">End user</option>
                <option value="technician">Technician</option>
                <option value="admin">Admin</option>
              </select>
              <Button onClick={createUser} disabled={submitting} className="w-full justify-center">
                {submitting ? "Creating…" : "Create user"}
              </Button>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
