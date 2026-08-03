# 452B (top-k saturation & k-sensitivity SUB-CONCERN) — Claim → Evidence map

> Scope: this maps the **452B-1** objection (CCR-by-construction + k-sensitivity) only. Reviewer
> 452B's **threat-model-practicality** objection (realistic direct/unauthenticated write access) is
> NOT covered here — it is deferred to A04/A05/A06 + the attacker-capability/write-path table +
> reduction of the direct-write claim. Reviewer 452B is NOT fully closed.


CIs are seed-as-unit percentile bootstrap, **PROVISIONAL pending Dr. Qian**. Raw paths + hashes in
`PROVENANCE.md`.

| # | Claim | Evidence | Value |
|---|---|---|---|
| C1 | CCR is not 1 by construction; CCR = min(budget,k)/k. | RET sweep k∈{3,5,10,20}×b∈{1,2,3,5} (170 new + 40 reused) | k5: .2/.4/.6/1.0; k10: .1/.2/.3/.5; k20: .05/.1/.15/.25 |
| C2 | Poison stays #1 and present at all k. | RET retrieval_competition | malicious-rank=1, poison-presence=1.0 at every cell |
| C3 | At the paper's EXACT asymmetric topology, aggregate CCR < 1 (measured, not reconstructed). | RET asymmetric baseline `topk-s03-p05`, budget 3 | aggregate 0.818; scout 1.0; supervisor 0.6 |
| C4 | **Only** the Scout CCR=1 (k=3, b=3) cell is saturated by construction. | C1 (k=3 column) | CCR=1 at k=budget only |
| C5 | Planner adoption at that cell (1.0) is an OBSERVED result, not guaranteed by construction. | PLAN k=3, A01 | adoption 1.0 [1.0,1.0] (empirical LLM outcome) |
| C6 | Planner adoption is operating-point-dependent and substantially weaker at large k. | PLAN k∈{3,5,10,20} | 1.0 → (0.4 / 0.6) → 0.1; k=20 vs k=3 delta = 0.9 |
| C7 | No strictly monotonic decay is claimed (mid-range non-monotonic, CIs overlap). | PLAN k=5 vs k=10 | 0.4 [0.1,0.7] vs 0.6 [0.3,0.9] — overlapping |
| C8 | Controls are clean; failures do not inflate adoption. | PLAN A00 (all k) + valid_plan_rate | A00 adoption 0.0; valid_plan_rate 1.0; adoption/valid == ITT |

## Headline (scoped)
> CCR = min(budget,k)/k (asymmetric aggregate 0.82, not 1); the Scout CCR=1 cell is saturated by
> construction; planner coordinate-adoption is an observed result that is operating-point-dependent
> and substantially weaker at large k (0.1 at k=20 vs 1.0 at k=3), non-monotonic in the mid-range.

## Out of scope (NOT claimed)
- **452B threat-model practicality** (is direct/unauthenticated memory injection realistic in UAV
  systems?) — OPEN; deferred to A04/A05/A06 + attacker-capability/write-path table + direct-write
  claim reduction. **452B is not fully closed.**
- Physical drone hijack (SITL/L4) — PLAN measures coordinate-adoption only.
- Strict monotonic adoption ordering across k.
- Memory-state effects (452A Part 1, closed separately); defended behavior (D1–D4).
