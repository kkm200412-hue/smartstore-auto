from visuals.base import *


def render(spec, t):
    img, d = canvas()
    k = stage(t, 0.0, 0.3)
    f = font(int(120 + 20 * (1 - k)))
    centered(d, str(spec.get("expr", "")), int(H * 0.32), f, ACCENT, alpha_t=k)
    if spec.get("caption"):
        centered(d, str(spec["caption"]), int(H * 0.62), font(52), MUTED, alpha_t=stage(t, 0.25, 0.5))
    return img
