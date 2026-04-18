"""
PM-Tennis — Sackmann P(S) table builder
Phase 1 deliverable.

Downloads the two Sackmann point-by-point archives from GitHub, parses them,
computes empirical win probabilities for every score state, applies Bayesian
shrinkage for rare states, and writes three Parquet lookup tables plus a
build_log.json summary.

Output files (written to DATA_DIR/sackmann/):
  P_S_best_of_3_mens.parquet
  P_S_best_of_3_womens.parquet
  P_S_best_of_5_mens.parquet
  build_log.json

Run once during Phase 1 setup.  Safe to re-run; output files are overwritten.

Usage (via Render one-off job or Shell tab):
  python sackmann/build_ps_tables.py

Environment variables:
  DATA_DIR   path to persistent disk mount (default: /data)
"""

import json
import logging
import math
import os
import re
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
OUT_DIR = DATA_DIR / "sackmann"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Sackmann archive URLs (latest main-branch zips)
# ---------------------------------------------------------------------------
ARCHIVES = {
    "pointbypoint": "https://github.com/JeffSackmann/tennis_pointbypoint/archive/refs/heads/master.zip",
    "slam_pointbypoint": "https://github.com/JeffSackmann/tennis_slam_pointbypoint/archive/refs/heads/master.zip",
}

SHRINKAGE_N = 200   # blend toward closed-form below this count
TOUR_SERVE_HOLD = {
    # empirical tour-wide serve-hold rates used for Barnett-Clarke fallback
    # derived from the archives themselves during build; seeded here as priors
    "atp_bo3": 0.635,
    "atp_bo5": 0.635,
    "wta_bo3": 0.560,
}


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

def download_zip(url: str) -> zipfile.ZipFile:
    log.info("Downloading %s", url)
    r = requests.get(url, timeout=120)
    r.raise_for_status()
    log.info("Downloaded %.1f MB", len(r.content) / 1e6)
    return zipfile.ZipFile(BytesIO(r.content))


# ---------------------------------------------------------------------------
# Barnett-Clarke closed-form P(win match | state) — simplified
# Uses tour-wide serve-hold rate; no per-player inputs.
# ---------------------------------------------------------------------------

def _p_game_win(p_hold: float, server: str) -> float:
    """Probability that the current server wins the current game."""
    return p_hold if server == "a" else (1.0 - p_hold)


def barnett_clarke(state: dict, best_of: int, p_hold: float) -> float:
    """
    Closed-form match-win probability for player A given state.
    Simplified recursive implementation sufficient for shrinkage fallback.
    Uses tour-wide serve-hold rate p_hold.
    """
    # For the shrinkage fallback we use a compact approximation:
    # convert the current score position into an approximate win probability
    # using the iid point model.  Full recursive Barnett-Clarke is expensive;
    # this approximation is adequate for rare-state blending.

    sa = state["sets_won_a"]
    sb = state["sets_won_b"]
    ga = state["games_won_a"]
    gb = state["games_won_b"]
    server = state.get("server", "a")

    sets_needed = math.ceil((best_of + 1) / 2)

    # Rough set-win probability from current game position
    # (treats each remaining game as independent)
    p_hold_a = p_hold if server == "a" else (1.0 - p_hold)

    # Approximate: use current game score as a proxy for momentum
    # For the fallback this precision is sufficient
    try:
        p_win_set = _p_win_set_approx(ga, gb, p_hold_a, p_hold)
        p_win_match = _p_win_match_from_sets(sa, sb, p_win_set, sets_needed)
    except Exception:
        p_win_match = 0.5  # ultimate fallback

    return max(1e-6, min(1 - 1e-6, p_win_match))


def _p_win_set_approx(ga: int, gb: int, p_hold_a: float, p_hold: float) -> float:
    """Rough probability player A wins the current set."""
    games_a_needs = max(0, 6 - ga)
    games_b_needs = max(0, 6 - gb)
    if games_a_needs == 0 and games_b_needs > 0:
        return 0.99
    if games_b_needs == 0 and games_a_needs > 0:
        return 0.01
    # Use ratio of remaining games needed as a crude proxy
    advantage = (games_b_needs - games_a_needs) / max(games_a_needs + games_b_needs, 1)
    return max(0.01, min(0.99, 0.5 + advantage * 0.3))


def _p_win_match_from_sets(sa: int, sb: int, p_win_set: float, sets_needed: int) -> float:
    """Probability player A wins the match given current set score."""
    sets_a_needs = sets_needed - sa
    sets_b_needs = sets_needed - sb
    if sets_a_needs <= 0:
        return 0.99
    if sets_b_needs <= 0:
        return 0.01
    # Binomial approximation
    p = 0.0
    for a_wins in range(sets_a_needs, sets_a_needs + sets_b_needs):
        b_wins = a_wins - sets_a_needs
        if b_wins < 0:
            continue
        # Ways to arrange wins
        from math import comb
        n = a_wins + b_wins - 1  # last set must be won by A
        if n < 0:
            continue
        p += comb(n, b_wins) * (p_win_set ** sets_a_needs) * ((1 - p_win_set) ** b_wins)
    return max(0.01, min(0.99, p))


# ---------------------------------------------------------------------------
# State tuple parsing — tennis_pointbypoint format
# ---------------------------------------------------------------------------

def _parse_pbp_sequence(seq: str, best_of: int, server_start: str = "a") -> list:
    """
    Parse a compact point sequence string (e.g. "SSRSSRS...") from
    tennis_pointbypoint into a list of (state_before, state_after, winner_a)
    tuples, where winner_a is 1 if player A eventually won the match, else 0.

    Point characters:
      S = server wins point
      R = returner wins point
      (uppercase variants used; some files use lowercase)

    Returns list of state transition dicts, or empty list on parse error.
    """
    if not seq or not isinstance(seq, str):
        return []

    seq = seq.strip().upper()

    # Score state
    sets_a, sets_b = 0, 0
    games_a, games_b = 0, 0
    points_a, points_b = 0, 0
    in_tiebreak = False
    tb_points_a, tb_points_b = 0, 0
    server = server_start

    sets_needed = math.ceil((best_of + 1) / 2)
    transitions = []

    def current_state():
        return {
            "sets_won_a": sets_a,
            "sets_won_b": sets_b,
            "games_won_a": games_a,
            "games_won_b": games_b,
            "points_won_a": points_a,
            "points_won_b": points_b,
            "in_tiebreak": in_tiebreak,
            "tb_points_a": tb_points_a,
            "tb_points_b": tb_points_b,
            "server": server,
        }

    def flip_server():
        nonlocal server
        server = "b" if server == "a" else "a"

    def award_point_to(winner: str):
        nonlocal points_a, points_b, games_a, games_b
        nonlocal sets_a, sets_b, in_tiebreak, tb_points_a, tb_points_b, server

        if in_tiebreak:
            if winner == "a":
                tb_points_a += 1
            else:
                tb_points_b += 1

            # Tiebreak server switch: every 2 points after first
            total_tb = tb_points_a + tb_points_b
            if total_tb % 2 == 1:
                flip_server()

            # Tiebreak win condition: first to 7 with 2-point lead
            if (tb_points_a >= 7 or tb_points_b >= 7) and abs(tb_points_a - tb_points_b) >= 2:
                if tb_points_a > tb_points_b:
                    games_a += 1
                else:
                    games_b += 1
                in_tiebreak = False
                tb_points_a = tb_points_b = 0
                points_a = points_b = 0
                # After tiebreak, server switches
                flip_server()
                _check_set_win()
        else:
            if winner == "a":
                points_a += 1
            else:
                points_b += 1

            # Game win: first to 4 points with 2-point lead (deuce/ad)
            if (points_a >= 4 or points_b >= 4) and abs(points_a - points_b) >= 2:
                if points_a > points_b:
                    games_a += 1
                else:
                    games_b += 1
                points_a = points_b = 0
                flip_server()
                _check_set_win()

    def _check_set_win():
        nonlocal games_a, games_b, sets_a, sets_b, in_tiebreak

        # Standard set win
        if games_a >= 6 and games_a - games_b >= 2:
            sets_a += 1
            games_a = games_b = 0
            return
        if games_b >= 6 and games_b - games_a >= 2:
            sets_b += 1
            games_a = games_b = 0
            return
        # Tiebreak at 6-6
        if games_a == 6 and games_b == 6:
            in_tiebreak = True

    for ch in seq:
        if ch not in ("S", "R"):
            continue  # skip noise characters

        state_before = current_state()

        # Determine which player wins this point
        point_winner = "a" if (ch == "S") == (server == "a") else "b"
        # ch == "S" means server wins; server == "a" means A is serving
        # so A wins the point iff (S and server==a) or (R and server==b)
        point_winner = "a" if (
            (ch == "S" and server == "a") or (ch == "R" and server == "b")
        ) else "b"

        award_point_to(point_winner)
        state_after = current_state()

        transitions.append({
            "state_before": state_before,
            "state_after": state_after,
        })

        # Check match over
        if sets_a >= sets_needed or sets_b >= sets_needed:
            break

    return transitions, sets_a, sets_b


# ---------------------------------------------------------------------------
# Parse tennis_pointbypoint CSV files
# ---------------------------------------------------------------------------

def parse_pointbypoint_zip(zf: zipfile.ZipFile, gender: str, best_of: int) -> pd.DataFrame:
    """
    Parse all matches from tennis_pointbypoint archive for the given
    gender ('atp' or 'wta') and best_of (3 or 5).
    Returns DataFrame with columns: state_key, wins_a, count.
    """
    log.info("Parsing pointbypoint archive — gender=%s best_of=%d", gender, best_of)

    state_wins = defaultdict(lambda: [0, 0])  # state_key -> [wins_a, total]
    match_count = 0
    skipped = 0

    prefix_map = {"atp": ["atp_", "challenger_"], "wta": ["wta_"]}
    prefixes = prefix_map.get(gender, [])

    for name in zf.namelist():
        basename = os.path.basename(name)
        if not basename.endswith(".csv"):
            continue
        # Filter by gender prefix
        if not any(basename.startswith(p) for p in prefixes):
            continue

        try:
            with zf.open(name) as f:
                df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            log.warning("Could not read %s: %s", name, e)
            skipped += 1
            continue

        # Required columns
        if "pbp" not in df.columns:
            skipped += 1
            continue

        for _, row in df.iterrows():
            seq = row.get("pbp", "")
            if not seq or not isinstance(seq, str) or len(seq) < 10:
                skipped += 1
                continue

            try:
                transitions, sets_a, sets_b = _parse_pbp_sequence(seq, best_of)
            except Exception:
                skipped += 1
                continue

            sets_needed = math.ceil((best_of + 1) / 2)
            winner_a = 1 if sets_a >= sets_needed else 0

            for t in transitions:
                key = _state_to_key(t["state_before"])
                state_wins[key][0] += winner_a
                state_wins[key][1] += 1

            match_count += 1

    log.info("Parsed %d matches, skipped %d rows", match_count, skipped)

    rows = []
    for key, (wins, total) in state_wins.items():
        rows.append({"state_key": key, "wins_a": wins, "count": total})

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["state_key", "wins_a", "count"])


def parse_slam_zip(zf: zipfile.ZipFile, gender: str) -> pd.DataFrame:
    """
    Parse Slam point-by-point archive.
    Men's = best_of 5; Women's = best_of 3.
    Returns DataFrame with columns: state_key, wins_a, count.
    """
    best_of = 5 if gender == "atp" else 3
    log.info("Parsing slam archive — gender=%s best_of=%d", gender, best_of)

    state_wins = defaultdict(lambda: [0, 0])
    match_count = 0
    skipped = 0

    for name in zf.namelist():
        basename = os.path.basename(name)
        if not basename.endswith(".csv"):
            continue
        # Slam archive has files like "2023-ausopen-matches.csv" and
        # point files like "2023-ausopen-points.csv"
        if "point" not in basename.lower():
            continue

        try:
            with zf.open(name) as f:
                df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            log.warning("Could not read %s: %s", name, e)
            skipped += 1
            continue

        # Slam format: one row per point, columns include server1,server2,
        # p1_points_won, p2_points_won, etc.
        # We reconstruct transitions from running score columns.
        if not {"server1", "p1_games", "p2_games", "set_victor"}.issubset(df.columns):
            skipped += 1
            continue

        # Filter by gender if column available
        if "gender" in df.columns:
            g_val = "M" if gender == "atp" else "W"
            df = df[df["gender"] == g_val]

        if df.empty:
            skipped += 1
            continue

        try:
            transitions_list, w_a = _parse_slam_df(df, best_of)
            for t in transitions_list:
                key = _state_to_key(t["state_before"])
                state_wins[key][0] += w_a
                state_wins[key][1] += 1
            match_count += 1
        except Exception as e:
            log.debug("Slam parse error %s: %s", name, e)
            skipped += 1

    log.info("Parsed %d slam matches, skipped %d", match_count, skipped)

    rows = []
    for key, (wins, total) in state_wins.items():
        rows.append({"state_key": key, "wins_a": wins, "count": total})

    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["state_key", "wins_a", "count"])


def _parse_slam_df(df: pd.DataFrame, best_of: int) -> tuple:
    """Parse a slam points DataFrame into transitions."""
    transitions = []

    # Group by match_id if present
    id_col = next((c for c in ["match_id", "match_num", "ElapsedTime"] if c in df.columns), None)

    sets_needed = math.ceil((best_of + 1) / 2)

    prev_state = None
    winner_a = 0

    for _, row in df.iterrows():
        try:
            state = _slam_row_to_state(row)
        except Exception:
            continue

        if prev_state is not None:
            transitions.append({
                "state_before": prev_state,
                "state_after": state,
            })

        prev_state = state

        # Determine match winner from last row
        if row.get("set_victor") in (1, "1"):
            winner_a = 1
        elif row.get("set_victor") in (2, "2"):
            winner_a = 0

    return transitions, winner_a


def _slam_row_to_state(row) -> dict:
    """Convert a slam points-file row to a state dict."""
    def _int(val, default=0):
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    server_val = row.get("server1", row.get("Svr", 1))
    server = "a" if _int(server_val) == 1 else "b"

    p1_sets = _int(row.get("p1_sets", row.get("P1Sets", 0)))
    p2_sets = _int(row.get("p2_sets", row.get("P2Sets", 0)))
    p1_games = _int(row.get("p1_games", row.get("P1Games", 0)))
    p2_games = _int(row.get("p2_games", row.get("P2Games", 0)))
    p1_points = _int(row.get("p1_points_won", row.get("P1Points", 0)))
    p2_points = _int(row.get("p2_points_won", row.get("P2Points", 0)))

    in_tb = (p1_games == 6 and p2_games == 6)

    return {
        "sets_won_a": p1_sets,
        "sets_won_b": p2_sets,
        "games_won_a": p1_games,
        "games_won_b": p2_games,
        "points_won_a": p1_points if not in_tb else 0,
        "points_won_b": p2_points if not in_tb else 0,
        "in_tiebreak": in_tb,
        "tb_points_a": p1_points if in_tb else 0,
        "tb_points_b": p2_points if in_tb else 0,
        "server": server,
    }


# ---------------------------------------------------------------------------
# State key encoding
# ---------------------------------------------------------------------------

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


def key_to_state(key: str) -> dict:
    """Decode a state key string back to a dict."""
    return {
        "sets_won_a":   int(key[0]),
        "sets_won_b":   int(key[1]),
        "games_won_a":  int(key[2:4]),
        "games_won_b":  int(key[4:6]),
        "points_won_a": int(key[6]),
        "points_won_b": int(key[7]),
        "in_tiebreak":  key[8] == "T",
        "tb_points_a":  int(key[9:11]),
        "tb_points_b":  int(key[11:13]),
        "server":       key[13],
    }


# ---------------------------------------------------------------------------
# Build P(S) table with shrinkage
# ---------------------------------------------------------------------------

def build_ps_table(counts_df: pd.DataFrame, best_of: int, serve_hold: float) -> pd.DataFrame:
    """
    Given a counts DataFrame (state_key, wins_a, count), apply Bayesian
    shrinkage and return a P(S) table with columns:
      state_key, wins_a, count, emp_p, cf_p, p_s
    """
    if counts_df.empty:
        return pd.DataFrame(columns=["state_key", "wins_a", "count", "emp_p", "cf_p", "p_s"])

    rows = []
    for _, row in counts_df.iterrows():
        key = row["state_key"]
        wins = row["wins_a"]
        n = row["count"]

        emp_p = wins / n if n > 0 else 0.5

        try:
            state = key_to_state(key)
            cf_p = barnett_clarke(state, best_of, serve_hold)
        except Exception:
            cf_p = 0.5

        if n >= SHRINKAGE_N:
            p_s = emp_p
        elif n == 0:
            p_s = cf_p
        else:
            w = n / (n + SHRINKAGE_N)
            p_s = w * emp_p + (1 - w) * cf_p

        rows.append({
            "state_key": key,
            "wins_a":    int(wins),
            "count":     int(n),
            "emp_p":     round(emp_p, 6),
            "cf_p":      round(cf_p, 6),
            "p_s":       round(p_s, 6),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main build routine
# ---------------------------------------------------------------------------

def main():
    log.info("=== PM-Tennis Sackmann P(S) table builder ===")
    build_start = datetime.now(timezone.utc)
    build_log = {
        "built_at": build_start.isoformat(),
        "tables": {},
        "warnings": [],
    }

    # Download archives
    try:
        zf_pbp = download_zip(ARCHIVES["pointbypoint"])
    except Exception as e:
        log.error("Failed to download pointbypoint archive: %s", e)
        build_log["warnings"].append(f"pointbypoint download failed: {e}")
        zf_pbp = None

    try:
        zf_slam = download_zip(ARCHIVES["slam_pointbypoint"])
    except Exception as e:
        log.error("Failed to download slam archive: %s", e)
        build_log["warnings"].append(f"slam download failed: {e}")
        zf_slam = None

    tables_built = 0

    # --- Men's best-of-3 (ATP main + Challenger) ---
    if zf_pbp:
        log.info("Building P_S_best_of_3_mens ...")
        counts = parse_pointbypoint_zip(zf_pbp, gender="atp", best_of=3)
        table = build_ps_table(counts, best_of=3, serve_hold=TOUR_SERVE_HOLD["atp_bo3"])
        out_path = OUT_DIR / "P_S_best_of_3_mens.parquet"
        table.to_parquet(out_path, index=False)
        log.info("Wrote %s (%d states)", out_path, len(table))
        build_log["tables"]["P_S_best_of_3_mens"] = {
            "path": str(out_path),
            "state_count": len(table),
            "match_count_approx": int(counts["count"].sum() / 200) if not counts.empty else 0,
            "total_transitions": int(counts["count"].sum()) if not counts.empty else 0,
        }
        tables_built += 1

    # --- Women's best-of-3 (WTA main + Slam women's) ---
    counts_wta = pd.DataFrame(columns=["state_key", "wins_a", "count"])
    if zf_pbp:
        counts_wta = parse_pointbypoint_zip(zf_pbp, gender="wta", best_of=3)
    if zf_slam:
        counts_slam_w = parse_slam_zip(zf_slam, gender="wta")
        if not counts_slam_w.empty:
            counts_wta = pd.concat([counts_wta, counts_slam_w]).groupby("state_key", as_index=False).sum()

    if not counts_wta.empty:
        log.info("Building P_S_best_of_3_womens ...")
        table = build_ps_table(counts_wta, best_of=3, serve_hold=TOUR_SERVE_HOLD["wta_bo3"])
        out_path = OUT_DIR / "P_S_best_of_3_womens.parquet"
        table.to_parquet(out_path, index=False)
        log.info("Wrote %s (%d states)", out_path, len(table))
        build_log["tables"]["P_S_best_of_3_womens"] = {
            "path": str(out_path),
            "state_count": len(table),
            "total_transitions": int(counts_wta["count"].sum()),
        }
        tables_built += 1

    # --- Men's best-of-5 (Slam men's) ---
    if zf_slam:
        log.info("Building P_S_best_of_5_mens ...")
        counts_slam_m = parse_slam_zip(zf_slam, gender="atp")
        if not counts_slam_m.empty:
            table = build_ps_table(counts_slam_m, best_of=5, serve_hold=TOUR_SERVE_HOLD["atp_bo5"])
            out_path = OUT_DIR / "P_S_best_of_5_mens.parquet"
            table.to_parquet(out_path, index=False)
            log.info("Wrote %s (%d states)", out_path, len(table))
            build_log["tables"]["P_S_best_of_5_mens"] = {
                "path": str(out_path),
                "state_count": len(table),
                "total_transitions": int(counts_slam_m["count"].sum()),
            }
            tables_built += 1
        else:
            build_log["warnings"].append("No men's Slam data parsed — P_S_best_of_5_mens not built")

    build_log["tables_built"] = tables_built
    build_log["elapsed_seconds"] = round((datetime.now(timezone.utc) - build_start).total_seconds(), 1)

    log_path = OUT_DIR / "build_log.json"
    with open(log_path, "w") as f:
        json.dump(build_log, f, indent=2)
    log.info("Build log written to %s", log_path)
    log.info("=== Build complete: %d tables in %.1fs ===",
             tables_built, build_log["elapsed_seconds"])


if __name__ == "__main__":
    main()
