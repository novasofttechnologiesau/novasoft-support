# Testing

Use Python 3.12, Node.js 22+ and a dedicated PostgreSQL database named with an `_test` suffix.
Never point these commands at a customer or production database. Tests create fictional records
inside rolled-back transactions; Alembic applies the schema to the dedicated database first.

```sh
pip install -r apps/api/requirements-dev.txt
cd apps/api
export TEST_DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@localhost:PORT/support_test'
export DATABASE_URL="$TEST_DATABASE_URL"
export JWT_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
alembic upgrade head
python -m pytest -q
```

From the repository root:

```sh
npm ci
npm run build
npm audit
cargo check --manifest-path apps/desktop/src-tauri/Cargo.toml --locked
```

API tests cover authentication/roles, ticket and device ownership, diagnostic association,
internal notes, client-scoped knowledge/AI context, disabled native actions, ticket escalation,
file limits, nested AI redaction and configuration validation. No real diagnostics, repairs or
external AI calls are executed by these tests.
