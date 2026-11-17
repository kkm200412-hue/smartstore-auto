"""Transcript -> structure Template (Gemini)."""
from __future__ import annotations
from pathlib import Path
import llm
from ingest import Video, condense
from schemas import Template

PROMPTS = Path(__file__).parent / "prompts"


def analyze(video: Video, caller=llm._call_gemini) -> Template:
    prompt = (PROMPTS / "analyze.md").read_text(encoding="utf-8").format(
        title=video.title or video.video_id, duration=int(video.duration), transcript=condense(video.segments)
    )
    t = llm.generate(prompt, Template, caller=caller)
    if video.duration:
        t.total_seconds = int(video.duration)  # trust measured length over the model's guess
    return t


def merge(templates: list[Template]) -> Template:
    """Combine several benchmark templates: average numbers, keep the first one's section skeleton."""
    if len(templates) == 1:
        return templates[0]
    base = templates[0].model_copy(deep=True)
    n = len(templates)
    base.total_seconds = round(sum(t.total_seconds for t in templates) / n)
    base.avg_scene_seconds = round(sum(t.avg_scene_seconds for t in templates) / n, 1)
    base.avg_sentence_chars = round(sum(t.avg_sentence_chars for t in templates) / n)
    base.transition_patterns = list(dict.fromkeys(p for t in templates for p in t.transition_patterns))[:6]
    base.visual_types = list(dict.fromkeys(v for t in templates for v in t.visual_types))
    return base
