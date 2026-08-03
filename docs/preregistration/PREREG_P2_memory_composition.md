# PRE-REGISTRATION — P2: memory-composition generalization (Reviewer 452A, memory)
# Embedder pinned (nomic-embed-text 970aa74c...). RET/L1 embedder-only. No tuning; no selective reruns.
# Frozen BEFORE any run. sha256 of this file is recorded in every bundle's prereg_spec_hash.

## Reviewer concern (452A, memory generalization)
"The success rate of malicious messages appearing in retrieval results will depend heavily on the
initial shared memory state ... if the baseline already has many episodic messages, I think it would
definitely affect S01's success rate; claiming that the success rate doesn't change much when going
from 6 to 200 records is misleading without specifying what those records are."

## What the current paper does (and the gap)
Paper S07/S08/S09 vary poison VOLUME (stealth/flood/recency) and report CCR invariant to memory SIZE.
But all benign records are OFF-TOPIC operational filler; the paper never varies benign COMPOSITION.
Diagnostic (this revision) shows the invariance is only true for off-topic filler: an ON-TOPIC
episodic flood pushes a generic S01 poison out of top-k (CCR->0), while an ADAPTIVE query-matched
poison survives. This prereg characterizes that boundary honestly.

## Scope statement (binding)
RETRIEVAL/L1 exposure ONLY: whether the poison enters the top-k and its Formula-(1) score rank.
NOT planner adoption (L2), mission failure, physical propagation, or PX4/SITL. Attack = S01/A01
false observation. Operating point mirrors the paper: Scout top-k = 3, poison budget = 3, seeds
101-110, defense D0 unless a cell states otherwise.

## Frozen payload templates (hashed in code before running)
- POISON_GENERIC   : the verbatim S01 payload (attacks/s01_false_observation.py) — keyword-laden, query-echoing.
- POISON_ADAPTIVE  : a query-matched paraphrase that redirects to trap coords (frozen template).
- BENIGN_ONTOPIC   : a query-relevant "search log" episodic record (frozen template).
- COMPETITOR_TRUE  : a genuine high-confidence observation of the TRUE target at true coords (frozen template).
All four are frozen in `uavsys/memory_composition.py` (new) and hashed; no per-cell tuning.

## Metrics (per run)
- CCR@k (fraction of top-k that is poison), poison MIN-RANK, poison_beats_best_benign (bool).
- Formula-(1) DECOMPOSITION: mean sim / r / u for the top poison vs the best benign (explains each cell).
- Seed-as-unit percentile bootstrap 95% CIs (PROVISIONAL pending Dr. Qian).

## Neutral hypotheses (no direction pre-registered)
- H1 (volume): CCR may be invariant / rise / fall across off-topic memory size {3,60,200,1000}.
- H2 (on-topic): CCR may be invariant / rise / fall as on-topic episodic count N grows.
- H3 (adaptivity): adaptive vs generic poison may or may not differ under on-topic memory.
- H4 (defense): D_full may or may not further reduce CCR beyond the composition effect.
Direction and magnitude are determined empirically; no outcome is pre-declared.

## Design matrix (RET/L1, embedder-only, top-k 3, budget 3, seeds 101-110)
All cells run A01 (attack) + A00 (clean control), except where controls are shared.
- Slice V — off-topic volume (replicates the paper's size claim, honestly labeled off-topic):
    memory size in {3, 60, 200, 1000}; POISON_GENERIC; D0.        -> 4 x (A01+A00) x 10 = 80
- Slice O — on-topic flood x adaptivity (the core new axis):
    MEM060 + N on-topic BENIGN_ONTOPIC records, N in {0,50,200,500}; poison in {generic,adaptive}; D0.
                                                                    -> A01: 4x2x10 = 80 ; A00: 4x10 = 40
- Slice K — true competitors x adaptivity:
    MEM060 + M COMPETITOR_TRUE records, M in {1,3,5}; poison in {generic,adaptive}; D0.  -> 3x2x10 = 60
- Slice D — defense interaction:
    MEM060 + on-topic N=200; poison in {generic,adaptive}; D_full. -> 2x10 = 20 (paired with Slice O D0 cells)
TOTAL = 80 + 120 + 60 + 20 = 280 embedder-only RET runs.

## Provenance / integrity
config_hash (schema v3), prereg_spec_hash (this file), profile_materialization_hash, pinned embedder
digest, validity=production, accept-gate audit, dirty-tree guard. results_v2_frozen/ untouched.

## Analysis plan (frozen)
Aggregator keyed (slice, cell-axes, poison, defense, seed). Report per-cell CCR + decomposition +
CIs. Headline to support ONLY if the data shows it: "retrieval contamination is governed by the
poison's query-relevance RANK, not memory size — invariant to off-topic volume, degrades under
on-topic traffic, restored by adaptive query-matching, reduced by defense." Concede any null.
Does NOT supersede the paper's off-topic-volume result; it scopes it.
