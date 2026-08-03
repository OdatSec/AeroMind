# 452A memory-composition — Provenance & evidence integrity

Raw bundles git-ignored (`results_v3_raw/`).

## Pre-registration & frozen templates
- `docs/preregistration/PREREG_P2_memory_composition.md` — **sha256 `d9a3779336f9bcba…`**.
- Frozen payloads `uavsys/memory_composition.py` — **spec_hash `bc2b7b4b1b97158f…`** (recorded in every
  bundle's `configured.composition_spec_hash`): POISON_GENERIC (verbatim S01), POISON_ADAPTIVE,
  BENIGN_ONTOPIC, COMPETITOR_TRUE. No per-cell tuning.

## Embedder
- `nomic-embed-text` **`sha256:970aa74c0a90ef7482477cf8…`**. Deterministic → CCR reported as **observed
  values** (not sampling CIs); the **binary** "poison present in top-k" outcome uses **Clopper-Pearson** CIs.

## Accepted production — THREE campaigns, **500 runs = 370 A01 + 130 controls** (verified from bundles)
- **Campaign A** — Part 1 (`PREREG_452A.md`, cc8c0e8b): 200 = 150 A01 + 50 controls (off-topic variants × budgets).
- **Campaign B** — composition (`PREREG_P2_memory_composition.md`, d9a37793): 240 = 170 A01 + 70 controls (V=60, O=120, K=60).
- **Campaign C** — P2b hardening (`PREREG_P2b_hardening.md`, 17f93d7e): 60 = 50 A01 + 10 controls.
All present in `results_v3_raw/` under their prereg hashes; verified by hash-filtered bundle count. Attack =
**A01/S01 only** in all three (composition isolation; orthogonal to P1). RET/L1 only.

## Campaign C — P2b hardening (`PREREG_P2b_hardening.md` sha256 `17f93d7e…`) — 60 runs
Frozen templates `uavsys/memory_composition_p2b.py` (spec_hash `9821cddf…`): STRONGER_COMPETITOR + 3
adaptive phrasings (adapt_v2/v3/v4). A01/S01, RET only, seeds 101–110. Test 1 = 30 (M=1 A01, M=3 A01,
M=3 A00 control); Test 2 = 30 (adapt_v2/v3/v4 A01). **All 60 accepted, 0 rejected/failed.** Deterministic
(all seeds identical per cell) → CCR observed values, binary "present in top-k" → Clopper-Pearson. Aggregate:
`experiments/p2b_hardening.py --aggregate`. Preflight (seed 9001, emit=False) is separate from these accepted runs.

## Accept-gate — PASS
`python3 experiments/p2_memory_composition.py --aggregate`: 240 bundles, 24 cells, A00 controls CCR=0,
Formula-(1) decomposition (`sim`/`recency`/`importance`) recorded per bundle. P2b: 60 bundles, control CCR=0.

## Metrics
CCR@k (poison share of top-k); poison min-rank; poison-beats-best-benign (bool); Formula-(1) decomposition.
Each bundle: `configured.composition` (slice/ot/cmp/poison), `composition_spec_hash`, `prereg_spec_hash`,
embedder digest, materialization hash.

## Curated artifacts (this directory)
- `cells.csv` (per-cell CCR + decomposition), `summary.json`.

## Conclusion & package status
This is the **canonical** P2 package; it **subsumes** Part 1 (Part 1's off-topic-volume result = Slice V
here, retained under `part1/`) and **supersedes Part 1's headline.** Final framing: raw memory *size* did
not matter for the tested off-topic profiles; **on-topic content evicts the generic poison**; a
**higher-ranking benign record evicts the poison (causal, P2b Test 1)**; and adaptive restoration is
**template-dependent, not general** — across the four adaptive phrasings tested (1 original + the **three**
frozen P2b templates adapt_v2/v3/v4), only adapt_v2 reached rank-1, adapt_v4 held rank-2 (CCR 0.333), and
**adapt_v3 failed entirely (CCR 0)**. We therefore **do not** claim "invariant to composition," **do not**
say the reviewer was "refuted," and **do not** claim general adaptive robustness.

**This is a CURATED closure package** — it contains the reports, per-cell aggregate CSVs, score audit,
pre-registrations, and campaign summaries, **but NOT** the 500 raw per-run evidence bundles or the
experiment scripts. Those live in the repository: raw bundles under `results_v3_raw/` (git-ignored, on the
machine); scripts at `experiments/p2_memory_composition.py`, `experiments/p2b_hardening.py`, and the frozen
template modules `uavsys/memory_composition.py`, `uavsys/memory_composition_p2b.py`. All results are
reproducible from those via the `--aggregate` commands in the REPORT. Part 1's raw bundles are untouched.
