# Third-party notices

NovaSoft's application code is MIT licensed. Third-party libraries retain their own terms.
This source repository does not vendor npm/Python packages or Rust crate source code.
The lockfiles identify dependencies downloaded during installation.

Major dependencies include:

- FastAPI, SQLAlchemy, Alembic, Pydantic, React, React Router, Vite and Tailwind CSS (MIT).
- Uvicorn (BSD-3-Clause), asyncpg (Apache-2.0), bcrypt (Apache-2.0).
- Python multipart parsing (Apache-2.0) and PyJWT (MIT).
- Tauri (MIT or Apache-2.0) and its platform-specific dependencies.
- PostgreSQL (PostgreSQL License), downloaded separately as a Docker image.
- psycopg (LGPL-3.0-or-later), used by optional synchronous tooling; it is not vendored.
- OpenAI's Python SDK (Apache-2.0) for the optional DeepSeek-compatible API integration.

This is a summary, not a replacement for dependency licences. Before distributing built
installers or containers, include the notices and meet the obligations for the exact resolved
versions and target platform. This initial release distributes source only, not installers.
Upstream projects and service providers do not endorse or sponsor this project.
