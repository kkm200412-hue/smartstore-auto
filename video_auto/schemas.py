"""Pydantic schemas shared by every pipeline stage."""
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

VisualType = Literal["title", "bullets", "diagram", "chart", "equation", "counter", "timeline"]
SectionRole = Literal["hook", "question", "explanation", "twist", "conclusion"]


class Section(BaseModel):
    role: SectionRole
    share: float = Field(description="fraction of total runtime, 0-1")
    scenes: int = Field(ge=1)
    technique: str = Field(description="how this section works, e.g. 'shocking number then question'")


class Template(BaseModel):
    """Structure-only description of a benchmark video (no original wording)."""
    channel_style: str
    tone: str
    total_seconds: int
    avg_scene_seconds: float
    avg_sentence_chars: int
    hook_pattern: str
    transition_patterns: list[str]
    visual_types: list[VisualType]
    sections: list[Section]


class Scene(BaseModel):
    section: SectionRole
    narration: str
    visual_type: VisualType
    visual_spec: dict[str, Any] = Field(default_factory=dict)


class Script(BaseModel):
    title: str
    scenes: list[Scene]
