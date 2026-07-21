"""Workstream 3b: trade activity metrics per season.

Splits trades into offseason / in-season / deadline-week, and tracks salary
aggregation (the mechanism the 2nd apron bans for apron teams), multi-team deals,
and players moved.

The trade deadline moves year to year (and shifted in the 2011-12 lockout and
2020-21 COVID seasons), so we DERIVE it as the latest trade date in the Jan-Mar
window rather than hardcoding dates.

Output: data/trade_metrics_by_season.csv
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

t = pd.read_csv(os.path.join(DATA, "transactions.csv"), parse_dates=["date"])
tr = t[t.type == "trade"].copy()
# collapse to distinct deals (one <p> per deal already, but guard duplicates)
tr = tr.drop_duplicates(["date", "teams"]).copy()
tr["month"] = tr.date.dt.month

# derive per-season deadline = latest trade in the Jan-Mar window
deadlines = (tr[tr.month.isin([1, 2, 3])]
             .groupby("season").date.max().rename("deadline"))
tr = tr.merge(deadlines, on="season", how="left")


def period(row):
    m = row["month"]
    dl = row["deadline"]
    if m in (6, 7, 8, 9, 10):
        return "offseason"
    if pd.notna(dl) and (dl - row["date"]).days <= 6 and row["date"] <= dl:
        return "deadline_week"
    return "in_season"


tr["period"] = tr.apply(period, axis=1)


def era(s):
    y = int(str(s)[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (2nd apron)"


rows = []
for s, g in tr.groupby("season"):
    pc = g.period.value_counts()
    rows.append({
        "season": s,
        "era": era(s),
        "deadline": g.deadline.iloc[0].date() if pd.notna(g.deadline.iloc[0]) else None,
        "total_trades": len(g),
        "offseason": int(pc.get("offseason", 0)),
        "in_season": int(pc.get("in_season", 0)),
        "deadline_week": int(pc.get("deadline_week", 0)),
        "aggregation_trades": int(g.is_aggregation.sum()),
        "aggregation_share": round(g.is_aggregation.mean(), 3),
        "multiteam_trades": int((g.n_teams >= 3).sum()),
        "avg_players_per_trade": round(g.n_players.mean(), 2),
    })

m = pd.DataFrame(rows)
m.to_csv(os.path.join(DATA, "trade_metrics_by_season.csv"), index=False)

era_sum = m.groupby("era").agg(
    seasons=("season", "count"),
    trades_per_yr=("total_trades", "mean"),
    offseason=("offseason", "mean"),
    in_season=("in_season", "mean"),
    deadline_week=("deadline_week", "mean"),
    aggregation_share=("aggregation_share", "mean"),
    multiteam_per_yr=("multiteam_trades", "mean"),
).round(2)
era_sum.to_csv(os.path.join(DATA, "trade_metrics_by_era.csv"))

print(m.to_string(index=False))
print("\n== by era ==")
print(era_sum.to_string())
