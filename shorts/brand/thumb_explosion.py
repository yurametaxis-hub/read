# Clickbait thumbnail for the long video: GTA 5 explosion vs GTA 6 car that only smokes.
# Fonts: in a fonts/ folder next to this file run
#   npm pack @fontsource/luckiest-guy @fontsource/bangers and unpack each .tgz into a folder of the same name.
"""Clickbait style thumbnail: GTA 5 explosion vs GTA 6 car that only smokes, marker style marks, comic font."""
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = "/root/.claude/uploads/7b73558d-f0ae-55b2-821f-adbe74710189/4bf24d0e-5.mkv"
FONTS = HERE / "fonts"
RENDER = "/home/user/read/shorts/brand/render_html.js"
W, H, MID = 1280, 720, 640


def frame(t, vf, out):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", SRC, "-frames:v", "1", "-vf", vf, str(out)], check=True)


# left: GTA 5 fireball with the car flipping, right: GTA 6 pickup with a small fire, Jason waiting
frame(16.55, "crop=660:720:252:0,eq=saturation=1.45:contrast=1.14:brightness=0.03,unsharp=5:5:0.9", HERE / "left.png")
frame(36.5, "scale=1152:648,crop=660:648:240:0,eq=saturation=0.62:contrast=0.96:brightness=-0.05,"
            "colorbalance=bs=0.10:bm=0.05:bh=0.04,unsharp=5:5:0.6", HERE / "right.png")

rnd = random.Random(7)


def marker_ellipse(cx, cy, rx, ry, a0=-2.2, overlap=0.5):
    pts = []
    n = 90
    for i in range(n + 1):
        a = a0 + (2 * math.pi + overlap) * i / n
        grow = 1 + 0.07 * i / n
        jit = 1 + rnd.uniform(-0.012, 0.012)
        pts.append((cx + rx * grow * jit * math.cos(a), cy + ry * grow * jit * math.sin(a)))
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


def wobble(points, amp=3):
    return [(x + rnd.uniform(-amp, amp), y + rnd.uniform(-amp, amp)) for x, y in points]


def path(points):
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in points)


def zigzag(x0, steps=7):
    pts, y = [(x0, -10)], -10
    for i in range(steps):
        y += (H + 20) / steps
        x = x0 + (34 if i % 2 == 0 else -30) + rnd.uniform(-6, 6)
        pts.append((x, y))
    return pts


zz = zigzag(MID)
clip = "polygon(" + ", ".join([f"0px -10px"] + [f"{x:.0f}px {y:.0f}px" for x, y in zz] + [f"0px {H + 10}px"]) + ")"

check = path(wobble([(70, 132), (118, 182), (214, 58)], 2))
cross = [path(wobble([(1112, 52), (1222, 160)], 2)), path(wobble([(1222, 52), (1112, 160)], 2))]
ring = marker_ellipse(1084, 300, 92, 62)
arrow_body = "M 900,470 C 960,440 1010,400 1030,360"
arrow_head = path([(1004, 372), (1033, 352), (1044, 390)])


def svg_marks():
    s = [f'<path d="{path(zz)}" stroke="#111" stroke-width="18" fill="none" stroke-linejoin="round"/>',
         f'<path d="{path(zz)}" stroke="#fff" stroke-width="9" fill="none" stroke-linejoin="round"/>']
    for d, col in ((check, "#25d046"),):
        s.append(f'<path d="{d}" stroke="#000" stroke-opacity=".55" stroke-width="54" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="translate(0,6)"/>')
        s.append(f'<path d="{d}" stroke="#fff" stroke-width="50" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        s.append(f'<path d="{d}" stroke="{col}" stroke-width="34" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    for d in cross:
        s.append(f'<path d="{d}" stroke="#000" stroke-opacity=".55" stroke-width="52" fill="none" stroke-linecap="round" transform="translate(0,6)"/>')
        s.append(f'<path d="{d}" stroke="#fff" stroke-width="48" fill="none" stroke-linecap="round"/>')
    for d in cross:
        s.append(f'<path d="{d}" stroke="#ff1e1e" stroke-width="32" fill="none" stroke-linecap="round"/>')
    for d in (ring, arrow_body, arrow_head):
        s.append(f'<path d="{d}" stroke="#000" stroke-opacity=".45" stroke-width="16" fill="none" stroke-linecap="round" stroke-linejoin="round" transform="translate(0,4)"/>')
        s.append(f'<path d="{d}" stroke="#ff2020" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(s)


def tape(x, y, w, h, rot):
    """Strip of white tape with torn short edges; it also hides the comparison channel's logo."""
    pts = [(x + rnd.uniform(0, 6), y)]
    pts += [(x + w - rnd.uniform(0, 6), y)]
    for i in range(1, 7):  # torn right edge
        pts.append((x + w + rnd.uniform(-7, 7), y + h * i / 7))
    pts.append((x + w - rnd.uniform(0, 6), y + h))
    pts.append((x + rnd.uniform(0, 6), y + h))
    for i in range(6, 0, -1):  # torn left edge
        pts.append((x + rnd.uniform(-7, 7), y + h * i / 7))
    d = path(pts) + "Z"
    cx, cy = x + w / 2, y + h / 2
    return (f'<g transform="rotate({rot} {cx} {cy})"><path d="{d}" fill="#000" fill-opacity=".45" transform="translate(4,7)"/>'
            f'<path d="{d}" fill="#f4f1e8"/></g>')


def page(main_html, main_size, small=None):
    return f'''<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: 'Lucky'; src: url(file://{FONTS}/fontsource-luckiest-guy-5.3.0/package/files/luckiest-guy-latin-400-normal.woff2); }}
@font-face {{ font-family: 'Bangers'; src: url(file://{FONTS}/fontsource-bangers-5.3.0/package/files/bangers-latin-400-normal.woff2); }}
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #0b0b14; }}
.r {{ position: absolute; left: {MID - 30}px; top: 0; width: 680px; height: 648px; background: url(file://{HERE}/right.png) left top/660px 648px no-repeat; }}
.r::after {{ content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 120px; background: linear-gradient(transparent, #0b0b14); }}
.l {{ position: absolute; left: 0; top: 0; width: {MID + 50}px; height: {H}px; clip-path: {clip};
      background: url(file://{HERE}/left.png) left top/660px 720px no-repeat; }}
.vig {{ position: absolute; inset: 0; background: radial-gradient(ellipse at 50% 42%, transparent 55%, rgba(0,0,0,.55) 100%); }}
svg {{ position: absolute; left: 0; top: 0; }}
.lab {{ position: absolute; font: 86px/1 'Bangers'; letter-spacing: 2px; color: #111; }}
.band {{ position: absolute; left: 0; right: 0; bottom: 0; height: 190px; background: linear-gradient(transparent, rgba(8,8,16,.85)); }}
.t .b {{ position: absolute; left: 0; top: 0; color: transparent; }}
.t .f {{ position: relative; }}
.t {{ position: absolute; left: 50%; bottom: 26px; transform: translateX(-50%) rotate(-3deg); white-space: nowrap;
      font: {main_size}px/1 'Lucky'; color: #ffe11a; }}
.t .b {{ -webkit-text-stroke: 26px #000; text-shadow: 0 10px 0 #000; }}
.t .w {{ color: #fff; }}
.small {{ position: absolute; left: 948px; top: 384px; transform: rotate(-8deg); font: 46px/1 'Bangers'; color: #fff; letter-spacing: 1px; }}
.small .b {{ position: absolute; left: 0; top: 0; color: transparent; -webkit-text-stroke: 10px #000; }}
.small .f {{ position: relative; }}
</style>
<div class="r"></div><div class="l"></div><div class="vig"></div>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{svg_marks()}</svg>
<div class="band"></div>
<svg width="{W}" height="{H}" viewBox="0 0 {W} {H}">{tape(292, -6, 222, 104, -3)}{tape(842, -6, 214, 104, 3)}</svg>
<div class="lab" style="left:322px;top:14px;transform:rotate(-3deg)">GTA 5</div>
<div class="lab" style="left:868px;top:14px;transform:rotate(3deg)">GTA 6</div>
{f'<div class="small"><span class="b">{small}</span><span class="f">{small}</span></div>' if small else ''}
<div class="t"><span class="b">{main_html}</span><span class="f">{main_html}</span></div>'''


variants = {
    "thumb_nerfed": ('<span class="w">GTA 6 GOT</span> NERFED?!', 104, None),
    "thumb_boom": ('WHERE\'S THE <span class="w">BOOM</span>?!', 108, None),
}
for name, (main, size, small) in variants.items():
    f = HERE / f"{name}.html"
    f.write_text(page(main, size, small))
    subprocess.run(["node", RENDER, str(f), str(HERE / f"{name}.png"), str(W), str(H)], check=True)
    print(HERE / f"{name}.png")
