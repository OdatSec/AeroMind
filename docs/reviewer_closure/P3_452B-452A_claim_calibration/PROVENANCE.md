# P3 — Provenance & integrity

**Documentation-only** package (no experiments). Every calibrated claim points to an already-accepted
evidence package; this file records that each source exists and the conventions used.

## Evidence packages referenced by the ledger (all verified present)
| Package | Used for | Status |
|---|---|---|
| `docs/reviewer_closure/452B-1_topk_saturation_ksensitivity/` | C1, C6, C7 — CCR=min(b,k)/k sweep, asymmetric 0.82, S12 adoption | ✓ exists |
| `docs/reviewer_closure/P2_452A_memory_generalization/` | C1, C4 — rank dominance is empirical; on-topic eviction | ✓ exists |
| `docs/reviewer_closure/P1_452B-452C_threat_model_realism/` | C2, C3 — planner adoption measured | ✓ exists |
| Manuscript `RAID_2026_Current/current_version.tex` (+ `sections/`) | C2/C3/C5/C7 Tables 5/6/8 | ✓ matches `RAID_2026_Current.pdf` |

## Uncertainty conventions (binding for the manuscript sweep)
- **Deterministic CCR** (pinned `nomic-embed-text`) → report **observed values**, not sampling CIs.
- **Clopper-Pearson 95% CIs** → **only** binary presence/adoption/physical outcomes across memory
  realizations / seeds (e.g. 35/35 → [~0.90, 1.0]; 10/10 → [0.69, 1.0]).
- **Saturation** `CCR = min(b,k)/k` is stated **conditionally** (requires ≥k poison to outrank all benign and
  occupy top-k); rank dominance is empirical.
- **Downstream** (planner/physical) is a **separate layer** from retrieval CCR and is **model-dependent**;
  never stated as universal.

## What is and is NOT in this package
- **In:** the ledger, saturation inventory, claim→evidence map, recommended manuscript change log, this file.
- **NOT in:** any manuscript edit (deferred to authors per instruction), and no raw experiment bundles
  (those live in their respective evidence packages / `results_v3_raw/`).

## Status: CALIBRATION PACKAGE COMPLETE — manuscript integration intentionally deferred
- **Calibration package COMPLETE:** every `MASTER_CLAIM_LEDGER.csv` row's `evidence_package` resolves to an
  existing accepted package — **verified TRUE above**. Ledger, saturation inventory, evidence mappings, and
  apply-ready wording are final.
- **Manuscript integration DEFERRED (author step):** apply `MANUSCRIPT_CHANGE_LOG.md`, rebuild the paper, and
  confirm the overclaim sweep clean. This package does **not** claim the manuscript has been corrected.
