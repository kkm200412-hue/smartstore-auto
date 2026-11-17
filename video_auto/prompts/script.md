You write narration for a science explainer video in {language}.
Topic: {topic}

Follow this structural template exactly (section order, scene counts, tone, hook recipe, transitions).
Template:
{template}

Rules:
- Total narration about {total_seconds} seconds (~{chars} Korean characters / {words} English words). One scene = one idea, ~{scene_seconds}s.
- Never reuse wording from any source video; write original sentences. Be scientifically accurate; avoid unverifiable numbers.
- Each scene needs a visual_type from [title, bullets, diagram, chart, equation, counter, timeline] and a visual_spec:
  - title: {{"text": str, "sub": str}}
  - bullets: {{"heading": str, "items": [str, ...<=4]}}
  - diagram: {{"nodes": [{{"id": str, "label": str}}...<=5], "edges": [{{"from": id, "to": id, "label": str}}...]}}
  - chart: {{"title": str, "unit": str, "bars": [{{"label": str, "value": number}}...<=6]}}
  - equation: {{"expr": str, "caption": str}}
  - counter: {{"label": str, "from": number, "to": number, "unit": str}}
  - timeline: {{"events": [{{"when": str, "what": str}}...<=5]}}
- If the template has scene_visuals/visual_notes, mirror that visual rhythm (types and order of visuals per section); put palette hints in no spec.
- Narration only contains spoken text (no stage directions).
