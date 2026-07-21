"""Odds-based parity metrics for the NBA, 2005-06 to 2025-26, by CBA era."""
import pandas as pd
import numpy as np

OUT = "/sessions/amazing-kind-ramanujan/mnt/outputs"

odds = pd.concat([
    pd.read_csv(f"{OUT}/odds_2005_2016.csv"),
    pd.read_csv(f"{OUT}/odds_2016_2026.csv"),
], ignore_index=True)

# Fix: covers.com shows Knicks as 2025-26 champions
odds.loc[(odds.season == "2025-26") & (odds.team == "New York Knicks"), "champion"] = 1
assert odds.groupby("season").champion.sum().eq(1).all()
assert odds.groupby("season").size().eq(30).all()

def implied_prob(american):
    a = float(american)
    return 100.0 / (a + 100.0) if a > 0 else abs(a) / (abs(a) + 100.0)

odds["p_raw"] = odds.odds_preseason_last.apply(implied_prob)
odds["p"] = odds.groupby("season").p_raw.transform(lambda s: s / s.sum())  # vig removed

def era(season):
    y = int(season[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (2nd apron)"

rows = []
for season, g in odds.groupby("season"):
    p = g.p.values
    p_sorted = np.sort(p)[::-1]
    ent = -(p * np.log(p)).sum()
    champ = g[g.champion == 1]
    champ_rank = int((g.p.rank(ascending=False, method="min")[g.champion == 1]).iloc[0])
    rows.append({
        "season": season,
        "era": era(season),
        "vig_overround": g.p_raw.sum(),
        "hhi": (p ** 2).sum(),
        "eff_contenders": 1.0 / (p ** 2).sum(),   # inverse-HHI: 'effective number of teams'
        "perplexity": np.exp(ent),                 # entropy-based equivalent
        "top1_share": p_sorted[0],
        "top3_share": p_sorted[:3].sum(),
        "top5_share": p_sorted[:5].sum(),
        "n_ge_5pct": int((p >= 0.05).sum()),
        "n_ge_2pct": int((p >= 0.02).sum()),
        "n_longshot_10k": int((g.odds_preseason_last >= 10000).sum()),
        "champ_team": champ.team.iloc[0],
        "champ_preseason_prob": champ.p.iloc[0],
        "champ_preseason_rank": champ_rank,
        "champ_preseason_odds": int(champ.odds_preseason_last.iloc[0]),
    })
m = pd.DataFrame(rows).sort_values("season").reset_index(drop=True)

# Win-total dispersion per season (expected-strength spread)
wt = pd.read_csv(f"{OUT}/win_totals.csv")
wt_disp = wt.groupby("season").win_total_line.agg(["std", "max", "min"])
wt_disp["wt_spread"] = wt_disp["max"] - wt_disp["min"]
m = m.merge(wt_disp[["std", "wt_spread"]].rename(columns={"std": "win_total_std"}),
            left_on="season", right_index=True, how="left")

m.to_csv(f"{OUT}/parity_metrics_by_season.csv", index=False, float_format="%.4f")

era_summary = m.groupby("era").agg(
    seasons=("season", "count"),
    eff_contenders=("eff_contenders", "mean"),
    top1_share=("top1_share", "mean"),
    top3_share=("top3_share", "mean"),
    n_ge_5pct=("n_ge_5pct", "mean"),
    n_ge_2pct=("n_ge_2pct", "mean"),
    champ_rank=("champ_preseason_rank", "mean"),
    champ_prob=("champ_preseason_prob", "mean"),
    win_total_std=("win_total_std", "mean"),
).round(3)
era_summary.to_csv(f"{OUT}/parity_metrics_by_era.csv")

pd.set_option("display.width", 200)
print(m[["season", "era", "eff_contenders", "top1_share", "top3_share",
         "n_ge_5pct", "n_ge_2pct", "champ_team", "champ_preseason_rank",
         "champ_preseason_odds", "win_total_std"]].to_string(index=False))
print()
print(era_summary.to_string())
