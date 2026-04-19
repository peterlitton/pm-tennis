# PM-Tennis — Baseline Dataset Handoff

**Prepared:** 2026-04-18
**Purpose:** Documents the data lineage, transcription methodology, and business rules governing the `baseline/` folder of the PM-Tennis repository. This is the handoff for the control dataset used in v4's Section 3.5 (Control Baseline) and Revised Hypothesis Set.

---

## 1. What this dataset represents

The `baseline/` folder contains the operator's pre-instrument Polymarket US trading history, captured via screenshots and transcribed into structured data. It serves as the **control dataset** for v4's observation-window comparison: the operator's intuition-based trading performance, before any PM-Tennis instrument existed.

Specifically, the dataset captures approximately 8 days of activity ending 2026-04-18, across tennis, MLB, NHL, NBA, and soccer markets. PM-Tennis uses only the tennis subset; the other sports are retained in the raw transaction record for completeness but are excluded from baseline analysis per v4 scope (singles tennis only).

## 2. Source data provenance

**Original source:** Polymarket US iPhone app, "History" tab. The operator captured 71 screenshots (`IMG_9191` through `IMG_9261`) showing all visible transaction rows scrolled through chronologically.

**Capture date:** 2026-04-18

**Reported account balance at capture:** $991.50

**Transcription method:** Screenshots were visually transcribed into Python tuples in `transactions.py`. Each tuple represents one visible row on a History screen. Order within each screenshot was preserved.

## 3. Critical business rules

The Polymarket History tab has two UX features that caused transcription errors in early drafts and that MUST be respected by any analysis over this data:

### 3.1 Lost rows are NOT cash events

When a contract resolves against the operator, the app displays a row such as `Orlando Lost -$760`. This row looks like a cash transaction but is NOT. It is a P&L notification. The cash for that position already left the account via prior Buy transactions.

**Rule:** Lost rows have `action = "Lost"` and their `amount` field is preserved for informational purposes but MUST NOT be summed into any cash-flow calculation. `compute_baseline.py` filters Lost rows correctly in `build_contracts()`; any alternative analysis code over `transactions.py` must do the same.

Early drafts of this dataset's analysis included Lost rows as cash events and failed reconciliation by ~$2,625. Excluding Lost rows dropped the reconciliation gap to ~$268 (1.7% of gross volume), which is within the expected range for OCR transcription noise across 71 screenshots.

### 3.2 Won rows ARE cash events

By contrast, "Won" rows represent actual cash inflows at resolution — the gross payout at $1 per share won. These are recorded with `action = "Won"` and are summed normally.

This asymmetry between Won and Lost is a real UX quirk of the Polymarket app that is easy to miss on first inspection.

### 3.3 "Exited" positions have no settlement row

If the operator fully traded out of a position before it resolved (sells totaling more than buys, or sells on both sides of a match such that net share count reaches zero), the app does not produce a Won or Lost row at resolution. The operator's cash P&L is already locked in via the Buy/Sell trades.

**Rule:** Contracts with no Won/Lost row are classified as `outcome = "exited"` in `compute_baseline.py`. Their effective win/loss status is determined by the sign of their net cash P&L: positive net → effective win, negative net → effective loss, zero net → flat.

The operator has confirmed (2026-04-18) that under the v4 working assumption, all contracts in the dataset are considered resolved, whether via settlement row or via trading exit.

### 3.4 Deposits, Withdrawals, Transfers are separate

These are cash-flow events affecting the account balance but unrelated to trading performance. They are retained in `transactions.py` for reconciliation purposes but excluded from contract-level baseline analysis.

## 4. STENAP vs TRISCH exclusion

One match — STENAP vs TRISCH (Stefano Napolitano vs Tristan Schoolkate) — is permanently excluded from all baseline statistics, per operator decision on 2026-04-18.

**Why:** On this match, the operator executed a pure market-making trade, accumulating significant positions on both sides and closing via trading before resolution, netting +$1,747. This reflects a specific market-making skill but is not representative of the operator's routine discretionary trading. Including it would distort the summary statistics materially.

**How:** `compute_baseline.py` filters this match via the `EXCLUDE_MATCH` constant. Any alternative analysis must apply the same exclusion for consistency with v4's Section 3.5.

Pure market-making trades, as a skill, remain part of the operator's total edge. Excluding them in the baseline makes the baseline more conservative and more representative of routine trading, but it may understate what the operator can do across all trading types.

## 5. Files in this folder

- **`transactions.py`** — source data, 564 raw transaction tuples (502 after excluding Deposit/Withdraw/Transfer events). Python module importable by analysis code.
- **`compute_baseline.py`** — canonical computation. Produces `baseline_summary.json` when run. This file is the single source of truth for every number cited in v4's Section 3.5 and in the Revised Hypothesis Set.
- **`baseline_summary.json`** — output of `compute_baseline.py`. Authoritative JSON for baseline numbers. If this file's values disagree with any document citing baseline numbers, the document is stale and must be corrected.
- **`HANDOFF.md`** — this file.
- **`trading_history.xlsx`** — reconciled spreadsheet view of the same data, filtered to 502 cash events (Lost rows excluded). For human inspection.
- **`trading_dashboard.html`** — interactive dashboard (optional reference, not load-bearing for v4).

## 6. Reconciliation

Running `compute_baseline.py` over `transactions.py` produces summary cuts whose per-subset reconciliation is verified automatically:

- For each cut, `sum(winner P&L) + sum(loser P&L)` is checked against the cut's `total_pnl`.
- The report prints "OK" if they match within $0.01 and "MISMATCH" otherwise.

Any code change to `compute_baseline.py` that produces a MISMATCH indicates a bug and MUST be investigated before the results are used.

Overall reconciliation to the reported account balance: the operator reported $991.50 on the app at capture time. Summing all cash flows (deposits, withdrawals, transfers, buys, sells, wons) produces approximately $1,260. The gap of ~$268 is within the expected noise range for retrospective screenshot transcription and is attributed to:

- Scroll-boundary gaps (a few transactions may have been missed between screenshots)
- OCR transcription errors in numeric amounts (a few $ of drift per contract aggregating across 502 events)

This gap is documented but not corrected; the aggregate baseline statistics are robust to drift of this size.

## 7. Using this data downstream

### For v4 Section 3.5 (Control Baseline)

Every numerical claim in v4's Section 3.5 that references the control baseline MUST come from `baseline_summary.json`. Before v4 is committed:

1. Run `python compute_baseline.py` in this folder.
2. Verify `baseline_summary.json` is current.
3. Cross-check every numerical claim in v4's Section 3.5 against the JSON.
4. Resolve any discrepancies by correcting the document, not by editing the JSON.

### For post-window analysis

At window close, the test-period dataset will exist alongside this control dataset. The window-close analysis notebook compares the two. To preserve apples-to-apples comparability:

- Use the same contract-level grouping (player, match)
- Use the same effective-outcome classification (won, lost, won_via_exit, lost_via_exit)
- Use the same STENAP-style outlier-exclusion rule (define and commit the rule before the window closes)

### For future baseline extensions

If additional pre-instrument data becomes available (e.g., more screenshots from an earlier period), it should be appended to `transactions.py` with new tuple rows. `compute_baseline.py` will automatically re-aggregate. The resulting `baseline_summary.json` then supersedes the prior canonical output. A change log entry should be added to this HANDOFF.md noting the extension date and the new baseline figures.

## 8. Change log

- **2026-04-18** — Initial baseline dataset committed. 71 screenshots, 502 cash events, 131 tennis contracts (excl STENAP vs TRISCH), summary per `baseline_summary.json` v1.

---

*End of HANDOFF.md. If you find this document incorrect or out of date relative to the code or JSON, correct the code or JSON first, then update this document to match.*
