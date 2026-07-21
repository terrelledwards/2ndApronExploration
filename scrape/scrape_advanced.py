"""Axis B: player impact metrics per season from B-Ref advanced tables.

Fetches /leagues/NBA_YYYY_advanced.html for 2006..2026 (21 pages, throttled+cached
via the same cache dir). Keeps BPM/OBPM/DBPM, VORP, WS, PER, USG%, plus G/GS/MP for
minutes filtering. Keyed to B-Ref player_id.

Traded players have one row per team plus a combined season-total row (Team = 'TOT'
in older seasons, '2TM'/'3TM'/... in newer ones). We keep the combined row so each
player-season is a single full-season line.

Output: data/advanced_by_season.csv
"""
import os
import re
import time
import requests
from io import StringIO
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(ROOT, "data")
os.makedirs(CACHE, exist_ok=True)

SEASONS = list(range(2006, 2027))
DELAY = 3.5
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
_last = [0.0]

KEEP = ["Age", "G", "GS", "MP", "PER", "TS%", "USG%", "WS", "WS/48",
        "OBPM", "DBPM", "BPM", "VORP"]


def fetch(url, key):
    path = os.path.join(CACHE, key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return open(path, encoding="utf-8").read()
    wait = DELAY - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, timeout=30)
        _last[0] = time.monotonic()
        if r.status_code == 200:
            open(path, "w", encoding="utf-8").write(r.text)
            return r.text
        if r.status_code == 429:
            time.sleep(60 * (attempt + 1))
            continue
        return None
    return None


def parse_season(year):
    html = fetch(f"https://www.basketball-reference.com/leagues/NBA_{year}_advanced.html",
                 f"advanced_{year}")
    if not html:
        return None
    html = html.replace("<!--", "").replace("-->", "")
    m = re.search(r'<table[^>]*id="advanced".*?</table>', html, re.S)
    if not m:
        return None
    block = m.group(0)
    tab = pd.read_html(StringIO(block))[0]
    pids = re.findall(r'data-append-csv="([a-z0-9]+)"', block)
    tab = tab[tab["Player"] != "Player"].copy()          # drop repeated header rows
    tab["player_id"] = (pids[:len(tab)] + [None] * len(tab))[:len(tab)]
    tab = tab.dropna(subset=["player_id"])
    team_col = "Team" if "Team" in tab.columns else "Tm"
    tab = tab.rename(columns={team_col: "team"})

    # keep combined season-total row for traded players (TOT / 2TM / 3TM / ...)
    combo = tab["team"].astype(str).str.match(r"(TOT|\dTM)$")
    dup_ids = tab.loc[tab.duplicated("player_id", keep=False), "player_id"].unique()
    keep_mask = (~tab["player_id"].isin(dup_ids)) | combo
    out = tab[keep_mask].drop_duplicates("player_id", keep="first").copy()

    out["season"] = f"{year-1}-{str(year)[2:]}"
    cols = ["season", "player_id", "Player"] + [c for c in KEEP if c in out.columns]
    out = out.rename(columns={"Player": "player"})
    cols = ["season", "player_id", "player"] + [c for c in KEEP if c in out.columns]
    return out[cols]


frames = []
for y in SEASONS:
    df = parse_season(y)
    if df is not None:
        frames.append(df)
        print(f"{y-1}-{str(y)[2:]}: {len(df)} player-seasons", flush=True)
    else:
        print(f"{y-1}-{str(y)[2:]}: FAILED", flush=True)

adv = pd.concat(frames, ignore_index=True)
adv.columns = [c.lower().replace("%", "_pct").replace("/", "_") for c in adv.columns]
adv.to_csv(os.path.join(DATA, "advanced_by_season.csv"), index=False)
print(f"\nadvanced_by_season: {len(adv)} rows, {adv.season.nunique()} seasons")
