"""Tests for document storage and CTD engine validation API."""

import io
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentPage
from app.services.ctd_validation import validate_ctd_documents

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_upload_document(client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    content = b"stability data long-term accelerated shelf life specification"
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": ("stability-report.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "stability-report.txt"
    assert body["parse_status"] == "EXTRACTED"
    assert "stability" in (body["text_excerpt"] or "")


def test_list_documents(client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={
            "file": (
                "spec.txt",
                io.BytesIO(b"specification acceptance criterion"),
                "text/plain",
            )
        },
    )
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    assert len(response.json()["documents"]) >= 1


def test_ctd_engine_validate(client, db_session: Session, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    doc = Document(
        filename="stability.txt",
        content_type="text/plain",
        byte_size=48,
        file_hash="abc123" * 5 + "abcd",
        storage_path=str(tmp_path / "stability.txt"),
        version=1,
        uploader="qa.tester",
        parse_status="EXTRACTED",
        text_excerpt="stability data long-term accelerated shelf life",
    )
    db_session.add(doc)
    db_session.flush()
    db_session.add(
        DocumentPage(
            document_id=doc.id,
            page_number=1,
            text_content="stability data long-term accelerated shelf life",
        )
    )
    db_session.commit()
    db_session.refresh(doc)

    response = client.post(
        "/api/v1/ctd-engine/validate",
        json={
            "document_ids": [doc.id],
            "frameworks": ["FDA"],
            "jurisdictions": ["United States"],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["schemaVersion"] == "maras.ctd-mapping.v1"
    assert body["packageStatus"] == "DRAFT_NOT_CONTROLLED"
    assert any(m["ctdSection"] == "3.2.S.7.3" for m in body["mappings"])


def test_validate_ctd_documents_leaf_coverage() -> None:
    doc = Document(
        filename="impurities.txt",
        content_type="text/plain",
        byte_size=42,
        file_hash="imp" + "0" * 61,
        storage_path="/tmp/impurities.txt",
        version=1,
        uploader="qa.tester",
        parse_status="EXTRACTED",
        text_excerpt="impurity degradant genotoxic impurity profile",
    )
    doc.pages = []
    result = validate_ctd_documents([doc], ["ICH"], ["Multi-Regional"])
    sections = {m["ctdSection"] for m in result["mappings"]}
    assert "3.2.S.3.2" in sections
    assert result["metrics"]["houseDocCount"] == 1
