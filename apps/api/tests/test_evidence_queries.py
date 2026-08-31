"""Tests for shared approved evidence queries."""

from app.services.evidence_queries import list_approved_evidence_for_dossier


def test_list_approved_evidence_for_dossier_excludes_pending(client, db_session) -> None:
    import io

    from app.models.evidence_item import EvidenceItem

    doc = client.post(
        "/api/v1/documents",
        data={"uploader": "qa"},
        files={"file": ("t.txt", io.BytesIO(b"text"), "text/plain")},
    ).json()
    approved = client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-QUERY",
            "ctd_section_code": "3.2.S.4.1",
            "source_document_id": doc["id"],
            "page_number": 1,
            "exact_source_excerpt": "approved text",
            "evidence_type": "DIRECT_EVIDENCE",
            "created_by": "author",
        },
    ).json()
    client.post(
        "/api/v1/evidence",
        json={
            "dossier_id": "DOS-QUERY",
            "ctd_section_code": "3.2.S.4.2",
            "exact_source_excerpt": "pending only",
            "evidence_type": "GAP",
            "created_by": "author",
        },
    )
    client.post(
        f"/api/v1/evidence/{approved['id']}/review",
        json={"reviewer": "qa", "decision": "APPROVED", "rationale": "ok"},
    )

    items = list_approved_evidence_for_dossier(db_session, "DOS-QUERY")
    assert len(items) == 1
    assert items[0].review_status == "APPROVED"
    assert isinstance(items[0], EvidenceItem)
