#!/usr/bin/env python3
"""Assemble the final Afrimax-style video with pure ffmpeg (no JSON2Video).

Chunked to survive environment process kills:
  stage 'segs' : render each scene segment (stretched, CFR30, yuv420p) — re-runnable
  stage 'final': xfade chain + title overlay + audio bus + loudness master
  (no stage)  : both in order

Timeline model identical to v1: scene length = VO + pad; xfade offsets
auto-computed; VO delayed per scene; moral card = VO + 3.4s.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
CLIPS, AUD, CARDS = BASE / "clips", BASE / "audio", BASE / "cards"
SEGS = BASE / "segs"
SEGS.mkdir(exist_ok=True)
OUT = Path("/home/z/my-project/download/videos")
OUT.mkdir(parents=True, exist_ok=True)
story = json.loads((BASE / "story.json").read_text())
meta = story["meta"]

D = 0.9          # xfade duration
FPS = 30
TARGET_MIX = -14.0   # LUFS, YouTube standard
MUSIC_SOLO = -19.0  # LUFS of music bed when narration is absent


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return r


def probe_dur(p: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(p)], capture_output=True, text=True, timeout=30)
    return float(r.stdout.strip())


def measure_lufs(input_path: Path, ss: float = 0, t: float = 90) -> float:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(ss), "-t", str(t),
                        "-i", str(input_path), "-af", "ebur128=framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True, timeout=180)
    m = re.search(r"I:\s*(-?[\d.]+)\s*LUFS", r.stderr)
    return float(m.group(1)) if m else -70.0


# ---------- timeline ----------
def build_timeline():
    vo = json.loads((AUD / "vo_durations.json").read_text())
    scenes = story["scenes"]
    L, vo_start = [], []
    for sc in scenes:
        L.append(round(vo[sc["id"]] + sc.get("pad", 1.2), 3))
    L.append(round(vo["moral"] + 3.4, 3))  # moral card
    S = [0.0]
    for i in range(1, len(L)):
        S.append(round(S[-1] + L[i - 1] - D, 3))
    for i, sc in enumerate(scenes):
        lead = 1.2 if i == 0 else 0.55
        vo_start.append(round(S[i] + lead, 3))
    vo_start.append(round(S[-1] + 1.1, 3))  # moral
    total = round(S[-1] + L[-1], 3)
    tl = {"scene_len": L, "scene_start": S, "vo_start": vo_start, "total": total}
    (BASE / "timeline.json").write_text(json.dumps(tl, indent=1))
    return L, S, vo_start, total


# ---------- stage 1: segments ----------
def seg_ok(i: int, L: list) -> bool:
    p = SEGS / f"seg{i}.mp4"
    return p.exists() and p.stat().st_size > 100_000


def render_segment(i: int, L: list) -> bool:
    """Render one segment; returns True when complete. Each call ~30-90s."""
    if seg_ok(i, L):
        return True
    n_scenes = len(story["scenes"])
    if i < n_scenes:
        src = CLIPS / f"{story['scenes'][i]['id']}.mp4"
        sp = min(1.0, probe_dur(src) / L[i])
        fc = (f"[0:v]scale=1080:1920:flags=lanczos,setsar=1,"
              f"setpts=PTS/{sp:.4f},trim=duration={L[i]:.3f},"
              f"setpts=PTS-STARTPTS,fps={FPS},format=yuv420p[v]")
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-i", str(src)]
    else:  # moral card: -loop MUST precede -i
        fc = (f"[0:v]crop=1080:1920:54:'54+84*min(t/{L[i]:.3f},1)',"
              f"trim=duration={L[i]:.3f},setpts=PTS-STARTPTS,"
              f"fps={FPS},format=yuv420p[v]")
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
               "-loop", "1", "-framerate", str(FPS), "-t", f"{L[i] + 0.5:.3f}",
               "-i", str(CARDS / "moral.png")]
    cmd += ["-filter_complex", fc, "-map", "[v]",
        "-c:v", "libx264", "-preset", "superfast", "-crf", "16",
        "-r", str(FPS), "-pix_fmt", "yuv420p", "-t", f"{L[i]:.3f}",
        str(SEGS / f"seg{i}.mp4")]
    print(f"[seg{i}] rendering ({L[i]:.1f}s) ...", flush=True)
    r = run(cmd, timeout=580)
    ok = r.returncode == 0 and (SEGS / f"seg{i}.mp4").stat().st_size > 100_000
    print(f"[seg{i}] {'OK' if ok else 'FAIL ' + r.stderr[-400:]}", flush=True)
    return ok


def stage_segs(L: list) -> None:
    for i in range(len(L)):
        if not render_segment(i, L):
            sys.exit(f"segment {i} failed; re-run this stage")
    print("all segments ready", flush=True)


# ---------- stage 2: final ----------
def stage_final(L: list, S: list, vo_start: list, total: float) -> None:
    n = len(L)
    bad = [i for i in range(n) if not seg_ok(i, L)]
    if bad:
        sys.exit(f"broken/missing segments {bad}; run stage 'segs' first")
    cmd = ["ffmpeg", "-y", "-hide_banner"]
    for i in range(n):
        cmd += ["-i", str(SEGS / f"seg{i}.mp4")]          # 0..n-1
    cmd += ["-loop", "1", "-t", "13", "-i", str(CARDS / "title.png")]   # n
    for sc in story["scenes"]:
        cmd += ["-i", str(AUD / f"{sc['id']}.mp3")]        # n+1 ..
    cmd += ["-i", str(AUD / "moral.mp3")]                  # 2n
    cmd += ["-i", str(BASE / "music" / "rising.mp3")]      # 2n+1

    vf = []
    for i in range(n):
        vf.append(f"[{i}:v]fps={FPS},format=yuv420p[v{i}]")
    prev = "v0"
    for i in range(1, n):
        trans = "fadeblack" if i == n - 1 else "fade"
        out = f"x{i}" if i < n - 1 else "xend"
        vf.append(f"[{prev}][v{i}]xfade=transition={trans}:duration={D}:"
                  f"offset={S[i]:.3f}[{out}]")
        prev = out
    vf.append(f"[{n}:v]format=rgba,fps={FPS},fade=t=in:st=6.9:d=0.7:alpha=1,"
              f"fade=t=out:st=10.9:d=0.8:alpha=1[tit]")
    vf.append("[xend][tit]overlay=0:0:eof_action=pass[vov]")
    vf.append(f"[vov]fade=t=in:st=0:d=0.9,fade=t=out:st={total-1.2:.3f}:d=1.2,"
              "format=yuv420p[vout]")

    music_lufs = measure_lufs(BASE / "music" / "rising.mp3", ss=55, t=total)
    mgain = round(MUSIC_SOLO - music_lufs, 2)
    print(f"music window LUFS={music_lufs} -> gain {mgain} dB", flush=True)

    af = []
    for idx in range(n):
        af.append(f"[{n+1+idx}:a]aresample=48000,highpass=f=70[a{idx}]")
        af.append(f"[a{idx}]adelay={int(vo_start[idx]*1000)}:all=1[d{idx}]")
    amixin = "".join(f"[d{i}]" for i in range(n))
    af.append(f"{amixin}amix=inputs={n}:normalize=0:duration=longest[nm]")
    af.append("[nm]loudnorm=I=-15:TP=-2:LRA=7,aresample=48000,asplit=2[narr][nsc]")
    af.append(f"[{2*n+1}:a]aresample=48000,atrim=start=55:duration={total},"
              f"asetpts=PTS-STARTPTS,volume={mgain}dB,afade=t=in:st=0:d=1.3,"
              f"afade=t=out:st={total-3.2:.3f}:d=3.2[mus]")
    af.append("[mus][nsc]sidechaincompress=threshold=0.05:ratio=4:attack=250:"
              "release=1000[musd]")
    af.append(f"[musd][narr]amix=inputs=2:normalize=0:duration=longest,"
              f"atrim=duration={total:.3f},asetpts=PTS-STARTPTS,aresample=48000[aout]")

    fc = ";".join(vf + af)
    (BASE / "filtergraph.txt").write_text(fc)
    out1 = OUT / "fishermans-gold-afrimax-v2-9x16.mp4"
    print("final pass: xfade + audio ...", flush=True)
    cmd += ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
            "-c:v", "libx264", "-preset", "superfast", "-crf", "19", "-r", str(FPS),
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
            "-movflags", "+faststart", "-t", str(total), str(out1)]
    r = run(cmd, timeout=580)
    if r.returncode != 0:
        print(r.stderr[-2500:])
        sys.exit("final pass failed; re-run stage 'final'")
    print("final pass done", flush=True)

    # ---- loudness trim pass ----
    I = measure_lufs(out1)
    trim = round(TARGET_MIX - I, 2)
    print(f"mix LUFS={I} -> trim {trim} dB", flush=True)
    if abs(trim) >= 0.4:
        final = OUT / "fishermans-gold-afrimax-v2-final.mp4"
        r = run(["ffmpeg", "-y", "-hide_banner", "-i", str(out1),
                 "-af", f"volume={trim}dB,alimiter=limit=0.891:level=false",
                 "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                 str(final)], timeout=300)
        if r.returncode != 0:
            print(r.stderr[-1500:])
            sys.exit("trim pass failed")
        out1.unlink()
        final.rename(out1)
        I = measure_lufs(out1)
    print(f"final loudness: {I} LUFS", flush=True)

    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-ss", "8.5", "-i", str(out1),
                   "-frames:v", "1", "-q:v", "3",
                   str(OUT / "fishermans-gold-afrimax-v2.jpg")], capture_output=True)
    print(f"DONE: {out1}", flush=True)


def main():
    stage = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "all"
    ids = [sc["id"] for sc in story["scenes"]]
    missing = [i for i in ids if not (CLIPS / f"{i}.mp4").exists()]
    if missing:
        sys.exit(f"missing clips: {missing} (run animate.py first)")
    L, S, vo_start, total = build_timeline()
    print(f"timeline: total={total}s  L={L}\n  S={S}\n  VO={vo_start}", flush=True)
    if stage in ("segs", "all"):
        stage_segs(L)
    if stage in ("final", "all"):
        stage_final(L, S, vo_start, total)


if __name__ == "__main__":
    main()
