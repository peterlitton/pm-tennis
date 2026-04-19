"""
Unit tests for src.stress_test.list_candidates.

Scope: argparse, output formatting, exit codes, the diagnostic
--show-rejected mode, and integration with slug_selector.list_candidates()
against tmp_path fixtures. No SDK, no network.

These tests deliberately reuse slug_selector's fixture pattern (same
_meta() helper shape, same data_root fixture) so the two modules' tests
read consistently.
"""

from __future__ import annotations

import io
import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from src.stress_test import list_candidates as lc
from src.stress_test import slug_selector
from src.stress_test.slug_selector import ProbeCandidate


# ---------------------------------------------------------------------------
# Fixture helpers (mirror tests/test_stress_test_slug_selector.py)
# ---------------------------------------------------------------------------


def _meta(
    event_id: str,
    *,
    slug: str = "aec-atp-test-2026-04-25",
    discovered_at: str = "2026-04-19T14:00:00+00:00",
    event_date: str = "2026-04-25",
    active: bool = True,
    ended: bool = False,
    live: bool = False,
    markets: list[dict] | None = None,
    title: str = "Test A vs Test B",
    **extra: Any,
) -> dict:
    if markets is None:
        markets = [
            {
                "market_id": f"mkt-{event_id}",
                "market_slug": slug,
                "active": active,
                "closed": ended,
            }
        ]
    out = {
        "event_id": event_id,
        "title": title,
        "event_date": event_date,
        "moneyline_markets": markets,
        "active_at_discovery": active,
        "ended_at_discovery": ended,
        "live_at_discovery": live,
        "discovered_at": discovered_at,
    }
    out.update(extra)
    return out


def _write_meta(root: Path, meta: dict) -> Path:
    p = root / "matches" / meta["event_id"] / "meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta), encoding="utf-8")
    return p


@pytest.fixture
def data_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fresh data root per test. Patches both the env var and the module-
    level DATA_ROOT in slug_selector AND list_candidates, since
    list_candidates re-imports DATA_ROOT at module load."""
    monkeypatch.setenv("PMTENNIS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(slug_selector, "DATA_ROOT", tmp_path)
    monkeypatch.setattr(lc, "DATA_ROOT", tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def test_parser_default_limit_is_5() -> None:
    parser = lc._build_parser()
    args = parser.parse_args([])
    assert args.limit == 5
    assert args.show_rejected is False
    assert args.json is False


def test_parser_accepts_limit_override() -> None:
    parser = lc._build_parser()
    args = parser.parse_args(["--limit", "10"])
    assert args.limit == 10


def test_parser_accepts_show_rejected_flag() -> None:
    parser = lc._build_parser()
    args = parser.parse_args(["--show-rejected"])
    assert args.show_rejected is True


def test_parser_accepts_json_flag() -> None:
    parser = lc._build_parser()
    args = parser.parse_args(["--json"])
    assert args.json is True


def test_parser_rejects_unknown_flag() -> None:
    parser = lc._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--definitely-not-a-flag"])


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------


def test_format_candidate_matches_rb002_snippet_shape() -> None:
    """The output line must look the same as the RB-002 §5.1 snippet's
    print() did, so the operator's mental model doesn't change."""
    c = ProbeCandidate(
        event_id="9999",
        market_slug="aec-atp-foo-bar-2026-04-25",
        discovered_at="2026-04-19T14:00:00+00:00",
        event_date="2026-04-25",
        title="Foo Bar vs Baz Qux",
    )
    line = lc._format_candidate(c)
    assert "9999" in line
    assert "aec-atp-foo-bar-2026-04-25" in line
    assert "discovered_at=2026-04-19T14:00:00+00:00" in line
    assert "event_date=2026-04-25" in line
    assert "'Foo Bar vs Baz Qux'" in line  # repr() form, matches snippet


def test_print_candidates_human_format_one_line_per_candidate() -> None:
    candidates = [
        ProbeCandidate("1", "slug-1", "t1", "2026-04-25", "A v B"),
        ProbeCandidate("2", "slug-2", "t2", "2026-04-26", "C v D"),
    ]
    out = io.StringIO()
    lc._print_candidates(candidates, limit=5, json_mode=False, out=out)
    lines = out.getvalue().strip().split("\n")
    assert len(lines) == 2
    assert "slug-1" in lines[0]
    assert "slug-2" in lines[1]


def test_print_candidates_json_format_emits_one_object_per_line() -> None:
    candidates = [
        ProbeCandidate("1", "slug-1", "t1", "2026-04-25", "A v B"),
        ProbeCandidate("2", "slug-2", "t2", "2026-04-26", "C v D"),
    ]
    out = io.StringIO()
    lc._print_candidates(candidates, limit=5, json_mode=True, out=out)
    lines = out.getvalue().strip().split("\n")
    assert len(lines) == 2
    obj0 = json.loads(lines[0])
    obj1 = json.loads(lines[1])
    assert obj0["event_id"] == "1"
    assert obj0["market_slug"] == "slug-1"
    assert obj0["event_date"] == "2026-04-25"
    assert obj0["title"] == "A v B"
    assert obj1["event_id"] == "2"


def test_print_candidates_respects_limit() -> None:
    candidates = [
        ProbeCandidate(str(i), f"slug-{i}", f"t{i}", "2026-04-25", "x") for i in range(10)
    ]
    out = io.StringIO()
    lc._print_candidates(candidates, limit=3, json_mode=False, out=out)
    lines = out.getvalue().strip().split("\n")
    assert len(lines) == 3


def test_print_candidates_limit_zero_prints_nothing() -> None:
    candidates = [ProbeCandidate("1", "slug-1", "t1", "2026-04-25", "x")]
    out = io.StringIO()
    lc._print_candidates(candidates, limit=0, json_mode=False, out=out)
    assert out.getvalue() == ""


def test_print_candidates_handles_empty_list() -> None:
    out = io.StringIO()
    lc._print_candidates([], limit=5, json_mode=False, out=out)
    assert out.getvalue() == ""


# ---------------------------------------------------------------------------
# Integration: main() against fixture data
# ---------------------------------------------------------------------------


def test_main_returns_ok_with_eligible_candidates(
    data_root: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A normal happy path: 2 eligible meta.json files on disk."""
    # Pick a today before the fixture event_date so the date filter passes.
    monkeypatch.setattr(
        "src.stress_test.slug_selector.datetime",
        _FrozenDatetime(date(2026, 4, 19)),
    )
    _write_meta(data_root, _meta("100"))
    _write_meta(data_root, _meta("200", slug="aec-wta-other-2026-04-26"))

    rc = lc.main([])
    captured = capsys.readouterr()

    assert rc == lc.EXIT_OK
    lines = captured.out.strip().split("\n")
    assert len(lines) == 2
    # Output is sorted freshest-first by discovered_at; both fixtures share
    # the default discovered_at so sort is non-strict — just check both
    # event_ids appear.
    out_text = captured.out
    assert "100" in out_text
    assert "200" in out_text


def test_main_returns_no_candidates_exit_when_disk_empty(
    data_root: Path,
    capsys: pytest.CaptureFixture,
) -> None:
    """No meta.json on disk → EXIT_NO_CANDIDATES + diagnostic on stderr."""
    rc = lc.main([])
    captured = capsys.readouterr()
    assert rc == lc.EXIT_NO_CANDIDATES
    assert captured.out == ""
    assert "No eligible probe candidates" in captured.err


def test_main_returns_no_candidates_when_all_filtered_out(
    data_root: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The I-016 scenario: meta.json files exist but event_date is empty."""
    monkeypatch.setattr(
        "src.stress_test.slug_selector.datetime",
        _FrozenDatetime(date(2026, 4, 19)),
    )
    _write_meta(data_root, _meta("100", event_date=""))
    _write_meta(data_root, _meta("200", event_date=""))

    rc = lc.main([])
    captured = capsys.readouterr()
    assert rc == lc.EXIT_NO_CANDIDATES
    assert captured.out == ""


def test_main_json_mode_emits_parseable_json(
    data_root: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.stress_test.slug_selector.datetime",
        _FrozenDatetime(date(2026, 4, 19)),
    )
    _write_meta(data_root, _meta("100"))

    rc = lc.main(["--json"])
    captured = capsys.readouterr()

    assert rc == lc.EXIT_OK
    obj = json.loads(captured.out.strip())
    assert obj["event_id"] == "100"
    assert obj["market_slug"] == "aec-atp-test-2026-04-25"


def test_main_limit_truncates_output(
    data_root: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.stress_test.slug_selector.datetime",
        _FrozenDatetime(date(2026, 4, 19)),
    )
    for i in range(10):
        _write_meta(data_root, _meta(str(i), slug=f"aec-atp-slug-{i}-2026-04-25"))

    rc = lc.main(["--limit", "3"])
    captured = capsys.readouterr()
    assert rc == lc.EXIT_OK
    lines = [ln for ln in captured.out.strip().split("\n") if ln]
    assert len(lines) == 3


def test_main_negative_limit_rejected() -> None:
    rc = lc.main(["--limit", "-1"])
    assert rc == lc.EXIT_BAD_USAGE


# ---------------------------------------------------------------------------
# --show-rejected diagnostic mode (I-016 investigation aid)
# ---------------------------------------------------------------------------


def test_diagnose_rejections_reports_per_file_status(
    data_root: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Three meta.json files: one passes, one fails status, one fails date."""
    _write_meta(data_root, _meta("pass"))                                  # passes all
    _write_meta(data_root, _meta("fail-status", live=True))                # fails status
    _write_meta(data_root, _meta("fail-date", event_date=""))              # fails date

    out = io.StringIO()
    lc._diagnose_rejections(today=date(2026, 4, 19), out=out)
    text = out.getvalue()

    # All three files are mentioned.
    assert "pass" in text
    assert "fail-status" in text
    assert "fail-date" in text
    # The pass case shows status_pass=True date_pass=True.
    pass_line = [ln for ln in text.split("\n") if "/pass/" in ln][0]
    assert "status_pass=True" in pass_line
    assert "date_pass=True" in pass_line
    # The status-fail case shows status_pass=False.
    status_line = [ln for ln in text.split("\n") if "/fail-status/" in ln][0]
    assert "status_pass=False" in status_line
    # The date-fail case shows date_pass=False AND surfaces the empty
    # event_date value (this is the I-016 diagnostic signal).
    date_line = [ln for ln in text.split("\n") if "/fail-date/" in ln][0]
    assert "date_pass=False" in date_line
    assert "event_date=''" in date_line


def test_diagnose_rejections_handles_unparseable_meta(
    data_root: Path,
) -> None:
    """A garbled meta.json prints PARSE_ERROR; doesn't crash the scan."""
    p = data_root / "matches" / "garbled" / "meta.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("{not valid json", encoding="utf-8")

    out = io.StringIO()
    lc._diagnose_rejections(today=date(2026, 4, 19), out=out)
    assert "PARSE_ERROR" in out.getvalue()


def test_main_show_rejected_writes_to_stderr_only(
    data_root: Path,
    capsys: pytest.CaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """--show-rejected output goes to stderr, not stdout; stdout stays
    parseable for scripting."""
    monkeypatch.setattr(
        "src.stress_test.slug_selector.datetime",
        _FrozenDatetime(date(2026, 4, 19)),
    )
    _write_meta(data_root, _meta("100"))
    _write_meta(data_root, _meta("rejected", event_date=""))

    rc = lc.main(["--show-rejected"])
    captured = capsys.readouterr()

    assert rc == lc.EXIT_OK
    # Stdout: only the 1 eligible candidate.
    stdout_lines = [ln for ln in captured.out.strip().split("\n") if ln]
    assert len(stdout_lines) == 1
    assert "100" in stdout_lines[0]
    assert "rejected" not in captured.out
    # Stderr: contains the per-file diagnostic for both.
    assert "100" in captured.err
    assert "rejected" in captured.err


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _FrozenDatetime:
    """Stand-in for slug_selector.datetime that pins now() to a fixed date.

    list_candidates() inside slug_selector calls
    datetime.now(timezone.utc).date() if the today= kwarg isn't passed.
    Patching the bound name lets us freeze time without touching real
    system time.
    """

    def __init__(self, today: date) -> None:
        self._today = today

    def now(self, tz=None):  # noqa: ARG002 - tz arg is for signature compat
        return _FrozenDateTimeNow(self._today)


class _FrozenDateTimeNow:
    def __init__(self, today: date) -> None:
        self._today = today

    def date(self) -> date:
        return self._today
