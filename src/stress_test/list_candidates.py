"""
list_candidates — operator-facing helper that prints eligible probe candidates
from Phase 2's meta.json archive.

This module exists to replace the multi-line shell snippet that was previously
documented in Runbook RB-002 §5.1. That snippet was pasted into the
pm-tennis-api Render Shell to list eligible probe candidates before the
operator passed a chosen slug to the probe via --slug. In practice (H-015)
the multi-line paste failed twice due to bracketed-paste escape markers
(^[[200~ wrapping the first token), making bash interpret the prefix as a
non-existent filename. A single-shot, single-line invocation avoids that
failure mode entirely:

    python -m src.stress_test.list_candidates

WHAT IT DOES

Calls slug_selector.list_candidates() and prints each candidate as one
human-readable line on stdout, freshest first (by discovered_at). The output
shape matches what the RB-002 §5.1 snippet produced so RB-002 step 5 reads
the same way as before:

    {event_id}  {market_slug}  discovered_at={...}  event_date={...}  '{title}'

Default output limit is 5 (matches the prior snippet). Override with --limit.

WHAT IT DOES NOT DO

- Does not invoke the probe. Selecting a slug and running the probe are two
  separate steps in the two-shell workflow (RB-002 §5).
- Does not modify any file. Read-only against /data/matches/.
- Does not require credentials or network. It is a local filesystem read.
- Does not touch Phase 2 code.

NOTES

- This module is invoked from the pm-tennis-api Render Shell, where /data
  is attached, NOT from the pm-tennis-stress-test service (which has no
  disk per D-027). On the stress-test service this script will print zero
  candidates, the same way slug_selector.list_candidates() returns []
  there.
- If the listing is empty on pm-tennis-api, that is meaningful: either no
  active pre-match tennis events exist in the next ~24h (operator-confirmed
  calendar block), OR the meta.json files have empty event_date fields and
  are being rejected by the date filter (RAID I-016, surfaced at H-015).
  The empty-list output is silent on which; for I-016 investigation use
  --show-rejected to see why each meta.json was filtered out.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional, TextIO

from src.stress_test import slug_selector
from src.stress_test.slug_selector import (
    DATA_ROOT,
    ProbeCandidate,
    _candidate_from_meta,
    _iter_meta_files,
    _load_meta,
    _passes_date_filter,
    _passes_status_filter,
)

log = logging.getLogger(__name__)


# Exit codes.
EXIT_OK = 0
EXIT_NO_CANDIDATES = 11  # matches probe.py's EXIT_NO_CANDIDATE convention
EXIT_BAD_USAGE = 2       # argparse default for unrecognized args


def _format_candidate(c: ProbeCandidate) -> str:
    """One human-readable line per candidate.

    Matches the format the RB-002 §5.1 snippet emitted, so the operator
    sees the same shape they're used to.
    """
    return (
        f"{c.event_id}  {c.market_slug}  "
        f"discovered_at={c.discovered_at}  "
        f"event_date={c.event_date}  "
        f"{c.title!r}"
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src.stress_test.list_candidates",
        description=(
            "List eligible probe candidates from Phase 2's meta.json "
            "archive. Use this to pick a slug for the stress-test probe; "
            "see Runbook RB-002 §5.1."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of candidates to print (default: 5).",
    )
    parser.add_argument(
        "--show-rejected",
        action="store_true",
        help=(
            "Also print, per-file, which filter rejected each meta.json "
            "(status / date / slug). Useful for investigating empty-list "
            "results (RAID I-016)."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help=(
            "Emit one JSON object per candidate, one per line, instead of "
            "the human-readable format. For scripting."
        ),
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: WARNING — keeps stdout clean).",
    )
    return parser


def _print_candidates(
    candidates: list[ProbeCandidate],
    *,
    limit: int,
    json_mode: bool,
    out: TextIO,
) -> None:
    """Print up to `limit` candidates to `out`."""
    for c in candidates[:limit]:
        if json_mode:
            print(
                json.dumps(
                    {
                        "event_id": c.event_id,
                        "market_slug": c.market_slug,
                        "discovered_at": c.discovered_at,
                        "event_date": c.event_date,
                        "title": c.title,
                    }
                ),
                file=out,
            )
        else:
            print(_format_candidate(c), file=out)


def _diagnose_rejections(
    data_root: Optional[Path] = None,
    today: Optional[date] = None,
    out: TextIO = sys.stderr,
) -> None:
    """Walk every meta.json and print which filter rejected each one.

    For investigating empty-list results (RAID I-016). Prints to stderr by
    default so it does not interleave with the candidate stdout output.
    Output shape per line:

        {path}  status_pass={bool}  date_pass={bool}  has_slug={bool}

    A meta.json that prints status_pass=True date_pass=True has_slug=True
    but is not in the candidates list indicates a bug.
    """
    root = (data_root if data_root is not None else DATA_ROOT) / "matches"
    now_date = today if today is not None else datetime.now(timezone.utc).date()

    for path in _iter_meta_files(root):
        meta = _load_meta(path)
        if meta is None:
            print(f"{path}  PARSE_ERROR", file=out)
            continue
        status_pass = _passes_status_filter(meta)
        date_pass = _passes_date_filter(meta, now_date)
        has_slug = _candidate_from_meta(meta) is not None
        # Surface the actual event_date value for I-016 diagnosis.
        event_date_val = meta.get("event_date", "<missing>")
        print(
            f"{path}  status_pass={status_pass}  date_pass={date_pass}  "
            f"has_slug={has_slug}  event_date={event_date_val!r}",
            file=out,
        )


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point. Returns exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    if args.limit < 0:
        print("--limit must be non-negative", file=sys.stderr)
        return EXIT_BAD_USAGE

    candidates = slug_selector.list_candidates()
    _print_candidates(
        candidates,
        limit=args.limit,
        json_mode=args.json,
        out=sys.stdout,
    )

    if args.show_rejected:
        print(
            f"--- show-rejected: scanning {DATA_ROOT}/matches ---",
            file=sys.stderr,
        )
        _diagnose_rejections(out=sys.stderr)

    if not candidates:
        # Print diagnostic to stderr; keep stdout empty for scriptability.
        print(
            f"No eligible probe candidates under {DATA_ROOT}/matches "
            f"(active=True, ended=False, live=False, event_date>=today UTC). "
            f"Re-run with --show-rejected to see per-file filter results.",
            file=sys.stderr,
        )
        return EXIT_NO_CANDIDATES

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
