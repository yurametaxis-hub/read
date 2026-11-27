#!/usr/bin/env python3
"""16:9 thumbnail (1280x720) from real game frames laid out with HTML.

    python3 shorts/make_thumb.py shorts/jobs/thumb_dating_a.json [more.json ...]

Job keys:
  out      png path
  frames   {"name": {"src": video, "t": seconds, "crop": [x, y, w, h], "w": px, "h": px,
                     "grade": "extra ffmpeg filters", "flip": false}}
           each frame is cut from the source, scaled to w x h and sharpened; the page uses it as @name
  css      page styles (@name works here too); fonts Anton, Bangers, Luckiest Guy, Permanent Marker, Titan One are loaded
  html     page body; @name is replaced with the frame's file url.
           <o>TEXT</o> draws TEXT with a thick outline that does not eat into the letters
           (style it with o .b { -webkit-text-stroke: 16px #000 })
Frames from 360p sources stay soft, so keep faces and text large and let the type carry the thumbnail.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
W, H = 1280, 720
FACES = (("Anton", "Anton-Regular.ttf"), ("Bangers", "Bangers-Regular.ttf"), ("Luckiest Guy", "LuckiestGuy-Regular.ttf"),
         ("Permanent Marker", "PermanentMarker-Regular.ttf"), ("Titan One", "TitanOne-Regular.ttf"))


def cut(fr, out):
    x, y, w, h = fr["crop"]
    vf = [f"crop={w}:{h}:{x}:{y}", f"scale={fr['w']}:{fr['h']}:flags=lanczos",
          "eq=contrast=1.08:saturation=1.22", "unsharp=7:7:1.1:5:5:0"]
    if fr.get("flip"):
        vf.append("hflip")
    if fr.get("grade"):
        vf.append(fr["grade"])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(fr["t"]), "-i", fr["src"], "-frames:v", "1",
                    "-vf", ",".join(vf), str(out)], check=True)


def outline(m):
    t = m.group(1)
    return f'<span class="o"><span class="b">{t}</span><span class="f">{t}</span></span>'


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        body, css = job["html"], job.get("css", "")
        for name in sorted(job["frames"], key=len, reverse=True):  # @sa2 before @sa
            cut(job["frames"][name], td / f"{name}.png")
            body = body.replace(f"@{name}", f"file://{td}/{name}.png")
            css = css.replace(f"@{name}", f"file://{td}/{name}.png")
        body = re.sub(r"<o>(.*?)</o>", outline, body, flags=re.S)
        faces = "".join(f"@font-face{{font-family:'{n}';src:url(file://{FONTS}/{f});}}" for n, f in FACES)
        page = f'''<!doctype html><meta charset="utf-8"><style>{faces}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#111}}
.o{{position:relative;display:inline-block}} .o .b{{position:absolute;left:0;top:0;color:transparent}}
.o .f{{position:relative}}
{css}
</style>{body}'''
        (td / "thumb.html").write_text(page)
        subprocess.run(["node", HERE / "brand" / "render_html.js", td / "thumb.html", out, str(W), str(H)], check=True)
    print(out)


if __name__ == "__main__":
    for j in sys.argv[1:]:
        build(j)
