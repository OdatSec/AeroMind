# P3 — Claim Calibration (Reviewers 452B + 452A) — status: OPEN

Cross-cutting, **documentation-only** consolidation of the claim-calibration concern. It does not run new
experiments; every calibrated claim points to an already-accepted evidence package. It covers two facets:
- **Facet 4 (452B):** "Results are, in some cases, overclaimed." / "CCR has to be 1, based on how retrieval works."
- **Facet 5 (452A):** "the 6→200 result is misleading without specifying what those records are."

**P2 remains … this package remains OPEN** until (a) every ledger row points to existing evidence [tracked here]
and (b) the manuscript sweep is applied by the authors (the corrected wording is provided in
`MANUSCRIPT_CHANGE_LOG.md`; per instruction the `.tex` is **not** edited here).

## The core calibration — three things that must be kept separate
Reviewer 452B is right that a naive reading makes "CCR = 1" look automatic. The precise, conditional statement:

1. **Saturation by construction (arithmetic, conditional).** `CCR = min(budget, k) / k` holds **only when at
   least `k` poisoned records outrank all benign candidates and therefore occupy the top-k slots.** At
   `budget = k` and under that rank-dominance condition, CCR = 1 **by construction**. It is **not** an
   unconditional architectural invariant.
2. **Empirically measured rank dominance.** *Whether* the poison outranks the benign candidates is an
   **empirical** question decided by the scoring function (relevance-dominated). Our composition study shows
   it is **not** guaranteed: on-topic benign content out-ranks a generic poison and **evicts** it (CCR → 0),
   and a higher-ranking benign competitor evicts it causally. So the "CCR=1" cells are saturated *given*
   measured rank dominance — a condition that can fail.
3. **Downstream (planner / physical) effects.** Planner adoption and physical redirection are a **separate
   layer** from retrieval CCR and are **not** implied by it. For the flagship coordinate hijack (S01) they were
   100% across the seven tested models; but one contagion case (Mistral, S06) reached 60% physical, and
   constraint injection (S12) adoption is **model-dependent** (0–100%). "Deterministic … regardless of model
   family" must be scoped accordingly.

## What this package contains
- **`MASTER_CLAIM_LEDGER.csv`** — every calibrated claim with: manuscript location · original wording ·
  calibration category · corrected wording · operating conditions · metric · uncertainty treatment ·
  evidence package · update status.
- **`SATURATION_INVENTORY.csv`** — each headline cell tagged *saturation-by-construction* /
  *measured-rank-dominance* / *downstream*, with its condition and evidence.
- **`CLAIM_TO_EVIDENCE.md`** — each calibrated claim → its accepted evidence package.
- **`MANUSCRIPT_CHANGE_LOG.md`** — recommended original→corrected wording per manuscript location (NOT applied here).
- **`PROVENANCE.md`** — evidence-package hashes, uncertainty conventions, what is/na verified.

## The two required explicit statements (verbatim, for the manuscript + response)
- **452B:** *"CCR = 1 is arithmetic that holds only conditional on at least `k` poisoned records outranking
  the benign records and occupying the top-k slots; at budget = k this is saturation by construction, not an
  architectural guarantee. Whether the poison outranks benign records is empirical (relevance-dominated) and
  can fail — on-topic benign content evicts a generic poison."*
- **452A:** *"The 3-to-200 size-invariance result is limited to the tested **off-topic** compositions;
  **on-topic** benign content evicted the generic poison. Contamination is governed by relative relevance
  ranking, not raw record count."*

## Uncertainty conventions (applied throughout)
Deterministic CCR values are reported as **observed values** (the pinned embedder makes retrieval
deterministic). **Clopper-Pearson 95% intervals** apply only to **binary presence** outcomes across memory
realizations / seeds (e.g. "poison present in top-k: 10/10 → [0.69, 1.0]").

## Closure gate (why still OPEN)
CLOSE only when: every `MASTER_CLAIM_LEDGER.csv` row's `evidence_package` resolves to an existing accepted
package (verified in `PROVENANCE.md`), **and** the authors have applied `MANUSCRIPT_CHANGE_LOG.md` and a final
overclaim sweep across abstract / introduction / results / discussion / conclusion / captions / response is clean.
