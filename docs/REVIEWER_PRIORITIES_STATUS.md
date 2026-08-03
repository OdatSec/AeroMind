# Reviewer Priorities — Status, What's New, and Why (living document)

Tracks each reviewer concern from `RAID_2026_Current.pdf` reviews (452A/B/C). For every FINISHED
priority: **what is NEW** (the evidence we didn't have before) and **WHY** we chose that approach as
the strongest. Updated as priorities complete. Full detail in each `docs/reviewer_closure/*` package.

Legend: ✅ FINISHED (closed, accept-gated) · 🔵 IN PROGRESS (preflight done, production pending) · ⚪ PENDING · 🤝 CAM.

---

## ✅ A2 — Agent-count & task-assignment scalability (Reviewer 452A)
**Closure:** `docs/reviewer_closure/452A_part2_agents_assignment/` · 240 accepted production runs · accept-gate PASS.
- **What's NEW:** assignment-invariant logical retrieval exposure — cross-scout exposure = 1.0 and full-fleet
  blast for scouts {2,4,8,16} × assignment {fixed,random,dynamic}; A00 clean control = 0.0; blast count scales
  3→17 while fraction stays 1.0.
- **WHY this is the strongest approach:** poison-BLIND assignment (identical map for clean/attacked arm) +
  seed-indexed attacked-subtask schedule (removes the S1 confound) + Supervisor separated from Scout metrics +
  NEUTRAL hypothesis. This isolates assignment cleanly and yields an *on-thesis* result — task partitioning does
  NOT contain a single poisoned shared-memory record — which is stronger and more honest than "assignment matters."

## ✅ B2 (sub-1) — Top-k saturation & k-sensitivity (Reviewer 452B "CCR=1 by construction")
**Closure:** `docs/reviewer_closure/452B-1_topk_saturation_ksensitivity/` · RET k×budget sweep + exact asymmetric baseline + PLAN adoption · accept-gate PASS.
- **What's NEW:** CCR = min(budget,k)/k (directly-measured asymmetric scout-3/sup-5 aggregate = **0.82, not 1.0**);
  planner coordinate-adoption is **operating-point-dependent** (1.0 / 0.4 / 0.6 / 0.1 at k=3/5/10/20 — non-monotonic,
  no strict-decay claim).
- **WHY strongest:** concede the saturated cell honestly, then measure the *boundary* with an independent k×budget
  sweep + the paper's exact asymmetric topology. Converts the "overclaim" objection into a calibrated, falsifiable law.

---

## 🔵 P1 — Threat-model realism (Reviewers 452B-B1, 452C-C1) — THE decisive concern
**Prereg:** `PREREG_P1_threat_model_realism.md` (5e59befa). NOW arm 140 runs (D0+D1); defended arm deferred to FD1/Cam.
- **What's NEW (preflight, disposable):** poison reaches CCR=1.0 via **signed insider** (A04/A05) and the
  **legitimate perception pipeline** (A06) — NOT only unauthenticated writes. Under D1+D2 the trust defense
  **demotes the unsigned A01 to CCR 0** but the **signed A04/A05 stay at 1.0**.
- **WHY strongest:** execute the already-implemented authenticated + perception attacks with a capability table
  tied to **cited real-world vectors** (MINJA query-only, Greshake indirect, Bedrock/Copilot/MCP incidents). This
  *empirically* refutes "it's just bad design / unauthenticated writes" — the defense that fixes the naive write
  does not stop the authenticated insider. Corroborates Cam's "D1 blocks nothing on A04/A05/A06."
- **Status:** production not yet run.

## 🔵 P2 — Memory generalization (Reviewer 452A memory) — current closure was fragile
**Prereg:** `PREREG_P2_memory_composition.md` (frozen). NOW arm 240 RET runs; defense slice deferred to FD1.
- **What's NEW (preflight, disposable):** contamination is governed by the poison's **query-relevance rank**, not
  memory size. Generic poison **collapses** under on-topic benign traffic (CCR→0); an **adaptive query-matched**
  poison survives (CCR~1.0). Formula-(1) decomposition shows **`sim` (relevance) is the sole discriminator**.
- **WHY strongest:** honestly concede the reviewer is right *in kind* (memory state matters), then out-characterize
  it — identify the true governing variable + the adaptive-attacker response + the mechanism — instead of asserting
  a fragile "invariant 3→200" that only held for off-topic filler.
- **Status:** production harness building; production not yet run.

---

## ⚪ P3 — Deterministic-retrieval explanation + claim-calibration master table (452A-Q1, 452B-B2/B3). Not started.
## 🤝 P4 — Defense generalization (452C-C3/C4). **Owned by Cam (WP5/WP6), FD1-gated.** I supply frozen inputs + P1 baseline.
## ⚪ P5 — Real-system / external validity (452A-A3, 452C-C1). PX4-SITL closed-loop; heaviest, per ASIACCS_DECISION_MEMO.

## Reviewer term clarifications (grounded in the paper; [authors] to write into manuscript)
A-Q1 `r(eᵢ)`/`u(eᵢ)` = recency (exp decay) / keyword-importance (Formula 1, §4.3). · A-Q2 "operator" = human
mission-submitter (Fig 1). · A-Q3 "stealth-optimized entry" = S07 (few crafted entries, CCR 0.82 without flooding).
