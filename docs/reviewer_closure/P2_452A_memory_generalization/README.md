# P2 — Memory Generalization (Reviewer 452A) — CLOSED

Single self-contained evidence package. Attack = **A01 / S01 only**, **retrieval (RET/L1) only** — this
isolates *memory composition* (orthogonal to the threat-model work; it does not generalize to other attacks).

## Reviewer concern (452A)
> "The attack is demonstrated on an extremely simple initial memory… it's unclear whether the attack would
> be successful with different initial memory states… claiming success doesn't change much from 6 to 200
> records is misleading without specifying what those records are."

## Conclusion (what the evidence shows)
**Retrieval contamination depends on relative relevance ranking — not raw memory size — for top-k occupancy.**
- Raw memory **size** did not matter for the tested **off-topic** profiles (3 / 60 / 200 records → CCR 1.0).
- **On-topic** benign content **evicts** the generic poison (CCR → 0).
- A **higher-ranking benign record evicts the poison** — confirmed *causally* (stronger-competitor test:
  3 competitors → CCR 0).
- **Sufficiently query-aligned poison may regain top-k, but this is template-dependent and fragile, NOT
  generally robust** (of 4 adaptive phrasings tested, one failed entirely; where restoration occurs it rests
  on a deterministic-but-fragile sub-0.01 margin).

We **revise — not "refute"** — the reviewer: composition matters; the concern is partly correct.

## Run accounting (500 runs = 370 A01/S01 + 130 controls; verified from raw bundles)
| Campaign | Prereg | Runs | A01 | Controls |
|---|---|--:|--:|--:|
| A — Part 1 (off-topic composition variants × poison budgets) | PREREG_452A | 200 | 150 | 50 |
| B — composition (on-topic flood / adaptive / competitor) | PREREG_P2_memory_composition | 240 | 170 | 70 |
| C — P2b hardening (stronger competitor + 3 adaptive templates) | PREREG_P2b_hardening | 60 | 50 | 10 |
| **TOTAL** | | **500** | **370** | **130** |

## Contents
- **`REPORT.md`** — full report: §6b deterministic-retrieval explanation + score audit + tie-break rule;
  §7 mechanism (causal via P2b); §8 post-hardening limitations; §10 hardening results (each template separate).
- **`CLAIM_TO_EVIDENCE.md`** — every claim → evidence; what is NOT claimed.
- **`PROVENANCE.md`** — prereg hashes, embedder digest, run accounting, integrity.
- **`data/`** — machine-readable results:
  - `composition_cells.csv` (Campaign B, 24 cells), `hardening_cells.csv` (Campaign C, Clopper-Pearson CIs),
  - `score_audit.csv` (deterministic score breakdown — the professor's question),
  - `part1_saturated_per_profile.csv`, `part1_nonsaturated_per_profile_budget.csv` (Campaign A aggregates),
  - `*_summary.json`.
- **`preregistration/`** — the three frozen pre-registrations.
- **`part1/`** — Part 1's closure docs (headline superseded by this package; supplies 200 of the 500 runs).

## Rigour notes
- CCR is **deterministic** given the pinned embedder (`nomic-embed-text`) → observed values; binary
  "poison present in top-k" → **exact Clopper-Pearson 95% CIs** (10/10 → [0.69, 1.0]).
- Scope stated explicitly (one on-topic template; 3 discrete off-topic sizes; A01/S01, RET only);
  no general-adaptive-robustness claim.
- Raw per-run evidence (500 bundles) lives on the machine under `results_v3_raw/` (too large to include;
  reproducible via `experiments/p2_memory_composition.py --aggregate` and `experiments/p2b_hardening.py --aggregate`).
