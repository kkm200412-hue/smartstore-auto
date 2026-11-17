from visuals.base import W, H
from visuals import title, bullets, diagram, chart, equation, counter, timeline

RENDERERS = {
    "title": title.render, "bullets": bullets.render, "diagram": diagram.render, "chart": chart.render,
    "equation": equation.render, "counter": counter.render, "timeline": timeline.render,
}


def render(visual_type: str, spec: dict, t: float):
    """Return a PIL RGB image for progress t in [0,1]. Unknown/invalid specs degrade to a title card."""
    try:
        return RENDERERS[visual_type](spec, t)
    except Exception:
        return title.render({"text": str(spec.get("text") or spec.get("heading") or "")}, t)
