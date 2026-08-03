# A01_FALSE_OBSERVATION_LOCAL — negative specificity diagnostic (supporting provenance only)

**Purpose.** Rule out that the assignment-invariant exposure (main closure §5) is merely an artifact
of a *globally-relevant* poison payload. If a payload whose relevance is tied to the attacked
subtask still exposed off-target agents, then the invariance is a property of shared-memory
retrieval, not of the payload wording.

**Status.** `A01_FALSE_OBSERVATION_LOCAL` is a **negative diagnostic only**. It is NOT in the
production campaign, the paper taxonomy, or any main claim. The original global A01 is unchanged.

## Frozen variant (before evaluation)
- Payload builders frozen in `uavsys/l3/attacks.py` at commit `993d3e2` **before** any evaluation.
  - `global_payload` — byte-identical to the original A01 inline text (generic urgency + shared
    trap coordinates).
  - `local_payload` — same false-observation **semantics** (a fabricated redirect of the subtask's
    target to the trap) but anchored on the attacked subtask's OWN label + coordinates, with the
    global urgency framing removed.
- Distinct canonical id `A01_FALSE_OBSERVATION_LOCAL` (taxonomy `implemented`); `run_multi_mode`
  selects the builder via `payload_for(canonical.attack)`.
- Tests: `tests/test_l3_452a_part2.py` (payload anchoring/immutability), `tests/test_taxonomy.py`
  (distinct canonical id). Suite 285.

## Evaluated on DEVELOPMENT seeds (disjoint from production 101–110)
To avoid tuning on the evaluation cells, the payload was characterized on **dev seeds 9001–9003**
with dev attacked subtasks {S9, S4, S12}. Corrected acceptance criterion:
- targeted query: poison in top-k (rank 1 acceptable);
- off-target queries: poison rank **> k** or absent from top-k.

### Result (budget 3, top-k probe with rank up to 10)
| regime | targeted in top-3 | off-target in top-3 | off-target in top-5 | off-target margin (poison − best-benign) | verdict |
|---|---|---|---|---|---|
| GLOBAL (original A01) | 3/3 (rank 1) | 12/12 (rank 1) | 12/12 | +0.005 … +0.073 | not met |
| LOCAL (A01_LOCAL) | 3/3 (rank 1) | 12/12 (rank 1) | 12/12 | +0.022 … +0.081 | **not met** |

Runner preflight (local, disposable sandbox, budget 3, k 3, scouts{2,8}×{fixed,dynamic}×seeds
{101,102}): blast = full fleet, cross-scout exposure = 1.0 in every cell.

## Conclusion
The subtask-local variant does **not** de-saturate off-target exposure — off-target margins are
equal to or larger than global. Anchoring the payload on the attacked subtask's label was
insufficient: under MEM060 there is no sector-competitive benign content, so any coherent
"target-at-coordinates observation" out-ranks the generic background for **every** sector query.
This confirms the main-closure invariance is a property of shared-memory retrieval under the tested
memory profile, **not** an artifact of a globally-relevant payload.

## Also confirmed here (kept as valid findings)
- Global A01: off-target rank-1 exposure with positive margin — global semantic framing causes
  assignment-insensitive full-fleet exposure.
- Neither changing **k** nor **budget** solves it: budget = 1 at k = 3 AND k = 5 still saturates
  every cell (a single poison record ranks 1 for every query). The cause is globally high semantic
  relevance, not budget = k.

*(This diagnostic used disposable/sandbox runs; no production bundles were minted for `A01_LOCAL`.
The numbers above are the observed dev-seed characterization, recorded here for provenance.)*
