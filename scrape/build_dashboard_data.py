"""Consolidate all workstream metrics into one compact JSON for the dashboard.

Output: data/dashboard_data.json
"""
import os
import json
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def era(s):
    y = int(str(s)[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (apron)"


def nn(v):
    """JSON-safe: NaN/NA -> None, numpy -> python."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, "item"):
        return v.item()
    return v


out = {}

# ---- PARITY ---- (parity_analysis.py writes to repo root)
par = pd.read_csv(os.path.join(ROOT, "parity_metrics_by_season.csv"))
out["parity"] = [{
    "season": r.season, "era": era(r.season),
    "eff_contenders": round(r.eff_contenders, 2),
    "top1_share": round(r.top1_share, 3),
    "top3_share": round(r.top3_share, 3),
    "champ": r.champ_team, "champ_rank": int(r.champ_preseason_rank),
    "win_total_std": round(r.win_total_std, 2),
} for r in par.itertuples()]

# ---- TRADES ----
tr = pd.read_csv(os.path.join(DATA, "trade_metrics_by_season.csv"))
out["trades"] = [{
    "season": r.season, "era": r.era,
    "total": int(r.total_trades), "offseason": int(r.offseason),
    "in_season": int(r.in_season), "deadline_week": int(r.deadline_week),
    "multiteam": int(r.multiteam_trades),
    "agg_share": round(r.aggregation_share, 3),
} for r in tr.itertuples()]

# ---- FREE AGENCY ----
fa = pd.read_csv(os.path.join(DATA, "fa_metrics_by_season.csv"))
out["fa"] = [{
    "season": r.season, "era": r.era,
    "median_day_big": nn(r.median_day_big),
    "median_day_rest": nn(r.median_day_rest),
    "star_move_rate": nn(r.star_move_rate),
    "n_big": int(r.n_big_contracts),
} for r in fa.itertuples()]

# ---- COMPENSATION ----
spine = pd.read_csv(os.path.join(DATA, "player_season_spine.csv"))

# (a) star pay as % of cap over time: top-1 and mean of top-5 salaries each season
comp_rows = []
for s, g in spine.dropna(subset=["pct_of_cap"]).groupby("season"):
    top = g.nlargest(5, "total_salary")
    comp_rows.append({
        "season": s, "era": era(s),
        "top1_pct": round(top.pct_of_cap.iloc[0], 2),
        "top5_mean_pct": round(top.pct_of_cap.mean(), 2),
        "top1_player": top.player.iloc[0],
    })
out["star_pay"] = comp_rows

# (b) surplus-value scatter, per season, qualified players only (MP>=500 -> impact_tier set)
q = spine[spine.impact_tier.notna() & spine.pct_of_cap.notna()].copy()
scatter = {}
for s, g in q.groupby("season"):
    scatter[s] = [{
        "p": r.player,
        "cap": round(r.pct_of_cap, 1),
        "bpm": round(r.bpm, 1) if pd.notna(r.bpm) else None,
        "sv": int(r.surplus_value) if pd.notna(r.surplus_value) else None,
        "exp": int(r.experience) if pd.notna(r.experience) else None,
    } for r in g.itertuples()]
out["scatter"] = scatter

# (c) middle-class squeeze: count of 5-15%-of-cap contracts (impact_tier>=3) per season
mc = []
for s, g in spine.dropna(subset=["pct_of_cap"]).groupby("season"):
    mc.append({
        "season": s, "era": era(s),
        "middle_class": int(((g.pct_of_cap >= 5) & (g.pct_of_cap < 15)).sum()),
        "max_plus": int((g.pct_of_cap >= 25).sum()),
        "minimum": int((g.pct_of_cap < 5).sum()),
    })
out["classes"] = mc

# ---- COUNTERFACTUAL TRADES ----
cf = pd.read_csv(os.path.join(DATA, "counterfactual_trades.csv"))
out["counterfactual"] = [{
    "year": int(r.year), "trade": r.trade, "star": r.star, "acq": r.acquirer,
    "tier": r.acq_spend_tier, "agg": int(r.salaries_aggregated), "picks": int(r.picks_out),
    "restricted": bool(r.relies_on_restricted_mechanism),
    "verdict": r.verdict, "reason": r.reason,
} for r in cf.itertuples()]

# ---- BIG-SPENDER AGGREGATION (per season) ----
bs = pd.read_csv(os.path.join(DATA, "bigspender_agg_by_season.csv"))
out["apron_agg"] = [{
    "season": r.season, "era": era(r.season),
    "big": round(r.agg_rate, 3), "all": round(r.agg_rate_all, 3),
} for r in bs.itertuples()]

# ---- CROSS-LEAGUE (Workstream 4) ----
with open(os.path.join(DATA, "cross_league.json")) as f:
    out["cross"] = json.load(f)

# era metadata for shading
out["eras"] = [
    {"name": "2005 CBA", "start": "2005-06", "end": "2010-11"},
    {"name": "2011 CBA", "start": "2011-12", "end": "2016-17"},
    {"name": "2017 CBA", "start": "2017-18", "end": "2022-23"},
    {"name": "2023 CBA (apron)", "start": "2023-24", "end": "2025-26"},
]

path = os.path.join(DATA, "dashboard_data.json")
with open(path, "w") as f:
    json.dump(out, f, separators=(",", ":"))
print(f"wrote {path} ({os.path.getsize(path)//1024} KB)")
print("keys:", list(out.keys()))
print("scatter seasons:", len(out["scatter"]),
      "| total scatter points:", sum(len(v) for v in out["scatter"].values()))
