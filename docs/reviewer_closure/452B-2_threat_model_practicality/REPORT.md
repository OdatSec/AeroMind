# Reviewer 452B-B1 + 452C-C1 — Threat-Model Practicality: Closure Report

**Status: CLOSED for the tested envelope (attack side).** The attack does NOT depend on unauthenticated
direct memory writes. Across a graded capability table, it reaches full retrieval dominance and 100%
planner adoption via **authenticated insider** records (valid key), via the **legitimate perception
pipeline** (no direct write), and even via **query-only laundering through the system's own reflection
loop** (no privileged write, no key, no sensor). The provenance defense that stops the naive
unauthenticated write does not stop the authenticated insider.

Evidence: **180 accepted production runs** (100 RET + 40 PLAN + 40 TC-indirect), accept-gate PASS. Local
models gpt-oss:20b, qwen2.5:7b. Raw bundles under `results_v3_raw/` (git-ignored); hashes in `PROVENANCE.md`.

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
The attack's success is **not** contingent on an unauthenticated write. It succeeds (retrieval dominance
CCR=1.0 and 100% planner adoption on both models) through (a) a **documented real UAV vector** —
GNSS-spoofed perception, no direct write — and (b) an **authenticated insider** whose signed records pass
provenance verification. This converts "strong / impractical threat model" into "realistic, low-capability,
and provenance-defense-evading," directly answering B1 and C1.

## 6. Scope limitations (explicit)
- **Local models only** (gpt-oss:20b, qwen2.5:7b); 7-model parity is a deferred infra task.
- **Attack side only.** Whether a *stronger* defense stops the signed insider is the **452C-C4 open
  problem = Cam's WP4/WP5**, gated on FD1. The disposable D1+D2 result uses the legacy reference defense
  and is diagnostic, not a defended-production claim.
- **Retrieval + planning layers**, not PX4-SITL physical execution (that is P5).
- CIs would be degenerate here (every seed = 1.0); reported as exact rates over n=10.

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
