#!/usr/bin/env python3
"""First batch of "what Rockstar is really saying" shorts: our own voice-over over the clips, never the
original commentary (it is someone else's work and some of its claims are not shown in the footage).

    python3 shorts/jobs/plan_hidden_batch1.py UPLOADS_DIR SCRATCH_DIR
    python3 shorts/make_voice_short.py shorts/jobs/voice_bear.json   (and the other three)
"""
import json
import sys
from pathlib import Path

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent


def scenes(cuts, end, skip=()):
    """Scene list from scenedetect cut times, trimmed 0.05 s at each cut; skip holds ranges to leave out."""
    pts = list(cuts) + [end]
    out = []
    for a, b in zip(pts, pts[1:]):
        a, b = a + 0.05, b - 0.05
        for s0, s1 in skip:
            if a < s1 and b > s0:
                if a < s0:
                    out.append([round(a, 2), round(s0, 2), None])
                a = max(a, s1)
        if b - a > 0.3:
            out.append([round(a, 2), round(b, 2), None])
    return out


SOURCES = {
    # h1: a "$3 billion" news card covers 14.9 to 17.7, never used
    "h1": {"path": f"{U}/8b330bbc-1_.mkv",
           "scenes": scenes([0, 5.1, 8.6, 11.4, 12.9, 18.9, 21.8, 24.0, 26.0, 28.7, 31.4], 38.0, skip=[(14.9, 17.7)])},
    # h4: a stock art card starts at 29.4; the bear protest is 16.25 to 29.3
    "h4": {"path": f"{U}/f7e4270c-4.mkv",
           "scenes": scenes([0, 2.3, 3.8, 9.0, 16.2, 32.6, 34.7], 36.7, skip=[(29.35, 32.6)])},
    # h5: 7.1 to 13.2 is a real person's reaction video, never used; BenedictPlays watermark on the painting
    "h5": {"path": f"{U}/d07d104b-5.mkv", "delogo": [[1058, 76, 184, 36]],
           "scenes": scenes([0, 6.3, 7.1, 13.2, 20.0, 23.4, 29.3], 35.5, skip=[(7.1, 13.2)])},
    "h9": {"path": f"{U}/426591e5-9.mkv",
           "scenes": scenes([0, 6.54, 8.98, 21.32, 22.62, 29.43, 31.46, 32.80, 34.20, 38.77, 45.61, 50.78, 55.66,
                             57.49, 58.39, 68.10, 74.97, 78.85], 80.88)},
    "h10": {"path": f"{U}/92941a1b-10.mkv",
            "scenes": scenes([0, 4.54, 7.67, 9.21, 12.85, 14.55, 16.32, 18.22, 20.69, 21.79, 22.79, 29.43, 31.57,
                              33.07, 42.01, 50.75, 52.92, 53.52, 54.72], 63.3)},
    "h16": {"path": f"{U}/861b7c16-16.mkv",
            "scenes": scenes([0, 0.77, 5.83, 7.53, 8.60, 9.60, 12.10, 13.53, 14.53, 15.93, 17.37, 18.77, 20.20, 21.87,
                              23.20, 24.53, 25.83, 26.77], 29.7)},
    "h18": {"path": f"{U}/73bc492c-18.mkv",
            "scenes": scenes([0, 7.93, 8.63, 10.53, 11.87, 13.30, 14.20, 19.00, 22.23, 23.93, 28.73, 31.37, 33.80,
                              39.60, 41.67, 44.67, 47.40, 48.83, 49.63, 50.60, 54.10, 56.83, 61.13, 66.63, 69.80,
                              73.17, 74.60], 75.7)},
    "h19": {"path": f"{U}/902db830-19.mkv",
            "scenes": scenes([0, 3.17, 5.00, 6.00, 7.47, 10.20, 12.23, 13.07, 16.77, 21.03, 23.10, 24.50], 26.7)},
    "A": {"path": f"{U}/a20a5ca3-GTA_6_Open_World_Police_Chase_Gameplay___Chaos_in_the_Leonida_Keys___INSANE_Police_Chase_on_PS5_Pro.mkv",
          "scenes": scenes([0, 20.03, 23.6, 29.6, 30.6], 41.4)},
}
BASE = {"voice": "am_fenrir", "speed": 1.05, "tts_model": f"{S}/tts/kokoro-v1.0.onnx",
        "tts_voices": f"{S}/tts/voices-v1.0.bin", "game_volume": 0, "sources": SOURCES}


def shot(src, t, **kw):
    return dict(src=src, t=t, **kw)


def job(name, title, lines):
    j = dict(BASE, out=f"{S}/hidden/out/{name}.mp4", work=f"{S}/hidden/work_{name}", title=title,
             paragraphs=[{"sentences": [{"text": t, "shots": s} for t, s in lines]}])
    (HERE / f"{name}.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))
    print(name, sum(len(t.split()) for t, _ in lines), "words")


sign = shot("h4", 20.15, x=0.13, y=0.36, zoom=1.6)
job("voice_bear", "GTA 6 is trolling *activists* 🐻", [
    ("Rockstar is trolling activists in GTA 6.", [sign, shot("h4", 16.3, x=0.35)]),
    ("Protesters block an animal services truck and want the driver to free a bear.",
     [shot("h4", 21.1, x=0.5, speed=0.8, whoosh=True)]),
    ("One of them is just filming it all for content.",
     [shot("h4", 18.05, x=0.664, x_end=0.60, y=0.45, zoom=1.3, speed=0.6, circle=[855, 300, 55], circle_t=[0.2, 2.0])]),
    ("Another one yells: stop being a tool of the bear abusers!", [shot("h4", 24.6, x=0.42, speed=0.7)]),
    ("Someone tries to break the truck open and says the tutorial made it look way easier.",
     [shot("h4", 27.0, x=0.7, zoom=1.1, speed=0.55)]),
    ("And then comes the best line: you can't just let her out, you'll mess up the ecology. You guys care about that, right?",
     [shot("h4", 22.0, x=0.62, zoom=1.35, repeat=True), shot("h4", 26.0, x=0.4, zoom=1.3, repeat=True)]),
    ("Rockstar still makes fun of everyone.", [shot("h1", 0.3, x=0.5, whoosh=True)]),
    ("Would you free the bear?", [dict(sign, repeat=True)]),
])

job("voice_sims", "GTA 6 turned into *The Sims* 😭", [
    ("We waited thirteen years for GTA 6.", [shot("h1", 8.7, x=0.5), shot("h1", 26.1, x=0.5)]),
    ("Heists, car chases, helicopters...", [shot("h4", 4.0, x=0.5), shot("h4", 9.3, x=0.55), shot("h1", 0.5, x=0.5)]),
    ("and Jason is painting walls.", [shot("h5", 13.4, x=0.38, whoosh=True)]),
    ("Paint can, roller, the whole thing.", [shot("h5", 20.15, x=0.62, circle=[870, 460, 115])]),
    ("Rockstar really turned GTA into The Sims.", [shot("h5", 15.8, x=0.62)]),
    ("Next update, Jason does his taxes.", [shot("h5", 18.4, x=0.45)]),
    ("Would you rather rob a bank, or paint your walls?", [shot("h4", 5.2, x=0.5), shot("h5", 22.4, x=0.55)]),
])

job("voice_woke1997", "GTA went *woke* in 1997? 😳", [
    ("Everyone says GTA 6 went woke.", [shot("h16", 12.2, x=0.5, y=0.45), shot("h10", 39.0, x=0.45)]),
    ("But Rockstar was doing this before most of you were born.", [shot("h16", 5.9, x=0.5, y=0.4), shot("h16", 9.7, x=0.5, y=0.4)]),
    ("The very first GTA, back in 1997, already let you play as a woman.",
     [shot("h16", 3.5, x=0.5, y=0.32, zoom=1.25, speed=0.4)]),
    ("Vice City Stories had a trans film director.", [shot("h18", 19.1, x=0.5, y=0.38, zoom=1.25)]),
    ("GTA 4 had Bernie, Niko's old army buddy, secretly dating the deputy mayor.",
     [shot("h19", 13.1, x=0.55, y=0.4, zoom=1.2, speed=0.8)]),
    ("And a whole expansion was named after a nightclub owner called Gay Tony.",
     [shot("h18", 50.65, x=0.5, y=0.38, zoom=1.2), shot("h18", 54.15, x=0.45, y=0.38, zoom=1.2)]),
    ("So GTA didn't suddenly go woke.", [shot("h9", 6.6, x=0.5, whoosh=True)]),
    ("It always had everyone in it, and it always roasted everyone.", [shot("h4", 24.0, x=0.45)]),
    ("Which old GTA character should come back in GTA 6?", [shot("h10", 50.8, x=0.5), shot("h19", 0.2, x=0.5, y=0.4, zoom=1.2)]),
])

job("voice_girlboss", "Is Lucia a *girl boss*? 🤔", [
    ("Is Lucia a girl boss?", [shot("h10", 44.6, x=0.5, zoom=1.1)]),
    ("In this robbery she flips a grown man over her shoulder like it's nothing.",
     [shot("h10", 46.1, x=0.5), shot("h10", 48.0, x=0.5, speed=0.5, boom=1.5)]),
    ("Some reviewers already call it silly.", [shot("h10", 49.15, x=0.5, speed=0.8)]),
    ("But Lara Croft was doing backflips in 1996, and nobody cared.", [shot("h9", 34.3, x=0.45, whoosh=True)]),
    ("And come on, it's GTA. Every main character takes out a small army alone.",
     [shot("h10", 34.0, x=0.45), shot("h9", 45.7, x=0.5)]),
    ("Jason does it every five minutes, and nobody asks if he's a boy boss.", [shot("A", 2.7, x=0.5)]),
    ("So is Lucia too much, or is this just GTA?", [shot("h10", 50.8, x=0.5), shot("h10", 39.6, x=0.45)]),
])
