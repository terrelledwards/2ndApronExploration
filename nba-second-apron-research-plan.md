# The Second Apron and the Reshaped NBA — Research Plan

**Goal:** Evaluate the effects of the 2023 CBA's second apron on the NBA — player compensation, competitive balance, trade activity, free agency, and cap punitiveness — with comparison to other leagues.

**Deliverables:** Written report + interactive dashboard.

---

## 1. Timeline & treatment definition

- **Pre-period:** 2005-06 through 2022-23 (spans the 2005, 2011, and 2017 CBAs — allows era-vs-era, not just before/after).
- **Transition:** 2023-24 (CBA signed June 2023; apron exists but harshest rules not yet active — expect *anticipation effects*).
- **Post-period:** 2024-25 onward (full second-apron restrictions: no salary aggregation, no cash in trades, frozen picks, no taxpayer MLE, etc.).
- **Key caveat:** ~2-3 post-treatment seasons vs. ~18 pre. All post-apron findings framed as early evidence; distinguish rule effects from anticipation effects.

## 2. Player grouping framework (three axes)

Every player-season gets coded on all three:

**A. Years of experience** (aligned to CBA max-contract eligibility)
- 0-4: rookie scale / early career (cheap-labor pool)
- 5-6: post-rookie, 25% max eligible
- 7-9: 30% max eligible
- 10+: 35% max / supermax eligible

**B. Performance (impact metric)**
- RAPTOR (FiveThirtyEight, historical through 2022-23, archived on GitHub)
- LEBRON (BBall Index, 2009-present, ongoing)
- Calibrate the two on the 2009-2023 overlap; bucket into tiers (e.g., All-NBA level / high starter / starter / rotation / replacement).

**C. Salary as % of cap**
- <5% (minimums, second-rounders)
- 5-15% (MLE / role-player class — the "middle class")
- 15-25% (sub-max starters)
- 25-30% (max)
- 30%+ (supermax)

Crossing B × C gives **surplus value** (production tier minus pay tier) — the currency most questions reduce to. Crossing A × C shows where teams buy their surplus (prediction: apron teams shift toward axis-A group 0-4).

## 3. Workstream 1 (first up): Parity & trade/FA trends

### 3a. Competitive balance
- **Preseason title odds concentration** (HHI / entropy of implied championship probabilities), by season. Best proxy for "how many teams are trying/able to win."
- Standings dispersion: std dev of win%, count of teams within 5 games of play-in.
- Champion & finalist payroll rank + luxury tax status, by season.
- **"Doomed by contracts" test:** define bad-contract position (high payroll, low surplus value, negative-value deals >15% of cap); track those teams' next-3-season win% and odds movement, pre vs. post apron.

### 3b. Trade activity
- Trade counts per league-year, split offseason vs. in-season vs. deadline week.
- Players and salary dollars moved per trade; frequency of salary-aggregation trades (the mechanism the apron bans).
- Number of teams participating in deadline trades; buyers vs. sellers among tax-line teams.
- **Counterfactual module (later flagship):** re-run ~20 landmark trades from 2005-2023 under 2023 rules → legal / legal-but-ruinous / illegal.

### 3c. Free agency timeline
- Days from FA opening to signing, distribution by year.
- Star signings (top salary decile) — do they sign first or last? Has order inverted?
- Extension share: % of big contracts signed as extensions vs. free agency (extensions have been displacing FA — quantify).
- All-NBA player movement rate per season (are more/fewer stars changing teams?).

### ✅ Workstream 3 — DATA + FIRST FINDINGS (2026-07-21)
Source: B-Ref transaction logs (`data/transactions.csv`, 20,604 parsed transactions). Metric files:
`trade_metrics_by_{season,era}.csv`, `fa_metrics_by_{season,era}.csv`, `fa_signing_timeline.csv`.
Builders: `scrape/parse_transactions.py`, `build_trade_metrics.py`, `build_fa_metrics.py`.

**Trades (per-year averages by era — 2005 / 2011 / 2017 / apron CBA):**
- Total trades: 46 → 51 → 55 → **59** — trading is *up*, not frozen, at league level.
- Multi-team (3+) trades: 2.8 → 5.3 → 6.7 → **9.3** — the apron-era workaround for the aggregation ban (route salary through a third team).
- Deadline-week trades: 9 → 10.5 → 16 → **22** — busiest deadlines ever under the apron.
- Salary-aggregation share: steady ~42-49% league-wide (apron bans it only for 2nd-apron teams → next step: isolate those teams).

**Free agency:**
- Signing timing compressed hard: median signing day for big (≥15%-of-cap) contracts fell ~27 days after open (2005 CBA) → **~7 days** (apron). The July 1-2 frenzy is real.
- Star (All-Star-level, impact_tier≥4) movement rate: 12% → 17% → **25%** (2017 empowerment peak) → **14%** (apron). Fewer stars change teams now.
- Caveat: 2011-12 (lockout) and 2020-21 (COVID) excluded from FA timeline — FA opened in Dec/Nov, not July.
- Still TODO: extension-vs-FA share (needs extension flag from B-Ref contract pages).

## 4. Queued workstreams

**W2 — Compensation shifts:** star share of team payroll over time; middle-class squeeze (count and $ share of 5-15%-of-cap contracts); supermax uptake and outcomes; "should stars take less" reframed as: what discount, if any, changes a team's apron position and title odds.

**W3 — Punitiveness:** all-in cost of an identical payroll (e.g., $220M in 2026 dollars, cap-scaled backward) under 2005 / 2011 / 2017 / 2023 CBAs — dollars *plus* basketball-currency penalties (frozen picks, lost exceptions, no aggregation). Punitiveness index over time.

**W4 — Cross-league comparison:** penalty-currency taxonomy — NBA 2023 (money + basketball penalties), EPL PSR (sporting penalties: point deductions), MLB CBT (money + draft picks), NFL (hard cap). Compare 20-year title concentration (HHI) across leagues against cap hardness.

**W5 — Further questions (mini-projects, roughly prioritized):**
1. Draft pick value then vs. now (in $ or replacement-level production) — picks are the currency apron teams have left; expect value inflation.
2. Title window: seasons from a core's first max contract to contention exit; test the "5-year window" hypothesis.
3. Is parity good for the league? Ratings/revenue vs. market size of finalists; big-market-champion seasons vs. league revenue growth.
4. Spending → ticket prices, wins, TV market size (elasticities).
5. Would a higher BRI split change behavior? (modeling exercise, not empirical.)

## 5. Data sources — verified 2026-07-16

| Data | Source | Status |
|---|---|---|
| Current contracts, payrolls, cap history | Basketball-Reference /contracts/ | ✅ Works — clean tables, 6 yrs forward per team |
| Transactions (trades, signings, waivers, **dated**) | Basketball-Reference /leagues/NBA_YYYY_transactions.html | ✅ Works — full log incl. pick details; covers trade counts AND FA signing dates |
| Impact metric (1977–2023) | RAPTOR archive, 538 GitHub (raw CSVs) | ✅ Works — player-season, WAR included, keyed to B-Ref player IDs |
| Impact metric (2023–present) | LEBRON (BBall Index) | ⚠️ Data lives in JS app (fanspo embed) — needs browser scrape or manual export. **Fallback: B-Ref BPM/VORP** (fully accessible, covers all seasons) |
| Preseason title odds (decades back) | covers.com/sportsoddshistory (nba-main per season) | ✅ Works — per-season Finals futures + win totals + playoff series prices |
| Historical player salaries by season | ~~HoopsHype / Spotrac~~ → **B-Ref team-season salary tables** | ✅ **COLLECTED 2026-07-20** — HoopsHype/Spotrac confirmed blocked; instead scraped the `salaries2` table from every team-season page (30 teams × 21 seasons, 12,186 player-seasons), keyed to B-Ref player IDs. See `data/` + `scrape/`. |
| Stats, standings, playoffs, awards | Basketball-Reference | ✅ Works |
| stats.nba.com (nba_api) | NBA official | ❌ Times out from this environment; not needed (B-Ref covers it) |
| CBA rules ground truth | Larry Coon's CBA FAQ (cbafaq.com) | Untested; static site, low risk |
| Other leagues | PSR docs, MLB CBT history, OverTheCap | Untested yet |

**~~Biggest gap~~ (RESOLVED 2026-07-20):** league-wide historical salary-by-season table is now built. Solved via option (b)-adjacent: B-Ref *team-season* pages (not per-player) — one `salaries2` table each, ~650 throttled+cached requests. Outputs:
- `data/salaries_by_season.csv` — raw team × season × player × salary (12,186 rows)
- `data/team_player_salaries.csv` — raw + `pct_of_cap` (per team-season-player)
- `data/player_season_salaries.csv` — **one row per player-season** (mid-season trades summed), with `n_teams`, `teams`, `salary_cap`, `pct_of_cap` (11,178 rows, 2,331 players)
- `data/salary_cap_history.csv` — league cap by season (nominal + partial inflation-adjusted)

Validated against known values (Kobe $30.5M/2013-14, Curry $59.6M/2025-26, GSW $206.8M top payroll 2023-24). Caveats: ~4.6% of rows have undisclosed salary (two-way/10-day — kept as NaN, flagged); recent team tables are transaction-inclusive (waived/dead-money + call-ups → ~24 entries/team) — correct for cap analysis, filter on disclosed salary for pure roster counts.
~~Remaining spine columns still to add~~ **(DONE 2026-07-21):** axis A (experience) + axis B (impact) now joined on `player_id`:
- `data/experience_by_season.csv` — years of experience (from cached team roster tables, zero new requests) + CBA-eligibility buckets.
- `data/advanced_by_season.csv` — BPM/OBPM/DBPM, VORP, WS, PER, USG%, MP (21 season pages). Chosen over RAPTOR because it covers the post-apron seasons (2024-25+) the RAPTOR archive lacks, consistently across all 21 seasons.
- `data/player_season_spine.csv` — **the full spine**: pay (axis C) × experience (A) × impact (B), with ordinal pay/impact tiers and `surplus_value = impact_tier − pay_tier`. Validated: 2024-25 top bargains = Wembanyama/Şengün/J.Williams (young + cheap + elite); top overpays = Beal/George/Booker (max $ + low BPM). Tier thresholds documented in `scrape/build_full_spine.py`.

## 6. Dashboard concept

One page per workstream: parity (odds concentration timeline), trades (volume + type by year), FA (signing-date distributions), compensation (surplus-value scatter: pay% vs. impact tier, animated by season), punitiveness (payroll cost across CBAs). Report narrates; dashboard lets readers explore.

## 7. Immediate next steps

1. Verify data availability: pull one season each of Spotrac salaries, RealGM transactions, RAPTOR archive, LEBRON — confirm access and formats.
2. Build the player-season spine (player × season × salary × % of cap × experience × metric tier), 2005-present.
3. Compute first parity metrics (3a) as proof of concept.
