"""Integration tests for persistent requirements mapping and approval gates."""

from sqlalchemy import select

from app.models.audit_event import AuditEvent
from app.models.requirements_mapping import RequirementsMapping


def _valid_mapping_data() -> dict:
    return {
        "source": {
            "sourceId": "SRC-TEST-001",
            "title": "Public regulatory guidance",
            "authority": "Example regulator",
            "version": "2026-01",
            "url": "https://example.gov/regulatory-guidance",
            "approvalStatus": "APPROVED_FOR_REVIEW",
            "clauseId": "section-4.2",
            "excerpt": "The organization shall maintain an approved record.",
        },
        "obligation": "Maintain an approved and retrievable record.",
        "applicability": "APPLICABLE",
        "system": {
            "name": "Document Control System",
            "finding": "VERIFIED_GAP",
            "evidenceRef": "TEST-REPORT-001: control not configured",
        },
        "clarification": {
            "question": "",
            "decision": "SME confirmed this obligation applies to the named system.",
            "decisionStatus": "CONFIRMED",
            "owner": "Regulatory SME",
            "dependencyStatus": "NOT_REQUIRED",
        },
        "requirement": (
            "The system shall retain the approved record and provide retrieval evidence."
        ),
        "pbi": {
            "title": "Retain and retrieve approved records",
            "acceptanceCriteria": (
                "Given an approved record, when retrieval is requested, then the record "
                "and audit trail are returned."
            ),
            "testEvidence": "Automated test case TC-001 and execution report",
        },
    }


def test_create_mapping_persists_draft_and_audit_event(client, db_session) -> None:
    response = client.post(
        "/api/v1/requirements-mappings",
        json={
            "dossier_id": "DOS-MAP-001",
            "created_by": "qa.author",
            "data": _valid_mapping_data(),
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["mapping_key"].startswith("MAP-")
    assert body["readiness_status"] == "BLOCKED_DRAFT"
    assert body["review_status"] == "PENDING"
    assert "Independent reviewer approval is required" in body["blockers"]
    stored = db_session.scalar(
        select(RequirementsMapping).where(RequirementsMapping.id == body["id"])
    )
    assert stored is not None
    event = db_session.scalar(
        select(AuditEvent).where(
            AuditEvent.event_type == "requirements_mapping_create"
        )
    )
    assert event is not None
    assert event.actor == "qa.author"


def test_mapping_approval_requires_all_completeness_gates(client) -> None:
    data = _valid_mapping_data()
    data["clarification"]["decisionStatus"] = "OPEN"
    created = client.post(
        "/api/v1/requirements-mappings",
        json={
            "dossier_id": "DOS-MAP-002",
            "created_by": "qa.author",
            "data": data,
        },
    )
    assert created.status_code == 201
    response = client.post(
        f"/api/v1/requirements-mappings/{created.json()['id']}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Reviewed",
        },
        headers={"Authorization": "Bearer reviewer-test-key"},
    )
    assert response.status_code == 409
    assert "Interpretation must be confirmed" in response.json()["detail"]


def test_approved_mapping_is_ready_and_audited(client, db_session) -> None:
    created = client.post(
        "/api/v1/requirements-mappings",
        json={
            "dossier_id": "DOS-MAP-003",
            "created_by": "qa.author",
            "data": _valid_mapping_data(),
        },
    )
    assert created.status_code == 201
    mapping_id = created.json()["id"]
    reviewed = client.post(
        f"/api/v1/requirements-mappings/{mapping_id}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "SME evidence and criteria reviewed.",
        },
        headers={"Authorization": "Bearer reviewer-test-key"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["readiness_status"] == "READY_FOR_CONTROLLED_REVIEW"
    assert reviewed.json()["review_status"] == "APPROVED"
    assert reviewed.json()["reviewer"] == "qa.reviewer"
    stored = db_session.get(RequirementsMapping, mapping_id)
    assert stored is not None
    assert stored.readiness_status == "READY_FOR_CONTROLLED_REVIEW"
    events = list(
        db_session.scalars(
            select(AuditEvent).where(
                AuditEvent.event_type == "requirements_mapping_review"
            )
        ).all()
    )
    assert len(events) == 1
    assert events[0].actor == "qa.reviewer"


def test_mapping_can_be_filtered_by_dossier(client) -> None:
    for dossier_id in ("DOS-A", "DOS-B"):
        response = client.post(
            "/api/v1/requirements-mappings",
            json={
                "dossier_id": dossier_id,
                "created_by": "qa.author",
                "data": _valid_mapping_data(),
            },
        )
        assert response.status_code == 201
    response = client.get(
        "/api/v1/requirements-mappings",
        params={"dossier_id": "DOS-A"},
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["dossier_id"] == "DOS-A"


def test_mapping_not_found_returns_404(client) -> None:
    response = client.get("/api/v1/requirements-mappings/99999")
    assert response.status_code == 404


def test_writer_key_cannot_approve_mapping(client) -> None:
    created = client.post(
        "/api/v1/requirements-mappings",
        json={
            "dossier_id": "DOS-ROLE-001",
            "created_by": "qa.author",
            "data": _valid_mapping_data(),
        },
    )
    assert created.status_code == 201
    response = client.post(
        f"/api/v1/requirements-mappings/{created.json()['id']}/review",
        json={
            "reviewer": "qa.reviewer",
            "decision": "APPROVED",
            "rationale": "Should be rejected",
        },
    )
    assert response.status_code == 401


def test_mapping_api_fails_closed_when_writer_key_missing(
    client,
    monkeypatch,
) -> None:
    monkeypatch.delenv("MARAS_REQUIREMENTS_MAPPING_WRITE_KEY")
    response = client.post(
        "/api/v1/requirements-mappings",
        json={
            "dossier_id": "DOS-KEY-001",
            "created_by": "qa.author",
            "data": _valid_mapping_data(),
        },
    )
    assert response.status_code == 503
