#!/usr/bin/env python3
"""Long video: "GTA 6 didn't invent dating, here's the proof". San Andreas (2004), GTA IV (2008), GTA V (2013), GTA VI.

    python3 shorts/jobs/plan_dating_long.py UPLOADS_DIR SCRATCH_DIR
    python3 shorts/make_longform.py shorts/jobs/longform_dating.json

Every claim is either shown in the footage, stated in the source channels' own captions, or a well documented
fact about the games (SA's Hot Coffee re-rating, the girlfriend perks, Michelle being an agent, GTA V having no
dating). The "listen" sentences play the games' own dialogue with yellow subtitles; their texts come from the
on-screen game subtitles where visible, otherwise from Whisper.
Credits from the watermarks: d1, d11, d12 TheJizzy; d13 Stilefty; d22, d23 GTASeriesVideos; GTA V clips from the
GTA 5 vs 6 comparisons; GTA VI clips unmarked.
"""
import json
import sys
from pathlib import Path

U, S = sys.argv[1], sys.argv[2]
HERE = Path(__file__).resolve().parent
SA, IV, V5, VI = "GTA SAN ANDREAS · 2004", "GTA IV · 2008", "GTA V · 2013", "GTA VI · 2026"


def scenes(cuts, end, skip=()):
    pts = list(cuts) + [end]
    out = []
    for a, b in zip(pts, pts[1:]):
        a, b = a + 0.05, b - 0.05
        for s0, s1 in skip:
            if a < s1 and b > s0:
                if a < s0 and s0 - a > 0.3:
                    out.append([round(a, 2), round(s0, 2), None])
                a = max(a, s1)
        if b - a > 0.3:
            out.append([round(a, 2), round(b, 2), None])
    return out


SACROP = [32, 36, 576, 324]  # drops the channel's commentary line at the top
SOURCES = {
    "d1": {"path": f"{U}/99b662a3-1.mkv", "crop": SACROP, "mute": True, "scenes": scenes([0, 40.6], 46.2)},
    "d11": {"path": f"{U}/a49ab43c-11.mkv", "crop": SACROP, "mute": True,
            "scenes": scenes([0, 12.8, 15.5, 16.2, 18.8, 21.6, 25.2, 30.1, 32.8, 33.8, 44.1], 51.1)},
    "d12": {"path": f"{U}/f6d8b481-12.mkv", "crop": SACROP, "mute": True,
            "scenes": scenes([0, 7.1, 11.2, 11.9, 46.7], 62.1, skip=[(7.1, 11.9)])},
    "d13": {"path": f"{U}/87fd1aa7-13.mkv", "scenes": scenes([0, 7.3, 8.1, 9.8, 13.4, 17.3, 22.0], 30.4, skip=[(7.3, 8.1), (17.3, 22.0)])},
    "d22": {"path": f"{U}/b66cafd5-22.mkv", "crop": [53, 0, 533, 300],  # drops the commentary and subtitles at the bottom
            "scenes": scenes([0, 0.9, 17.8, 18.7, 54.1, 69.0, 71.8, 80.4, 142.5, 144.3, 152.7, 157.1, 177.0, 182.3, 185.8, 187.4, 188.3],
                             192.0, skip=[(69.0, 80.4), (139.0, 144.3), (157.1, 177.0)])},
    "d23": {"path": f"{U}/bdc5bad1-23.mkv", "mute": True,
            "scenes": scenes([0, 7.0, 7.6, 15.5, 19.2, 23.9, 29.4, 32.5, 39.1, 41.6, 43.9, 51.6, 64.4], 69.4, skip=[(53.3, 60.6)])},
    "d6": {"path": f"{U}/25604d3b-6.mkv",
           "scenes": scenes([0, 5.1, 20.3, 30.4, 40.5, 50.7, 55.7, 166.1], 182.8, skip=[(86.0, 98.5), (160.2, 182.8)])},
    "d61": {"path": f"{U}/0ae9728f-61.mkv",
            "scenes": scenes([0, 5.1, 26.2, 34.1, 36.8, 41.9, 65.9, 86.1, 111.5, 122.4, 123.5], 182.4)},
    "f1": {"path": f"{U}/c3376b15-1.mkv", "mute": True, "scenes": scenes([0, 3.03, 9.40, 14.87, 19.87, 24.87, 29.87, 34.87], 36.0)},
    "h10": {"path": f"{U}/92941a1b-10.mkv", "mute": True, "scenes": scenes([42.01, 50.75], 50.75)},
    "c7": {"path": f"{U}/d1349b1f-7.mkv", "scenes": [[5.7, 16.25, None], [31.3, 44.55, None]]},
    "c9": {"path": f"{U}/bb1f6490-9.mkv", "scenes": [[0.0, 14.85, None], [35.5, 65.1, None]]},
    "c10": {"path": f"{U}/f6ce6b2c-10.mkv", "scenes": [[23.0, 39.75, None], [50.4, 61.55, None]]},
    "c11": {"path": f"{U}/9e6094d9-11.mkv", "scenes": [[12.3, 41.85, None]]},
}


def sh(src, t, label=None, **kw):
    d = dict(src=src, t=t, **kw)
    if label:
        d["label"] = label
    return d


def card(k, title, bg, t, **kw):
    return dict(card=k, title=title, bg=bg, t=t, **kw)


def listen(src, a, b, label, subs):
    return {"listen": [src, a, b], "label": label, "subs": subs}


EYEFIND, LOVE, AD, PHOTO = [70, 30, 480, 270], [300, 60, 320, 180], [80, 50, 400, 225], [120, 40, 320, 180]
TIRE, HANDS = [287, 120, 320, 180], [320, 180, 320, 180]
CARMEN = [12, 0, 456, 256]  # her likes card: full name, darts, bars, Burger Shot 50%

P = [
    # hook
    [("Ever since GTA 6 came out, I keep seeing the same comment.", [sh("d6", 45.0, VI)]),
     ("Rockstar finally added dating. A girlfriend, romance, a couple at the center of the story.",
      [sh("d6", 1.0, VI), sh("d61", 67.5, VI)]),
     ("Something GTA has never done before.", [sh("d61", 6.0, VI)]),
     ("Except it has.", [sh("d1", 32.0, SA, boom=0.15)]),
     ("Dating in GTA is twenty two years old.", [card("THE PROOF", "DATING IN GTA|IS 22 YEARS OLD", "d11", 26)]),
     ("In this video, I'll show you all of it: San Andreas, GTA 4, and why so many people think it's brand new.",
      [sh("d13", 1.5, SA), sh("d22", 9.0, IV), sh("d6", 24.0, VI)])],
    # San Andreas
    [("Let's go back to 2004.", [card("2004", "GTA SAN ANDREAS", "d1", 24)]),
     ("Grand Theft Auto San Andreas gave CJ six girlfriends.", [sh("d11", 16.3, SA), sh("d11", 18.9, SA)]),
     ("Two of them are part of the story. The other four, you meet out in the world.",
      [sh("d12", 28.0, SA), sh("d12", 21.0, SA)]),
     ("And he meets the first one, Denise, in the worst way possible.", [sh("d1", 2.0, SA)]),
     ("A corrupt cop, Frank Tenpenny, orders CJ to burn down a house.", [sh("d1", 12.5, SA)]),
     ("When the house is already on fire, he hears a woman screaming inside.", [sh("d1", 23.5, SA, speed=0.85)]),
     ("So he runs back into the fire and gets her out.", [sh("d1", 34.5, SA)]),
     ("That's Denise. And she becomes his girlfriend.", [sh("d13", 10.0, SA)]),
     ("And this wasn't just a cutscene. Dating was a whole system.", [sh("d13", 13.5, SA, speed=0.9)]),
     ("You picked her up, took her out to eat or for a drink, and drove her home.",
      [sh("d11", 22.0, SA), sh("d11", 30.3, SA), sh("d13", 23.5, SA)]),
     ("Every good date filled up her progress bar. Ignore her for too long, and it started to drop.",
      [sh("d11", 25.5, SA), sh("d11", 34.0, SA)]),
     ("Some girlfriends were picky.", [sh("d12", 31.5, SA)]),
     ("Katie, a nurse in San Fierro, only liked muscular guys, so you'd hit the gym before you even asked her out.",
      [sh("d12", 35.5, SA), sh("d12", 41.0, SA)]),
     ("And dating her paid off. If CJ got wasted, he kept all his weapons.", [sh("d12", 48.0, SA), sh("d12", 55.5, SA)]),
     ("Barbara, in El Quebrados, did the same for when he got busted.", [sh("d11", 38.5, SA), sh("d11", 46.5, SA)]),
     ("Dating in San Andreas even caused the biggest scandal in GTA history.",
      [card("2005", "THE HOT COFFEE|SCANDAL", "d13", 12, boom=0.1)]),
     ("In 2005, a mod unlocked a hidden minigame left in the game's code, and San Andreas got re-rated Adults Only and pulled from store shelves.",
      [sh("d11", 4.0, SA), sh("d12", 1.0, SA)]),
     ("That was twenty one years before GTA 6.", [sh("d1", 41.0, SA)])],
    # GTA IV
    [("Four years later, GTA 4 took dating online.", [card("2008", "GTA IV|ONLINE DATING", "d22", 147)]),
     ("Niko Bellic found three of his girlfriends on dating sites inside the game.",
      [sh("d22", 145.0, IV, crop=EYEFIND), sh("d22", 148.5, IV, crop=LOVE)]),
     ("Alex posted an ad on the in-game craplist: party girl seeks man for fun and blog material.",
      [sh("d22", 153.0, IV, crop=EYEFIND), sh("d22", 177.4, IV, crop=AD, w=1.4)]),
     ("And yes, she really did keep a blog.", [sh("d22", 188.4, IV, crop=PHOTO)]),
     ("Their first date: a diner.", [sh("d22", 12.0, IV)]),
     listen("d22", 1.3, 6.3, IV, [[1.38, 2.9, "ALEX: Let's eat here."],
                                  [2.96, 6.1, "ALEX: It's not exactly going to be a gastronomic rollercoaster, though, is it?"]]),
     ("On the drive home, they talk about her blog.", [sh("d22", 24.0, IV)]),
     listen("d22", 35.4, 47.45, IV, [[35.62, 39.2, "NIKO: So, this blog you write, is that all you want to do?"],
                                     [39.5, 41.8, "ALEX: God, I've never thought of it that way."],
                                     [42.2, 44.45, "ALEX: I've never thought that writing my blog was doing something."],
                                     [44.74, 47.35, "ALEX: It's just an extension of my personality. I'm creative."]]),
     ("And if the date went well, Niko could ask to come in.", [sh("d22", 19.2, IV)]),
     listen("d22", 56.7, 59.85, IV, [[56.82, 58.65, "NIKO: You want me to come in?"], [58.84, 59.75, "ALEX: I'd like that, Niko."]]),
     ("Every girlfriend had her own taste.", [sh("d23", 0.4, IV)]),
     ("Carmen, a nurse, loved bars and darts, but gave Burger Shot only fifty percent.",
      [sh("d23", 3.3, IV, crop=CARMEN, repeat=True)]),
     ("She even cared about what Niko was wearing.", [sh("d23", 9.0, IV), sh("d23", 25.0, IV)]),
     ("And girlfriends came with perks.", [sh("d23", 33.0, IV)]),
     ("Carmen could heal Niko over the phone. Kiki could make his wanted level disappear. And Alex got him half price on clothes.",
      [sh("d23", 44.5, IV), sh("d23", 16.0, IV), sh("d23", 20.0, IV)]),
     ("But dating in GTA 4 had a dark side, and her name was Kiki.", [sh("d22", 80.5, IV, mute=True)]),
     ("Kiki is a lawyer, and she's the jealous type.", [sh("d22", 85.3, IV, mute=True)]),
     ("Date another girl, and she shows up, calls, or texts Niko that she saw him with someone else.",
      [sh("d22", 88.6, IV, mute=True)]),
     listen("d22", 96.95, 108.7, IV, [[97.16, 102.2, "NIKO: You're seeing things, Kiki. Take some pills, have a hot bath and chill out."],
                                      [102.5, 108.6, "KIKI: What we have is sacred, Niko. Do you know what happens to those who piss on something sacred?"]]),
     ("Then he finds his tire slashed.", [sh("d22", 108.8, IV, crop=TIRE, boom=0.4)]),
     ("Jealousy, stalking, revenge. In 2008.", [sh("d22", 116.0, IV)]),
     ("And Niko's very first girlfriend, Michelle, turned out to be an undercover government agent.",
      [card("PLOT TWIST", "HIS FIRST GIRLFRIEND|WAS AN AGENT", "d22", 60)])],
    # GTA V
    [("So where did dating go?", [card("2013", "GTA V|NO DATING", "c9", 50)]),
     ("GTA 5 dropped it. Three main characters, and no dating system for any of them.",
      [sh("c9", 40.0, V5), sh("c10", 26.0, V5)]),
     ("And for millions of players, GTA 5 was their first GTA.", [sh("c11", 20.0, V5)]),
     ("They played it for thirteen years.", [sh("c7", 8.0, V5)]),
     ("So when GTA 6 put a couple at the center of the story, it looked like something brand new.",
      [sh("d6", 10.0, VI), sh("d6", 34.0, VI)])],
    # GTA VI
    [("And to be fair, GTA 6 really does change something.", [card("2026", "GTA VI|THE COUPLE IS THE STORY", "d6", 120)]),
     ("Your girlfriend isn't a side activity anymore. Lucia is one of the two main characters.",
      [sh("h10", 45.4, VI), sh("d61", 45.5, VI)]),
     ("There's literally a button to hold her hand.", [sh("d6", 29.0, VI, crop=HANDS)]),
     ("You walk around Vice City as a couple,", [sh("d6", 46.0, VI, repeat=True)]),
     ("and people notice.", [sh("d6", 57.6, VI)]),
     listen("d6", 59.9, 62.4, VI, [[60.24, 62.25, "STRANGER: Hey, you two. Looking good."]]),
     ("They even talk about their future.", [sh("d6", 126.5, VI)]),
     listen("d6", 133.3, 146.7, VI, [[133.6, 138.3, "LUCIA: Yo, wherever we end up, there's gotta be a beach."],
                                     [138.8, 139.3, "JASON: Oh, yeah?"],
                                     [139.9, 144.3, "LUCIA: Mm-hmm. No moving me to some cattle ranch in the middle of the country."],
                                     [144.8, 146.6, "LUCIA: I need sun and sand."]]),
     ("They go shopping together.", [sh("d61", 27.0, VI), sh("d61", 38.0, VI)]),
     ("They get into fights together.", [sh("d61", 99.5, VI, mute=True)]),
     listen("d61", 117.45, 119.3, VI, [[117.66, 118.5, "That was fun."], [118.7, 119.25, "Again!"]]),
     ("And the cops look for them together.", [sh("d61", 123.6, VI)]),
     listen("d61", 126.2, 132.5, VI, [[126.3, 128.95, "POLICE RADIO: Getting reports of an assault in Ocean Beach."],
                                      [130.5, 132.45, "POLICE RADIO: Be advised, we have two suspects."]]),
     listen("d61", 141.6, 146.45, VI, [[141.74, 144.6, "POLICE RADIO: Our second suspect is in their 20s, a Latina female."],
                                       [145.3, 146.35, "POLICE RADIO: They have long brown hair."]]),
     ("That's the real change. In GTA 6, your girlfriend is your partner in crime.", [sh("d61", 160.0, VI, mute=True)]),
     ("And the body system? That's old news too.", [sh("f1", 25.5, VI)]),
     ("GTA 6 tracks weight, calories and muscle, but CJ was getting fat on Cluckin' Bell and buff at the gym back in 2004.",
      [sh("f1", 3.4, VI), sh("d11", 8.0, SA)])],
    # verdict
    [("So, did GTA 6 invent dating?", [sh("d6", 100.0, VI)]),
     ("No. San Andreas did it in 2004, with six girlfriends, real perks, and a real scandal.", [sh("d13", 26.5, SA)]),
     ("GTA 4 put dating online, gave every girlfriend her own taste, and gave us a girlfriend who slashes your tires.",
      [sh("d22", 128.0, IV), sh("d22", 63.0, IV)]),
     ("What GTA 6 actually changed is who your girlfriend is. Not a side quest, but the other half of the story.",
      [sh("d6", 151.0, VI), sh("d6", 156.5, VI)]),
     ("Which GTA had the best relationships? San Andreas, 4, or 6? Tell me in the comments.",
      [card("YOUR TURN", "SA, IV OR VI?", "d6", 145)]),
     ("And subscribe for more GTA history like this.", [card("SUBSCRIBE", "MORE GTA HISTORY", "d61", 165)]),
     ("See you in Leonida.", [])],
]

paragraphs = []
for par in P:
    sents = []
    for item in par:
        if isinstance(item, dict):
            sents.append(item)
        else:
            text, shots = item
            sents.append({"text": text, "shots": shots})
    paragraphs.append({"sentences": sents})

job = {"out": f"{S}/dating/out/gta_dating_long.mp4", "work": f"{S}/dating/work_long",
       "voice": "am_michael", "speed": 1.0, "tts_model": f"{S}/tts/kokoro-v1.0.onnx", "tts_voices": f"{S}/tts/voices-v1.0.bin",
       "music": "doc", "music_volume": 1.0, "sources": SOURCES, "paragraphs": paragraphs}
(HERE / "longform_dating.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
words = sum(len(s.get("text", "").split()) for p in paragraphs for s in p["sentences"])
print(f"{sum(len(p['sentences']) for p in paragraphs)} sentences, {words} words")
