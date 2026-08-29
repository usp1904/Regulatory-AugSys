"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.ctd_sections import router as ctd_sections_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(ctd_sections_router)
