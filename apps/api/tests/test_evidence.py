"""Tests for evidence capture, review, versioning, and export."""

import io

from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.document import Document, DocumentPage


def _upload_txt(client, content: bytes, filename: str = "source.txt") -> dict:
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.tester"},
        files={"file": (filename, io.BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()


def test_create_evidence_from_document(client, db_session) -> None:
    doc = _upload_txt(client, b"Stability data long-term accelerated shelf life study")
    response = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-2026-001",
            "ctd_section_code": "3.2.S.7.3",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "Stability data long-term accelerated",
            "normalized_summary": "Stability study excerpt",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "cmc.author",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["review_status"] == "PENDING"
    assert body["source_document_version"] == doc["version"]
    assert body["excerpt_locked"] is False

    event = db_session.scalar(
        select(AuditEvent).where(AuditEvent.event_type == "evidence_create")
    )
    assert event is not None
    assert event.evidence_id == body["id"]


def test_approve_evidence_locks_excerpt(client) -> None:
    doc = _upload_txt(client, b"Specification acceptance criterion for assay")
    created = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-2026-001",
            "ctd_section_code": "3.2.S.4.1",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "Specification acceptance criterion",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "cmc.author",
        },
    ).json()
    reviewed = client.post(
        f"/api/v1/evidence/{created['id']}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Excerpt matches source page 1.",
        },
    )
    assert reviewed.status_code == 200
    body = reviewed.json()
    assert body["review_status"] == "APPROVED"
    assert body["excerpt_locked"] is True


def test_changing_approved_excerpt_creates_new_version(client) -> None:
    doc = _upload_txt(client, b"Impurity profile for degradants")
    created = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-2026-002",
            "ctd_section_code": "3.2.S.3.2",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "Impurity profile",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "cmc.author",
        },
    ).json()
    evidence_id = created["id"]
    client.post(
        f"/api/v1/evidence/{evidence_id}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Approved.",
        },
    )
    updated = client.patch(
        f"/api/v1/evidence/{evidence_id}",
        json={
            "actor": "cmc.author",
            "exact_source_excerpt": "Impurity profile revised wording",
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["evidence_version"] == 2
    assert body["review_status"] == "PENDING"
    assert body["supersedes_id"] == evidence_id


def test_export_includes_only_approved(client) -> None:
    doc = _upload_txt(client, b"Batch analyses for release")
    approved = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-EXPORT-1",
            "ctd_section_code": "3.2.S.4.4",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "Batch analyses",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "cmc.author",
        },
    ).json()
    client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-EXPORT-1",
            "ctd_section_code": "3.2.S.4.4",
            "exact_source_excerpt": "Missing validation protocol",
            "normalized_summary": "Gap: validation protocol not supplied",
            "evidence_type": "GAP",
            "created_by": "cmc.author",
        },
    )
    client.post(
        f"/api/v1/evidence/{approved['id']}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Approved batch analyses excerpt.",
        },
    )
    gap = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-EXPORT-1",
            "ctd_section_code": "3.2.S.4.3",
            "source_document_id": doc["id"],
            "exact_source_excerpt": "Confidential vendor method unavailable",
            "evidence_type": "CONFIDENTIAL_REFERENCE",
            "created_by": "cmc.author",
        },
    ).json()
    assert "id" in gap
    client.post(
        f"/api/v1/evidence/{gap['id']}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Approved gap statement.",
        },
    )

    export = client.get("/api/v1/evidence/export", params={"dossier_id": "DOS-EXPORT-1"})
    assert export.status_code == 200
    payload = export.json()
    assert payload["package_status"] == "DRAFT_NOT_CONTROLLED"
    assert len(payload["items"]) == 2
    labels = {item["export_label"] for item in payload["items"]}
    assert "APPROVED_EVIDENCE" in labels
    assert "CONTROLLED_GAP_STATEMENT" in labels
    assert len(payload["items"]) == len(labels)


def test_review_context_returns_source_text(client, db_session) -> None:
    doc = _upload_txt(client, b"Page one stability text here")
    document = db_session.get(Document, doc["id"])
    db_session.add(
        DocumentPage(
            document_id=document.id,
            page_number=1,
            text_content="Page one stability text here",
        )
    )
    db_session.commit()

    evidence = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-CTX-1",
            "ctd_section_code": "3.2.S.7.3",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "Page one stability",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "cmc.author",
        },
    ).json()
    context = client.get(f"/api/v1/evidence/{evidence['id']}/review-context")
    assert context.status_code == 200
    body = context.json()
    assert "stability" in body["source_text"].lower()
