# 452A Memory Generalization (canonical) — Claim → Evidence map

CCR is deterministic (pinned embedder) → observed values. Binary "poison present in top-k" → Clopper-Pearson 95% CI.
Attack = **A01 only** (isolates memory composition; orthogonal to P1 entry paths; does NOT generalize to A04/A05/A06/TC-reflect).

| # | Claim (calibrated) | Evidence | Value |
|---|---|---|---|
| C1 | Raw memory SIZE did not matter for the tested OFF-TOPIC profiles. | Slice V, MEM003/060/200, 10 seeds each | CCR = 1.0 (all seeds); present 10/10 [0.69,1.0]; controls 0.0 |
| C2 | ON-TOPIC benign content EVICTED the generic poison. | Slice O generic, N∈{50,200,500} | CCR 1.0 → 0.0; present 0/10 [0,0.31]; best-benign sim 0.838 > poison 0.729 |
| C3 | A query-matched adaptive poison RESTORED retrieval, in the tested configuration (one frozen template). | Slice O adaptive | CCR = 1.0 (N≤200), 0.667 (N=500), observed; sim 0.854 |
| C4 | A same-template competitor is a NEAR-TIE — not evidence competitors don't matter. | Slice K, M∈{1,3,5} | generic wins by a 0.005 sim margin (0.7286 vs 0.7234) |
| C5 | Controls are clean. | A00 (70 runs Campaign B + 10 P2b control) | CCR 0.0 |
| C6 | A higher-ranking benign competitor DISPLACES/EVICTS the poison (causal). | P2b Test 1 (30 runs): competitor 0.897 > poison 0.817 | M=1 → CCR 0.667 (rank 2); M=3 → CCR 0.0 (rank 4), present 0/10 [0,0.31] |
| C7 | Adaptive restoration is TEMPLATE-DEPENDENT — does NOT generalize. | P2b Test 2 (30 runs), 3 frozen templates, each separate | adapt_v2 rank-1 (CCR 0.667, margin +0.005 fragile); adapt_v4 rank-2 (CCR 0.333); **adapt_v3 evicted (CCR 0, 0/10)** |

## Canonical conclusion (scoped, hardened)
> Using attack A01 to isolate memory composition: **retrieval contamination depends on relative relevance
> ranking, not raw memory size alone.** Raw size did not matter for the tested off-topic profiles
> (MEM003/060/200 → CCR 1.0); **a higher-ranking benign record evicts the poison** (P2b Test 1: M=3
> stronger competitors → CCR 0); and **sufficiently query-aligned poison may regain top-k placement — but
> this is template-dependent, not general** (P2b Test 2: only 1 of 3 frozen adaptive phrasings reached
> rank-1; one failed entirely). This **revises** — does not "refute" — the reviewer: composition matters,
> and the reviewer's concern is partly correct.

## What P2b did NOT establish
- **NOT general adaptive robustness** — restoration is template-dependent (adapt_v3 failed; adapt_v4 weak);
  where it occurs it rests on a **deterministic but fragile** sub-0.01 margin.
- Off-topic size = 3 discrete profiles; one on-topic template; A01 + RET only; local embedder.

## Explicitly NOT claimed
- NOT "invariant to memory composition"; NOT "reviewer refuted."
- Adaptive result scoped to one frozen template; competitor result is a fragile 0.005 near-tie.
- RET/L1 only; A01 only; local embedder; no generalization to P1 entry paths (A04/A05/A06/TC-reflect).
- Off-topic "size" = 3 discrete profiles, not a continuous sweep (MEM1000 not built).
