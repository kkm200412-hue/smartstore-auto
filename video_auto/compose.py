"""Scenes + audio -> MP4. Frames are drawn with Pillow and piped straight into ffmpeg."""
from __future__ import annotations
import re, subprocess
from pathlib import Path
from PIL import ImageDraw
import visuals
from visuals.base import W, H, font, wrap, FG
from schemas import Script

PAD = 0.5  # seconds of silence after each scene


def split_subtitle(text: str, max_chars: int = 28) -> list[str]:
    """Split narration into short caption chunks at sentence/comma boundaries."""
    parts = [p.strip() for p in re.split(r"(?<=[.!?。…,，])\s*", text) if p.strip()]
    chunks: list[str] = []
    for p in parts:
        if chunks and len(chunks[-1]) + len(p) + 1 <= max_chars:
            chunks[-1] += " " + p
        else:
            chunks.append(p)
    return chunks or [text]


def _draw_caption(img, text: str) -> None:
    d = ImageDraw.Draw(img, "RGBA")
    lines = wrap(d, text, font(50), W - 360)[:2]
    h = len(lines) * 64 + 30
    y0 = H - 70 - h
    d.rounded_rectangle([140, y0, W - 140, y0 + h], 20, fill=(0, 0, 0, 150))
    for i, ln in enumerate(lines):
        d.text(((W - d.textlength(ln, font=font(50))) / 2, y0 + 15 + i * 64), ln, font=font(50), fill=FG)


def _pad_audio(src: Path, dst: Path, dur: float) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-af", f"apad=whole_dur={dur}",
                    "-t", str(dur), "-ar", "44100", "-ac", "1", str(dst)], check=True)


def compose(script: Script, audio: list[tuple[Path, float]], out: Path, workdir: Path, fps: int = 24,
            captions: bool = True, bgm: Path | None = None, on_progress=lambda f: None) -> Path:
    assert len(script.scenes) == len(audio), "scene/audio count mismatch"
    workdir.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)
    durs = [a[1] + PAD for a in audio]

    padded = []
    for i, ((src, _), dur) in enumerate(zip(audio, durs)):
        p = workdir / f"pad_{i:03d}.wav"
        _pad_audio(src, p, dur)
        padded.append(p)
    lst = workdir / "audio.txt"
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in padded))
    full = workdir / "narration.wav"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lst), str(full)], check=True)

    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
           "-r", str(fps), "-i", "-", "-i", str(full)]
    if bgm:
        cmd += ["-stream_loop", "-1", "-i", str(bgm), "-filter_complex",
                "[2:a]volume=0.08[b];[1:a][b]amix=inputs=2:duration=first:normalize=0[a]", "-map", "0:v", "-map", "[a]"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out)]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    total = sum(round(d * fps) for d in durs)
    done = 0
    try:
        for scene, (_, adur), dur in zip(script.scenes, audio, durs):
            n = round(dur * fps)
            caps = split_subtitle(scene.narration)
            weights = [len(c) for c in caps]
            bounds, acc = [], 0.0
            for w in weights:
                acc += w / sum(weights) * adur
                bounds.append(acc)
            for f in range(n):
                t_sec = f / fps
                img = visuals.render(scene.visual_type, scene.visual_spec, min(1.0, t_sec / max(dur - PAD, 0.1)))
                if captions and t_sec < adur:
                    idx = next((i for i, b in enumerate(bounds) if t_sec < b), len(caps) - 1)
                    _draw_caption(img, caps[idx])
                proc.stdin.write(img.tobytes())
                done += 1
                if done % fps == 0:
                    on_progress(done / total)
    finally:
        proc.stdin.close()
        rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"ffmpeg failed with exit code {rc}")
    on_progress(1.0)
    return out
