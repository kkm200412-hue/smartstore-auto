"""python cli.py --url <youtube link> [--url ...] --topic "블랙홀" [--minutes 5] -o out/video.mp4"""
import argparse
from pathlib import Path
import pipeline


def main():
    ap = argparse.ArgumentParser(description="링크 → 같은 흐름의 새 과학 영상")
    ap.add_argument("--url", action="append", required=True, help="벤치마킹할 영상 링크 (여러 번 가능)")
    ap.add_argument("--topic", required=True, help="새 영상 주제")
    ap.add_argument("--minutes", type=float, help="목표 길이(분). 기본: 원본과 동일")
    ap.add_argument("--tts", default="edge", choices=["edge", "silent"])
    ap.add_argument("--visual", action="store_true", help="영상 자체도 Gemini로 분석(화면 구성·색감·연출). 느리고 비용 증가")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("-o", "--out", default="out/video.mp4")
    a = ap.parse_args()
    out = pipeline.run(a.url, a.topic, Path(a.out), a.minutes, a.tts, visual=a.visual, captions=not a.no_captions,
                       on_progress=lambda f: print(f"\r렌더링 {f:4.0%}", end="", flush=True))
    print(f"\n완료: {out}")


if __name__ == "__main__":
    main()
