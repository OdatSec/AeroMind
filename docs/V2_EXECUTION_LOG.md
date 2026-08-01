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

<!-- New entries appended below as part of each implementation commit. -->
