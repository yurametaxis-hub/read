"""Channel art in a Vice City sunset style: avatar with monogram, avatar without text, YouTube banner.

    python3 shorts/brand/gen.py LEONIDA Daily LD    (writes PNGs next to this file)
"""
import math
import random
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAME = sys.argv[1] if len(sys.argv) > 1 else "LEONIDA"
NAME2 = sys.argv[2] if len(sys.argv) > 2 else "Daily"
MONO = sys.argv[3] if len(sys.argv) > 3 else "LD"
TAGLINE = "GTA 6 CLIPS · STREAMER REACTIONS · EVERY DAY"

INK = "#12052b"


def bez(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * p0[k] + 2 * (1 - t) * t * p1[k] + t * t * p2[k] for k in (0, 1))


def bez_d(p0, p1, p2, t):
    return tuple(2 * (1 - t) * (p1[k] - p0[k]) + 2 * t * (p2[k] - p1[k]) for k in (0, 1))


def ribbon(p0, p1, p2, width, n=60):
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        x, y = bez(p0, p1, p2, t)
        dx, dy = bez_d(p0, p1, p2, t)
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln
        w = width(t, i)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    pts = left + right[::-1]
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def palm(base, height, lean, seed=1, fronds=11, fill=INK):
    rnd = random.Random(seed)
    bx, by = base
    crown = (bx + lean, by - height)
    ctrl = (bx + lean * 0.12, by - height * 0.55)
    w0, w1 = height * 0.05, height * 0.022
    parts = [ribbon((bx, by), ctrl, crown, lambda t, i: (w0 * (1 - t) + w1 * t) / 2 * (1 + 0.1 * (i % 2)), 80)]
    for k in range(fronds):
        a = math.radians(150 + k * (240 / (fronds - 1)) + rnd.uniform(-8, 8))
        lf = height * rnd.uniform(0.36, 0.48)
        d = (math.cos(a), math.sin(a))
        droop = lf * (0.22 + 0.42 * abs(d[0]))
        end = (crown[0] + d[0] * lf, crown[1] + d[1] * lf + droop)
        c = (crown[0] + d[0] * lf * 0.55, crown[1] + d[1] * lf * 0.55 - lf * 0.14)

        def width(t, i, lf=lf):
            base_w = lf * 0.09 * math.sin(math.pi * min(t, 0.999) ** 0.75)
            return base_w * (1.0 if i % 2 == 0 or t < 0.1 else 0.3)
        parts.append(ribbon(crown, c, end, width, 64))
    nuts = "".join(f'<circle cx="{crown[0] + dx:.1f}" cy="{crown[1] + dy:.1f}" r="{height * 0.022:.1f}"/>'
                   for dx, dy in ((-height * 0.025, height * 0.03), (height * 0.02, height * 0.035), (0, height * 0.055)))
    return f'<g fill="{fill}">' + "".join(f'<path d="{p}"/>' for p in parts) + nuts + "</g>"


def sun(cx, cy, r, uid, stripes=7):
    rects = "".join(
        f'<rect x="{cx - r - 5}" y="{cy + r * (0.04 + j * 0.15):.1f}" width="{2 * r + 10}" height="{r * (0.018 + j * 0.017):.1f}" fill="black"/>'
        for j in range(stripes))
    return f'''
    <defs>
      <linearGradient id="sg{uid}" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#ffe86b"/><stop offset=".5" stop-color="#ff9a3c"/><stop offset="1" stop-color="#ff2e88"/>
      </linearGradient>
      <mask id="sm{uid}"><rect x="0" y="0" width="100%" height="100%" fill="white"/>{rects}</mask>
      <filter id="glow{uid}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="{r * 0.18:.0f}"/></filter>
    </defs>
    <circle cx="{cx}" cy="{cy}" r="{r * 1.08:.0f}" fill="#ff2e88" opacity=".55" filter="url(#glow{uid})"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#sg{uid})" mask="url(#sm{uid})"/>'''


def sky(w, h, uid):
    return f'''<defs><linearGradient id="sky{uid}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#0d0221"/><stop offset=".38" stop-color="#2b0f54"/>
      <stop offset=".66" stop-color="#7a1c72"/><stop offset=".86" stop-color="#e2366f"/></linearGradient></defs>
      <rect width="{w}" height="{h}" fill="url(#sky{uid})"/>'''


def ground(w, h, horizon, vx, uid, lines=14):
    g = [f'<rect x="0" y="{horizon}" width="{w}" height="{h - horizon}" fill="{INK}"/>']
    for j in range(1, lines):
        y = horizon + (h - horizon) * (j / lines) ** 2.2
        g.append(f'<line x1="0" y1="{y:.1f}" x2="{w}" y2="{y:.1f}"/>')
    for k in range(-24, 25):
        g.append(f'<line x1="{vx}" y1="{horizon}" x2="{vx + k * w * 0.09:.1f}" y2="{h}"/>')
    return (f'<g stroke="#ff2e88" stroke-opacity=".7" stroke-width="{max(2, w // 600)}">' + "".join(g)
            + f'</g><line x1="0" y1="{horizon}" x2="{w}" y2="{horizon}" stroke="#ffd1e8" stroke-width="{max(3, w // 400)}"/>')


def page(w, h, svg):
    return f'''<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#000}}
    svg text{{font-family:'Montserrat';font-weight:900}}</style>
    <svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{svg}</svg>'''


def text_glow_defs(uid, blur):
    return (f'<defs><filter id="tg{uid}" x="-20%" y="-40%" width="140%" height="180%">'
            f'<feDropShadow dx="0" dy="0" stdDeviation="{blur}" flood-color="#ff2e88" flood-opacity=".9"/></filter></defs>')


def avatar_mono():
    w = h = 1024
    hz = 690
    s = [sky(w, h, "a"), sun(512, 400, 290, "a"), ground(w, h, hz, 512, "a", 10),
         palm((30, 1010), 760, 60, seed=3, fronds=9), palm((1000, 1020), 700, -70, seed=8, fronds=9),
         text_glow_defs("a", 22),
         f'<text x="512" y="{hz + 10}" text-anchor="middle" font-size="430" font-style="italic" fill="#fff" '
         f'stroke="{INK}" stroke-width="30" paint-order="stroke" stroke-linejoin="round" filter="url(#tga)">{MONO}</text>']
    return page(w, h, "".join(s))


def avatar_symbol():
    w = h = 1024
    hz = 720
    s = [sky(w, h, "b"), sun(512, 470, 330, "b"), ground(w, h, hz, 512, "b", 10),
         palm((330, 1010), 820, 150, seed=5), palm((800, 1030), 560, -60, seed=11, fronds=9)]
    return page(w, h, "".join(s))


def banner():
    w, h = 2560, 1440
    hz = 980
    s = [sky(w, h, "c"), sun(1280, 900, 360, "c"), ground(w, h, hz, 1280, "c", 16),
         palm((380, 1300), 1100, 160, seed=2), palm((150, 1330), 820, 90, seed=7, fronds=9),
         palm((2190, 1300), 1060, -170, seed=4), palm((2420, 1340), 760, -80, seed=9, fronds=9),
         text_glow_defs("c", 18),
         f'<text x="1280" y="700" text-anchor="middle" font-size="190" font-style="italic" fill="#fff" letter-spacing="6" '
         f'stroke="{INK}" stroke-width="22" paint-order="stroke" stroke-linejoin="round" filter="url(#tgc)">{NAME}'
         f'<tspan font-family="Lobster Two" font-weight="700" fill="#2de2e6" font-size="200" dx="30">{NAME2}</tspan></text>',
         f'<rect x="{1280 - 640}" y="760" width="1280" height="96" rx="48" fill="{INK}" fill-opacity=".82"/>',
         f'<text x="1280" y="824" text-anchor="middle" font-size="46" fill="#fff" letter-spacing="5" '
         f'style="font-weight:800">{TAGLINE}</text>']
    return page(w, h, "".join(s))


for name, html, w, h in (("avatar_mono", avatar_mono(), 1024, 1024), ("avatar_symbol", avatar_symbol(), 1024, 1024),
                         ("banner", banner(), 2560, 1440)):
    f = HERE / f"{name}.html"
    f.write_text(html)
    subprocess.run(["node", HERE / "render_html.js", f, HERE / f"{name}.png", str(w), str(h)], check=True)
    print(name)
