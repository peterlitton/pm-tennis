"""
CLI tests for src.stress_test.probe.

Scope: exercise argument parsing, the D-027 slug-source precedence in
run_probe(), and the early-return paths (config error, no candidate) that
do not touch the network or the SDK client constructor.

We deliberately do NOT test the live probe path by mocking the SDK. Per
H-012 addendum guidance and H-008 post-mortem: mocking the polymarket-us
SDK methods would hide exactly the drift class that killed H-008 (symbols
that don't exist, wrong method signatures, wrong wire shapes). The probe's
network-touching path is exercised in H-014 against the live gateway.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.stress_test import probe, slug_selector


# ---------------------------------------------------------------------------
# Argparse
# ---------------------------------------------------------------------------


def test_parser_accepts_probe_flag() -> None:
    parser = probe._build_parser()
    args = parser.parse_args(["--probe"])
    assert args.probe is True
    assert args.slug is None
    assert args.event_id is None


def test_parser_accepts_slug_and_event_id() -> None:
    parser = probe._build_parser()
    args = parser.parse_args(
        ["--probe", "--slug", "aec-atp-test-2026-05-01", "--event-id", "12345"]
    )
    assert args.probe is True
    assert args.slug == "aec-atp-test-2026-05-01"
    assert args.event_id == "12345"


def test_parser_defaults_no_probe() -> None:
    """Without --probe the default is self-check (probe=False)."""
    parser = probe._build_parser()
    args = parser.parse_args([])
    assert args.probe is False


# ---------------------------------------------------------------------------
# run_probe config-error path — credentials missing
# ---------------------------------------------------------------------------


def test_run_probe_returns_config_error_when_creds_missing(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)

    rc = probe.run_probe(cli_slug="aec-test", cli_event_id="test-ev")

    assert rc == probe.EXIT_CONFIG_ERROR
    err = capsys.readouterr().err
    assert "config error" in err.lower()
    # Make sure the error names the variables (by name, not value).
    assert "POLYMARKET_US_API_KEY_ID" in err
    assert "POLYMARKET_US_API_SECRET_KEY" in err


# ---------------------------------------------------------------------------
# run_probe EXIT_NO_CANDIDATE path — no --slug, no disk fallback
# ---------------------------------------------------------------------------


def test_run_probe_exit_no_candidate_when_slug_missing_and_disk_empty(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Creds present so we get past the config check.
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-key-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    # Disk root exists but contains no matches/ subdir.
    monkeypatch.setenv("PMTENNIS_DATA_ROOT", str(tmp_path))
    monkeypatch.setattr(slug_selector, "DATA_ROOT", tmp_path)

    rc = probe.run_probe(cli_slug=None, cli_event_id=None)

    assert rc == probe.EXIT_NO_CANDIDATE
    err = capsys.readouterr().err
    assert "no --slug provided" in err or "no probe candidates" in err
    # Fallback-was-attempted language should appear (D-027 informational path).
    assert "D-027" in err or "slug_selector" in err


# ---------------------------------------------------------------------------
# run_probe short-circuit: --slug present but creds missing => config error,
# NOT NO_CANDIDATE. Verifies the precedence: config is checked before the
# slug-source branch.
# ---------------------------------------------------------------------------


def test_run_probe_config_check_precedes_slug_branch(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)

    rc = probe.run_probe(cli_slug="some-slug", cli_event_id="some-event")

    # Expected: we fail on config before we ever consider the slug.
    assert rc == probe.EXIT_CONFIG_ERROR


# ---------------------------------------------------------------------------
# main() dispatch
# ---------------------------------------------------------------------------


def test_main_defaults_to_self_check(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main() with no --probe argv delegates to run_self_check."""
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)

    rc = probe.main([])

    # Self-check completes OK regardless of missing creds / missing disk.
    assert rc == probe.EXIT_OK
    err = capsys.readouterr().err
    assert "self-check" in err.lower()


def test_main_probe_flag_routes_to_run_probe(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """main(['--probe']) with no creds hits the config-error path in run_probe.

    Confirms main() dispatches to run_probe, not run_self_check, when --probe
    is passed.
    """
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)

    rc = probe.main(["--probe", "--slug", "x"])

    assert rc == probe.EXIT_CONFIG_ERROR
    err = capsys.readouterr().err
    # Probe mode banner differs from self-check banner.
    assert "probe" in err.lower()
    assert "self-check" not in err.lower()


# ---------------------------------------------------------------------------
# ProbeOutcome dataclass smoke — fields default correctly
# ---------------------------------------------------------------------------


def test_probe_outcome_defaults() -> None:
    outcome = probe.ProbeOutcome()
    assert outcome.classification == ""
    assert outcome.message_count_by_event == {}
    assert outcome.error_events == []
    assert outcome.close_events == []
    assert outcome.connected is False
    assert outcome.subscribe_sent is False


def test_probe_outcome_json_round_trip() -> None:
    """asdict(outcome) must be JSON-serializable — it's what we print on
    stdout at end of probe run."""
    from dataclasses import asdict

    outcome = probe.ProbeOutcome(
        probe_started_at_utc="2026-04-19T20:00:00+00:00",
        market_slug="aec-test",
        event_id="1234",
        classification="accepted",
        message_count_by_event={"market_data": 5, "heartbeat": 2},
    )
    serialized = json.dumps(asdict(outcome), default=str)
    reloaded: Any = json.loads(serialized)
    assert reloaded["market_slug"] == "aec-test"
    assert reloaded["classification"] == "accepted"
    assert reloaded["message_count_by_event"]["market_data"] == 5


# ---------------------------------------------------------------------------
# Classification → exit code mapping
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "classification,expected",
    [
        ("accepted", probe.EXIT_OK),
        ("rejected", probe.EXIT_PROBE_REJECTED),
        ("ambiguous", probe.EXIT_PROBE_AMBIGUOUS),
        ("exception", probe.EXIT_PROBE_EXCEPTION),
        ("", probe.EXIT_PROBE_AMBIGUOUS),  # fallback
        ("unknown-classification", probe.EXIT_PROBE_AMBIGUOUS),  # fallback
    ],
)
def test_classification_to_exit_code(classification: str, expected: int) -> None:
    assert probe._classification_to_exit_code(classification) == expected


# ---------------------------------------------------------------------------
# ProbeConfig: observation-seconds sanity clamping
# ---------------------------------------------------------------------------


def test_load_probe_config_uses_default_observation_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "k")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "s")
    monkeypatch.delenv("PROBE_OBSERVATION_SECONDS", raising=False)
    cfg = probe.load_probe_config()
    assert cfg.observation_seconds == probe.DEFAULT_OBSERVATION_SECONDS


def test_load_probe_config_clamps_nonsense_observation_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "k")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "s")
    # negative => clamped to default
    monkeypatch.setenv("PROBE_OBSERVATION_SECONDS", "-5")
    cfg = probe.load_probe_config()
    assert cfg.observation_seconds == probe.DEFAULT_OBSERVATION_SECONDS
    # above-ceiling => clamped to default
    monkeypatch.setenv("PROBE_OBSERVATION_SECONDS", "99999")
    cfg = probe.load_probe_config()
    assert cfg.observation_seconds == probe.DEFAULT_OBSERVATION_SECONDS
    # unparseable => default
    monkeypatch.setenv("PROBE_OBSERVATION_SECONDS", "not-a-float")
    cfg = probe.load_probe_config()
    assert cfg.observation_seconds == probe.DEFAULT_OBSERVATION_SECONDS


def test_load_probe_config_accepts_valid_observation_seconds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "k")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "s")
    monkeypatch.setenv("PROBE_OBSERVATION_SECONDS", "7.5")
    cfg = probe.load_probe_config()
    assert cfg.observation_seconds == 7.5
