"""Tests for CTD Module 3.2.S taxonomy seed and API."""

from sqlalchemy import select

from app.data.ctd_module_32s import CTD_MODULE_32S_SEED
from app.models.ctd_section import CtdSection


def test_seed_codes_are_unique() -> None:
    codes = [row["code"] for row in CTD_MODULE_32S_SEED]
    assert len(codes) == len(set(codes)), "duplicate codes in seed data"


def test_seed_every_child_has_valid_parent() -> None:
    codes = {row["code"] for row in CTD_MODULE_32S_SEED}
    for row in CTD_MODULE_32S_SEED:
        parent_code = row["parent_code"]
        if parent_code is None:
            continue
        assert parent_code in codes, f"{row['code']} references missing parent {parent_code!r}"


def test_database_seed_codes_unique(db_session) -> None:
    sections = db_session.scalars(select(CtdSection)).all()
    codes = [s.code for s in sections]
    assert len(codes) == len(set(codes))


def test_database_every_child_has_valid_parent(db_session) -> None:
    sections = db_session.scalars(select(CtdSection)).all()
    by_id = {s.id: s for s in sections}
    for section in sections:
        if section.parent_id is None:
            assert section.code == "3.2.S"
            continue
        assert section.parent_id in by_id
        parent = by_id[section.parent_id]
        assert section.code.startswith(parent.code + ".")


def test_api_ctd_sections_returns_tree(client) -> None:
    response = client.get("/api/v1/ctd-sections")
    assert response.status_code == 200
    body = response.json()
    assert body["module"] == "3.2.S"
    assert len(body["sections"]) == 1
    root = body["sections"][0]
    assert root["code"] == "3.2.S"
    assert root["title"] == "Drug Substance"
    child_codes = {c["code"] for c in root["children"]}
    assert child_codes == {
        "3.2.S.1",
        "3.2.S.2",
        "3.2.S.3",
        "3.2.S.4",
        "3.2.S.5",
        "3.2.S.6",
        "3.2.S.7",
    }
    general = next(c for c in root["children"] if c["code"] == "3.2.S.1")
    assert [c["code"] for c in general["children"]] == [
        "3.2.S.1.1",
        "3.2.S.1.2",
        "3.2.S.1.3",
    ]


def test_api_ctd_sections_total_count(client) -> None:
    response = client.get("/api/v1/ctd-sections")
    assert response.status_code == 200

    def count_nodes(nodes: list[dict]) -> int:
        total = len(nodes)
        for node in nodes:
            total += count_nodes(node.get("children", []))
        return total

    total = count_nodes(response.json()["sections"])
    assert total == len(CTD_MODULE_32S_SEED)
