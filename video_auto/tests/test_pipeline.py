import json, subprocess, sys
from pathlib import Path
import pytest
sys.path.insert(0, str(Path(__file__).parent.parent))
import ingest, analyze, script as sc, pipeline
from schemas import Template

FIXTURE_TEMPLATE = {
    "channel_style": "calm explainer", "tone": "curious", "total_seconds": 40, "avg_scene_seconds": 6,
    "avg_sentence_chars": 30, "hook_pattern": "surprising fact -> why?", "transition_patterns": ["question"],
    "visual_types": ["title", "diagram", "chart"],
    "sections": [{"role": "hook", "share": 0.3, "scenes": 2, "technique": "fact"},
                 {"role": "conclusion", "share": 0.7, "scenes": 2, "technique": "recap"}],
}
FIXTURE_SCRIPT = {"title": "t", "scenes": [
    {"section": "hook", "narration": "별은 어떻게 빛날까요? 오늘 알아봅니다.", "visual_type": "title", "visual_spec": {"text": "별의 빛", "sub": "왜?"}},
    {"section": "explanation", "narration": "수소가 헬륨으로 융합합니다.", "visual_type": "diagram",
     "visual_spec": {"nodes": [{"id": "h", "label": "수소"}, {"id": "he", "label": "헬륨"}], "edges": [{"from": "h", "to": "he", "label": "핵융합"}]}},
    {"section": "explanation", "narration": "온도에 따라 밝기가 다릅니다.", "visual_type": "chart",
     "visual_spec": {"title": "온도", "unit": "K", "bars": [{"label": "A", "value": 3000}, {"label": "B", "value": 6000}]}},
    {"section": "twist", "narration": "숫자가 커집니다.", "visual_type": "counter", "visual_spec": {"label": "나이", "from": 0, "to": 4600, "unit": "백만 년"}},
    {"section": "conclusion", "narration": "정리합니다.", "visual_type": "bullets", "visual_spec": {"heading": "요약", "items": ["a", "b"]}},
    {"section": "conclusion", "narration": "끝.", "visual_type": "equation", "visual_spec": {"expr": "E=mc²", "caption": "질량-에너지"}},
]}


def test_parse_video_id():
    assert ingest.parse_video_id("https://youtu.be/wd1RG5BIsqE?si=abc") == "wd1RG5BIsqE"
    assert ingest.parse_video_id("https://www.youtube.com/watch?v=kAtfE1rcvq8&t=3") == "kAtfE1rcvq8"
    with pytest.raises(ValueError):
        ingest.parse_video_id("https://example.com")


def test_condense():
    segs = [{"start": 0, "text": "a"}, {"start": 4, "text": "b"}, {"start": 12, "text": "c"}]
    assert ingest.condense(segs).splitlines() == ["[00:00] a b", "[00:12] c"]


def test_analyze_and_script_with_fake_llm():
    v = ingest.Video("x" * 11, "T", "C", 40, [{"start": 0, "text": "hello"}])
    t = analyze.analyze(v, caller=lambda p: json.dumps(FIXTURE_TEMPLATE))
    assert t.total_seconds == 40 and len(t.sections) == 2
    s = sc.write_script(t, "별", caller=lambda p: json.dumps(FIXTURE_SCRIPT))
    assert len(s.scenes) == 6


def test_llm_retries_on_bad_json():
    import llm
    calls = iter(["not json", json.dumps(FIXTURE_TEMPLATE)])
    assert llm.generate("p", Template, caller=lambda p: next(calls)).tone == "curious"


def test_render_end_to_end(tmp_path):
    from schemas import Script
    s = Script.model_validate(FIXTURE_SCRIPT)
    out = pipeline.render_video(s, tmp_path / "v.mp4", engine="silent", fps=8)
    info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
                           "-of", "json", str(out)], capture_output=True, text=True).stdout
    j = json.loads(info)
    assert {st["codec_type"] for st in j["streams"]} == {"video", "audio"}
    assert float(j["format"]["duration"]) > 8


def test_bad_spec_degrades_to_title():
    import visuals
    img = visuals.render("chart", {"bars": [{"label": "x", "value": "oops"}]}, 0.5)
    assert img.size == (1920, 1080)
