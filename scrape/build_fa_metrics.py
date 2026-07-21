"""Workstream 3c: free-agency timeline & star movement.

Questions: do signings happen later? do big-money players sign first or last?
are more stars changing teams?

Signing timing: offseason signings (subtype contract/free_agent) with a real player
match in the spine. days_from_open = signing date - July 1 of the season's start year.
A "big contract" = year-1 salary >= 15% of the cap (sub-max starter and up).

Star movement: a player is a "star" in season Y if impact_tier >= 4 (All-Star level,
BPM>=2, MP>=500). Their main team = the team paying them the most that season. Movement
rate[Y] = share of stars present in Y-1 whose main team changed.

Outputs: data/fa_signing_timeline.csv, data/fa_metrics_by_season.csv
"""
import os
from datetime import date
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

tx = pd.read_csv(os.path.join(DATA, "transactions.csv"), parse_dates=["date"])
spine = pd.read_csv(os.path.join(DATA, "player_season_spine.csv"))
tps = pd.read_csv(os.path.join(DATA, "team_player_salaries.csv"))


def era(s):
    y = int(str(s)[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (2nd apron)"


# ---------- signing timeline ----------
sign = tx[(tx.type == "signing") & (tx.subtype.isin(["contract", "free_agent"]))].copy()
sign["player_id"] = sign["players"].str.split("/").str[0]
sign["start_year"] = sign["season"].str[:4].astype(int)
sign["fa_open"] = sign["start_year"].apply(lambda y: pd.Timestamp(date(y, 7, 1)))
sign["days_from_open"] = (sign["date"] - sign["fa_open"]).dt.days
# offseason FA window only: July 1 (day 0) through ~Oct 31 (day 122)
fa = sign[(sign.days_from_open >= 0) & (sign.days_from_open <= 122)].copy()

# attach the player's salary/impact for that season
key = spine[["season", "player_id", "pct_of_cap", "impact_tier", "total_salary"]]
fa = fa.merge(key, on=["season", "player_id"], how="left")
fa["is_big_contract"] = fa["pct_of_cap"] >= 15
fa["era"] = fa["season"].apply(era)
fa[["season", "era", "date", "days_from_open", "player_id",
    "pct_of_cap", "total_salary", "impact_tier", "is_big_contract"]] \
    .to_csv(os.path.join(DATA, "fa_signing_timeline.csv"), index=False)

# ---------- star movement ----------
# main team per player-season = team with the largest salary that season
tps2 = tps.dropna(subset=["salary"]).sort_values("salary", ascending=False)
main = tps2.drop_duplicates(["season", "player_id"])[["season", "player_id", "team"]]
main = main.rename(columns={"team": "main_team"})
main["start_year"] = main["season"].str[:4].astype(int)

stars = spine[spine.impact_tier >= 4][["season", "player_id"]].copy()
stars["start_year"] = stars["season"].str[:4].astype(int)
stars = stars.merge(main[["player_id", "start_year", "main_team"]],
                    on=["player_id", "start_year"], how="left")
prev = main[["player_id", "start_year", "main_team"]].copy()
prev["start_year"] = prev["start_year"] + 1
prev = prev.rename(columns={"main_team": "prev_team"})
stars = stars.merge(prev, on=["player_id", "start_year"], how="left")
stars = stars.dropna(subset=["prev_team", "main_team"])
stars["moved"] = stars["main_team"] != stars["prev_team"]
move = stars.groupby("season").agg(stars_tracked=("moved", "size"),
                                    stars_moved=("moved", "sum")).reset_index()
move["star_move_rate"] = (move["stars_moved"] / move["stars_tracked"]).round(3)

# ---------- per-season summary ----------
rows = []
for s in sorted(fa.season.unique()):
    g = fa[fa.season == s]
    big = g[g.is_big_contract]
    small = g[~g.is_big_contract]
    mv = move[move.season == s]
    rows.append({
        "season": s,
        "era": era(s),
        "n_fa_signings": len(g),
        "median_day_all": g.days_from_open.median(),
        "median_day_big": big.days_from_open.median() if len(big) else None,
        "median_day_rest": small.days_from_open.median() if len(small) else None,
        "n_big_contracts": len(big),
        "star_move_rate": mv.star_move_rate.iloc[0] if len(mv) else None,
        "stars_moved": int(mv.stars_moved.iloc[0]) if len(mv) else None,
        "stars_tracked": int(mv.stars_tracked.iloc[0]) if len(mv) else None,
    })
m = pd.DataFrame(rows)
m.to_csv(os.path.join(DATA, "fa_metrics_by_season.csv"), index=False)

era_sum = m.groupby("era").agg(
    seasons=("season", "count"),
    fa_signings=("n_fa_signings", "mean"),
    median_day_big=("median_day_big", "mean"),
    median_day_rest=("median_day_rest", "mean"),
    big_contracts=("n_big_contracts", "mean"),
    star_move_rate=("star_move_rate", "mean"),
).round(2)
era_sum.to_csv(os.path.join(DATA, "fa_metrics_by_era.csv"))

pd.set_option("display.width", 200)
print(m.to_string(index=False))
print("\n== by era (median_day: 0 = July 1; higher = signs later) ==")
print(era_sum.to_string())
