#!/usr/bin/env python3
"""High-quality voiceover via edge-tts (GitHub open-source, Microsoft neural voices).

Voice: en-NG-AbeoNeural (Nigerian male storyteller). Output 24kHz mp3 per scene,
resampled/normalized later in the ffmpeg mix. Produces audio/vo_durations.json.
"""
import json
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
AUD = BASE / "audio"
AUD.mkdir(exist_ok=True)
story = json.loads((BASE / "story.json").read_text())
meta = story["meta"]


def ffprobe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=30)
    return float(r.stdout.strip())


def tts(text: str, out: Path) -> None:
    for attempt in range(4):
        r = subprocess.run(["python3", "-m", "edge_tts",
                            f"--voice={meta['voice']}",
                            f"--rate={meta['voice_rate']}",
                            f"--pitch={meta['voice_pitch']}",
                            "--text", text,
                            f"--write-media={out}"],
                           capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and out.exists() and out.stat().st_size > 5000:
            return
        print(f"  retry {attempt}: rc={r.returncode} {(r.stderr or '')[-150:]}", flush=True)
    raise SystemExit(f"TTS failed for {out.name}")


if __name__ == "__main__":
    durs = {}
    # moral card voiceover (meta.moral_line)
    moral_out = AUD / "moral.mp3"
    if not (moral_out.exists() and moral_out.stat().st_size > 5000):
        print(f"[moral] voicing: {meta['moral_line']}", flush=True)
        tts(meta["moral_line"], moral_out)
    durs["moral"] = round(ffprobe_dur(moral_out), 3)
    print(f"[moral] {durs['moral']:.2f}s", flush=True)
    for sc in story["scenes"]:
        out = AUD / f"{sc['id']}.mp3"
        text = " ".join(sc["narration"])
        if not (out.exists() and out.stat().st_size > 5000):
            print(f"[{sc['id']}] voicing: {text[:60]}...", flush=True)
            tts(text, out)
        d = ffprobe_dur(out)
        durs[sc["id"]] = round(d, 3)
        print(f"[{sc['id']}] {d:.2f}s", flush=True)
    (AUD / "vo_durations.json").write_text(json.dumps(durs, indent=1))
    print(f"total VO: {sum(durs.values()):.1f}s", flush=True)
