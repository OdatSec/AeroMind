# 452A Part 1 — Provenance & evidence integrity

Raw evidence bundles are **NOT** committed to git (git-ignored `results_v3_raw/`, same
model as `results_v2_frozen/`). They live on disk; this file records their exact paths and
the hashes needed to verify them.

## Pre-registration hashes
- `docs/preregistration/PREREG_452A.md` — **sha256 `cc8c0e8b36b5069ce54757052ecff988e30fed0f4e32694cbf56d3457441e073`** (recorded in every bundle's `configured.prereg_spec_hash`).
- `docs/preregistration/PREREG_452A_nonsaturated.md` — **sha256 `9884e94e687f4af56e33eaf538683c4e12b3e4178a39e5fa00c09f852809a7ef`** (budget-axis addendum; templates unchanged).

## Embedder (digest-pinned, recorded in every bundle `environment.json`)
- model-layer (weights): `sha256:970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6`
- manifest config: `sha256:31df23ea7daa448f9ccdbbcecce6c14689c8552222b80defd3830707c0139d4f`
- (nomic-embed-text; the DIGEST is authoritative, not the `latest` tag.)

## Per-profile materialization hashes (seed 101 shown; full 10-seed set in each bundle + `similarity_audit_452a.json`)
| Profile | materialization_hash(seed 101) |
|---|---|
| MEM003_SPARSE | `fb41ab2f127d7a15…` |
| MEM060_OPERATIONAL | `ba5fcb9fd9529b48…` |
| MEM200_DENSE | `c4405a6286210b88…` |
| MEM060_EPISODIC_HEAVY | `9ebdef3224bc0327…` |
| MEM060_BENIGN_HIGHSIM | `996fdc87051b58fc…` |

## Raw evidence paths (under `results_v3_raw/`, git-ignored)
Canonical layout: `<ATTACK>/T01_SEARCH_RESCUE/<MEM>/RET/model-gpt-oss-20b/D0/topk-03/<BUDGET>/temp-na/seed-01NN/run-<id>/`

| Slice | Attack | Budget dir | Count | Bundle commit_start |
|---|---|---|---|---|
| Saturated attack | `A01_FALSE_OBSERVATION` | `budget-03` | 50 | `1e3d0eb` |
| Controls (reused) | `A00_CLEAN` | `budget-00` | 50 | `1e3d0eb` |
| Non-saturated attack | `A01_FALSE_OBSERVATION` | `budget-01` | 50 | `ac5ceb4` |
| Non-saturated attack | `A01_FALSE_OBSERVATION` | `budget-02` | 50 | `ac5ceb4` |

Example: `results_v3_raw/A01_FALSE_OBSERVATION/T01_SEARCH_RESCUE/MEM060_BENIGN_HIGHSIM/RET/model-gpt-oss-20b/D0/topk-03/budget-01/temp-na/seed-0108/run-fa012585-6d5711e1/`

Each bundle: `manifest.json` (validity=production, config_hash, commit, seed, canonical),
`config.yaml`, `environment.json` (embedder digest), `memory_before/injected/memory_after.jsonl`,
`retrieval_trace.jsonl`, `metrics.json` (rates + `retrieval_competition`), `status.json`,
`checksums.sha256`. Every bundle passed the accept-gate (files+checksums, production+clean
tree, prereg-hash, materialization-hash, embedder-digest, CCR-recompute, unique path).

## Code commits (branch `revision/452a-generalization`)
| Commit | What |
|---|---|
| `96334fd` | Freeze `PREREG_452A.md` (spec hash cc8c0e8b) |
| `a8824b6` | Part 1 impl: 3 new profiles, malicious-rank/clean-displacement, similarity-audit tool |
| `2203170` | V3 runner integration (5 profiles) + retrieval-competition metrics + provenance recording |
| `1e3d0eb` | Campaign aggregator + log rename V2→V3 — **saturated campaign ran here** |
| `4261c48` | clean_displacement multiplicity fix + non-saturated addendum + aggregator |
| `ac5ceb4` | gitignore generated campaign subfolders — **non-saturated campaign ran here** |

## Regeneration
Campaign summaries regenerate from the raw bundles: `python3 experiments/campaign_452a.py`
(saturated) and `python3 experiments/campaign_452a_nonsaturated.py` (non-saturated). The
curated copies here (`saturated_*`, `nonsaturated_*`) are the accepted snapshot.

## Immutability
`results_v2_frozen/` untouched throughout (0 git changes). No raw bundle was edited,
renamed, or recomputed. No selective reruns; no template tuning.
