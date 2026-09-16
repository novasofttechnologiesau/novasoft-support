# v0.1.0 release review — 16 September 2026

Scope: a clean source-only export of NovaSoft Support for local evaluation with fictional
records. Local configuration, assistant files, runtime data, build outputs and the original
private remote/history are excluded. This is a targeted release review, not a certification
or independent penetration test.

## Corrections made before publication

- Required random signing credentials and generated private local database/demo passwords.
- Bound the database to loopback and rejected placeholder signing secrets.
- Enforced ticket and device ownership across diagnostics, action history and AI routes.
- Checked linked devices/tickets/clients; prevented explicit-null assignment bypasses.
- Scoped knowledge retrieval and AI context to global/matching-client articles.
- Hid staff AI analysis from end-user responses; preserved internal note restrictions.
- Required explicit external-AI opt-in and expanded best-effort nested redaction.
- Excluded native repair implementations and command registrations. Only escalation runs.
- Added upload/request bounds, session-only token storage and native CSP.
- Removed automatic device-health collection at login and added snapshot consent.
- Updated dependencies identified by npm audit, pip-audit and cargo-audit.

## Local verification

- 14 PostgreSQL-backed/API regression tests passed.
- Fresh schema migration and fictional demo seeding passed.
- Configuration generation, owner-only file permissions and overwrite refusal passed.
- Both frontend production builds passed.
- macOS Tauri Rust compilation passed with the updated lockfile.
- Browser checks: administrator login/dashboard and end-user login/ticket submission passed.
- Gitleaks release-file scan: no findings.
- npm audit and pip-audit: no known vulnerabilities in the scanned dependency sets.
- cargo-audit: no entries in its vulnerability list after lockfile updates.

## Rust advisory limitations

Cargo still reports upstream informational warnings for unmaintained crates (`paste`,
`proc-macro-error` and several `unic-*` crates), plus the Linux GLib advisory
[RUSTSEC-2024-0429](https://rustsec.org/advisories/RUSTSEC-2024-0429.html).
The GLib dependency belongs to the Linux GUI stack; Linux native desktop builds are outside
this preview's supported/tested targets. Warnings are recorded rather than suppressed.
Check current upstream advisories before producing or distributing native binaries.

## Remaining boundaries

GitHub Actions checks the backend, frontends and macOS/Windows source compilation.
Compilation does not validate Windows device diagnostics. No Windows device repair tests,
real customer data, external AI calls, signed installers or public application hosting are
part of this release. See `security.md` for deployment gaps. Dependency scans are a snapshot
of known advisories and cannot establish that all vulnerabilities have been found.
