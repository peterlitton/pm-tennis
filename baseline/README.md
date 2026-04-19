# PM-Tennis / baseline

Control dataset for PM-Tennis v4's observation-window comparison. Represents the operator's pre-instrument (intuition-based) trading performance over approximately 8 days ending 2026-04-18.

## Quick start

```bash
cd baseline/
python3 compute_baseline.py
```

This runs the canonical computation and writes `baseline_summary.json` with the authoritative control-period statistics cited in v4 Section 3.5 and the Revised Hypothesis Set.

## What's in here

| File | Purpose |
|------|---------|
| `transactions.py` | Source data. 564 raw transaction tuples transcribed from 71 iPhone screenshots. |
| `compute_baseline.py` | Canonical computation. Run to regenerate `baseline_summary.json`. |
| `baseline_summary.json` | Authoritative output. If documents disagree with this file, the documents are wrong. |
| `HANDOFF.md` | Full methodology, business rules, reconciliation notes, and lineage. **Read this before modifying anything.** |
| `trading_history.xlsx` | Reconciled human-readable spreadsheet view. |
| `trading_dashboard.html` | Interactive dashboard. Optional reference. |

## Critical rules

1. **Lost rows are NOT cash events.** See HANDOFF.md §3.1.
2. **STENAP vs TRISCH is permanently excluded** from all baseline analysis. See HANDOFF.md §4.
3. **The JSON is authoritative.** If a v4 document cites numbers that differ from `baseline_summary.json`, the document is out of date and must be corrected.

## When to re-run

- After any modification to `transactions.py` (new data appended, corrections made)
- Before citing baseline numbers in a new document
- At the start of any session that will write or modify v4 text referencing the control baseline

The computation is deterministic and fast (~1 second).
