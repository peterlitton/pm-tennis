"""
PM-Tennis — Canonical Baseline Computation
===========================================

This module is the single source of truth for every baseline number cited
anywhere in PM-Tennis documentation (including v4's Section 3.5 Control
Baseline and the Revised Hypothesis Set artifact).

Any numerical claim about the operator's pre-instrument discretionary
trading performance MUST be derivable from running this file. If a
document cites a number that differs from this file's output, the
document is wrong and must be corrected. This file is authoritative.

Usage
-----

    $ python compute_baseline.py

Produces `baseline_summary.json` in the current directory with the
canonical summary. Running the file also prints a human-readable report
to stdout.

Data source
-----------

Reads `transactions.py` (sibling file), which contains the full 502-cash-event
transcription of 71 iPhone screenshots of the operator's Polymarket US History
tab, captured 2026-04-18. The transcription methodology and business rules are
documented in `HANDOFF.md`.

Scope
-----

Output numbers apply to:
- Tennis only
- STENAP vs TRISCH permanently excluded (pure market-making outlier,
  not representative of discretionary trading; operator-directed)
- All trades within the 50% taker-fee rebate promo window through
  2026-04-30 (fee-net against `breakeven.json` threshold of 58.2%)

Verification history
--------------------

- 2026-04-18: Initial version. Verified against trading_history.xlsx
  reconciliation (reconciles to ~1.7% of gross volume).
"""

import sys
import json
import math
from collections import defaultdict

# Constants ---------------------------------------------------------------
EXCLUDE_MATCH = "STENAP vs TRISCH"
BREAKEVEN_THRESHOLD = 0.582  # from PM-Tennis breakeven.json, committed in H-005
TENNIS = "Tennis"


# Core functions ----------------------------------------------------------

def load_transactions():
    """Load transaction records from sibling transactions.py module."""
    from transactions import transactions
    return transactions


def build_contracts(transactions, sport=TENNIS, exclude_match=EXCLUDE_MATCH):
    """Group individual transactions into per-contract records.

    A contract is a (player, match) tuple. Each contract aggregates all
    Buy, Sell, Won, and Lost events for that player in that match.

    Returns a list of dicts, one per contract.
    """
    contracts = defaultdict(lambda: {
        "event": None, "player": None, "match": None,
        "n_buys": 0, "n_sells": 0,
        "buy": 0.0, "sell": 0.0, "won": 0.0,
        "has_won": False, "has_lost": False,
    })
    for t in transactions:
        # Transaction tuple: (img, idx, event, txn_type, player, match, action, amount, reltime)
        img, idx, event, txn_type, player, match, action, amount, reltime = t
        if txn_type in ("Deposit", "Withdraw", "Transfer"):
            continue
        if event != sport:
            continue
        if not match:
            continue
        if match == exclude_match:
            continue
        c = contracts[(player, match)]
        c["event"] = event
        c["player"] = player
        c["match"] = match
        if action == "Buy":
            c["n_buys"] += 1
            c["buy"] += amount
        elif action == "Sell":
            c["n_sells"] += 1
            c["sell"] += amount
        elif action == "Won":
            c["won"] += amount
            c["has_won"] = True
        elif action == "Lost":
            c["has_lost"] = True

    # Compute derived fields for each contract
    records = []
    for key, c in contracts.items():
        net = c["buy"] + c["sell"] + c["won"]
        cost = -c["buy"]

        # Determine effective outcome
        if c["has_won"]:
            outcome = "won"
        elif c["has_lost"]:
            outcome = "lost"
        elif net > 0:
            outcome = "won_via_exit"
        elif net < 0:
            outcome = "lost_via_exit"
        else:
            outcome = "flat"

        # Effective win/loss for win-rate calculation
        if outcome in ("won", "won_via_exit"):
            effective = "win"
        elif outcome in ("lost", "lost_via_exit"):
            effective = "loss"
        else:
            effective = "flat"

        records.append({
            "player": c["player"],
            "match": c["match"],
            "event": c["event"],
            "n_buys": c["n_buys"],
            "n_sells": c["n_sells"],
            "buy_gross": round(c["buy"], 2),
            "sell_gross": round(c["sell"], 2),
            "won_gross": round(c["won"], 2),
            "net_pnl": round(net, 2),
            "cost_basis": round(cost, 2),
            "outcome": outcome,
            "effective": effective,
            "strategy": "swing" if c["n_sells"] > 0 else "hold",
        })

    return records


def binom_p_ge(k, n, p):
    """Upper-tail probability P(X >= k) under Binomial(n, p)."""
    if n == 0:
        return None
    return sum(
        math.comb(n, i) * (p**i) * ((1 - p)**(n - i))
        for i in range(k, n + 1)
    )


def pearson_correlation(xs, ys):
    """Pearson correlation coefficient."""
    n = len(xs)
    if n == 0:
        return 0.0
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return num / (dx * dy) if dx * dy > 0 else 0.0


def percentile(arr, p):
    """Linear-interpolated percentile."""
    arr = sorted(arr)
    if not arr:
        return 0
    k = (len(arr) - 1) * p
    f = int(k)
    c = min(int(k) + 1, len(arr) - 1)
    return arr[f] + (arr[c] - arr[f]) * (k - f)


def summarize_subset(label, records, threshold=BREAKEVEN_THRESHOLD):
    """Produce a canonical summary for a subset of contract records."""
    n = len(records)
    if n == 0:
        return None

    wins = [r for r in records if r["effective"] == "win"]
    losses = [r for r in records if r["effective"] == "loss"]
    flats = [r for r in records if r["effective"] == "flat"]
    n_wins = len(wins)
    n_losses = len(losses)
    n_flats = len(flats)
    decided = n_wins + n_losses

    total_wagered = sum(r["cost_basis"] for r in records)
    total_pnl = sum(r["net_pnl"] for r in records)

    winner_pnls = [r["net_pnl"] for r in wins]
    loser_pnls = [r["net_pnl"] for r in losses]
    sum_winner_pnl = sum(winner_pnls)
    sum_loser_pnl = sum(loser_pnls)
    mean_winner = sum_winner_pnl / n_wins if n_wins else 0.0
    mean_loser = sum_loser_pnl / n_losses if n_losses else 0.0
    magnitude_ratio = (
        abs(mean_winner) / abs(mean_loser) if mean_loser != 0 else None
    )

    win_rate = n_wins / decided if decided > 0 else 0.0
    roi = total_pnl / total_wagered if total_wagered > 0 else 0.0
    p_value = binom_p_ge(n_wins, decided, threshold) if decided > 0 else None

    return {
        "label": label,
        "n_contracts": n,
        "n_wins": n_wins,
        "n_losses": n_losses,
        "n_flats": n_flats,
        "win_rate": round(win_rate, 4),
        "win_rate_vs_breakeven_pp": round((win_rate - threshold) * 100, 2),
        "total_wagered": round(total_wagered, 2),
        "total_pnl": round(total_pnl, 2),
        "roi": round(roi, 4),
        "mean_winner": round(mean_winner, 2),
        "mean_loser": round(mean_loser, 2),
        "magnitude_ratio": round(magnitude_ratio, 3) if magnitude_ratio else None,
        "sum_winner_pnl": round(sum_winner_pnl, 2),
        "sum_loser_pnl": round(sum_loser_pnl, 2),
        "reconciles": round(sum_winner_pnl + sum_loser_pnl, 2),  # should equal total_pnl
        "binomial_p_value_vs_breakeven": (
            round(p_value, 4) if p_value is not None else None
        ),
    }


def compute_sizing_buckets(records):
    """Bucket contracts by cost basis and summarize each bucket."""
    buckets = [
        ("<$25", 0, 25),
        ("$25-50", 25, 50),
        ("$50-100", 50, 100),
        ("$100-200", 100, 200),
        ("$200-500", 200, 500),
        (">$500", 500, float("inf")),
    ]
    out = []
    for label, lo, hi in buckets:
        bucket = [r for r in records if lo <= r["cost_basis"] < hi]
        if not bucket:
            continue
        wins = sum(1 for r in bucket if r["effective"] == "win")
        losses = sum(1 for r in bucket if r["effective"] == "loss")
        decided = wins + losses
        total_wagered = sum(r["cost_basis"] for r in bucket)
        total_pnl = sum(r["net_pnl"] for r in bucket)
        out.append({
            "range": label,
            "n_contracts": len(bucket),
            "wins": wins,
            "losses": losses,
            "win_rate": round(wins / decided, 4) if decided > 0 else None,
            "total_wagered": round(total_wagered, 2),
            "total_pnl": round(total_pnl, 2),
            "roi": round(total_pnl / total_wagered, 4) if total_wagered > 0 else None,
        })
    return out


def compute_canonical_summary():
    """Produce the complete canonical baseline summary."""
    transactions = load_transactions()
    records = build_contracts(transactions)
    swing_records = [r for r in records if r["strategy"] == "swing"]
    hold_records = [r for r in records if r["strategy"] == "hold"]

    # Correlations
    costs = [r["cost_basis"] for r in records]
    nets = [r["net_pnl"] for r in records]
    wins_binary = [1 if r["effective"] == "win" else 0 for r in records]

    # Size by strategy
    size_by_strategy = {}
    for strat, subset in [("swing", swing_records), ("hold", hold_records)]:
        sizes = [r["cost_basis"] for r in subset]
        if sizes:
            size_by_strategy[strat] = {
                "n": len(subset),
                "median": round(percentile(sizes, 0.5), 2),
                "mean": round(sum(sizes) / len(sizes), 2),
                "min": round(min(sizes), 2),
                "max": round(max(sizes), 2),
            }

    return {
        "metadata": {
            "source": "71 iPhone screenshots of Polymarket US History tab",
            "capture_date": "2026-04-18",
            "period_covered": "Approximately 8 days ending 2026-04-18",
            "scope": "Tennis only",
            "excluded_match": EXCLUDE_MATCH,
            "excluded_reason": (
                "Pure market-making outlier; not representative of "
                "discretionary trading. Operator-directed exclusion."
            ),
            "fee_treatment": (
                "Fee-net; all trades within 50% taker-fee rebate promo "
                "window through 2026-04-30. Compared against breakeven.json "
                f"threshold of {BREAKEVEN_THRESHOLD * 100:.1f}%."
            ),
        },
        "cuts": {
            "all_tennis": summarize_subset(
                "All tennis contracts (excl outlier)", records
            ),
            "swing_only": summarize_subset(
                "Swing-strategy contracts (excl outlier)", swing_records
            ),
            "hold_only": summarize_subset(
                "Hold-strategy contracts (excl outlier)", hold_records
            ),
        },
        "sizing_buckets": compute_sizing_buckets(records),
        "correlations": {
            "cost_vs_net_pnl_pearson": round(pearson_correlation(costs, nets), 3),
            "cost_vs_win_binary_pearson": round(
                pearson_correlation(costs, wins_binary), 3
            ),
        },
        "size_by_strategy": size_by_strategy,
    }


def print_report(summary):
    """Human-readable report to stdout."""
    print("=" * 72)
    print("PM-TENNIS BASELINE — CANONICAL SUMMARY")
    print("=" * 72)

    md = summary["metadata"]
    print(f"\nSource: {md['source']}")
    print(f"Captured: {md['capture_date']}")
    print(f"Period: {md['period_covered']}")
    print(f"Scope: {md['scope']}")
    print(f"Excluded: {md['excluded_match']}")
    print(f"Fees: {md['fee_treatment']}")

    for key, cut in summary["cuts"].items():
        if cut is None:
            continue
        print(f"\n--- {cut['label']} ---")
        print(f"  N contracts:       {cut['n_contracts']}")
        print(f"  Wins / Losses:     {cut['n_wins']} / {cut['n_losses']}"
              f" (flats: {cut['n_flats']})")
        print(f"  Win rate:          {cut['win_rate'] * 100:.1f}%"
              f" (vs 58.2% breakeven: {cut['win_rate_vs_breakeven_pp']:+.1f} pp)")
        print(f"  Total wagered:     ${cut['total_wagered']:,.2f}")
        print(f"  Total P&L:         ${cut['total_pnl']:+,.2f}")
        print(f"  ROI:               {cut['roi'] * 100:+.1f}%")
        print(f"  Mean winner:       ${cut['mean_winner']:+.2f}")
        print(f"  Mean loser:        ${cut['mean_loser']:+.2f}")
        if cut["magnitude_ratio"]:
            print(f"  Magnitude ratio:   {cut['magnitude_ratio']:.3f}x")
        if cut["binomial_p_value_vs_breakeven"] is not None:
            print(f"  Binomial p-value:  {cut['binomial_p_value_vs_breakeven']:.3f}")
        print(f"  Reconciliation:    winners+losers = "
              f"${cut['reconciles']:+,.2f} vs total P&L ${cut['total_pnl']:+,.2f}"
              f" -- {'OK' if abs(cut['reconciles'] - cut['total_pnl']) < 0.01 else 'MISMATCH'}")

    print("\n--- Sizing buckets ---")
    for b in summary["sizing_buckets"]:
        wr = f"{b['win_rate'] * 100:.1f}%" if b["win_rate"] is not None else "—"
        roi = f"{b['roi'] * 100:+.1f}%" if b["roi"] is not None else "—"
        print(f"  {b['range']:<10} n={b['n_contracts']:>3}"
              f"  {b['wins']}W/{b['losses']}L  WR={wr:>6}"
              f"  wagered=${b['total_wagered']:>8,.0f}"
              f"  pnl=${b['total_pnl']:>+7,.0f}  ROI={roi:>6}")

    print("\n--- Correlations ---")
    for k, v in summary["correlations"].items():
        print(f"  {k}: {v:+.3f}")

    print("\n--- Size by strategy ---")
    for strat, s in summary["size_by_strategy"].items():
        print(f"  {strat}: n={s['n']:>3}"
              f"  median=${s['median']:.0f}"
              f"  mean=${s['mean']:.0f}"
              f"  min=${s['min']:.0f}"
              f"  max=${s['max']:.0f}")
    print()


def main():
    summary = compute_canonical_summary()

    # Write canonical JSON
    with open("baseline_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=float)

    # Print human-readable report
    print_report(summary)

    print(f"\nCanonical summary written to: baseline_summary.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
