"""YouTube URL -> metadata + timestamped transcript."""
from __future__ import annotations
import re
from dataclasses import dataclass, field

_ID_RE = re.compile(r"(?:youtu\.be/|v=|/shorts/|/embed/)([A-Za-z0-9_-]{11})")


def parse_video_id(url: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", url.strip()):
        return url.strip()
    m = _ID_RE.search(url)
    if not m:
        raise ValueError(f"Cannot find a YouTube video id in: {url}")
    return m.group(1)


@dataclass
class Video:
    video_id: str
    title: str = ""
    channel: str = ""
    duration: float = 0.0
    segments: list[dict] = field(default_factory=list)  # {"start": s, "text": str}


def _transcript(video_id: str, langs=("ko", "en")) -> list[dict]:
    from youtube_transcript_api import YouTubeTranscriptApi
    if hasattr(YouTubeTranscriptApi, "get_transcript"):  # <1.0
        raw = YouTubeTranscriptApi.get_transcript(video_id, languages=list(langs))
        return [{"start": float(r["start"]), "text": r["text"]} for r in raw]
    fetched = YouTubeTranscriptApi().fetch(video_id, languages=list(langs))
    return [{"start": float(s.start), "text": s.text} for s in fetched]


def _metadata(url: str) -> dict:
    import yt_dlp
    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        return ydl.extract_info(url, download=False)


def fetch_video(url: str) -> Video:
    vid = parse_video_id(url)
    v = Video(video_id=vid)
    try:
        info = _metadata(f"https://www.youtube.com/watch?v={vid}")
        v.title, v.channel, v.duration = info.get("title", ""), info.get("channel", ""), float(info.get("duration") or 0)
    except Exception:
        pass  # metadata is optional
    v.segments = _transcript(vid)
    if not v.duration and v.segments:
        v.duration = v.segments[-1]["start"] + 5
    return v


def condense(segments: list[dict], bucket: float = 10.0) -> str:
    """Merge caption lines into ~10s buckets: '[00:30] text...' (keeps prompt small)."""
    out, cur_t, buf = [], 0.0, []
    for s in segments:
        if s["start"] - cur_t >= bucket and buf:
            out.append(f"[{int(cur_t)//60:02d}:{int(cur_t)%60:02d}] {' '.join(buf)}")
            cur_t, buf = s["start"], []
        buf.append(s["text"].replace("\n", " "))
    if buf:
        out.append(f"[{int(cur_t)//60:02d}:{int(cur_t)%60:02d}] {' '.join(buf)}")
    return "\n".join(out)


def download_video(video_id: str, outdir) -> "Path":
    """Download a small (<=360p) copy for visual analysis. Cached."""
    from pathlib import Path
    import yt_dlp
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    target = outdir / f"{video_id}.mp4"
    if target.exists():
        return target
    opts = {"quiet": True, "outtmpl": str(target), "merge_output_format": "mp4",
            "format": "bv*[height<=360][ext=mp4]+ba[ext=m4a]/b[height<=360]/worst"}
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
    return target
