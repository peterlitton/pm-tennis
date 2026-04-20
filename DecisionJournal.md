# PM-Tennis — Decision Journal

This document records every non-trivial decision made during the PM-Tennis project, with enough reasoning for future-Claude (and future-operator) to understand the *why* behind each choice. Per Section 1.5.4 of the build plan, Claude logs decisions at the moment they are made. Per the session-close ritual (Playbook §2), the operator's gate verdicts and out-of-protocol acknowledgements are also recorded here.

The Decision Journal is a project artifact, not a session summary. It accumulates across all sessions without deletion or revision. Its value is cumulative — a reader arriving late in the project can reconstruct the reasoning behind every choice without consulting session transcripts.

---

## Conventions

- **Sequential IDs.** Each decision has a unique sequential ID (D-001, D-002, ...). IDs are never reused, never skipped, and never reassigned.
- **Reverse chronological order.** Newest decisions appear at the top so that the most recent context is immediately visible at session open.
- **No in-place revision.** Decisions are not edited after the fact. If a decision is changed or overridden, a new entry is added referencing the prior ID. The prior entry receives a one-line note at the bottom: `SUPERSEDED BY D-xxx (date)`. The original reasoning is preserved in full.
- **Gate verdicts.** When the operator passes or fails a phase-exit gate, the verdict is logged here at the top of the session following the gate, before any new work begins. Format: `Gate verdict: [Phase N exit] — [PASS / FAIL / DEFER] — [date] — [brief rationale]`.
- **Out-of-protocol events.** Every out-of-protocol invocation is logged here, in addition to the session handoff's self-report section. Format is given in D-004.
- **Entry structure.** Each entry carries: date, session ID (handoff ID), type tag, the decision, what was considered, the reasoning, and the commitment the decision creates. Sub-questions that remain open are listed explicitly and resolved by a later entry or a sub-ruling.
- **Reconstructed entries.** An entry may be marked "Reconstructed" when it was journaled in a later session from handoff sources rather than at the moment of decision. Reconstructed entries carry both a decision date and a journaling date; their Source line names the authoritative material used.

---

## D-033 — `polymarket-us==0.1.2` full exception surface surfaced at H-020 SDK introspection: frozenset assignments revised

**Date:** 2026-04-20
**Session:** H-020
**Type:** SDK-surface clarification / Classifier frozenset revision

**Source:** Claude surfaced during H-020 checkpoint 3 SDK introspection (post-install of `polymarket-us==0.1.2` per `src/stress_test/requirements.txt`). The check was a discipline layer beyond §16.9 step 1's README re-fetch — introspecting the installed module's `__all__` and exception hierarchy. This check is the H-013 / §15.1.3 standard that §16.9 did not name explicitly. Operator ruled at checkpoint 3 hard pause.

**Finding.** `polymarket-us==0.1.2` top-level namespace (and `polymarket_us.__all__`) exports **twelve** exception classes; [E]'s README Error Handling section illustrates **six** of them via its import example. The README's six is an illustrative import list, not an exhaustive type enumeration. Complete hierarchy rooted at `PolymarketUSError ← Exception`:

```
PolymarketUSError (root)
├── APIError
│   ├── APIConnectionError                [README]
│   │   └── APITimeoutError               [README]
│   └── APIStatusError (HTTP 4xx/5xx base)
│       ├── BadRequestError (400)         [README]
│       ├── AuthenticationError (401)     [README]
│       ├── PermissionDeniedError (403)
│       ├── NotFoundError (404)           [README]
│       ├── RateLimitError (429)          [README]
│       └── InternalServerError (500+)
└── WebSocketError
```

Types documented in the README's Error Handling example: 6 (marked [README] above). Types present in the installed module but not in the README example: 6 (`PolymarketUSError`, `APIError`, `APIStatusError`, `PermissionDeniedError`, `InternalServerError`, `WebSocketError`). HTTP-status-code mappings come from each class's own docstring in `polymarket_us/errors.py` (verified at H-020 via source read).

**Framing this against the §16.9 re-fetch:** H-020 §16.9 step 1 re-fetch recommended exit state A (clean) on the basis that the [E] README text was identical to H-019's baseline, including the six-type import example in the Error Handling section. That ruling holds for the README-as-text check §16.9 step 1 names. The finding here is at a different layer: the *installed module* exports more than the README illustrates. Per the "when uncertain, default to B" rule, this gap between the research record (§16.1 + [A] citation) and the installed surface is B material — a contradiction between the research record and what the code will actually execute against — that was not caught at H-019 re-fetch time because the re-fetch was README-only. The README re-fetch was correct per §16.9's letter; the gap is in what §16.9 asks for, not in how the re-fetch was performed.

**Decision:**

1. **Expand `DOCUMENTED_REJECTED_EXCEPTION_TYPES`** to include `PermissionDeniedError`. Final set of 5 type names:
   `{"AuthenticationError", "BadRequestError", "NotFoundError", "PermissionDeniedError", "RateLimitError"}`.
   Criterion: 4xx client-error class under `APIStatusError` — the server received the request and refused it for a documented reason. A 403 is a documented client refusal; classifying it as `rejected` preserves the "server responded with a documented refusal" signal.

2. **Expand `DOCUMENTED_TRANSPORT_EXCEPTION_TYPES`** to include `InternalServerError` and `WebSocketError`. Final set of 5 type names:
   `{"APIConnectionError", "APITimeoutError", "TimeoutError", "InternalServerError", "WebSocketError"}`.
   Criterion: transport/infrastructure-layer error — the request either didn't reach the server, didn't complete, or failed server-side in a way the client request didn't cause. `InternalServerError` (5xx) is a server-side failure, not a client refusal; `WebSocketError` is WS-layer transport, analogous to `APIConnectionError` for HTTP.

3. **`APIError`, `APIStatusError`, `PolymarketUSError`** — base classes. Under normal SDK behavior these are not raised directly (leaf subclasses are). If one does raise at runtime, catch-all in the classifier routes to `exception`. No frozenset assignment.

**Considered:**

- **(1) Stay with the README-named six.** Classify the three newly-surfaced non-base types (`PermissionDeniedError`, `InternalServerError`, `WebSocketError`) via catch-all → `exception`. Rejected — `PermissionDeniedError` is structurally a sibling of the four named `APIStatusError` leaves; classifying it as `exception` loses information that the classifier already preserves for 400/401/404/429. Same reasoning applies to `InternalServerError` (known 5xx semantic) and `WebSocketError` (known transport semantic).
- **(2) Expand by `isinstance` against base classes.** Import `APIStatusError` and `APIConnectionError` into the classifier, use `isinstance(exc, APIStatusError)` → rejected and `isinstance(exc, APIConnectionError)` → exception. Cleaner semantically but requires importing the SDK into `classify_cell`. Rejected — the classifier is deliberately import-light (string-matching against frozensets) so the unit tests exercise classification without installing the SDK (D-021). Maintains probe.py's exception-type-string convention.
- **(3) Expand named, with `WebSocketError` deferred to live-smoke observation.** The checkpoint 3 pause proposal. Rejected — `WebSocketError`'s docstring and source (takes a `request_id` parameter, inherits from `PolymarketUSError` directly, not under `APIStatusError`) are clear enough that deferral is unnecessary. WS is the transport for the markets-ws channel sweeps exercises; a WS-layer error is a transport error.
- **(4) Expand by documented semantic with InternalServerError routed to rejected instead of transport.** Alternate reading — since `InternalServerError` is an `APIStatusError` subclass (4xx/5xx group), treat it as rejected. Rejected — 5xx is a server-side failure; classifying it as `rejected` implies the sweep's request was refused, which mis-attributes the failure to the sweep when it's a server-infrastructure signal. The `APIStatusError` inheritance is a Python-level factoring choice; the HTTP-semantic split (4xx client error vs 5xx server error) is the more faithful classifier boundary.

**Reasoning:**

The [A] citation block in probe.py cites README Error Handling and names six exception types as the documented SDK surface. At H-013, probe.py's classifier used those six because that was the surface probe.py needed to classify against and the README was the authoritative public-doc source at the time. H-013 did not hit any exception in the clean-probe run (§14.3), so the gap between README-exported and module-installed was never observationally tested.

Sweeps exercises a much larger surface than probe.py — N connections × M subscriptions × 100 slugs per subscription, including deliberately-invalid placeholder slugs on the M4 control cell. The M4 control cell is precisely the path most likely to raise `BadRequestError`, `NotFoundError`, or `PermissionDeniedError` if the server does hard-reject placeholder slugs. Sweeps is also the first piece of code that will observe WS-layer concurrent-connection behavior, where `WebSocketError` is the most likely raise site for any cap-boundary behavior.

The `polymarket_us.__all__` list is the SDK's authoritative public surface declaration — it's the SDK's own statement of what the public API is. Twelve exception classes are public per `__all__`; six are illustrated in the Error Handling example. The classifier's frozensets should align with `__all__`, not with the README example, because `__all__` is what the SDK commits to supporting as stable public API.

The HTTP-status-code framing in the docstrings (`400`, `401`, `403`, `404`, `429`, `500+`) is a second authoritative source — each class's own docstring pins its semantic. Using those docstring-named HTTP semantics to partition into `rejected` (4xx) vs `transport` (5xx + network + WS) is more faithful to the SDK's self-documentation than grouping strictly by Python inheritance.

**Commitment:**

1. `src/stress_test/sweeps.py` `DOCUMENTED_REJECTED_EXCEPTION_TYPES` = `frozenset({"AuthenticationError", "BadRequestError", "NotFoundError", "PermissionDeniedError", "RateLimitError"})`.
2. `src/stress_test/sweeps.py` `DOCUMENTED_TRANSPORT_EXCEPTION_TYPES` = `frozenset({"APIConnectionError", "APITimeoutError", "TimeoutError", "InternalServerError", "WebSocketError"})`.
3. Module header [A]-equivalent citation block updated to cite the **installed module's `__all__`** as the authoritative public-surface source alongside [E]'s README (which remains cited for the illustrative example and HTTP-status-code semantics). The header names the twelve exception classes explicitly so the classifier's frozenset membership is traceable to a specific source at code read time.
4. Classifier unit tests cover each of the five rejected types and each of the five transport types firing their respective steps (5 + 5 = 10 type-specific sanity checks plus the undocumented-type catch-all).
5. No `isinstance` / SDK-import is added to the classifier — frozenset string-matching is preserved per D-021 testability discipline.

**Scope and carve-outs:**

- **D-033 does not supersede §16.** §16 remains accepted and frozen at H-019. D-033 is a code-turn clarification of `§16.1`'s fetch-record claim (SDK surface unchanged) and `§16.4`/`§16.7`'s exception-type assignments. §16 prose is not edited.
- **D-033 does not change §16.7's precedence list.** Steps 1–7 are unchanged. Only the frozensets that step 1 and step 2 consult are revised.
- **D-033 does not change §16.6's outcome record shapes.** `exception_type` remains a string; `exception_message` remains a string-truncated-at-PREVIEW_TRUNCATION_CHARS.
- **D-033 adds a standing addition to §16.9 (proposed in H-020 handoff):** future code-turn sessions perform both (a) [E]/[F]/[G] README re-fetch AND (b) `pip install` of the pinned SDK version + `__all__` / exception-hierarchy / public-surface introspection. README-documented and module-exported surfaces can diverge; the re-fetch discipline must cover both. This is the H-013 / §15.1.3 standard applied to §16 code turns.
- **D-033 does not gate on live-smoke observation.** All five rejected-type assignments and all five transport-type assignments are based on docstring + HTTP-status-code semantics + module inheritance; no assignment requires H-021 live smoke to disambiguate. H-021 live smoke will observationally confirm (or contradict) the assignments; if any assignment's observed behavior contradicts this ruling, a follow-up DJ entry at that session revises.

**Effect on other decisions:**

- **D-016 (research-first):** preserved and honored. D-033 was surfaced during SDK introspection before any code change that depended on the broader frozenset assignments shipped. The classifier as shipped at checkpoint 2 used the README-documented six; D-033 is the correction before the frozensets become load-bearing for H-021 live smoke.
- **D-019 (research-first):** preserved. D-033 is a code-turn correction of a research-record gap, surfaced honestly rather than papered over.
- **D-021 (testing posture):** preserved and strengthened. Classifier tests remain SDK-import-free; string-matching against frozensets is the mechanism.
- **D-025 commitment 4 (surface ambiguity literally):** honored. The README-vs-module surface gap was surfaced at the moment it was noticed, not resolved silently by either staying with six or silently expanding.
- **D-027 (operator-supplied slug; slug_selector not in sweeps):** unchanged. D-033 touches exception classification, not anchor sourcing.
- **D-032 (§16.7 Reading B):** unchanged. D-033 is orthogonal — it revises which exception-type strings step 1 vs step 2 match, not the clean-(iii) predicate.
- **§16.1 (fetch record, research-doc):** unchanged as frozen prose. D-033 is the standing clarification that §16.1's "SDK unchanged" claim was README-accurate but module-surface-incomplete.
- **§16.9 (session-close discipline, research-doc):** unchanged as frozen prose. D-033 proposes a standing addition to §16.9 in H-020's handoff — future code-turn sessions add the install-and-introspect step. The addition is proposed in handoff, not journaled as a §16 amendment.

**Evidence trail:**

- `polymarket_us.__all__` at H-020 introspection: 14 entries, 12 of them exception classes (`PolymarketUS`, `AsyncPolymarketUS`, and the 12 exception classes listed above).
- `polymarket_us/errors.py` source at H-020 (path: `/usr/local/lib/python3.12/dist-packages/polymarket_us/errors.py`): 12 exception classes, each with a one-line docstring naming the HTTP status code (for `APIStatusError` subclasses) or the transport semantic (`APIConnectionError`: "Network connection error"; `APITimeoutError`: "Request timed out"; `WebSocketError`: "WebSocket-related error").
- [E] README Error Handling section (re-fetched H-020 §16.9 step 1): six types in the import example — the same six `[A]` cites in probe.py lines 200-206.
- Inheritance trace at H-020: `APIStatusError ← APIError ← PolymarketUSError`; six `*Error` leaves under `APIStatusError`; `APIConnectionError ← APIError`; `APITimeoutError ← APIConnectionError`; `WebSocketError ← PolymarketUSError` directly (not under `APIError`).
- `WebSocketError.__init__` signature at H-020: `(self, message: str, request_id: str | None = None)` — carries a `request_id` parameter, meaning WS-layer errors can be attributed to a specific subscribe call when raised.
- H-020 code: `/home/claude/pm-tennis/src/stress_test/sweeps.py` `DOCUMENTED_REJECTED_EXCEPTION_TYPES` and `DOCUMENTED_TRANSPORT_EXCEPTION_TYPES` post-D-033 revision.

---

## D-032 — §16.7 clean-(iii) reading: anchor-specific per Meaning column (Reading B)

**Date:** 2026-04-20
**Session:** H-020
**Type:** Research-doc clarification / Code-turn reading-question resolution

**Source:** Claude surfaced an internal inconsistency in research-doc §16.7 during mechanical transcription of the classification state machine at H-020 checkpoint 2 (§16.6 / §16.7 code-turn transcription per §16.9). Operator ruled at checkpoint 2 pause.

**The inconsistency.** §16.7's `clean` row has a Meaning column and a Rule column that disagree on clean-condition (iii) for default cells:

- **Meaning column:** *"message traffic received on the anchor slug(s) within the observation window"* — requires anchor-slug-specific traffic.
- **Rule column:** *"at least one `market_data` or `trade` or `heartbeat` received across the cell"* — requires any qualifying traffic anywhere in the cell.

Meanwhile §16.7's `degraded` row names *"anchor slug produced zero traffic across the observation window"* as an anomaly that forces step 6 to classify `ratio == 1.0` cells as `degraded`. Under a literal reading of the Rule column (call it Reading A), a cell with heartbeat-only traffic and zero anchor-slug traffic would satisfy clean-(iii) (heartbeat counts) AND the `degraded` anchor-zero anomaly — an overlapping case where step 5 resolves first and the anchor-zero anomaly at step 6 becomes operationally unreachable. Reading A makes the textually-named anomaly unreachable in practice.

**Decision:** Adopt **Reading B** — clean-(iii) is anchor-slug-specific per the Meaning column. The Rule column's "across the cell" phrasing is imprecise transcription of the Meaning column's intent. Under Reading B, a cell with heartbeat-only traffic and zero anchor-slug traffic fails clean-(iii) at step 5, and step 6's anchor-zero-traffic anomaly fires cleanly. The M4 control cell's relaxed-clean caveat (no traffic required) is preserved unchanged.

**Considered:**

- **(A) Rule column literal, clean dominates.** Clean-(iii) as written requires any qualifying traffic; anchor-zero anomaly at step 6 becomes unreachable when step 5 has already fired. Preserves the Rule column's literal wording at the cost of making the `degraded` row's anchor-zero anomaly operationally inert. Rejected — textually-named but operationally-unreachable anomaly is the inconsistency signal.
- **(B) Meaning column literal, anchor-specific.** Selected. Clean-(iii) requires anchor-specific traffic; step 6's anchor-zero anomaly becomes the path from "ratio 1.0 but no anchor traffic" to `degraded`, which is textually consistent.
- **(C) Both hold, degraded vetoes clean on anomaly.** Keeps the Rule column's broader clean-(iii) but lets any anomaly condition override step 5. Richer; generalizes to future anomaly conditions. Rejected — §16 names three anomalies (errors, closes, anchor-zero) and only anchor-zero creates the inconsistency. Over-engineering for H-020 scope; if future anomalies require the veto pattern, a future research-doc addendum revises.

**Reasoning:** §16.5's rationale for the 1+99 anchor-plus-placeholder composition is to produce *attributable* traffic for M1 measurement — traffic the harness can attribute to a specific subscription via the `marketSlug` echo (§14.3). Heartbeat traffic is connection-level and does not carry a `marketSlug` echo; it is not subscription-attributable. A cell with heartbeats but zero anchor `market_data` / `trade` is meaningfully degraded — the anchor is doing the work §16.5 specifies it for *precisely when* clean-(iii) requires anchor-specific traffic. The Meaning column captures this design intent; the Rule column was sloppy transcription.

**Commitment:**

1. `src/stress_test/sweeps.py` implements Reading B: `_cell_has_anchor_slug_traffic_qualifying` is the clean-(iii) predicate for default cells. Heartbeat alone does not satisfy clean-(iii).
2. §16.7's Rule column phrasing stands unedited — §16 is frozen at H-019 and §16.11 names that §16 does not amend §§1–15 during the code turn. D-032 clarifies §16.7's Rule column vs. Meaning column by ruling Reading B authoritative, without editing §16 prose. If a future research-doc addendum (§17 or later) revises §16.7's text for clarity, it cites D-032.
3. The M4 control cell's relaxed-clean caveat is preserved: M4 requires only subscribe success + no error events + no close events, no traffic required. §16.7's M4 caveat is unchanged by D-032.
4. The `degraded` row's three anomalies (error_events non-empty, close_events non-empty, anchor slug zero traffic) all fire correctly at step 6 under Reading B. The regression test Claude wrote at checkpoint 2 (heartbeat-only traffic, zero anchor traffic → expect `degraded`) is the standing regression.

**Scope and carve-outs:**

- **D-032 does not supersede §16.** §16 remains accepted and frozen at H-019. D-032 resolves an ambiguity in §16.7 that operator review at H-019 did not catch. §16 prose is not edited.
- **D-032 does not change §16.7's precedence list.** Steps 1–7 are unchanged. Only the clean-(iii) predicate (what counts as "traffic" for default cells) is clarified.
- **D-032 does not affect the M4 control cell's relaxed-clean caveat.** M4 is explicitly untouched.
- **D-032 does not change §16.6's outcome record shapes.** SubscribeObservation fields (`real_slug`, `per_slug_message_counts`, `message_count_by_event`) already support Reading B without modification.
- **D-032 does not require revision of v4.1-candidate plan revisions.** §16.7 is a research-doc section, not plan-text. Plan revisions queued in STATE `pending_revisions` are unchanged.

**Effect on other decisions:**

- **§16 (H-019 addendum):** unchanged as frozen artifact. D-032 is the standing clarification reference.
- **D-019 (research-first):** preserved. D-032 is a code-turn reading resolution of a research-doc ambiguity, not a research-first bypass. The surfacing itself exercised research-first discipline — Claude paused code transcription to surface the ambiguity rather than pick a reading silently.
- **D-021 (testing posture):** preserved. The regression test for the anchor-zero anomaly lives in the sweeps sanity suite and will appear in `tests/test_stress_test_sweeps.py` at checkpoint 3.
- **D-025 commitment 4 (surface ambiguity literally):** honored. The §16.7 ambiguity was surfaced at the code-turn moment it was noticed, not resolved silently.

**Evidence trail:**

- §16.7 `clean` row (research-doc line 1051): Meaning column vs Rule column textual comparison.
- §16.7 `degraded` row (research-doc line 1052): anchor-zero-traffic anomaly text.
- §16.5 (research-doc lines 920–922): 1+99 anchor rationale — "This ensures every subscription has at least one slug that can produce traffic, giving M1 attribution evidence continuously across the grid."
- §14.3 (research-doc lines 558–601): n=1 evidence that `market_data` payloads carry the `marketSlug` echo; heartbeat does not appear in the observed payload and is not subscription-attributable.
- H-020 checkpoint 2 sanity-test-trace: one test expected `degraded` for heartbeat-only + zero-anchor-traffic; Reading A returned `clean`; Reading B returns `degraded`. The test is the regression standing behind D-032.
- H-020 code: `/home/claude/pm-tennis/src/stress_test/sweeps.py` `_cell_has_anchor_slug_traffic_qualifying` and step 5 (default cell branch) implement Reading B.

---

## D-031 — RAID I-017 resolution: align `TestVerifySportSlug` tests with intentional `RuntimeError` behavior per commit `bae6ee8e`

**Date:** 2026-04-20
**Session:** H-018
**Type:** Bug fix / Test-code reconciliation / Pre-H-004 drift resolution

**Source:** Operator ruling at H-018 following Claude's investigation of RAID I-017, supplemented by targeted `git blame` and commit-message inspection as requested by the operator before final ruling.

**Finding 1 — the drift is not incidental.** `git blame` on `src/capture/discovery.py` lines 558 and 562 points to commit `bae6ee8e` (peterlitton, 2026-04-18 20:46:03). The commit message is explicit: `"fix: replace SystemExit with RuntimeError in verify_sport_slug"`. The diff shows a targeted change — only the two `raise` sites were modified, paired with a small refactor of `GatewayClient.get_all_sports()`'s response-shape handling. This was a deliberate, intentional behavior change by the operator during early bootstrap, not an incidental edit.

**Finding 2 — why the tests drifted.** `bae6ee8e` is dated 2026-04-18 20:46:03, which is pre-H-004 — i.e., before the project's single-authoring-channel governance discipline was established. In the pre-H-004 environment, tests were not being kept in lockstep with code by the current Claude-authors / operator-commits-only workflow. The `TestVerifySportSlug` tests at `tests/test_discovery.py` lines 566 and 574 were created at (or before) `f3db86e2` with `pytest.raises(SystemExit)` assertions consistent with the then-current code; when `bae6ee8e` changed the code twenty minutes later, the tests were not updated in the same commit and no later commit caught up. The drift surfaced at H-016 during D-028 test runs as two persistent red tests on `main`, logged as RAID I-017.

**Finding 3 — production behavior confirms `RuntimeError` is the intended semantics.** The production caller in `main.py` lines 40–62 wraps discovery startup in `while True: try ... except Exception as exc: log.critical(...) await asyncio.sleep(30)`. `RuntimeError` is caught by `except Exception`; `SystemExit` inherits from `BaseException` and would *not* be caught, which would leave the asyncio task dead without restart. The current `RuntimeError` behavior integrates with the retry wrapper; the original `SystemExit` behavior did not, suggesting `bae6ee8e` was a deliberate fix to make `verify_sport_slug` play well with the supervising retry loop. The production `main.py` path has been running uninterrupted since H-009's revert through H-016's I-016 fix without startup-verification incident.

**Decision:** Apply Option (a) — update the two failing tests at `tests/test_discovery.py` to expect `RuntimeError` rather than `SystemExit`. Rename methods from `test_*_raises_system_exit` to `test_*_raises_runtime_error`. Add an inline comment in each renamed test pointing to D-031 and `bae6ee8e` so the rationale is visible without a journal round-trip.

No change to `src/capture/discovery.py`. No change to `main.py`. Scope is test-file only.

**Considered:**
- **(a) Update tests to expect `RuntimeError`.** Selected. Aligns tests with intentional production behavior established by `bae6ee8e`; no Phase 2 code touch; no D-016 authorization ceremony; no paired `main.py` revision required.
- **(b) Update `src/capture/discovery.py` to raise `SystemExit`.** Rejected. Would revert `bae6ee8e`'s intentional decision. Would require a paired `main.py` revision (widen `except Exception` to `except BaseException`, or accept that the discovery asyncio task dies with no retry). Touches Phase 2 code, which per D-016 commitment 2 is gated on explicit operator authorization with narrow justification. Intentional-commit evidence from `bae6ee8e` removes any ambiguity about which side is the source of truth.

**Reasoning:** The blame evidence resolves the direction of drift. The intentional commit is the code change; the test was the one that didn't catch up. Pre-H-004 context matters here: this is not someone being careless. It is a test file that never caught up with an intentional code change made before the single-authoring-channel governance discipline was in force. Under current discipline, a code change of this kind would travel with its test update in the same commit; under pre-H-004 discipline, that coupling was not enforced, and some drift accumulated. I-017 is one such piece of accumulated drift, and D-031 resolves it by bringing the tests into conformance with the intentional behavior.

This is a deliberate, bounded reconciliation. It is explicitly **not** a test-weakening of the class Playbook §4.2 tripwire (d) names. The tests continue to assert that an exception is raised on each of the two failure modes; only the named exception type is brought into conformance with the code's intentional behavior. The tests remain functionally equivalent in what they verify.

**Commitment:**

1. `tests/test_discovery.py` lines 566–579 are modified:
   - Method `test_network_failure_raises_system_exit` → `test_network_failure_raises_runtime_error`; `pytest.raises(SystemExit)` → `pytest.raises(RuntimeError)`.
   - Method `test_empty_sports_list_raises_system_exit` → `test_empty_sports_list_raises_runtime_error`; `pytest.raises(SystemExit)` → `pytest.raises(RuntimeError)`.
   - Inline comments added to both methods citing D-031 and `bae6ee8e`.

2. `src/capture/discovery.py` is **not** modified. `main.py` is **not** modified. No Phase 2 code touch.

3. RAID I-017 is marked **Resolved** with reference to D-031.

4. This is a test-file fix; no live smoke test required per D-021 scope (D-021 applies to Phase 3 deliverables; I-017 is a pre-existing test mismatch, not a deliverable).

**Verification:**
- `tests/test_discovery.py` in isolation: 49 passed, 0 failed in a fresh venv against pinned `requirements.txt` deps.
- Full `tests/` directory: 112 passed. One pre-existing, environmental failure in `tests/test_stress_test_probe_cli.py::test_main_defaults_to_self_check` (root cause: `polymarket_us` SDK is in `src/stress_test/requirements.txt`, not the top-level `requirements.txt`; baseline venv does not install it). Unrelated to I-017 and unrelated to this change.

**Scope and carve-outs:**

- **D-031 resolves only I-017.** Other pre-H-004 drift (if any) is not surveyed or resolved here. If similar test-code mismatches surface later, each is its own targeted entry.
- **The pre-existing `DeprecationWarning` on `asyncio.get_event_loop()` in `test_slug_found` (line 550) is not addressed.** It predates I-017, is not in the scope of this fix, and affects four tests in the class (only two of which are being modified). Worth a future cleanup pass; not in scope here.
- **The environmental failure in `test_main_defaults_to_self_check` is not addressed.** It is a consequence of the D-024 / D-020 dep-isolation design (`polymarket_us` lives in `src/stress_test/requirements.txt`, intentionally separate from the top-level `requirements.txt` per D-024 commitment 1). Any test-runner that needs this to pass must install both requirements files; that is a test-execution-documentation concern, not a code defect.

**Effect on other decisions and governance artifacts:**

- **D-016 commitment 2** (research-first, Phase 2 touch requires explicit authorization): not triggered. This fix is test-file only; no Phase 2 code touch.
- **D-021** (testing posture for Phase 3 attempt 2): not applicable. I-017 is a pre-existing test mismatch, not a Phase 3 deliverable. Completion bar is: test file passes in clean venv, operator code review, journaled.
- **D-029 §3** (always-replace-never-patch): followed. `tests/test_discovery.py` is delivered as a complete-replacement file in the session-close bundle.
- **Always-replace convention (H-016):** followed.

**Evidence trail:**

- `git blame -L 555,565 src/capture/discovery.py` → commit `bae6ee8e` authored lines 558 and 562 (the two `raise` sites).
- `git show bae6ee8e` → commit message "fix: replace SystemExit with RuntimeError in verify_sport_slug"; full diff showing deliberate `-raise SystemExit(1)` → `+raise RuntimeError(...)` changes.
- Commit metadata: author `peterlitton`, date 2026-04-18 20:46:03 -0500, predates H-004.
- `tests/test_discovery.py` test run before fix: 2 failed, 2 passed (TestVerifySportSlug class); after fix: 4 passed. Full test_discovery.py: 49/49 passed.
- `main.py` lines 40–62: production caller confirms `except Exception`-style retry-wrapper behavior, which `RuntimeError` satisfies and `SystemExit` would not.
- RAID I-017 entry (H-016 open) for original description of the drift.

---

## D-030 — D-029 authentication mechanism: architectural gap at first-use; interim flow adopted per Playbook §13.5.7

**Date:** 2026-04-19
**Session:** H-017
**Type:** Governance / Process / Operational carve-out on D-029 implementation

**Source:** First-use validation of D-029 at H-017 session open. D-029 landed at H-016 close with an implementation sequence (§Implementation sequencing): operator generates PAT → stores on Render env var → creates claude-staging branch → Claude test-pushes at H-017 open. Execution of this sequence at H-017 surfaced a gap between D-029's drafted mechanism and the actual working environment.

**Finding 1 — the gap.** D-029 Commitment §2 and Playbook §13.2 both specify that Claude authenticates via a GitHub PAT stored as a Render environment variable. This presumes a working environment in which Claude can read Render env vars. Claude.ai's sandbox (`/home/claude`) has no such access — Render env vars are readable only by processes running on the Render service itself, not by the Claude.ai chat environment where Claude authors files. The PAT-on-Render-env-var pattern as drafted in D-029 §2 is therefore not directly usable from Claude's actual working environment.

**Finding 2 — what is working.** The Render side of D-029 is sound, verified at H-017 via operator-performed dashboard inspection: `pm-tennis-api` Auto-Deploy is set to "On commit" with Branch set to `main`. Pushes to `claude-staging` are ignored by auto-deploy; code only reaches the production service via a merge to `main`. The `claude-staging` branch exists on remote (operator-created from `main` at commit `66def97` per H-016 close). The merge-gate safety property that D-029 was primarily designed to create is structurally available.

**Finding 3 — Playbook §13.5.7 is the correct anchor.** Playbook §13.5.7 ("Operator has not yet set up authentication at session open") was drafted as a transitional failure mode for session-level setup lag, but its text applies equally to this architectural gap: "the staging workflow is not yet available. Procedure: session reverts to the pre-D-029 drag-and-drop flow for the duration of that session." The interim flow described below is an invocation of §13.5.7, extended in scope (from "this session" to "every session until the authentication gap is resolved") but not in substance.

**Decision:** Adopt the interim flow described below for H-017 and all subsequent sessions, until D-029's authentication mechanism is fixed by a future DJ entry. D-029 itself is preserved unchanged; D-030 records that D-029's Commitment §2 is architecturally incomplete and how the project operates in the meantime.

**The interim flow:**

1. Claude produces complete-replacement files in the sandbox working environment (`/home/claude`), per the "always replace, never patch" convention established at H-016.
2. Claude presents files to the operator via the `present_files` tool (or equivalent download surface) at points where the session naturally produces a reviewable unit of work.
3. Operator uploads via GitHub web UI to the `claude-staging` branch — not `main`. Per Playbook §13, never push directly to `main` outside of a merge action.
4. Operator reviews the diff via GitHub's compare or PR interface (staging vs. main).
5. When satisfied, operator merges `claude-staging` → `main`. Render auto-deploys from `main`.

**What this interim flow preserves from D-029:**

- **Merge-gate.** Operator is the sole committer to `main` via the staging → main merge. ✅
- **Single-authoring-channel.** Claude is still the sole author of code and documentation. ✅
- **Always-replace discipline.** Claude never produces splice-into-file artifacts. ✅ (H-016 commitment, baked into D-029 §3, carried forward here.)
- **No secret values in chat.** The PAT-to-sandbox gap is acknowledged; the interim flow avoids it entirely by not requiring Claude to push. ✅

**What this interim flow does not preserve from D-029:**

- **Claude-originated pushes.** The "Claude pushes to staging" automation benefit is deferred. Operator still performs the upload step; the benefit over the pre-D-029 workflow is that operator uploads to `claude-staging` (reviewable) rather than `main` (immediately live).
- **Claude-led pre-push validation.** D-029 Commitment §4 specified Claude-run tests, path-correctness check, and stale-artifact check before push. Under the interim flow these checks still happen (Claude runs them in sandbox and reports in chat), but they're advisory rather than push-gating. Operator is the effective gate for all four.

**Considered (and rejected) alternatives:**

- **(a) Revise D-029 itself.** Adding a superseding clause to D-029 §2 that describes the interim flow. Rejected as heavier than needed — D-029's core commitments are correct; only one clause of its implementation picture is incomplete. Retaining D-029 as-is and recording the gap in a separate entry preserves D-029's legibility and makes the gap discoverable as a distinct governance event.
- **(b) Wait to resolve until a push mechanism is available.** Reject the interim flow, pause all session work until D-029 is properly implementable. Rejected — the project has substantive work (main sweeps, I-017 disposition, stale-file cleanup) that is independent of the push mechanism and does not benefit from being blocked. §13.5.7 exists precisely to allow work to proceed during setup gaps.
- **(c) Paste PAT into chat under OOP each session.** Use Playbook §5 to override SECRETS_POLICY §A.6 per session. Rejected — SECRETS_POLICY §A.6 is one of the tightest governance commitments in the project, and routinely OOP-overriding it to save operator upload effort is a bad governance tradeoff. OOP is for genuine emergencies, not for working around architectural gaps.

**Commitment:**

1. **The interim flow (steps 1-5 above) is the default deployment mechanism for this project for H-017 and all subsequent sessions, until superseded.** No per-session re-ratification is required. The default is safe-by-fail — if Claude or operator is uncertain about mechanism at any session-open, drag-and-drop-to-staging is the assumed flow.

2. **`main` is never pushed to directly.** All commits reach `main` via a merge from `claude-staging`. This is operator-enforced (Claude has no push mechanism) and, optionally, can be structurally enforced via GitHub branch protection rules on `main` (not required by D-030; recommended as complementary hygiene).

3. **D-029 Commitment §2 (authentication via Render env var) is suspended pending resolution.** The Render env var `GITHUB_PAT` (if set by operator per D-029 implementation §2) is not currently referenced by any active code path. Operator may leave it set or delete it; no functional difference. Future resolution of the authentication mechanism may or may not use that specific pattern.

4. **A new pending operator decision is opened** (`POD-H017-D029-mechanism`) tracking the question "how should D-029's push mechanism actually work given Claude.ai's sandbox environment?" This POD is not urgent; it has no deadline, and the project operates correctly without it being resolved. It will be listed in STATE's `open_items.pending_operator_decisions` as an open item and surfaced at each session-open until resolved.

**Resolution path (not a commitment, just direction):**

At each future session-open, Claude surfaces the D-029 mechanism question briefly if any of the following has changed:

- GitHub MCP connector added to Anthropic's registry (check takes one `search_mcp_registry` call).
- Other sandbox-accessible secret-injection mechanisms made available in Claude.ai.
- Operator preferences shift (e.g., "I'm fine pasting the PAT per session with rotation," which would require a SECRETS_POLICY §A.6 revision DJ entry, not an OOP).
- An alternative architecture surfaces (e.g., a small shim service that reads `GITHUB_PAT` from Render and pushes on Claude's behalf via an API Claude can call).

Any of these, if material, becomes its own targeted DJ entry at that session. No pressure to resolve on any particular cadence.

**Scope and carve-outs:**

- **D-029's substantive commitments remain fully active.** Merge-gate, sole-authoring, always-replace, no-secrets-in-chat, observation-lock-preservation, OOP-cannot-bypass-merge-gate — all preserved. D-030 touches only Commitment §2 (the authentication mechanism clause).
- **Playbook §13 stands unchanged.** §13.5.7's transitional-failure-mode text is applicable to the current state. If §13 text needs revising to reflect the new default (e.g., because §13.5.7's language implies the failure is temporary-and-specific-to-a-session rather than general), that's a Playbook revision to do when we have more clarity on the resolution path — not now.
- **SECRETS_POLICY is unchanged.** The PAT (if it exists on Render) is still a secret; §A.6 still governs it.
- **OBSERVATION_ACTIVE soft lock is unchanged.** Enforced in Claude's behavior layer, independent of commit mechanism.

**Effect on other decisions and governance artifacts:**

- **D-029:** preserved verbatim; Commitment §2 annotated as "suspended pending resolution per D-030" in any downstream references.
- **Playbook §13.5.7:** currently-invoked failure mode, now the effective default. No text change to §13 at this time.
- **STATE:** gains `POD-H017-D029-mechanism` in `open_items.pending_operator_decisions`. DJ counter increments 29 → 30. No other YAML changes caused by D-030 specifically.
- **Plan §1.5.3 / §1.5.4 revision (v4.1-candidate-4):** still queued; the revision target text (Claude pushes to staging; operator merges) remains correct at the governance-intent level. The interim mechanism doesn't change the plan-revision's target text, only its implementation schedule.

**What this decision does not decide:**

- **Which resolution path is best.** Options named above are sketched, not evaluated. Evaluation happens in a targeted future DJ entry when one of the options becomes concretely available.
- **A deadline for resolution.** Open-ended; the project operates correctly under the interim flow.
- **Whether D-029 should eventually be retracted and replaced.** Premature; depends on what the resolution looks like.
- **Whether per-session re-ratification should be required if the situation persists for many sessions.** β-i was chosen per operator ruling at H-017; if drift concerns surface later, a follow-up DJ entry can impose ratification cadence.

**Evidence trail:**

- D-029 §2 (H-016 DecisionJournal): PAT-via-Render-env-var mechanism as drafted.
- Playbook §13.2, §13.5.7 (H-016): preconditions requiring Render-env-var access; transitional-failure-mode language.
- H-017 chat exchange: Claude surface of architectural gap before first-use; operator validation of Render config (Auto-Deploy: On commit, Branch: main); operator ruling on Option β-i.
- SECRETS_POLICY §A.6: secret values never in chat transcript (constraint that rules out Option (c) above).
- H-016 always-replace-never-patch commitment (carried forward in interim flow step 1).

---

## D-029 — Deployment procedure revision: Claude pushes to a staging branch; operator merges to `main`

**Date:** 2026-04-19
**Session:** H-016
**Type:** Governance / Process / Supersedes plan §1.5.3 language

**Source:** Operator direction at H-016 close ("I also want to modify the deployment procedures as this session has simply underscored the need for") following an in-session exchange about the risks of the current drag-and-drop upload flow. Motivated by concrete recurring failure modes observed across H-012 through H-016:

- **H-014:** STATE v11 omitted from H-013 commit bundle (operator error at upload time). H-014-Claude had to surface the discrepancy before any substantive work and receive the missing file out-of-band.
- **H-015:** two multi-line pasted snippets in the Render Shell failed due to bracketed-paste markers. Separate from commit flow but same class of manual-interaction fragility.
- **H-016:** on the same bundle upload, (a) `DecisionJournal.md` was not included in the first commit (operator had to make a follow-up commit to add it), and (b) three reference artifacts (`COMMIT_MANIFEST.md`, `CHECKSUMS.txt`, `D-028-entry-to-insert.md`) were inadvertently committed. The `D-028-entry-to-insert.md` artifact was itself a Claude-originated process error — mid-session Claude produced a splice-into-existing-file instruction rather than a complete replacement file, deviating from the established "Claude produces full replacements; operator uploads" convention. The combination of Claude's process error and the drag-and-drop workflow's silent-missing-file failure mode produced a partially-wrong commit that required detection and remediation mid-session.

The pattern across these events: the current workflow's failure modes are not in the authoring (Claude's code/docs are generally correct) but in the transfer from chat to repository. The friction of "operator manually assembles the bundle" is not adding safety; it is adding a class of mechanical errors that silently corrupt commits.

**Decision:** Adopt a two-stage deployment model:

1. **Claude pushes code and documentation changes to a dedicated staging branch (`claude-staging`).** Claude uses a non-expiring GitHub personal access token (PAT) with write access scoped to the `peterlitton/pm-tennis` repository only. The PAT value is stored as a Render environment variable (e.g., `GITHUB_PAT`) on the working service; values never enter the chat transcript per SECRETS_POLICY §A.6.

2. **Operator merges the staging branch to `main` on explicit approval.** The merge is the human-in-the-loop checkpoint that replaces the current upload step. Operator reviews the staging branch's diff in the GitHub web UI before merging. The merge is the single action that promotes code to production.

This supersedes the plan's §1.5.3 language "Claude writes code and documentation; operator reviews and commits but does not author" with a revised version that reads: "Claude writes code and documentation and pushes to a staging branch; operator reviews and merges staging to main." The single-authoring-channel principle is preserved — Claude is still the sole author of code and docs — but the commit mechanism changes.

**Considered:**

- **(a) Keep current workflow.** Rejected. Three sessions of failure modes document the real cost; H-016's specific compound error (missing DJ + stale artifacts committed) demonstrated the drag-and-drop flow's risk exceeds its benefit as an oversight mechanism.
- **(b) Claude pushes directly to `main`.** Rejected. Removes the human-in-the-loop checkpoint entirely. H-008 is a cautionary tale: if Claude had pushed directly at H-008, the fabricated Sports WS URL would have hit production with no pause for operator review. Even with strong research-first discipline, the merge gate has independent safety value.
- **(c) Claude pushes to a feature branch per session, operator merges per-branch.** Similar to (d) but with per-session branch names (`h-016-staging`, `h-017-staging`, etc.). Rejected as marginally more complex than a single `claude-staging` branch with no corresponding benefit; per-session branches would accumulate in the repo, and session boundaries are already tracked via handoffs and STATE.
- **(d) Claude pushes to a single persistent `claude-staging` branch, operator merges to `main`.** **Selected.** Single branch, clear merge path, diff-review built into GitHub's PR/merge UI, history preserved in git.

Selected: (d). Operator ruling.

**Rationale:**

1. **The failure modes are real and recurring.** Three separate sessions (H-014, H-015, H-016) produced upload-flow failures of different kinds. The current workflow's safety value depends on operator scrutiny of files before upload, which is not happening in practice — the operator has stated explicitly "I'm already blindly just taking your files and uploading them to Git without scrutinizing them." The drag-and-drop step is therefore not contributing to safety; it is only contributing to failure rate.

2. **The staging-branch model preserves what matters about the current flow.** The human-in-the-loop checkpoint — operator sees what's landing before it lands — moves from "operator looks at filenames in a drag-and-drop dialog" to "operator reviews a diff in GitHub's PR/merge UI." The latter is strictly more informative. The former was already not being exercised.

3. **Claude-led validation on deployed-but-not-merged code catches a class of bugs the current flow cannot catch.** Tests that run in Claude's sandbox run against Claude's filesystem layout and Python version. Tests that run on the deployed staging branch (via a Render preview environment or a GitHub Action) run against the actual Render Python version, the actual filesystem layout, and the actual deployed dependency set. This is qualitatively stronger coverage. Claude can add staging-branch validation steps (run tests, lint, check paths, smoke-deploy to a preview Render service) as pre-merge evidence.

4. **The failure mode the staging approach newly introduces is bounded.** If Claude pushes wrong content to staging, it lives in the staging branch until operator merges. Operator reviews the diff before merge. A bad push to staging is auto-contained; it does not affect `main` or any deployed service. Recovery is: Claude pushes a fix to staging, operator re-reviews, merges when satisfied. Cost: ~nothing.

5. **The authentication material is already well-governed.** SECRETS_POLICY §A.6 already prohibits secret values from entering the chat. D-023 demonstrated the pattern for Polymarket credentials (Render env vars, read by name, never in repo). The same pattern applies to a GitHub PAT or MCP token: stored in the platform's credential interface, never in chat, never in repo.

6. **The H-008 objection is addressed by the merge gate, not by the push mechanism.** H-008's failure was research-first discipline, not commit mechanics. Research-first (D-016 commitment 2, R-010) remains fully in force under this revision. The merge gate in the staging model provides an additional independent safety layer — even if Claude's research-first discipline slipped, the bad push would sit in staging for operator review before reaching main.

**Commitment:**

1. **A `claude-staging` branch exists in the `peterlitton/pm-tennis` repository.** It tracks `main` at session open and receives Claude's pushes during the session. Per session, Claude pushes all changes to staging; operator merges staging → main once per session (or less frequently, batching multiple sessions into one merge if appropriate). The merge is the gate.

2. **Claude authenticates to GitHub via a non-expiring, fine-grained Personal Access Token (PAT).** Operator generates the PAT via GitHub settings → Developer settings → Personal access tokens → Fine-grained tokens. Scope: single repository (`peterlitton/pm-tennis`), read/write on Contents, no admin, **expiration set to "No expiration"**. PAT value stored as a Render environment variable (e.g., `GITHUB_PAT`) on the working service. Value never enters the chat transcript per SECRETS_POLICY §A.6. Rotation is operator-initiated at any time (revoke in GitHub settings, generate new, update Render env var); not scheduled.

   **Rationale for no expiration:** generic "rotate every 60-90 days" security advice is oriented toward multi-person teams and broader-scope credentials. For this project specifically — single operator, solo project, PAT scoped to one repository with write-only permission, stored in the same env-var system that already holds Polymarket credentials — the failure mode the expiry guards against (indefinite exposure from a leaked credential) is narrow. The failure mode no-expiry guards against (rotation-miss friction at a rotation date) is proportionally larger. Non-expiring is the right tradeoff for this project's threat model. Operator may rotate voluntarily at any cadence.

   **MCP connector alternative explicitly not selected.** At H-016 investigation, Claude searched the Anthropic MCP registry and found GitLab, Microsoft Learn, and other connectors listed, but not GitHub. The MCP-connector option Claude had initially recommended in-session was therefore not available at decision time. Future Claude sessions may re-check the MCP registry; if GitHub MCP is added later and operator prefers to migrate, that migration is its own (small) DJ entry and does not require superseding D-029.

3. **Claude's push discipline on the staging branch:**
   - Claude pushes logically coherent units of work (e.g., "helper-snippet flip", "I-016 fix", "§14 addendum") rather than single-file pushes. A typical session produces 1–5 pushes to staging.
   - Each push has a descriptive commit message identifying the H-NNN session, the scope, and any referenced DJ/RAID items.
   - Claude pushes the complete replacement of every changed file. No patch files, no splice-into-existing instructions, no "paste this section in." This was the rule pre-D-029 and remains the rule post-D-029 — D-028's preparation artifact (`D-028-entry-to-insert.md`) was a Claude-authored deviation from the established convention that should not recur.
   - Pre-existing files on `main` that Claude is not touching in a given session are NOT pushed to staging redundantly. The staging branch reflects main's state plus Claude's per-session changes; it does not drift from main on files Claude hasn't touched.

4. **Validation Claude runs before requesting merge:**
   - **Full test suite in clean venv against pinned deps.** Same posture as the current in-session sandbox test run, now cited in the merge request.
   - **Path-correctness verification.** Claude lists every file it pushed, the path it pushed it to, and an assertion that the path matches the intended location. This catches the class of bugs where a file was produced but placed at the wrong repo path.
   - **Schema/coupling check where applicable.** If Claude touched a commitment file, the SHA change is named. If Claude touched a file whose behavior is documented elsewhere (doc-code-coupling rule per Orientation §8), the paired documentation update is named.
   - **Summary presented to operator with explicit merge-request language:** "Staging push complete. NN files changed (list). Tests: pass. Ready for your review and merge when you are." No ambiguity about whether Claude has finished.

5. **Operator merge-gate discipline:**
   - Operator reviews the diff in GitHub's web UI (compare branch view or PR view) before merging. Spot-check scope is operator's choice — at minimum, the file list and commit message, ideally skim of any critical-path changes (commitment files, STATE, DecisionJournal, build plan).
   - Merge is explicit: squash-merge or merge-commit, operator preference. No auto-merge.
   - Operator may request changes before merge. Claude addresses and re-pushes to staging; operator re-reviews. No limit on iteration cycles.
   - If operator discovers a problem post-merge, the problem is logged as a DJ entry, the fix goes through the same staging workflow (Claude pushes fix to staging, operator merges).

6. **Observation-active soft lock is not weakened by this revision.** Claude refuses to modify any commitment file or any file during an active observation window regardless of the commit mechanism. The staging branch does not receive pushes to locked files during observation. The lock is enforced in Claude's behavior, not in the commit mechanism.

7. **Out-of-protocol invocations (Playbook §5) are not affected.** OOP can suspend specific rituals for a specific task; the merge-gate is not itself an OOP-suspendable step because it is the single operator-authority moment in the workflow. An OOP request that would push directly to main (bypassing the merge gate) is refused, same as an OOP request to modify a commitment file during observation is refused.

8. **Session-close handoff production and STATE update are unchanged.** Both remain Claude-authored, pushed to staging, merged with the rest of the session's output. The handoff and STATE updates are part of the per-session bundle.

**Scope and carve-outs:**

- **Pre-existing operator-authored commits are not retroactively remediated.** The stale artifacts committed at H-016 (`COMMIT_MANIFEST.md`, `CHECKSUMS.txt`, `D-028-entry-to-insert.md`) remain in the repo until an H-017 cleanup commit removes them. No retroactive rewriting of history.

- **Operator-initiated mechanical actions remain permitted per Playbook §10.** Creating a branch, merging a PR, deleting a misplaced file in the web UI — these remain operator-permitted actions and do not require opening a session. Playbook §10's permitted-actions list is unchanged.

- **The `main` branch remains the source of truth for deploy.** Render's `pm-tennis-api` continues to auto-deploy from `main`. Staging pushes do not trigger a deploy of production services. Staging may optionally be configured to deploy to a preview Render environment for Claude-led validation; that is a setup decision at D-029 implementation time.

**Effect on other decisions and governance artifacts:**

- **Plan §1.5.3** (single-authoring-channel): requires revision. Queued as `v4.1-candidate-4` in STATE `pending_revisions`. Target text: "Claude writes code and documentation and pushes to the `claude-staging` branch; operator reviews and merges staging to `main`. Claude is the sole author of code and documentation; operator is the sole committer to `main`." To be applied in the next plan revision per Playbook §12.

- **Playbook §10** (out-of-session commit ritual): no change. Its scope is "operator making an edit directly between sessions" — distinct from the staging-branch workflow. §10 still governs the "operator-authored commit outside a session" failure mode.

- **Playbook §13** (new): the staging-push-and-merge ritual. Created as part of this commitment. Covers: ritual name and scope, preconditions, procedure, postconditions, failure modes, logging requirements. Follows the standard Playbook structure.

- **SECRETS_POLICY §A.2 / §B.2**: implicitly extended to cover the GitHub PAT or MCP token if applicable. Existing language already names GitHub personal access tokens as a secret class; this revision uses one but does not change policy about it.

- **D-016 commitment 2** (research-first discipline): fully preserved. Claude's obligation to cite external API shapes, module symbols, etc. against authoritative sources is unchanged. The staging mechanism does not relax any authoring-side discipline.

- **OBSERVATION_ACTIVE soft lock**: fully preserved. Enforced in Claude's refusal behavior, not in commit mechanism. Pushing to staging is still refused for locked files.

**What this decision does not decide:**

- **Branch protection rules on `main`.** Setting up branch protection (requiring PR review, blocking force-push) is a GitHub-level operator action that complements this decision but is not required by it. Recommended at setup time.
- **Preview environment for staging.** Deploying the staging branch to a preview Render service is a setup-time option, valuable if main-sweeps or similar work benefits from live-on-Render test runs pre-merge. Not required.
- **Scope of Claude-led validation.** D-029 names the minimum validation (tests, paths, schema, summary). Additional validations (linting, typechecking, deploy smoke) are added as specific deliverables warrant, logged as decisions when they reach DJ-entry threshold.
- **Future MCP migration.** If GitHub MCP connector becomes available in the Anthropic registry later and operator prefers it, migration is its own (small) DJ entry at that time. D-029 stands as-is until superseded.

**Implementation sequencing:**

1. **Operator generates the PAT.** GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token. Scope: repository access = only `peterlitton/pm-tennis`; repository permissions = Contents (read+write); expiration = "No expiration." Copy the generated token (GitHub shows it once).
2. **Operator adds the PAT to Render.** Dashboard → the service Claude will push from (likely `pm-tennis-api` or a dedicated service — either works) → Environment → add `GITHUB_PAT` (or similar name) with the token value. Render masks after save per D-023 subsidiary finding 3. **Do not paste the PAT value into chat per SECRETS_POLICY §A.6.**
3. **Operator creates the `claude-staging` branch** from current `main` in the GitHub web UI. Optional but recommended: configure main-branch protection in GitHub settings (require merge commit, block force-push, no direct-push-to-main). These settings supplement D-029 by making the merge gate structurally enforced rather than just policy-enforced.
4. **Operator reports back to Claude at next session open:** "D-029 auth ready, env var name is `GITHUB_PAT`, staging branch exists." Claude verifies via a small test push to staging.
5. **First real use** of the staging flow: first non-trivial commit of H-017 or later.
6. **Plan §1.5.3 and §1.5.4 revision** (`v4.1-candidate-4`) applied at the next plan-revision cadence per Playbook §12.

**Evidence trail:**

- H-014 handoff §9 and Handoff_H-014 notes: STATE v11 missed from commit bundle.
- H-015 handoff §3.2 and §6: two multi-line paste failures in Render Shell (distinct from commit flow but same fragility class).
- H-016 chat transcript: operator "I've already committed the zip file content" → Claude verification → finding that `DecisionJournal.md` was absent from the first commit and stale artifacts were present. Operator subsequent commit `83c0bf8` to add the DJ. Operator explicit statement: "DJ was not in the bundle just the entry to insert (BAD execution choice—too much manual error risk. for every deploy in other sessions I've ALWAYS been instructed to replace)".
- Extended H-016 exchange on the tradeoffs between direct-push-to-main, staging-push, current-flow, with operator surfacing the specific failure modes the current flow had produced.

---

## D-028 — RAID I-016 fix: source `event_date` from `startDate`, with `slug_selector` fallback for historical meta.json

**Date:** 2026-04-19
**Session:** H-016
**Type:** Bug fix / Phase 2 + Phase 3 / Operator-authorized

**Source:** Operator authorization at H-016 ("c with thorough documentation"), responding to Claude's three-option proposal for fixing RAID I-016 (empty `event_date` field in production meta.json). Investigation triggered by H-015's blocked probe attempt, completed at H-016 by reading a real raw gateway payload from event 9471 in the `pm-tennis-api` Render Shell.

**Decision:** Apply Fix C — both a forward-going extraction fix in `src/capture/discovery.py` AND a backward-compatible fallback in `src/stress_test/slug_selector.py`. Specifically:

1. **`src/capture/discovery.py` line 328** — change the `event_date` extraction from `event.get("eventDate")` (a key the gateway response does not include) to `str(event.get("startDate") or "").strip()[:10]`. Preserves the `event_date` field name on `TennisEventMeta` and its YYYY-MM-DD format; only the source key changes. Phase 2 code touched per explicit operator authorization separate from the Phase 3 attempt 2 work package (D-016 commitment 2).

2. **`src/stress_test/slug_selector.py` `_passes_date_filter`** — modify to read `event_date` first, then fall back to `start_date_iso[:10]` if `event_date` is empty or unparseable. The `start_date_iso` field has been correctly populated since Phase 2 deploy (it has always been sourced from `event.get("startDate")` on line 330 of discovery.py); the fallback makes ~116 historical meta.json files (written H-007 through H-016 with empty `event_date`) usable as probe candidates without mutating the immutable on-disk records.

3. **Test fixture correction at `tests/test_discovery.py`** — remove the `"eventDate": event_date` key from `make_raw_event()` (line 89 pre-fix). The fixture had been silently masking I-016: the production gateway has no `eventDate` key, but the test fixture provided one, so production code passed tests against a payload shape that did not match reality. The fix removes the false key and adds a fixture-level assertion in the new I-016 regression tests to guard against re-introduction.

**Considered (from H-016 in-session proposal):**

- (A) **Fix discovery.py only.** Smallest change. Forward-going correctness; historical 116+ meta.json files remain unusable (they're immutable per `_write_meta`).
- (B) **Workaround in slug_selector only, no Phase-2 touch.** Historical files immediately usable; bug in discovery.py persists; any future consumer of meta.json's `event_date` field still sees empty values.
- (C) **Both.** Forward correctness AND backward compatibility. Two file changes; touches Phase 2.

Selected: (C). Operator ruling.

**Rationale (operator-approved):**

1. **The investigation produced ground truth.** A live read of `/data/matches/9471/meta.json` in the pm-tennis-api Render Shell at H-016 confirmed the I-016 hypothesis: `event_date=""`, `start_date_iso="2026-04-21T08:00:00Z"`, `start_time="2026-04-21T08:00:00Z"`, `end_date_iso="2026-04-21T23:59:00Z"`. Three of the four date-ish fields are populated; only `event_date` is empty. The Polymarket gateway payload uses `startDate`, not `eventDate`. This is not inferred — it is read.

2. **Surface-area minimization.** Fix A is one line. Fix B is one function rewrite with comprehensive docstring. The total code change is small (under 100 lines including comments), and its blast radius is bounded: discovery.py extracts the same field name in the same format from a different source; slug_selector falls back through a field that has always been populated. No cross-module signature changes, no schema changes to meta.json.

3. **Backward compatibility is real value.** ~116 meta.json files exist on disk at H-016 (up from 74 at H-012 and 38 at H-009). Phase 2 discovery has been writing one file per discovered event since H-007. All of them have empty `event_date`. Without Fix B, every one of those files would never reach probe-eligibility — they would be filtered out forever. The probe could only run against events discovered AFTER the H-016 fix lands, which would needlessly delay the Phase 3 work by however long it takes for fresh eligible matches to come into the discovery window. With Fix B, the existing archive is immediately usable.

4. **The doc-coupling rule applies.** Per Orientation §8, code changes whose behavior is described in project documentation require the documentation to be updated in the same commit. The slug_selector module docstring (top of file, item 1 in the design-constraints list) named `event_date` as a required field. The function docstring of `_passes_date_filter` described "Require event_date to be today or future" with no mention of fallback. Both are updated to reflect the new behavior.

5. **Test fixture honesty.** The pre-fix fixture in `tests/test_discovery.py` line 89 included `"eventDate": event_date`, simulating a gateway response shape that does not exist in reality. This is the same failure mode H-008 surfaced (writing code against names Claude never verified exist), expressed in test-fixture form. The fix corrects the fixture and adds a regression test that asserts `"eventDate" not in raw` before parsing — guarding against any future re-introduction of the same masking bug.

**Subsidiary finding surfaced during investigation (worth recording, not a separate decision):**

Production behavior of `_check_duplicate_players` (discovery.py line 416) has been silently broken since Phase 2 deployed at H-007. The function short-circuits to `return False` on line 424 when `new_meta.event_date` is empty. Because every meta.json from H-007 through H-016 had empty `event_date`, the duplicate-player detection has never fired in production — the `duplicate_player_flag` field has been unconditionally `False` across all 116+ records.

The H-016 fix automatically restores this functionality going forward: meta.json files written from H-016 onward will have correct `event_date`, so `_check_duplicate_players` will work as designed for new events. The historical 116+ files remain affected (their `duplicate_player_flag` stays at the never-checked default) but cannot be retroactively corrected without re-writing immutable on-disk records, which is out of scope.

This is a side-benefit of the fix, not its motivation. No separate code change is needed; flagging here for completeness so the duplicate-player metric can be interpreted correctly during any future analysis (e.g., "duplicate_player_flag is reliable for events with discovered_at >= H-016 timestamp; treat as missing for earlier records").

**Commitment:**

1. `src/capture/discovery.py` line 328 reads `event_date` from `startDate[:10]`. This is the canonical source going forward. Any future change to the date-extraction logic that does not match this pattern requires a new DJ entry.

2. `src/stress_test/slug_selector.py` `_passes_date_filter` falls back to `start_date_iso[:10]` when `event_date` is empty or malformed. This fallback is permanent — even after all historical meta.json files have aged out of relevance (events past their match date), removing the fallback would be a behavior change that requires its own DJ entry. The cost of keeping it is essentially zero (one extra dict lookup); the value is defense-in-depth against any future similar regression.

3. Test fixture in `tests/test_discovery.py` `make_raw_event()` does NOT include an `eventDate` key. Three new tests (`test_i016_event_date_sourced_from_startDate`, `test_i016_event_date_empty_when_startDate_missing`, `test_i016_event_date_ignores_legacy_eventDate_key`) pin the new behavior and explicitly guard against fixture-level masking re-introduction.

4. Six new tests in `tests/test_stress_test_slug_selector.py` (the `test_i016_fallback_*` group) cover the fallback path: empty event_date + future start_date_iso passes; empty event_date + past start_date_iso rejected; both empty rejected; malformed event_date falls through to fallback; populated event_date wins over divergent start_date_iso; non-string fallback rejected gracefully.

5. RAID I-016 is marked Resolved at H-016, with reference to this entry. The RAID Issues table is updated in the H-016 commit bundle.

6. Three plan-text revisions queued in STATE `pending_revisions` are NOT modified by this entry; they remain Phase 2 / cross-section corrections to be cut in a future plan revision under Playbook §12.

**Effect on other decisions:**

- **D-016 commitment 2** (research-first discipline): satisfied. The fix was driven by a live read of the actual gateway payload, not by inference from documentation. Every claim about the gateway shape in this entry traces to the operator-pasted output of `cat /data/matches/9471/meta.json` at H-016.
- **D-016 commitment 1** (Phase 2 attempt 2 begins from c63f7c1d-equivalent state): unchanged. This entry modifies one line of Phase 2 code under explicit operator authorization, which is the supported escape hatch. The c63f7c1d baseline remains the reference point for the Phase 3 attempt 2 work package.
- **D-027 commitment 1** (probe-slug supplied via CLI `--slug` argument): unchanged. This fix makes the slug-selection path more reliable but does not change the transport mechanism.
- **D-018, D-019, D-020, D-021, D-022, D-023, D-024, D-025, D-026**: unchanged.

**What this entry does not decide:**

- It does not authorize a backfill of historical meta.json files. The 116+ existing files remain as written; the fallback in slug_selector handles their consumption.
- It does not modify the `start_time` field's behavior in discovery.py (the dataclass docstring on line 160 says "HH:MM or empty" but the actual gateway returns a full ISO timestamp; `start_time` is currently a duplicate of `start_date_iso` in production). This is a separate schema-doc-vs-reality drift surfaced incidentally during H-016 investigation; it does not affect probe selection or any downstream consumer in current scope. Logged for a future minor cleanup, not for this commit.
- It does not change any commitment file (`fees.json`, `breakeven.json`, `signal_thresholds.json`, `data/sackmann/build_log.json`). None are in the path of this fix.

**Evidence trail:**

- Live raw read at H-016 from pm-tennis-api Render Shell:
  - `ls -t /data/matches/ | head -5` → top 5 event_ids: 9471, 9469, 9470, 9466, 9467.
  - `cat /data/matches/9471/meta.json` → revealed `event_date=""`, `start_date_iso="2026-04-21T08:00:00Z"`, `start_time="2026-04-21T08:00:00Z"`, `end_date_iso="2026-04-21T23:59:00Z"`.
- Code reads at H-016:
  - `src/capture/discovery.py` lines 328–331 (extraction code)
  - `src/capture/discovery.py` lines 139–193 (TennisEventMeta dataclass)
  - `src/capture/discovery.py` lines 416–435 (_check_duplicate_players, surfaced subsidiary finding)
  - `src/stress_test/slug_selector.py` lines 142–156 (_passes_date_filter pre-fix)
  - `tests/test_discovery.py` line 89 (fixture with false eventDate key)
- Test runs against pinned deps in clean venv (polymarket-us==0.1.2, pytest==8.3.4, Python 3.12.13):
  - Baseline (unmodified main branch at commit 274cd09): 38/38 stress-test tests pass; 47/49 discovery tests pass with 2 pre-existing failures in `TestVerifySportSlug` unrelated to I-016.
  - Post-fix: 79/79 tests pass in the scope of H-016 changes (15 in TestParseEvent including 3 new I-016 regression tests; 4 in TestCheckDuplicatePlayers; 25 in slug_selector including 6 new I-016 fallback tests; 19 in probe_cli unchanged; 20 in list_candidates from earlier H-016 work). The 2 pre-existing TestVerifySportSlug failures are unaffected by this fix and remain out of scope.

**Subsidiary finding to surface for separate disposition:**

Two pre-existing test failures in `TestVerifySportSlug` (`test_network_failure_raises_system_exit`, `test_empty_sports_list_raises_system_exit`) exist on the baseline `main` branch at H-016 open and persist through the H-016 fix. Both expect `SystemExit` but the production code raises `RuntimeError`. This is unrelated to I-016 — the affected code path is `verify_sport_slug` startup behavior, not `_parse_event` extraction. Worth a separate RAID entry or DJ entry at next session, but explicitly out of scope for D-028.

---

## D-027 — Probe-slug transport: operator-supplied CLI argument (supersedes D-025 commitment 1)

**Date:** 2026-04-19
**Session:** H-013
**Type:** Architecture / Supersession

**Source:** Operator ruling at H-013 after Claude fetched `render.com/docs/disks` during probe-scaffolding work and discovered the D-025 commitment 1 architecture was not implementable on Render. Operator ruled "Option D" then "Supersession" when asked whether D-027 should re-interpret or supersede D-025.

**Decision:** The probe slug is supplied to the stress-test probe as an operator-provided CLI argument (`--slug=SLUG`, with optional `--event-id=EVENT_ID` for traceability), not read from the shared Render persistent disk. `src/stress_test/slug_selector.py` remains in the codebase as a library for local development and for a pm-tennis-api-Shell helper command that lists eligible candidates, but is not called by the production probe path on the isolated `pm-tennis-stress-test` Render service.

This supersedes D-025 commitment 1, which specified the probe would read one gateway-sourced slug directly from a Phase 2 `meta.json` file under `/data/matches/`. The research-question intent of D-025 (probe a gateway-sourced slug against the api WebSocket to characterize the gateway-to-api slug bridge) is preserved; only the transport mechanism changes. D-025 commitments 2, 3, and 4 are unaffected.

**Considered (from in-session exchange, full text in Handoff_H-013):**

- (A) Run the probe from `pm-tennis-api` Shell — uses the already-attached disk natively, but requires modifying `pm-tennis-api/requirements.txt` to add `polymarket-us` (violating D-024 commitment 1) and weakens the D-020/Q2=(b) isolation.
- (B) Expose an HTTP endpoint on `pm-tennis-api` that returns eligible candidates as JSON; stress-test service fetches via HTTPS — preserves isolation but requires a behavior change to the production discovery service and adds an auth surface (shared-secret reuse).
- (C) Have the probe fetch candidates directly from the gateway (`gateway.polymarket.us/v2/sports/tennis/events`) at runtime — perfect isolation but conflicts with D-025's commitment-1 language literally (slug sourced fresh from gateway at probe time, not from Phase 2's archived copy), and pulls a new external dependency onto the probe critical path.
- (D) Operator picks a slug via `pm-tennis-api` Shell and passes it to the probe as `--slug` — preserves all isolation commitments, preserves D-025's research-question intent, adds an operator-in-the-loop step consistent with the rest of the project's posture.

Selected: (D). Operator ruling.

**Rationale (operator-approved):**

1. **Discovery that forced the ruling.** During H-013 probe-scaffolding work, Claude fetched `https://render.com/docs/disks` to verify the proposed shared-disk attach step in draft Runbook RB-002. The fetch returned authoritative text: *"A persistent disk is accessible by only a single service instance, and only at runtime. This means: You can't access a service's disk from any other service. You can't scale a service to multiple instances if it has a disk attached. You can't access persistent disks during a service's build command or pre-deploy command (these commands run on separate compute). You can't access a service's disk from a one-off job you run for the service."* This is fully authoritative Render documentation and does not admit any read-only-shared-mount pattern. Also confirmed in `feedback.render.com` staff response: "only a single instance can write to/read from them."

2. **D-024 commitment 1 and D-020/Q2=(b) are the binding isolation constraints.** `pm-tennis-api/requirements.txt` must not be modified by Phase 3 attempt 2; the stress-test code must run in a new, separate Render service, torn down after. Option A violates both. Option B preserves both but requires adding an endpoint to the running discovery service. Option D preserves both without any change to `pm-tennis-api`.

3. **D-025's research-question intent is preserved.** D-025 exists to answer: "can a slug that Phase 2 observed via the gateway be used to subscribe on `api.polymarket.us`'s WebSocket?" The operator picking that slug from Phase 2's archive via pm-tennis-api Shell and passing it to the probe is the same research question, same evidence — the slug was gateway-sourced, Phase 2 wrote it byte-identically to disk, the operator copies it out. The probe tests exactly what D-025 intended to test. Option D is semantically equivalent at the research level while being the only option compatible with Render's actual disk model.

4. **Supersession, not re-interpretation.** Per operator ruling, this entry is recorded as supersession of D-025 commitment 1 rather than re-interpretation. The reasoning the operator accepted: re-interpretation sets a precedent that Claude can soften committed language when implementation realities shift; supersession is more conservative, keeps D-025's original text intact in the historical record, and forces the new reality into a named, dated, numbered decision entry.

**Commitment:**

1. The stress-test probe (`src/stress_test/probe.py`) takes `--slug=SLUG` as its authoritative slug source in probe mode. `--event-id=EVENT_ID` is optional and informational only (appears in the outcome record for traceability, not dispatched on).
2. `slug_selector.py` remains in the repo. It is used by (a) the stress-test self-check mode as an informational report on local-dev fallback availability; (b) the pm-tennis-api Shell helper workflow for the operator to list candidates prior to probe invocation. It is **not** called in the production probe code path on the Render stress-test service.
3. If neither `--slug` nor a usable `slug_selector` fallback is available, the probe exits `EXIT_NO_CANDIDATE` with stderr naming the missing `--slug` argument and referencing RB-002. Silent fallback to whatever `slug_selector` returns is avoided because on the isolated Render service there is no `/data/matches/` to return from; any non-empty result would indicate a bug.
4. Runbook RB-002 (the Render-provisioning walkthrough) must be updated before H-014 deployment: Step 3 ("attach disk") becomes "skip — no disk attach for the stress-test service"; Step 5 ("how H-014 will execute the probe") becomes the two-shell workflow — list candidates in pm-tennis-api Shell, invoke probe in pm-tennis-stress-test Shell with `--slug` and `--event-id`. H-013 does not update RB-002 this session per the operator's Option X cut; the update is the first H-014 task.
5. `src/stress_test/README.md` similarly carries known-stale content about disk-based slug selection; update bundled with the RB-002 fix at H-014 open.

**Effect on other decisions:**

- **D-025 commitment 1:** superseded. D-025 footer updated to reference D-027. Commitments 2, 3, 4 remain unaffected. The hybrid-probe-first architecture itself (one-slug probe before main sweeps, outcome-determines-main-sweep-slug-source) is preserved intact.
- **D-024:** unchanged. SDK-based approach stands. D-024 commitment 1 (pm-tennis-api requirements.txt not modified) is actively reinforced by D-027's Option D.
- **D-020:** unchanged. Q2=(b) isolated Render service stands.
- **D-023:** unchanged. Credential env-var names and storage location stand.
- **D-026:** unchanged. §6 survey findings and N baseline stand; the survey's probe-slug-default recording (event 9392) is still the traceability anchor, now with the operator-selection workflow as the consuming path rather than runtime filesystem read.

**What this entry does not decide:**

- The specific text of Runbook RB-002's revised Steps 3 and 5 — authored at H-014 open.
- The specific text of `src/stress_test/README.md`'s revised sections — authored at H-014 open.
- Whether research-doc v4 gets a §15 additive or a v5 bump — H-014 ruling.
- Whether a pm-tennis-api Shell helper command for listing eligible candidates is a committed artifact or a throwaway one-liner — H-014 judgment; either suffices for the stress-test workflow.

**Evidence trail:**

- Render docs fetched H-013 via `web_fetch https://render.com/docs/disks` — full text preserved in the H-013 chat transcript.
- Research-doc v4 §4.5 remains the authoritative record of what the stress test exists to measure (per-subscription count, concurrent-connection count); D-027 changes none of that.
- Code changes landing this session implementing D-027: `src/stress_test/probe.py` (CLI flags + run_probe slug-source precedence + self-check D-027 awareness + section-header references); `tests/test_stress_test_probe_cli.py` (19 new tests covering argparse + exit-code paths + main() dispatch + ProbeOutcome + classification mapping + ProbeConfig clamping). All 38 tests (slug_selector 19 + probe CLI 19) pass.

---

## D-026 — POD-H010-§6-survey resolved: authorized and executed; N baseline = 74

**Date:** 2026-04-19
**Session:** H-012
**Type:** Research / Survey execution / POD resolution

**Source:** Operator direction at H-012: "Authorize §6 survey + read discovery.py first." Resolves POD-H010-§6-survey. Survey script produced by Claude, reviewed against `src/capture/discovery.py`-derived schema before execution, and executed by operator via Render shell on `pm-tennis-api` at 2026-04-19T16:22:29Z. Survey output pasted back in-session. Findings recorded in `docs/clob_asset_cap_stress_test_research.md` v4 §13.2.

**Decision:** POD-H010-§6-survey is authorized and executed. The three survey objectives (confirm on-disk schema, produce current N baseline for stress-test sweeps, identify probe-slug candidates for Q5′=(c′)) are met. No further operator decisions are required from this POD.

**Considered:**
- (a) Authorize and execute this session, with Claude reading `discovery.py` first to verify the `meta.json` schema before drafting commands
- (b) Authorize and execute this session, drafting from research-doc §6 alone without schema verification
- (c) Authorize but defer execution to a later session

Selected: (a). Operator ruling. Rationale for (a)-over-(b): research-doc v3 §6 was written before H-010 had access to the actual `meta.json` on-disk schema and used the casual phrasing "/data/events/" for the meta.json location, which is in fact the raw-poll-snapshot directory; per-match meta.json files live at `/data/matches/{event_id}/meta.json` per `discovery.py` `_meta_path()`. Drafting commands against research-doc §6 alone would have pointed at the wrong directory. Reading `discovery.py` first caught the drift before command execution. This is a small but concrete illustration of the H-011-addendum lesson about checking second sources.

**Survey script as-executed:** reproduced verbatim in Handoff_H-012 §4. Five sections: (1) directory and count, (2) sample meta.json, (3) total slug count, (4) distribution, (5) status flags + sample slugs. All read-only; no mutation.

**Findings:**

1. **On-disk schema confirmed.** `meta.json` contents match the `TennisEventMeta` dataclass in `src/capture/discovery.py` lines 139–193. Top-level `moneyline_markets[]` with per-element `market_slug` (string). The schema reflected in the v3 research doc (under §2 and §3) is confirmed as accurate at the field-name level; the only correction is the *path* (research-doc v3's casual "/data/events/" reference, now corrected to `/data/matches/{event_id}/meta.json`).

2. **N baseline = 74.** Total market slugs across all 74 active tennis events at survey time. Up from the ≈38 estimate in research-doc v3 §5 ("actual asset count we expect") which was as-of H-009 close. The doubling is explained by ~36 hours of continuous Phase 2 discovery writing new immutable `meta.json` files since H-009 — `_write_meta` never overwrites (discovery.py line 371), so the archive accumulates monotonically. This is expected behavior, not drift.

3. **Distribution is uniform.** All 74 events carry exactly 1 moneyline market. No multi-moneyline events in the current population. Sweep arithmetic in §7 Q3 remains valid; the 100-slug-per-subscription cap (§4.4) is not approached by real slugs alone.

4. **All 40 surveyed events are active/not-ended/not-live.** `active=True`, `ended=False`, `live=False` on every surveyed row. No status filtering is needed for the probe — any surveyed event is a valid candidate at survey time.

5. **Probe-slug default selected.** Event 9392, slug `aec-atp-digsin-meralk-2026-04-21`, ATP match 2026-04-21 between Digvijaypratap Singh and Mert Alkaya. Selected from the most-recently-discovered batch (timestamp 2026-04-19T14:04:52Z, 4 candidates in that batch). Recorded in research-doc v4 §13.4 for traceability. Not committed as the probe slug at code-turn time — at code-turn time a fresh `meta.json` scan selects the probe slug, because the survey snapshot will be ~hours to ~days old by then and candidates may have ended.

6. **Incidental confirmation.** `participant_type` on the sample event is `PARTICIPANT_TYPE_TEAM`, consistent with STATE `discovery.participant_type_confirmed` and A-009. The slug format `aec-<tour>-<player_a_abbrev>-<player_b_abbrev>-<YYYY-MM-DD>` is observed consistently across all 40 surveyed slugs; the `aec-` prefix is a Polymarket US convention not interpreted by this document.

**Commitment:**

1. The code-turn scoping document (research-doc v4 §13.5) is the canonical reference for what the stress-test code inherits. It consolidates D-023, D-024, D-025, and D-026 findings.
2. The probe-slug default (event 9392) is a traceability anchor only. Actual slug selection at code-turn time re-reads `/data/matches/*/meta.json`.
3. STATE `discovery` block updated at session close to reflect the new event and meta.json counts (38 → 74) per the survey findings. This is a refresh of a stale snapshot, not a revision of prior work.
4. Research-doc v4 is the canonical version going forward. v3 is preserved in git history.

**Subsidiary finding surfaced during survey:**

Research-doc v3 referenced meta.json locations casually as "/data/events/" in several places (§7 Q5′ and D-025's commitment 1 draft, pre-H-012). The actual path is `/data/matches/{event_id}/meta.json`. **This is a v3 text error, not a v4 revision target** — per the scoping decision for v4 (additive only), v3's text is preserved as accepted; v4 §13 notes the correction in the survey-findings discussion. If the operator wants v3's "/data/events/" references retroactively corrected, that becomes a separate v4.1 revision or a future-session cleanup. Not urgent.

**Effect on other pending operator decisions:**

None remain blocking the code turn. The H-010 POD queue (POD-H010-Q4, -Q5′, -§12, -§6-survey) is fully resolved across H-011 (D-023) and H-012 (D-024, D-025, D-026). Code turn is blocked only on code-turn research tasks (byte-level Ed25519 signing via SDK; timestamp-unit cross-check) that are not PODs.

---

## D-025 — POD-H010-Q5′ resolved: hybrid probe-first for slug source

**Date:** 2026-04-19
**Session:** H-012
**Type:** Architecture / Scope / Research-first

**Source:** Operator direction at H-012: "Resolve POD-H010-Q5′: (c′) hybrid probe-first". Resolves POD-H010-Q5′ per `docs/clob_asset_cap_stress_test_research.md` v3 §7 Q5′ option (c′). Jointly ruled with POD-H010-§12 (see D-024).

**Decision:** Option (c′) per research-doc §7 Q5′. The stress test begins with a one-slug probe that uses a gateway-sourced slug (a slug already present in Phase 2's `meta.json` archive on `/data/events/`) to subscribe against `wss://api.polymarket.us/v1/ws/markets` via the SDK. Probe outcome determines the slug source for the main stress-test sweeps:
- If the probe succeeds (subscription accepted, market-data messages received): the gateway-to-api slug bridge is confirmed working; the main sweeps may use either gateway-sourced or api-sourced slugs. The default in that case is api-sourced (cleanest, and the SDK's `markets.list()` provides them).
- If the probe fails (subscription rejected, error response, connection closed with an error): the bridge is confirmed broken; the main sweeps use api-sourced slugs (SDK's `markets.list()`) exclusively. The probe result is itself data — recorded in the stress-test addendum to the research document.

**Considered (from research-doc §7 Q5′):**
- (a′) Stress-test-from-api — SDK or raw HTTPS against `api.polymarket.us/v1/markets`, subscribe via `/v1/ws/markets`. Clean test; gateway bridge not tested.
- (b′) Stress-test-from-gateway — use slugs Phase 2 wrote to `meta.json`, subscribe via `/v1/ws/markets`. Tests bridge at scale; if bridge is broken, main stress test loses its slug source.
- (c′) Hybrid probe-first — one-slug gateway probe to resolve the bridge question definitively, then choose (a′) or (b′) for the main sweeps based on the probe result.

Selected: (c′).

**Reasoning (Claude's recommendation, operator-approved under "most conservative" framing clarified in-session):** Most research-first-consistent path of the three. The ~30 seconds of probe code resolves an open unknown (gateway-to-api slug compatibility, identified in research-doc §4.7 as partially resolved by the SDK README read but not confirmed for gateway-sourced slugs specifically) before the main stress-test measurements begin. Under (a′), the bridge question is simply deferred — a legitimate choice but carries the unknown forward into Phase 3's full deliverable. Under (b′), the bridge question is on the critical path of the main sweeps — if it fails, the stress-test main run is lost along with the bridge finding, and the stress test's main deliverable is compromised. (c′) preserves the stress test's integrity and resolves the bridge question as a side effect.

The operator's initial "most conservative" phrasing admitted of two readings — (a′) under a minimize-test-risk reading and (c′) under a research-first-maximalism reading — and was clarified in-session as (c′). The clarification is logged because the dual-reading ambiguity is itself a small lesson about operator-language precision that future-Claude may benefit from seeing: "conservative" is not a self-defining term when competing risk vectors are in play.

**Commitment:**

1. The stress-test code includes, as its first runtime action after authentication, a one-slug probe:
   - Select one gateway-sourced slug from a Phase 2 `meta.json` file on the `/data/events/` Render persistent disk.
   - Subscribe it via the SDK's `markets_ws.subscribe()` with `SUBSCRIPTION_TYPE_MARKET_DATA` and the single slug in `marketSlugs`.
   - Observe the response for a short window (proposed ~10 seconds; exact bound set at code-turn time).
   - Record probe outcome explicitly: accepted, rejected with error payload, connection closed with code, or silent/no response.
   - Disconnect and proceed to the main sweeps.
2. The main sweeps' slug source is determined by probe outcome per the decision above.
3. The probe outcome is written to a stress-test-results artifact and added as an addendum to `docs/clob_asset_cap_stress_test_research.md` (v3.1 or v4, per H-010 next-action §4) alongside the §6 survey results.
4. If the probe outcome is ambiguous (e.g., slow response that eventually succeeds, or partial message stream), the ambiguity is itself surfaced in the addendum rather than quietly resolved by the stress-test code. This is a preventive application of the research-first discipline: probe results that Claude does not understand unambiguously are not silently collapsed into a binary pass/fail.

**Joint ruling note:** This decision is coherent with D-024 (SDK-based). The SDK's `markets_ws.subscribe(request_id, subscription_type, market_slugs_list)` is the probe vehicle; the SDK's `markets.list()` provides api-sourced slugs for the main sweeps under either probe outcome.

**Subsidiary finding surfaced during resolution:**

The research-doc §7 Q5′ language describes (c′) as "Claude's preferred path — most research-first-consistent." That language was written by Claude-H-010 in H-010 and was approved by operator in-session at H-012 with the clarification described above. Future-Claude reading this entry should understand that the (c′) rationale is not a retrospective justification; it was the Claude-H-010 recommendation before the ruling, preserved in the research document as v3 since H-010 close.

**SUPERSEDED IN PART BY D-027 (2026-04-19, H-013).** Commitment 1's specification of reading the probe slug from Phase 2's meta.json archive on the shared Render persistent disk is superseded by D-027 Option D (operator-supplied slug via `--slug=SLUG` CLI argument) after H-013 research confirmed Render disks are strictly single-service per `render.com/docs/disks`. The research-question intent of D-025 — probing a gateway-sourced slug against the api WebSocket — is preserved in D-027; only the slug-to-probe transport changes. Commitments 2, 3, and 4 are unaffected.

---

## D-024 — POD-H010-§12 resolved: SDK for the stress test

**Date:** 2026-04-19
**Session:** H-012
**Type:** Architecture / Scope

**Source:** Operator direction at H-012: "Resolve POD-H010-§12: (a) SDK". Resolves POD-H010-§12 per `docs/clob_asset_cap_stress_test_research.md` v3 §12 option (a). Jointly ruled with POD-H010-Q5′ (see D-025).

**Decision:** Option (a) per research-doc §12. The Phase 3 attempt 2 asset-cap stress test is built on the official Polymarket US Python SDK (`polymarket-us`, repository `github.com/Polymarket/polymarket-us-python`). Stress-test code uses SDK methods — at minimum `client.ws.markets()`, `await markets_ws.connect()`, and `await markets_ws.subscribe(request_id, subscription_type, market_slugs_list)` — rather than a hand-rolled WebSocket client against `wss://api.polymarket.us/v1/ws/markets`.

**Considered (from research-doc §12):**
- (a) Use `polymarket-us` SDK — minimal Tripwire 1 exposure, ships fastest, one new dependency
- (b) Hand-rolled WebSocket client — full visibility, zero new deps, high Tripwire 1 surface (every wire field is a citation requirement)
- (c) Hybrid — SDK for connection/auth, hand-rolled pool management on top

Selected: (a).

**Reasoning (Claude's recommendation, operator-approved):** The stress test's goal is to characterize Polymarket US's undocumented connection and subscription limits (research-doc §4.5, §5, §11 point 1), not to exercise the pool-management code that Phase 3's full deliverable will eventually implement. The SDK gets to "can we hold N subscriptions across M connections?" fastest, with wire-format correctness as the SDK's responsibility rather than a per-field citation burden on hand-rolled code. The SDK's youth (5 stars / 10 commits at H-010 v3 fetch time) is a known risk but is outweighed for a time-boxed stress test whose runtime is ≤30 minutes per configuration (research-doc §5).

The decision for the stress test explicitly does **not** commit the Phase 3 full deliverable (CLOB pool with 15-minute proactive recycle and 90-second liveness probe per plan §5.4) to SDK-based construction. That architectural choice is re-evaluated after the stress test results are in hand. The plan §5.4 pool-management semantics (recycle cadence, liveness probe) may or may not align with what the SDK provides; that is a later decision.

**Commitment:**

1. The stress-test code adds `polymarket-us` to a requirements file in a new, separate Render service per D-020 / Q2=(b) (isolated stress-test service, torn down after). The `pm-tennis-api` service's `requirements.txt` is not modified.
2. Every SDK symbol referenced in stress-test code traces to the Polymarket US Python SDK README (the source read during H-010 v3 research). Unverified SDK internals are not assumed; if a needed detail is not in the README, the SDK source is fetched at code-turn time (research-doc §4.3.1 closing note) and cited in the addendum to the research document.
3. Authentication credentials are read via `os.environ["POLYMARKET_US_API_KEY_ID"]` and `os.environ["POLYMARKET_US_API_SECRET_KEY"]` per D-023. The SDK's own authentication flow consumes these.
4. The two code-turn research tasks flagged in D-023 still stand, now scoped through the SDK: (a) byte-level Ed25519 signing — if the SDK owns signing internally, this collapses to "trust the SDK" rather than byte-level verification; if any signing surface is exposed to user code, that surface is cited; (b) timestamp-unit cross-check against `docs.polymarket.us/api-reference/authentication` — runs regardless of SDK use, because the SDK may or may not expose the timestamp it sent.

**Joint ruling note:** This decision interacts with D-025 (POD-H010-Q5′). The SDK's `client.markets.list()` on `api.polymarket.us` provides a natural api-sourced slug path, compatible with the Q5′=(c′) hybrid probe-first ruling in D-025.

---

## D-023 — POD-H010-Q4 resolved: Polymarket US API credentials exist and are stored at Render env vars

**Date:** 2026-04-19
**Session:** H-011
**Type:** Configuration / Secret-handling

**Source:** Operator confirmation in H-011 that credentials were generated at `polymarket.us/developer` and stored on the `pm-tennis-api` Render service. Polymarket-supplied usage instructions pasted into chat (instructions only, not key values), and verified against the H-010 research document §4.2.

**Decision:** Option (a) per POD-H010-Q4 enumeration in `docs/clob_asset_cap_stress_test_research.md` v3 §7 Q4. Polymarket US API credentials exist. They are stored as Render environment variables on the `pm-tennis-api` service under the names:

- `POLYMARKET_US_API_KEY_ID` — the Polymarket-issued Key ID
- `POLYMARKET_US_API_SECRET_KEY` — the Polymarket-issued Secret Key

Stress-test code and all subsequent Polymarket-US-authenticated code paths read these values via `os.environ` by name. Neither the names-plus-values pair nor the values themselves ever enter the repo, in accordance with SECRETS_POLICY §A.2, §A.5, and §B.2.

**Considered (from research-doc §7 Q4):**
- (a) Credentials exist — operator supplies via Render env vars, code reads by name
- (b) Credentials do not exist — operator generates at `polymarket.us/developer`
- (c) Credentials exist but operator wants a separate scoped stress-test key

Selected: (a). Operator generated the credentials during H-011 (outside-session action at `polymarket.us/developer`), stored them in Render env vars directly in the Render dashboard, and reported the variable names back in chat. No value ever appeared in the chat transcript.

**Reasoning:** The three-header auth scheme (`X-PM-Access-Key`, `X-PM-Timestamp`, `X-PM-Signature`) that Polymarket's usage instructions describe matches what the H-010 research doc §4.2 established from `docs.polymarket.us/api-reference/websocket/overview` and `docs.polymarket.us/api-reference/authentication`. Scoped keys per option (c) were not requested; Polymarket's standard key issuance is used. The SECRETS_POLICY-prescribed storage mechanism (platform environment variables, read by name in code, never committed) is used.

**Commitment:** Any code that authenticates against Polymarket US's private endpoints reads the credential values from `POLYMARKET_US_API_KEY_ID` and `POLYMARKET_US_API_SECRET_KEY` via `os.environ` at runtime. The variable names are load-bearing; renaming them requires a DecisionJournal entry and a coordinated update of both the Render dashboard and any code that references them. Values are rotated at Polymarket US and updated in the Render dashboard if SECRETS_POLICY §B.5 procedures are ever invoked.

**Subsidiary findings surfaced during Q4 resolution:**

1. **Timestamp unit disambiguated.** Polymarket's usage instructions specify `X-PM-Timestamp: {unix_ms}` — milliseconds. The H-010 research doc §4.2 cited the authentication page's "30 seconds of server time" language but did not definitively pin the timestamp unit. The millisecond unit is the canonical value for code purposes; the authentication page will be re-fetched at code-turn time to cross-check. If the documentation page still reads ambiguously or specifies seconds, the inconsistency is surfaced at that point, not now.

2. **Byte-level Ed25519 signing operation still not fully verified.** The H-010 research doc §4.2 noted that the precise byte sequence being signed (exact input bytes, exact encoding) "is a detail the code turn must verify via the authentication page or the official Python SDK." Polymarket's usage instructions do not fully resolve this either — they state "sign the timestamp" but do not specify byte-level canonical form. This remains a code-turn research task; it is not a pending operator decision and does not block H-012 session-open.

3. **Render environment variable visibility.** Render masks env var values by default in the dashboard; there is no separate "mark as secret" toggle. This deviated from Claude's initial recommendation language (which had implied such a toggle might exist) and was corrected in H-011.

**Effect on other pending operator decisions:**
- **POD-H010-Q5'** (slug source) and **POD-H010-§12** (SDK vs hand-roll): unblocked from the credential-availability angle. Remain open for operator ruling at H-012.
- **POD-H010-§6-survey**: not affected by Q4; remains open for operator authorization at H-012.

---

## D-022 — Ruling 5: commit cadence for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Governance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (menu paste in H-010 session opening, Ruling 5).

**Decision:** Periodic commits within a deliverable are permitted; a handoff is required at session end. This matches the commit cadence used during Phase 2.

**Considered:**
- (a) One commit per deliverable; handoff required before each commit
- (b) One commit per deliverable; handoff required only at session end
- (c) Periodic commits within a deliverable are fine; handoff required at session end
- (d) Something else

**Reasoning (operator):** "Same cadence used for Phase 2 (which succeeded). The H-008 problem was the missing handoff, not the number of commits."

**Commitment:** Intra-deliverable commit pacing is a judgment call for the work being done. The hard requirement is Playbook §2 session-close and R-011 proactive-handoff discipline. The attempt-1 failure is addressed by the handoff rule, not by restricting commit frequency.

---

## D-021 — Ruling 4: testing posture for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Quality

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 4).

**Decision:** Each deliverable is tested with unit tests plus a lightweight live smoke test before it is considered complete.

**Considered:**
- (a) Unit tests only; live validation deferred to the Ruling 3 checkpoint
- (b) Unit tests plus a lightweight live smoke test on one match or one asset before the deliverable is considered complete
- (c) Live-first — thinnest working version against real data, validate by inspection, then add tests
- (d) Something else

**Reasoning (operator):** "Addresses the specific attempt-1 failure mode (tests passed, live operation failed) without reversing the testing pyramid."

**Commitment:** No Phase 3 attempt 2 deliverable is declared complete on unit-test evidence alone. A live smoke test is part of the completion bar. The live smoke test is narrower than the Ruling 3 checkpoint (one match / one asset / one connection is sufficient); the Ruling 3 checkpoint is the broader acceptance event.

---

## D-020 — Ruling 3: definition of done for the first deliverable

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Acceptance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 3, including the adjustment note for the asset-cap stress test).

**Decision:** The first deliverable of Phase 3 attempt 2 is accepted when (1) unit tests pass, (2) the operator has reviewed the code, and (3) a single live verification has run against the actual Polymarket US gateway. Because the first deliverable is the asset-cap stress test (D-018), the single-live-verification language is adjusted per the operator's menu note: **the stress test runs to completion against the actual gateway with the actual asset count we expect.** "Actual asset count we expect" is the asset count implied by current discovery volume under the subscription-unit interpretation established by the Phase 3 attempt 2 research document; it is not a pre-guessed number.

**Considered:**
- (a) Unit tests + operator code review + single live poll/connection against one real market
- (b) (a) plus a 1-hour unattended test
- (c) (a) plus a manual walkthrough of the admin UI surfaces
- (d) Something else

**Reasoning (operator):** "Unit-tests-only missed the H-008 failure; live verification on one real market catches it without requiring hours of unattended runtime."

**Commitment:** The Ruling 3 checkpoint is a per-deliverable acceptance event distinct from the Phase 3 exit gate. The Phase 3 exit gate (48-hour unattended run, pool stale-connection handling, Sports WS retirement handler, handicap median, asset-cap stress test, first-server identification) remains the eventual target; Ruling 3 is the interim bar each deliverable clears. The first-deliverable live verification is the stress test itself running to completion; there is no separate "single live connection" step layered on top.

---

## D-019 — Ruling 2: research-first form for Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Process / Governance

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 2). Implements D-016 commitment 2 (research-first discipline for external APIs and cross-module symbols).

**Decision:** Research that concerns external endpoints or cross-module symbols is produced as a **standalone research document** first. Operator reviews the document. Code begins in a subsequent Claude turn only after the review.

**Considered:**
- (a) Standalone research document first, operator reviews, then code begins in a subsequent Claude turn
- (b) Research produced inline, operator spot-checks each citation, code begins immediately after each research block is accepted
- (c) Operator supplies the documentation links; Claude works strictly from supplied material and refuses to use anything else

**Reasoning (operator):** "Maximum distance from the H-008 fabrication pattern."

**Commitment:** The research-document-then-code sequencing applies for the duration of Phase 3 attempt 2 unless explicitly lifted. Each research document goes through operator review before the turn that begins the corresponding code. Hybrid — operator supplies links during a research turn — is compatible with (a) and does not constitute a switch to (c). A switch to (b) or (c) for a specific deliverable requires a new ruling and a new DecisionJournal entry.

---

## D-018 — Ruling 1: first deliverable of Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-010
**Type:** Scope / Sequencing

**Source:** Operator direction for H-010 — Phase 3 attempt 2 scope (Ruling 1).

**Decision:** The first deliverable of Phase 3 attempt 2 is the deferred CLOB asset-cap stress test from Phase 1 (RAID I-002). Other Phase 3 components (CLOB pool, Sports WS client, correlation layer, handicap updater) follow after the stress test resolves pool sizing.

**Considered:**
- (a) CLOB WebSocket pool
- (b) Sports WebSocket client
- (c) Correlation layer
- (d) Handicap updater
- (e) Deferred CLOB asset-cap stress test (I-002)
- (f) Something else

**Reasoning (operator):** "Resolving the sizing question first determines how the CLOB pool gets built and avoids redoing pool design later."

**Commitment:** The asset-cap stress test runs before the CLOB pool is built. The "soft 150-asset cap" referenced in plan §5.4 and §11.3 is verified empirically against the Polymarket US CLOB service before any long-lived pool code is written. The stress-test design is scoped by the Phase 3 attempt 2 research document (v1 produced this session; v2 pending §4 external research).

---

## D-017 — v3→v4 plan revision (retroactive journaling)

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Plan revision / Retroactive entry

**Source:** Reconstructed H-009 from Handoff_H-006.md §2. The decision was labeled "D-008" in H-006's handoff before the numbering conflict with the pre-existing D-008 (Section 1.5 forward references, H-002) was identified at the same session by D-012. D-012 resolved the numbering policy but did not retroactively assign a canonical ID to the plan-revision decision itself. D-017 closes that gap per Playbook §12.3 step 6, which requires a DecisionJournal entry for every plan revision.

**Decision:** Produce v4 of the PM-Tennis Build Plan; premise shift from mispricing-test to instrument-vs-intuition test.

**Motivating evidence:** Baseline analysis of 71 Polymarket US iPhone screenshots (502 cash events, 131 resolved tennis contracts excluding STENAP/TRISCH) showing operator ROI of +8.5% overall and +14.3% on swing trades, with effective swing win rate of 55.9% (vs 58.2% breakeven, p=0.697, statistically indistinguishable from breakeven). Analysis performed in an adjacent chat session on 2026-04-18.

**Chain of authorship:** Analysis adjacent → premise shift directed by operator → source artifacts (Premise Brief, Baseline Summary v2, Hypothesis Set v2, Injection Instruction v2) produced adjacent → v4 produced in H-006 under Playbook §12.

**Rationale for v4 rather than v3.x:** A premise-level shift requires one clean reading. Mixing v3's mispricing framing with v4 amendments would burden all downstream phases.

**Commitment:** v4 is the active build plan. v3 is preserved in git history. `STATE.project.plan_document.current_version = v4`.

**Downstream consequences (from H-006):**
- D-009 (H3 hypothesis dropped) — scope implication of the revised research question.
- D-010 (conviction scoring + exit context ship together at Phase 5) — new instrument features introduced by v4.
- D-011 (pilot-then-freeze deferred to Phase 7) — reserved decision slot carried forward from v3.
- D-012 (decision numbering corrected) — resolves the conflict that motivated this retroactive entry.

**Retroactive-journaling note:** This entry is dated 2026-04-19 (journaling date) but records a decision made 2026-04-18 (decision date). The dual dating is intentional per Playbook §1.5.2's reconstruction discipline.

---

## D-016 — Phase 3 attempt 1 failed; revert main to pre-attempt state and begin Phase 3 attempt 2

**Date:** 2026-04-19
**Session:** H-009
**Type:** Recovery / Governance

### What happened

Between H-007 session close and the beginning of H-009, a session occurred (labeled H-008 for handoff-sequence integrity, though no handoff was ever produced) in which Phase 3 capture components were authored, tested, committed to the repo on main, and deployed. The commits are visible in git history, timestamped 2026-04-19 02:11:12Z through 02:18:56Z:

- `677016c1` — src/capture/clob_pool.py (10.9 KB)
- `a10486b3` — src/capture/correlation.py (12.2 KB)
- `00282260` — src/capture/sports_ws.py (18.1 KB)
- `bab716ef` — src/capture/handicap.py (8.6 KB)
- `d319e09e` — main.py rewritten (12.0 KB) to wire all components
- `8bdc3859` — tests/test_capture_phase3.py (23.4 KB)
- `40973377` — pytest.ini (asyncio_mode=auto)

After deployment, the code began failing in live operation. Per operator's explanation at session H-009: *"Claude failed to read the documentation thoroughly and made up a placeholder URL for live Sports WS. Trying to correct it in that session just made it worse."* The session ended without producing a handoff document or an updated STATE.md. The operator subsequently deleted the session transcript.

### The fabrication pattern

During H-009 revert validation (V4 log scan), Render runtime logs surfaced a second fabrication from the failed session: `main.py` at `d319e09e` contained the import `from src.capture.discovery import DiscoveryLoop, DiscoveryConfig`. The `DiscoveryConfig` class does not exist in `discovery.py` (which was unchanged from H-007). Claude assumed a symbol existed in an unmodified file. The service crash-looped with `ImportError: cannot import name 'DiscoveryConfig' from 'src.capture.discovery'` from 03:10:11Z through 03:13:20Z (six documented ImportError events during the delete phase of the revert transaction).

Two fabrications in one failed session, of different kinds:
1. An external endpoint URL (Sports WS) fabricated rather than researched against documentation.
2. An internal module symbol (`DiscoveryConfig`) assumed to exist in an existing-but-unmodified file.

The common failure mode is: writing code that references names Claude never verified exist.

### What is recoverable and what is not

Recoverable: the code itself (present in git history), the commit timestamps and messages, the order of commits, the general shape of what was attempted, the ImportError evidence from Render logs.

Not recoverable: the exact fabricated Sports WS URL, what it was "corrected" to during the attempted fixes, the specific failure signatures beyond the ImportError, the reasoning at each decision point during the session, and any intermediate diagnostic output.

### Root causes (as stated and as observed)

Stated by operator: Claude fabricated an endpoint URL for the live Sports WebSocket rather than researching the actual endpoint from Sportradar or Polymarket US documentation. Attempting to correct the URL in-session without returning to documentation compounded the failure.

Observed during H-009 revert validation: also an internal-symbol fabrication (`DiscoveryConfig`). This is the same failure class as the URL fabrication — writing code that presumes a name exists without verifying it does.

Both are direct violations of build plan §1.5.4 ("Claude shall not silently adapt to unexpected findings") and of the research-first discipline that should govern any external-API integration work or cross-module coupling.

### Ruling by operator at H-009

1. **Option A1 adopted.** Revert main to its state at commit `c63f7c1d` (the last commit before the Phase 3 attempt, dated 2026-04-19 01:46:44Z, message "fix: discovery task catches all exceptions and retries"). Remove the five new Phase 3 files (clob_pool.py, sports_ws.py, correlation.py, handicap.py, test_capture_phase3.py) and pytest.ini; restore main.py to its c63f7c1d content. Approach executed through GitHub web UI, walked through with Claude step by step.

2. **Tripwire classification:**
   - **Tripwire 1** (integrity discrepancy between STATE/handoff and repo): real, caused by missed session-close ritual at H-008. No governance breach in the commits themselves; STATE v6 and handoff H-007 are stale because H-008 never produced its handoff.
   - **Tripwire 2** (out-of-session commits per Playbook §10): false positive, withdrawn. Commits were legitimate in-session outputs of H-008.
   - **Tripwire 3** (DecisionJournal gap D-009 through D-015): real, predates H-008, independent of the failure. Addressed in H-009 via reconstruction from handoff sources (D-009 through D-012 from H-006; D-013 through D-015 from H-007), each entry flagged as reconstructed per Playbook §1.5.2.

3. **Commit-message variance note.** The five delete commits in the revert transaction were committed with GitHub's default `"Delete <filename>"` messages (plus a free-form `"Claude fuck up"` tag added by the operator) rather than the structured `"revert: remove failed Phase 3 <file> (N/7)"` format Claude had drafted. The `main.py` restore commit (`17f44eb1`) used the structured format. The seven-commit revert transaction remains unambiguously identifiable in the git log by timestamp cluster (03:08:45Z–03:17:11Z) and by the "(7/7)" tag on the main.py restore. No action needed; noted for future-Claude reading the log.

### Revert validation outcomes (H-009)

Seven validation checks were performed after the revert commits landed:

- **V1** — 38 `meta.json` files present on persistent disk. ✓
- **V2** — `meta.json` well-formed, contains expected fields and `PENDING_PHASE3` stubs. ✓ (with two documentation notes: participant type observed is `PARTICIPANT_TYPE_TEAM` not `PARTICIPANT_TYPE_PLAYER` as H-007 claimed; `sportradar_game_id` empty across all 38 events, consistent with no-live-matches context.)
- **V3** — discovery delta stream being written, daily raw-poll archive being written. ✓ (with one informational note: raw-poll archive grows ~290 MB/day uncompressed, which has runway implications before Phase 4 compression arrives.)
- **V4** — No ERROR / WARN / Traceback in Render logs after the 03:18:49Z revert deploy. ✓
- **V5** — Build log confirms `pip install -r requirements.txt` installed full dependency set (fastapi, uvicorn, pandas, numpy, pyarrow, requests, scipy, httpx). ✓
- **V6** — Environment variables minimal and expected (ENVIRONMENT, LOG_LEVEL, PM_TENNIS_TOKEN). No failed-attempt leftovers. ✓
- **V7** — `/data` mounted as real persistent volume (`/dev/nvme2n1`, 9.8 GB, ~35 MB used). ✓

### Commitments created by this decision

1. **Phase 3 attempt 2 begins from c63f7c1d-equivalent repo state.** No code from the failed attempt carries forward into attempt 2. Phase 3 design choices do not inherit from attempt 1.

2. **Research-first discipline for all external APIs and cross-module references.** Before any code is written for Phase 3 attempt 2 that (a) calls an external endpoint, or (b) imports a symbol from a module that is not being concurrently modified, Claude produces a short research summary citing the actual documentation source (for endpoints) or the actual module definition (for symbols). Fabrication of URLs, endpoint shapes, message formats, authentication schemes, module names, class names, or function signatures is a tripwire. This applies at minimum to the Sports WebSocket endpoint (the specific URL failure point), the CLOB WebSocket subscription format, correlation metadata shape, and any symbol imported from `src.capture.discovery` or other pre-existing modules.

3. **Session-close ritual discipline.** The missed handoff at H-008 is the proximate cause of the governance debris H-009 cleaned up. Future sessions that end before Claude can produce a handoff voluntarily apply Playbook §2.5.2: Claude proactively offers to produce the handoff when the session seems near close, rather than waiting for explicit close request. If a session ends abruptly mid-task, the next session treats the prior session's missed handoff as a Failure-mode-1.5.2 lost-handoff event and reconstructs per §9.3.

4. **H-009 produces no new Phase 3 code.** Its entire output is the revert transaction, the DecisionJournal reconstruction (D-009 through D-015) plus this entry (D-016) plus the retroactive plan-revision entry (D-017), STATE v7, RAID updates, and handoff H-009. Phase 3 attempt 2 begins in H-010 or later.

### What this session does not decide

This entry does not prescribe the technical approach for Phase 3 attempt 2. Sub-deliverable sequencing, module structure, testing strategy, first deliverable — all remain open for operator direction at the start of the next Phase 3 session.

---

## D-015 — Tennis sport slug confirmed as "tennis"

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Technical verification / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The Polymarket US gateway uses sport slug `"tennis"` with leagues `["wta", "atp"]`. The default value in `TENNIS_SPORT_SLUG` is correct and requires no override.

**Confirmed by:** Live gateway response at startup during H-007, logged at INFO level. Re-confirmed during the 03:18:49Z revert deploy startup in H-009: `✓ MATCH — sport slug='tennis' name='Tennis' leagues=['wta', 'atp']`.

**Commitment:** Discovery module's tennis-slug default stands. No override file needed.

---

## D-014 — Discovery loop runs inside pm-tennis-api, not as a separate service

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Architecture / Deviation from plan / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The discovery background task runs as an asyncio task inside the FastAPI process on pm-tennis-api, not as a separate Render background worker service.

**Rationale:** Render persistent disks are per-service and cannot be shared between services. Running discovery inside the API service ensures both read and write access to the same `/data` disk. A separate background worker service was created and deleted during H-007 after this constraint was discovered empirically.

**Consequence:** pm-tennis-api serves two roles: HTTP API (Phase 4 will expand this) and continuous discovery worker. Represents an architectural deviation from the build plan's implied service separation, justified by the disk-sharing constraint.

**Commitment:** Capture worker and API share a process. Phase 3 attempt 2 and later phases inherit this architecture.

---

## D-013 — Polymarket US gateway is the correct API target

**Date of decision:** 2026-04-19
**Session of decision:** H-007
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Technical / Scope / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-007.md §2.

**Decision:** The discovery module polls `gateway.polymarket.us` (Polymarket US public API), not `gamma-api.polymarket.com` (offshore Polymarket). These are separate products with separate API structures.

**Rationale:** Build plan Section 1.2 is explicit that the offshore Polymarket product is out of scope. The Polymarket US public gateway requires no authentication for read operations.

**Endpoints confirmed:**
- `GET /v2/sports` — enumerate sports, verify tennis slug
- `GET /v2/sports/{slug}/events` — paginated event discovery

**Commitment:** All Polymarket endpoints used by this project come from `gateway.polymarket.us` (read) and, when trading actions are eventually needed, from `api.polymarket.us`. Offshore URLs are out of scope permanently.

---

## D-012 — Decision numbering corrected

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Governance / Bookkeeping / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The Injection Instruction's references to "D-002 pilot-then-freeze" and "D-003 Sports WS gate" were build-plan internal labels, not canonical RAID/STATE decision IDs. Canonical numbering (D-001 through D-007 per STATE.md) is authoritative. The v3→v4 revision and related decisions are assigned D-008 through D-011 in H-006 (with D-017 later retroactively journaling the plan-revision decision itself).

**Reasoning:** Prevents ambiguity between in-document cross-references and canonical DecisionJournal IDs.

**Commitment:** All future DecisionJournal IDs derive from this journal, not from plan-internal references.

---

## D-011 — Pilot-then-freeze protocol deferred to Phase 7

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Pre-commitment / Scheduling / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The pilot-then-freeze protocol for `signal_thresholds.json` is a Phase 7 decision. v4 notes it as a placeholder. Full specification and formal ID assignment at Phase 7.

**Reasoning:** Operator comfortable with deferral; no content yet to commit. The pilot protocol is itself a pre-commitment artifact and must be written before any pilot data is inspected.

**Commitment:** Phase 7's exit gate adds a requirement for a pilot protocol document. This entry reserves the decision slot.

---

## D-010 — Conviction scoring and exit context ship together at Phase 5

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Scope / Scheduling / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** Build plan Sections 4.6 (Conviction Scoring) and 4.7 (Exit Context) are parallel instrument features, both shipping at Phase 5. No staged rollout.

**Reasoning:** Both derived from the same fair-price computation; they serve the same operator-decision moment.

**Commitment:** Phase 5 deliverables include both features simultaneously. Neither may ship without the other.

---

## D-009 — H3 hypothesis dropped

**Date of decision:** 2026-04-18
**Session of decision:** H-006
**Date of journaling:** 2026-04-19
**Session of journaling:** H-009
**Type:** Scope / Research question / Reconstructed

**Source:** Reconstructed H-009 from Handoff_H-006.md §2.

**Decision:** The hold-strategy rehabilitation hypothesis (H3) is permanently dropped from v4 and all future plan documents.

**Reasoning:** Operator direction. Not to be raised again.

**Commitment:** v4 tests H1 and H2 only. H3 is not a candidate for reinstatement.

---

## D-008 — Section 1.5 forward references are aspirational; scaffolding realizes them

**Date:** 2026-04-18
**Session:** H-002
**Type:** Governance confirmation

**Decision:** Section 1.5 of the build plan references project assets (DecisionJournal, RAID log, STATE.md, PreCommitmentRegister, OBSERVATION_ACTIVE lock, runbooks) that did not exist at the time Section 1.5 was written. The operator confirmed this is acceptable as an aspirational governance posture. The scaffolding work in H-002 and H-003 makes those references concrete.

**Considered:** (a) Treat Section 1.5's references as binding from day one and block progress until all referenced artifacts exist; (b) treat them as aspirational and build the artifacts to match them as scaffolding progresses. Option (a) is circular — the artifacts cannot exist until they are built, and the governance model cannot govern their construction if it does not exist. Option (b) is the only workable path.

**Reasoning:** Section 1.5 was written to lock in the governance model before the assets existed. Writing the governance posture first and building the artifacts to match it is the correct sequencing — the alternative (build assets first, write governance after) risks the assets diverging from the intended model. The posture is acknowledged explicitly so that neither party is confused when Section 1.5 names an asset that is still being built.

**Commitment:** The scaffolding files produced in H-002 and H-003 must faithfully implement Section 1.5's described behavior. If a scaffolding file diverges from Section 1.5, the divergence is surfaced and either the file or Section 1.5 is corrected — silent divergence is not acceptable.

---

## D-007 — Session-open self-audit block is included

**Date:** 2026-04-18
**Session:** H-002
**Type:** Protocol

**Decision:** On handoff acceptance at the start of every session, Claude produces a visible self-audit block documenting: the handoff ID received, what repo files (or uploaded files) were checked against the handoff's claimed modifications, commitment-file checksums compared against the handoff's record (once those files exist), any inconsistencies found, and an explicit orientation statement (current phase, current work package, next action).

**Considered:** (a) Self-audit block on every session-open, produced by Claude and visible in the chat; (b) operator-only audits via unprompted spot-checks with no claim-side audit from Claude. Option (b) relies entirely on operator vigilance and is unverifiable without something to check against. Option (a) adds a visible surface on every session that can itself be checked against the handoff and the repo state — it is auditable.

**Reasoning:** The operator noted in H-001 that drift is a real risk and that Claude's prior pattern of skipping process is a known failure mode. Making the audit visible at session start raises the cost of drift to Claude (a missing or sparse self-audit is itself a red flag the operator can catch on review) and gives the operator a consistent artifact to spot-check. Spot-checks still happen on top of this; the self-audit is not a substitute.

**Commitment:** Every session handoff acceptance includes a self-audit block. The block must list at minimum: handoff ID received, files checked, any inconsistencies found, and the orientation statement. A missing or perfunctory self-audit is a protocol violation that must be flagged in that session's handoff self-report.

---

## D-006 — Handoff carrier is markdown files

**Date:** 2026-04-18
**Session:** H-002
**Type:** Process

**Decision:** Handoff documents are transported between sessions as markdown files. Claude produces a `Handoff_H-NNN.md` at session end. The operator saves or downloads it and pastes or uploads it at the start of the next session.

**Considered:** (a) Markdown files produced by Claude; (b) copy-paste into a personal note system; (c) auto-sync via a third-party tool. Option (c) adds an external dependency and a new failure surface. Option (b) is workable but degrades when the operator changes note systems or copy-pastes incorrectly. Option (a) keeps the handoff as a self-contained file that can be committed to the repo once the repo exists, reviewed as a document, and re-uploaded cleanly.

**Reasoning:** Markdown is the existing project documentation format. A single consistent format removes the conversion step and keeps handoffs compatible with the repo and the rest of the project artifacts. Handoff files in the repo also serve as a complete session audit trail.

**Commitment:** Claude produces `Handoff_H-NNN.md` at session end. Operator preserves it and provides it at the next session start. A lost handoff is an operator responsibility and cannot be reconstructed by Claude — though prior session transcripts may allow the operator to reconstruct one manually.

---

## D-005 — Repo access model is a public GitHub repository

**Date:** 2026-04-18
**Session:** H-002
**Type:** Infrastructure / Security

**Decision:** The project's Git repository is a public GitHub repository. Claude accesses repo contents via the public GitHub URL when the operator provides it, or via operator-uploaded file batches when files are being actively worked on. No read-only tokens or per-session credential sharing is required.

**Considered:** (a) Public repo; (b) private repo with a read-only personal access token shared per session; (c) operator re-uploads key files at the start of each session. Option (c) is high-friction and error-prone — the operator must remember which files are current. Option (b) adds credential management per session and is the kind of friction that causes protocol drift. Option (a) is the lowest-friction model but imposes a hard constraint on what may be committed.

**Reasoning:** A public repo forces secrets discipline that is desirable regardless — no credentials, API keys, Polymarket account identifiers, or personal data may ever land in the repo. Environment variables in the hosting platforms' web UIs (Render, Netlify) hold all secrets; the code that reads them by name is public but does not contain the values. The project's subject matter (a personal trading instrument built around a public exchange's public feeds) is not itself sensitive. The strategy specifics are, but the plan already commits to transparency of the commitment files.

**Commitment:** No secrets in the repo, ever. `SECRETS_POLICY.md` (produced H-002) specifies what counts as a secret, where secrets live, and what the audit procedure is. Any commit that would introduce a secret is a tripwire event refused by Claude and flagged for operator review.

---

## D-004 — Out-of-protocol trigger phrase is "out-of-protocol"

**Date:** 2026-04-18
**Session:** H-002
**Type:** Governance

**Decision:** When the operator begins a request with the literal phrase "out-of-protocol", the usual full protocol is suspended for that specific task. The phrase must appear at the start of the request to be recognized as a governance signal.

**Considered:** Candidate phrases: "out-of-protocol", "quick fix", "OOP", or operator's choice of any phrase. "OOP" is brief but less mnemonic and could appear incidentally in technical context. "Quick fix" describes the situation type rather than the governance signal, making it ambiguous when the operator says it in passing conversation. "Out-of-protocol" names what it does, is unambiguous, and is unlikely to appear by accident in any other project context.

**Reasoning:** The phrase needs to be: (1) distinctive enough that it cannot appear by accident, (2) explicit about what it signals, and (3) consistent across sessions so Claude can reliably detect it without ambiguity. "Out-of-protocol" meets all three criteria. The cost of false negatives (operator forgets the phrase) is a mild friction. The cost of false positives (Claude incorrectly suspends protocol) is drift, which is the more dangerous failure mode, so the bar for detection is set high.

**Commitment:** Every out-of-protocol invocation is logged in two places: (1) the session handoff's Claude self-report section, and (2) a new entry in this DecisionJournal citing the OOP phrase, the request made, the work performed, and any rules that were suspended. The `OBSERVATION_ACTIVE` soft lock is unconditional and is **not** overridable by "out-of-protocol" — if an OOP request would modify a commitment file during an active observation window, Claude refuses and surfaces the Section 9.6 rule regardless of OOP invocation.

---

## D-003 — Sports WebSocket granularity is a go/no-go gate, not a silent downgrade

**Date:** 2026-04-18
**Session:** H-002
**Type:** Technical / Decision criterion

**Decision:** Phase 1's Sports WebSocket granularity verification is an explicit go/no-go gate surfaced to the operator. If point-level data is confirmed on the public Sports WebSocket, the project proceeds as planned. If only game-boundary transitions are emitted, Claude stops, produces an assessment of which signal classes survive the game-level coarsening, and the operator rules go / no-go / defer before Phase 2 begins. The operator's ruling is logged to the DecisionJournal before Phase 2 starts.

**Considered:** The plan as originally written (Section 11.1, severity 7) treated the game-level fallback as "weaker thesis but still viable" and allowed silent continuation. Claude's review pushed back: break-point and deuce transitions carry the highest log-odds evidence in the model, and these are exactly the transitions lost if granularity is game-level only. The thesis's most leveraged signal class is therefore the one most likely to be unavailable under the fallback.

**Reasoning:** A silent downgrade risks the observation window being run on an instrument that cannot observe the states the thesis most depends on. The operator cannot evaluate that tradeoff if Claude handles it silently. Making it an explicit gate preserves the operator's ability to decide whether a game-level instrument is worth building and running, or whether the project should pause or redirect.

**Commitment:** Phase 1's acceptance criteria must include this gate explicitly. The plan document's Section 8 Phase 1 and Section 11.1 are queued for update under the doc-code coupling rule (tracked in STATE's `pending_revisions` block). The update is applied when the plan text is next revised.

---

## D-002 — Signal-threshold derivation uses a pilot-then-freeze protocol

**Date:** 2026-04-18
**Session:** H-002
**Type:** Decision criterion / Pre-commitment

**Decision:** Between Phase 7 completion and the opening of the observation window, a pilot phase calibrates the values in `signal_thresholds.json` against archive data accumulated by the instrument. At pilot end, thresholds are frozen, `OBSERVATION_ACTIVE` is engaged, and the 250-signal / 60-day window clock starts. Pilot data is excluded from the window.

**Considered:** (a) Keep the plan's committed guesses (X=0.08 etc.) and acknowledge the weakness; (b) pilot-then-freeze; (c) skip pre-committed thresholds entirely and run the window as a threshold-sweep exploration. Option (a) weakens the Bayesian pre-commitment discipline — the window protects against in-window tuning but not against the plan being wrong at the start in a way that makes the window uninformative. Option (c) sacrifices falsification discipline entirely. Option (b) preserves both: the pilot calibrates, the freeze preserves pre-commitment, the pilot-data exclusion keeps the window independent.

**Reasoning:** The plan's Section 9 pre-commitment model depends on thresholds that are grounded in data, not arbitrary. Arbitrary starting thresholds create a real risk that an otherwise-valid thesis fails the window due to miscalibrated thresholds — or passes due to thresholds that happened to work on the pilot data. The pilot-then-freeze protocol separates calibration from evaluation, which is the same principle that separates training from test in predictive modeling.

**Open sub-questions (not decided in H-002; to be resolved before the pilot begins, i.e., before Phase 7 exit gate):**
1. **Pilot duration** — calendar time (e.g., 14 days), data volume (e.g., first 500 qualifying events), or both with a bound?
2. **Calibration method** — grid search over thresholds risks overfitting to pilot noise; alternatives include cross-validated search, a coarse pre-specified discrete grid with committed resolutions, or expert-judgement calibration against summary statistics only.
3. **Overfitting guardrails** — how to ensure pilot thresholds generalize to the window. Candidates: hold out part of the pilot data, pre-commit to a small set of candidate threshold tuples and select only among them.
4. **No-tradeable-configuration branch** — if the pilot reveals no threshold tuple that passes the breakeven bar under reasonable assumptions, the project pauses rather than proceeding with uncalibrated thresholds.

**Commitment:** Phase 7's exit gate adds a requirement: a pilot protocol document must exist and be accepted by the operator before the pilot begins. The pilot protocol is itself a pre-commitment artifact — it must be written and committed before any pilot data is inspected, to prevent it from being tuned to pilot data. Plan Sections 8 (Phase 7), 9, and 11 are queued for update (tracked in STATE).

---

## D-001 — Development environment, roles, and governance model

**Date:** 2026-04-18
**Session:** H-001
**Type:** Foundational / Governance

**Decision:** Project is built end-to-end by Claude across discrete chat sessions, under direction of a single non-technical operator who uses no terminals, SSH, or command-line tools. Deployment uses a managed PaaS (Render) for backend, Netlify for frontend, GitHub for the repository. Governance operates on four layers: session protocol (handoff/accept ritual), gate-blocking language in acceptance criteria, named tripwires, and operator spot-checks. The session model requires a handoff produced at session end and accepted at session start; thin handoffs trigger stop-and-surface, not best-effort reconstruction. Claude's obligations are defined by the "shall" and "shall not" rules in Section 1.5.4. The observation-active soft lock via the `OBSERVATION_ACTIVE` file protects commitment files during windows unconditionally.

**Considered:** The plan's original assumption was a conventional developer-operator setup with a Hetzner VPS and SSH access. That assumption was replaced once the actual operator profile (non-technical, no terminal access) was established. PaaS options considered: Render, Railway, Fly.io. Fly.io was excluded because its setup uses a CLI, which conflicts with the no-terminal constraint. Railway and Render are both compatible; Render was chosen for its Netlify-like UI experience and predictable pricing.

**Reasoning:** A plan built for a developer-operator who doesn't exist creates silent failures when a non-technical operator tries to execute it. Section 1.5 was written at length to make the actual environment explicit before any code is written. The governance structure (four-layer model, tripwires, handoff protocol) was specified up front because prior multi-session AI-assisted projects have shown that protocol discipline degrades without explicit structure — naming the rules and naming the failure modes is the first line of defense.

**Commitment:** All downstream sections of the plan are interpreted under Section 1.5. Acceptance criteria requiring terminal access are not acceptable; every phase is responsible for building the web-UI surfaces that expose its diagnostics. Section 1.5.6 lists the specific downstream sections requiring reconciliation and assigns Claude responsibility for applying the reconciliation during the relevant phases.

---

*End of DecisionJournal.md — updated at H-009 session close.*
*Next entry will be D-018 or a gate verdict, whichever comes first.*
