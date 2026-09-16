# Local setup

Follow the root README for the quick start. Python 3.12 and Node.js 22+ are the reference
environments. Native desktop builds also require Rust, platform build tools and the
[Tauri prerequisites](https://v2.tauri.app/start/prerequisites/).

## Configuration

Run `python3 scripts/configure_local.py` once from the repository root. This creates
owner-readable `.env` files with unique random database, JWT and demo login credentials.
The files are ignored by Git. Existing files are never overwritten.

Docker Compose exposes PostgreSQL on **127.0.0.1:5433 only**. API commands must run from
`apps/api` so its `.env` is loaded. The two Vite frontends use `http://localhost:8000` by
default. Use `VITE_API_BASE_URL` in their own local `.env` files to change that address.

The seed script is explicitly opt-in via `ALLOW_DEMO_SEED=true` and requires a generated
`DEMO_SEED_PASSWORD` of at least 16 characters. It creates fictional accounts and data.
Re-running it does not reset existing users' passwords.

If you change the database port, update both the root `.env` `POSTGRES_PORT` and the API's
`DATABASE_URL`. If a database port is already occupied, use a different local port.
Changing the root password later does not reset a password in an existing PostgreSQL volume.

## End-user application

- Browser demo: `npm run dev --workspace apps/desktop`, then <http://localhost:1420>.
- Native shell: `npm run dev:desktop` from the repository root.
- Frontend build: `npm run build` from the repository root.
- Rust check: `cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml --locked`.

Device registration uses an anonymous generated display label; it does not run diagnostics
or read the machine's username during login. Diagnostic and My Device snapshot actions
show a consent notice before collecting information. Browser previews use simulated data.

The native Content Security Policy allows the local API at `http://localhost:8000`.
A different deployment requires an explicit CSP `connect-src` update in
`apps/desktop/src-tauri/tauri.conf.json` and matching backend CORS configuration.
Do not add wildcard network origins. Native repair actions are absent from this release.

Windows-only checks are limited and have not been exercised on a real Windows machine
for this release. Source compilation is not equivalent to validating device behavior.

## Optional external AI

Default: `AI_PROVIDER=mock`, `ALLOW_EXTERNAL_AI=false`. No model call leaves the machine.
DeepSeek requires all three settings:

```dotenv
AI_PROVIDER=deepseek
ALLOW_EXTERNAL_AI=true
DEEPSEEK_API_KEY=
```

Enter your own key privately in `apps/api/.env`. `AI_MODEL` defaults to `deepseek-chat`.
Enabling the provider sends ticket text, diagnostic content, related ticket summaries,
relevant knowledge articles and action descriptions to DeepSeek. Obvious secret patterns
are redacted and direct requester/device name fields are replaced, but this is **not
complete anonymisation**. Use only data you are authorised to send. Calls may incur costs.
Provider failure falls back to mock triage; do not mistake a mock response for model analysis.

## Cleanup

Stop local API and frontend processes with Ctrl+C. `docker compose down` stops the demo
database container while preserving its volume. No production deployment is included.
