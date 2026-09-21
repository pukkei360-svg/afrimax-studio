#!/usr/bin/env python3
"""Generate keyframes for new scenes via z-ai image CLI (no JSON2Video)."""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent
KF = BASE / "kframes"
KF.mkdir(exist_ok=True)
story = json.loads((BASE / "story.json").read_text())


def gen(id_: str, prompt: str) -> None:
    img = KF / f"{id_}.png"
    if img.exists() and img.stat().st_size > 50_000:
        print(f"[{id_}] exists, skip", flush=True)
        return
    for attempt in range(1, 4):
        print(f"[{id_}] generating keyframe (attempt {attempt})", flush=True)
        r = subprocess.run(["z-ai", "image", "-p", prompt, "-o", str(img), "-s", "768x1344"],
                           capture_output=True, text=True, timeout=300)
        if r.returncode == 0 and img.exists() and img.stat().st_size > 50_000:
            print(f"[{id_}] OK {img.stat().st_size/1e3:.0f} KB", flush=True)
            return
        err = (r.stderr or r.stdout or "")[-200:]
        print(f"[{id_}] fail: {err}", flush=True)
        if "429" in err:
            time.sleep(45 * attempt)
        else:
            time.sleep(5)
    raise SystemExit(f"keyframe {id_} failed")


if __name__ == "__main__":
    for sc in story["scenes"]:
        if sc.get("reuse"):
            # copy reused assets into our layout
            src = Path("/home/z/my-project/scripts/afrimax_scene") / sc["reuse"]["keyframe"]
            dst = KF / f"{sc['id']}.png"
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
            print(f"[{sc['id']}] reuses {sc['reuse']['keyframe']}", flush=True)
            continue
        gen(sc["id"], sc["keyframe_prompt"])
    print("all keyframes ready", flush=True)
