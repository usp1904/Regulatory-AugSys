"""Pydantic schemas for CTD sections."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CtdSectionNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    title: str
    sort_order: int
    children: list[CtdSectionNode] = []


class CtdSectionTreeResponse(BaseModel):
    module: str = "3.2.S"
    title: str = "Drug Substance"
    sections: list[CtdSectionNode]
