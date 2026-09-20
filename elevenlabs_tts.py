#!/usr/bin/env python3
"""OPTIONAL: ElevenLabs voiceover provider (drop-in alternative to edge-tts).

ElevenLabs voices are studio-grade but require an API key (free tier: 10k
chars/month at https://elevenlabs.io). To use instead of edge-tts:

  1. export ELEVENLABS_API_KEY="xi-..."     (or put it in .env)
  2. Edit voiceover.py: import tts from this module and replace the edge_tts call.

Compatible voices for an African storyteller narrator include e.g.
"pNInz6obpgDQGcFmaJgB" (Adam, deep) — browse the Voice Library for African
English narrators and set VOICE_ID accordingly.
"""
import os
import sys
from pathlib import Path

import requests

API = "https://api.elevenlabs.io/v1"
VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")


def tts(text: str, out: Path, model: str = "eleven_multilingual_v2") -> None:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        sys.exit("ELEVENLABS_API_KEY not set")
    r = requests.post(
        f"{API}/text-to-speech/{VOICE_ID}",
        headers={"xi-api-key": key},
        json={"text": text, "model_id": model,
              "voice_settings": {"stability": 0.5, "similarity_boost": 0.75,
                                  "style": 0.2, "use_speaker_boost": True}},
        timeout=120,
    )
    r.raise_for_status()
    out.write_bytes(r.content)
    print(f"[elevenlabs] wrote {out.name} ({len(r.content)/1e3:.0f} KB)")


if __name__ == "__main__":
    tts("What would you do, if you found a bag full of gold?",
        Path(__file__).parent / "audio" / "elevenlabs_test.mp3")
