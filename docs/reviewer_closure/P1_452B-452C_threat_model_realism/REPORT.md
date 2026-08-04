# Reviewer 452B-B1 + 452C-C1 — Threat-Model Practicality: Closure Report

**Status: CLOSED for the tested envelope (attack side).** Calibrated finding:

> In the tested AeroMind environment, the **signed-insider (episodic, A05)** and **modeled
> perception-ingress (A06)** paths achieved **retrieval CCR = 1.0** and **20/20 planner coordinate-adoption
> per path** across two local models. Separately, the **reflection pipeline promoted low-trust episodic
> content into trusted semantic memory in 10/10 GPT-OSS runs and 1/10 Qwen runs**; top-k CCR and planner
> impact were **not** measured for this path. These results demonstrate that the attack does **not** depend
> exclusively on unauthenticated direct memory-store access, but they do **not** establish physical
> execution or universal success across models.

Retrieval CCR = 1.0 was also measured for the unauthenticated (A01) and signed-semantic (A04) paths; those
two were **not** taken to the planner. **Evidence: 180 accepted production runs** (100 RET + 40 PLAN +
**40 TC-reflect**), accept-gate PASS. Local models gpt-oss:20b, qwen2.5:7b. Rates reported with exact
Clopper-Pearson 95% CIs (n=10 per cell, n=20 per planner path). Raw bundles under `results_v3_raw/`
(git-ignored); hashes in `PROVENANCE.md`.

---

## 1. Reviewer concerns
> **452B-B1:** "The threat model is quite strong… does not validate how practical it is for actual UAV systems."
> **452C-C1 (biggest concern):** "assumes adversarial write access but does not show how such access would
> realistically arise… UAV agents usually operate in a more closed mission-control loop."

## 2. Re-design: distinct realistic entry paths (NOT a ranked ladder)
The paper assumed one flat capability ("can write to memory"). We instead evaluate **several distinct,
incomparable realistic entry paths** and measure what each achieves — the attack does not require the
strong "unauthenticated store access" assumption. These are different threat actors, not a weakest→strongest
ordering.

## 3. Results (180 production runs; seeds 101–110; Clopper-Pearson 95% CI)
### Retrieval (RET/L1) — CCR, 100 runs
| attack | entry path | CCR (D0) | CCR (D1) | per-cell (n=10) |
|---|---|--:|--:|---|
| A00 clean | — | 0.0 | 0.0 | 0/10, CI [0, 0.31] |
| A01 | unauthenticated direct write | 1.0 | 1.0 | 10/10, CI [0.69, 1.0] |
| A04 | signed semantic (authorized writer + key) | 1.0 | 1.0 | 10/10, CI [0.69, 1.0] |
| A05 | signed episodic (authorized writer + key) | 1.0 | 1.0 | 10/10, CI [0.69, 1.0] |
| A06 | perception ingress (no attacker-direct write) | 1.0 | 1.0 | 10/10, CI [0.69, 1.0] |

### Planning (PLAN/L2) — planner routes a goto to the trap, 40 runs (A05, A06 only)
| attack | model | coordinate_adoption | valid_plan |
|---|---|--:|--:|
| A05 signed episodic | gpt-oss:20b | 1.0 (10/10) | 1.0 |
| A05 signed episodic | qwen2.5:7b | 1.0 (10/10) | 1.0 |
| A06 perception | gpt-oss:20b | 1.0 (10/10) | 1.0 |
| A06 perception | qwen2.5:7b | 1.0 (10/10) | 1.0 |
Per path (n=20): adoption 20/20, CI [0.83, 1.0]. **A01 and A04 were retrieval-only — not taken to the planner.**

### TC-reflect — reflection promotion, 40 runs (executed)
Attacker plants **one low-privilege episodic** false observation (a write — not query-only); the
Supervisor's own `consolidate_memory()` (Park-2023 reflection) promotes it into **trusted semantic memory**
(`source=reflection`). We measured **promotion only** — top-k CCR and planner impact were **not** measured.
| model | promotion | CI (n=10) | laundered source |
|---|--:|---|---|
| gpt-oss:20b | 10/10 (1.0) | [0.69, 1.0] | reflection |
| qwen2.5:7b | 1/10 (0.1) | [0.003, 0.45] | reflection |
| A00 controls | 0/10 per model (0.0) | [0, 0.31] | — |
Strongly **model-dependent** (qwen's reflection JSON often fails to parse).

## 4. Interpretation (scoped)
Retrieval contamination (CCR = 1.0) is reached via an authorized-writer compromise (A04/A05), a
perception-ingress path (A06), and the unauthenticated write (A01) — so the attack does **not** require
unauthenticated store access. For the signed-episodic (A05) and perception (A06) paths this carried to
**20/20 planner adoption** across two models. The reflection path additionally **promotes** low-trust
episodic content into trusted semantic memory (model-dependent). This answers B1/C1 **without** claiming
every path was taken end-to-end, CCR for the reflection path, physical execution, or cross-model universality.

## 5. Limitations — exactly what each path did and did NOT demonstrate
- **Distinct, incomparable capabilities — NOT a ranked ("lowest/highest") ladder.**
- **Signed insider (A04/A05)** needs control of an **authorized writer** that holds signing authority — not "just a key."
- **Perception (A06) = no attacker-direct write** (the legitimate pipeline writes it), and it models the
  **ingress point only** — the **full RF GNSS-spoofing chain was not executed.**
- **TC-reflect requires one low-privilege episodic write** (it is **not** "query-only" or "no write"). We
  measured **promotion only — top-k CCR and planner hijack were NOT measured** — and it is model-dependent.
- **Planner hijack measured for A05 and A06 only** (20/20 each). A01 and A04 were retrieval-only.
- **No physical execution** (PX4-SITL closed-loop is P5/#6).
- **Local models only** (gpt-oss:20b, qwen2.5:7b); 7-model parity deferred.
- **Novelty NOT claimed.** Whether reflection-based promotion is novel vs MINJA / reflection-attack /
  AgentPoison requires a prior-work comparison (task for #7). MINJA is *query-only*; our tested method is a
  low-privilege write + reflection, so we do **not** call this path "query-only."
- **Defense is out of scope (Cam / FD1).** This attack-side package makes **no defended-production claim**;
  whether a stronger defense stops the signed insider is 452C-C4 = Cam's WP4/WP5.
- Rates reported with exact **Clopper-Pearson 95% CIs** (n=10 or n=20) — a point estimate of 1.0 at n=10
  still carries a CI lower bound of 0.69, so results are stated as proportions with uncertainty, not as "always."

## 6. Reproduce
```
python3 experiments/campaign_p1_threat_model.py --audit          # RET + PLAN
python3 experiments/p1b_indirect_consolidation.py --aggregate    # TC-reflect
```
Read only P1/P1b production bundles (filtered by prereg hash); run no experiments.
