# Reviewer 452A — Memory Generalization (composition): Closure Report

**Status: CLOSED for the tested envelope.** Retrieval contamination is governed by the poison's
**query-relevance rank**, not by memory size. It is invariant to *off-topic* memory volume (3→200),
**collapses to zero** under *on-topic* benign traffic, and is **restored by an adaptive query-matched
attacker**. The governing quantity is the relevance term of Formula (1) (`sim`), shown per cell.

This **revises** the earlier `452A_part1_memory_generalization` headline: the "invariant 3→200" result is
true only for *off-topic* filler — exactly the "misleading without specifying what those records are"
the reviewer flagged. The off-topic-volume facet remains valid; it is now one facet of a bounded law.

Evidence: **240 accepted production runs** (24 cells × 10 seeds), deterministic, accept-gate PASS. RET/L1
embedder-only, top-k 3, budget 3, seeds 101–110. Raw bundles git-ignored; hashes in `PROVENANCE.md`.

---

## 1. Reviewer concern (452A, memory)
> "The attack is demonstrated on an extremely simple initial memory… it's unclear whether the attack would
> be successful with different initial memory states. If the baseline already has many episodic messages, I
> think it would definitely affect S01's success rate; claiming the success rate doesn't change much from 6
> to 200 records is misleading without specifying what those records are."

## 2. What the paper did (and the gap)
Paper S07/S08/S09 vary poison *volume* (stealth/flood/recency); the benign memory is always *off-topic*
operational filler, and its *composition* is never varied. So "invariant 3→200" only ever tested off-topic
growth — the reviewer's on-topic hypothesis was untested.

## 3. Results — 240 production runs (frozen templates, `uavsys/memory_composition.py`)
### Slice V — off-topic volume (the paper's claim, honestly labeled off-topic)
| memory | CCR (generic) | best-benign sim |
|---|--:|--:|
| MEM003 (3) | 1.00 | 0.672 |
| MEM060 (60) | 1.00 | 0.614 |
| MEM200 (200) | 1.00 | 0.696 |
→ invariant to off-topic volume (poison sim 0.729 > all). A00 control 0.0.

### Slice O — on-topic episodic flood × attacker adaptivity (the reviewer's exact scenario)
| on-topic N | CCR generic | CCR adaptive | best-benign sim |
|--:|--:|--:|--:|
| 0 | 1.00 | 1.00 | 0.614 |
| 50 | **0.00** | 1.00 | 0.838 |
| 200 | **0.00** | 1.00 | 0.838 |
| 500 | **0.00** | 0.667 | 0.847 |
→ **the reviewer is right**: on-topic traffic (sim 0.838) out-ranks the generic poison (sim 0.729) and
evicts it. An **adaptive** poison (sim 0.854) survives. A00 control 0.0 throughout.

### Slice K — genuine competing true-target observations
| competitors M | CCR generic | CCR adaptive |
|--:|--:|--:|
| 1 / 3 / 5 | 1.00 | 1.00 |
→ same-template true observations (sim 0.723) do NOT dislodge the poison (generic wins by a 0.005 sim margin).

## 4. Interpretation (scoped)
Success is not a function of memory *size* but of whether the poison out-ranks the benign content on
**query relevance** (`sim`, weight 0.6 in Formula 1). Recency and importance are identical across records
(1.0 and 0.9) and do not discriminate. Hence: invariant to off-topic volume; degrades to 0 under on-topic
traffic; restored by an adaptive query-matching attacker. This directly answers the reviewer with a
mechanism and a boundary rather than a fragile invariance claim.

## 5. Scope limitations (explicit)
- **RET/L1 embedder-only**; not planner adoption, physical execution, or defended runs (defense slice
  deferred to FD1/Cam).
- Volume axis {3,60,200} (covers the reviewer's "6 to 200"; MEM1000 not built).
- CIs degenerate (deterministic embedder → every seed identical); reported as exact rates over n=10.

## 6. Reproduce
```
python3 experiments/p2_memory_composition.py --aggregate
```
Reads only P2 production bundles (filtered by the P2 prereg hash); runs no experiments.
