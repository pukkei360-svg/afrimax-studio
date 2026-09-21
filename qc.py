#!/usr/bin/env python3
"""QC the final video: frame grid (vision) + audio loudness verification."""
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
OUT = Path("/home/z/my-project/download/videos/fishermans-gold-afrimax-v2-9x16.mp4")

TIMES = [2.0, 8.7, 12.5, 24.0, 32.0, 41.0, 50.0, 60.0, 66.0, 73.0, 76.0]


def grid():
    from PIL import Image
    for i, t in enumerate(TIMES):
        subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                        "-ss", str(t), "-i", str(OUT), "-frames:v", "1",
                        "-vf", "scale=324:576", str(BASE / f"qc_f{i:02d}.png")],
                       capture_output=True, timeout=60)
    imgs = [Image.open(BASE / f"qc_f{i:02d}.png") for i in range(len(TIMES))]
    cols, rows = 4, 3
    w, h = imgs[0].size
    g = Image.new("RGB", (cols * w + (cols - 1) * 6, rows * h + (rows - 1) * 6), (12, 12, 12))
    for i, im in enumerate(imgs):
        g.paste(im, ((i % cols) * (w + 6), (i // cols) * (h + 6)))
    g.save(BASE / "qc_grid.jpg", quality=90)
    print(f"grid: {g.size} -> qc_grid.jpg", flush=True)


def audio_stats():
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(OUT),
                       "-af", "ebur128=framelog=quiet", "-f", "null", "-"],
                      capture_output=True, text=True, timeout=180)
    s = r.stderr
    I = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", s)
    TP = re.search(r"Peak:\s*(-?[\d.]+)\s*dBFS", s)
    LRA = re.search(r"LRA:\s*(-?[\d.]+)", s)
    print(f"integrated={I.group(1) if I else '?'} LUFS, "
          f"LRA={LRA.group(1) if LRA else '?'}, truepeak={TP.group(1) if TP else '?'} dBFS",
          flush=True)
    # segment loudness: speech moment vs music-only moral-card tail
    for label, ss, t in [("speech-mid (t=41)", 40.0, 6), ("moral-card tail (t=75)", 74.5, 2.4)]:
        rr = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(ss), "-t", str(t),
                             "-i", str(OUT), "-af", "ebur128=framelog=quiet",
                             "-f", "null", "-"], capture_output=True, text=True, timeout=60)
        m = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", rr.stderr)
        print(f"  {label}: {m.group(1) if m else '?'} LUFS", flush=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(OUT)], capture_output=True, text=True)
    print(f"duration={d.stdout.strip()}s", flush=True)


if __name__ == "__main__":
    if not OUT.exists():
        sys.exit("final video missing")
    audio_stats()
    grid()
