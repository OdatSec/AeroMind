# P3 — Claim → Evidence map

Each calibrated claim from `MASTER_CLAIM_LEDGER.csv` maps to an **already-accepted** evidence package
(no new experiments). Categories: **OC** = overclaim to correct · **M** = measured, retain (with uncertainty note).

| Claim | Facet | Cat. | Calibrated statement | Evidence package |
|---|---|---|---|---|
| C1 | 452B | OC | CCR=min(b,k)/k holds ONLY when ≥k poison outrank all benign & occupy top-k; at b=k = saturation *by construction*, not an invariant; rank dominance is empirical & can fail. | `452B-1_topk_saturation_ksensitivity` (sweep); `P2_452A_memory_generalization` (eviction) |
| C2 | 452B | OC | Retrieval dominance on all backbones (deterministic); S01 physical 100% on 7 models; S06 contagion 6/7 (Mistral 60%); S12 adoption model-dependent. | `P1_452B-452C_threat_model_realism`; paper Tables 5/6/8 |
| C3 | 452B | OC | "Deterministic regardless of model" scoped to S01; downstream adoption NOT universal (S06 6/7, S12 0–100%). | paper Tables 5/6/8; `452B-2` |
| C4 | 452A | OC | Size-invariance limited to tested **off-topic** compositions; **on-topic** content evicts the generic poison; contamination governed by relevance ranking, not record count. | `P2_452A_memory_generalization` |
| C5 | 452B | M | S01 100% planner adoption + 100% physical over 7×5 = 35/35; "zero variance" = deterministic retriever, report 35/35 with Clopper-Pearson. | paper Table 5 |
| C6 | 452B | M | System-wide CCR = **0.82** (9/11), **not 1** — supervisor k=5 leaves legit slots. Directly rebuts "CCR has to be 1." | `452B-1_topk_saturation_ksensitivity` |
| C7 | 452B | M | Constraint-injection (S12) adoption model-dependent (100%/60%/20%/0%). | `452B-1` (PLAN); paper Table 8 |

## The two required explicit statements
- **452B (facet 4):** CCR = 1 is arithmetic that holds **only conditional on ≥k poison records outranking the
  benign records and occupying the top-k**; at budget = k this is saturation *by construction*, not an
  architectural guarantee — and the rank-dominance condition is empirical and can fail (on-topic benign evicts).
- **452A (facet 5):** the 3-to-200 result is limited to the tested **off-topic** compositions; **on-topic**
  benign content evicted the generic poison. Contamination is governed by relative relevance ranking, not raw
  record count.

## Uncertainty treatment (all claims)
Deterministic CCR → **observed values**. Clopper-Pearson 95% CIs → **only** binary presence outcomes across
memory realizations / seeds. No bootstrap/"provisional" CI language.
