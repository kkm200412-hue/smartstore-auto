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


class SceneVisual(BaseModel):
    start: float = Field(description="seconds from video start")
    visual_type: VisualType
    description: str = Field(description="abstract description of what is on screen, no copied text")


class VisualProfile(BaseModel):
    """What the benchmark video LOOKS like (from watching the video itself)."""
    visual_notes: str = Field(description="overall look: palette, typography, motion, pacing of cuts")
    palette: list[str] = Field(default_factory=list, description="dominant hex colours")
    scene_visuals: list[SceneVisual]


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
    visual_notes: str = ""
    palette: list[str] = Field(default_factory=list)
    scene_visuals: list[SceneVisual] = Field(default_factory=list)


class Scene(BaseModel):
    section: SectionRole
    narration: str
    visual_type: VisualType
    visual_spec: dict[str, Any] = Field(default_factory=dict)


class Script(BaseModel):
    title: str
    scenes: list[Scene]
