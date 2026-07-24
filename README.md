# The Second Apron and the Reshaped NBA

A sports-analytics project evaluating how the 2023 CBA's **second apron** has reshaped the
NBA — competitive balance, trade activity, free agency, player compensation, and the trade
market itself — with a comparison to how other leagues (NFL, MLB, Premier League) control costs.

See [`nba-second-apron-research-plan.md`](nba-second-apron-research-plan.md) for the full
research design (treatment timeline, three-axis player-grouping framework, and workstreams).

## Interactive dashboard

[`nba_apron_dashboard.html`](nba_apron_dashboard.html) — a self-contained page (open in any
browser; no server needed) with six era-shaded, tabbed, interactive views:

| Tab | What it shows |
|---|---|
| **Parity** | Effective contenders & top-3 title share by season; champions by preseason rank |
| **Trades** | Total / multi-team / deadline-week trades by season |
| **Free Agency** | Signing-speed compression; All-Star movement rate |
| **Compensation** | Pay-vs-production surplus map (per season, filterable by team roster); stars' share of the cap over time |
| **Apron Rules** | Counterfactual trade timeline + ledger; big-spender aggregation rate |
| **Leagues** | Cross-league balance, spending inequality, and penalty-currency taxonomy |

Every chart has a hover layer and an accessible data table; the page is theme-aware and
responsive. Rebuild its embedded data with `scrape/build_dashboard_data.py`.

## Headline findings

- **Parity rebounded.** Effective title contenders fell to 3.3 in the 2016-17 superteam era,
  then recovered to ~10 under the apron — with a different champion every year.
- **Trades rerouted, didn't freeze.** Total trades are up; multi-team (3+) deals nearly
  tripled (2.8 → 9.3/yr) as teams route salary around the aggregation ban.
- **Free agency compressed** from a ~27-day median signing window (big contracts) to ~7 days.
- **Star movement fell** from a 25% peak (2017 CBA) to 14% under the apron.
- **Stars take a smaller slice** of the cap than a decade ago (Kobe 51.9% in 2013-14 vs ~38% today).
- **The aggregation ban binds its targets.** Big spenders' salary-aggregation rate roughly
  halved (0.24 → 0.14); the biggest spenders now aggregate *least*, reversing history.
- **Cross-league:** cap hardness sets spending inequality (NFL 1.2× → EPL 8.4×) but not
  balance — a cap controls spending; league structure (playoffs, draft) controls balance.

## Repository layout

```
nba_apron_dashboard.html      the six-tab interactive dashboard (self-contained)
nba-second-apron-research-plan.md   research design + findings log
parity_analysis.py            odds-based competitive-balance metrics by CBA era
*.csv (root)                  parity / odds inputs + outputs (futures, win totals)
data/                         collected + computed datasets (see below)
scrape/                       scrapers and metric builders
scrape/cache/                 raw HTML cache (git-ignored, ~480 MB, regenerable)
```

## Datasets (`data/`)

**Salary spine** (Basketball-Reference team-season tables, 2005-06 → 2025-26, keyed to B-Ref player IDs):
| File | Description |
|---|---|
| `salaries_by_season.csv` | Raw team × season × player × salary (12,186 rows) |
| `team_player_salaries.csv` | Raw rows + `pct_of_cap` |
| `player_season_salaries.csv` | One row per player-season (mid-season trades summed) |
| `experience_by_season.csv` | Years of experience + CBA-eligibility bucket (axis A) |
| `advanced_by_season.csv` | BPM / OBPM / DBPM / VORP / WS / PER / MP (axis B) |
| `player_season_spine.csv` | **Full spine**: pay × experience × impact, tiers + `surplus_value` |
| `salary_cap_history.csv` | League salary cap by season |
| `team_payrolls.csv` | Team-season payroll + spending tier (tax/apron analog) |

**Transactions & derived metrics** (B-Ref transaction logs):
| File | Description |
|---|---|
| `transactions.csv` | 20,604 parsed transactions (trade/signing/waiver/…) with aggregation flag |
| `trade_metrics_by_{season,era}.csv` | Trade timing (offseason/in-season/deadline), multi-team, aggregation |
| `fa_metrics_by_{season,era}.csv`, `fa_signing_timeline.csv` | Signing timing + star movement |
| `counterfactual_trades.csv` / `.json` | 20 landmark trades judged under 2023 apron rules |
| `apron_team_trades_by_tier_era.csv`, `bigspender_agg_by_season.csv` | Aggregation by spending tier |
| `cross_league.json` | Title concentration, payroll dispersion, penalty taxonomy (NBA/NFL/MLB/EPL) |
| `dashboard_data.json` | Everything above, consolidated for the dashboard |

**Parity / odds** (repo root): preseason championship futures and win-total lines with computed
balance metrics (`parity_metrics_by_{season,era}.csv`).

## Reproducing

```bash
python3 -m venv .venv
.venv/bin/pip install pandas requests beautifulsoup4 lxml

# 1. Scrape (throttled + disk-cached; ~35 min cold, instant on re-run)
.venv/bin/python scrape/scrape_salaries.py
.venv/bin/python scrape/scrape_advanced.py
.venv/bin/python scrape/scrape_transactions.py

# 2. Build the spine + metrics
.venv/bin/python scrape/build_spine.py
.venv/bin/python scrape/build_experience.py
.venv/bin/python scrape/build_full_spine.py
.venv/bin/python scrape/parse_transactions.py
.venv/bin/python scrape/build_trade_metrics.py
.venv/bin/python scrape/build_fa_metrics.py
.venv/bin/python scrape/build_team_payrolls.py
.venv/bin/python scrape/build_counterfactuals.py
.venv/bin/python scrape/build_apron_team_trades.py
.venv/bin/python scrape/build_cross_league.py
.venv/bin/python parity_analysis.py

# 3. Consolidate for the dashboard
.venv/bin/python scrape/build_dashboard_data.py
```

Every fetched page is cached under `scrape/cache/` (git-ignored), so re-runs never re-hit
Basketball-Reference. The dashboard's data is embedded at build time, so the published HTML
is fully self-contained.

## Data sources

Basketball-Reference (salaries, cap history, advanced stats, transactions); covers.com /
sportsoddshistory (historical betting odds); Wikipedia (cross-league champion lists, verified);
public payroll trackers for cross-league spending. See the research plan for the full source table.

## Caveats

- ~4.6% of salary rows are undisclosed (two-way / 10-day contracts), kept as `NaN`.
- Recent team salary tables are transaction-inclusive (waived players, dead money, call-ups),
  which inflates per-team row counts; filter on disclosed salary for roster counts.
- Post-apron seasons (2024-25 onward) are **early evidence** — ~2 post vs. ~18 pre-treatment seasons.
- Counterfactual verdicts judge each trade's *mechanics* against the apron rulebook given the
  acquirer's spending tier that season; they are analytical, not official league rulings.
- Cross-league payroll ratios use each league's own reported basis (NFL cap, NBA cap-sheet,
  MLB opening-day payroll, EPL wages) — comparable in magnitude, not to the dollar.
