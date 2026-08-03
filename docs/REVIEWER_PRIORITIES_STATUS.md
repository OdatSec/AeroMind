# Reviewer Priorities — Status, What's New, and Why (living document)

One unified priority numbering across all three reviews (452A/B/C), ranked by leverage on the accept
decision. For each finished item: **what's NEW** + **WHY it's the strongest approach**. Legacy labels
(A2/B2/P1…) noted for continuity. Full detail in each `docs/reviewer_closure/*` package.

Legend: ✅ CLOSED (accept-gated) · 🔵 RUNNING · ⚪ PENDING · 🤝 CAM · ✍️ AUTHORS.

| # | Priority | Reviewer(s) | Status | old label |
|---|---|---|---|---|
| 1 | Threat-model realism | 452B-B1 + 452C-C1 | ✅ **CLOSED** | P1 |
| 2 | Memory generalization | 452A memory | ✅ **CLOSED** (500 runs, 3 campaigns) | P2 |
| 3 | Overclaim / claim calibration | 452B-B2 + 452A 6→200 | ⚪ next (3a done, 3b pending) | P3 |
| 3a | └ top-k / k-sensitivity | 452B | ✅ CLOSED | B2 |
| 4 | Defense generalization + signed-but-malicious | 452C-C3/C4 | 🤝 Cam · FD1-gated | P4 |
| 5 | Agent count & task assignment | 452A | ✅ CLOSED | A2 |
| 6 | Real-system / closed mission-loop | 452A-A3 + 452C-C1 | ⚪ later | P5 |
| 7 | Writing (novelty, formula, terminology) | 452C + 452A | ✍️ authors | — |

---

## ✅ #1 Threat-model realism — 452B-B1 + 452C-C1  (`452B-2_threat_model_practicality`)
180 accepted production runs (100 RET + 40 PLAN + 40 TC-reflect), accept-gate PASS. Rates with
Clopper-Pearson 95% CIs.
- **What's NEW (calibrated):** the attack does not require unauthenticated store access. Retrieval CCR = 1.0
  (10/10 per cell, CI [0.69,1.0]) via authorized-writer compromise (A04/A05), perception-ingress (A06), and
  A01. **Planner coordinate-adoption = 20/20 per path (CI [0.83,1.0])** for the signed-**episodic** (A05)
  and perception (A06) paths across both local models; A01/A04 were retrieval-only (planner not measured).
- **What's NEW (TC-reflect, +40 runs, executed):** attacker makes one low-privilege episodic write; the
  system's **own reflection loop promotes it into trusted semantic memory** (`source=reflection`). Promotion
  gpt-oss 10/10 [0.69,1.0], qwen 1/10 [0.003,0.45] (model-dependent), controls 0/10. **top-k CCR and planner
  impact NOT measured for this path.**
- **WHY this approach:** replaced the single "can write memory" assumption with **distinct realistic entry
  paths tied to documented vectors** (authorized-writer compromise; GNSS-spoofed perception — INGRESS
  modeled; low-privilege-write + reflection) — anchors Bedrock/Copilot/MCP, cites MINJA/Greshake. Shows the
  attack does not need unauthenticated store access. **NOT claimed:** a ranked ladder, planner impact for
  A01/A04/TC-reflect, physical execution, cross-model universality, or novelty (needs prior-work comparison).
  Defense is Cam's WP (FD1). 180 runs total.

## ✅ #2 Memory generalization — 452A (canonical `452A_memory_composition`; consolidates `452A_part1`) — CLOSED
**Evidence base = 500 runs = 370 A01/S01 + 130 controls** (verified from bundles): Campaign A / Part 1
(`PREREG_452A.md`, 200 = 150+50, off-topic composition variants × budgets) + Campaign B / composition
(`PREREG_P2_memory_composition.md`, 240 = 170+70) + Campaign C / P2b (`PREREG_P2b_hardening.md`, 60 = 50+10).
Attack = **A01/S01 only, RET only** (isolates memory composition; **orthogonal to P1**; does NOT generalize
to A04/A05/A06/TC-reflect). CCR deterministic → observed values; binary present/absent → Clopper-Pearson CI.
**Conclusion: relative relevance ranking — not raw memory size — governs top-k occupancy; higher-ranking
benign records evict poison; adaptive restoration is template-dependent and fragile, not generally robust.**
- **Result (calibrated):** raw memory **size** did not matter for the tested **off-topic** profiles
  (MEM003/060/200 → CCR 1.0); **on-topic** benign content **evicted** the generic poison (CCR 1.0→0); a
  query-matched **adaptive** poison **restored** retrieval **in the tested configuration** (one frozen
  template; CCR 1.0 at N≤200, 0.667 at N=500). Same-template competitor = a **0.005 near-tie** (not robust).
- **NOT claimed:** "invariant to composition"; that the reviewer was "refuted" (reviewer is **partly
  correct** — composition matters); a general adaptive law; generalization to P1 entry paths.
- **Hardening (P2b, +60 runs, A01/RET):** **Test 1 CONFIRMED** — a higher-ranking benign competitor (0.897 >
  poison 0.817) displaces (M=1→CCR 0.667) and **evicts** (M=3→CCR 0) the poison → relevance-ranking is
  causal. **Test 2 MIXED** — adaptive restoration is **template-dependent, NOT general**: of 3 frozen
  phrasings only adapt_v2 reached rank-1 (fragile +0.005), adapt_v4 rank-2 (CCR 0.333), **adapt_v3 failed
  (CCR 0)**. **No general-adaptive-robustness claim.**
- **CLOSED** (reviewed & signed off): scope caveats retained honestly — one on-topic template, 3 discrete
  off-topic sizes (no MEM1000), A01/S01 + RET only; no general-adaptive-robustness claim.

## ✅ #3a Top-k / k-sensitivity — 452B  (`452B-1`)
CCR = min(budget,k)/k; asymmetric aggregate 0.82 (not 1.0); adoption operating-point-dependent. Concede the
saturated cell, measure the boundary.

## ✅ #5 Agent count & task assignment — 452A  (`452A_part2`)
Assignment-invariant logical exposure (240 runs). Poison-blind + schedule-decoupled design; on-thesis.

---

## ⚪ #3b Claim-calibration master table — 452B overclaim + 452A 6→200 — NEXT
Consolidate all closures + #1/#2 into one claim-to-evidence table; tag saturated-by-construction cells and
operating-point dependence. Cheap; depends on #1/#2 (now done).

## 🤝 #4 Defense generalization + signed-but-malicious — 452C — Cam WP4/WP5, FD1-gated
## ⚪ #6 Real-system / closed mission-loop — 452A + 452C — later (PX4-SITL, per ASIACCS_DECISION_MEMO)
## ✍️ #7 Writing — 452C novelty; 452A formula r(eᵢ)/u(eᵢ) (resolved: recency/keyword-importance); 452A "operator"/"stealth-optimized" (resolved: human mission-submitter / S07)

---
**Now:** #1, #2, #3a, #5 CLOSED. Next together: **#3b** (claim-calibration master table).
