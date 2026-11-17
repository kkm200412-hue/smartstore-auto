from visuals.base import *


def render(spec, t):
    img, d = canvas()
    ev = list(spec.get("events", []))[:5]
    if not ev:
        return img
    y = H // 2
    x0, x1 = 200, W - 200
    d.line([x0, y, lerp(x0, x1, stage(t, 0.0, 0.5)), y], fill=T.muted, width=6)
    for i, e in enumerate(ev):
        x = lerp(x0, x1, i / max(len(ev) - 1, 1))
        k = stage(t, 0.1 + i * 0.12, 0.3 + i * 0.12)
        r = 22 * k
        d.ellipse([x - r, y - r, x + r, y + r], fill=T.accent)
        up = i % 2 == 0
        col = fade(T.fg, k)
        w = d.textlength(str(e.get("when", "")), font=font(56))
        d.text((x - w / 2, y + (-130 if up else 50)), str(e.get("when", "")), font=font(56), fill=fade(T.accent, k))
        for j, ln in enumerate(wrap(d, str(e.get("what", "")), font(38), 340)[:3]):
            lw = d.textlength(ln, font=font(38))
            d.text((x - lw / 2, y + (-250 + j * 46 if up else 130 + j * 46)), ln, font=font(38), fill=col)
    return img
