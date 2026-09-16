import { Card } from "../components/Card";
import { useAuth } from "../lib/auth";

export function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <h1 className="text-xl font-semibold">Settings</h1>

      <Card title="Profile">
        <dl className="space-y-2 text-sm">
          <div>
            <dt className="text-xs text-nova-muted">Full name</dt>
            <dd>{user?.full_name}</dd>
          </div>
          <div>
            <dt className="text-xs text-nova-muted">Email</dt>
            <dd>{user?.email}</dd>
          </div>
          <div>
            <dt className="text-xs text-nova-muted">Role</dt>
            <dd className="capitalize">{user?.role.replace("_", " ")}</dd>
          </div>
        </dl>
      </Card>

      <Card title="About">
        <p className="text-sm text-nova-muted">NovaSoft Support Desktop v0.1.0</p>
        <p className="mt-1 text-xs text-nova-muted">
          Diagnostics never collect your personal files, browser history, passwords, or private document contents.
        </p>
      </Card>
    </div>
  );
}
