# 링크 → 과학 영상 자동 생성기

과학 유튜브 영상 링크를 넣으면 그 영상의 **구성 흐름(훅→질문→설명→반전→결론, 장면 수, 호흡, 톤)** 을
분석해, 같은 흐름을 따르는 **새 주제의 영상**(인포그래픽 + TTS 나레이션 + 자막)을 만듭니다.
원본의 문장/영상은 복제하지 않고 구조만 템플릿으로 저장합니다.

```
링크 → ingest(자막) → analyze(Gemini: 구조 템플릿) → script(Gemini: 새 대본)
     → tts(Edge-TTS) → visuals(Pillow 인포그래픽) → compose(ffmpeg) → MP4
```

## 설치 (사용자 PC)
```
pip install -r requirements.txt     # + ffmpeg 설치 필요
cp .env.example .env                # GEMINI_API_KEY 입력
```
한글 폰트: Windows/macOS는 시스템 폰트 자동 사용. Linux는 `assets/fonts/`에 Noto Sans KR(.ttf/.otf)를 넣으세요.

## 사용
```
streamlit run app.py                                   # 웹 UI: 분석 → 대본 수정 → 렌더
python cli.py --url https://youtu.be/wd1RG5BIsqE --url https://youtu.be/kAtfE1rcvq8 \
              --topic "블랙홀은 왜 빛을 삼킬까?" --minutes 5 -o out/video.mp4
```
`--visual`(UI에서는 체크박스)을 주면 영상 자체를 내려받아(360p) Gemini가 직접 보고 화면 구성·색감·연출 리듬까지 분석합니다. 느리고 API 비용이 늘어납니다.
링크를 여러 개 주면 공통 흐름으로 병합됩니다. 분석 결과는 `work/<영상ID>/template.json`에 캐시됩니다.

## 구조
`ingest.py` `analyze.py` `script.py` `tts.py` `compose.py` `pipeline.py` · `visuals/`(title, bullets, diagram, chart,
equation, counter, timeline) · `prompts/`(프롬프트 튜닝은 여기서) · `tests/`
새 장면 유형은 `visuals/`에 `render(spec, t)` 함수를 추가하고 `visuals/__init__.py`·`schemas.py`에 등록하면 됩니다.

## 테스트
`pytest tests` — Gemini/YouTube 없이 가짜 LLM + 무음 TTS로 전체 렌더까지 검증합니다.
