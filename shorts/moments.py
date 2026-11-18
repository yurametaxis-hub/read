#!/usr/bin/env python3
"""Candidate moments in a stream piece: the loudest spots with the speech around them,
plus the full transcript with timestamps.

    python3 shorts/moments.py SOURCE.mp4 --out WORKDIR [--top 12]

Writes WORKDIR/NAME.transcript.txt and NAME.segments.json (reused on the next run).
Transcription runs at roughly half real time on this machine: an hour of stream takes about 30 min.
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np


def fmt(t):
    t = int(t)
    return f"{t // 3600}:{t % 3600 // 60:02d}:{t % 60:02d}" if t >= 3600 else f"{t // 60}:{t % 60:02d}"


def loudness(src, sr=16000, hop_s=0.5):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    hop = int(sr * hop_s)
    n = len(y) // hop
    db = 20 * np.log10(np.sqrt(np.mean(y[: n * hop].reshape(n, hop) ** 2, axis=1)) + 1e-6)
    return np.convolve(db, np.ones(3) / 3, mode="same"), hop_s  # 1.5 s smoothing, single claps do not win


def transcript(src, cache, lang, model_name):
    if cache.exists():
        return json.loads(cache.read_text())
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    it, _ = model.transcribe(src, language=lang, initial_prompt="Yo, chat! What's up? Let's go, bro. Wait, what?")
    segs = [{"s": round(s.start, 1), "e": round(s.end, 1), "t": s.text.strip()} for s in it]
    cache.write_text(json.dumps(segs, ensure_ascii=False, indent=1))
    return segs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("--out", default=".")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--gap", type=float, default=12, help="min seconds between two peaks")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--model", default="large-v3-turbo")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / Path(a.source).stem

    db, hop = loudness(a.source)
    peaks = []
    for i in np.argsort(db)[::-1]:
        t = i * hop
        if all(abs(t - p) >= a.gap for p in peaks):
            peaks.append(t)
        if len(peaks) >= a.top:
            break

    segs = transcript(a.source, Path(f"{stem}.segments.json"), a.lang, a.model)
    Path(f"{stem}.transcript.txt").write_text("\n".join(f"[{fmt(s['s'])}] {s['t']}" for s in segs) + "\n")
    print(f"transcript: {stem}.transcript.txt\nloudest moments:")
    for t in sorted(peaks):
        near = " ".join(s["t"] for s in segs if s["e"] >= t - 6 and s["s"] <= t + 6)
        print(f"{fmt(t):>8}  {db[int(t / hop)]:6.1f} dB  {near[:180]}")


if __name__ == "__main__":
    main()
