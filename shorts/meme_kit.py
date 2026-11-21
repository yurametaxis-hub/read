"""Meme sound effects and music beds, synthesized from scratch: no samples, nothing to license or get claimed.

    import meme_kit as MK
    MK.sfx("vine_boom")            -> stereo float array at 48 kHz
    MK.music("phonk", 30.0)        -> 30 s loop: phonk, horror, doc, pizz
Run this file to write every sound into a folder for a listen: python3 shorts/meme_kit.py OUT_DIR
"""
import sys
from pathlib import Path

import numpy as np
from scipy import signal

SR = 48000


def _rng(seed):
    return np.random.default_rng(seed)


def _t(d):
    return np.arange(int(round(d * SR))) / SR


def _phase(freq):
    return np.cumsum(freq) / SR


def _sine(freq):
    return np.sin(2 * np.pi * _phase(freq))


def _saw(freq):
    return 2 * (_phase(freq) % 1.0) - 1


def _square(freq, duty=0.5):
    return np.where((_phase(freq) % 1.0) < duty, 1.0, -1.0)


def _const(f, n):
    return np.full(n, float(f))


def _filt(x, kind, f, order=4):
    f = np.atleast_1d(np.asarray(f, float)) / (SR / 2)
    sos = signal.butter(order, f if kind == "bandpass" else f[0], btype="band" if kind == "bandpass" else kind,
                        output="sos")
    return signal.sosfilt(sos, x, axis=0)


def _noise(n, seed=1):
    return _rng(seed).standard_normal(n)


def _env(n, a=0.003, d=0.3, hold=0.0):
    t = np.arange(n) / SR
    e = np.minimum(1.0, t / max(a, 1e-4))
    return e * np.where(t < a + hold, 1.0, np.exp(-(t - a - hold) / d))


def _edges(x, fin=0.004, fout=0.03):
    n = len(x)
    e = np.ones(n)
    a, b = max(1, int(fin * SR)), max(1, int(fout * SR))
    e[:a] = np.linspace(0, 1, a)
    e[-b:] *= np.linspace(1, 0, b)
    return x * e


def _sweep_lp(x, fc):
    """One-pole low-pass with a cutoff that moves per sample (wah, sweeps)."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = 1 - np.exp(-2 * np.pi * np.clip(fc, 10, SR / 2.2) / SR)
    y = np.empty_like(x)
    s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s)
        y[i] = s
    return y


def _sweep_bp(x, fc, q=0.35):
    """Chamberlin state variable filter, band output, cutoff per sample."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    f = 2 * np.sin(np.pi * np.clip(fc, 20, SR / 6) / SR)
    low = band = 0.0
    y = np.empty_like(x)
    for i in range(len(x)):
        low += f[i] * band
        high = x[i] - low - q * band
        band += f[i] * high
        y[i] = band
    return y


def _reverb(x, decay=1.0, wet=0.25, seed=3):
    n = int(decay * SR)
    ir = _noise(n, seed) * np.exp(-np.arange(n) / SR / (decay / 5))
    ir = _filt(ir, "lowpass", 5000, 2)
    ir /= np.sqrt((ir ** 2).sum())
    y = signal.fftconvolve(x, ir)
    out = np.zeros(len(y))
    out[: len(x)] += x * (1 - wet)
    return out + y * wet


def _norm(x, peak=0.89):
    m = np.abs(x).max()
    return x * (peak / m) if m > 0 else x


def _stereo(x, spread=0.0):
    x = np.asarray(x, float)
    if spread <= 0:
        return np.stack([x, x], 1).astype(np.float32)
    k = int(spread * 0.0004 * SR)
    r = np.concatenate([np.zeros(k), x[:-k]]) if k else x
    return np.stack([x, r], 1).astype(np.float32)


def _place(dst, x, t0, gain=1.0):
    i = int(t0 * SR)
    if i >= len(dst):
        return
    m = min(len(x), len(dst) - i)
    dst[i:i + m] += x[:m] * gain


# ---------------------------------------------------------------- sound effects

def vine_boom():
    t = _t(1.5)
    n = len(t)
    f = 42 + 70 * np.exp(-t / 0.05)
    body = (_sine(f) + 0.35 * _sine(2 * f) + 0.12 * _sine(3 * f)) * _env(n, 0.002, 0.42)
    body = np.tanh(2.2 * body) / np.tanh(2.2)
    click = _filt(_noise(n), "lowpass", 2500) * _env(n, 0.0005, 0.012) * 0.6
    return _stereo(_norm(_reverb(body + click, 1.1, 0.22)))


def record_scratch():
    bt = _t(3.0)
    base = 0.6 * _saw(_const(196, len(bt))) + 0.8 * _filt(_noise(len(bt)), "bandpass", (700, 4500))
    t = _t(0.6)
    r = np.interp(t, [0, 0.08, 0.16, 0.26, 0.38, 0.5, 0.6], [0, 3.2, 3.0, -2.6, 3.4, 0.6, 0])
    x = np.interp(1.2 + np.cumsum(r) / SR, bt, base) * np.clip(np.abs(r) / 3, 0, 1) ** 0.7
    return _stereo(_norm(_edges(_filt(x, "highpass", 150, 2))))


def airhorn():
    n = int(1.55 * SR)
    x = np.zeros(n)
    for a, b in [(0.0, 0.13), (0.18, 0.31), (0.37, 1.45)]:
        i0, i1 = int(a * SR), int(b * SR)
        m = i1 - i0
        tt = np.arange(m) / SR
        vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * tt)
        drop = 1 - 0.04 * np.clip((tt - (m / SR - 0.2)) / 0.2, 0, 1) if b > 1 else 1
        s = sum(_saw(_const(f, m) * vib * drop) for f in (311.13, 392.0, 466.16, 622.25))
        x[i0:i1] += s * np.minimum(1, tt / 0.01) * np.minimum(1, (m / SR - tt) / 0.04)
    x = _filt(x, "bandpass", (350, 4200), 2)
    return _stereo(_norm(np.tanh(1.8 * x / np.abs(x).max())), spread=1)


def sad_trombone():
    out = []
    for k, (f0, d) in enumerate([(233.08, 0.45), (220.0, 0.45), (207.65, 0.45), (196.0, 1.5)]):
        n = int(d * SR)
        tt = np.arange(n) / SR
        vib = 1 + (0.018 * np.clip(tt / 0.4, 0, 1) if k == 3 else 0.004) * np.sin(2 * np.pi * 5.5 * tt)
        f = f0 * vib * (1 - 0.02 * np.exp(-tt / 0.05))
        tone = 0.7 * _saw(f) + 0.3 * _square(f)
        if k < 3:
            fc = 300 + 1600 * np.sin(np.pi * np.clip(tt / d, 0, 1)) ** 1.5
        else:
            fc = 300 + 1400 * np.clip(tt / 0.25, 0, 1) * np.exp(-np.clip(tt - 0.25, 0, None) / 0.9)
        tone = _sweep_lp(_sweep_lp(tone, fc), fc)
        out.append(tone * np.minimum(1, tt / 0.03) * np.minimum(1, (d - tt) / 0.06))
    return _stereo(_norm(_reverb(np.concatenate(out), 0.8, 0.15)))


def ding():
    t = _t(1.4)
    x = sum(a * np.sin(2 * np.pi * 1318.5 * r * t) * np.exp(-t / (0.55 / r)) for r, a in ((1, 1), (2.01, 0.4), (3.02, 0.15)))
    return _stereo(_norm(_reverb(x * np.minimum(1, t / 0.002), 0.7, 0.15)))


def buzzer():
    n = int(0.55 * SR)
    x = _square(_const(120, n)) + _square(_const(127, n))
    return _stereo(_norm(_edges(_filt(x, "lowpass", 2500, 2), 0.01, 0.03)) * 0.8)


def bonk():
    t = _t(0.3)
    x = np.sin(2 * np.pi * _phase(120 + 200 * np.exp(-t / 0.03))) * np.exp(-t / 0.07)
    x += _filt(_noise(len(t)), "bandpass", (1500, 6000)) * np.exp(-t / 0.006) * 0.5
    return _stereo(_norm(x))


def boing():
    t = _t(0.8)
    f = 260 * (1 + 0.25 * np.sin(2 * np.pi * 12 * t) * np.exp(-t / 0.4))
    return _stereo(_norm(_sine(f) * _env(len(t), 0.003, 0.3)))


def pop():
    t = _t(0.12)
    x = _sine(600 + 900 * t / 0.12) * np.exp(-t / 0.03)
    return _stereo(_norm(x) * 0.6)


def shutter():
    n = int(0.25 * SR)
    x = np.zeros(n)
    for t0, d in ((0.0, 0.004), (0.065, 0.003)):
        m = int(0.03 * SR)
        burst = _filt(_noise(m, int(t0 * 1000) + 5), "highpass", 2000) * _env(m, 0.0003, d)
        x[int(t0 * SR):int(t0 * SR) + m] += burst
    return _stereo(_norm(x))


def rewind():
    t = _t(0.9)
    f = (900 + 2400 * (t / 0.9) ** 0.7) * (1 + 0.08 * np.sin(2 * np.pi * 25 * t))
    x = 0.6 * _sine(f) + 0.5 * _sweep_bp(_noise(len(t)), f, 0.6)
    x *= np.sin(np.pi * np.clip(t / 0.9, 0, 1)) ** 0.5
    return _stereo(_norm(np.tanh(1.5 * x)), spread=1)


def heartbeat(bpm=70, beats=4):
    gap = 60 / bpm
    n = int((gap * beats + 0.5) * SR)
    x = np.zeros(n)
    m = int(0.25 * SR)
    tt = np.arange(m) / SR
    thump = np.sin(2 * np.pi * _phase(45 + 30 * np.exp(-tt / 0.03))) * np.exp(-tt / 0.07)
    thump += _filt(_noise(m), "lowpass", 300) * np.exp(-tt / 0.02) * 0.4
    for k in range(beats):
        _place(x, thump, k * gap)
        _place(x, thump, k * gap + 0.22, 0.7)
    return _stereo(_norm(np.tanh(1.5 * x)))


def jumpscare():
    t = _t(1.6)
    n = len(t)
    trem = 1 + 0.5 * np.sin(2 * np.pi * 14 * t)
    cluster = sum(_saw(_const(f, n)) for f in (523, 554, 740, 1046, 1108)) * trem * _env(n, 0.005, 0.5)
    burst = _filt(_noise(n), "bandpass", (500, 6000)) * _env(n, 0.002, 0.25)
    x = 0.5 * cluster / 5 + 0.6 * burst
    x[: len(vine_boom()[:, 0])] += 0.5 * vine_boom()[:n, 0]
    return _stereo(_norm(_reverb(x, 1.0, 0.25)), spread=1)


def riser(d=1.8):
    t = _t(d)
    fc = 300 + 4700 * (t / d) ** 2
    x = _sweep_bp(_noise(len(t)), fc, 0.5) + 0.25 * _sine(200 + 700 * (t / d) ** 1.5)
    return _stereo(_norm(x * (t / d) ** 2), spread=1)


def whoosh():
    t = _t(0.5)
    x = _sweep_bp(_noise(len(t)), 2200 - 1700 * t / 0.5, 0.6) * np.sin(np.pi * t / 0.5) ** 2
    return _stereo(_norm(x) * 0.7, spread=1)


def slowmo():
    t = _t(0.9)
    x = _sine(60 + 460 * np.exp(-t / 0.25)) * np.exp(-t / 0.5)
    x += _sweep_lp(_noise(len(t)), 4000 * np.exp(-t / 0.2) + 100) * 0.5 * np.exp(-t / 0.4)
    return _stereo(_norm(x))


def kaching():
    t = _t(0.9)
    x = np.zeros(len(t))
    for t0 in (0.0, 0.12):
        tt = np.clip(t - t0, 0, None)
        on = t >= t0
        x += on * sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.18) for f in (2637, 3520, 5274))
    x += _filt(_noise(len(t)), "lowpass", 900) * np.exp(-np.clip(t - 0.25, 0, None) / 0.05) * (t >= 0.25) * 0.8
    return _stereo(_norm(x))


def glitch():
    n = int(0.35 * SR)
    x = np.zeros(n)
    rng = _rng(11)
    i = 0
    while i < n:
        m = int(rng.uniform(0.015, 0.04) * SR)
        if rng.random() < 0.5:
            seg = _square(_const(rng.uniform(80, 1800), m))
        else:
            seg = np.round(_noise(m, int(rng.integers(1e6))) * 3) / 3
        x[i:i + m] = seg[: n - i] * rng.uniform(0.4, 1.0)
        i += m + int(rng.uniform(0, 0.01) * SR)
    return _stereo(_norm(_filt(x, "highpass", 100, 2)) * 0.8)


def dun_dun():
    out = []
    for f0, d in ((164.81, 0.26), (174.61, 0.26), (155.56, 1.35)):
        n = int(d * SR)
        tt = np.arange(n) / SR
        trem = 1 + (0.25 * np.sin(2 * np.pi * 7 * tt) * np.clip(tt / 0.4, 0, 1) if d > 1 else 0)
        tone = sum(0.6 * _saw(_const(f0 * m, n)) + 0.4 * _square(_const(f0 * m, n)) for m in (1, 2))
        tone = _filt(tone, "lowpass", 2200, 2) * trem
        out.append(tone * np.minimum(1, tt / 0.02) * np.minimum(1, (d - tt) / 0.05))
    return _stereo(_norm(_reverb(np.concatenate(out), 1.0, 0.2)))


SFX = {f.__name__: f for f in (vine_boom, record_scratch, airhorn, sad_trombone, ding, buzzer, bonk, boing, pop,
                               shutter, rewind, heartbeat, jumpscare, riser, whoosh, slowmo, kaching, glitch, dun_dun)}
_cache = {}


def sfx(name, **kw):
    key = (name, tuple(sorted(kw.items())))
    if key not in _cache:
        _cache[key] = SFX[name](**kw)
    return _cache[key]


# ---------------------------------------------------------------- music beds

def _pluck(f, d, bright=1.0):
    t = _t(d)
    x = sum(np.sin(2 * np.pi * f * k * t) / k ** 1.2 * np.exp(-t / (0.9 / k ** (0.7 * bright))) for k in range(1, 12))
    return x * np.minimum(1, t / 0.002)


def _kick(d=0.45):
    t = _t(d)
    x = np.sin(2 * np.pi * _phase(48 + 110 * np.exp(-t / 0.035))) * np.exp(-t / 0.25)
    return np.tanh(2.5 * x)


def _clap(d=0.25):
    t = _t(d)
    x = _filt(_noise(len(t), 4), "bandpass", (900, 5000)) * np.exp(-t / 0.07)
    return x + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.04)


def _hat(d=0.06, seed=9):
    t = _t(d)
    return _filt(_noise(len(t), seed), "highpass", 7000) * np.exp(-t / 0.018)


def _cowbell(f, d=0.22):
    t = _t(d)
    x = _square(_const(f, len(t))) + _square(_const(f * 1.48, len(t)))
    return _filt(x, "bandpass", (f * 0.9, f * 3.5), 2) * np.exp(-t / 0.09)


def phonk(dur, bpm=128):
    step = 60 / bpm / 4
    bar = step * 16
    n = int(dur * SR) + SR
    drums, bass, bell = np.zeros(n), np.zeros(n), np.zeros(n)
    roots = [43.65, 43.65, 51.91, 38.89]
    melody = [(0, 698.5), (3, 698.5), (6, 830.6), (8, 1046.5), (10, 830.6), (12, 932.3), (14, 830.6)]
    melody2 = [(0, 698.5), (3, 622.3), (6, 698.5), (8, 830.6), (11, 1046.5), (13, 932.3), (14, 830.6)]
    k = 0
    while k * bar < dur + bar:
        t0 = k * bar
        for s in (0, 6, 8, 11):
            _place(drums, _kick(), t0 + s * step)
        for s in (4, 12):
            _place(drums, _clap(), t0 + s * step, 0.55)
        for s in range(0, 16, 2):
            _place(drums, _hat(), t0 + s * step, 0.22 if s % 4 else 0.3)
        if k % 2:
            for s in (13, 14, 15):
                _place(drums, _hat(0.04, 10 + s), t0 + s * step, 0.15)
        f = roots[k % 4]
        m = int(bar * SR)
        tt = np.arange(m) / SR
        b = np.tanh(3 * np.sin(2 * np.pi * f * tt)) * 0.9
        duck = np.ones(m)
        for s in (0, 6, 8, 11):
            i = int(s * step * SR)
            j = min(m, i + int(0.09 * SR))
            duck[i:j] = np.linspace(0.2, 1, j - i)
        _place(bass, b * duck, t0)
        for s, fr in (melody if k % 2 == 0 else melody2):
            _place(bell, _cowbell(fr), t0 + s * step)
        k += 1
    x = 0.9 * drums + 0.55 * bass + 0.35 * bell
    return _stereo(_norm(np.tanh(1.2 * x[: int(dur * SR)])) * 0.8, spread=1)


def horror(dur):
    t = _t(dur)
    n = len(t)
    drone = _filt(_saw(_const(55, n)) + _saw(_const(55.6, n)) + 0.5 * _saw(_const(82.4, n)), "lowpass", 220, 2)
    drone *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.11 * t)
    wind = _filt(_noise(n, 21), "bandpass", (180, 900), 2) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.07 * t + 1)) * 0.35
    ring = (np.sin(2 * np.pi * 1567 * t) + np.sin(2 * np.pi * 1661 * t)) * 0.02 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * t))
    x = (drone * 0.35 + wind + ring) * (0.6 + 0.4 * t / max(dur, 1))
    return _stereo(_norm(_edges(x, 0.5, 1.0)) * 0.7, spread=2)


def doc(dur):
    chords = [(130.81, 164.81, 196.0, 246.94), (110.0, 130.81, 164.81, 196.0),
              (87.31, 110.0, 130.81, 164.81), (98.0, 123.47, 146.83, 164.81)]
    n = int(dur * SR) + 2 * SR
    pad, harp = np.zeros(n), np.zeros(n)
    k = 0
    while k * 4 < dur + 4:
        ch = chords[k % 4]
        m = int(4.8 * SR)
        tt = np.arange(m) / SR
        tone = sum(_saw(_const(f, m)) + _saw(_const(f * 1.004, m)) for f in ch)
        tone = _filt(tone, "lowpass", 900, 2) * np.minimum(1, tt / 1.0) * np.minimum(1, np.clip(4.8 - tt, 0, None) / 1.0)
        _place(pad, tone, k * 4)
        for j, f in enumerate((ch[0] * 4, ch[2] * 2, ch[1] * 4, ch[3] * 2, ch[2] * 4, ch[1] * 2, ch[3] * 4, ch[2] * 2)):
            _place(harp, _pluck(f, 1.2), k * 4 + j * 0.5, 0.5)
        k += 1
    x = _reverb(0.25 * pad / 8 + 0.4 * harp[:n], 1.6, 0.3)[: int(dur * SR)]
    return _stereo(_norm(_edges(x, 0.3, 0.8)) * 0.7, spread=2)


def pizz(dur, bpm=112):
    e = 60 / bpm / 2
    n = int(dur * SR) + SR
    x = np.zeros(n)
    bassline = [130.81, 0, 98.0, 0, 103.83, 0, 98.0, 0, 130.81, 0, 98.0, 0, 116.54, 0, 123.47, 0]
    tune = [523.25, 0, 622.25, 783.99, 739.99, 783.99, 0, 622.25, 523.25, 0, 466.16, 523.25, 622.25, 0, 587.33, 0]
    i = 0
    while i * e < dur + e:
        b = bassline[i % 16]
        if b:
            _place(x, _pluck(b, 0.35, 1.4), i * e, 0.9)
        m = tune[i % 16] if (i // 16) % 2 == 0 else tune[(i + 8) % 16]
        if m:
            _place(x, _pluck(m, 0.25, 1.6), i * e, 0.45)
        if i % 2 == 1:
            tt = _t(0.05)
            _place(x, np.sin(2 * np.pi * 950 * tt) * np.exp(-tt / 0.012), i * e, 0.25)
        i += 1
    return _stereo(_norm(_reverb(x[: int(dur * SR)], 0.6, 0.12)[: int(dur * SR)]) * 0.75, spread=1)


MUSIC = {"phonk": phonk, "horror": horror, "doc": doc, "pizz": pizz}


def music(style, dur):
    return MUSIC[style](dur)


if __name__ == "__main__":
    import soundfile as sf
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "meme_kit_demo")
    out.mkdir(parents=True, exist_ok=True)
    for name in SFX:
        sf.write(out / f"{name}.wav", sfx(name), SR)
    for name in MUSIC:
        sf.write(out / f"music_{name}.wav", music(name, 12.0), SR)
    print("wrote", len(SFX), "effects and", len(MUSIC), "music beds to", out)
