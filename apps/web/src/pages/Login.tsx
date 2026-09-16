import { useState, type FormEvent } from "react";
import { Navigate } from "react-router-dom";
import { Button } from "../components/Button";
import { ApiError } from "../lib/api";
import { useAuth } from "../lib/auth";

export function LoginPage() {
  const { user, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to="/tickets" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-nova-bg px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex flex-col items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-nova-accent text-xl font-bold text-white">N</div>
          <div className="text-center">
            <div className="text-lg font-semibold">NovaSoft Support</div>
            <div className="text-sm text-nova-muted">Technician &amp; Admin Dashboard</div>
          </div>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4 rounded-xl border border-nova-border bg-nova-card p-6">
          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Email</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm outline-none focus:border-nova-accent"
              placeholder="tech@novasoft.example"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-xs font-medium text-nova-muted">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-nova-border bg-nova-surface px-3 py-2 text-sm outline-none focus:border-nova-accent"
              placeholder="••••••••"
            />
          </div>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <Button type="submit" disabled={submitting} className="w-full justify-center">
            {submitting ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </div>
    </div>
  );
}
