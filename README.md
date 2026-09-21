# Afrimax-Studio — African Moral Story Video Maker

Generate YouTube-ready **African animated moral-story shorts** (Afrimax-style:
9:16, warm narrator, emotional music, moral end card) using a **100% open-source
pipeline** — no JSON2Video, no watermark, no render quotas.

```
story.json ──> 01 keyframes (AI image) ──> 02 animate (AI image-to-video)
          ──> 03 voiceover (edge-tts)  ──> 04 title/moral cards (Pillow)
          ──> 05 assemble (ffmpeg)     ──> 1080x1920 MP4 + YouTube thumbnail
```

## Stack (all free / open-source)

| Step | Tool | License |
|------|------|---------|
| Keyframes | `z-ai image` (CogView) | CLI from environment |
| Motion | `z-ai video` (CogVideoX-3 image-to-video) | CLI from environment |
| Narration | **edge-tts** — Microsoft neural voices, incl. Nigerian `en-NG-AbeoNeural` | GPL-3.0 |
| Music | Kevin MacLeod "Rising" (incompetech.com) | CC-BY 4.0 |
| Cards | Pillow + Bebas Neue / Archivo Black (OFL) | MIT / OFL |
| Assembly | **ffmpeg** — xfade, slow-mo, overlay, sidechain ducking, EBU R128 | LGPL |

## Quick start

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt      # edge-tts, pillow, requests

# 1. Write your story (scenes, narration, prompts) in story.json
# 2. Run the pipeline:
python3 gen_keyframes.py             # AI keyframes per scene
python3 voiceover.py                 # narration mp3 per scene (skip if you want VO later)
python3 animate.py                   # image-to-video clips (resumable, slow - be patient)
python3 make_cards.py                # title overlay + moral end card
python3 assemble.py                  # final render (ffmpeg)
# Output: ../../download/videos/<your-story>-9x16.mp4
```

`assemble.py` automatically: measures narration loudness (EBU R128), aligns
music peak with the moral card, auto-ducks music under speech (sidechain
compression), and masters the mix to **-14 LUFS / -1.5 dBTP** (YouTube spec).

## Customizing

- **New story**: edit `story.json` — scene narration lines, keyframe/motion
  prompts, and pad per scene. Keep the character description identical in
  every prompt for consistency.
- **Voice**: `meta.voice` — any edge-tts voice (`edge-tts --list-voices`),
  e.g. `en-NG-EzinneNeural` (Nigerian female), `en-KE-ChilembaNeural` (Kenyan).
- **Duration**: scene length = voiceover + `pad`; music auto-fits.
- **ElevenLabs**: for studio-grade narration, set `ELEVENLABS_API_KEY` and use
  `elevenlabs_tts.py` instead of edge-tts (see file header).

## Tips learned the hard way

- `z-ai video` allows **one concurrent task**; on HTTP 429 back off 45s+.
  `animate.py` is fully resumable — just re-run it.
- Image-to-video inputs need a **public URL**; keyframes are uploaded to
  uguu.se (auto-cleans in ~3h) by `animate.py`.
- Motion prompts must say what **stays still** ("stable background, holds a
  stable pose") or faces/backgrounds morph.
- Slow-motion factor per scene is clamped to <= 1.0; scenes longer than the
  clip get the clip stretched, never sped up.

## Credits / licenses

- Music: "Rising" — Kevin MacLeod (incompetech.com), CC BY 4.0
- Fonts: Bebas Neue (OFL), Archivo Black (OFL)
- Voices: Microsoft neural TTS via edge-tts (GPL-3.0)

---

## House Style (v3 — channel owner approved)

**Every video: same African visual world + American-style script.**
See `SCRIPT_STYLE.md` for the full rules. Quick version:

- Visuals: Pixar-quality 3D, African setting, golden-hour grade, 9:16
- Script: American YouTube-narrator style — cold-open hook in 5s, direct
  address, short punchy sentences, escalation beats, one-line spoken moral
- Voice: `en-US-AndrewMultilingualNeural` (edge-tts, rate -10%)
  — alternates in `voice_samples/`
- Cut: **no intro title text, no moral end card** — moral is spoken over the
  final scene, then slow fade to black
- Control via `story.json` meta flags: `"title_overlay": false`,
  `"end_card": false`, `"voice"`, `"out_name"`

## Cuts of The Fisherman's Gold

| Cut | Style | File |
|-----|-------|------|
| v2 | Nigerian narrator + title + moral card | release v1.0.0 |
| v3 | American narrator, clean (no text) | release v1.1.0 |
