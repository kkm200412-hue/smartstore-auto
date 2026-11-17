"""Shared theme + drawing helpers for infographic scenes."""
from __future__ import annotations
import glob, os, re
from functools import lru_cache
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1920, 1080


class Theme:
    """Mutable colour theme shared by all renderers (updated in place by set_theme)."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.bg_top, self.bg_bottom = (11, 18, 38), (28, 40, 82)
        self.fg, self.muted, self.accent, self.accent2 = (240, 244, 255), (150, 165, 205), (255, 200, 87), (96, 200, 255)
        if "_bg" in globals():
            _bg.cache_clear()


T = Theme()


def _parse_hex(c) -> tuple[int, int, int] | None:
    c = str(c).strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", c):
        return None
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def _lum(c) -> float:
    def f(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (f(v) for v in c)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _sat(c) -> float:
    mx, mn = max(c), min(c)
    return 0 if mx == 0 else (mx - mn) / mx


def mix(a, b, k):
    return tuple(int(x + (y - x) * k) for x, y in zip(a, b))


def set_theme(palette) -> bool:
    """Derive a theme from benchmark hex colours. Returns False (default theme kept) if unusable."""
    T.reset()
    cols = [c for c in (_parse_hex(p) for p in (palette or [])) if c]
    cols = list(dict.fromkeys(cols))
    if len(cols) < 3:
        return False
    cols.sort(key=_lum)
    dark, light = cols[0], cols[-1]
    if _lum(dark) > 0.25:  # no dark colour -> not a usable dark-background palette
        return False
    mids = sorted(cols[1:-1], key=_sat, reverse=True)
    bg_top = dark
    bg_bottom = mix(dark, light, 0.12)
    fg = light if contrast(light, bg_bottom) >= 4.5 else (255, 255, 255)
    acc1 = mids[0] if mids else fg
    acc2 = mids[1] if len(mids) > 1 else mix(acc1, fg, 0.4)
    # accents must stay readable on the background
    acc1 = acc1 if contrast(acc1, bg_bottom) >= 3 else mix(acc1, (255, 255, 255), 0.5)
    acc2 = acc2 if contrast(acc2, bg_bottom) >= 3 else mix(acc2, (255, 255, 255), 0.5)
    T.bg_top, T.bg_bottom, T.fg, T.accent, T.accent2 = bg_top, bg_bottom, fg, acc1, acc2
    T.muted = mix(fg, bg_bottom, 0.45)
    _bg.cache_clear()
    return True

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
        img.putpixel((0, y), tuple(int(a + (b - a) * k) for a, b in zip(T.bg_top, T.bg_bottom)))
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


def centered(draw, text, y, fnt, fill=None, max_w=W - 320, alpha_t: float = 1.0, line_gap=1.25) -> int:
    """Draw wrapped centered text; returns y after the block. alpha_t blends colour toward background."""
    col = fade(fill or T.fg, alpha_t)
    for line in wrap(draw, text, fnt, max_w):
        w = draw.textlength(line, font=fnt)
        draw.text(((W - w) / 2, y), line, font=fnt, fill=col)
        y += int(fnt.size * line_gap)
    return y


def fade(color, k: float):
    """Blend a colour toward the background (k=0 invisible, 1 full)."""
    return tuple(int(b + (f - b) * k) for f, b in zip(color, T.bg_top))


def lerp(a: float, b: float, k: float) -> float:
    return a + (b - a) * k
