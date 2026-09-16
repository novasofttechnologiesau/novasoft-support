import type { ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../lib/auth";

const NAV_ITEMS = [
  { to: "/tickets", label: "Ticket Queue", icon: "🎫" },
  { to: "/devices", label: "Devices", icon: "🖥️" },
  { to: "/users", label: "Users", icon: "👤", adminOnly: true },
  { to: "/clients", label: "Clients", icon: "🏢", adminOnly: true },
  { to: "/knowledge-base", label: "Knowledge Base", icon: "📚" },
  { to: "/audit-logs", label: "Audit Logs", icon: "🛡️", adminOnly: true },
];

export function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen bg-nova-bg">
      <aside className="flex w-60 flex-shrink-0 flex-col border-r border-nova-border bg-nova-surface">
        <div className="flex items-center gap-2 border-b border-nova-border px-5 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-nova-accent font-bold text-white">N</div>
          <div>
            <div className="text-sm font-semibold leading-tight">NovaSoft</div>
            <div className="text-xs leading-tight text-nova-muted">Support Dashboard</div>
          </div>
        </div>
        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV_ITEMS.filter((item) => !item.adminOnly || user?.role === "admin").map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive ? "bg-nova-accent/15 text-nova-accent" : "text-nova-muted hover:bg-nova-card hover:text-nova-text"
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-nova-border px-4 py-4">
          <div className="mb-2 text-sm">
            <div className="font-medium">{user?.full_name}</div>
            <div className="text-xs capitalize text-nova-muted">{user?.role.replace("_", " ")}</div>
          </div>
          <button onClick={logout} className="text-xs font-medium text-nova-muted hover:text-nova-text">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
