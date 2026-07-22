# The Second Apron and the Reshaped NBA

A sports-analytics project evaluating how the 2023 CBA's **second apron** has affected the
NBA — player compensation, competitive balance, trade activity, free agency, and cap
punitiveness — with comparison to other leagues (EPL PSR, MLB CBT, NFL cap).

See [`nba-second-apron-research-plan.md`](nba-second-apron-research-plan.md) for the full
research design (treatment timeline, player-grouping framework, and workstreams).

**Interactive dashboard:** [`nba_apron_dashboard.html`](nba_apron_dashboard.html) — a
self-contained page (open it in any browser) with tabbed, era-shaded charts for parity,
trades, free agency, and compensation. Rebuild its embedded data with
`scrape/build_dashboard_data.py`.

## Repository layout

```
data/        Collected + computed datasets (CSV)
scrape/      Data collection scripts (Basketball-Reference scrapers)
*.csv        Parity / odds datasets (championship futures, win totals)
parity_analysis.py   Odds-based competitive-balance metrics by CBA era
```

## Datasets

### Salaries (`data/`)
Scraped from Basketball-Reference team-season salary tables, 2005-06 → 2025-26, keyed to
B-Ref player IDs (which link to the RAPTOR impact archive).

| File | Description |
|---|---|
| `salaries_by_season.csv` | Raw team × season × player × salary (12,186 rows) |
| `team_player_salaries.csv` | Raw rows + `pct_of_cap`, for team-payroll analysis |
| `player_season_salaries.csv` | One row per player-season (mid-season trades summed), with `n_teams`, `teams`, `salary_cap`, `pct_of_cap` |
| `salary_cap_history.csv` | League salary cap by season |

### Parity / odds (repo root)
Preseason championship futures and win-total lines, 2005-06 → 2025-26, plus computed
competitive-balance metrics (HHI, effective contenders, top-N title-probability share) by
season and by CBA era.

## Reproducing

```bash
python3 -m venv .venv
.venv/bin/pip install pandas requests beautifulsoup4 lxml
.venv/bin/python scrape/scrape_salaries.py   # throttled + cached; ~35 min cold
.venv/bin/python scrape/build_spine.py        # builds the joined salary spine
```

The scraper caches every fetched page under `scrape/cache/` (git-ignored), so re-runs are
instant and never re-hit Basketball-Reference.

## Data sources

Basketball-Reference (salaries, cap history, stats), covers.com / sportsoddshistory
(historical betting odds). See the research plan for the full source table and access notes.

## Caveats

- ~4.6% of salary rows are undisclosed (two-way / 10-day contracts) — kept as `NaN`.
- Recent team salary tables are transaction-inclusive (waived players, dead money, mid-season
  call-ups), which inflates per-team row counts; filter on disclosed salary for roster counts.
- Post-apron seasons (2024-25 onward) are early evidence — ~2 post vs. ~18 pre-treatment seasons.
