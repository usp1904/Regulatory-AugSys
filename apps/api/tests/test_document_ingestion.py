"""Unit and integration tests for controlled document ingestion."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.document import DocumentPage
from app.services.document_extraction import (
    extract_docx_paragraphs,
    extract_pdf_pages,
    extract_txt_pages,
)
from app.services.document_storage import DocumentValidationError, validate_upload_metadata
from tests.fixture_factory import write_sample_docx, write_sample_pdf

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture()
def ingestion_env(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))
    from app.core.config import get_settings

    get_settings.cache_clear()
    return tmp_path


@pytest.fixture()
def ingestion_env_small(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_ROOT", str(tmp_path / "storage"))
    monkeypatch.setenv("MAX_UPLOAD_BYTES", "2048")
    from app.core.config import get_settings

    get_settings.cache_clear()
    return tmp_path


def test_validate_upload_metadata_rejects_unsupported_mime(ingestion_env_small) -> None:
    with pytest.raises(DocumentValidationError, match="Unsupported media type"):
        validate_upload_metadata("report.exe", "application/octet-stream", 10)


def test_validate_upload_metadata_rejects_oversize(ingestion_env_small) -> None:
    from app.core.config import get_settings

    limit = get_settings().max_upload_bytes
    with pytest.raises(DocumentValidationError, match="maximum size"):
        validate_upload_metadata("report.txt", "text/plain", limit + 1)


def test_validate_upload_metadata_rejects_extension_mismatch(ingestion_env_small) -> None:
    with pytest.raises(DocumentValidationError, match="does not match"):
        validate_upload_metadata("report.pdf", "text/plain", 10)


def test_extract_txt_pages_reads_utf8() -> None:
    result = extract_txt_pages(b"Hello controlled document")
    assert result.status == "EXTRACTED"
    assert result.pages == ["Hello controlled document"]


def test_extract_pdf_pages_from_fixture() -> None:
    data = (FIXTURES / "sample.pdf").read_bytes()
    result = extract_pdf_pages(data)
    assert result.status == "EXTRACTED"
    assert len(result.pages) == 2
    assert "stability" in result.pages[0].lower()


def test_extract_docx_paragraphs_from_fixture() -> None:
    data = (FIXTURES / "sample.docx").read_bytes()
    result = extract_docx_paragraphs(data)
    assert result.status == "EXTRACTED"
    assert len(result.paragraphs) == 2
    assert "nomenclature" in result.paragraphs[0].lower()


def test_upload_txt_creates_audit_and_page(client, ingestion_env, db_session) -> None:
    content = (FIXTURES / "sample.txt").read_bytes()
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": ("sample.txt", io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["parse_status"] == "EXTRACTED"
    assert body["uploader"] == "qa.tester"
    assert body["version"] == 1
    assert body["byte_size"] == len(content)
    assert len(body["file_hash"]) == 64

    pages = db_session.scalars(
        select(DocumentPage).where(DocumentPage.document_id == body["id"])
    ).all()
    assert len(pages) == 1
    assert "specification" in pages[0].text_content

    events = db_session.scalars(
        select(AuditEvent).where(AuditEvent.document_id == body["id"])
    ).all()
    event_types = {event.event_type for event in events}
    assert {"upload", "extraction_success"}.issubset(event_types)


def test_upload_pdf_extracts_pages(client, ingestion_env) -> None:
    content = (FIXTURES / "sample.pdf").read_bytes()
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "ra.reviewer"},
        files={"file": ("sample.pdf", io.BytesIO(content), "application/pdf")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["parse_status"] == "EXTRACTED"

    detail = client.get(f"/api/v1/documents/{body['id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["pages"]) == 2
    assert detail_body["paragraphs"] == []


def test_upload_docx_extracts_paragraphs(client, ingestion_env) -> None:
    content = (FIXTURES / "sample.docx").read_bytes()
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "cmc.author"},
        files={
            "file": (
                "sample.docx",
                io.BytesIO(content),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 201
    detail = client.get(f"/api/v1/documents/{response.json()['id']}")
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["paragraphs"]) == 2
    assert detail_body["pages"] == []


def test_document_detail_and_download(client, ingestion_env) -> None:
    content = b"Downloadable controlled text"
    upload = client.post(
        "/api/v1/documents",
        data={"uploader": "records.manager"},
        files={"file": ("download-me.txt", io.BytesIO(content), "text/plain")},
    )
    document_id = upload.json()["id"]

    download = client.get(f"/api/v1/documents/{document_id}/download")
    assert download.status_code == 200
    assert download.content == content


def test_deletion_request_audit_event(client, ingestion_env, db_session) -> None:
    upload = client.post(
        "/api/v1/documents",
        data={"uploader": "records.manager"},
        files={"file": ("delete-me.txt", io.BytesIO(b"delete"), "text/plain")},
    )
    document_id = upload.json()["id"]
    response = client.post(
        f"/api/v1/documents/{document_id}/deletion-request",
        json={"actor": "records.manager", "reason": "Superseded by v2"},
    )
    assert response.status_code == 204

    event = db_session.scalar(
        select(AuditEvent)
        .where(AuditEvent.document_id == document_id)
        .where(AuditEvent.event_type == "deletion_request")
    )
    assert event is not None
    assert event.actor == "records.manager"


def test_version_increments_for_same_filename(client, ingestion_env) -> None:
    first = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": ("versioned.txt", io.BytesIO(b"version one"), "text/plain")},
    )
    second = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": ("versioned.txt", io.BytesIO(b"version two"), "text/plain")},
    )
    assert first.json()["version"] == 1
    assert second.json()["version"] == 2


def test_fixture_factory_generates_binary_samples() -> None:
    pdf = write_sample_pdf()
    docx = write_sample_docx()
    assert pdf.startswith(b"%PDF")
    assert docx.startswith(b"PK")
