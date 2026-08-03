# Reviewer 452B-B1 + 452C-C1 — Threat-Model Practicality: Closure Report

**Status: CLOSED for the tested envelope (attack side).** Calibrated finding:

> In the tested AeroMind environment, the **signed-insider (episodic, A05)** and **modeled
> perception-ingress (A06)** paths achieved **CCR = 1.0** and **20/20 planner coordinate adoption per
> path** across two local models. Separately, the **reflection pipeline promoted low-trust episodic
> content into trusted semantic memory in 10/10 GPT-OSS runs and 1/10 Qwen runs**; top-k CCR and planner
> impact were **not** measured for this path. These results demonstrate that the attack does **not**
> depend exclusively on unauthenticated direct memory-store access, but they do **not** establish
> physical execution or universal success across models.

Additionally, retrieval CCR = 1.0 was measured for the unauthenticated (A01) and signed-semantic (A04)
paths, but those two were **not** taken to the planner. Evidence: **180 accepted production runs**
(100 RET + 40 PLAN + 40 TC-indirect), accept-gate PASS. Local models gpt-oss:20b, qwen2.5:7b. See
§Limitations for exactly what each path did and did not demonstrate.

---

## 1. Reviewer concerns
> **452B-B1:** "The threat model is quite strong for the attack… it's more like a bad design. We all
> know unauthenticated memory writes are bad. The paper does not validate how practical this threat
> model is for actual UAV systems."
> **452C-C1 (their biggest concern):** "The paper assumes adversarial write access to shared memory but
> does not show how such access would realistically arise… UAV agents usually operate in a more closed
> mission-control loop."

## 2. What the paper assumed (and the gap)
A single attacker capability: "can inject or alter records in shared long-term memory before retrieval."
Reviewers read this as the *strongest* attacker and as "just bad design." The paper did not (a) ground
the write access in realistic UAV vectors, nor (b) show the attack survives when writes ARE authenticated.

## 3. Re-design: graded attacker-capability tiers tied to REAL vectors
Instead of one strong assumption, a capability table (see `CAPABILITY_TABLE.md`), each tier tied to a
documented real-world vector. The flagship, most-realistic UAV vector is **perception ingestion** — the
attacker corrupts a sensor input (GNSS spoof / adversarial patch / compromised sensor driver) and the
*legitimate* pipeline writes the attacker-influenced observation as a trusted record. This is the
"indirect / query-only" injection that 452C-C1 itself calls realistic, and it is UAV-specific.

## 4. Results — 140 production runs (seeds 101–110)
### Retrieval (RET/L1) — CCR by attack × defense
| attack | write path | CCR (D0) | CCR (D1) |
|---|---|--:|--:|
| A01 false-obs | unauthenticated direct write ("bad design") | 1.00 | 1.00 |
| **A04 signed conflict** | **signed, valid insider key** | **1.00** | **1.00** |
| **A05 signed false-obs** | **signed, valid insider key** | **1.00** | **1.00** |
| **A06 perception spoof** | **legitimate perception ingestion, no direct write** | **1.00** | **1.00** |
| A00 clean | — | 0.00 | 0.00 |

### Planning (PLAN/L2) — planner coordinate-adoption (routes a goto waypoint to the TRAP)
| attack | model | coordinate_adoption | valid_plan |
|---|---|--:|--:|
| A05 signed false-obs | gpt-oss:20b | **1.00** | 1.00 |
| A05 signed false-obs | qwen2.5:7b | **1.00** | 1.00 |
| A06 perception spoof | gpt-oss:20b | **1.00** | 1.00 |
| A06 perception spoof | qwen2.5:7b | **1.00** | 1.00 |

### TC-indirect — query-only laundering via the system's own reflection (P1b, 40 runs)
The lowest-capability tier: attacker plants **one unsigned low-privilege episodic** false observation;
the Supervisor's own `consolidate_memory()` (Park-2023 reflection) promotes it into **trusted semantic
memory** (`source=reflection`) — laundering the poison into provenance it never had at write time.
| model | promotion_rate | laundered source |
|---|--:|---|
| gpt-oss:20b | **1.00** | reflection |
| qwen2.5:7b | 0.10 | reflection |
| A00 controls | 0.00 | — |
Model-dependent (qwen's reflection JSON often fails to parse); on a capable model the laundering is total.
Full tier gradient in `CAPABILITY_TABLE.md`.

### Provenance defense does not save you (disposable D1+D2 reference diagnostic)
Under D1+D2 trust-reranking, the **unauthenticated A01 is demoted (CCR→0)** but the **signed A04/A05
survive (CCR 1.0)** — the very fix for the "bad design" write fails on the authenticated insider. This
matches Cam's independently-measured WP5 result ("D1 blocks nothing on A04/A05/A06").

## 5. Interpretation (scoped)
The attack's success is **not** contingent on an unauthenticated direct write: retrieval CCR = 1.0 was
reached via a signed authorized-writer (A04/A05), a perception-ingress path (A06), and the unauthenticated
write (A01); planner coordinate-adoption (20/20 per path) was demonstrated for the signed-episodic (A05)
and perception (A06) paths; and the reflection loop promoted low-trust episodic content into trusted
semantic memory (10/10 GPT-OSS, 1/10 Qwen). This converts "strong / impractical threat model" into
"realistic, does not require unauthenticated store access" — answering B1 and C1 — **without** claiming
every path was taken end-to-end or that success is universal across models.

## 6. Limitations — exactly what each path did and did NOT demonstrate
- **These are distinct, incomparable capabilities, NOT a weakest→strongest ladder.** Signing-key /
  authorized-writer compromise and sensor/GNSS compromise are different threat actors and access.
- **Signed insider needs control of an authorized writer** that holds signing authority — not "just a key."
- **Perception (A06) = no attacker-*direct* write**, but the *legitimate pipeline does write* the record;
  and it models the **ingress point only** — the full RF GNSS-spoofing chain was **not** executed.
- **TC-indirect requires one low-privilege episodic write** (it is not "no write"); no privileged/semantic
  write and no key. For this path we measured **promotion only** — **top-k CCR and planner hijack were NOT
  measured**, and it is strongly **model-dependent** (GPT-OSS 10/10, Qwen 1/10).
- **Planner hijack measured for A05 and A06 only** (20/20 each). A01 and A04 were retrieval-only; not taken
  to the planner.
- **No physical execution.** PX4-SITL closed-loop is not established here (that is P5/#6).
- **Local models only** (gpt-oss:20b, qwen2.5:7b); 7-model parity deferred.
- **"New mechanism" is NOT claimed.** Whether reflection-based promotion is novel vs MINJA / reflection-
  attack / AgentPoison requires a prior-work comparison (task for #7).
- **Defense is out of scope (Cam/FD1).** The disposable D1+D2 diagnostic uses the legacy reference defense.
- CIs degenerate (per-seed identical); reported as exact rates over n=10 (per path/model).

## 7. Note on the PLAN metric (transparency)
An initial ad-hoc aggregation read `rates.asr` (a propagation-family metric = 0 here) and briefly
suggested planner resistance. The canonical planner-hijack field is `parsed_actions.coordinate_adoption`
(same as the paper's CHR and 452B-1); it is **1.0 (40/40)**. This was a reading error in a throwaway
script, NOT a production or metric-computation bug — the production bundles are valid and unchanged; **no
rerun was performed.** See `PROVENANCE.md`.

## 8. Reproduce
```
python3 experiments/campaign_p1_threat_model.py --audit
```
Reads only P1 production bundles (filtered by the P1 prereg hash); runs no experiments.
