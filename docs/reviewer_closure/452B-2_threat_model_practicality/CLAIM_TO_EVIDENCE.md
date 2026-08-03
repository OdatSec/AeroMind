# 452B-2 — Claim → Evidence map

Rates are Clopper-Pearson exact 95% CIs. Every claim states exactly what was measured.

| # | Claim | Evidence | Value (95% CI) |
|---|---|---|---|
| C1 | The attack does not require unauthenticated store access: a signed authorized-writer reaches retrieval CCR 1.0. | RET A04/A05, 10/10 each | CCR 1.0 [0.69, 1.0], D0 and D1 |
| C2 | It also reaches retrieval CCR 1.0 via a perception-ingress path with no attacker-direct write. | RET A06, 10/10; `attacks/s18` + `uavsys/ingest/perception.py` (ingress modeled, not the RF chain) | CCR 1.0 [0.69, 1.0] |
| C3 | For the signed-episodic (A05) and perception (A06) paths, contamination carries to planner adoption. | PLAN A05, A06 × 2 models, `coordinate_adoption` | 20/20 per path [0.83, 1.0]; valid_plan 1.0 |
| C4 | The system's reflection promotes a low-privilege episodic write into trusted semantic memory (model-dependent). | TC-reflect (P1b), 40 runs | gpt-oss 10/10 [0.69,1.0]; qwen 1/10 [0.003,0.45]; source=reflection |
| C5 | Controls are clean. | A00 (RET D0/D1; TC-reflect) | CCR 0; TC-reflect promotion 0/10 per model [0, 0.31] |

## Headline (scoped)
> A realistic attacker that does NOT hold unauthenticated store access — via an authorized-writer compromise
> or a perception-ingress path — reaches retrieval CCR 1.0; for the signed-**episodic** (A05) and perception
> (A06) paths this carries to **planner coordinate-adoption 20/20 per path** across two local models. A
> low-privilege-plus-reflection path additionally **promotes** poison into trusted semantic memory
> (gpt-oss 10/10, qwen 1/10; top-k CCR and planner impact NOT measured). Attack side only; local models;
> **no physical execution**; distinct capabilities (not a ladder).

## Explicitly NOT claimed here
- **No planner impact** for A01, A04, or TC-reflect (retrieval/promotion only).
- **No top-k CCR** for TC-reflect (promotion only).
- **No physical execution** (PX4-SITL = P5/#6).
- **No universal cross-model success** (qwen reflection 1/10).
- **No full GNSS-spoofing chain** (A06 = ingress modeled).
- **No novelty claim** for reflection promotion (needs prior-work comparison — #7; MINJA is query-only, our method is not).
- **No defense claim.** Whether a stronger defense stops the signed insider = 452C-C4 = **Cam's WP4/WP5**;
  this attack-side package presents no defended-production evidence.
