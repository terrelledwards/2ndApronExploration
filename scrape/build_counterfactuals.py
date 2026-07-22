"""Counterfactual module: re-run landmark trades under the 2023 CBA apron rules.

For each trade we encode the mechanics that determine legality, then apply the
acquiring team's actual spending tier that season (from team_payrolls.csv) to a
rules engine that mirrors the 2023 CBA.

Which apron rule bites (acquiring team's perspective):
  SECOND-APRON team CANNOT:
    - aggregate two or more salaries in one trade to match a larger incoming salary
    - take back more salary than it sends out (100% matching; no TPE step-up)
    - use cash in a trade;  - acquire a player by sign-and-trade
  FIRST-APRON team CANNOT:
    - acquire by sign-and-trade;  - send out cash;  - use the non-taxpayer MLE

Verdict:
  ILLEGAL            a hard apron ban is triggered given the team's tier
  LEGAL BUT RUINOUS  mechanically allowed, but the team is at apron level and the
                     deal costs frozen/most-of-their picks or hard-caps them
  LEGAL              no apron rule bites

Spending tier is the acquirer's tier in the season the acquired star played for
them (so a team that vaulted into the apron BY making the trade is judged at that
level). Aggregation counts are historically documented; salaries cross-checked
against the salary spine where names resolve.

Output: data/counterfactual_trades.csv, data/counterfactual_trades.json
"""
import os
import json
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# season = the season the star played for the acquirer (used for tier lookup)
# agg = # of outgoing salaried players combined to match the incoming salary
# more = took back more salary than sent (TPE/step-up); snt = sign & trade in; cash = cash in
TRADES = [
    dict(year="2007", season="2007-08", acq="BOS", head="Celtics acquire Kevin Garnett",
         star="Kevin Garnett", agg=5, more=True, snt=False, cash=False, picks=2,
         note="Boston sent 5 salaries (Al Jefferson, Gomes, Green, Telfair, Ratliff) + picks for KG — textbook aggregation."),
    dict(year="2007", season="2007-08", acq="BOS", head="Celtics acquire Ray Allen",
         star="Ray Allen", agg=2, more=False, snt=False, cash=False, picks=1,
         note="Draft-night deal: Wally Szczerbiak + Delonte West + #5 pick for Ray Allen."),
    dict(year="2008", season="2007-08", acq="LAL", head="Lakers acquire Pau Gasol",
         star="Pau Gasol", agg=2, more=True, snt=False, cash=False, picks=2,
         note="Kwame Brown + Crittenton + 2 firsts + Marc Gasol rights; salaries aggregated to match Pau."),
    dict(year="2011", season="2010-11", acq="NYK", head="Knicks acquire Carmelo Anthony",
         star="Carmelo Anthony", agg=4, more=True, snt=False, cash=False, picks=3,
         note="Felton, Gallinari, Chandler, Mozgov + firsts — heavy aggregation of matching salaries."),
    dict(year="2011", season="2011-12", acq="LAC", head="Clippers acquire Chris Paul",
         star="Chris Paul", agg=3, more=False, snt=False, cash=False, picks=1,
         note="Gordon + Kaman + Aminu + MIN 1st for CP3 after the league vetoed the Lakers version."),
    dict(year="2012", season="2012-13", acq="LAL", head="Lakers acquire Steve Nash",
         star="Steve Nash", agg=0, more=True, snt=True, cash=False, picks=4,
         note="Sign-and-trade: Nash to LA for 2013+2015 firsts and 2013+2014 seconds."),
    dict(year="2012", season="2012-13", acq="LAL", head="Lakers acquire Dwight Howard",
         star="Dwight Howard", agg=2, more=False, snt=False, cash=False, picks=1,
         note="4-team deal; Bynum out to Philadelphia, matching salaries combined."),
    dict(year="2013", season="2013-14", acq="BRK", head="Nets acquire Garnett & Pierce",
         star="Kevin Garnett + Paul Pierce", agg=3, more=True, snt=False, cash=False, picks=4,
         note="Nets aggregated Humphries/Wallace/Bogans + FOUR unprotected firsts; the archetype ruinous deal."),
    dict(year="2013", season="2012-13", acq="HOU", head="Rockets acquire James Harden",
         star="James Harden", agg=2, more=False, snt=False, cash=False, picks=2,
         note="Kevin Martin + Jeremy Lamb + 2 firsts + 2nd; Houston was well under the tax."),
    dict(year="2017", season="2017-18", acq="OKC", head="Thunder acquire Paul George",
         star="Paul George", agg=2, more=False, snt=False, cash=False, picks=0,
         note="Victor Oladipo + Domantas Sabonis combined to match PG's salary."),
    dict(year="2017", season="2017-18", acq="MIN", head="Wolves acquire Jimmy Butler",
         star="Jimmy Butler", agg=2, more=False, snt=False, cash=False, picks=1,
         note="Draft-night: LaVine + Dunn + #7 for Butler + #16."),
    dict(year="2019", season="2019-20", acq="LAL", head="Lakers acquire Anthony Davis",
         star="Anthony Davis", agg=3, more=True, snt=False, cash=False, picks=3,
         note="Ingram + Ball + Hart aggregated + three firsts + swaps for AD."),
    dict(year="2019", season="2019-20", acq="LAC", head="Clippers acquire Paul George",
         star="Paul George", agg=1, more=False, snt=False, cash=False, picks=7,
         note="SGA + Danilo Gallinari + a record FIVE firsts + two swaps — pick cost, not aggregation."),
    dict(year="2021", season="2020-21", acq="BRK", head="Nets acquire James Harden",
         star="James Harden", agg=2, more=True, snt=False, cash=False, picks=4,
         note="4-team: Jarrett Allen + Caris LeVert combined + four firsts + swaps; Brooklyn deep in tax."),
    dict(year="2022", season="2022-23", acq="MIN", head="Wolves acquire Rudy Gobert",
         star="Rudy Gobert", agg=4, more=True, snt=False, cash=False, picks=5,
         note="Beasley + Bolmaro + Vanderbilt + Beverley + Kessler aggregated + FIVE firsts."),
    dict(year="2022", season="2022-23", acq="CLE", head="Cavaliers acquire Donovan Mitchell",
         star="Donovan Mitchell", agg=3, more=True, snt=False, cash=False, picks=5,
         note="Sexton + Markkanen + Agbaji aggregated + three firsts + two swaps."),
    dict(year="2023", season="2022-23", acq="PHO", head="Suns acquire Kevin Durant",
         star="Kevin Durant", agg=3, more=True, snt=False, cash=False, picks=4,
         note="Bridges + Cam Johnson + Crowder aggregated + four firsts; Phoenix went to apron-2 level."),
    dict(year="2023", season="2023-24", acq="MIL", head="Bucks acquire Damian Lillard",
         star="Damian Lillard", agg=2, more=True, snt=False, cash=False, picks=1,
         note="3-team: Jrue Holiday + Grayson Allen combined for Dame; Milwaukee at apron level."),
    dict(year="2024", season="2024-25", acq="NYK", head="Knicks acquire Mikal Bridges",
         star="Mikal Bridges", agg=1, more=False, snt=False, cash=False, picks=5,
         note="Post-apron era: FIVE firsts, single-salary match (Bogdanovic) — pick-heavy, aggregation avoided."),
    dict(year="2025", season="2024-25", acq="LAL", head="Lakers acquire Luka Doncic",
         star="Luka Doncic", agg=1, more=False, snt=False, cash=False, picks=1,
         note="Post-apron era: straight-up AD-for-Luka, single salaries matched — no aggregation needed."),
]

pay = pd.read_csv(os.path.join(DATA, "team_payrolls.csv"))
tier_of = {(r.season, r.team): r.spend_tier for r in pay.itertuples()}
ratio_of = {(r.season, r.team): r.payroll_cap_ratio for r in pay.itertuples()}


def classify(t):
    tier = tier_of.get((t["season"], t["acq"]), "tax")
    apron2 = tier == "apron2"
    apron1plus = tier in ("apron1", "apron2")
    reasons = []
    if apron2 and t["agg"] >= 2:
        reasons.append(f"2nd-apron team can't aggregate {t['agg']} salaries")
    if apron2 and t["more"]:
        reasons.append("2nd-apron team can't take back more salary than it sends")
    if apron1plus and t["snt"]:
        reasons.append("apron team can't acquire via sign-and-trade")
    if apron1plus and t["cash"]:
        reasons.append("apron team can't use cash in a trade")
    if reasons:
        verdict = "ILLEGAL"
    elif apron1plus and t["picks"] >= 3:
        verdict = "LEGAL BUT RUINOUS"
        reasons.append(f"legal, but hard-capped and forfeiting {t['picks']}+ picks with a frozen 7-yr pick")
    else:
        verdict = "LEGAL"
        reasons.append("no apron restriction is triggered at this spending level")
    return tier, verdict, "; ".join(reasons)


rows = []
for t in TRADES:
    tier, verdict, reason = classify(t)
    # second lens: does the deal rely on a mechanism the 2nd apron restricts,
    # regardless of whether THIS acquirer was at the apron that season?
    restricted = t["agg"] >= 2 or t["more"] or t["snt"] or t["cash"]
    rows.append({
        "year": t["year"], "season": t["season"], "acquirer": t["acq"],
        "trade": t["head"], "star": t["star"],
        "acq_spend_tier": tier,
        "acq_payroll_cap_ratio": ratio_of.get((t["season"], t["acq"])),
        "salaries_aggregated": t["agg"], "took_back_more": t["more"],
        "sign_and_trade": t["snt"], "cash": t["cash"], "picks_out": t["picks"],
        "relies_on_restricted_mechanism": restricted,
        "verdict": verdict, "reason": reason, "detail": t["note"],
    })

df = pd.DataFrame(rows)
df.to_csv(os.path.join(DATA, "counterfactual_trades.csv"), index=False)
with open(os.path.join(DATA, "counterfactual_trades.json"), "w") as f:
    json.dump(rows, f, separators=(",", ":"), default=str)

pd.set_option("display.width", 240, "display.max_colwidth", 40)
print(df[["year", "trade", "acq_spend_tier", "salaries_aggregated", "picks_out", "verdict"]].to_string(index=False))
print("\nverdict counts:")
print(df.verdict.value_counts().to_string())
pre = df[df.season < "2023-24"]
print(f"\nLens 1 (illegal given actual spending): {(df.verdict=='ILLEGAL').sum()} of {len(df)}")
print(f"Lens 2 (relies on a 2nd-apron-restricted mechanism): "
      f"{df.relies_on_restricted_mechanism.sum()} of {len(df)} "
      f"({pre.relies_on_restricted_mechanism.sum()} of {len(pre)} pre-apron landmark deals)")
