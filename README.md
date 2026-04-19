# PM-Tennis Stress-Test Service

**Status:** scaffolded at H-013 (2026-04-19). Live-probe execution + main sweeps
deferred to H-014 per operator cut at H-013 open.

**Isolated from pm-tennis-api.** This code is deployed as a separate Render
service (`pm-tennis-stress-test`) per D-020/Q2=(b) and D-024 commitment 1.
`pm-tennis-api`'s `requirements.txt` is not modified by Phase 3 attempt 2.

## What this service does

Two modes, selected by CLI flag:

**Self-check (default).** Verifies imports, credential presence (by name
only), and slug-selector can find eligible probe candidates on the shared
persistent disk. **No network. No WebSocket. Safe to run at every service
boot.** This is what the default Render start command runs.

**Probe (`--probe`).** Executes the D-025 hybrid-probe-first single-slug
probe: selects the freshest eligible slug from `/data/matches/*/meta.json`,
authenticates via the `polymarket-us` SDK, subscribes once on the Markets
WebSocket, observes for a configurable window (default 10s), records
structured outcome JSON, disconnects. Used manually or on an explicit
trigger; not the default behavior.

## Why both modes

Per the H-013 cut, the service is deployed this session but the main sweeps
are in H-014. The service may sit idle, get re-deployed, restart. Making
the default boot a no-op means nothing in the service lifecycle accidentally
consumes stress-test resources against the live gateway.

## Authoritative inheritance

Every external fact this service depends on traces to:

- **SDK method surface** (`AsyncPolymarketUS`, `client.ws.markets()`,
  `markets_ws.on(...)`, `markets_ws.connect()`, `markets_ws.subscribe(...)`,
  `markets_ws.close()`, exception types) — `github.com/Polymarket/polymarket-us-python`
  README fetched at H-013.
- **Auth handshake semantics** (three headers, Ed25519, 30-sec window,
  milliseconds) — `docs.polymarket.us/api-reference/authentication` fetched at
  H-013. The SDK handles all signing internally — no user-facing signing
  surface — so the probe never touches the Ed25519 path directly.
- **Subscription type enum `SUBSCRIPTION_TYPE_MARKET_DATA`** — SDK README
  and research-doc v4 §4.3.
- **Slug schema + path** — `src/capture/discovery.py` `TennisEventMeta`
  dataclass + `_meta_path()` helper. Not `/data/events/` (that's the
  raw-poll-snapshot directory per D-026).
- **Probe-candidate selection criteria** — research-doc v4 §13.4 + D-025
  commitment 1.

Fabrication check (per D-016 and H-012 addendum): every SDK symbol
referenced in `probe.py` is listed in the module-header citations block
and was resolved by `python -m src.stress_test.probe` self-check before this
README was written.

## Environment variables

| Name | Required | Purpose |
|---|---|---|
| `POLYMARKET_US_API_KEY_ID` | probe mode | Polymarket US API Key ID (UUID). Set per D-023 in the Render dashboard. |
| `POLYMARKET_US_API_SECRET_KEY` | probe mode | Polymarket US API Secret (base64-encoded Ed25519 private key). Set per D-023 in the Render dashboard. |
| `PMTENNIS_DATA_ROOT` | optional | Defaults to `/data`. Overridable for local testing. |
| `PROBE_OBSERVATION_SECONDS` | optional | Defaults to 10.0. Clamped to (0, 300]. |

## Dependencies

See `requirements.txt`. Pinned:

- `polymarket-us==0.1.2`
- `pytest==8.3.4` (used for acceptance unit tests, installed in the service
  so the gate-evidence test run can happen in-cloud).

Transitive: `httpx`, `pynacl` (libsodium bindings — SDK's Ed25519 backend),
`websockets`, plus standard transitives. All available as wheels for
Linux/x86_64 + CPython 3.12; no compile required on Render.

## Running locally

```bash
# From repo root
pip install -r src/stress_test/requirements.txt
PYTHONPATH=. python -m src.stress_test.probe          # self-check
PYTHONPATH=. python -m src.stress_test.probe --probe  # actual probe
```

Self-check works offline with no credentials. Probe mode requires both
credentials set AND at least one eligible meta.json record.

## Running on Render

Start command (in the Render service dashboard):

```
python -m src.stress_test.probe
```

This runs self-check on every boot. Probe execution is a separate,
manually-triggered invocation (see Runbook RB-002).

## Tests

```bash
PYTHONPATH=. python -m pytest tests/test_stress_test_slug_selector.py -v
```

19 tests covering slug_selector. No network, no SDK mocking — pure
on-disk fixtures. Probe-module smoke-testing is deferred to H-014 against
the live gateway (unit tests with heavy SDK mocking would hide the kind
of drift that tripped H-008).

## Exit codes (probe mode)

| Code | Meaning |
|---|---|
| 0 | `accepted` — subscription produced market_data, trade, or heartbeat traffic. |
| 1 | `rejected` — `AuthenticationError`, `BadRequestError`, `NotFoundError`, or error event with no other traffic. |
| 2 | `ambiguous` — `RateLimitError`, or subscribe sent but no response within the window, or connection closed without explicit error or data. Per D-025 commitment 4, surface this to the operator rather than silently resolving. |
| 3 | `exception` — transport error, timeout, or unclassified SDK exception. |
| 10 | Config error (credentials missing, SDK import failed). |
| 11 | No probe candidate on disk (slug_selector returned []). |

## What probe mode writes

- **stdout:** one JSON object matching the `ProbeOutcome` dataclass in
  `probe.py`. This is the raw material for the research-doc §14 addendum.
  Render logs capture stdout, so the probe record is trivially retrievable
  post-run.
- **stderr:** human-readable running commentary + final summary.

## Teardown

This service is intended to be torn down after the H-014 stress-test is
complete and the §14 addendum is written. Deletion in the Render dashboard
destroys the service; the code stays in the repo at this path for audit
and for potential reuse if a v5 re-test is ever warranted.
