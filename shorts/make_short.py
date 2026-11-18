#!/usr/bin/env python3
"""Stacked reaction short for TikTok and YouTube Shorts (1080x1920).

Top part: the streamer's facecam. Bottom part: what they are watching.
A title plaque sits on the seam, word by word captions go under it.

    python3 shorts/make_short.py --grid SOURCE.mp4 120     # gridded frame for picking crop boxes
    python3 shorts/make_short.py shorts/jobs/example.json   # build the clip

Job keys (times are seconds in the SOURCE, boxes are [x, y, w, h] in source pixels):
  source, start, end, out   required
  top, bottom               crop boxes, required; scaled to cover their part, extra is cut evenly
  split                     seam height in the output frame, default 960
  title                     plaque text, emoji are fine, *word* gets the accent color
  accent                    accent color for *word*, default red
  captions                  true or false, default true
  captions_y                vertical centre of captions, default split + 470 (clear of the app buttons)
  fixes                     {"Lucien": "Lucia"} replacements for recognized words
  punch                     [[start, end], ...] quick zoom on the top part at these source times
  punch_box                 crop box used during punches, default: top box zoomed 1.25x on its centre
  lang, whisper_model       default "en" and "large-v3-turbo"
Words are cached in OUT.words.json; edit that file and rerun to fix captions by hand.
"""
import argparse
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FILLERS = {"UH", "UM", "UHM", "ERM", "HMM", "MM"}


def sh(cmd, capture=False):
    cmd = [str(c) for c in cmd]
    r = subprocess.run(cmd, text=True, capture_output=capture)
    if r.returncode:
        sys.exit(f"command failed: {' '.join(cmd)[:400]}\n{(r.stderr or '')[-2000:]}")
    return (r.stdout or "") + (r.stderr or "")


def probe(src):
    out = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=width,height,r_frame_rate", "-of", "json", src], capture=True)
    s = json.loads(out)["streams"][0]
    num, den = map(int, s["r_frame_rate"].split("/"))
    return s["width"], s["height"], num / den


def grid(src, t, out):
    w, h, _ = probe(src)
    step = 40 if w <= 960 else 80
    size = max(10, w // 64)
    parts = [f"drawgrid=w={step}:h={step}:t=1:c=white@0.35"]
    parts += [f"drawtext=fontfile={FONT}:text={x}:x={x}+2:y=2:fontsize={size}:fontcolor=yellow"
              for x in range(0, w, step * 2)]
    parts += [f"drawtext=fontfile={FONT}:text={y}:x=2:y={y}+2:fontsize={size}:fontcolor=cyan"
              for y in range(step * 2, h, step * 2)]
    parts.append(f"scale={max(1280, w)}:-2:flags=neighbor")
    sh(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", src, "-frames:v", "1", "-vf", ",".join(parts), out])
    print(out)


def transcribe(src, start, dur, cache, lang, model_name):
    """Words with times relative to the clip start. A few seconds before the clip go in
    as context, without it the model drops punctuation and captions group badly."""
    if cache.exists():
        return json.loads(cache.read_text())
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    pad = min(start, 15.0)
    with tempfile.TemporaryDirectory() as td:
        wav = Path(td) / "a.wav"
        sh(["ffmpeg", "-v", "error", "-y", "-ss", start - pad, "-t", dur + pad, "-i", src,
            "-ac", "1", "-ar", "16000", wav])
        model = WhisperModel(model_name, device="cpu", compute_type="int8")
        segs, _ = model.transcribe(str(wav), language=lang, word_timestamps=True,
                                   initial_prompt="Yo, chat! What's up? Let's go, bro. Wait, what?")
        words = [{"w": w.word.strip(), "s": round(w.start - pad, 2), "e": round(w.end - pad, 2)}
                 for s in segs for w in s.words if w.word.strip()]
    words = [w for w in words if w["e"] > 0.05 and w["s"] < dur]
    for w in words:
        w["s"] = max(w["s"], 0.0)
    cache.write_text(json.dumps(words, ensure_ascii=False, indent=1))
    return words


def clean(word, fixes):
    for a, b in fixes.items():
        word = re.sub(rf"\b{re.escape(a)}\b", b, word, flags=re.I)
    word = re.sub(r"[,.…]+$", "", word)
    return word.upper()


def group_words(words, max_words=3, max_chars=14, gap=0.35):
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= max_words or w["s"] - cur[-1]["e"] > gap
                    or len(" ".join(x["t"] for x in cur + [w])) > max_chars
                    or re.search(r"[.!?…]$", cur[-1]["w"])):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build_ass(words, path, y, fixes):
    import pysubs2
    for w in words:
        w["t"] = clean(w["w"], fixes)
    words = [w for w in words if w["t"] and w["t"].strip("!?") not in FILLERS]
    subs = pysubs2.SSAFile()
    subs.info.update({"PlayResX": str(W), "PlayResY": str(H), "WrapStyle": "0", "ScaledBorderAndShadow": "yes"})
    subs.styles["Cap"] = pysubs2.SSAStyle(
        fontname="Montserrat Black", fontsize=76, primarycolor=pysubs2.Color(255, 255, 255),
        outlinecolor=pysubs2.Color(0, 0, 0), backcolor=pysubs2.Color(0, 0, 0, 110),
        outline=7, shadow=4, alignment=pysubs2.Alignment.MIDDLE_CENTER, marginl=120, marginr=120)
    groups = group_words(words)
    for gi, g in enumerate(groups):
        nxt = groups[gi + 1][0]["s"] if gi + 1 < len(groups) else None
        for j, w in enumerate(g):
            end = g[j + 1]["s"] if j + 1 < len(g) else w["e"] + 0.25
            if j + 1 == len(g) and nxt is not None:
                end = min(end, nxt)
            end = max(end, w["s"] + 0.08)
            line = " ".join("{\\c&H00E1FF&}" + x["t"] + "{\\c&HFFFFFF&}" if k == j else x["t"]
                            for k, x in enumerate(g))
            pop = "{\\fscx86\\fscy86\\t(0,90,\\fscx100\\fscy100)}" if j == 0 else ""
            subs.append(pysubs2.SSAEvent(start=int(w["s"] * 1000), end=int(end * 1000), style="Cap",
                                         text=f"{{\\pos(540,{y})}}{pop}{line}"))
    subs.save(str(path))


def render_title(text, out, accent):
    esc = re.sub(r"\*(.+?)\*", r"<b>\1</b>", html.escape(text))
    sh(["node", HERE / "render_title.js", out, json.dumps({"html": esc, "accent": accent})])


def loudnorm_filter(src, start, dur):
    base = "loudnorm=I=-14:TP=-1.5:LRA=11"
    out = sh(["ffmpeg", "-hide_banner", "-ss", start, "-t", dur, "-i", src, "-vn",
              "-af", base + ":print_format=json", "-f", "null", "-"], capture=True)
    m = json.loads(out[out.rindex("{"):out.rindex("}") + 1])
    return (f"{base}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
            f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample=48000")


def cover(box, w, h, pre):
    x, y, bw, bh = box
    return (f"crop={bw}:{bh}:{x}:{y},{pre}scale={w}:{h}:force_original_aspect_ratio=increase:flags=lanczos,"
            f"crop={w}:{h},setsar=1")


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    src, out = job["source"], Path(job["out"])
    start, end = float(job["start"]), float(job["end"])
    dur = round(end - start, 3)
    split = int(job.get("split", 960))
    out.parent.mkdir(parents=True, exist_ok=True)
    work = out.with_suffix("")
    _, _, fps = probe(src)
    pre = "hqdn3d=1.5:1.5:6:6," if job.get("denoise", True) else ""

    inputs = ["-ss", start, "-t", dur, "-i", src]
    fg, last = [], None
    punches = job.get("punch", [])
    fg.append("[0:v]split=3[vt][vb][vp]" if punches else "[0:v]split=2[vt][vb]")
    fg.append(f"[vt]{cover(job['top'], W, split, pre)}[top0]")
    if punches:
        x, y, bw, bh = job["top"]
        pbox = job.get("punch_box") or [round(x + bw * 0.1), round(y + bh * 0.1), round(bw * 0.8), round(bh * 0.8)]
        fg.append(f"[vp]{cover(pbox, W, split, pre)}[topz]")
        en = "+".join(f"between(t,{a - start:.3f},{b - start:.3f})" for a, b in punches)
        fg.append(f"[top0][topz]overlay=0:0:enable='{en}'[top]")
    else:
        fg[-1] = fg[-1].replace("[top0]", "[top]")
    fg.append(f"[vb]{cover(job['bottom'], W, H - split, pre)}[bot]")
    fg.append("[top][bot]vstack=inputs=2,unsharp=5:5:0.6:5:5:0[v1]")
    last = "v1"

    if job.get("title"):
        png = Path(str(work) + ".title.png")
        render_title(job["title"], png, job.get("accent", "#e0262f"))
        inputs += ["-loop", "1", "-i", png]
        fg.append(f"[{last}][1:v]overlay=(W-w)/2:{split}-h/2[v2]")
        last = "v2"

    if job.get("captions", True):
        words = transcribe(src, start, dur, Path(str(work) + ".words.json"),
                           job.get("lang", "en"), job.get("whisper_model", "large-v3-turbo"))
        ass = Path(str(work) + ".ass")
        build_ass(words, ass, int(job.get("captions_y", split + 470)), job.get("fixes", {}))
        fg.append(f"[{last}]ass={ass}:fontsdir=/usr/share/fonts[v3]")
        last = "v3"

    fg.append(f"[0:a]{loudnorm_filter(src, start, dur)}[aout]")
    sh(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
        "-filter_complex", ";".join(fg), "-map", f"[{last}]", "-map", "[aout]",
        "-t", dur, "-r", f"{min(fps, 60):.5f}", "-c:v", "libx264", "-preset", "slow", "-crf", "18",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", out])
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job", nargs="?")
    ap.add_argument("--grid", nargs=2, metavar=("SOURCE", "SECONDS"))
    ap.add_argument("--grid-out", default="grid.png")
    a = ap.parse_args()
    if a.grid:
        grid(a.grid[0], a.grid[1], a.grid_out)
    elif a.job:
        build(a.job)
    else:
        ap.print_help()
