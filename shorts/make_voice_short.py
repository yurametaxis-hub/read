#!/usr/bin/env python3
"""Vertical short (1080x1920) with an AI voice-over: footage band over a blurred fill, title plaque on the
band's top edge, word-by-word captions, red marker circles and pop-up texts.

    python3 shorts/make_voice_short.py shorts/jobs/voice_bear.json

The job follows make_longform.py: "sources" (path, optional crop and scenes) and "paragraphs" of
sentences, each with its shots; Kokoro reads the sentences. Extra keys:
  title, title_sub, accent   plaque on the band's top edge, *word* gets the accent colour
  fg_h, fg_y                 band height and top edge, default 1000 and 420
  captions_y                 caption line centre, default fg_y + fg_h - 150
  game_volume                source audio under the voice, default 0.35; use 0 when the source has
                             someone else's voice in it
  fixes                      caption spelling fixes, as in make_short.py
  tail                       seconds after the last word, default 1.0
Shot keys: src, t or t_end, x, y, zoom, speed, w, label, boom, whoosh, repeat (as in make_longform.py), plus
  x_end                      glide the crop from x to x_end over the shot, to follow someone walking
  circle: [x, y, r]          red marker circle around a point given in source pixels (at the start of the shot)
  circle_t: [a, b]           seconds into the shot when the circle shows, default from 0.2 to the end
  text: "WAIT..."            pop-up text near the top of the band for the length of the shot
Source keys: path, crop, scenes, and delogo: [[x, y, w, h], ...] to paint over another channel's watermark.
"""
import argparse
import difflib
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import make_longform as LF  # noqa: E402
from make_edit import build_texts, crop_box  # noqa: E402
from make_short import build_ass, render_title  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
VERSION = 1
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def probe_size(path):
    out = LF.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                  "-of", "csv=p=0", path])
    w, h = out.strip().split(",")[:2]
    return int(w), int(h)


def circle_png(path, cx, cy, r, seed):
    """Marker style ellipse that overshoots its start a little, drawn at 2x and scaled down for smooth edges."""
    rnd, s = random.Random(seed), 2
    pts = []
    for i in range(81):
        a = -2.2 + (2 * math.pi + 0.45) * i / 80
        g = (1 + 0.08 * i / 80) * (1 + rnd.uniform(-0.015, 0.015))
        pts.append(((cx + r * 1.15 * g * math.cos(a)) * s, (cy + r * 0.85 * g * math.sin(a)) * s))
    img = Image.new("RGBA", (W * s, H * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.line([(x + 3 * s, y + 5 * s) for x, y in pts], fill=(0, 0, 0, 110), width=16 * s, joint="curve")
    d.line(pts, fill=(255, 32, 32, 255), width=12 * s, joint="curve")
    img.resize((W, H), Image.LANCZOS).save(path)


def render_shot(sh, nframes, sources, sdir, fg_h, fg_y):
    dur = nframes / FPS
    src = sources[sh["src"]]
    sig = hashlib.sha1(json.dumps([sh, nframes, fg_h, fg_y, VERSION, src["path"], src.get("crop"),
                                   src.get("delogo")]).encode()).hexdigest()[:14]
    final_v, final_a = sdir / f"{sig}.mp4", sdir / f"{sig}.wav"
    if final_v.exists() and final_a.exists():
        return final_v, final_a
    vout, aout = sdir / f"{sig}.part.mp4", sdir / f"{sig}.part.wav"
    sp = float(sh.get("speed", 1.0))
    need, t = dur * sp, sh["_t"]
    # watermarks of other channels are painted over before anything is cropped
    pre = "".join(f"delogo=x={x}:y={y}:w={w}:h={h}," for x, y, w, h in src.get("delogo", []))
    sw, shh = src["w"], src["h"]
    if src.get("crop"):
        c = src["crop"]
        pre += f"crop={c[2]}:{c[3]}:{c[0]}:{c[1]},"
        sw, shh = c[2], c[3]
    z = float(sh.get("zoom", 1.0))
    cw, ch, cx, cy = crop_box(sw, shh, fg_h, sh.get("x", 0.5), sh.get("y", 0.5), z)
    xexpr = str(cx)
    if sh.get("x_end") is not None:  # glide sideways to keep a moving subject in frame
        cx2 = crop_box(sw, shh, fg_h, sh["x_end"], sh.get("y", 0.5), z)[2]
        xexpr = f"'{cx}+({cx2}-{cx})*(0.5-0.5*cos(PI*min(t/{dur:.3f},1)))'"
    fc = (f"[0:v]setpts=PTS-STARTPTS,{pre}" + (f"setpts=PTS/{sp}," if sp != 1 else "") +
          f"fps={FPS},tpad=stop_mode=clone:stop_duration=30,split=2[a][b];"
          f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=22:2,"
          "eq=brightness=-0.14:saturation=0.8[bg];"
          f"[b]crop={cw}:{ch}:{xexpr}:{cy},scale={W}:{fg_h}:flags=lanczos,setsar=1,"
          "eq=contrast=1.05:saturation=1.12,unsharp=5:5:0.5:5:5:0[fg];"
          f"[bg][fg]overlay=0:{fg_y}")
    tag = sh.get("label")
    if tag in LF.TAG:
        fc += (f",drawtext=fontfile={LF.FONT_XB}:text='{tag}':fontsize=40:fontcolor=white:box=1:"
               f"boxcolor={LF.TAG[tag]}@0.95:boxborderw=14:x=36:y={fg_y + 84}")
    ins = ["-ss", f"{t:.3f}", "-t", f"{need + 1:.3f}", "-i", src["path"]]
    if sh.get("circle"):
        x, y, r = sh["circle"]
        s = W / cw
        png = sdir / f"{sig}.circle.png"
        circle_png(png, (x - cx) * s, fg_y + (y - cy) * s, r * s, seed=int(sig[:6], 16))
        ins += ["-loop", "1", "-i", png]
        c0, c1 = sh.get("circle_t", [0.2, dur + 1])
        fc += f"[v0];[v0][1:v]overlay=0:0:enable='between(t,{c0},{c1})'"
    LF.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", fc, "-frames:v", nframes, "-an", *ENC, vout])
    LF.clip_audio(src["path"], t, need, dur, sp, aout)
    vout.replace(final_v)
    aout.replace(final_a)
    return final_v, final_a


def narration_words(work, sents):
    """Word timings for the captions: Whisper on the clean TTS track, spelled as in the script."""
    key = hashlib.sha1(json.dumps([[s["text"], round(s["t0"], 2)] for s in sents]).encode()).hexdigest()
    cache = work / "narration.words.json"
    if cache.exists():
        data = json.loads(cache.read_text())
        if data.get("key") == key:
            return data["words"]
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    from faster_whisper import WhisperModel
    model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = model.transcribe(str(work / "narration.wav"), language="en", word_timestamps=True)
    heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
    norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
    out = []
    for s in sents:
        script = s["text"].split()
        cand = [h for h in heard if s["t0"] - 0.25 <= h[1] <= s["t1"] + 0.25]
        times = [None] * len(script)
        sm = difflib.SequenceMatcher(None, [norm(x) for x in script], [norm(h[0]) for h in cand], autojunk=False)
        for a, b, size in sm.get_matching_blocks():
            for k in range(size):
                times[a + k] = (cand[b + k][1], cand[b + k][2])
        k = 0
        while k < len(script):  # fill words Whisper spelled differently, by character share of the gap
            if times[k] is not None:
                k += 1
                continue
            j = k
            while j < len(script) and times[j] is None:
                j += 1
            lo = times[k - 1][1] if k > 0 else s["t0"]
            hi = times[j][0] if j < len(script) else s["t1"]
            lens = [len(w) + 1 for w in script[k:j]]
            acc = lo
            for m, ln in zip(range(k, j), lens):
                step = (hi - lo) * ln / sum(lens)
                times[m] = (acc, acc + step)
                acc += step
            k = j
        out += [{"w": w, "s": round(a, 3), "e": round(b, 3)} for w, (a, b) in zip(script, times)]
    cache.write_text(json.dumps({"key": key, "words": out}))
    return out


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    fg_h, fg_y = int(job.get("fg_h", 1000)), int(job.get("fg_y", 420))
    sources = job["sources"]
    for s in sources.values():
        s["dur"] = LF.duration(s["path"])
        s["w"], s["h"] = probe_size(s["path"])
    sents = []
    for p in job["paragraphs"]:
        for k, s in enumerate(p["sentences"]):
            s["last_in_par"] = k == len(p["sentences"]) - 1
            sents.append(s)
    LF.narrate(job, work, sents)
    total = sents[-1]["t1"] + float(job.get("tail", 1.0))
    print(f"narration {total:.1f}s, {sum(len(s['text'].split()) for s in sents)} words")

    tl = []
    for i, s in enumerate(sents):
        a = 0.0 if i == 0 else s["t0"]
        b = sents[i + 1]["t0"] if i + 1 < len(sents) else total
        if not s.get("shots"):
            tl[-1]["end"] = b
            continue
        ws = [sh.get("w", 1) for sh in s["shots"]]
        t = a
        for sh, w in zip(s["shots"], ws):
            d = (b - a) * w / sum(ws)
            tl.append({"shot": sh, "start": t, "end": t + d})
            t += d
    frames = [round(x["end"] * FPS) - round(x["start"] * FPS) for x in tl]
    warnings = []
    for x, n in zip(tl, frames):
        sh = x["shot"]
        sh["_t"], w = LF.check_shot(sh, n / FPS * float(sh.get("speed", 1.0)), sources)
        if w:
            warnings.append(f"{x['start']:5.1f}s {w}")
    print("\n".join(["shot warnings:"] + warnings) if warnings else "shots ok")

    sdir = work / "shots"
    sdir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda a: render_shot(*a), [(x["shot"], n, sources, sdir, fg_h, fg_y) for x, n in zip(tl, frames)]))
    (work / "list.txt").write_text("".join(f"file '{v}'\n" for v, _ in res))
    LF.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", work / "list.txt", "-c", "copy", work / "broll.mp4"])

    def exact(a, n):
        x = sf.read(a, dtype="float32", always_2d=True)[0][: n * SR // FPS]
        return np.pad(x, ((0, n * SR // FPS - len(x)), (0, 0)))
    sf.write(work / "game.wav", np.concatenate([exact(a, n) for (_, a), n in zip(res, frames)]), SR)

    events = []
    for x in tl:
        sh = x["shot"]
        if sh.get("whoosh"):
            events.append(("whoosh", max(x["start"] - 0.3, 0.0)))
        if "boom" in sh:
            events.append(("boom", x["start"] + sh["boom"]))
    LF.sfx_track(total, events, work, work / "sfx.wav")
    LF.synth_pad(total, work / "pad.wav")

    cap_y = int(job.get("captions_y", fg_y + fg_h - 150))
    build_ass(narration_words(work, sents), work / "captions.ass", cap_y, job.get("fixes", {}))
    pops = [{"text": x["shot"]["text"], "start": x["start"], "end": x["end"], "y": fg_y + 170, "size": 70}
            for x in tl if x["shot"].get("text")]
    build_texts(pops, work / "texts.ass")

    def gain_to(path, target):
        meas = LF.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"])
        i = float(json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])["input_i"])
        return 0.0 if i < -70 else target - i
    gv = float(job.get("game_volume", 0.35))
    gn = gain_to(work / "narration.wav", -16)
    gg = gain_to(work / "game.wav", -22) if gv > 0 else 0.0
    pad_v = 0.45 if gv > 0 else 0.7
    mix = (f"[0:a]aresample=48000,aformat=channel_layouts=stereo,volume={gn:.2f}dB,apad=whole_dur={total:.3f},asplit=3[n1][n2][n3];"
           f"[1:a]volume={gg:.2f}dB,volume={gv * 2:.3f},apad=whole_dur={total:.3f}[g0];"
           "[g0][n2]sidechaincompress=threshold=0.015:ratio=12:attack=10:release=400[gd];"
           f"[2:a]volume={pad_v},apad=whole_dur={total:.3f}[m0];[m0][n3]sidechaincompress=threshold=0.015:ratio=4:attack=40:release=800[md];"
           f"[3:a]apad=whole_dur={total:.3f}[fx];[n1][gd][md][fx]amix=inputs=4:normalize=0:duration=first[mix]")
    LF.run(["ffmpeg", "-v", "error", "-y", "-i", work / "narration.wav", "-i", work / "game.wav", "-i", work / "pad.wav",
            "-i", work / "sfx.wav", "-filter_complex", mix, "-map", "[mix]", "-t", total, work / "mix.wav"])
    meas = LF.run(["ffmpeg", "-hide_banner", "-i", work / "mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    loud = (f"apad=whole_dur={total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
            "aresample=48000")

    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    ins, vf, last = ["-i", work / "broll.mp4", "-i", work / "mix.wav"], [], "0:v"
    if job.get("title"):
        png = work / "title.png"
        render_title(job["title"], png, job.get("accent", "#e0262f"), job.get("title_sub"), job.get("title_size"))
        ins += ["-loop", "1", "-i", png]
        vf.append(f"[0:v][2:v]overlay=(W-w)/2:{fg_y}-h/2[v1]")
        last = "v1"
    vf.append(f"[{last}]ass={work / 'captions.ass'}:fontsdir=/usr/share/fonts,ass={work / 'texts.ass'}:fontsdir=/usr/share/fonts[v]")
    vf.append(f"[1:a]{loud}[a]")
    LF.run(["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(vf), "-map", "[v]", "-map", "[a]",
            "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    build(ap.parse_args().job)
