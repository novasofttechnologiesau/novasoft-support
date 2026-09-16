"""Create private local demo configuration without overwriting existing files."""
from pathlib import Path
import os
import secrets

root = Path(__file__).resolve().parents[1]
paths = [root / ".env", root / "apps/api/.env"]
if any(p.exists() for p in paths):
    raise SystemExit("Configuration already exists. Edit it manually; existing files were not changed.")
db_password = secrets.token_urlsafe(32)
root_env = f"POSTGRES_PASSWORD={db_password}\nPOSTGRES_PORT=5433\n"
api_env = (root / "apps/api/.env.example").read_text()
api_env = api_env.replace("DATABASE_URL=", f"DATABASE_URL=postgresql+asyncpg://novasoft:{db_password}@localhost:5433/novasoft_support", 1)
api_env = api_env.replace("JWT_SECRET=", f"JWT_SECRET={secrets.token_urlsafe(48)}", 1)
api_env = api_env.replace("DEMO_SEED_PASSWORD=", f"DEMO_SEED_PASSWORD={secrets.token_urlsafe(24)}", 1)
api_env = api_env.replace("ALLOW_DEMO_SEED=false", "ALLOW_DEMO_SEED=true")
for path, content in zip(paths, [root_env, api_env]):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as output:
        output.write(content)
print("Created private .env files. Find your demo login password in apps/api/.env.")
