#!/usr/bin/env python3
"""Meme style vertical shorts (1080x1920) built frame by frame: narration per beat, punch zooms, shakes, freeze
frames, rewinds, deep fry, VHS, flashes, emoji and text stickers, speech bubbles, marker circles and arrows,
CAUGHT IN 4K and TO BE CONTINUED overlays, synthesized meme sounds and music (meme_kit.py).

    python3 shorts/make_meme_short.py shorts/jobs/meme_karma.json

A job is a list of beats. A beat holds shots, an optional narration line ("say"), meme voice lines, sound
effects and stickers; its length is the longest of: the narration plus a pad, the fixed shot lengths, "min".
Shots without "dur" share what is left. Times inside a beat are seconds from the beat start.

Shot keys: src, t, dur, speed, reverse, freeze, layout ("band" 1080x1260 over a blurred fill, or "fill"),
  x, y (crop centre as a share of the source), zoom, x_to, y_to, zoom_to, ease ("smooth", "out", "punch"),
  ease_time, fx: {flash: [colour, at], shake: [[a, b, px], ...], deepfry: [a, b], sepia, bw, vhs, rewind}
Sticker keys: type (emoji, text, bubble, circle, arrow, rec, tbc), at, dur, x, y or src: [sx, sy] (source pixels
  of the shot on screen at that moment), anim (pop, slam, fade, slide, none), wobble, rot, track: [[t, x, y]],
  blink; text: text, font, size, color, bg, stroke; emoji: emoji, size; bubble: text, size, tail;
  circle: r or src_r; arrow: from, to, label.
"""
import argparse
import difflib
import hashlib
import html
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from scipy.signal import resample_poly

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meme_kit as MK  # noqa: E402
from make_longform import speakable  # noqa: E402

W, H, FPS, SR = 1080, 1920, 30, 48000
BAND_Y, BAND_H = 340, 1260
FONTS = HERE / "fonts"
MARKER = str(FONTS / "PermanentMarker-Regular.ttf")
BANGERS = str(FONTS / "Bangers-Regular.ttf")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def run(cmd, data=None):
    r = subprocess.run([str(c) for c in cmd], input=data, capture_output=True)
    if r.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))[:300]}\n{r.stderr.decode()[-1500:]}")
    return r.stdout


def sha(*parts):
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- voice

class Voices:
    def __init__(self, job, work):
        self.model, self.voices = job["tts_model"], job["tts_voices"]
        self.dir = work / "tts"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.k = None
        self.whisper = None

    def say(self, text, voice, speed):
        spoken = speakable(text)
        f = self.dir / f"{sha(voice, speed, spoken)}.wav"
        if not f.exists():
            from kokoro_onnx import Kokoro
            self.k = self.k or Kokoro(self.model, self.voices)
            a, sr = self.k.create(spoken, voice=voice, speed=speed, lang="en-gb" if voice[0] == "b" else "en-us")
            loud = np.flatnonzero(np.abs(a) > 0.02 * np.abs(a).max())
            a = a[max(loud[0] - int(0.03 * sr), 0): loud[-1] + int(0.08 * sr)]
            sf.write(f, a, sr)
        a, sr = sf.read(f, dtype="float32")
        return f, resample_poly(a, SR, sr).astype(np.float32)

    def words(self, wav, text):
        """Script words with times from Whisper run on the clean line; misheard words keep the script spelling."""
        cache = wav.with_suffix(".words.json")
        if cache.exists():
            return json.loads(cache.read_text())
        if self.whisper is None:
            os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
            from faster_whisper import WhisperModel
            self.whisper = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
        segs, _ = self.whisper.transcribe(str(wav), language="en", word_timestamps=True)
        heard = [(w.word.strip(), w.start, w.end) for s in segs for w in s.words]
        dur = sf.info(str(wav)).duration
        script = text.split()
        norm = lambda x: re.sub(r"[^a-z0-9]", "", x.lower())
        times = [None] * len(script)
        sm = difflib.SequenceMatcher(None, [norm(x) for x in script], [norm(h[0]) for h in heard], autojunk=False)
        for a, b, n in sm.get_matching_blocks():
            for k in range(n):
                times[a + k] = (heard[b + k][1], heard[b + k][2])
        k = 0
        while k < len(script):
            if times[k] is not None:
                k += 1
                continue
            j = k
            while j < len(script) and times[j] is None:
                j += 1
            lo = times[k - 1][1] if k else 0.0
            hi = times[j][0] if j < len(script) else dur
            lens = [len(w) + 1 for w in script[k:j]]
            acc = lo
            for m, ln in zip(range(k, j), lens):
                step = (hi - lo) * ln / sum(lens)
                times[m] = (acc, acc + step)
                acc += step
            k = j
        out = [[w, round(a, 3), round(b, 3)] for w, (a, b) in zip(script, times)]
        cache.write_text(json.dumps(out))
        return out


# ---------------------------------------------------------------- stickers

def chrome_stickers(specs, work):
    """specs: {key: html}; renders the missing ones in one Chromium session, returns {key: RGBA array}."""
    sdir = work / "stickers"
    sdir.mkdir(parents=True, exist_ok=True)
    todo = [{"out": str(sdir / f"{k}.png"), "html": h} for k, h in specs.items() if not (sdir / f"{k}.png").exists()]
    if todo:
        (work / "stickers.json").write_text(json.dumps(todo))
        run(["node", HERE / "render_stickers.js", work / "stickers.json", FONTS])
    return {k: np.array(Image.open(sdir / f"{k}.png").convert("RGBA")) for k in specs}


def outlined(text, stroke, fill_html=None):
    inner = fill_html if fill_html is not None else html.escape(text)
    return (f'<span class="o"><span class="b" style="-webkit-text-stroke:{stroke}px #000">{inner}</span>'
            f'<span class="f">{inner}</span></span>')


def emoji_html(e, size):
    return f'<span style="font:{size}px/1 \'Noto Color Emoji\'">{e}</span>'


def text_html(s):
    font, size = s.get("font", "Bangers"), s.get("size", 100)
    text = s["text"].upper() if s.get("upper", True) else s["text"]
    esc = html.escape(text)
    esc = re.sub(r"\[(.+?)\]", rf'<span style="color:{s.get("hl", "#FFE600")}">\1</span>', esc)
    style = (f"font-family:'{font}','Noto Color Emoji';font-size:{size}px;line-height:1.05;color:{s.get('color', '#fff')};"
             f"text-align:center;letter-spacing:{s.get('spacing', 1)}px;max-width:{s.get('maxw', 960)}px;display:inline-block;")
    if s.get("bg"):
        style += (f"background:{s['bg']};padding:{s.get('pad', '10px 26px')};border-radius:{s.get('radius', 14)}px;"
                  f"box-shadow:0 8px 0 rgba(0,0,0,.55);")
    if s.get("rot"):
        style += f"transform:rotate({s['rot']}deg);"
    body = outlined(text, s["stroke"], esc) if s.get("stroke") else esc
    return f'<div style="{style}">{body}</div>'


def bubble_html(s):
    size = s.get("size", 64)
    tail = s.get("tail", "down")
    pos = {"down": "left:50%;bottom:-34px;margin-left:-22px;border-width:36px 22px 0 22px;border-color:#111 transparent transparent transparent",
           "left": "left:60px;bottom:-34px;border-width:36px 26px 0 0;border-color:#111 transparent transparent transparent",
           "right": "right:60px;bottom:-34px;border-width:36px 0 0 26px;border-color:#111 transparent transparent transparent"}[tail]
    inner = pos.replace("#111", "#fff").replace("-34px", "-24px").replace("36px", "26px").replace("22px", "16px")
    return (f'<div style="position:relative;display:inline-block;background:#fff;border:7px solid #111;border-radius:42px;'
            f'padding:{s.get("pad", "18px 34px")};margin-bottom:40px;font:{size}px/1.05 \'Luckiest Guy\',\'Noto Color Emoji\';color:#111;'
            f'text-align:center;max-width:{s.get("maxw", 820)}px;box-shadow:0 8px 0 rgba(0,0,0,.4)">{html.escape(s["text"])}'
            f'<span style="position:absolute;width:0;height:0;border-style:solid;{pos}"></span>'
            f'<span style="position:absolute;width:0;height:0;border-style:solid;{inner}"></span></div>')


def hook_html(text):
    esc = html.escape(text.upper())
    esc = re.sub(r"\[(.+?)\]", r'<span style="color:#FFE600">\1</span>', esc)
    return (f"<div style=\"font:86px/1.02 'Anton','Noto Color Emoji';letter-spacing:1px;color:#fff;text-align:center;"
            f"max-width:1000px;display:inline-block\">{outlined(text, 16, esc)}</div>")


def credit_html(text):
    return (f'<div style="font:600 27px/1 \'DejaVu Sans\',\'Noto Color Emoji\';color:rgba(255,255,255,.88);'
            f'text-shadow:0 2px 6px rgba(0,0,0,.9),0 0 2px #000">{html.escape(text)}</div>')


def marker_circle(r, color=(255, 32, 32), seed=1, ry=None):
    ry = ry or r * 0.78
    pad = 30
    s = 2
    size = (int((r * 1.25 + pad) * 2 * s), int((ry * 1.25 + pad) * 2 * s))
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = np.random.default_rng(seed)
    cx, cy = size[0] / 2, size[1] / 2
    pts = []
    for i in range(81):
        a = -2.2 + (2 * math.pi + 0.45) * i / 80
        g = (1 + 0.08 * i / 80) * (1 + rnd.uniform(-0.015, 0.015))
        pts.append((cx + r * s * g * math.cos(a), cy + ry * s * g * math.sin(a)))
    d.line([(x + 4 * s, y + 6 * s) for x, y in pts], fill=(0, 0, 0, 110), width=16 * s, joint="curve")
    d.line(pts, fill=color + (255,), width=12 * s, joint="curve")
    img = img.resize((size[0] // s, size[1] // s), Image.LANCZOS)
    return np.array(img)


def marker_arrow(p0, p1, label=None, color=(255, 32, 32)):
    """Full-frame RGBA layer with a marker arrow from p0 to p1 and an optional label at p0."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(y1 - y0, x1 - x0)
    hl, hw = 56, 40
    bx, by = x1 - hl * math.cos(ang), y1 - hl * math.sin(ang)
    head = [(x1, y1), (bx + hw * math.sin(ang), by - hw * math.cos(ang)), (bx - hw * math.sin(ang), by + hw * math.cos(ang))]
    for off, col, wd in (((4, 6), (0, 0, 0, 110), 18), ((0, 0), color + (255,), 14)):
        d.line([(x0 + off[0], y0 + off[1]), (bx + off[0], by + off[1])], fill=col, width=wd)
        d.polygon([(x + off[0], y + off[1]) for x, y in head], fill=col)
    if label:
        f = ImageFont.truetype(MARKER, 64)
        tw = d.textlength(label, font=f)
        tx = min(max(x0 - tw / 2, 20), W - tw - 20)
        ty = y0 - 86 if y1 > y0 else y0 + 10
        d.text((tx + 4, ty + 6), label, font=f, fill=(0, 0, 0, 150))
        d.text((tx, ty), label, font=f, fill=color + (255,), stroke_width=3, stroke_fill=(255, 255, 255, 255))
    return np.array(img)


def rec_overlay():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = 50, BAND_Y + 80, W - 50, BAND_Y + BAND_H - 60
    L = 90
    for (cx, cy, sx, sy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        d.line([(cx, cy), (cx + sx * L, cy)], fill=(255, 255, 255, 235), width=8)
        d.line([(cx, cy), (cx, cy + sy * L)], fill=(255, 255, 255, 235), width=8)
    f = ImageFont.truetype(MONO, 44)
    d.text((x0 + 92, y0 + 30), "REC", font=f, fill=(255, 255, 255, 240), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    d.text((x1 - 300, y0 + 30), "4K  60FPS", font=f, fill=(255, 255, 255, 240), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    d.rectangle([x1 - 150, y1 - 80, x1 - 60, y1 - 40], outline=(255, 255, 255, 235), width=5)
    d.rectangle([x1 - 60, y1 - 68, x1 - 52, y1 - 52], fill=(255, 255, 255, 235))
    d.rectangle([x1 - 142, y1 - 72, x1 - 90, y1 - 48], fill=(255, 255, 255, 235))
    d.text((x0 + 30, y1 - 85), "00:00:13:07", font=f, fill=(255, 255, 255, 240), stroke_width=2, stroke_fill=(0, 0, 0, 160))
    return np.array(img)


def rec_dot():
    img = Image.new("RGBA", (60, 60), (0, 0, 0, 0))
    ImageDraw.Draw(img).ellipse([6, 6, 54, 54], fill=(255, 30, 30, 255))
    return np.array(img)


def tbc_arrow():
    w, h = 640, 150
    img = Image.new("RGBA", (w + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(10, 30), (w - 130, 30), (w - 130, 5), (w, h / 2 + 10), (w - 130, h + 15), (w - 130, h - 10), (10, h - 10)]
    d.polygon([(x + 6, y + 8) for x, y in pts], fill=(0, 0, 0, 120))
    d.polygon(pts, fill=(232, 205, 150, 255), outline=(70, 45, 20, 255), width=8)
    f = ImageFont.truetype(BANGERS, 66)
    d.text((40, 42), "TO BE CONTINUED", font=f, fill=(70, 45, 20, 255))
    return np.array(img)


def vhs_text(label):
    img = Image.new("RGBA", (520, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(MONO, 52)
    d.text((6, 10), label, font=f, fill=(255, 255, 255, 235), stroke_width=2, stroke_fill=(0, 0, 0, 120))
    return np.array(img)


def premul(rgba):
    a = rgba[..., 3:4].astype(np.float32) / 255
    return np.concatenate([rgba[..., :3].astype(np.float32) * a, a * 255], 2)


def blend(frame, pm, x, y, alpha=1.0):
    """pm: premultiplied float32 RGBA; (x, y) top-left; frame uint8 RGB modified in place."""
    h, w = pm.shape[:2]
    x0, y0, x1, y1 = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if x0 >= x1 or y0 >= y1:
        return
    p = pm[y0 - y:y1 - y, x0 - x:x1 - x]
    a = p[..., 3:4] / 255 * alpha
    reg = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = np.clip(p[..., :3] * alpha + reg * (1 - a), 0, 255).astype(np.uint8)


def transform(pm, scale, rot):
    if abs(scale - 1) < 1e-3 and abs(rot) < 0.05:
        return pm
    h, w = pm.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, scale)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw, nh = int(h * sin + w * cos) + 2, int(h * cos + w * sin) + 2
    M[0, 2] += nw / 2 - w / 2
    M[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(pm, M, (nw, nh), flags=cv2.INTER_LINEAR, borderValue=(0, 0, 0, 0))


class Sticker:
    def __init__(self, rgba, t0, t1, x, y, anim="pop", rot=0.0, wobble=0.0, track=None, blink=None, layer=1):
        self.pm = premul(rgba)
        self.t0, self.t1, self.x, self.y = t0, t1, x, y
        self.anim, self.rot, self.wobble, self.track, self.blink, self.layer = anim, rot, wobble, track, blink, layer
        self._static = None

    def draw(self, frame, t):
        if not (self.t0 <= t < self.t1):
            return
        u = t - self.t0
        if self.blink and int(u / self.blink) % 2:
            return
        scale, alpha, dx = 1.0, 1.0, 0.0
        if self.anim == "pop":
            scale = 0.25 + 0.95 * min(u / 0.12, 1) if u < 0.12 else (1.2 - 0.2 * min((u - 0.12) / 0.08, 1))
        elif self.anim == "slam":
            scale, alpha = (1.7 - 0.7 * min(u / 0.1, 1)), min(u / 0.06, 1)
        elif self.anim == "fade":
            alpha = min(u / 0.15, 1)
        elif self.anim == "slide":
            k = min(u / 0.25, 1)
            dx = -900 * (1 - k) ** 3
        left = self.t1 - t
        if left < 0.08 and self.anim in ("pop", "slam"):
            scale *= max(left / 0.08, 0.2)
        rot = self.rot + (self.wobble * math.sin(2 * math.pi * 1.4 * u) if self.wobble else 0)
        x, y = self.x, self.y
        if self.track:
            ts = [k[0] for k in self.track]
            x, y = float(np.interp(u, ts, [k[1] for k in self.track])), float(np.interp(u, ts, [k[2] for k in self.track]))
        static = abs(scale - 1) < 1e-3 and not self.wobble
        if static:
            if self._static is None:
                self._static = transform(self.pm, 1.0, self.rot)
            img = self._static
        else:
            img = transform(self.pm, scale, rot)
        h, w = img.shape[:2]
        blend(frame, img, int(x - w / 2 + dx), int(y - h / 2), alpha)


# ---------------------------------------------------------------- video effects

class Looks:
    def __init__(self):
        rng = np.random.default_rng(5)
        self.noise = [(rng.standard_normal((H // 2, W // 2)) * 9).astype(np.float32) for _ in range(6)]
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vig = np.clip(1.15 - 0.45 * r ** 2, 0.35, 1).astype(np.float32)[..., None]
        self.scan = np.where((np.arange(H) % 3) == 0, 0.86, 1.0).astype(np.float32)[:, None, None]
        self.play, self.rew = vhs_text("PLAY ►"), vhs_text("◄◄ REWIND")
        self.play_pm, self.rew_pm = premul(self.play), premul(self.rew)
        sh = np.zeros((H, W, 1), np.float32)
        for y0, y1 in ((BAND_Y - 26, BAND_Y), (BAND_Y + BAND_H, BAND_Y + BAND_H + 26)):
            ramp = np.linspace(0, 1, y1 - y0)[:, None, None] if y0 < BAND_Y else np.linspace(1, 0, y1 - y0)[:, None, None]
            sh[y0:y1] = ramp * 0.55
        self.band_shadow = 1 - sh

    def vhs(self, f, k, rewind=False):
        x = f.astype(np.float32)
        x[..., 0] = np.roll(x[..., 0], 4, axis=1)
        x[..., 2] = np.roll(x[..., 2], -4, axis=1)
        n = cv2.resize(self.noise[k % 6], (W, H), interpolation=cv2.INTER_NEAREST)[..., None]
        x = (x * 0.92 + 10) * self.scan * self.vig + n
        x *= 1 + 0.035 * math.sin(k * 1.7) + 0.02 * ((k * 7919) % 11 - 5) / 5
        out = np.clip(x, 0, 255).astype(np.uint8)
        if rewind:
            rng = np.random.default_rng(k)
            for _ in range(3):
                y = int(rng.integers(BAND_Y, BAND_Y + BAND_H - 80))
                hgt = int(rng.integers(20, 70))
                out[y:y + hgt] = np.roll(out[y:y + hgt], int(rng.integers(-70, 70)), axis=1)
                out[y + hgt:y + hgt + 3] = 230
        blend(out, self.rew_pm if rewind else self.play_pm, W - 420, BAND_Y + 24)
        return out

    @staticmethod
    def deepfry(f):
        hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[..., 1] = np.clip(hsv[..., 1] * 2.4, 0, 255)
        x = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
        x = (x - 128) * 1.55 + 140
        x[..., 0] *= 1.12
        x[..., 2] *= 0.85
        x = np.clip(x, 0, 255).astype(np.uint8)
        x = cv2.addWeighted(x, 2.2, cv2.GaussianBlur(x, (0, 0), 3), -1.2, 0)
        small = cv2.resize(x, (W // 2, H // 2))
        ok, enc = cv2.imencode(".jpg", cv2.cvtColor(small, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 7])
        x = cv2.cvtColor(cv2.imdecode(enc, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
        return cv2.resize(x, (W, H), interpolation=cv2.INTER_NEAREST)

    @staticmethod
    def sepia(f):
        m = np.array([[0.393, 0.769, 0.189], [0.349, 0.686, 0.168], [0.272, 0.534, 0.131]], np.float32)
        return np.clip(f.astype(np.float32) @ m.T * 0.95, 0, 255).astype(np.uint8)

    @staticmethod
    def bw(f):
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)
        return np.repeat(g[..., None], 3, 2)


# ---------------------------------------------------------------- shots

def ease(u, kind):
    u = min(max(u, 0.0), 1.0)
    if kind == "out":
        return 1 - (1 - u) ** 3
    if kind == "linear":
        return u
    return u * u * (3 - 2 * u)


def geometry(sh, tau, src_wh):
    sw, shh = src_wh
    et = sh.get("ease_time") or (0.18 if sh.get("ease") == "punch" else max(sh["_dur"], 1e-3))
    e = ease(tau / et, "out" if sh.get("ease") == "punch" else sh.get("ease", "smooth"))
    z = sh.get("zoom", 1.0) + (sh.get("zoom_to", sh.get("zoom", 1.0)) - sh.get("zoom", 1.0)) * e
    x = sh.get("x", 0.5) + (sh.get("x_to", sh.get("x", 0.5)) - sh.get("x", 0.5)) * e
    y = sh.get("y", 0.5) + (sh.get("y_to", sh.get("y", 0.5)) - sh.get("y", 0.5)) * e
    ow, oh = (W, BAND_H) if sh["_layout"] == "band" else (W, H)
    rh = shh / z
    rw = rh * ow / oh
    if rw > sw:
        rw = sw
        rh = rw * oh / ow
    cx = min(max(x * sw, rw / 2), sw - rw / 2)
    cy = min(max(y * shh, rh / 2), shh - rh / 2)
    return cx, cy, rw, rh, ow, oh


def src_to_screen(sh, tau, src_wh, sx, sy):
    cx, cy, rw, rh, ow, oh = geometry(sh, tau, src_wh)
    s = oh / rh
    oy = BAND_Y if sh["_layout"] == "band" else 0
    return (sx - (cx - rw / 2)) * s, oy + (sy - (cy - rh / 2)) * s, s


def shake_offset(fx, tau):
    dx = dy = rot = 0.0
    for a, b, amp in fx.get("shake", []):
        if a <= tau < b:
            k = 1 - (tau - a) / max(b - a, 1e-3)
            dx += amp * k * (0.6 * math.sin(2 * math.pi * 17 * tau + 1.3) + 0.4 * math.sin(2 * math.pi * 29 * tau))
            dy += amp * k * (0.6 * math.sin(2 * math.pi * 19 * tau + 0.4) + 0.4 * math.sin(2 * math.pi * 31 * tau + 2))
            rot += amp / 30 * k * math.sin(2 * math.pi * 11 * tau)
    return dx, dy, rot


def load_frames(path, t0, t1, wh):
    t0 = max(0.0, t0)
    n = max(1, int(math.ceil((t1 - t0) * FPS)) + 2)
    raw = run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-i", path, "-frames:v", n, "-vf", f"fps={FPS}",
               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"])
    return np.frombuffer(raw, np.uint8).reshape(-1, wh[1], wh[0], 3), t0


def src_time(sh, tau):
    if sh.get("freeze"):
        return sh["t"]
    sp = sh.get("speed", 1.0)
    return sh["t"] - tau * sp if sh.get("reverse") else sh["t"] + tau * sp


def render_shot(sh, n, src, looks, stickers, hooks, t_abs0, pipe, look):
    wh = src["wh"]
    taus = [k / FPS for k in range(n)]
    times = [src_time(sh, tau) for tau in taus]
    frames, ft0 = load_frames(src["path"], min(times) - 0.02, max(times) + 0.1, wh)
    fx = sh.get("fx", {})
    blendmode = sh.get("speed", 1.0) < 0.8 and not sh.get("freeze")
    for k, (tau, st) in enumerate(zip(taus, times)):
        fi = (st - ft0) * FPS
        i0 = int(min(max(math.floor(fi), 0), len(frames) - 1))
        i1 = min(i0 + 1, len(frames) - 1)
        a = fi - math.floor(fi)
        img = frames[i0] if not blendmode or a < 0.05 or i0 == i1 else cv2.addWeighted(frames[i0], 1 - a, frames[i1], a, 0)
        cx, cy, rw, rh, ow, oh = geometry(sh, tau, wh)
        s = oh / rh
        dx, dy, rot = shake_offset(fx, tau)
        M = np.array([[s, 0, -(cx - rw / 2) * s + dx], [0, s, -(cy - rh / 2) * s + dy]], np.float32)
        if rot:
            R = cv2.getRotationMatrix2D((ow / 2, oh / 2), rot, 1.0)
            M = (np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]))[:2].astype(np.float32)
        fg = cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        if sh["_layout"] == "band":
            small = cv2.GaussianBlur(cv2.resize(img, (160, 90), interpolation=cv2.INTER_AREA), (0, 0), 3.5)
            cw = 90 * W / H
            x0 = int(80 - cw / 2)
            bg = cv2.resize(small[:, x0:x0 + int(cw)], (W, H), interpolation=cv2.INTER_LINEAR)
            out = (bg.astype(np.float32) * 0.5).astype(np.uint8)
            out[BAND_Y:BAND_Y + BAND_H] = fg
            for y0, y1 in ((BAND_Y - 26, BAND_Y), (BAND_Y + BAND_H, BAND_Y + BAND_H + 26)):
                out[y0:y1] = (out[y0:y1] * looks.band_shadow[y0:y1]).astype(np.uint8)
        else:
            out = fg
        if fx.get("deepfry") and fx["deepfry"][0] <= tau < fx["deepfry"][1]:
            out = looks.deepfry(out)
        if fx.get("sepia"):
            out = looks.sepia(out)
        if fx.get("bw"):
            out = looks.bw(out)
        if fx.get("vhs") or look == "vhs" or fx.get("rewind"):
            out = looks.vhs(out, int((t_abs0 + tau) * FPS), rewind=bool(fx.get("rewind")))
        if fx.get("flash"):
            col, at = fx["flash"] if isinstance(fx["flash"], list) else (fx["flash"], 0.0)
            u = tau - at
            if 0 <= u < 0.3:
                c = np.array({"white": (255, 255, 255), "red": (230, 20, 20)}[col], np.float32)
                al = 0.85 * (1 - u / 0.3) ** 2
                out = np.clip(out.astype(np.float32) * (1 - al) + c * al, 0, 255).astype(np.uint8)
        t = t_abs0 + tau
        for stk in sorted(stickers, key=lambda q: q.layer):
            stk.draw(out, t)
        for hk in hooks:
            hk.draw(out, t)
        pipe.stdin.write(np.ascontiguousarray(out).tobytes())


def shot_audio(sh, n, src):
    dur = n / FPS
    m = int(round(dur * SR))
    if sh.get("freeze") or sh.get("mute"):
        return np.zeros((m, 2), np.float32)
    sp = sh.get("speed", 1.0)
    span = dur * sp
    a0 = sh["t"] - span if sh.get("reverse") else sh["t"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(a0, 0):.3f}", "-t", f"{span + 0.05:.3f}", "-i", src["path"],
                          "-vn", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2)
    if len(x) == 0:
        return np.zeros((m, 2), np.float32)
    if sh.get("reverse"):
        x = x[::-1]
    if abs(sp - 1) > 1e-3:
        idx = np.linspace(0, len(x) - 1, max(int(len(x) / sp), 1))
        x = np.stack([np.interp(idx, np.arange(len(x)), x[:, c]) for c in range(2)], 1)
    x = x[:m]
    return np.pad(x, ((0, m - len(x)), (0, 0))).astype(np.float32)


# ---------------------------------------------------------------- build

def build(job_path):
    job = json.loads(Path(job_path).read_text())
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    voices = Voices(job, work)
    for s in job["sources"].values():
        w, h = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                    "-of", "csv=p=0", s["path"]]).decode().strip().split(",")[:2]
        s["wh"] = (int(w), int(h))
    voice, speed = job.get("voice", "am_puck"), job.get("speed", 1.05)
    mvoice, mspeed = job.get("meme_voice", "am_onyx"), job.get("meme_speed", 0.92)

    # 1. timeline
    t = 0.0
    shots, lines, memes, sfx_ev, raw_stickers, cuts = [], [], [], [], [], []
    for bi, beat in enumerate(job["beats"]):
        delay, pad = beat.get("delay", 0.0), beat.get("pad", 0.22)
        say_len = 0.0
        if beat.get("say"):
            f, a = voices.say(beat["say"], beat.get("voice", voice), beat.get("speed", speed))
            say_len = len(a) / SR
            lines.append({"t": t + delay, "audio": a, "wav": f, "text": beat["say"]})
        meme_end = 0.0
        for mm in beat.get("meme", []):
            f, a = voices.say(mm["say"], mm.get("voice", mvoice), mm.get("speed", mspeed))
            memes.append({"t": t + mm.get("at", 0.0), "audio": a, "gain": mm.get("gain", 1.0)})
            meme_end = max(meme_end, mm.get("at", 0.0) + len(a) / SR)
        fixed = sum(s["dur"] for s in beat["shots"] if "dur" in s)
        flex = [s for s in beat["shots"] if "dur" not in s]
        D = max(beat.get("min", 0.0), (delay + say_len + pad) if beat.get("say") else 0.0,
                fixed + 0.35 * len(flex), meme_end + 0.15)
        rest = D - fixed
        ws = sum(s.get("w", 1.0) for s in flex)
        tt = t
        for k, s in enumerate(beat["shots"]):
            d = s["dur"] if "dur" in s else rest * s.get("w", 1.0) / ws
            if not flex and k == len(beat["shots"]) - 1:
                d += D - fixed
            s = dict(s, _layout=s.get("layout", job.get("layout", "band")), _start=tt)
            shots.append(s)
            s["_end"] = tt + d
            tt += d
        for e in beat.get("sfx", []):
            sfx_ev.append((t + e.get("at", 0.0), e["name"], e.get("gain", 0.8), e.get("kw", {})))
        for st in beat.get("stickers", []):
            t1 = None if st.get("until") == "video" else t + (st.get("at", 0.0) + st["dur"] if "dur" in st else D)
            raw_stickers.append(dict(st, _t0=t + st.get("at", 0.0), _t1=t1))
        if beat.get("music_cut"):
            cuts.append((t, t + D))
        t += D
    total = t
    for s in shots:  # frame-exact lengths
        s["_n"] = round(s["_end"] * FPS) - round(s["_start"] * FPS)
        s["_dur"] = s["_n"] / FPS
    print(f"{len(job['beats'])} beats, {len(shots)} shots, {total:.1f}s")

    # 2. stickers
    html_specs, built = {}, []
    hook_key = "hook_" + sha(job["hook"])
    html_specs[hook_key] = hook_html(job["hook"])
    if job.get("credit"):
        html_specs["credit_" + sha(job["credit"])] = credit_html(job["credit"])
    for st in raw_stickers:
        tp = st["type"]
        if tp == "emoji":
            st["_key"] = "e_" + sha(st["emoji"], st.get("size", 220))
            html_specs[st["_key"]] = emoji_html(st["emoji"], st.get("size", 220))
        elif tp == "text":
            st["_key"] = "t_" + sha({k: v for k, v in st.items() if not k.startswith("_") and k not in ("at", "dur", "x", "y", "anim", "track")})
            html_specs[st["_key"]] = text_html(st)
        elif tp == "bubble":
            st["_key"] = "b_" + sha(st["text"], st.get("size", 64), st.get("tail", "down"), st.get("maxw", 820), st.get("pad"))
            html_specs[st["_key"]] = bubble_html(st)
    imgs = chrome_stickers(html_specs, work)

    def shot_at(tabs):
        for s in shots:
            if s["_start"] <= tabs < s["_end"]:
                return s
        return shots[-1]

    stickers = []
    for i, st in enumerate(raw_stickers):
        t0 = st["_t0"]
        t1 = st["_t1"] if st["_t1"] is not None else total
        x, y = st.get("x", W / 2), st.get("y", 900)
        scale_src = 1.0
        if "src" in st:
            s = shot_at(t0 + 1e-3)
            x, y, scale_src = src_to_screen(s, t0 - s["_start"], job["sources"][s["src"]]["wh"], *st["src"])
            x += st.get("dx", 0)
            y += st.get("dy", 0)
        tp = st["type"]
        anim = st.get("anim", {"emoji": "pop", "text": "pop", "bubble": "pop", "circle": "pop", "arrow": "fade",
                               "rec": "none", "tbc": "slide"}[tp])
        if tp in ("emoji", "text", "bubble"):
            rgba = imgs[st["_key"]]
            if tp == "bubble" and st.get("anchor") == "tail":
                y -= rgba.shape[0] / 2 - 20
        elif tp == "circle":
            r = st.get("src_r", 0) * scale_src if "src_r" in st else st.get("r", 120)
            rgba = marker_circle(r, seed=i + 3, ry=st.get("ry"))
        elif tp == "arrow":
            p1 = (x, y) if "src" in st else tuple(st["to"])
            rgba = marker_arrow(tuple(st["from"]), p1, st.get("label"))
            x, y = W / 2, H / 2
        elif tp == "rec":
            stickers.append(Sticker(rec_dot(), t0, t1, 50 + 60, BAND_Y + 80 + 56, "none", blink=0.5, layer=3))
            rgba = rec_overlay()
            x, y = W / 2, H / 2
        elif tp == "tbc":
            rgba = tbc_arrow()
            x, y = st.get("x", 380), st.get("y", BAND_Y + BAND_H - 140)
        stickers.append(Sticker(rgba, t0, t1, x, y, anim, st.get("rot", 0.0), st.get("wobble", 0.0),
                                st.get("track"), st.get("blink"), st.get("layer", 1)))
    hooks = [Sticker(imgs[hook_key], 0.0, total + 1, W / 2, 0, "slam", layer=9)]
    hooks[0].y = 165 + hooks[0].pm.shape[0] / 2 - 28
    if job.get("credit"):
        cimg = imgs["credit_" + sha(job["credit"])]
        hooks.append(Sticker(cimg, 0.0, total + 1, 30 + cimg.shape[1] / 2 - 28, BAND_Y + 34, "none", layer=9))

    # 3. video
    looks = Looks()
    vid = work / "video.mp4"
    pipe = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                             "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "15",
                             "-pix_fmt", "yuv420p", str(vid)], stdin=subprocess.PIPE)
    for s in shots:
        render_shot(s, s["_n"], job["sources"][s["src"]], looks, stickers, hooks, round(s["_start"] * FPS) / FPS,
                    pipe, job.get("look"))
    pipe.stdin.close()
    pipe.wait()

    # 4. audio
    n_all = int(round(total * SR)) + SR
    narr = np.zeros((n_all, 2), np.float32)
    for ln in lines:
        MK._place(narr, np.stack([ln["audio"]] * 2, 1), ln["t"])
    for mm in memes:
        MK._place(narr, np.stack([mm["audio"]] * 2, 1) * mm["gain"], mm["t"])
    game = np.concatenate([shot_audio(s, s["_n"], job["sources"][s["src"]]) for s in shots])
    game = np.pad(game, ((0, max(0, n_all - len(game))), (0, 0)))[:n_all]
    fx = np.zeros((n_all, 2), np.float32)
    for t0, name, gain, kw in sfx_ev:
        MK._place(fx, MK.sfx(name, **kw), t0, gain)
    mus = np.zeros((n_all, 2), np.float32)
    if job.get("music"):
        m = MK.music(job["music"], total + 0.5)
        env = np.ones(len(m), np.float32)
        for a, b in cuts:
            i0, i1 = int(a * SR), int(b * SR)
            env[i0:i1] = 0
            ramp = int(0.06 * SR)
            env[max(i0 - ramp, 0):i0] = np.minimum(env[max(i0 - ramp, 0):i0], np.linspace(1, 0, i0 - max(i0 - ramp, 0)))
            env[i1:i1 + ramp] = np.minimum(env[i1:i1 + ramp], np.linspace(0, 1, len(env[i1:i1 + ramp])))
        m = m * env[:, None] * job.get("music_volume", 0.5)
        MK._place(mus, m, 0.0)
    for name, arr in (("narr", narr), ("game", game), ("fx", fx), ("mus", mus)):
        sf.write(work / f"{name}.wav", arr[: int(total * SR)], SR)

    def gain_to(path, target):
        meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(path), "-af", "loudnorm=print_format=json", "-f", "null", "-"],
                              capture_output=True, text=True).stderr
        i = float(json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])["input_i"])
        return 0.0 if i < -70 else target - i

    gn = gain_to(work / "narr.wav", -15)
    gg = gain_to(work / "game.wav", -21) + 20 * math.log10(max(job.get("game_volume", 0.7), 1e-3))
    mix = (f"[0:a]volume={gn:.2f}dB,asplit=3[n1][n2][n3];"
           f"[1:a]volume={gg:.2f}dB[g0];[g0][n2]sidechaincompress=threshold=0.02:ratio=8:attack=10:release=350[gd];"
           "[3:a]volume=1.0[m0];[m0][n3]sidechaincompress=threshold=0.02:ratio=5:attack=30:release=600[md];"
           f"[2:a]volume={job.get('sfx_volume', 1.0)}[fx];[n1][gd][md][fx]amix=inputs=4:normalize=0:duration=first[mix]")
    run(["ffmpeg", "-v", "error", "-y", "-i", work / "narr.wav", "-i", work / "game.wav", "-i", work / "fx.wav",
         "-i", work / "mus.wav", "-filter_complex", mix, "-map", "[mix]", work / "mix.wav"])
    meas = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(work / "mix.wav"), "-af",
                           "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(meas[meas.rindex("{"): meas.rindex("}") + 1])
    loud = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
            f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,aresample={SR}")

    # 5. captions
    import pysubs2
    subs = pysubs2.SSAFile()
    subs.info.update({"PlayResX": str(W), "PlayResY": str(H), "WrapStyle": "2", "ScaledBorderAndShadow": "yes"})
    subs.styles["C"] = pysubs2.SSAStyle(fontname="Luckiest Guy", fontsize=job.get("caption_size", 98),
                                        primarycolor=pysubs2.Color(255, 255, 255), outlinecolor=pysubs2.Color(0, 0, 0),
                                        backcolor=pysubs2.Color(0, 0, 0, 110), outline=8, shadow=5,
                                        alignment=pysubs2.Alignment.MIDDLE_CENTER)
    colors = ["&HFFFFFF&", "&H00E6FF&", "&HFFFFFF&", "&H6EFF3D&"]
    keys = {k.lower() for k in job.get("keywords", [])}
    rng = np.random.default_rng(3)
    cy = job.get("caption_y", 1470)
    k = 0
    for ln in lines:
        ws = [(w, ln["t"] + a, ln["t"] + b) for w, a, b in voices.words(ln["wav"], ln["text"])]
        chunks, cur = [], []
        for w in ws:
            txt = " ".join(x[0] for x in cur + [w])
            if cur and (len(cur) >= 2 or len(txt) > 12 or re.search(r"[.,!?:;]$", cur[-1][0])):
                chunks.append(cur)
                cur = []
            cur.append(w)
        if cur:
            chunks.append(cur)
        for j, ch in enumerate(chunks):
            a = ch[0][1]
            b = chunks[j + 1][0][1] if j + 1 < len(chunks) else ch[-1][2] + 0.15
            b = max(b, a + 0.12)
            words = " ".join(re.sub(r"[.,;:]+$", "", w[0]) for w in ch).upper()
            col = "&H3B3BFF&" if any(re.sub(r"[^a-z0-9$']", "", w[0].lower()) in keys for w in ch) else colors[k % len(colors)]
            rot = float(rng.uniform(-3, 3))
            subs.append(pysubs2.SSAEvent(start=int(a * 1000), end=int(b * 1000), style="C",
                                         text=f"{{\\pos(540,{cy})\\frz{rot:.1f}\\1c{col}\\fscx45\\fscy45"
                                              f"\\t(0,90,\\fscx116\\fscy116)\\t(90,160,\\fscx100\\fscy100)}}{words}"))
            k += 1
    ass = work / "captions.ass"
    subs.save(str(ass))

    # 6. final
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", vid, "-i", work / "mix.wav", "-filter_complex",
         f"[0:v]ass={ass}:fontsdir={FONTS}[v];[1:a]{loud}[a]", "-map", "[v]", "-map", "[a]", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-profile:v", "high", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out])
    print(out, f"{total:.1f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    build(ap.parse_args().job)
