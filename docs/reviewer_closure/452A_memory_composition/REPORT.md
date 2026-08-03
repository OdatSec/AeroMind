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
4. **Same-template competitor is a NEAR-TIE, not a result.** A genuine true-target observation using the
   same template (sim 0.7234) did not evict the generic poison (sim 0.7286) — **only by a 0.005 margin.**
   This is a coin-flip-thin margin, **NOT** evidence that competitors don't matter.

## 6. Explicitly NOT claimed (corrections)
- **NOT "invariant to memory composition."** Composition matters: on-topic content evicts the generic poison.
- **The reviewer was NOT "refuted."** The concern is **partly correct** — richer (on-topic) memory reduces
  the generic attack's success. We **concede** this and characterize the boundary.
- **NOT a general "adaptive restores" law** — scoped to one frozen template.
- **NOT generalized** to signed / perception / reflection entry paths (that is P1).

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

## 9. Reproduce
```
python3 experiments/p2_memory_composition.py --aggregate
```
Reads only P2 production bundles (prereg-hash filtered); runs no experiments.
