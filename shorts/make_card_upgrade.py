#!/usr/bin/env python3
"""Vertical "card upgrade" short (1080x1920): each player's current card flips into an upgraded one, the rating
rolls up, stat gains pop, a big +N stamp lands. Cards are our own design (not EA's art), faces come from club
portraits cut out with shorts/cutout.py. Music and effects are synthesized (meme_kit), nothing to get claimed.

    python3 shorts/make_card_upgrade.py shorts/jobs/hull_upgrade.json

Job keys: out, work, header [line1, line2], hook_sub, outro, music (meme_kit bed), fps,
players: [{name, photo (rgba png), flag (emoji), pos, gk (bool), old {ovr, stats[6]}, new {ovr, stats[6]},
           size: small | big | hero, reasons: [{text, after (bool)}]}]   "[word]" in a reason is highlighted.
Order the players from the smallest upgrade to the biggest: the last one is the payoff the hook promises.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import meme_kit as MK  # noqa: E402

W, H = 1080, 1920
SR = MK.SR
TIMING = {"small": (3.3, 1.45), "big": (4.7, 2.3), "hero": (5.9, 3.0)}   # segment length, reveal time
HOOK_END = 0.9
OUTRO = 4.2


def o(text):
    """Text with a thick outline that stays outside the letters."""
    return f'<span class="o"><span class="b">{text}</span><span class="f">{text}</span></span>'


def hl(text):
    return re.sub(r"\[(.+?)\]", r'<span class="hl">\1</span>', html.escape(text))


def card(p, side):
    c = p[side]
    labels = ["DIV", "HAN", "KIC", "REF", "SPD", "POS"] if p.get("gk") else ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
    stats = "".join(f'<div class="st"><b>{v}</b><span>{lab}</span><i>+{p["new"]["stats"][k] - p["old"]["stats"][k]}</i></div>'
                    for k, (v, lab) in enumerate(zip(c["stats"], labels)))
    style = "gold" if side == "old" else "up"
    ribbon = '<div class="ribbon">FAN UPGRADE</div>' if side == "new" else ""
    return f'''<div class="card {style}"><div class="cin"><div class="pat"></div>
<img class="face" src="file://{p["photo"]}"><div class="ovr">{c["ovr"]}</div><div class="pos">{p["pos"]}</div>
<div class="flag">{p["flag"]}</div><div class="nm">{html.escape(p["name"])}</div><div class="sep"></div>
<div class="stats">{stats}</div>{ribbon}</div></div>'''


def timeline(job):
    segs, t = [], HOOK_END + 0.3        # the first card comes in once the title has moved up
    for p in job["players"]:
        dur, rv = TIMING[p.get("size", "small")]
        lines, k = [], 0
        for r in p.get("reasons", []):
            at = rv + 0.55 if r.get("after") else 0.2 + 0.85 * k
            k += 0 if r.get("after") else 1
            lines.append({"at": round(at, 3)})
        segs.append({"start": round(t, 3), "dur": dur, "rv": rv, "lines": lines})
        t += dur
    return segs, {"start": round(t, 3), "dur": OUTRO}


def page(job, segs, outro):
    fonts = HERE / "fonts"
    slots = "".join(f'''<div class="slot" id="slot{i}"><div class="side front">{card(p, "old")}</div>
<div class="side back">{card(p, "new")}</div><div class="badge">{o("+" + str(p["new"]["ovr"] - p["old"]["ovr"]))}</div></div>'''
                    for i, p in enumerate(job["players"]))
    reasons = "".join(f'<div class="rs" id="rs{i}">' + "".join(f'<div class="rl">{hl(r["text"])}</div>' for r in p.get("reasons", []))
                      + "</div>" for i, p in enumerate(job["players"]))
    data = {"segs": segs, "outro": outro, "hookEnd": HOOK_END,
            "players": [{"old": p["old"], "new": p["new"]} for p in job["players"]]}
    h1, h2 = (html.escape(x) for x in job["header"])
    return f'''<!doctype html><meta charset="utf-8"><style>
@font-face{{font-family:Anton;src:url(file://{fonts}/Anton-Regular.ttf)}}
@font-face{{font-family:MontX;src:url(file:///usr/share/fonts/opentype/montserrat/Montserrat-ExtraBold.otf)}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:#050505}}
#bg{{position:absolute;inset:0;background:radial-gradient(circle at 50% 44%,#4a2a06 0%,#170c02 42%,#050505 100%)}}
#stripes{{position:absolute;inset:-200px;background:repeating-linear-gradient(115deg,rgba(255,150,30,.07) 0 46px,transparent 46px 140px)}}
#rays{{position:absolute;left:540px;top:860px;width:2400px;height:2400px;margin:-1200px;border-radius:50%;
  background:repeating-conic-gradient(rgba(255,175,50,.13) 0deg 5deg,transparent 5deg 15deg);
  -webkit-mask-image:radial-gradient(circle,#000 0%,rgba(0,0,0,.6) 30%,transparent 62%)}}
#glow{{position:absolute;left:540px;top:860px;width:1300px;height:1300px;margin:-650px;border-radius:50%;
  background:radial-gradient(circle,rgba(255,160,30,.55),rgba(255,120,0,.15) 40%,transparent 68%)}}
.o{{position:relative;display:inline-block}} .o .b{{position:absolute;left:0;top:0;color:transparent}} .o .f{{position:relative}}
.slot{{position:absolute;left:240px;top:430px;width:600px;height:860px;display:none}}
.side{{position:absolute;inset:0}}
.card{{position:absolute;inset:0;clip-path:polygon(12% 0,88% 0,100% 7%,100% 90%,50% 100%,0 90%,0 7%)}}
.cin{{position:absolute;inset:11px;clip-path:polygon(12% 0,88% 0,100% 7%,100% 90%,50% 100%,0 90%,0 7%);overflow:hidden}}
.card.gold{{background:linear-gradient(165deg,#a87b22,#f6dc8c 40%,#9a6c18)}}
.card.gold .cin{{background:linear-gradient(165deg,#fff4c6 0%,#f0d07a 34%,#d1a43f 66%,#f5da8a 100%);color:#3a2805}}
.card.up{{background:linear-gradient(165deg,#ffd27a,#ff8a00 45%,#ffbd45)}}
.card.up .cin{{background:radial-gradient(circle at 60% 18%,#3b2406 0%,#140c03 45%,#070707 100%);color:#fff}}
.pat{{position:absolute;inset:0}}
.gold .pat{{background:repeating-linear-gradient(120deg,rgba(255,255,255,.22) 0 16px,transparent 16px 62px)}}
.up .pat{{background:repeating-linear-gradient(115deg,rgba(255,140,0,.20) 0 22px,transparent 22px 66px)}}
.face{{position:absolute;left:118px;top:34px;height:440px;-webkit-mask-image:linear-gradient(#000 70%,transparent 99%)}}
.ovr{{position:absolute;left:44px;top:52px;font:150px/.9 Anton;letter-spacing:-2px}}
.pos{{position:absolute;left:50px;top:198px;font:56px/1 Anton}}
.flag{{position:absolute;left:46px;top:268px;font:62px/1 'Noto Color Emoji'}}
.up .ovr{{color:#ffb22e;text-shadow:0 0 30px rgba(255,160,30,.55)}}
.nm{{position:absolute;left:20px;right:20px;top:476px;text-align:center;font:76px/1 Anton;letter-spacing:1px;white-space:nowrap}}
.sep{{position:absolute;left:96px;right:96px;top:566px;height:3px;background:currentColor;opacity:.3}}
.up .sep{{background:#ffb22e;opacity:.8}}
.stats{{position:absolute;left:60px;right:60px;top:584px;display:grid;grid-template-columns:1fr 1fr;grid-auto-flow:column;
  grid-template-rows:repeat(3,52px);column-gap:30px}}
.st{{display:flex;align-items:baseline;justify-content:center;gap:12px;position:relative}}
.st b{{font:52px/1 Anton;width:66px;text-align:right}} .st span{{font:30px/1 MontX;width:66px;opacity:.85}}
.up .st span{{color:#ffb22e;opacity:1}}
.st i{{position:absolute;right:-10px;top:-8px;font:31px/1 MontX;font-style:normal;color:#3cff7a;opacity:0}}
.gold .st i{{display:none}}
.ribbon{{position:absolute;left:0;right:0;bottom:46px;text-align:center;font:22px/1 MontX;letter-spacing:7px;color:#ffb22e}}
.badge{{position:absolute;left:400px;top:-70px;font:150px/1 Anton;color:#3cff7a;opacity:0}}
.badge .b{{-webkit-text-stroke:18px #000}}
#ring{{position:absolute;left:540px;top:860px;width:700px;height:700px;margin:-350px;border-radius:50%;
  border:16px solid #ffb22e;opacity:0}}
#flash{{position:absolute;inset:0;background:#fff;opacity:0}}
.rs{{position:absolute;left:50px;right:50px;top:1330px;text-align:center;display:none}}
.rl{{font:52px/1.18 MontX;color:#fff;margin-bottom:16px;opacity:0;text-wrap:balance;
  text-shadow:0 4px 0 #000,0 0 22px rgba(0,0,0,.9),2px 2px 0 #000,-2px -2px 0 #000}}
.hl{{color:#ffb22e}}
#title{{position:absolute;left:540px;top:760px;text-align:center;white-space:nowrap}}
#title .t1{{font:118px/1 Anton;color:#ffa51f;letter-spacing:3px}} #title .t2{{font:150px/1 Anton;color:#fff}}
#title .t3{{font:46px/1.2 MontX;color:#fff;margin-top:22px;text-shadow:0 4px 0 #000}}
#title .b{{-webkit-text-stroke:16px #000}}
#outro{{position:absolute;left:0;right:0;top:1395px;text-align:center;font:100px/1 Anton;color:#fff;opacity:0}}
#outro .b{{-webkit-text-stroke:16px #000}}
</style>
<div id="bg"></div><div id="stripes"></div><div id="rays"></div><div id="glow"></div>
{slots}<div id="ring"></div>{reasons}
<div id="title"><div class="t1">{o(h1)}</div><div class="t2">{o(h2)}</div><div class="t3">{html.escape(job["hook_sub"])}</div></div>
<div id="outro">{o(html.escape(job["outro"]))}</div><div id="flash"></div>
<script>
const D = {json.dumps(data, ensure_ascii=False)};
const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const cl = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const out3 = (x) => 1 - Math.pow(1 - cl(x), 3), in3 = (x) => Math.pow(cl(x), 3);
const io3 = (x) => (x = cl(x), x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const back = (x) => (x = cl(x), 1 + 2.70158 * Math.pow(x - 1, 3) + 1.70158 * Math.pow(x - 1, 2));
const slots = D.players.map((_, i) => $('#slot' + i)), rs = D.players.map((_, i) => $('#rs' + i));
// names shrink until they fit their card (measured while every card is shown, hidden ones have no width)
slots.forEach((el) => {{ el.style.display = 'block'; $$('.side', el).forEach((x) => (x.style.display = 'block')); }});
$$('.nm').forEach((n) => {{ let s = 76; while (n.scrollWidth > n.clientWidth && s > 30) {{ s -= 2; n.style.fontSize = s + 'px'; }} }});
slots.forEach((el) => (el.style.display = 'none'));
const GRID = D.players.map((_, i) => [(i % 4 - 1.5) * 255, (Math.floor(i / 4) - 0.5) * 370 - 60]);

function cardAt(i, u, s) {{
  const el = slots[i], p = D.players[i], front = $('.front', el), backS = $('.back', el), badge = $('.badge', el);
  const f = io3((u - s.rv) / 0.34);                    // flip progress
  const ang = f * 180;
  front.style.display = ang < 90 ? 'block' : 'none';
  backS.style.display = ang >= 90 ? 'block' : 'none';
  front.style.transform = `perspective(1800px) rotateY(${{ang}}deg)`;
  backS.style.transform = `perspective(1800px) rotateY(${{ang - 180}}deg)`;
  const k = out3((u - s.rv - 0.12) / 0.7);             // numbers roll
  $('.ovr', backS).textContent = Math.round(p.old.ovr + (p.new.ovr - p.old.ovr) * k);
  $$('.st', backS).forEach((st, j) => {{
    const d = p.new.stats[j] - p.old.stats[j];
    $('b', st).textContent = Math.round(p.old.stats[j] + d * k);
    const c = back((u - s.rv - 0.4 - j * 0.06) / 0.25), chip = $('i', st);
    chip.style.opacity = d > 0 && u > s.rv + 0.4 + j * 0.06 ? 1 : 0;
    chip.style.transform = `scale(${{c}})`;
  }});
  const g = u >= s.rv ? Math.exp(-(u - s.rv) * 1.6) : 0;
  backS.style.filter = `drop-shadow(0 0 ${{20 + 60 * g}}px rgba(255,165,40,${{0.35 + 0.6 * g}})) drop-shadow(0 30px 30px rgba(0,0,0,.6))`;
  front.style.filter = 'drop-shadow(0 30px 30px rgba(0,0,0,.6))';
  const b = back((u - s.rv - 0.45) / 0.28);
  badge.style.opacity = u > s.rv + 0.45 ? 1 : 0;
  badge.style.transform = `rotate(-11deg) scale(${{b}})`;
}}

window.render = function (t) {{
  $('#stripes').style.transform = `translateX(${{(t * 26) % 186}}px)`;
  let pulse = 0, flash = 0, ring = -1;
  // title: slams in, then becomes the header
  const ti = $('#title'), m = io3((t - D.hookEnd) / 0.4);
  const slam = back(t / 0.28);
  ti.style.top = (760 - 510 * m) + 'px';  // header ends below TikTok's top bar
  ti.style.transform = `translate(-50%,-50%) scale(${{(1 - 0.48 * m) * (t < 0.28 ? 0.6 + 0.4 * slam : 1)}})`;
  ti.style.opacity = cl(t / 0.12);
  $('.t3', ti).style.opacity = 1 - cl((t - D.hookEnd) / 0.25);
  const outT = t - D.outro.start;
  D.segs.forEach((s, i) => {{
    const el = slots[i], u = t - s.start;
    if (outT >= 0) {{                                   // outro: every upgraded card in a grid
      const pop = back((outT - i * 0.08) / 0.32);
      el.style.display = outT >= i * 0.08 ? 'block' : 'none';
      el.style.transform = `translate(${{GRID[i][0]}}px,${{GRID[i][1]}}px) scale(${{0.4 * pop}})`;
      cardAt(i, s.dur, s);
      $('.badge', el).style.opacity = 0;
      rs[i].style.display = 'none';
      return;
    }}
    if (u < 0 || u >= s.dur) {{ el.style.display = 'none'; rs[i].style.display = 'none'; return; }}
    el.style.display = 'block';
    const e = out3(u / 0.32), x = in3((u - (s.dur - 0.28)) / 0.28);
    let dx = (1 - e) * 760 - x * 820, rot = (1 - e) * 10 - x * 10;
    let sc = 1 + 0.015 * Math.sin(u * 2.2), dy = Math.sin(u * 1.7) * 6;
    if (u > s.rv - 0.75 && u < s.rv) {{                  // tension before the flip
      const a = (u - (s.rv - 0.75)) / 0.75;
      dx += Math.sin(u * 95) * 7 * a; dy += Math.cos(u * 83) * 5 * a; sc += 0.03 * a;
    }}
    if (u >= s.rv) sc += 0.12 * Math.sin(Math.PI * cl((u - s.rv) / 0.34));
    el.style.transform = `translate(${{dx}}px,${{dy}}px) rotate(${{rot}}deg) scale(${{sc}})`;
    cardAt(i, u, s);
    if (u >= s.rv) {{ flash = Math.max(flash, 0.85 * (1 - (u - s.rv) / 0.22)); ring = u - s.rv; }}
    pulse = Math.max(pulse, u >= s.rv ? Math.exp(-(u - s.rv) * 1.4) : 0);
    rs[i].style.display = 'block';
    $$('.rl', rs[i]).forEach((l, j) => {{
      const a = out3((u - s.lines[j].at) / 0.3), z = 1 - cl((u - (s.dur - 0.3)) / 0.25);
      l.style.opacity = a * z;
      l.style.transform = `translateY(${{(1 - a) * 30}}px)`;
    }});
  }});
  $('#flash').style.opacity = cl(flash);
  const rg = $('#ring');
  if (ring >= 0 && ring < 0.6) {{ rg.style.opacity = 0.9 * (1 - ring / 0.6); rg.style.transform = `scale(${{0.4 + ring * 3}})`; }}
  else rg.style.opacity = 0;
  $('#rays').style.transform = `rotate(${{t * 9}}deg) scale(${{1 + 0.15 * pulse}})`;
  $('#rays').style.opacity = 0.55 + 0.45 * pulse;
  $('#glow').style.opacity = 0.35 + 0.65 * pulse;
  const oo = out3((outT - 0.6) / 0.35);
  $('#outro').style.opacity = outT >= 0 ? oo : 0;
  $('#outro').style.transform = `scale(${{0.8 + 0.2 * back((outT - 0.6) / 0.35)}})`;
}};
</script>'''


def audio(job, segs, outro, total, path):
    n = int((total + 0.5) * SR)
    mix = np.zeros((n, 2))
    bed = MK.music(job.get("music", "phonk"), total + 0.5)[:n]
    gain = np.full(n, 0.55)
    hero = [s for s, p in zip(segs, job["players"]) if p.get("size") == "hero"]
    for s in hero:                                     # the music drops out under the last riser
        a, b = int((s["start"] + s["rv"] - 0.9) * SR), int((s["start"] + s["rv"]) * SR)
        gain[a:b] = np.linspace(0.55, 0.12, b - a)
    gain[-int(1.2 * SR):] *= np.linspace(1, 0, int(1.2 * SR))
    mix[: len(bed)] += bed * gain[: len(bed), None]

    def put(name, t, g=1.0, **kw):
        x = MK.sfx(name, **kw)
        i = int(t * SR)
        j = min(n, i + len(x))
        if i < n:
            mix[i:j] += x[: j - i] * g

    put("vine_boom", 0.0, 0.7)
    for k, (s, p) in enumerate(zip(segs, job["players"])):
        put("whoosh", s["start"] - 0.05, 0.5)
        put("riser", s["start"] + s["rv"] - 0.9, 0.35, d=0.9)
        put("vine_boom", s["start"] + s["rv"], 0.85)
        for j in range(6):
            put("pop", s["start"] + s["rv"] + 0.14 + j * 0.1, 0.18)
        put("ding", s["start"] + s["rv"] + 0.45, 0.45)
        if p.get("size") == "hero":
            put("airhorn", s["start"] + s["rv"] + 0.05, 0.45)
    put("whoosh", outro["start"] - 0.05, 0.5)
    for i in range(len(segs)):
        put("pop", outro["start"] + i * 0.08, 0.3)
    peak = np.abs(mix).max()
    sf.write(path, mix / peak * 0.89, SR)


def build(job_path):
    job = json.loads(Path(job_path).read_text())
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    fps = job.get("fps", 30)
    segs, outro = timeline(job)
    total = outro["start"] + outro["dur"]
    (work / "page.html").write_text(page(job, segs, outro))
    audio(job, segs, outro, total, work / "audio.wav")
    subprocess.run(["node", HERE / "render_frames.js", work / "page.html", work / "video.mp4", str(fps), f"{total:.3f}",
                    str(W), str(H)], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", work / "video.mp4", "-i", work / "audio.wav", "-map", "0:v",
                    "-map", "1:a", "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
                    "-ar", "48000", "-shortest", "-movflags", "+faststart", job["out"]], check=True)
    print(job["out"], f"{total:.1f}s")


STILLS_JS = """const { chromium } = require('playwright');
(async () => {
  const [, , page, dir, ...ts] = process.argv;
  const b = await chromium.launch(), p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  await p.goto('file://' + page);
  await p.evaluate(async () => { await document.fonts.ready; });
  for (const t of ts) { await p.evaluate((x) => window.render(x), +t); await p.screenshot({ path: `${dir}/still_${t}.png` }); }
  await b.close();
})();"""


def stills(job_path, times):
    """Frames at chosen times, to check the layout before a full render."""
    job = json.loads(Path(job_path).read_text())
    work = Path(job["work"])
    work.mkdir(parents=True, exist_ok=True)
    segs, outro = timeline(job)
    (work / "page.html").write_text(page(job, segs, outro))
    (work / "stills.js").write_text(STILLS_JS)
    subprocess.run(["node", work / "stills.js", work / "page.html", work, *times], check=True, cwd=HERE)
    print("segments:", [(round(s["start"], 2), round(s["start"] + s["rv"], 2)) for s in segs], "outro", outro["start"])


if __name__ == "__main__":
    if "--stills" in sys.argv:
        i = sys.argv.index("--stills")
        stills(sys.argv[1], sys.argv[i + 1].split(","))
    else:
        for j in sys.argv[1:]:
            build(j)
