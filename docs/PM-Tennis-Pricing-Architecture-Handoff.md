# PM-Tennis Pricing Architecture: Technical Handoff

**Date:** 2026-05-05
**Status:** Validated empirically against Polymarket iPhone app
**Audience:** Operator (you), and any future developer who will implement the production rollout

---

## How to read this document

Each major section has two parts:

- **For the user (operator):** what this means in plain language, why it matters, what you can verify yourself.
- **For the developer:** specific technical detail, code, endpoints, file references — enough to implement without prior context from our conversation.

---

# Part 1 — Where we are: the current dashboard

## 1.1 What the dashboard does (user view)

The PM-Dashboard (deployed at https://pm-dashboard-o71w.onrender.com) tracks live tennis matches on Polymarket. For each live match it displays:

- Both players' names and rankings
- Each player's current Polymarket price (in cents, e.g. "47¢" / "53¢")
- A live score from a separate sports data provider
- Position state (whether you currently hold long or short shares in either side)
- Recent trades you've placed, attributed to specific market events

The operator places trades manually on the Polymarket iPhone app while watching the dashboard. The dashboard is a decision-support tool — it is not a trading bot, and it does not place orders.

The single most important number in each match row is the displayed price for each player. **The acceptance criterion for the entire pricing system is: each player's displayed price on the dashboard must match what the iPhone app shows for that player, within roughly 1 percentage point, and changes on the iPhone must propagate to the dashboard within roughly 1 second.**

## 1.2 Current technical implementation (developer view)

### 1.2.1 Codebase layout

The repository is at https://github.com/peterlitton/PM-Dashboard, deployed on Render via `render.yaml`. The relevant Python source files are under `src/`:

```
src/
  main.py                  Flask app, HTTP routes, dashboard HTML rendering
  polymarket_worker.py     Polymarket data ingestion (REST polling + WS subscription)
  api_tennis_worker.py     Sports score data from API-Tennis
  cross_feed.py            Joins Polymarket matches with API-Tennis matches
  state.py                 Shared in-memory state model
  state_recorder.py        Periodic snapshot logging
  trade_attribution.py     Maps user trades to market events
  ...
```

The Polymarket integration is entirely in `polymarket_worker.py`. The frontend (`dashboard.html`, `dashboard.js`) reads JSON state from `main.py` HTTP endpoints and renders the table.

### 1.2.2 Polymarket data sources currently used

The dashboard talks to **Polymarket US**, the CFTC-regulated US-domestic platform launched in 2026. It uses two surfaces:

**REST polling (every 15 seconds):**
```
GET https://gateway.polymarket.us/v2/sports/tennis/events
```
This is the public consumer API. Returns a list of tennis events. For each event:
- Event metadata (slug, title, startDate, live status, score)
- One `markets[]` entry containing the moneyline market
- Inside that, `marketSides[]` with two entries — one per player outcome

The structure of `marketSides` per side is:
```json
{
  "id": 40437,
  "marketSideType": "MARKET_SIDE_TYPE_ERC1155",
  "identifier": "aec-atp-juseng-nikizq-2026-05-04",
  "description": "Justin Engel",
  "long": true,
  "teamId": 3252,
  "team": { ... },
  "participantId": "event_10678_team_3252",
  "quote": { "value": "0.350", "currency": "USD" }
}
```

**WebSocket subscription:**
```
wss://api.polymarket.us/v1/ws/markets
```
Authenticated via Ed25519 signed headers (key generated at polymarket.us/developer after KYC). The dashboard subscribes by **slug** (e.g., `aec-atp-juseng-nikizq-2026-05-04`) using the SDK's MARKET_DATA subscription type. Payloads carry a single set of `bids[]` and `offers[]` for that slug, plus `stats` (lastTradePx, openPx, etc.).

### 1.2.3 How the dashboard currently extracts prices per player

In `polymarket_worker.py`, the `extract_prices()` function tries multiple paths in order:

**Path A — `marketSides[].quote.value` (REST schema, REST-rate updates):**
```python
sides = market_data.get("marketSides")
if isinstance(sides, list) and len(sides) >= 2:
    for side in sides[:2]:
        q = side.get("quote")
        # ... extract q["value"] for each side
```
This gets us a per-side displayed price for both players. But because the WebSocket payloads do not carry a `marketSides` block (see comment at line 250: "no `marketSides` block in any of the 60+ payloads"), this only updates at the REST polling cadence — every 15 seconds. Side B's price reflects activity from up to 15 seconds ago.

**Path B — `bids[0].px` and `offers[0].px` (WS book):**
```python
best_bid = _extract_px(bids[0].get("px"))
best_ask = _extract_px(offers[0].get("px"))
```
These come from the WS book updates and are real-time. But they are a single set of bids and offers — there is no per-player breakdown in the WS payload.

**Path C — `stats.lastPriceSample.longPx` and `stats.lastPriceSample.shortPx`:**
```python
last_sample = stats.get("lastPriceSample") or {}
long_px = _extract_px(last_sample.get("longPx"))
short_px = _extract_px(last_sample.get("shortPx"))
```
A paired sample of long-side and short-side prices at the same point in time. These are sourced from the matching engine's last trade. They update less frequently than the book itself.

### 1.2.4 The fundamental problem

The Polymarket US public WebSocket endpoint exposes **one order book per slug**. A tennis moneyline market has one slug — but two outcomes (one per player). The single book on that slug does not contain enough information to derive both players' real-time prices independently.

What the dashboard ends up doing:

- **Player A (the "long" side, Polymarket's `long=True`):** gets a real-time price from the WS bids/offers, computed as best_ask. Updates within ~1 second of book changes.
- **Player B (the "short" side, `long=False`):** has no real-time WS source. Falls back to `marketSides[1].quote.value` (REST, 15s cadence) or `lastPriceSample.shortPx` (slower still). Lags 20–60 seconds behind reality.

The operator validated this lag empirically by comparing the dashboard side-by-side with the Polymarket iPhone app over a 2-minute window. Player A's price matched within ~1 second; Player B's was anywhere from 20 to 60 seconds stale.

### 1.2.5 Past failed fix attempts

Multiple fixes were shipped against this bug across versions v0.7.0 through v0.7.9:

- **v0.7.0–v0.7.7:** various attempts to read different fields, smooth time series, add diagnostic logging. None addressed the root cause (no per-side WS feed for side B).
- **v0.7.8 (rejected):** introduced a derivation `side_b_price = 1 - side_a_best_ask`, presented as a "fabricated `1-best_ask` fix." Operator rejected this with: *"You've created a pricing model that doesn't match reality. X-100=y. NO."* The fix produced numbers that summed to exactly 1.00, which is mechanically wrong (real markets have a non-zero spread between the two sides — the sums should be greater than 1.00 by some small margin, the platform's overround).
- **v0.7.9 (current production):** revert to v0.7.7 with extraction diagnostic logging in place. Side B still lags.

### 1.2.6 Constraints carried into the new architecture

The operator-locked principles from prior shipments:

- **Receipts win.** Empirical iPhone comparison is the only acceptable validation. No sums-to-100 self-check, no "looks plausible" — match the iPhone or it's wrong.
- **Diagnostic-first.** Any fix must include logging that lets us audit what the system did vs. what reality showed.
- **Slow down when asked.** No charging ahead with unverified assumptions. When the operator says "go read the docs," that means: read the docs, don't infer.
- **Tarballs flat-layout WITH directory structure.** Deployment artifacts should preserve `src/`, `templates/`, `log/`, `methods/`.

---

# Part 2 — What we learned

## 2.1 The shape of the problem (user view)

When the operator looks at a tennis match on the iPhone, both players' prices update independently in real time. Player A might tick from 47¢ to 48¢ while Player B sits at 53¢, and a moment later Player B might tick to 52¢ while A sits still. The two prices move on their own clocks.

This means somewhere in Polymarket's infrastructure, there are two independent order books — one per player — both streaming live to the iPhone. The question is: how does the iPhone get them, and how can the dashboard get the same thing?

Three possibilities had to be examined:

1. The Polymarket US consumer API exposes them somewhere, but we hadn't found the right endpoint.
2. There's a separate Polymarket US institutional/exchange API that exposes them.
3. The iPhone app isn't using Polymarket US at all — it's using a different platform (Polymarket Global, the international crypto-based exchange).

After investigation, the answer is **#3**. The iPhone app uses Polymarket Global. The Polymarket US consumer API does not have the data we need.

## 2.2 Polymarket has three APIs (developer view)

This was the central confusion that took many iterations to resolve. There are three distinct Polymarket trading platforms with three distinct APIs.

### 2.2.1 Polymarket US Consumer API (currently used by the dashboard)

- **Base URL:** `https://gateway.polymarket.us` (public REST), `https://api.polymarket.us` (authenticated REST + WS)
- **Authentication:** Ed25519 keys generated at `polymarket.us/developer` after KYC. iOS-only KYC flow.
- **Identifiers:** Uses **slugs** for markets (e.g., `aec-atp-juseng-nikizq-2026-05-04`).
- **Subscription model:** WS subscribes by `marketSlugs: [...]`. Returns one book per slug.
- **Limitation:** A binary moneyline market has one slug → one book. Per-side prices are derived/REST-only, not real-time WS.
- **SDK:** The `polymarket_us` Python package wraps this. Source confirms slug-only subscription via `_MarketSubscriptionPayload.marketSlugs`.

### 2.2.2 Polymarket US Institutional / Exchange Gateway

- **Base URLs:** `https://api.prod.polymarketexchange.com` (REST), `grpc-api.prod.polymarketexchange.com` (gRPC streaming).
- **Authentication:** Auth0 JWT via Private Key JWT (RS256-signed assertions). Tokens expire every 3 minutes. Application-gated access — contact `onboarding@qcex.com` to apply, not self-serve.
- **Identifiers:** Uses **per-instrument symbols** (e.g., `tec-nfl-sbw-2026-02-08-kc` and `tec-nfl-sbw-2026-02-08-phi` — two symbols per moneyline match, one per outcome).
- **Subscription model:** gRPC `MarketDataSubscriptionAPI.CreateMarketDataSubscription` with `symbols: [...]`. Returns independent per-symbol order books in real time.
- **What we'd get:** Truly per-outcome WS streams. Solves the problem in principle.
- **Why we're NOT using it:** Application-gated; you would need institutional onboarding through QC Exchange. And separately, this exchange's liquidity is the same pool as the Polymarket US consumer side, which is NOT what the iPhone shows.

### 2.2.3 Polymarket Global CLOB (what the iPhone uses, what we will use)

- **Base URLs:**
  - Market metadata (REST, public, no auth): `https://gamma-api.polymarket.com`
  - Order book streaming (WebSocket, public, no auth): `wss://ws-subscriptions-clob.polymarket.com/ws/market`
  - REST CLOB (public + authenticated): `https://clob.polymarket.com`
- **Authentication:** None for read-only market data. (Trading would need EIP-712 wallet signatures, but we are not implementing trading.)
- **Identifiers:** Uses **ERC1155 token IDs** (long numeric strings, e.g., `105060544933...`). Each outcome has its own token. A binary moneyline has two tokens.
- **Subscription model:** Open a WebSocket, send `{"assets_ids": [token1, token2, ...], "type": "market", "custom_feature_enabled": true}`. Returns independent per-token order book updates in real time, routed by `asset_id`.
- **What we get:** True per-outcome streams. Both players' books update independently. This matches what the iPhone shows.

## 2.3 How we proved the iPhone uses Global, not US

Two pieces of evidence:

1. **Operator confirmation:** The operator has a Polymarket.com (Global) account. The operator's iPhone trades **do not show up** in that Polymarket Global account view. The operator confirmed with Polymarket directly that this is expected. This rules out "iPhone trades on Global account-view," but does not by itself prove "iPhone reads prices from Global." However, combined with #2, it strongly suggests the iPhone display reads from Global (since Global is the only platform with a public real-time per-outcome WS feed, and the iPhone clearly shows independent per-outcome real-time prices).

2. **The architectural constraint:** The Polymarket US consumer WS only exposes one book per slug. The iPhone shows two independent prices per match. Therefore the iPhone is not using the Polymarket US consumer WS for its display. It is using either (a) Polymarket US institutional gRPC, which is application-gated and unlikely for a consumer iPhone app, or (b) Polymarket Global. By elimination, (b).

A consultant analysis explicitly concluded: *"iPhone app = Global trading venue. US API = separate system."*

## 2.4 Trading-layer separation (what's still uncertain)

The dashboard's existing trading-layer integration (positions, orders, account balances) reads from Polymarket US authenticated APIs using Ed25519 keys. The operator places orders manually on the iPhone.

If iPhone trades execute on Polymarket Global, then the dashboard's US-side position/order integration is reading from a venue the operator does not actually trade on — and would show empty positions while the operator clearly has them. This has not been observed to be the case, suggesting the iPhone may execute on US even while displaying Global prices. But this is unconfirmed.

For the immediate price-feed shipment, this is not a blocker. The price fix proceeds independently. The trading-layer alignment is flagged as a follow-on item for the operator to verify after the price fix is in production.

## 2.5 The display-rule discovery (revised, final)

The consultant WS-only handoff doc specified:

```
display = (best_bid + best_ask) / 2     if spread <= 0.10
display = last_trade_price              otherwise
```

This is the "midpoint or last trade" rule from Polymarket's own documentation. It is the correct rule for a per-token CLOB.

### 2.5.1 The 2026-05-05 false start

An initial empirical iPhone comparison on 2026-05-05 concluded `display = best_bid`. That conclusion was wrong but understandable in context:

- The validation was done against ONE low-liquidity match with a thin spread.
- On that match, best_bid happened to be within 1¢ of the midpoint and the iPhone's displayed value, so they were visually indistinguishable.
- The conclusion `display = best_bid` was logged as the validated rule and `_TokenBook.display_price()` was set accordingly.
- A side artifact appeared: across all matches, sum of A's best_bid and B's best_bid landed at 97-99¢. This was rationalized at the time as "the spread is the platform's overround." That was the wrong interpretation — see 2.5.2.

### 2.5.2 The 2026-05-06 correction

A second pass of validation on 2026-05-06 surfaced the contradiction. The operator observed that:

- On Polymarket the iPhone displayed prices nearly always sum to 100-101¢ across both players.
- The dashboard (using best_bid) was consistently summing to 97-99¢.
- Market makers are incentivized to maintain ~1¢ spreads on each side; the displayed-price sum reflects bid-side OR ask-side, and only the midpoint sums correctly when both spreads are accounted for symmetrically.

A new diagnostic page (`/dashboard-replica`) was deployed exposing per-token bid AND ask AND midpoint side-by-side. Direct comparison against the iPhone confirmed:

```
display = (best_bid + best_ask) / 2
```

When both books are populated, midpoint sums across players consistently land in 99-101¢, matching the iPhone within 1-2¢. The earlier best_bid sums of 97-99¢ were the underwriter's edge accruing to whichever side of the book a single bid value is taken from — not what the iPhone or market displays.

### 2.5.3 Spec confirmation

The WS-only handoff doc (section 17, "Derived Metrics") had specified midpoint all along:

```
midpoint = (best_bid + best_ask) / 2
sum_midpoint = player_a_midpoint + player_b_midpoint
cross_outcome_gap = abs(1 - sum_midpoint)
```

The doc's CROSS_OUTCOME_GAP warning (section 18) only fires when `abs(1 - sum_midpoint) > 0.03`, indicating the spec authors expected sum_midpoint ≈ 1.0 with tolerance for ±3¢ deviations during fast moves or thin liquidity.

### 2.5.4 Edge cases (one-sided book)

When only one side has quotes (best_bid exists but best_ask doesn't, or vice versa — rare and transient on liquid books, common on illiquid ones):

```
if both sides:    display = (bid + ask) / 2
elif bid only:    display = bid
elif ask only:    display = ask
else:             display = None
```

This fallback was added because an empty ask side appears at the start of subscription before the first ask snapshot arrives, and we don't want the page to flap to None for a few hundred ms each time. To revisit: confirm that the iPhone's behavior in genuinely empty-ask-side states is indeed best_bid (rather than last_trade_price or "—") — currently unverified.

### 2.5.5 Why earlier consultant arguments for "mirrored CLOB" were wrong

Earlier in the investigation, the arxiv paper "Arbitrage Analysis in Polymarket NBA Markets" was cited to argue that per-token CLOB books are "mirrored": a bid of $0.40 on outcome A appears as a synthetic ask of $0.60 on outcome B. This led to expectations that querying one token's book yields a pathologically wide spread (e.g., bid=98¢, ask=1¢) and that midpoints would always converge to 50¢.

This was investigated empirically and proved incorrect for our use case:

- The Polymarket Global public WS endpoint (`wss://ws-subscriptions-clob.polymarket.com/ws/market`) returns clean per-token books with realistic spreads (typically 1-3¢).
- Bid and ask values are not mirrors of the other outcome — they are direct bids and asks on this outcome's token.
- Midpoints are realistic and match the iPhone, not stuck at 50¢.

Whether the underlying matching engine performs synthetic mirror-order generation is a deeper microstructure question; what matters is that the public WS feed presents per-token books that midpoint correctly. The arxiv paper either described a different surface or my reading of it conflated outcome books with combined views.

## 2.6 Two display surfaces, two rules — match-row vs OPEN-row

The midpoint rule documented in section 2.5 applies to **match-row prices only** — the per-side prices shown next to each player on the live match line. There is a SECOND price-display surface on the dashboard, the OPEN sub-row's "now" field, which uses a different rule.

| Surface | Rule | Source |
|---|---|---|
| Match-row per-side prices | `midpoint = (best_bid + best_ask) / 2` of that player's own token | Polymarket Global per-token book (this player) |
| OPEN-row "now" price | `100 − opposing_player's_match_row_price` | Derived from the OTHER player's displayed match-row price |

### Why two rules

The match-row price answers "what is the market saying about this player's win probability" — midpoint of their own token's book is the natural answer.

The OPEN-row "now" price answers a different question: "what would I realize if I exited this position right now?" When the operator holds a long position on Player A and wants to exit, they sell Player A shares — and the price they get is bound by what the market is paying on Player B's token. Sourcing OPEN's "now" from the opposing side's displayed price (subtracted from 100) gives the operator a number that correctly models exit value.

This is the operator-locked rule. Empirically validated against the iPhone Polymarket app on 2026-05-06. See `docs/PM-D5-Now-Price-From-Opposing-Side.md` for the specification, implementation steps, acceptance criteria, and rollback procedure. **Do not unify the two rules** without operator authorization — they serve different purposes and the operator validates each surface against a different reference number on the iPhone.

### Implementation note

The OPEN-row rule is implemented in the **frontend only** (`static/dashboard.js`). The price values stored in `state.matches[*].p{1,2}_price_cents` and served by the backend are the match-row midpoints; the OPEN-row derivation happens at render time in `renderRow` via the `deriveNowCents` helper. The `positionSubRow` function itself is generic — it renders whatever `currentPriceCents` argument it receives and does not encode the rule.

### P&L computation is independent

The dollar and percent P&L on the OPEN row come from server-computed `position.cost_cents` and `position.cash_value_cents` fields, NOT from the displayed "now" price. Changing the displayed "now" price does NOT change the displayed P&L. If a future change is needed to align P&L with the opposing-side rule, it is a separate change at the resolver level and must be specified separately.

## 2.7 Match ordering — stable cross-status sort by scheduled start time (v0.8.3)

Prior to v0.8.3 the dashboard rendered live matches first (in dict-insertion order), then upcoming matches sorted by start time. This caused live rows to reshuffle whenever a new match transitioned from upcoming to live: the new live match would jump to the top, displacing every other live match's vertical position. The operator could not keep visual track of any given match across status transitions.

### The fix

A single chronological sort by `start_time` ascending across all matches, regardless of status:

```python
# state.snapshot() — v0.8.3
all_matches = sorted(
    matches.values(),
    key=lambda m: m.start_time or "",
)
```

To support this, `start_time` is now populated for every match (live, upcoming, finished), not only for upcoming. The change is in `api_tennis_worker._upsert_match`: the previous condition `_start_time(item) if status == "upcoming" else None` is replaced with the unconditional `_start_time(item)`. Underlying API-Tennis fields `event_date` and `event_time` are emitted on every frame regardless of match status, so no data is lost.

### Why ordering by start time, not by something else

The operator considered alphabetical, by-tournament, and by-priority orderings. Scheduled start time wins because:

1. It is monotonic — a match's start time is fixed at scheduling and never changes (or, if rescheduled, changes once and stays put).
2. It groups same-tournament matches together naturally (tournaments tend to publish slot-based schedules).
3. It lets the operator memorize a row's position over the course of a viewing session, which is the actual goal: "the Boulter match is about a third of the way down the page" should be true at minute 5 and minute 50.

### Edge cases

- A match with no `start_time` (data quality issue, or a match that escaped scheduling) sorts to the very top via the empty-string fallback. Visible-but-undated rows are easier to debug than silently-hidden ones.
- Two matches with identical `start_time` (e.g. two simultaneous opens at the same tournament) sort by Python's stable-sort tiebreaker, which is dict insertion order. This is fine: the order is still stable across snapshots.
- Finished matches: not currently rendered (the frontend filters by `tradeable` = has at least one price), but if they ever are, they'll slot in chronologically alongside everything else.

---

# Part 3 — The solution

## 3.1 What changes (user view)

The dashboard's price feed will be replaced. Instead of polling Polymarket US REST and subscribing to one slug per match on the Polymarket US WebSocket, it will:

1. Continue using Polymarket US REST briefly, but only to discover **which** matches are currently live (the existing match-discovery mechanism does not break). This is then used to look up the corresponding Polymarket Global market.
2. Look up each match's two outcome token IDs from the Polymarket Global metadata API (Gamma).
3. Open a WebSocket connection to Polymarket Global's public CLOB stream and subscribe to all the token IDs for all currently tracked matches.
4. Maintain a per-token order book in memory.
5. Display each player's price as the **midpoint** of bid and ask on that player's token on the match row — the validated rule (see section 2.5).
6. Display each player's "now" price on the OPEN sub-row as `100 − opposing_player's_match_row_price` — the operator-locked exit-value rule (see section 2.6).

What you will see:

- Both players' prices update independently in real time, with no 20–60s lag on either side.
- Prices match the iPhone within ~1 percentage point.
- Sums of the two players' displayed prices land near 100¢ (typically 99-101¢). The expected gap is small (<3¢ per the spec); larger gaps indicate cross-outcome divergence and trigger the CROSS_OUTCOME_GAP warning.

## 3.2 Architecture (developer view)

### 3.2.1 Three-layer structure

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 1: Discovery                                         │
│  - Poll Polymarket US gateway REST every 60s                │
│  - Extract list of live tennis matches (US slug + names)    │
│  - For each new match: query Polymarket Global Gamma,       │
│    fuzzy-match player names against Gamma `question` field, │
│    extract `clobTokenIds[]`, assign tokens to A/B sides     │
│  - Cache (US slug) → (player names, token A, token B)       │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 2: WebSocket book maintenance                        │
│  - One persistent connection to                             │
│    wss://ws-subscriptions-clob.polymarket.com/ws/market     │
│  - Subscribe with all active token IDs                      │
│  - Per-token in-memory order book: bids:Map, asks:Map       │
│  - Apply `book` events (full snapshot replace)              │
│  - Apply `price_change` events (deltas: BUY→bids,           │
│    SELL→asks, size 0 = remove level)                        │
│  - Track last_trade_px from `last_trade_price` events       │
│  - PING/PONG keepalive every 10s                            │
│  - Reconnect+resubscribe on token-set changes or disconnect │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: Display                                           │
│  - For each match, for each player:                         │
│    display_price = midpoint(token) = (best_bid + best_ask) / 2  │
│  - Render on dashboard                                      │
└─────────────────────────────────────────────────────────────┘
```

### 3.2.2 Why three layers, not two

Discovery has a 60-second cadence; WS has continuous-update cadence. They are decoupled so that WS book maintenance is never blocked by Gamma pagination latency, and so that the WS connection can persist across discovery refreshes (only resubscribing when the active token set actually changes).

### 3.2.3 Discovery in detail

Polymarket US gateway gives us tennis events with a flag for live status, plus player names in `marketSides[].description`. This continues to work. No change.

Polymarket Global Gamma is a separate metadata API. We use:

```
GET https://gamma-api.polymarket.com/events?active=true&closed=false&limit=100&offset=0&tag_slug=tennis
```

Critical: The `/markets` endpoint **does not** honor `tag_slug=tennis`. It returns all markets (~25,000). The `/events` endpoint **does** filter server-side to tennis (~1,700 markets across ~60 events). Use `/events`.

Each event in the response has a `markets[]` array. Each market object has:
- `question` — human-readable, e.g., `"Brazzaville: Florent Bax vs Adrian Arcon"`
- `outcomes` — JSON-string-encoded array, e.g., `'["Florent Bax", "Adrian Arcon"]'`
- `clobTokenIds` — JSON-string-encoded array of two token IDs

Both `outcomes` and `clobTokenIds` are JSON-encoded **strings**, not arrays. They must be `json.loads()`ed before use.

### 3.2.4 Mapping US slugs to Global markets

US slugs like `aec-atp-juseng-nikizq-2026-05-04` and Global slugs like `florent-bax-vs-adrian-arcon-2026-05-05` are not programmatically equivalent. Player abbreviations differ; word ordering differs; tournament prefixes differ.

The reliable mapping path:

1. Get player full names from US gateway response: `marketSides[0].description = "Florent Bax"`, `marketSides[1].description = "Adrian Arcon"`.
2. Iterate Gamma tennis markets. For each, look at `question`.
3. Normalize names (lowercase, strip non-alpha) to enable substring matching.
4. Filter out non-moneyline derivative markets (totals, spreads, set winners, props) by excluding questions containing tokens like `"total sets"`, `"o/u"`, `"set 1"`, `"set winner"`, `"tiebreak"`, `"+"`, `"1.5"`, `"2.5"`, `"3.5"`.
5. Of remaining candidates, find ones whose normalized question contains both player names (full or last-name fallback for short last names).
6. Prefer the candidate with the shortest question (most likely to be the plain moneyline rather than a derivative we missed).

Once matched, parse the `clobTokenIds` JSON string and call the assignment function to figure out which of the two token IDs corresponds to player A vs B (by checking which outcome name in `outcomes[]` matches player A's name).

### 3.2.5 WebSocket protocol

The Polymarket Global CLOB WebSocket protocol is JSON-over-text. After connecting to `wss://ws-subscriptions-clob.polymarket.com/ws/market`, send a single subscription message:

```json
{
  "assets_ids": ["token_id_1", "token_id_2", "..."],
  "type": "market",
  "custom_feature_enabled": true
}
```

`custom_feature_enabled: true` enables additional events: `best_bid_ask`, `new_market`, `market_resolved`. We use these for corroboration and lifecycle but the core state comes from `book` and `price_change`.

After subscription the server sends events as JSON objects (sometimes individually, sometimes batched in arrays — handle both). Every event has `event_type` and `asset_id`. Route by `asset_id` to the right token book.

**Event types we care about:**

- `book`: full snapshot. Clear local bids/asks for that token, then load all `bids[].price/.size` and `asks[].price/.size`. This is the source of truth on (re)subscribe.
- `price_change`: incremental update. Has `price_changes[]` (or sometimes `changes[]`) with `{price, size, side}`. `side="BUY"` updates bids, `side="SELL"` updates asks. `size=0` removes the level; `size>0` sets it.
- `last_trade_price`: a recent trade. Stores `price` for diagnostic display only (not used for the chosen display rule, but useful for audit).
- `best_bid_ask`: optional top-of-book. Can be used to corroborate the local book. Not relied upon as primary state.
- `tick_size_change`: rare; tick precision changed. Store new value for future order placement (we don't trade, so just log).
- `market_resolved`: outcome decided. Mark match as resolved; stop treating updates as live.

**Heartbeats:** Send `PING` text frames every ~10 seconds. Server may reply with `PONG`; ignore those when processing messages.

**Reconnect:** On disconnect: mark all subscribed token books stale, exponential backoff (1s → 2s → 5s → 10s → 30s max), reconnect, resubscribe to the same token list. Wait for fresh `book` snapshots before treating data as live.

### 3.2.6 Token-set change handling

When discovery finds a new live match (or a previously-tracked match drops off), the active token set changes. The simplest implementation: track a version counter; when discovery updates the set, bump the version; the WS loop notices the bump, closes its connection, and reconnects with the new full token list. This re-uses the reconnect path and ensures the server sees a consistent subscription.

This means there is a brief gap (a few seconds) when matches start or end, during which prices may be stale. Acceptable for an MVP and for production unless validation reveals it as a problem.

### 3.2.7 Display rule

```python
def display_price(book) -> Optional[float]:
    if not book.bids:
        return None
    return max(book.bids.keys())
```

That's all. Best bid. No spread check. No last-trade fallback (unless we explicitly later determine the iPhone falls back to last trade when there are no bids — to be confirmed during production rollout).

## 3.3 What's been validated (via the MVP)

A standalone terminal-only Python MVP (file `pm-mvp/app.py`) was built to validate this architecture without touching the production dashboard. The MVP:

- Discovers live tennis matches from Polymarket US gateway
- Resolves each to its Polymarket Global token IDs via Gamma
- Lets the operator pick one match and one player at a time
- Subscribes to that one player's token over the Polymarket Global WS
- Streams prices to the terminal in real time, showing all candidate display values (bid, ask, midpoint, last trade) in separate columns

Operator validation 2026-05-05 (initial): ran the MVP, picked a live match, picked a player, confirmed against iPhone. The bid column appeared to match the iPhone, leading to a tentative `display = best_bid` rule.

Operator re-validation 2026-05-06 (final): exposed bid, ask, and midpoint side-by-side on `/dashboard-replica` for all live matches at once. Compared against iPhone. The midpoint column consistently matched within 1-2¢, across both players in each match, and across active and quiet matches. The earlier best_bid result reflected coincidental alignment on a low-liquidity match where best_bid and midpoint differed by less than 1¢. The corrected rule: `display = (best_bid + best_ask) / 2`. See section 2.5 for the full revision history.

The MVP does **not** scale to all matches simultaneously in its current form — it's deliberately one-player-at-a-time for simple validation. Production needs the full multi-match architecture described in section 3.2.

## 3.4 Code samples (developer view)

The MVP code is the reference implementation. Key functions, copied verbatim from `pm-mvp/app.py`:

### 3.4.1 Discovery: fetch live matches from US gateway

```python
async def fetch_us_live_matches() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=20.0,
        headers={"User-Agent": "pm-mvp/0.2", "Accept": "application/json"},
    ) as client:
        all_events = []
        offset = 0
        while True:
            resp = await client.get(
                f"{US_GATEWAY}/v2/sports/tennis/events",
                params={"limit": 100, "offset": offset},
            )
            resp.raise_for_status()
            data = resp.json()
            page = data.get("events") or []
            all_events.extend(page)
            if len(page) < 100:
                break
            offset += 100

    live = []
    for ev in all_events:
        if not ev.get("live"):
            continue
        markets = ev.get("markets") or []
        if not markets:
            continue
        m = markets[0]
        sides = m.get("marketSides") or []
        if len(sides) != 2:
            continue
        names = [s.get("description") or "" for s in sides]
        if not all(names):
            continue
        live.append({
            "us_slug": m.get("slug"),
            "player_a_name": names[0],
            "player_b_name": names[1],
        })
    return live
```

### 3.4.2 Discovery: fetch tennis markets from Gamma

```python
async def fetch_gamma_tennis_markets() -> list[dict[str, Any]]:
    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "pm-mvp/0.2", "Accept": "application/json"},
    ) as client:
        all_markets: list[dict[str, Any]] = []
        offset = 0
        page_limit = 100
        while True:
            resp = await client.get(
                f"{GAMMA_BASE}/events",
                params={
                    "active": "true",
                    "closed": "false",
                    "limit": page_limit,
                    "offset": offset,
                    "tag_slug": "tennis",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "data" in data:
                data = data["data"]
            if not isinstance(data, list) or not data:
                break
            for ev in data:
                for m in ev.get("markets") or []:
                    all_markets.append(m)
            if len(data) < page_limit:
                break
            offset += page_limit
            if offset > 5000:
                break
        return all_markets
```

### 3.4.3 Mapping: US match to Gamma market

```python
def normalize_name(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())

def match_us_to_gamma(us_match, gamma_markets):
    a_norm = normalize_name(us_match["player_a_name"])
    b_norm = normalize_name(us_match["player_b_name"])
    a_last = normalize_name(us_match["player_a_name"].split()[-1])
    b_last = normalize_name(us_match["player_b_name"].split()[-1])
    candidates = []
    for gm in gamma_markets:
        question = gm.get("question") or ""
        q_lower = question.lower()
        # Exclude derivative markets (totals, sets, props, spreads)
        if any(tok in q_lower for tok in (
            "total sets", "o/u", "over/under", "total games",
            "spread", "handicap", "first set",
            "set 1", "set 2", "set 3", "set 4", "set 5", "set winner",
            "tiebreak", "tiebreaker", "props", "+",
            "1.5", "2.5", "3.5",
        )):
            continue
        q_norm = normalize_name(question)
        a_hit = a_norm in q_norm or (len(a_last) >= 4 and a_last in q_norm)
        b_hit = b_norm in q_norm or (len(b_last) >= 4 and b_last in q_norm)
        if a_hit and b_hit:
            candidates.append(gm)
    if not candidates:
        return None
    candidates.sort(key=lambda m: len(m.get("question") or ""))
    return candidates[0]
```

### 3.4.4 Token extraction and side assignment

```python
def parse_clob_token_ids(gm):
    raw = gm.get("clobTokenIds")
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return None
    if isinstance(raw, list) and len(raw) == 2 and all(isinstance(x, str) for x in raw):
        return raw
    return None

def assign_tokens_to_sides(us_match, gm, token_ids):
    """Return (token_a, token_b) where token_a corresponds to player A."""
    outcomes_raw = gm.get("outcomes")
    outcomes = []
    if isinstance(outcomes_raw, str):
        try:
            outcomes = json.loads(outcomes_raw)
        except Exception:
            outcomes = []
    elif isinstance(outcomes_raw, list):
        outcomes = outcomes_raw

    a_norm = normalize_name(us_match["player_a_name"])
    a_last = normalize_name(us_match["player_a_name"].split()[-1])

    if len(outcomes) == 2 and len(token_ids) == 2:
        for i, oc in enumerate(outcomes):
            on = normalize_name(oc)
            if a_norm in on or (len(a_last) >= 4 and a_last in on):
                if i == 0:
                    return token_ids[0], token_ids[1]
                else:
                    return token_ids[1], token_ids[0]
    return token_ids[0], token_ids[1]
```

### 3.4.5 Token book state

```python
class TokenBook:
    def __init__(self, token_id: str, label: str) -> None:
        self.token_id = token_id
        self.label = label
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.last_trade_px: Optional[float] = None
        self.last_event_ts_ms: Optional[int] = None
        self.last_local_ts_ms: Optional[int] = None
        self.frames_received = 0

    def best_bid(self) -> Optional[float]:
        return max(self.bids.keys()) if self.bids else None

    def best_ask(self) -> Optional[float]:
        return min(self.asks.keys()) if self.asks else None

    def display(self) -> Optional[float]:
        # VALIDATED RULE (2026-05-06): display = midpoint of bid/ask
        b = self.best_bid()
        a = self.best_ask()
        if b is not None and a is not None:
            return (b + a) / 2.0
        if b is not None:
            return b
        if a is not None:
            return a
        return None
```

The midpoint rule matches the iPhone's displayed price within ~1-2¢ across active and quiet matches; sums across both players consistently land at 99-101¢.

### 3.4.6 WebSocket loop

```python
async def stream_player(book: TokenBook, stop_event: asyncio.Event) -> None:
    backoff = 1.0
    while not stop_event.is_set():
        try:
            async with websockets.connect(WS_URL, ping_interval=None, close_timeout=5) as ws:
                sub = {
                    "assets_ids": [book.token_id],
                    "type": "market",
                    "custom_feature_enabled": True,
                }
                await ws.send(json.dumps(sub))
                backoff = 1.0

                async def pinger():
                    while True:
                        await asyncio.sleep(10)
                        try:
                            await ws.send("PING")
                        except Exception:
                            return

                p_task = asyncio.create_task(pinger())
                try:
                    async for msg in ws:
                        if msg == "PONG":
                            continue
                        try:
                            payload = json.loads(msg)
                        except Exception:
                            continue
                        events = payload if isinstance(payload, list) else [payload]
                        for ev in events:
                            handle_event(book, ev)
                finally:
                    p_task.cancel()
        except Exception as exc:
            if stop_event.is_set():
                return
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
```

(For production, the subscription scope changes from one token to many — `assets_ids: [...all tokens for all matches...]` — and the routing dispatches by `asset_id` to the right TokenBook in a dict, rather than streaming to a single bound book.)

### 3.4.7 Event handlers

```python
def handle_event(book, ev):
    et = ev.get("event_type")
    aid = ev.get("asset_id")
    if aid and aid != book.token_id:
        return

    if et == "book":
        book.bids.clear()
        book.asks.clear()
        for level in ev.get("bids") or []:
            try:
                px = float(level["price"])
                sz = float(level["size"])
            except Exception:
                continue
            if sz > 0 and 0.0 <= px <= 1.0:
                book.bids[px] = sz
        for level in ev.get("asks") or []:
            try:
                px = float(level["price"])
                sz = float(level["size"])
            except Exception:
                continue
            if sz > 0 and 0.0 <= px <= 1.0:
                book.asks[px] = sz
        book.frames_received += 1

    elif et == "price_change":
        changes = ev.get("price_changes") or ev.get("changes") or []
        for c in changes:
            try:
                px = float(c["price"])
                sz = float(c["size"])
            except Exception:
                continue
            side = c.get("side", "")
            if not (0.0 <= px <= 1.0):
                continue
            target = book.bids if side == "BUY" else book.asks if side == "SELL" else None
            if target is None:
                continue
            if sz == 0:
                target.pop(px, None)
            else:
                target[px] = sz
        book.frames_received += 1

    elif et == "last_trade_price":
        try:
            px = float(ev.get("price"))
        except Exception:
            return
        book.last_trade_px = px
        book.frames_received += 1

    elif et is None and "bids" in ev and "asks" in ev:
        ev["event_type"] = "book"
        handle_event(book, ev)
```

## 3.5 What does NOT change

- `api_tennis_worker.py` — sports score data, untouched
- `cross_feed.py` — joins Polymarket matches with API-Tennis matches, untouched (just receives different price values)
- The dashboard frontend (`dashboard.html`, `dashboard.js`) — receives price values via the same JSON shape from `main.py`; values just come from a different upstream
- The trading-layer Polymarket US authenticated worker (positions, orders, account) — untouched (see section 4 for the open risk on this)
- Trade attribution, state recorder, momentum, all other workers — untouched

The change is scoped to `polymarket_worker.py` (and possibly a renamed/replaced file).

---

# Part 4 — Open risks and follow-on items

## 4.1 Trading venue alignment (user view)

The dashboard's price feed will move to Polymarket Global. The dashboard's existing positions/orders/account integration stays on Polymarket US.

These two could be misaligned. If the operator places trades on the iPhone and those trades execute on Polymarket Global, then the dashboard would show prices that match the iPhone (good) but the dashboard's positions would always be empty (bad — there would be nothing to attribute trades to, no position context for decisions).

What we know:
- Operator's trades **don't** appear in the operator's Polymarket.com (Global) account-view. Polymarket support confirmed this is expected.
- This **doesn't prove** trades execute on US either. They could be in some third surface we haven't identified.

Working assumption: existing US trading-layer integration is approximately aligned with iPhone trading. We are NOT changing it as part of this shipment. Once the price fix is in production, the operator should observe whether the dashboard's positions still reflect their actual iPhone activity. If they diverge, the trading layer becomes the next problem.

## 4.2 Trading venue alignment (developer view)

The Ed25519-authenticated Polymarket US worker that reads positions/orders/account stays untouched in this shipment. If a future shipment needs to migrate trading-layer reads to Polymarket Global, the new auth model is wallet-derived (EIP-712 signed orders, API keys derived from wallet signatures). Reference: existing Polymarket Global Python SDK `py_clob_client`, and the auth flow at https://docs.polymarket.com/api-reference/authentication.

## 4.3 One-sided book fallback

The validated display rule is midpoint of bid/ask. Current code falls back to bid (or ask) when only one side is populated — a transient state on liquid books, occasional on illiquid ones. The iPhone's behavior in genuinely empty-ask states is unverified. To revisit during sustained Phase 2 observation: capture an iPhone snapshot when the book is one-sided and confirm whether iPhone shows bid, ask, last_trade_price, or "—". Patch the fallback to match.

## 4.4 Sum-of-displayed-prices visualization

Displayed prices sum to ~99-101¢ across both players. The dashboard UI doesn't currently call attention to deviations from 100¢. Optional enhancement: show the sum next to each match row and mark it green if in the expected 0.97-1.03 range (matches the spec's CROSS_OUTCOME_GAP threshold), red outside. Not required for shipment but useful as a real-time data-quality indicator.

## 4.5 Match coverage

Some live US tennis matches may not have a Polymarket Global counterpart (markets exist on US that aren't listed on Global, or vice versa). Discovery should detect these and either:
(a) drop the row entirely (cleanest, but operator loses visibility into the match)
(b) show the row with a placeholder price and a "no Global market" marker (preserves visibility)

Recommendation: (b). Implement as a "global_status" field on the match state: `resolved | unresolved | no_global_market`.

## 4.6 Discovery latency

Gamma pagination takes ~1–3 seconds. Discovery runs every 60 seconds. This means a brand-new live match takes up to ~63 seconds to appear on the dashboard. Acceptable for tennis (matches last 1–3 hours). Not acceptable for sports with shorter event windows; revisit if the dashboard expands beyond tennis.

---

# Part 5 — Reference: endpoints, payloads, fields

## 5.1 Polymarket US Gateway (still used for discovery)

```
GET https://gateway.polymarket.us/v2/sports/tennis/events
  ?limit=100
  &offset=0
```

Response shape (relevant fields only):
```json
{
  "events": [
    {
      "id": "10678",
      "slug": "atp-juseng-nikizq-2026-05-04",
      "title": "Justin Engel vs. Nikolas Sanchez Izquierdo",
      "live": true,
      "ended": false,
      "score": "7-6(7-2), 2-5:15-30",
      "markets": [
        {
          "slug": "aec-atp-juseng-nikizq-2026-05-04",
          "marketSides": [
            { "description": "Justin Engel", "long": true, ... },
            { "description": "Nikolas Sanchez Izquierdo", "long": false, ... }
          ],
          "sportsMarketTypeV2": "SPORTS_MARKET_TYPE_MONEYLINE",
          ...
        }
      ]
    }
  ]
}
```

We use: `events[].live`, `events[].markets[0].slug`, `events[].markets[0].marketSides[].description`.

## 5.2 Polymarket Global Gamma (new, for token resolution)

```
GET https://gamma-api.polymarket.com/events
  ?active=true
  &closed=false
  &limit=100
  &offset=0
  &tag_slug=tennis
```

Response: array of event objects. Each event has `markets[]`:

```json
[
  {
    "id": 12345,
    "title": "Brazzaville: Florent Bax vs Adrian Arcon",
    "tags": [{"slug": "tennis"}, {"slug": "atp"}],
    "markets": [
      {
        "id": 67890,
        "question": "Brazzaville: Florent Bax vs Adrian Arcon",
        "slug": "florent-bax-vs-adrian-arcon-2026-05-05",
        "outcomes": "[\"Florent Bax\", \"Adrian Arcon\"]",
        "outcomePrices": "[\"0.93\", \"0.07\"]",
        "clobTokenIds": "[\"105060544933...\", \"101532849819...\"]",
        "active": true,
        "closed": false,
        ...
      }
    ]
  }
]
```

Critical:
- `outcomes`, `outcomePrices`, `clobTokenIds` are JSON-encoded **strings** at the top level. Decode with `json.loads()`.
- The two `clobTokenIds` correspond positionally to the two `outcomes`. To map to "player A", check which outcome string matches player A's name.
- `outcomePrices` is REST-cached and stale. Do NOT use for live prices.
- The `/markets` endpoint does NOT honor `tag_slug=tennis`. Use `/events`.

## 5.3 Polymarket Global CLOB WebSocket

**Endpoint:**
```
wss://ws-subscriptions-clob.polymarket.com/ws/market
```

**Auth:** None for read-only market data.

**Subscription message (client → server):**
```json
{
  "assets_ids": ["TOKEN_ID_1", "TOKEN_ID_2", ...],
  "type": "market",
  "custom_feature_enabled": true
}
```

**Heartbeat:** Send `PING` text frame every ~10s. Server may reply with `PONG` text.

### Event: `book`

Full snapshot for one token. On (re)subscribe, the server sends one of these per token. May also be re-sent during the connection.

```json
{
  "event_type": "book",
  "asset_id": "TOKEN_ID",
  "market": "MARKET_ID_OR_CONDITION_ID",
  "bids": [
    { "price": "0.45", "size": "100" },
    { "price": "0.44", "size": "250" }
  ],
  "asks": [
    { "price": "0.46", "size": "150" }
  ],
  "timestamp": "1710000000000",
  "hash": "BOOK_HASH"
}
```

Handling: clear local bids/asks for that token, load all entries.

### Event: `price_change`

Incremental delta. May contain multiple changes in one event.

```json
{
  "event_type": "price_change",
  "asset_id": "TOKEN_ID",
  "price_changes": [
    {
      "price": "0.45",
      "size": "80",
      "side": "BUY",
      "best_bid": "0.45",
      "best_ask": "0.46"
    }
  ],
  "timestamp": "1710000000000",
  "hash": "BOOK_HASH"
}
```

Some payloads use `changes` instead of `price_changes`. Support both.

Handling: for each change, route by `side` (BUY → bids, SELL → asks). `size=0` removes the level; `size>0` sets it.

### Event: `last_trade_price`

```json
{
  "event_type": "last_trade_price",
  "asset_id": "TOKEN_ID",
  "price": "0.46",
  "side": "BUY",
  "size": "50",
  "timestamp": "1710000000000"
}
```

Handling: store `price` for diagnostic display. Not used for the validated display rule.

### Event: `best_bid_ask`

Optional top-of-book signal.

```json
{
  "event_type": "best_bid_ask",
  "asset_id": "TOKEN_ID",
  "best_bid": "0.45",
  "best_ask": "0.46",
  "spread": "0.01",
  "timestamp": "1710000000000"
}
```

Handling: optional corroboration. Don't replace local book maintenance.

### Event: `market_resolved`

```json
{
  "event_type": "market_resolved",
  "asset_id": "TOKEN_ID",
  "market": "MARKET_ID",
  "timestamp": "1710000000000"
}
```

Handling: mark match as resolved, stop treating updates as live.

---

# Part 6 — Glossary

- **Slug** (Polymarket US): string identifier for a market on Polymarket US, e.g., `aec-atp-juseng-nikizq-2026-05-04`. Used for REST and WS subscriptions.
- **Token ID / asset ID** (Polymarket Global): long numeric string, an ERC1155 conditional token ID on the Polygon blockchain. Each outcome of a binary market has its own token ID.
- **Moneyline** (sports betting): a binary market on which side wins outright (no spread, no totals). For tennis, "Player A wins the match" vs "Player B wins the match."
- **CLOB**: Central Limit Order Book. The matching-engine model Polymarket uses (off-chain matching, on-chain settlement).
- **Best bid**: highest price someone is currently willing to pay to buy a share of an outcome.
- **Best ask** (or best offer): lowest price someone is currently willing to sell a share of an outcome at.
- **Midpoint**: `(best_bid + best_ask) / 2`. The validated iPhone display rule (see section 2.5) and the rule specified in the WS-only handoff doc.
- **Mirrored liquidity**: a buy order for outcome A automatically generates a synthetic sell order for outcome B at the complementary price. Why per-token book queries return seemingly-crossed bid/ask spreads.
- **Overround / spread / vig**: a deviation of the sum of two outcomes' midpoints from 1.00, indicating market-maker margin on tight books or transient cross-outcome divergence on fast moves.
- **Long / short** (Polymarket US `marketSides`): an arbitrary assignment Polymarket makes when creating a binary market. The "long" side gets `long=true`; the "short" side gets `long=false`. Empirically appears to follow alphabetical ordering of player abbreviations, but this is a slug-construction convention, not a market designation.
- **Gamma**: Polymarket Global's metadata API at `gamma-api.polymarket.com`. Public, no auth.
- **EIP-712**: an Ethereum standard for typed data signing. Polymarket Global uses it for order placement (not relevant to our read-only price feed).
- **Auth0 Private Key JWT**: the Polymarket US institutional API auth flow. Not relevant to our shipment.
- **Ed25519**: the public-key signature scheme used by Polymarket US consumer API. The dashboard's existing trading-layer integration uses this; we are not touching it.

---

# Part 7 — Appendix: prior history of failed approaches

Including this so future readers understand WHY the architecture is shaped the way it is.

**Approach 1: Use REST `marketSides[].quote.value` for both sides.** This is what early dashboard versions did and what v0.7.7 / v0.7.9 currently do. Side A's quote is real-time-ish; Side B's lags 20–60 seconds because the WS doesn't refresh `marketSides`.

**Approach 2: Derive Side B from Side A as `1 - best_ask`.** Implemented in v0.7.8. Operator rejected: produces unrealistic exact-100¢ sums, fabricates data instead of reading reality. Reverted.

**Approach 3: Use `stats.lastPriceSample.longPx / shortPx`.** Tried as a fallback. Slow update cadence; not real-time. Useful as a low-confidence backup but not a fix.

**Approach 4: Find a per-side endpoint on Polymarket US gateway.** None exists. Confirmed by reading the SDK source and trying various URL patterns (`/v1/markets/sides/{id}`, `/v1/markets/{slug}/sides`, etc. — all 404).

**Approach 5: Use Polymarket US Institutional gRPC.** Has the right shape (per-instrument symbols with independent books). But application-gated (apply to onboarding@qcex.com, not self-serve), uses Auth0 JWT instead of Ed25519, and crucially does NOT have the same liquidity as what the iPhone displays. Wrong venue.

**Approach 6: Use Polymarket Global CLOB WebSocket.** This is the chosen approach. Public, no auth, per-token streams, matches iPhone.

The journey through approaches 1–5 cost several days of iteration. The path forward is approach 6 with the validated display rule: midpoint = (best_bid + best_ask) / 2.

---

# End of document

The MVP code (`pm-mvp/app.py`) is the working reference. The implementation plan in the companion document (`PM-Tennis-Pricing-Implementation-Plan.md`) translates this into concrete shipment phases, acceptance criteria, and success conditions.
