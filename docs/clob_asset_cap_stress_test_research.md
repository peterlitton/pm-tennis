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

*End of research document — v4, §13 H-012 additive + §14 H-016 probe-outcome addendum + §15 H-014 additive.*
