"""Story Map workspace business logic."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.ctd_section import CtdSection
from app.models.evidence_item import EvidenceItem
from app.models.story_map import (
    GROUP_BY_OPTIONS,
    RELEASE_MEANINGS,
    STORY_MAP_TEMPLATES,
    STORY_STATUSES,
    TRACE_LINK_TYPES,
    TRACE_SOURCE_WORKSPACES,
    StoryMap,
    StoryMapBackbone,
    StoryMapReleaseSlice,
    StoryMapStory,
    StoryMapTraceLink,
)
from app.schemas.story_map import (
    BackboneCreateRequest,
    ReleaseSliceCreateRequest,
    StoryCreateRequest,
    StoryMapCreateRequest,
    StoryMapResponse,
    StoryMapUpdateRequest,
    StoryResponse,
    StoryUpdateRequest,
    TraceLinkCreateRequest,
    TraceLinkResponse,
)


class StoryMapServiceError(Exception):
    pass


def _load_story_map(db: Session, map_id: int) -> StoryMap | None:
    return db.scalar(
        select(StoryMap)
        .where(StoryMap.id == map_id)
        .options(
            joinedload(StoryMap.backbones),
            joinedload(StoryMap.release_slices),
            joinedload(StoryMap.stories).joinedload(StoryMapStory.trace_links),
        )
    )


def story_map_to_response(story_map: StoryMap) -> StoryMapResponse:
    return StoryMapResponse(
        id=story_map.id,
        map_key=story_map.map_key,
        title=story_map.title,
        template=story_map.template,
        intent=story_map.intent,
        group_by=story_map.group_by,
        package_status=story_map.package_status,
        created_by=story_map.created_by,
        backbones=[
            {"id": b.id, "title": b.title, "sort_order": b.sort_order} for b in story_map.backbones
        ],
        release_slices=[
            {
                "id": r.id,
                "name": r.name,
                "release_meaning": r.release_meaning,
                "description": r.description,
                "sort_order": r.sort_order,
            }
            for r in story_map.release_slices
        ],
        stories=[story_to_response(s) for s in story_map.stories],
        created_at=story_map.created_at,
        updated_at=story_map.updated_at,
    )


def story_to_response(story: StoryMapStory) -> StoryResponse:
    return StoryResponse(
        id=story.id,
        title=story.title,
        backbone_id=story.backbone_id,
        release_slice_id=story.release_slice_id,
        sort_order=story.sort_order,
        group_key=story.group_key,
        owner=story.owner,
        outcome_or_obligation=story.outcome_or_obligation,
        acceptance_criteria=story.acceptance_criteria,
        evidence_required=story.evidence_required,
        risk=story.risk,
        dependency=story.dependency,
        source_control_ref=story.source_control_ref,
        status=story.status,
        trace_links=[TraceLinkResponse.model_validate(link) for link in story.trace_links],
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


def create_story_map(db: Session, payload: StoryMapCreateRequest) -> StoryMap:
    if payload.template not in STORY_MAP_TEMPLATES:
        raise StoryMapServiceError(f"Invalid template: {payload.template}")
    if payload.group_by not in GROUP_BY_OPTIONS:
        raise StoryMapServiceError(f"Invalid group_by: {payload.group_by}")

    story_map = StoryMap(
        map_key=StoryMap.new_map_key(),
        title=payload.title,
        template=payload.template,
        intent=payload.intent,
        group_by=payload.group_by,
        created_by=payload.created_by,
    )
    db.add(story_map)
    db.commit()
    db.refresh(story_map)
    loaded = _load_story_map(db, story_map.id)
    assert loaded is not None
    return loaded


def list_story_maps(db: Session) -> list[StoryMap]:
    maps = db.scalars(
        select(StoryMap)
        .options(
            joinedload(StoryMap.backbones),
            joinedload(StoryMap.release_slices),
            joinedload(StoryMap.stories).joinedload(StoryMapStory.trace_links),
        )
        .order_by(StoryMap.updated_at.desc())
    ).unique().all()
    return list(maps)


def get_story_map(db: Session, map_id: int) -> StoryMap:
    story_map = _load_story_map(db, map_id)
    if story_map is None:
        raise StoryMapServiceError("Story map not found")
    return story_map


def update_story_map(db: Session, map_id: int, payload: StoryMapUpdateRequest) -> StoryMap:
    story_map = get_story_map(db, map_id)
    if payload.title is not None:
        story_map.title = payload.title
    if payload.intent is not None:
        story_map.intent = payload.intent
    if payload.group_by is not None:
        if payload.group_by not in GROUP_BY_OPTIONS:
            raise StoryMapServiceError(f"Invalid group_by: {payload.group_by}")
        story_map.group_by = payload.group_by
    db.commit()
    return get_story_map(db, map_id)


def delete_story_map(db: Session, map_id: int) -> None:
    story_map = db.get(StoryMap, map_id)
    if story_map is None:
        raise StoryMapServiceError("Story map not found")
    db.delete(story_map)
    db.commit()


def add_backbone(db: Session, map_id: int, payload: BackboneCreateRequest) -> StoryMap:
    story_map = get_story_map(db, map_id)
    backbone = StoryMapBackbone(
        story_map_id=story_map.id,
        title=payload.title,
        sort_order=payload.sort_order,
    )
    db.add(backbone)
    db.commit()
    return get_story_map(db, map_id)


def add_release_slice(
    db: Session, map_id: int, payload: ReleaseSliceCreateRequest
) -> StoryMap:
    story_map = get_story_map(db, map_id)
    if payload.release_meaning not in RELEASE_MEANINGS:
        raise StoryMapServiceError(f"Invalid release_meaning: {payload.release_meaning}")
    release_slice = StoryMapReleaseSlice(
        story_map_id=story_map.id,
        name=payload.name,
        release_meaning=payload.release_meaning,
        description=payload.description,
        sort_order=payload.sort_order,
    )
    db.add(release_slice)
    db.commit()
    return get_story_map(db, map_id)


def add_story(db: Session, map_id: int, payload: StoryCreateRequest) -> StoryMapStory:
    story_map = get_story_map(db, map_id)
    if payload.status not in STORY_STATUSES:
        raise StoryMapServiceError(f"Invalid status: {payload.status}")

    if payload.backbone_id is not None:
        backbone = db.get(StoryMapBackbone, payload.backbone_id)
        if backbone is None or backbone.story_map_id != story_map.id:
            raise StoryMapServiceError("Invalid backbone_id for this story map")

    if payload.release_slice_id is not None:
        release_slice = db.get(StoryMapReleaseSlice, payload.release_slice_id)
        if release_slice is None or release_slice.story_map_id != story_map.id:
            raise StoryMapServiceError("Invalid release_slice_id for this story map")

    story = StoryMapStory(
        story_map_id=story_map.id,
        backbone_id=payload.backbone_id,
        release_slice_id=payload.release_slice_id,
        title=payload.title,
        sort_order=payload.sort_order,
        group_key=payload.group_key,
        owner=payload.owner,
        outcome_or_obligation=payload.outcome_or_obligation,
        acceptance_criteria=payload.acceptance_criteria,
        evidence_required=payload.evidence_required,
        risk=payload.risk,
        dependency=payload.dependency,
        source_control_ref=payload.source_control_ref,
        status=payload.status,
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    loaded = db.scalar(
        select(StoryMapStory)
        .where(StoryMapStory.id == story.id)
        .options(joinedload(StoryMapStory.trace_links))
    )
    assert loaded is not None
    return loaded


def update_story(db: Session, story_id: int, payload: StoryUpdateRequest) -> StoryMapStory:
    story = db.scalar(
        select(StoryMapStory)
        .where(StoryMapStory.id == story_id)
        .options(joinedload(StoryMapStory.trace_links))
    )
    if story is None:
        raise StoryMapServiceError("Story not found")

    if payload.status is not None and payload.status not in STORY_STATUSES:
        raise StoryMapServiceError(f"Invalid status: {payload.status}")

    if payload.backbone_id is not None:
        backbone = db.get(StoryMapBackbone, payload.backbone_id)
        if backbone is None or backbone.story_map_id != story.story_map_id:
            raise StoryMapServiceError("Invalid backbone_id for this story map")

    if payload.release_slice_id is not None:
        release_slice = db.get(StoryMapReleaseSlice, payload.release_slice_id)
        if release_slice is None or release_slice.story_map_id != story.story_map_id:
            raise StoryMapServiceError("Invalid release_slice_id for this story map")

    for field in (
        "title",
        "backbone_id",
        "release_slice_id",
        "sort_order",
        "group_key",
        "owner",
        "outcome_or_obligation",
        "acceptance_criteria",
        "evidence_required",
        "risk",
        "dependency",
        "source_control_ref",
        "status",
    ):
        value = getattr(payload, field)
        if value is not None:
            setattr(story, field, value)

    db.commit()
    db.refresh(story)
    return story


def reorder_stories(db: Session, map_id: int, story_ids: list[int]) -> StoryMap:
    story_map = get_story_map(db, map_id)
    story_by_id = {s.id: s for s in story_map.stories}
    if set(story_ids) != set(story_by_id.keys()):
        raise StoryMapServiceError("story_ids must include every story in the map exactly once")
    for index, story_id in enumerate(story_ids):
        story_by_id[story_id].sort_order = index
    db.commit()
    return get_story_map(db, map_id)


def delete_story(db: Session, story_id: int) -> None:
    story = db.get(StoryMapStory, story_id)
    if story is None:
        raise StoryMapServiceError("Story not found")
    db.delete(story)
    db.commit()


def add_trace_link(
    db: Session,
    story_id: int,
    payload: TraceLinkCreateRequest,
) -> StoryMapTraceLink:
    story = db.get(StoryMapStory, story_id)
    if story is None:
        raise StoryMapServiceError("Story not found")
    if payload.link_type not in TRACE_LINK_TYPES:
        raise StoryMapServiceError(f"Invalid link_type: {payload.link_type}")
    if payload.source_workspace not in TRACE_SOURCE_WORKSPACES:
        raise StoryMapServiceError(f"Invalid source_workspace: {payload.source_workspace}")

    link = StoryMapTraceLink(
        story_id=story.id,
        link_type=payload.link_type,
        external_ref=payload.external_ref,
        label=payload.label,
        source_workspace=payload.source_workspace,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


def delete_trace_link(db: Session, link_id: int) -> None:
    link = db.get(StoryMapTraceLink, link_id)
    if link is None:
        raise StoryMapServiceError("Trace link not found")
    db.delete(link)
    db.commit()


def get_linkable_sources(db: Session) -> dict:
    ctd_sections = db.scalars(select(CtdSection).order_by(CtdSection.code)).all()
    evidence_items = db.scalars(
        select(EvidenceItem).order_by(EvidenceItem.id.desc()).limit(200)
    ).all()
    return {
        "ctd_sections": [
            {"code": s.code, "title": s.title, "module": s.code.split(".")[0] if s.code else None}
            for s in ctd_sections
        ],
        "evidence_items": [
            {
                "id": e.id,
                "evidence_key": e.evidence_key,
                "dossier_id": e.dossier_id,
                "ctd_section_code": e.ctd_section_code,
                "review_status": e.review_status,
                "evidence_type": e.evidence_type,
            }
            for e in evidence_items
        ],
    }
