"""Tests for evidence-based dossier export to PDF, DOCX, and TXT."""

import io
import zipfile
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.dossier_export import DossierExport
from app.services.dossier_export import (
    GAP_BLOCK_HEADER,
    WATERMARK,
    collect_approved_evidence,
    verify_content_excludes_pending_rejected,
)


def _upload_txt(client, content: bytes, filename: str = "source.txt") -> dict:
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": (filename, io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def _create_evidence(
    client,
    *,
    dossier_id: str,
    excerpt: str,
    ctd_section_code: str,
    doc_id: int | None = None,
    evidence_type: str = "DIRECT_EVIDENCE",
) -> dict:
    payload = {
        "dossier_id": dossier_id,
        "ctd_section_code": ctd_section_code,
        "exact_source_excerpt": excerpt,
        "evidence_type": evidence_type,
        "created_by": "cmc.author",
    }
    if doc_id is not None:
        payload["source_document_id"] = doc_id
        payload["page_number"] = 1
    response = client.post("/api/v1/evidence", json=payload)
    assert response.status_code == 201
    return response.json()


def _review(client, evidence_id: int, decision: str = "APPROVED") -> None:
    response = client.post(
        f"/api/v1/evidence/{evidence_id}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": decision,
            "rationale": f"Review decision: {decision}",
        },
    )
    assert response.status_code == 200


def _seed_mixed_evidence(client) -> dict[str, str]:
    doc = _upload_txt(client, b"Approved stability data for long-term shelf life")
    approved = _create_evidence(
        client,
        dossier_id="DOS-EXPORT-FILE",
        excerpt="Approved stability data for long-term",
        ctd_section_code="3.2.S.7.3",
        doc_id=doc["id"],
    )
    pending = _create_evidence(
        client,
        dossier_id="DOS-EXPORT-FILE",
        excerpt="PENDING_ONLY_EXCERPT_SHOULD_NOT_EXPORT",
        ctd_section_code="3.2.S.4.1",
        doc_id=doc["id"],
    )
    rejected = _create_evidence(
        client,
        dossier_id="DOS-EXPORT-FILE",
        excerpt="REJECTED_ONLY_EXCERPT_SHOULD_NOT_EXPORT",
        ctd_section_code="3.2.S.4.2",
        doc_id=doc["id"],
    )
    gap = _create_evidence(
        client,
        dossier_id="DOS-EXPORT-FILE",
        excerpt="Gap: validation protocol not supplied",
        ctd_section_code="3.2.S.4.3",
        evidence_type="GAP",
    )
    _review(client, approved["id"], "APPROVED")
    _review(client, gap["id"], "APPROVED")
    _review(client, rejected["id"], "REJECTED")
    return {
        "approved": approved["exact_source_excerpt"],
        "pending": pending["exact_source_excerpt"],
        "rejected": rejected["exact_source_excerpt"],
        "gap": gap["exact_source_excerpt"],
        "doc_filename": doc["filename"],
    }


def test_txt_export_excludes_pending_and_rejected(client, db_session) -> None:
    texts = _seed_mixed_evidence(client)
    response = client.post(
        "/api/v1/dossiers/DOS-EXPORT-FILE/export",
        json={"actor": "export.operator", "format": "txt"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["export_format"] == "txt"
    assert len(body["manifest"]["evidence_ids"]) == 2

    download = client.get(f"/api/v1/dossier-exports/{body['export_id']}/download")
    assert download.status_code == 200
    content = download.content
    assert verify_content_excludes_pending_rejected(
        content,
        approved_text=texts["approved"],
        pending_text=texts["pending"],
        rejected_text=texts["rejected"],
    )
    text = content.decode("utf-8")
    assert WATERMARK in text
    assert GAP_BLOCK_HEADER in text
    assert texts["gap"] in text
    assert texts["doc_filename"] in text
    assert "Export ID:" in text
    assert "Document hashes:" in text

    event = db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "dossier_export")
    )
    assert event is not None
    assert event.actor == "export.operator"

    stored = db_session.scalar(
        select(DossierExport).where(DossierExport.export_id == body["export_id"])
    )
    assert stored is not None
    assert Path(stored.storage_path).exists()


@pytest.mark.parametrize("export_format", ["docx", "pdf"])
def test_binary_export_excludes_pending_and_rejected(client, export_format) -> None:
    texts = _seed_mixed_evidence(client)
    response = client.post(
        "/api/v1/dossiers/DOS-EXPORT-FILE/export",
        json={"actor": "export.operator", "format": export_format},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["manifest"]["item_count"] == 2

    download = client.get(f"/api/v1/dossier-exports/{body['export_id']}/download")
    assert download.status_code == 200
    content = download.content
    assert len(content) > 100
    assert texts["pending"].encode() not in content
    assert texts["rejected"].encode() not in content

    if export_format == "docx":
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            doc_xml = archive.read("word/document.xml").decode("utf-8")
        assert texts["approved"] in doc_xml
        assert GAP_BLOCK_HEADER in doc_xml
        assert WATERMARK in doc_xml
        assert texts["pending"] not in doc_xml
        assert texts["rejected"] not in doc_xml


def test_ctd_sections_render_in_numeric_order(client) -> None:
    doc = _upload_txt(client, b"section content")
    early = _create_evidence(
        client,
        dossier_id="DOS-ORDER",
        excerpt="Later section evidence",
        ctd_section_code="3.2.S.4.2",
        doc_id=doc["id"],
    )
    first = _create_evidence(
        client,
        dossier_id="DOS-ORDER",
        excerpt="Earlier section evidence",
        ctd_section_code="3.2.S.4.1",
        doc_id=doc["id"],
    )
    _review(client, early["id"])
    _review(client, first["id"])

    response = client.post(
        "/api/v1/dossiers/DOS-ORDER/export",
        json={"actor": "export.operator", "format": "txt"},
    )
    assert response.status_code == 201
    content = client.get(
        f"/api/v1/dossier-exports/{response.json()['export_id']}/download"
    ).content.decode("utf-8")
    assert content.index("Earlier section evidence") < content.index("Later section evidence")


def test_export_requires_approved_evidence(client) -> None:
    _create_evidence(
        client,
        dossier_id="DOS-EMPTY",
        excerpt="Only pending item",
        ctd_section_code="3.2.S.1",
        doc_id=_upload_txt(client, b"x")["id"],
    )
    response = client.post(
        "/api/v1/dossiers/DOS-EMPTY/export",
        json={"actor": "export.operator", "format": "txt"},
    )
    assert response.status_code == 400


def test_collect_approved_evidence_only(client, db_session) -> None:
    texts = _seed_mixed_evidence(client)
    rows = collect_approved_evidence(db_session, "DOS-EXPORT-FILE")
    excerpts = {row.exact_source_excerpt for row in rows}
    assert texts["approved"] in excerpts
    assert texts["gap"] in excerpts
    assert texts["pending"] not in excerpts
    assert texts["rejected"] not in excerpts
