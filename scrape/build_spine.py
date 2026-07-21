"""Build the salary spine from scraped B-Ref data.

Inputs (from scrape_salaries.py):
  data/salaries_by_season.csv      raw team x season x player salaries
  data/salary_cap_history.csv      league salary cap by season

Outputs:
  data/team_player_salaries.csv    raw rows + pct_of_cap (per team-season-player)
  data/player_season_salaries.csv  ONE row per player-season (trades summed),
                                   with n_teams, teams, salary_cap, pct_of_cap
"""
import os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

sal = pd.read_csv(os.path.join(DATA, "salaries_by_season.csv"))
cap = pd.read_csv(os.path.join(DATA, "salary_cap_history.csv"))[["season", "salary_cap"]]

# ---- team-level table with pct_of_cap ----
team = sal.merge(cap, on="season", how="left")
team["pct_of_cap"] = (team["salary"] / team["salary_cap"] * 100).round(2)
team.to_csv(os.path.join(DATA, "team_player_salaries.csv"), index=False)

# ---- player-season table (trades summed) ----
# One row per (season, player_id): total salary that season across all teams.
g = (sal.dropna(subset=["player_id"])
        .groupby(["season", "season_end", "player_id"], as_index=False)
        .agg(player=("player", "first"),
             total_salary=("salary", "sum"),
             n_teams=("team", "nunique"),
             teams=("team", lambda s: "/".join(sorted(set(s))))))
# salary sum of all-NaN group -> 0; restore NaN so undisclosed stays undisclosed
salary_known = (sal.dropna(subset=["player_id"])
                   .groupby(["season", "player_id"])["salary"]
                   .apply(lambda s: s.notna().any()))
g = g.merge(salary_known.rename("has_salary"),
            on=["season", "player_id"], how="left")
g.loc[~g["has_salary"], "total_salary"] = pd.NA
g = g.drop(columns="has_salary")

g = g.merge(cap, on="season", how="left")
g["pct_of_cap"] = (g["total_salary"] / g["salary_cap"] * 100).round(2)
g = g.sort_values(["season", "total_salary"], ascending=[True, False])
g.to_csv(os.path.join(DATA, "player_season_salaries.csv"), index=False)

print(f"team_player_salaries: {len(team)} rows")
print(f"player_season_salaries: {len(g)} rows "
      f"({g.player_id.nunique()} distinct players, {g.season.nunique()} seasons)")
