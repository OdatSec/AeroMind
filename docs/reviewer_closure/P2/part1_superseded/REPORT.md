# Reviewer 452A — Part 1 (Memory Generalization): Closure Report

**Status: CLOSED for the tested envelope** — RET, top-k = 3, poison budgets ∈ {1, 2, 3},
five pre-registered memory profiles, seeds 101–110. **Agent-count and task-assignment
generalization remain open as Part 2** (see `CLAIM_TO_EVIDENCE.md` §Out of scope).

Evidence: **200 accepted production runs** across two campaigns (100 saturated + 100
non-saturated), plus 50 reused A00 controls. Accept-gate PASS on both. Raw bundles under
`results_v3_raw/` (git-ignored); exact paths + hashes in `PROVENANCE.md`.

---

## 1. Reviewer concern (452A, Part 1)
> "The attack is demonstrated on an extremely simple initial memory ('two legitimate
> semantic targets and one benign procedural template'); it's unclear whether the attack
> would be successful with different initial memory states. E.g., if the baseline already
> has many episodic messages, I think it would definitely affect S01's success rate;
> claiming that the success rate doesn't change much when going from 6 to 200 records is
> somewhat misleading without specifying what those records are."

## 2. Old paper — evidence & claim
- **Initial memory:** a single 3-record state = 2 semantic targets (person, car) + 1
  procedural template. (Reproduced here as `MEM003_SPARSE`.)
- **Claim:** attack success ≈ invariant from ~6 → 200 records, **without documenting the
  composition** of those records.

## 3. Pre-registered design (frozen before any attack run)
- **Spec:** `docs/preregistration/PREREG_452A.md` — sha256 `cc8c0e8b…441e073`.
- **Addendum (non-saturated slice):** `docs/preregistration/PREREG_452A_nonsaturated.md`
  — sha256 `9884e94e…09a7ef`. Same frozen templates; only the poison-budget axis extends.
- **Discipline:** templates frozen before outcomes; no tuning; no selective reruns;
  materialization hashes recorded per (profile, seed); embedder pinned by digest.

## 4. Five memory profiles (composition documented)
| Profile | n | Composition (by layer/category) |
|---|---|---|
| `MEM003_SPARSE` | 3 | 2 semantic/target + 1 procedural (the old baseline) |
| `MEM060_OPERATIONAL` | 60 | semantic 12 (2 target, 2 fact, 8 state), procedural 6, coordination 12, episodic 30 |
| `MEM200_DENSE` | 200 | operational scaled + **60 dense-similar** (target/coordinate vocabulary) |
| `MEM060_EPISODIC_HEAVY` | 60 | **50 episodic** (83%) + 2 target,1 fact,2 state,2 proc,3 coord — *the reviewer's "many episodic messages"* |
| `MEM060_BENIGN_HIGHSIM` | 60 | **40 high-similarity benign** distractors at the exact target coords + 2 target,2 state,2 proc,2 coord,12 episodic |

Deterministic builder (`uavsys/memory_profiles.py`), `random.Random(seed)`, byte-identical
per (profile, seed). Per-seed materialization hashes in `PROVENANCE.md` / bundle manifests.

## 5. Pre-attack similarity audit (verifies the "dense/high-sim" design, embedder-pinned)
Embedder **nomic-embed-text**, model-layer digest `sha256:970aa74c…0139d4f` (pinned; runs
abort on mismatch). Mean cosine similarity to the target query Q(S1), pooled over seeds:

| Block | mean cos → Q(S1) | records ≥ 0.60 |
|---|---|---|
| `MEM200_DENSE` dense_similar | **0.807** | 600/600 |
| `MEM060_BENIGN_HIGHSIM` benign_highsim | **0.697** | 400/400 |
| `MEM060_OPERATIONAL` episodic (baseline noise) | 0.554 | 2/300 |

Full artifact: `docs/preregistration/similarity_audit_452a.json`.

## 6. Exact configuration
`Attack A01_FALSE_OBSERVATION (+ A00_CLEAN control) · Task T01_SEARCH_RESCUE ·
Eval RET (L1) · Model gpt-oss:20b · Embedder nomic-embed-text (digest-pinned) ·
top-k 3 · poison budget ∈ {0(control),1,2,3} · Defense D0 · seeds 101–110 (n=10).`
CI method: percentile bootstrap, seed-as-unit — **PROVISIONAL pending Dr. Qian**.

## 7. Accept-gate results
| Campaign | runs | complete+checksum | production+clean-tree | prereg-hash | mat-hash | embedder-digest | CCR-recompute | unique paths | FAIL |
|---|---|---|---|---|---|---|---|---|---|
| Saturated (b=3) + controls (b=0) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 |
| Non-saturated (b=1, b=2) | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 100 | 0 |

## 8. Results (seed-as-unit, n=10, 95% bootstrap CI)
**Saturated (budget = top-k = 3):** identical for all five profiles —
CCR 1.0 [1.0,1.0], MTR 1.0, RIS 0.0, malicious-rank 1 [1,1], clean-displacement 9.0 [9,9];
A00 control CCR 0.0.

**Non-saturated (budget < top-k):** identical for all five profiles —
| budget | CCR | poison-presence | malicious-rank | clean-displacement |
|---|---|---|---|---|
| 1 | **0.333 [0.333,0.333]** | 1.0 | 1 [1,1] | 3.0 [3,3] |
| 2 | **0.667 [0.667,0.667]** | 1.0 | 1 [1,1] | 6.0 [6,6] |

**Combined:** `CCR = budget / top-k` exactly (0.333 / 0.667 / 1.0), with **zero variance
across memory size, composition, and seed**; the poison ranks **#1 in every profile and
every seed** (malicious-rank = 1).

## 9. Interpretation  ⚠️ SUPERSEDED — see the canonical package `452A_memory_composition`
At the tested envelope, retrieval contamination is governed by the poison-budget-to-top-k ratio and is
invariant to memory size (3–200 records) **across the tested OFF-TOPIC composition variants** (operational,
episodic-heavy, dense-similar, high-similarity-benign). **CORRECTION:** all five Part-1 profiles are
*off-topic*; this does **NOT** establish invariance to memory composition in general, and it does **NOT**
"refute" the reviewer. The canonical study `452A_memory_composition` (Campaign B) shows that **ON-TOPIC**
benign content **evicts** the generic poison — i.e., composition **does** matter and the reviewer's concern
is **partly correct.** Read Part 1 only as: *raw off-topic size/variants did not reduce the generic attack;
the on-topic case is in the canonical package.*

## 10. Limitations (carry into the manuscript)
- **Operating point:** closed only for **top-k = 3, budgets 1–3**. CCR-vs-top-k is the
  separate **452B** k×budget sweep; the b=3 point is CCR=1 by construction (budget=k).
- **Determinism:** RET retrieval is deterministic (no temperature), hence zero variance;
  the invariance is a property of embedding ranks, not a statistical average over noise.
- **Untested regime:** we did not construct a benign memory record *more* query-relevant
  than the poison; our high-similarity-benign block (0.697) is the strongest realistic
  competitor and does not dislodge the poison (0.7+). A hostile-benign record that
  out-ranks the poison is out of scope.
- **Metric note:** `clean_displacement` uses multiplicity (multiset) counting after fixing
  an earlier set()-collapse undercount on duplicate-text records; verified on existing
  bundles (no rerun).
- **Scope:** RET (L1) only; planner-level (L2) confirmation and agent-count/assignment
  (Part 2) are separate.

## 11. Final scoped claim  ⚠️ SUPERSEDED by `452A_memory_composition`
> "Across five pre-registered, composition-documented **OFF-TOPIC** memory states (3–200 records,
> incl. episodic-heavy, dense-similar, and high-similarity-benign) and poison budgets 1–3
> at top-k = 3, coordinate-hijack retrieval contamination follows CCR = budget/top-k and is
> invariant to memory size and **to these off-topic composition variants** (n=10 seeds/cell). This
> does **NOT** establish invariance to composition in general: the canonical study shows **on-topic**
> content evicts the generic poison. We replace the earlier undocumented size-invariance statement with
> this characterized, CI-backed **off-topic** result. The top-k dependence (452B) and agent-count/assignment
> generalization (Part 2) are addressed separately."

---
> **UPDATE (memory-composition study, `452A_memory_composition`):** the "invariant 3→200" result here is
> for *off-topic* filler only. On-topic benign traffic evicts a generic poison (CCR→0); an adaptive
> query-matched attacker restores it. Contamination is governed by query-relevance rank, not memory size.
> See `docs/reviewer_closure/452A_memory_composition/`.
