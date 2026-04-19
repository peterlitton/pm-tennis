# PM-Tennis Session Handoff — H-006

**Session type:** Injected work package (v3→v4 plan revision) + routine handoff
**Handoff ID:** H-006
**Session start:** 2026-04-18 (following H-005)
**Session end:** 2026-04-18
**Status:** v4 accepted and committed. Phase 2 ready to begin next session.

---

## 1. What this session accomplished

H-006 was an injected plan-revision session. No Phase 2 work was performed. The session produced Build Plan v4 under Playbook §12.

| Item | Status |
|------|--------|
| H-005 handoff accepted | ✅ Complete |
| STATE.md v5 committed (from H-005) | ✅ Confirmed in repo |
| RAID.md updated (from H-005) | ✅ Confirmed in repo |
| Four v4 source artifacts read and reviewed | ✅ Complete |
| Four flags raised and resolved with operator | ✅ Complete |
| Scope confirmation checkpoint (N5) | ✅ Complete — all five items confirmed |
| Decision numbering conflict identified and resolved | ✅ Complete |
| Build Plan v4 drafted, validated, and accepted | ✅ Complete |
| PM-Tennis_Build_Plan_v4.docx committed to repo root | ✅ Confirmed in repo |
| baseline/ folder committed (6 files) | ✅ Confirmed in repo |

---

## 2. Decisions made this session

### D-008: v3→v4 plan revision
**Decision:** Produce v4 of the PM-Tennis Build Plan; premise shift from mispricing-test to instrument-vs-intuition test.
**Motivating evidence:** Baseline analysis of 71 Polymarket iPhone screenshots (502 cash events, 131 resolved tennis contracts excluding STENAP/TRISCH) showing operator ROI of +8.5% overall and +14.3% on swing trades, with effective swing win rate of 55.9% (vs 58.2% breakeven, p=0.697, statistically indistinguishable from breakeven). Analysis performed in an adjacent chat session on 2026-04-18.
**Chain of authorship:** Analysis adjacent → premise shift directed by operator → source artifacts (Premise Brief, Baseline Summary v2, Hypothesis Set v2, Injection Instruction v2) produced adjacent → v4 produced in PM-Tennis session under §12.
**Rationale for v4 rather than v3.x:** Premise-level shift requires one clean reading. Mixing v3's mispricing framing with v4 amendments would burden all downstream phases.
**Commitment:** v4 is the active build plan. v3 is preserved in git history.

### D-009: H3 hypothesis dropped
**Decision:** The hold-strategy rehabilitation hypothesis (H3) is permanently dropped from v4 and all future plan documents.
**Reason:** Operator direction. Not to be raised again.

### D-010: Conviction scoring and exit context ship together at Phase 5
**Decision:** Sections 4.6 (Conviction Scoring) and 4.7 (Exit Context) are parallel instrument features, both shipping at Phase 5. No staged rollout.
**Reason:** Both derived from the same fair-price computation; they serve the same operator-decision moment.

### D-011: Pilot-then-freeze protocol deferred to Phase 7
**Decision:** The pilot-then-freeze protocol for signal_thresholds.json is a Phase 7 decision. v4 notes it as a placeholder. Full specification and formal ID assignment at Phase 7.
**Reason:** Operator comfortable with deferral; no content yet to commit.

### D-012: Decision numbering corrected
**Decision:** The Injection Instruction's references to "D-002 pilot-then-freeze" and "D-003 Sports WS gate" were build-plan internal labels, not canonical RAID/STATE decision IDs. Canonical numbering (D-001 through D-007 per STATE.md) is authoritative. The v3→v4 revision and related decisions are assigned D-008 through D-011 in this session.

---

## 3. Key v4 changes (summary for future sessions)

**Research question:** Shifted from "do mispricings exist?" to "does data-informed decision-making improve the operator's existing trading outcomes?"

**Hypotheses:** Two testable hypotheses replace the prior framework:
- H1 (primary, gating): swing win rate improvement over control (55.9%) + Bayesian posterior P(true rate > 58.2%) ≥ 0.80
- H2 (secondary, informational): swing magnitude ratio improvement from 1.79× baseline to ≥ 2.00×

**Control baseline:** 131 resolved tennis contracts, 8-day window, operator ROI +8.5% overall / +14.3% swing, swing win rate 55.9%. Numbers are authoritative in `baseline/baseline_summary.json`.

**New instrument features:** Section 4.6 (Conviction Scoring) and Section 4.7 (Exit Context), both shipping at Phase 5.

**Position sizing:** Fixed $25 removed. Variable sizing permitted; instrument logs stake + conviction score at each trade.

**Sections preserved verbatim:** 1.5, 2, 4.1–4.5, 5, 6, 8 Phase 1 (already executed), 10, 12, 13.

---

## 4. Files created / modified / deleted this session

| File | Action | Location |
|------|--------|----------|
| PM-Tennis_Build_Plan_v4.docx | Created | repo root |
| baseline/compute_baseline.py | Created | repo |
| baseline/baseline_summary.json | Created | repo |
| baseline/transactions.py | Created | repo |
| baseline/HANDOFF.md | Created | repo |
| baseline/README.md | Created | repo |
| baseline/trading_history.xlsx | Created | repo |

Note: PM-Tennis_Build_Plan_v3.docx was not explicitly deleted from repo (operator could not locate it in the UI). v3 is preserved in git history. v4 is the active plan document.

---

## 5. Repository state at H-006 close

```
peterlitton/pm-tennis
├── .gitignore
├── .python-version
├── README.md
├── DecisionJournal.md
├── Handoff_H-004.md
├── Handoff_H-005.md
├── Orientation.md
├── PM-Tennis_Build_Plan_v4.docx      ← active plan document
├── Playbook.md
├── PreCommitmentRegister.md
├── RAID.md                            ← updated H-005 (I-001 resolved)
├── SECRETS_POLICY.md
├── STATE.md                           ← v5, updated H-005
├── breakeven.json
├── fees.json
├── main.py
├── requirements.txt
├── baseline/
│   ├── HANDOFF.md
│   ├── README.md
│   ├── baseline_summary.json          ← authoritative baseline numbers
│   ├── compute_baseline.py
│   ├── trading_history.xlsx
│   └── transactions.py
├── docs/
│   └── sports_ws_granularity_verification.md
├── runbooks/
│   └── Runbook_GitHub_Render_Setup.md
└── sackmann/
    ├── build_ps_tables.py
    └── fair_price.py
```

---

## 6. Open questions requiring operator input

None blocking for Phase 2.

Carried forward:
- Object storage provider — Phase 4 decision
- Pilot-then-freeze protocol content — Phase 7 decision (D-011)

---

## 7. Pending items for next session

One minor correction to v4 is queued but not yet applied:

**Section 5.6 correction:** The storage layout currently lists `data/baseline/` as a path on the Render persistent disk. This is incorrect — the baseline files live in the repo under `baseline/`, not on the Render disk. This path should be removed from Section 5.6. The correction is minor and can be applied at the start of the next plan-touching session, or batched with any other v4 corrections that emerge. It does not block Phase 2.

---

## 8. Flagged issues / tripwires

**No tripwires fired.**

**Governance note:** The v4 revision was motivated by analysis performed in an adjacent chat session outside PM-Tennis governance. The four source artifacts (Premise Brief, Baseline Summary v2, Hypothesis Set v2, Injection Instruction v2) served as the formal bridge. The DecisionJournal entry for D-008 should document this lineage explicitly. Future sessions should commit a D-008 DecisionJournal entry if one is not already present.

**Baseline arithmetic correction:** The v1 source artifacts contained erroneous swing-subset magnitude figures (+$60 / −$48 / 1.26×). Corrected figures (+$50.63 / −$28.30 / 1.79×) were confirmed by the operator and are the values used in v4. The v2 artifacts reflect the correction. `baseline/baseline_summary.json` is authoritative for any future citation.

---

## 9. Claude self-report

Per Playbook §2.

Four flags raised before drafting: baseline arithmetic inconsistency (caught and corrected); H3 framing gap (resolved by operator dropping H3 entirely); exit-strategy placement (resolved as Section 4.7); D-002 content unavailability (resolved by decision-numbering audit and operator direction to defer).

Decision numbering conflict surfaced and resolved cleanly. The Injection Instruction's internal labels did not match the canonical RAID/STATE IDs; this was identified before drafting and corrected rather than silently applied.

v4 document: 609 paragraphs, validated clean. All scope confirmation items confirmed before drafting began. One minor Section 5.6 correction identified post-acceptance and queued.

**Out-of-protocol events this session:** 0. Cumulative: 0.

---

## 10. Next-action statement

**The next session's first actions are: (1) accept handoff H-006, (2) begin Phase 2 — Discovery and metadata.**

Phase 2 scope: Gamma polling loop for active tennis markets; asset-ID map construction; meta.json writes for each discovered match; discovery-delta stream feeding the capture worker.

The Section 5.6 minor correction can be applied at the start of the Phase 2 session or deferred — operator's call at session open.

---

*End of handoff H-006.*
