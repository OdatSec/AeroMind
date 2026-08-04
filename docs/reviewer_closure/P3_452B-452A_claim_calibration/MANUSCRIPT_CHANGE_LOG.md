# P3 — Manuscript Change Log (RECOMMENDED — not applied here)

Apply-ready corrected wording for the overclaimed manuscript claims. **Per instruction the `.tex` is NOT
edited in this task**; this log is the authoritative change set for the authors to apply in
`RAID_2026_Current/sections/*.tex` (source verified to match `RAID_2026_Current.pdf`). After applying, run
the overclaim sweep (bottom) and only then can P3 be marked closed.

Legend: OC = overclaim (edit) · M = measured (retain, add uncertainty note).

## C1 — §1 Introduction (`1_introduction.tex:37–39`) — OC · facet 452B
**Original:** "…exactly $k$ poisoned entries---where $k$ is the retrieval window size---achieve full context
saturation, making the attack cost a predictable architectural invariant rather than an empirical artifact."
**Corrected:** "…when at least $k$ poisoned entries **outrank the benign candidates**, they occupy the
top-$k$, giving $\ccr=\min(b,k)/k$; at $b=k$ this is saturation **by construction**. Whether the poison
outranks benign candidates is an **empirical** matter of relevance ranking (§\ref{sec:evaluation:s07} and
our composition study), not an architectural guarantee — on-topic benign content can evict a generic poison."

## C2 — Abstract (`current_version.tex:74`) — OC · facet 452B
**Original:** "…corrupted entries deterministically hijack flight paths across all model backbones tested,
propagate to every agent in the swarm, and persist across missions."
**Corrected:** "…corrupted entries dominate retrieval on all tested backbones (retrieval is deterministic);
for the flagship coordinate hijack this drives **100\% physical redirection on all seven models**, contagion
on six of seven (one function-call outlier at 60\%), and persistence across missions. Constraint-injection
adoption is **model-dependent**."

## C3 — §7.1/§7.2 (`7_attack_evaluation.tex:73–74, 85`) — OC · facet 452B
**Original:** "…three episodic entries deterministically redirect physical execution regardless of model family."
**Corrected:** "…for the S01 coordinate hijack, retrieval is deterministic and planner adoption and physical
redirection reached 100\% on all seven tested models; downstream adoption is **not universal** — cross-agent
contagion holds on six of seven (Mistral 60\%) and constraint-injection adoption is model-dependent (§7.4)."

## C4 — §4.2 / §7.3 / abstract-intro size framing — OC · facet 452A
**Original:** "…[simple initial memory: two legitimate semantic targets + one procedural template]; success
$\approx$ invariant from ~6 to 200 records."
**Add / correct (methodology + results):** "The size-invariance result is limited to the tested **off-topic**
compositions (MEM003/060/200). **On-topic** benign content out-ranks and evicts a generic poison; a
higher-ranking benign record evicts it causally. Retrieval contamination is governed by **relative relevance
ranking**, not raw record count. (See composition study.)"

## C5 — §7.1 (`7_attack_evaluation.tex:13–15`) — M · retain + CI note · facet 452B
**Original:** "…100\% planner adoption and 100\% physical hijack across all seven model families and all five
seeds---with zero variance."
**Retain, add note:** "…(S01; 35/35 model×seed runs; Clopper-Pearson 95\% CI ≈ [0.90,1.0]). 'Zero variance'
reflects the **deterministic retriever**, not the absence of sampling uncertainty."

## C6 — §7.1 CCR=0.82 — M · retain (use to answer 452B)
**Keep as-is**; in the response, cite it explicitly: system-wide CCR = **0.82** (9/11), **not 1**, because the
supervisor's $k=5$ window leaves legitimate slots — the direct rebuttal to "CCR has to be 1."

## C7 — §7.4 S12 — M · retain
**Keep**; it is the honest model-dependence (100\%/60\%/20\%/0\%) that supports scoping the determinism claims.

---
## Sweep coverage — every absolute/universal instance found, mapped
Audit of `current_version.tex` + `sections/*.tex` (backups excluded):
- **EDIT (overclaim):** `1_introduction.tex:23` (RQ "deterministically redirect"), `:32` ("every agent…
  across any backend"), `:38–39` (full saturation / architectural invariant) → **C1/C2/C3**;
  `current_version.tex:74` (abstract) → **C2**; `7_attack_evaluation.tex:73–74, 85` ("deterministic…
  regardless of model family") → **C3**; `7_attack_evaluation.tex:180` ("every agent in the swarm") → **C3**
  (S06 is 6/7, scope it).
- **RETAIN — accurate (measured), add uncertainty note only:** `7_attack_evaluation.tex:61–62, 162`
  ("$\chr=100\%$ in every seed"), `:245` ("$\ccr=1.0$ in every seed" for S08 flood) → **C5** (S01/S08 are
  genuinely 100%/1.0 on the tested set; report as k/n with Clopper-Pearson; "zero variance" = deterministic).
- **RETAIN — correct as written:** "retrieval metrics are **model-invariant**" (`7:25`, `1:59`) — retrieval
  precedes LLM invocation, so model-invariance of *retrieval CCR* is a true, defensible statement (do NOT
  flag). "integrity guarantees" (`10_conclusion.tex:12`) refers to the DEFENSE, not an attack overclaim.

## Final overclaim sweep checklist (authors run after applying C1–C5)
Search each for absolute/universal language ("deterministic(ally)", "always", "every model/agent/seed",
"invariant", "guarantee", "full saturation", "predictable … invariant", "100\%") and ensure each is scoped:
- [ ] Abstract  - [ ] §1 Introduction  - [ ] §7 Results (+ all captions/tables)  - [ ] §9 Discussion
- [ ] §10 Conclusion  - [ ] Figure/Table captions  - [ ] Reviewer-response letter
Rule: retrieval CCR = observed values; binary presence/adoption/physical = Clopper-Pearson; downstream
adoption is model-dependent and must not be stated as universal; CCR saturation is conditional on rank dominance.
