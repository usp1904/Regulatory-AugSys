"""Tests for Story Map workspace API."""

from fastapi.testclient import TestClient


def test_create_story_map_with_hierarchy(client: TestClient) -> None:
    create_resp = client.post(
        "/api/v1/story-maps",
        json={
            "title": "Part 11 LIMS rollout",
            "template": "regulatory_compliance",
            "intent": "Map controls to release slices for SME review",
            "group_by": "outcome",
            "created_by": "qa.reviewer",
        },
    )
    assert create_resp.status_code == 201
    story_map = create_resp.json()
    map_id = story_map["id"]
    assert story_map["package_status"] == "DRAFT_NOT_CONTROLLED"
    assert story_map["map_key"].startswith("SM-")

    backbone_resp = client.post(
        f"/api/v1/story-maps/{map_id}/backbones",
        json={"title": "Audit trail controls", "sort_order": 0},
    )
    assert backbone_resp.status_code == 200
    backbone_id = backbone_resp.json()["backbones"][0]["id"]

    slice_resp = client.post(
        f"/api/v1/story-maps/{map_id}/release-slices",
        json={
            "name": "Wave 1 — MVP",
            "release_meaning": "mvp_value_increment",
            "description": "Initial validated increment",
            "sort_order": 0,
        },
    )
    assert slice_resp.status_code == 200
    release_slice_id = slice_resp.json()["release_slices"][0]["id"]

    story_resp = client.post(
        f"/api/v1/story-maps/{map_id}/stories",
        json={
            "title": "As QA lead I need immutable audit trails",
            "backbone_id": backbone_id,
            "release_slice_id": release_slice_id,
            "sort_order": 0,
            "group_key": "QA Lead",
            "owner": "qa.reviewer",
            "outcome_or_obligation": "21 CFR Part 11 audit trail",
            "acceptance_criteria": "Audit events are attributable and tamper-evident",
            "evidence_required": "IQ/OQ protocol excerpt",
            "risk": "Medium — legacy LIMS gaps",
            "dependency": "Vendor upgrade",
            "source_control_ref": "FDA Part 11",
            "status": "planned",
        },
    )
    assert story_resp.status_code == 201
    story_id = story_resp.json()["id"]

    link_resp = client.post(
        f"/api/v1/story-maps/stories/{story_id}/trace-links",
        json={
            "link_type": "ctd_section",
            "external_ref": "3.2.S.4.5",
            "label": "CTD 3.2.S.4.5 — justification of specification",
            "source_workspace": "ctd_ectd",
        },
    )
    assert link_resp.status_code == 201
    assert link_resp.json()["source_workspace"] == "ctd_ectd"

    export_resp = client.get(f"/api/v1/story-maps/{map_id}/export")
    assert export_resp.status_code == 200
    export = export_resp.json()
    assert export["schema_version"] == "maras.story-map.v1"
    assert export["package_status"] == "DRAFT_NOT_CONTROLLED"
    assert len(export["story_map"]["stories"]) == 1
    assert export["story_map"]["stories"][0]["trace_links"][0]["link_type"] == "ctd_section"


def test_reorder_stories(client: TestClient) -> None:
    create_resp = client.post(
        "/api/v1/story-maps",
        json={
            "title": "Reorder test",
            "template": "feature_breakdown",
            "created_by": "tester",
        },
    )
    map_id = create_resp.json()["id"]

    ids = []
    for index, title in enumerate(["Story A", "Story B", "Story C"]):
        resp = client.post(
            f"/api/v1/story-maps/{map_id}/stories",
            json={"title": title, "sort_order": index},
        )
        ids.append(resp.json()["id"])

    reorder_resp = client.post(
        f"/api/v1/story-maps/{map_id}/stories/reorder",
        json={"story_ids": [ids[2], ids[0], ids[1]]},
    )
    assert reorder_resp.status_code == 200
    titles = [s["title"] for s in reorder_resp.json()["stories"]]
    assert titles == ["Story C", "Story A", "Story B"]


def test_linkable_sources(client: TestClient) -> None:
    resp = client.get("/api/v1/story-maps/linkable-sources")
    assert resp.status_code == 200
    data = resp.json()
    assert "ctd_sections" in data
    assert "evidence_items" in data
    assert len(data["ctd_sections"]) > 0


def test_update_story_status(client: TestClient) -> None:
    create_resp = client.post(
        "/api/v1/story-maps",
        json={
            "title": "Status test",
            "template": "outcome_oriented",
            "created_by": "tester",
        },
    )
    map_id = create_resp.json()["id"]
    story_resp = client.post(
        f"/api/v1/story-maps/{map_id}/stories",
        json={"title": "Outcome story", "status": "planned"},
    )
    story_id = story_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/story-maps/stories/{story_id}",
        json={"status": "completed"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "completed"
