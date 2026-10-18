"""Integration tests for source-linked obligation extraction."""

import io

from fastapi.testclient import TestClient


def _upload_regulatory_text(client: TestClient) -> int:
    text = (
        "2.1 The organization shall maintain an approved record. "
        "The system may provide a dashboard."
    )
    response = client.post(
        "/api/v1/documents",
        data={"uploader": "qa.author"},
        files={"file": ("regulatory-test.txt", io.BytesIO(text.encode()), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_obligation_extraction_is_source_linked_and_idempotent(client: TestClient) -> None:
    document_id = _upload_regulatory_text(client)
    first = client.post(
        f"/api/v1/requirements-mappings/obligations/extract/{document_id}",
        json={"requested_by": "qa.author"},
    )
    assert first.status_code == 200
    assert len(first.json()) == 1
    candidate = first.json()[0]
    assert candidate["clause_id"] == "2.1"
    assert candidate["status"] == "DRAFT"
    assert candidate["source_document_id"] == document_id
    assert len(candidate["source_file_hash"]) == 64
    assert candidate["extraction_method"] == "RULE_BASED_V1"

    second = client.post(
        f"/api/v1/requirements-mappings/obligations/extract/{document_id}",
        json={"requested_by": "qa.author"},
    )
    assert second.status_code == 200
    assert [item["obligation_key"] for item in second.json()] == [candidate["obligation_key"]]


def test_approved_obligation_creates_traceable_mapping_draft(client: TestClient) -> None:
    document_id = _upload_regulatory_text(client)
    extracted = client.post(
        f"/api/v1/requirements-mappings/obligations/extract/{document_id}",
        json={"requested_by": "qa.author"},
    )
    candidate_id = extracted.json()[0]["id"]
    reviewed = client.put(
        f"/api/v1/requirements-mappings/obligations/{candidate_id}/review",
        json={
            "reviewer": "regulatory.sme",
            "decision": "APPROVED",
            "rationale": "The excerpt expresses an explicit normative obligation.",
        },
        headers={"Authorization": "Bearer reviewer-test-key"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "APPROVED"

    created = client.post(
        f"/api/v1/requirements-mappings/obligations/{candidate_id}/create-mapping",
        params={"created_by": "qa.author"},
    )
    assert created.status_code == 200
    mapping = created.json()
    assert mapping["data"]["source"]["sourceDocumentId"] == document_id
    assert mapping["data"]["source"]["clauseId"] == "2.1"
    assert mapping["data"]["obligation"] == (
        "2.1 The organization shall maintain an approved record."
    )

    listed = client.get(
        "/api/v1/requirements-mappings/obligations",
        params={"document_id": document_id},
    )
    assert listed.status_code == 200
    assert listed.json()[0]["mapping_id"] == mapping["id"]
