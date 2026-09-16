from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.body_limit import BodyLimitMiddleware

app = FastAPI(title="NovaSoft Support API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(BodyLimitMiddleware, max_bytes=(settings.MAX_UPLOAD_MB + 1) * 1024 * 1024)

app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
