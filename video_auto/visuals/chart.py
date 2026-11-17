from visuals.base import *


def render(spec, t):
    img, d = canvas()
    centered(d, str(spec.get("title", "")), 90, font(70), T.accent)
    bars = list(spec.get("bars", []))[:6]
    if not bars:
        return img
    mx = max(float(b.get("value", 0)) for b in bars) or 1.0
    left, base_y, ch = 200, H - 190, 600
    bw = (W - 2 * left) / len(bars)
    for i, b in enumerate(bars):
        k = stage(t, 0.05 + i * 0.1, 0.5 + i * 0.1)
        v = float(b.get("value", 0))
        h = ch * v / mx * k
        x = left + i * bw + bw * 0.15
        d.rounded_rectangle([x, base_y - h, x + bw * 0.7, base_y], 12, fill=T.accent2 if i % 2 else T.accent)
        lab = f"{v * k:,.0f}{spec.get('unit', '')}"
        d.text((x + bw * 0.35 - d.textlength(lab, font=font(44)) / 2, base_y - h - 62), lab, font=font(44), fill=T.fg)
        ll = str(b.get("label", ""))
        d.text((x + bw * 0.35 - d.textlength(ll, font=font(40)) / 2, base_y + 24), ll, font=font(40), fill=T.muted)
    d.line([left - 20, base_y, W - left + 20, base_y], fill=T.muted, width=3)
    return img
