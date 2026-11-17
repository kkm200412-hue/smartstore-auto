from visuals.base import *
import math


def render(spec, t):
    img, d = canvas()
    nodes = list(spec.get("nodes", []))[:5] or [{"id": "a", "label": ""}]
    n = len(nodes)
    bw, bh = 300, 130
    gap = (W - 240 - n * bw) / max(n - 1, 1) if n > 1 else 0
    pos = {}
    for i, nd in enumerate(nodes):
        x = 120 + i * (bw + gap) if n > 1 else (W - bw) / 2
        pos[nd["id"]] = (x, H / 2 - bh / 2 + (60 if i % 2 else -60))
    for j, e in enumerate(spec.get("edges", [])):
        if e.get("from") not in pos or e.get("to") not in pos:
            continue
        k = stage(t, 0.25 + j * 0.15, 0.45 + j * 0.15)
        (x1, y1), (x2, y2) = pos[e["from"]], pos[e["to"]]
        a = (x1 + bw if x2 > x1 else x1, y1 + bh / 2); b = (x2 if x2 > x1 else x2 + bw, y2 + bh / 2)
        end = (lerp(a[0], b[0], k), lerp(a[1], b[1], k))
        d.line([a, end], fill=ACCENT, width=6)
        if k > 0.95:
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            for s in (0.5, -0.5):
                d.line([b, (b[0] - 28 * math.cos(ang + s), b[1] - 28 * math.sin(ang + s))], fill=ACCENT, width=6)
            if e.get("label"):
                w = d.textlength(str(e["label"]), font=font(38))
                d.text(((a[0] + b[0]) / 2 - w / 2, (a[1] + b[1]) / 2 - 62), str(e["label"]), font=font(38), fill=MUTED)
    for i, nd in enumerate(nodes):
        k = stage(t, i * 0.08, 0.2 + i * 0.08)
        x, y = pos[nd["id"]]
        pad = (1 - k) * 30
        d.rounded_rectangle([x + pad, y + pad, x + bw - pad, y + bh - pad], 24, fill=(40, 58, 110), outline=ACCENT2, width=4)
        if k > 0.6:
            lines = wrap(d, str(nd.get("label", "")), font(42), bw - 30)
            ty = y + bh / 2 - len(lines) * 26
            for ln in lines:
                d.text((x + (bw - d.textlength(ln, font=font(42))) / 2, ty), ln, font=font(42), fill=FG)
                ty += 52
    return img
