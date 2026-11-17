import json
from pathlib import Path
import streamlit as st
import pipeline
from schemas import Script, Template

st.set_page_config(page_title="과학 영상 자동 생성기", layout="wide")
st.title("🔬 링크 → 과학 영상 자동 생성기")

urls_txt = st.text_area("벤치마킹할 유튜브 링크 (줄바꿈으로 여러 개)", height=100)
c1, c2, c3 = st.columns(3)
topic = c1.text_input("새 영상 주제", placeholder="예: 블랙홀은 왜 빛을 삼킬까?")
minutes = c2.number_input("목표 길이(분, 0=원본과 동일)", 0.0, 30.0, 0.0, 0.5)
engine = c3.selectbox("음성 엔진", ["edge", "silent"])

if st.button("1) 구조 분석", type="primary", disabled=not urls_txt.strip()):
    with st.spinner("자막 수집·분석 중…"):
        st.session_state.template = pipeline.build_template([u for u in urls_txt.splitlines() if u.strip()], log=st.write)
        st.session_state.pop("script", None)

if "template" in st.session_state:
    st.subheader("분석된 흐름 (수정 가능)")
    edited = st.text_area("template.json", st.session_state.template.model_dump_json(indent=1), height=300)
    if st.button("2) 대본 생성", disabled=not topic):
        with st.spinner("대본 작성 중…"):
            tpl = Template.model_validate_json(edited)
            st.session_state.script = pipeline.build_script(tpl, topic, minutes or None)

if "script" in st.session_state:
    st.subheader("대본 (수정 가능)")
    edited_s = st.text_area("script.json", st.session_state.script.model_dump_json(indent=1), height=400)
    if st.button("3) 영상 렌더링"):
        script = Script.model_validate_json(edited_s)
        bar = st.progress(0.0)
        out = Path("out") / "video.mp4"
        pipeline.render_video(script, out, engine=engine, on_progress=bar.progress)
        st.video(str(out))
        st.download_button("MP4 다운로드", out.read_bytes(), "video.mp4", "video/mp4")
