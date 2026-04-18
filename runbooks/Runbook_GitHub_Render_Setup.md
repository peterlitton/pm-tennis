PM-Tennis — Runbook: GitHub Repository & Render Backend Setup
Runbook ID: RB-001  
Version: 1.0  
Produced session: H-004  
Status: Active  
Operator-executable: Yes — all steps are web-UI only; no terminal required  
Estimated time: 45–75 minutes total (split across two platforms, can pause between sections)
---
Purpose
This runbook guides the operator through creating the PM-Tennis GitHub repository, committing the existing governance scaffolding files, provisioning a Render backend service, connecting it to the repository, and verifying that the service is reachable. At the end of this runbook the project will have:
A public GitHub repository with all scaffolding files committed
A Render backend service connected to that repository, building on every push
A live `/healthcheck` endpoint (placeholder, extended in Phase 4) confirming the service is up
All environment variables in place for future phases
This runbook does not begin Phase 1 technical work (Sackmann pipeline, WebSocket capture, etc.). It is infrastructure only. Phase 1 begins in the session after this runbook is successfully executed.
---
Prerequisites — verify before starting
Item	Required state	How to check
GitHub account	Exists, logged in	Can reach github.com/[your-username]
Render account	Does not need to exist yet	Will be created in Section 3
Local files	All 7 scaffolding files saved	See Section 1.1
Internet connection	Active	Obvious
Time available	~45–75 minutes uninterrupted	Prefer not to split mid-section
1.1 — Scaffolding files checklist
Before starting, confirm you have all 7 of these files saved locally (downloaded from prior Claude sessions):
[ ] `STATE.md`
[ ] `Orientation.md`
[ ] `Playbook.md`
[ ] `SECRETS_POLICY.md`
[ ] `DecisionJournal.md`
[ ] `RAID.md`
[ ] `PreCommitmentRegister.md`
Plus the build plan, which you have access to through the project. The build plan does not need to be committed to the repo at this stage — it lives in project knowledge.
Also, Claude will produce two new files during this runbook session that also need to be committed:
[ ] This runbook file (`Runbook_GitHub_Render_Setup.md`) — produced by Claude in H-004
[ ] `Handoff_H-004.md` — produced by Claude at session close
[ ] `STATE.md` (v4) — updated version produced by Claude at session close
These last three will be committed after they are produced.
---
Section 1 — Create the GitHub Repository
Time estimate: 10–15 minutes  
Platform: github.com
Step 1.1 — Create the repository
Go to github.com and sign in.
Click the + icon in the top-right corner → New repository.
Fill in the form:
Repository name: `pm-tennis`
Description: `Polymarket US in-play tennis moneyline instrument and trading system`
Visibility: Public (per D-005 — public because no secrets will ever be in the repo; secrets live in platform environment variables per SECRETS_POLICY.md)
Initialize this repository with: check Add a README file
Add .gitignore: choose Python from the dropdown
Choose a license: None (leave as None — this is a personal project)
Click Create repository.
What you should see: A new repository page at `github.com/[your-username]/pm-tennis` with a single commit containing `README.md` and `.gitignore`.
Report back: The repository URL (e.g., `https://github.com/yourusername/pm-tennis`).
---
Step 1.2 — Update the README
The auto-generated README is a placeholder. Replace it with something minimal and accurate.
On the repository page, click on `README.md`.
Click the pencil icon (Edit this file) in the top-right of the file view.
Replace all content with the following:
```
# PM-Tennis

Polymarket US in-play tennis moneyline mispricing instrument and trading system.

This repository contains the capture engine, API, replay simulator, and operator dashboard
for the PM-Tennis project. See the project build plan for full specification.

**Status:** Pre-build — infrastructure setup in progress.
```
Scroll down to the Commit changes section.
In the commit message field, type: `docs: initialize README`
Leave "Commit directly to the `main` branch" selected.
Click Commit changes.
---
Step 1.3 — Create the folder structure
GitHub does not allow creating empty folders directly. We create the structure by uploading files into the correct paths. The folder structure we need now:
```
pm-tennis/
├── README.md               (already exists)
├── .gitignore              (already exists)
├── STATE.md
├── Orientation.md
├── Playbook.md
├── SECRETS_POLICY.md
├── DecisionJournal.md
├── RAID.md
├── PreCommitmentRegister.md
├── runbooks/
│   └── Runbook_GitHub_Render_Setup.md   (this file)
└── data/                   (created later in Phase 1)
```
We commit the scaffolding files in two batches. GitHub's browser interface allows uploading multiple files at once.
---
Step 1.4 — Commit the scaffolding files (Batch 1: root-level governance files)
On the repository main page (`github.com/[your-username]/pm-tennis`), click Add file → Upload files.
Drag all 7 of the following files into the upload area, or use the file picker:
`STATE.md`
`Orientation.md`
`Playbook.md`
`SECRETS_POLICY.md`
`DecisionJournal.md`
`RAID.md`
`PreCommitmentRegister.md`
In the commit message at the bottom, type:
`docs: add governance scaffolding layer (H-001 through H-003)`
In the extended description (optional box below the message), type:
`STATE.md v3, Orientation.md v1, Playbook.md v1, SECRETS_POLICY.md v1, DecisionJournal.md v1 (formal rebuild), RAID.md v1 (32 entries), PreCommitmentRegister.md v1 (31 entries)`
Leave "Commit directly to the `main` branch" selected.
Click Commit changes.
What you should see: The repository page now shows all 7 files listed alongside README.md and .gitignore.
---
Step 1.5 — Commit the runbook (Batch 2: runbooks folder)
This step commits this runbook file into a `runbooks/` subfolder.
On the repository main page, click Add file → Upload files.
Before dragging the file, GitHub needs to know you want it inside a folder. The browser uploader does not let you specify a path for drag-and-drop. Use this workaround:
Instead of drag-and-drop, click choose your files in the upload area.
This opens your OS file picker. Navigate to and select `Runbook_GitHub_Render_Setup.md`.
After selecting it, you'll see the file listed in the upload area.
In the commit message, type:
`docs: add RB-001 GitHub + Render setup runbook`
Click Commit changes.
Note: GitHub's browser uploader places the file in the root. To move it to `runbooks/`, we'll use the in-browser file editor:
After committing, click on `Runbook_GitHub_Render_Setup.md` to open it.
Click the pencil icon to edit.
At the top of the edit view, you'll see the filename in an editable path bar. Click on the filename portion and change it to `runbooks/Runbook_GitHub_Render_Setup.md` (type the folder name and a `/` before the filename — GitHub will automatically create the `runbooks/` folder).
Scroll to the bottom, commit message: `refactor: move runbook into runbooks/ folder`
Commit to main.
What you should see: A `runbooks/` folder in the repository containing `Runbook_GitHub_Render_Setup.md`.
---
Step 1.6 — Verify repository state
After both commit batches, the repository root should contain:
```
.gitignore
README.md
DecisionJournal.md
Orientation.md
Playbook.md
PreCommitmentRegister.md
RAID.md
SECRETS_POLICY.md
STATE.md
runbooks/
  Runbook_GitHub_Render_Setup.md
```
Check: Click on each of the 7 governance files and confirm the content is what you expect (spot-check a few lines). If any file shows garbled content or is unexpectedly empty, it needs to be re-uploaded.
Report back: Confirm the file list matches. Note the URL of the repository and the commit hash of the most recent commit (visible in the repository's commit history — click the clock/commits icon).
---
Section 2 — Create the Render Backend Service
Time estimate: 20–30 minutes  
Platform: render.com  
Depends on: Section 1 complete
Step 2.1 — Create a Render account
Go to render.com.
Click Get Started for Free or Sign In if you already have an account.
Sign up using your GitHub account — click GitHub as the sign-up method. This is important: connecting Render to GitHub via OAuth now makes the repository-linking step in 2.3 much simpler.
Authorise Render to access your GitHub account when prompted.
You should land on the Render dashboard at `dashboard.render.com`.
Report back: Confirm you're logged into the Render dashboard.
---
Step 2.2 — Understand what we're creating on Render
Before clicking anything, here is what we're setting up and why:
Service type	What it is	Why we need it
Web Service	An always-on HTTP server	Hosts the API (Phase 4), the `/healthcheck` endpoint, and eventually the trade-logging POST endpoint
Background Worker	An always-on process with no HTTP port	Hosts the capture engine (Phase 3) — polls Gamma, maintains WebSocket connections, writes JSONL archive
Persistent Disk	Attached storage that survives deploys	Holds the JSONL archive and SQLite index — critical, must not be ephemeral
Cron Jobs	Scheduled tasks	Nightly gzip, backup sync, commitment-file checksum (Phase 4)
In this session we create the Web Service only, with a placeholder application that serves `/healthcheck`. The Background Worker and Cron Jobs are added in Phase 3 and Phase 4 respectively.
The Persistent Disk is attached to the Web Service for now and will be shared with the Background Worker when it is added. The disk is the most important cost item — Render charges for persistent disk separately from compute.
---
Step 2.3 — Create the Web Service
In the Render dashboard, click New + → Web Service.
On the "Create a new Web Service" screen, choose Build and deploy from a Git repository.
Click Connect next to your GitHub account (it should already be authorised from Step 2.1).
Find and select your `pm-tennis` repository from the list.
Click Connect.
---
Step 2.4 — Configure the Web Service
You'll see a configuration form. Fill it in as follows:
Field	Value	Notes
Name	`pm-tennis-api`	This becomes part of the service URL
Region	`Oregon (US West)`	Closest to Polymarket's US-centric infrastructure; see note below
Branch	`main`	
Root Directory	(leave blank)	We'll set this when Phase 3 code exists
Runtime	`Python 3`	
Build Command	`pip install fastapi uvicorn`	Minimal placeholder; replaced in Phase 4
Start Command	`uvicorn main:app --host 0.0.0.0 --port $PORT`	Render injects $PORT
Instance Type	`Starter` ($7/month)	Sufficient for now; upgrade path available
Region note: Render offers US Oregon, US Ohio, EU Frankfurt, and Singapore. Oregon (US West) is the default and is adequate — Polymarket's endpoints are Cloudflare-anycast so edge proximity follows the client connection, not the origin datacenter. This is pre-committed as assumption A-001 in the RAID; actual latency will be measured in Phase 1.
Scroll down to Advanced settings and expand it.
---
Step 2.5 — Add environment variables
Still on the configuration form, in the Environment Variables section, add the following variables now. These are placeholders — the actual secrets are added in Phase 4 when the relevant subsystems are built. Setting the variable names now means the service knows what to expect.
Click Add Environment Variable for each:
Key	Value	Notes
`PM_TENNIS_TOKEN`	`placeholder-replace-in-phase-4`	The shared-secret for the trade-logging POST endpoint. Replace with a real random string before Phase 5.
`ENVIRONMENT`	`development`	Changes to `production` when observation window opens
`LOG_LEVEL`	`INFO`	
Important: Do not paste API keys, Polymarket credentials, or any other real secrets here. The `PM_TENNIS_TOKEN` placeholder is intentionally non-secret for now. Per SECRETS_POLICY.md, the real token is generated and set in Phase 5, not now.
---
Step 2.6 — Add a Persistent Disk
Still in Advanced settings, find the Disks section.
Click Add Disk:
Field	Value	Notes
Name	`pm-tennis-data`	
Mount Path	`/data`	This is where the JSONL archive will live
Size	`10 GB`	Sufficient for the observation window; upgrade path available. 10 GB at Render's pricing is ~$1.25/month
Click Add.
---
Step 2.7 — Create a placeholder application
Before clicking "Create Web Service," we need to ensure the repository has a `main.py` file that Render can actually run. Without it, the first deploy will fail.
Do this before clicking Create:
Open a new browser tab to your GitHub repository (`github.com/[your-username]/pm-tennis`).
Click Add file → Create new file.
Name the file `main.py`.
Paste the following content:
```python
"""
PM-Tennis API — placeholder.
This file is the minimal FastAPI application deployed to Render.
It will be replaced with the full API in Phase 4.
"""

from fastapi import FastAPI
import os
import datetime

app = FastAPI(title="PM-Tennis API", version="0.0.1-placeholder")


@app.get("/healthcheck")
def healthcheck():
    return {
        "status": "ok",
        "service": "pm-tennis-api",
        "version": "0.0.1-placeholder",
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "note": "Placeholder application. Phase 4 will replace this with the full API."
    }


@app.get("/")
def root():
    return {"service": "pm-tennis-api", "status": "placeholder"}
```
Commit message: `feat: add placeholder FastAPI app for Render deploy`
Commit to main.
---
Step 2.8 — Create the Web Service (final click)
Go back to the Render tab with the configuration form.
Review your settings one final time:
Name: `pm-tennis-api`
Region: Oregon
Runtime: Python 3
Build Command: `pip install fastapi uvicorn`
Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
Instance Type: Starter
Environment variables: 3 added
Disk: `pm-tennis-data` at `/data`, 10 GB
Click Create Web Service.
---
Step 2.9 — Watch the first deploy
Render will immediately start building and deploying. You'll see a log stream on the service page.
What a successful deploy looks like:
```
==> Cloning from https://github.com/[your-username]/pm-tennis...
==> Checking out commit [hash] for branch main
==> Running build command: pip install fastapi uvicorn
Successfully installed fastapi uvicorn ...
==> Build successful
==> Starting service with: uvicorn main:app --host 0.0.0.0 --port $PORT
INFO: Started server process
INFO: Waiting for application startup.
INFO: Application startup complete.
INFO: Uvicorn running on http://0.0.0.0:[PORT]
```
The status badge in the top of the page should change from Deploying to Live (green).
What to do if it fails: Look at the log for the error line. The most common first-deploy failures are:
`ModuleNotFoundError: No module named 'fastapi'` — the build command didn't run. Check spelling of build command.
`main:app — not found` — the `main.py` file wasn't committed or was committed to a subfolder. Check repository file list.
Report back: The URL Render assigned to your service. It will look like `https://pm-tennis-api.onrender.com` (Render assigns a subdomain based on your service name).
---
Step 2.10 — Verify the healthcheck endpoint
Once the deploy shows Live:
Open a new browser tab.
Navigate to: `https://[your-service-url]/healthcheck`
(e.g., `https://pm-tennis-api.onrender.com/healthcheck`)
You should see a JSON response like:
```json
{
  "status": "ok",
  "service": "pm-tennis-api",
  "version": "0.0.1-placeholder",
  "environment": "development",
  "timestamp": "2026-04-18T18:32:00Z",
  "note": "Placeholder application. Phase 4 will replace this with the full API."
}
```
Also verify on your phone: open the URL in Safari or Chrome on the iPhone you'll use for trading. If it loads, the service is reachable from your trading device.
Report back: Screenshot or paste the JSON response. Confirm it loaded on iPhone.
---
Section 3 — Connect Render Auto-Deploy
Time estimate: 5 minutes  
Platform: render.com  
Depends on: Sections 1 and 2 complete
Render's GitHub integration triggers an automatic redeploy every time you push a commit to the `main` branch. This is already active from the moment you created the service in Step 2.3. Verify it:
Step 3.1 — Verify auto-deploy is active
In the Render dashboard, click on `pm-tennis-api`.
Click the Settings tab.
Scroll to the Build & Deploy section.
Confirm Auto-Deploy shows "Yes" and Branch shows "main".
If auto-deploy shows "No" or is missing, click to enable it and select "main" as the branch.
Step 3.2 — Test auto-deploy with a trivial commit
Go to your GitHub repository.
Click on `README.md` → edit (pencil icon).
Add a blank line at the end of the file.
Commit message: `chore: trigger auto-deploy verification`
Commit to main.
Go back to Render → your service page → Events tab.
You should see a new deploy triggered within 30 seconds.
It should complete and show Live again within 2–3 minutes.
Report back: Confirm the auto-deploy event appeared in Render's Events tab.
---
Section 4 — Commit Final H-004 Artifacts
Time estimate: 5–10 minutes  
Depends on: All prior sections complete, and Claude has produced H-004 closing artifacts
After the interactive walkthrough is complete, Claude will produce:
`Handoff_H-004.md`
`STATE.md` (v4)
These are committed to GitHub as the final step of H-004.
Step 4.1 — Commit session-close artifacts
On the repository main page, click Add file → Upload files.
Upload:
`Handoff_H-004.md`
`STATE.md` (v4 — the updated version, replacing v3)
Commit message: `docs: H-004 session close — Handoff_H-004 and STATE v4`
Commit to main.
What you should see: The `STATE.md` in the repository has been replaced with the v4 version, and `Handoff_H-004.md` appears in the root.
---
Post-Runbook Verification Checklist
Once all four sections are complete, verify this full checklist before declaring the runbook done:
Item	Expected state	Verified
GitHub repository exists	`github.com/[your-username]/pm-tennis`	[ ]
Repository is public	Visible without login	[ ]
All 7 governance files committed	STATE, Orientation, Playbook, SECRETS_POLICY, DecisionJournal, RAID, PreCommitmentRegister	[ ]
Runbook committed in `runbooks/` folder	`runbooks/Runbook_GitHub_Render_Setup.md`	[ ]
`main.py` placeholder committed	Exists at repo root	[ ]
Render service exists	`pm-tennis-api` in Render dashboard	[ ]
Render service status is Live	Green badge	[ ]
`/healthcheck` returns JSON	Status "ok" in browser	[ ]
`/healthcheck` loads on iPhone	Confirmed on trading device	[ ]
Persistent disk attached	`pm-tennis-data` at `/data`, 10 GB	[ ]
Auto-deploy active	Test commit triggered a deploy	[ ]
Handoff_H-004.md committed	In repo root	[ ]
STATE.md v4 committed	In repo root, replaces v3	[ ]
---
Decisions and assumptions recorded in this runbook
Item	Value	Rationale	Record
Repository visibility	Public	D-005	DecisionJournal
Render region	Oregon (US West)	Closest US region; Polymarket is anycast so latency not critical	RAID A-001
Persistent disk size	10 GB	Sufficient for observation window; ~1.25/month	Phase 1 assumption
Initial instance type	Starter ($7/month)	Adequate for placeholder; upgrade in Phase 3 if needed	Phase 1 assumption
PM_TENNIS_TOKEN	Placeholder only	Real token generated in Phase 5 per SECRETS_POLICY	SECRETS_POLICY
---
End of Runbook RB-001 — GitHub + Render Setup  
Produced: H-004 | Author: Claude | Operator-executable: Yes
