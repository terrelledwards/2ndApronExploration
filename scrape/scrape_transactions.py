"""Fetch B-Ref season transaction logs (2006..2026), throttled + cached.

Output: raw HTML cached under scrape/cache/transactions_YYYY.html (parsed separately).
"""
import os
import time
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache")
os.makedirs(CACHE, exist_ok=True)

SEASONS = list(range(2006, 2027))
DELAY = 3.5
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
_last = [0.0]


def fetch(url, key):
    path = os.path.join(CACHE, key + ".html")
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return "cached"
    wait = DELAY - (time.monotonic() - _last[0])
    if wait > 0:
        time.sleep(wait)
    for attempt in range(5):
        r = requests.get(url, headers=HEADERS, timeout=30)
        _last[0] = time.monotonic()
        if r.status_code == 200:
            open(path, "w", encoding="utf-8").write(r.text)
            return "fetched"
        if r.status_code == 429:
            time.sleep(60 * (attempt + 1))
            continue
        return f"HTTP {r.status_code}"
    return "failed"


for y in SEASONS:
    status = fetch(f"https://www.basketball-reference.com/leagues/NBA_{y}_transactions.html",
                   f"transactions_{y}")
    print(f"{y-1}-{str(y)[2:]}: {status}", flush=True)
print("DONE", flush=True)
