"""Axis A: years of NBA experience per player-season.

Reads the cached team-season pages (scrape/cache/team_*.html) — no network — and
pulls the `roster` table's `Exp` column ('R' = rookie = 0). A player who appears on
multiple teams in a season carries the same experience, so we dedupe to one row per
(season, player_id).

Output: data/experience_by_season.csv
"""
import os
import re
import glob
from io import StringIO
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "scrape", "cache")
DATA = os.path.join(ROOT, "data")

rows = []
for path in sorted(glob.glob(os.path.join(CACHE, "team_*.html"))):
    fname = os.path.basename(path)                       # team_LAL_2024.html
    m = re.match(r"team_([A-Z]{3})_(\d{4})\.html", fname)
    if not m:
        continue
    team, year = m.group(1), int(m.group(2))
    html = open(path, encoding="utf-8").read().replace("<!--", "").replace("-->", "")
    t = re.search(r'<table[^>]*id="roster".*?</table>', html, re.S)
    if not t:
        continue
    block = t.group(0)
    tab = pd.read_html(StringIO(block))[0]
    pids = re.findall(r'data-append-csv="([a-z0-9]+)"', block)
    tab = tab[tab["Player"].notna()].copy()
    tab["player_id"] = (pids[:len(tab)] + [None] * len(tab))[:len(tab)]
    tab["season"] = f"{year-1}-{str(year)[2:]}"
    tab["exp_raw"] = tab["Exp"].astype(str).str.strip()
    tab["experience"] = tab["exp_raw"].replace("R", "0")
    tab["experience"] = pd.to_numeric(tab["experience"], errors="coerce").astype("Int64")
    rows.append(tab[["season", "player_id", "experience"]])

exp = pd.concat(rows, ignore_index=True).dropna(subset=["player_id"])
# one row per player-season (max handles any inconsistency across a traded player's teams)
exp = (exp.groupby(["season", "player_id"], as_index=False)["experience"].max())

# CBA max-eligibility buckets (per research plan axis A)
def exp_bucket(e):
    if pd.isna(e):
        return None
    e = int(e)
    if e <= 4:
        return "0-4 (rookie scale / early)"
    if e <= 6:
        return "5-6 (25% max eligible)"
    if e <= 9:
        return "7-9 (30% max eligible)"
    return "10+ (35% / supermax eligible)"

exp["exp_bucket"] = exp["experience"].apply(exp_bucket)
exp.to_csv(os.path.join(DATA, "experience_by_season.csv"), index=False)
print(f"experience_by_season: {len(exp)} player-seasons, "
      f"{exp.season.nunique()} seasons, {exp.experience.isna().sum()} missing exp")
print(exp.exp_bucket.value_counts(dropna=False).to_string())
