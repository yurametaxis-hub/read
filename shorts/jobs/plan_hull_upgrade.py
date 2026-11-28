#!/usr/bin/env python3
"""Hull City fan upgrades (FC 27 cards), make_card_upgrade.py job. usage: plan_hull_upgrade.py SCRATCHPAD

Current cards are copied from the FUTBIN screenshots the client sent (28 Nov 2026). The upgrades are a fan take,
sized by 2026/27 form as found on 28 Nov 2026: Tzolakis MOTM with a clean sheet in the 2-0 over Man United and
9 saves at Arsenal, Mendy scored in that 2-0, McBurnie 17 goals and 7 assists in the 2025/26 promotion season
(the client wanted him to get the biggest jump), Butland no PL minutes yet, Morita back from a groin injury,
Iroegbunam signed from Everton and back from injuries, Norton-Cuffy barely played, Thomas 1 assist in 5 games.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
S = sys.argv[1]
CUT = f"{S}/hull/cut"
ENG = "\U0001F3F4\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F"
SCO = "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F"
WAL = "\U0001F3F4\U000E0067\U000E0062\U000E0077\U000E006C\U000E0073\U000E007F"
GRE, JPN, SEN = "\U0001F1EC\U0001F1F7", "\U0001F1EF\U0001F1F5", "\U0001F1F8\U0001F1F3"


def pl(name, photo, flag, pos, old, new, size, *reasons, gk=False):
    return {"name": name, "photo": f"{CUT}/{photo}.png", "flag": flag, "pos": pos, "gk": gk,
            "old": {"ovr": old[0], "stats": old[1:]}, "new": {"ovr": new[0], "stats": new[1:]}, "size": size,
            "reasons": [{"text": r[1:], "after": True} if r.startswith(">") else {"text": r} for r in reasons]}


players = [
    pl("BUTLAND", "butland", ENG, "GK", [75, 76, 74, 72, 76, 49, 75], [77, 78, 76, 73, 78, 49, 77], "small",
       "[0] Premier League minutes this season", ">+2 just for patience \U0001F605", gk=True),
    pl("MORITA", "morita", JPN, "CM", [78, 68, 71, 75, 78, 72, 78], [80, 69, 72, 78, 80, 74, 79], "small",
       "Back from a [groin injury]"),
    pl("NORTON-CUFFY", "nortoncuffy", ENG, "RB", [75, 82, 49, 66, 75, 70, 68], [78, 85, 50, 69, 77, 74, 70], "small",
       "[22] years old with [82] pace already"),
    pl("IROEGBUNAM", "iroegbunam", ENG, "CDM", [76, 65, 58, 68, 74, 75, 72], [79, 66, 60, 71, 76, 79, 75], "small",
       "Signed from [Everton], fit again"),
    pl("THOMAS", "thomas", WAL, "LM", [75, 87, 71, 74, 73, 48, 70], [78, 88, 72, 78, 76, 49, 71], "small",
       "[1] assist in his first [5] PL games"),
    pl("MENDY", "mendy", SEN, "CB", [75, 80, 46, 58, 62, 73, 82], [81, 82, 55, 62, 65, 80, 85], "big",
       "A centre-back who [scored]", "in the [2-0] win over [Man United]"),
    pl("TZOLAKIS", "tzolakis", GRE, "GK", [79, 78, 76, 76, 83, 54, 78], [86, 85, 83, 79, 89, 56, 85], "big",
       "[Man of the Match] vs Man United", "[9 saves] at Arsenal", gk=True),
    pl("McBURNIE", "mcburnie", SCO, "ST", [75, 59, 76, 66, 71, 36, 84], [85, 65, 86, 72, 78, 40, 89], "hero",
       "[17 goals] + [7 assists]", "to get Hull promoted \U0001F525"),
]

job = {"out": f"{S}/hull/out/hull_upgrade.mp4", "work": f"{S}/hull/work", "fps": 30,
       "header": ["HULL CITY", "FAN UPGRADES"], "hook_sub": "wait for the last one \U0001F440",
       "outro": "WHO DESERVES MORE? \U0001F447", "music": "phonk", "players": players}
Path(job["out"]).parent.mkdir(parents=True, exist_ok=True)
(HERE / "hull_upgrade.json").write_text(json.dumps(job, ensure_ascii=False, indent=1))
print(len(players), "players")
