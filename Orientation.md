# PM-Tennis — Orientation

This document is the starting point for anyone new to the PM-Tennis project, or for a returning participant who needs to re-orient after a break. It describes what the project is, how it is structured, where everything lives, and how the pieces fit together. It is intentionally stable — it describes structure and purpose, not current status. For current status, read STATE.md. For step-by-step procedures, read Playbook.md.

**If you are a new Claude instance opening this project for the first time in a session:** read this document after the handoff and STATE.md, but before doing any substantive work. This document gives you the project's geography. STATE gives you the current coordinates. The handoff tells you what to do next.

---

## 1. What this project is

PM-Tennis is a data-capture instrument and a trading decision-support system built around a specific thesis about Polymarket US's in-play tennis markets.

**The instrument** records every tick of order-book activity and every score-state change across all active men's and women's singles matches on Polymarket US — ATP main-tour, WTA main-tour, Grand Slams, and Challenger-level — time-synchronized to wall-clock. It runs continuously and unattended on a managed backend service, writing structured archives to persistent storage.

**The trading system** sits on top of the instrument. It computes a running fair-value estimate for each YES contract in each active match, compares that estimate to the observed market price, and surfaces moments when the market appears to have undershot the level that the pre-match consensus plus the score history jointly justify. At those moments, the operator places a passive buy order on the Polymarket US iPhone app and waits for the price to drift toward its fair value.

**The thesis** is that Polymarket US's in-play tennis markets sometimes underreact to score events — either due to liquidity-provider latency, retail flow asymmetry, or reduced attention on low-salience matches — and that in the window before the market closes that gap, a YES contract can be bought below its fair value and sold higher. The observation window (Section 6 below) tests whether this is true in practice.

**What this project is not:** It is not a handicapping operation. It does not predict who will win matches. It does not automate trade execution. All trades are placed manually by the operator on the Polymarket US iPhone app; the system's job is to identify when and where to buy, not to execute.

For the full thesis statement and the fair-price model, read Sections 3 and 4 of the build plan.

---

## 2. The four things that shape everything

Four constraints determine almost every design decision in this project. A reader who internalizes these four will be able to follow the reasoning in every downstream section.

**1. The venue is Polymarket US, not the offshore Polymarket.** Polymarket US (polymarketexchange.com) is the CFTC-regulated exchange. The offshore product (polymarket.com) is entirely out of scope. All fee schedules, market structures, and execution mechanics in this project reference Polymarket US exclusively.

**2. All trading is executed on an iPhone through the Polymarket US app.** The app supports four actions: place a passive buy, place a passive sell, cancel a resting order, and sell at market. There are no stop-loss orders, no conditional triggers, no ability to short. Every position is entered by a resting buy that waits for the market to come to it, and is exited either by a resting sell or by a sell-at-market action. The entire strategy is constrained to what these four actions can express.

**3. The tradeable direction is always long-on-YES-then-exit-higher.** Because the app cannot short, the only profitable setup is: buy a YES contract below fair value, wait for the market to lift it toward fair, sell higher. If a YES contract is overpriced, that is simply no trade.

**4. The fair price combines two inputs in log-odds space.** The pre-match Polymarket US consensus price encodes the players' relative strength. The Sackmann point-by-point archives encode the statistical impact of each score state in tennis. These two inputs are combined in log-odds space to produce a running fair-value estimate that updates with every score event. Section 4 of the build plan develops this in full.

---

## 3. The people and their roles

**The operator** is the project's sole human participant. The operator acts simultaneously as product owner, UAT tester, trader, and custodian of project state between sessions. The operator places all trades manually on the Polymarket US iPhone app; logs every trade action through the dashboard; performs UAT pass/fail on every phase-exit gate; maintains the external accounts the project depends on (Polymarket US, GitHub, Netlify, Render); and preserves and provides handoff documents at session boundaries. The operator does not write code or edit documentation files directly — that is Claude's role.

**Claude** is the sole author of all project code, documentation, tests, diagnostics, and analysis. Claude works across discrete chat sessions with no memory between them. Each session begins from context provided by the operator (handoff document + current files) and ends with a handoff document and updated STATE.md that carry the project forward. Claude's obligations are enumerated in Section 1.5.4 of the build plan.

**The session boundary** is the most important structural fact about how this project operates. Claude retains no state between sessions. Everything that must survive a session boundary must be written down — either in the repository (code and documentation) or in the handoff document (session-specific context). A fact that exists only in a chat transcript is, for practical purposes, lost. The handoff protocol and the session-open self-audit exist specifically to make this constraint manageable.

---

## 4. The file geography

### 4.1 Where things live

The project's canonical assets live in three places:

| Location | What lives there | How accessed |
|----------|-----------------|--------------|
| **GitHub repository** (public) | All source code, documentation, governance files, commitment files, data schemas, runbooks | GitHub web UI; operator uploads files via drag-and-drop; automatic deploys triggered on push |
| **Render** (managed PaaS) | Backend services: capture worker, API, replay simulator, scheduled jobs, persistent data archive | Render web dashboard; deploys from GitHub automatically |
| **Netlify** (static site host) | Frontend: live dashboard, admin UI, trade-entry form | Netlify web dashboard; deploys from GitHub automatically |

Secrets (API keys, account credentials, tokens) never appear in the GitHub repository. They are configured as environment variables in the Render and Netlify web UIs. The repository is public; anything in it is visible to anyone.

### 4.2 Repository layout (target state — populated as phases execute)

```
/                              ← project root
├── STATE.md                   ← cross-session state snapshot (read every session)
├── Orientation.md             ← this document
├── Playbook.md                ← ritual procedures
├── SECRETS_POLICY.md          ← what counts as a secret and where it lives
├── DecisionJournal.md         ← all non-trivial decisions with reasoning
├── RAID.md                    ← risks, assumptions, issues, dependencies
├── PreCommitmentRegister.md   ← pre-committed values with reasoning
├── OBSERVATION_ACTIVE         ← soft lock file; present only during observation window
│
├── src/
│   ├── capture/               ← Gamma poller, CLOB pool, Sports WS client
│   ├── api/                   ← FastAPI endpoints (read-only + trade POST)
│   ├── replay/                ← replay simulator
│   └── dashboard/             ← static frontend (deployed to Netlify)
│
├── data/                      ← persistent archive (on Render disk; backed up nightly)
│   ├── events/                ← raw Gamma poll responses
│   ├── matches/               ← per-match JSONL archives (clob, sports, final)
│   ├── sackmann/              ← P(S) lookup tables and build_log.json
│   ├── overrides/             ← name_aliases.json for correlation overrides
│   ├── fees.json              ← commitment file: Polymarket US fee schedule
│   ├── breakeven.json         ← commitment file: derived breakeven win rate
│   ├── signal_thresholds.json ← commitment file: signal filter values
│   └── index.sqlite           ← match index (WAL mode; cache over JSONL)
│
├── tests/                     ← unit tests and parity test vectors
├── handoffs/                  ← session handoff documents (H-001, H-002, ...)
├── runbooks/                  ← operational runbooks (one per subsystem)
└── docs/                      ← additional reference documentation
```

### 4.3 The governance files and their relationships

Six governance files work together. Understanding how they relate prevents confusion about which one to consult in each situation:

| File | What it is | When to read it |
|------|-----------|-----------------|
| **STATE.md** | Current-state snapshot: phase, session counters, file statuses, commitment-file SHAs, open items | Every session open; any time you need to know where the project is right now |
| **Orientation.md** (this file) | Project map: what everything is and how it fits together | First time in the project; after a long break; when disoriented |
| **Playbook.md** | Step-by-step rituals: exactly what to do in each governed situation | When you are about to perform a specific ritual (session-open, gate-UAT, observation-window-open, etc.) |
| **DecisionJournal.md** | All non-trivial decisions with reasoning; gate verdicts; OOP events | When you need to understand why something is the way it is; at session open as part of the self-audit spot-check |
| **RAID.md** | Risks, assumptions, issues, dependencies — structured log of known unknowns | When assessing what could go wrong; when updating risk or issue status; during phase-exit gates |
| **PreCommitmentRegister.md** | Pre-committed values and their reasoning, with freeze-event tracking | When populating or verifying commitment files; at observation-window open; when the Bayesian pre-commitment discipline needs to be verified |
| **SECRETS_POLICY.md** | What counts as a secret and where it lives | Before any commit; when onboarding a new dependency; when unsure whether something belongs in the repo |

None of these files duplicates another. When you find a conflict between two of them, the authority order is: Playbook wins over procedures described elsewhere; YAML block in STATE wins over STATE prose; DecisionJournal wins over plan document where they describe the same decision; the plan document's Section 1.5.6 reconciliation mapping governs the original plan sections that it identifies as requiring reinterpretation.

---

## 5. The build phases

The project moves through seven build phases, each leaving the system in a working state. Phases are executed in strict order; each depends only on the phases before it.

| Phase | Delivers | Gate condition |
|-------|----------|---------------|
| **Phase 1** | Host/PaaS setup; Sports WS granularity verified (D-003 gate); Sackmann P(S) tables; fees.json; breakeven.json | All commitment files committed; Sports WS gate ruled by operator |
| **Phase 2** | Gamma discovery loop; asset-to-match routing; metadata |  Discovery runs standalone, writing event snapshots |
| **Phase 3** | Full capture: CLOB pool, Sports WS, correlation, envelopes, I/O, handicap capture, retirement handling | Capture runs unattended through at least one recycle; handicap capture verified |
| **Phase 4** | SQLite index; local API; trade logging; backups | All API endpoints responding; trade POST logging to archive |
| **Phase 5** | Public TLS API; Netlify dashboard; live fair-price signal; JS/Python parity guard | Dashboard loads on iPhone via cellular; score event updates fair-price display correctly |
| **Phase 6** | Replay simulator with adverse-selection metric; validated against real fills | Simulator fill-timing agrees with actual fills within 5 seconds on ≥80% of comparable fills |
| **Phase 7** | Monitoring, watchdog, runbooks; simulated-failure test; pilot protocol document | Seven consecutive days unattended; simulated failure triggers alert and recovery; pilot protocol accepted |

After Phase 7, a **pilot phase** calibrates `signal_thresholds.json` against archive data (per D-002). Pilot data is excluded from the observation window. At pilot end, thresholds are frozen, `OBSERVATION_ACTIVE` is created, and the observation window clock starts.

For the full phase specifications including acceptance criteria, read Section 8 of the build plan.

---

## 6. The observation window

The observation window is the falsification test for the thesis. Its design is fixed before it opens; its decision criteria cannot be revised while it runs.

**Duration:** Closes when 250 qualifying signals are recorded OR 60 calendar days elapse, whichever comes first.

**Primary criterion:** Bayesian posterior probability that the true win rate exceeds the `breakeven.json` value. ≥80% posterior → pass. ≤40% → fail. 40%–80% → ambiguous, requiring extension or a follow-up window. Plus six additional conditions including the adverse-selection metric (see PCR-W-002 and PCR-W-003 in the PreCommitmentRegister).

**Secondary criterion:** Actual operator fills and P&L during logged active-coverage windows. Tests whether iPhone-plus-human execution can capture what the simulator says is capturable (see PCR-W-004).

**Decision matrix:** Four outcomes — clear go, ambiguous, primary pass / secondary fail (iPhone can't capture it), fail (thesis falsified or adverse selection). The decision matrix is in Section 9.5 of the build plan. No outcome automatically opens an automation path.

**The soft lock:** While the observation window is open, the file `OBSERVATION_ACTIVE` is present in the repository root. Its presence triggers Claude to refuse any modification to the four commitment files (`fees.json`, `breakeven.json`, `signal_thresholds.json`, `build_log.json`) regardless of the reason and regardless of whether the out-of-protocol phrase is invoked. This is the single unconditional rule in the project.

---

## 7. The session model

Because Claude has no memory between sessions, the project's continuity depends entirely on written artifacts.

**At every session end:** Claude produces a handoff document (`Handoff_H-NNN.md`) and an updated `STATE.md`. The operator saves both. The handoff contains a session summary, files modified, open questions, a self-report, and the next-action statement. STATE contains the structured state snapshot.

**At every session start:** The operator provides the prior handoff (pasted or uploaded). Claude reads the handoff, reads STATE.md, performs the self-audit, and confirms orientation before any substantive work begins. A thin handoff triggers stop-and-surface per Playbook §9.

**Handoff ID sequence:** H-001 was the kickoff session. H-002 was the first governance-scaffolding session. The current handoff ID at any moment is visible in `STATE.md` under `sessions.next_handoff_id`. Gaps in the sequence are detectable and are flagged in the self-audit.

For the full session-open and session-close procedures, read Playbook §1 and Playbook §2.

---

## 8. The governance model

Governance operates on four layers, in ascending order of strength:

**Layer 1 — Session protocol.** The handoff-and-accept ritual ensures context survives session boundaries. A session without a handoff at close, or substantive work before the accept ritual at open, is a protocol violation flagged in the handoff self-report.

**Layer 2 — Gate-blocking language.** Phase-exit gates require explicit operator UAT pass verdicts. Claude does not self-certify gates. A gate cannot be bypassed by proceeding to the next phase without a recorded verdict.

**Layer 3 — Named tripwires.** Specific high-risk situations trigger a hard stop rather than silent adaptation. The tripwires are enumerated in Section 1.5.5 of the build plan and in Playbook §4. When a tripwire fires, Claude stops, surfaces the situation, and waits for operator direction.

**Layer 4 — Operator spot-checks.** Unpredictable cadence checks of governance artifacts: last three DecisionJournal entries, current commitment-file SHAs, STATE diff from prior session. Predictable spot-checks are less effective; the operator should vary timing and focus.

**The out-of-protocol mechanism:** The operator may invoke "out-of-protocol" at the start of a request to suspend the usual full protocol for that specific task. Every invocation is logged to the DecisionJournal and the session handoff self-report. The `OBSERVATION_ACTIVE` soft lock is unconditional and is not overridable by "out-of-protocol."

**Doc-code coupling rule:** Any code change whose behavior is described in project documentation requires a corresponding documentation update in the same commit. A commit that modifies code without updating affected documentation is incomplete.

---

## 9. Key cross-references

When you need to go deeper on any topic, here is where to look:

| Topic | Where to find it |
|-------|-----------------|
| Full thesis and fair-price model | Build plan Sections 3 and 4 |
| iPhone execution mechanics and fee structure | Build plan Section 2 |
| Data architecture, feeds, envelope format, storage layout | Build plan Section 5 |
| System architecture, host, language, containerization | Build plan Section 6 |
| Observation workflow and two-client sync | Build plan Section 7 |
| Phase specifications and acceptance criteria | Build plan Section 8 |
| Observation window design and decision criteria | Build plan Section 9 |
| Scope boundaries (what is and isn't in scope) | Build plan Section 10 |
| Open issues at plan-writing time | Build plan Section 11 |
| Risks and mitigations | Build plan Section 12 (summarized in RAID.md) |
| All decisions with reasoning | DecisionJournal.md |
| All known risks, assumptions, issues, dependencies | RAID.md |
| All pre-committed values and their reasoning | PreCommitmentRegister.md |
| Session rituals step by step | Playbook.md |
| Secrets discipline | SECRETS_POLICY.md |
| Current phase, open items, file status | STATE.md |

---

## 10. What does not belong in this document

Orientation is intentionally **not** the place for:

- Current status (phase, open items, session counters) → STATE.md
- Step-by-step procedures → Playbook.md
- Reasoning for specific decisions → DecisionJournal.md
- Risk and issue tracking → RAID.md
- Specific committed values → PreCommitmentRegister.md
- Secrets handling → SECRETS_POLICY.md
- Code, schemas, or data formats → source files and build plan Section 5

If you find yourself wanting to update Orientation to reflect a current-state change (e.g., "we are now in Phase 3"), stop: that belongs in STATE.md, not here. Orientation is updated only when the project's structure changes — a new governance file is added, the deployment model changes, a section becomes obsolete.

---

*End of Orientation.md — v1, H-003.*
