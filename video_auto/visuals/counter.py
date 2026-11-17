from visuals.base import *


def render(spec, t):
    img, d = canvas()
    a, b = float(spec.get("from", 0)), float(spec.get("to", 0))
    v = lerp(a, b, stage(t, 0.05, 0.8))
    txt = f"{v:,.0f}" if abs(b) >= 100 else f"{v:,.1f}"
    centered(d, str(spec.get("label", "")), int(H * 0.2), font(64), MUTED)
    centered(d, txt, int(H * 0.38), font(220), ACCENT)
    centered(d, str(spec.get("unit", "")), int(H * 0.68), font(72), FG)
    return img
