from visuals.base import *


def render(spec, t):
    img, d = canvas()
    d.text((160, 130), str(spec.get("heading", "")), font=font(84), fill=T.accent)
    d.rectangle([160, 245, 460, 251], fill=T.accent2)
    items = list(spec.get("items", []))[:4]
    for i, item in enumerate(items):
        k = stage(t, 0.1 + i * 0.18, 0.3 + i * 0.18)
        y = 330 + i * 150
        x = 160 + (1 - k) * 80
        d.ellipse([x, y + 22, x + 28, y + 50], fill=T.accent2)
        col = fade(T.fg, k)
        d.text((x + 60, y), str(item), font=font(64), fill=col)
    return img
