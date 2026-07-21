"""Assemble the full player-season spine: axes A (experience) x B (impact) x C (pay).

Joins on (season, player_id):
  player_season_salaries.csv   pay  (axis C: pct_of_cap)
  experience_by_season.csv     experience (axis A)
  advanced_by_season.csv       impact (axis B: BPM/VORP/WS)

Then assigns ordinal tiers and a surplus-value proxy.

TIER DEFINITIONS (documented so they can be tuned):

  Pay tier (axis C) from salary as % of cap:
    1  <5%     minimums / second-rounders
    2  5-15%   MLE / role-player "middle class"
    3  15-25%  sub-max starters
    4  25-30%  max
    5  30%+    supermax

  Impact tier (axis B) from BPM (Box Plus/Minus, a per-100-poss rate stat, so it is
  robust to short/lockout seasons). Standard BPM reference points:
    5  BPM >= 5    All-NBA level
    4  2..5        All-Star / high starter
    3  0..2        solid starter / league average
    2  -2..0       rotation
    1  < -2        replacement / negative
  Only assigned when minutes are sufficient (MP >= 500); below that BPM is too noisy
  and impact_tier is left null (player kept, flagged low_minutes=True).

  Surplus value (ordinal proxy) = impact_tier - pay_tier, range -4..+4.
    Positive = produces above pay grade (bargain); negative = paid above production.

Output: data/player_season_spine.csv
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

pay = pd.read_csv(os.path.join(DATA, "player_season_salaries.csv"))
exp = pd.read_csv(os.path.join(DATA, "experience_by_season.csv"))
adv = pd.read_csv(os.path.join(DATA, "advanced_by_season.csv"))

spine = (pay.merge(exp, on=["season", "player_id"], how="left")
            .merge(adv.drop(columns=["player"], errors="ignore"),
                   on=["season", "player_id"], how="left"))


def pay_tier(pct):
    if pd.isna(pct):
        return pd.NA
    if pct < 5:   return 1
    if pct < 15:  return 2
    if pct < 25:  return 3
    if pct < 30:  return 4
    return 5


def impact_tier(bpm, mp):
    if pd.isna(bpm) or pd.isna(mp) or mp < 500:
        return pd.NA
    if bpm >= 5:  return 5
    if bpm >= 2:  return 4
    if bpm >= 0:  return 3
    if bpm >= -2: return 2
    return 1


spine["pay_tier"] = spine["pct_of_cap"].apply(pay_tier).astype("Int64")
spine["low_minutes"] = spine["mp"].fillna(0) < 500
spine["impact_tier"] = spine.apply(lambda r: impact_tier(r["bpm"], r["mp"]), axis=1).astype("Int64")
spine["surplus_value"] = (spine["impact_tier"] - spine["pay_tier"]).astype("Int64")

# CBA era tag (matches parity_analysis.py)
def era(season):
    y = int(str(season)[:4])
    if y <= 2010: return "2005 CBA"
    if y <= 2016: return "2011 CBA"
    if y <= 2022: return "2017 CBA"
    return "2023 CBA (2nd apron)"

spine["era"] = spine["season"].apply(era)

spine.to_csv(os.path.join(DATA, "player_season_spine.csv"), index=False)

print(f"player_season_spine: {len(spine)} rows, {spine.season.nunique()} seasons")
print(f"  with experience: {spine.experience.notna().sum()}")
print(f"  with impact metric (any MP): {spine.bpm.notna().sum()}")
print(f"  with impact_tier (MP>=500): {spine.impact_tier.notna().sum()}")
print("\nsurplus_value distribution (impact_tier - pay_tier):")
print(spine.surplus_value.value_counts(dropna=False).sort_index().to_string())
