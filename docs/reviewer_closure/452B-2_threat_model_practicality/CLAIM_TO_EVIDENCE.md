# 452B-2 — Claim → Evidence map

| # | Claim | Evidence | Value |
|---|---|---|---|
| C1 | The attack does not need an unauthenticated write: signed insider records reach retrieval dominance. | RET A04/A05, 20+20 runs | CCR 1.0 at D0 and D1 |
| C2 | The attack works via the legitimate perception pipeline with NO direct memory write. | RET A06, 20 runs; `attacks/s18` + `uavsys/ingest/perception.py` | CCR 1.0 |
| C3 | Provenance-signing alone (D1) stops none of them. | RET all attacks × D1 | CCR 1.0 (unchanged from D0) |
| C4 | The trust defense that catches the unauthenticated write does NOT catch the signed insider. | disposable D1+D2 reference diagnostic | A01 CCR→0; A04/A05 CCR 1.0 |
| C5 | The realistic/authenticated poison hijacks the planner, not just retrieval. | PLAN A05/A06 × 2 models, 40 runs, `coordinate_adoption` | adoption 1.0 (40/40); valid_plan 1.0 |
| C6 | Controls are clean. | A00 × {D0,D1}, 20 runs | CCR 0.0 |

## Headline (scoped)
> A realistic attacker that does NOT hold unauthenticated store access — via an authorized-writer
> compromise or a perception-ingress path — achieves retrieval contamination (CCR 1.0); for the
> signed-**episodic** (A05) and perception (A06) paths this carries to **planner coordinate-adoption 20/20
> per path** across two local models. A low-privilege-plus-reflection path additionally launders poison
> into trusted semantic memory (promotion 10/10 GPT-OSS, 1/10 Qwen; CCR/planner not measured). Attack side
> only; local models; no physical execution; distinct capabilities (not a ladder).

## Out of scope (NOT claimed here)
- Whether a **stronger** defense stops the signed insider → **452C-C4 = Cam WP4/WP5**, FD1-gated.
- 7-model parity (deferred infra); PX4-SITL physical execution (P5); the query-only/indirect TC-tier
  (cited via MINJA/Greshake, not executed here).
