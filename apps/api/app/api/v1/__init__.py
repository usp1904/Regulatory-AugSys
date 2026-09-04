"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.agents import router as agents_router
from app.api.v1.ctd_engine import router as ctd_engine_router
from app.api.v1.ctd_sections import router as ctd_sections_router
from app.api.v1.documents import router as documents_router
from app.api.v1.dossier_exports import router as dossier_exports_router
from app.api.v1.evidence import router as evidence_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(ctd_sections_router)
api_v1_router.include_router(documents_router)
api_v1_router.include_router(ctd_engine_router)
api_v1_router.include_router(evidence_router)
api_v1_router.include_router(dossier_exports_router)
api_v1_router.include_router(agents_router)
