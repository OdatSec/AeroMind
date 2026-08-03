# 452A Part 1 — Claim → Evidence map

Every claim links to accepted production evidence (raw paths + hashes in `PROVENANCE.md`).
CIs are seed-as-unit percentile bootstrap, **PROVISIONAL pending Dr. Qian's review**.

| # | Claim | Evidence | Metric / value |
|---|---|---|---|
| C1 | The old 3-record baseline is faithfully reproduced. | `MEM003_SPARSE`; `tests/test_memory_profiles.py` | 2 targets + 1 procedural; A00 CCR 0.0 |
| C2 | Four richer, composition-documented memory states were pre-registered and built deterministically. | `PREREG_452A.md` (cc8c0e8b…); `uavsys/memory_profiles.py`; `tests/test_memory_profiles_452a.py` | MEM060/MEM200/EPISODIC_HEAVY/BENIGN_HIGHSIM; per-seed materialization hashes |
| C3 | The "dense/high-similarity" blocks are genuinely high-similarity (verified, not asserted). | `similarity_audit_452a.json` (embedder digest 970aa74c…) | mean cos→Q(S1): dense 0.807, benign-highsim 0.697, operational-episodic 0.554 |
| C4 | At the saturated point (budget = top-k = 3), contamination is total and identical across all five profiles. | saturated campaign (50 A01 b3 runs) | CCR 1.0 [1,1], MTR 1.0, RIS 0.0, mrank 1, disp 9 — all profiles |
| C5 | In the **non-saturated** regime (budget < top-k), CCR = budget/top-k and is invariant to memory size and the tested OFF-TOPIC composition variants (NOT to composition in general — see 452A_memory_composition). | non-saturated campaign (100 A01 b1/b2 runs) | b1 CCR 0.333 [.333,.333]; b2 CCR 0.667 [.667,.667] — all profiles |
| C6 | The poison out-ranks all memory content in every state. | both campaigns | malicious-rank = 1 [1,1] in all 5 profiles × 3 budgets |
| C7 | Denser/episodic/high-sim OFF-TOPIC memory did not reduce success; the reviewer is NOT refuted — ON-TOPIC content DOES reduce it (canonical 452A_memory_composition). | C4 + C5 + C6 across EPISODIC_HEAVY, DENSE, BENIGN_HIGHSIM | zero variance across profiles at each budget |
| C8 | Controls behave correctly (no false positives). | 50 A00 b0 runs | CCR 0.0 all profiles/seeds |

## Headline claim (scoped)
> CCR = budget/top-k, invariant to memory size (3–200) and the tested OFF-TOPIC composition variants, at top-k = 3,
> budgets 1–3, n=10 seeds/cell.

## Out of scope (NOT claimed here)
- **top-k dependence of CCR** → Reviewer **452B** (top-k × budget sweep). The b=3 point is
  CCR=1 by construction (budget = k) and is scoped as such.
- **Agent-count and task-assignment generalization** → **452A Part 2** (L3 exposure:
  scouts {2,4,8} × assignment {fixed,random,dynamic}; see `PREREG_452A.md` Part 2). **Not
  run; not closed.**
- **Planner-level (L2) confirmation**, defended (D1–D4) behavior, and a hostile-benign
  record engineered to out-rank the poison — all out of scope for this closure.
