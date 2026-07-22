"""Parse cached B-Ref transaction logs into one structured row per transaction.

Each <li> is a date carrying one or more <p> transaction descriptions. Team links
carry data-attr-from / data-attr-to; player links are /players/x/id.html. We classify
each <p> by verb and extract movement.

Output: data/transactions.csv with columns:
  season, date, type, subtype, teams, n_teams, players, n_players,
  players_out, players_in, is_aggregation, text
"""
import os
import re
import glob
from datetime import datetime
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "scrape", "cache")
DATA = os.path.join(ROOT, "data")

PLAYER_RE = re.compile(r'/players/[a-z]/([a-z0-9]+)\.html')
FROM_RE = re.compile(r'data-attr-from="([A-Z]{3})"')
TO_RE = re.compile(r'data-attr-to="([A-Z]{3})"')
TAG_RE = re.compile(r'<[^>]+>')


def strip(html):
    return re.sub(r'\s+', ' ', TAG_RE.sub('', html)).strip()


def classify(text):
    t = text.lower()
    if 'traded' in t or 'as part of a' in t and 'trade' in t:
        return 'trade', None
    if 'signed' in t:
        if 'two-way' in t:
            return 'signing', 'two_way'
        if '10-day' in t or 'ten-day' in t:
            return 'signing', 'ten_day'
        if 'as a free agent' in t:
            return 'signing', 'free_agent'
        if 'multi-year' in t or 'one-year' in t or 'multiyear' in t or re.search(r'\b\d+-year', t):
            return 'signing', 'contract'
        return 'signing', 'other_signing'
    if 'waived' in t:
        return 'waiver', None
    if 'claimed' in t:
        return 'claim', None
    if 'released' in t:
        return 'released', None
    return 'other', None


def count_players_out_in(raw_html):
    """Split the RAW trade <p> HTML at 'in exchange for'/' for ' (keeps player links)
    to estimate players going out vs coming in for the subject team."""
    parts = re.split(r'in exchange for|\bfor\b', raw_html, maxsplit=1)
    out_ids = set(PLAYER_RE.findall(parts[0]))
    in_ids = set(PLAYER_RE.findall(parts[1])) if len(parts) > 1 else set()
    return len(out_ids), len(in_ids)


rows = []
for path in sorted(glob.glob(os.path.join(CACHE, "transactions_*.html"))):
    year = int(re.search(r'transactions_(\d{4})', path).group(1))
    season = f"{year-1}-{str(year)[2:]}"
    html = open(path, encoding="utf-8").read()
    m = re.search(r"<ul class='page_index'>(.*?)</ul>", html, re.S)
    if not m:
        print(f"  !! no page_index for {season}")
        continue
    ul = m.group(1)
    # split into <li> blocks
    for li in re.split(r'<li>', ul):
        li = li.strip()
        if not li:
            continue
        dm = re.match(r'<span>(.*?)</span>', li)
        if not dm:
            continue
        date_txt = dm.group(1).strip()
        try:
            date = datetime.strptime(date_txt, "%B %d, %Y").date()
        except ValueError:
            continue
        for p in re.findall(r'<p>(.*?)</p>', li, re.S):
            text = strip(p)
            if not text:
                continue
            typ, sub = classify(text)
            teams = sorted(set(FROM_RE.findall(p)) | set(TO_RE.findall(p)))
            players = list(dict.fromkeys(PLAYER_RE.findall(p)))
            out_n, in_n = (count_players_out_in(p) if typ == 'trade' else (0, 0))
            # the aggregating/sending team is the first "data-attr-from" (subject of
            # "The X traded A, B ... to Y"); its outgoing count is out_n
            fm = FROM_RE.search(p)
            subject_team = fm.group(1) if fm else ""
            rows.append({
                "season": season,
                "date": date.isoformat(),
                "type": typ,
                "subtype": sub,
                "teams": "/".join(teams),
                "n_teams": len(teams),
                "subject_team": subject_team,
                "players": "/".join(players),
                "n_players": len(players),
                "players_out": out_n,
                "players_in": in_n,
                "is_aggregation": bool(typ == 'trade' and out_n >= 2),
                "text": text,
            })

df = pd.DataFrame(rows)
df.to_csv(os.path.join(DATA, "transactions.csv"), index=False)
print(f"transactions: {len(df)} rows, {df.season.nunique()} seasons")
print(df.type.value_counts().to_string())
