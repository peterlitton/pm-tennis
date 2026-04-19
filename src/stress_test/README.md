# PM-Tennis Stress-Test Service

**Status:** scaffolded at H-013 (2026-04-19); D-027 supersession
reflected in this README at H-014 (2026-04-19). Live-probe execution
and main sweeps deferred to H-015 per operator cut at H-014 open.

**Isolated from pm-tennis-api.** This code is deployed as a separate Render
service (`pm-tennis-stress-test`) per D-020/Q2=(b) and D-024 commitment 1.
`pm-tennis-api`'s `requirements.txt` is not modified by Phase 3 attempt 2.

## What this service does

Two modes, selected by CLI flag:

**Self-check (default).** Verifies imports and credential presence (by
name only), then reports on the `slug_selector` fallback path
informationally. **No network. No WebSocket. Safe to run at every service
boot.** This is what the default Render start command runs. On the
isolated Render service, `slug_selector` finds 0 candidates by design —
that is expected behavior under D-027, not an error. See "slug source"
below.

**Probe (`--probe --slug=SLUG`).** Executes the D-025 hybrid-probe-first
single-slug probe: takes the operator-supplied slug, authenticates via
the `polymarket-us` SDK, subscribes once on the Markets WebSocket,
observes for a configurable window (default 10s), records structured
outcome JSON on stdout, disconnects. Used manually per the two-shell
workflow in Runbook RB-002; not the default behavior.

## Slug source — D-027 supersedes D-025 commitment 1

Render persistent disks are strictly single-service per
`render.com/docs/disks` ("A persistent disk is accessible by only a
single service instance ... You can't access a service's disk from any
other service"). D-025's original commitment 1 — probe reads the slug
from Phase 2's `meta.json` archive on the shared disk — is not
implementable with the isolated-service architecture required by D-024
commitment 1 and D-020/Q2=(b).

**D-027 Option D:** the operator selects a gateway-sourced slug from
Phase 2's `meta.json` archive via the `pm-tennis-api` Render Shell, then
passes it to the probe as `--slug=SLUG` on the `pm-tennis-stress-test`
Shell. The research-question intent of D-025 is preserved — the probe
still tests a gateway-sourced slug against the api WebSocket — only the
transport changes.

`slug_selector` remains in this package as a library:

- **Local development** — run the probe with no `--slug` and it falls
  back to `slug_selector` reading `PMTENNIS_DATA_ROOT/matches/*/meta.json`.
- **pm-tennis-api Shell helper** — operator can import and call
  `list_candidates()` from that service's Shell, where `/data` is
  attached, to surface eligible slugs before running the probe.

`slug_selector` is **not** called in the production probe code path on
the Render stress-test service — the isolated service has no `/data`
attachment and the fallback path will always return `[]` there. See
the exit-code table for how the probe surfaces that state.

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
- **Slug schema + path** (for `slug_selector` library use only, not the
  production probe path) — `src/capture/discovery.py` `TennisEventMeta`
  dataclass + `_meta_path()` helper. meta.json lives under
  `/data/matches/{event_id}/`, **not** under `/data/events/` (the latter
  is the raw-poll-snapshot JSONL directory per D-026).
- **Probe-candidate selection criteria** (for `slug_selector` library
  and pm-tennis-api-Shell helper use) — research-doc v4 §13.4. In
  production, slug selection is operator-driven per D-027, not
  selector-code-driven.

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

# Self-check — no network, no credentials needed
PYTHONPATH=. python -m src.stress_test.probe

# Probe with operator-supplied slug (the production invocation shape)
PYTHONPATH=. \
  POLYMARKET_US_API_KEY_ID=<id> POLYMARKET_US_API_SECRET_KEY=<key> \
  python -m src.stress_test.probe --probe \
    --slug=<gateway-sourced-slug> [--event-id=<event_id>]

# Probe with slug_selector fallback (requires a populated local
# PMTENNIS_DATA_ROOT/matches/ tree — useful for development)
PYTHONPATH=. \
  POLYMARKET_US_API_KEY_ID=<id> POLYMARKET_US_API_SECRET_KEY=<key> \
  PMTENNIS_DATA_ROOT=/path/to/local/fixture \
  python -m src.stress_test.probe --probe
```

Self-check works offline with no credentials. Probe mode requires both
credentials set AND either `--slug=SLUG` OR a populated
`PMTENNIS_DATA_ROOT/matches/` fixture tree for the fallback path.

## Running on Render

Start command (in the Render service dashboard):

```
python -m src.stress_test.probe
```

This runs the self-check on every boot — no network, no credentials
required to succeed (missing credentials log as `[warn]`, not `[FAIL]`).
The self-check exits 0 and Render restarts the service; that restart
churn is expected. An alternative start command that runs self-check
once then sleeps is described in Runbook RB-002 Step 4.

**The probe is NOT invoked by the start command.** Probe execution is
a manual, operator-driven workflow per D-027 and Runbook RB-002:

1. **In the `pm-tennis-api` Shell** (where `/data/matches/` is
   attached): operator runs a one-line Python snippet to list eligible
   probe candidates from Phase 2's meta.json archive, then copies one
   slug + its event_id.
2. **In the `pm-tennis-stress-test` Shell** (this service's Shell):
   operator runs `python -m src.stress_test.probe --probe
   --slug=<SLUG> --event-id=<EID>`.
3. Operator copies the stdout `ProbeOutcome` JSON back to Claude for
   the research-doc addendum.

Runbook RB-002 is authoritative for the step-by-step procedure.

## Tests

```bash
PYTHONPATH=. python -m pytest \
  tests/test_stress_test_slug_selector.py \
  tests/test_stress_test_probe_cli.py -v
```

38 tests total — 19 for slug_selector (pure on-disk fixtures) and 19
for the probe CLI (argparse, config paths, ProbeOutcome dataclass,
classification-to-exit-code mapping). No network, no SDK mocking. The
probe module's live-network path is exercised at H-014 against the
actual gateway (unit tests with heavy SDK mocking would hide the kind
of drift that tripped H-008).

## Exit codes (probe mode)

| Code | Meaning |
|---|---|
| 0 | `accepted` — subscription produced market_data, trade, or heartbeat traffic. |
| 1 | `rejected` — `AuthenticationError`, `BadRequestError`, `NotFoundError`, or error event with no other traffic. |
| 2 | `ambiguous` — `RateLimitError`, or subscribe sent but no response within the window, or connection closed without explicit error or data. Per D-025 commitment 4, surface this to the operator rather than silently resolving. |
| 3 | `exception` — transport error, timeout, or unclassified SDK exception. |
| 10 | Config error (credentials missing, SDK import failed). |
| 11 | `EXIT_NO_CANDIDATE` — no `--slug` provided AND the fallback `slug_selector` returned []. On the isolated Render stress-test service the fallback always returns [] (no disk access per D-027), so this code means the operator forgot to pass `--slug=SLUG`. See RB-002 for the correct invocation. |

## What probe mode writes

- **stdout:** one JSON object matching the `ProbeOutcome` dataclass in
  `probe.py`. This is the raw material for the research-doc §15
  addendum (H-014) or a later addendum. Render logs capture stdout, so
  the probe record is trivially retrievable post-run.
- **stderr:** human-readable running commentary + final summary.

## Teardown

This service is intended to be torn down after the H-014 stress-test is
complete and the §14 addendum is written. Deletion in the Render dashboard
destroys the service; the code stays in the repo at this path for audit
and for potential reuse if a v5 re-test is ever warranted.
