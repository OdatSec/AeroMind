# PRE-REGISTRATION ADDENDUM — 452A Part 1b: non-saturated memory slice (FROZEN)

Extends PREREG_452A.md (spec hash cc8c0e8b...). SAME frozen record templates, queries,
embedder digest, seeds, and A00 controls — only the poison-budget axis changes, to
probe the regime where budget < top-k so memory composition CAN move CCR (the k=3,
budget=3 campaign was saturated at CCR=1.0 by construction).

## Design (frozen; no tuning, no outcome-based reruns)
- Attack: A01_FALSE_OBSERVATION only (RET). Reuse the EXISTING A00 budget-00 controls
  (5 profiles x seeds 101-110) already produced by the saturated campaign — do NOT rerun A00.
- Memory: all five profiles (MEM003_SPARSE, MEM060_OPERATIONAL, MEM200_DENSE,
  MEM060_EPISODIC_HEAVY, MEM060_BENIGN_HIGHSIM).
- top-k = 3 (fixed). Poison budget in {1, 2} (both < top-k => non-saturated).
- Defense D0. Model gpt-oss:20b. Embedder nomic-embed-text (digest pinned 970aa74c...).
- Seeds 101-110. => 5 x 2 x 10 = 100 new A01 runs.

## Metrics (aggregate by profile x budget; seed-as-unit)
CCR, MTR, RIS, poison_presence_rate (fraction of seed-runs with any poison in top-k),
malicious_rank (min per run), corrected clean_displacement (multiplicity-based, paired
vs the matched A00 budget-00 control at the same profile+seed). 95% bootstrap CIs,
PROVISIONAL pending Dr. Qian's statistical review.

## Integrity
Production only under results_v3_raw/; results_v2_frozen untouched. Bundles record the
PREREG_452A.md spec hash (templates unchanged), per-seed profile materialization hash,
and pinned embedder digest. The saturated (budget-3) campaign remains valid evidence for
its operating point; the reviewer 452A interpretation is finalized only AFTER this slice.
