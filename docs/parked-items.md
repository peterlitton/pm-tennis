# Parked Items

Every item deferred from the build queue with explicit activation
criteria. Walk this doc before starting a session of "what should I
work on next" — many candidates already exist with reasoning attached.

This is a *current state* doc — items are removed when activated or
retired (with retirement reason). The chronological history of each
item lives in `log/working_log.md`.

**Last full audit:** 2026-05-03 night, v0.6.11 ship (WS instability watchdog shipped — three pieces: [WS-RECOVERED] log line surfacing self-healed outages, auto-restart on N=5 consecutive failures via os._exit, uptime badge in dashboard header. Retires "WS instability — auto-restart watchdog + uptime badge" parked entry. Empirical foundation: incidents #1 [17:30 UTC, 30 min, manual restart] and #2 [23:45 UTC, ~32s, self-healed] from 2026-05-03 motivated the three-piece scope — recovery logging for the typical short-outage case, auto-restart for the sticky tail, badge for operator awareness across both)

---

## Contents

1. [Quick fixes](#quick-fixes) — under 30 minutes, no dependencies
2. [Ready to schedule](#ready-to-schedule) — clear scope, no blockers
3. [Parked with criteria](#parked-with-criteria) — needs evidence or data first
4. [Investigation candidates](#investigation-candidates) — research spikes
5. [Retired](#retired) — items closed without shipping (with reason)

---

## Quick fixes

Items under 30 minutes that should bundle with the next ship of any size.

### `pull_trade_history.py` summary sort fix

**Source:** Working log 2026-04-26 (line 1890)
**Estimated effort:** 5 minutes

The summary section in `scripts/pull_trade_history.py` sorts markets
ascending by realized P&L, which buries wins and shows only losses in
the visible top 20. The aggregate +$23,418 is correct; the per-market
view is misleading.

**Fix:** Sort descending by `abs(realized_pnl)` to surface the largest
P&L impacts (wins and losses) at the top, OR provide both sorts in
two side-by-side tables.

**Trigger to ship:** Next time we touch the analysis/ directory or
ship anything operationally adjacent. Don't ship in isolation.

### Repo cleanup follow-up

**Source:** PM-D.3 first-pass clone audit, 2026-05-03 night. Operator deferred to handle directly; recorded here so the items aren't lost.
**Estimated effort:** 10-15 minutes (operator-side; no code dependency)

PM-D.3 ran the new "Audit the repo on clone" principle (paid for by D.2 missing these across multiple sessions) and surfaced repo-hygiene items still tracked at HEAD as of v0.6.8 ship:

- `pm-dashboard/` directory at repo root — nested duplicate tree, ~8.6M, the literal anti-pattern PM-D.1's flat-tarball rule warned against
- Stray top-level files: `cross_feed_overrides.yaml`, `working_log_entry_2026-05-01.md` (canonical copies live in their proper subdirs)
- `.gitignore` not committed despite the cleanup working log entry stating it was added
- 4 `src/__pycache__/*.pyc` files (already cleaned per cleanup entry; verify gone post-next-deploy)

A partial cleanup tarball shipped (per `working_log.md` 2026-05-03 evening entry: `dashboard.{css,html,js}` and `src/__pycache__/` were `git rm`'d, `docs/README.md` Start-here pointer was fixed, root `README.md` was refreshed). Items above are remaining stragglers.

**Why parked, not blocking:** None affect production behavior. The nested directory is invisible to the running service. Operator preference is to handle directly when convenient. PM-D.3 caught these on first-pass clone and handed them back per operator direction.

**Trigger to ship:** Operator-driven, no Claude action required.

### Polymarket price extraction wrong-field bug

**Source:** PM-D.3 conversation, 2026-05-04 evening. Operator surfaced live Bai/Lu match showing impossible price sum (Bai 70¢ + Lu 4¢ = 74¢, not ~100¢). Order book screenshots confirmed real Polymarket prices were Bai 69-70¢ / Lu 31-32¢ with healthy 1¢ spreads on both sides. Dashboard reading wrong field for one side.

**Status:** Active diagnostic — root cause not yet identified. Two diagnostic ships deployed:
- v0.6.12 (PRICEDIAG-WS) — per-slug WS market_data + trade payload loggers
- v0.6.13 (PRICEDIAG-REST) — per-slug REST events payload logger

**Discovery progression:**

1. **Initial trigger (2026-05-04 evening):** Bai/Lu sum 74¢ during live ATP Challenger qualifier. Order book screenshots confirmed real bid/ask ~31¢/32¢ on Lu side, ~69¢/70¢ on Bai side, both 1¢ spreads with thousands of shares of liquidity. Dashboard showed Lu at 4¢ — frozen at session-low value while Bai's price moved correctly.

2. **Pattern repeats:** Wong Hong Yi vs Yao showed same failure mode at 26+56=82¢. Lajovic vs Choinski at 95¢. All three matches were live Asian Challenger / qualifier markets. Most other live matches summed cleanly to ~100-105¢.

3. **v0.6.12 deployed:** captured 60+ raw WS market_data payloads after deploy. Findings:
   - WS payloads contain only YES-side book data (bids/offers/stats per slug)
   - No `marketSides` block in any captured WS payload — Path A in `_extract_prices_from_market_data` never fires from WS
   - Path B is the only active path: extracts best_ask, applies 5¢ spread guard, writes only `side_a_cents`
   - WS therefore can ONLY update side_a; side_b is entirely REST-owned by architecture
   - Lajovic/Choinski WS payload showed best_bid=9¢, best_ask=10¢, healthy 1¢ spread, BUT `stats.lowPx=4¢` (the session low — a single bad print earlier in the day). Pattern across affected matches: stuck-low side correlates with markets where one side has hit a low session price during one-sided dynamics.

4. **Initial hypothesis (REST broken on side_b) was a guess — not confirmed.** WS log inspection ruled out one path but did not identify the cause. The 4¢ value's origin has not been traced to a specific data field. Multiple plausible mechanisms remain.

**Hypotheses to test (none committed):**

- **H1:** REST `marketSides[1].quote.value` returning a stale/wrong value for low-liquidity matches with one-sided dynamics
- **H2:** REST has per-side timestamps showing one side is stale; the dashboard doesn't check them
- **H3:** Resolver merge logic has a stale-preservation bug between REST and WS writes (one source's value persists across the other source's update)
- **H4:** side_a/side_b → p1/p2 mapping has a failure mode (e.g., Bai's value being mapped to Lu's field, not a wrong-source-data issue at all)
- **H5:** `lastPriceSample.shortPx` (visible in WS payloads) is the No-side price, currently unused, which we should be reading for side_b
- **H6:** Some other field in REST is the correct authoritative source we're not using

**Diagnostic plan:**

1. v0.6.13 (PRICEDIAG-REST) deployed: per-slug one-shot logger captures full event JSON in `_extract_moneyline_with_prices`. Fires on every slug, ~100 logs total per process lifetime.
2. After next live match window with broken sums: pull logs, find broken-match REST payload + matching v0.6.12 WS payload for the same slug. Cross-reference fields.
3. Establish healthy-match baseline from REST captures of correctly-summing matches.
4. Audit the resolver merge path between REST writes, WS writes, and rendered `p1/p2_price_cents`. Look for stale-preservation, side-mapping issues.
5. After steps 1-4: hypothesis is confirmed or eliminated by data, then design fix specific to actual cause.

**Decisions explicitly NOT made:**
- No fix designed
- No derivation of side_b from side_a (operator declined; volatile spreads can legitimately make sums >100¢, and derivation would lose the volatility signal)
- No field substitutions, resolver changes, or fallback logic
- v0.6.13 is diagnostic-only, same shape as v0.6.12

**Closure criterion:**

1. Both v0.6.12 and v0.6.13 logs hit during a live match showing the bug
2. Cross-reference REST + WS payloads for the broken match
3. Cross-reference against healthy-match baselines (also captured)
4. Identify the actual data-flow path producing the wrong rendered value
5. Design fix specific to the identified cause
6. Verify on subsequent live matches by `p1_price_cents + p2_price_cents` falling in plausible band (95-130¢ range)

**Why parked at "Quick fixes" tier:** The extraction bug is a real correctness issue — operator could make a wrong trade on a market where one side reads 4¢ when reality is 31¢. Diagnostic patches shipped (no behavior change, zero risk). Once the bug is diagnosed, fix scope will likely be bounded to a single function. Graduates from Quick fix to Ready to schedule once root cause is identified.

**Cross-reference:**
- `log/working_log_entry_2026-05-04-pricediag.md` — initial v0.6.12 ship (now stale on diagnosis; superseded by next entry)
- `log/working_log_entry_2026-05-04-pricediag-rest.md` — v0.6.13 ship + updated diagnosis state
- `log/working_log_entry_2026-05-03-ws-diag.md` — prior 50-row diagnostic that produced the current Path B logic
- Latency-validation Finding 3 (empirical-probe-first discipline) — the discipline this investigation follows

---

## Ready to schedule

Items with clear scope and no remaining blockers. Ready when there's
a build session to allocate.

### Upcoming match rendering — SHIPPED, awaiting operator validation

**Status:** Shipped 2026-05-02 across two ship cycles (v0.5.9 + v0.6.0). Architecturally complete. Awaiting operator validation across multiple sessions before retiring.

**What shipped:**
- v0.5.9: API-Tennis fixtures REST poll (5min cadence) added concurrently with WS supervisor
- v0.6.0: Polymarket-only upcoming match render via `state.matches[pm:{ev_id}]` shadow records; pre-match edge badges (Step 5) finally visible

**First-deploy validation (2026-05-02):** 10 [PMONLY] created lines, 7 upcoming matches in header counter, Sinner/Zverev/Walton-Wong/Faria-Safiullin all rendering with ranks + prices + edge badges.

**Second validation observed live (2026-05-03 15:13):** clean shadow → live transition for Sinner/Zverev: `[PMONLY] transition: ev_id=10558 shadow=pm:10558 → live match found, popping shadow`. Worked exactly as designed.

**Retire when:** operator has used the dashboard with shadows visible across at least 3 trading sessions, including position-on-shadow observed cleanly through to settlement.


### Player database build — Steps A-E + F-shadow SHIPPED, F-flip + G remaining

**Status:** Multi-step build per `Player-DB-Build-Plan-2026-05-02-v3.md`. Steps A through E shipped 2026-05-03 including country flag rendering. Step F shipped in shadow mode 2026-05-03 night (v0.6.8). Remaining: flag flip to live + cleanup + Step G verification.

**What shipped 2026-05-03:**
- **Step A (v0.6.1):** `state.Player` dataclass adds `player_key: Optional[int]`. API-Tennis worker `_player()` extracts `first_player_key`/`second_player_key`. Verified live + fixtures matches show numeric player_keys.
- **Step C (no version bump, build script only):** `data/build_player_metadata.py` (~470 lines) including 140-entry COUNTRY_TO_ISO3 table covering all observed ATP/WTA standings countries.
- **CSV bundled (v0.6.2):** `data/player_metadata.csv` with 3,667 records, 2,196 ATP-ranked, 1,471 WTA-ranked, 94% with country_iso3.
- **Step D (v0.6.2):** `src/player_metadata.py` runtime lookup module — `lookup_by_key()`, `lookup_by_name()`, `lookup_by_name_all()`, `stats()`. Lazy-loads CSV at startup.
- **Step B+E (v0.6.3):** Polymarket-only shadow path bootstraps player_key + country via `lookup_by_name`; API-Tennis worker falls back to `lookup_by_key` when API-Tennis country missing. Verified shadows show 86%+ key coverage, 82%+ country coverage.
- **Country flags (v0.6.4):** 108 flat ISO-style SVGs bundled at `static/flags/{ISO}.svg` from country-flag-icons (MIT, ~62 KB total). 24×16px (3:2 ratio) matching existing placeholder dimensions. Mobile rendering remains hidden via existing `@media` rule. Real flags visible for first time on dashboard.
- **Name alias mechanism (v0.6.5):** `lookup_by_name` now consults `data/sackmann_overrides.yaml` for word-order variants (e.g. "Juan Pablo Ficovich" → "Pablo Ficovich Juan"). Reuses existing operator-controlled override system rather than building a separate aliases mechanism.
- **Step F shadow mode (v0.6.8):** `cross_feed.resolve_event_key` now computes both player_key and name-token paths every call. Env flag `CROSS_FEED_USE_PLAYER_KEY` (default `0`) controls which is authoritative. In shadow mode (default), name-token result is returned and disagreements are logged once per pm_event_id as `[STEPF-DIAG]` for post-deploy review. `ApiTennisMatchView` extended with `p1_player_key`/`p2_player_key` fields. `polymarket_worker._resolver_iteration` populates them in the projection. See `log/working_log_entry_2026-05-03-stepF-shadow.md`.

**Live system observations during ship:**
- Clean shadow → live transition observed for Sinner/Zverev (15:13:13): `[PMONLY] transition: ev_id=10558 shadow=pm:10558 → live match found, popping shadow`
- Step G interim: live 7/7 player_key, shadows 43/50 player_key (86%), shadows 41/50 country (82%)
- Argentine flag now renders next to Juan Pablo Ficovich (was placeholder before override)
- Empirical bootstrap spot-check (smoke test, 2026-05-03 night) — Polymarket-form names: Hurkacz/Andreeva/Kalinskaya resolve cleanly via `lookup_by_name`; Burruchaga and Kostyuk variants don't. Shadow mode will surface this concretely; remediation is `sackmann_overrides.yaml` entries (small, operator-curated).

**Remaining steps:**
- **Step F flag flip:** after 1-2 sessions of `[STEPF-DIAG]` capture confirming the player_key path is correct, set `CROSS_FEED_USE_PLAYER_KEY=1` on Render. Env-var-only change, no redeploy.
- **Step F cleanup ship:** after stable behavior post-flip, remove the env flag and the name-token fallback inside `resolve_event_key`. Shrinks function to player_key-only with overrides as fallback.
- **Step G:** final verification across all paths. ~10 min after cleanup ship.

**Retire when:** Step F flag flipped, cleanup ship lands, all `cross_feed: unmapped` log noise gone for known players, and any word-order overrides identified during shadow observation are in `sackmann_overrides.yaml`.

### Match archive worker (deferred half of Step 8)

**Source:** Working log 2026-04-26 PM
**Estimated effort:** 4-6 hours

Per-match archive JSONL writer that captures the full point-by-point
sequence when a match transitions to `finished` status. One file per
match; structured for replay.

**Purpose:** Forward-looking infrastructure for Direction Y (learned
indicators per [`Data-Driven-Indicators-Concept.md`](./Data-Driven-Indicators-Concept.md)). Also enables
post-mortem analysis of individual matches: "what did the dashboard
show at the moment of the third break point?"

**Why ready:** No data dependency — works against any match completing
in the live session. Independent of Step 7.

**Why not yet done:** Step 7 took precedence; match archives are not
on the critical path for Direction X analysis.

### Trade-count warning indicator

**Source:** Working log 2026-04-25; Draft 5 Finding 6
**Estimated effort:** Indicator definition: 1-2 hours. Wiring to live
position state: blocked on Step 9.

Indicator that warns when an open position has had ≥5 trades — Draft
5 found 7+ trade swings produce 28.6% win rate vs 63.6% for 1-2 trade
swings.

**Build the indicator definition independently:** threshold (5 vs 7?),
visual (warning pill on position row), version constant, state log
capture in `position.trade_count` when `position` field populates.

**Activation:** Wiring to live position state requires Step 9. The
*indicator logic* is independent and could ship now as a stub that
fires against a synthetic position field for testing.

**Why parked:** Wiring is the work. Building the stub without a
position field to test against is mostly speculative.

### Upstream feed down/stale signal on dashboard

**Source:** 2026-05-01 — API-Tennis WS upstream returned HTTP 502 for an extended period; dashboard showed stale/empty data with no explicit signal that upstream was down. Operator surfaced the gap. **Sharpened 2026-05-03 evening** — Polymarket markets WS broke for 30 minutes while REST polling continued, dashboard showed normal age counter throughout. Operator traded blind to the degradation.
**Estimated effort:** ~1-2 hours. Pure render + threshold logic.

The header design already reserves space for per-source health. Today: green dot + label + age (e.g., "API-Tennis 2s"). Today's behavior when upstream is down: stale age count keeps incrementing silently, no explicit "down" indicator. Today's behavior when WS is broken but REST is polling: age counter looks fresh because REST writes update the timestamp — operator can't distinguish sub-second WS prices from 15s REST prices.

**What to build:**
- Color/treatment shift based on `state.source_timestamps[<source>]` age vs threshold (covers full-feed-down case)
- **Distinguish WS-state from REST-state for Polymarket** (covers today's incident): if WS connection is alive AND last frame ≤ 30s, show "Polymarket Xs" green; if WS down but REST still updating, show degraded state (e.g. "Polymarket REST 15s" yellow); if both down, red. Underlying signal: the `polymarket_worker` already tracks WS connection state via the supervisor's reconnect loop — needs to surface a boolean to `state.feed_health` for the renderer to consume.
- Two sources: `api_tennis`, `polymarket`. Same overall logic, different thresholds (Polymarket polls every ~15s; API-Tennis is event-driven and naturally bursty).
- Visible without being a banner (operator preference TBD at build time).

**Decisions to make at build time** (not now):
1. Threshold values: when does "fresh" become "stale" become "down" for each source?
2. Visual treatment: color shift on existing dot, replacement label, dedicated banner, or combination?
3. Render location: footer (where dots live), header (next to live count), or top banner?
4. Polymarket WS-vs-REST presentation: two separate pills, one combined pill with degraded-state, or one pill with hover-detail?

**Why parked, not blocking:** Workers reconnect correctly during upstream outages — the bug is invisible-failure-mode, not broken-functionality. Operator can verify upstream health by external means (Render logs, status pages, direct curl). Build when there's appetite OR when the next WS instability incident provides clear motivation. The 2026-05-03 evening incident is the second data point arguing for this entry's activation; one more would justify scheduling.

### WS instability — auto-restart watchdog + uptime badge

**Status:** SHIPPED 2026-05-03 v0.6.11 — see Retired section below.

### Indicator legend / help surface

**Status:** SHIPPED 2026-05-03 v0.6.10 — see Retired section below.

---

## Parked with criteria

Items that need evidence or data accumulation before activation. Each
has explicit trigger criteria.

### Match state system mini-project

**Status:** Off-the-record planning brief authored 2026-04-30 by PM-D.1; memorialized in repo 2026-05-03 night under operator direction. Brief lives at [`design/PM-D1-match-state-system-mini-project-2026-04-30.md`](../design/PM-D1-match-state-system-mini-project-2026-04-30.md). Decisions pending; no previews drawn.

**Activation criteria (any of):**
- Operator wants Suspended/Medical-timeout/Just-finished treatment to ship — the brief stages Suspended as the first state to land, but as the first product of the system rather than as an ad hoc one-off
- Any new match-state visual treatment becomes a candidate (e.g. operator surfaces a tiebreak-highlight idea) — the systematizing intent is to prevent ad hoc drift before the second one-off treatment ships
- Operator instinct that the dashboard's visual coherence is starting to drift across states

**Background:** The dashboard today renders three match-lifecycle treatments — live (red dot, status text), upcoming (dimmed, time + countdown), finished (drops from list). Every other state collapses into "live" or doesn't appear. PM-D.1 was about to add a one-off rain-delay treatment when operator reframed: "your designs raise the question of the default condition for a match underway with a red dot. Maybe we need to consider all of the match conditions and develop a system vs ad hoc mods." That pivot triggered the brief.

**Scope:** Enumerate all 17 match-lifecycle states (4 pre-match / 3 live / 4 interruption / 5 terminal / 1 anomaly), define a small visual vocabulary (5 color tokens, 7 primitives) with composition rules, decide which states get distinct treatment vs collapse into shared treatments, draw side-by-side preview HTML for each operator-decision-point, document the system in a new `design/Match_State_System.md`, then ship Suspended as the first state under the framework. CSS class additions plus a `_classify_status` mapping in `src/api_tennis_worker.py` plus frontend renders.

**Effort:** ~2 sessions per the brief's cost breakdown — ~1 session of preview-driven decisions, ~0.5 documentation, ~0.5 build.

**Adjacent work to coordinate when activated:**
- **Path A vs B for upcoming-match rendering** (footnote 1 in the brief) — was pending in 2026-04-30. Resolved 2026-05-02 via Polymarket-only shadow path (v0.6.0 / `[PMONLY]`). State 2 (Scheduled today) is partially in production via shadows; states 3 (Starting soon) and 4 (Delayed start) decisions are unaffected. Brief footnote should be updated when the system activates.
- **State 17 (Stale data) overlaps with this doc's "Upstream feed down/stale signal on dashboard" entry** — same idea, different framing. Activation should merge them; row-level vs header-only signal becomes a state-system Step 5 preview decision.
- **Notification brief** (`PM-D1-event-notifications-brief-2026-04-30.md`, not in repo) — every state transition is potentially a notification trigger. State system defines *what is true about a match*; notification system defines *what happens when state changes*. State system ships first per the brief; notifications wire into it after.
- **Indicator legend / help surface** (this doc, "Ready to schedule") — both are dashboard-render-touching ships. Could ride together on one ship cycle if scope allows; the legend is footer-anchored, the state system is row-styling, mostly orthogonal.

**Why parked rather than now:** Building visuals iteratively means each new state treatment justifies itself locally without checking against a system, which produces drift. The Suspended treatment was about to be the first such drift in 2026-04-30; that's the trigger to stop and systematize. Today the activation pressure isn't there — the dashboard's three-treatment baseline is holding — but the moment any second one-off treatment becomes a candidate, this brief activates before that one-off ships. The brief is comprehensive enough that activation costs ~2 sessions, not weeks.

**Sequencing note:** PM-D.1's brief proposed shipping the state system before Step 7 trade attribution if Step 7 was several days out. Step 7 has since shipped and activated 2026-05-02; that sequencing question is resolved. State system can ship whenever activation criteria fire, no Step 7 dependency.

### Step 4.3 — momentum surprise

**Status:** Specced; reserved version slot in state recorder schema. Sackmann coverage blocker reduced 2026-05-02 (operator-weighted coverage near-100%).
**Activation criteria:** 3+ findings.md entries describing situations where the operator wished for an explicit "surprise" surface.

Pre-match prediction (Sackmann pre_pct) compared to in-match momentum
state. When the in-match leader is the pre-match underdog, that's a
surprise — a signal that live state is diverging from prior expectation.

**Pending design questions:**
- Numerical formulation (just delta vs. pre_pct, or scaled?)
- Visual placement (separate pill, or embedded in momentum pill?)
- Threshold for "meaningful" surprise

**Why parked:** Indicator design needs operator-narrative evidence
before being designed. Building speculatively risks shipping the wrong
thing. Sackmann coverage is no longer a soft blocker — operator-weighted
coverage measured at 98.3% on Madrid 2026-05-02.

### Step 9 — position display + exit signals

**Status:** Specced (visual reference in
[`design/dashboard_v0_7_position_design.html`](../design/dashboard_v0_7_position_design.html); behavior reference in
[`Exit-Signal-Architecture-Concept.md`](./Exit-Signal-Architecture-Concept.md)).
**Activation criteria:** After Step 7 / Direction X first run.

Position row beneath each match showing operator's open position with
exit-signal pills firing under various conditions.

**Why parked behind Step 7:** Step 9's exit signals will need tuning
thresholds, and tuning requires Direction X analysis, which requires
Step 7 trade attribution data. Building Step 9 first means shipping
un-tuned exit signals, then re-tuning later — wasted iteration.

**Could jump the queue if:** Running losses without stop-loss
protection becomes urgent enough to warrant un-tuned alerting better
than no alerting. Operator's call.

### Step 6 — live edge badge

**Status:** Pending observation evidence. Soft blockers updated 2026-05-02.
**Activation criteria:**
1. Findings.md evidence that operator wants live edge during matches
2. ~~Soft-coupled to Option B (fresh Elo)~~ — **resolved 2026-05-01** by Tennis Abstract refresh; Elo now reflects 2026-04-20 data
3. Operator's instinct: "do I want this signal or is it distracting?"

**2026-05-02 update:** Sackmann coverage was previously a soft blocker (concern that live edge would be silent on too many matches). Operator-weighted coverage measured 98.3% on Madrid — concern resolved. Activation now driven primarily by criterion (1) and (3).

Same data layer as pre-match edge badge (Step 5), different rendering
path. Compares pre_pct against current Polymarket price *during* live
matches, where the market price has already moved relative to the start.

### Option B — fresh Elo refresh pipeline (automation remaining)

**Status:** One-shot refresh shipped 2026-05-01 via `data/refresh_elo_from_tennisabstract.py`. CSVs now reflect Tennis Abstract data refreshed 2026-04-20 instead of Sackmann's static 2024-12-30 snapshot. **Automation pipeline still parked.**
**Activation criteria for automation work:**
1. Step 6 (live edge badge) build is prioritized — automation becomes a soft prerequisite to keep Elo fresh as match results land
2. OR: operator decides manual weekly re-runs are too much friction
3. OR: data-driven analysis surfaces that Elo staleness within a refresh cycle materially affects edge-badge accuracy

What's done:
- Sackmann's GitHub repos (tennis_atp, tennis_wta) confirmed dormant since 2024-12-30 — they cannot be the source going forward
- Tennis Abstract (tennisabstract.com) publishes weekly Elo tables under same author + methodology, license CC BY-NC-SA 4.0 (operator use is personal/non-commercial → qualifies)
- Scrape script writes CSVs in same schema `src/sackmann.py` consumes — drop-in replacement
- Country codes preserved via left-join from prior CSVs (~60% match rate)

What's NOT done — the automation pipeline:
- Refresh runs manually (operator triggers from local clone, commits the resulting CSVs)
- No scheduled cadence, no CI, no drift alerting
- Three contributing limits Tennis Abstract HTML doesn't publish: `country_iso3`, `last_match_date`, `matches_played`. Country preservation works via prior-CSV left-join but degrades over time as new players are added without country codes
- ATP rank coverage still depends on `data/refresh_rankings.py` depth — separate from Elo refresh

**Why automation parked:** One-shot fixes the staleness floor for current operator use. Automation has real engineering cost (cron infra, drift detection, schema-change monitoring on Tennis Abstract HTML) and value scales with how often the freshness matters. With pre-match trading limited (per Sackmann coverage limits entry), staleness within a week or two is unlikely to show up as a meaningful problem.

**Future scope when activated:**
- Scheduled run cadence (weekly to match Tennis Abstract's update cadence)
- Drift detection — alert if scrape returns 0 rows or wildly different counts
- Country code backfill source — Tennis Abstract player profile pages have country, but require per-player fetch (~500 requests). Worth building if/when country flag coverage is a real friction
- Last-match-date backfill — Tennis Abstract probably has match log per player; would let staleness profiling work post-refresh

### Sackmann coverage limits on pre-match indicators

**Status:** Known limitation, **substantially reframed 2026-05-02**. Original capture 2026-05-01 from `sackmann_profile.py` output. Updated 2026-05-01 (Elo staleness resolved by Tennis Abstract refresh). Reframed 2026-05-02 (operator-weighted coverage measured).
**Activation criteria:** Pre-match trading grows materially, OR Step 7 attribution surfaces a pre-match-vs-live difference, OR operator decides quality investment is worth it.

**Reframing 2026-05-02 — the headline number was misleading.**

The global coverage numbers (WTA 32%, ATP 9.8%, Ch. 0%) are weighted by ALL match-observations in the state log, including doubles, qualifying, ITF feeders, and other matches the operator never trades. They overstate the structural problem.

Operator-weighted coverage was measured today via `scripts/sackmann_coverage_focused.py`:

- **Madrid Open:** 98.3% Sackmann hit rate across 60 distinct player-sides in 30 distinct matches. Only 1 player missed: F. Auger-Aliassime (name-matching bug, hyphenated last name — see Investigation candidates).
- **Traded-pairs analysis (last 3 days):** script has a date-filter bug (rejects all activities); fix and re-run before trusting that number, but Madrid as a proxy is highly suggestive.

**What this changes:**

The "Sackmann coverage gap" is mostly not a gap on the matches that matter. Where attention goes, Sackmann is essentially complete. The classifier-routing bug below is real but affects far fewer operator-felt traded matches than the global numbers suggest.

**What's still true:**

1. Tennis Abstract's "10+ matches in last 52 weeks" filter limits the player population — lower-ranked / inactive players genuinely don't have Elo. This affects Challenger / ITF matches the operator does trade occasionally.
2. **Production classifier bug:** `_classify_tour` in `src/api_tennis_worker.py` routes "Challenger Women Singles" to `"Ch."` before checking WTA keywords; the Sackmann lookup branch (lines 685-704) only runs for ATP/WTA. WTA-tier ITF matches (Sorribes-style) get null Sackmann data even when players exist. **Lower priority now** — affects edge cases, not main flow.
3. **Rankings depth:** Deployed `sackmann_rankings_atp.csv` at 150 rows, `sackmann_rankings_wta.csv` at 249, even though `data/refresh_rankings.py` defaults `--limit 600`. Investigation candidate; possibly a quick win.

**Tooling already exists:** `scripts/sackmann_profile.py`, `scripts/sackmann_coverage_focused.py`, `scripts/inspect_state_log.py`, `data/refresh_elo_from_tennisabstract.py`.

**The architectural question stands:** what's the model meant to add that the Polymarket price doesn't already provide? Three paths: α (market-dynamics indicator using Polymarket prices as reference), β (broader fair-value source), γ (accept the structural limit, lean on momentum/score/price-trajectory for non-covered matches). Reframing doesn't change this question.

Live indicators (momentum, score, prices) are unaffected by this. Step 7 activation can proceed.

### Step 4.1 — momentum threshold tuning

**Status:** Reframed 2026-04-27. v2.0.0's 2/2 thresholds confirmed
calibrated correctly via diagnostic.
**Activation criteria:** Different friction surface than over/under
firing. Specifically: "leader fires but the wrong player" type
threshold problem (which side, not how often).

**Reframing reason:** Original parking was "pending observation
friction" — vague. After 2026-04-27 first live session, diagnostic
ran 49% leader / 43% none / 8% contested distribution. 2/2 thresholds
are correct for *firing rate*. Step 4.1 stays parked but for a
different friction type.

### Price trajectory indicator

**Status:** Pending observation friction.
**Activation criteria:** Operator-narrative evidence that price
movement context (sparkline, delta, arrow) is missing from current
dashboard surface.

Multiple plausible forms (sparkline / delta number / directional
arrow). Decide form once decision is made to ship.

**Why parked:** No friction observed yet. Don't build speculatively.

### Match-flash diagnostic

**Status:** Pending observed flash event. **Likely solved structurally
as a side-effect of upcoming-match-rendering build** (see
"Ready to schedule") — Path A's IANA timezone lookup addresses the
underlying parsing ambiguity. Retire concurrent with that build if
flash events stop being observed.
**Activation criteria:** A match that visibly flashes (renders briefly
then disappears) during a session, with logs captured to support
diagnosis.

Suspected cause from earlier investigation (working log Step 3.6):
upcoming-window filter rejection due to timezone parsing ambiguity in
`_start_time`. Hypothesis B in that entry covers the diagnosis path.

**Why parked:** Building a fix without diagnostic data risks
introducing a hardcoded tournament-zone lookup that gets it wrong
silently for non-European tournaments.

### Trading page contract source-of-truth refactor (Fix B)

**Status:** Parked 2026-05-01.
**Activation criteria:** Trading page cross-day fix (shipped 2026-05-01) reveals limitations that warrant a deeper refactor — e.g., 2-day lookback proves insufficient and operator wants longer holds, OR aggregate numbers across days become a frequent need, OR per-contract analysis tooling needs a stable contract identifier across days.

**Background:** The current trading page reads from per-day Polymarket activity slices and stitches contracts together via narrow + wide fetches (Fix A, shipped today). This works for the cross-day visibility case but doesn't solve the general problem of "treat a contract as a single thing across its lifetime."

**Fix B scope:** Build a `contracts.csv` (or similar persistent record) representing complete-life-of-contract entries: open timestamp, close timestamp, full fill list, lifecycle state, P&L, etc. Daily views become *filters* over this dataset, not separate datasets.

**Why parked:** Fix A (today's narrow + wide fetch in `/trading`) covers the immediate visibility gap. Fix B's value is architectural cleanliness — bigger refactor, no immediate operator-visible benefit beyond Fix A. Right time when Fix A's limitations bite, not before.

---

## Investigation candidates

Items requiring research that may or may not produce a concrete
deliverable.

### Hyphenated / multi-word last-name matching (PARTIALLY RESOLVED, full closure with Step F)

**Status:** Partially resolved 2026-05-03 via the player database build (Steps A-E shipped). Full structural closure ships with Step F.

**Resolution shipped:**
- API-Tennis worker now extracts `player_key` from every match payload (Step A). For live and fixtures matches, joins are key-based when downstream code uses them.
- `lookup_by_name` consults `data/sackmann_overrides.yaml` for word-order variants (Ficovich case 2026-05-03 PM). Operator can add one line per case to handle e.g. "Roman Andres Burruchaga" vs "Andres Burruchaga Roman".
- `player_metadata.csv` provides the canonical name → player_key mapping for ~3,667 players.

**What's still in name-matching land:**
- Cross-feed module (`src/cross_feed.py`) still uses name-token overlap for the live-match-to-Polymarket-event join. This is what produces the recurring `cross_feed: unmapped` log warnings.
- Step F (deferred) migrates this final path to player_key joins. Once shipped, name-matching fully retires.

**Auger-Aliassime case specifically:** The hyphenated-name failure now has TWO escape hatches: (1) if his player_key is in our metadata, the cross-feed path uses it post-Step-F; (2) if a specific name variant breaks, add an override line. Combination eliminates the issue functionally even before Step F.

**Until Step F:** The cross-feed warnings persist for known-affected events. Cosmetic, doesn't break operator-visible behavior — shadows render correctly via Step B+E.

### Polymarket count-up indicator — possible improvement

**Status:** Parked 2026-05-02. Operator instinct, no spec.

**Background:** Operator noticed there's a count-up indicator visible on the Polymarket app (or possibly elsewhere) showing some kind of price/order/activity rate. Saw it during initial markets-WS validation while the dashboard was receiving real-time data. Operator's read: "there might be an improvement we can make to make it more useful."

**What's not yet known:**
- Exactly what the indicator is showing (price update frequency? trade volume rate? order book depth changes?)
- Whether it's something on the Polymarket app or elsewhere
- What "more useful" would look like for our dashboard

**When to pick this up:** After markets-WS validation phase produces operator observations during volatile conditions. The validation will surface clearer instincts about what's missing or what would help. Until then, the design questions are too vague to action.

**Connection to other work:** May overlap with the Price Movement Indicator project scope (already drafted as `PM-D2-price-movement-scope-2026-05-01.md`) — if this turns out to be about price-change visibility, that scope already covers some of the territory.

### Direction X analysis tooling

**Status:** Premature today; right time post-activation.
**Activation criteria:** ~50-100 attributed trades after Step 7
activation.

Extend `analysis/compute_baseline.py` (Draft 5 methodology) with
Step-7-aware mode: per-trade attribution table, entry-rule match rate,
momentum-state-at-entry distribution, time-gap distribution,
signed-delta-vs-outcome correlation.

**Why investigation, not "ready to schedule":** Without real
attribution output to test against, the analysis tooling would be
speculative. Right time is *with* the first real attribution data in
hand. Same lesson as Step 7 itself: ground in data, don't speculate.

### Findings.md structure + capture script

**Status:** Identified 2026-04-27 PM.
**Activation criteria:** Operator decides whether structured capture
adds enough value to justify mild friction increase per finding.

Light template (entry timestamp, trade ID if applicable, indicator
state observed, friction noted, classification) plus a tiny CLI tool
that prepends timestamped entries to `findings/` from anywhere.

**Why investigation:** The right structure depends on what we'll
mine for. Build after one Direction X analysis run identifies what
information would have been useful to capture systematically.

### Order ID extraction (per-click aggregation prerequisite)

**Status:** Identified 2026-04-30 PM. Surfaced during receipt-validation
session against today's Sorribes contract.
**Activation criteria:** None firm. Investigate when the dashboard's
fill-level activity count diverges meaningfully from the operator's
iPhone click count and that becomes operational friction.

The dashboard, the CSV, AND the iPhone receipts are all currently
**fill-level** views, not click-level. When Polymarket's order book
splits one operator click across multiple fills (most commonly: a
resting limit order that fills opportunistically over minutes or hours
as the market touches the limit price), each fill produces its own
record on every surface — including separate iPhone "You bought"
receipts. There is no surface in our current stack that shows the
operator-click view.

To aggregate fills back to clicks correctly, the parser would need a
**signal that distinguishes "one order, multiple fills" from "two
separate clicks at coincidentally similar timing."** Time-window
heuristics cannot do this — a resting limit order can produce fills
hours apart, while accidental rapid double-clicks can produce records
seconds apart. Any time window short enough to avoid merging
double-clicks is too short to capture resting-order fills; any window
long enough to capture resting-order fills will silently merge real
double-clicks.

The signal that exists in principle is **`Order ID`**. Every fill from
a single order shares its Order ID; separate orders have separate IDs.
The CSV column already exists (`src/trades_csv.py` line 47, the
`Order ID` field) but is empty on every row in current production data
— meaning either:
1. Polymarket's activities API doesn't expose Order ID for this
   account type (unfixable from our side)
2. Polymarket's API exposes it but the parser isn't extracting it
   (fixable in `src/trades_csv.py`)

**The investigation:** Pull a raw activity record with full JSON
preservation (e.g., one row from `scripts/pull_trade_history.py`'s
trades.json output) and inspect every field. Look for any identifier
that groups fills by parent order — `orderId`, `parent_order_id`,
`clientOrderId`, or similar. If found, wire into the parser's
`_combine_fills` rule: same Order ID → one operator click.

**What this would unlock:** the `/trading` page and `/reports/today.csv`
could ship a click-level "trades" view alongside the existing fill-level
detail. Activity counts on `/trading` would match what the operator
sees in their iPhone History tab when scrolling through their own
clicks. Resting-order patterns become visible as one trade with
multiple partial fills, instead of as N independent rows.

**Why parked rather than now:** No example case in today's data where
the divergence caused friction. The receipts-and-CSV both show 16
fill-level rows for today; both correctly map to 13 operator clicks
across 4 contracts. Operator confirmed the dashboard "as we have it" is
fine for now. The cost of the investigation is unknown until the API
surface is examined; the value is also unknown until divergence becomes
observed friction.

**See also:**
- [`docs/trade-data-semantics.md`](./trade-data-semantics.md) §Polymarket
  terminology — the existing fill-level model documentation
- [`docs/principles.md`](./principles.md) §"When receipts contradict the
  parser, receipts win" — the family of which this question is a member
  (receipts vs CSV agreeing doesn't make either operator-perspective
  truth; both can be fill-level when the operator-perspective view is
  click-level)

### Surface tagging coverage gap

**Status:** Identified 2026-05-01 from `inspect_state_log.py` output.
**Activation criteria:** Investigate when a surface-conditioned
indicator or analysis becomes load-bearing. Currently low priority
because no shipped indicator depends on surface for non-Madrid matches.

API-Tennis returns surface metadata only for Madrid (Masters/1000
tier). Of 474,833 match-observations across 5 days of state log
capture, 19,567 have `surface: Clay` (all Madrid) and the remaining
455,266 (96%) have `surface: None`. The state recorder is correctly
preserving what API-Tennis provides — the gap is upstream.

**The investigation:** check API-Tennis subscription tier and WSS
payload structure. Determine whether: (a) the subscription doesn't
include surface for Challenger/Futures/smaller WTAs, (b) the field
exists but under a different key the parser isn't reading, or (c)
API-Tennis simply doesn't carry it for those tours.

**What this would unlock:** the `tournament_surface` indicator
(currently v1.0.0) becomes meaningfully applicable beyond Madrid
main-draw. Surface-conditioned analysis (e.g., "operator's hit rate
on Clay vs Hard") becomes statistically robust beyond a 4% slice.

**Why parked rather than now:** No current indicator or shipped feature
depends on surface for non-Madrid matches. The Step 5 pre-match edge
badge uses Sackmann Elo which is surface-aware on its side
(separate ATP/WTA Elo files), but doesn't condition on the
state-recorder's surface field. Activation gate for Step 7 passes
without surface coverage being broader. Worth solving when
surface-stratified analysis becomes desired.

### state-recorder.md disk usage estimate correction

**Status:** Identified 2026-05-01 from `inspect_state_log.py` output.
**Activation criteria:** Update the doc when next touched (or as part
of a post-Step-7 housekeeping ship).

`docs/state-recorder.md` currently estimates "~1,500 snapshots/day
during active trading windows" and "~195 days of headroom" on the
974 MB Render Disk. Empirical observation (5 days, ~35,810 snapshots
total) shows the actual rate is closer to ~8,500 snapshots/day in
active windows — roughly 5.7× higher. Recomputed headroom: ~35 days
at current rate, not 195.

**Why parked rather than now:** 35 days is still sufficient runway
for the activation-and-first-Direction-X-analysis horizon. The
estimate doesn't affect any operational decision. Doc-only correction
worth bundling with the next state-recorder.md edit.

**Note:** the per-snapshot size estimate (~3-5 KB) appears roughly
correct — total disk consumption today is ~140-180 MB across 5 days
(35,810 × 4 KB ≈ 143 MB), which matches what `du -sh /var/data/` would
show.

### Cross-feed unmapping — recurring offenders (RESOLVES WITH STEP F)

**Status:** Persistent issue with structural fix queued (Step F of player database build, deferred from 2026-05-03 session). Same Polymarket events fail to map to API-Tennis events across multiple sessions: Andreeva/Kostyuk (id=10490), Onclin/Coulibaly (id=10554), Hurkacz/Burruchaga (id=10556), Visker/Mmoh (id=10571), and others surface intermittently.

**Operational impact today:** Cosmetic. The Polymarket-only shadow path (v0.6.0) renders these events correctly with prices, ranks, edge badges, and (post-v0.6.4) flags. The `cross_feed: unmapped` log lines are noise — operator-visible behavior is unaffected.

**Likely root cause:** name-token overlap fails when player names diverge between feeds (different transliterations, accent handling, hyphenated names, word-order variants like Burruchaga's "Roman Andres Burruchaga" / "Andres Burruchaga Roman").

**Structural fix (Step F):** Cross-feed module migrates from name-token joins to player_key joins. Both feeds resolve to API-Tennis `player_key` via existing infrastructure (Step A populates from API-Tennis payloads, Step B+E bootstraps Polymarket-only names via `player_metadata.lookup_by_name`). Once shipped, the unmap warnings stop because there's no name-matching to fail.

**Bandaid available (not recommended):** `cross_feed_overrides.yaml` could absorb one-off entries. Decided against that earlier in this session — adds technical debt that gets removed when Step F lands.

**Retire when:** Step F shipped and verified across 1-2 sessions, `cross_feed: unmapped` log lines no longer appear for known players.

---

## Retired

### WS instability — auto-restart watchdog + uptime badge — SHIPPED 2026-05-03 v0.6.11

Three-piece watchdog:

1. **`[WS-RECOVERED]` log line.** Emitted whenever the markets WS supervisor loop completes a successful connect cycle following ≥1 failed attempt. Captures `consecutive_failures` count, `outage_ms` duration, and `last_failure_class` (exception type name). Surfaces transient self-healed outages — like the 23:45 incident #2 (~32s, 4 failed attempts) — that would otherwise be operationally invisible.

2. **Auto-restart on N consecutive failures.** New env var `MARKETS_WS_RESTART_AFTER_N_FAILS` (default 5, set 0 to disable). When threshold hit, worker logs `[WS-WATCHDOG]` with outage summary, flushes log handlers, calls `os._exit(1)`. Render's auto-restart picks it up. Automates exactly what manual restart did during incident #1 (17:30 UTC, 30 min, 225 attempts). Threshold chosen so today's incident #2 (4 attempts, self-healed) wouldn't have triggered — preserves recovery for transient cases, restarts only the sticky tail.

3. **Uptime badge in dashboard header.** Subtle "uptime Xm" between the Polymarket health row and the clock. Backend exposes `process_started_ms` via `state.snapshot()`; frontend ticks every 500ms alongside liveness counters. Combined with #2: an unexpected uptime drop (after stepping away) signals "watchdog auto-restarted, investigate." Without it, silent restart leaves no operator-visible trace.

Forensic trail: `[WS-RECOVERED]` for self-heals, `[WS-WATCHDOG]` for forced restarts, uptime drop for either. Not all three fire in every event — depends on duration + threshold. See `log/working_log_entry_2026-05-03-watchdog.md`.

Diagnosis preserved (incident root cause + monkey-patch lever as last-resort): `websockets` library raises `NotImplementedError` when the handshake response has a `Transfer-Encoding` header (RFC 7230 §3.3.3 strictness). A monkey-patch on `websockets.http11.Response.parse` would remove the failure mode entirely — held as an emergency lever if watchdog-based recovery proves insufficient. polymarket-us SDK is at v0.1.2; the websockets version is a transitive dep, not directly upgradable. PM-D.1's DIAG-1/2/4 patch (commit `999c8c9`) remains in production for now; consider removing in a cleanup ship after the watchdog has captured a few real events.

Lesson preserved (PM-D.2 phantom WS investigation, 2026-05-03 evening): when investigating "X is missing from logs," widen the search window to before AND after the alleged failure, search for the affirmative signal not just the failure signature, and verify across multiple processes if recurrence is claimed. Failure to confirm absence before declaring it cost ~90 minutes that night.

### Indicator legend / help surface — SHIPPED 2026-05-03 v0.6.10

Footer-anchored collapsible legend block. Backend-driven from `state.snapshot()`'s new `momentum_indicator` block — single source of truth, no doc-drift risk. Renders the active MI parameter set with parameter names operator can reference when directing tuning ("set noise_floor to 3"). Other indicators (edge badge, rank, flag, position, liveness) get static reference rows. Ships alongside the momentum trend arrow + MI.1 versioning for a coherent first cycle of "see the indicator on the page, expand the legend, name the parameter, direct the tune." See `log/working_log_entry_2026-05-03-momentum-trend-MI.md`.

### Step 4.2 v2 — momentum trend arrow — SHIPPED 2026-05-03 v0.6.10

Trend arrow direction added to the momentum leader pill. Arrow inside the existing pill now reflects whether the leader's lead is extending (↗) or closing (↘) over the most recent 6 points. Holding state renders no arrow (bare `+N` pill) per operator economy — only "active" trends get visual weight. New `momentum.compute_trend()` computes via delta-of-delta with leader-flip handling. ±2 trend threshold matches v2.0.0's differential threshold. State recorder schema adds `momentum_trend` field per match record. Trade attribution `indicators_at_entry` lifts both `momentum_trend` and `momentum_indicator_version` (MI.1) so Direction X analysis can correlate trade outcomes against trend state and tuning regime. Frontend swaps to one of two SVG arrow glyphs (or no glyph) based on trend value. Algorithm and decay weights from v2.0.0 unchanged. Backwards-compatible — old snapshots without `momentum_trend` remain interpretable. See `log/working_log_entry_2026-05-03-momentum-trend-MI.md`.

### Quick fix: Ficovich override warning loop in sackmann logs — SHIPPED 2026-05-03 v0.6.8

The 2-second-cadence `WARNING sackmann: override 'Juan Pablo Ficovich' → 'Pablo Ficovich Juan' not found in ATP data` loop is silenced via once-per-(name, tour) dedup in `_resolve_player`. New module-level set `_override_miss_logged: set[tuple[str, str]]` gates the warning; first miss logs once, subsequent calls are silent. Smaller fix than the parked options 1-3 (no new file, no shared-overrides reversal, no per-tour existence check at load time). v0.6.5's "shared overrides file" decision is preserved. The override itself continues to work for `player_metadata.lookup_by_name` (Argentine flag still renders for Ficovich); the warning that was a 30-line/min log noise is now ~1 line per process restart. Bundled with the Step F shadow ship since both edited the player-resolution layer. See `log/working_log_entry_2026-05-03-stepF-shadow.md`.

### Polymarket markets WS — proper price-merge fix — SHIPPED 2026-05-03 v0.6.7

Diagnostic v0.6.6 captured 50 paired observations during live ATP Challenger play 17:14-17:17. Quantitative analysis showed WS `best_ask` matched REST `side_a_cents` near-perfectly (median 0¢ delta, mean 0.02¢) while alternatives showed 1-9¢ deltas. Side overround analysis identified stale-market REST corruption (rows summing to 137-140¢ instead of normal ~101¢) correlating 100% with wide spread (>5¢) — gives a reliable skip signal. Fix shipped in `_extract_prices_from_market_data` Path B: writes `side_a_cents` from WS best_ask when Path A didn't set it AND spread (ask-bid) ≤ 5¢. Doesn't touch side_b (REST owns). [WS-DIAG] diagnostic block removed. Replaces the HIGH PRIORITY parked entry that called for diagnostic-then-fix; both phases shipped in the same session. See `log/working_log_entry_2026-05-03-ws-fix.md`.

### Step 7 activation — ACTIVATED 2026-05-02

Trade attribution worker activated via `TRADE_ATTRIBUTION_ENABLED=1` env var on 2026-05-02. State log gate validated comfortably (44,169 snapshots, 713 distinct matches, 6 days). 1,559 historical trades backfilled successfully. First-day attribution: 18 of today's trades attributed with 17 (94%) populating `indicators_at_entry`. The single miss was a known cross_feed unmapping (Mmoh). Worker stable, polling at 60s cadence, writing to `/var/data/trade_log/`. Closing this entry — Step 7 is now operational, not parked.

---

## Audit conventions

When walking this doc:

**Promotion to "ready to schedule":** When activation criteria fire,
the item moves up. The working log entry that triggered the promotion
references this move.

**Demotion to "retired":** When an item is no longer worth doing
(superseded by other work, criteria proven wrong, etc.), it moves
to "Retired" with the reason. Don't delete — kept as guardrail.

**New items:** Start in the section that fits their state. Don't put
new investigation work in "ready to schedule" until investigation
shows it's actually ready.

**Audit cadence:** Walk this doc whenever a build session starts. The
"last full audit" header date should update at least monthly even if
no items move — confirms the doc is being maintained.

---

## See also

- [`README.md`](./README.md) — documentation contract and concept-doc index
- `log/working_log.md` — full chronological history of every item
- [`indicators.md`](./indicators.md) — current state of every shipped indicator
