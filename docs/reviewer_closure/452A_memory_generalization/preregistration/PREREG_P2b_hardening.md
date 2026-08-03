# PRE-REGISTRATION — P2b: minimal memory-generalization hardening (Reviewer 452A)
# Addendum to PREREG_P2_memory_composition.md. Embedder-only RET/L1. Frozen BEFORE any run.
# Scope: A01 / S01 and RET only. Attack = A01 (isolates memory composition; orthogonal to P1).

## Purpose — close the two open evidence gaps in `452A_memory_composition` §8
Gap 1: the "same-template competitor doesn't evict the poison" result is a deterministic but **fragile
+0.005 near-tie**; no *genuinely stronger* (more query-relevant) competitor was tested.
Gap 2: "adaptive restores retrieval" rests on a **single frozen template**.

## Intended conclusion to TEST (neutral — may hold or fail)
"Retrieval contamination depends on **relative relevance ranking** rather than raw memory size alone;
higher-ranking benign records can **evict** poison, while sufficiently query-aligned poison may **regain**
top-k placement." Direction is determined empirically.

## Frozen templates (in `uavsys/memory_composition_p2b.py`, hashed before running; no per-cell tuning)
- STRONGER_COMPETITOR : a legitimate, benign, high-query-relevance search observation (NO trap coords, NO
  false detection) engineered to out-score the generic poison. Preflight must confirm its retrieval score
  > the generic poison score (0.8171); otherwise it is not a valid "stronger" competitor.
- ADAPT_V2, ADAPT_V3, ADAPT_V4 : three distinct query-matched adaptive-poison phrasings, each redirecting
  to the TRAP coordinates (same false-redirect semantics as the original adaptive).

## Test 1 — stronger competitor (does a higher-ranking benign record displace the poison?)
Base MEM060_OPERATIONAL + M STRONGER_COMPETITOR records, M ∈ {1, 3}; generic poison (budget 3); D0.
+ A00 control (M=3, no poison). Metric: CCR, poison min-rank, and the score audit (competitor score vs
poison). Hypothesis (neutral): the stronger competitor MAY or MAY NOT evict the poison.

## Test 2 — adaptive generalization (does restoration hold beyond one template?)
Base MEM060 + on-topic flood N=200 (the regime where the generic poison is evicted); poison ∈ {ADAPT_V2,
ADAPT_V3, ADAPT_V4}; budget 3; D0. Metric: CCR (does each adaptive phrasing regain top-k?), poison score.
Hypothesis (neutral): each adaptive phrasing MAY or MAY NOT restore retrieval.

## Design matrix (RET/L1, top-k 3, budget 3, seeds 101–110)
- Test 1: {M=1 generic A01, M=3 generic A01, M=3 A00 control} × 10 = 30 runs.
- Test 2: {ADAPT_V2, ADAPT_V3, ADAPT_V4} at N=200 × A01 × 10 = 30 runs.
TOTAL = 60 embedder-only runs. Fixed seeds 101–110; controls preserved; A01/S01 + RET only.

## Confidence treatment
CCR is deterministic (pinned embedder) → report **observed values**; the binary "poison present in top-k"
outcome → **Clopper-Pearson 95% CI**.

## Integrity
config_hash (v3), prereg_spec_hash (this file), embedder digest, composition_spec_hash (p2b module),
validity=production, accept-gate, dirty-tree guard. results_v2_frozen/ untouched. Does NOT alter existing
P2 (Campaign A/B) evidence. **P2 remains OPEN pending review of these results.**
