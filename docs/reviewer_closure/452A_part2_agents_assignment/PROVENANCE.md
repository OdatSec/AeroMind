# 452A Part 2 — Provenance & evidence integrity

Raw evidence bundles are **NOT** committed to git (git-ignored `results_v3_raw/`, same model as
`results_v2_frozen/`). They live on disk; this file records their exact paths and the hashes needed
to verify them.

## Pre-registration hash
- `docs/preregistration/PREREG_452A_part2_agents_assignment.md` — **sha256
  `f2314da536bc635579c737f5e008020445e9068677827c707bed4eeefab86cc0`** (recorded in every bundle's
  `configured.prereg_spec_hash`; frozen at commit `92318c9`, before any run).

## Embedder (digest-pinned; recorded in every bundle)
- model-layer (weights): `sha256:970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6`
- manifest config: `sha256:31df23ea7daa448f9ccdbbcecce6c14689c8552222b80defd3830707c0139d4f`
- (nomic-embed-text; the DIGEST is authoritative, not the `latest` tag. Embedder-only run — no chat
  model, `model-na`.)

## Memory profile — MEM060_OPERATIONAL materialization hashes (per seed; full set in each bundle)
| seed | profile_materialization_hash (prefix) |
|---|---|
| 101 | `ba5fcb9fd9529b48…` (matches 452A Part 1 — same profile/seed) |
| 110 | `b224e91e0dcd1e31…` |

## Accepted campaign (240 production bundles)
Operating point: MEM060_OPERATIONAL, top-k 3, D0, T01_SEARCH_RESCUE, seeds 101–110, `model-na`.
All bundles: `validity=production`, `run_class=production`, `dirty_start=dirty_end=False`,
`commit_start = 4aca5138c2e6f48eef889cb278ee8d306c5e4e27`.

| Arm | Attack | Budget dir | Cells | Runs |
|---|---|---|---|---|
| Attack | `A01_FALSE_OBSERVATION` | `budget-03` | 12 (scouts{2,4,8,16} × assign{fixed,random,dynamic}) | 120 |
| Control | `A00_CLEAN` | `budget-00` | 12 | 120 |

Canonical layout (git-ignored `results_v3_raw/`):
```
<ATTACK>/T01_SEARCH_RESCUE/MEM060_OPERATIONAL/MULTI/model-na/D0/topk-03/budget-<03|00>/
  temp-na/agents-<03|05|09|17>/assign-<fixed|random|dynamic>/seed-01NN/run-<id>/
```
Example:
`results_v3_raw/A01_FALSE_OBSERVATION/T01_SEARCH_RESCUE/MEM060_OPERATIONAL/MULTI/model-na/D0/topk-03/budget-03/temp-na/agents-03/assign-fixed/seed-0108/run-1a9101b1-cbd6de17/`

Each bundle: `manifest.json` (validity, config_hash, commit, seed, canonical, prereg/embedder/
materialization hashes), `config.yaml`, `environment.json`, memory snapshots
(`memory_before/injected/memory_after`), `retrieval_trace` (per-agent exposure + queries),
`metrics.json` (manipulation checks + outcomes + assignment_map), `status.json`, `checksums.sha256`.

## Accept-gate audit — PASS (0 problems)
`python3 experiments/campaign_452a_part2.py --audit` verified, over all 240 bundles:
1. 240/240 production bundles present (12 cells × 10 seeds × 2 arms).
2. Poison-blindness: A00 and A01 `assignment_map` byte-identical at every cell/seed.
3. Attacked-subtask schedule identical across all three policies per seed (policy-independent).
4. A00 control exposure = 0 (`total_fleet_blast_radius_count == 0`) in every cell/seed.
5. Provenance present on every bundle: `prereg_spec_hash` + pinned embedder `digest`.

## Curated artifacts (in this directory)
- `campaign_summary.json` — full per-cell aggregation + accept-gate result (sha256 `29c8ea12…dee0`).
- `fleet_by_assignment.csv` — the 12-row fleet-size × assignment table.
- `SPECIFICITY_DIAGNOSTIC_A01_LOCAL.md` — negative subtask-local diagnostic (supporting only).

## Deterministic regeneration
```
python3 experiments/campaign_452a_part2.py --audit
```
Bootstrap is seeded (`random.Random(0)`); regenerating overwrites `campaign_summary.json`
byte-identically (verified: sha256 stable across two runs). Aggregation only — runs nothing, reads
only frozen production bundles.

## Code commits (branch `revision/452a-part2-agents-assignment`)
| Commit | What |
|---|---|
| `92318c9` | Freeze pre-registration (sha256 `f2314da5…86cc0`) |
| `19d1c20` | L3 logical multi-agent exposure simulator + `--mode MULTI` |
| `993d3e2` | Freeze `A01_FALSE_OBSERVATION_LOCAL` subtask-local variant (negative diagnostic) |
| `4aca513` | L3 campaign aggregator + accept-gate audit (the run commit) |
