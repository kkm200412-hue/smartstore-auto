"""Orchestrates ingest -> analyze -> script -> tts -> compose with on-disk caching."""
from __future__ import annotations
import json
from pathlib import Path
import analyze as an, compose as cp, ingest, script as sc, tts
from schemas import Script, Template

WORK = Path(__file__).parent / "work"


def _cached(path: Path, model, producer):
    if path.exists():
        return model.model_validate_json(path.read_text(encoding="utf-8"))
    obj = producer()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(obj.model_dump_json(indent=1), encoding="utf-8")
    return obj


def build_template(urls: list[str], log=print, visual: bool = False) -> Template:
    templates = []
    for url in urls:
        vid = ingest.parse_video_id(url)
        def produce(url=url):
            log(f"[1/2] {vid}: 자막 수집 및 구조 분석 중…")
            return an.analyze(ingest.fetch_video(url))
        tpl = _cached(WORK / vid / "template.json", Template, produce)
        if visual and not tpl.scene_visuals:
            log(f"[visual] {vid}: 영상 다운로드 및 Gemini 시각 분석 중…")
            tpl = an.add_visual(tpl, ingest.download_video(vid, WORK / vid))
            (WORK / vid / "template.json").write_text(tpl.model_dump_json(indent=1), encoding="utf-8")
        templates.append(tpl)
    return an.merge(templates)


def build_script(template: Template, topic: str, minutes: float | None = None, language: str = "Korean") -> Script:
    return sc.write_script(template, topic, language=language, minutes=minutes)


def render_video(script: Script, out: Path, engine: str = "edge", voice: str | None = None, fps: int = 24,
                 captions: bool = True, bgm: Path | None = None, palette: list[str] | None = None,
                 on_progress=lambda f: None) -> Path:
    from visuals.base import set_theme
    set_theme(palette)  # None/unusable -> default theme
    work = out.parent / (out.stem + "_work")
    audio = tts.synthesize([s.narration for s in script.scenes], work / "audio", engine=engine, voice=voice)
    return cp.compose(script, audio, out, work, fps=fps, captions=captions, bgm=bgm, on_progress=on_progress)


def run(urls: list[str], topic: str, out: Path, minutes: float | None = None, engine: str = "edge", log=print,
        visual: bool = False, use_palette: bool = True, **kw) -> Path:
    template = build_template(urls, log, visual)
    log("[2/4] 대본 작성 중…")
    script = build_script(template, topic, minutes)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".script.json").write_text(script.model_dump_json(indent=1), encoding="utf-8")
    log("[3/4] 음성·영상 렌더링 중…")
    return render_video(script, out, engine=engine, palette=template.palette if use_palette else None, **kw)
