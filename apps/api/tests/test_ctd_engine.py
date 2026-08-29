"""Tests for document storage and CTD engine validation API."""

import io

from app.models.document import Document
from app.services.ctd_validation import validate_ctd_documents


def test_upload_document(client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    content = b"stability data long-term accelerated shelf life specification"
    response = client.post(
        "/api/v1/documents",
        files={"file": ("stability-report.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["filename"] == "stability-report.txt"
    assert body["parse_status"] == "PARSED"
    assert "stability" in (body["text_excerpt"] or "")


def test_list_documents(client, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    from app.core.config import get_settings

    get_settings.cache_clear()

    client.post(
        "/api/v1/documents",
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


def test_ctd_engine_validate(client, db_session, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path))
    doc = Document(
        filename="stability.txt",
        content_type="text/plain",
        file_hash="abc123",
        storage_path=str(tmp_path / "stability.txt"),
        parse_status="PARSED",
        text_excerpt="stability data long-term accelerated shelf life",
    )
    db_session.add(doc)
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
        file_hash="imp",
        storage_path="/tmp/impurities.txt",
        parse_status="PARSED",
        text_excerpt="impurity degradant genotoxic impurity profile",
    )
    result = validate_ctd_documents([doc], ["ICH"], ["Multi-Regional"])
    sections = {m["ctdSection"] for m in result["mappings"]}
    assert "3.2.S.3.2" in sections
    assert result["metrics"]["houseDocCount"] == 1
