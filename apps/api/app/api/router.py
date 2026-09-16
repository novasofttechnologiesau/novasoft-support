from fastapi import APIRouter

from app.api.routes import actions, admin, ai, auth, diagnostics, knowledge, tickets

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(tickets.router)
api_router.include_router(diagnostics.router)
api_router.include_router(ai.router)
api_router.include_router(actions.router)
api_router.include_router(admin.router)
api_router.include_router(knowledge.router)
