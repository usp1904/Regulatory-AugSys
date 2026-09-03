"""Story Map workspace API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.story_map import (
    BackboneCreateRequest,
    LinkableSourcesResponse,
    ReleaseSliceCreateRequest,
    StoryCreateRequest,
    StoryMapCreateRequest,
    StoryMapExportResponse,
    StoryMapListResponse,
    StoryMapResponse,
    StoryMapUpdateRequest,
    StoryReorderRequest,
    StoryResponse,
    StoryUpdateRequest,
    TraceLinkCreateRequest,
    TraceLinkResponse,
)
from app.services.story_map import (
    StoryMapServiceError,
    add_backbone,
    add_release_slice,
    add_story,
    add_trace_link,
    create_story_map,
    delete_story_map,
    delete_story,
    delete_trace_link,
    get_linkable_sources,
    get_story_map,
    list_story_maps,
    reorder_stories,
    story_map_to_response,
    story_to_response,
    update_story,
    update_story_map,
)

router = APIRouter(prefix="/story-maps", tags=["story-maps"])


@router.get("/linkable-sources", response_model=LinkableSourcesResponse)
def list_linkable_sources(db: Session = Depends(get_db)) -> LinkableSourcesResponse:
    sources = get_linkable_sources(db)
    return LinkableSourcesResponse(**sources)


@router.post("", response_model=StoryMapResponse, status_code=201)
def create_story_map_item(
    payload: StoryMapCreateRequest,
    db: Session = Depends(get_db),
) -> StoryMapResponse:
    try:
        story_map = create_story_map(db, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.get("", response_model=StoryMapListResponse)
def list_story_map_items(db: Session = Depends(get_db)) -> StoryMapListResponse:
    items = list_story_maps(db)
    return StoryMapListResponse(items=[story_map_to_response(item) for item in items])


@router.get("/{map_id}", response_model=StoryMapResponse)
def get_story_map_item(map_id: int, db: Session = Depends(get_db)) -> StoryMapResponse:
    try:
        story_map = get_story_map(db, map_id)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.get("/{map_id}/export", response_model=StoryMapExportResponse)
def export_story_map(map_id: int, db: Session = Depends(get_db)) -> StoryMapExportResponse:
    try:
        story_map = get_story_map(db, map_id)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return StoryMapExportResponse(story_map=story_map_to_response(story_map))


@router.patch("/{map_id}", response_model=StoryMapResponse)
def patch_story_map(
    map_id: int,
    payload: StoryMapUpdateRequest,
    db: Session = Depends(get_db),
) -> StoryMapResponse:
    try:
        story_map = update_story_map(db, map_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.delete("/{map_id}", status_code=204)
def remove_story_map(map_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_story_map(db, map_id)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{map_id}/backbones", response_model=StoryMapResponse)
def create_backbone(
    map_id: int,
    payload: BackboneCreateRequest,
    db: Session = Depends(get_db),
) -> StoryMapResponse:
    try:
        story_map = add_backbone(db, map_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.post("/{map_id}/release-slices", response_model=StoryMapResponse)
def create_release_slice(
    map_id: int,
    payload: ReleaseSliceCreateRequest,
    db: Session = Depends(get_db),
) -> StoryMapResponse:
    try:
        story_map = add_release_slice(db, map_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.post("/{map_id}/stories", response_model=StoryResponse, status_code=201)
def create_story_item(
    map_id: int,
    payload: StoryCreateRequest,
    db: Session = Depends(get_db),
) -> StoryResponse:
    try:
        story = add_story(db, map_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return story_to_response(story)


@router.post("/{map_id}/stories/reorder", response_model=StoryMapResponse)
def reorder_story_items(
    map_id: int,
    payload: StoryReorderRequest,
    db: Session = Depends(get_db),
) -> StoryMapResponse:
    try:
        story_map = reorder_stories(db, map_id, payload.story_ids)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return story_map_to_response(story_map)


@router.patch("/stories/{story_id}", response_model=StoryResponse)
def patch_story_item(
    story_id: int,
    payload: StoryUpdateRequest,
    db: Session = Depends(get_db),
) -> StoryResponse:
    try:
        story = update_story(db, story_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return story_to_response(story)


@router.delete("/stories/{story_id}", status_code=204)
def remove_story_item(story_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_story(db, story_id)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/stories/{story_id}/trace-links", response_model=TraceLinkResponse, status_code=201)
def create_trace_link(
    story_id: int,
    payload: TraceLinkCreateRequest,
    db: Session = Depends(get_db),
) -> TraceLinkResponse:
    try:
        link = add_trace_link(db, story_id, payload)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TraceLinkResponse.model_validate(link)


@router.delete("/trace-links/{link_id}", status_code=204)
def remove_trace_link(link_id: int, db: Session = Depends(get_db)) -> None:
    try:
        delete_trace_link(db, link_id)
    except StoryMapServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
