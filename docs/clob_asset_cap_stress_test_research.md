# CLOB asset-cap stress test — research document (v4)

**Deliverable:** Phase 3 attempt 2, first deliverable (Ruling 1(e), H-010).
**Authors:** Claude, sessions H-010 (v1–v3) and H-012 (v4).
**Version history:**
- v1 (H-010, earlier turn): initial document. Surfaced §2 ambiguity, §4 as set of unanswered questions, §7 as three operator decisions.
- v2 (H-010, earlier turn): §4 answered via operator-authorized web_fetch research. §2 ambiguity resolved. §3, §5, §7 updated against cited documentation. §11 added naming what research surfaced that changes v1's model.
- v2.1 (H-010, earlier turn): operator follow-up 1 on v2 review. §4.3 code block re-verified as verbatim from the Markets WebSocket page. §4.3.1 added surfacing a case-style inconsistency between the WebSocket Overview page and the Markets WebSocket page that v2 did not note.
- v3 (H-010, later turn): operator ruling Q5=(a). Polymarket US Python SDK README fetched and read. §4.3.1 resolved in favor of Markets WebSocket page's camelCase wire shape. §4.7 resolved: SDK uses a single slug namespace across REST and WebSocket on `api.polymarket.us`; bridging gateway slugs remains unverified but a cleaner path is now visible (§4.7.1). §12 added summarizing SDK-vs-hand-rolled code decision now surfaced. Scope tightened: v3 does not re-open any section not directly affected by the SDK read.
- **v4 (H-012): three H-012 rulings resolved and the §6 meta.json survey executed. §13 added capturing (a) the ruling on POD-H010-§12 = SDK (D-024), (b) the ruling on POD-H010-Q5′ = hybrid probe-first (D-025), (c) the authorization and execution of POD-H010-§6-survey (D-026), (d) the survey findings, (e) the probe-slug default for the Q5′=(c′) probe. v4 is additive only: §§1–12 are unchanged from v3. §5's "actual asset count we expect" estimate (≈38 at H-009 close) and §7's placeholder-bracket discussion are explicitly not revised; §13 cross-references them and notes the updated N=74 baseline instead, preserving v3's operator-accepted text.**
**Status:** Draft for operator review. No code has been written. No endpoint, subscription format, module path, class name, or function signature has been committed to code based on this document. Every external fact in §4 is cited with URL and excerpt per Ruling 2(a) and Tripwire 1. §13 findings are from a read-only in-session survey of the `pm-tennis-api` Render persistent disk; no writes, no mutation.

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

*End of research document — v4, session H-012.*
