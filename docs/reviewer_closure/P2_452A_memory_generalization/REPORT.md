# Reviewer 452A — Memory Generalization: CANONICAL conclusion (consolidates Part 1 + composition)

**Status: CLOSED.** Consolidation + calibration + P2b hardening complete; the two prior evidence gaps
(stronger competitor; adaptive generalization) are now closed by the P2b intervention (§10).

This is the **canonical P2 conclusion.** It consolidates `452A_part1_memory_generalization` (off-topic
volume — now Slice V here) and the memory-composition study into one result, and **supersedes Part 1's
headline.** Part 1's raw bundles are untouched and retained.

## 1. Reviewer concern (452A)
> "The attack is demonstrated on an extremely simple initial memory… it's unclear whether the attack would
> be successful with different initial memory states… claiming that the success rate doesn't change much
> from 6 to 200 records is misleading without specifying what those records are."

## 2. Run accounting (verified from the actual bundles — THREE campaigns)
**P2 total = 500 production runs = 370 A01/S01 + 130 controls** (verified by prereg-hash bundle count).
Three distinct campaigns under three preregs:

| Campaign | Prereg (sha256) | Runs | A01 | Controls |
|---|---|--:|--:|--:|
| A — Part 1 (off-topic composition variants × budgets) | `PREREG_452A.md` (cc8c0e8b) | 200 | 150 | 50 |
| B — composition (on-topic / adaptive / competitor) | `PREREG_P2_memory_composition.md` (d9a37793) | 240 | 170 | 70 |
| C — P2b hardening (stronger competitor + 3 adaptive templates) | `PREREG_P2b_hardening.md` (17f93d7e) | 60 | 50 | 10 |
| **TOTAL** | | **500** | **370** | **130** |

- Campaign B breakdown: Slice V (60) = 30 A01 + 30 ctrl; Slice O (120) = 80 A01 + 40 ctrl; Slice K (60) = 60 A01.
- Campaign C breakdown: Test 1 (30) = 20 A01 + 10 ctrl; Test 2 (30) = 30 A01.

All 500 are present in `results_v3_raw/` (git-ignored) under their prereg hashes; aggregates in
`results_v3_campaigns/{P2_memory_composition, P2b_hardening}/` and Part-1's campaign dir. Nothing missing or
stored elsewhere. (The "200/50" figure is Campaign A and is real; an earlier note that wrongly said it
"could not be reproduced" was because only Campaign B had been counted.)

## 3. What A01 isolates (scope — read this first)
P2 uses attack **A01 (unauthenticated false observation) ONLY**, to isolate the effect of **memory
composition** on retrieval. It is **orthogonal to P1's entry-path threat model.** These results do **NOT**
generalize to A04 / A05 / A06 / TC-reflect without additional evidence.

## 4. Confidence treatment
CCR is **deterministic** given the pinned embedder; the 10 seeds are 10 different memory realizations. So
CCR is reported as **observed values** (identical across the 10 realizations unless a range is shown), and
the **binary** outcome "poison present in top-k" is reported with a **Clopper-Pearson 95% CI**.

## 5. Result (what was actually measured)
Metric = CCR (poison share of scout top-k = 3), budget 3, seeds 101–110.

1. **Raw memory SIZE did not matter for the tested OFF-TOPIC profiles.** MEM003 / MEM060 / MEM200 +
   generic poison → **CCR = 1.0** (all 10 seeds each; poison present 10/10, CI [0.69, 1.0]); controls 0.0.
2. **ON-TOPIC benign content EVICTED the generic poison.** Adding on-topic "search-log" records
   (N = 50 / 200 / 500) → generic **CCR 1.0 → 0.0** (poison present 0/10, CI [0, 0.31]); the on-topic
   benign records out-rank the generic poison (best-benign sim 0.838 > poison sim 0.729).
3. **A query-matched ADAPTIVE poison RESTORED retrieval — in the tested configuration.** The **single
   frozen** adaptive template (sim 0.854) held **CCR = 1.0** at N ≤ 200 and **CCR = 0.667** at N = 500
   (observed values). Scoped to that one template; **not** a general claim about adaptive attackers.
4. **Same-template competitor is a DETERMINISTIC but FRAGILE near-tie.** A genuine true-target observation
   using the same template (sim 0.7234) did not evict the generic poison (sim 0.7286) — the poison wins
   **reproducibly** (deterministic — same result every seed), but by only a **+0.005 margin.** It is
   **not** a coin flip (it is deterministic), but it is **fragile**: a slightly more query-relevant
   competitor would flip it — which is exactly what hardening test #1 (§10) is designed to check. It is
   **NOT** evidence that competitors don't matter.

## 6. Explicitly NOT claimed (corrections)
- **NOT "invariant to memory composition."** Composition matters: on-topic content evicts the generic poison.
- **The reviewer was NOT "refuted."** The concern is **partly correct** — richer (on-topic) memory reduces
  the generic attack's success. We **concede** this and characterize the boundary.
- **NOT a general "adaptive restores" law** — tested across 4 frozen adaptive phrasings (1 original + 3 in
  P2b); restoration is **template-dependent** (some restore, one failed), not general.
- **NOT generalized** to signed / perception / reflection entry paths (that is P1).

## 6b. Why Part 1's retrieval was DETERMINISTIC (professor's question)
> In Part 1, retrieval was deterministic because the query, embedding model, scoring function, poison
> wording, and top-k depth were fixed. The poison scored above the tested benign records, so *b* poison
> records occupied *b* of the *k*=3 positions, producing CCR = *b*/3. The flat lines therefore show
> **deterministic rank dominance over those tested distractors — not universal invariance to memory
> composition.**

### Retrieval-score audit (score = 0.6·sim + 0.2·recency + 0.2·importance; seed 101; reproduces production)
| cell | poison score (sim/rec/imp) | best-benign score (sim/rec/imp) | top-3 cutoff | margin | outcome |
|---|---|---|--:|--:|---|
| V/MEM003 generic | **0.8171** (0.729/1.0/0.9) | 0.7633 (0.672/1.0/0.8) | 0.8142 | **+0.054** | poison in top-3 → CCR 1.0 |
| V/MEM060 generic | **0.8171** (0.729/1.0/0.9) | 0.7481 (0.614/1.0/0.9) | 0.8142 | **+0.069** | poison in top-3 → CCR 1.0 |
| V/MEM200 generic | **0.8171** (0.729/1.0/0.9) | 0.7552 (0.692/1.0/0.7) | 0.8142 | **+0.062** | poison in top-3 → CCR 1.0 |
| O/N=50 generic | evicted | 0.8828 (0.838/1.0/0.9) | 0.8744 | negative | poison **evicted** → CCR 0.0 |
| O/N=200 generic | evicted | 0.8823 (0.838/1.0/0.9) | 0.8784 | negative | poison **evicted** → CCR 0.0 |
| O/N=200 adaptive | 0.8921 (0.854/1.0/0.9) | 0.8823 (0.838/1.0/0.9) | 0.8851 | **+0.010** | poison in top-3 → CCR 1.0 (fragile) |
| O/N=500 adaptive | 0.8921 (0.854/1.0/0.9) | 0.8881 (0.847/1.0/0.9) | 0.8863 | **+0.004** | poison rank-1 → CCR 0.667 (fragile) |

Full table incl. Slice-K competitor: `score_audit.csv`. Key facts: the **poison score is FIXED** (0.8171
generic / 0.8921 adaptive) regardless of profile — only the *benign* score changes; `recency`≈1.0 and
`importance`=0.9 are constant, so the **relevance (sim) term alone moves the margin**. Off-topic distractors
score ≤0.76 → poison wins by +0.05–0.07; on-topic benign scores 0.88 > generic poison 0.817 → **evicts it**;
the adaptive poison (0.892) squeaks past on-topic benign by **+0.004–0.010**.
**Tie-breaking rule:** `scored_items.sort(key=score, reverse=True)` — a stable sort on scores rounded to
4 decimals; equal scores retain candidate order.

## 7. Mechanism (causally demonstrated by the P2b intervention)
Across the cells the poison's `sim` (relevance) term varied while recency (1.0) and importance (0.9) were
**held constant**, so the outcome tracked `sim`. This was originally a *correlational* observation, but the
**P2b Test 1 intervention makes it causal** (§10): deliberately inserting a benign record that out-ranks the
poison **displaces** it (M=1 → CCR 0.667) and enough of them **evict** it (M=3 → CCR 0). Relative relevance
ranking therefore *governs* top-k occupancy in the tested configuration — not merely correlates with it.

## 8. Limitations (post-hardening; scope of the closed result)
- Off-topic "size" = **3 discrete profiles** {MEM003, MEM060, MEM200} (covers the reviewer's "6 to 200");
  not a continuous sweep; MEM1000 not built.
- **Adaptive restoration is template-dependent, not general** (P2b Test 2: of 3 frozen phrasings only
  adapt_v2 reached rank-1, adapt_v4 rank-2, adapt_v3 failed); where it occurs it rests on a **deterministic
  but fragile** sub-0.01 margin. We make **no general-adaptive-robustness claim.**
- On-topic content is one frozen template; the eviction threshold (N) is specific to its relevance.
- RET/L1 only; no planner or physical execution; **A01/S01 only** (composition isolation; orthogonal to P1);
  local embedder only.

## 10. Hardening results (P2b, `PREREG_P2b_hardening.md` sha256 17f93d7e) — A01/S01, RET only
**60 accepted production runs, 0 rejected/failed** (seeds 101–110; fully deterministic — all 10 seeds
identical per cell, so "CCR" is an observed value and the binomial CI is on "poison present in top-k").
Run accounting: Test 1 = 30 (M=1 A01:10, M=3 A01:10, M=3 A00 control:10); Test 2 = 30 (adapt_v2/v3/v4 A01,
10 each). Score = 0.6·sim + 0.2·rec + 0.2·imp; recency ≈ 1.0 and importance = 0.9 constant → sim drives it.

### Test 1 — does a higher-ranking benign competitor displace the poison? **YES (causal).**
Stronger competitor (benign, no trap) score **0.8974** (sim 0.862) > generic poison **0.8171** (sim 0.729).
| M competitors | poison score | poison rank | top-3 CCR | poison-in-top-3 / 10 | CI |
|--:|--:|--:|--:|--:|---|
| **0** (baseline, Campaign B) | 0.8171 | 1 | 1.0 | 10/10 | [0.69,1.0] |
| **1** | 0.8171 | 2 | 0.667 | 10/10 | [0.69,1.0] |
| **3** | 0.8171 | **4** | **0.0** | **0/10** | [0,0.31] |
| 3 (A00 control) | — | — | 0.0 | 0/10 | [0,0.31] |
→ A benign record that out-ranks the poison **displaces** it (M=1) and enough of them **evict** it (M=3 →
CCR 0). This upgrades the mechanism from correlational to **causal**: relative relevance ranking governs.

### Test 2 — does adaptive restoration generalize beyond one template? **NO — template-dependent.**
Each frozen phrasing reported SEPARATELY (all 3 preregistered templates tested; base MEM060 + on-topic N=200,
where the generic poison is evicted; best-benign score 0.8823):
| template | poison score (sim) | poison rank | top-3 CCR | poison-in-top-3 / 10 | margin | CI | verdict |
|---|--:|--:|--:|--:|--:|---|---|
| **adapt_v2** | 0.8874 (0.846) | **1** | 0.667 | 10/10 | **+0.0051** | [0.69,1.0] | restores (rank-1) — **deterministic but fragile** |
| **adapt_v4** | 0.8819 (0.837) | 2 | 0.333 | 10/10 | −0.0004 | [0.69,1.0] | partial (rank-2), weak |
| **adapt_v3** | evicted | — | **0.0** | **0/10** | — | [0,0.31] | **FAILS to restore** |
→ Only **1 of 3** frozen phrasings (adapt_v2) regains rank-1; adapt_v4 barely holds rank-2 (CCR 0.333);
adapt_v3 is evicted. **We therefore do NOT claim general adaptive robustness** — restoration is
**template-dependent** and, where it occurs, rests on a **deterministic but fragile** sub-0.01 margin.

### Preflight vs production
The preflight (seed 9001, `emit=False`, no bundles) previewed Test 1 (M=1→0.667, M=3→0) and adapt_v2
(rank-1); the accepted results above are the **10-seed production** runs (bundle-backed, accept-gated).

## 9. Reproduce
```
python3 experiments/p2_memory_composition.py --aggregate     # Campaign B (composition, 240 runs)
python3 experiments/p2b_hardening.py --aggregate              # Campaign C (P2b hardening, 60 runs)
```
Each reads only its production bundles (prereg-hash filtered); runs no experiments.
