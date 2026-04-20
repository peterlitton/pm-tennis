"""
Unit tests for src.stress_test.sweeps.

Scope: everything that happens in memory and in argument parsing, no SDK
network calls, no client construction. The sweeps harness's network-
touching path (_run_cell_async, _fetch_anchor_slug, _run_sweep_async) is
exercised in H-021 against the live gateway, not here — mocking the
polymarket-us SDK surfaces would hide exactly the drift class that killed
H-008 (symbols that don't exist, wrong method signatures, wrong wire
shapes). Per D-021 and the H-012 addendum, the SDK is imported by the
tests only for exception-class construction; no method is called.

Tests are organized into sections:
  - CLI parser
  - Config loading
  - Grid enumeration and filtering
  - Placeholder-slug synthesis
  - Outcome record dataclasses and serialization
  - Classification state machine (the 15 sanity checks from H-020
    checkpoint 2, plus the D-032 anchor-zero regression)
  - D-033 per-exception-type regression tests
  - Aggregate helpers
  - M-resolver helpers
  - Self-check mode
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

import httpx
import pytest

from src.stress_test import sweeps
from src.stress_test.sweeps import (
    CellSpec,
    ConnectionObservation,
    SubscribeObservation,
    SweepCellOutcome,
    SweepConfig,
    SweepRunOutcome,
)


# ---------------------------------------------------------------------------
# Test-factory helpers — parallel the sanity-check helpers from H-020
# checkpoint 2. Exported at module level so every test can reach them.
# ---------------------------------------------------------------------------


def _make_sub(
    *,
    subscribe_sent: bool,
    real_slug: str = "aec-atp-real-2026-04-21",
    msg_counts: dict[str, int] | None = None,
    per_slug_counts: dict[str, int] | None = None,
    request_id: str = "test-req",
) -> SubscribeObservation:
    """Build one SubscribeObservation for classifier/aggregator tests."""
    return SubscribeObservation(
        request_id=request_id,
        subscribe_sent=subscribe_sent,
        slugs=["a", "b"],
        real_slug=real_slug,
        placeholder_slugs_count=1 if real_slug else 2,
        message_count_by_event=msg_counts or {},
        per_slug_message_counts=per_slug_counts or {},
    )


def _make_cell(
    *,
    axis: str = "subscriptions",
    axis_value: int = 1,
    subs: list[SubscribeObservation],
    connections_connected: bool = True,
    error_events: list[str] | None = None,
    close_events: list[str] | None = None,
    exception_type: str = "",
    exception_message: str = "",
    n_connections: int = 1,
) -> SweepCellOutcome:
    """Build one SweepCellOutcome for classifier tests."""
    if n_connections == 1:
        conns = [
            ConnectionObservation(
                connection_index=0,
                connected=connections_connected,
                subscribe_calls=subs,
                error_events=error_events or [],
                close_events=close_events or [],
                closed_cleanly=True,
            )
        ]
    else:
        conns = []
        for i in range(n_connections):
            idx = i % len(subs)
            conns.append(
                ConnectionObservation(
                    connection_index=i,
                    connected=connections_connected,
                    subscribe_calls=[subs[idx]],
                    error_events=error_events or [],
                    close_events=close_events or [],
                    closed_cleanly=True,
                )
            )
    return SweepCellOutcome(
        sweep_id="sweep-test",
        cell_id=f"{axis}-axis-n{axis_value}",
        cell_axis=axis,
        cell_axis_value=axis_value,
        slugs_per_subscription=100,
        connections=conns,
        exception_type=exception_type,
        exception_message=exception_message,
    )


def _fake_response(status_code: int) -> httpx.Response:
    """Minimal httpx.Response for APIStatusError subclass constructors.

    The SDK's APIStatusError constructors require a response with a
    status_code and a request. We build a minimal one here rather than
    pulling in httpx mocking — we only need the object to satisfy the
    constructor, not to make any actual HTTP call.
    """
    return httpx.Response(
        status_code=status_code,
        request=httpx.Request(
            "POST", "https://api.polymarket.us/v1/ws/markets"
        ),
    )


# ===========================================================================
# CLI parser
# ===========================================================================


def test_parser_default_is_self_check() -> None:
    """Without --sweep, argparse produces sweep=None which dispatches to
    run_self_check() in main()."""
    parser = sweeps._build_parser()
    args = parser.parse_args([])
    assert args.sweep is None
    assert args.seed_slug is None
    assert args.log_level == "INFO"


def test_parser_accepts_sweep_subscriptions() -> None:
    parser = sweeps._build_parser()
    args = parser.parse_args(["--sweep=subscriptions"])
    assert args.sweep == "subscriptions"


def test_parser_accepts_sweep_connections() -> None:
    parser = sweeps._build_parser()
    args = parser.parse_args(["--sweep=connections"])
    assert args.sweep == "connections"


def test_parser_accepts_sweep_both() -> None:
    parser = sweeps._build_parser()
    args = parser.parse_args(["--sweep=both"])
    assert args.sweep == "both"


def test_parser_accepts_seed_slug() -> None:
    parser = sweeps._build_parser()
    args = parser.parse_args(
        ["--sweep=both", "--seed-slug=aec-atp-foo-2026-04-21"]
    )
    assert args.sweep == "both"
    assert args.seed_slug == "aec-atp-foo-2026-04-21"


def test_parser_rejects_invalid_sweep_value() -> None:
    """argparse's choices= should reject anything not in the enum."""
    parser = sweeps._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--sweep=invalid"])


def test_parser_rejects_invalid_log_level() -> None:
    parser = sweeps._build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--log-level=TRACE"])


# ===========================================================================
# Config loading
# ===========================================================================


def test_load_sweep_config_raises_on_missing_both_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)
    with pytest.raises(KeyError) as excinfo:
        sweeps.load_sweep_config()
    assert "POLYMARKET_US_API_KEY_ID" in str(excinfo.value)
    assert "POLYMARKET_US_API_SECRET_KEY" in str(excinfo.value)


def test_load_sweep_config_raises_on_missing_secret_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)
    with pytest.raises(KeyError) as excinfo:
        sweeps.load_sweep_config()
    assert "POLYMARKET_US_API_SECRET_KEY" in str(excinfo.value)
    # Key that IS set should not be in the error message.
    assert "POLYMARKET_US_API_KEY_ID" not in str(excinfo.value)


def test_load_sweep_config_uses_default_observation_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    monkeypatch.delenv("SWEEP_OBSERVATION_SECONDS", raising=False)
    cfg = sweeps.load_sweep_config()
    assert cfg.observation_seconds == sweeps.DEFAULT_OBSERVATION_SECONDS
    assert cfg.observation_seconds == 30.0


def test_load_sweep_config_honors_observation_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    monkeypatch.setenv("SWEEP_OBSERVATION_SECONDS", "60")
    cfg = sweeps.load_sweep_config()
    assert cfg.observation_seconds == 60.0


def test_load_sweep_config_clamps_under_floor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values below MIN_OBSERVATION_SECONDS fall back to default."""
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    monkeypatch.setenv("SWEEP_OBSERVATION_SECONDS", "0.5")
    cfg = sweeps.load_sweep_config()
    assert cfg.observation_seconds == sweeps.DEFAULT_OBSERVATION_SECONDS


def test_load_sweep_config_clamps_over_ceiling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Values above MAX_OBSERVATION_SECONDS fall back to default."""
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    monkeypatch.setenv("SWEEP_OBSERVATION_SECONDS", "9999")
    cfg = sweeps.load_sweep_config()
    assert cfg.observation_seconds == sweeps.DEFAULT_OBSERVATION_SECONDS


def test_load_sweep_config_handles_non_numeric_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-numeric env value falls back to default, does not raise."""
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    monkeypatch.setenv("SWEEP_OBSERVATION_SECONDS", "not-a-number")
    cfg = sweeps.load_sweep_config()
    assert cfg.observation_seconds == sweeps.DEFAULT_OBSERVATION_SECONDS


# ===========================================================================
# Grid enumeration and filtering
# ===========================================================================


def test_default_grid_size_and_m4_first() -> None:
    """§16.5 commits to the 8-cell grid: 1 M4 control + 4 subscriptions-
    axis + 3 connections-axis. M4 control must be first per H-020 ruling."""
    grid = sweeps.build_default_grid()
    assert len(grid) == 8
    assert grid[0].is_m4_control is True
    assert grid[0].cell_id == sweeps.M4_CONTROL_CELL_ID


def test_default_grid_every_cell_has_100_slugs() -> None:
    """§16.5 commits every cell to 100 slugs per subscription (either
    1 real + 99 placeholder or 0 real + 100 placeholder for M4 control)."""
    grid = sweeps.build_default_grid()
    for cell in grid:
        assert cell.slugs_per_subscription == 100


def test_default_grid_subscriptions_axis_values() -> None:
    """§16.5 committed subscriptions-axis: 1, 2, 5, 10."""
    grid = sweeps.build_default_grid()
    subs_cells = [c for c in grid if c.cell_axis == "subscriptions"]
    assert [c.cell_axis_value for c in subs_cells] == [1, 2, 5, 10]
    for c in subs_cells:
        assert c.connection_count == 1
        assert c.subscriptions_per_connection == c.cell_axis_value


def test_default_grid_connections_axis_values() -> None:
    """§16.5 committed connections-axis: 1, 2, 4."""
    grid = sweeps.build_default_grid()
    conn_cells = [c for c in grid if c.cell_axis == "connections"]
    assert [c.cell_axis_value for c in conn_cells] == [1, 2, 4]
    for c in conn_cells:
        assert c.subscriptions_per_connection == 1
        assert c.connection_count == c.cell_axis_value


def test_default_grid_m4_control_shape() -> None:
    """M4 control cell: 1 conn × 1 sub × 0 real + 100 placeholder."""
    grid = sweeps.build_default_grid()
    m4 = grid[0]
    assert m4.is_m4_control is True
    assert m4.connection_count == 1
    assert m4.subscriptions_per_connection == 1
    assert m4.real_slugs_per_subscription == 0
    assert m4.placeholder_slugs_per_subscription == 100
    assert m4.intended_subscribe_count == 1


def test_cell_spec_intended_subscribe_count() -> None:
    """intended_subscribe_count is N_connections × subs_per_connection."""
    cell = CellSpec(
        cell_id="test", cell_axis="subscriptions", cell_axis_value=5,
        connection_count=1, subscriptions_per_connection=5,
        real_slugs_per_subscription=1, placeholder_slugs_per_subscription=99,
    )
    assert cell.intended_subscribe_count == 5
    cell_conn = CellSpec(
        cell_id="test-conn", cell_axis="connections", cell_axis_value=4,
        connection_count=4, subscriptions_per_connection=1,
        real_slugs_per_subscription=1, placeholder_slugs_per_subscription=99,
    )
    assert cell_conn.intended_subscribe_count == 4


def test_filter_grid_subscriptions() -> None:
    grid = sweeps.build_default_grid()
    filtered = sweeps.filter_grid_by_sweep_selector(grid, "subscriptions")
    assert len(filtered) == 4
    assert all(c.cell_axis == "subscriptions" for c in filtered)


def test_filter_grid_connections() -> None:
    grid = sweeps.build_default_grid()
    filtered = sweeps.filter_grid_by_sweep_selector(grid, "connections")
    assert len(filtered) == 3
    assert all(c.cell_axis == "connections" for c in filtered)


def test_filter_grid_both_preserves_order_with_m4_first() -> None:
    """'both' selector returns full grid, M4 control first."""
    grid = sweeps.build_default_grid()
    filtered = sweeps.filter_grid_by_sweep_selector(grid, "both")
    assert len(filtered) == 8
    assert filtered[0].is_m4_control is True


def test_filter_grid_rejects_unknown_selector() -> None:
    grid = sweeps.build_default_grid()
    with pytest.raises(ValueError):
        sweeps.filter_grid_by_sweep_selector(grid, "invalid")


# ===========================================================================
# Placeholder-slug synthesis
# ===========================================================================


def test_placeholder_slug_format() -> None:
    """§16.5 synthesis: aec-ph-<abbrev_a>-<abbrev_b>-2099-12-31 shape.

    The format has three independent non-real signals per H-020 checkpoint
    1 ruling: the 'ph' tour token, 8-char abbreviations (longer than the
    ~6-char observed ceiling), and far-future date 2099-12-31.
    """
    slug = sweeps.synthesize_placeholder_slug("test-cell", 0, 0)
    parts = slug.split("-")
    # aec, ph, abbrev_a, abbrev_b, 2099, 12, 31 — seven parts
    assert len(parts) == 7
    assert parts[0] == "aec"
    assert parts[1] == sweeps.PLACEHOLDER_SLUG_TOUR
    assert len(parts[2]) == sweeps.PLACEHOLDER_SLUG_ABBREV_LEN
    assert len(parts[3]) == sweeps.PLACEHOLDER_SLUG_ABBREV_LEN
    # Date suffix 2099-12-31 split into 2099, 12, 31.
    assert parts[4] == "2099"
    assert parts[5] == "12"
    assert parts[6] == "31"


def test_placeholder_slug_is_deterministic() -> None:
    """Same (cell_id, sub_idx, slug_idx) tuple → same slug."""
    s1 = sweeps.synthesize_placeholder_slug("cell-a", 0, 0)
    s2 = sweeps.synthesize_placeholder_slug("cell-a", 0, 0)
    assert s1 == s2


def test_placeholder_slugs_are_unique_across_tuple_components() -> None:
    """Different (cell_id, sub_idx, slug_idx) tuples produce distinct slugs."""
    by_slug_idx = sweeps.synthesize_placeholder_slug("cell-a", 0, 1)
    by_sub_idx = sweeps.synthesize_placeholder_slug("cell-a", 1, 0)
    by_cell = sweeps.synthesize_placeholder_slug("cell-b", 0, 0)
    base = sweeps.synthesize_placeholder_slug("cell-a", 0, 0)
    assert len({base, by_slug_idx, by_sub_idx, by_cell}) == 4


def test_build_slug_list_for_default_cell_has_anchor_first() -> None:
    grid = sweeps.build_default_grid()
    default_cell = [c for c in grid if c.cell_axis == "subscriptions"][0]
    slugs = sweeps.build_slug_list_for_subscription(
        cell=default_cell,
        subscription_index=0,
        real_anchor_slug="aec-atp-real-2026-04-21",
    )
    assert len(slugs) == 100
    assert slugs[0] == "aec-atp-real-2026-04-21"
    # Remaining 99 are placeholders starting with aec-ph-
    for placeholder in slugs[1:]:
        assert placeholder.startswith("aec-ph-")


def test_build_slug_list_for_m4_control_has_all_placeholders() -> None:
    grid = sweeps.build_default_grid()
    m4 = grid[0]
    slugs = sweeps.build_slug_list_for_subscription(
        cell=m4,
        subscription_index=0,
        real_anchor_slug="should-not-appear",
    )
    assert len(slugs) == 100
    assert "should-not-appear" not in slugs
    for slug in slugs:
        assert slug.startswith("aec-ph-")


# ===========================================================================
# Outcome record dataclasses and serialization
# ===========================================================================


def test_subscribe_observation_defaults() -> None:
    """All fields default to empty/False/None so progressive population
    during cell execution works."""
    sub = SubscribeObservation()
    assert sub.request_id == ""
    assert sub.subscribe_sent is False
    assert sub.slugs == []
    assert sub.real_slug == ""
    assert sub.message_count_by_event == {}
    assert sub.first_message_latency_seconds is None


def test_connection_observation_defaults() -> None:
    conn = ConnectionObservation()
    assert conn.connection_index == 0
    assert conn.connected is False
    assert conn.subscribe_calls == []
    assert conn.error_events == []
    assert conn.close_events == []


def test_sweep_cell_outcome_defaults() -> None:
    cell = SweepCellOutcome()
    assert cell.cell_classification == ""
    assert cell.m1_resolution is None
    assert cell.m3_observations == {}


def test_sweep_run_outcome_serializes_to_json() -> None:
    """Full asdict → json.dumps round-trip works for the emitted stdout shape."""
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 3},
        per_slug_counts={"aec-atp-real-2026-04-21": 3},
    )
    cell = _make_cell(subs=[sub])
    cell.cell_classification = "clean"
    run = SweepRunOutcome(
        run_id="sweep-test-001",
        cells=[cell],
        run_classification="clean",
    )
    serialized = json.dumps(asdict(run), indent=2, default=str)
    # Round-trip parse to confirm valid JSON.
    parsed = json.loads(serialized)
    assert parsed["run_id"] == "sweep-test-001"
    assert parsed["run_classification"] == "clean"
    assert len(parsed["cells"]) == 1
    assert parsed["cells"][0]["cell_classification"] == "clean"


# ===========================================================================
# Classification state machine — H-020 checkpoint 2 sanity checks
# transcribed as standing regression suite (A-series sanity checks A1–A14;
# A15 aggregates tested in their own section below).
# ===========================================================================


def test_classify_step_1_api_timeout_error_is_exception() -> None:
    """Step 1: transport-class exception (APITimeoutError) → exception."""
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type="APITimeoutError",
        exception_message="request timed out",
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"
    assert "step 1" in reason


def test_classify_step_1_undocumented_exception_is_exception() -> None:
    """Step 1: undocumented type name → exception via catch-all."""
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type="SomethingNovelError",
        exception_message="unexpected",
    )
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"


@pytest.mark.parametrize(
    "exc_name",
    ["AuthenticationError", "BadRequestError", "NotFoundError", "RateLimitError"],
)
def test_classify_step_2_readme_documented_rejected_types(exc_name: str) -> None:
    """Step 2: each of the four README-documented rejected types routes to
    rejected via DOCUMENTED_REJECTED_EXCEPTION_TYPES."""
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=False)],
        exception_type=exc_name,
        exception_message="denied",
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 2" in reason


def test_classify_step_3_single_subscribe_ratio_zero_is_rejected() -> None:
    """Step 3: N=1 with subscribe failure (ratio 0) → rejected."""
    cell = _make_cell(subs=[_make_sub(subscribe_sent=False)])
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 3" in reason


def test_classify_step_3_n10_ratio_03_is_rejected() -> None:
    """Step 3: N=10 with only 3 subscribes succeeded (ratio 0.3) → rejected."""
    subs = [_make_sub(subscribe_sent=True)] * 3 + [_make_sub(subscribe_sent=False)] * 7
    cell = _make_cell(axis="subscriptions", axis_value=10, subs=subs)
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"


def test_classify_step_3_boundary_ratio_05_is_rejected() -> None:
    """Step 3 boundary: ratio exactly 0.5 → rejected (≤ is inclusive).

    Pins the §16.7 threshold direction. If a future revision makes the
    half-threshold exclusive, this test must be revised alongside §16.7.
    """
    subs = [_make_sub(subscribe_sent=True)] * 5 + [_make_sub(subscribe_sent=False)] * 5
    cell = _make_cell(axis="subscriptions", axis_value=10, subs=subs)
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"


def test_classify_step_4_ratio_above_half_below_one_is_degraded() -> None:
    """Step 4: 0.5 < ratio < 1.0 → degraded."""
    subs = [_make_sub(subscribe_sent=True)] * 6 + [_make_sub(subscribe_sent=False)] * 4
    cell = _make_cell(axis="subscriptions", axis_value=10, subs=subs)
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "degraded"
    assert "step 4" in reason


def test_classify_step_5_default_clean_requires_anchor_traffic() -> None:
    """Step 5 default cell clean: ratio 1.0, all connected, anchor traffic,
    no errors, no closes → clean. This is the baseline happy-path."""
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 5, "heartbeat": 2},
        per_slug_counts={"aec-atp-real-2026-04-21": 5},
    )
    cell = _make_cell(subs=[sub])
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "clean"
    # Reason cites D-032 since the clean-(iii) predicate is the Reading B
    # anchor-specific one.
    assert "D-032" in reason


def test_classify_step_5_m4_control_is_clean_without_traffic() -> None:
    """Step 5 M4 control: relaxed clean — subscribe succeeded, no errors,
    no closes; traffic not required per §16.7 M4 caveat."""
    m4_sub = SubscribeObservation(
        request_id="m4-req",
        subscribe_sent=True,
        slugs=["ph1", "ph2"],
        real_slug="",
        placeholder_slugs_count=2,
    )
    m4_cell = SweepCellOutcome(
        sweep_id="sweep-test",
        cell_id="m4-control-100p-0r",
        cell_axis="m4-control",
        cell_axis_value=1,
        slugs_per_subscription=100,
        connections=[
            ConnectionObservation(
                connection_index=0,
                connected=True,
                subscribe_calls=[m4_sub],
                closed_cleanly=True,
            )
        ],
    )
    label, reason = sweeps.classify_cell(m4_cell, is_m4_control=True)
    assert label == "clean"
    assert "M4 control" in reason


def test_classify_step_6_error_event_forces_degraded() -> None:
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 1},
        per_slug_counts={"aec-atp-real-2026-04-21": 1},
    )
    cell = _make_cell(subs=[sub], error_events=["<error payload>"])
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "degraded"
    assert "step 6" in reason
    assert "error_events" in reason


def test_classify_step_6_close_event_forces_degraded() -> None:
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 1},
        per_slug_counts={"aec-atp-real-2026-04-21": 1},
    )
    cell = _make_cell(subs=[sub], close_events=["<close payload>"])
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "degraded"
    assert "close_events" in reason


def test_d032_anchor_zero_traffic_regression() -> None:
    """D-032 regression: heartbeat-only traffic with zero anchor-slug
    traffic must classify as degraded at step 6.

    See DecisionJournal.md D-032 for the reading resolution. §16.7's
    Meaning column requires anchor-slug-specific traffic for clean-(iii);
    the Rule column's "across the cell" phrasing was imprecise
    transcription. Under Reading B, a cell with heartbeat traffic but
    zero anchor-slug traffic fails clean-(iii) at step 5 and fires the
    anchor-zero-traffic anomaly at step 6.

    If this test ever fails, D-032 has been silently reverted. See
    DecisionJournal.md D-032 for the resolution rationale before editing.
    """
    sub_no_anchor = _make_sub(
        subscribe_sent=True,
        # There IS qualifying traffic (heartbeat + market_data) at cell level...
        msg_counts={"market_data": 1, "heartbeat": 1},
        # ...but NONE of it attributed to the anchor slug.
        per_slug_counts={"some-other-slug": 1},
    )
    cell = _make_cell(subs=[sub_no_anchor])
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "degraded", (
        f"D-032 regression: heartbeat-only with zero anchor traffic should "
        f"be degraded, got {label!r}. See DJ D-032."
    )
    assert "anchor slug" in reason
    assert "step 6" in reason


def test_classify_step_6_m4_error_is_degraded() -> None:
    """M4 control cell with error event → degraded. The anchor-zero-traffic
    sub-check does not apply to M4 (no anchor); only error/close anomalies."""
    m4_err_sub = SubscribeObservation(
        request_id="m4-req",
        subscribe_sent=True,
        slugs=["ph"],
        real_slug="",
        placeholder_slugs_count=1,
    )
    m4_cell = SweepCellOutcome(
        sweep_id="sweep-test",
        cell_id="m4-control-100p-0r",
        cell_axis="m4-control",
        cell_axis_value=1,
        slugs_per_subscription=100,
        connections=[
            ConnectionObservation(
                connection_index=0,
                connected=True,
                subscribe_calls=[m4_err_sub],
                closed_cleanly=True,
                error_events=["<m4 error>"],
            )
        ],
    )
    label, _reason = sweeps.classify_cell(m4_cell, is_m4_control=True)
    assert label == "degraded"


def test_classify_step_7_edge_not_connected_with_ratio_one() -> None:
    """Step 7 fallthrough: ratio 1.0, anchor traffic present, no errors,
    no closes, but connections_connected False → ambiguous via step 7."""
    sub_good = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 1},
        per_slug_counts={"aec-atp-real-2026-04-21": 1},
    )
    cell = _make_cell(subs=[sub_good], connections_connected=False)
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "ambiguous"
    assert "step 7" in reason


# ===========================================================================
# D-033 per-exception-type regression tests
# ===========================================================================
# Each test constructs the minimal exception instance the classifier would
# see in live execution, using actual SDK classes from polymarket_us. The
# exception is recorded onto a cell outcome as (type(exc).__name__,
# str(exc)[:PREVIEW_TRUNCATION_CHARS]) — the same path _run_cell_async
# uses at runtime. classify_cell is invoked and the step-1 vs step-2
# assignment verified against the D-033 frozenset declarations.
#
# Pattern mirrors D-032's regression test (test_d032_anchor_zero_traffic_
# regression above). If any frozenset assignment is ever reverted, these
# tests fail with an immediate trace to D-033.


def test_d033_authentication_error_routes_to_rejected() -> None:
    """D-033: AuthenticationError (401) → DOCUMENTED_REJECTED_EXCEPTION_TYPES
    → step 2 rejected. See DJ D-033 for the five rejected-type assignments."""
    from polymarket_us import AuthenticationError
    exc = AuthenticationError("Authentication failed (401)", response=_fake_response(401))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 2" in reason


def test_d033_bad_request_error_routes_to_rejected() -> None:
    """D-033: BadRequestError (400) → step 2 rejected. See DJ D-033."""
    from polymarket_us import BadRequestError
    exc = BadRequestError("Bad request (400)", response=_fake_response(400))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 2" in reason


def test_d033_not_found_error_routes_to_rejected() -> None:
    """D-033: NotFoundError (404) → step 2 rejected. See DJ D-033."""
    from polymarket_us import NotFoundError
    exc = NotFoundError("Resource not found (404)", response=_fake_response(404))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 2" in reason


def test_d033_permission_denied_error_routes_to_rejected() -> None:
    """D-033: PermissionDeniedError (403) is a D-033 ADDITION to the
    rejected frozenset. Under the pre-D-033 README-only frozenset this
    would route via catch-all to exception; under D-033 it correctly
    routes to rejected alongside the four README-named 4xx siblings.

    If this test fails, D-033's PermissionDeniedError → rejected
    assignment has been reverted. See DJ D-033 for reasoning.
    """
    from polymarket_us import PermissionDeniedError
    exc = PermissionDeniedError("Permission denied (403)", response=_fake_response(403))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected", (
        f"D-033 PermissionDeniedError → rejected assignment reverted; "
        f"got {label!r}. See DJ D-033."
    )
    assert "step 2" in reason


def test_d033_rate_limit_error_routes_to_rejected() -> None:
    """D-033: RateLimitError (429) → step 2 rejected. See DJ D-033."""
    from polymarket_us import RateLimitError
    exc = RateLimitError("Rate limit exceeded (429)", response=_fake_response(429))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "rejected"
    assert "step 2" in reason


def test_d033_api_connection_error_routes_to_exception() -> None:
    """D-033: APIConnectionError → DOCUMENTED_TRANSPORT_EXCEPTION_TYPES →
    step 1 exception. See DJ D-033 for the five transport-type assignments."""
    from polymarket_us import APIConnectionError
    exc = APIConnectionError(message="Connection error.")
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"
    assert "step 1" in reason


def test_d033_api_timeout_error_routes_to_exception() -> None:
    """D-033: APITimeoutError → step 1 exception. See DJ D-033."""
    from polymarket_us import APITimeoutError
    exc = APITimeoutError()
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"
    assert "step 1" in reason


def test_d033_asyncio_timeout_error_qualname_routes_to_exception() -> None:
    """D-033: asyncio.TimeoutError's qualname is 'TimeoutError' (3.11+);
    the transport frozenset matches on that string. See DJ D-033."""
    import asyncio
    exc = asyncio.TimeoutError()
    assert type(exc).__name__ == "TimeoutError"
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"
    assert "step 1" in reason


def test_d033_internal_server_error_routes_to_exception() -> None:
    """D-033: InternalServerError (500+) is a D-033 ADDITION to the
    transport frozenset. 5xx is server-side infrastructure failure, not
    a client-request refusal — classifying as transport/exception
    preserves the "not the sweep's fault" signal vs misattributing to
    rejected. See DJ D-033 for the 4xx-vs-5xx partition reasoning.

    If this test fails, D-033's InternalServerError → transport
    assignment has been reverted. See DJ D-033.
    """
    from polymarket_us import InternalServerError
    exc = InternalServerError("Internal server error (500+)", response=_fake_response(500))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception", (
        f"D-033 InternalServerError → transport/exception assignment "
        f"reverted; got {label!r}. See DJ D-033."
    )
    assert "step 1" in reason


def test_d033_websocket_error_routes_to_exception() -> None:
    """D-033: WebSocketError is a D-033 ADDITION to the transport
    frozenset. WS is the transport layer for sweeps' markets_ws channel;
    a WS-layer error is a transport error analogous to APIConnectionError
    for HTTP. See DJ D-033.

    If this test fails, D-033's WebSocketError → transport assignment
    has been reverted. See DJ D-033.
    """
    from polymarket_us import WebSocketError
    exc = WebSocketError("WebSocket error occurred", request_id="some-req-id")
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception", (
        f"D-033 WebSocketError → transport/exception assignment "
        f"reverted; got {label!r}. See DJ D-033."
    )
    assert "step 1" in reason


def test_d033_api_error_base_class_routes_to_exception_via_catch_all() -> None:
    """D-033: APIError is a base class; not in either frozenset. Routes
    to step 1 via catch-all. See DJ D-033 base-class carve-out."""
    from polymarket_us import APIError
    exc = APIError("Generic API error")
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"


def test_d033_api_status_error_base_class_routes_to_exception_via_catch_all() -> None:
    """D-033: APIStatusError is a base class; catch-all. See DJ D-033."""
    from polymarket_us import APIStatusError
    exc = APIStatusError("Generic status error", response=_fake_response(418))
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"


def test_d033_polymarket_us_error_root_routes_to_exception_via_catch_all() -> None:
    """D-033: PolymarketUSError is the root base class; catch-all. See DJ D-033."""
    from polymarket_us import PolymarketUSError
    exc = PolymarketUSError("Root error")
    cell = _make_cell(
        subs=[_make_sub(subscribe_sent=True)],
        exception_type=type(exc).__name__,
        exception_message=str(exc)[:sweeps.PREVIEW_TRUNCATION_CHARS],
    )
    label, _reason = sweeps.classify_cell(cell, is_m4_control=False)
    assert label == "exception"


def test_d033_frozenset_membership() -> None:
    """Pin the two frozensets' memberships explicitly. If any
    type-name string is added to or removed from the frozensets outside
    of a DJ-entry-backed revision, this test fails with direct
    traceability. See DJ D-033."""
    assert sweeps.DOCUMENTED_REJECTED_EXCEPTION_TYPES == frozenset({
        "AuthenticationError",
        "BadRequestError",
        "NotFoundError",
        "PermissionDeniedError",
        "RateLimitError",
    })
    assert sweeps.DOCUMENTED_TRANSPORT_EXCEPTION_TYPES == frozenset({
        "APIConnectionError",
        "APITimeoutError",
        "TimeoutError",
        "InternalServerError",
        "WebSocketError",
    })


# ===========================================================================
# Aggregate helpers — run classification, M1/M2/M5
# ===========================================================================


def _cell_with(
    classification: str,
    *,
    axis: str = "subscriptions",
    axis_value: int = 1,
    m1: str | None = None,
    m2: str | None = None,
) -> SweepCellOutcome:
    return SweepCellOutcome(
        cell_axis=axis,
        cell_axis_value=axis_value,
        cell_classification=classification,
        m1_resolution=m1,
        m2_resolution=m2,
    )


def test_aggregate_run_classification_all_clean() -> None:
    cells = [_cell_with("clean"), _cell_with("clean"), _cell_with("clean")]
    assert sweeps.aggregate_run_classification(cells) == "clean"


def test_aggregate_run_classification_mixed_clean_degraded_is_partial() -> None:
    cells = [_cell_with("clean"), _cell_with("degraded"), _cell_with("clean")]
    assert sweeps.aggregate_run_classification(cells) == "partial"


def test_aggregate_run_classification_any_rejected_is_failed() -> None:
    cells = [_cell_with("clean"), _cell_with("rejected"), _cell_with("degraded")]
    assert sweeps.aggregate_run_classification(cells) == "failed"


def test_aggregate_run_classification_any_exception_is_failed() -> None:
    cells = [_cell_with("clean"), _cell_with("exception")]
    assert sweeps.aggregate_run_classification(cells) == "failed"


def test_aggregate_run_classification_ambiguous_no_rejected_is_ambiguous() -> None:
    cells = [_cell_with("clean"), _cell_with("ambiguous"), _cell_with("degraded")]
    assert sweeps.aggregate_run_classification(cells) == "ambiguous"


def test_aggregate_run_classification_empty_is_ambiguous() -> None:
    """Empty cells list → ambiguous (surface literally, D-025)."""
    assert sweeps.aggregate_run_classification([]) == "ambiguous"


def test_aggregate_m1_replace_dominates_compose() -> None:
    """H-020 ruling 3: structural binary counterexample dominates."""
    cells = [_cell_with("clean", m1="compose"), _cell_with("clean", m1="replace")]
    assert sweeps.aggregate_m1_resolution(cells) == "replace"


def test_aggregate_m1_ambiguous_dominates_compose() -> None:
    """H-020 ruling 3 refinement: if no replace observed, ambiguous
    dominates compose (honest surfacing, not averaging away)."""
    cells = [
        _cell_with("clean", m1="compose"),
        _cell_with("clean", m1="ambiguous"),
        _cell_with("clean", m1="compose"),
    ]
    assert sweeps.aggregate_m1_resolution(cells) == "ambiguous"


def test_aggregate_m1_all_compose_is_compose() -> None:
    cells = [_cell_with("clean", m1="compose"), _cell_with("clean", m1="compose")]
    assert sweeps.aggregate_m1_resolution(cells) == "compose"


def test_aggregate_m1_none_tested_is_not_tested() -> None:
    cells = [_cell_with("clean"), _cell_with("clean")]
    assert sweeps.aggregate_m1_resolution(cells) == "not-tested"


def test_aggregate_m2_shared_dominates_independent() -> None:
    cells = [_cell_with("clean", m2="independent"), _cell_with("clean", m2="shared")]
    assert sweeps.aggregate_m2_resolution(cells) == "shared"


def test_aggregate_m2_ambiguous_dominates_independent() -> None:
    cells = [
        _cell_with("clean", m2="independent"),
        _cell_with("clean", m2="ambiguous"),
    ]
    assert sweeps.aggregate_m2_resolution(cells) == "ambiguous"


def test_aggregate_m5_upper_bound_highest_clean_connections_axis() -> None:
    cells = [
        _cell_with("clean", axis="connections", axis_value=1),
        _cell_with("clean", axis="connections", axis_value=2),
        _cell_with("degraded", axis="connections", axis_value=4),
        _cell_with("clean", axis="subscriptions", axis_value=10),
    ]
    # Only connections-axis clean cells count; n=4 is degraded.
    assert sweeps.aggregate_m5_upper_bound(cells) == 2


def test_aggregate_m5_upper_bound_zero_when_no_connections_clean() -> None:
    cells = [_cell_with("clean", axis="subscriptions", axis_value=10)]
    assert sweeps.aggregate_m5_upper_bound(cells) == 0


# ===========================================================================
# M-resolver helpers — per-cell measurement-question resolution
# ===========================================================================


def test_resolve_m1_skipped_for_single_subscribe_cell() -> None:
    """Only subscriptions-axis cells with N≥2 test M1."""
    grid = sweeps.build_default_grid()
    cell = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 1][0]
    outcome = _make_cell(subs=[_make_sub(subscribe_sent=True)])
    assert sweeps._resolve_m1(outcome, cell) is None


def test_resolve_m1_compose_when_multiple_rids_get_traffic() -> None:
    grid = sweeps.build_default_grid()
    n2 = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 2][0]
    sub1 = _make_sub(
        subscribe_sent=True, request_id="sweep-X-Y-conn0-sub0",
        msg_counts={"market_data": 3}, per_slug_counts={"aec-atp-real-2026-04-21": 3},
    )
    sub2 = _make_sub(
        subscribe_sent=True, request_id="sweep-X-Y-conn0-sub1",
        msg_counts={"market_data": 2}, per_slug_counts={"aec-atp-real-2026-04-21": 2},
    )
    outcome = _make_cell(axis_value=2, subs=[sub1, sub2])
    assert sweeps._resolve_m1(outcome, n2) == "compose"


def test_resolve_m1_replace_when_only_last_rid_gets_traffic() -> None:
    """When only the sub_idx == N-1 subscribe receives traffic, M1
    resolves to replace."""
    grid = sweeps.build_default_grid()
    n2 = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 2][0]
    sub1 = _make_sub(
        subscribe_sent=True, request_id="sweep-X-Y-conn0-sub0",
        msg_counts={}, per_slug_counts={},
    )
    sub2 = _make_sub(
        subscribe_sent=True, request_id="sweep-X-Y-conn0-sub1",
        msg_counts={"market_data": 2}, per_slug_counts={"aec-atp-real-2026-04-21": 2},
    )
    outcome = _make_cell(axis_value=2, subs=[sub1, sub2])
    assert sweeps._resolve_m1(outcome, n2) == "replace"


def test_resolve_m1_error_when_exception_fired() -> None:
    grid = sweeps.build_default_grid()
    n2 = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 2][0]
    outcome = _make_cell(
        axis_value=2, subs=[_make_sub(subscribe_sent=True), _make_sub(subscribe_sent=True)],
        exception_type="BadRequestError",
    )
    assert sweeps._resolve_m1(outcome, n2) == "error"


def test_resolve_m2_skipped_for_single_connection_cell() -> None:
    grid = sweeps.build_default_grid()
    n1_conn = [c for c in grid if c.cell_axis == "connections" and c.cell_axis_value == 1][0]
    outcome = _make_cell(axis="connections", subs=[_make_sub(subscribe_sent=True)])
    assert sweeps._resolve_m2(outcome, n1_conn) is None


def test_resolve_m3_populates_latency_and_slug_counts() -> None:
    grid = sweeps.build_default_grid()
    cell_n1 = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 1][0]
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 10, "heartbeat": 3},
        per_slug_counts={"aec-atp-real-2026-04-21": 10},
    )
    sub.first_message_latency_seconds = 1.25
    outcome = _make_cell(subs=[sub])
    m3 = sweeps._resolve_m3(outcome, cell_n1)
    assert m3["cell_slugs_per_subscription"] == 100
    assert m3["first_message_latencies_seconds"] == [1.25]
    assert m3["median_first_message_latency_seconds"] == 1.25
    assert m3["total_messages_by_event"] == {"market_data": 10, "heartbeat": 3}
    assert m3["distinct_slugs_with_traffic"] == 1


def test_resolve_m4_silent_filter_inferred_when_no_placeholder_traffic() -> None:
    """M4 control cell with subscribe success and zero placeholder
    traffic → silent_filter_inferred True."""
    grid = sweeps.build_default_grid()
    m4 = grid[0]
    m4_sub = SubscribeObservation(
        request_id="m4-req", subscribe_sent=True, slugs=["ph1", "ph2"],
        real_slug="", placeholder_slugs_count=100,
        message_count_by_event={}, per_slug_message_counts={},
    )
    outcome = SweepCellOutcome(
        cell_axis="m4-control", cell_axis_value=1,
        slugs_per_subscription=100,
        connections=[ConnectionObservation(
            connection_index=0, connected=True, subscribe_calls=[m4_sub],
            closed_cleanly=True,
        )],
    )
    m4_obs = sweeps._resolve_m4(outcome, m4)
    assert m4_obs["is_m4_control_cell"] is True
    assert m4_obs["placeholder_traffic_observed"] is False
    assert m4_obs["hard_rejection_observed"] is False
    assert m4_obs["silent_filter_inferred"] is True


def test_resolve_m4_hard_rejection_observed_when_bad_request_error() -> None:
    """BadRequestError on M4 critical path → hard_rejection_observed True."""
    grid = sweeps.build_default_grid()
    m4 = grid[0]
    m4_sub = SubscribeObservation(
        request_id="m4-req", subscribe_sent=False, slugs=["ph"],
        real_slug="", placeholder_slugs_count=100,
    )
    outcome = SweepCellOutcome(
        cell_axis="m4-control", cell_axis_value=1,
        slugs_per_subscription=100,
        exception_type="BadRequestError",
        connections=[ConnectionObservation(
            connection_index=0, connected=True, subscribe_calls=[m4_sub],
            closed_cleanly=True,
        )],
    )
    m4_obs = sweeps._resolve_m4(outcome, m4)
    assert m4_obs["hard_rejection_observed"] is True
    assert m4_obs["silent_filter_inferred"] is False


def test_resolve_m5_per_connection_observations() -> None:
    grid = sweeps.build_default_grid()
    cell_n2 = [c for c in grid if c.cell_axis == "connections" and c.cell_axis_value == 2][0]
    sub_a = _make_sub(
        subscribe_sent=True, request_id="r0",
        msg_counts={"market_data": 5}, per_slug_counts={"aec-atp-real-2026-04-21": 5},
    )
    sub_b = _make_sub(
        subscribe_sent=True, request_id="r1",
        msg_counts={"market_data": 3}, per_slug_counts={"aec-atp-real-2026-04-21": 3},
    )
    outcome = _make_cell(
        axis="connections", axis_value=2, subs=[sub_a, sub_b], n_connections=2,
    )
    m5 = sweeps._resolve_m5(outcome, cell_n2)
    assert m5["cell_connection_count"] == 2
    assert m5["all_connected"] is True
    assert len(m5["per_connection"]) == 2
    assert m5["per_connection"][0]["total_messages_received"] == 5
    assert m5["per_connection"][1]["total_messages_received"] == 3


# ===========================================================================
# Aggregate summary dict schemas — committed at checkpoint 3 per operator
# ruling 4.
# ===========================================================================


def test_build_m3_aggregate_summary_schema() -> None:
    """Confirm the committed schema keys. Pins the dict shape for
    downstream (§17-eventually) consumers."""
    grid = sweeps.build_default_grid()
    cell_n1 = [c for c in grid if c.cell_axis == "subscriptions" and c.cell_axis_value == 1][0]
    sub = _make_sub(
        subscribe_sent=True,
        msg_counts={"market_data": 1},
        per_slug_counts={"aec-atp-real-2026-04-21": 1},
    )
    sub.first_message_latency_seconds = 0.5
    outcome = _make_cell(subs=[sub])
    outcome.m3_observations = sweeps._resolve_m3(outcome, cell_n1)
    agg = sweeps.build_m3_aggregate_summary([outcome])
    assert set(agg.keys()) == {
        "per_cell_median_latency_seconds",
        "overall_median_latency_seconds",
        "total_messages_by_event",
        "cells_with_latency_data",
    }
    assert agg["overall_median_latency_seconds"] == 0.5
    assert agg["cells_with_latency_data"] == 1


def test_build_m4_aggregate_summary_schema_silent_filter() -> None:
    """Confirm committed schema + silent_filter category detection."""
    grid = sweeps.build_default_grid()
    m4 = grid[0]
    m4_sub = SubscribeObservation(
        request_id="m4-req", subscribe_sent=True, slugs=["ph"],
        real_slug="", placeholder_slugs_count=100,
    )
    outcome = SweepCellOutcome(
        cell_axis="m4-control", cell_axis_value=1,
        slugs_per_subscription=100,
        connections=[ConnectionObservation(
            connection_index=0, connected=True, subscribe_calls=[m4_sub],
            closed_cleanly=True,
        )],
    )
    outcome.m4_observations = sweeps._resolve_m4(outcome, m4)
    agg = sweeps.build_m4_aggregate_summary([outcome])
    assert set(agg.keys()) == {
        "m4_control_cell_observed",
        "m4_control_behavior",
        "placeholder_traffic_in_any_cell",
        "hard_rejection_in_any_cell",
        "total_placeholder_messages",
    }
    assert agg["m4_control_cell_observed"] is True
    assert agg["m4_control_behavior"] == "silent_filter"


# ===========================================================================
# Self-check mode — no network, no client construction
# ===========================================================================


def test_run_self_check_returns_ok_with_valid_env(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Self-check should succeed cleanly when the SDK is importable and
    credentials are present. Does not construct an SDK client."""
    monkeypatch.setenv("POLYMARKET_US_API_KEY_ID", "fake-id")
    monkeypatch.setenv("POLYMARKET_US_API_SECRET_KEY", "fake-secret")
    rc = sweeps.run_self_check()
    assert rc == sweeps.EXIT_OK
    err = capsys.readouterr().err
    assert "self-check" in err.lower()
    assert "polymarket_us import ok" in err.lower()


def test_run_self_check_warns_on_missing_creds_but_passes(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Missing credentials produce a warning in self-check, not a
    failure. The sweep mode enforces credentials; self-check only names
    them as present/absent."""
    monkeypatch.delenv("POLYMARKET_US_API_KEY_ID", raising=False)
    monkeypatch.delenv("POLYMARKET_US_API_SECRET_KEY", raising=False)
    rc = sweeps.run_self_check()
    assert rc == sweeps.EXIT_OK
    err = capsys.readouterr().err
    assert "NOT SET" in err
