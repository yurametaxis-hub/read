#!/usr/bin/env python3
"""Long-form 16:9 video essay: AI narration (Kokoro), b-roll synced to every sentence, section cards,
GTA 5 and GTA 6 labels, burned captions, game audio ducked under the voice and a soft synth pad.

    python3 shorts/make_longform.py shorts/jobs/longform_gta5_better.json

Job keys:
  out, work                 output mp4 and a work folder (TTS and shots are cached there)
  voice, speed              Kokoro voice (am_fenrir, am_michael, af_heart, ...) and speaking rate
  tts_model, tts_voices     kokoro-v1.0.onnx and voices-v1.0.bin
  sources                   {"c5": {"path": "...", "crop": [x, y, w, h]}}; crop trims stream overlays
  paragraphs                [{"sentences": [{"text": "...", "shots": [...]}, ...]}, ...]
Shots share their sentence's time by weight "w"; a sentence with "shots": [] extends the previous shot.
  {"src": "c5", "t": 8.0, "label": "GTA 5"}               clip from t ("t_end" instead: the shot ends there)
  {"src": "c2", "t": 2, "crop": [0, 180, 640, 360]}       zoom into a region of the source
  {"src": "c5", "t": 16, "speed": 0.4, "boom": 0.5}       slow motion, impact sound 0.5 s into the shot
  {"card": "REASON #1", "title": "REALISM KILLED|THE CHAOS", "bg": "c5", "t": 22}
  {"grid": [["A", 0.5], ["B", 14], ...]}                  3x3 wall of nine clips
  {"pair": [["c8", 5.0], ["c8", 27.6]]}                    own split screen, GTA 5 left and GTA 6 right
Sources may list "scenes": [[start, end, "GTA 5" | "GTA 6" | "split"], ...]; shots are kept inside one
scene (no running into a transition or into the other game) and a mismatched label is reported.
Labels: "GTA 5", "GTA 6", "GTA SAN ANDREAS · 2004", "GTA IV · 2008", "GTA V · 2013", "GTA VI · 2026", or "split".
Sources and shots take "mute": true for someone else's music or a line that cannot air.
A sentence can be {"listen": [src, t0, t1], "subs": [[t0, t1, "NAME: line"], ...], "label": ...}: the narrator
pauses and the clip's own dialogue plays, levelled like the narration, with yellow subtitles (source times).
Job keys: music ("synthpad" or a meme_kit bed such as "doc"), music_volume, dialogue_lufs (default -17).
"""
import argparse
import hashlib
import html
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from make_edit import make_sfx  # noqa: E402

W, H, FPS, SR = 1920, 1080, 30, 48000
VERSION = 2  # bump to re-render every cached shot
FONT_XB = "/usr/share/fonts/opentype/montserrat/Montserrat-ExtraBold.otf"
TAG = {"GTA 5": "0x27AE60", "GTA 6": "0xFF2E88",
       "GTA SAN ANDREAS · 2004": "0xE8731A", "GTA IV · 2008": "0x3D6FB5",
       "GTA V · 2013": "0x27AE60", "GTA VI · 2026": "0xE6197A"}
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def run(cmd):
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))[:300]}\n{r.stderr[-1500:]}")
    return r.stdout + r.stderr


def duration(path):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).strip())


# ---------------------------------------------------------------- narration

def speakable(text):
    """Spellings Kokoro reads right; each one was checked by running the audio back through Whisper."""
    words = {"1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five", "6": "Six"}
    text = re.sub(r"\bGTA ([1-6])\b", lambda m: "GTA " + words[m.group(1)], text)
    for k, v in (("FiveM", "Five M"), ("Cayo Perico", "Kai-oh Perico"), ("San Fierro", "San Fee-airo"),
                 ("El Quebrados", "El Keh-brah-dos")):
        text = text.replace(k, v)
    return text


def narrate(job, work, sents):
    from kokoro_onnx import Kokoro
    tdir = work / "tts"
    tdir.mkdir(parents=True, exist_ok=True)
    kokoro = None
    pieces, t, sr = [], 0.4, 24000
    for s in sents:
        if "listen" in s:  # real game dialogue: the narrator stays quiet for the length of the clip
            _, a, b = s["listen"]
            s["t0"], s["t1"] = t, t + (b - a)
            t = s["t1"] + (0.45 if s["last_in_par"] else 0.2)
            continue
        key = hashlib.sha1(f"{job['voice']}|{job['speed']}|{speakable(s['text'])}".encode()).hexdigest()[:16]
        f = tdir / f"{key}.wav"
        if not f.exists():
            kokoro = kokoro or Kokoro(job["tts_model"], job["tts_voices"])
            audio, sr = kokoro.create(speakable(s["text"]), voice=job["voice"], speed=job["speed"], lang="en-us")
            loud = np.flatnonzero(np.abs(audio) > 0.02 * np.abs(audio).max())
            audio = audio[max(loud[0] - int(0.03 * sr), 0): loud[-1] + int(0.08 * sr)]
            sf.write(f, audio, sr)
        audio, sr = sf.read(f)
        s["t0"], s["t1"] = t, t + len(audio) / sr
        pieces.append((t, audio))
        t = s["t1"] + (0.7 if s["last_in_par"] else 0.28)
    total = t + 1.6
    out = np.zeros(int(total * sr) + 1, dtype=np.float32)
    for t0, a in pieces:
        i = int(t0 * sr)
        out[i:i + len(a)] += a
    out /= max(np.abs(out).max(), 1e-6) / 0.9
    sf.write(work / "narration.wav", out, sr)
    return total


# ---------------------------------------------------------------- shots

def labels(label):
    def tag(text, x):
        return (f"drawtext=fontfile={FONT_XB}:text='{text}':fontsize=44:fontcolor=white:box=1:"
                f"boxcolor={TAG[text]}@0.95:boxborderw=16:x={x}:y=44")
    if label == "split":
        return [tag("GTA 5", 52), tag("GTA 6", W // 2 + 52)]
    return [tag(label, 52)] if label in TAG else []


def fit(crop):
    pre = [f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}"] if crop else []
    return pre + [f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos", f"crop={W}:{H}", "setsar=1"]


def clip_audio(path, t, need, dur, speed, out):
    af = f"aresample={SR}"
    if speed < 1:
        af += f",asetrate={int(SR * speed)},aresample={SR}"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-t", f"{need + 0.5:.3f}", "-i", path, "-vn",
         "-af", af + f",apad,atrim=0:{dur:.4f}", "-ac", "2", "-ar", SR, out])


def silence(dur, out):
    sf.write(out, np.zeros((int(round(dur * SR)), 2), dtype=np.float32), SR)


def card_png(kicker, title, out):
    t = "<br>".join(html.escape(x) for x in title.split("|"))
    page = f'''<!doctype html><meta charset="utf-8"><style>
      html, body {{ margin: 0; width: {W}px; height: {H}px; background: transparent; }}
      .box {{ position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center;
              justify-content: center; text-align: center; font-family: 'Montserrat'; font-style: italic; }}
      .k {{ font-weight: 900; font-size: 60px; letter-spacing: 8px; color: #ff2e88; margin-bottom: 18px;
            text-shadow: 0 4px 18px rgba(0,0,0,.6); }}
      .t {{ position: relative; font-weight: 900; font-size: 132px; line-height: 1.02; }}
      .t span {{ display: block; }}
      .back {{ position: absolute; inset: 0; color: transparent; -webkit-text-stroke: 26px #0d0221; }}
      .front {{ position: relative; color: #fff; }}
    </style><div class="box"><div class="k">{html.escape(kicker)}</div>
    <div class="t"><span class="back">{t}</span><span class="front">{t}</span></div></div>'''
    f = Path(str(out) + ".html")
    f.write_text(page)
    run(["node", HERE / "brand" / "render_html.js", f, out, W, H])


def check_shot(sh, need, sources):
    """Keep a clip shot inside one scene of its source, so a GTA 5 label never runs into GTA 6 footage
    or into a transition wipe. Returns the corrected start time and a warning or None."""
    src = sources[sh["src"]]
    t = sh["t_end"] - need if "t_end" in sh else sh.get("t", 0.0)
    scenes = src.get("scenes") or [[0.0, src["dur"], None]]
    t = max(0.0, min(t, src["dur"] - 0.05))
    sc = next((s for s in scenes if s[0] - 0.05 <= t < s[1]), None)
    if sc is None:
        sc = min(scenes, key=lambda s: min(abs(t - s[0]), abs(t - s[1])))
        t = sc[0]
    warn = None
    if t + need > sc[1]:
        t2 = sc[1] - need
        if t2 >= sc[0]:
            t = t2
        else:
            t = sc[0]
            warn = f"{sh['src']}@{sh.get('t', sh.get('t_end'))}: needs {need:.1f}s, scene {sc[0]}-{sc[1]} is shorter"
    want = sc[2]
    crop = sh.get("crop")
    if want == "split" and crop:
        want = "GTA 5" if crop[0] < 320 else "GTA 6"
    if want and sh.get("label") and want != sh["label"]:
        warn = (warn or "") + f" | {sh['src']}@{t:.1f} labelled {sh['label']} but scene is {want}"
    return t, warn


def render_shot(i, sh, nframes, sources, sdir):
    dur = nframes / FPS
    keys = [sh.get("src"), sh.get("bg")] + [k for k, _ in sh.get("pair", [])] + [k for k, _ in sh.get("grid", [])]
    srcinfo = [[sources[k]["path"], sources[k].get("crop"), sources[k].get("mute")] for k in keys if k in sources]
    sig = hashlib.sha1(json.dumps([sh, nframes, VERSION, srcinfo]).encode()).hexdigest()[:14]
    final_v, final_a = sdir / f"{sig}.mp4", sdir / f"{sig}.wav"
    if final_v.exists() and final_a.exists():
        return final_v, final_a
    # write under temporary names and rename at the end, so a stopped render never leaves a cut file
    vout, aout = sdir / f"{sig}.part.mp4", sdir / f"{sig}.part.wav"
    head = ["ffmpeg", "-v", "error", "-y"]
    if "card" in sh:
        src = sources[sh["bg"]]
        png = sdir / f"{sig}.card.png"
        card_png(sh["card"], sh["title"], png)
        bg = ",".join(fit(src.get("crop")) + [f"fps={FPS}", "tpad=stop_mode=clone:stop_duration=30",
                                              "boxblur=24:2", "eq=brightness=-0.22:saturation=0.75"])
        run(head + ["-ss", sh.get("t", 0), "-t", dur + 1, "-i", src["path"], "-loop", "1", "-i", png,
                    "-filter_complex", f"[0:v]{bg}[bg];[1:v]format=rgba,fade=in:st=0:d=0.3:alpha=1[t];"
                    "[bg][t]overlay=0:0", "-frames:v", nframes, "-an", *ENC, vout])
        silence(dur, aout)
    elif "pair" in sh:
        # home-made split screen: GTA 5 moment on the left, GTA 6 moment on the right
        ins, fl, auds = [], [], []
        for k, ((key, _), t) in enumerate(zip(sh["pair"], sh["_pt"])):
            src = sources[key]
            ins += ["-ss", f"{t:.3f}", "-t", f"{dur + 1:.3f}", "-i", src["path"]]
            crop = src.get("crop")
            pre = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
            fl.append(f"[{k}:v]{pre}scale=958:1080:force_original_aspect_ratio=increase:flags=lanczos,crop=958:1080,"
                      f"setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration=30[p{k}]")
            a = sdir / f"{sig}.{k}.wav"
            clip_audio(src["path"], t, dur, dur, 1.0, a)
            auds.append(sf.read(a, dtype="float32", always_2d=True)[0])
        fl.append(f"color=black:s=4x1080:r={FPS}[div];[p0][div][p1]hstack=3,eq=contrast=1.04:saturation=1.1,"
                  "unsharp=5:5:0.4:5:5:0," + ",".join(labels("split")))
        run(head + ins + ["-filter_complex", ";".join(fl), "-frames:v", nframes, "-an", *ENC, vout])
        n = min(len(x) for x in auds)
        sf.write(aout, 0.6 * (auds[0][:n] + auds[1][:n]), SR)
    elif "grid" in sh:
        ins, fl = [], []
        for k, (key, t) in enumerate(sh["grid"]):
            src = sources[key]
            ins += ["-ss", t, "-t", dur + 1, "-i", src["path"]]
            crop = src.get("crop")
            pre = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
            fl.append(f"[{k}:v]{pre}scale=632:352:force_original_aspect_ratio=increase,crop=632:352,setsar=1,"
                      f"fps={FPS},tpad=stop_mode=clone:stop_duration=30,pad=640:360:4:4:black[g{k}]")
        layout = "|".join(f"{x * 640}_{y * 360}" for y in range(3) for x in range(3))
        fl.append("".join(f"[g{k}]" for k in range(9)) + f"xstack=inputs=9:layout={layout}," + ",".join(labels("GTA 6")))
        run(head + ins + ["-filter_complex", ";".join(fl), "-frames:v", nframes, "-an", *ENC, vout])
        silence(dur, aout)
    else:
        src = sources[sh["src"]]
        sp = float(sh.get("speed", 1.0))
        need = dur * sp
        t = sh["_t"]
        vf = fit(sh.get("crop") or src.get("crop"))
        if sp != 1:
            vf.append(f"setpts=PTS/{sp}")
        vf += [f"fps={FPS}", "tpad=stop_mode=clone:stop_duration=30",
               "eq=contrast=1.04:saturation=1.1", "unsharp=5:5:0.4:5:5:0"] + labels(sh.get("label"))
        run(head + ["-ss", f"{t:.3f}", "-t", f"{need + 1:.3f}", "-i", src["path"], "-vf", ",".join(vf),
                    "-frames:v", nframes, "-an", *ENC, vout])
        if sh.get("mute") or src.get("mute"):  # someone else's music or a line that cannot air
            silence(dur, aout)
        else:
            clip_audio(src["path"], t, need, dur, sp, aout)
    vout.replace(final_v)
    aout.replace(final_a)
    return final_v, final_a


# ---------------------------------------------------------------- captions, music, mix

def captions(sents, path, max_chars=44):
    import pysubs2
    subs = pysubs2.SSAFile()
    subs.info.update({"PlayResX": str(W), "PlayResY": str(H), "WrapStyle": "0", "ScaledBorderAndShadow": "yes"})
    subs.styles["Cap"] = pysubs2.SSAStyle(
        fontname="Montserrat ExtraBold", fontsize=54, primarycolor=pysubs2.Color(255, 255, 255),
        outlinecolor=pysubs2.Color(0, 0, 0), backcolor=pysubs2.Color(0, 0, 0, 120), outline=4, shadow=2,
        alignment=pysubs2.Alignment.BOTTOM_CENTER, marginv=60, marginl=160, marginr=160)
    subs.styles["Dlg"] = pysubs2.SSAStyle(
        fontname="Montserrat ExtraBold", fontsize=52, italic=True, primarycolor=pysubs2.Color(255, 236, 170),
        outlinecolor=pysubs2.Color(0, 0, 0), backcolor=pysubs2.Color(0, 0, 0, 120), outline=4, shadow=2,
        alignment=pysubs2.Alignment.BOTTOM_CENTER, marginv=60, marginl=140, marginr=140)
    for s in sents:
        if "listen" in s:
            a = s["listen"][1]
            for st, en, line in s.get("subs", []):
                name, _, said = line.partition(": ") if ": " in line else ("", "", line)
                tag = f"{{\\c&H3BC8FF&\\i0}}{name}:{{\\r}} " if name else ""
                subs.append(pysubs2.SSAEvent(start=int((s["t0"] + st - a) * 1000), end=int((s["t0"] + en - a) * 1000),
                                             style="Dlg", text=tag + said))
            continue
        words, chunks, cur = s["text"].split(), [], []
        for w in words:
            if cur and (len(" ".join(cur + [w])) > max_chars or re.search(r"[.!?:;,]$", cur[-1]) and len(" ".join(cur)) > 18):
                chunks.append(" ".join(cur))
                cur = []
            cur.append(w)
        chunks.append(" ".join(cur))
        total = sum(len(c) for c in chunks)
        t = s["t0"]
        for c in chunks:
            d = (s["t1"] - s["t0"]) * len(c) / total
            subs.append(pysubs2.SSAEvent(start=int(t * 1000), end=int((t + d) * 1000), style="Cap", text=c))
            t += d
    subs.save(str(path))


def synth_pad(total, path):
    """Slow synthwave pad, Am F C G, four seconds per chord, detuned saws through a low-pass."""
    from scipy.signal import butter, lfilter
    n = int(total * SR)
    t = np.arange(int(4.8 * SR)) / SR
    midi = {"A2": 45, "C3": 48, "E3": 52, "F2": 41, "G2": 43, "A3": 57, "B3": 59, "C4": 60, "D4": 62, "E4": 64, "G4": 67}
    chords = [("A2", "E3", "A3", "C4", "E4"), ("F2", "C3", "A3", "C4", "E4"),
              ("C3", "G2", "E4", "G4", "C4"), ("G2", "D4", "B3", "D4", "G4")]
    env = np.minimum(1, np.minimum(t / 0.8, (t[-1] - t) / 0.8)).clip(0)
    out = np.zeros((n + len(t), 2))
    b, a = butter(2, 900 / (SR / 2))
    for k in range(int(np.ceil(total / 4)) + 1):
        notes = chords[k % 4]
        seg = np.zeros((len(t), 2))
        for note in notes:
            f0 = 440 * 2 ** ((midi[note] - 69) / 12)
            for ch, det in ((0, -0.07), (1, 0.07)):
                for d in (det, -det / 2):
                    f = f0 * 2 ** (d / 12)
                    seg[:, ch] += 2 * ((t * f + 0.13 * ch) % 1) - 1
        seg = lfilter(b, a, seg, axis=0) * env[:, None]
        i = int(k * 4 * SR)
        out[i:i + len(t)] += seg[: len(out) - i]
    out = out[:n]
    delay = int(0.31 * SR)
    out[delay:] += 0.35 * out[:-delay][:, ::-1]
    out /= np.abs(out).max() / 0.25
    sf.write(path, out.astype(np.float32), SR)


def sfx_track(total, events, work, path):
    boom, whoosh = make_sfx(work)
    tr = np.zeros((int(total * SR) + SR, 2), dtype=np.float32)
    for kind, t in events:
        a, _ = sf.read(boom if kind == "boom" else whoosh)
        i = max(int(t * SR), 0)
        tr[i:i + len(a)] += a[: len(tr) - i] * (0.9 if kind == "boom" else 1.0)
    sf.write(path, tr[: int(total * SR)], SR)


# ---------------------------------------------------------------- main

def build(job_path):
    job = json.loads(Path(job_path).read_text())
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    sources = job["sources"]
    for s in sources.values():
        s["dur"] = duration(s["path"])
    sents = []
    for p in job["paragraphs"]:
        for k, s in enumerate(p["sentences"]):
            s["last_in_par"] = k == len(p["sentences"]) - 1
            sents.append(s)
    total = narrate(job, work, sents)
    print(f"narration {total:.1f}s, {sum(len(s.get('text', '').split()) for s in sents)} words, "
          f"{sum(s['t1'] - s['t0'] for s in sents if 'listen' in s):.1f}s of game dialogue")
    for s in sents:
        if "listen" in s and not s.get("shots"):
            src, a, _ = s["listen"]
            s["shots"] = [dict(s.get("shot", {}), src=src, t=a, label=s.get("label"), _listen=True)]

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
        if "src" in sh:
            sh["_t"], w = check_shot(sh, n / FPS * float(sh.get("speed", 1.0)), sources)
            if w:
                warnings.append(f"{int(x['start'] // 60)}:{x['start'] % 60:04.1f} {w}")
        if "pair" in sh:
            sh["_pt"] = []
            for (key, t), lab in zip(sh["pair"], ("GTA 5", "GTA 6")):
                pt, w = check_shot({"src": key, "t": t, "label": lab}, n / FPS, sources)
                sh["_pt"].append(pt)
                if w:
                    warnings.append(f"{int(x['start'] // 60)}:{x['start'] % 60:04.1f} pair {w}")
    used = {}
    for x, n in zip(tl, frames):  # the same moment of footage shown twice is a repeat the viewer notices
        sh = x["shot"]
        parts = [(sh["src"], sh["_t"], float(sh.get("speed", 1.0)))] if "src" in sh else []
        parts += [(k, t, 1.0) for (k, _), t in zip(sh.get("pair", []), sh.get("_pt", []))]
        for key, t, sp in parts:
            a, b = t, t + n / FPS * sp
            for a2, b2, at in used.get(key, []):
                if min(b, b2) - max(a, a2) > 1.0 and not sh.get("repeat") and x["start"] - at < 150:
                    warnings.append(f"{int(x['start'] // 60)}:{x['start'] % 60:04.1f} repeats {key} "
                                    f"{max(a, a2):.1f}-{min(b, b2):.1f} first used at {int(at // 60)}:{at % 60:04.1f}")
            used.setdefault(key, []).append((a, b, x["start"]))
    print("\n".join(["shot warnings:"] + warnings) if warnings else "shots ok")
    if job.get("check_only"):
        return

    sdir = work / "shots"
    sdir.mkdir(exist_ok=True)
    with ThreadPoolExecutor(3) as ex:
        res = list(ex.map(lambda a: render_shot(*a), [(i, x["shot"], n, sources, sdir) for i, (x, n) in enumerate(zip(tl, frames))]))
    (work / "list.txt").write_text("".join(f"file '{v}'\n" for v, _ in res))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", work / "list.txt", "-c", "copy", work / "broll.mp4"])
    def exact(a, n):  # every shot's audio cut or padded to its frame count, so nothing drifts
        x = sf.read(a, dtype="float32", always_2d=True)[0][: n * SR // FPS]
        return np.pad(x, ((0, n * SR // FPS - len(x)), (0, 0)))
    game = np.concatenate([exact(a, n) for (_, a), n in zip(res, frames)])
    sf.write(work / "game.wav", game, SR)

    events = []
    for x in tl:
        sh = x["shot"]
        if "card" in sh:
            events.append(("whoosh", x["start"] - 0.25))
        if "boom" in sh:
            events.append(("boom", x["start"] + sh["boom"]))
    sfx_track(total, events, work, work / "sfx.wav")
    style = job.get("music", "synthpad")
    if style == "synthpad":
        synth_pad(total, work / "pad.wav")
    else:  # one of the meme_kit beds, levelled like the synth pad
        import meme_kit as MK
        bed = MK.music(style, total + 0.5)[: int(total * SR)]
        sf.write(work / "pad.wav", (bed * 0.25 / max(np.abs(bed).max(), 1e-6)).astype(np.float32), SR)
    captions(sents, work / "captions.ass")

    # 5. game dialogue moves from the ducked game track to its own track, mixed like the narration
    listens = [(s["t0"], s["t1"]) for s in sents if "listen" in s]
    dial = np.zeros_like(game)
    fade = int(0.03 * SR)
    for t0, t1 in listens:
        i0, i1 = int(t0 * SR), min(int((t1 + 0.12) * SR), len(game))
        seg = game[i0:i1].copy()
        ramp = np.ones(len(seg), np.float32)
        ramp[:fade] = np.linspace(0, 1, min(fade, len(seg)))[: len(ramp[:fade])]
        ramp[-fade:] = np.linspace(1, 0, fade)
        dial[i0:i1] = seg * ramp[:, None]
        game[i0:i1] = game[i0:i1] * (1 - ramp[:, None])
    sf.write(work / "game.wav", game, SR)
    sf.write(work / "dial.wav", dial, SR)

    # Static gains measured up front: dynamic loudnorm keeps a 3 s lookahead and dropped the last
    # word of the narration, and a sidechain ends as soon as its key input ends, so everything is padded.
    def gain_to(path, target):
        meas = run(["ffmpeg", "-hide_banner", "-i", path, "-af", "loudnorm=print_format=json", "-f", "null", "-"])
        i = float(json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])["input_i"])
        return 0.0 if i < -70 else target - i
    gn, gg = gain_to(work / "narration.wav", -16), gain_to(work / "game.wav", -22)
    gd = gain_to(work / "dial.wav", job.get("dialogue_lufs", -17))
    mv = 0.45 * float(job.get("music_volume", 1.0))
    mix = (f"[1:a]aresample=48000,aformat=channel_layouts=stereo,volume={gn:.2f}dB,apad=whole_dur={total:.3f}[nv];"
           f"[5:a]volume={gd:.2f}dB,apad=whole_dur={total:.3f}[dv];"
           "[nv][dv]amix=inputs=2:normalize=0:duration=first,asplit=3[n1][n2][n3];"
           f"[2:a]volume={gg:.2f}dB,volume=0.7,apad=whole_dur={total:.3f}[g0];"
           "[g0][n2]sidechaincompress=threshold=0.015:ratio=12:attack=10:release=400[gd];"
           f"[3:a]volume={mv:.3f},apad=whole_dur={total:.3f}[m0];[m0][n3]sidechaincompress=threshold=0.015:ratio=4:attack=40:release=800[md];"
           f"[4:a]apad=whole_dur={total:.3f}[fx];[n1][gd][md][fx]amix=inputs=4:normalize=0:duration=first[mix]")
    run(["ffmpeg", "-v", "error", "-y", "-i", work / "broll.mp4", "-i", work / "narration.wav", "-i", work / "game.wav",
         "-i", work / "pad.wav", "-i", work / "sfx.wav", "-i", work / "dial.wav", "-filter_complex", mix, "-map", "[mix]",
         "-t", total, work / "mix.wav"])
    meas = run(["ffmpeg", "-hide_banner", "-i", work / "mix.wav", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    loud = (f"apad=whole_dur={total:.3f},loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}"
            f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
            "aresample=48000")
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", work / "broll.mp4", "-i", work / "mix.wav",
         "-filter_complex", f"[0:v]ass={work / 'captions.ass'}:fontsdir=/usr/share/fonts[v];"
                            f"[1:a]{loud},alimiter=limit=0.79:attack=2:release=60:level=0[a]",
         "-map", "[v]", "-map", "[a]", "-t", total, "-c:v", "libx264", "-preset", "fast", "-crf", "21",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    chapters = [(x["start"], x["shot"]) for x in tl if "card" in x["shot"]]
    (work / "chapters.txt").write_text("".join(f"{int(s // 60)}:{int(s % 60):02d} {sh['card']} {sh['title'].replace('|', ' ')}\n" for s, sh in chapters))
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    build(ap.parse_args().job)
