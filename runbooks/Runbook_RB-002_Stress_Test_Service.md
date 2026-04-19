# Runbook RB-002 — Stand up the `pm-tennis-stress-test` Render service

**Runbook ID:** RB-002
**Produced:** H-013 (2026-04-19); **rewritten:** H-014 (2026-04-19) per D-027
**Status:** Active
**Purpose:** operator-executed steps to provision the isolated Render
service that hosts the Phase 3 attempt 2 stress-test code.
**Audience:** operator. No terminal or SSH required; everything is in the
Render web dashboard and two Render Shell sessions.
**Time estimate:** 10–15 minutes for provisioning (Steps 1–4);
additional 2–3 minutes per probe invocation (Step 5).

---

## Why isolated

D-024 commitment 1 and D-020/Q2=(b) require the stress-test code to run
on a **new, separate Render service**, not added to `pm-tennis-api`.
This is the "separate service, torn down after" design. The benefits:

- `pm-tennis-api` discovery loop stays untouched — no risk of breaking
  Phase 2 with Phase 3 code.
- Teardown is trivial: delete the service when stress-test work is
  complete.
- Environment variable scope is its own — credentials are entered
  separately on this service, not shared from `pm-tennis-api`.

## Why no shared disk (D-027)

The earlier draft of this runbook proposed mounting `pm-tennis-api`'s
persistent disk read-only on the stress-test service so the probe could
read `/data/matches/*/meta.json` directly. That architecture is not
supported: Render documents persistent disks as strictly single-service
("A persistent disk is accessible by only a single service instance ...
You can't access a service's disk from any other service" —
`render.com/docs/disks`).

D-027 (H-013) ruled **Option D**: operator picks a slug from
`pm-tennis-api`'s Shell (where `/data` is attached), then passes it
to the probe as `--slug=SLUG` in the stress-test service's Shell. The
research-question intent of D-025 is preserved — the probe still tests a
gateway-sourced slug against `wss://api.polymarket.us/v1/ws/markets`;
only the slug-to-probe transport changes.

---

## Preconditions

- [ ] The H-013 bundle + the H-014 bundle have been committed to `main`
  on GitHub (`peterlitton/pm-tennis`). In particular:
  `src/stress_test/` exists with `__init__.py`, `probe.py`,
  `slug_selector.py`, `requirements.txt`, and (D-027-correct) `README.md`.
  Check in the GitHub web UI.
- [ ] You still have access to the Polymarket US Key ID and Secret Key
  from the developer portal. D-023 stored them as Render env vars on
  `pm-tennis-api`; we will **re-enter the same values** as new env vars
  on the new service. Render does not share env vars across services.
- [ ] `pm-tennis-api` service is live and healthy (Step 5 depends on its
  Shell being available for slug selection).

---

## Step 1 — Create the new web service in Render

1. Go to `https://dashboard.render.com`.
2. Click **New +** → **Web Service**.
3. Connect to the existing GitHub repo `peterlitton/pm-tennis`. (Render
   already has OAuth access from `pm-tennis-api`.)
4. Fill in the service form:
   - **Name:** `pm-tennis-stress-test`
   - **Region:** Oregon (US West). Same region as `pm-tennis-api` is
     preferred but not required. (D-027 removed the shared-disk
     dependency; region is now only a latency/cost consideration.)
   - **Branch:** `main`
   - **Runtime:** Python
   - **Build Command:** `pip install -r src/stress_test/requirements.txt`
   - **Start Command:** `python -m src.stress_test.probe`
     - This runs **self-check only** — no network, no probe. It's safe
       to run at boot.
   - **Instance Type:** `Starter` (cheapest). We don't need Standard;
     probe invocations are ~10 seconds of traffic against one WebSocket.
   - **Auto-Deploy:** **Off** (set to "No" or "Manual").
     - We want explicit control over when the service redeploys during
       the H-015 stress-test sweeps. Auto-deploy on every push would be
       noise during the live run.
5. Scroll to **Advanced** and set:
   - **Health Check Path:** leave blank / disabled.
     - This is not a long-running web server. The default start command
       exits after self-check. A health check would keep reporting
       unhealthy.

**Do NOT create the service yet.** Add env vars in the same form before
submitting (Step 2).

---

## Step 2 — Add environment variables in the same form

In the service form, scroll to **Environment Variables**. Add:

| Key | Value |
|---|---|
| `POLYMARKET_US_API_KEY_ID` | (your Key ID from the developer portal) |
| `POLYMARKET_US_API_SECRET_KEY` | (your Secret Key from the developer portal) |

Optional (has a sensible default in code):

| Key | Value |
|---|---|
| `PROBE_OBSERVATION_SECONDS` | `10.0` (default; leave unset unless you want a different window) |

Note: `PMTENNIS_DATA_ROOT` is **not** set on this service. The
stress-test service has no persistent disk; the `slug_selector` fallback
path will always return `[]` here, which is expected behavior per
D-027. The production probe invocation supplies `--slug` explicitly.

**Important:**

- Type the values directly into the Render form. **Do not paste them
  into the chat with Claude.** Per SECRETS_POLICY §A.6, secret values
  never enter the chat transcript.
- Render masks values by default after save (D-023 subsidiary finding 3).

Now click **Create Web Service**. Render will provision and run the first
build. This takes 2–5 minutes.

---

## Step 3 — Skip: no disk attach

**Skip this step.** Under D-027, the stress-test service does not mount
a persistent disk. Slug selection happens in the `pm-tennis-api` Shell
and the slug is passed to the probe as a CLI argument (Step 5). There
is no `/data` mount on this service.

If you find yourself wanting to attach a disk anyway because the
self-check output in Step 4 reports "0 probe candidates" — don't. That
output is expected. It is the signal that the service is correctly
isolated per D-027.

---

## Step 4 — Verify first build and self-check

1. After the service reports "Live", open **Logs** in the service
   dashboard.
2. Expected stderr output, in order:
   ```
   === pm-tennis stress-test self-check ===
   [ok] polymarket_us import ok (version: 0.1.2)
   [ok] SDK surfaces AsyncPolymarketUS + exception types importable
   [ok] POLYMARKET_US_API_KEY_ID set
   [ok] POLYMARKET_US_API_SECRET_KEY set
   [info] 0 probe candidates from slug_selector (PMTENNIS_DATA_ROOT=/data).
          Expected on Render stress-test service per D-027 — disks are
          single-service. Probe mode requires --slug=SLUG from operator.
   === self-check complete ===
   ```
   Notes:
   - Both credential lines should read `[ok] ... set`. If either reads
     `[warn] ... NOT SET`, go back to Step 2 and re-enter the env var
     in the Render dashboard, then manually redeploy.
   - The `[info] 0 probe candidates` line is **expected** and confirms
     D-027-correct isolation. It is not a warning or error.
3. The service exits 0 after self-check. Render marks it "Live" briefly
   then restarts it. **This is expected** — the start command is a CLI
   that finishes, not a long-running server. Render's restart churn is
   harmless because each restart just reruns the no-op self-check.

**Alternative — quieter logs via a sleep-after-selfcheck start command.**
If the restart churn is noisy, edit the start command in the Render
dashboard to:

```
sh -c "python -m src.stress_test.probe && sleep 86400"
```

That runs self-check once at boot, then sleeps 24h to keep the service
in its "running" state without further activity. Acceptable workaround;
not required.

---

## Step 5 — Executing the probe (two-shell workflow per D-027)

This step is run during H-015 (live probe execution), not at
provisioning time. Documented here for reference.

### 5.1 — Pick a slug in the `pm-tennis-api` Shell

1. Open the Render dashboard → `pm-tennis-api` service → **Shell** tab.
2. Paste the following one-liner. It imports `slug_selector` (the repo
   that `pm-tennis-api` has checked out contains `src/stress_test/`
   even though `pm-tennis-api` itself doesn't use that package at
   runtime) and lists the top 5 eligible probe candidates:
   ```bash
   PYTHONPATH=/opt/render/project/src python -c "
   from src.stress_test.slug_selector import list_candidates
   for c in list_candidates()[:5]:
       print(f'{c.event_id}  {c.market_slug}  discovered_at={c.discovered_at}  event_date={c.event_date}  {c.title!r}')
   "
   ```
   (Adjust the `PYTHONPATH` prefix if Render mounts the repo at a
   different path; `cd /opt/render/project/src && pwd && ls` will
   confirm the path and that `src/stress_test/` is present.)
3. Read the output. Each line is one candidate, freshest first. Pick
   the topmost candidate whose `event_date` is at least 24 hours in
   the future (gives the match time to stay pre-match through the
   probe's ~10-second observation window).
4. Copy the `event_id` and `market_slug` of the picked candidate.

**If the list is empty:** Phase 2 discovery has no current pre-match
tennis events. Unusual but possible during off-peak hours. Wait an hour
and retry, or surface to Claude for investigation.

### 5.2 — Run the probe in the `pm-tennis-stress-test` Shell

1. Open the Render dashboard → `pm-tennis-stress-test` service →
   **Shell** tab.
2. Run:
   ```bash
   python -m src.stress_test.probe --probe \
     --slug=<MARKET_SLUG_FROM_STEP_5.1> \
     --event-id=<EVENT_ID_FROM_STEP_5.1>
   ```
3. The probe runs for ~10 seconds (the default observation window),
   then prints a `ProbeOutcome` JSON object to stdout and a short
   human-readable summary to stderr.
4. Copy the full stdout JSON block back to the Claude chat.

### 5.3 — Exit-code interpretation

| Exit | Classification | Interpretation |
|---|---|---|
| 0 | `accepted` | Subscription produced market_data / trade / heartbeat traffic. Gateway-to-api slug bridge is working. Main sweeps (H-015) can use either gateway-sourced or api-sourced slugs per D-025. |
| 1 | `rejected` | Auth error, bad-request, not-found, or error event with no traffic. Surface JSON to Claude — `classification_reason` names the specific SDK exception. |
| 2 | `ambiguous` | Rate-limited, or subscribe sent with no response. Surface to Claude per D-025 commitment 4. |
| 3 | `exception` | Transport or SDK error. Surface JSON to Claude for analysis. |
| 10 | Config error | Missing env vars. Go back to Step 2. |
| 11 | No candidate | You forgot `--slug=`. Re-run with the slug from Step 5.1. |

---

## Step 6 — Report back (at end of provisioning, Step 4)

Report to Claude in chat:

- Service URL (e.g., `https://pm-tennis-stress-test.onrender.com` — may
  or may not be reachable via HTTP; we don't serve HTTP, but Render
  assigns a URL regardless).
- Build success / failure. If failure, paste the last 10 lines of the
  build log.
- Self-check output — the full `=== pm-tennis stress-test self-check ===`
  through `=== self-check complete ===` block from the Logs tab.

Based on the report, H-014 closes out with the service provisioned and
ready for H-015 live-probe execution, OR addresses any deployment issue
that surfaces.

---

## Teardown (after stress-test work completes)

1. Render dashboard → `pm-tennis-stress-test` → **Settings** →
   **Delete Service**. Confirm.
2. No env-var cleanup on `pm-tennis-api` needed (its env vars were
   unchanged by this service's lifecycle).
3. The `src/stress_test/` code remains in the repo for audit and
   potential reuse.

---

*End of Runbook RB-002.*
