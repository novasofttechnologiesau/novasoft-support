# Architecture

- `apps/api`: FastAPI, PostgreSQL, SQLAlchemy and Alembic; authentication, access checks,
  ticketing, diagnostic records, AI orchestration and audit events.
- `apps/web`: React technician/admin dashboard built with Vite.
- `apps/desktop`: React end-user UI and Tauri shell with five read-only diagnostic commands.
- `packages/shared`: TypeScript interfaces consumed directly by both frontends.

Both frontends call the API over JSON/HTTP locally. Only the backend accesses PostgreSQL.
The backend never opens connections to end-user devices. Native diagnostic results are
submitted by the desktop client after consent. Browser previews substitute mock diagnostics.

AI providers accept a constructed context and return schema-validated recommendations.
The mock provider is deterministic; DeepSeek is optional and explicitly opt-in. AI has no
command execution interface. Only server-side ticket escalation is implemented in v0.1.0.
All clients belong to one support provider; technicians intentionally see all client companies.
