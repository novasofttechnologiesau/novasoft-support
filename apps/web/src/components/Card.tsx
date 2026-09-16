import type { ReactNode } from "react";

export function Card({ title, action, children, className = "" }: { title?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-xl border border-nova-border bg-nova-card p-5 ${className}`}>
      {(title || action) && (
        <div className="mb-4 flex items-center justify-between">
          {title && <h3 className="text-sm font-semibold uppercase tracking-wide text-nova-muted">{title}</h3>}
          {action}
        </div>
      )}
      {children}
    </div>
  );
}
