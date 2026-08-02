# AeroMind V2 Results — Provenance & Rules

This directory holds **all** evidence for the AeroMind V2 campaign. It is the
**only** writable results root (enforced in code by `uavsys/paths.py`).

## Origin
- Legacy RAID results were produced **before** the V2 campaign and now live,
  unchanged, under `results_legacy_raid/` as **read-only evidence**.
- The V2 results branch (`revision/v2`) is based on commit
  `24ffb50bb2c1eb8219be72b28cdf686ab983d95f`; this migration was recorded at
  commit `1ee3ba3f53b5b03b35a118c2c73ff0224fee7f45`.

## Non-negotiable rules
1. **Never mix legacy and V2 results.** `results_legacy_raid/` (legacy) and
   `results_v2_frozen/` (V2) must not appear together in the same table, plot,
   or aggregate. Legacy values are for reproduction comparison only.
2. **Legacy is read-only.** Do not write into, edit, or delete anything under
   `results_legacy_raid/`. V2 code is guarded to refuse writes there.
3. **All new V2 runs write only here**, under `results_v2_frozen/`.
4. **No result is valid unless it was generated from committed code** with a
   recorded **commit hash** and **config hash** in its run bundle. Results from
   uncommitted or unversioned code are not admissible evidence.

## Layout (created lazily by runs)
`results_v2_frozen/attacks/<scenario>/<mode>.json`, plus per-campaign
subdirectories (e.g. `agent_scaling/`, `k_sensitivity/`). Raw run bundles are
git-ignored; only this document is tracked.

## Smoke-validation runs
- **`C0__L1__model-gpt-oss-20b__seed0042__D0__cfg-3b571f7a__61eeaafc/`** — the first
  V2 evidence bundle. This is a **smoke-validation run** of the C0 (B0) clean
  baseline at L1 (retrieval), produced to validate the evidence pipeline
  end-to-end (code commit `3f9bc7b`, clean tree). It is a real, valid production
  bundle (validity=production), not scientific campaign evidence; keep it as the
  pipeline-validation reference.
- **`C1__L1__model-gpt-oss-20b__seed0042__D0__cfg-cc32b7ff__87b55565/`** —
  **SUPERSEDED** smoke-validation bundle for C1 (S01) at L1 (code `d54c1fd`).
  **Known defect:** `injected_records.jsonl` contains only **1 of the 3** injected
  records. The runner computed the injected delta using a bare row `id`, but row
  ids are per-table AUTOINCREMENT, so the injected episodic ids 1,2 collided with
  pre-existing semantic ids 1,2 and were filtered out. Fixed by keying record
  identity on `(layer, id)`.
  **The full delta remains recoverable from this bundle**: `memory_before.jsonl`
  and `memory_after.jsonl` are complete and correct, and their `(layer, id)`
  difference — equivalently the three `source="atk:S01"` records in
  `memory_after` — yields the true injected set. All other artifacts (checksums,
  manifest hashes, timepoints, retrieval trace, metrics) are valid.
  Retained for audit continuity; superseded by the post-fix C1 re-run.
- **`C1__L1__model-gpt-oss-20b__seed0042__D0__cfg-0d4c5af3__0b783e9d/`** —
  **ACCEPTED** C1 (S01) L1 smoke-validation bundle (code `fdaca36`); supersedes
  `…cfg-cc32b7ff__87b55565`. Verified: `injected_records.jsonl` contains all
  **3** records `(episodic,1/2/3)` with `source="atk:S01"`; memory before/after =
  3/6 with `after == before ∪ injected`; score components (relevance/recency/
  importance) present for all 11 retrieved items; checksums, commit/spec hashes,
  `validity=production` all pass. Reproduced the superseded run exactly —
  identical retrieval ordering and per-item scores, CCR 0.8182, MTR 0.8667,
  RIS 0.0, CASR 1.0.
  **Note on `config_hash`:** this bundle predates the config-fingerprint fix, so
  its `config_hash` was computed over a config view that still included the
  ephemeral `DB_PATH` (a per-run temp file) and therefore is **not** reproducible
  across runs. This affects only the fingerprint's comparability — all scientific
  artifacts and checksums in this bundle remain valid and were re-verified. From
  the fix onward, `config_hash` excludes execution-ephemeral fields and the
  manifest records the fingerprint schema (`config_hash_schema`). This bundle was
  **not** re-run for the hash change.
