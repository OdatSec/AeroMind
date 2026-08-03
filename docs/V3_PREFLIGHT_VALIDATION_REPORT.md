# V3 Pre-Production Validation Report

**Verdict: ✅ READY FOR SCIENTIFIC CAMPAIGNS**

Disposable end-to-end validation of the Final Campaign V3 system, run against a
**temporary sandbox root** (`AEROMIND_V3_RAW_ROOT` / `AEROMIND_V3_CAMPAIGNS_ROOT`
→ scratchpad). **Production `results_v2_frozen/` and `results_v3_raw/` were never
touched; all sandbox artifacts were deleted afterward.** Code at commit `9c6b3ec`.

## Scope executed
- **Evaluations:** RET (embedder-only) and PLAN (LLM).
- **Models:** `gpt-oss:20b` and `qwen2.5:7b` (two locally-installed models).
- **Attacks:** A00_CLEAN + A01_FALSE_OBSERVATION, A03_FALSE_RESTRICTION,
  A05_SIGNED_FALSE_OBSERVATION (D1), A07_FALSE_COMPLETION (T02), A08_FALSE_SAFETY (T03).
- **Tasks:** T01_SEARCH_RESCUE, T02_MULTI_TARGET, T03_RESTRICTED_ZONE.
- **Memory:** MEM003_SPARSE, MEM060_OPERATIONAL.
- **Swept axes:** top-k (3, 5), poison budget (default, 3), temperature (0.1, 0.7),
  seeds (201, 202), model path, defense (D0, D1).
- **15 real production-valid bundles** across these cells, plus 4 negative checks.

## Results
| Check | Result |
|---|---|
| Every run exited 0; 15 bundles produced | ✅ |
| Every argument saved in the correct folder **and** manifest | ✅ 15/15 — `canonical` block == path segments; `config_hash_schema v3` with `budget` in `run_axes`; `validity=production`, `valid=true`, `dirty_start=false` |
| No run overwrote or mixed | ✅ 15/15 unique directories |
| Metrics agree with raw outputs | ✅ RET `ccr == poisoned/total` (4/4); PLAN `parsed_actions.tools_used == plan_json steps` and `outcome↔valid_plan` consistent (11/11) |
| Axis variations distinct & correct | ✅ `topk-05`, `temp-0.7`, `budget-03`, `seed-0202`, `model-gpt-oss-20b`, `D1` each produced their own folder |
| Invalid / deferred / MULTI / unavailable fail loud | ✅ A08+T02 (lock) → exit 1; A09 (deferred) → exit 1; MULTI (L3, no runner) → exit 1; unknown id → exit 1; SITL px4-unavailable → backend guard raises (covered by `test_backend_guard`) |
| Campaign artifacts generated & labeled | ✅ README / campaign_summary.json / paired_results.csv / bundle_index.yaml / INSIGHTS_DRAFT.md / CLAIMS.md; INSIGHTS labeled **DRAFT / not a paper finding**; CLAIMS carries the **PRE-PRODUCTION VALIDATION** caveat |
| `PAPER_FINDINGS.md` never auto-written | ✅ (human-only) |

Attacks were **not** tuned and were **not** required to succeed — any outcome was
recorded as-is.

## Genuine fixes committed during preflight
1. `feat(v3): redirectable V3 roots via env` (`fd58088`) — `AEROMIND_V3_RAW_ROOT` /
   `AEROMIND_V3_CAMPAIGNS_ROOT` enable sandboxed/CI validation without touching
   production; V2 root remains non-overridable.
2. `feat(runner): --topk / --temp sweep flags` (`9c6b3ec`) — top-k and temperature
   are now CLI-settable and fold into both the config-hash and the path (required
   for the G2 top-k × budget × temperature sweep).

## Test suite
Full suite green at each step (226 tests), including taxonomy alias equivalence,
task locks, config-hash schema v1/v2/v3 (budget), hierarchical paths, the sandbox
axis-matrix (no mixing), campaign/insight generation, and V2 backward-compat.

## Handoff readiness for Cam (defense integration)
**Ready to hand off**, with these interfaces in place:
- Canonical defenses **D0–D4** in the taxonomy; `--defense`/`--defense-config`
  wiring; defense recorded in the path (`<DEFENSE>`) and manifest; D1 signing
  exercised here (A05).
- **Remaining (Cam / Dr. Qian's scope):** add the **D2-only and D3-only** isolation
  configs to `configs/defense_sweeps.yaml` (currently bundled in D_authz/D_full),
  then run defended campaigns (D1–D4) against the accepted attack bundles. Defense
  taxonomy freeze is FD1.

## Cleanup confirmation
All sandbox artifacts deleted; `results_v3_raw/` does not exist in the repo;
`results_v2_frozen/` unchanged (0 git changes).
