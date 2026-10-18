"""Regression tests for Layer 1 source truth and Layer 2 interpretation approval."""

from app.models.document import Document
from app.models.extracted_obligation import ExtractedObligation


def _source_fixture(db_session):
    document = Document(
        filename="regulation-v1.txt",
        content_type="text/plain",
        byte_size=90,
        file_hash="a" * 64,
        storage_path="/tmp/regulation-v1.txt",
        version=1,
        uploader="test",
        parse_status="EXTRACTED",
        text_excerpt="The manufacturer shall maintain complete batch records for every lot.",
    )
    db_session.add(document)
    db_session.flush()
    obligation = ExtractedObligation(
        obligation_key="OBL-LAYER12-TEST",
        source_document_id=document.id,
        source_version=1,
        source_file_hash=document.file_hash,
        clause_id="4.2",
        segment_index=1,
        excerpt="The manufacturer shall maintain complete batch records for every lot.",
        trigger_terms="shall, maintain",
        extraction_method="TEST_FIXTURE",
        confidence=0.5,
        status="APPROVED",
    )
    db_session.add(obligation)
    db_session.commit()
    return document, obligation


def test_layer1_source_must_be_verified_before_layer2_approval(client, db_session):
    document, obligation = _source_fixture(db_session)
    source_response = client.post(
        "/api/v1/requirements-mappings/regulatory-sources",
        json={
            "document_id": document.id,
            "title": "Good Manufacturing Practice Guidance",
            "issuing_authority": "Example Regulator",
            "jurisdiction": "Example Jurisdiction",
            "document_type": "Guidance",
            "official_url": "https://regulator.example/guidance",
            "version_label": "v1",
            "publication_date": "2025-01-01",
            "effective_date": "2025-02-01",
            "applicability_scope": "Manufacturing sites in this jurisdiction",
            "created_by": "source-curator",
        },
    )
    assert source_response.status_code == 201, source_response.text
    source = source_response.json()
    assert source["source_status"] == "UNVERIFIED"
    assert source["content_hash"] == document.file_hash

    decision_payload = {
        "obligation_id": obligation.id,
        "interpretation": "Batch records must be retained and retrievable for each manufactured lot.",
        "applicability": "APPLICABLE",
        "rationale": "The organisation manufactures products within the stated scope.",
        "assumptions": "The controlled manufacturing site is in the jurisdiction.",
        "unresolved_questions": "",
        "decision_owner": "Quality Owner",
        "submitted_by": "analyst",
    }
    decision_response = client.post(
        "/api/v1/requirements-mappings/interpretations", json=decision_payload
    )
    assert decision_response.status_code == 201, decision_response.text
    decision = decision_response.json()

    blocked = client.put(
        f"/api/v1/requirements-mappings/interpretations/{decision['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality-reviewer",
            "reviewer_role": "Quality SME",
            "decision": "APPROVED",
            "rationale": "Reviewed against the controlled source.",
        },
    )
    assert blocked.status_code == 409
    assert "Layer 1 source must be verified" in blocked.json()["detail"]

    verified = client.put(
        f"/api/v1/requirements-mappings/regulatory-sources/{source['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "regulatory-reviewer",
            "decision": "VERIFIED",
            "rationale": "Verified against the regulator's controlled publication.",
        },
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["source_status"] == "VERIFIED"

    # Hash integrity must be rechecked at the point of interpretation approval.
    document.file_hash = "b" * 64
    db_session.commit()
    hash_drift = client.put(
        f"/api/v1/requirements-mappings/interpretations/{decision['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality-reviewer",
            "reviewer_role": "Quality SME",
            "decision": "APPROVED",
            "rationale": "Approval must be blocked when source bytes drift.",
        },
    )
    assert hash_drift.status_code == 409
    assert "content changed after verification" in hash_drift.json()["detail"]
    document.file_hash = "a" * 64
    db_session.commit()

    self_approval = client.put(
        f"/api/v1/requirements-mappings/interpretations/{decision['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "analyst",
            "reviewer_role": "Quality SME",
            "decision": "APPROVED",
            "rationale": "Attempted self-approval should be blocked.",
        },
    )
    assert self_approval.status_code == 409
    assert "cannot approve their own" in self_approval.json()["detail"]

    approved = client.put(
        f"/api/v1/requirements-mappings/interpretations/{decision['id']}/review",
        headers={"Authorization": "Bearer reviewer-test-key"},
        json={
            "reviewer": "quality-reviewer",
            "reviewer_role": "Quality SME",
            "decision": "APPROVED",
            "rationale": "Interpretation reviewed and accepted for this organisation.",
        },
    )
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "APPROVED"
    assert approved.json()["reviewed_by"] == "quality-reviewer"


def test_layer1_rejects_non_https_urls(client):
    response = client.post(
        "/api/v1/requirements-mappings/regulatory-sources",
        json={
            "document_id": 1,
            "title": "Example guidance",
            "issuing_authority": "Example Regulator",
            "jurisdiction": "Example Jurisdiction",
            "document_type": "Guidance",
            "official_url": "http://not-secure.example/guidance",
            "version_label": "v1",
            "applicability_scope": "A defined regulated product scope",
            "created_by": "source-curator",
        },
    )
    assert response.status_code == 422
