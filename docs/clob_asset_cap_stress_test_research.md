# CLOB asset-cap stress test — research document (v4)

**Deliverable:** Phase 3 attempt 2, first deliverable (Ruling 1(e), H-010).
**Authors:** Claude, sessions H-010 (v1–v3), H-012 (v4 §13 additive), H-014 (v4 §15 additive).
**Version history:**
- v1 (H-010, earlier turn): initial document. Surfaced §2 ambiguity, §4 as set of unanswered questions, §7 as three operator decisions.
- v2 (H-010, earlier turn): §4 answered via operator-authorized web_fetch research. §2 ambiguity resolved. §3, §5, §7 updated against cited documentation. §11 added naming what research surfaced that changes v1's model.
- v2.1 (H-010, earlier turn): operator follow-up 1 on v2 review. §4.3 code block re-verified as verbatim from the Markets WebSocket page. §4.3.1 added surfacing a case-style inconsistency between the WebSocket Overview page and the Markets WebSocket page that v2 did not note.
- v3 (H-010, later turn): operator ruling Q5=(a). Polymarket US Python SDK README fetched and read. §4.3.1 resolved in favor of Markets WebSocket page's camelCase wire shape. §4.7 resolved: SDK uses a single slug namespace across REST and WebSocket on `api.polymarket.us`; bridging gateway slugs remains unverified but a cleaner path is now visible (§4.7.1). §12 added summarizing SDK-vs-hand-rolled code decision now surfaced. Scope tightened: v3 does not re-open any section not directly affected by the SDK read.
- **v4 (H-012): three H-012 rulings resolved and the §6 meta.json survey executed. §13 added capturing (a) the ruling on POD-H010-§12 = SDK (D-024), (b) the ruling on POD-H010-Q5′ = hybrid probe-first (D-025), (c) the authorization and execution of POD-H010-§6-survey (D-026), (d) the survey findings, (e) the probe-slug default for the Q5′=(c′) probe. v4 is additive only: §§1–12 are unchanged from v3. §5's "actual asset count we expect" estimate (≈38 at H-009 close) and §7's placeholder-bracket discussion are explicitly not revised; §13 cross-references them and notes the updated N=74 baseline instead, preserving v3's operator-accepted text.**
- **v4 §15 additive (H-014): three H-013 code-turn-research tasks resolved against authoritative sources (Ed25519 signing fully internal to SDK; timestamp unit milliseconds; SDK transitive-dep footprint 12 wheel-available packages). D-027 supersession of D-025 commitment 1 after Render disks confirmed strictly single-service — probe slug is now operator-supplied via `--slug=SLUG` CLI arg; D-025's other commitments unaffected. Probe scaffolding at `src/stress_test/` (H-013) documented. Known-stale artifacts from H-013's Option X cut (`src/stress_test/README.md`, `runbooks/Runbook_RB-002_Stress_Test_Service.md`) rewritten at H-014 start. §14 reserved for H-015 probe-outcome addendum. No sections in §§1–14 revised.**
**Status:** Draft document; v3 operator-accepted at H-010, §13 operator-accepted at H-012, §15 produced at H-014. Scaffolding code at `src/stress_test/` produced at H-013 per §13.5 (operator-committed, 38 unit tests passing, zero SDK mocking, live-probe deferred to H-015 per operator Option X cut). No live probe has been run against Polymarket US; no main-sweep run has been executed. Every external fact in §4 is cited with URL and excerpt per Ruling 2(a) and Tripwire 1. §15 findings extend the same discipline: SDK source and Render docs were fetched and cited before code was written or runbook procedures finalized.

---

## 1. What I-002 asks

From `RAID.md` (H-009 session-close version, committed at HEAD `6808b6c8`):

> **I-002** — CLOB pool asset-cap stress test — soft 150-asset pool cap not yet verified under stress. Severity 2. Deferred to Phase 3 when capture code skeleton exists. **Open — deferred to Phase 3 attempt 2.**

From `PM-Tennis_Build_Plan_v4.docx` §5.4:

> The capture worker maintains a pool of CLOB WebSocket connections, one per active match. Connections are recycled proactively every 15 minutes regardless of observed health, and a 90-second liveness probe backstops silent stalls. Pool size is bounded by the soft 150-asset cap (to be stress-tested in Phase 3).

From `PM-Tennis_Build_Plan_v4.docx` §11.3:

> soft 150-asset pool cap (2) — stress test deferred to Phase 3

**Unchanged from v1:** The cap itself is inherited; it is not derived in any committed source I have read. The origin of "150" is not documented in the repo. I continue to treat it as a stated design constraint whose origin is not documented. The §4 research now shows that the number does not correspond to any limit Polymarket US publishes, which reshapes the test's question — see §11.

---

## 2. The §2 ambiguity — resolved

v1 named a plan-level ambiguity: "one per active match" vs "150-asset cap" pointed at different units. Three possibilities were enumerated: per-identifier, multiplexed-by-asset, or per-match.

**Resolution from §4 research: none of the three v1 possibilities is correct. The actual Polymarket US subscription unit is `marketSlug`.** A single Polymarket US Markets WebSocket subscription accepts a list of `marketSlugs` (up to 100 per subscription); each subscription delivers order-book updates for all listed market slugs over a single connection. See §4.3.

One consequence: the `side.identifier` value that `src/capture/discovery.py` line 37 comments as "asset/token ID for CLOB subscription" is **not** the subscription unit for Polymarket US's documented Markets WebSocket. The actual subscription unit comes from a different field — `marketSlug` — which `discovery.py` already records (as `market_slug` on the `MoneylineMarket` dataclass, line 131). The `identifier` field may still be used internally by Polymarket US's systems, but the documented wire-level subscription input is the slug. This is a Phase-2 documentation correction — see §11 item 3.

---

## 3. What is currently known from committed project material

Unchanged from v1 except for the one row marked **[revised]**:

| Fact | Source | Notes |
|---|---|---|
| Polymarket US public gateway base URL | `discovery.py` line 86, D-013 | `https://gateway.polymarket.us`, no auth for reads |
| Gateway is HTTP/JSON, polled at 60s intervals | `discovery.py` lines 584ff, STATE `discovery.poll_interval_seconds` | Not the CLOB WebSocket |
| Polymarket US authenticated API base | STATE `architecture_notes` | `api.polymarket.us` |
| Tennis events currently active | STATE `discovery.first_poll_events_discovered` | 38, stable at H-009 close |
| **Each event carries moneyline markets with a `market_slug` and YES/NO sides. `market_slug` is recorded by Phase 2; `side.identifier` is also recorded but is not the documented CLOB subscription unit** **[revised]** | `discovery.py` lines 30–37 and 129–131 | Plan's "asset ID for CLOB subscription" comment is misleading against Polymarket US docs. See §11. |
| Non-moneyline markets exist on tennis events | Plan §2.1 | "moneyline, first-set winner, set handicap, match totals, and others" — discovery extracts moneyline only |
| Capture worker runs inside `pm-tennis-api` FastAPI process | D-014 | Stress test runs in this process if run in production |
| Render persistent disk growth currently ~290 MB/day (Phase 2 alone) | STATE `discovery`, R-012 | Stress test should not materially accelerate this |

Observation from `discovery.py` preserved: `side.marketSideType` has values like `"MARKET_SIDE_TYPE_ERC1155"` (dataclass comment at line 124). Per operator direction in H-010 review, this is an observation only; **v2 does not infer WebSocket protocol details from it.**

---

## 4. External research — citations per Tripwire 1

All citations in this section were fetched via `web_fetch` in the session that produced v2 (2026-04-19). URLs were reached via `web_search` starting from the query "Polymarket US CFTC CLOB WebSocket developer documentation" and follow-up queries. Fetched content is quoted with ellipsis where appropriate; the cited URL is the fetch target.

Every claim below is from `docs.polymarket.us` (Polymarket US), not `docs.polymarket.com` (offshore). Per D-013 and v1 §4.6, offshore sources were not used to infer any Polymarket US behavior.

### 4.1 Endpoint

**Claim:** The Polymarket US Markets WebSocket endpoint is `wss://api.polymarket.us/v1/ws/markets`. A sibling endpoint `wss://api.polymarket.us/v1/ws/private` serves private user data (orders, positions, balances) and is not in scope for this deliverable.

**Source:** WebSocket API Overview — "Connect to the WebSocket endpoints with your API key credentials: wss://api.polymarket.us/v1/ws/private wss://api.polymarket.us/v1/ws/markets"
URL: `https://docs.polymarket.us/api-reference/websocket/overview`

### 4.2 Authentication

**Claim:** Both Polymarket US WebSocket endpoints require API-key authentication. Three headers participate in the connection handshake: `X-PM-Access-Key`, `X-PM-Timestamp`, `X-PM-Signature`. The signature is constructed from `timestamp + "GET" + path` where path is `/v1/ws/private` or `/v1/ws/markets`. The underlying authentication scheme is Ed25519 per the Polymarket US authentication page (timestamps must be within 30 seconds of server time).

**Sources:**
- WebSocket API Overview — endpoint table shows both `/v1/ws/private` and `/v1/ws/markets` require "API Key" authentication; handshake headers listed are X-PM-Access-Key, X-PM-Timestamp, X-PM-Signature; signature is "timestamp + 'GET' + path"
URL: `https://docs.polymarket.us/api-reference/websocket/overview`
- Authentication page — "If you're not using an SDK, each request needs three headers: The signature is built by combining the timestamp, HTTP method, and path, then signing it with your secret key. Timestamps must be within 30 seconds of server time."
URL: `https://docs.polymarket.us/api-reference/authentication`

**Crypto detail not committed to code yet.** The precise byte-level signing operation (Ed25519 over exactly what input bytes) is a detail the code turn must verify via the authentication page or the official Python SDK (`polymarket-us-python`, searchable on GitHub per search result 11). v2 does not commit to a signing code path; it commits only to the three-header fact and the Ed25519 algorithm.

**Consequence:** read-only market-data access for the stress test requires a funded, KYC-verified Polymarket US account with API credentials generated at `polymarket.us/developer`. The operator already holds a funded account per plan §1.2 and STATE `deployment.backend` context. Whether API credentials have been generated for this project is unknown to me at this time and is surfaced to operator in §7 Q4 (new below).

### 4.3 Subscription model

**Claim:** The subscription unit is **`marketSlug`** (not asset ID, not condition ID, not event ID, not token ID). A subscription request names one or more market slugs in a `marketSlugs` array. A single connection can carry multiple subscriptions; a single subscription can name up to 100 market slugs.

**Subscription message format — verbatim excerpt from the Markets WebSocket page "Subscribe to Full Market Data" example:**

```
{
  "subscribe": {
    "requestId": "md-sub-1",
    "subscriptionType": "SUBSCRIPTION_TYPE_MARKET_DATA",
    "marketSlugs": ["market-slug-1", "market-slug-2"]
  }
}
```

*(v2 rendered this inside a ` ```json ` fenced block; the docs page renders it without a language tag. Content — keys, values, ordering, whitespace — is unchanged. v2.1 removes the language tag to match the source exactly.)*

**Subscription types available on `/v1/ws/markets`** (verbatim names from the Markets WebSocket page's "Subscription Types" table; the text after the em-dash is my one-line paraphrase, not part of the source):

- `SUBSCRIPTION_TYPE_MARKET_DATA` — full order book and market stats
- `SUBSCRIPTION_TYPE_MARKET_DATA_LITE` — lightweight price data only
- `SUBSCRIPTION_TYPE_TRADE` — real-time trade notifications

**Source:** Markets WebSocket page — subscription request shown with `marketSlugs` array; subscription types listed as `SUBSCRIPTION_TYPE_MARKET_DATA`, `SUBSCRIPTION_TYPE_MARKET_DATA_LITE`, `SUBSCRIPTION_TYPE_TRADE`; response format shows `marketSlug` in the response payload
URL: `https://docs.polymarket.us/api-reference/websocket/markets`

### 4.3.1 Case-style inconsistency between the two Polymarket US WebSocket pages (surfaced in v2.1, resolved in v3)

During v2.1 verification, a real inconsistency between two Polymarket US documentation pages surfaced. v2 did not note it. It has material implications for code, so it is called out here:

**WebSocket API Overview page** (`/api-reference/websocket/overview`) states:

> "All WebSocket messages are JSON formatted with snake_case field names."

…and shows its generic Request Format example as:

```
{
  "subscribe": {
    "request_id": "unique-request-id",
    "subscription_type": 1,
    "market_slugs": ["market-slug-1", "market-slug-2"]
  }
}
```

Note: `request_id`, `subscription_type` (integer `1`), `market_slugs` — **snake_case, integer subscription type**.

**Markets WebSocket page** (`/api-reference/websocket/markets`) shows its specific Subscribe to Full Market Data example as the block reproduced in §4.3 above: `requestId`, `subscriptionType` (string enum `"SUBSCRIPTION_TYPE_MARKET_DATA"`), `marketSlugs` — **camelCase, enum-string subscription type**.

The two pages contradict each other on both the case style and the subscription-type value representation.

**Resolution in v3 (via SDK README read):**

The Polymarket US Python SDK README (fetched v3, `https://github.com/Polymarket/polymarket-us-python`) shows the Markets WebSocket handler code as:

```python
markets_ws.on("market_data", lambda d: print(f"Book: {d['marketData']}"))
markets_ws.on("trade", lambda d: print(f"Trade: {d['trade']}"))
```

The response data is dereferenced as `d['marketData']` — **camelCase**, matching the Markets WebSocket page's response schema (§4.3 excerpt includes a top-level `"marketData": { ... }` response object). The README's event-name strings `"market_data"` and `"trade"` are Python event dispatch names defined by the SDK, **not** wire-protocol field names.

**Conclusion:** The Markets WebSocket wire format is camelCase with enum-string subscription types. The Overview page's "snake_case" prose and integer-typed example are stale documentation; they were not verified against the current server implementation. Option (a) from v2.1's enumeration stands.

**Important qualification not resolved by the README alone:** the SDK README shows Python API calls (`.subscribe(request_id, subscription_type, market_slugs_list)`) and response handlers (`d['marketData']`). It does NOT show the literal JSON bytes the SDK's internal code emits on the WebSocket. The inference that the wire format matches the Markets WebSocket page's camelCase example is strongly supported by the response-side evidence but not byte-confirmed from the SDK source. The code turn will either:
- Use the SDK directly (which makes wire-shape correctness the SDK's responsibility — see §12 below), or
- If hand-rolling, fetch `github.com/Polymarket/polymarket-us-python` source and cite the exact line where the subscribe JSON is constructed.

**Code implication (updated):** Tripwire 1 still applies to hand-rolled code paths; v3 does not lift it. What v3 does say: the camelCase wire shape is the one to target, and any test that begins by sending the snake_case shape the Overview page shows would be sending a shape there is now direct evidence against.

### 4.4 Documented limit — per-subscription cap

**Claim:** A single subscription on `/v1/ws/markets` accepts at most 100 market slugs. Multiple subscriptions can be opened on the same or separate connections to cover more.

**Source:** Markets WebSocket page subscription-limits callout — "You can subscribe to a maximum of 100 markets per subscription. Use multiple subscriptions if you need more."
URL: `https://docs.polymarket.us/api-reference/websocket/markets`

This is the only explicit numeric limit I found in the authoritative Polymarket US WebSocket documentation.

### 4.5 Rate limits and connection caps — not documented where I looked

**Claim:** The Polymarket US `/api-reference/websocket/overview` and `/api-reference/websocket/markets` pages do **not** document any of the following: per-connection subscription count limit beyond the 100-per-subscription cap; per-IP connection count limit; per-account connection count limit; message-receive rate limit; subscription-create rate limit; behavior when limits are exceeded (close code, error payload, or silent drop).

**Sources searched:** the two pages fetched above, plus `web_search` queries "`docs.polymarket.us` rate limits" and variants. Third-party sources (quantvps blog, agentbets blog) state contradictory numbers (60/min, "up to 10 instruments," 15,000/10s); these either quote offshore-Polymarket numbers or are unsourced. I did not find a dedicated Polymarket US rate-limits page. This is a documented non-finding, not a gap in my search I am declining to mention.

**Consequence for the stress test:** the test has to actually measure connection-count and subscription-count behavior empirically, because the authoritative documentation is silent on it. This is the original motivation of I-002 — the cap is "soft" precisely because the code has never seen it under load.

### 4.6 Heartbeats and keepalive

**Claim:** The server sends heartbeat messages (`{"heartbeat": {}}`). Clients are advised to either respond to heartbeats or implement their own keepalive. No specific interval is documented on the overview page.

**Source:** WebSocket API Overview heartbeats section — "The server sends periodic heartbeat messages to keep the connection alive: {\"heartbeat\": {}}. Clients should respond to heartbeats or implement their own keep-alive mechanism."
URL: `https://docs.polymarket.us/api-reference/websocket/overview`

Plan §5.4 specifies a 90-second liveness probe; that requirement is orthogonal to whatever server-side heartbeat cadence Polymarket US uses and can coexist.

### 4.7 Slug origin — partially resolved by v3 SDK read

**Question (from v2):** Whether the `market_slug` values Phase 2 `discovery.py` reads from `gateway.polymarket.us/v2/sports/tennis/events` are identical to the `marketSlugs` values accepted by `wss://api.polymarket.us/v1/ws/markets`.

**What the SDK README established:**

The Polymarket US Python SDK (`github.com/Polymarket/polymarket-us-python`, README fetched v3) exposes a single slug namespace across its REST and WebSocket surfaces:

- `client.events.retrieve_by_slug(slug)` — REST, by slug
- `client.markets.retrieve_by_slug(slug)` — REST, by slug
- `client.markets.book(slug)` — REST order book, by slug
- `client.markets.bbo(slug)` — REST best bid/offer, by slug
- `await markets_ws.subscribe("md-sub-1", "SUBSCRIPTION_TYPE_MARKET_DATA", ["btc-100k-2025"])` — WebSocket subscribe, by slug

The README example uses `"btc-100k"` for REST and `"btc-100k-2025"` for WebSocket (these are demonstration strings, possibly for the same market — the README doesn't say). What is consistent is the format: lowercase-with-hyphens, descriptive. **`api.polymarket.us` uses a single slug namespace across REST and WebSocket.** That portion of v2's §4.7 question is resolved.

**What the SDK README does NOT establish:**

Whether a slug observed on `gateway.polymarket.us/v2/sports/tennis/events` is the same string that `api.polymarket.us`'s `markets.retrieve_by_slug()` or `markets_ws.subscribe()` would accept. The gateway is a separate base URL. The SDK does not mention the gateway. The two plausibilities from v2 narrow to two:

- (a') Gateway and api share a slug namespace — most likely, since both products are operated by Polymarket organization and serve the same underlying market catalog. But **not confirmed by any source I have fetched.**
- (b') Gateway exposes a distinct slug namespace — possible if the gateway is a read-only proxy with different slug derivation.

**Important alternative the SDK read surfaced:**

The SDK provides `client.markets.list()` and `client.markets.retrieve_by_slug()` on `api.polymarket.us` directly. If Phase 3 attempt 2 uses the SDK's `markets.list()` for market discovery instead of the gateway poll, the gateway-to-api bridge question disappears — the same client is the source of truth for both slugs and subscriptions. This is a **design option for the code turn**, not a rewrite of Phase 2 (Phase 2 uses the gateway, is committed and live, and §10 of the H-010 scope forbids touching `discovery.py`).

Two possible architectures going forward:

- **Stress-test-from-api** — use the SDK or raw HTTPS against `api.polymarket.us/v1/markets` to list markets and obtain slugs, then subscribe via `/v1/ws/markets`. Gateway-to-api bridge is never tested because it's never used for the stress test. This is cleanest for the stress test but produces no evidence on whether gateway slugs work with the WebSocket, which Phase 3 full deliverable may want to know.
- **Stress-test-from-gateway** — use the slugs Phase 2 already wrote to meta.json, feed them to `/v1/ws/markets`, observe whether they accept. This is an explicit test of the bridge.

The choice affects what the stress test *proves*, not whether it can run. v3 does not decide between them — this is now surfaced as **§7 Q5' (new in v3)** below.

**How the remaining unknown gets resolved:**
1. An exploratory single-subscription test (still v2's option 3, renumbered to Q5' (b) in §7): pick one gateway-listed slug, subscribe via `api.polymarket.us/v1/ws/markets`, observe accept-or-error. This is the cheapest probe and gives a definitive answer.
2. Fetch the SDK source (not just README) to see if `api.polymarket.us`'s markets list produces slugs identical to gateway output.
3. Operator-supplied confirmation.

### 4.8 Offshore sources considered and rejected

Per D-013 and v1 §4.6, I did not use content from any of the following to establish any fact above:
- `docs.polymarket.com` (offshore developer docs)
- `clob.polymarket.com` (offshore CLOB endpoint)
- `gamma-api.polymarket.com` (offshore Gamma API)
- `ws-subscriptions-clob.polymarket.com` (offshore CLOB WebSocket)

These URLs appeared prominently in search results for generic "Polymarket" queries. They describe a structurally different product (Polygon-chain, EIP-712/L1 + HMAC-SHA256/L2 auth, asset-id subscription, different endpoints). Using their documentation to infer Polymarket US behavior would be a D-013 violation and a Tripwire-1 fabrication by transposition.

---

## 5. Proposed stress-test shape — now bracketed by real numbers

**Test objective (invariant from v1):** Determine whether a pool of N *subscriptions* (plural, across some number of connections) can be sustained stably for a meaningful duration against `wss://api.polymarket.us/v1/ws/markets` without (a) disconnections, (b) rate-limiting, (c) message loss, or (d) process exhaustion.

**Definitions clarified in v2:**

- **Subscription** = a single `{"subscribe": {...}}` message carrying up to 100 market slugs.
- **Connection** = a single WebSocket session to `wss://api.polymarket.us/v1/ws/markets`, authenticated with the handshake headers. Multiple subscriptions may be multiplexed onto one connection per §4.3.
- **N** = total number of distinct market slugs being tracked across all subscriptions on all connections.

**"Actual asset count we expect"** (operator-adjusted Ruling 3 language, D-020):

Under the moneyline-only scope that `discovery.py` currently captures, the slug count is one per moneyline market per event. With 38 active tennis events at H-009 close and (probably) one moneyline market per event, the current demand is ≈38 slugs. This is well below the 100-per-subscription cap — a single subscription on a single connection covers it.

Slam-week scope projection: 128 first-round singles × 1 moneyline = 128 slugs across both tours at peak. Still a single connection; would require two subscriptions (100 + 28). If non-moneyline markets are ever brought into scope (plan §2.1 lists four), per-event slug count rises to 4, and slam-week peak = 128 × 4 = 512 slugs → 6 subscriptions spread across any number of connections ≥ 1.

**None of these numbers exceeds the 100-per-subscription cap by more than ~5×, and all are within plausible multi-subscription multiplexing.** The stress test no longer has a natural bracket at 150 "assets" — because 150 assets (now read as 150 slugs) is (a) not a Polymarket US limit, (b) reachable with 2 subscriptions, (c) already exceeded in the slam-week projection under any meaningful scope expansion. The test's question has to reshape — see §11.

**Revised test shape:**

The stress test should measure two things the docs don't specify:

1. **Per-connection subscription count**: how many subscriptions can multiplex onto a single connection before Polymarket US drops or rejects new subscriptions. The documentation is silent (§4.5). Empirical target: add subscriptions to a single connection until a failure mode fires. Start conservative (1, 2, 5, 10 subscriptions per connection, each at 100 slugs of placeholder targets — see §7 Q5 about placeholders).
2. **Per-IP or per-account connection count**: how many WebSocket connections can be held simultaneously by the `pm-tennis-api` process before any Polymarket US limit kicks in. Start conservative (1, 2, 3 connections) with the stated warning that commercial API services typically cap concurrent connections per account at single-digit to low-double-digit numbers.

**Failure modes the test must surface explicitly** (unchanged from v1 but refined):
- Handshake rejected with a 401/403 (auth issue, not a limit issue — stop and surface).
- Subscription-accept response not received within a documented-or-reasonable window.
- `error` field returned in response to a subscribe message (§4 shows this shape on the overview page).
- Connection closed by server with a close code. Log the close code and surface.
- Connection stays open but heartbeats stop (§4.6).
- Process-level memory or file-descriptor exhaustion on the Render Starter instance.

**Test duration:** proposed 15 minutes per configuration, as in v1. Keeps R-012 runway consumption immaterial.

**What the test does not attempt** (unchanged from v1):
- Full CLOB pool lifecycle (15-min recycle, 90-sec liveness probe).
- Persistence of received tick data to JSONL.
- Sports WS correlation.

---

## 6. Data needed from the live environment before the test — unchanged from v1

**Unchanged.** A read-only meta.json survey on the Render persistent disk is still needed to confirm the current distribution of `moneyline_markets[].marketSides[]` counts per event. v2's §4.3 resolution of the subscription unit does not remove the need for the survey — it refines what the survey is counting (market slugs, not side identifiers).

Per operator direction: the survey is run by the operator via Render shell **after** v2 of this document is complete. v2 is now complete. The survey is the next action after this document is accepted.

---

## 7. Design decisions I need from the operator — updated

v1 surfaced three design questions (Q1–Q3). v2 preserves them and adds two more (Q4–Q5) that only became visible after §4 research.

**Q1. Does the stress test write to disk?**
- (a) Pure connection-level test — establish and hold subscriptions, verify liveness, discard received tick content.
- (b) Full-path test including envelope write.

*Claude's recommendation unchanged from v1:* **(a)** for this deliverable.

**Q2. Does the stress test run on Render (production) or elsewhere?**
- (a) Run on Render — production conditions. Touches the live `pm-tennis-api` process.
- (b) Run on a separate Render service — a purpose-built stress-test service, isolated from `pm-tennis-api`, deployed and torn down for the test.
- (c) Run locally via a temporary harness — not feasible per v1 §7 Q2 analysis (no local developer workstation).

*Claude's recommendation changed slightly for v2:* **(b)** — a separate Render service. This avoids touching `main.py` (session scope constraint), avoids consuming file descriptors on the production discovery service, and can be deleted cleanly when the test is done. It adds the small operational cost of spinning up and tearing down one extra Render service. This is a revision from v1's soft recommendation of (a)-via-admin-endpoint.

**Q3. What N values does the test target?**

Now shaped by §4.4 (100-per-subscription cap) and §4.5 (nothing else documented).

- (a) Sweep per-connection subscription counts: 1, 2, 5, 10 subscriptions per connection × 100 placeholder slugs each = 100, 200, 500, 1000 tracked slugs at a single connection. Measure the point of first failure.
- (b) Sweep connection counts: 1, 2, 4 connections, each with 1 subscription × 100 slugs. Measure whether concurrent connections trigger a separate limit.
- (c) Both — do (a) and (b) in sequence. (Takes longer but gives the cleanest data.)
- (d) Something else.

*Claude's recommendation:* **(c)** — both sweeps, total ~30 minutes of run time, trivial R-012 impact. (a) informs the pool design directly; (b) informs whether the pool needs multi-connection fanout.

**Q4. (NEW in v2) API credential generation.**

§4.2 established that Markets WebSocket requires API-key authentication. I do not know whether the operator has generated API credentials at `polymarket.us/developer` for this project.

- (a) Credentials exist — operator supplies Key ID and Secret Key via Render environment variables (never committed to repo per D-005 / SECRETS_POLICY). Stress-test code reads them via `os.environ`.
- (b) Credentials do not exist — operator generates them at `polymarket.us/developer` before the stress test runs. Generation is outside the session (operator-only action on polymarket.us).
- (c) Credentials exist but operator wants a separate stress-test key — to bound what a test-only code path can access.

**I cannot write authentication code until this is resolved.** Tripwire 1 applies: whatever the stress test sends in `X-PM-Access-Key` must come from the operator.

**Q5. (NEW in v2; resolved in v3 by operator ruling Q5=(a).)** Slug namespace verification (§4.7).

Operator ruled (a) at v2 review: read the Polymarket US SDK. Done in v3 (this turn). See §4.7 for the partial resolution.

**Q5'. (NEW in v3)** Slug source for the stress test — gateway or api.

The SDK read resolved that `api.polymarket.us` REST and WebSocket share a slug namespace. It did not confirm that `gateway.polymarket.us` slugs are usable directly on `api.polymarket.us`. Two architectures for the stress test:

- (a') **Stress-test-from-api** — get slugs from `api.polymarket.us/v1/markets` (via the SDK or raw HTTPS). Subscribe on `/v1/ws/markets`. No gateway-to-api bridge is tested; the stress test is clean. But the gateway-to-api slug compatibility question remains open for Phase 3's later deliverables.
- (b') **Stress-test-from-gateway** — use slugs Phase 2 wrote to meta.json (gateway-sourced). Subscribe on `/v1/ws/markets`. The stress test simultaneously characterizes subscription behavior *and* tests the gateway-to-api bridge. If a gateway slug fails to subscribe, that's data about the bridge, not a test failure.
- (c') **Hybrid** — begin with a single real-slug probe (one gateway slug) to resolve the bridge question definitively, then decide (a') or (b') for the full stress test based on the probe result. Claude's preferred path — most research-first-consistent.

*Claude's recommendation:* **(c')** — hybrid, probe first. The probe is ~30 seconds of code (connect, authenticate, subscribe with one slug, observe response, disconnect) and resolves the question independently of the stress-test's main measurements.

---

## 8. Session-scope boundaries acknowledged — unchanged from v1

Unchanged. Added note: v2 research confirmed WebSocket subscription to live order books is the test's object. That is not a deviation; it is the test per D-018. The v1 §8 guardrail about "something weirder" applies if, e.g., authentication turns out to require capabilities the operator does not hold.

---

## 9. Decisions and non-decisions — updated

**Decided (committed by operator ruling at v2 review, no further decision needed):**
- First deliverable is the asset-cap stress test (D-018).
- Research-first form is standalone document → review → code (D-019).
- Testing posture is unit tests + lightweight live smoke (D-021).
- Commit cadence is periodic commits + session-end handoff (D-022).
- Definition of done for stress test = "runs to completion against the actual gateway with the actual asset count we expect" (D-020).
- **Q1 = (a)** pure connection-level test, no disk writes.
- **Q2 = (b)** separate Render service, isolated, torn down after.
- **Q3 = (c)** both sweeps (per-connection subscription count × concurrent connection count).
- **Q5 = (a)** SDK read first. Executed in v3 turn.

**Resolved by v2 §4 research + v3 SDK read:**
- Endpoint = `wss://api.polymarket.us/v1/ws/markets` (§4.1).
- Authentication = API-key, three-header, Ed25519, 30-second clock window (§4.2).
- Subscription unit = market slug, **wire format camelCase with enum-string subscription types** (§4.3, resolved in §4.3.1 via SDK README read).
- Per-subscription cap = 100 market slugs (§4.4).
- `api.polymarket.us` REST and WebSocket share a single slug namespace (§4.7, first half).
- Offshore docs not used (§4.8).

**Not yet decided; operator review of v3 is the decision point:**
- **§7 Q4** — API credential status. Still requires operator input. Claude was delegated this at v2 review but has no visibility into whether credentials exist at `polymarket.us/developer`. Surfacing back: this needs the operator's direct answer, not Claude's best guess.
- **§7 Q5' (new in v3)** — slug source for the stress test (api / gateway / hybrid). Claude's recommendation: hybrid with probe first.
- **§12 (new in v3)** — SDK-vs-hand-roll decision for the stress-test code.

**Unknown and not resolved by any fetch or SDK read (flagged for the code turn, not this document):**
- Precise Ed25519 signing byte-level operation. Fetch `github.com/Polymarket/polymarket-us-python` source at code-turn time, not assumed.
- Rate limits, connection caps, per-account limits (§4.5). The test will measure these empirically — that is the test.
- Whether gateway-sourced slugs are usable on `api.polymarket.us` (§4.7, second half). Resolved by Q5' ruling or by the probe the Q5'=(c') hybrid path runs.

**Not in scope for this deliverable** (unchanged):
- CLOB pool lifecycle behavior (15-min recycle, 90-sec liveness).
- Archive write pipeline.
- Sports WS client, correlation layer, handicap updater.
- First-server identification.

**§6 meta.json survey:** per operator direction, runs after v3 completes (i.e. next turn or next session).

---

## 10. Next action if v3 is accepted

Per operator's direction at v2 review: v3 is produced as a narrow §4.7 resolution turn, then stop and wait. v3 does not propose additional immediate work — Claude waits for operator to (1) accept or reject v3, (2) rule on Q4 and Q5' (and §12), and (3) authorize the §6 meta.json survey walkthrough.

Sequence from here:

1. **Operator reviews v3.** Accepts or requests v3.1.
2. **Operator rules on Q4 (API credentials), Q5' (slug source), and §12 (SDK vs hand-roll).**
3. **§6 meta.json survey.** Operator runs it via Render shell with Claude's walkthrough. Survey produces the concrete slug-count baseline the stress test targets.
4. **Code turn.** Stress-test code gets written per operator rulings and against the citations in this document. Code uses either the SDK (if §12 = (a)) or hand-rolled WebSocket code (if §12 = (b) or (c)).

No code is written before step 4. No commitment files are touched. `discovery.py` and `main.py` remain unchanged.

---

## 11. What v2 research surfaced that changes v1's model

Three findings that reshape how the deliverable is understood.

1. **The "150-asset cap" is not a real Polymarket US limit.** Polymarket US documents one numeric cap on the Markets WebSocket: 100 market slugs per subscription. The plan's 150 does not correspond to any documented Polymarket US value. The stress test's function is no longer "verify the documented cap" — it is "characterize undocumented limits that the plan anticipated would exist." This is a stronger motivation for the test, not a weaker one, but it means the test's name ("asset-cap stress test") is inherited nomenclature; the test is actually a **per-connection subscription-multiplexing and concurrent-connection stress test**. No renaming is proposed in this session — the task's identity carries over from I-002 — but flagging it for the operator's awareness.

2. **Authentication is required for market data, contra an open question in v1 §4.2.** v1 left open whether Markets WebSocket read-access might be unauthenticated (since the HTTP gateway is). It is not. This shifts Q4 (API credentials) from an implementation detail to a blocker for any stress-test code.

3. **`discovery.py` line 37's comment — `"side.identifier — asset/token ID for CLOB subscription"` — is misleading against Polymarket US's actual subscription model.** The documented subscription unit is `marketSlug`, not `side.identifier`. `discovery.py` already records both fields, so the correction is cosmetic (a comment edit), not a code change to the extractor. Surfacing as a Phase 2 documentation issue, not a Phase 3 attempt 2 deliverable. **This is not fixed in this session** (operator direction: "do not touch discovery.py"). Tracking: a candidate RAID issue or STATE `pending_revisions` item at session close, for operator decision.

---

## 12. SDK versus hand-rolled WebSocket client — new in v3

The SDK read in v3 surfaced an architectural decision that v1 and v2 did not visibly contemplate: whether the stress-test code uses the official `polymarket-us` Python SDK or writes its own WebSocket client.

**Option (a): Use `polymarket-us` SDK.** `pip install polymarket-us`. Stress-test code uses `client.ws.markets()`, `await markets_ws.connect()`, `await markets_ws.subscribe("md-sub-1", "SUBSCRIPTION_TYPE_MARKET_DATA", [slug_list])`. Authentication, signing, reconnection, and wire format correctness are the SDK's responsibility. Tripwire 1 is satisfied by using documented SDK methods (each SDK symbol referenced in code comes from the SDK README — a source in this session).

**Option (b): Hand-rolled client.** Phase 3 attempt 2's code implements its own WebSocket client against the documented shapes in §4. Signing done via `cryptography` library Ed25519. Closer to plan §5.4's implied model where the pool is an application-level construct. But every wire field name becomes a Tripwire 1 concern: every hardcoded string must cite the documentation page that shows it.

**Option (c): Hybrid.** Use the SDK for authentication and connection setup (where signing complexity lives); hand-roll the pool-management and subscription-multiplexing layer on top.

**Tradeoffs:**

| Concern | (a) SDK | (b) Hand-roll | (c) Hybrid |
|---|---|---|---|
| Tripwire 1 exposure | Minimal — SDK owns wire format | High — every field is a citation requirement | Moderate |
| Phase 3 full-deliverable fit | Unknown — SDK's pool-management semantics may or may not match plan §5.4's recycle/liveness design | Clean — the code *is* the pool | Good — SDK handles connection, we own pool |
| Dependency weight | One package (`polymarket-us`). Python 3.10+ already compatible with Phase 2's 3.12. | Zero new dependencies; uses `websockets` or `httpx` already likely present. | `polymarket-us` + whatever the pool uses |
| Risk of SDK quirks | Non-zero — the SDK is young (5 GitHub stars at v3 fetch time, 2 contributors, 10 commits). A bug in the SDK is harder to diagnose than a bug in our own code. | Zero | Limited |
| Code visibility | Lower — SDK internals are not obvious | Full — we wrote every line | Mixed |

*Claude's recommendation:* **(a) for the stress test, defer (c) decision to post-stress-test.** The stress test's goal is to characterize Polymarket US's limits, not to exercise the pool-management code we will eventually write. Using the SDK for the stress test gets us to "can we hold N subscriptions across M connections?" fastest, with minimal Tripwire 1 exposure. The full Phase 3 deliverable (pool with 15-min recycle, 90-sec liveness) is a separate later code task and can be re-evaluated then.

**Operator ruling needed.** If (a), the next code turn adds `polymarket-us` to a new requirements file in the separate Render service (per Q2=(b)) and uses SDK methods throughout. If (b) or (c), code will need an additional research step before it runs — probably a fetch of the SDK source to verify the exact wire-format byte sequence.

---

*End of research document — v3, session H-010.*

---

## 13. H-012 rulings and §6 survey findings — new in v4

This section closes out three of the four H-010 PODs in a single H-012 session and records the §6 meta.json survey results. §§1–12 are unchanged from v3.

### 13.1 H-012 rulings summary

Three operator rulings at H-012. Each is a full DecisionJournal entry; this section cross-references them and records their effect on this document.

**POD-H010-§12 → D-024: SDK (option a).** The stress-test code is built on the official Polymarket US Python SDK (`polymarket-us`, `github.com/Polymarket/polymarket-us-python`). Ships fastest, minimal Tripwire 1 exposure, one new dependency. Does not commit the Phase 3 full deliverable (CLOB pool with 15-min recycle + 90-sec liveness) to SDK-based construction — that architectural choice is re-evaluated after stress-test results are in hand.

**POD-H010-Q5′ → D-025: hybrid probe-first (option c′).** The stress test runs a one-slug probe as its first runtime action after authentication: one gateway-sourced slug from Phase 2's `meta.json` archive is subscribed via the SDK against `wss://api.polymarket.us/v1/ws/markets`; probe outcome determines slug source for the main sweeps. Probe-outcome-dependent branch for the main sweeps: api-sourced (`markets.list()`) by default, with gateway-sourced as an option if the bridge is confirmed working and the operator wants to continue exercising it. The probe is ~30 seconds of code; its outcome is itself data captured in a later addendum.

**POD-H010-§6-survey → D-026: authorized and executed in-session.** Render-shell walkthrough completed at 2026-04-19T16:22:29Z. §13.2 below records findings.

With D-024/D-025/D-026 logged, the three H-012 PODs that blocked the code turn are resolved. The code turn is no longer blocked on operator decisions — it is blocked only on the code-turn-research items flagged in D-023 (byte-level Ed25519 signing via SDK; timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication`).

### 13.2 §6 meta.json survey findings

Survey executed as a single consolidated bash script on the `pm-tennis-api` Render shell at 2026-04-19T16:22:29Z. Script content is reproduced in Handoff_H-012 §4; reproduced here only by its five-section outputs.

**Section 1 — Inventory.**
- `/data/matches/` exists as the per-match meta.json directory (correcting the research-doc v3 casual reference to "/data/events/"; `/data/events/` is the raw-poll-snapshot JSONL directory per `src/capture/discovery.py` `_events_snapshot_dir()`, not the per-match meta directory).
- Total `meta.json` files on disk: **74**. STATE v9 `discovery.meta_json_files_written` records 38 as of H-009 close; the 74 figure reflects ~36 hours of continuous Phase 2 discovery adding new events to the immutable archive since H-009. The growth is expected behavior — `_write_meta` never overwrites (discovery.py line 371).

**Section 2 — Schema verification.** Sample `meta.json` contents match the `TennisEventMeta` dataclass in `src/capture/discovery.py` lines 139–193 exactly. Top-level `moneyline_markets` is an array; each element has `market_id`, `market_slug`, `active`, `closed`. The sample slug is `"aec-atp-digsin-meralk-2026-04-21"` — lowercase, hyphen-separated, with an `aec-` prefix observed consistently across all 40 surveyed slugs in Section 5. The `aec-` prefix is a Polymarket US convention; v4 does not attempt to interpret it. Participant type observed is `PARTICIPANT_TYPE_TEAM`, consistent with STATE `discovery.participant_type_confirmed` and A-009.

**Section 3 — N baseline.** **Total market slug count across all 74 events: 74.** One moneyline market per event.

**Section 4 — Distribution.** Perfectly uniform: 74 events × 1 moneyline market each. No multi-moneyline events in the current population.

**Section 5 — Status and probe candidates.** All 40 events shown (of 74 total; `head -40` applied) are `active=True ended=False live=False`. Discovery timestamps range from 2026-04-19T01:47:35Z (earliest surveyed) to 2026-04-19T14:04:52Z (most recent). All observed slugs are for match dates 2026-04-19 through 2026-04-21.

### 13.3 How §13 relates to §5 and §7 in v3

**§5 "actual asset count we expect" — still reads ≈38, not revised in v4.** That figure was explicitly as-of H-009 close. The current figure is 74, and the v3 §5 slam-week projection of 128 is still the applicable upper bound. Neither the sweep shapes in §7 Q3 nor the bracketing logic in §5 needs to be rewritten — they were designed to *exceed* real N with placeholder slugs, and 74 continues to fit under a single subscription (100-slug cap per §4.4).

**§7 Q3 sweep bracketing — unchanged.** The sweep (1, 2, 5, 10 subscriptions per connection × 100 placeholder slugs each) is still the right shape. Real-slug-only sweeps would top out at 74 in one subscription, which does not exercise per-subscription limits. The placeholder strategy from §7 Q3 remains the mechanism for probing the multiplexing and concurrent-connection limits.

### 13.4 Probe-slug default for Q5′=(c′)

The Q5′=(c′) probe (D-025 commitment 1) requires one gateway-sourced slug as its input. Default selection, recorded here for traceability:

- **Event ID:** `9392`
- **Slug:** `aec-atp-digsin-meralk-2026-04-21`
- **Match:** Digvijaypratap Singh vs Mert Alkaya, 2026-04-21 (ATP)
- **Discovery timestamp:** 2026-04-19T14:04:52Z (most recent poll tick; among the freshest meta.json files on disk at survey time)
- **Status at survey:** active=True, ended=False, live=False

**Rationale:** picked from the most-recently-discovered batch (2026-04-19T14:04:52Z discovery timestamp, 4 candidates total in that batch). Most recent discovery is preferred because the event is least likely to have ended between survey time and probe execution. This specific slug was also the Section 2 sample, which means the survey has already verified its `meta.json` is well-formed — one less unknown when the probe code reads it.

**Disclaimer — explicit:** This default is for the **addendum record only**. The actual probe slug at code-turn time must be re-selected by reading `/data/matches/*/meta.json` again at that moment — candidates may have ended, new ones will have been written, and the survey snapshot is ~hours to ~days old by then. The default is a pointer, not a commitment. The code turn selects fresh.

### 13.5 What the code turn inherits from v4

Consolidated for the code turn:

1. **Dependency:** `polymarket-us` SDK (D-024 commitment 1). Added to a new, isolated Render service per D-020 / Q2=(b); not added to `pm-tennis-api`.
2. **Credentials:** `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` via `os.environ` (D-023). SDK authentication flow consumes these.
3. **First runtime action:** Q5′=(c′) probe (D-025 commitment 1). One gateway-sourced slug, SDK subscribe, ~10-second observation window, record outcome.
4. **Main sweeps:** §7 Q3=(c) — both per-subscription count sweep and concurrent-connection count sweep. Shape: 1, 2, 5, 10 subscriptions per connection × 100 placeholder slugs; 1, 2, 4 concurrent connections. ~30 minutes total. Per §7 Q1=(a), pure connection-level test — no disk writes of received tick content.
5. **Slug source for main sweeps:** probe-outcome-dependent (D-025). API-sourced (`markets.list()`) by default; gateway-sourced as an option if bridge is confirmed.
6. **Code-turn research tasks** (from D-023, scoped through SDK per D-024 commitment 4):
   - Byte-level Ed25519 signing: collapses to "SDK owns this" unless a signing surface is exposed to user code.
   - Timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication` to verify the "30 seconds of server time" language aligns with the millisecond unit Polymarket's usage instructions specified (D-023 subsidiary finding 1). The SDK may or may not expose the timestamp it sends; cross-check is against documentation, not SDK behavior.
7. **N baseline for stress-test sweep sanity checks:** 74 market slugs across 74 events at H-012 close (§13.2). Slam-week projection ≈128 from v3 §5.
8. **Probe slug default:** event 9392, `aec-atp-digsin-meralk-2026-04-21` — for addendum traceability only; fresh selection at code-turn time required.

### 13.6 What v4 does not change

- No claim in §4 is revised. The external citations to `docs.polymarket.us` and the Polymarket US Python SDK README stand as v3 recorded them.
- §12's tradeoff table and Claude's recommendation stand — operator ruled (a), so the SDK option is now commitment rather than recommendation, but the analysis v3 presented is unchanged.
- §7 Q1, Q2, Q3, Q4, Q5 are unchanged. Q5′ is resolved in §13.1. §12 is resolved in §13.1.
- §11 findings (1, 2, 3) stand.
- No plan-text revisions are cut by this document; plan-text revisions v4.1-candidate, v4.1-candidate-2, and v4.1-candidate-3 remain queued in STATE `pending_revisions`.

---

## 14. H-016 probe-outcome addendum — the D-025 hybrid-probe-first probe ran

This section is additive to v4. Written at H-016 (2026-04-19) to record the outcome of the D-025 hybrid-probe-first one-slug probe against `wss://api.polymarket.us/v1/ws/markets`. §14 was reserved at H-014 and remained empty at H-015 (probe attempt blocked on the RAID I-016 data-extraction bug in discovery.py; see §14.1). The probe actually ran at H-016 after I-016 was investigated, a fix was authorized and landed (D-028), and the service was redeployed.

§14 is out-of-order in the document (written after §15) by deliberate H-014 convention: the probe outcome is its own unit of analysis, distinct from code-turn research, and the reserved-slot pattern preserves readability of the outcome-vs-implementation separation for future readers. §§1–13, §15 are unchanged by this section.

### 14.1 Why the probe was deferred H-015 → H-016

H-015 attempted the two-shell workflow per RB-002 §5. Step 1 (slug selection in pm-tennis-api Shell via the RB-002 §5.1 pasted snippet) returned an empty `slug_selector.list_candidates()` result. Two operator-authorized diagnostics in the pm-tennis-api Shell surfaced two co-occurring causes: (a) operator-confirmed calendar block — no eligible matches in the next ~24h regardless; and (b) RAID I-016 — 10 most-recent meta.json files all showed `event_date=""` (empty string) despite event titles encoding the date text. Because slug_selector's date filter requires `event_date >= today`, the empty field meant no candidate could ever pass the filter even when calendar-eligible matches existed. H-015 filed I-016 at sev 6 and closed with the probe unrun.

H-016 investigated I-016 by reading a real raw gateway event payload from `/data/matches/9471/meta.json` in the pm-tennis-api Shell (operator-executed, Claude-directed). The payload revealed: `event_date=""`, `start_date_iso="2026-04-21T08:00:00Z"`, `start_time="2026-04-21T08:00:00Z"`, `end_date_iso="2026-04-21T23:59:00Z"`. Root cause: `src/capture/discovery.py` line 328 read `event.get("eventDate")` but the Polymarket gateway response has no top-level `eventDate` key; the canonical date source is `startDate`. Operator authorized Fix C (ruling: "c with thorough documentation"). D-028 was written, `discovery.py` was changed to source `event_date` from `startDate[:10]`, `slug_selector._passes_date_filter` was modified to fall back to `start_date_iso[:10]` when `event_date` is empty (handles ~116 historical meta.json files immutably written H-007 through H-016), and nine new tests were added. The full bundle landed in commits `d7b2bd2` (code + doc + RAID) and `83c0bf8` (DecisionJournal with D-028).

A second-order H-016 finding: the H-014 RB-002 §5.1 pasted-snippet helper had failed twice at H-015 due to bracketed-paste markers in the Render Shell. H-016 flipped the convention to a committed module (`src/stress_test/list_candidates.py`) invocable as a single-line `python -m src.stress_test.list_candidates`. This is the first H-016 commit (part of `d7b2bd2`). The flip eliminates the multi-line-paste failure mode. See §14.5 for the full H-016 work summary.

### 14.2 Probe input

After `pm-tennis-api` redeployed with the H-016 bundle, slug selection was executed in the pm-tennis-api Shell via the new committed helper:

```
render@pm-tennis-api:~/project/src$ python -m src.stress_test.list_candidates
9471  aec-wta-paubad-julgra-2026-04-21  discovered_at=2026-04-19T20:20:51.113080+00:00  event_date=  'Paula Badosa vs. Julia Grabher 2026-04-21'
9470  aec-wta-beamai-jesman-2026-04-21  discovered_at=2026-04-19T20:20:51.113060+00:00  event_date=  'Beatriz Haddad Maia vs. Jessica Bouzas Maneiro 2026-04-21'
9469  aec-wta-tatmar-lausam-2026-04-21  discovered_at=2026-04-19T20:20:51.113037+00:00  event_date=  'Tatjana Maria vs. Laura Samson 2026-04-21'
9467  aec-wta-shuzha-evalys-2026-04-21  discovered_at=2026-04-19T20:20:51.113016+00:00  event_date=  'Shuai Zhang vs. Eva Lys 2026-04-21'
9466  aec-wta-taytow-katbou-2026-04-21  discovered_at=2026-04-19T20:20:51.112995+00:00  event_date=  'Taylor Townsend vs. Katie Boulter 2026-04-21'
```

Notes on this output:
- Five eligible candidates surfaced, all WTA matches on 2026-04-21 (two days from probe time).
- Every `event_date` column is empty — these are all pre-H-016 historical meta.json files; the slug_selector fallback to `start_date_iso[:10]` is what let them pass the date filter.
- Discovery count at H-016 probe time: **126 active tennis events** (up from 116 at H-015 and 74 at H-012; growth consistent with expected ~1-2 events/hour during normal hours).

**Probe slug selected:** `aec-wta-paubad-julgra-2026-04-21` (topmost / freshest discovered_at), event_id `9471`. Paula Badosa vs. Julia Grabher, 2026-04-21. Slug was gateway-sourced via Phase 2 discovery — the intent of D-025's hybrid-probe-first design.

### 14.3 Probe execution and outcome

Probe was executed in the `pm-tennis-stress-test` Render Shell:

```
$ python -m src.stress_test.probe --probe --slug=aec-wta-paubad-julgra-2026-04-21 --event-id=9471
```

Observation window: 10.0 seconds (default per `PROBE_OBSERVATION_SECONDS`).

**Full `ProbeOutcome` JSON (verbatim from stdout):**

```json
{
  "probe_started_at_utc": "2026-04-19T22:20:24.550172+00:00",
  "probe_ended_at_utc": "2026-04-19T22:20:35.824712+00:00",
  "observation_window_seconds": 10.0,
  "elapsed_seconds": 11.275,
  "event_id": "9471",
  "market_slug": "aec-wta-paubad-julgra-2026-04-21",
  "candidate_discovered_at": "",
  "candidate_event_date": "",
  "eligible_candidates_count": 1,
  "subscription_request_id": "probe-h013-1776637224",
  "connected": true,
  "subscribe_sent": true,
  "first_message_latency_seconds": 1.15,
  "message_count_by_event": {
    "market_data": 1
  },
  "first_message_event": "market_data",
  "first_message_preview": "{'requestId': 'probe-h013-1776637224', 'subscriptionType': 'SUBSCRIPTION_TYPE_MARKET_DATA', 'marketData': {'marketSlug': 'aec-wta-paubad-julgra-2026-04-21', 'bids': [{'px': {'value': '0.020', 'currency': 'USD'}, 'qty': '16000.000'}], 'offers': [{'px': {'value': '0.980', 'currency': 'USD'}, 'qty': '16000.000'}], 'state': 'MARKET_STATE_OPEN', 'stats': {'settlementPx': {'value': '0.500', 'currency': 'USD'}, 'settlementSetTime': '2026-04-19T21:00:00.015058283Z', 'notionalSetTime': '2026-04-19T21:00:",
  "error_events": [],
  "close_events": [],
  "classification": "accepted",
  "classification_reason": "subscription produced traffic: market_data=1 market_data_lite=0 trade=0 heartbeat=0",
  "exception_type": "",
  "exception_message": "",
  "sdk_import_ok": true,
  "sdk_version": "0.1.2"
}
```

**Stderr summary:** `=== probe complete: classification=accepted elapsed=11.275s ===` / `reason: subscription produced traffic: market_data=1 market_data_lite=0 trade=0 heartbeat=0`.

### 14.4 Classification, interpretation, and D-025 branch selected

**Classification: `accepted`** per `_classify_outcome` in probe.py. The classification rule: a `market_data`, `market_data_lite`, `trade`, or `heartbeat` message within the observation window → accepted. The probe received one `market_data` message at `first_message_latency_seconds=1.15` (1.15 seconds after subscribe-sent), which satisfies the rule unambiguously. Exit code: 0.

**D-025 branch selected:** per D-025 commitment language,

> If the probe succeeds (subscription accepted, market-data messages received): the gateway-to-api slug bridge is confirmed working; the main sweeps may use either gateway-sourced or api-sourced slugs. The default in that case is api-sourced (cleanest, and the SDK's `markets.list()` provides them).

The probe succeeded on all three checks: subscription accepted (no auth/bad-request/not-found error), market-data message received (one), and the message carried the correct `marketSlug` echo matching the subscribed slug. **The gateway-to-api slug bridge is confirmed working** for at least this slug; main sweeps (H-017 scope) have slug-source flexibility and will default to api-sourced per D-025's language.

**Supporting observations from the probe outcome:**

1. **Subscription request-id echo.** The first-message preview shows `'requestId': 'probe-h013-1776637224'` — the exact request_id the probe sent on subscribe. This is a soft confirmation that the SDK's subscribe/response pairing is working as the README documents (no request-id drift).

2. **`subscriptionType` enum is correct.** First-message preview shows `'subscriptionType': 'SUBSCRIPTION_TYPE_MARKET_DATA'` — matches the enum string the probe sent (cited in probe.py header block [A]). No enum mismatch.

3. **Market state is `MARKET_STATE_OPEN`.** Valid pre-match market. Wide bid/ask spread (0.02 / 0.98) is consistent with a market two days out from match time with minimal trading activity — not a bug, just quiescent. Not relevant to the probe's research question; logged as fair-price-model-relevant observation for Phase 5 design only.

4. **Zero errors, zero close events, no exceptions.** Every error-surface is empty in the outcome JSON. The H-008-risk surface (live network against the Polymarket US API) was finally exercised and came up clean. Every SDK symbol cited in probe.py's [A]-[D] citation block resolved correctly against `polymarket-us==0.1.2` as installed on the stress-test Render service. No fabrication-class bugs in the probe code path.

5. **`candidate_discovered_at` and `candidate_event_date` are empty** in the outcome JSON. Both fields are populated by the probe's pre-fix candidate-lookup path, which under D-027 is not exercised (slug is supplied via `--slug` directly). Per D-027 design, these fields are informational-only and expected to be empty on Render-executed probes; they would populate only if the probe were run from a local-dev environment with a populated `PMTENNIS_DATA_ROOT/matches/` fixture tree. Not a concern.

6. **`eligible_candidates_count: 1`** appears in the outcome JSON but is `1` under D-027's slug-from-CLI path because the self-reported count reflects "the slug was obtained" rather than "selector found candidates." Cosmetic; not a data anomaly.

### 14.5 H-016 work summary for the research record

Consolidated for future readers of this document:

| H-016 deliverable | Status at H-016 close |
|---|---|
| RB-002 §5.1 helper-snippet flip to committed module | Landed as `src/stress_test/list_candidates.py` (20 new tests) in commit `d7b2bd2`. RB-002 §5.1 and `src/stress_test/README.md` updated. |
| RAID I-016 investigation | Completed in pm-tennis-api Shell against event 9471 meta.json. |
| RAID I-016 fix authorization | Operator-authorized Fix C (both discovery.py update AND slug_selector fallback). |
| D-028 (RAID I-016 fix, full text) | Committed in `83c0bf8`. |
| Fix A (discovery.py event_date extraction) | Landed in commit `d7b2bd2`. Phase-2 code touched per D-016 commitment 2 with explicit operator authorization. |
| Fix B (slug_selector.py fallback) | Landed in commit `d7b2bd2`. |
| Test fixture correction (removes false `eventDate` key) | Landed in commit `d7b2bd2`. Adds regression assertion against re-introduction. |
| New regression tests | 3 in TestParseEvent, 6 in test_stress_test_slug_selector. All passing. |
| RAID I-016 marked Resolved | Landed in commit `d7b2bd2`. |
| RAID I-017 added | Two pre-existing TestVerifySportSlug failures (SystemExit vs RuntimeError drift) surfaced during H-016 testing. Out of scope for D-028; H-017 disposition. |
| Subsidiary finding: `_check_duplicate_players` silently broken in production since H-007 | Documented in D-028 and I-016 status cell. Fix automatically restores function going forward; historical 116+ files retain stale `duplicate_player_flag=False` (not retroactively correctable). |
| Live probe execution (D-025 hybrid-probe-first) | Executed this session; classification=accepted. D-025 branch: main sweeps may use either slug source; default is api-sourced. |

### 14.6 What H-017 picks up

Consolidated for the next session:

1. **Main sweeps per §7 Q3=(c).** Shape: 1/2/5/10 subscriptions × 100 placeholder slugs × 1/2/4 concurrent connections. ~30 minutes. Per §7 Q1=(a), no disk writes of received tick content. Per D-021 testing posture: unit tests + operator code review + smoke run constitute the acceptance bar. Code not yet written; this is H-017 code-turn work. Expected new module(s): `src/stress_test/sweeps.py` or equivalent.
   - **Slug source per D-025 branch-selected:** api-sourced via `client.markets.list()` as default, with gateway-sourced as fallback if needed. Per H-014-Claude and H-015-Claude's emphatic notes: re-fetch `github.com/Polymarket/polymarket-us-python` README at code-turn time before using any SDK method beyond the probe's current citation block [A]-[D]; `client.markets.list()` and multi-subscription semantics on `markets_ws` are first net-new SDK surfaces.
2. **Placeholder-slug generation strategy (for >100-slug subscriptions).** §15.5 item 3 called this a code-turn decision informed by probe outcome. Probe outcome now in hand. Decision can be made at H-017 open with probe evidence (the single real slug subscribed cleanly; §4.4's 100-slug-per-subscription cap is documented; placeholder-slug rejection behavior under real-subscription load is the open empirical question).
3. **Main-sweeps addendum (§16 or further-additive).** Written after main sweeps complete.
4. **RAID I-017 disposition.** Two pre-existing TestVerifySportSlug failures. Small fix either side (update tests or update code). Out of scope for H-016; surface at H-017 open.
5. **Cleanup of stale files in repo root.** `CHECKSUMS.txt`, `COMMIT_MANIFEST.md`, and `D-028-entry-to-insert.md` were reference artifacts inadvertently committed at H-016. Can be deleted in an H-017 cleanup commit.
6. **Teardown of the stress-test Render service** after §16 addendum is in hand.

### 14.7 What §14 does not change

- No claim in §§1–13 is revised.
- §15's recording of H-013 code-turn resolutions and D-027 supersession of D-025 commitment 1 stands unchanged.
- No plan-text revisions are cut by this section. Plan-text revisions v4.1-candidate, v4.1-candidate-2, and v4.1-candidate-3 remain queued in STATE `pending_revisions`.
- D-025 commitments 2, 3, 4 remain in force. D-027 supersession of D-025 commitment 1 remains in force. D-028 is the new Phase-2-touching decision landing in this session.

---

## 15. H-013 code-turn results and D-027 — new in H-014 additive

This section is additive to v4. Written at H-014 (2026-04-19) to record: the three H-013 code-turn-research task resolutions, the Render disk-architecture finding that produced D-027, the D-027 supersession of D-025 commitment 1, the probe-scaffolding landing at `src/stress_test/`, and the H-014 correction of the known-stale artifacts committed under H-013's Option X cut. §14 is reserved for the probe-outcome addendum that will be written at H-015 after live probe execution against the Polymarket US gateway; §14 is intentionally out-of-order because the probe outcome is its own unit of analysis and this session (H-014) had no live run.

v4 remains the current version. §§1–14 are unchanged by this section (§14 was reserved when this section was written at H-014; populated at H-016 per §14 itself). A v5 bump was considered at H-014 open and rejected in favor of this §15 additive, following the H-012 precedent for §13.

### 15.1 H-013 code-turn-research resolutions

Three research items were carried forward from D-023/D-024 as not-yet-resolved-but-not-PODs at H-012 close. H-013 resolved all three against authoritative sources before writing code. Each is fully cited below so future sessions have the evidence trail without needing to re-fetch.

**15.1.1 Ed25519 signing surface (D-024 commitment 4a).** Resolved: **fully internal to the `polymarket-us` SDK. No user-code signing surface.** The D-024 commitment-4 escape hatch ("if SDK owns signing, collapses to 'trust the SDK'") is the operative branch.

Evidence:
- **SDK README** (`github.com/Polymarket/polymarket-us-python`, fetched H-013): the SDK accepts `key_id` and `secret_key` (raw base64) at `AsyncPolymarketUS(...)` construction and exposes no signing primitive, no signing-options argument, no signature-callback hook. All three handshake headers (`X-PM-Access-Key`, `X-PM-Timestamp`, `X-PM-Signature`) are produced inside the SDK; the caller never sees the signed bytes.
- **Authentication page** (`docs.polymarket.us/api-reference/authentication`, fetched H-013): documents Ed25519 over `timestamp + "GET" + path` with 30-sec clock window. No user-visible signing surface is documented for SDK-based integrations.
- **Backend library:** `pynacl` (libsodium Python bindings), verified via the SDK's declared deps and via `pip install --dry-run` — see §15.1.3.

Implication: the probe code does not handle any byte-level signing material. The signing-correctness surface is fully inside the SDK. Future-Claude: do not re-open this question unless the SDK's API surface changes.

**15.1.2 Timestamp unit cross-check (D-024 commitment 4b).** Resolved: **milliseconds, unambiguous.** Polymarket's authentication page now contains a header table that reads literally `X-PM-Timestamp: Current time in milliseconds`. The "30 seconds of server time" prose language that v3 §4.2 noted remains on the page as the clock-tolerance description, but is no longer the canonical unit specification — the header table is. Alignment with Polymarket's usage instructions at H-011 (`{unix_ms}`) is now confirmed against the documentation page itself, not just against the usage instructions.

Implication: the SDK sends the timestamp in milliseconds. D-023 subsidiary finding 1 is now fully verified against the authoritative source.

**15.1.3 SDK transitive-dependency footprint (H-012 addendum quiet-uncertainty).** Resolved: **12 packages total, all wheel-available for Linux/x86_64 + CPython 3.12.** No compile required on Render.

Verified H-013 via `pip install polymarket-us==0.1.2 --dry-run --report` in a clean venv:

| Layer | Package | Version constraint |
|---|---|---|
| direct | `httpx` | `>=0.27.0` |
| direct | `pynacl` | `>=1.5.0` |
| direct | `websockets` | `>=12.0` |
| transitive | `httpcore` | (via httpx) |
| transitive | `anyio` | (via httpx/httpcore) |
| transitive | `idna` | (via httpx) |
| transitive | `certifi` | (via httpx) |
| transitive | `h11` | (via httpcore) |
| transitive | `typing_extensions` | (via anyio) |
| transitive | `cffi` | (via pynacl) |
| transitive | `pycparser` | (via cffi) |

Implication: the stress-test service's Render build will install in under a minute and will not require a build toolchain. The H-014 (this session) installation under a local `venv` for test running confirmed the same package set at the same versions; the 38-test suite passes against it.

### 15.2 D-027 supersession of D-025 commitment 1

During H-013 probe-scaffolding work, Claude fetched `render.com/docs/disks` to verify the proposed shared-disk attachment in draft Runbook RB-002 Step 3. The fetch returned authoritative text ruling out the shared-disk architecture:

> A persistent disk is accessible by only a single service instance, and only at runtime. This means: You can't access a service's disk from any other service. You can't scale a service to multiple instances if it has a disk attached. You can't access persistent disks during a service's build command or pre-deploy command (these commands run on separate compute). You can't access a service's disk from a one-off job you run for the service.

This confirms Render disks are strictly single-service. D-025 commitment 1 (probe reads gateway-sourced slug from shared-mounted `/data/matches/` on the stress-test service) is not implementable under the isolated-service architecture required by D-024 commitment 1 and D-020/Q2=(b).

**D-027 (H-013) ruled Option D** after Claude surfaced four options (A: modify pm-tennis-api/requirements.txt — violates D-024 commitment 1; B: expose a candidates-list HTTP endpoint on pm-tennis-api — adds behavior to production discovery service and an auth surface; C: fetch candidates directly from the gateway at probe time — conflicts with D-025's language literally and adds a net-new external dependency to the probe critical path; D: operator picks a slug via pm-tennis-api Shell and passes it to the probe as `--slug=SLUG` — preserves all isolation commitments).

Under D-027, the probe slug is supplied as `--slug=SLUG` on the `pm-tennis-stress-test` Render Shell invocation. `slug_selector.py` remains in the package as a library used by (a) local development, (b) self-check's informational report, (c) a pm-tennis-api Shell helper command (documented in RB-002 §5.1) that lists eligible candidates for operator selection. `slug_selector` is **not** called in the production probe code path on the isolated stress-test service.

D-025's research-question intent is preserved: the probe still tests a gateway-sourced slug against `wss://api.polymarket.us/v1/ws/markets`. The operator selects that slug from Phase 2's byte-identical `meta.json` archive in pm-tennis-api's Shell; it is the same slug D-025 contemplated, sourced by the same mechanism, just reaching the probe via CLI rather than shared-disk filesystem read. The probe outcome (accepted/rejected/ambiguous/exception) answers the same gateway-to-api-slug-bridge question D-025 set out to answer.

**D-025 commitments 2, 3, and 4 are unaffected.** D-027 operator ruling chose supersession over re-interpretation at explicit Claude request — supersession keeps D-025's original text intact in the historical record and forces the new reality into a named, dated, numbered DJ entry. D-025's footer has been updated with `SUPERSEDED IN PART BY D-027`.

### 15.3 Probe scaffolding landed (H-013)

The `src/stress_test/` package was created and committed at H-013 per D-024 commitment 1 and the H-013 cut. Structure:

| File | Purpose |
|---|---|
| `src/stress_test/__init__.py` | Package init; version string `0.1.0-stress-test-h013`. |
| `src/stress_test/probe.py` | Entry point with self-check (default) and probe (`--probe --slug=SLUG`) modes. Every SDK symbol cited against the Polymarket US Python SDK README in the module-header citations block ([A] through [D]). |
| `src/stress_test/slug_selector.py` | Library for reading `/data/matches/*/meta.json` under local/helper invocation. Schema verified against `src/capture/discovery.py` `TennisEventMeta` dataclass. Under D-027 not called in the production probe path. |
| `src/stress_test/requirements.txt` | Isolated deps: `polymarket-us==0.1.2`, `pytest==8.3.4`. Per D-024 commitment 1, `/requirements.txt` at the repo root (used by `pm-tennis-api`) is NOT modified. |
| `src/stress_test/README.md` | Package documentation. Rewritten at H-014 to reflect D-027 (§15.4). |
| `tests/test_stress_test_slug_selector.py` | 19 tests covering positive/negative/filter-by-status/filter-by-date/malformed-JSON/empty/multi-market/realistic-survey-shape paths. Pure on-disk fixtures; no mocking. |
| `tests/test_stress_test_probe_cli.py` | 19 tests covering argparse, config-error path, NO_CANDIDATE path, config-checked-before-slug precedence, main() dispatch, ProbeOutcome dataclass, classification-to-exit-code mapping, ProbeConfig clamping. Zero SDK mocking per the H-012 addendum guidance that SDK-mocking would hide the drift class that killed H-008. |

**38 tests pass** (H-013 close and re-verified at H-014 open under a fresh `venv` with the pinned deps). The network-touching probe path is deferred to H-015 live smoke per the D-021 testing posture + live-smoke bar of D-020.

End-to-end smoke of the four CLI exit paths was verified at H-013 close and re-verified at H-014 open:
- Self-check (no creds, no disk) → `EXIT_OK` with clean stderr output.
- `--probe --slug=dummy` (no creds) → `EXIT_CONFIG_ERROR`.
- `--probe` (no `--slug`, empty `PMTENNIS_DATA_ROOT`) → `EXIT_NO_CANDIDATE`.
- `--help` → renders the argparse help text correctly.

### 15.4 Known-stale artifacts corrected at H-014

Two files committed at H-013 carried sections known-stale under D-027 (flagged in Handoff_H-013 §5 for H-014 first-task correction). Both were rewritten this session before any deployment step:

- **`src/stress_test/README.md`**: `## What this service does` (revised to clarify self-check is informational on slug_selector under D-027; probe mode takes `--slug`); new `## Slug source — D-027 supersedes D-025 commitment 1` section added; `## Authoritative inheritance` slug-schema bullet scoped to "library use only"; `## Running locally` code block updated with `--slug` example and fallback invocation; `## Running on Render` rewritten to describe the two-shell workflow and reference RB-002; exit-code-11 row revised to reflect D-027 meaning ("no `--slug` provided AND fallback returned []"); status line updated to note the H-014 D-027 pass.

- **`runbooks/Runbook_RB-002_Stress_Test_Service.md`**: full rewrite. Step 1 language about region being "load-bearing" for disk-sharing removed (now a latency/cost consideration only). Step 3 ("Attach the persistent disk read-only") replaced with "Skip — no disk attach" and explanatory rationale. The three fallback options (A/B/C) that Step 3 proposed are now inert (D-027 already picked Option D) and removed. Step 4 expected-log-output block revised to show `[info] 0 probe candidates from slug_selector — expected under D-027` as the success signal, not a warn state. Step 5 entirely rewritten as the two-shell workflow: 5.1 in pm-tennis-api Shell (operator runs a short Python snippet importing `slug_selector.list_candidates`, picks a slug); 5.2 in pm-tennis-stress-test Shell (operator runs `python -m src.stress_test.probe --probe --slug=<SLUG> --event-id=<EID>`); 5.3 exit-code interpretation table. Step 6 "Disk-attach outcome" reporting line removed. Teardown section preserved.

One sub-ruling applied under delegated authority at H-014: for the pm-tennis-api-Shell candidate-listing helper, the pasted one-line Python snippet (inlined in RB-002 §5.1) was chosen over a committed `src/stress_test/list_candidates.py` helper file. Rationale: a pasted snippet avoids a new file that would itself require tests, documentation, and maintenance; the Shell-pasted form is transparent and self-documenting. Surfaced in Handoff_H-014 §3 for visibility. If operator prefers a committed helper file at H-015 open, adding one is a cheap reversal.

### 15.5 What H-015 picks up

Consolidated for the next session:

1. **Live probe execution** per §7 Q5′=(c′), D-025 commitments 2–4, and D-027 Option D.
   - In pm-tennis-api Shell: list candidates via RB-002 §5.1 snippet; pick one freshest active not-ended not-live not-live slug.
   - In pm-tennis-stress-test Shell: `python -m src.stress_test.probe --probe --slug=<SLUG> --event-id=<EID>`.
   - Copy the `ProbeOutcome` JSON from stdout back to chat.
   - Claude logs outcome, classifies probe result, and decides (or surfaces to operator) the main-sweep slug source per D-025 hybrid-probe-first logic.
2. **Main sweeps** per §7 Q3=(c). Shape: 1/2/5/10 subscriptions × 100 placeholder slugs × 1/2/4 concurrent connections. ~30 minutes. Per §7 Q1=(a), no disk writes of received tick content. Per D-021 testing posture: unit tests + operator code review + smoke run constitute the acceptance bar. Code not yet written — this is H-015 code-turn work. Expected new module: `src/stress_test/sweeps.py` or equivalent.
3. **Probe-outcome addendum (§14).** Written after live probe result is in hand.
4. **Main-sweeps addendum** (§16 or further-additive). Written after main sweeps complete.
5. **Teardown** of the stress-test Render service after the §16 addendum is in hand.

### 15.6 What §15 does not change

- No claim in §§1–12 is revised. All external citations to `docs.polymarket.us` and the Polymarket US Python SDK README stand as v3 recorded them; §15.1.1 and §15.1.2 are confirmations of v3 claims via re-fetch, not revisions of them.
- §13's H-012 rulings and survey findings stand. D-027 is supersession of **D-025 commitment 1 only**; D-025's commitments 2/3/4 and the probe-slug default at §13.4 remain in force.
- §13.5's "what the code turn inherits" list is still accurate for the probe's runtime behavior; the slug-source item (point 3) now reads as "operator-supplied via `--slug=SLUG`" under D-027, but the probe-behavior specification (one slug, SDK subscribe, ~10s observation, record outcome, disconnect) is unchanged.
- No plan-text revisions are cut. Plan-text revisions v4.1-candidate, v4.1-candidate-2, and v4.1-candidate-3 remain queued in STATE `pending_revisions`.

---

## 16. H-019 main-sweeps-scope addendum — §7 Q3=(c) harness design, cited against the re-fetched SDK

This section is additive to v4. Written at H-019 (2026-04-20) to scope the main stress-test sweeps per §7 Q3=(c), following the research-first-then-code sequencing committed in D-019. The code turn implementing this scope is expected at H-020 or later, not this session. §§1–15 are unchanged by this section.

§16 is the research artifact for the main sweeps. It cites its external sources against authoritative material re-fetched this session, inherits the rulings committed in D-018 through D-031, names the empirical questions the sweeps code is designed to answer, and specifies the harness shape and acceptance bar. Every commitment §16 makes to main-sweeps design is traceable either to a cited authoritative source or to a named measurement question the sweeps code will resolve empirically.

### 16.1 Fetch record

Sources re-fetched at H-019 session start. Every §16 claim about SDK surface or documented Polymarket US behavior traces to one of these fetches.

| Source | URL | Fetched at H-019 | Repo/page state at fetch |
|---|---|---|---|
| [E] | `github.com/Polymarket/polymarket-us-python` (README.md on `main` branch) | 2026-04-20 | 10 commits, 5 stars, 0 forks. **Unchanged commit count from H-013's "10 commits" (research-doc §12, §15.1).** MIT license. PyPI link: `pypi.org/project/polymarket-us/`. |
| [F] | `docs.polymarket.us/api-reference/websocket/markets` (Markets WebSocket documentation page) | 2026-04-20 | Page content current. Subscription Limits section present. |
| [G] | `libraries.io/pypi/polymarket-us` (PyPI version metadata) | 2026-04-20 | Latest release: `0.1.2` (2026-01-22). First release: `0.1.1` (2026-01-22, same day). **Two releases total; 0.1.2 is still current.** `pip install polymarket-us==0.1.2` remains the pinned target per D-024 commitment 1 and H-013's stability ruling. |

**Baseline — this is what the re-fetch established against prior research:**

1. The SDK has not moved. `polymarket-us==0.1.2` is still the latest release on PyPI; the GitHub repo's commit count is unchanged from H-013. D-024 commitment 1's pin is current-against-upstream as of H-019.
2. Every SDK symbol cited in probe.py's [A]–[D] block (H-013) still resolves correctly against [E]. `AsyncPolymarketUS` constructor shape, `client.ws.markets()` factory, `markets_ws.connect()`/`subscribe(request_id, subscription_type, market_slugs_list)`/`close()` methods, the `on(event_name, fn)` handler pattern, the six documented exception types (`AuthenticationError`, `APIConnectionError`, `APITimeoutError`, `BadRequestError`, `NotFoundError`, `RateLimitError`), and the `SUBSCRIPTION_TYPE_MARKET_DATA` enum-string — all unchanged.
3. Ed25519 signing remains fully internal to the SDK per [E]'s Authentication section (*"The SDK automatically signs requests with your credentials"*). §15.1.1's H-013 finding is re-confirmed. No user-code signing surface is exposed.
4. Python 3.10+ requirement is explicit in [E]. `polymarket-us==0.1.2` depends on `httpx>=0.27.0`, `pynacl>=1.5.0`, `websockets>=12.0` per §15.1.3's verified dep tree (12 packages total, all wheel-available for Linux/x86_64 + CPython 3.12, no compile required).
5. No contradictions with the research record surfaced during the re-fetch. §16 drafts cleanly against [E], [F], and prior research.

This baseline is the load-bearing context for every commitment §16 makes below. If H-020-Claude (or later) reads §16 and finds the re-fetch baseline contradicted by newer SDK state at code-turn time, that is a research-first event (per D-019, R-010) and warrants re-opening the relevant §16 commitments before writing code against them.

### 16.2 What §16 inherits from prior rulings

Consolidated for the sweeps code turn. Every item below is a prior ruling in force at H-019 session close; §16 does not re-litigate any of them.

1. **Scope: deferred CLOB asset-cap stress test.** Per D-018, the first deliverable of Phase 3 attempt 2 is the stress test from RAID I-002. The main sweeps are the test itself.
2. **Form: research-doc first, operator review, code follows in a subsequent turn.** Per D-019. §16 is the research-doc artifact; H-020 code implements against operator-reviewed §16.
3. **Definition of done: unit tests + operator code review + stress test runs to completion against actual gateway with actual asset count.** Per D-020 and D-021. §16 names the acceptance bar in §16.8.
4. **Testing posture: zero SDK mocking.** Per H-012 addendum, reinforced by H-013's 38-test probe suite. Sweeps unit tests exercise the non-network paths (config loading, grid generation, classification, outcome serialization) without stubbing SDK surfaces.
5. **Commit cadence: periodic commits within a deliverable permitted; handoff required at session end.** Per D-022.
6. **Isolation: separate Render service, torn down after.** Per D-020 / §7 Q2=(b). Sweeps run on `pm-tennis-stress-test`; `pm-tennis-api/requirements.txt` is not modified (D-024 commitment 1).
7. **Authentication: SDK-internal Ed25519.** Per D-023 / D-024 commitment 4a / §15.1.1. Credential env vars on `pm-tennis-stress-test`: `POLYMARKET_US_API_KEY_ID`, `POLYMARKET_US_API_SECRET_KEY`.
8. **Slug source for sweeps: api-sourced via `client.markets.list()` as default; gateway-sourced optional.** Per D-025 resolved branch after H-016 probe outcome (§14.4). The gateway-to-api slug bridge is confirmed working for at least one slug (sample of one — see §16.5); main sweeps default to api-sourced because it does not depend on the shared-disk architecture Render does not support (D-027 / §15.2).
9. **No disk writes of received tick content.** Per §7 Q1=(a). The sweeps are connection-level measurements, not archive-write tests.
10. **Sweep grid shape: 1/2/5/10 subscriptions per connection × 1/2/4 concurrent connections.** Per §7 Q3=(c). Slug count per subscription is 100 placeholder slugs, targeting the documented cap [F].
11. **No Phase 2 code touch.** Per D-016 commitment 2; the sweeps do not read `/data/matches/` or modify `discovery.py` / `main.py`.
12. **Deployment: Claude pushes to `claude-staging`, operator merges to `main`.** Per D-029, operating under the D-030 interim drag-and-drop flow until the authentication mechanism is resolved. The code turn's session-close bundle follows this discipline; §16 itself follows it at this session's close.

### 16.3 The 100-slug-per-subscription cap — re-cited for §16's sweep grid

Directly quoted from [F] (`docs.polymarket.us/api-reference/websocket/markets`, Subscription Limits section):

> Subscription Limits: You can subscribe to a maximum of 100 markets per subscription. Use multiple subscriptions if you need more.

This citation anchors §16's choice of **100 placeholder slugs per subscription** in the sweep grid. The cap is a documented hard limit; sweeps at N=100 slugs per subscription hit the cap exactly and serve as the positive control. Sweeps that exceed the cap are out of scope for §7 Q3=(c) — the cap is documented, not the research question.

The "Use multiple subscriptions if you need more" phrase in [F] is the prescribed pattern for >100-slug needs. That pattern is what §7 Q3=(c)'s "1/2/5/10 subscriptions per connection" sweep is measuring the feasibility of at scale. It is supporting evidence for Measurement Question M1 (§16.4) — the documentation describes the pattern; the harness measures it.

### 16.4 Measurement questions

The sweeps are designed to answer a small set of explicit empirical questions. Each is named with an identifier so the sweeps code can be read against them directly. These are not prose observations — they are the experimental questions the harness is built to answer.

**M1 — multi-same-type subscription composition on one `markets_ws`.**

*Question:* Do multiple `await markets_ws.subscribe(request_id, "SUBSCRIPTION_TYPE_MARKET_DATA", slug_list)` calls on one `markets_ws` object, each with a distinct `request_id` and a distinct (or overlapping) slug list, compose into N concurrent `SUBSCRIPTION_TYPE_MARKET_DATA` subscriptions — or does each call replace the prior, or produce some other behavior?

*Why this is empirical and not pinned:*
- [E] (the SDK README) demonstrates multi-subscription composition on one `markets_ws` via two `subscribe()` calls with **different subscription types**: one `SUBSCRIPTION_TYPE_MARKET_DATA` and one `SUBSCRIPTION_TYPE_TRADE`. It demonstrates three-subscription composition on `private_ws` (a different WS factory) with three different subscription types. It does **not** directly demonstrate the multi-`MARKET_DATA`-with-distinct-slug-lists pattern specifically.
- [F] states the prescribed pattern for >100 slugs is "Use multiple subscriptions." That is consistent with M1 resolving as "compose" but does not prove it at the wire level for same-type calls.
- §14.3 (H-016 probe outcome) is a sample of one — one `subscribe()` call, one `market_data` message back with correct `marketSlug` echo. Supporting evidence for subscription-addressability-by-`requestId`, not proof of multi-subscription composition.

*How the harness measures it:* Each sweeps cell that specifies ≥2 subscriptions per connection issues N distinct `subscribe()` calls on the same `markets_ws` object, each with a distinct `request_id` (e.g., `sweep-h020-{timestamp}-sub-{n}`) and a distinct 100-slug placeholder list. The harness records per-`requestId` message counts over the observation window. M1 resolves as:
- **Compose** if each `requestId` receives its own distinct traffic during the observation window (i.e., sum of per-`requestId` message counts equals total, with attribution reliable).
- **Replace** if only the most recent `requestId` receives traffic.
- **Error** if the second `subscribe()` call raises `BadRequestError` or similar.
- **Ambiguous** if some other behavior (partial attribution, cross-subscription noise) is observed.

M1 is the single most load-bearing question for §7 Q3=(c)'s "subscriptions per connection" sweep. Its resolution determines whether the sweep's axis-label "N subscriptions per connection" means what §7 Q3 presumes it means.

**M2 — multi-connection composition on one client.**

*Question:* Do multiple `client.ws.markets()` calls on one `AsyncPolymarketUS` client produce N independent markets WebSocket connections — or does the second call return the same `markets_ws` object as the first, or produce some other behavior?

*Why this is empirical and not pinned:*
- [E] demonstrates one-client-can-host-multiple-WS-connections with **different WS factories**: one `client.ws.private()` AND one `client.ws.markets()` on the same client, running concurrently. It does **not** directly demonstrate two `client.ws.markets()` calls on one client.
- Prior research (§4.5, §15.2) records concurrent-connection limits as undocumented on `docs.polymarket.us`. That concerns Polymarket-side caps; M2 concerns the SDK-side question of whether the factory can produce multiple independent instances.

*How the harness measures it:* Each sweeps cell that specifies ≥2 concurrent connections instantiates N `markets_ws` objects via N calls to `client.ws.markets()`. The harness connects, subscribes, and observes on each. M2 resolves as:
- **Independent** if each `markets_ws` connects cleanly and receives traffic independently.
- **Shared** if the second `client.ws.markets()` call returns the first's object (same identity) and the two subscribe paths collide on one connection.
- **Error** if the second `connect()` call raises an exception the SDK documents (likely `APIConnectionError` family) or raises an undocumented exception type.
- **Ambiguous** if some other behavior is observed.

If M2 resolves as "shared" or "error," the concurrent-connections axis of §7 Q3=(c) is not testable via a single `AsyncPolymarketUS` client, and the harness design needs a secondary strategy (multiple clients, one per connection). §16 commits to the single-client design as default because it matches [E]'s demonstrated pattern for cross-factory concurrency; if M2 resolves against it, a targeted DJ entry at code-turn time specifies the secondary strategy before writing it.

**M3 — per-subscription cap behavior at 100 slugs.**

*Question:* Does a `subscribe()` call with exactly 100 placeholder slugs succeed cleanly, and does a call with 101 slugs raise the documented failure? If it succeeds, what is the first-message latency and the subsequent message rate for 100-slug subscriptions under the observation window?

*Why this is partially pinned:*
- [F] documents the 100-slug cap as a hard limit. §16.3 re-cites.
- [E] does not demonstrate 100-slug subscriptions; the example shows single-slug subscriptions.
- §14.3 (H-016 probe) demonstrated single-slug subscription latency of 1.15 seconds to first `market_data` message. Behavior at 100-slug load is not pinned.

*How the harness measures it:* Every sweeps cell uses 100 placeholder slugs per subscription as the default (the documented cap). A single 101-slug cell is included as the negative control. The harness records first-message latency, per-slug message attribution (via the `marketSlug` echo in `market_data` payloads — observed in §14.3), and total message volume across the observation window.

**M4 — placeholder-slug rejection behavior.**

*Question:* When the harness subscribes to placeholder slugs that do not correspond to real markets on Polymarket US (the bulk of the 100-slug sweep, since only a handful of real tennis slugs exist at any given time), does the subscription:
- (a) succeed at the subscribe level but produce no `market_data` messages for the placeholder slugs (silent filter)?
- (b) raise `BadRequestError` or `NotFoundError` on the entire subscription (hard rejection)?
- (c) partially accept — real slugs produce traffic, placeholder slugs silently don't, and the subscription stays alive?
- (d) some other behavior?

*Why this is empirical:*
- [E]'s Error Handling section documents `BadRequestError` and `NotFoundError` as generic failure surfaces. It does not pin whether they fire on per-slug-not-found or whole-subscription-rejected semantics.
- [F] does not discuss placeholder-slug behavior.
- §14.3 subscribed to one real slug and got one `market_data` back. Placeholder-slug behavior is not pinned.

*How the harness measures it:* Each sweeps subscription's slug list is 1 real slug (from `markets.list()`, to anchor the subscription) + 99 placeholder slugs (synthetically constructed — see §16.5). The harness observes which slugs produce traffic via the `marketSlug` echo and records whether the subscribe call raised or succeeded.

**M5 — connection-level concurrent-connection cap.**

*Question:* At what N does the 1/2/4-connections axis stop working cleanly? Specifically: does 4 concurrent connections from one client succeed (M2 resolves independent) and stay alive through the observation window, or does the Nth connection get rejected, rate-limited, or silently broken?

*Why this is empirical:*
- Per prior research (§4.5, §15.2), Polymarket US concurrent-connection caps are undocumented. The sweeps exist to characterize them.
- [E] and [F] do not mention concurrent-connection limits.

*How the harness measures it:* The connection-count sweep (1, 2, 4) runs each cell and records for each connection: connect success/failure, subscribe success/failure, first-message latency, observation-window message count, explicit error events, close events. Any non-success across the 4-connection cell answers M5 at an upper bound; success across all three cells answers M5 as "≥4 concurrent OK."

### 16.5 Harness design

The sweeps harness is the main-sweeps analogue of probe.py's design. Its structure mirrors probe.py's but generalizes to a grid.

**Module identity.** `src/stress_test/sweeps.py`, entry point `python -m src.stress_test.sweeps`. Unit tests at `tests/test_stress_test_sweeps.py`. Same package, same Render service (`pm-tennis-stress-test`), same credentials, same SDK pin.

**CLI surface (preliminary; final details resolve at code-turn time):**
- `--sweep=subscriptions` — run the per-connection subscription-count sweep (axis: 1, 2, 5, 10 subscriptions × 100 slugs each, one connection).
- `--sweep=connections` — run the concurrent-connection-count sweep (axis: 1, 2, 4 connections × 1 subscription × 100 slugs each).
- `--sweep=both` — both sweeps in sequence. Approximate total runtime ~30 minutes per §7 Q3=(c).
- `--observation-seconds=N` — per-cell observation window (default inherited from probe's `DEFAULT_OBSERVATION_SECONDS = 10.0`, but likely longer for sweeps; code-turn decides).
- `--slug-source=api` (default; uses `client.markets.list()`) or `--slug-source=gateway` (operator-supplied seed slug via `--seed-slug=SLUG`, similar to probe's `--slug` under D-027, optional under D-025 resolved branch).

**Slug composition per cell (default).** Each subscription in a default sweep cell uses 100 slugs:
- 1 **real anchor slug** fetched via `client.markets.list()` (or operator-supplied via `--seed-slug` if `--slug-source=gateway`). This ensures every subscription has at least one slug that can produce traffic, giving M1 attribution evidence continuously across the grid — even if placeholder-rejection behavior (M4) fails in a way that drops placeholder traffic entirely, the anchor guarantees the cell still produces meaningful data.
- 99 **placeholder slugs** synthesized to match the observed Polymarket US slug format (`aec-<tour>-<abbrev_a>-<abbrev_b>-<YYYY-MM-DD>` per §13.2's observed format). The placeholders are guaranteed not to correspond to real markets (e.g., YYYY-MM-DD set far in the past or with syntactically distinct but format-matching content). Synthesis is deterministic per-cell so results are reproducible across sweep runs.

Placeholder synthesis is a point where §16 commits to a concrete strategy but the code turn may refine it based on what [E]/[F] do or do not say about invalid-slug formatting at code-turn re-fetch time.

**Dedicated M4 control cell (100P/0R).** In addition to the default 1+99 composition across the main grid, the sweep runs **one dedicated control cell** with a pure-placeholder composition: 100 placeholder slugs, 0 real anchor. This cell is a single-subscription, single-connection cell (the simplest shape) and runs alongside the main grid.

The purpose is to give M4 a clean, unconfounded measurement. In the default 1+99 cells, the presence of the 1 real anchor means any observed traffic on the subscription could come from the anchor regardless of placeholder behavior; M4 is still measurable via per-slug attribution, but placeholder rejection is inferred from the absence of placeholder-keyed messages rather than observed directly. The 100P/0R control cell measures placeholder behavior against a baseline of "zero real slugs to confound the signal" — it resolves M4 directly:
- **Silent filter (M4 option a):** Subscribe succeeds, no messages produced over the observation window.
- **Hard rejection (M4 option b):** Subscribe raises `BadRequestError` or `NotFoundError`.
- **Unexpected traffic (other):** Subscribe succeeds and produces messages keyed to slugs the harness did not believe were real. Surface literally; flag for investigation.

The 100P/0R cell is cheap — one additional cell adds ~30–60 seconds to the ~30-minute sweep. Its inclusion disambiguates M4 without requiring a separate invocation or a different CLI surface. It is enumerated in the grid alongside the default cells and receives the same `SweepCellOutcome` treatment, flagged in `cell_id` (e.g., `m4-control-100p-0r`) and in `SubscribeObservation.real_slug` (set to an empty string to signal the pure-placeholder composition).

**Per-cell execution:**
1. For a connections-axis cell of N connections: spawn N `client.ws.markets()` instances (or N `AsyncPolymarketUS` clients if M2 resolves shared, decided at code-turn). For a subscriptions-axis cell of N subscriptions: one `markets_ws`, N subscribe calls.
2. Register handlers: `market_data`, `market_data_lite`, `trade`, `heartbeat`, `error`, `close` — same pattern as probe.py lines 445–450.
3. Connect; record `connected: true/false` per connection.
4. Subscribe; record `subscribe_sent: true/false` per subscription.
5. Observe for the configured window. Record per-`requestId` message counts (for M1), per-`marketSlug` attribution (for M4), first-message latency per connection (for M5), explicit error events, explicit close events.
6. Close each connection; record close outcome.
7. Emit one `SweepCellOutcome` record (JSON) per cell.

**Event attribution.** Per-`requestId` message attribution is the load-bearing observation mechanism. §14.3 demonstrated that the first `market_data` message preview included both `'requestId': 'probe-h013-1776637224'` and `'marketSlug': 'aec-wta-paubad-julgra-2026-04-21'`. Main sweeps presume both fields are reliably present in `market_data` payloads; if they aren't at code-turn time, the harness falls back to aggregate counts per connection and M1 resolves as "ambiguous — could not attribute per-subscription."

**No debouncing.** [F] documents a `responsesDebounced: true` subscribe parameter that batches updates at regular intervals. Main sweeps explicitly set `responsesDebounced: false` (or omit the parameter, whichever the SDK treats as undebounced) to get maximum per-subscription message volume for load characterization. Debouncing is out of scope for §7 Q3=(c); §16 names it here so H-020-Claude does not reach for it.

**No disk writes of received tick content.** Per §7 Q1=(a). The sweeps harness keeps per-cell state in memory; only the final aggregate outcome JSON is emitted (to stdout per cell; aggregated to a final summary). This is unchanged from probe.py's posture.

### 16.6 `SweepCellOutcome` and `SweepRunOutcome` record shapes

The outcome records are the main-sweeps analogue of probe.py's `ProbeOutcome` (probe.py lines 135–183). §16 commits to the shape below; field names and types are final; final code-turn details on optional vs required fields resolve at code-turn time.

**`SweepCellOutcome`** (one per grid cell):

```
- sweep_id: str                            # identifies the parent run
- cell_id: str                             # e.g., "subscriptions-axis-n5"
- cell_axis: str                           # "subscriptions" | "connections"
- cell_axis_value: int                     # N for the axis
- slugs_per_subscription: int              # always 100 in committed grid
- cell_started_at_utc: str
- cell_ended_at_utc: str
- observation_window_seconds: float
- elapsed_seconds: float

# per-connection records (list length = cell_axis_value for connections-axis,
#                         1 for subscriptions-axis)
- connections: list[ConnectionObservation]

# classification
- cell_classification: str                 # "clean" | "degraded" | "rejected" | "exception" | "ambiguous"
- cell_classification_reason: str

# measurement-question resolution flags for this cell
- m1_resolution: Optional[str]             # "compose" | "replace" | "error" | "ambiguous" | null (not tested in this cell)
- m2_resolution: Optional[str]             # "independent" | "shared" | "error" | "ambiguous" | null
- m3_observations: dict                    # first-message latency, per-slug message counts
- m4_observations: dict                    # per-slug attribution for placeholder vs real
- m5_observations: dict                    # per-connection connect/subscribe/message outcomes

- exception_type: str
- exception_message: str
```

**`ConnectionObservation`** (one per connection within a cell):

```
- connection_index: int
- connected: bool
- subscribe_calls: list[SubscribeObservation]
- error_events: list[str]
- close_events: list[str]
- closed_cleanly: bool
```

**`SubscribeObservation`** (one per `subscribe()` call within a connection):

```
- request_id: str
- subscribe_sent: bool
- slugs: list[str]                         # the 100 slugs for this subscription
- real_slug: str                           # the 1 real anchor from markets.list()
- placeholder_slugs_count: int             # 99 (if real anchor present)
- message_count_by_event: dict[str, int]   # {"market_data": N, "heartbeat": M, ...}
- per_slug_message_counts: dict[str, int]  # attribution via marketSlug echo
- first_message_latency_seconds: Optional[float]
- first_message_event: Optional[str]
- first_message_preview: Optional[str]     # truncated repr, like probe.py
```

**`SweepRunOutcome`** (one per full sweep invocation; emitted to stdout at run end):

```
- run_id: str                              # sweep_id
- sweep_started_at_utc: str
- sweep_ended_at_utc: str
- cells: list[SweepCellOutcome]
- m1_aggregate_resolution: str             # synthesized across all cells that tested M1
- m2_aggregate_resolution: str             # synthesized across all cells that tested M2
- m3_aggregate_summary: dict               # per-N latency medians, etc.
- m4_aggregate_summary: dict               # placeholder-rejection behavior across cells
- m5_upper_bound: int                      # highest connection count observed to succeed cleanly
- run_classification: str                  # "clean" | "partial" | "failed" | "ambiguous"
- sdk_version: str
- run_notes: str                           # free text for anomalies
```

The outcome shape is verbose by design. Main sweeps produce data that §17 (or the next additive section) will interpret; interpretation depends on having every per-cell observation in structured form. Probe.py's `ProbeOutcome` at 500-char preview truncation is a good precedent; sweeps apply the same truncation policy for individual payload previews.

### 16.7 Cell classification state machine

Per-cell classification generalizes probe.py's four-way classifier (`accepted` / `rejected` / `ambiguous` / `exception`, probe.py `_classify_outcome` logic lines 536–582). For sweeps cells, a fifth classification is added because the sweep's success mode is more nuanced than the probe's.

**Subscribe-success threshold — the primary partition between `clean` / `degraded` / `rejected`.**

Sweeps cells have an intended subscribe count per cell: for subscriptions-axis cells, it is `cell_axis_value` (e.g., 5 subscribes at N=5); for connections-axis cells, it is the cell's connection count × 1 subscribe per connection (e.g., 4 at N=4 connections). The observed subscribe count is the number of those intended subscribes that returned successfully (the SDK did not raise, `subscribe_sent == True`). The ratio of observed to intended is the classification threshold:

- **All intended subscribes succeeded** (observed == intended): candidate for `clean` (final classification depends on the other `clean` conditions below).
- **More than half but not all succeeded** (observed > intended/2, observed < intended): `degraded`.
- **Half or fewer succeeded** (observed ≤ intended/2): `rejected`.

The "more than half" cutoff is the threshold; cells on either side of it get different classifications. The threshold is pinned at cell-authoring time, not delegated to H-020-Claude's judgment. If code-turn experience suggests a different threshold (e.g., "any failed subscribe is `rejected`" as a stricter bar, or a ratio tuned to sweep size), that is a follow-up ruling with its own DJ entry — but §16 commits to the half-threshold as the initial bar so the sweeps produce classification data against a named standard from the first run.

For single-subscribe cells (N=1 subscription): the threshold degenerates — observed is 0 or 1. 0 → `rejected`; 1 → candidate for `clean`. No `degraded` possible at N=1, by construction. This matches probe.py's single-subscribe classifier behavior.

For the M4 control cell (100P/0R, single subscribe): same as N=1 logic. The cell's classification reflects subscribe success/failure, not placeholder-traffic behavior; M4's resolution is recorded in `m4_observations`, not in the cell's classification.

| Classification | Meaning | Rule |
|---|---|---|
| `clean` | Every connection connected; every intended subscribe succeeded (observed == intended); message traffic received on the anchor slug(s) within the observation window; no error/close events during observation. | All of: `connections[*].connected == True`; subscribe ratio `observed == intended`; for default cells, at least one `market_data` or `trade` or `heartbeat` received across the cell; `connections[*].error_events == []`; `connections[*].close_events == []`. For the M4 control cell: relaxed — no anchor-slug traffic is expected; `clean` requires the subscribe succeeded and no error events fired, regardless of message count. |
| `degraded` | Subscribe ratio is above the half-threshold but below 1.0 (more than half of intended subscribes succeeded, but not all) — OR all subscribes succeeded but the cell has one or more of: `error_events` non-empty during observation, `close_events` non-empty mid-window, anchor slug produced zero traffic across the observation window. The cell produced meaningful data but with identifiable anomalies. | Subscribe ratio in (0.5, 1.0) exclusive, OR (ratio == 1.0 AND one of the anomaly conditions fires). |
| `rejected` | Subscribe ratio is at or below the half-threshold (half or fewer of intended subscribes succeeded) — OR the SDK raised a documented exception (`AuthenticationError`, `BadRequestError`, `NotFoundError`, `RateLimitError`) on the cell's critical path. | Subscribe ratio ≤ 0.5, OR documented exception caught per probe.py's pattern (probe.py lines 476–510). |
| `exception` | Transport-layer error or undocumented SDK exception type on the cell's critical path. | `APITimeoutError`, `APIConnectionError`, `asyncio.TimeoutError`, or catch-all (`Exception` matched with undocumented type name). Takes precedence over subscribe-ratio classification — if an exception was raised, the cell is `exception` regardless of how many subscribes succeeded before the exception. |
| `ambiguous` | Connected but observation window elapsed with no traffic and no explicit error on a default cell — or M1/M2 empirical resolution within the cell is "ambiguous." | Per D-025 commitment 4, ambiguity is surfaced literally, not silently collapsed. Reserved for cases where the cell's own observations don't cleanly fit any of the other four classifications. The M4 control cell is never `ambiguous` by the zero-traffic criterion alone — pure-placeholder cells are expected to produce zero traffic under the silent-filter branch of M4. |

**Classification precedence (applied top to bottom at classification time):**
1. If an uncaught exception escaped the cell's execution → `exception`.
2. Else if a documented SDK exception was raised on the critical path → `rejected`.
3. Else if subscribe ratio ≤ 0.5 → `rejected`.
4. Else if subscribe ratio in (0.5, 1.0) exclusive → `degraded`.
5. Else (ratio == 1.0) if all `clean` conditions hold → `clean`.
6. Else (ratio == 1.0 but some anomaly condition fires) → `degraded`.
7. Else → `ambiguous` (should be rare; used only when none of the above rules resolve).

Sweep-run classification (`SweepRunOutcome.run_classification`) is aggregated from cell classifications:
- `clean` — every cell is `clean`.
- `partial` — some cells clean, some degraded, none rejected/exception/ambiguous.
- `failed` — one or more cells rejected or exception.
- `ambiguous` — one or more cells ambiguous and none rejected/exception.

### 16.8 Acceptance bar

Per D-021 (testing posture) and D-020 (definition of done), the sweeps deliverable is accepted when:

1. **Unit tests pass in a fresh venv against pinned deps.** The `tests/test_stress_test_sweeps.py` suite exercises non-network paths: grid generation (cell enumeration from CLI args), placeholder-slug synthesis (deterministic, format-correct, non-colliding with real slugs), classification state machine (each rule path covered), outcome record serialization, config loading (inherits `POLYMARKET_US_API_KEY_ID` / `POLYMARKET_US_API_SECRET_KEY` discipline from probe.py's `load_probe_config`). Zero SDK mocking, per H-012 addendum.

2. **Operator code review.** Claude presents the `sweeps.py` + test files for review in the same session that produces them (or in a subsequent session, at operator's cut). Review follows the same shape as H-013's probe.py review.

3. **Live smoke run against actual gateway.** Per D-020's "actual asset count we expect" language as revised per §13.2's N=74 baseline (now ≈126 per §14.2's H-016 observation; will be larger at H-020), the live run covers at least:
   - One successful cell of `--sweep=subscriptions` at N=1 (positive control — mirrors the probe's shape).
   - One successful cell of `--sweep=subscriptions` at N≥2 (answers M1 directly).
   - One successful cell of `--sweep=connections` at N≥2 (answers M2 directly).
   - The dedicated M4 control cell (100P/0R single-subscription, single-connection) runs to completion and M4 resolves to one of the named options (silent filter / hard rejection / unexpected-traffic flag).
   - The full `--sweep=both` run, completing within its documented ~30-minute window, producing a `SweepRunOutcome` JSON that captures M1–M5 resolutions.
   - Outcome JSON is preserved for the §17 (or next additive) research-doc analysis.

4. **All results cited against [E], [F], [G] or against §16's measurement questions.** No prose interpretation of outcomes without traceable source. If the sweeps produce an unexpected observation that does not fit §16's M1–M5 frame, the observation is logged literally in the `run_notes` field and surfaced to operator rather than reinterpreted.

The acceptance bar is the same discipline probe.py cleared at H-016 — unit tests plus operator-reviewed code plus live smoke against the actual gateway producing data that a subsequent research-doc section interprets.

### 16.9 Session-close discipline for the code turn

For H-020-Claude (or whichever session implements the sweeps code) reading this section to know what to do:

1. **Re-fetch [E] at code-turn time.** The re-fetch at H-019 established a clean baseline, but code-turn sessions operate under R-010 (Claude fabrication) and D-016 commitment 2 (research-first for external APIs); the pin-against-fresh-source discipline applies at every code-touch of the SDK surface, not just at research-doc time. Fetch record for the code-turn session goes in the session handoff, not in a revised §16 — §16 is frozen at H-019.
2. **If [E] has moved materially** (commit count changed, SDK version past 0.1.2, any surface change): do not write code against §16's commitments without first surfacing the delta. That is a governance-layer event and warrants a targeted DJ entry before code.
3. **If [E] is unchanged** from H-019's fetch record (§16.1): proceed to code, citing §16 in the sweeps module header block [H]+, and citing [E], [F] for SDK/wire-format material as probe.py cited [A]–[C].
4. **No Phase 2 code touch** per D-016 commitment 2. Sweeps are in `src/stress_test/` only.
5. **No modification to `pm-tennis-api/requirements.txt`** per D-024 commitment 1. Sweeps deps live in `src/stress_test/requirements.txt` and reuse the existing pins.
6. **Always-replace convention** per D-029 §3 / H-016: `sweeps.py` and test files are produced as complete files, never as splice-into-existing-file instructions.
7. **Session cut discipline.** If H-020 cuts the session at code-only (deferring live smoke to H-021), the acceptance bar's items 3 and 4 defer with it; §17 (or next additive) is not written until after live smoke produces data. One-deliverable-per-session is the project's pattern.

### 16.10 What §16 does not decide

- **Exact observation-window length per cell.** Default is inherited from probe.py's 10 seconds; sweeps may want longer (30–60s per cell) because aggregate message volume is the measurement. Final value set at code-turn time, informed by [E]'s behavior at 100-slug scale.
- **Exact placeholder-slug synthesis details.** §16.5 commits to format-matching synthesis with deterministic seeding; the exact construction (e.g., whether placeholder date suffixes are past-dated, far-future, or syntactically invalid) is a code-turn decision informed by M4 pilot observations.
- **Module-internal architecture of `sweeps.py`.** Whether the grid is enumerated as a Python generator, a data-class tree, a CLI-flag-parsed list — all are implementation details of one module; §16 commits to the external CLI surface and the outcome-record shape, not to the internal code structure.
- **Whether `SweepRunOutcome` is written to stdout only or also persisted to a file.** Per §7 Q1=(a) no-disk-writes commitment, the default is stdout-only. Code-turn may want a `--output-file` flag for convenience; if so, it reads from `/tmp` (ephemeral, not the persistent disk) and is flagged as operator-scrapable rather than archival.
- **Whether `--sweep=subscriptions` and `--sweep=connections` run in the same process or via two separate invocations.** Both are sound; code-turn picks one.
- **The shape of §17** (the main-sweeps-outcome addendum that will interpret the live smoke results). §14 is the precedent; §17 will follow that convention when written.
- **The teardown of `pm-tennis-stress-test`** after sweeps complete. Per RB-002 teardown section, the service is deleted after stress-test work is in hand; §16 does not schedule this, but flags it as the post-§17 cleanup step.
- **Plan-text revisions v4.1-candidate-2 (the 150-asset-cap vs documented-100-cap reconciliation).** Remains queued in STATE `pending_revisions`. §16 does not cut a plan revision; it populates the research the revision will reference.

### 16.11 What §16 does not change

- **§16 does not amend §§1–15.** §§1–15 are preserved byte-identical from v4 as recorded pre-H-019; §16 is a purely additive section appended after §15. No claim in §§1–15 is revised, no wording in §§1–15 is edited, no §-level renumbering occurs. §15.1's H-013 findings on Ed25519 signing, timestamp unit, and dep footprint stand as recorded; §16.1's re-fetch is confirmation, not revision. §14.3's probe outcome stands; §16 cites it as supporting evidence (n=1) for M1 without re-interpreting it.
- **§7 Q1/Q2/Q3/Q4/Q5/Q5′ resolutions stand.** D-023/D-024/D-025/D-027 commitments are in force as-recorded.
- **D-025 commitments 2, 3, and 4 stand.** D-027 supersedes commitment 1 only; §16's api-sourced default for main sweeps implements D-025's resolved branch from §14.4.
- **No plan-text revisions are cut.** v4.1-candidate, v4.1-candidate-2, v4.1-candidate-3, v4.1-candidate-4 remain queued in STATE `pending_revisions`.
- **No commitment files are touched.** `fees.json`, `breakeven.json`, `signal_thresholds.json` (which does not exist), `data/sackmann/build_log.json` — none in the path of §16 or of the sweeps code turn.
- **No Phase 2 source files are touched.** `src/capture/discovery.py`, `main.py` — untouched by §16.
- **No RAID entries added or modified by §16 itself.** §16 populates the research record; it does not surface new risks or issues. If code-turn work does surface any, that is H-020's scope, not H-019's.

---

## 17. H-023 main-sweeps-outcome addendum — two runs of live-gateway evidence against §16's harness

This section is additive to v4. Written at H-024 (2026-04-21) to record the outcome of two live-smoke sweep invocations executed at H-023 against the Polymarket US Markets WebSocket gateway, using the sweeps harness committed at H-020 per §16.8 and the pinned SDK surface confirmed at H-022 via RB-002 Step 4 validation. §17 follows §14's precedent for an outcome addendum: input, execution, outcome, classification and interpretation, work summary, what the next session picks up, what §17 does not change. §§1–16 are unchanged by this section.

§17 is written one session after the evidence was captured. H-023-Claude held §17 drafting for H-024 under the one-deliverable-per-session discipline, and under the judgment that transcription and interpretation of two 180KB `SweepRunOutcome` JSON artifacts plus structural findings on anchor-slug sourcing and WebSocket error-event behavior warranted its own focused session rather than bundling with the execution that produced them. H-024 is that session.

### 17.1 Why §17 is written now and what it scopes

§16 committed the sweeps harness design (§16.5), the per-cell outcome record shapes (§16.6), the classification state machine (§16.7), and the acceptance bar (§16.8) without data against any of them. §16.8 names the live smoke run against the actual gateway as the third leg of the acceptance bar, producing data that a subsequent additive section would interpret. H-023 executed that live smoke run in two invocations and produced the data. §17 is that interpretation.

§17 scopes only the empirical content of the two H-023 runs: what was observed, how observations classify against §16.7's state machine, which of §16.4's measurement questions (M1 through M5) each run resolved and which remain open, and which findings surfaced that §16 did not anticipate. §17 does not reopen any §16 commitment. §17 does not revise §16's frame. §17 does not cut any plan-text revision. If post-§17 work motivates a revision to the sweeps harness, the anchor-slug sourcing strategy, or the exception-type partition, that work is explicitly deferred past H-024 — frame-extension or redesign work is research-first per D-019 and does not belong in a transcription addendum.

One framing-precision discipline governs §17 throughout and warrants naming at the top rather than repeated at every claim. **The two runs observed a specific slice of gateway behavior: one 30-second observation window per cell, one anchor slug per run, two runs separated by ~80 minutes.** Every quantitative claim in §17 is bound by those parameters. Message counts are for a 30-second window on a specific anchor; timing intervals are for a specific pair of runs; per-cell classifications reflect a specific harness state at a specific moment against a specific live match. §17 does not make general claims about gateway architecture, SDK behavior, or market dynamics; it records what the harness observed and interprets the observations within the scope the harness defined.

### 17.2 Run inputs

Both runs executed from the `pm-tennis-stress-test` Render service at the known-good runtime state established at H-022 (RB-002 Step 4 self-check seven-for-seven, per §14 precedent for runtime-validation posture). No Manual Deploy between the two runs; no code changes between the two runs; same commit, same deployed binary, same credential environment. The difference between runs is one parameter: the anchor slug supplied to `_fetch_anchor_slug`.

**Run 1** exercised `_fetch_anchor_slug`'s default path (no `--seed-slug` argument; the function calls `client.markets.list({"limit": 1})` and takes the first element).

**Run 2** exercised `_fetch_anchor_slug`'s operator-supplied path via `--seed-slug=<slug>`. The operator sourced the slug from the `pm-tennis-api` service's persistent-disk meta.json corpus — specifically `/data/matches/9579/meta.json`, whose `moneyline_markets[0].market_slug` field names an active Challenger-level men's singles match (Kicker vs Mayo, Challenger Savannah, ATP, event id 9579). The operator confirmed on the Polymarket US iPhone app that the match was live in-play (first set) at the moment of invocation.

Run inputs summary:

| Parameter | Run 1 | Run 2 |
|---|---|---|
| Invocation | `python -m src.stress_test.sweeps --sweep=both --log-level=INFO` | `python -m src.stress_test.sweeps --sweep=both --log-level=INFO --seed-slug=aec-atp-nickic-aidmay-2026-04-21` |
| Started (UTC) | 2026-04-21 ~13:05 | 2026-04-21 14:24:19 (run_id 1776781459) |
| Wall-clock | ~4 min | ~4 min |
| Output redirect | `> /tmp/sweep_h021.json 2> /tmp/sweep_h021.stderr.log` | `> /tmp/sweep_h023_run2.json 2> /tmp/sweep_h023_run2.stderr.log` |
| Exit code | 5 (`EXIT_SWEEP_PARTIAL`) | 5 (`EXIT_SWEEP_PARTIAL`) |
| JSON size | 176,843 bytes | 187,891 bytes |
| Stderr size | 4,242 bytes | 4,395 bytes |
| Anchor-slug source path | `_fetch_anchor_slug` → `client.markets.list({"limit": 1})` → first-element dict → field-name fallback chain | `_fetch_anchor_slug` → `--seed-slug` short-circuit (sweeps.py line 1454 branch) |
| Anchor slug resolved to | `aec-nfl-lac-ten-2025-11-02` (settled NFL game, Nov 2025) | `aec-atp-nickic-aidmay-2026-04-21` (live in-play ATP Challenger, operator-supplied) |

The ~80-minute gap between runs is not a designed interval; it reflects the investigation and remediation work between run 1's surfacing of the settled-anchor result and run 2's invocation with a live anchor. The gap is informational for the M4 silent-filter replication claim in §17.4 — the two M4 control-cell observations are separated by ~80 minutes of wall-clock.

### 17.3 Run executions and outcomes

Both runs executed the committed grid per §16.5: one M4 control cell (100P/0R) first, then subscriptions-axis cells at N=1/2/5/10, then connections-axis cells at N=1/2/4. Eight cells per run.

**Run 1 outcomes — settled-anchor baseline.** Because `_fetch_anchor_slug`'s default path resolved to a settled NFL game from November 2025, the anchor slug produced zero traffic across every cell's observation window. Every cell's subscribe succeeded at the SDK level (subscribe_ratio == 1.0 in every cell), which is the expected behavior if placeholder-slug rejection is silent (M4's option a — silent filter). Under §16.7's classification precedence and D-032's Reading B, the M4 control cell classified `clean` via its relaxed caveat (no error events, no close events, traffic not required), and every other cell classified `degraded` via precedence step 6 — subscribe ratio 1.0 but anchor slug produced zero traffic across the observation window. Per-cell `cell_classification_reason` on cells 1–7 read verbatim: *"step 6: subscribe ratio 1.0 but anchor slug produced zero traffic across the observation window"*. The run-level `run_classification` was `partial` per §16.7's aggregation rule (some clean, some degraded, none rejected/exception/ambiguous), matching exit code 5 (`EXIT_SWEEP_PARTIAL`).

M4 control cell result: `m4_observations.m4_control_behavior = "silent_filter"` with `silent_filter_inferred = true`. Subscribe succeeded, no error events, no close events, zero messages for 100 placeholder slugs over the 30-second window. This is a positive first sample for M4 option (a) per §16.4.

M1 and M2 cells all resolved `ambiguous` rather than resolving cleanly into compose/replace (M1) or independent/shared (M2). The resolvers' logic is traffic-distribution-based — `_resolve_m1` returns `compose` only if two or more `request_id` values received traffic, and `_resolve_m2` returns `independent` only if every connection received traffic on its anchor. With zero traffic across all cells, both resolvers fall through to `ambiguous` as the unresolved-by-evidence verdict. This is the designed behavior per §16.4 and per the resolvers' docstrings (sweeps.py lines 1858–1918 for M1, 1921–1973 for M2): ambiguous-without-traffic is the legitimate verdict when the observation window produced no data to discriminate on, and the harness does not force a verdict from absent evidence.

**Run 2 outcomes — live-anchor remediation.** With `--seed-slug` supplying an in-play tennis match slug, the anchor-zero-traffic degradation path on cells 1–7 cleared for cells that had not also surfaced a new anomaly. Four cells classified `clean` via precedence step 5 (cells 1, 5, 6, 7). Three cells classified `degraded` via precedence step 6 with a new anomaly reason (cells 2, 3, 4). M4 control cell classified `clean` via its relaxed caveat for the second time, with field-for-field identical `m4_observations` to run 1. Run-level `run_classification` was `partial` per §16.7's aggregation, matching exit code 5.

Per-cell run-2 summary:

| Cell | Axis / value | Subs per conn | Conns | Classification | Reason (step) | Total msgs |
|---|---|---|---|---|---|---|
| 0 | m4-control (100P/0R) | 1 | 1 | `clean` | step 5 (M4 caveat, no traffic required) | 0 |
| 1 | subscriptions-axis-n1 | 1 | 1 | `clean` | step 5 | 73 |
| 2 | subscriptions-axis-n2 | 2 | 1 | `degraded` | step 6 (error_events fired) | 30 |
| 3 | subscriptions-axis-n5 | 5 | 1 | `degraded` | step 6 (error_events fired) | 66 |
| 4 | subscriptions-axis-n10 | 10 | 1 | `degraded` | step 6 (error_events fired) | 52 |
| 5 | connections-axis-n1 | 1 | 1 | `clean` | step 5 | 78 |
| 6 | connections-axis-n2 | 1 | 2 | `clean` | step 5 | 67 |
| 7 | connections-axis-n4 | 1 | 4 | `clean` | step 5 | 53 |

Per H-023 handoff §9 E9, the per-cell message totals are for the ~30-second per-cell observation window on the operator-supplied anchor slug; these numbers are window-bound and anchor-bound and should not be generalized to "cell N produces Y messages" outside those parameters.

The degraded reason string on cells 2, 3, 4 reads verbatim *"step 6: subscribe ratio 1.0 but error_events fired during observation (N total)"* with N scaling across the cells: N=1 for cell 2 (2 subscribes), N=4 for cell 3 (5 subscribes), N=9 for cell 4 (10 subscribes). The error_events were delivered via the `markets_ws.on('error', ...)` handler pattern (sweeps.py lines 1688–1698), stored in the `ConnectionObservation.error_events` list as truncated repr strings, and fired during the observation window rather than during subscribe. Every subscribe in every cell reported `subscribe_sent = True`; the errors are observation-window events, not subscribe-phase failures. The error-event payload content itself was not extracted into §17 (held per scope discipline; extractable from `/tmp/sweep_h023_run2.json` on the stress-test service's Shell if that artifact still persists at the time of any future analysis, or via a re-sweep if artifacts are evicted).

Zero D-033-predicted exception types fired on any cell in either run. No `PermissionDeniedError`, no `InternalServerError`, no `WebSocketError`. No other exceptions either. Both runs executed the critical path without raising any Python exception the classifier would route to the `rejected` (step 2) or `exception` (step 1) branches of §16.7's precedence.

### 17.4 Classification, interpretation, and findings

Four distinct findings emerge from the run outcomes. Each is recorded below with its empirical support and explicit scope bounds on what the evidence does and does not license.

**17.4.1 M4 silent-filter behavior replicated across two independent runs.** The M4 control cell produced `m4_observations.m4_control_behavior = "silent_filter"` in both runs — the documented-option-(a) result per §16.4's M4 resolution vocabulary. Run 2's M4 control-cell `m4_observations` record was field-for-field identical to run 1's on every pinned field. The ~80-minute interval between runs, during which no code changed and no deploy occurred, gives an additional temporal-stability signal against the M4 control cell's behavior: pure-placeholder subscribes (100 placeholder slugs, 0 real anchors) succeeded at the subscribe level and produced zero messages over the 30-second observation window, in both samples.

This is directionally supportive of the silent-filter branch of M4 as a stable characterization for the placeholder format the harness generates (`aec-ph-<hex>-<hex>-2099-12-31` per §16.5's synthesis strategy). Two samples is not a large basis for a stability claim, and the placeholder-generation code path and format have not changed between the samples. §17 records the observation without generalizing it beyond the two samples and the specific placeholder format tested.

**17.4.2 M2 concurrent-connection independence resolved for the first time on the connections-axis cells — at the traffic-distribution layer.** Run 2's connections-axis-n2 cell (cell 6) and connections-axis-n4 cell (cell 7) both produced `m2_resolution = "independent"`. This is the first non-ambiguous M2 resolution in the project's sweep history; run 1's cells 6 and 7 had produced `ambiguous` under the no-traffic default.

One framing-precision call is load-bearing for how §17 records this finding. The `_resolve_m2` resolver (sweeps.py lines 1921–1973) documents its semantics explicitly in the docstring, and the docstring flags a caveat worth preserving in the research record:

> shared: only one connection appears to have received traffic, OR all connections share identity (cannot be detected here without SDK-level introspection; we use a weaker observable — traffic distribution across connection slots).

The resolver's `independent` verdict is an **observable-level** claim about traffic distribution: all N connections connected, and every connection received traffic on its anchor over the observation window. It is not an SDK-identity-level claim that the two `markets_ws` objects produced by `client.ws.markets()` calls have distinct Python identity or distinct underlying transport connections at the SDK implementation layer. The resolver does not test identity; it tests traffic distribution. A true shared-identity scenario where the SDK returns the same object twice but subscribes produce divergent traffic routing would not be distinguishable by this resolver from genuine independence. §17 therefore records the M2 observation as: at N=2 and N=4 concurrent `client.ws.markets()` instances, on one anchor slug, over a 30-second observation window, traffic was observed on every connection slot — consistent with independence at the observable level the harness measures.

That per-slot traffic attribution would ideally be verified against the per-connection message counts in `ConnectionObservation.subscribe_calls[*].message_count_by_event`. The aggregate totals in the cell-level table (67 for cell 6, 53 for cell 7) support the verdict at the aggregate level — if any connection had received zero traffic at the per-slot level, the resolver would have returned `shared` (at N=2 with trafficked_count==1) or `ambiguous` (at N=4 with partial trafficked_count). The resolver returning `independent` on both cells means the per-slot check passed for every connection in each cell. The per-connection breakdown itself was not extracted into §17 narrative; it is present in the run-2 `SweepRunOutcome` JSON if future work needs the per-connection numbers.

**17.4.3 WebSocket error-event scaling observed on the multi-subscribe cells — a category orthogonal to D-033's partition.** On cells 2, 3, 4 (subscriptions-axis at N=2, 5, 10 subscribes on one connection), the harness observed WebSocket `error_events` firing during the observation window. The count of error_events scaled across the cells: 1 error on cell 2 (2 subscribes), 4 errors on cell 3 (5 subscribes), 9 errors on cell 4 (10 subscribes). The same operator-supplied anchor slug, same observation-window length, same credentials, same service runtime state; the only varying parameter across these three cells is the number of `subscribe()` calls on the single `markets_ws` connection.

The `error_events` are delivered via the `markets_ws.on('error', ...)` handler registration (sweeps.py lines 1688–1698) and stored in `ConnectionObservation.error_events` as truncated repr strings. They are **not Python exceptions**. They never flow through the try/except structure in `_run_cell_async`; they never populate `SweepCellOutcome.exception_type`; they do not trigger `_classify_outcome`'s step 1 or step 2 (which classify on Python exception types). They are WebSocket-protocol-level event payloads delivered via the SDK's event-handler mechanism, and they fire during observation rather than during subscribe (each subscribe reported `subscribe_sent = True` before the errors appeared in the observation window).

This places error_events outside the scope D-033 addresses. D-033 partitions the documented Python exception-type surface of `polymarket-us==0.1.2` into two frozensets (`DOCUMENTED_REJECTED_EXCEPTION_TYPES` and `DOCUMENTED_TRANSPORT_EXCEPTION_TYPES`), which the classifier consults at precedence steps 1 and 2 via string-matching the caught exception's type name. Error_events have no Python exception type to match against; they are orthogonal data. The finding is **not** that D-033's partition is incomplete for its scope — D-033 scopes exception classification and the partition remains correct for the category D-033 addressed. The finding is that error_events are a category D-033 did not scope to address. Frame-extension work covering error_events as an orthogonal classification input — what they indicate, whether they warrant their own partition, how they should influence cell classification or measurement resolution — is deferred past H-024 per §17.6. This extension is research-first work per D-019 and does not belong in §17.

Further scope bounds on the scaling claim itself. The 1/4/9 pattern is one observation across three cell configurations (N=2, 5, 10) on one anchor slug in one 30-second window in one run. It is not a general law about how error_events scale with subscribe count; it is a single observation of three data points in a specific configuration. Whether the pattern replicates under different anchors, different window lengths, different subscribe cadences, or different times of day is not pinned by §17. The pattern is recorded as observed; its replicability is an open empirical question for any future sweep that revisits the multi-subscribe axis.

The payload content of the error_events themselves — what the errors say about which subscribe-request-id they correlate to, what error codes or messages they carry, whether they cluster in time or arrive spread across the observation window — is not extracted into §17 narrative. That extraction requires reading the `ConnectionObservation.error_events` list in the run-2 `SweepRunOutcome` JSON artifact, which lives on the `pm-tennis-stress-test` Shell's `/tmp/` filesystem and may or may not persist across session boundaries. §17 records the count scaling and the delivery mechanism; payload content is a legitimate H-025+ inquiry either via artifact extraction (if still present) or via a targeted re-sweep (new scope).

**17.4.4 Anchor-slug sourcing via `client.markets.list({"limit": 1})` returned a settled non-tennis market — an empirical finding about default SDK behavior, not a bug.** Run 1's `_fetch_anchor_slug` default path exercised the SDK call `client.markets.list({"limit": 1})` and resolved to `aec-nfl-lac-ten-2025-11-02`, an NFL game from November 2025 (settled market). Zero traffic resulted from subscribes against this slug, degrading every cell except the M4 control to `degraded`-via-step-6-anchor-zero-traffic.

The finding is structural and empirical. The SDK function-contract does not promise "return active tennis markets" or even "return active markets" — it promises "return some markets." The function delivered on that contract; it returned a valid markets record for a settled NFL game. The project's `_fetch_anchor_slug` default strategy was built on the implicit assumption that the top-ordered result from `markets.list()` would be usable as a live-anchor source for a tennis-sweep harness. That assumption is not supported by the observed SDK default-ordering behavior.

Two subsidiary observations contribute to the finding. First, `_fetch_anchor_slug`'s defensive field-name chain resolved via its third fallback `'slug'` (not `'marketSlug'` or `'market_slug'`) when extracting the slug from the returned element (sweeps.py line 1495 dict-path branch — empirical confirmation of §16.1's note that inner element shape was not pinned at §16 authoring). The fall-through warning path at line 1499 did not fire on either run, meaning the defensive chain is adequate for the shape the SDK actually returns. Second, during H-023's run-2 remediation investigation, an operator-side exploratory `client.markets.list({"limit": 100})` query returned 57 NBA + 43 NFL markets — zero tennis markets in the top 100 under the default ordering. Tennis content exists on Polymarket US (confirmed by the `pm-tennis-api` discovery loop writing 126 active tennis event meta.json files at H-016 and continuing growth); it does not surface via `markets.list()`'s default-ordering at top rank.

This is a finding about what `_fetch_anchor_slug`'s default strategy needs to do, not a claim that `markets.list()` is broken. The `_fetch_anchor_slug` redesign — whether to pass filter parameters to `markets.list()`, whether to read from `pm-tennis-api`'s meta.json corpus as the primary source, whether to require `--seed-slug` rather than accept a default, whether to fall through to `markets.list()` only after filter-based approaches — is research-first work per D-019, deferred past H-024 per §17.6.

Run 2's `_fetch_anchor_slug` operator-supplied path (the `--seed-slug=<slug>` short-circuit at sweeps.py lines 1454–1458) executed without exercising the `markets.list()` default path. The stderr log line confirmed the path taken verbatim: *"anchor slug: using operator-supplied --seed-slug=aec-atp-nickic-aidmay-2026-04-21"*. Both code paths of `_fetch_anchor_slug` now have empirical evidence — the default `markets.list()` path on run 1 and the `--seed-slug` short-circuit on run 2.

**17.4.5 Additional M-question status after both runs.** Beyond the above four findings:

- **M1** (multi-same-type subscription composition on one `markets_ws`) resolved `ambiguous` on every M1-testable cell across both runs. Run 1 cells 2–4 produced no traffic (settled anchor); the resolver had no per-request_id attribution data to discriminate `compose` from `replace`. Run 2 cells 2–4 produced traffic (30/66/52 messages respectively) but the M1 resolver still returned `ambiguous` on those same cells. The resolver's `compose` verdict requires ≥2 distinct `request_id` values each receiving nonzero traffic; its `replace` verdict requires exactly one `request_id` receiving traffic and that one being the last subscribe; its `ambiguous` verdict catches everything else. The resolver returning `ambiguous` with traffic present means the per-`request_id` distribution did not cleanly satisfy either `compose` or `replace` under the conditions observed. M1 remains an open measurement question — unresolved by the two runs available. Mechanism-level interpretation of why the resolver returned `ambiguous` with traffic present is out of scope for §17 and deferred to the H-025+ work named in §17.6.

- **M3** (per-subscription cap behavior at 100 slugs) is not directly tested by the committed grid; the grid uses 100 slugs per subscription (1 real + 99 placeholder) as the default, and the harness observed first-message latency and per-slug attribution per §16.4's M3 measurement-method. First-message latency values are present in run 2's cell outcomes (not summarized in §17 narrative; in the `SweepRunOutcome` JSON). A dedicated 101-slug negative-control cell is named in §16.4 as the negative control; that cell is not in the default grid and was not tested in either run.

- **M5** (connection-level concurrent-connection cap) received positive evidence up to N=4 concurrent connections. Cell 7's `m2_resolution = "independent"` combined with its `clean` classification means all four concurrent connections connected cleanly, subscribed successfully, received traffic, and closed cleanly within the observation window. At N=4, no connect failure, no subscribe failure, no rate-limiting, no silent-broken connection was observed. §16.4's M5 measurement specifies "any non-success across the 4-connection cell answers M5 at an upper bound; success across all three cells answers M5 as `≥4 concurrent OK`." By that criterion, M5 resolves at `≥4 concurrent OK` for the configuration tested on run 2. Upper-bound behavior (at what N the axis stops working cleanly) is not tested by the committed grid, which caps at N=4.

- **D-033 exception-type predictions** (PermissionDeniedError, InternalServerError, WebSocketError) remained unexercised across both runs. Zero instances of any of the three predicted types fired on any cell critical path. This is neither evidence for nor against the partition — the sweep grid as designed does not naturally exercise the code paths that trigger these types. D-033's partition remains hypothesis-correct-by-construction; empirical confirmation or contradiction requires a future experiment outside §16's scope.

### 17.5 H-023 work summary for the research record

Consolidated for future readers of this document.

| H-023 deliverable | Status at H-023 close |
|---|---|
| §16.9 step 1a+1b re-fetch at session open | Operator ruled exit state A (clean) on combined [E]/[F]/[G] + installed-module introspection layers. D-033 frozenset validity preserved; 91/91 sweeps unit tests pass. |
| Run 1 live-smoke execution (default `_fetch_anchor_slug`) | Executed on pm-tennis-stress-test Shell against current main binary at H-022 known-good runtime state. Exit 5. JSON 176,843 bytes; stderr 4,242 bytes. Wall-clock ~4 min. |
| Run 1 finding: settled-anchor zero-traffic degradation | Cells 1–7 all `degraded` via step 6 anchor-zero-traffic. M4 control cell `clean` with `silent_filter_inferred=true` (first sample). |
| Run 2 live-smoke execution (`--seed-slug` operator-supplied, live ATP Challenger) | Slug sourced from `pm-tennis-api` meta.json corpus (event 9579); operator confirmed live in-play on Polymarket US iPhone app before invocation. Exit 5. JSON 187,891 bytes; stderr 4,395 bytes. Wall-clock ~4 min. |
| Run 2 finding: four cells clean, three degraded via error_events, M4 replicated | Cells 1, 5, 6, 7 `clean` via step 5 with anchor-slug traffic. Cells 2, 3, 4 `degraded` via step 6 error_events (1/4/9 errors for 2/5/10 subscribes). M4 control cell `clean` with `silent_filter_inferred=true` (second sample, field-identical to run 1). |
| M2 concurrent-connection independence resolved | First non-ambiguous M2 resolution in project sweep history: `'independent'` on connections-axis-n2 and connections-axis-n4, at the traffic-distribution observable level per resolver docstring caveat. |
| M1 multi-subscribe composition resolution | `'ambiguous'` on all testable cells across both runs; with and without traffic. Unresolved by the two runs available. |
| D-033 exception-type prediction exercise | Unexercised across both runs. Neither evidence for nor against the partition. |
| `_fetch_anchor_slug` both code paths empirically exercised | Default `markets.list()` path via run 1 (field-name resolved via third fallback `'slug'`); operator-supplied `--seed-slug` short-circuit via run 2. Fall-through warning path did not fire either run. |
| Novel finding: WebSocket error_events scaling under multi-subscribe load | 1/4/9 error_events for 2/5/10 subscribes on one connection. Orthogonal to D-033's Python-exception partition. Payload content not extracted; held for H-025+ frame-extension work. |
| Novel finding: `markets.list()` default-ordering returns non-tennis settled markets | Structural finding on SDK default behavior. Motivates `_fetch_anchor_slug` redesign (deferred past H-024, research-first per D-019). |

H-023 made zero code changes, zero test changes, zero DJ entries, zero RAID changes, and zero commitment-file changes. Deploy state of `pm-tennis-stress-test` remained at H-022's known-good runtime state throughout; neither run triggered a new deploy. The session's evidence is preserved in Handoff_H-023 §9 (evidence trail E1–E10 and synthesized items 1–7) as the canonical source; §17 is the interpretation layer over that evidence.

### 17.6 What H-025+ picks up

§17 explicitly defers the following work past H-024. Each is named here so the deferral is visible in the research record rather than implicit.

1. **`_fetch_anchor_slug` redesign.** The default `markets.list()` path is empirically unsuited as a live-anchor source for tennis-sweep work (per §17.4.4); the `--seed-slug` path requires operator-side sourcing. Redesign is research-first work per D-019 — a standalone research document evaluating candidate strategies against the SDK surface, filter capabilities, and cross-service data-access constraints precedes the code turn. The candidate set itself is research-first scope and §17 does not enumerate it.

2. **D-033 frame extension to cover WebSocket error_events as an orthogonal category.** D-033 scopes Python exception-type classification via frozenset string-matching at classifier steps 1 and 2. WebSocket error_events are a different category (protocol-level event payloads delivered via `markets_ws.on('error', ...)`, not Python exceptions — per §17.4.3). Extending the frame to cover error_events is research-first per D-019; the shape of the extension (whether an amendment to §16's classification state machine, a new research-doc section, or something else) is itself research-first scope and §17 does not pre-determine it.

3. **M1 resolution work.** The two runs of evidence leave M1 unresolved (per §17.4.5). Advancing M1 is dependent on item 1 as a prerequisite — a cleanly-sourced live anchor is a precondition for any M1 follow-up experiment. The form the M1 follow-up takes (targeted re-sweep against the redesigned anchor source, or some other experiment shape) is research-first scope and §17 does not pre-determine it.

4. **Error-event payload extraction.** The `ConnectionObservation.error_events` list contains truncated repr strings for each fired error_event in run 2 cells 2, 3, 4. Extraction into interpretable form (error codes, correlation to subscribe request_ids, timing within the observation window) was held out of §17 per scope discipline. Extraction is available via the run-2 `SweepRunOutcome` JSON if the `/tmp/` artifact persists on `pm-tennis-stress-test` Shell at extraction time, or via a targeted re-sweep if artifacts are evicted. Extraction is a prerequisite to the D-033 frame-extension work in item 2.

5. **Any code changes** to sweeps.py, the classifier, the outcome records, or the tests. Zero code changes were made at H-023; §17 does not motivate any code change on its own. Code-turn work follows D-019 research-first sequencing and is gated on the research-document-first-then-code pattern H-019 established for §16 and reinforced by H-020.

6. **Phase 3 exit gate candidate work.** §17 does not close Phase 3. §17 closes the §16 sweeps deliverable's acceptance bar per §16.8 items 3 and 4 — live smoke run executed, outcome JSON preserved, results cited against §16's measurement questions. Other Phase 3 exit triggers (48-hour unattended capture, CLOB pool recycle, Sports WS retirement, handicap capture, first-server identification) remain untested and ungated.

### 17.7 What §17 does not change

- **§17 does not amend §§1–16.** §§1–16 are preserved byte-identical from v4 + §§13–16 additives as recorded pre-H-024; §17 is a purely additive section appended after §16.11. No claim in §§1–16 is revised, no wording in §§1–16 is edited, no §-level renumbering occurs. The §14 precedent for additive-after-the-fact outcome addenda is followed.
- **§16's five measurement questions (M1–M5) remain as scoped.** §17 records which questions the two runs resolved (M4 silent_filter replicated, M2 `'independent'` at observable level up to N=4, M5 `≥4 concurrent OK` for the tested configuration) and which remain open (M1 unresolved, M3 not directly grid-tested). The questions themselves are not re-opened or re-framed.
- **§16.7's classification state machine is not revised.** The seven-step precedence rules executed as written; every cell in both runs classified via one of the named steps with the documented reason string. D-032's Reading B held. No step was bypassed, no rule was re-interpreted.
- **§16.6's outcome record shapes stand.** `SweepCellOutcome`, `ConnectionObservation`, `SubscribeObservation`, `SweepRunOutcome` all populated as specified. No new fields added, no existing fields re-interpreted.
- **D-032, D-033 stand as ruled.** D-032's Reading B predicate drove the clean-vs-degraded decision on every cell; D-033's frozensets stand correct for the category they scope. §17.4.3's error_events finding is orthogonal to D-033, not a revision of D-033.
- **D-025 commitments 2, 3, 4 stand.** D-027 supersession of D-025 commitment 1 stands. The `--seed-slug` operator-supplied path exercised in run 2 is consistent with D-027 Option D's spirit (operator-supplied slug via CLI argument preserves isolation).
- **D-019 research-first discipline stands.** The deferred items in §17.6 are each explicitly research-first scope. §17 itself is transcription of already-observed evidence against an already-committed research frame and does not bypass research-first.
- **No plan-text revisions are cut by this section.** Plan-text revisions v4.1-candidate, v4.1-candidate-2, v4.1-candidate-3, v4.1-candidate-4 remain queued in STATE `pending_revisions`.
- **No commitment files are touched.** `fees.json`, `breakeven.json`, `signal_thresholds.json` (which does not exist), `data/sackmann/build_log.json` — none in the path of §17.
- **No Phase 2 source files are touched.** `src/capture/discovery.py`, `main.py` — untouched by §17.
- **No RAID entries added or modified by §17 itself.** §17 records empirical findings against §16's frame; any new risks or issues motivated by the findings would be raised at the session producing the follow-up work (H-025+), not in §17.

---

*End of research document — v4, §13 H-012 additive + §14 H-016 probe-outcome addendum + §15 H-014 additive + §16 H-019 main-sweeps-scope addendum + §17 H-024 main-sweeps-outcome addendum.*
