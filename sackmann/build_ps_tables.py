"""
PM-Tennis — Sackmann P(S) table builder  (v2 — correct column names)
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

Usage (Render Shell):
  python sackmann/build_ps_tables.py

Environment variables:
  DATA_DIR   path to persistent disk mount (default: /data)
"""

import json
import logging
import math
import os
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import pandas as pd
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
OUT_DIR = DATA_DIR / "sackmann"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ARCHIVES = {
    "pointbypoint": "https://github.com/JeffSackmann/tennis_pointbypoint/archive/refs/heads/master.zip",
    "slam_pointbypoint": "https://github.com/JeffSackmann/tennis_slam_pointbypoint/archive/refs/heads/master.zip",
}

SHRINKAGE_N = 200

TOUR_SERVE_HOLD = {
    "atp_bo3": 0.635,
    "atp_bo5": 0.635,
    "wta_bo3": 0.560,
}

# Files to parse per gender from tennis_pointbypoint archive
PBP_FILE_PATTERNS = {
    "atp": [
        "pbp_matches_atp_main_archive.csv",
        "pbp_matches_atp_main_current.csv",
        "pbp_matches_ch_main_archive.csv",
        "pbp_matches_ch_main_current.csv",
    ],
    "wta": [
        "pbp_matches_wta_main_archive.csv",
        "pbp_matches_wta_main_current.csv",
    ],
}


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_zip(url: str) -> zipfile.ZipFile:
    log.info("Downloading %s", url)
    r = requests.get(url, timeout=180)
    r.raise_for_status()
    log.info("Downloaded %.1f MB", len(r.content) / 1e6)
    return zipfile.ZipFile(BytesIO(r.content))


# ---------------------------------------------------------------------------
# State key encoding / decoding
# ---------------------------------------------------------------------------

def state_to_key(s: dict) -> str:
    return (
        f"{s['sets_won_a']}{s['sets_won_b']}"
        f"{s['games_won_a']:02d}{s['games_won_b']:02d}"
        f"{s['points_won_a']}{s['points_won_b']}"
        f"{'T' if s['in_tiebreak'] else 'G'}"
        f"{s['tb_points_a']:02d}{s['tb_points_b']:02d}"
        f"{s['server']}"
    )


def key_to_state(key: str) -> dict:
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
# Barnett-Clarke closed-form fallback (simplified)
# ---------------------------------------------------------------------------

def barnett_clarke(state: dict, best_of: int, p_hold: float) -> float:
    from math import comb
    sa = state["sets_won_a"]
    sb = state["sets_won_b"]
    ga = state["games_won_a"]
    gb = state["games_won_b"]
    sets_needed = math.ceil((best_of + 1) / 2)

    sets_a_need = sets_needed - sa
    sets_b_need = sets_needed - sb

    if sets_a_need <= 0:
        return 0.99
    if sets_b_need <= 0:
        return 0.01

    games_a_need = max(0, 6 - ga)
    games_b_need = max(0, 6 - gb)
    total = games_a_need + games_b_need
    if total == 0:
        p_win_set = 0.5
    else:
        advantage = (games_b_need - games_a_need) / total
        p_win_set = max(0.05, min(0.95, 0.5 + advantage * 0.3))

    p_match = 0.0
    for a_wins in range(sets_a_need, sets_a_need + sets_b_need):
        b_wins = a_wins - sets_a_need
        if b_wins < 0:
            continue
        n = max(0, a_wins + b_wins - 1)
        try:
            p_match += comb(n, b_wins) * (p_win_set ** sets_a_need) * ((1 - p_win_set) ** b_wins)
        except Exception:
            pass

    return max(1e-6, min(1 - 1e-6, p_match))


# ---------------------------------------------------------------------------
# Parse tennis_pointbypoint (pbp string format)
# Columns: server1 (1 or 2), winner (1 or 2), pbp (string of S/R)
# ---------------------------------------------------------------------------

def parse_pbp_string(pbp: str, server1_is_a: bool, best_of: int) -> tuple:
    """
    Parse a compact point sequence.
    S = server wins point, R = returner wins point.
    server1_is_a: True if player A (player 1) served first.
    Returns (transitions list, sets_a, sets_b).
    """
    pbp = pbp.strip().upper()
    sets_needed = math.ceil((best_of + 1) / 2)

    sets_a = sets_b = 0
    games_a = games_b = 0
    points_a = points_b = 0
    in_tiebreak = False
    tb_a = tb_b = 0
    server = "a" if server1_is_a else "b"

    transitions = []

    def flip():
        nonlocal server
        server = "b" if server == "a" else "a"

    def make_state():
        return {
            "sets_won_a": sets_a, "sets_won_b": sets_b,
            "games_won_a": games_a, "games_won_b": games_b,
            "points_won_a": points_a if not in_tiebreak else 0,
            "points_won_b": points_b if not in_tiebreak else 0,
            "in_tiebreak": in_tiebreak,
            "tb_points_a": tb_a if in_tiebreak else 0,
            "tb_points_b": tb_b if in_tiebreak else 0,
            "server": server,
        }

    def maybe_end_set():
        nonlocal games_a, games_b, sets_a, sets_b, in_tiebreak
        if games_a >= 6 and games_a - games_b >= 2:
            sets_a += 1
            games_a = games_b = 0
        elif games_b >= 6 and games_b - games_a >= 2:
            sets_b += 1
            games_a = games_b = 0
        elif games_a == 6 and games_b == 6:
            in_tiebreak = True

    for ch in pbp:
        if ch not in ("S", "R"):
            continue

        state_before = make_state()

        server_wins_point = (ch == "S")
        point_to_a = server_wins_point if server == "a" else not server_wins_point

        if in_tiebreak:
            if point_to_a:
                tb_a += 1
            else:
                tb_b += 1
            total_tb = tb_a + tb_b
            if total_tb % 2 == 1:
                flip()
            if (tb_a >= 7 or tb_b >= 7) and abs(tb_a - tb_b) >= 2:
                if tb_a > tb_b:
                    games_a += 1
                else:
                    games_b += 1
                in_tiebreak = False
                tb_a = tb_b = 0
                points_a = points_b = 0
                flip()
                maybe_end_set()
        else:
            if point_to_a:
                points_a += 1
            else:
                points_b += 1
            if (points_a >= 4 or points_b >= 4) and abs(points_a - points_b) >= 2:
                if points_a > points_b:
                    games_a += 1
                else:
                    games_b += 1
                points_a = points_b = 0
                flip()
                maybe_end_set()

        state_after = make_state()
        transitions.append({"state_before": state_before, "state_after": state_after})

        if sets_a >= sets_needed or sets_b >= sets_needed:
            break

    return transitions, sets_a, sets_b


def parse_pointbypoint_zip(zf: zipfile.ZipFile, gender: str, best_of: int) -> pd.DataFrame:
    log.info("Parsing pointbypoint archive — gender=%s best_of=%d", gender, best_of)
    target_files = set(PBP_FILE_PATTERNS.get(gender, []))
    state_wins = defaultdict(lambda: [0, 0])
    match_count = 0
    skipped = 0

    for name in zf.namelist():
        basename = os.path.basename(name)
        if basename not in target_files:
            continue

        log.info("  Reading %s", basename)
        try:
            with zf.open(name) as f:
                df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            log.warning("Could not read %s: %s", name, e)
            skipped += 1
            continue

        if not {"server1", "winner", "pbp"}.issubset(df.columns):
            log.warning("Missing columns in %s", basename)
            skipped += 1
            continue

        for _, row in df.iterrows():
            pbp = row.get("pbp", "")
            if not isinstance(pbp, str) or len(pbp) < 10:
                skipped += 1
                continue
            try:
                server1 = int(row["server1"])
                winner = int(row["winner"])
            except (TypeError, ValueError):
                skipped += 1
                continue

            server1_is_a = (server1 == 1)
            winner_a = 1 if winner == 1 else 0

            try:
                transitions, sa, sb = parse_pbp_string(pbp, server1_is_a, best_of)
            except Exception as e:
                log.debug("Parse error: %s", e)
                skipped += 1
                continue

            for t in transitions:
                key = state_to_key(t["state_before"])
                state_wins[key][0] += winner_a
                state_wins[key][1] += 1

            match_count += 1

        log.info("  After %s: %d matches so far, %d skipped", basename, match_count, skipped)

    log.info("Parsed %d matches total, %d skipped", match_count, skipped)
    rows = [{"state_key": k, "wins_a": v[0], "count": v[1]} for k, v in state_wins.items()]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["state_key", "wins_a", "count"])


# ---------------------------------------------------------------------------
# Parse tennis_slam_pointbypoint
# Points files: 20XX-<slam>-points.csv
# Matches files: 20XX-<slam>-matches.csv
# Key columns: match_id, SetNo, P1GamesWon, P2GamesWon,
#              P1PointsWon, P2PointsWon, PointServer, PointWinner,
#              SetWinner, event_name
# ---------------------------------------------------------------------------

def parse_slam_zip(zf: zipfile.ZipFile, gender: str) -> pd.DataFrame:
    best_of = 5 if gender == "atp" else 3
    gender_str = "men" if gender == "atp" else "women"
    log.info("Parsing slam archive — gender=%s best_of=%d", gender, best_of)

    # Load match winners from matches files
    match_winners = {}
    for name in zf.namelist():
        if not os.path.basename(name).endswith("-matches.csv"):
            continue
        try:
            with zf.open(name) as f:
                mdf = pd.read_csv(f, low_memory=False)
            if {"match_id", "winner"}.issubset(mdf.columns):
                for _, row in mdf.iterrows():
                    try:
                        match_winners[str(row["match_id"])] = int(row["winner"])
                    except Exception:
                        pass
        except Exception:
            pass

    log.info("Loaded %d match winners", len(match_winners))

    state_wins = defaultdict(lambda: [0, 0])
    match_count = 0
    skipped = 0

    for name in zf.namelist():
        if not os.path.basename(name).endswith("-points.csv"):
            continue
        try:
            with zf.open(name) as f:
                df = pd.read_csv(f, low_memory=False)
        except Exception as e:
            log.warning("Could not read %s: %s", name, e)
            skipped += 1
            continue

        required = {"match_id", "SetNo", "P1GamesWon", "P2GamesWon", "PointServer", "PointWinner"}
        if not required.issubset(df.columns):
            skipped += 1
            continue

        # Gender filter
        if "event_name" in df.columns:
            mask = df["event_name"].str.lower().str.contains(gender_str, na=False)
            df = df[mask]
            if df.empty:
                continue

        for mid, grp in df.groupby("match_id"):
            mid_str = str(mid)
            winner_val = match_winners.get(mid_str)
            if winner_val is None:
                skipped += 1
                continue

            winner_a = 1 if winner_val == 1 else 0

            try:
                transitions = _parse_slam_group(grp, best_of)
            except Exception as e:
                log.debug("Slam group error %s: %s", mid_str, e)
                skipped += 1
                continue

            for t in transitions:
                key = state_to_key(t["state_before"])
                state_wins[key][0] += winner_a
                state_wins[key][1] += 1

            match_count += 1

    log.info("Parsed %d slam matches, %d skipped", match_count, skipped)
    rows = [{"state_key": k, "wins_a": v[0], "count": v[1]} for k, v in state_wins.items()]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["state_key", "wins_a", "count"])


def _parse_slam_group(grp: pd.DataFrame, best_of: int) -> list:
    transitions = []

    def _int(val, default=0):
        try:
            return int(val)
        except Exception:
            return default

    if "PointNumber" in grp.columns:
        grp = grp.sort_values("PointNumber")

    sets_a = sets_b = 0
    prev_set_no = None

    for _, row in grp.iterrows():
        set_no = _int(row.get("SetNo", 1), 1)
        ga = _int(row.get("P1GamesWon", 0))
        gb = _int(row.get("P2GamesWon", 0))

        if prev_set_no is not None and set_no != prev_set_no:
            sw = _int(row.get("SetWinner", 0))
            if sw == 1:
                sets_a += 1
            elif sw == 2:
                sets_b += 1

        prev_set_no = set_no

        p1_pts = min(_int(row.get("P1PointsWon", 0)), 3)
        p2_pts = min(_int(row.get("P2PointsWon", 0)), 3)

        in_tb = (ga == 6 and gb == 6)
        server_val = _int(row.get("PointServer", 1), 1)
        server = "a" if server_val == 1 else "b"

        state_before = {
            "sets_won_a": sets_a, "sets_won_b": sets_b,
            "games_won_a": ga, "games_won_b": gb,
            "points_won_a": p1_pts if not in_tb else 0,
            "points_won_b": p2_pts if not in_tb else 0,
            "in_tiebreak": in_tb,
            "tb_points_a": p1_pts if in_tb else 0,
            "tb_points_b": p2_pts if in_tb else 0,
            "server": server,
        }

        pw = _int(row.get("PointWinner", 0))
        if pw == 1:
            p1_after = min(p1_pts + 1, 4)
            p2_after = p2_pts
        elif pw == 2:
            p1_after = p1_pts
            p2_after = min(p2_pts + 1, 4)
        else:
            continue

        state_after = {
            "sets_won_a": sets_a, "sets_won_b": sets_b,
            "games_won_a": ga, "games_won_b": gb,
            "points_won_a": p1_after if not in_tb else 0,
            "points_won_b": p2_after if not in_tb else 0,
            "in_tiebreak": in_tb,
            "tb_points_a": p1_after if in_tb else 0,
            "tb_points_b": p2_after if in_tb else 0,
            "server": server,
        }

        transitions.append({"state_before": state_before, "state_after": state_after})

    return transitions


# ---------------------------------------------------------------------------
# Build P(S) table with Bayesian shrinkage
# ---------------------------------------------------------------------------

def build_ps_table(counts_df: pd.DataFrame, best_of: int, serve_hold: float) -> pd.DataFrame:
    if counts_df.empty:
        return pd.DataFrame(columns=["state_key", "wins_a", "count", "emp_p", "cf_p", "p_s"])

    rows = []
    for _, row in counts_df.iterrows():
        key = row["state_key"]
        wins = int(row["wins_a"])
        n = int(row["count"])
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
            "state_key": key, "wins_a": wins, "count": n,
            "emp_p": round(emp_p, 6), "cf_p": round(cf_p, 6), "p_s": round(p_s, 6),
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=== PM-Tennis Sackmann P(S) table builder v2 ===")
    build_start = datetime.now(timezone.utc)
    build_log = {
        "built_at": build_start.isoformat(),
        "builder_version": 2,
        "tables": {},
        "warnings": [],
    }

    try:
        zf_pbp = download_zip(ARCHIVES["pointbypoint"])
    except Exception as e:
        log.error("Failed to download pointbypoint: %s", e)
        build_log["warnings"].append(str(e))
        zf_pbp = None

    try:
        zf_slam = download_zip(ARCHIVES["slam_pointbypoint"])
    except Exception as e:
        log.error("Failed to download slam: %s", e)
        build_log["warnings"].append(str(e))
        zf_slam = None

    tables_built = 0

    # Men's best-of-3
    if zf_pbp:
        counts = parse_pointbypoint_zip(zf_pbp, gender="atp", best_of=3)
        table = build_ps_table(counts, best_of=3, serve_hold=TOUR_SERVE_HOLD["atp_bo3"])
        out = OUT_DIR / "P_S_best_of_3_mens.parquet"
        table.to_parquet(out, index=False)
        total = int(counts["count"].sum()) if not counts.empty else 0
        log.info("Wrote %s (%d states, %d transitions)", out, len(table), total)
        build_log["tables"]["P_S_best_of_3_mens"] = {"state_count": len(table), "total_transitions": total}
        tables_built += 1

    # Women's best-of-3
    counts_wta = pd.DataFrame(columns=["state_key", "wins_a", "count"])
    if zf_pbp:
        counts_wta = parse_pointbypoint_zip(zf_pbp, gender="wta", best_of=3)
    if zf_slam:
        cw = parse_slam_zip(zf_slam, gender="wta")
        if not cw.empty:
            counts_wta = pd.concat([counts_wta, cw]).groupby("state_key", as_index=False).sum()
    if not counts_wta.empty:
        table = build_ps_table(counts_wta, best_of=3, serve_hold=TOUR_SERVE_HOLD["wta_bo3"])
        out = OUT_DIR / "P_S_best_of_3_womens.parquet"
        table.to_parquet(out, index=False)
        total = int(counts_wta["count"].sum())
        log.info("Wrote %s (%d states, %d transitions)", out, len(table), total)
        build_log["tables"]["P_S_best_of_3_womens"] = {"state_count": len(table), "total_transitions": total}
        tables_built += 1

    # Men's best-of-5
    if zf_slam:
        cm = parse_slam_zip(zf_slam, gender="atp")
        if not cm.empty:
            table = build_ps_table(cm, best_of=5, serve_hold=TOUR_SERVE_HOLD["atp_bo5"])
            out = OUT_DIR / "P_S_best_of_5_mens.parquet"
            table.to_parquet(out, index=False)
            total = int(cm["count"].sum())
            log.info("Wrote %s (%d states, %d transitions)", out, len(table), total)
            build_log["tables"]["P_S_best_of_5_mens"] = {"state_count": len(table), "total_transitions": total}
            tables_built += 1
        else:
            build_log["warnings"].append("No men's Slam data parsed")

    build_log["tables_built"] = tables_built
    build_log["elapsed_seconds"] = round(
        (datetime.now(timezone.utc) - build_start).total_seconds(), 1)

    log_path = OUT_DIR / "build_log.json"
    with open(log_path, "w") as f:
        json.dump(build_log, f, indent=2)

    log.info("=== Build complete: %d tables in %.1fs ===",
             tables_built, build_log["elapsed_seconds"])
    print(json.dumps(build_log, indent=2))


if __name__ == "__main__":
    main()
