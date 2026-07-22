"""Team-season payrolls and spending tiers (tax/apron analog).

Payroll = sum of disclosed salaries on each team's cap sheet that season (from
team_player_salaries.csv; transaction-inclusive, so it approximates gross cap
commitment incl. dead money — fine for ranking spenders).

Thresholds: real cap/tax/apron dollar lines are hardcoded for the seasons where the
apron exists and matters (2023-24 onward). For all seasons we ALSO compute an
era-normalized ratio payroll/cap, and derive a spending tier from it so pre-apron
and apron seasons are comparable on one scale:

  tier by payroll/cap ratio:
    under      < 1.10
    tax        1.10 - 1.25   (~ luxury-tax territory historically)
    apron1     1.25 - 1.37   (~ first-apron-level spender)
    apron2     >= 1.37       (~ second-apron-level spender)

The 1.25/1.37 cuts are calibrated so the 2024-25 real first/second apron lines
($178.1M / $188.9M on a $140.6M cap = 1.267 / 1.343) land in the right buckets.

Output: data/team_payrolls.csv
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# Real dollar lines (millions) for apron-era seasons — documented CBA figures.
LINES = {  # season: (cap, tax, apron1, apron2)
    "2023-24": (136.021, 165.294, 172.346, 182.794),
    "2024-25": (140.588, 170.814, 178.132, 188.931),
    "2025-26": (154.647, 187.895, 195.945, 207.824),
}

tps = pd.read_csv(os.path.join(DATA, "team_player_salaries.csv"))
cap = pd.read_csv(os.path.join(DATA, "salary_cap_history.csv"))[["season", "salary_cap"]]

pay = (tps.dropna(subset=["salary"]).groupby(["season", "team"], as_index=False)
          .agg(payroll=("salary", "sum"), n_on_books=("player_id", "nunique")))
pay = pay.merge(cap, on="season", how="left")
pay["payroll_cap_ratio"] = (pay["payroll"] / pay["salary_cap"]).round(3)
pay["payroll_rank"] = pay.groupby("season")["payroll"].rank(ascending=False, method="min").astype(int)


def tier(r):
    x = r["payroll_cap_ratio"]
    if x < 1.10:  return "under"
    if x < 1.25:  return "tax"
    if x < 1.37:  return "apron1"
    return "apron2"


pay["spend_tier"] = pay.apply(tier, axis=1)


def era(s):
    y = int(str(s)[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (apron)"


pay["era"] = pay["season"].apply(era)

# actual over-apron flag for real-apron seasons (payroll in $M vs real 2nd-apron line)
def over_apron2(r):
    L = LINES.get(r["season"])
    if not L:
        return None
    return bool(r["payroll"] / 1e6 >= L[3])


pay["over_2nd_apron_real"] = pay.apply(over_apron2, axis=1)
pay = pay.sort_values(["season", "payroll"], ascending=[True, False])
pay.to_csv(os.path.join(DATA, "team_payrolls.csv"), index=False)

print(f"team_payrolls: {len(pay)} team-seasons")
print("\nspend-tier counts by era:")
print(pay.groupby(["era", "spend_tier"]).size().unstack(fill_value=0).to_string())
print("\nReal 2nd-apron teams (2023-26):")
print(pay[pay.over_2nd_apron_real == True][["season", "team", "payroll", "payroll_cap_ratio"]]
      .assign(payroll=lambda d: (d.payroll/1e6).round(1)).to_string(index=False))
print("\nSanity — 2024-25 top-5 payrolls ($M):")
print((pay[pay.season == "2024-25"].head(5)
       .assign(pay_m=lambda d:(d.payroll/1e6).round(1)))[["team","pay_m","payroll_cap_ratio","spend_tier"]].to_string(index=False))
