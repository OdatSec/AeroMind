# 452A Part 2 — Claim → Evidence map

Every claim links to accepted production evidence (raw paths + hashes in `PROVENANCE.md`).
CIs are seed-as-unit percentile bootstrap, **PROVISIONAL pending Dr. Qian's review**.

| # | Claim | Evidence | Metric / value |
|---|---|---|---|
| C1 | Fleet size and assignment policy were genuinely varied (not relabeled). | `uavsys/l3/assignment.py`; `tests/test_l3_452a_part2.py`; manipulation checks | opportunity fraction 0.5→0.25→0.125→0.0625 across scouts{2,4,8,16}; fixed≠random blocks; dynamic coverage 15/16 |
| C2 | Assignment is poison-blind: identical map for A00 and A01 at every cell. | accept-gate map-equality check over all 120 cell/seed pairs | 0 mismatches (240/240) |
| C3 | The attacked-subtask schedule is policy-independent (S1 confound removed). | accept-gate schedule-invariance check | attacked_subtask identical across {fixed,random,dynamic} per seed |
| C4 | Cross-scout exposure is **invariant** to fleet size and assignment policy. | 120 A01 runs (12 cells × 10 seeds) | cross-scout exposure = 1.0 [1.0,1.0] in all 12 cells |
| C5 | Blast radius is the full fleet regardless of policy; absolute count scales with fleet. | 120 A01 runs | blast fraction 1.0 [1.0,1.0]; blast count 3/5/9/17 by fleet |
| C6 | Off-target (non-assigned) scouts are still exposed — assignment does not contain the poison. | opportunity fraction << 1 while cross-scout exposure = 1.0 | e.g. 16 scouts: 0.0625 tasked, 1.0 exposed |
| C7 | Supervisor exposure is assignment-independent. | 120 A01 runs | supervisor exposure rate = 1.0 in all cells (reported separately) |
| C8 | Controls behave correctly (no false positives). | 120 A00 runs | blast fraction = 0.0 in all 12 cells |
| C9 | The invariance is not an artifact of a globally-relevant payload. | `SPECIFICITY_DIAGNOSTIC_A01_LOCAL.md`; frozen `A01_LOCAL` (commit 993d3e2), dev seeds 9001–9003 | subtask-local payload also saturates off-target (12/12 in top-3) |

## Headline claim (scoped)
> Under MEM060_OPERATIONAL, top-k = 3, budget = 3, logical retrieval exposure to a single poisoned
> shared-memory record is **assignment-invariant**: cross-scout exposure = 1.0 and blast radius =
> full fleet for scouts {2,4,8,16} × assignment {fixed,random,dynamic}, n = 10 seeds/cell, with the
> A00 clean control at 0.0. Task partitioning does not contain the poison.

## Out of scope (NOT claimed here)
- **Planner coordinate-adoption (L2)**, mission failure, physical/actuation propagation, external
  systems — no claim; the metric is retrieval exposure only.
- **Other operating points** — k ≠ 3, budget ≠ 3, and memory profiles other than MEM060 are not
  evaluated here; the invariance is asserted only for the tested envelope.
- **A memory profile engineered to let assignment modulate exposure** — deliberately not built (no
  redesign to force an assignment-dependent result). The observed saturation is partly a property of
  MEM060's (non-sector-competitive) benign composition; this is stated, not hidden.
- **A01_FALSE_OBSERVATION_LOCAL as an attack** — retained only as a negative specificity diagnostic;
  not in production, the paper taxonomy, or the main claims.
- **Write-path practicality of the injection** (452B second objection) — handled elsewhere (A04–A06
  + capability table).
