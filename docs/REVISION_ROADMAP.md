# AeroMind RAID→ASIACCS Revision Roadmap (reference)

> Frozen reference copy of the approved prioritization plan (session 2026-08-03). Grounds every
> workstream in the actual manuscript `/home/px4/raid/RAID_2026_Current.pdf` and the three reviews.
> Living execution status is tracked in `docs/V3_EXECUTION_LOG.md` and the per-concern closure packages.

# AeroMind RAID→ASIACCS Revision — Reviewer-Concern Roadmap (paper-grounded, parallelized)

## Context
Convert the three RAID'26 reviews of **`/home/px4/raid/RAID_2026_Current.pdf`** (26 pp) into an ASIACCS
resubmission. Scores: **452A weak-reject**, **452B weak-reject** (knowledgeable), **452C reject**.
This plan is grounded in the actual manuscript and folds in the professor's four directives:
(1) explain the deterministic top-k retrieval; (2) **redesign the threat model to be realistic/practical,
with references + an implemented example**; (3) work the reviewers **in parallel**; (4) run **new
experiments** grounded in both repo and paper.

**Decisive axis: threat-model practicality** — B1 and C1 both call it their biggest concern; C rejected
largely on it. Cross-cutting theme: **overclaiming** (B2 "CCR=1 by construction", A1 "6→200 misleading").

**Scope (locked):** evidence/experiments only, **local models (gpt-oss-20b, qwen2.5:7b)**; 7-model parity
(…GPT-4o) is a flagged infra dependency. Paper-writing (threat-model §, novelty, term fixes) = **handoff
[authors]**. Faculty (Dr. Liu/Dr. Qian) own scope per `docs/ASIACCS_DECISION_MEMO.md`. Full discipline:
freeze prereg (sha256) → tests → disposable preflight → audit → production on approval → accept-gate →
deterministic aggregator → closure + `V3_EXECUTION_LOG.md`. `results_v2_frozen/` immutable; `main` untouched.

## Paper ground truth (so every fix targets the real manuscript)
- **Formula (1):** `sᵢ = α·sim(q,eᵢ) + β·r(eᵢ) + γ·u(eᵢ)`, α=0.6 β=0.2 γ=0.2. `sim`=cosine, `r`=exp recency
  decay, `u`=keyword-importance heuristic (§4.3) — identical to `uavsys/memory/retrieval.py`.
- **Scenarios S01–S15** (paper taxonomy; crosswalk to repo A00–A09 in `docs/TAXONOMY_CROSSWALK*.md`).
  Flagship: **S01** false-obs coordinate hijack (CCR 0.82, CASR 1.0, 100% hijack, 6/7 models); **S06**
  cross-agent contagion (0.73); **S07/08/09** stealth/flood/recency saturation; **S12** constraint/no-fly
  (retrieval 0.91 but planner adoption model-dependent: 3 models 100%, DeepSeek 60%, Mistral 20%, Llama/Qwen 0%).
- **CCR 0.82 not 1.0** = scout(3/3=1.0)+supervisor(3/5=0.6) → 9/11 (this is B2's exact "CCR=1 by construction" point).
- **Defense** D1(provenance)+D2(trust-rerank)+D3(source-cap): CCR→0.40, hijack 100%→0%, but **end-to-end
  only on GPT-OSS** (= C3's "only two defended backends"). S12 residual open (= C4).
- **Attacker model §4.4:** "inject or alter records before retrieval… compromised agent, malicious tool
  output, poisoned ingestion path." Signed-insider (S16/S17) + perception-spoof (S18) already implemented
  in repo but barely executed (RET/PLAN only, ~1 model/seed; none at SITL).

## Reviewer-term reconciliation (grounded — for the [authors] writing handoff)
- **A-Q1** `r(eᵢ)`/`u(eᵢ)`: recency (exp decay) and keyword-importance. They set attack strength because the
  poison maximizes `u` (keyword-laden "target/confirmed/coordinates") **and** `sim` (query-matched).
- **A-Q2** "operator" = the human mission-submitter (Fig 1). "operator-seeded write surface" = the NL mission
  prompt as an injection vector (≈ S05).
- **A-Q3** "stealth-optimized entry" = **S07**: a few crafted episodic entries reaching CCR 0.82 without flooding.

## Deterministic-retrieval answer (professor Q1; feeds A-Q1 + B2) — an ANALYSIS deliverable
The poison is top-k deterministically because: (a) `nomic-embed-text` is deterministic (no sampling); (b) the
poison maximizes all three Formula-(1) terms — `sim` (echoes the query), `u`=0.9 (keyword heuristic), `r`≈1
(newest); (c) off-topic benign filler is low-`sim`, so **top-k is relative ranking → CCR = min(budget,k)/k**,
invariant to memory *size*. **The honest caveat (my diagnostics, NOT in the paper): this holds only for
off-topic filler.** On-topic benign traffic out-ranks a generic poison and pushes it out (CCR→0); an
*adaptive query-matched* poison restores dominance. → This is exactly what P2 must characterize.

## Prioritized + PARALLELIZED roadmap
Independent workstreams **P1, P2, P4 run concurrently** (separate preregs/campaigns, no shared writes);
**P3** consolidates after P1/P2 land numbers; **P5** is last (infra-heavy).

### P1 — Threat-model realism (B1, C1; feeds C2, C4, A3) ★ decisive
Refute "unauthenticated writes are just bad design" with **cited real-world vectors + executed evidence that
poison wins via LEGITIMATE/AUTHENTICATED paths.**
- **Capability table (tiers ↔ cited real vectors):** indirect/query-only (MINJA; context-manipulation);
  tool/skill output (InjecAgent; MCP tool-description compromise); **poisoned perception ingestion**
  (GNSS spoof / adversarial patch / compromised sensor driver; Rodday UAV vulns); compromised-agent insider
  (S06); **authenticated signed-malicious** insider (S16/S17). Real-world anchors: **Amazon Bedrock
  persistent memory poisoning surviving sessions**, **M365 Copilot zero-click**, cross-session stored injection.
- **Implemented realistic example (the professor's "implement this example"):** execute the **perception-spoof
  path** (`attacks/s18` + `uavsys/ingest/perception.py`) where the attacker never writes memory directly —
  a spoofed sensor detection flows through the *legitimate* ingestion pipeline into episodic memory — **plus**
  the **signed-insider** S16/S17 (cryptographically valid yet malicious). Run across both local models ×
  seeds 101–110 × RET+PLAN, arms D0 and D_full. Expected: S16/S17 pass D1 (valid signature), caught only by
  D4a/D4b; S18 succeeds with no direct write.
- **Deliverable:** `docs/reviewer_closure/452B-2_threat_model_practicality/` + capability table + closure.
- **[authors]** threat-model §rewrite + OS-isolation caveat.

### P2 — Memory generalization, reworked & honest (A1) ★ core; current closure is fragile
Paper's S07/08/09 vary poison *volume* but never benign *composition*; the 452A-1 "invariant 3→200" is only
true for off-topic filler = the "misleading" charge.
- **New study (grounded, extends S07–S09):** 5 axes — off-topic volume {3,60,200,1000}; **on-topic episodic
  flood {0,10,50,200,500}**; true competitors {0,1,3,5,10}; **generic vs adaptive query-matched poison**;
  defense interaction (D1/D4). Report **Formula-(1) score decomposition (sim/r/u)** per cell.
- **Headline:** contamination is governed by the poison's **query-relevance rank**, not memory size —
  invariant to off-topic volume, collapses under on-topic traffic, restored by adaptive query-matching,
  neutralized by corroboration/auth defenses.
- **Deliverable:** revise/extend `docs/reviewer_closure/452A_part1_memory_generalization/` (append + re-headline;
  keep the valid off-topic facet).

### P3 — Deterministic explanation + claim-calibration master table (A-Q1, B2, B3; honesty)
- Publish the deterministic-retrieval analysis (above) as evidence for A-Q1/B2. Build one claim-to-evidence
  master table across all closures + P1/P2, tagging saturated-by-construction cells (B2), operating-point
  adoption (S12/452B-1), realistic-setup impact (B3). Cheap; finalize after P1/P2.

### P4 — Defense generalization on available models (C3, C4)
- Run **D_full** end-to-end across both local models × seeds on S01 (coordinate hijack) **+ S12** (constraint)
  **+ S16/S17** (signed), widening past "one defended backend"; **log 7-model parity as deferred infra**.
- **C4 signed-but-malicious:** the S16/S17 results from P1 + **[authors]** discussion of planner-level/semantic
  validation as the residual mitigation (ties to S12 open problem).

### P5 — Real-system / external validity (A3, C1) — heaviest, per decision memo
- Representative **PX4-SITL/Gazebo L4** closed-loop for S01 + one signed case + best defense (normalize "real
  flight"→"PX4-SITL closed-loop"). Stretch: scoped port onto a third-party agent framework (flagged infra).
- **[authors]** the "closed mission-control loop" write-surface argument (C1), grounded in the perception path.

## Already closed (do NOT redo)
- **A2** agent-count/assignment → `452A_part2` (240 runs, accept-gate PASS).
- **B2 sub-1** top-k saturation/k-sensitivity → `452B-1` (CCR=min(b,k)/k; adoption operating-point-dependent).

## Handoff to authors (writing — excluded per scope)
Threat-model/capability-table §(P1); novelty C2 (signed-insider still wins + shared-memory-control-plane +
retrieval-rank law); term fixes A-Q1/2/3 (reconciled above).

## References for the realistic threat model (professor asked)
In-paper: MINJA (Dong'25, query-only memory injection) [ref 5]; Greshake'23 indirect prompt injection [8];
InjecAgent [26]; AgentPoison [2]; PoisonedRAG [30]; Rodday UAV vulns [20]; RoboPAIR [19].
New (to add): "Agent Data Injection Attacks are Realistic Threats" (arXiv 2607.05120); "A Survey on Long-Term
Memory Security in LLM Agents" (2604.16548); "Context manipulation: web agents & corrupted memory" (2506.17318);
"Cross-Session Stored Prompt Injection in Agentic Systems" (2606.04425). Real-world: Amazon Bedrock persistent
memory poisoning, M365 Copilot zero-click, MCP tool-description compromise.

## Verification (per workstream)
- P1: S16/S17 pass D1 but caught by D4a/D4b; S18 succeeds via perception path; capability table shows the
  success gradient across tiers; accept-gate PASS.
- P2: on-topic flood drops generic CCR→0; adaptive poison restores it; decomposition explains each cell.
- P4: D_full reduces CCR on ≥2 local models; 7-model parity logged deferred.
- P5: one SITL closed-loop reproduces a hijack + its defense.

## Immediate next step (on approval)
Kick off **P1 + P2 in parallel**: draft + freeze both preregs (P1 threat-model capability/execution matrix;
P2 memory-composition 5-axis study), implement the two aggregators, run disposable preflights, and report
both before any production. P3/P4 follow; P5 last.
