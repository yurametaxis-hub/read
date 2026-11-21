#!/usr/bin/env python3
"""Five WTF shorts from the ReplayNext GTA 6 compilation clips (original moments by the Reddit users credited
on screen). New style: am_puck and bm_george voices, Luckiest Guy captions, Anton hooks, meme kit sounds.

    python3 shorts/jobs/plan_meme_batch1.py UPLOADS_DIR SCRATCH_DIR
    python3 shorts/make_meme_short.py shorts/jobs/meme_karma.json      (and the other four)

Every line describes what the footage shows; dialogue in bubbles is the game's own subtitle text.
ReplayNext's baked-in meme captions are cut around or covered by our own stickers.
"""
import json
import sys
from pathlib import Path

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent
SRC = {"w1": "821d1f49-1", "w2": "c2762f34-2", "w4": "33eda07f-4", "w6": "a0b9f0ce-6", "w8": "aa757a09-8",
       "w9": "3446ee03-9", "w10": "5d39c651-10"}
BASE = {"tts_model": f"{S}/tts/kokoro-v1.0.onnx", "tts_voices": f"{S}/tts/voices-v1.0.bin",
        "meme_voice": "am_onyx", "meme_speed": 0.92, "layout": "band"}


def job(name, used, **kw):
    j = dict(BASE, out=f"{S}/wtf/out/{name}.mp4", work=f"{S}/wtf/work_{name}",
             sources={k: {"path": f"{U}/{SRC[k]}.mkv"} for k in used}, **kw)
    (HERE / f"{name}.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))
    words = sum(len(b.get("say", "").split()) for b in j["beats"])
    print(name, len(j["beats"]), "beats,", words, "words")


def sh(src, t, **kw):
    return dict(src=src, t=t, **kw)


def txt(text, at=0.0, **kw):
    return dict(type="text", text=text, at=at, **kw)


def emo(e, at=0.0, **kw):
    return dict(type="emoji", emoji=e, at=at, **kw)


def bub(text, at=0.0, **kw):
    return dict(type="bubble", text=text, at=at, **kw)


# 1. ---------------------------------------------------------------- night drive, someone on the windshield
job("meme_windshield", ["w1", "w2"], voice="bm_george", speed=0.95, music="horror", music_volume=0.7, look="vhs",
    grade={"gamma": 1.75, "contrast": 1.08, "lift": 6},
    game_volume=0.55, hook="WHAT IS ON HIS [WINDSHIELD]?? 😳", credit="🎥 u/Technical-Problem982 · via ReplayNext",
    keywords=["windshield", "gone"],
    beats=[
        {"shots": [sh("w2", 12.2, dur=1.0, layout="fill", y=0.45, zoom=1.3, zoom_to=1.7, ease="out",
                      fx={"flash": ["red", 0.0], "shake": [[0.0, 0.7, 30]]})],
         "sfx": [{"name": "jumpscare", "at": 0.0, "gain": 0.8}]},
        {"shots": [sh("w2", 12.2, dur=0.9, reverse=True, speed=4, y=0.42, zoom=1.2, fx={"rewind": True})],
         "sfx": [{"name": "rewind", "at": 0.0, "gain": 0.5}]},
        {"say": "Late at night, somewhere in Leonida.", "shots": [sh("w1", 11.1, zoom=1.0, zoom_to=1.08)]},
        {"say": "Thick fog. An empty road. He's just driving.", "shots": [sh("w2", 0.4, zoom=1.0, zoom_to=1.1)],
         "sfx": [{"name": "heartbeat", "at": 0.6, "gain": 0.55, "kw": {"bpm": 62, "beats": 4}}]},
        {"say": "And then...", "min": 2.6, "music_cut": True, "shots": [sh("w2", 6.0, y=0.42, zoom=1.2, zoom_to=1.32)],
         "sfx": [{"name": "heartbeat", "at": 0.0, "gain": 0.7, "kw": {"bpm": 110, "beats": 5}}]},
        {"min": 1.5, "shots": [sh("w2", 10.62, layout="fill", y=0.45, zoom=1.15, zoom_to=1.5, ease="punch",
                                 fx={"flash": ["red", 0.0], "shake": [[0.0, 0.8, 38]]})],
         "sfx": [{"name": "jumpscare", "at": 0.0, "gain": 0.9}],
         "meme": [{"say": "Nope.", "at": 0.85}],
         "stickers": [emo("😳", 0.45, x=830, y=720, size=230, dur=1.0)]},
        {"say": "Someone is lying face down on his windshield.", "shots": [sh("w2", 12.05, zoom=1.1, zoom_to=1.25)]},
        {"say": "Long hair. Arms spread wide. And they are not letting go.", "shots": [sh("w2", 13.4, zoom=1.15, zoom_to=1.3)]},
        {"say": "Then there's a flash... and they're just gone.",
         "shots": [sh("w2", 15.25, dur=1.05), sh("w2", 16.4)], "sfx": [{"name": "whoosh", "at": 0.35, "gain": 0.7}]},
        {"say": "GTA 6, or a horror game? Would you keep driving?", "pad": 0.6,
         "shots": [sh("w2", 16.9, freeze=True, zoom=1.0, zoom_to=1.12)],
         "sfx": [{"name": "vine_boom", "at": 0.2, "gain": 0.6}],
         "stickers": [txt("GTA 6 OR A HORROR GAME? 💀", 0.2, font="Bangers", size=88, bg="#b30000", y=960, rot=-3)]},
    ])

# 2. ---------------------------------------------------------------- the robbery that ends with a scooter
DLG = dict(x=0.6, y=0.43, zoom=1.25)
HIT = dict(x=0.66, y=0.45, zoom=1.2)
job("meme_karma", ["w9"], voice="am_puck", speed=1.05, music="pizz", music_volume=0.45, game_volume=0.6,
    hook="HE TRIED TO ROB JASON... [INSTANT KARMA] 💀", credit="🎥 u/alpha_hen96 · via ReplayNext",
    keywords=["scooter", "rob", "gun"],
    beats=[
        {"say": "Yep. That's him. You're probably wondering how he got here.", "delay": 0.9, "music_cut": True,
         "shots": [sh("w9", 12.75, dur=0.85, speed=0.4, **HIT), sh("w9", 13.1, freeze=True, **dict(HIT, zoom_to=1.28))],
         "sfx": [{"name": "record_scratch", "at": 0.85, "gain": 0.8}],
         "stickers": [dict(type="circle", src=[960, 360], src_r=95, at=0.95),
                      dict(type="arrow", **{"from": [300, 760]}, src=[900, 330], label="HIM", at=1.1)]},
        {"shots": [sh("w9", 13.1, dur=1.1, reverse=True, speed=9, fx={"rewind": True}, **HIT)],
         "sfx": [{"name": "rewind", "at": 0.0, "gain": 0.5}]},
        {"say": "So this guy runs up to Jason and asks where the nearest ATM is.",
         "shots": [sh("w9", 1.3, **DLG), sh("w9", 6.0, w=1.2, **DLG)]},
        {"say": "Then he goes for it.", "shots": [sh("w9", 7.62, dur=0.5, speed=0.5, **DLG), sh("w9", 7.87, freeze=True, **DLG)],
         "stickers": [bub("GIVE ME YOUR CASH!", 0.5, x=600, y=600, size=66, tail="left")],
         "sfx": [{"name": "dun_dun", "at": 0.5, "gain": 0.5}]},
        {"say": "Bro even asks: you don't see my gun? Jason: yeah, no.",
         "shots": [sh("w9", 8.12, dur=2.0, freeze=True, **DLG), sh("w9", 8.32, freeze=True, **DLG)],
         "stickers": [bub("YOU DON'T SEE MY GUN?", 0.0, dur=2.0, x=600, y=600, size=62, tail="left"),
                      bub("YEAH, NO.", 2.0, x=330, y=560, size=80, tail="left"),
                      dict(type="circle", src=[800, 285], src_r=62, at=2.2)],
         "sfx": [{"name": "bonk", "at": 2.05, "gain": 0.7}]},
        {"say": "Then Jason offers to beat him up, just to speed things up.",
         "shots": [sh("w9", 8.86, freeze=True, **DLG)],
         "stickers": [bub("IF I KICKED YOUR A**, WOULD THAT HURRY THIS ALONG?", 0.0, x=470, y=600, size=52, maxw=760, tail="left")]},
        {"say": "And the robber goes: you know what? You got a point. I'm just gonna go.",
         "shots": [sh("w9", 9.45, speed=0.62, **DLG)],
         "stickers": [bub("I'M JUST GONNA GO.", 1.6, x=600, y=600, size=66, tail="left")]},
        {"say": "He takes one step...", "music_cut": True, "shots": [sh("w9", 12.2, speed=0.4, **HIT)],
         "sfx": [{"name": "riser", "at": 0.0, "gain": 0.5, "kw": {"d": 1.2}}]},
        {"say": "and gets absolutely deleted by a guy on a scooter.", "delay": 0.35, "music_cut": True,
         "shots": [sh("w9", 12.72, dur=1.4, speed=0.3, **dict(HIT, zoom_to=1.4),
                      fx={"shake": [[0.3, 1.2, 34]], "flash": ["white", 0.3]})],
         "sfx": [{"name": "vine_boom", "at": 0.3, "gain": 0.9}],
         "stickers": [emo("💀", 0.35, x=840, y=760, size=240)]},
        {"min": 2.4, "shots": [sh("w9", 12.62, speed=0.25, x=0.62, y=0.42, zoom=2.0)],
         "sfx": [{"name": "shutter", "at": 0.0, "gain": 0.9}],
         "meme": [{"say": "Emotional damage.", "at": 0.9}],
         "stickers": [dict(type="rec", at=0.0), txt("CAUGHT IN 4K 📸", 0.1, font="Bangers", size=84, bg="#e01b1b", y=560, rot=-2),
                      txt("EMOTIONAL DAMAGE", 0.9, font="Anton", size=92, color="#fff", bg="#111", y=1180, rot=3, anim="slam")]},
        {"say": "And Jason had two hundred sixty-four bucks on him the whole time.",
         "shots": [sh("w9", 13.4, speed=0.4, **HIT)],
         "sfx": [{"name": "kaching", "at": 1.3, "gain": 0.7}],
         "stickers": [emo("💸", 1.3, x=820, y=720, size=210)]},
        {"say": "Would you have given him the money?", "pad": 0.6,
         "shots": [sh("w9", 14.6, freeze=True, **dict(HIT, zoom_to=1.3))],
         "stickers": [txt("WOULD YOU PAY? 👇", 0.2, font="Bangers", size=86, bg="#1565c0", y=960, rot=-3)]},
    ])

# 3. ---------------------------------------------------------------- BMX vs cops
BMX = dict(x=0.5, zoom=1.0)  # x 0.5 keeps the Reddit handle label out of the crop
job("meme_bmx", ["w9", "w10"], voice="am_puck", speed=1.05, music="phonk", music_volume=0.32, game_volume=0.8,
    hook="HE TOLD THE COPS ['YOU CAN'T CATCH ME'] 💀", credit="🎥 u/According-Amoeba-936 · via ReplayNext",
    keywords=["cops", "steals", "bmx"],
    beats=[
        # the BMX clip starts at 23.03 (before that is the end of the plane clip); slowed so it lasts the two lines
        {"say": "This man saw a cop car and chose violence.", "shots": [sh("w9", 23.08, speed=0.55, **dict(BMX, zoom_to=1.08))]},
        {"say": "He rides up on a BMX and yells:", "shots": [sh("w9", 24.4, speed=0.55, **BMX)]},
        {"min": 1.15, "shots": [sh("w9", 25.55, dur=1.15, **BMX)],
         "stickers": [bub("YOU CAN'T CATCH ME!", 0.2, dur=0.95, src=[582, 312], anchor="center", size=72, pad="22px 40px")]},
        {"say": "Two seconds later...", "shots": [sh("w9", 26.82, dur=2.2, speed=0.3, **dict(BMX, zoom_to=1.2),
                                                       fx={"shake": [[0.6, 1.8, 34]], "flash": ["white", 0.6]})],
         "sfx": [{"name": "vine_boom", "at": 0.6, "gain": 0.9}]},
        {"min": 2.3, "music_cut": True, "shots": [sh("w9", 27.45, freeze=True, fx={"sepia": True}, **dict(BMX, zoom=1.2, zoom_to=1.28))],
         "sfx": [{"name": "record_scratch", "at": 0.0, "gain": 0.8}, {"name": "sad_trombone", "at": 0.5, "gain": 0.6}],
         "meme": [{"say": "Bruh.", "at": 0.9}],
         "stickers": [dict(type="tbc", at=0.0)]},
        {"say": "But wait. It gets better.", "shots": [sh("w10", 0.2, x=0.5)]},
        {"say": "He gets up, walks over to the cop car...", "shots": [sh("w10", 1.4, x=0.5)]},
        {"say": "and just takes it.", "shots": [sh("w10", 3.8, x=0.5)],
         "sfx": [{"name": "vine_boom", "at": 0.5, "gain": 0.7}], "stickers": [emo("🗿", 0.5, x=800, y=700, size=230)]},
        {"min": 1.55, "shots": [sh("w10", 6.3, dur=1.55, x=0.5)],
         "stickers": [bub("SEE YOU LATER! 👋", 0.55, src=[595, 332], anchor="center", size=96, pad="30px 44px")]},
        {"say": "Technically... they really couldn't catch him.", "pad": 0.6, "shots": [sh("w10", 7.85, freeze=True, x=0.5)],
         "sfx": [{"name": "airhorn", "at": 0.1, "gain": 0.45}],
         "stickers": [txt("GTA 6 COPS 🤡", 0.0, src=[595, 332], font="Bangers", size=128, bg="#e01b1b", pad="18px 34px")]},
    ])

# 4. ---------------------------------------------------------------- the bird
job("meme_bird", ["w4"], voice="bm_george", speed=0.95, music="doc", music_volume=0.6, game_volume=0.5,
    hook="THIS BIRD [DESTROYED] HIS CAR 💀", credit="🎥 u/catchlight22 · via ReplayNext", keywords=["bird", "car"],
    beats=[
        {"say": "Leonida. A paradise of sun, sea, and birds.", "shots": [sh("w4", 6.9, speed=0.6, zoom=1.0, zoom_to=1.06)],
         "stickers": [txt("PLANET LEONIDA 🌴", 0.2, font="Anton", size=74, stroke=12, y=620)]},
        {"say": "Here we observe a man, peacefully driving across the bridge.", "shots": [sh("w4", 8.6, speed=0.37)]},
        {"say": "And then... the bird arrives.", "shots": [sh("w4", 11.45, speed=0.18)]},
        {"say": "With one gentle touch...", "music_cut": True,
         "shots": [sh("w4", 11.85, dur=1.0, speed=0.12), sh("w4", 11.95, freeze=True)]},
        {"say": "it flips the entire car.", "delay": 0.3, "music_cut": True,
         "shots": [sh("w4", 12.13, dur=1.1, speed=0.45, fx={"deepfry": [0.0, 0.6], "shake": [[0.0, 0.9, 40]], "flash": ["white", 0.0]})],
         "sfx": [{"name": "vine_boom", "at": 0.0, "gain": 0.9}], "stickers": [emo("💀", 0.1, x=820, y=720, size=250)]},
        {"min": 2.3, "shots": [sh("w4", 11.5, speed=0.15, x=0.55, y=0.42, zoom=1.5)],
         "meme": [{"say": "What the hell?", "at": 1.1}],
         "stickers": [txt("INSTANT REPLAY ⏪", 0.0, font="Bangers", size=80, bg="#111", y=560, rot=-2)]},
        {"say": "Nature is truly beautiful.", "shots": [sh("w4", 11.8, freeze=True, x=0.55, y=0.42, zoom=1.4, zoom_to=1.55)]},
        {"say": "Rockstar, why is the bird stronger than the car?", "pad": 0.6,
         "shots": [sh("w4", 11.8, freeze=True, x=0.55, y=0.42, zoom=1.55, zoom_to=1.65)],
         "sfx": [{"name": "vine_boom", "at": 0.1, "gain": 0.6}],
         "stickers": [txt("BIRDS ARE THE FINAL BOSS 🐦", 0.1, font="Bangers", size=84, bg="#1565c0", y=980, rot=-3, maxw=900)]},
    ])

# 5. ---------------------------------------------------------------- three pilots
P1 = dict(x=0.45, y=0.42, zoom=1.15)
job("meme_pilots", ["w6", "w8", "w9"], voice="am_puck", speed=1.05, music="phonk", music_volume=0.3, game_volume=0.75,
    hook="NEVER LET THEM [FLY] IN GTA 6 😭", credit="🎥 u/User88885 · u/RoaRos · u/Tubii · via ReplayNext",
    keywords=["truck", "cartwheel", "kamikaze"],
    beats=[
        {"say": "Three pilots. Zero skill.", "delay": 0.2,
         "shots": [sh("w8", 7.6, speed=0.5, x=0.55, zoom=1.15, fx={"flash": ["white", 0.3], "shake": [[0.3, 1.2, 30]]})],
         "sfx": [{"name": "vine_boom", "at": 0.3, "gain": 0.8}]},
        {"say": "Pilot number one is coming in for a landing.", "shots": [sh("w6", 7.9, **P1)],
         "stickers": [txt("PILOT #1", 0.1, font="Bangers", size=90, color="#FFE600", stroke=12, y=560, rot=-4)]},
        {"say": "Perfect landing...", "shots": [sh("w6", 10.0, speed=0.6, **P1)]},
        {"say": "right on top of a pickup truck.", "shots": [sh("w6", 10.7, speed=0.5, **dict(P1, zoom_to=1.35), fx={"shake": [[0.2, 1.0, 28]]})],
         "sfx": [{"name": "vine_boom", "at": 0.25, "gain": 0.8}], "stickers": [emo("🗿", 0.35, x=820, y=700, size=230)]},
        {"say": "His only comment? Hoo yeah.", "shots": [sh("w6", 13.3, **P1)]},
        {"say": "Pilot number two walks up to his plane...", "shots": [sh("w9", 15.15, x=0.45)],
         "stickers": [txt("PILOT #2", 0.1, font="Bangers", size=90, color="#FFE600", stroke=12, y=560, rot=3)]},
        {"say": "and it just leaves without him.", "shots": [sh("w9", 17.2, speed=0.8, x=0.42)]},
        {"say": "Runs somebody over, then does a cartwheel.",
         "shots": [sh("w9", 18.3, speed=0.55, x=0.4, fx={"shake": [[0.8, 1.6, 26]]})],
         "sfx": [{"name": "bonk", "at": 0.25, "gain": 0.8}, {"name": "vine_boom", "at": 1.25, "gain": 0.6}],
         "stickers": [emo("😭", 1.3, x=820, y=720, size=220)]},
        {"say": "And pilot number three is just flying a helicopter...", "shots": [sh("w8", 3.0, x=0.55)],
         "stickers": [txt("PILOT #3", 0.1, font="Bangers", size=90, color="#FFE600", stroke=12, y=560, rot=-3)]},
        {"say": "when another chopper goes full kamikaze.", "shots": [sh("w8", 7.35, speed=0.35, x=0.55, zoom=1.0, zoom_to=1.2)]},
        {"min": 2.6, "shots": [sh("w8", 8.0, speed=0.4, x=0.55, zoom=1.2,
                                 fx={"flash": ["white", 0.0], "shake": [[0.0, 1.2, 40]], "deepfry": [0.0, 0.5]})],
         "sfx": [{"name": "vine_boom", "at": 0.0, "gain": 0.9}],
         "meme": [{"say": "Mission failed. We'll get em next time.", "at": 0.5}],
         "stickers": [emo("💀", 0.1, x=820, y=720, size=250)]},
        {"say": "Which pilot was the worst? One, two, or three?", "pad": 0.6,
         "shots": [sh("w6", 11.5, freeze=True, x=0.48, y=0.6, zoom=1.15, zoom_to=1.25)],
         "stickers": [txt("1, 2 OR 3? 👇", 0.2, font="Bangers", size=96, bg="#e01b1b", y=980, rot=-3)]},
    ])
