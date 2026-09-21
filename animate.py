#!/usr/bin/env python3
"""Animate keyframes via z-ai video i2v (cogvideox-3). Resumable, no JSON2Video.

Image input needs a public URL: keyframes are uploaded to uguu.se (temp host).
Reuses task-4 pattern: sequential submission, state files, 429 backoff.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import requests

BASE = Path(__file__).parent
KF = BASE / "kframes"
CLIPS = BASE / "clips"
CLIPS.mkdir(exist_ok=True)
story = json.loads((BASE / "story.json").read_text())


def run_cli(args: list, timeout: int = 420, on_429_sleep: int = 45) -> dict:
    for attempt in range(1, 8):
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        out_path = Path(args[args.index("--output") + 1])
        if r.returncode == 0 and out_path.exists():
            try:
                return json.loads(out_path.read_text())
            except json.JSONDecodeError:
                pass
        err = (r.stderr or "") + (r.stdout or "")
        if ("429" in err or "Too many requests" in err) and attempt < 7:
            wait = on_429_sleep * attempt
            print(f"    429, backing off {wait}s (attempt {attempt})", flush=True)
            time.sleep(wait)
            continue
        raise RuntimeError(f"CLI rc={r.returncode} tail: {err.strip()[-300:]}")


def upload_uguu(path: Path) -> str:
    for attempt in range(3):
        r = requests.post("https://uguu.se/upload.php",
                          files={"files[]": (path.name, open(path, "rb"), "image/png")},
                          timeout=60)
        if r.status_code == 200:
            url = r.json()["files"][0]["url"]
            assert requests.head(url, timeout=15).status_code == 200, "head check failed"
            return url
        print(f"    uguu {r.status_code}, retry {attempt}", flush=True)
        time.sleep(10)
    raise RuntimeError(f"uguu upload failed for {path.name}")


def clip_done(id_: str) -> bool:
    mp4 = CLIPS / f"{id_}.mp4"
    return mp4.exists() and mp4.stat().st_size > 300_000


def animate(id_: str, motion_prompt: str) -> None:
    state = BASE / f"state_{id_}.json"
    url = None
    for cycle in range(60):  # bounded retries overall
        if clip_done(id_):
            print(f"[{id_}] clip exists, skip", flush=True)
            return
        data = json.loads(state.read_text()) if state.exists() else None
        st = data.get("task_status") if data else None
        if st in ("FAILED", "ERROR"):
            print(f"[{id_}] task failed -> resubmitting", flush=True)
            state.unlink(missing_ok=True)
            continue
        try:
            if data and data.get("id") and st in ("PROCESSING", "PENDING"):
                print(f"[{id_}] polling cycle {cycle}", flush=True)
                data = run_cli(["z-ai", "async-result", "-i", data["id"], "--poll",
                                "--poll-interval", "5", "--max-polls", "110",
                                "--output", str(state)], timeout=680)
            elif st == "SUCCESS":
                pass  # fall through to download
            else:
                url = upload_uguu(KF / f"{id_}.png")
                print(f"[{id_}] hosted at {url}", flush=True)
                print(f"[{id_}] submitting i2v", flush=True)
                data = run_cli(["z-ai", "video", "-i", url, "-p", motion_prompt,
                                "-s", "768x1344", "-d", "10", "-q", "quality", "--fps", "30",
                                "--poll", "--poll-interval", "5", "--max-polls", "110",
                                "--output", str(state)], timeout=680)
        except subprocess.TimeoutExpired:
            print(f"[{id_}] poll cycle timed out (task still server-side), retrying", flush=True)
            continue
        if data.get("task_status") != "SUCCESS":
            print(f"[{id_}] status={data.get('task_status')}, continuing", flush=True)
            time.sleep(10)
            continue
        url = (data.get("video_result") or [{}])[0].get("url")
        try:
            r = requests.get(url, timeout=300)
            r.raise_for_status()
            (CLIPS / f"{id_}.mp4").write_bytes(r.content)
            print(f"[{id_}] downloaded {len(r.content)/1e6:.1f} MB", flush=True)
            return
        except Exception as e:  # noqa: BLE001
            print(f"[{id_}] download retry: {e}", flush=True)
            time.sleep(15)
    raise SystemExit(f"animate {id_} exhausted retries")


if __name__ == "__main__":
    # copy reused clips first
    for sc in story["scenes"]:
        if sc.get("reuse"):
            src = Path("/home/z/my-project/scripts/afrimax_scene") / sc["reuse"]["clip"]
            dst = CLIPS / f"{sc['id']}.mp4"
            if not dst.exists():
                dst.write_bytes(src.read_bytes())
            print(f"[{sc['id']}] reuses {sc['reuse']['clip']}", flush=True)
    for sc in story["scenes"]:
        if sc.get("reuse"):
            continue
        animate(sc["id"], sc["motion_prompt"])
    done = [sc["id"] for sc in story["scenes"] if clip_done(sc["id"])]
    print(f"\nclips done: {done}", flush=True)
    sys.exit(0 if len(done) == len(story["scenes"]) else 1)
