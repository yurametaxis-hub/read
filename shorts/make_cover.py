#!/usr/bin/env python3
"""Cover image (1080x1920) for a short: frames from the source, huge outlined text, red circles and arrows.

The main picture goes into the 3:4 zone y 240..1680, which is what the TikTok profile grid shows;
the strips above and below are a blurred copy so the full 9:16 cover still looks finished.

    python3 shorts/make_cover.py shorts/jobs/cover_fight.json

Job keys (all coordinates are in the 1080x1920 cover, crops in source pixels):
  out                     PNG path
  panels                  [{"src": video, "t": 71.15, "crop": [x, y, w, h], "dest": [x, y, w, h], "gamma": 1.0}, ...]
  text                    [{"html": "ONE *PUNCH* 💀", "y": 1380, "size": 150, "rotate": -4}]  *word* = yellow,
                          a | in html breaks the line
  circles                 [{"cx": 850, "cy": 680, "r": 200}]
  arrows                  [{"from": [700, 1130], "to": [520, 1260]}]
  tag                     small label at the bottom of the main zone, e.g. "FAN CONCEPT"
"""
import html
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
W, H = 1080, 1920
EMOJI = re.compile(r"([\U0001F300-\U0001FAFF☀-➿]+)")


def frame(src, t, crop, size, out, gamma=1.0):
    x, y, w, h = crop
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf",
                    f"crop={w}:{h}:{x}:{y},scale={size[0]}:{size[1]}:flags=lanczos,"
                    f"unsharp=5:5:0.8:5:5:0,eq=contrast=1.06:saturation=1.2:gamma={gamma}", str(out)], check=True)


def text_html(t, outline):
    s = html.escape(t["html"].upper() if t.get("upper", True) else t["html"])
    s = re.sub(r"\*(.+?)\*", r'<span class="hl">\1</span>', s)
    s = EMOJI.sub(r'<span class="e">\1</span>', s).replace("|", "<br>")
    cls = "txt back" if outline else "txt"
    return (f'<div class="{cls}" style="top:{t["y"]}px;font-size:{t.get("size", 150)}px;'
            f'transform:translate(-50%,-50%) rotate({t.get("rotate", -4)}deg)">{s}</div>')


def arrow_svg(a):
    (x1, y1), (x2, y2) = a["from"], a["to"]
    ang = math.atan2(y2 - y1, x2 - x1)
    hl, hw = 70, 52
    bx, by = x2 - hl * math.cos(ang), y2 - hl * math.sin(ang)
    p1 = (bx + hw * math.sin(ang), by - hw * math.cos(ang))
    p2 = (bx - hw * math.sin(ang), by + hw * math.cos(ang))
    head = f"M{x2},{y2} L{p1[0]:.0f},{p1[1]:.0f} L{p2[0]:.0f},{p2[1]:.0f} Z"
    line = f"M{x1},{y1} L{bx:.0f},{by:.0f}"
    return (f'<path d="{line}" stroke="#fff" stroke-width="40" stroke-linecap="round"/>'
            f'<path d="{head}" fill="#fff" stroke="#fff" stroke-width="16" stroke-linejoin="round"/>'
            f'<path d="{line}" stroke="#ff1f1f" stroke-width="24" stroke-linecap="round"/>'
            f'<path d="{head}" fill="#ff1f1f"/>')


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        imgs = []
        for i, p in enumerate(job["panels"]):
            f = td / f"p{i}.png"
            frame(p["src"], p["t"], p["crop"], p["dest"][2:], f, p.get("gamma", 1.0))
            imgs.append((f, p["dest"]))
        bg = imgs[0][0]
        panels = "".join(f'<img src="file://{f}" style="left:{d[0]}px;top:{d[1]}px;width:{d[2]}px;height:{d[3]}px">'
                         for f, d in imgs)
        svg = "".join(f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" stroke="#fff" stroke-width="30"/>'
                      f'<circle cx="{c["cx"]}" cy="{c["cy"]}" r="{c["r"]}" fill="none" stroke="#ff1f1f" stroke-width="16"/>'
                      for c in job.get("circles", []))
        svg += "".join(arrow_svg(a) for a in job.get("arrows", []))
        texts = "".join(text_html(t, True) + text_html(t, False) for t in job.get("text", []))
        tag = f'<div class="tag">{html.escape(job["tag"])}</div>' if job.get("tag") else ""
        page = f'''<!doctype html><meta charset="utf-8"><style>
          html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #000; }}
          .bg {{ position: absolute; inset: -80px; background: url(file://{bg}) center/cover; filter: blur(36px) brightness(.5); }}
          img {{ position: absolute; object-fit: cover; }}
          .seam {{ position: absolute; left: 0; width: {W}px; height: 6px; background: #000; }}
          svg {{ position: absolute; left: 0; top: 0; }}
          .txt {{ position: absolute; left: 50%; width: 1040px; text-align: center; line-height: 1.02;
                  font-family: 'Montserrat', 'Noto Color Emoji', sans-serif; font-weight: 900; font-style: italic;
                  color: #fff; letter-spacing: -1px; }}
          .back {{ color: transparent; -webkit-text-stroke: 34px #000; filter: drop-shadow(0 10px 18px rgba(0,0,0,.6)); }}
          .back .e {{ visibility: hidden; }}
          .hl {{ color: #ffd400; }}
          .back .hl {{ color: transparent; }}
          .tag {{ position: absolute; left: 50%; top: 1610px; transform: translateX(-50%); padding: 10px 26px;
                  background: rgba(0,0,0,.72); color: #fff; border-radius: 40px; font: 800 34px 'Montserrat';
                  letter-spacing: 4px; white-space: nowrap; }}
        </style>
        <div class="bg"></div>{panels}
        {"".join(f'<div class="seam" style="top:{d[1] - 3}px;left:{d[0]}px;width:{d[2]}px"></div>' for _, d in imgs[1:] if d[1] > 240)}
        {"".join(f'<div class="seam" style="left:{d[0] - 3}px;top:{d[1]}px;width:6px;height:{d[3]}px"></div>' for _, d in imgs[1:] if d[0] > 0)}
        <svg width="{W}" height="{H}" viewBox="0 0 {W} {H}" fill="none">{svg}</svg>{texts}{tag}'''
        page_file = td / "cover.html"
        page_file.write_text(page)
        subprocess.run(["node", HERE / "brand" / "render_html.js", page_file, out, str(W), str(H)], check=True)
    print(out)


if __name__ == "__main__":
    for j in sys.argv[1:]:
        build(j)
