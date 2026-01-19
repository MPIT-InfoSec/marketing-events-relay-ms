"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.routes import events, health

router = APIRouter()

# Health routes (no prefix, no auth)
router.include_router(health.router)

# Event routes (v1 prefix, auth required)
router.include_router(events.router, prefix="/v1")
