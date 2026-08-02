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
- **Commit:** `7c5c956c1048b9e9830a5e5628ad3ccf64e4a7ab` (batch **B5**; hash
  backfilled by the E6 commit, per the no-amend convention).
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

## E6 · Evidence-bundle writer (integrity-checked per-run artifacts)
- **WP item:** WP1 — foundation (the artifact contract every V2 run must satisfy).
- **Commit:** `bbe358948f62ed065c09c14cc5dd72b70b975530` (batch **B6**; hash
  backfilled by the E7 commit, per the no-amend convention).
- **Problem fixed:** the RAID paper's artifacts were incomplete/inconsistent
  (missing files, the CASR=1.5 mismatch), so results were not independently
  verifiable and failed runs could vanish. There was no per-run bundle, no
  environment/commit/config capture, and no checksums.
- **RAID concern addressed:** all (**452A/452B/452C**) via evidence integrity —
  every reported number becomes traceable to committed code, a config+spec hash,
  the backend, the roster, and per-file checksums; failures stay countable.
- **Files / tests / evidence:** new `uavsys/evidence/bundle.py` (`EvidenceBundle`)
  — passive collector; git commit+dirty captured at start AND finalize; a
  production bundle (under the V2 results root) is refused if dirty at either
  point or if the commit changed mid-run; `allow_dirty` is forbidden under the
  results root and marks dev bundles `valid=False`/`development-only`; required
  files depend on layer AND outcome (aborted timeout/parse/infra still yields a
  complete failure bundle that stays in the denominator); manifest records
  spec_hash, config_hash (secret-redacted), resolved params, embedder identity,
  requested/actual backend, and memory params; collision-safe run IDs + atomic
  stage→`os.replace` publish. New `MemoryInterface.snapshot()` (records without
  raw vectors; carries `vector_sha256`+`vector_dim`). New
  `tests/test_evidence_bundle.py` (12 tests: dev-invalid, production happy path,
  dirty-at-start/commit-change/dirty-at-finalize refusals, allow_dirty-under-root
  refusal, incomplete-success rejection, aborted-run complete failure bundle,
  L2-requires-planner, collision-safe IDs, secret redaction + checksum validity).
  Full suite: **63 passing**.
- **Minimum wiring:** `experiment_runner` retrieval mode gains **opt-in**
  `--evidence-bundle` (default OFF — existing behavior unchanged). The bundle is
  created EARLY; `memory_before` is captured at its TRUE timepoint (post-seed /
  pre-inject) via a `seed_and_inject(on_seeded=...)` hook — never reconstructed
  post hoc; `memory_after` is the post-inject snapshot and `injected` is the real
  id-delta. Any exception after bundle creation is finalized into a failure
  bundle (`included_in_denominator=true`), not left as an orphan staging dir.
  Legacy→C mapping added (`LEGACY_TO_C`); `evidence_dir` param enables hermetic
  tests.
- **Atomicity:** the staging dir is `final_dir + ".staging-<uuid>"` (same parent
  and filesystem as the final bundle), so `os.replace(stage, final)` is a genuine
  atomic publish.
- **Effect on manuscript claims:** none yet; enables auditable, reproducible V2
  evidence and honest failure accounting once enabled.
- **Validation status / next step:** writer + wiring are unit- and
  integration-tested (mocked memory, no live embeddings); a full L1 run is still
  NOT run-validated. Recommended next step is a supervised 1-seed smoke run with
  `--evidence-bundle` on a clean tree. Added
  `tests/test_runner_evidence_integration.py` (2 tests: true-timepoint L1 bundle;
  failure→failure-bundle).
- **Remaining dependencies:** wiring for L2/L4 bundles; L4 telemetry/trajectory
  capture; digest capture for embedder/models (currently recorded null when
  unavailable).

## E7 · Fail-loud retrieval (no silent embedding-failure success)
- **WP item:** WP1 — foundation (evidence integrity; closes a false-success path).
- **Commit:** `d05f435023f13b2056b9d28e1959801098be44f6` (batch **B7**; hash
  backfilled by the E8 commit, per the no-amend convention).
- **Problem fixed:** `MemoryInterface.retrieve()` caught embedding failures and
  returned `{"results": [], "error": ...}` — a key no caller reads (all use
  `get("matches", [])`), so an Ollama/embedding outage silently became "zero
  matches" and could finalize as a **successful** scientific run (CCR=0). This
  was the false-success risk flagged in the C0 smoke plan.
- **RAID concern addressed:** all (**452A/452B/452C**) via result integrity — an
  infrastructure failure can never masquerade as a valid zero-poison result.
- **Files / tests / evidence:** `uavsys/memory/memory_interface.py` — new
  `RetrievalInfrastructureError`; the embedding path now **raises** it (fail
  loud) instead of returning a silent-empty error dict. A legitimate zero-match
  (embedding OK, nothing retrieved) is unchanged (`{"matches": []}`). The
  retrieval runner's evidence path already finalizes any such exception into an
  `infrastructure_failure` bundle (`included_in_denominator=true`) with the error
  recorded in `status.json`. New `tests/test_retrieval_failloud.py` (retrieve
  raises on embedding failure) and 2 added runner-integration tests
  (embedding-failure → infra bundle with error recorded; legitimate zero-match →
  success). Full suite: **68 passing**.
- **Behavior change (intended):** any caller of `retrieve()` (agents, all
  runners, demo) now sees an exception on embedding failure instead of silent
  empty matches — a strict fail-loud improvement, not just the evidence path.
- **Effect on manuscript claims:** protects every retrieval-stage number from an
  undetected infrastructure failure being reported as a real result.
- **Remaining dependencies:** none new; unblocks the supervised C0 smoke run.

## E8 · Runner invocation hardening (direct path run resolves uavsys)
- **WP item:** WP1 — foundation (reproducibility of the run harness).
- **Commit:** `3f9bc7b2bf8c266f49f4d682527897d3a0ffb9bc` (batch **B8**; hash
  backfilled by the E9 commit, per the no-amend convention).
- **Problem fixed:** the mode-runners' `main()` does `from uavsys.paths import ...`,
  but running a runner by direct path (`python experiments/experiment_runner.py`)
  puts `experiments/` on `sys.path[0]`, not the repo root, so `uavsys` was not
  importable → `ModuleNotFoundError` at run start. The documented C0 smoke command
  hit exactly this (clean failure: no bundle, no staging, tree clean).
- **RAID concern addressed:** reproducibility/integrity (—): the documented run
  command must work for any operator without remembering `PYTHONPATH`/`-m`.
- **Files / tests / evidence:** `experiments/experiment_runner.py`,
  `experiments/s12_runner.py`, `experiments/s15_runner.py` — 2-line module-top
  `sys.path` bootstrap inserting the repo root. New `tests/test_runner_invocation.py`
  (3 tests): each runner, invoked by path with `PYTHONPATH` stripped, gets past
  the deferred `uavsys` import (reaches the legacy-path guard) — no Ollama/DB.
  Full suite: **71 passing**.
- **Effect on manuscript claims:** none; unblocks the documented C0 smoke run.
- **Remaining dependencies:** none. The standalone V1 sweep scripts
  (k_sensitivity, gpt4o_validation, etc.) still expect `-m`/PYTHONPATH; out of
  scope here (not on the V2 C0–C6 path).

## E9 · Evidence integrity: (layer, id) record identity + configured/observed split
- **WP item:** WP1 — foundation (evidence correctness; found by the C1 smoke run).
- **Commit:** `fdaca3626b7bdc8b6a6b3255e61cd8ea2398b27e` (batch **B9**; hash
  backfilled by the E10 commit, per the no-amend convention).
- **Problem fixed:** the runner computed the injected-record delta with a **bare
  row `id`**. Row ids are per-table AUTOINCREMENT, so the C1/S01 injected episodic
  ids 1,2 collided with pre-existing semantic ids 1,2 and were filtered out —
  `injected_records.jsonl` recorded **1 of 3** genuinely injected records. Two
  smaller evidence gaps were closed alongside: the retrieval score-component
  breakdown (already computed by the engine) was dropped, and the manifest's
  `memory_*` fields conflated requested inputs with measured facts.
- **RAID concern addressed:** all (**452A/452B/452C**) via evidence correctness —
  the record of what an attack actually wrote must be exact and auditable.
- **Files / tests / evidence:** `experiments/experiment_runner.py` — new
  `record_key()` ((layer, id)), `flatten_snapshot()` (stamps the authoritative
  layer from the snapshot key), `injected_delta()`; the evidence path now uses
  them. Retrieval trace items now preserve `relevance`/`recency`/`importance`
  (the engine's alpha/beta/gamma components). `uavsys/evidence/bundle.py` —
  `memory_params` replaced by an explicit **`configured`** block (requested:
  memory_profile, top_k_by_agent, poison_budget — `None` means "scenario
  default") and an **`observed`** block auto-derived in `record_memory()`
  (memory_records_before/after, injected_records, attack_tagged_records_after);
  the ambiguous flat `memory_size`/`memory_poison_budget` names are gone. New
  `tests/test_record_identity.py` (5, incl. a test asserting the old bare-id
  delta undercounts 1-of-3 while the fix yields 3) and a runner-level end-to-end
  regression with colliding per-table ids asserting all three S01 records are
  captured and the configured/observed split is present. Full suite: **77 passing**.
- **Scope:** evidence-only. No attack, defense, ranking, or metric behavior changed.
- **Effect on manuscript claims:** injected-record evidence is now exact; score
  components are auditable per retrieved item; configured vs observed values can
  no longer be confused in the manifest.
- **Superseded artifact:** the pre-fix C1 smoke bundle
  (`C1__...__cfg-cc32b7ff__87b55565`) is retained and labeled in
  `results_v2_frozen/PROVENANCE.md` with its known defect and a note that the
  full delta is recoverable from `memory_before`/`memory_after`.

## E10 · Reproducible config fingerprint (ephemeral fields excluded)
- **WP item:** WP1 — foundation (evidence auditability).
- **Commit:** `6c204f92404c2c3df8d7c25651e4044f76d80aab` (batch **B10**; hash
  backfilled by the E11/E12 commit, per the no-amend convention).
- **Problem fixed:** `config_hash` was computed over the whole `Config`, which
  includes execution-ephemeral fields — notably `DB_PATH`, a fresh tempfile per
  run. Two C1 runs with identical seed/parameters therefore reported different
  `config_hash` values (`cc32b7ff` vs `0d4c5af3`; a byte-diff of the two
  `config.yaml` files showed `DB_PATH` as the ONLY difference). The fingerprint
  could not support "same configuration ⇒ same hash", and the `cfg-XXXXXXXX`
  component of `run_id` was effectively random rather than a config identifier.
- **RAID concern addressed:** — (reproducibility/auditability underpinning
  **452A/452B**: every reported number must be attributable to an identifiable,
  comparable configuration).
- **Files / tests / evidence:** `uavsys/evidence/bundle.py` — new
  `EPHEMERAL_CONFIG_FIELDS = ("DB_PATH", "RUN_ID")` and
  `CONFIG_HASH_SCHEMA_VERSION`; `_compute_config_hash()` fingerprints the
  canonical view (full config minus ephemeral fields) with the schema version
  bound INTO the hashed payload, so a canonicalization change can never collide
  with an old fingerprint. `config.yaml` still records every field verbatim
  (secrets redacted). The manifest gains `config_hash_schema`
  {version, excluded_fields, note} so an auditor can recompute the hash. The
  stable `cfg-` prefix stays in `run_id`, and the uuid suffix keeps collision
  safety. New `tests/test_config_hash_stability.py` (14): DB_PATH/RUN_ID changes
  (individually and together) preserve the hash; TOP_K_SCOUT/TOP_K_PLANNING/
  CHAT_MODEL/EMBED_MODEL/DEFENSE_ENABLED/DEFENSE_TRUST_WEIGHT/alpha/beta/gamma
  each change it; schema version is bound into the hash; and an end-to-end check
  that two bundles differing only in DB_PATH share a config_hash and `cfg-`
  prefix while keeping distinct run_ids, with full values still in config.yaml.
  Full suite: **91 passing**.
- **Scope:** evidence/auditability only. No attack, defense, ranking, or metric
  behavior changed. C1 was deliberately **not** re-run for this change.
- **Effect on manuscript claims:** configurations across V2 runs are now
  comparable by fingerprint, so tables can state that runs shared an identical
  configuration rather than asserting it informally.
- **Artifacts labeled:** `results_v2_frozen/PROVENANCE.md` now marks
  `…cfg-cc32b7ff…` **superseded** (injected-delta defect, delta recoverable) and
  `…cfg-0d4c5af3…` **accepted** (with an explicit note that it predates this fix,
  so its config_hash includes the temp DB path while all scientific artifacts and
  checksums remain valid). Neither bundle was modified.
- **Remaining dependencies:** none for L1. `attack_tagged_records_after` stays a
  diagnostic cross-check, not an invariant — it legitimately diverges from
  `injected_records` for overwrite-style scenarios (e.g. S02 fact corruption).

## E11 · L2 planning-mode evidence wiring + metric integrity (retroactive entry)
- **WP item:** WP1 — foundation (planner-stage evidence).
- **Commit:** `9ab42d97008aa0813a3a82fe202d07385f18f29d` (batch **B11**).
- **Process note:** this entry is **retroactive**. Batch B11 was committed without
  its execution-log entry, breaking the convention that a task is not complete
  until its entry exists in the same commit. Recorded here for completeness; the
  convention stands.
- **Problem fixed:** planning mode (L2) produced no evidence bundle at all, and
  its outcome handling conflated infrastructure faults with planner behaviour:
  a parse failure was swallowed (`except: plan_json = {}`), there was no timeout,
  the true raw model response was discarded (only the re-serialized plan was
  kept), and `save_aggregate` averaged the legacy `cognitive_hijack` boolean over
  ALL runs so a parse error/timeout counted as a clean non-adoption (e.g. 0.33
  instead of 1.0).
- **RAID concern addressed:** **452B** (overclaiming / metric integrity — planner
  rates must not be deflated by infrastructure failures) and **452C** (planner
  adoption evidence for the signed-insider cases).
- **Files / tests / evidence:** new `uavsys/evidence/planner.py` (pure
  classification; infrastructure outcomes return null behavioural fields;
  success-with-no-parseable-plan downgrades to `parse_error`; attempted vs
  valid_plan denominators). `resolve_model_identity()` in `ollama_client.py`
  (requested vs actually-invoked model, provider, seed_control — `claude-*` is
  served by `claude-sonnet-4-6`; commercial providers get no seed).
  `experiment_runner.py`: L2 bundle wiring with true memory timepoints and
  failure finalization; `asyncio.wait_for` timeout; provider-failure/timeout
  classification; records exact planner messages, UNMODIFIED raw output, parsed
  actions; behavioural aggregation restricted to valid-plan runs plus a new
  `planner` block (attempted_runs, valid_plan_runs, outcome counts, null-when-no
  -valid-plan rates). `provider_failure` added to `ABORTED_OUTCOMES`. Spec gains
  two constraints (C4/C5 signing-capable requirement; L2 claim boundary).
  Tests: `test_planner_evidence.py` (18), `test_runner_planning_evidence.py` (6),
  `test_planner_aggregation.py` (5) — 120 total.
- **Effect on manuscript claims:** planner adoption/refusal rates are now
  computed over honest denominators and traceable to the exact prompt and raw
  response. L2 supports adoption/refusal claims only — never trajectory or
  physical impact.
- **Remaining dependencies:** local model digest capture (FD2); L2 retrieval
  score components (fixed in E12).

## E12 · L2 retrieval score components + bundle bookkeeping correction
- **WP item:** WP1 — foundation (evidence parity and record accuracy).
- **Commit:** `f3b58d4ba25882608a284bfc07215cfc9c1b5509` (batch **B12**; hash
  backfilled by the E13 commit, per the no-amend convention).
- **Problem fixed:** (a) the L2 `retrieval_trace.jsonl` carried `score` but not the
  `relevance`/`recency`/`importance` breakdown that L1 bundles carry — planning
  mode builds `retrieval_items` from a separate code path that was not updated
  when the components were added to retrieval mode; found during the C0 L2 smoke.
  (b) The bundle count reported after that smoke was wrong ("nine accepted"),
  and the C0 L1 entry had never been explicitly labeled ACCEPTED.
- **RAID concern addressed:** — (evidence parity across layers and accurate
  artifact bookkeeping; underpins **452A/452B** reproducibility claims).
- **Files / tests / evidence:** `experiments/experiment_runner.py` — planning-mode
  `retrieval_items` now carries the three engine-computed components, matching the
  L1 format. `tests/test_runner_planning_evidence.py` — new test asserting EVERY
  L2 retrieved item preserves all three components with values carried through
  unchanged (fake retrieval now returns two items so the check covers every item,
  not just the first). Full suite: **121 passing**.
  `results_v2_frozen/PROVENANCE.md` — added an authoritative **bundle inventory
  table**: 8 directories = 7 accepted (6 × L1 + 1 × L2) + 1 preserved-superseded;
  every directory listed; C0 L1 explicitly labeled ACCEPTED.
- **Scope:** evidence-only. No retrieval, ranking, planner, attack, metric, or
  defense behavior changed. C0 was NOT re-run — the existing C0 L2 bundle keeps
  its documented score-component gap and remains valid.
- **Remaining dependencies:** none for L2 parity.

## E13 · Namespace crosswalk + mission/profile/outcome foundation (WP3a start)
- **WP item:** WP3a — G1/G2 foundation (mission registry, memory profiles, outcome detectors).
- **Commit:** `SELF` (batch **B13**; hash backfilled by the next docs-touching commit, no amend).
- **What shipped:**
  1. **Namespace hygiene (docs/draft-spec only).** Four namespaces fixed —
     missions **M1-M4**, frozen cases **C0-C6**, legacy aliases **Sxx/B0**,
     variants **MV*** — with the authoritative C0-C6<->legacy map, the run-identity
     schema (`mission x case|variant x profile x layer x model x seed x defense`),
     and an applicability matrix. New `docs/TAXONOMY_CROSSWALK.md`; the draft spec
     gains `namespaces`/`legacy_alias_map`/`missions`/`variants`/`identity_schema`/
     `applicability`. **Naming conflict resolved:** variants renamed V1-V3 ->
     `MV1_FALSE_CLEARANCE` / `MV2_FALSE_SAFETY` / `MV3_TARGET_RELOCATION` to avoid
     the project-version token `V2`. C0-C6 and all legacy aliases unchanged; spec
     stays `status: draft`.
  2. **Config-driven mission registry** `uavsys/missions.py` (M1-M3; M4 declared,
     not implemented). `Mission`/`Target`/`NoFlyZone` dataclasses. M1 objective is
     byte-identical to `experiment_runner.MISSION_GOAL` (backward compat);
     M2 = 6-target survey (enables MV1); M3 = a GENUINE no-fly zone the clean
     planner must respect, with the target outside it (enables MV2).
  3. **Deterministic memory-profile builder** `uavsys/memory_profiles.py`
     (P1 sparse = the observed 3-record baseline; P2 operational = 60-record
     mixture). Seeded RNG -> reproducible; no DB writes.
  4. **Pre-registered outcome detectors** `uavsys/evidence/outcomes.py`:
     `target_omission()` (MV1; nearest-target-within-radius, because person/car are
     ~3 m apart) and `unsafe_entry()` (MV2; genuine-NFZ breach), plus
     `extract_waypoints`/`haversine_m`.
- **RAID concern addressed:** **452A** (mission diversity + richer outcome taxonomy;
  new availability/safety failure modes as mission variants, not new cases).
- **Tests:** `tests/test_missions.py`, `tests/test_memory_profiles.py`,
  `tests/test_outcomes.py` (24 new, hermetic — no DB/LLM/PX4). Full suite: **145**.
- **Backward compatibility:** additive only. No existing runtime module changed
  (`experiments/`, `uavsys/memory/`, `uavsys/utils/`, `uavsys/llm/`, `seeding.py`,
  `attacks/` untouched); all prior bundles and behavior unaffected.
- **Scope:** no experiments run; registry not yet wired into the run loops (that is
  a later batch). The rule baseline is deliberately NOT part of this batch — it is
  not a dependency for the M1-M3 / P1-P2 / MV1-MV2 foundation.

<!-- New entries appended below as part of each implementation commit. -->
