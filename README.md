# NovaSoft Support — Community Preview

An open-source IT support starter with ticketing, a technician dashboard, a desktop
client and optional AI triage. Built by NovaSoft with FastAPI, PostgreSQL, React and Tauri.

**v0.1.0 is a developer preview for local evaluation with fictional data.** It is not a
production-ready managed support service. Native repair actions are deliberately disabled.
No customer data, credentials, deployment configuration or model weights are included.

## What works

- End-user ticket creation, comments and attachment upload/metadata.
- Technician queue, assignment, status updates and internal notes.
- Admin client/user management and audit history.
- Five read-only diagnostic packs, with available fields varying by operating system.
- Deterministic mock AI triage with no API key or external model call.
- Optional DeepSeek integration, disabled unless explicitly enabled by the operator.
- Server-side ticket escalation. No remote shell or device repair commands.

The backend checks client membership and ticket/device ownership. Staff belong to one
support organisation and intentionally have access across its client companies.
See [security and limits](docs/security.md) before trying real deployments.

## Start locally

Requires Docker, Node.js 22+, and Python 3.12. Rust is only needed for the native desktop app.

```sh
git clone https://github.com/novasofttechnologiesau/novasoft-support.git
cd novasoft-support
python3 scripts/configure_local.py
docker compose up -d
python3 -m venv .venv
source .venv/bin/activate
pip install -r apps/api/requirements.txt
cd apps/api
alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In another terminal, from the repository root:

```sh
npm ci
npm run dev:web
```

Open <http://localhost:5173>. Demo accounts:

| Role | Email |
| --- | --- |
| Administrator | `admin@novasoft.example` |
| Technician | `tech@novasoft.example` |
| End user | `user@acme.example` |

All demo accounts use **your generated `DEMO_SEED_PASSWORD` from `apps/api/.env`**.
There is no published default password. The setup script generates private local database
and signing credentials and refuses to overwrite existing configuration.

For the end-user browser preview, run `npm run dev --workspace apps/desktop` and open
<http://localhost:1420>. Diagnostics in browser preview are explicitly simulated.
For native diagnostics, run `npm run dev:desktop`; see [setup](docs/setup.md).

## Release boundaries

- No signed installers or production hosting are supplied.
- Windows-specific diagnostic behavior still needs real Windows hardware validation.
- Native repair code is excluded; the UI cannot restart services, flush DNS or stop apps.
- Attachment download, session revocation, MFA, deployment rate limiting and malware
  scanning are not implemented. Uploaded files remain private on the backend filesystem.
- AI responses are suggestions and can be incorrect. Mock fallback is intended for demos.
- No promise of enterprise support, a support SLA or ongoing compatibility.

## Development and checks

```sh
npm ci
npm run build
```

Backend regression tests require a dedicated PostgreSQL database whose name ends in `_test`.
See [testing](docs/testing.md). GitHub Actions runs the backend tests, frontend builds and
native compilation checks; no customer systems or external AI calls are used.

- [Architecture](docs/architecture.md)
- [Setup](docs/setup.md)
- [Security](docs/security.md)
- [Diagnostics](docs/diagnostics.md)
- [Actions](docs/approved-actions.md)
- [Release audit](docs/release-audit.md)

## License and contribution

NovaSoft's application code is [MIT licensed](LICENSE). Dependencies keep their own
licences; see [third-party notices](THIRD_PARTY_NOTICES.md).
Bug reports, tests and small improvements are welcome; see [CONTRIBUTING.md](CONTRIBUTING.md).
For vulnerability reporting, see [SECURITY.md](SECURITY.md).
