# 452A memory-composition — Provenance & evidence integrity

Raw bundles git-ignored (`results_v3_raw/`).

## Pre-registration & frozen templates
- `docs/preregistration/PREREG_P2_memory_composition.md` — **sha256 `d9a3779336f9bcba…`**.
- Frozen payloads `uavsys/memory_composition.py` — **spec_hash `bc2b7b4b1b97158f…`** (recorded in every
  bundle's `configured.composition_spec_hash`): POISON_GENERIC (verbatim S01), POISON_ADAPTIVE,
  BENIGN_ONTOPIC, COMPETITOR_TRUE. No per-cell tuning.

## Embedder
- `nomic-embed-text` **`sha256:970aa74c0a90ef7482477cf8…`** (deterministic → zero-variance CIs).

## Accepted production (240 runs, `validity=production`, `commit_start=850177c…`, dirty=False)
24 cells × 10 seeds: Slice V (6 cells: 3 profiles × A01/A00), Slice O (12: 4 N × {generic,adaptive,A00}),
Slice K (6: 3 M × {generic,adaptive}).

## Accept-gate — PASS
`python3 experiments/p2_memory_composition.py --aggregate`: 240 bundles, 24 cells, A00 controls CCR=0,
Formula-(1) decomposition (`sim`/`recency`/`importance`) recorded per bundle.

## Metrics
CCR@k (poison share of top-k); poison min-rank; poison-beats-best-benign (bool); Formula-(1) decomposition.
Each bundle: `configured.composition` (slice/ot/cmp/poison), `composition_spec_hash`, `prereg_spec_hash`,
embedder digest, materialization hash.

## Curated artifacts (this directory)
- `cells.csv` (per-cell CCR + decomposition), `summary.json`.

## Relationship to `452A_part1_memory_generalization`
Part 1 established off-topic-volume invariance (still valid; = Slice V here). This package REVISES the
headline: the invariance holds only for off-topic filler; on-topic traffic evicts a generic poison, and an
adaptive attacker restores it. Part 1's bundles are untouched.
