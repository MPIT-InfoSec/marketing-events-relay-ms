"""Admin API v1 router."""

from fastapi import APIRouter

from app.api.admin.v1.routes import credentials, platforms, sgtm_configs, storefronts

router = APIRouter(prefix="/admin/v1")

router.include_router(storefronts.router)
router.include_router(sgtm_configs.router)
router.include_router(platforms.router)
router.include_router(credentials.router)
