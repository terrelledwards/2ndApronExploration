"""Isolate big-spender ("apron-level") teams and compare their trade behavior.

The apron's aggregation ban targets only 2nd-apron teams — so the real test of the
rule is whether the biggest spenders aggregate LESS now than comparable big spenders
did before. We attribute each trade to the teams involved, tag each team-season by
spending tier, and compare aggregation-trade involvement across eras.

Inputs: transactions.csv (trades), team_payrolls.csv (spend_tier per team-season)
Outputs:
  data/apron_team_trades_by_tier_era.csv   tier x era behavior
  data/bigspender_agg_by_season.csv        big-spender aggregation rate per season
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

tx = pd.read_csv(os.path.join(DATA, "transactions.csv"))
pay = pd.read_csv(os.path.join(DATA, "team_payrolls.csv"))
tier_of = {(r.season, r.team): r.spend_tier for r in pay.itertuples()}
era_of = {r.season: r.era for r in pay.itertuples()}

tr = tx[(tx.type == "trade") & (tx.teams.notna())].drop_duplicates(["date", "teams"]).copy()

# explode each trade into (season, team) participations. Aggregation is attributed
# ONLY to the subject/sending team (the one that combined 2+ salaries) — that is the
# team the 2nd-apron ban actually restricts.
recs = []
for r in tr.itertuples():
    teams = str(r.teams).split("/")
    for tm in teams:
        recs.append({
            "season": r.season, "team": tm,
            "did_aggregate": bool(r.is_aggregation) and tm == r.subject_team,
            "multiteam": len(teams) >= 3,
        })
part = pd.DataFrame(recs)
part["tier"] = part.apply(lambda x: tier_of.get((x["season"], x["team"]), "under"), axis=1)
part["era"] = part["season"].map(era_of)
part["big_spender"] = part["tier"].isin(["apron1", "apron2"])

# ---- tier x era behavior ----
g = part.groupby(["era", "tier"]).agg(
    team_trade_participations=("team", "size"),
    agg_rate=("did_aggregate","mean"),
    multiteam_rate=("multiteam", "mean"),
).round(3).reset_index()
g.to_csv(os.path.join(DATA, "apron_team_trades_by_tier_era.csv"), index=False)

# ---- headline: big spenders vs the rest, by era ----
big = part.groupby(["era", "big_spender"]).agg(
    participations=("team", "size"),
    agg_rate=("did_aggregate","mean"),
    multiteam_rate=("multiteam", "mean"),
).round(3).reset_index()

# ---- big-spender aggregation rate per season (for a dashboard line) ----
bs = part[part.big_spender].groupby("season").agg(
    big_spender_trades=("team", "size"),
    agg_rate=("did_aggregate","mean"),
).round(3).reset_index()
alls = part.groupby("season").agg(agg_rate_all=("did_aggregate", "mean")).round(3).reset_index()
bs = bs.merge(alls, on="season", how="left")
bs["era"] = bs["season"].map(era_of)
bs.to_csv(os.path.join(DATA, "bigspender_agg_by_season.csv"), index=False)

ORDER = ["2005 CBA", "2011 CBA", "2017 CBA", "2023 CBA (apron)"]
print("=== Big spenders (apron1/apron2) vs rest — aggregation-trade involvement ===")
piv = big.pivot(index="era", columns="big_spender", values="agg_rate").reindex(ORDER)
piv.columns = ["rest", "big_spender"]
print(piv.to_string())
print("\n=== tier x era: aggregation involvement rate ===")
print(g.pivot(index="era", columns="tier", values="agg_rate").reindex(ORDER).to_string())
print("\n=== big-spender trade participations per era (are they trading at all?) ===")
print(big[big.big_spender].set_index("era")["participations"].reindex(ORDER).to_string())
