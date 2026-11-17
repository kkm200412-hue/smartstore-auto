"""Narration -> audio files with measured durations."""
from __future__ import annotations
import asyncio, os, subprocess, wave
from pathlib import Path


def probe_duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def _edge(text: str, path: Path, voice: str) -> None:
    import edge_tts
    asyncio.run(edge_tts.Communicate(text, voice).save(str(path)))


def _silent(text: str, path: Path, voice: str) -> None:
    """Offline fallback (tests / no network): silence sized by text length."""
    secs = max(1.5, len(text) / 6.0)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000)
        w.writeframes(b"\x00\x00" * int(24000 * secs))


ENGINES = {"edge": ("mp3", _edge), "silent": ("wav", _silent)}


def synthesize(narrations: list[str], outdir: Path, engine: str = "edge", voice: str | None = None) -> list[tuple[Path, float]]:
    ext, fn = ENGINES[engine]
    voice = voice or os.environ.get("TTS_VOICE", "ko-KR-SunHiNeural")
    outdir.mkdir(parents=True, exist_ok=True)
    result = []
    for i, text in enumerate(narrations):
        p = outdir / f"scene_{i:03d}.{ext}"
        if not p.exists():  # cache
            fn(text, p, voice)
        result.append((p, probe_duration(p)))
    return result
