#!/usr/bin/env python3
"""Cover (1080x1920) for comparison footage: two panels side by side from the left and right halves of one
source frame, big labels at the bottom, a VS badge and a hook at the top. Everything that matters sits in the
3:4 zone y 240..1680 that the TikTok profile grid shows.

    python3 shorts/make_split_cover.py shorts/jobs/cover_fit.json

Job keys: src, t, out, crop_l and crop_r ([x, y, w, h] in source pixels; w/h close to 536/1400),
delogo ([[x, y, w, h], ...] baked labels to paint out before cropping),
labels (two strings, emoji allowed), colors (two CSS colours), hook ("[word]" gets yellow), vs (badge text).
"""
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FONTS = HERE / "fonts"
W, H = 1080, 1920
PY, PH, PW = 250, 1400, 536


def frame(src, t, crop, size, out, extra="", pre=""):
    x, y, w, h = crop
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-vf",
                    f"{pre}crop={w}:{h}:{x}:{y},scale={size[0]}:{size[1]}:flags=lanczos,"
                    f"eq=contrast=1.06:saturation=1.18,unsharp=7:7:0.9:5:5:0{extra}", str(out)], check=True)


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    out = Path(job["out"])
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        pre = "".join(f"delogo=x={x}:y={y}:w={w}:h={h}," for x, y, w, h in job.get("delogo", []))
        frame(job["src"], job["t"], job["crop_l"], (PW, PH), td / "l.png", pre=pre)
        frame(job["src"], job["t"], job["crop_r"], (PW, PH), td / "r.png", pre=pre)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(job["t"]), "-i", job["src"], "-frames:v", "1", "-vf",
                        "scale=270:480:force_original_aspect_ratio=increase,crop=270:480,gblur=sigma=14,"
                        "eq=brightness=-0.12:saturation=0.9,scale=1080:1920", str(td / "bg.png")], check=True)
        hook = html.escape(job["hook"].upper())
        hook = re.sub(r"\[(.+?)\]", r'<span class="y">\1</span>', hook)
        la, lb = (html.escape(s) for s in job["labels"])
        ca, cb = job.get("colors", ["#e0262f", "#19b14c"])
        faces = "".join(f"@font-face{{font-family:'{n}';src:url(file://{FONTS}/{f});}}" for n, f in (
            ("Anton", "Anton-Regular.ttf"), ("Bangers", "Bangers-Regular.ttf"), ("Luckiest Guy", "LuckiestGuy-Regular.ttf")))
        page = f'''<!doctype html><meta charset="utf-8"><style>{faces}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#0b0b10}}
.bg{{position:absolute;inset:0;background:url(file://{td}/bg.png)}}
.frame{{position:absolute;left:0;top:{PY - 10}px;width:{W}px;height:{PH + 20}px;background:#0b0b10;
        box-shadow:0 0 40px rgba(0,0,0,.8)}}
.p{{position:absolute;top:{PY}px;width:{PW}px;height:{PH}px;background-size:cover}}
.l{{left:0;background-image:url(file://{td}/l.png)}} .r{{left:{W - PW}px;background-image:url(file://{td}/r.png)}}
.shade{{position:absolute;left:0;width:{W}px}}
.top{{top:{PY}px;height:380px;background:linear-gradient(rgba(0,0,0,.55),transparent)}}
.bot{{top:{PY + PH - 360}px;height:360px;background:linear-gradient(transparent,rgba(0,0,0,.6))}}
.o{{position:relative;display:inline-block}} .o .b{{position:absolute;left:0;top:0;color:transparent}} .o .f{{position:relative}}
.hook{{position:absolute;left:0;right:0;top:{PY + 40}px;text-align:center;font:104px/1.02 'Anton','Noto Color Emoji';
       letter-spacing:1px;color:#fff}}
.hook .b{{-webkit-text-stroke:18px #000;text-shadow:0 8px 0 #000}} .hook .y{{color:#FFE600}}
.lab{{position:absolute;top:{PY + PH - 170}px;font:150px/1 'Bangers','Noto Color Emoji';letter-spacing:4px;color:#fff;
      padding:8px 34px 0;border-radius:18px;box-shadow:0 12px 0 rgba(0,0,0,.55);border:7px solid #000}}
.lab .b{{-webkit-text-stroke:16px #000}}
.la{{left:30px;background:{ca};transform:rotate(-4deg)}} .lb{{right:30px;background:{cb};transform:rotate(4deg)}}
.vs{{position:absolute;left:{W // 2 - 92}px;top:{job.get("vs_y", 560)}px;width:184px;height:184px;border-radius:50%;
     background:#FFE600;border:9px solid #000;box-shadow:0 10px 0 rgba(0,0,0,.6);display:flex;align-items:center;
     justify-content:center;font:110px/1 'Luckiest Guy';color:#000;transform:rotate(-8deg)}}
</style>
<div class="bg"></div><div class="frame"></div><div class="p l"></div><div class="p r"></div>
<div class="shade top"></div><div class="shade bot"></div>
<div class="hook"><span class="o"><span class="b">{hook}</span><span class="f">{hook}</span></span></div>
<div class="vs">{html.escape(job.get("vs", "VS"))}</div>
<div class="lab la"><span class="o"><span class="b">{la}</span><span class="f">{la}</span></span></div>
<div class="lab lb"><span class="o"><span class="b">{lb}</span><span class="f">{lb}</span></span></div>'''
        (td / "cover.html").write_text(page)
        subprocess.run(["node", HERE / "brand" / "render_html.js", td / "cover.html", out, str(W), str(H)], check=True)
    print(out)


if __name__ == "__main__":
    for j in sys.argv[1:]:
        build(j)
