#!/usr/bin/env python3
"""Dating series, batch 1: "GTA 6 didn't invent dating". Five shorts from San Andreas, GTA IV and GTA VI footage.

    python3 shorts/jobs/plan_dating_batch1.py UPLOADS_DIR SCRATCH_DIR
    python3 shorts/make_meme_short.py shorts/jobs/dating_invented.json   (and the other four)

Sources are 640x360, so the series uses the "wide" layout (1080x760) instead of a hard vertical crop.
Credits from the watermarks: d1, d11, d12 TheJizzy; d13 Stilefty; d22, d23 GTASeriesVideos; GTA VI clips unmarked.
SA clips (TheJizzy) carry background music, so their audio is muted; their commentary text sits in the top
34 px and is cropped away (zoom 1.12, y 0.55). The GTA IV clip has commentary and subtitles at the bottom,
cropped with zoom 1.2, y 0.415. Every claim in the narration is either shown on screen or stated in the
sources' own captions (6 girlfriends, Denise and Burning Desire, Katie the nurse who likes muscular men,
Barbara, Kiki slashing tires, Carmen's like values) or is visible GTA VI gameplay.
Kiki's first phone line contains slurs, so that shot is muted and shown as a bubble.
"""
import json
import sys
from pathlib import Path

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent
FILES = {"d1": "99b662a3-1", "d11": "a49ab43c-11", "d12": "f6d8b481-12", "d13": "87fd1aa7-13", "d22": "b66cafd5-22",
         "d23": "bdc5bad1-23", "d6": "25604d3b-6", "d61": "0ae9728f-61", "f1": "c3376b15-1"}
GAME = {"d1": "SA", "d11": "SA", "d12": "SA", "d13": "SA", "d22": "IV", "d23": "IV", "d6": "VI", "d61": "VI", "f1": "VI"}
MUTED = {"d1", "d11", "d12", "d23"}  # background music from the source channel, not game audio
FRAME = {"d1": dict(zoom=1.12, y=0.55), "d11": dict(zoom=1.12, y=0.55), "d12": dict(zoom=1.12, y=0.55),
         "d13": dict(zoom=1.08, y=0.53), "d22": dict(zoom=1.2, y=0.415), "d23": dict(zoom=1.0, x=0.45),
         "d6": dict(zoom=1.05), "d61": dict(zoom=1.05),
         "f1": dict(zoom=1.16, y=0.43)}  # f1: crop above the baked FAT/FIT labels, our own labels go on top
CHIPS = {"SA": {"text": "GTA San Andreas · 2004", "color": "#e8731a"},
         "IV": {"text": "GTA IV · 2008", "color": "#3d6fb5"},
         "VI": {"text": "GTA VI · 2026", "color": "#e6197a"}}
BASE = {"tts_model": f"{S}/tts/kokoro-v1.0.onnx", "tts_voices": f"{S}/tts/voices-v1.0.bin",
        "voice": "am_michael", "speed": 1.05, "meme_voice": "am_onyx", "meme_speed": 0.92,
        "layout": "wide", "chips": CHIPS, "caption_font": "Titan One", "caption_size": 88, "caption_y": 1395,
        "game_volume": 1.0}
TOP = 600  # sticker line near the top of the frame (frame spans y 470..1230)


def sh(src, t, **kw):
    d = dict(FRAME[src], src=src, t=t, chip=GAME[src])
    if src in MUTED:
        d["mute"] = True
    d.update(kw)
    return d


def txt(text, at=0.0, **kw):
    return dict(type="text", text=text, at=at, **kw)


def emo(e, at=0.0, **kw):
    return dict(type="emoji", emoji=e, at=at, **kw)


def bub(text, at=0.0, **kw):
    return dict(type="bubble", text=text, at=at, **kw)


def job(name, hook, credit, music, music_volume, beats, keywords=(), **kw):
    used = sorted({s["src"] for b in beats for s in b["shots"]})
    j = dict(BASE, out=f"{S}/dating/out/{name}.mp4", work=f"{S}/dating/work_{name}", hook=hook, credit=credit,
             music=music, music_volume=music_volume, keywords=list(keywords), beats=beats,
             sources={k: {"path": f"{U}/{FILES[k]}.mkv"} for k in used}, **kw)
    (HERE / f"{name}.json").write_text(json.dumps(j, ensure_ascii=False, indent=1))
    print(name, len(beats), "beats,", sum(len(b.get("say", "").split()) for b in beats), "words")


# 1 ---------------------------------------------------------------- overview
job("dating_invented", "GTA 6 DIDN'T [INVENT] DATING 😤", "🎥 SA: TheJizzy, Stilefty · IV: GTASeriesVideos", "doc", 0.55,
    keywords=["wrong", "six", "kiki", "tires"],
    beats=[
        {"say": "Everyone says GTA 6 invented dating.", "delay": 0.2,
         "shots": [sh("d6", 31.0, zoom=1.15, zoom_to=1.05, ease="punch")]},
        {"say": "Wrong. Back in 2004, CJ already had six girlfriends.",
         "shots": [sh("d11", 18.9, speed=0.8)],
         "sfx": [{"name": "record_scratch", "at": 0.0, "gain": 0.8}],
         "stickers": [txt("6 GIRLFRIENDS 😳", 1.4, y=TOP, font="Bangers", size=92, bg="#e8731a", rot=-3)]},
        {"say": "He took them out to dinner,", "shots": [sh("d11", 25.3, speed=0.8)]},
        {"say": "to the bar,", "shots": [sh("d13", 10.0)]},
        {"say": "and one of them was a nurse who only dated muscular guys.", "shots": [sh("d12", 31.0, speed=0.9)],
         "stickers": [emo("💪", 1.6, x=860, y=780, size=200)]},
        {"say": "In 2008, Niko was dating girls he met online.", "shots": [sh("d22", 1.6)]},
        {"say": "And if he cheated, his girlfriend Kiki slashed his tires.",
         "shots": [sh("d22", 82.0, w=1.3), sh("d22", 106.6, speed=0.7, zoom=1.35, zoom_to=1.5, x=0.6, y=0.49)],
         "sfx": [{"name": "vine_boom", "at": 2.1, "gain": 0.8}],
         "stickers": [emo("💀", 2.2, x=860, y=760, size=210)]},
        {"say": "GTA 6 just made your girlfriend a main character.", "shots": [sh("d61", 67.5)]},
        {"say": "So who had the best dating? San Andreas, 4, or 6?", "pad": 0.7,
         "shots": [sh("d6", 112.0, speed=0.8, zoom=1.05, zoom_to=1.12)],
         "stickers": [txt("SA, IV OR VI? 👇", 0.2, y=TOP, font="Bangers", size=96, bg="#e6197a", rot=-3)]},
    ])

# 2 ---------------------------------------------------------------- Denise
job("dating_denise", "HE BURNED HER HOUSE DOWN... THEN [DATED] HER 💀", "🎥 TheJizzy · Stilefty", "pizz", 0.45,
    keywords=["burning", "fire", "denise"],
    beats=[
        {"say": "CJ met his first girlfriend by setting her house on fire.", "delay": 0.25,
         "shots": [sh("d1", 32.5, zoom=1.25, zoom_to=1.12, ease="punch", fx={"flash": ["white", 0.0], "shake": [[0.0, 0.6, 26]]})],
         "sfx": [{"name": "vine_boom", "at": 0.0, "gain": 0.8}]},
        {"say": "A corrupt cop, Frank Tenpenny, ordered him to burn a house down.", "shots": [sh("d1", 15.4, speed=0.9)]},
        {"say": "So he did.", "shots": [sh("d1", 24.4)], "sfx": [{"name": "whoosh", "at": 0.0, "gain": 0.7}],
         "meme": [{"say": "Bro.", "at": 1.0}]},
        {"say": "Then he heard a woman screaming inside.", "music_cut": True, "shots": [sh("d1", 30.4, speed=0.85)],
         "sfx": [{"name": "heartbeat", "at": 0.2, "gain": 0.55, "kw": {"bpm": 96, "beats": 3}}]},
        {"say": "He ran into the fire and got her out.", "shots": [sh("d1", 36.0)],
         "sfx": [{"name": "riser", "at": 0.0, "gain": 0.45, "kw": {"d": 1.4}}]},
        {"say": "Her name was Denise.", "shots": [sh("d13", 10.1, zoom=1.15)],
         "stickers": [txt("DENISE ❤️", 0.3, y=TOP, font="Bangers", size=96, bg="#c2185b", rot=-3)],
         "sfx": [{"name": "ding", "at": 0.3, "gain": 0.5}]},
        {"say": "And she became his girlfriend. First date? A bar.", "shots": [sh("d13", 13.6), sh("d13", 17.6)],
         "meme": [{"say": "Smooth.", "at": 3.2}]},
        {"say": "Worst way to meet your girlfriend in GTA history?", "pad": 0.7,
         "shots": [sh("d1", 41.0, freeze=True, zoom=1.12, zoom_to=1.2)],
         "stickers": [txt("WORST FIRST MEETING? 👇", 0.2, y=TOP, font="Bangers", size=88, bg="#e8731a", rot=-3, maxw=980)]},
    ])

# 3 ---------------------------------------------------------------- Kiki
TIRE = dict(zoom=1.35, x=0.6, y=0.49)  # window ends at y 310, above the burned-in subtitles
job("dating_kiki", "GTA 4 HAD THE MOST [TOXIC] GIRLFRIEND 💀", "🎥 footage: GTASeriesVideos", "horror", 0.6,
    keywords=["kiki", "tires", "slashed"],
    beats=[
        {"say": "She slashed his tires.", "delay": 0.9,
         "shots": [sh("d22", 106.8, dur=0.9, speed=0.5, **TIRE), sh("d22", 107.25, freeze=True, **dict(TIRE, zoom_to=1.45))],
         # the scratch ends before the first word, otherwise it masks the "Sh" of "She"
         "sfx": [{"name": "record_scratch", "at": 0.3, "gain": 0.6}],
         "stickers": [dict(type="circle", at=1.0, x=650, y=1112, r=150)]},
        {"shots": [sh("d22", 107.25, dur=0.9, reverse=True, speed=9, fx={"rewind": True}, **TIRE)],
         "sfx": [{"name": "rewind", "at": 0.0, "gain": 0.5}]},
        {"say": "Niko takes Alex out to dinner.", "shots": [sh("d22", 1.5)]},
        {"say": "Then he drives her home.", "shots": [sh("d22", 56.0)]},
        {"say": "But Niko already has a girlfriend. Kiki.", "shots": [sh("d22", 82.0)],
         "stickers": [txt("KIKI 😡", 1.8, y=TOP, font="Bangers", size=96, bg="#b71c1c", rot=-3)]},
        {"min": 3.4, "shots": [sh("d22", 92.6, mute=True)],
         "sfx": [{"name": "dun_dun", "at": 0.1, "gain": 0.55}],
         "stickers": [bub("📱 KIKI: I'M WATCHING YOU, NIKO 👀", 0.2, x=540, y=650, size=58, maxw=900)]},
        {"min": 3.9, "shots": [sh("d22", 97.0)],
         "stickers": [bub("NIKO: TAKE SOME PILLS, HAVE A HOT BATH AND CHILL OUT", 0.2, x=540, y=660, size=50, maxw=900)]},
        {"min": 5.1, "shots": [sh("d22", 101.4)],
         "stickers": [bub("📱 KIKI: WHAT WE HAVE IS SACRED, NIKO.", 0.3, x=540, y=650, size=56, maxw=900)]},
        {"say": "Then he finds his tire slashed.", "music_cut": True,
         "shots": [sh("d22", 106.6, speed=0.6, **dict(TIRE, zoom_to=1.5), fx={"shake": [[0.9, 1.6, 22]]})],
         "sfx": [{"name": "vine_boom", "at": 0.9, "gain": 0.85}],
         "meme": [{"say": "Red flag.", "at": 2.0}],
         "stickers": [emo("🚩", 1.0, x=880, y=760, size=200)]},
        {"say": "Jealous girlfriends were already in GTA 4. Back in 2008.", "shots": [sh("d22", 113.6)]},
        {"say": "Would you date Kiki?", "pad": 0.7, "shots": [sh("d22", 118.0, freeze=True)],
         "stickers": [txt("WOULD YOU DATE KIKI? 👇", 0.2, y=TOP, font="Bangers", size=90, bg="#3d6fb5", rot=-3, maxw=980)]},
    ])

# 4 ---------------------------------------------------------------- date night in GTA VI
job("dating_gta6_date", "DATE NIGHT IN [GTA 6] BE LIKE 💀", "", "phonk", 0.32,
    keywords=["step", "wanted"],
    beats=[
        {"min": 1.3, "shots": [sh("d61", 105.4, mute=True, fx={"shake": [[0.0, 1.0, 30]], "flash": ["white", 0.0]})],
         "sfx": [{"name": "vine_boom", "at": 0.0, "gain": 0.8}], "stickers": [emo("💀", 0.1, x=860, y=760, size=210)]},
        {"shots": [sh("d61", 105.4, dur=0.8, reverse=True, speed=10, mute=True, fx={"rewind": True})],
         "sfx": [{"name": "rewind", "at": 0.0, "gain": 0.5}]},
        {"say": "Step one: go shoe shopping together.", "shots": [sh("d61", 27.0), sh("d61", 37.6)],
         "stickers": [txt("STEP 1 👟", 0.0, y=TOP, font="Bangers", size=92, bg="#e6197a", rot=-3)]},
        {"say": "Step two: hold hands.", "shots": [sh("d6", 46.8, zoom=1.18)],
         "stickers": [txt("STEP 2 🤝", 0.0, y=TOP, font="Bangers", size=92, bg="#e6197a", rot=3)]},
        {"say": "Step three: fight a random guy.", "shots": [sh("d61", 99.6, mute=True, fx={"shake": [[1.0, 1.8, 24]]})],
         "sfx": [{"name": "bonk", "at": 1.1, "gain": 0.8}],
         "stickers": [txt("STEP 3 👊", 0.0, y=TOP, font="Bangers", size=92, bg="#e6197a", rot=-3)]},
        {"min": 2.6, "shots": [sh("d61", 116.9)],
         "stickers": [bub("WELL, THAT WAS FUN.", 0.35, x=540, y=650, size=66), bub("AGAIN!", 1.75, x=700, y=820, size=80)]},
        {"say": "Step four: become wanted together.", "shots": [sh("d61", 124.0)],
         "stickers": [txt("STEP 4 🚨", 0.0, y=TOP, font="Bangers", size=92, bg="#e6197a", rot=3)]},
        {"min": 6.3, "shots": [sh("d61", 126.4, dur=4.2), sh("d61", 140.6)],
         "stickers": [txt("📻 POLICE RADIO", 0.1, y=TOP, font="Anton", size=64, bg="#111", rot=-2)]},
        {"say": "Step five: steal a lowrider and drive into the sunset.", "shots": [sh("d61", 155.0, mute=True)],
         "stickers": [txt("STEP 5 🚗", 0.0, y=TOP, font="Bangers", size=92, bg="#e6197a", rot=-3)]},
        {"say": "Is this couple goals, or a red flag?", "pad": 0.7, "shots": [sh("d6", 112.0, freeze=True, zoom=1.05, zoom_to=1.12)],
         "stickers": [txt("COUPLE GOALS OR 🚩? 👇", 0.2, y=TOP, font="Bangers", size=90, bg="#111", rot=-3, maxw=980)]},
    ])

# 5 ---------------------------------------------------------------- standards
CARD = dict(zoom=1.0, x=0.42)
FATFIT = [txt("FAT 🍔", 0.0, x=270, y=1150, font="Bangers", size=72, bg="#d81b1b", anim="none"),
          txt("FIT 💪", 0.0, x=810, y=1150, font="Bangers", size=72, bg="#18a84a", anim="none")]
job("dating_standards", "GTA GIRLFRIENDS HAD [STANDARDS] 😭", "🎥 SA: TheJizzy · IV: GTASeriesVideos", "doc", 0.55,
    keywords=["muscular", "gym", "calories"],
    beats=[
        {"say": "In San Andreas, some girlfriends had standards.", "delay": 0.2,
         "shots": [sh("d12", 30.2, zoom=1.2, zoom_to=1.12, ease="punch")]},
        {"say": "Katie, a nurse in San Fierro, only liked muscular guys.", "shots": [sh("d12", 36.0, speed=0.9)],
         "stickers": [txt("💪 MUSCLES REQUIRED", 1.6, y=TOP, font="Bangers", size=86, bg="#e8731a", rot=-3)]},
        {"say": "So you hit the gym before asking her out.", "shots": [sh("d12", 47.5, speed=0.9)],
         "meme": [{"say": "Light weight, baby!", "at": 2.4}]},
        {"say": "In GTA 4, every girlfriend rated every bar, restaurant, and activity.", "shots": [sh("d23", 0.4, **CARD)]},
        {"say": "Carmen liked darts eighty percent, but Burger Shot only fifty.",
         "shots": [sh("d23", 3.4, freeze=True, **CARD)],
         "stickers": [dict(type="circle", at=0.4, src=[110, 121], src_r=48), dict(type="circle", at=2.3, src=[112, 242], src_r=58)]},
        {"say": "And now GTA 6 counts your calories.", "shots": [sh("f1", 25.5)], "sfx": [{"name": "ding", "at": 1.4, "gain": 0.5}],
         "stickers": FATFIT},
        {"say": "Rockstar has been judging your body since 2004.", "shots": [sh("f1", 3.4)], "stickers": FATFIT},
        {"say": "Gym, or Cluckin' Bell?", "pad": 0.7, "shots": [sh("d12", 40.0, freeze=True, zoom=1.12, zoom_to=1.2)],
         "stickers": [txt("GYM 💪 OR CLUCKIN' BELL 🍗? 👇", 0.2, y=TOP, font="Bangers", size=80, bg="#e8731a", rot=-3, maxw=990)]},
    ])
