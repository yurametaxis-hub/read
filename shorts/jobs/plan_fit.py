#!/usr/bin/env python3
"""FAT vs FIT short from a split-screen GTA 6 body comparison (left half FAT, right half FIT, 5 s per scene).

    python3 shorts/jobs/plan_fit.py UPLOADS_DIR SCRATCH_DIR
    python3 shorts/make_meme_short.py shorts/jobs/meme_fit.json

Source scenes (seconds): 0-3.03 BEST SHAPE STATS (Lucia left, Jason right, stat panels at the top),
3.03-9.40 Lucia walking away, 9.40-14.87 Lucia and Jason walking (front view from ~12), 14.87-19.87 Jason face,
19.87-24.87 Jason profile, 24.87-29.87 Jason torso, 29.87-34.87 Lucia face, 34.87-36.05 Lucia profile.
The source audio is someone's background music, so it stays muted. Stat values read off the panel:
135 LB and 222 LB, WELL RESTED, HUNGRY, CALORIE BALANCE, SHREDDED, MAX muscle, LOW body fat.
Crops use zoom 1.12 and y 0.45 so the baked FAT and FIT labels at the bottom stay out of frame.
"""
import json
import sys
from pathlib import Path

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent
PANEL = dict(layout="split", zoom=1.12, y=0.45)
LX, RX = 268, 812  # panel centres on screen
LABEL_Y = 440


def sh(t, **kw):
    return dict(PANEL, src="f1", t=t, **kw)


def txt(text, at=0.0, **kw):
    return dict(type="text", text=text, at=at, **kw)


def emo(e, at=0.0, **kw):
    return dict(type="emoji", emoji=e, at=at, **kw)


def labels(at=0.0, anim="none"):
    return [txt("FAT 🍔", at, x=LX, y=LABEL_Y, font="Bangers", size=78, bg="#d81b1b", anim=anim),
            txt("FIT 💪", at, x=RX, y=LABEL_Y, font="Bangers", size=78, bg="#18a84a", anim=anim)]


ROW = dict(font="Anton", size=58, bg="rgba(88,40,120,.92)", pad="6px 30px", radius=8, upper=True, anim="pop", spacing=2)
stat_rows = [txt(label, at, x=540, y=560 + i * 92, **ROW) for i, (label, at) in enumerate(
    [("⚖️ WEIGHT", 0.05), ("😴 SLEEP", 0.5), ("🥗 NUTRITION", 1.0), ("🍔 CALORIES", 1.7), ("💪 MUSCLE", 2.3), ("🍩 BODY FAT", 2.75)])]

beats = [
    # hook: the strongest contrast first, it becomes the preview frame
    {"say": "Wait. GTA 6 is counting your calories?", "delay": 0.25,
     "shots": [sh(25.0, speed=0.85, zoom=1.3, zoom_to=1.12, ease="punch", fx={"flash": ["white", 0.0], "shake": [[0.0, 0.5, 22]]})],
     "sfx": [{"name": "vine_boom", "at": 0.0, "gain": 0.8}],
     "stickers": labels(0.05, "pop")},
    {"say": "Weight, sleep, nutrition, calories, muscle, body fat.", "pad": 0.35,
     "shots": [sh(0.1, speed=0.8, xl=0.32, xr=0.68)],
     "sfx": [{"name": "pop", "at": r["at"], "gain": 0.7} for r in stat_rows],
     "stickers": [txt("LUCIA", 0.0, x=LX, y=LABEL_Y, font="Bangers", size=70, bg="#111", anim="none"),
                  txt("JASON", 0.0, x=RX, y=LABEL_Y, font="Bangers", size=70, bg="#111", anim="none")] + stat_rows},
    {"say": "And it actually changes how they look.", "shots": [sh(3.15)],
     "sfx": [{"name": "whoosh", "at": 0.0, "gain": 0.6}], "stickers": labels(0.0, "pop")},
    {"say": "Same walk, same bikini. Fat on the left, fit on the right.", "shots": [sh(5.6, speed=0.95)],
     "stickers": labels()},
    {"say": "One side gets abs. The other side gets snacks.", "shots": [sh(12.2, speed=0.85, x=0.42)],
     "sfx": [{"name": "ding", "at": 0.75, "gain": 0.5}, {"name": "bonk", "at": 2.1, "gain": 0.7}],
     "stickers": labels() + [emo("💪", 0.75, x=RX, y=900, size=200), emo("🍔", 2.1, x=LX, y=900, size=200)]},
    {"say": "Even the face changes.", "shots": [sh(15.1, speed=0.9, y=0.42, zoom=1.12, zoom_to=1.3)],
     "meme": [{"say": "Bro let himself go.", "at": 1.75}],
     "stickers": labels() + [emo("💀", 1.85, x=LX, y=880, size=210)]},
    {"say": "And Jason goes from dad bod to fully shredded.", "shots": [sh(26.9, speed=0.9, zoom=1.12, zoom_to=1.24)],
     "meme": [{"say": "Light weight, baby!", "at": 2.85}],
     "sfx": [{"name": "airhorn", "at": 2.2, "gain": 0.35}],
     "stickers": labels() + [txt("SHREDDED", 2.15, x=RX, y=1180, font="Anton", size=72, bg="#18a84a", rot=-4, anim="slam"),
                             emo("🗿", 2.9, x=RX, y=860, size=190)]},
    {"say": "Even Lucia's face changes.", "shots": [sh(30.1, speed=0.9, y=0.42)], "stickers": labels()},
    {"say": "So, are you hitting the gym in Leonida, or Burger Shot?", "pad": 0.7,
     "shots": [sh(32.3, speed=0.62, y=0.42, zoom=1.12, zoom_to=1.2)],
     "sfx": [{"name": "vine_boom", "at": 0.1, "gain": 0.45}],
     "stickers": labels() + [txt("GYM 💪 OR BURGER SHOT 🍔?", 0.15, x=540, y=1000, font="Bangers", size=78, bg="#d81b1b",
                                 rot=-3, maxw=980)]},
]

job = {"out": f"{S}/fit/out/meme_fit.mp4", "work": f"{S}/fit/work_meme_fit",
       "tts_model": f"{S}/tts/kokoro-v1.0.onnx", "tts_voices": f"{S}/tts/voices-v1.0.bin",
       "voice": "af_heart", "speed": 1.05, "meme_voice": "am_onyx", "meme_speed": 0.92,
       "music": "phonk", "music_volume": 0.38, "game_volume": 0.0, "layout": "split",
       "hook": "GTA 6 COUNTS YOUR [CALORIES]?! 😳", "keywords": ["calories", "fat", "fit", "shredded"],
       "sources": {"f1": {"path": f"{U}/c3376b15-1.mkv"}}, "beats": beats}
(HERE / "meme_fit.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
print("meme_fit", len(beats), "beats,", sum(len(b.get("say", "").split()) for b in beats), "words")
