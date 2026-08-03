# Reviewer 452B — top-k × poison-budget + planner adoption: Closure Report

**Concern (452B):** "supervisor retrieves 5, scout receives 3, attacker injects 3 high-overlap
poison ⇒ CCR may be 1 by construction; k-sensitivity shows attack effectiveness decreasing as k
increases."

**Status: CLOSED for the tested envelope** — RET (retrieval) k∈{3,5,10,20} × budget∈{1,2,3,5} +
the exact asymmetric scout3/sup5 baseline; PLAN (planner adoption) planner_k∈{3,5,10,20}. Memory
fixed = MEM060_OPERATIONAL, D0, seeds 101–110. Evidence: **170 accepted RET runs** (+40 reused
452A k=3) and **80 accepted PLAN runs**; accept-gate PASS on both. Raw bundles under
`results_v3_raw/` (git-ignored); paths + hashes in `PROVENANCE.md`.

---

## 1. Precise scope of the "saturation" concession
Only the **Scout retrieval CCR = 1 at k=3, budget=3 is saturated by construction** (poison budget
equals the scout's retrieval depth, so a maximally query-relevant poison fills the top-k). This is
the specific cell the reviewer identified, and we concede it.

**Planner adoption = 1.0 at that same cell is an OBSERVED result, not guaranteed by construction.**
The planner *choosing* to place a waypoint at the malicious coordinates is an empirical outcome of
the LLM planner, distinct from the retrieval CCR being 1.

## 2. RET result — CCR is not 1 by construction
`CCR = min(budget, k)/k`, measured exactly (seed-as-unit, n=10, deterministic retrieval):

| top-k | b=1 | b=2 | b=3 | b=5 |
|---|---|---|---|---|
| 3 (reused) | 0.333 | 0.667 | **1.0** | — |
| 5 | 0.20 | 0.40 | 0.60 | **1.0** |
| 10 | 0.10 | 0.20 | 0.30 | 0.50 |
| 20 | 0.05 | 0.10 | 0.15 | 0.25 |

CCR < 1 whenever k > budget. `poison-presence = 1.0` and `malicious-rank = 1` at every cell (poison
stays #1 even at k=20 / CCR=0.05).

**Exact asymmetric baseline (measured directly, scout_k=3, supervisor_k=5, budget 3):** aggregate
CCR = **0.818 (9/11)** — scout 1.0, supervisor 0.6 — **not 1**.

## 3. PLAN result — planner coordinate-adoption (does contamination become adoption?)
Scope: "adoption" = the planner placed a waypoint at the malicious (trap) coordinates within 5 m.
This is planner coordinate-adoption, **not** demonstrated physical hijack (SITL/L4, out of scope).
`valid_plan_rate = 1.0` at every cell (all `success`, no parse/timeout/provider failures), so
adoption-among-valid **equals** intent-to-treat (ITT) adoption; A00 controls adopt 0.0 everywhere.

| planner_k | valid-plan rate | adoption/valid (95% CI) | ITT adoption | A01−A00 Δ | CCR |
|---|---|---|---|---|---|
| 3 | 1.0 | **1.0** [1.0,1.0] | 1.0 | 1.0 | 1.0 |
| 5 | 1.0 | **0.4** [0.1,0.7] | 0.4 | 0.4 | 0.6 |
| 10 | 1.0 | **0.6** [0.3,0.9] | 0.6 | 0.6 | 0.3 |
| 20 | 1.0 | **0.1** [0.0,0.3] | 0.1 | 0.1 | 0.15 |

## 4. Verdict — operating-point dependence and substantial weakening at large k (NOT strict monotonic decay)
Adoption is **not** a strictly monotonic function of planner_k: k=5 (0.4) and k=10 (0.6) are
**non-monotonic with overlapping confidence intervals**, so no ordered decay between them is claimed.
What the data DO support: **operating-point dependence** — adoption is complete at the saturated
k=3 cell and **substantially weaker at large k**, most clearly **k=20 (0.1) versus k=3 (1.0)**.
Adoption is also not a clean function of CCR (at k=10, adoption 0.6 > CCR 0.3), consistent with the
poison's rank-1 retrieval giving it disproportionate influence; but by k=20 it is low. This
**supports the reviewer's k-sensitivity concern** at the adoption level, rather than a
construction-invariant effect.

## 5. Denominators (exact)
- RET CCR: poisoned-retrieved / total-retrieved (aggregate over agents; per-role also reported for
  the asymmetric baseline). Seed = unit (n=10).
- PLAN adoption_among_valid = adoptions / valid plans; ITT adoption = adoptions / attempted (=10).
  valid_plan_rate = 1.0 everywhere, so the two coincide here; parse/timeout/provider failures would
  count against the ITT denominator (none occurred). Seed = unit (n=10).
- CIs: percentile bootstrap, seed-as-unit, seeded RNG — **PROVISIONAL pending Dr. Qian**.

## 6. Limitations
- RET retrieval is deterministic (no temperature) → tight/degenerate CIs; the invariance is a rank
  property, not a statistical average. PLAN uses the LLM at temp 0.0.
- Memory fixed = MEM060_OPERATIONAL (452A established memory-invariance). Single planner model
  (gpt-oss:20b). n=10 seeds ⇒ wide PLAN CIs (esp. the k=5/k=10 mid-range).
- PLAN measures **planner coordinate-adoption only** — not physical execution.

## 7. Final scoped reviewer response
> "CCR is not 1 by construction: `CCR = min(budget,k)/k`, so CCR < 1 whenever k > budget; at the
> paper's exact asymmetric topology (scout 3, supervisor 5, budget 3) the measured aggregate CCR is
> 0.82, not 1. We concede that the Scout CCR=1 cell (k=3, budget=3) is saturated by construction.
> We add a planner-adoption study: the planner adopting the malicious coordinates is an observed
> result (adoption 1.0 at k=3), and adoption is operating-point-dependent — substantially weaker at
> large k (0.1 at k=20 vs 1.0 at k=3), with a non-monotonic mid-range (k=5, k=10) whose CIs overlap.
> This supports the reviewer's k-sensitivity concern at the adoption level. All effectiveness claims
> are scoped to planner coordinate-adoption; physical execution is not demonstrated here."

## Out of scope
- SITL/L4 physical execution; defended (D1–D4) behavior; other memory profiles/models; the
  memory-generalization axis (Reviewer 452A Part 1, closed separately).

## Regenerate (one command)
`python3 experiments/campaign_452b.py && python3 experiments/campaign_452b_plan.py`
(reproduces the curated `ret_*` and `plan_*` summaries byte-identically from `results_v3_raw/`).
