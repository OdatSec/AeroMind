# 452B — Provenance & evidence integrity

Raw bundles are NOT committed to git (git-ignored `results_v3_raw/`, same model as
`results_v2_frozen/`). Paths + hashes below verify them.

## Pre-registration hashes (recorded in each bundle `configured.prereg_spec_hash`)
- Memory templates: `docs/preregistration/PREREG_452A.md` — sha256 `cc8c0e8b…441e073`.
- RET k×budget: `docs/preregistration/PREREG_452B_topk_budget.md` — sha256 `b8c6ddbb…67e8c2`.
- PLAN adoption: `docs/preregistration/PREREG_452B_PLAN_adoption.md` — sha256 `8d707892…c02394`.
  (RET bundles attest the RET prereg; PLAN bundles attest the PLAN prereg — via `AEROMIND_PREREG`.)

## Embedder (pinned; in every bundle `environment.json`)
- model-layer: `sha256:970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6`
- manifest config: `sha256:31df23ea7daa448f9ccdbbcecce6c14689c8552222b80defd3830707c0139d4f`

## Memory materialization (MEM060_OPERATIONAL; recorded per bundle `configured.profile_materialization_hash`)
- seed 101: `ba5fcb9fd9529b48…` (full per-seed set in each bundle manifest).

## Raw evidence paths (under `results_v3_raw/`, git-ignored)
RET (memory MEM060, eval RET):
  `<A01_FALSE_OBSERVATION|A00_CLEAN>/T01_SEARCH_RESCUE/MEM060_OPERATIONAL/RET/model-gpt-oss-20b/D0/<TOPK>/budget-<BB>/temp-na/seed-01NN/run-<id>/`
  <TOPK> ∈ topk-03 | topk-05 | topk-10 | topk-20 (symmetric)  OR  topk-s03-p05 (asymmetric baseline, budget-03)
PLAN (memory MEM060, eval PLAN):
  `<A01_FALSE_OBSERVATION|A00_CLEAN>/T01_SEARCH_RESCUE/MEM060_OPERATIONAL/PLAN/model-gpt-oss-20b/D0/topk-<0N>/budget-<00|03>/temp-0.0/seed-01NN/run-<id>/`

| Slice | count | eval | notes |
|---|---|---|---|
| RET symmetric A01 k∈{5,10,20}×b∈{1,2,3,5} | 120 | RET | new |
| RET symmetric A00 controls k∈{5,10,20} b0 | 30 | RET | new |
| RET asymmetric scout3/sup5 (A01 b3 + A00 b0) | 20 | RET | new, `topk-s03-p05` |
| RET reused k=3 (452A MEM060 A01 b{1,2,3} + A00 b0) | 40 | RET | reused |
| PLAN planner_k∈{3,5,10,20} × {A00,A01} | 80 | PLAN | new |

Each bundle: manifest (validity=production, config_hash, commit, seed, canonical, configured incl.
scout/supervisor topk, prereg hash, materialization hash), config, environment (embedder digest),
memory before/injected/after, retrieval_trace, metrics (+ RET topology/retrieval_competition),
and for PLAN: planner_context / planner_raw_output / parsed_actions (valid_plan, planner_outcome,
coordinate_adoption). All passed the accept-gate (RET 170/170 new; PLAN 80/80).

## Code commits (branch `revision/452b-topk-budget`)
| Commit | What |
|---|---|
| `15b2896` | Freeze PREREG_452B_topk_budget (b8c6ddb) |
| `0e3e549` | Asymmetric scout/supervisor top-k + collision/backward-compat tests |
| `13a8af1` | RET k×budget aggregator + campaign results (170 accepted) |
| `9fb911f` | Freeze PREREG_452B_PLAN_adoption (8d70789) |
| `09dfde6` | PLAN provenance fields (embedder digest, materialization + prereg hash) + tests |

## Regeneration (one command; deterministic)
`python3 experiments/campaign_452b.py && python3 experiments/campaign_452b_plan.py`
→ reproduces `results_v3_campaigns/452B_topk_budget/` and `.../452B_PLAN_adoption/`; the curated
`ret_*` / `plan_*` copies here are the accepted snapshot.

## Immutability
`results_v2_frozen/` untouched (0 changes). No raw bundle edited/renamed/recomputed. No selective
reruns; no template tuning. RET campaign NOT rerun for the PLAN study.
