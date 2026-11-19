#!/usr/bin/env python3
"""Script and shot plan for the long video "GTA 5 is better than GTA 6".

Every shot lists candidate moments in order of preference. The allocator reads the narration
lengths from the TTS cache, then gives each shot the first candidate that fits inside one scene
of its source and does not reuse footage already shown (shifting the start by up to 3 s if needed).
Writes longform_gta5_better.json next to this file.

    python3 shorts/jobs/plan_gta5_better.py UPLOADS_DIR SCRATCH_DIR
"""
import hashlib
import json
import sys
from pathlib import Path

import soundfile as sf

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent
L5, L6, SP = "GTA 5", "GTA 6", "split"
lh, rh = [0, 180, 640, 360], [640, 180, 640, 360]
logo = [140, 40, 440, 248]
hud = [860, 0, 416, 234]


def c(*cands):
    """One shot: candidates as (src, t, label, extra) tuples, or pair() dicts."""
    out = []
    for cand in cands:
        if isinstance(cand, dict):
            out.append(cand)
        else:
            s, t, lab, *x = cand
            out.append(dict(src=s, t=t, **({"label": lab} if lab else {}), **(x[0] if x else {})))
    return out


def pair(s5, t5, s6, t6):
    """Own split screen: a GTA 5 moment left, a GTA 6 moment right."""
    return {"pair": [[s5, t5], [s6, t6]]}


def card(k, title, bg, t, **kw):
    return [dict(card=k, title=title, bg=bg, t=t, **kw)]


P = [
 [("GTA 6 is finally out.", [c(("F3", 0.2, None, {"crop": logo}))]),
  ("Thirteen years after GTA 5, two delays later, after trailers that broke YouTube records, my whole feed is people calling it the best game ever made.",
   [c(("c4", 0.3, SP), ("c7", 0.3, SP)), c(("A", 28.8, L6)), c(("B", 13.6, L6))]),
  ("So here's the opinion that's going to get me roasted in the comments.", [c(("c5", None, L5, {"t_end": 16.0}))]),
  ("GTA 5 is the better game.", [card("UNPOPULAR OPINION", "GTA 5 > GTA 6", "c5", 16.1, boom=0.05)]),
  ("GTA 6 is the better looking game, I'm not arguing with that.", [c(("c3", 3.5, SP), ("c2", 9.5, SP))]),
  ("But looking better and being better are two different things, and in this video I'll show you exactly where they split.",
   [c(("c2", 9.5, SP), ("c1", 0.5, SP)), c(("c3", 8.5, SP), ("c2", 16.0, SP))]),
  ("Quick ground rules before the comments explode.", [c(("c10", 59.0, L5), ("c4", 12.0, L5))]),
  ("I'm not saying GTA 6 is bad. Honestly, it's probably a masterpiece.", [c(("F4", 136.0, L6), ("c11", 47.0, L6))]),
  ("I'm saying that if you asked me which one I'd rather play for the next thousand hours, my answer might surprise you.",
   [c(("c9", 57.5, L5), ("c10", 26.0, L5))])],
 [("Let's get the obvious part out of the way first.", [c(("c1", 0.8, SP))]),
  ("Look at this beach.", []),
  ("On the left, GTA 5: a handful of people, a couple of umbrellas, and a lot of empty sand.", [c(("c2", 2.0, L5, {"crop": lh}))]),
  ("On the right, GTA 6: crowds, towels, kites, people actually doing things.", [c(("c2", 2.0, L6, {"crop": rh, "repeat": True}))]),
  ("Same idea, thirteen years apart, and honestly, the difference is ridiculous.", [c(("c2", 15.0, SP), ("c2", 13.0, SP))]),
  ("The water is on another level too.", [c(("c7", 0.2, SP))]),
  ("Drive into the harbor in GTA 6, and the car floats for a moment, with waves rolling off it, before it sinks into the murky water.",
   [c(("c9", 18.5, L6, {"w": 2})), c(("c9", 27.0, L6))]),
  ("Go diving, and the water is so clear it barely looks like a game.", [c(("c11", 46.0, L6))]),
  ("And yes, there are sharks.", [c(("c11", None, L6, {"t_end": 71.8}))]),
  ("Same story with damage.", [c(("c3", 0.3, SP))]),
  ("Hit a wall in a GTA 5 taxi and you get a little dent.", [c(("c8", 3.0, L5))]),
  ("Do it in GTA 6 and the whole front end folds up.", [c(("c8", 27.6, L6)), c(("c8", 37.0, L6))]),
  ("In GTA 6 every bullet leaves its own hole, the glass cracks right where you hit it, and the metal dents where it should.",
   [c(("c3", 8.0, L6, {"crop": rh}), ("c4", 21.0, L6)), c(("c4", 24.0, L6), ("c5", 24.0, L6))]),
  ("If you care about detail, GTA 6 wins basically every side by side comparison, and it isn't close.",
   [c(pair("c10", 27.0, "c10", 40.5), pair("c7", 12.5, "c7", 17.0)), c(pair("c9", 50.0, "c10", 9.0), pair("c9", 59.0, "c10", 14.0))]),
  ("But I never played GTA 5 for the sand.", [c(("c2", 20.5, L5, {"crop": lh}), ("c2", 19.0, L5, {"crop": lh}))])],
 [("Reason number one: realism quietly killed the chaos.", [card("REASON #1", "REALISM KILLED|THE CHAOS", "c5", 22)]),
  ("Watch this.", [c(("c5", None, L5, {"t_end": 16.6, "repeat": True}))]),
  ("GTA 5. Franklin unloads into a parked car, and a few seconds later it catches fire and goes up in a massive fireball.", []),
  ("Completely unrealistic. Absolutely glorious.", [c(("c5", 16.0, L5, {"speed": 0.4, "boom": 0.5, "repeat": True}))]),
  ("Now GTA 6.", [c(("c5", 21.0, L6))]),
  ("Same experiment: a full magazine into an SUV on the beach.", []),
  ("It takes the hits, it smokes, it looks real.", []),
  ("And then you're just standing there, waiting for something to happen.", []),
  ("GTA was never a simulator.", [c(("c4", 8.0, L5))]),
  ("It was a cartoon of America with a rocket launcher.", []),
  ("The magic of GTA 5 was cause and effect at maximum volume: you do something stupid, and the game answers with something even more stupid.",
   [c(("c7", 6.0, L5))]),
  ("Cars flip, cops pile up, and everything explodes.", [c(("c8", 43.4, L5))]),
  ("Think about what you actually remember from GTA 5.", [c(("c7", 33.0, L5))]),
  ("It's usually not a mission, it's an accident.", []),
  ("A getaway that turned into a pileup, a cop car flying off a ramp, a rampage that started because somebody bumped into you.",
   [c(("c7", 39.5, L5), ("c10", 24.5, L5)), c(("c10", 0.3, L5), ("c9", 36.0, L5))]),
  ("Nobody remembers how realistic a puddle looked.", [c(("c11", 42.2, L6))]),
  ("The more realistic a game gets, the more it pushes back on that.", [c(("c10", 6.0, L6))]),
  ("Realistic damage means fewer fireballs.", [c(("c5", 33.0, L6))]),
  ("Smarter police means shorter rampages.", [c(("A", 0.2, L6))]),
  ("And characters that feel like real people make it a lot harder to run them over for fun.", [c(("c11", 2.0, L6), ("c10", 43.0, L6))]),
  ("All of that is amazing for a story.", [c(("F3", 7.2, L6))]),
  ("It's worse for the thing most of us actually did in GTA 5 for years, which was mess around.", [c(("c10", 51.0, L5))])],
 [("Reason number two: GTA 5 had Trevor.", [card("REASON #2", "GTA 5|HAD TREVOR", "c2", 3)]),
  ("Okay, not only Trevor.", [c(("c7", 56.0, L5), ("c10", 23.2, L5))]),
  ("GTA 5 gave you three protagonists you could switch between at almost any moment.", [card("3 PROTAGONISTS", "MICHAEL|FRANKLIN|TREVOR", "c4", 9)]),
  ("Michael, the retired bank robber in the middle of a midlife crisis.", [card("MICHAEL", "RETIRED|BANK ROBBER", "c5", 2)]),
  ("Franklin, the kid trying to get out of the hood.", [c(("c10", 58.0, L5), ("c4", 14.0, L5))]),
  ("And Trevor, who is just... Trevor.", [card("TREVOR", "JUST|TREVOR", "c5", 16.6)]),
  ("Switching between them was one of the best ideas Rockstar ever had.", [c(("c9", 2.0, L5)), c(("c10", 30.0, L5), ("c7", 56.0, L5))]),
  ("You'd jump to Trevor and find him waking up on a beach in his underwear, or in the middle of a fight nobody explained.", [c(("c9", 38.0, L5))]),
  ("And then GTA Online let you build your own character on top of all that, and a lot of people lived in that city for more than a decade.",
   [c(("c8", 10.5, L5))]),
  ("GTA 6 goes with two leads, Lucia and Jason, a couple on the run.", [c(("F3", 9.0, L6))]),
  ("That's a great setup for a story, a modern Bonnie and Clyde, and judging by the opening scene, the writing is sharp.",
   [c(("F3", 37.5, L6)), c(("F3", 41.3, L6))]),
  ("But three completely different lives crashing into each other is a bigger toy box than one relationship, no matter how good that relationship is.",
   [c(("c10", 12.0, L6)), c(("A", 18.9, L6))])],
 [("Reason number three, and this one is just math.", [card("REASON #3", "13 YEARS|OF CONTENT", "c4", 10)]),
  ("GTA 6 launched with whatever Rockstar managed to finish for day one.", [c(("A", 3.0, L6))]),
  ("GTA 5 has had thirteen years.", [card("SEPT 2013 TO NOV 2026", "13 YEARS", "c5", 4)]),
  ("Thirteen years of GTA Online updates.", [c(("c5", 0.5, L5))]),
  ("Heists, businesses, hundreds of cars, whole new places like Cayo Perico.",
   [c(("c10", 34.0, L5), ("c10", 30.0, L5)), c(("c7", 1.0, L5, {"crop": lh, "repeat": True}))]),
  ("GTA 5 even gave players Director Mode and the Rockstar Editor, basically a free movie studio.", [c(("c11", 16.0, L5))]),
  ("Some of the GTA 5 footage in this very video was recorded in Director Mode.",
   [c(("c8", 7.2, L5), ("c9", 9.0, L5)), c(("c8", 7.2, L5, {"crop": hud, "repeat": True}))]),
  ("And then there's everything Rockstar didn't make: the mods, and the roleplay servers that turned GTA 5 into a completely different game for millions of people and kept it near the top of Twitch years after release.",
   [c(("c8", 14.0, L5), ("c7", 56.0, L5)), c(("c9", 50.0, L5), ("c9", 56.0, L5)), c(("c5", 4.0, L5), ("c4", 16.0, L5))]),
  ("Rockstar liked that so much, they bought the team behind FiveM in 2023.", [card("2023", "ROCKSTAR BUYS|THE FIVEM TEAM", "c2", 8)]),
  ("And GTA 6 is console only for now, so the modding scene that kept GTA 5 alive hasn't even started.", [c(("B", 0.5, L6), ("A", 36.0, L6))]),
  ("And all of it still runs on PCs that are close to ten years old.", [c(("c4", 16.0, L5), ("c4", 14.0, L5))]),
  ("Day one GTA 6 has to compete with all of that at once.", [c(("B", 4.5, L6))]),
  ("That's not really GTA 6's fault.", [c(("A", 12.0, L6))]),
  ("But nobody picks a game on a fairness scale. If I have one free weekend, I'm going with the game that has more stuff to do.",
   [c(("c11", 29.5, L5))]),
  ("Honestly, any launch game would look small next to thirteen years of everything.", [c(("c10", 35.0, L5), ("c9", 8.5, L5))])],
 [("Reason number four might age badly itself, but here it is: realism has an expiration date.",
   [card("REASON #4", "REALISM HAS AN|EXPIRATION DATE", "c3", 8)]),
  ("Every console generation, some game gets crowned the most realistic thing ever made, and a few years later that same footage looks normal, and then it looks old.",
   [c(("c11", 50.5, L6)), c(("c9", 3.0, L5), ("c11", 36.0, L5))]),
  ("Graphics are a moving target.", [c(("c7", 2.6, SP), ("c2", 22.2, SP))]),
  ("Whatever blows your mind today is the minimum next generation.", [c(("F4", 118.0, L6))]),
  ("What doesn't age is how a game feels.", [c(("c10", 56.5, L5), ("c4", 18.0, L5))]),
  ("GTA 5's driving, its chaos, its jokes about Los Angeles.", [c(("c9", 45.5, L5)), c(("c7", 41.0, L5), ("c8", 15.0, L5))]),
  ("People still boot it up in 2026 and have a great time.", [c(("c11", 22.0, L5))]),
  ("That's the real test, and GTA 6 can't take it yet, because nobody knows how it'll feel once the shine wears off.",
   [c(("F4", 128.0, L6)), c(("B", 24.0, L6))]),
  ("GTA 5 has already passed it, every single year since 2013.", [c(("c9", 48.0, L5), ("c1", 2.5, SP))])],
 [("Reason number five is bigger than GTA: games stop being relevant a lot faster than they used to.",
   [card("REASON #5", "THE HYPE|BURNS FASTER", "A", 30)]),
  ("GTA 5 grew up in a world where one game could stay the main topic for years.", [c(("c4", 17.0, L5), ("c5", 9.0, L5), ("c11", 13.0, L5))]),
  ("Think about how many huge games we all played for a month and then completely forgot.", [c(("A", 24.0, L6))]),
  ("On launch day they were everywhere, and two weeks later the conversation had moved on.", [c(("B", 26.0, L6), ("B", 40.0, L6))]),
  ("GTA 5 is one of the very few games that dodged that, and it did it before TikTok even existed.", [c(("c11", 35.5, L5), ("c9", 10.0, L5))]),
  ("GTA 6 launches into a feed that moves on every week.",
   [[dict(grid=[["c7", 20.0], ["c8", 30.0], ["c9", 21.0], ["c10", 8.0], ["c11", 50.0], ["A", 0.5], ["B", 14.0], ["F3", 5.0], ["c11", 66.0]])]]),
  ("Today it's the only thing anyone is posting.", []),
  ("In a month, people will have seen every big moment in clips without ever playing it, and the algorithm will be pushing the next thing.",
   [c(("A", 33.5, L6)), c(("B", 15.5, L6), ("B", 44.0, L6))]),
  ("The hype for GTA 6 is arguably the biggest any game has ever had.", [c(("F3", 0.2, None, {"crop": logo, "repeat": True}))]),
  ("But hype that big burns fast, and the higher it goes, the harder it is to live up to.", [c(("B", 44.0, L6), ("A", 36.0, L6))]),
  ("GTA 5 never had to compete with thirteen years of people imagining it.", [c(("c5", 0.3, L5), ("c7", 31.3, L5), ("c1", 0.6, SP, {"repeat": True}))])],
 [("To be fair, let me argue against myself for a second.", [card("TO BE FAIR", "LET ME ARGUE|AGAINST MYSELF", "B", 5)]),
  ("GTA 6 is on day one.", [c(("A", 9.0, L6))]),
  ("GTA 5 on day one didn't have online heists either.", [c(("c4", 14.5, L5), ("c5", 10.0, L5), ("c9", 12.0, L5))]),
  ("Those came a year and a half later.", []),
  ("Rockstar will support this game for a decade, and if GTA Online taught us anything, the GTA 6 we're playing in 2030 will be way bigger than what's out today.",
   [c(("B", 22.0, L6), ("B", 0.5, L6)), c(("F4", 134.0, L6), ("F4", 100.0, L6))]),
  ("It can also still get really stupid.", [c(("c7", 19.9, L6))]),
  ("Here's a police chase that ends with the GPS saying turn left, straight into the jungle.",
   [c(("B", 32.6, L6, {"crop": [0, 450, 480, 270]})), c(("B", 34.0, L6, {"w": 2}))]),
  ("So the chaos isn't gone, it just takes a bit more effort.", [c(("c7", 24.6, L6))]),
  ("And Red Dead Redemption 2 already proved Rockstar's realism can age well.", [card("RED DEAD REDEMPTION 2", "OUT SINCE|2018", "F4", 136)]),
  ("It came out in 2018 and it still looks better than most games released this year.", []),
  ("So maybe in five years this video ages like milk.", [c(("c7", 44.7, L6), ("c3", 8.5, SP, {"repeat": True}))]),
  ("I'm okay with that.", [])],
 [("But today, if you ask me which game I'd rather lose a whole weekend in, it's still GTA 5.",
   [c(("c10", 33.0, L5), ("c10", 37.0, L5)), c(("c8", None, L5, {"t_end": 46.6, "repeat": True}))]),
  ("GTA 6 is the more impressive game.", [c(("c11", 55.0, L6))]),
  ("GTA 5 is the more fun one.", [c(("c5", 16.0, L5, {"speed": 0.5, "repeat": True}))]),
  ("So tell me in the comments: am I crazy, or does GTA 5 still hit harder?", [card("YOUR TURN", "GTA 5 OR|GTA 6?", "c2", 12)]),
  ("And tell me which of my five reasons is the weakest, because I know one of them is.", []),
  ("And if you want the best GTA 6 moments as they happen, subscribe.", [card("NEW CLIPS EVERY DAY", "SUBSCRIBE", "B", 8)]),
  ("I'll see you in Leonida.", [])],
]

crop360 = [128, 0, 512, 288]
G5, G6 = L5, L6
src = lambda n: f"{U}/{n}.mkv"
SOURCES = {
 "c1": {"path": src("c4d04f28-1"), "scenes": [[0, 6.0, SP]]},
 "c2": {"path": src("647f8765-2"), "scenes": [[0, 24.0, SP]]},
 "c3": {"path": src("cb4668c6-3"), "scenes": [[0, 12.0, SP]]},
 "c4": {"path": src("65f2afac-4"), "scenes": [[0, 6.6, SP], [7.7, 20.25, G5], [20.35, 33.9, G6]]},
 "c5": {"path": src("4bf24d0e-5"), "scenes": [[0, 20.7, G5], [20.85, 41.4, G6]]},
 "c7": {"path": src("d1349b1f-7"), "scenes": [[0, 4.5, SP], [5.7, 16.25, G5], [16.35, 30.2, G6], [31.3, 44.55, G5], [44.65, 54.6, G6], [55.8, 58.3, G5]]},
 "c8": {"path": src("e935d9ef-8"), "scenes": [[0, 19.75, G5], [19.85, 42.0, G6], [43.2, 46.9, G5]]},
 "c9": {"path": src("bb1f6490-9"), "scenes": [[0, 14.85, G5], [14.95, 34.3, G6], [35.5, 65.1, G5]]},
 "c10": {"path": src("f6ce6b2c-10"), "scenes": [[0, 4.35, G5], [4.45, 21.8, G6], [23.0, 39.75, G5], [39.85, 49.2, G6], [50.4, 61.55, G5], [61.65, 63.6, G6]]},
 "c11": {"path": src("9e6094d9-11"), "scenes": [[0, 11.1, G6], [12.3, 41.85, G5], [41.95, 71.9, G6]]},
 "A": {"path": f"{U}/a20a5ca3-GTA_6_Open_World_Police_Chase_Gameplay___Chaos_in_the_Leonida_Keys___INSANE_Police_Chase_on_PS5_Pro.mkv",
       "scenes": [[0, 41.35, G6]]},
 "B": {"path": f"{U}/5462d642-w.mkv", "scenes": [[0, 52.75, G6]]},
 "F1": {"path": f"{U}/1537e350-__.mkv", "crop": crop360, "scenes": [[0, 49.5, G6]]},
 "F3": {"path": f"{U}/12bd0782-__.mkv", "crop": crop360, "scenes": [[0, 71.5, None]]},
 "F4": {"path": f"{U}/4ef0c96b-___.mkv", "crop": crop360, "scenes": [[0, 143.0, G6]]},
}
job = {"out": f"{S}/longform/out/gta5_better_than_gta6_v2.mp4", "work": f"{S}/longform/work",
       "voice": "am_fenrir", "speed": 0.95, "tts_model": f"{S}/tts/kokoro-v1.0.onnx", "tts_voices": f"{S}/tts/voices-v1.0.bin",
       "sources": SOURCES}

# ---- sentence slots from the TTS cache (make_longform.py lays the narration out the same way)
tdir = Path(job["work"]) / "tts"
slots, t = [], 0.4
flat = [(text, shots, k == len(par) - 1) for par in P for k, (text, shots) in enumerate(par)]
for text, _, last in flat:
    key = hashlib.sha1(f"{job['voice']}|{job['speed']}|{text}".encode()).hexdigest()[:16]
    f = tdir / f"{key}.wav"
    if not f.exists():
        sys.exit(f"no narration cached for: {text[:50]} (run make_longform.py once to synthesize)")
    a, sr = sf.read(f)
    gap = 0.7 if last else 0.28
    slots.append(len(a) / sr + gap)
slots[0] += 0.4

# ---- allocator
# A moment may come back only after FAR seconds of video; the explosion and the pier jump are kept
# out of the fallback pools so they stay reserved for the shots that name them.
FAR = 150
RESERVED = {"c5": [(15.8, 20.7)], "c8": [(43.2, 46.9)]}
POOLS = {
 L5: [("c7", 5.7, 16.25), ("c9", 35.5, 65.1), ("c10", 23.0, 39.75), ("c10", 50.4, 61.55), ("c11", 12.3, 41.85),
      ("c8", 0, 19.75), ("c9", 0, 14.85), ("c7", 31.3, 44.55), ("c4", 7.7, 20.25), ("c5", 0, 20.7),
      ("c7", 55.8, 58.3), ("c10", 0, 4.35)],
 L6: [("c11", 41.95, 71.9), ("c10", 4.45, 21.8), ("c8", 19.85, 42.0), ("c9", 14.95, 34.3), ("c7", 16.35, 30.2),
      ("c7", 44.65, 54.6), ("c10", 39.85, 49.2), ("c11", 0, 11.1), ("c4", 20.35, 33.9), ("c5", 20.85, 41.4),
      ("A", 0, 41.35), ("B", 0, 52.75)],
 SP: [("c2", 0, 24.0), ("c3", 0, 12.0), ("c1", 0, 6.0), ("c4", 0, 6.6), ("c7", 0, 4.5)],
}
used = {}


def scene_of(srcname, t):
    for s in SOURCES[srcname]["scenes"]:
        if s[0] - 0.05 <= t < s[1]:
            return s
    return None


def fits(srcname, a, b, now):
    return all(min(b, b2) - max(a, a2) <= 0.5 or now - at >= FAR for a2, b2, at in used.get(srcname, []))


def pool_pick(label, need, now):
    for srcname, lo, hi in POOLS.get(label, []):
        a = lo + 0.1
        while a + need <= hi - 0.1:
            clash = any(min(a + need, r1) - max(a, r0) > 0 for r0, r1 in RESERVED.get(srcname, []))
            if not clash and fits(srcname, a, a + need, now):
                return srcname, round(a, 2)
            a += 0.5
    return None


plan, report = [], []
for (text, shots, _), slot in zip(flat, slots):
    if not shots:
        plan[-1]["text"] += " " + text
        plan[-1]["slot"] += slot
        continue
    plan.append({"text": text, "slot": slot, "shots": shots})

resolved, now = [], 0.0
for item in plan:
    ws = [cands[0].get("w", 1) for cands in item["shots"]]
    out = []
    for cands, w in zip(item["shots"], ws):
        need0 = item["slot"] * w / sum(ws)
        if "card" in cands[0] or "grid" in cands[0]:
            out.append(cands[0])
            now += need0
            continue
        pick = None
        for cand in [x for x in cands if "pair" in x]:
            for off in (0, 0.5, -0.5, 1, -1, 1.5, -1.5, 2, -2, 2.5, -2.5, 3, -3):
                parts = [(k, t + off) for k, t in cand["pair"]]
                scs = [scene_of(k, t) for k, t in parts]
                if all(sc and t + need0 <= sc[1] for sc, (k, t) in zip(scs, parts)) and \
                        all(fits(k, t, t + need0, now) for k, t in parts):
                    pick = {"pair": [[k, round(t, 2)] for k, t in parts]}
                    break
            if pick:
                break
        if pick:
            for k, t in pick["pair"]:
                used.setdefault(k, []).append((t, t + need0, now))
            out.append(pick)
            now += need0
            continue
        if all("pair" in x for x in cands):
            pick = cands[0]
            report.append(f"{int(now // 60)}:{now % 60:04.1f} REPEAT pair {item['text'][:40]}")
            out.append(pick)
            now += need0
            continue
        for cand in [x for x in cands if "pair" not in x]:
            need = need0 * cand.get("speed", 1.0)
            t0 = cand["t_end"] - need if cand.get("t_end") is not None else cand["t"]
            sc = scene_of(cand["src"], max(t0, 0.0)) or scene_of(cand["src"], cand.get("t_end", 0) - 0.1)
            if sc is None:
                continue
            for off in (0, 0.5, -0.5, 1, -1, 1.5, -1.5, 2, -2, 2.5, -2.5, 3, -3):
                a = min(max(t0 + off, sc[0]), sc[1] - need)
                if a < sc[0] - 0.01:
                    break
                if cand.get("repeat") or fits(cand["src"], a, a + need, now):
                    pick = dict(cand, t=round(a, 2))
                    pick.pop("t_end", None)
                    break
            if pick:
                break
        if pick is None:
            first = cands[0]
            label = first.get("label") or (SP if first.get("crop") is None else None)
            found = pool_pick(label, need0 * first.get("speed", 1.0), now)
            if found:
                pick = {k: v for k, v in first.items() if k not in ("crop", "t_end")}
                pick["src"], pick["t"] = found
                report.append(f"{int(now // 60)}:{now % 60:04.1f} pool  {item['text'][:44]:44s} -> {found[0]}@{found[1]}")
            else:
                pick = dict(first)
                report.append(f"{int(now // 60)}:{now % 60:04.1f} REPEAT {item['text'][:44]:44s} -> {pick['src']}")
        need = need0 * pick.get("speed", 1.0)
        used.setdefault(pick["src"], []).append((pick["t"], pick["t"] + need, now))
        out.append(pick)
        now += need0
    resolved.append(out)

# ---- write the job: the first sentence of each merged group carries the shots, the rest are []
paragraphs, k = [], 0
for par in P:
    sents = []
    for text, shots in par:
        if shots:
            sents.append({"text": text, "shots": resolved[k]})
            k += 1
        else:
            sents.append({"text": text, "shots": []})
    paragraphs.append({"sentences": sents})
job["paragraphs"] = paragraphs
(HERE / "longform_gta5_better.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
print(f"{len(flat)} sentences, {sum(len(t.split()) for t, _, _ in flat)} words, {sum(slots):.1f}s")
print("\n".join(report) if report else "allocator: every shot has its own footage")
