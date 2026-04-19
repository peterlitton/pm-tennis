# Runbook RB-002 — Stand up the `pm-tennis-stress-test` Render service

**Produced:** H-013 (2026-04-19)
**Purpose:** operator-executed steps to provision the isolated Render
service that hosts the Phase 3 attempt 2 stress-test code.
**Audience:** operator. No terminal or SSH required; everything is in the
Render web dashboard.
**Time estimate:** 10–15 minutes.

## Why isolated

D-024 commitment 1 and D-020/Q2=(b) require the stress-test code to run on
a **new, separate Render service**, not added to `pm-tennis-api`. This is
the "separate service, torn down after" design. The benefits:

- `pm-tennis-api` discovery loop stays untouched — no risk of breaking
  Phase 2 with Phase 3 code.
- Teardown is trivial: delete the service when H-014 is done.
- Environment variable scope is its own — credentials go on this service,
  not `pm-tennis-api`.

## Preconditions

- [ ] The H-013 bundle has been committed to `main` on GitHub
  (`peterlitton/pm-tennis`). In particular: `src/stress_test/` exists with
  `__init__.py`, `probe.py`, `slug_selector.py`, `requirements.txt`, and
  `README.md`. Check in the GitHub web UI.
- [ ] You still have access to the Polymarket US Key ID and Secret Key
  (from the developer portal). D-023 stored them as Render env vars on
  `pm-tennis-api`; we will add them as **new env vars on the new service**
  — we do not share env vars across services.

## Step 1 — Create the new web service in Render

1. Go to https://dashboard.render.com.
2. Click **New +** → **Web Service**.
3. Connect to the existing GitHub repo `peterlitton/pm-tennis`. (Render
   already has OAuth access from `pm-tennis-api`.)
4. Fill in the service form:
   - **Name:** `pm-tennis-stress-test`
   - **Region:** Oregon (US West) — **same region as `pm-tennis-api`**.
     This is load-bearing: the persistent disk will be shared via Render's
     attached-disk model only if both services are in the same region.
     (See Step 3.)
   - **Branch:** `main`
   - **Runtime:** Python
   - **Build Command:** `pip install -r src/stress_test/requirements.txt`
   - **Start Command:** `python -m src.stress_test.probe`
     - This runs **self-check only** — no network, no probe. It's safe to
       run at boot.
   - **Instance Type:** `Starter` (cheapest). We don't need Standard; the
     probe is ~10 seconds of traffic against one WebSocket.
   - **Auto-Deploy:** **Off** (set to "No" or "Manual").
     - We want explicit control over when the service redeploys during the
       H-014 stress test. Auto-deploy on every push would be noise.
5. Scroll to **Advanced** and set:
   - **Health Check Path:** leave blank / disabled.
     - This is not a long-running web server. It's a CLI that exits after
       self-check. A health check would keep reporting unhealthy.
6. **Do NOT create the service yet.** Stop before clicking "Create Web
   Service". You need to add env vars in the same form before submit, and
   we attach the disk after creation.

## Step 2 — Add environment variables in the same form

In the service form, scroll to **Environment Variables**, add:

| Key | Value |
|---|---|
| `POLYMARKET_US_API_KEY_ID` | (your Key ID from developer portal) |
| `POLYMARKET_US_API_SECRET_KEY` | (your Secret Key from developer portal) |
| `PMTENNIS_DATA_ROOT` | `/data` |

**Important:**

- Type the values directly into the Render form. **Do not paste them into
  the chat with Claude.** Per SECRETS_POLICY §A.6, secret values never
  enter the chat transcript.
- Render masks values by default after save. No "secret toggle" needed
  (confirmed H-011 D-023 subsidiary finding 3).

Now click **Create Web Service**. Render will provision the service and
run the first build. This will take 2–5 minutes.

## Step 3 — Attach the persistent disk (read-only)

The stress-test service needs to read `/data/matches/*/meta.json` from the
same persistent disk `pm-tennis-api` writes to. Render disks are
per-service, so we attach `pm-tennis-api`'s disk to this new service as a
shared read-only mount.

**Check current Render UI for the exact label — this step depends on
Render's disk-sharing offering. If the UI does not expose a
"shared/read-only" option at service-creation time, surface this back to
Claude: we will either need to mount a separate volume with a one-time
copy of meta.json, or adjust the probe to fetch meta.json via the
`pm-tennis-api` service's HTTP API.**

Preferred path if Render supports shared disks:

1. Go to the `pm-tennis-stress-test` service dashboard.
2. Left sidebar → **Disks** → **Add Disk**.
3. Select **existing disk** from `pm-tennis-api`. Mount path: `/data`.
   Access: read-only.
4. Save.
5. Manual deploy to pick up the mount.

**If Render does not support shared disks** (this is the most likely
outcome based on how Render has historically documented its disk model),
stop here and report back in chat. Claude will propose one of:

- **Option A:** run the probe from the `pm-tennis-api` service instead by
  adding a single endpoint to its API that runs the probe on demand. This
  breaks D-024/D-020 isolation and would need a new operator ruling.
- **Option B:** write a small one-shot utility that syncs `meta.json`
  files to object storage (Render managed blob/S3) and have the stress-test
  service read from there. Adds complexity but preserves isolation.
- **Option C:** run the probe **locally** on the `pm-tennis-api` Render
  shell instead, using its already-attached disk. Not ideal from a
  process-isolation standpoint but the lightest-weight path. Would still
  need a ruling.

**Do not pick one of these without a new DJ entry.** Report the Render UI
findings back to Claude.

## Step 4 — Verify first build and self-check

1. After the service reports "Live", open **Logs** in the service
   dashboard.
2. You should see, in order:
   - Build logs ending with `pip install` success and no errors.
   - Start-command log lines beginning with `=== pm-tennis stress-test
     self-check ===`.
   - `[ok] polymarket_us import ok (version: 0.1.2)`
   - `[ok] SDK surfaces AsyncPolymarketUS + exception types importable`
   - `[ok] POLYMARKET_US_API_KEY_ID set`
   - `[ok] POLYMARKET_US_API_SECRET_KEY set`
   - Either:
     - `[ok] N probe candidate(s) eligible; freshest: ...` (if disk is
       attached and populated), or
     - `[warn] 0 probe candidates on disk ...` (if disk is not yet
       attached / shared).
   - `=== self-check complete ===`
3. The service will then **exit 0** because self-check is a CLI that
   finishes. Render will mark it "Live" briefly then restart. **This is
   expected** — the start command is a self-check, not a server. Render
   will keep restarting it; that's fine for now because we will flip the
   start command between self-check and probe manually (Step 5).

**Alternative — set start command to a wait loop so Render stays "Live".**
If the restart churn is noisy in logs, edit the start command to:

```
sh -c "python -m src.stress_test.probe && sleep 86400"
```

That runs self-check once at boot, then sleeps 24h to keep the service
in its "running" state without any further activity. Acceptable workaround.

## Step 5 — How H-014 will execute the probe

**For awareness; not an H-013 action.**

In H-014, when ready to actually run the probe, you will:

1. Open the service dashboard → **Shell** tab (Render provides a shell
   directly in the dashboard for services with `/data` attached).
2. Run: `python -m src.stress_test.probe --probe`.
3. Copy the stdout JSON block back into the Claude chat for the research-doc
   §14 addendum.

No code deploy is needed to run the probe — the code is already on the
service; the CLI flag is the only difference.

## Step 6 — Report back

Report to Claude in chat:

- Service URL (e.g., `https://pm-tennis-stress-test.onrender.com` — may or
  may not be reachable via HTTP; we don't serve HTTP, but Render assigns
  a URL regardless).
- Build success / failure (paste last 10 lines of build log if failure).
- Self-check output — the full `=== pm-tennis stress-test self-check ===`
  block from Logs.
- Disk-attach outcome (did Render expose a shared/read-only option, or
  not).

Based on report, H-013 proceeds to:

- Close out the session with DJ entries, research-doc v5, STATE v11, and
  Handoff_H-013, OR
- Address any deployment issue that surfaces.
