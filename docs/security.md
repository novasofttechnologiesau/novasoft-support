# Security model and limits

This is a local developer preview for fictional data. The release review fixes identified
issues and adds regression checks; it is not an independent penetration test or a guarantee
that the application is free of vulnerabilities.

## Authentication and access

- No public signup. Administrators create users. Password creation enforces 12–72 UTF-8 bytes;
  passwords use bcrypt hashes. JWT signing requires a non-placeholder random secret.
- Tokens require subject, issue time and expiration; HS256 is the only accepted algorithm.
  The API loads current user role and active status from the database on each request.
- Tokens live in frontend session storage. Logout removes the local token and records an
  audit event, but does not revoke copied tokens; they expire after 30 minutes by default.
- End users access their own tickets, devices, diagnostics, attachments and action history.
  Internal notes and detailed AI technician analysis remain staff-only.
- Knowledge articles are global or scoped to a client. AI context uses global and matching
  client articles only. Staff intentionally serve all clients in one support organisation.
- This is not an isolation model for multiple independent support providers sharing an API.

## Device boundary

Only five read-only diagnostic commands are registered with Tauri. Native repair
implementations and command registrations are excluded from this version. Backend action
checks reject unavailable handlers even if a stale database row enables them.
The only implemented action is server-side ticket escalation, validated against ticket
and device ownership and matching client/device associations.

Diagnostic consent is a user-interface control, not an OS security boundary. Do not run an
untrusted frontend inside the desktop shell. The native CSP restricts scripts to bundled
assets and API calls to the configured loopback service. There is no generic shell bridge.

## AI

Mock triage is the default. External AI requires `ALLOW_EXTERNAL_AI=true` plus provider and
key configuration. Input stays untrusted even when it came from a database. The system prompt
asks for allowlisted suggestions, but prompts are not security enforcement. No AI response
can invoke a native action. Backend allowlist checks are independent of recommendations.
Best-effort redaction covers nested text and known credential fields, but cannot guarantee
that arbitrary ticket text or diagnostics contain no personal information. See setup for
exactly what may be transmitted. Provider exceptions are not logged with raw response bodies.

## Uploads and deployment

Uploads use generated storage names, an extension allowlist and a per-file size limit.
A whole-request cap applies before JSON/multipart parsing, including chunked request bodies.
Uploads are not executable assets and there is no unauthenticated download/static route.
Extension checks are not malware scanning. Plan scanning, retention and authenticated
file download before using attachments operationally.

The development database binds only to loopback. Configuration and demo login passwords are
randomly generated and stored in ignored, owner-readable local files. No private deployment
history, credentials, uploads or local assistant configuration are included in Git.

## Known production gaps

This release has no MFA, durable token revocation, login throttling, per-user storage quotas,
backup/recovery workflow, malware scanning or tested public deployment configuration.
Diagnostic fields are incomplete; device identity is self-reported and is not hardware-attested.
There is no real Windows device validation or signed installer release. Review these controls,
TLS, proxy limits, tenancy and retention requirements before considering real client data.
