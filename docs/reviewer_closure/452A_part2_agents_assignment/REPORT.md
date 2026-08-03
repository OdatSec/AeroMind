# Reviewer 452A — Part 2 (Agent-Count & Task-Assignment): Closure Report

**Status: CLOSED for the tested envelope** — L3 logical retrieval exposure, MEM060_OPERATIONAL,
top-k = 3, poison budget = 3, D0, T01_SEARCH_RESCUE, scouts ∈ {2, 4, 8, 16} + exactly one
Supervisor (total agents {3, 5, 9, 17}), assignment ∈ {fixed, random, dynamic}, seeds 101–110.

**Result: assignment-invariant logical retrieval exposure.** Varying the number of agents and the
task-assignment policy does **not** change the exposure outcome — every non-compromised scout and
the supervisor retrieve the poison in all 12 fleet×policy cells. This is the preserved/null
assignment effect the pre-registration explicitly permits; it was **not** tuned or forced.

Evidence: **240 accepted production runs** (120 A01 + 120 A00 controls). Accept-gate PASS
(0 problems). Raw bundles under `results_v3_raw/` (git-ignored); exact paths + hashes in
`PROVENANCE.md`.

---

## 1. Reviewer concern (452A, agent-count / task-assignment)
> "The attack is on a single multi-agent scenario with fixed task assignment; vary the number of
> agents and the task assignment."

## 2. Old paper — evidence & claim
A single multi-agent configuration with one fixed task partition. No variation of fleet size or of
how subtasks are assigned to agents; no measurement of how exposure scales with either.

## 3. Pre-registered design (frozen BEFORE any run)
- **Spec:** `docs/preregistration/PREREG_452A_part2_agents_assignment.md` — sha256
  `f2314da5…86cc0` (recorded in every bundle's `configured.prereg_spec_hash`).
- **Neutral hypothesis:** assignment policy MAY increase, preserve, or reduce cross-scout exposure;
  direction and magnitude are determined empirically; no policy is pre-declared superior.
- **Poison-blind assignment:** the map = f(policy, scout_count, seed, CLEAN pre-injection state)
  only; the **same** map is used for A00 and A01 at a cell (proved by test + verified in the
  accept-gate). The compromised writer (Scout 0) poisons the attacked subtask **after** the map is
  frozen.
- **Attacked-subtask schedule:** `attacked_subtask(seed)` is frozen and **identical across all
  three policies and both arms**, removing the S1 confound (dynamic's clean-state priority is
  independent of the attacked subtask; alignment is incidental, seed 101 only).
- **Manipulation checks vs outcomes:** query-opportunity and coverage are manipulation checks (they
  confirm assignment actually varied), reported **separately** from the empirical exposure outcomes.
- **Scope (pre-declared):** logical retrieval exposure only — embedder-only, no chat model, no
  planner, no PX4.

## 4. What was run
240 embedder-only L3 runs at the frozen operating point: A01_FALSE_OBSERVATION (budget 3) +
A00_CLEAN control (budget 0), × scouts{2,4,8,16} × assignment{fixed,random,dynamic} × seeds 101–110
= 4 × 3 × 2 × 10. All from a single clean commit `4aca513`.

## 5. Empirical outcomes (A01) — the fleet-size × assignment table
CIs = seed-as-unit percentile bootstrap (PROVISIONAL, pending Dr. Qian). `[1.0,1.0]` = every one of
the 10 seeds returned exactly 1.0 (degenerate → min,max).

| scouts | total | policy | cross-scout exposure | blast fraction | blast count | supervisor rate | A00 control blast |
|--:|--:|:--|:--:|:--:|:--:|:--:|:--:|
| 2 | 3 | fixed | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 3 | 1.0 | 0.0 |
| 2 | 3 | random | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 3 | 1.0 | 0.0 |
| 2 | 3 | dynamic | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 3 | 1.0 | 0.0 |
| 4 | 5 | fixed | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 5 | 1.0 | 0.0 |
| 4 | 5 | random | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 5 | 1.0 | 0.0 |
| 4 | 5 | dynamic | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 5 | 1.0 | 0.0 |
| 8 | 9 | fixed | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 9 | 1.0 | 0.0 |
| 8 | 9 | random | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 9 | 1.0 | 0.0 |
| 8 | 9 | dynamic | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 9 | 1.0 | 0.0 |
| 16 | 17 | fixed | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 17 | 1.0 | 0.0 |
| 16 | 17 | random | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 17 | 1.0 | 0.0 |
| 16 | 17 | dynamic | 1.0 [1.0,1.0] | 1.0 [1.0,1.0] | 17 | 1.0 | 0.0 |

## 6. Manipulation checks (by construction — NOT attack-effectiveness), reported separately
| scouts | policy | query-opportunity fraction | assignment coverage |
|--:|:--|:--:|:--:|
| 2 | fixed / random / dynamic | 0.500 / 0.500 / 0.550 | 1.0 / 1.0 / 0.9375 |
| 4 | fixed / random / dynamic | 0.250 / 0.250 / 0.275 | 1.0 / 1.0 / 0.9375 |
| 8 | fixed / random / dynamic | 0.125 / 0.125 / 0.125 | 1.0 / 1.0 / 0.9375 |
| 16 | fixed / random / dynamic | 0.0625 / 0.0625 / 0.0625 | 1.0 / 1.0 / 0.9375 |

These confirm the design genuinely varied assignment: the fraction of scouts **directly assigned**
the attacked subtask halves with every fleet doubling (≈ 1/scout_count under fixed/random; slightly
higher for dynamic, which replicates the priority subtask; the seed-101 alignment is incidental),
and dynamic drops coverage to 15/16. The exposure outcome (§5) is nonetheless invariant.

## 7. Interpretation (scoped)
Under the tested **MEM060 / top-k=3 / budget=3** operating point, logical retrieval exposure is
**assignment-invariant**. Even as the fraction of scouts directly tasked with the attacked subtask
shrinks toward 0.06 at 16 scouts, **every** non-compromised scout and the supervisor still retrieve
the poison, because retrieval over shared memory is not bounded by task assignment. The absolute
blast **count** scales with the fleet (3→5→9→17) while the **fraction** stays 1.0. Task partitioning
(fixed/random/dynamic) does not contain a single poisoned shared-memory record. The A00 clean
control is 0.0 in every cell, so the effect is real, not an artifact of the harness.

This is a genuine, on-thesis finding: the shared memory plane — not any particular agent assignment —
is the vulnerability. It directly answers the reviewer's "vary agents and assignment" concern with a
measured, assignment-independent result rather than a single fixed configuration.

## 8. Supporting negative diagnostic (provenance only)
A subtask-local payload variant, `A01_FALSE_OBSERVATION_LOCAL`, was implemented and frozen
(`uavsys/l3/attacks.py`, commit `993d3e2`) and evaluated on **development seeds 9001–9003** (disjoint
from production 101–110) to test whether the invariance was an artifact of a globally-relevant
payload. It is **not** — the local variant also saturates off-target queries (see
`SPECIFICITY_DIAGNOSTIC_A01_LOCAL.md`). This confirms the invariance is a property of shared-memory
retrieval under MEM060, not of the specific payload. `A01_LOCAL` is retained **only** as this
documented negative diagnostic; it is **not** in production, the paper taxonomy, or any main claim.

## 9. Scope limitations (explicit — what this closure does NOT claim)
- **Single operating point.** top-k = 3, budget = 3, MEM060_OPERATIONAL only. The invariance is
  established for this envelope; other k/budget/memory points are not claimed here.
- **Partly a property of the benign memory composition.** MEM060 carries no sector-competitive
  benign content, so a coherent poison out-ranks the generic background for every sector query.
  Whether a sector-structured memory would let assignment modulate exposure is a separate design
  question, deliberately NOT pursued (no memory redesign to force a result).
- **Logical retrieval exposure ONLY.** No claim about planner coordinate-adoption (L2), mission
  failure, physical/actuation propagation, or any external system. Exposure = "the poison appears in
  an agent's top-k retrieval," nothing downstream.
- **CIs PROVISIONAL** pending Dr. Qian's statistical-method sign-off.
- **Supervisor exposure** is reported as an assignment-independent binary rate (§5), consistent with
  the pre-registration; it is not part of the cross-scout denominator.

## 10. Reproduce
```
python3 experiments/campaign_452a_part2.py --audit
```
Deterministic (bootstrap seeded `random.Random(0)`); regenerates
`results_v3_campaigns/452A_part2_agents_assignment/campaign_summary.json` byte-identically
(sha256 `29c8ea12…dee0`). Reads only production bundles; runs no experiments.
