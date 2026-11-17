"""Shared theme + drawing helpers for infographic scenes."""
from __future__ import annotations
import glob, os
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080
BG_TOP, BG_BOTTOM = (11, 18, 38), (28, 40, 82)
FG, MUTED, ACCENT, ACCENT2 = (240, 244, 255), (150, 165, 205), (255, 200, 87), (96, 200, 255)

_FONT_GLOBS = [
    str(Path(__file__).parent.parent / "assets/fonts/*.[to]tf"),
    "/usr/share/fonts/**/NotoSansCJK*Bold*", "/usr/share/fonts/**/NotoSansKR*", "/usr/share/fonts/**/Nanum*Bold*",
    "/usr/share/fonts/**/Nanum*", "C:/Windows/Fonts/malgunbd.ttf", "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/**/DejaVuSans-Bold.ttf",
]


@lru_cache(maxsize=None)
def font(size: int) -> ImageFont.FreeTypeFont:
    for g in _FONT_GLOBS:
        for f in sorted(glob.glob(g, recursive=True)):
            try:
                return ImageFont.truetype(f, size)
            except OSError:
                continue
    return ImageFont.load_default(size)


def ease(t: float) -> float:
    t = min(max(t, 0.0), 1.0)
    return 1 - (1 - t) ** 3


def stage(t: float, start: float, end: float) -> float:
    """Local eased progress of an animation that runs between start..end of the scene."""
    return ease((t - start) / (end - start)) if end > start else 1.0


@lru_cache(maxsize=1)
def _bg() -> Image.Image:
    img = Image.new("RGB", (1, H))
    for y in range(H):
        k = y / (H - 1)
        img.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(BG_TOP, BG_BOTTOM)))
    return img.resize((W, H))


def canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = _bg().copy()
    return img, ImageDraw.Draw(img)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt, max_w: int) -> list[str]:
    """Wrap by words, falling back to characters for CJK text without spaces."""
    lines, cur = [], ""
    tokens = text.split(" ") if " " in text else list(text)
    sep = " " if " " in text else ""
    for tok in tokens:
        trial = f"{cur}{sep}{tok}" if cur else tok
        if draw.textlength(trial, font=fnt) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = tok
    if cur:
        lines.append(cur)
    return lines


def centered(draw, text, y, fnt, fill=FG, max_w=W - 320, alpha_t: float = 1.0, line_gap=1.25) -> int:
    """Draw wrapped centered text; returns y after the block. alpha_t blends colour toward background."""
    col = tuple(int(b + (f - b) * alpha_t) for f, b in zip(fill, BG_TOP))
    for line in wrap(draw, text, fnt, max_w):
        w = draw.textlength(line, font=fnt)
        draw.text(((W - w) / 2, y), line, font=fnt, fill=col)
        y += int(fnt.size * line_gap)
    return y


def lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k
