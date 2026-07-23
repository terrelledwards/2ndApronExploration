"""Workstream 4: cross-league comparison — competitive balance, compensation, and
the player-movement / penalty-currency taxonomy.

Champions: most-recent 20 completed seasons per league, verified against Wikipedia
(2026-07). Balance = HHI of titles + distinct champions + effective champions (1/HHI).

Compensation: richest/poorest team payroll ratio, most recent season. Definitions
differ by league (noted) but the order of magnitude is the comparison:
  NFL cap-based; NBA cap-sheet (computed from our data); MLB opening-day payroll;
  EPL playing wage bill. Sources in COMP notes.

Output: data/cross_league.json  (+ console summary)
"""
import os
import json
from collections import Counter
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

CHAMPS = {
    "NBA": ["Heat","Spurs","Celtics","Lakers","Lakers","Mavericks","Heat","Heat","Spurs",
            "Warriors","Cavaliers","Warriors","Warriors","Raptors","Lakers","Bucks",
            "Warriors","Nuggets","Celtics","Thunder"],  # 2005-06 .. 2024-25
    "NFL": ["Steelers","Colts","Giants","Steelers","Saints","Packers","Giants","Ravens",
            "Seahawks","Patriots","Broncos","Patriots","Eagles","Patriots","Chiefs",
            "Buccaneers","Rams","Chiefs","Chiefs","Eagles"],  # 2005 .. 2024 seasons
    "MLB": ["White Sox","Cardinals","Red Sox","Phillies","Yankees","Giants","Cardinals",
            "Giants","Red Sox","Giants","Royals","Cubs","Astros","Red Sox","Nationals",
            "Dodgers","Braves","Astros","Rangers","Dodgers"],  # 2005 .. 2024
    "EPL": ["Chelsea","Chelsea","Man Utd","Man Utd","Man Utd","Chelsea","Man Utd","Man City",
            "Man Utd","Man City","Chelsea","Leicester","Chelsea","Man City","Man City",
            "Liverpool","Man City","Man City","Man City","Man City"],  # 2004-05 .. 2023-24
}

# cap type governs expected balance; ordered soft -> hard
CAP = {
    "NFL": {"type": "Hard cap", "hardness": 4, "currency": "Contract voided if over the cap",
            "movement": "Cap casualties + franchise tag; heavy forced churn"},
    "NBA": {"type": "Soft cap + two aprons", "hardness": 3,
            "currency": "Luxury-tax $ + basketball penalties (frozen picks, no aggregation)",
            "movement": "Trades/FA, but apron bans lock big spenders out of moves"},
    "MLB": {"type": "No cap (luxury tax / CBT)", "hardness": 2,
            "currency": "Escalating tax $ + lost/lowered draft picks",
            "movement": "Unrestricted free agency; spend past the tax if you pay"},
    "EPL": {"type": "No cap (PSR)", "hardness": 1,
            "currency": "Sporting penalties — points deductions (Everton, Forest)",
            "movement": "Free transfers; spending limited only by PSR loss limits"},
}

# richest/poorest team payroll, most recent season (see notes)
COMP = {
    "NFL": {"season": "2024", "hi": 255.4, "lo": 210.0, "unit": "$M cap",
            "note": "Hard cap $255.4M; all teams within it (cash range approx)."},
    "NBA": {"season": "2024-25", "hi": 214.4, "lo": 141.8, "unit": "$M salary",
            "note": "Cap-sheet salary from this project's data (PHX high, DET low)."},
    "MLB": {"season": "2024", "hi": 305.6, "lo": 60.5, "unit": "$M payroll",
            "note": "Opening-day payroll: Mets high, Athletics low (Yahoo/AP)."},
    "EPL": {"season": "2023-24", "hi": 205.8, "lo": 24.6, "unit": "£M wages",
            "note": "Playing wage bill: Man Utd high, Luton Town low (PlanetFootball)."},
}


def metrics(champs):
    n = len(champs)
    c = Counter(champs)
    hhi = sum((v / n) ** 2 for v in c.values())
    top, topn = c.most_common(1)[0]
    return {
        "seasons": n, "distinct": len(c), "hhi": round(hhi, 3),
        "eff_champions": round(1 / hhi, 2),
        "top_team": top, "top_titles": topn,
        "counts": dict(c.most_common()),
    }


out = {"leagues": [], "window": "most recent 20 completed seasons (~2005-2024)"}
ORDER = ["EPL", "NBA", "MLB", "NFL"]  # soft -> hard-ish, for display
for lg in ORDER:
    m = metrics(CHAMPS[lg])
    comp = COMP[lg]
    out["leagues"].append({
        "league": lg,
        **m,
        "cap_type": CAP[lg]["type"], "hardness": CAP[lg]["hardness"],
        "penalty_currency": CAP[lg]["currency"], "movement": CAP[lg]["movement"],
        "pay_hi": comp["hi"], "pay_lo": comp["lo"], "pay_unit": comp["unit"],
        "pay_ratio": round(comp["hi"] / comp["lo"], 2), "pay_season": comp["season"],
        "pay_note": comp["note"],
    })

with open(os.path.join(DATA, "cross_league.json"), "w") as f:
    json.dump(out, f, separators=(",", ":"))

print(f"{'League':6} {'Distinct':>8} {'HHI':>6} {'EffChamp':>9} {'Top team (titles)':<22} {'Pay ratio':>9}")
for r in out["leagues"]:
    print(f"{r['league']:6} {r['distinct']:>8} {r['hhi']:>6} {r['eff_champions']:>9} "
          f"{(r['top_team']+' ('+str(r['top_titles'])+')'):<22} {r['pay_ratio']:>8}x")
