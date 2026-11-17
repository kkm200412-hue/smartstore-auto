"""Template + topic -> scene-by-scene Script (Gemini)."""
from __future__ import annotations
import json
from pathlib import Path
import llm
from schemas import Script, Template

PROMPTS = Path(__file__).parent / "prompts"


def write_script(template: Template, topic: str, language: str = "Korean", minutes: float | None = None,
                 caller=llm._call_gemini) -> Script:
    secs = int(minutes * 60) if minutes else template.total_seconds
    prompt = (PROMPTS / "script.md").read_text(encoding="utf-8").format(
        language=language, topic=topic, template=json.dumps(template.model_dump(), ensure_ascii=False, indent=1),
        total_seconds=secs, chars=secs * 6, words=secs * 2, scene_seconds=template.avg_scene_seconds,
    )
    s = llm.generate(prompt, Script, caller=caller)
    if not s.scenes:
        raise RuntimeError("Script has no scenes")
    return s
