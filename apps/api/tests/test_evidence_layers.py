"""Regression tests for regulatory source truth and approved interpretation."""

import io

from app.models.approved_interpretation import ApprovedInterpretation
from app.models.regulatory_source import RegulatorySource


def _source_document(client) -> int:
    text = (
        "Section 4.2: The organisation shall maintain a controlled record "
        "of each approved procedure and retain it for the required period."
    )
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "source.author"},
        files={"file": ("guidance.txt", io.BytesIO(text.encode()), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def _register_source(client) -> dict:
    response = client.post(
        "/api/v1/evidence-layers/sources",
        json={
            "document_id": _source_document(client),
            "authority": "Example Regulatory Authority",
            "jurisdiction": "Example jurisdiction",
            "source_type": "REGULATION",
            "title": "Records control guidance",
            "official_url": "https://example.gov/guidance/records",
            "source_version_label": "Version 1.2",
            "publication_date": "2026-01-01",
            "effective_date": "2026-02-01",
            "review_due_date": "2027-02-01",
            "clause_id": "4.2",
            "excerpt": "Section 4.2: The organisation shall maintain a controlled record of each approved procedure and retain it for the required period.",
            "created_by": "source.author",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_layer_one_preserves_provenance_and_requires_review(client):
    source = _register_source(client)
    assert source["source_status"] == "PENDING_REVIEW"
    assert source["currentness_status"] == "UNVERIFIED"
    assert source["document_version"] == 1
    assert len(source["file_hash"]) == 64
    assert source["clause_id"] == "4.2"

    rejected_excerpt = client.post(
        "/api/v1/evidence-layers/sources",
        json={
            "document_id": source["document_id"],
            "authority": "Example Regulatory Authority",
            "jurisdiction": "Example jurisdiction",
            "source_type": "REGULATION",
            "title": "Incorrect excerpt",
            "official_url": "https://example.gov/guidance/records",
            "source_version_label": "Version 1.2",
            "clause_id": "4.3",
            "excerpt": "This text is not in the controlled document at all.",
            "created_by": "source.author",
        },
    )
    assert rejected_excerpt.status_code == 400
    assert "exactly match" in rejected_excerpt.json()["detail"]

    reviewed = client.post(
        f"/api/v1/evidence-layers/sources/{source['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "regulatory.reviewer",
            "decision": "APPROVED",
            "rationale": "Checked against the nominated official publication.",
            "currentness_status": "CURRENT_VERIFIED",
        },
    )
    assert reviewed.status_code == 200, reviewed.text
    assert reviewed.json()["source_status"] == "APPROVED"
    assert reviewed.json()["currentness_status"] == "CURRENT_VERIFIED"


def test_layer_two_requires_approved_current_source_and_independent_confirmation(client, db_session):
    source = _register_source(client)
    interpretation_payload = {
        "source_id": source["id"],
        "interpretation": "The organisation must retain approved procedure records for the applicable retention period.",
        "applicability": "APPLICABLE",
        "rationale": "The controlled process creates and retains approved procedures within this organisation.",
        "decision_owner": "quality.owner",
        "created_by": "analyst",
    }
    blocked = client.post(
        "/api/v1/evidence-layers/interpretations",
        json=interpretation_payload,
    )
    assert blocked.status_code == 400
    assert "approved regulatory source" in blocked.json()["detail"]

    approved = client.post(
        f"/api/v1/evidence-layers/sources/{source['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "regulatory.reviewer",
            "decision": "APPROVED",
            "rationale": "Source identity checked; currentness not yet verified.",
            "currentness_status": "UNVERIFIED",
        },
    )
    assert approved.status_code == 200
    created = client.post("/api/v1/evidence-layers/interpretations", json=interpretation_payload)
    assert created.status_code == 201, created.text
    item = created.json()
    assert item["status"] == "DRAFT"

    not_current = client.post(
        f"/api/v1/evidence-layers/interpretations/{item['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality.reviewer",
            "decision": "CONFIRMED",
            "rationale": "Interpretation reviewed against the source.",
        },
    )
    assert not_current.status_code == 409
    assert "currentness is verified" in not_current.json()["detail"]

    source_review = client.post(
        f"/api/v1/evidence-layers/sources/{source['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "regulatory.reviewer",
            "decision": "APPROVED",
            "rationale": "Verified against the current official publication.",
            "currentness_status": "CURRENT_VERIFIED",
        },
    )
    # A reviewed source is deliberately immutable; a correction requires a new source record.
    assert source_review.status_code == 409

    # Register a new source with verified currentness for the confirmation path.
    source2 = client.post(
        "/api/v1/evidence-layers/sources",
        json={
            "document_id": source["document_id"],
            "authority": "Example Regulatory Authority",
            "jurisdiction": "Example jurisdiction",
            "source_type": "REGULATION",
            "title": "Records control guidance current copy",
            "official_url": "https://example.gov/guidance/records",
            "source_version_label": "Version 1.2",
            "clause_id": "4.2-current",
            "excerpt": "Section 4.2: The organisation shall maintain a controlled record of each approved procedure and retain it for the required period.",
            "created_by": "source.author",
        },
    )
    assert source2.status_code == 201, source2.text
    source2_review = client.post(
        f"/api/v1/evidence-layers/sources/{source2.json()['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "regulatory.reviewer",
            "decision": "APPROVED",
            "rationale": "Verified against the current official publication.",
            "currentness_status": "CURRENT_VERIFIED",
        },
    )
    assert source2_review.status_code == 200
    payload2 = {**interpretation_payload, "source_id": source2.json()["id"]}
    confirmed_item = client.post("/api/v1/evidence-layers/interpretations", json=payload2)
    assert confirmed_item.status_code == 201
    self_approval = client.post(
        f"/api/v1/evidence-layers/interpretations/{confirmed_item.json()['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality.owner",
            "decision": "CONFIRMED",
            "rationale": "Reviewed.",
        },
    )
    assert self_approval.status_code == 409
    confirmed = client.post(
        f"/api/v1/evidence-layers/interpretations/{confirmed_item.json()['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality.reviewer",
            "decision": "CONFIRMED",
            "rationale": "Interpretation reviewed and confirmed independently.",
        },
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "CONFIRMED"
    stored = db_session.get(ApprovedInterpretation, confirmed_item.json()["id"])
    assert stored is not None
    assert stored.reviewer == "quality.reviewer"


def test_duplicate_clause_and_source_version_is_rejected(client):
    source = _register_source(client)
    duplicate = client.post(
        "/api/v1/evidence-layers/sources",
        json={
            "document_id": source["document_id"],
            "authority": "Example Regulatory Authority",
            "jurisdiction": "Example jurisdiction",
            "source_type": "REGULATION",
            "title": "Duplicate clause",
            "official_url": "https://example.gov/guidance/records",
            "source_version_label": "Version 1.2",
            "clause_id": "4.2",
            "excerpt": "Section 4.2: The organisation shall maintain a controlled record of each approved procedure and retain it for the required period.",
            "created_by": "source.author",
        },
    )
    assert duplicate.status_code == 500 or duplicate.status_code == 409
