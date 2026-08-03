# 452A memory-composition — Claim → Evidence map

| # | Claim | Evidence | Value |
|---|---|---|---|
| C1 | Contamination is invariant to OFF-TOPIC memory volume 3→200. | Slice V, 3 profiles × 10 seeds | CCR 1.0 (MEM003/060/200) |
| C2 | The reviewer is right: ON-TOPIC memory reduces success. | Slice O generic, N∈{50,200,500} | CCR 1.0→**0.0** |
| C3 | The governing variable is query-relevance rank (`sim`), not size. | per-cell decomposition | generic sim 0.729 < on-topic 0.838 |
| C4 | An adaptive query-matched attacker restores success. | Slice O adaptive | CCR 1.0 (0.667 at N=500); sim 0.854 |
| C5 | Recency/importance do not discriminate. | decomposition | recency 1.0, importance 0.9 for all |
| C6 | Genuine same-template competitors do not dislodge the poison. | Slice K, M∈{1,3,5} | CCR 1.0 (margin 0.005) |
| C7 | Controls clean. | A00 cells | CCR 0.0 |

## Headline (scoped)
> Retrieval contamination is governed by the poison's **query-relevance rank** — invariant to off-topic
> memory volume (3→200), collapses to 0 under on-topic benign traffic, and is restored by an adaptive
> query-matched attacker. RET/L1, top-k 3, budget 3, n=10 seeds/cell.

## Supersedes / scopes
Revises `452A_part1`'s "invariant 3→200" to "invariant to *off-topic* volume; sensitive to *on-topic*
composition." Off-topic facet retained. Out of scope: planner adoption, defended runs (FD1/Cam), MEM1000.
