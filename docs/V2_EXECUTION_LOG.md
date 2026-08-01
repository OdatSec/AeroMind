# AeroMind V2 — Execution Log

Permanent, append-only record tying every completed implementation batch to the
**V2 plan** (`/home/px4/raid/AeroMind_V2_Implementation_Plan.md`, work packages
WP1–WP8) and to the **RAID 2026 reviewer concerns** (452A/B/C).

**Convention.** A task is not "done" until it has an entry here. Every
implementation commit must add or update its entry in the same commit (so the
plan/reviewer mapping travels with the code). Entries are newest-last. Reviewer
tags: **452A** (generalization, method clarity), **452B** (threat-model
strength, overclaiming/`CCR=1`-by-construction), **452C** (novelty, defense
scope, signed-malicious memory). "—" means an entry is foundational/integrity
work that no single reviewer named but that underpins their concerns.

---

## E1 · Repo-anchored, guarded V2 output paths
- **WP item:** WP1 — foundation/integrity (centralize + guard writable result paths).
- **Commit:** `1ee3ba3f53b5b03b35a118c2c73ff0224fee7f45` (2026-08-01).
- **Problem fixed:** result output paths were hard-coded to the legacy `results/`
  tree across 11 runtime/runner sites, with a relative root that depended on the
  working directory. This risked V2 runs silently mixing into or overwriting
  legacy RAID evidence, and stray `results_v2_frozen/` folders outside the repo.
- **RAID concern addressed:** — (integrity foundation enabling clean, separable
  evidence for **452A** generalization and **452B** overclaiming rebuttals).
- **Files / tests / evidence:** new `uavsys/paths.py` (repo-anchored
  `RESULTS_ROOT`, `v2_path`, `default_attack_output`, `assert_writable`);
  repointed 11 writers (`experiment_runner`, `s12_runner`, `s15_runner`,
  `demo.py`, `gpt4o_validation`, `k_sensitivity_sweep`, `benign_utility_sweep`,
  `pool_scaling_experiment`, `agent_scaling_experiment`,
  `agent_scaling_s06_experiment`, `adaptive_attacker_experiment`); new
  `tests/test_paths.py` (30 passing, incl. cwd-independence and `../`/absolute/
  symlink guard-bypass rejection + a repo invariant that fails if any legacy
  write literal reappears).
- **Effect on manuscript claims:** none directly; enables the "evidence bundles
  are self-contained and reproducible" and "no legacy/V2 mixing" claims the V2
  methodology section will make.
- **Remaining limitations / dependencies:** guard is object-level within one
  process; `EXPERIMENT_SPEC_V2.yaml` and the evidence-bundle writer still to come.

## E2 · Legacy/V2 results separation (directory migration)
- **WP item:** WP1 — foundation/integrity (audited results-layout migration).
- **Commit:** `a24c7fbe23b115752c4543169ef216268ae99de0` (2026-08-01).
- **Problem fixed:** legacy RAID results and forthcoming V2 results shared one
  ambiguous `results/` directory, inviting accidental mixing.
- **RAID concern addressed:** — (integrity; supports **452B** by keeping the
  discredited legacy numbers strictly separate from the new evidence base).
- **Files / tests / evidence:** filesystem rename `results/` →
  `results_legacy_raid/` (757 files, 18,206,358 bytes, **checksums identical**
  pre/post — git-ignored, so no git footprint); new tracked
  `results_v2_frozen/PROVENANCE.md`; `.gitignore` updated (legacy ignored; V2
  raw outputs ignored except tracked docs); `tests/test_paths.py` symlink-guard
  test repointed to the existing legacy root. Full suite: 30 passing.
- **Effect on manuscript claims:** underwrites the reproducibility-package and
  data-provenance statements (legacy = read-only comparison; V2 = the only
  writable, committed-code-backed evidence root).
- **Remaining limitations / dependencies:** legacy evidence remains outside
  version control by design (on-disk, read-only); V2 raw bundles are ignored,
  so reproducibility relies on committed code + recorded commit/config hashes.

## E3 · CASR denominator: config-frozen eligible-agent roster
- **WP item:** WP1 — foundation/integrity (metric-correctness fix).
- **Commit:** `cafccd82286d36ad765ca1350486c0a5ffc07268` (batch **B3**; hash
  backfilled by the E4 commit, per the no-amend convention).
- **Problem fixed:** Cross-Agent Spread Rate used a hard-coded denominator of 3
  (`N_SYSTEM_AGENTS = 3`) — the fragile pattern behind the legacy `CASR = 1.5`
  artifact and wrong for any run with a different agent count (G3's 2/4/8/16).
  A participation-derived denominator would also let non-retrieving roles
  (timeouts, early failures, plan-only Supervisor) drop out and inflate CASR
  (e.g. planning mode retrieves only Agent 1 → would report 1/1 instead of 1/3).
  `k_sensitivity_sweep.py` hard-coded `/3` inline as well.
- **RAID concern addressed:** **452B** (overclaiming / metric integrity — a
  defensible, in-range CASR) and **452A** (correct agent-count scaling for the
  multi-agent generalization study).
- **Files / tests / evidence:** `uavsys/utils/metrics.py` — CASR denominator is
  the eligible-agent roster, **frozen from run config at init** via
  `set_eligible_agents()`; once frozen, retrieval/propagation involving an agent
  outside the roster is **rejected (raise)**, not silently added; if never
  frozen it falls back to participation auto-registration (best-effort for
  ad-hoc callers/tests). Infected ⊆ eligible by construction (CASR ∈ [0,1]);
  out-of-range is rejected loudly. Runners `experiment_runner.py`, `s12_runner.py`,
  `s15_runner.py` freeze `SYSTEM_ROSTER = (Agent 1, Agent 2, Supervisor)` at both
  the retrieval and planning `RunMetrics` sites (full-pipeline logs no retrieval,
  so untouched). `k_sensitivity_sweep.py` — inline `/3` replaced by a dynamic
  eligible-roster denominator. `tests/test_metrics_casr.py` (15 tests): legacy-1.5
  → 1.0; 2/4/8/16 counts; **frozen roster keeps a non-retrieving role in the
  denominator** (timeout case, 2/3 not 2/2); frozen variable-count no-inflation;
  unknown retrieval agent and unknown propagation endpoint both raise;
  zero-retrieval; out-of-range raises. Full suite: **45 passing**.
- **Effect on manuscript claims:** CASR values in the V2 tables are valid in
  [0,1], scale correctly with agent count, and are anchored to the declared
  system roster (not to which agents happened to run), removing the discredited
  1.5 artifact and preventing timeout-driven inflation — supports 452A/452B.
- **Remaining limitations / dependencies:** the freeze is wired into the three
  scenario runners; other RunMetrics-based entry points (and any future V2 run
  harness / evidence bundle) must likewise call `set_eligible_agents()` at init.
  The `agent_scaling_*` scripts still compute CASR independently (already dynamic
  via `/n_agents`); unifying them onto `RunMetrics` is a possible later cleanup.

## E4 · Explicit vehicle backend; no silent PX4→mock fallback
- **WP item:** WP1 — foundation/integrity (execution-evidence integrity).
- **Commit:** `6b04a74f4ab3e3c3f6e6347896f83c3e5dec2c8e` (batch **B4**; hash
  backfilled by the E5 commit, per the no-amend convention).
- **Problem fixed:** `MavsdkClient.connect()` caught any timeout/exception and set
  `mock_mode = True`, so a PX4/SITL run whose connection failed would **silently
  degrade to mock** and still be recorded — a full-pipeline result could look
  like closed-loop vehicle execution when no vehicle ever connected. The backend
  was also implicit (no way to declare intent) and not recorded per run.
- **RAID concern addressed:** **452A** (physical/SITL execution realism — closed-
  loop evidence must be genuine, not silent mock) and **452B** (no overclaiming —
  never report mock as SITL execution).
- **Files / tests / evidence:** `uavsys/drones/mavsdk_client.py` — explicit
  `backend` ('px4'|'mock', validated); px4 connect failure/timeout now **raises**
  (never sets mock_mode); mock skips real I/O; `System` is created lazily (px4
  path only) so mock/tests spawn no mavsdk server; records `requested_backend`
  and `actual_backend`. `experiments/experiment_runner.py` — new
  `--vehicle-backend px4|mock` (default **px4**), threaded into
  `run_full_pipeline_mode`; full-pipeline client uses it and records
  requested/actual in each agent bundle; planning constructs `backend="mock"`.
  `experiments/s12_runner.py`, `experiments/s15_runner.py` — explicit backends at
  every MavsdkClient site (full-pipeline `px4`, planning `mock`) so the new
  default cannot silently switch them to mock. New `tests/test_backend_guard.py`
  (6 tests: invalid backend rejected; mock skips I/O and spawns no System; px4
  success → actual=px4; px4 failure and px4 timeout both raise and never set
  mock; requested backend recorded). Full suite: **51 passing**.
- **Effect on manuscript claims:** any full-pipeline/SITL result now carries a
  recorded requested/actual backend and can never be a silent mock, so the
  closed-loop execution evidence (and the "SITL, not real hardware" wording) is
  trustworthy and auditable.
- **Design note (intentional, not an omission):** only `experiment_runner` (the
  primary V2 runner) exposes the `--vehicle-backend` flag; `s12`/`s15` are
  deliberately pinned (full-pipeline=`px4`, planning=`mock`). This is
  safety-preserving — every backend is explicit and no path can silently fall
  back to mock — while keeping the batch scoped (no new CLI surface on the
  boundary/legacy runners). A flag can be added to them later if a real need
  arises.
- **Remaining dependencies:** the evidence-bundle writer (later WP1 item) should
  persist requested/actual backend at the run (not just per-agent) level.

## E5 · V2 experiment spec — DRAFT contract (not frozen)
- **WP item:** WP1 — foundation (frozen experiment contract; the Aug-2-style spec freeze).
- **Commit:** `SELF` (batch **B5**; hash backfilled by the next docs-touching commit, no amend).
- **Problem fixed:** the V2 campaign had no single, machine-readable source of truth
  mapping scenarios, layers, models, seeds, defenses, and matrices to reviewer
  concerns — so runs would drift and be hard to audit. This adds
  `configs/EXPERIMENT_SPEC_V2.yaml` as a declarative contract a thin expander can
  later consume; it deliberately does NOT change runner behavior yet.
- **RAID concern addressed:** all — **452A** (memory/agent generalization via
  anchored G1/G3), **452B** (retrieval-boundary G2; anchored matrix + validity
  constraints prevent an arbitrary/rigged grid), **452C** (D0–D4 per-mechanism
  defense ablation; novelty framing per scenario claim_scope).
- **Files / evidence:** `configs/EXPERIMENT_SPEC_V2.yaml` — C0–C6↔legacy mapping;
  L1–L4 layers; provisional pinned models with immutable-pinning policy; tiered
  seeds; **D0–D4** taxonomy (recommended) with code crosswalk; anchored G1/G2/G3
  with boundary-preserving subsets; validity constraints; promotion rules incl.
  L4 physical-impact demonstrators (C1/C2/C6, +C5 contagion); metrics; required
  evidence-bundle manifest fields; stop conditions. Reviewer targets + claim
  scope attached throughout.
- **NOT frozen:** `meta.status: draft`. Four `pending_faculty_decisions` remain
  (FD1 defense taxonomy — Cam/Dr. Qian; FD2 planner models; FD3 seed tiers/CI;
  FD4 matrix subsets). No defense configs added and no experiments run.
- **Effect on manuscript claims:** none yet; it is the contract that makes future
  V2 results auditable and reviewer-mapped.
- **Remaining dependencies:** G1 needs the memory generator; G3 needs the L3
  simulator; D2-only/D3-only isolated defense configs are `needs-config`
  (owned by Cam/Dr. Qian). Next foundational item: the evidence-bundle writer,
  which the spec's `evidence.manifest_fields` already targets.

<!-- New entries appended below as part of each implementation commit. -->
