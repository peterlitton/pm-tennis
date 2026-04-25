"""
src/capture/diagnostics.py
PM-Tennis H-032 — runtime memory and task instrumentation.

Purpose: surface enough live-system data to identify Mechanism 1's source
in the next observation window. The H-032 static-reading diagnosis ruled
out the original leading hypothesis (SDK ws-retention-after-close); the
~15-20 MB/min steady accumulation has a real cause not visible in static
review of clob_pool.py / archive_writer.py / polymarket_us SDK source.

Two periodic tasks:

  - heavy_snapshot every 5 minutes:
      * tracemalloc top 10 allocations by total size, with file:line.
      * Live MarketsWebSocket instance count via gc.get_objects() filter.
      * RSS memory in MB via resource.getrusage.
    This is expensive (gc.get_objects() walks the whole heap) so cadence
    is sparse.

  - task_snapshot every 1 minute:
      * Count of asyncio.all_tasks() bucketed by coroutine name.
    This is cheap and runs more frequently to catch task accumulation.

Each log line is prefixed with a session_id (process-start UUID prefix)
so multi-line tracemalloc dumps can be reassembled across the Render Logs
stream. tracemalloc dumps are split if they would exceed ~1500 chars per
line (Render Logs' display threshold).

Wiring: main.py launches start_diagnostics() as a startup task. If
tracemalloc.start() has not been called before the first heavy_snapshot,
the snapshot will log a one-time warning and skip the tracemalloc section
(the task/RSS sections still run).
"""

from __future__ import annotations

import asyncio
import gc
import logging
import os
import resource
import tracemalloc
import uuid
from collections import Counter

log = logging.getLogger("pm_tennis.diagnostics")


HEAVY_SNAPSHOT_INTERVAL_SECONDS = 5 * 60   # tracemalloc + gc + RSS
TASK_SNAPSHOT_INTERVAL_SECONDS = 60        # asyncio.all_tasks bucketing
TRACEMALLOC_TOP_N = 10
LOG_LINE_SOFT_LIMIT_CHARS = 1500           # Render Logs display threshold

# Session id (8-char hex) so multi-line dumps can be correlated in
# downstream log analysis. Computed once at module import.
SESSION_ID = uuid.uuid4().hex[:8]


def _rss_mb() -> float:
    """Resident set size in MB. Linux ru_maxrss is in KB."""
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0


def _count_ws_instances() -> tuple[int, int]:
    """Return (markets_ws_count, base_ws_count) by walking gc.get_objects()
    and counting instances of MarketsWebSocket and BaseWebSocket.

    Imports SDK types lazily to avoid hard dependency at module-import
    time (tests must be able to import this module without the SDK
    installed, since instrumentation is wired separately from clob_pool).
    """
    try:
        from polymarket_us.websocket.base import BaseWebSocket
        from polymarket_us.websocket.markets import MarketsWebSocket
    except ImportError:
        return (-1, -1)
    markets_count = 0
    base_count = 0
    for obj in gc.get_objects():
        if isinstance(obj, MarketsWebSocket):
            markets_count += 1
        # MarketsWebSocket extends BaseWebSocket — count base separately
        # to detect cases where instances of OTHER subclasses (private ws,
        # if ever used) accumulate.
        if isinstance(obj, BaseWebSocket) and not isinstance(obj, MarketsWebSocket):
            base_count += 1
    return (markets_count, base_count)


def _format_traceback_frame(stat) -> str:
    """One-line summary of a tracemalloc Statistic for Render Logs."""
    frame = stat.traceback[0] if stat.traceback else None
    location = f"{frame.filename}:{frame.lineno}" if frame else "<unknown>"
    size_kb = stat.size / 1024.0
    return f"{location} count={stat.count} size_kb={size_kb:.1f}"


async def heavy_snapshot_loop() -> None:
    """5-minute cadence: tracemalloc top-N + gc-counted ws instances + RSS."""
    log.info(
        "diagnostics: heavy_snapshot_loop starting session_id=%s "
        "interval=%ds",
        SESSION_ID, HEAVY_SNAPSHOT_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(HEAVY_SNAPSHOT_INTERVAL_SECONDS)
            await _emit_heavy_snapshot()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("diagnostics: heavy_snapshot iteration raised; continuing")


async def _emit_heavy_snapshot() -> None:
    rss_mb = _rss_mb()
    markets_count, base_count = _count_ws_instances()

    log.info(
        "diagnostics:%s rss_mb=%.1f markets_ws_live=%d other_base_ws_live=%d "
        "pid=%d",
        SESSION_ID, rss_mb, markets_count, base_count, os.getpid(),
    )

    if not tracemalloc.is_tracing():
        log.warning(
            "diagnostics:%s tracemalloc not tracing — start in main.py "
            "before launching diagnostics",
            SESSION_ID,
        )
        return

    snapshot = tracemalloc.take_snapshot()
    # Filter out tracemalloc's own bookkeeping and the diagnostics module
    # itself so we surface signal, not measurement noise.
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
        tracemalloc.Filter(False, tracemalloc.__file__),
        tracemalloc.Filter(False, __file__),
    ))
    top_stats = snapshot.statistics("lineno")[:TRACEMALLOC_TOP_N]

    # Split top-N across multiple log lines so each line stays under the
    # Render Logs display threshold. One stat per line keeps it simple
    # and trivially greppable.
    log.info(
        "diagnostics:%s tracemalloc_top_%d_begin",
        SESSION_ID, TRACEMALLOC_TOP_N,
    )
    for rank, stat in enumerate(top_stats, start=1):
        line = _format_traceback_frame(stat)
        if len(line) > LOG_LINE_SOFT_LIMIT_CHARS:
            line = line[:LOG_LINE_SOFT_LIMIT_CHARS] + "...[truncated]"
        log.info(
            "diagnostics:%s tracemalloc_rank=%d %s",
            SESSION_ID, rank, line,
        )
    log.info(
        "diagnostics:%s tracemalloc_top_%d_end",
        SESSION_ID, TRACEMALLOC_TOP_N,
    )


async def task_snapshot_loop() -> None:
    """1-minute cadence: asyncio.all_tasks() bucketed by coroutine name."""
    log.info(
        "diagnostics: task_snapshot_loop starting session_id=%s "
        "interval=%ds",
        SESSION_ID, TASK_SNAPSHOT_INTERVAL_SECONDS,
    )
    while True:
        try:
            await asyncio.sleep(TASK_SNAPSHOT_INTERVAL_SECONDS)
            _emit_task_snapshot()
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("diagnostics: task_snapshot iteration raised; continuing")


def _emit_task_snapshot() -> None:
    tasks = asyncio.all_tasks()
    buckets: Counter[str] = Counter()
    message_loop_count = 0
    for t in tasks:
        coro = t.get_coro()
        # Coroutine __qualname__ is the most readable identifier; fallback
        # to the task name (less informative but always present).
        name = getattr(coro, "__qualname__", None) or t.get_name()
        buckets[name] += 1
        # SDK message loop is BaseWebSocket._message_loop; we substring-match
        # rather than exact-match to survive SDK-side qualname renames.
        if "_message_loop" in name:
            message_loop_count += 1
    total = sum(buckets.values())
    # Compose a single-line summary; sorted by count desc for readability.
    parts = [f"{name}={count}" for name, count in buckets.most_common()]
    summary = " ".join(parts)
    if len(summary) > LOG_LINE_SOFT_LIMIT_CHARS:
        summary = summary[:LOG_LINE_SOFT_LIMIT_CHARS] + "...[truncated]"
    # message_loop_count is surfaced as a top-level field so log analysis
    # can grep+diff it directly against markets_ws_live from the heavy
    # snapshot. Divergence (loops > ws) signals orphaned _message_task
    # tasks holding ws references the pool can't see.
    log.info(
        "diagnostics:%s tasks_total=%d message_loop_tasks=%d %s",
        SESSION_ID, total, message_loop_count, summary,
    )


def start_diagnostics() -> tuple[asyncio.Task, asyncio.Task]:
    """Launch heavy and task snapshot loops as background tasks.

    Returns the (heavy_task, task_task) pair so the caller can hold
    references (preventing GC of background tasks per asyncio docs)
    and cancel them at shutdown if desired.

    Caller is responsible for tracemalloc.start() before calling this
    if tracemalloc dumps are wanted.
    """
    # Single startup line tying SESSION_ID to a wall-clock anchor —
    # makes log search trivial: find this line, scope all subsequent
    # `diagnostics:<SESSION_ID>` lines to the same process lifetime.
    import datetime as _dt
    start_iso = _dt.datetime.now(_dt.timezone.utc).isoformat()
    log.info(
        "diagnostics: SESSION_ID=%s process_start_utc=%s pid=%d",
        SESSION_ID, start_iso, os.getpid(),
    )
    heavy = asyncio.create_task(heavy_snapshot_loop(), name="diagnostics_heavy")
    task = asyncio.create_task(task_snapshot_loop(), name="diagnostics_tasks")
    log.info("diagnostics: started session_id=%s", SESSION_ID)
    return heavy, task
