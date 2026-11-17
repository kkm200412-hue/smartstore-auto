from visuals.base import *


def render(spec, t):
    img, d = canvas()
    k = stage(t, 0.0, 0.25)
    y = int(H * 0.36 + (1 - k) * 40)
    y = centered(d, str(spec.get("text", "")), y, font(104), FG, alpha_t=k)
    if spec.get("sub"):
        d.rectangle([W / 2 - 80, y + 20, W / 2 + 80, y + 26], fill=ACCENT)
        centered(d, str(spec["sub"]), y + 60, font(52), MUTED, alpha_t=stage(t, 0.15, 0.4))
    return img
