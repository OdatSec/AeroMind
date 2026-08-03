# Reviewer Priorities — Status, What's New, and Why (living document)

One unified priority numbering across all three reviews (452A/B/C), ranked by leverage on the accept
decision. For each finished item: **what's NEW** + **WHY it's the strongest approach**. Legacy labels
(A2/B2/P1…) noted for continuity. Full detail in each `docs/reviewer_closure/*` package.

Legend: ✅ CLOSED (accept-gated) · 🔵 RUNNING · ⚪ PENDING · 🤝 CAM · ✍️ AUTHORS.

| # | Priority | Reviewer(s) | Status | old label |
|---|---|---|---|---|
| 1 | Threat-model realism | 452B-B1 + 452C-C1 | ✅ **CLOSED** | P1 |
| 2 | Memory generalization | 452A memory | ✅ **CLOSED** | P2 |
| 3 | Overclaim / claim calibration | 452B-B2 + 452A 6→200 | ⚪ next (3a done, 3b pending) | P3 |
| 3a | └ top-k / k-sensitivity | 452B | ✅ CLOSED | B2 |
| 4 | Defense generalization + signed-but-malicious | 452C-C3/C4 | 🤝 Cam · FD1-gated | P4 |
| 5 | Agent count & task assignment | 452A | ✅ CLOSED | A2 |
| 6 | Real-system / closed mission-loop | 452A-A3 + 452C-C1 | ⚪ later | P5 |
| 7 | Writing (novelty, formula, terminology) | 452C + 452A | ✍️ authors | — |

---

## ✅ #1 Threat-model realism — 452B-B1 + 452C-C1  (`452B-2_threat_model_practicality`)
140 accepted production runs (100 RET + 40 PLAN), accept-gate PASS.
- **What's NEW:** the attack needs NO unauthenticated write. **Signed insiders** (A04/A05, valid key) and
  the **legitimate perception pipeline** (A06, no direct write) reach **RET CCR 1.0** (D0 and D1) and
  **100% planner coordinate-adoption** on both local models (40/40). The provenance defense that demotes
  the unauthenticated A01 (CCR→0 under D1+D2) leaves signed A04/A05 at 1.0.
- **What's NEW (TC-indirect, +40 runs):** the lowest-capability tier — attacker plants one unsigned
  low-privilege episodic; the system's **own reflection loop launders it into trusted semantic memory**
  (`source=reflection`). gpt-oss:20b **promotion 1.0**, qwen 0.1 (model-dependent), controls 0.
- **WHY strongest:** re-designed the single "can write memory" assumption into **capability tiers tied to
  documented real vectors** — flagship = **GNSS-spoofed perception** (a real UAV attack, closed-loop,
  indirect); lowest tier = **self-laundering via the agent's own reflection** — with real-world anchors
  (Bedrock/Copilot/MCP) and academic cites (MINJA/Greshake). The attack wins at the *lowest* realistic
  capability, refuting "strong/impractical / just bad design" with evidence. Corroborates Cam's WP5.
  **180 runs total** (100 RET + 40 PLAN + 40 TC-indirect).

## ✅ #2 Memory generalization — 452A  (`452A_memory_composition`)
240 accepted production runs, deterministic, accept-gate PASS.
- **What's NEW:** contamination is governed by the poison's **query-relevance rank**, not memory size:
  invariant to off-topic volume (3→200, CCR 1.0), **collapses to 0** under on-topic benign traffic
  (generic CCR 1.0→0), **restored** by an adaptive query-matched poison (CCR 1.0). Formula-(1)
  decomposition shows `sim` is the sole discriminator (generic 0.729 < on-topic 0.838 < adaptive 0.854).
- **WHY strongest:** concede the reviewer is right *in kind*, then out-characterize it — the true governing
  variable + adaptive-attacker boundary + mechanism — instead of the fragile "invariant 3→200" (which held
  only for off-topic filler = the "misleading" charge). Revises `452A_part1` honestly; off-topic facet kept.

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
**Now:** #1, #2, #3a, #5 CLOSED. Next together: **#3b** (claim calibration).
