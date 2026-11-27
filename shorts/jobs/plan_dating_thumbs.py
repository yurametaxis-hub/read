#!/usr/bin/env python3
"""Thumbnails for the dating essay (make_thumb.py jobs). usage: plan_dating_thumbs.py UPLOADS SCRATCHPAD

A: two tilted screenshots, GTA VI 2026 under "GTA 6" and San Andreas 2004 under "THIS?", an equals badge
and a marker arrow pointing at San Andreas.
B: one big San Andreas bar scene with a small GTA VI card between CJ and Denise.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
U, S = sys.argv[1], sys.argv[2]
SA = f"{U}/87fd1aa7-13.mkv"   # Stilefty, CJ and Denise at the bar
VI = f"{U}/25604d3b-6.mkv"    # Jason and Lucia holding hands on the beach

CHIP = """.chip{position:absolute;font:92px/1 'Bangers';letter-spacing:3px;color:#fff;padding:8px 22px 0;
  border:6px solid #000;border-radius:14px;box-shadow:0 8px 0 rgba(0,0,0,.6)}
.chip .b{-webkit-text-stroke:14px #000}"""

a = {
    "out": f"{S}/dating/out/thumb_dating_a.png",
    "frames": {
        "bg": {"src": VI, "t": 128.0, "crop": [0, 0, 640, 360], "w": 1280, "h": 720,
               "grade": "gblur=sigma=16,eq=brightness=-0.18:saturation=1.1"},
        "sa": {"src": SA, "t": 13.5, "crop": [14, 0, 480, 352], "w": 600, "h": 440},
        "vi": {"src": VI, "t": 128.0, "crop": [140, 48, 422, 310], "w": 600, "h": 440},
    },
    "css": CHIP + """
.bg{position:absolute;inset:0;background:url(@bg) center/cover}
.dim{position:absolute;inset:0;background:radial-gradient(ellipse at 50% 62%,rgba(0,0,0,.1),rgba(0,0,0,.7))}
.hook{position:absolute;left:0;right:0;top:6px;text-align:center;font:132px/1 'Anton';color:#fff;letter-spacing:1px;
  transform:rotate(-1.5deg)}
.hook .b{-webkit-text-stroke:20px #000;text-shadow:0 9px 0 #000} .y{color:#FFE600}
.card{position:absolute;width:600px;height:440px;border:8px solid #fff;box-shadow:0 16px 34px rgba(0,0,0,.75);
  background-size:cover}
.c1{left:22px;top:216px;background-image:url(@vi);transform:rotate(-3deg)}
.c2{left:650px;top:200px;background-image:url(@sa);transform:rotate(3deg)}
.k1{left:34px;top:598px;background:#e6197a;transform:rotate(-6deg)}
.k2{left:676px;top:586px;background:#e8731a;transform:rotate(5deg)}
svg{position:absolute;left:0;top:0}
.eq{position:absolute;left:566px;top:356px;width:148px;height:148px;border-radius:50%;background:#FFE600;
  border:8px solid #000;box-shadow:0 10px 0 rgba(0,0,0,.6);transform:rotate(-8deg);box-sizing:border-box}
.eq i{position:absolute;left:30px;width:72px;height:20px;background:#000;border-radius:4px}""",
    "html": """<div class="bg"></div><div class="dim"></div>
<div class="card c1"></div><div class="card c2"></div>
<div class="chip k1"><o>2026</o></div><div class="chip k2"><o>2004</o></div>
<svg width="1280" height="720" fill="none" stroke-linecap="round" stroke-linejoin="round">
 <g stroke="#000" stroke-width="22"><path d="M1012,136 C1034,182 1004,228 965,256"/><path d="M1002,252 L965,256 L974,220"/></g>
 <g stroke="#ff2b2b" stroke-width="12"><path d="M1012,136 C1034,182 1004,228 965,256"/><path d="M1002,252 L965,256 L974,220"/></g>
</svg>
<div class="eq"><i style="top:42px"></i><i style="top:78px"></i></div>
<div class="hook"><o>GTA 6 <span class="y">COPIED</span> THIS?</o></div>""",
}

b = {
    "out": f"{S}/dating/out/thumb_dating_b.png",
    "frames": {
        "sa": {"src": SA, "t": 13.5, "crop": [0, 0, 560, 315], "w": 1280, "h": 720},
        "vi": {"src": VI, "t": 128.0, "crop": [150, 60, 400, 260], "w": 380, "h": 247},
    },
    "css": CHIP + """
.full{position:absolute;inset:0;background:url(@sa) center/cover}
.shade{position:absolute;left:0;right:0;bottom:0;height:360px;background:linear-gradient(transparent,rgba(0,0,0,.8))}
.inset{position:absolute;left:446px;top:30px;width:380px;height:247px;border:7px solid #fff;background:url(@vi) center/cover;
  transform:rotate(5deg);box-shadow:0 14px 30px rgba(0,0,0,.75)}
.k2{left:690px;top:226px;font-size:64px;background:#e6197a;transform:rotate(7deg)}
.k1{left:1010px;top:318px;background:#e8731a;transform:rotate(-7deg)}
.txt{position:absolute;left:30px;bottom:22px;font:134px/.9 'Anton';color:#fff;transform:rotate(-2deg);
  transform-origin:left bottom}
.txt .b{-webkit-text-stroke:20px #000;text-shadow:0 9px 0 #000} .y{color:#FFE600}""",
    "html": """<div class="full"></div><div class="shade"></div>
<div class="inset"></div><div class="chip k2"><o>GTA 6</o></div>
<div class="chip k1"><o>2004</o></div>
<div class="txt"><o><span class="y">SAN ANDREAS</span><br>DID IT FIRST</o></div>""",
}

for name, job in (("a", a), ("b", b)):
    (HERE / f"thumb_dating_{name}.json").write_text(json.dumps(job, indent=1))
print("ok")
