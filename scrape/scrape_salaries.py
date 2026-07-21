"""Scrape league-wide NBA player salaries by season from Basketball-Reference.

Strategy: for each season (ending year 2006..2026), read the league page to get
that season's team abbreviations (auto-handles relocations/renames), then pull the
`salaries2` table from each team-season page. Salaries are keyed to B-Ref player
IDs (data-append-csv), which link to the RAPTOR archive.

Robustness:
  - Every fetched page is cached to scrape/cache/ ; re-runs never re-hit the network.
  - Live requests are throttled (BREF ~20 req/min limit) with backoff on 429.
  - Output is written incrementally so partial progress is always usable.

Run:  ../.venv/bin/python scrape_salaries.py
"""
import os
import re
import sys
import time
import requests
from io import StringIO
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CACHE = os.path.join(HERE, "cache")
DATA = os.path.join(ROOT, "data")
os.makedirs(CACHE, exist_ok=True)
os.makedirs(DATA, exist_ok=True)

SEASONS = list(range(2006, 2027))  # ending years: 2005-06 .. 2025-26
DELAY = 3.5                        # seconds between LIVE requests (~17/min)
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}

_last_live = [0.0]


def fetch(url, cache_key):
    """Return page HTML, from disk cache if present, else throttled live fetch."""
    path = os.path.join(CACHE, cache_key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        with open(path, encoding="utf-8") as f:
            return f.read()
    # throttle
    wait = DELAY - (time.monotonic() - _last_live[0])
    if wait > 0:
        time.sleep(wait)
    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, timeout=30)
        _last_live[0] = time.monotonic()
        if r.status_code == 200:
            with open(path, "w", encoding="utf-8") as f:
                f.write(r.text)
            return r.text
        if r.status_code == 429:
            back = 60 * (attempt + 1)
            print(f"    429 rate-limited; sleeping {back}s", flush=True)
            time.sleep(back)
            continue
        print(f"    HTTP {r.status_code} for {url}", flush=True)
        return None
    return None


def uncomment(html):
    return html.replace("<!--", "").replace("-->", "")


def teams_for_season(year):
    html = fetch(f"https://www.basketball-reference.com/leagues/NBA_{year}.html",
                 f"league_{year}")
    if not html:
        return []
    return sorted(set(re.findall(rf'/teams/([A-Z]{{3}})/{year}\.html', html)))


def salaries_for_team_season(team, year):
    html = fetch(f"https://www.basketball-reference.com/teams/{team}/{year}.html",
                 f"team_{team}_{year}")
    if not html:
        return None
    html = uncomment(html)
    m = re.search(r'<table[^>]*id="salaries2".*?</table>', html, re.S)
    if not m:
        return None
    block = m.group(0)
    try:
        tab = pd.read_html(StringIO(block))[0]
    except ValueError:
        return None
    # player ids appear in row order within the table's <a data-append-csv=...>
    pids = re.findall(r'data-append-csv="([a-z0-9]+)"', block)
    tab = tab.rename(columns={tab.columns[1]: "player", "Salary": "salary_raw"})
    tab = tab[tab["player"].notna() & (tab["player"] != "Salary")].copy()
    tab["player_id"] = (pids[:len(tab)] + [None] * len(tab))[:len(tab)]
    tab["salary"] = (tab["salary_raw"].astype(str)
                     .str.replace(r"[^0-9]", "", regex=True)
                     .replace("", pd.NA).astype("Int64"))
    tab["team"] = team
    tab["season_end"] = year
    tab["season"] = f"{year-1}-{str(year)[2:]}"
    return tab[["season", "season_end", "team", "player", "player_id", "salary"]]


def main():
    out_path = os.path.join(DATA, "salaries_by_season.csv")
    frames = []
    for year in SEASONS:
        teams = teams_for_season(year)
        print(f"[{year-1}-{str(year)[2:]}] {len(teams)} teams: {teams}", flush=True)
        for t in teams:
            df = salaries_for_team_season(t, year)
            if df is None or df.empty:
                print(f"    !! no salary table for {t} {year}", flush=True)
                continue
            frames.append(df)
        # incremental write after each season
        pd.concat(frames, ignore_index=True).to_csv(out_path, index=False)
        print(f"    -> wrote {sum(len(f) for f in frames)} rows so far", flush=True)

    # salary cap history
    cap_html = fetch("https://www.basketball-reference.com/contracts/salary-cap-history.html",
                     "salary_cap_history")
    if cap_html:
        cap = pd.read_html(StringIO(uncomment(cap_html)))[0]
        cap.columns = ["season", "salary_cap", "cap_2022_dollars"][:len(cap.columns)]
        for c in ["salary_cap", "cap_2022_dollars"]:
            if c in cap:
                cap[c] = cap[c].astype(str).str.replace(r"[^0-9]", "", regex=True)
                cap[c] = pd.to_numeric(cap[c], errors="coerce").astype("Int64")
        cap.to_csv(os.path.join(DATA, "salary_cap_history.csv"), index=False)
        print(f"cap history: {len(cap)} seasons", flush=True)

    print("DONE", flush=True)


if __name__ == "__main__":
    main()
