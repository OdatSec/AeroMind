# Reviewer 452A — Memory Generalization: CANONICAL conclusion (consolidates Part 1 + composition)

**Status: NOT CLOSED — consolidation + calibration complete; closure deferred pending the evidence gaps in §8.**

This is the **canonical P2 conclusion.** It consolidates `452A_part1_memory_generalization` (off-topic
volume — now Slice V here) and the memory-composition study into one result, and **supersedes Part 1's
headline.** Part 1's raw bundles are untouched and retained.

## 1. Reviewer concern (452A)
> "The attack is demonstrated on an extremely simple initial memory… it's unclear whether the attack would
> be successful with different initial memory states… claiming that the success rate doesn't change much
> from 6 to 200 records is misleading without specifying what those records are."

## 2. Run accounting (reconciled from the actual bundles — TWO campaigns)
P2 consists of **two distinct campaigns under two preregs; total = 440 production runs.** The "200/50" and
"240" figures refer to *different* campaigns — there is no missing-40 gap; they are simply not the same set.

**Campaign A — Part 1 (`PREREG_452A.md`): 200 runs = 150 A01 + 50 A00 controls.** Off-topic *composition
variants* (sparse / operational / dense / episodic-heavy / benign-high-sim) × poison budgets {1,2,3}. This
is the source of the "200 total, 50 controls" figure. (Bundles under the Part-1 prereg hash.)

**Campaign B — this composition study (`PREREG_P2_memory_composition.md`): 240 runs = 170 A01 + 70 controls.**
- Slice V (60) = 3 off-topic sizes × (A01 generic + A00) × 10 = 30 A01 + 30 controls.
- Slice O (120) = 4 on-topic N × (A01 generic + A01 adaptive + A00) × 10 = 80 A01 + 40 controls.
- Slice K (60) = 3 competitor M × (A01 generic + A01 adaptive) × 10 = 60 A01 + 0 controls.

**All 240 of Campaign B are present** in `results_v3_raw/` (verified by prereg-hash filter) and aggregated in
`results_v3_campaigns/P2_memory_composition/`; **all 200 of Campaign A** are present under the Part-1 prereg
hash. Nothing is missing or stored elsewhere. (Correction: an earlier note wrongly said the 200/50 figure
"could not be reproduced" — that was because only Campaign B was counted; the 200/50 is Campaign A and is real.)

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
- **NOT a general "adaptive restores" law** — scoped to one frozen template.
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

## 7. Mechanism (correlational, within Formula (1))
In the tested cells the poison's `sim` (relevance) term varied while recency (1.0) and importance (0.9)
were **held constant**, and the outcome **tracked `sim`**. This is a **correlational** observation within
the scoring function on these cells — **not** a proven general causal law.

## 8. Limitations & remaining evidence gaps (why closure is deferred)
- Off-topic "size" = **3 discrete profiles** {MEM003, MEM060, MEM200} (covers the reviewer's "6 to 200");
  not a continuous sweep; MEM1000 not built.
- **Adaptive rests on a single frozen template** — robustness across phrasings untested.
- **Competitor result is a 0.005 near-tie** — a genuinely-stronger competitor (more relevant than the
  poison) has NOT been tested, so the "relevance-rank governs" reading is **not robustly** established.
- RET/L1 only; no planner or physical execution; A01 only (composition isolation); local embedder only.

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
python3 experiments/p2_memory_composition.py --aggregate
```
Reads only P2 production bundles (prereg-hash filtered); runs no experiments.
