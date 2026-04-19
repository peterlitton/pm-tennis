# H-016 Commit Manifest

**Commit message:** `H-016: helper-snippet flip + RAID I-016 fix (D-028)`

**11 file changes total.** Listed by action.

---

## REPLACE existing files (8)

Drop these into the repo at the listed paths. They overwrite existing files.

| Source in zip | Destination in repo |
|---|---|
| `src/capture/discovery.py` | `src/capture/discovery.py` |
| `src/stress_test/__init__.py` | `src/stress_test/__init__.py` |
| `src/stress_test/README.md` | `src/stress_test/README.md` |
| `src/stress_test/slug_selector.py` | `src/stress_test/slug_selector.py` |
| `tests/test_discovery.py` | `tests/test_discovery.py` |
| `tests/test_stress_test_slug_selector.py` | `tests/test_stress_test_slug_selector.py` |
| `runbooks/Runbook_RB-002_Stress_Test_Service.md` | `runbooks/Runbook_RB-002_Stress_Test_Service.md` |
| `RAID.md` | `RAID.md` (repo root) |

---

## ADD new files (2)

These do not exist in the repo yet. Create them at the listed paths.

| Source in zip | Destination in repo |
|---|---|
| `src/stress_test/list_candidates.py` | `src/stress_test/list_candidates.py` |
| `tests/test_stress_test_list_candidates.py` | `tests/test_stress_test_list_candidates.py` |

---

## INSERT into existing file (1)

Open `DecisionJournal.md` in the repo. The current top of the file looks like:

```
# PM-Tennis — Decision Journal

[... conventions header ...]

---

## D-027 — Probe-slug transport: operator-supplied CLI argument...
```

Open `D-028-entry-to-insert.md` from this zip. **Copy its entire contents** and paste them into `DecisionJournal.md` in the gap between `---` and `## D-027`. So the new file should read:

```
# PM-Tennis — Decision Journal

[... conventions header ...]

---

## D-028 — RAID I-016 fix: source `event_date` from `startDate`...

[... full D-028 entry ...]

---

## D-027 — Probe-slug transport: operator-supplied CLI argument...
```

The `---` separator between D-028 and D-027 is included at the end of the D-028 entry already.

---

## DO NOT commit (1)

`COMMIT_MANIFEST.md` (this file) is for your reference only. Do not commit it to the repo.
`D-028-entry-to-insert.md` is also for reference only — its contents go INTO DecisionJournal.md, but the file itself does not get committed.

---

## File checksums (so you can verify the upload worked)

If you want to spot-check that the right file landed at the right path, here are SHA-256 checksums for each file as it exists in the zip. Compute the SHA of any uploaded file and compare; mismatches mean something went wrong.

(See `CHECKSUMS.txt` in the zip.)

---

## Final test status

| Suite | Pass / Total |
|---|---|
| `TestParseEvent` (incl. 3 new I-016 regression tests) | 15 / 15 |
| `TestCheckDuplicatePlayers` | 4 / 4 |
| Other `test_discovery.py` tests | 28 / 28 |
| `TestVerifySportSlug` | 2 / 4 — **2 pre-existing failures, filed as RAID I-017** |
| `test_stress_test_slug_selector.py` (incl. 6 new I-016 fallback tests) | 25 / 25 |
| `test_stress_test_probe_cli.py` | 19 / 19 |
| `test_stress_test_list_candidates.py` (new) | 20 / 20 |
| **Total** | **113 / 115; 2 failures pre-exist** |
