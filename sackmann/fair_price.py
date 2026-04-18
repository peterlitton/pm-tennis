"""
PM-Tennis — fair_price.py
Phase 1 deliverable.

Core fair-price computation helpers:
  - logit / sigmoid
  - P_S lookup (loads from Parquet tables built by build_ps_tables.py)
  - fair_price_series — running fair value from handicap + score events

Used by:
  - replay simulator (Phase 6)
  - /state API endpoint (Phase 4)
  - JS parity test vector validation (Phase 5)

Environment variables:
  DATA_DIR   path to persistent disk mount (default: /data)
"""

import math
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
SACKMANN_DIR = DATA_DIR / "sackmann"

SHRINKAGE_N = 200


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def logit(p: float) -> float:
    """Log-odds of probability p.  Clamped to avoid infinities."""
    p = max(1e-9, min(1 - 1e-9, p))
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    """Inverse logit."""
    return 1.0 / (1.0 + math.exp(-x))


# ---------------------------------------------------------------------------
# P(S) table loader
# ---------------------------------------------------------------------------

@lru_cache(maxsize=4)
def _load_table(best_of: int, gender: str) -> dict:
    """
    Load a P(S) Parquet table and return it as a dict: state_key -> p_s.
    Cached — loaded once per process per (best_of, gender) combination.
    """
    if best_of == 5:
        fname = "P_S_best_of_5_mens.parquet"
    elif gender == "wta":
        fname = "P_S_best_of_3_womens.parquet"
    else:
        fname = "P_S_best_of_3_mens.parquet"

    path = SACKMANN_DIR / fname
    if not path.exists():
        raise FileNotFoundError(
            f"P(S) table not found: {path}. "
            "Run sackmann/build_ps_tables.py first."
        )

    df = pd.read_parquet(path, columns=["state_key", "p_s"])
    return dict(zip(df["state_key"], df["p_s"]))


def _state_to_key(s: dict) -> str:
    """Encode a state dict as a compact string key."""
    return (
        f"{s['sets_won_a']}{s['sets_won_b']}"
        f"{s['games_won_a']:02d}{s['games_won_b']:02d}"
        f"{s['points_won_a']}{s['points_won_b']}"
        f"{'T' if s['in_tiebreak'] else 'G'}"
        f"{s['tb_points_a']:02d}{s['tb_points_b']:02d}"
        f"{s['server']}"
    )


def P_S(state: dict, best_of: int, gender: str) -> float:
    """
    Return the empirical (shrinkage-blended) probability that player A
    wins the match from the given state.

    Parameters
    ----------
    state   : dict with keys sets_won_a, sets_won_b, games_won_a,
              games_won_b, points_won_a, points_won_b,
              in_tiebreak, tb_points_a, tb_points_b, server
    best_of : 3 or 5
    gender  : 'atp' or 'wta'

    Returns
    -------
    float in (0, 1)
    """
    table = _load_table(best_of, gender)
    key = _state_to_key(state)
    p = table.get(key)
    if p is None:
        # State not in archive — return 0.5 as neutral fallback
        # (Bayesian shrinkage in the builder handles most rare states;
        # this catches structurally impossible states or parse mismatches)
        return 0.5
    return float(p)


# ---------------------------------------------------------------------------
# Fair price series
# ---------------------------------------------------------------------------

def fair_price_series(
    handicap_mid: float,
    score_events: list,
    match_meta: dict,
) -> list:
    """
    Compute the running fair value for player A across a sequence of
    score events using the log-odds update rule.

    Parameters
    ----------
    handicap_mid  : pre-match midpoint price for player A's YES contract
    score_events  : list of dicts, each with keys:
                      ts_recv     — ISO timestamp string (used for ordering)
                      state_before — state dict before the point
                      state_after  — state dict after the point
    match_meta    : dict with keys best_of (int) and gender (str 'atp'|'wta')

    Returns
    -------
    list of (ts_recv, fair_price) tuples.
    First entry has ts_recv=None and is the pre-match fair price.
    """
    best_of = match_meta["best_of"]
    gender = match_meta["gender"]

    fair_logit_val = logit(handicap_mid)
    out = [(None, sigmoid(fair_logit_val))]

    sorted_events = sorted(score_events, key=lambda e: e["ts_recv"])

    for ev in sorted_events:
        p_before = P_S(ev["state_before"], best_of, gender)
        p_after  = P_S(ev["state_after"],  best_of, gender)

        delta = logit(p_after) - logit(p_before)
        fair_logit_val += delta

        out.append((ev["ts_recv"], sigmoid(fair_logit_val)))

    return out


# ---------------------------------------------------------------------------
# Parity test vector
# ---------------------------------------------------------------------------

# This dict is the canonical test vector shared with the JavaScript
# implementation (Phase 5).  Any change here must be mirrored in
# frontend/test/parity_vector.json.
#
# Scenario: men's best-of-3, even pre-match (handicap 0.50).
# One score event: break at 4-4, 30-40 in set 3.
# state_before: serving at 4-4 30-40 in set 3
# state_after:  B serving at 5-4 in set 3
#
# Expected fair price after event: ~0.29 (see build plan Section 4.3.4)

PARITY_TEST_VECTOR = {
    "handicap_mid": 0.50,
    "match_meta": {"best_of": 3, "gender": "atp"},
    "score_events": [
        {
            "ts_recv": "2026-04-17T18:32:14.500Z",
            "state_before": {
                "sets_won_a": 0, "sets_won_b": 0,
                "games_won_a": 4, "games_won_b": 4,
                "points_won_a": 2, "points_won_b": 3,
                "in_tiebreak": False,
                "tb_points_a": 0, "tb_points_b": 0,
                "server": "a",
            },
            "state_after": {
                "sets_won_a": 0, "sets_won_b": 0,
                "games_won_a": 4, "games_won_b": 5,
                "points_won_a": 0, "points_won_b": 0,
                "in_tiebreak": False,
                "tb_points_a": 0, "tb_points_b": 0,
                "server": "b",
            },
        }
    ],
    # Tolerance: fair price must land within this range
    "expected_fair_price_min": 0.20,
    "expected_fair_price_max": 0.38,
}


def run_parity_check() -> dict:
    """
    Run the parity test vector and return a result dict.
    Called by the admin UI's diagnostics endpoint.
    """
    vec = PARITY_TEST_VECTOR
    series = fair_price_series(
        vec["handicap_mid"],
        vec["score_events"],
        vec["match_meta"],
    )
    final_price = series[-1][1]
    passed = vec["expected_fair_price_min"] <= final_price <= vec["expected_fair_price_max"]
    return {
        "passed": passed,
        "fair_price_after_event": round(final_price, 6),
        "expected_range": [vec["expected_fair_price_min"], vec["expected_fair_price_max"]],
        "handicap_mid": vec["handicap_mid"],
        "series": [(ts, round(p, 6)) for ts, p in series],
    }
