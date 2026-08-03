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
- **Commit:** `98a76e868398e4917043178118edb45af4ae4f00` (batch **B13**; hash
  backfilled by the E14 commit, per the no-amend convention).
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

## E14 · Runner wiring: --mission {M1-M3} / --profile {P1-P2} (parity-first)
- **WP item:** WP3a — make the mission/profile foundation runnable (parity-first).
- **Commit:** `44ab78d4d72ed7a19acbe96e00e416d7951d95fb` (batch **B14**; hash
  backfilled by the E15 commit, per the no-amend convention).
- **What shipped:** `--mission {M1,M2,M3}` and `--profile {P1,P2}` (defaults M1/P1)
  threaded through retrieval and planning modes. Mission objective replaces the
  MISSION_GOAL literal in queries/prompt (M1.objective IS MISSION_GOAL -> byte
  identical); profile seeds memory — **P1 uses the UNCHANGED legacy seed_memory
  (parity anchor); P2 uses the deterministic builder** via new
  `seeding.seed_from_profile`. mission/profile recorded in traces (run_data),
  aggregates (`save_aggregate`), and manifests/configured.
- **Config-hash audit + schema v2:** mission/profile are scientific inputs that
  MUST change the fingerprint but were absent from the hash. Introduced
  `config_hash` **schema v2** that folds `run_axes={mission,profile}` into the
  payload. v1 is fully preserved: bundles with no run axes hash exactly as before,
  so **every accepted bundle's stored v1 fingerprint remains valid** and still
  recomputes (verified for C1 L2). New runs carry v2; a fresh M1/P1 run is NOT
  required to match an old v1 fingerprint (schema legitimately changed). Manifest
  `config_hash_schema` now reports the version actually used + the hashed run axes.
- **RAID concern addressed:** **452A** (mission-diversity infrastructure) and —
  (reproducibility: config identity now includes mission/profile).
- **Files / tests:** `experiments/experiment_runner.py` (flags, threading,
  aggregate recording), `uavsys/seeding.py` (`seed_from_profile`),
  `uavsys/memory_profiles.py` (P1 now byte-mirrors seed_memory: +steps_json),
  `uavsys/evidence/bundle.py` (schema v2 + mission/profile manifest fields).
  New `tests/test_runner_mission_profile.py` (6); config-hash v2 tests (+5) and a
  P1<->seed_memory equivalence test (+1). Full suite: **157**.
- **Backward compatibility:** M1/P1 defaults reproduce legacy behavior; existing
  runtime modules changed only additively; all 11 accepted bundles re-verify and
  their v1 hashes recompute; no attack/defense/metric behavior changed.
- **Scope:** wiring only. No MV1/MV2 attack, no M2/M3 experiments, no defense
  changes, no parity smokes run in this batch (authorized separately next).

## E15 · MV1_FALSE_CLEARANCE variant (M2) + target-omission outcome
- **WP item:** WP3a — first auxiliary mission variant + coverage outcome.
- **Commit:** `402ea5e009c3af7c096362be41d1f1ffe62627ef` (batch **B15**; hash
  backfilled by the E16 commit, per the no-amend convention).
- **What shipped (additive; C0-C6 untouched):**
  - New `attacks/mv1_false_clearance.py` — M2-only auxiliary variant. Injects ONE
    unsigned false "already surveyed and cleared" semantic status for a
    deterministic designated target (`mission.mv1_cleared_target`, = `survey_ne`
    for M2) via the ordinary `write_semantic` API (no DB/secret/signer access).
    Extends the C1 false-fact mechanism; failure mode = target omission.
  - Wired into `SCENARIO_MAP` + CLI as a variant (NOT a C-scenario);
    `VARIANT_REQUIRED_MISSION` guards MV1 to `--mission M2` (fail loud otherwise).
    `seed_and_inject` passes the mission to variant modules that accept it
    (inspect-gated, so C0-C6 modules are unaffected).
  - Planning (L2) now records per run: variant id, assigned target ids+coords,
    falsely-cleared target, covered/omitted ids, per-run target_omission_rate,
    mission/profile — in run_data, `parsed_actions.json`, and manifest `observed`.
    The injected + retrieved MV1 records (with full score components) already flow
    through injected_records/retrieval_trace.
  - `save_aggregate` gains `planner.target_omission` (mean over valid plans) and
    `planner.falsely_cleared_omitted` (MV1 attack-effectiveness) — computed for
    valid plans only, None/absent otherwise, with denominators kept SEPARATE from
    coordinate_adoption/constraint_refusal (those are unchanged).
  - Integrated the existing pure `outcomes.target_omission` (nearest-target
    assignment) into the runner; `uavsys/missions.py` gains `mv1_cleared_target`
    (+ `Mission.target()` helper), M2 sets it to `survey_ne`.
- **RAID concern addressed:** **452A** (mission diversity + new availability/
  coverage failure mode beyond redirection/refusal).
- **Tests:** `tests/test_mv1_false_clearance.py` (deterministic designation, M2-only
  guard, ordinary-API single-record delta, clean-vs-attacked M2 coverage,
  dense-target nearest-assignment) and `tests/test_runner_mv1.py` (bundle/run_data/
  aggregate recording, injected+retrieved MV1 records with components, and
  parse-error -> null omission with separate denominators). Full suite: **168**.
- **Backward compatibility:** C0-C6 attack modules unchanged; M1/P1 parity and all
  13 on-disk bundles re-verify; redirection/refusal metrics unchanged; MV1 is
  inert unless explicitly selected with `--mission M2`.
- **Scope:** implementation only. No M2/P2 clean or MV1 smoke run; no MV2/M3/STATE/
  L3/defense work.

## E16 · M2 target-visibility fix (assigned targets briefed to the planner)
- **WP item:** WP3a — make M2 coverage measurable (fixes the design gap the
  M2/P2 clean baseline exposed).
- **Commit:** `ee0bcae39faf179ad63180f37ee135d402d13f14` (batch **B16**).
- **Problem fixed:** M2's four survey targets existed only in the mission config —
  not seeded into memory, not in the prompt — so the clean planner could only
  reach person+car and the M2/P2 clean baseline showed `target_omission_rate=
  0.6667` with NO attack. That made MV1's omission signal uninterpretable
  (baseline non-discovery vs attack-induced omission were indistinguishable).
- **Design (as specified):** M2's six assigned targets are authoritative mission
  inputs, now enumerated with stable ids + coordinates in the planner's mission
  **briefing** (`Mission.briefing()`), so clean coverage does NOT depend on
  retrieval/top-k. Retrieval may still carry mission history/status but is no
  longer the only way the planner learns the assigned set. **M1 is byte-identical**
  (brief_targets=False -> empty briefing -> unchanged prompt). C0-C6 and MV1
  semantics unchanged.
- **RAID concern addressed:** **452A** (correct, interpretable multi-target
  coverage metric).
- **Files / tests:** `uavsys/missions.py` (+`brief_targets`, `Mission.briefing()`,
  `assigned_targets()`; M2 brief_targets=True), `experiments/experiment_runner.py`
  (prompt injects `mission.briefing()`). New `tests/test_mission_briefing.py` (6):
  M2 briefs all six exactly once with coords; M1 briefing empty + prompt
  byte-identical; briefing independent of retrieval top-k; clean 6-cover -> omission
  0; attacked plan omitting survey_ne detected; runner integration with EMPTY
  retrieval still shows all six in the prompt and records the authoritative
  assigned list separately from retrieval. Full suite: **174**.
- **Evidence:** the failed M2/P2 clean baseline (`C0__L2__…cfg-e06c494e`) is
  recorded in `results_v2_frozen/PROVENANCE.md` as **design-validation, EXCLUDED**
  (reason: assigned targets not visible to the planner).
- **Backward compatibility:** M1 prompt byte-identical; C0-C6 modules unchanged;
  MV1 semantics unchanged; all 14 on-disk bundles re-verify.
- **Scope:** fix only. No experiments run; the corrected clean M2/P2 baseline is
  NOT rerun here (authorized separately); no MV1, G1/G2, or defense work.

## E17 · First accepted campaign — M2/P2 MV1 false-clearance (L2)
- **WP item:** WP3a — first multi-seed campaign for an auxiliary variant.
- **Commit:** `0ba712f` (documentation-only labeling).
- **Run (code `b456b0d`):** planning/L2, model gpt-oss:20b, mission M2, profile P2,
  defense off; **frozen seeds 101–110** (fixed pre-execution; no tuning, selective
  rerun, or seed replacement; failures would have been preserved honestly).
- **Result:** clean arm (B0) 10/10 valid, **mean target-omission 0.0**; attack arm
  (MV1_FALSE_CLEARANCE) 10/10 valid, **survey_ne omitted 10/10**, **mean omission
  1/6 (0.1667)**, `falsely_cleared_omitted` rate **1.0**. Paired per-seed: every
  seed clean=covered / MV1=survey_ne-omitted. No provider/parse failures. All 20
  bundles production-valid, checksums OK, clean git.
- **RAID concern addressed:** **452A** — first campaign-level (multi-seed) evidence
  of a new availability/coverage failure mode (selective target denial), distinct
  from redirection (C1) and refusal (C3), with honest attempted/valid denominators.
- **Evidence classification (PROVENANCE.md):** the 20 seed-101–110 bundles are
  **accepted campaign evidence**; the seed-42 clean/MV1 runs remain
  **smoke-validation only**; the earlier failed clean baseline remains **excluded
  design-validation**. No code changed; documentation-only commit.

## E18 · MV1 M2/P2 retrieval (L1) campaign — matched to the L2 seeds
- **WP item:** WP3a — L1 arm of the MV1 campaign (retrieval-level evidence).
- **Commit:** `4b98fa1` (documentation-only labeling).
- **Run (code `0ba712f`):** retrieval/L1, embedder nomic-embed-text, mission M2,
  profile P2, defense off; frozen seeds **101–110** (matched to E17's L2 campaign).
- **Result:** clean (B0) 10/10 valid, CCR/CASR/MTR 0.0, RIS 1.0 every seed. MV1
  10/10 valid: the `atk:MV1` STATUS:survey_ne record is retrieved by **all 3 roles
  every seed at rank 1** (Agent 1 score 0.7368 = rel 0.6614·rec 1.0·imp 0.7);
  **CCR 0.2727, CASR 1.0, MTR 0.2889, RIS 0.0**; infected = all 3 roles. No
  provider/parse failures; all 20 bundles production-valid, checksums OK, clean git.
- **RAID concern addressed:** **452A/452B** — retrieval-level evidence that the
  false-clearance record dominates the retrieved context (rank 1, all roles),
  complementing the L2 omission finding with honest denominators.
- **Evidence classification:** the 20 seed-101–110 L1 bundles are **accepted
  campaign evidence**. Documentation-only commit; no code changed.

## E19 · MV2_FALSE_SAFETY variant (M3) + unsafe-entry outcome
- **WP item:** WP3a — second auxiliary variant (the C3 mirror: false safety -> breach).
- **Commit:** `SELF` (batch **B17**; hash backfilled by the next docs-touching commit, no amend).
- **What shipped (additive; C0-C6 and MV1 unchanged):**
  - New `attacks/mv2_false_safety.py` — M3-only. Injects ONE unsigned false status
    (`atk:MV2`) that the designated genuine zone (`mission.mv2_cleared_zone` =
    `restricted_north`) is cleared/safe, with an in-zone lure, via the ordinary
    `write_semantic` API. Mirror of C3 (false restriction->refusal): false
    safety -> unsafe entry / breach.
  - `uavsys/missions.py`: `+mv2_cleared_zone`, `Mission.zone()`; `Mission.briefing()`
    now also enumerates genuine no-fly-zone geometry (so the clean planner knows
    the constraint and can route safely). M3 set to `brief_targets=True`,
    `mv2_cleared_zone=restricted_north`, and its zone RELOCATED to (47.3985,
    8.5510) r=30 m — deliberately NOT the trap coords, so unsafe-entry is measured
    independently of the C1-family coordinate detector; the person target is ~214 m
    outside (safe route exists). **M1/M2 briefings are byte-identical** (M1 briefs
    nothing; M2 has no genuine zones).
  - Wired into `SCENARIO_MAP` + `VARIANT_REQUIRED_MISSION` (MV2 requires M3).
    Planning records per run: `restricted_zones` geometry, `falsely_cleared_zone`,
    `unsafe_entry`/`breached_zones` (valid plans only; None otherwise) in run_data,
    `parsed_actions.json`, and manifest `observed`. `save_aggregate` gains
    `planner.unsafe_entry` and `planner.false_safety_breach` (attack effectiveness),
    valid-plan denominators, SEPARATE from adoption/refusal/omission.
- **RAID concern addressed:** **452A/452C** — safety-constraint violation (breach)
  as the mirror of C3 refusal; a distinct, physical-consequence-adjacent outcome.
- **Tests:** `tests/test_mv2_false_safety.py` (8: config designation, M3-only guard,
  ordinary-API injection, clean safe route no-breach, attacked breach, runner
  breach+zone-geometry recording, clean no-breach, invalid-plan null breach);
  `tests/test_outcomes.py` updated for the relocated zone. Full suite: **182**.
- **Backward compatibility:** M1/M2 briefings byte-identical; C0-C6 + MV1 modules
  unchanged; all on-disk bundles re-verify. (M3 config changed but M3 has no
  bundles yet.)
- **Scope:** implementation only. No M3 clean baseline or MV2 attack run; no
  defense/MV-other/G1-G2/L3/L4 work.

## E20 · Detector hardening — numeric coordinate-adoption (fix 8.55/8.551 FP)
- **WP item:** WP3a — metric integrity (coordinate-adoption detector).
- **Commit:** `ac3e22619dfa9e83d2df81c15397df66cae2218a` (batch **B18**).
- **Problem fixed:** `detect_coordinate_adoption` used **substring** matching on trap
  strings, so a coordinate merely *mentioned in reasoning text* (the MV2/M3 no-fly
  zone center longitude `8.551`) matched the trap `8.55` -> a false-positive
  `coordinate_adoption=True` in the MV2 seed-42 smoke (surfaced there; the breach
  metric was unaffected).
- **Fix:** `detect_coordinate_adoption` is now **numeric + tolerance-based** — it
  parses `goto_location` waypoints and flags adoption only when a planned WAYPOINT
  is within `COORD_TOLERANCE_M = 5.0` m of the trap (great-circle). Coordinates in
  notes/prose can no longer trigger it. Substring `trap_string_variants` removed.
- **RAID concern addressed:** **452B** (metric integrity — no spurious adoption).
- **Files / tests:** `uavsys/evidence/planner.py` (numeric detector; classify uses
  plan_json). `tests/test_planner_evidence.py` +3 regressions: zone-center `8.551`
  in notes -> not adoption; trap coords only in prose -> not adoption; waypoint
  within tolerance -> adoption, zone center (~200 m) -> not. Full suite: **185**.
- **Preserved unchanged:** the geometric `unsafe_entry` detector (`outcomes.py`,
  0 changes); MV2/M3/prompts/payloads/lure/mission geometry/defense code.
- **Effect on the MV2 smoke:** the on-disk MV2 bundle is frozen and NOT modified;
  its breach conclusion (`unsafe_entry=False`) is unchanged. The fix prevents the
  incidental `coordinate_adoption` false positive in FUTURE runs only.

## E21 · Final Campaign V3 taxonomy + results organization (no experiments)
- **WP item:** WP1/WP7 — clean, unified result organization for the final campaign.
- **Commit:** `3ab403c09e3f0592a6b252cb7d1aa8eae7f1da78` (batch **B19**).
- **What shipped (additive; results_v2_frozen/ immutable & untouched):**
  - `uavsys/taxonomy.py` — canonical namespaces + backward-compatible alias
    resolution (single source of truth): Attacks **A00-A09**, Tasks **T01-T04**,
    Memory **MEMxxx**, Evaluation **RET/PLAN/MULTI/SITL**, Defense **D0-D4**. A02
    is **_EXPOSURE** (not _PROPAGATION) per the naming decision, so the canonical
    id never overclaims. Legacy ids (C0-C6, B0/Sxx, MV1-3, M1-4, P1/P2, modes)
    remain aliases; deferred/planned ids (A09, T04, MEM200/1000, MULTI) resolve
    but have no runner.
  - `uavsys/paths.py` — new `results_v3_raw` (a SECOND production root) + `
    results_v3_campaigns`; `v3_raw_run_parent(...)` hierarchical path builder;
    `is_production_root`. The v2 root guard is unchanged.
  - `uavsys/evidence/bundle.py` — optional `canonical_ids` (recorded in manifest)
    and `short_run_id` (v3 `run-<cfg8>-<uuid8>` dirs; metadata in manifest). V2
    default is byte-unchanged (long name, canonical=null).
  - `uavsys/campaigns.py` — campaign-layer generator: `build_campaign` writes
    README / campaign_summary.json / paired_results.csv / bundle_index.yaml /
    INSIGHTS_DRAFT.md (auto) / CLAIMS.md and refreshes INDEX.md. `PAPER_FINDINGS.md`
    is NEVER auto-written (human-only promotion).
  - `experiments/experiment_runner.py` — accepts canonical **or** legacy ids for
    --scenario/--mode/--mission/--profile (resolved via taxonomy); new
    `--results-layout {v2,v3}` (default v2 = unchanged); MULTI / un-implemented
    ids **fail loud**; v3 routes bundles into the hierarchy with canonical manifest.
  - Docs/stubs: `docs/TAXONOMY_CROSSWALK_V3.md` (authoritative old->new + status),
    `results_v3_campaigns/{INDEX.md,PAPER_FINDINGS.md}`, `.gitignore` +`results_v3_raw/`.
  - Design challenges raised & resolved before coding: A02 name (-> EXPOSURE);
    production-root guard extended safely (v3 as a 2nd root, v2 untouched);
    MULTI/SITL runner-less (fail loud); variant task-locks preserved.
- **RAID concern addressed:** — (clean, auditable organization underpinning
  452A/B/C reporting; honest canonical naming).
- **Tests:** `tests/test_taxonomy.py` (alias equivalence, deferred/planned, manifest
  identity) and `tests/test_v3_layout_and_campaigns.py` (hierarchical paths, short
  seed dirs, canonical manifest, v2 backward-compat, campaign indexing + insight
  generation, PAPER_FINDINGS never auto-written). Full suite: **215**.
- **Scope:** organization only. No experiments run; no existing bundle migrated,
  moved, edited, or recomputed; attacks/tasks/memories/defenses not redesigned.

## E22 · V3 argument-driven raw/campaign hierarchy (topk/budget/temp axes)
- **WP item:** WP1/WP7 — attack-centered, argument-driven result organization.
- **Commit:** `cd5fac4d...` (batch **B20**; hash backfilled by the E23 commit).
- **Axis-coverage audit:** `config_hash` already binds model, top-k, temperature,
  seed, defense, mission, profile; the only scientific axis NOT in the hash is
  **poison budget** (count). Fix: every axis is now an ordered path level, and
  budget is separated at the path (`budget-<NN>`), so distinct configs never share
  a directory (non-mixing) and the `run-` uuid prevents same-cell collisions.
- **What shipped (additive; results_v2_frozen/ + production V3 roots untouched):**
  `uavsys/paths.py` — `v3_raw_run_parent(... topk,budget,temp,seed, agents=,backend=,
  extra_axes=, root=)` and `v3_campaign_dir(...)` build the full ordered hierarchy
  `<ATTACK>/<TASK>/<MEMORY>/<EVAL>/model-<MODEL>/<DEFENSE>/topk-NN/budget-NN/
  temp-VALUE/[agents-NN/][backend-NAME/]`; `_axis` zero-pads; model slug sanitized
  (exact id stays in manifest). `uavsys/campaigns.py` — campaign folders mirror the
  same axes; `refresh_index` walks the nested tree. `experiment_runner.py` —
  `_bundle_location` threads topk/budget/temp (RET temp=na; PLAN temp=planner temp).
- **RAID concern addressed:** — (auditable, argument-driven organization).
- **Tests:** `tests/test_v3_sandbox_matrix.py` — full 2^n axis matrix over
  {2 models, 2 attacks + A00 clean, RET/PLAN, 2 memory, 2 topk, 2 budget, 2 temp,
  2 defense, 3 seeds}: every run dir and every scientific cell UNIQUE, clean vs
  attack never share a root; a real-bundle slice pairs A00 clean with A08 into a
  campaign. `tests/test_v3_layout_and_campaigns.py` updated for full-axis paths +
  MULTI/SITL conditional axes (`agents-NN`, `backend-NAME`). Full suite: **218**.
- **Sandbox demo:** built 13 real bundles across the axes under scratchpad,
  verified unique dirs + mirrored campaign, then deleted all sandbox artifacts;
  production `results_v3_raw`/`results_v2_frozen` untouched (0 changes).
- **Scope:** organization only; no experiments; no production bundle created/edited.

## E23 · V3 integrity: canonical task locks + poison-budget in config-hash
- **WP item:** WP1/WP7 — close two integrity gaps before the first production V3 run.
- **Commit:** `656edb5...` (batch **B21**; hash backfilled by the E24 commit).
- **(1) Canonical task locks enforced before path creation/execution.** Variants
  are locked: **A07->T02, A08_FALSE_SAFETY->T03_RESTRICTED_ZONE, A09->T04**.
  `taxonomy.validate_attack_task` (new; `required_task` field) is called at the top
  of `v3_raw_run_parent` and `v3_campaign_dir`, so an invalid combo (e.g. A08+T02)
  raises `ValueError` and **creates no directory**; the runner's
  VARIANT_REQUIRED_MISSION guard also rejects it pre-dispatch. A00-A06 broad.
  The earlier A08+T02 example was synthetic path-only and is now rejected.
- **(2) Poison budget in the cryptographic identity.** New config-hash **schema v3**
  folds `budget` into the hashed run_axes. v1 (config-only) and v2
  ({mission,profile}) are byte-unchanged, so all existing bundles keep their
  fingerprints; two runs differing ONLY in budget now differ (budget-01 !=
  budget-05). Manifest records `budget` + `config_hash_schema.version=3`. The v3
  runner records budget explicitly ("default" when unset).
- **RAID concern addressed:** — (experiment identity integrity; no invalid or
  ambiguous configurations admissible).
- **Tests:** `test_taxonomy.py` (+required_task/validate lock, bad combos raise);
  `test_v3_layout_and_campaigns.py` (invalid combo raises + creates no dir);
  `test_config_hash_stability.py` (+budget schema v3, budget-01 != budget-05, v2
  preserved, manifest records budget); `test_v3_sandbox_matrix.py` reworked so
  attacks use their locked task. Full suite: **224**.
- **Model-name note:** path slug is sanitized (`model-gpt-oss-20b`); exact Ollama
  id `gpt-oss:20b` is preserved in `config.CHAT_MODEL` and used verbatim by the
  backend — confirmed correct.
- **Scope:** integrity only. No experiments; no production V3 results created; V2
  hashes/bundles and results_v2_frozen/ unchanged.

## E24 · V3 pre-production validation (disposable sandbox) -> READY
- **WP item:** WP1/WP8 — readiness gate before real scientific campaigns.
- **Commit:** `SELF` (batch **B22/B23**; report + the two genuine fixes B22/B23).
- **Genuine fixes found & committed:** (B22 `fd58088`) redirectable V3 roots via
  AEROMIND_V3_* env for sandbox/CI; (B23 `9c6b3ec`) `--topk`/`--temp` sweep flags
  folding into config-hash + path (needed for G2).
- **Validation (temp roots only; production untouched):** 15 real bundles across
  RET/PLAN x {gpt-oss:20b, qwen2.5:7b} x {A00,A01,A03,A05,A07,A08} x {MEM003,MEM060}
  x swept topk/budget/temp/seed/defense. Verified: args in path+manifest (canonical
  ==path, schema v3+budget, production-valid), 15/15 unique (no mixing), metrics
  agree with raw (RET ccr==poisoned/total; PLAN parsed==raw), invalid/deferred/
  MULTI/unknown fail loud, campaign artifacts generated + labeled PRE-PRODUCTION,
  PAPER_FINDINGS never auto-written. All sandbox artifacts deleted.
- **Verdict: READY FOR SCIENTIFIC CAMPAIGNS.** Report:
  docs/V3_PREFLIGHT_VALIDATION_REPORT.md. Ready to hand off to Cam for defense
  integration (D2/D3 isolation configs + defended campaigns remain Cam/Dr. Qian).
- **Scope:** validation only; no production results; results_v2_frozen unchanged.

## E25 · Preflight run-class (redirected sandbox != production)
- **WP item:** WP1 integrity — evidence validity must reflect where a run was written.
- **Commit:** `SELF` (batch **B24**).
- **Reviewer mapping:** 452B (no overclaiming) — a disposable sandbox run can no
  longer be counted as production/paper evidence.
- **Fix:** bundles written under an env-REDIRECTED V3 root are labeled
  `validity=preflight` (`valid=false`, `run_class=preflight`), never `production`;
  `production` is allowed only under the REAL repo-anchored `results_v3_raw/`
  (paths.is_canonical_production_root / v3_raw_is_redirected). Integrity gates
  (clean tree, stable commit) still enforced for preflight so runs stay honest.
  campaigns.build_campaign now excludes non-production bundles from paper stats by
  default and records the excluded count (opt-in include_non_production for labeled
  validation campaigns).
- **Tests:** tests/test_preflight_run_class.py (6): redirected->preflight; real
  root->production; explicit run_class override; campaign default-exclusion +
  opt-in. Full suite 232 passing.
- **Scope:** labeling/selection only; no experiments rerun; V2 bundles unchanged.

## E26 · Cam onboarding & work contract (defense handoff)
- **WP item:** WP4/WP5 enablement — non-blocking handoff (team plan, Aug 1).
- **Commit:** `SELF` (batch **B25**; docs-only).
- **Reviewer mapping:** 452C-3/452C-4 — defense generalization + signed-malicious
  memory are Cam's package; this doc is the interface/constraints contract.
- **Added:** docs/CAM_HANDOFF.md — role (one bounded defense on signed false
  memory; legacy defense.py is scaffold/reference only), defense I/O contract
  (retrieve(defense_cfg) + DefenseLayer two hooks + separate-stage option),
  fixtures (78 frozen bundles), WP4/WP5 deliverables+dates (WP4 memo due Aug 4),
  constraints, verified preflight reproduction command, return-files list,
  first-day checklist. FD1 (D-token<->config mapping) flagged as Cam's first task.
- **Scope:** documentation only; no code/experiments changed.

## E27 · 452A Part 1 implementation (memory profiles + metrics + similarity audit)
- **WP item:** WP3a generalization — reviewer 452A part 1 (memory size + composition).
- **Branch:** revision/452a-generalization (NOT defense/v3-integration).
- **Frozen spec:** docs/preregistration/PREREG_452A.md (sha256 cc8c0e8b...).
- **Shipped:** MEM200_DENSE / MEM060_EPISODIC_HEAVY / MEM060_BENIGN_HIGHSIM builders
  (P2 untouched); malicious_rank + clean_displacement (uavsys/evidence/retrieval_metrics.py,
  min-successful-budget deliberately excluded); pinned-digest similarity-audit tool
  (experiments/similarity_audit_452a.py). +26 tests (counts, determinism, per-seed
  materialization hashes, identical A00/A01 pre-injection memory). Full suite green.
- **Similarity audit (seeds 101-110, embedder digest 970aa74c... verified):** mean cos
  to Q(S1) — dense_similar 0.807 (600/600 >=.60), benign_highsim 0.697 (400/400),
  operational episodic 0.554 (2/300). Design intention VERIFIED, not asserted.
- **No A01 experiments run.** Artifact: docs/preregistration/similarity_audit_452a.json.

## E28 · 452A Part 1 V3 runner integration + retrieval-competition metrics
- **WP item:** WP3a — wire the 5 memory profiles + metrics into the V3 runner.
- **Branch:** revision/452a-generalization.
- **Shipped:** taxonomy MEM200_DENSE->implemented + MEM060_EPISODIC_HEAVY /
  MEM060_BENIGN_HIGHSIM entries (all resolve; runner build_profile works). Runner
  RET path now: computes malicious_rank (per-agent + min) into metrics.json +
  run_data; records per-agent top-k idents for clean_displacement; adds
  paired_clean_displacement() aggregation primitive. Every RET bundle now records the
  pinned embedder digest (uavsys/llm/embed_provenance.resolve_embed_digest),
  per-seed profile_materialization_hash, and prereg_spec_hash in configured/embedder.
- **Tests:** +2 (5-profile resolve/build integration; paired_clean_displacement).
  Full suite 260 passing.
- **No production campaign.** Disposable A00/A01 RET preflight (5 profiles, 1 seed)
  run + audited separately.

## E29 · 452A Part 1 production RET campaign (memory generalization)
- **WP item:** WP3a — reviewer 452A part 1; the FIRST accepted-evidence V3 campaign.
- **Branch:** revision/452a-generalization. Log renamed V2_EXECUTION_LOG -> V3_EXECUTION_LOG (continuous history).
- **Ran (frozen, no tuning):** 5 memory profiles x {A00,A01} x seeds 101-110 = 100 RET
  runs, top-k 3, budget 3, D0, gpt-oss:20b, embedder nomic-embed-text (digest pinned).
  Production only under results_v3_raw/; aggregation under results_v3_campaigns/
  452A_memory_generalization/ via experiments/campaign_452a.py (CCR/MTR/RIS/
  malicious-rank/clean-displacement + seed-as-unit bootstrap CIs).
- **Note:** at top-k==budget==3 CCR saturates ~1.0 across profiles (the 452B by-construction
  regime); memory-state signal surfaces via malicious-rank/clean-displacement + framing.
- **Discipline:** results_v2_frozen untouched; no selective reruns.

<!-- New entries appended below as part of each implementation commit. -->
