"""Dossier export API routes."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.dossier_export import DossierExport
from app.schemas.dossier_export import DossierExportCreateRequest, DossierExportResponse
from app.services.dossier_export import (
    DossierExportError,
    create_dossier_export,
    dossier_export_to_response,
)

router = APIRouter(tags=["dossier-exports"])


@router.post(
    "/dossiers/{dossier_id}/export",
    response_model=DossierExportResponse,
    status_code=201,
)
def export_dossier(
    dossier_id: str,
    payload: DossierExportCreateRequest,
    db: Session = Depends(get_db),
) -> DossierExportResponse:
    try:
        record = create_dossier_export(db, dossier_id, payload.format, payload.actor)
    except DossierExportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return dossier_export_to_response(record)


@router.get("/dossier-exports/{export_id}", response_model=DossierExportResponse)
def get_dossier_export(export_id: str, db: Session = Depends(get_db)) -> DossierExportResponse:
    record = db.scalar(select(DossierExport).where(DossierExport.export_id == export_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Export not found")
    return dossier_export_to_response(record)


@router.get("/dossier-exports/{export_id}/download")
def download_dossier_export(export_id: str, db: Session = Depends(get_db)) -> FileResponse:
    record = db.scalar(select(DossierExport).where(DossierExport.export_id == export_id))
    if record is None:
        raise HTTPException(status_code=404, detail="Export not found")
    path = Path(record.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Export file missing from storage")
    return FileResponse(
        path=path,
        media_type=record.content_type,
        filename=f"{record.dossier_id}_v{record.dossier_version}.{record.export_format}",
    )
