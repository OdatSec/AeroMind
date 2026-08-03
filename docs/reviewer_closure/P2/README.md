# P2 — Memory Generalization (Reviewer 452A) — CLOSED

Self-contained evidence package for the memory-generalization concern. Attack = **A01 / S01 only**,
**retrieval (RET/L1) only** (this isolates *memory composition*; it is orthogonal to the threat-model
work and does not generalize to other attacks).

## Reviewer concern (452A)
> "The attack is demonstrated on an extremely simple initial memory… it's unclear whether the attack
> would be successful with different initial memory states… claiming success doesn't change much from
> 6 to 200 records is misleading without specifying what those records are."

## Conclusion (what the evidence shows)
**Retrieval contamination depends on relative relevance ranking — not raw memory size — for top-k occupancy.**
- Raw memory **size** did not matter for the tested **off-topic** profiles (3 / 60 / 200 records → CCR 1.0).
- **On-topic** benign content **evicts** the generic poison (CCR → 0).
- A **higher-ranking benign record evicts the poison** (stronger-competitor test: 3 competitors → CCR 0).
- **Sufficiently query-aligned poison may regain top-k — but this is template-dependent and fragile,
  NOT generally robust** (of 3 frozen adaptive phrasings, only one reached rank-1; one failed entirely).

We therefore **revise — not "refute"** — the reviewer: composition matters; the concern is partly correct.

## Run accounting (500 runs = 370 A01/S01 + 130 controls; verified from raw bundles)
| Campaign | Prereg | Runs | A01 | Controls |
|---|---|--:|--:|--:|
| A — Part 1 (off-topic composition variants × poison budgets) | PREREG_452A | 200 | 150 | 50 |
| B — composition (on-topic flood / adaptive / competitor) | PREREG_P2_memory_composition | 240 | 170 | 70 |
| C — P2b hardening (stronger competitor + 3 adaptive templates) | PREREG_P2b_hardening | 60 | 50 | 10 |
| **TOTAL** | | **500** | **370** | **130** |

## What's in this folder
- **`REPORT.md`** — full report incl. §6b (the professor's deterministic-retrieval explanation + the
  retrieval-score audit + tie-break rule) and §10 (hardening results, each template reported separately).
- **`CLAIM_TO_EVIDENCE.md`** — every claim mapped to its evidence, with what is NOT claimed.
- **`PROVENANCE.md`** — prereg hashes, embedder digest, run accounting, integrity.
- **`data/`** — machine-readable results:
  - `composition_cells.csv` — Campaign B (24 cells).
  - `hardening_cells.csv` — Campaign C (Test 1 & Test 2, with Clopper-Pearson CIs).
  - `score_audit.csv` — deterministic score breakdown (poison/benign score, sim/recency/importance,
    top-3 cutoff, margin) — answers the deterministic-retrieval question row by row.
  - `*.json` — campaign summaries.
- **`preregistration/`** — the three frozen pre-registrations (design fixed before running).
- **`part1_superseded/`** — Part 1's closure docs (its headline is superseded by this package; retained
  because Part 1 supplies 200 of the 500 runs).

## Notes on rigour
- CCR is **deterministic** given the pinned embedder (`nomic-embed-text`); reported as observed values.
  Binary "poison present in top-k" outcomes use **exact Clopper-Pearson 95% CIs** (10/10 → [0.69, 1.0]).
- Scope/limitations are stated explicitly (one on-topic template; 3 discrete off-topic sizes; A01/S01, RET
  only). No general-adaptive-robustness claim.
- Raw per-run evidence (500 bundles: manifest, metrics, retrieval trace, memory snapshots, checksums) lives
  on the machine under `results_v3_raw/` (too large to include here; reproducible via the aggregators).
