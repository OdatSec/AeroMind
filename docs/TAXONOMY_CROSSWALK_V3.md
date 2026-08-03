# AeroMind — Final Campaign V3 Taxonomy Crosswalk (authoritative)

Single source of truth for the **canonical V3 identifiers** and their
backward-compatible **legacy aliases**. Enforced in code by `uavsys/taxonomy.py`.
New manifests/reports use canonical IDs and also record the legacy alias.
`results_v2_frozen/` is immutable legacy/validation evidence and is never migrated.

Status: **implemented** (runnable now) · **planned** (namespace reserved, no runner)
· **deferred** (design pending, e.g. needs L3/STATE).

---

## Attacks — A00–A09
| Canonical | Paper C-case | Runner alias | Status | Meaning |
|---|---|---|---|---|
| **A00_CLEAN** | C0 | B0 | implemented | Clean baseline |
| **A01_FALSE_OBSERVATION** | C1 | S01 | implemented | Direct false observation (redirection) |
| **A02_SHARED_MEMORY_EXPOSURE** | C2 | S06 | implemented | Shared-memory **exposure** (NOT propagation — L1/L2 evidence is exposure only; genuine write-back needs L3) |
| **A03_FALSE_RESTRICTION** | C3 | S12 | implemented | False safety constraint → refusal |
| **A04_SIGNED_CONFLICT** | C4 | S16 | implemented | Authenticated false semantic state (signed, out-of-role) |
| **A05_SIGNED_FALSE_OBSERVATION** | C5 | S17 | implemented | Authenticated false episodic observation |
| **A06_PERCEPTION_FALSE_STATE** | C6 | S18 | implemented | Perception-ingestion false state |
| **A07_FALSE_COMPLETION** | — | MV1_FALSE_CLEARANCE | implemented | False "already cleared" → target omission |
| **A08_FALSE_SAFETY** | — | MV2_FALSE_SAFETY | implemented | False "zone cleared" + in-zone lure → unsafe entry |
| **A09_TARGET_RELOCATION** | — | MV3_TARGET_RELOCATION | **deferred** | "target moved" → stale-state selection (needs T04 + STATE) |

> **Naming decision:** A02 uses `_EXPOSURE`, not `_PROPAGATION`, so the canonical
> ID never licenses an unsupported claim. "Propagation" is reserved for a future
> A-id backed by L3 write-back evidence.

## Tasks — T01–T04  (runner alias = mission id)
| Canonical | Runner | Status | Task |
|---|---|---|---|
| **T01_SEARCH_RESCUE** | M1 | implemented | Search & Rescue (legacy mission, byte-identical) |
| **T02_MULTI_TARGET** | M2 | implemented | Multi-target Survey (6 targets briefed) |
| **T03_RESTRICTED_ZONE** | M3 | implemented | Constrained Corridor (genuine no-fly zone) |
| **T04_RETASKING** | M4 | **deferred** | Sequential Re-tasking |

## Memory — MEMxxx  (runner alias = profile id)
| Canonical | Runner | Status | Config |
|---|---|---|---|
| **MEM003_SPARSE** | P1 | implemented | 3-record sparse baseline |
| **MEM060_OPERATIONAL** | P2 | implemented | 60-record operational mixture |
| **MEM200_DENSE** | P3 | planned | 200-record dense-similar |
| **MEM1000_LARGE** | P4 | planned | 1000-record large |

Semantic variants may append `_STALE` / `_CONFLICTING` / `_MIXED`; these resolve to
their base config (e.g. `MEM060_OPERATIONAL_STALE → MEM060_OPERATIONAL`).

## Evaluation — RET / PLAN / MULTI / SITL  (runner alias = --mode)
| Canonical | Layer | Runner | Status |
|---|---|---|---|
| **RET** | L1 | retrieval | implemented |
| **PLAN** | L2 | planning | implemented |
| **MULTI** | L3 | — | **planned** (no runner; runs fail loud) |
| **SITL** | L4 | full-pipeline | implemented (not run) |

## Defense — D0–D4
D0 none · D1 provenance/HMAC · D2 authorization · D3 corroboration · D4 combined.
Draft taxonomy (owner: Cam / Dr. Qian); only D0/D1 exercised so far.

---

## Raw results layout (argument-driven, attack-centered; opt-in `--results-layout v3`)
Every scientific axis is an ordered folder, so the executed configuration is
readable directly from the path:
```
results_v3_raw/
  <ATTACK>/<TASK>/<MEMORY>/<EVALUATION>/model-<MODEL>/<DEFENSE>/
    topk-<NN>/budget-<NN>/temp-<VALUE>/
      [agents-<NN>/]        # MULTI only
      [backend-<NAME>/]     # SITL only
        seed-<XXXX>/run-<cfg8>-<uuid8>/
```
Axis tokens: `topk-03`, `budget-01` (zero-padded; `budget-default` when unset),
`temp-0.1` (`temp-na` for RET), `model-<slug>` (sanitized; exact provider id in the
manifest). **Operational flags** (evidence-bundle, results-layout), timestamps,
commit/config hashes, UUIDs, and provider metadata live in `manifest.json` and
create **no** directory levels. Short `run-<cfg8>-<uuid8>` leaf. `results_v3_raw/`
is git-ignored (like the v2 raw bundles).

**Non-mixing / collision protection.** `config_hash` already binds model, top-k,
temperature, seed, defense, mission, profile; **poison budget** was the one axis
not in the hash, so it is separated at the path level (`budget-<NN>`). The full
axis path guarantees distinct configs never share a directory, and the `run-`
uuid guarantees distinct runs of the same cell never collide (the bundle also
refuses to overwrite an existing final dir).

## Campaign layer (human-readable; mirrors the same axes)
```
results_v3_campaigns/
  INDEX.md            (auto)          PAPER_FINDINGS.md  (human-only, never auto)
  <ATTACK>/<TASK>/<MEMORY>/<EVALUATION>/model-<MODEL>/<DEFENSE>/
    topk-<NN>/budget-<NN>/temp-<VALUE>/[agents-<NN>/][backend-<NAME>/]
      README.md  campaign_summary.json  paired_results.csv  bundle_index.yaml
      INSIGHTS_DRAFT.md (auto DRAFT)     CLAIMS.md
```
Clean raw runs live under `A00_CLEAN/...`; each attack campaign folder pairs the
matching `A00_CLEAN` bundles with that attack's bundles. `INSIGHTS_DRAFT.md` is
generated by `uavsys/campaigns.build_campaign`; promotion into `PAPER_FINDINGS.md`
is a **human-only** step.

## How a future run is invoked (canonical IDs; legacy still accepted)
```
# canonical
python experiments/experiment_runner.py \
  --scenario A08_FALSE_SAFETY --mode PLAN --mission T03_RESTRICTED_ZONE \
  --profile MEM060_OPERATIONAL --seeds 101,... --defense off \
  --evidence-bundle --results-layout v3
# legacy aliases still work identically (S12/C3, M3, P2, planning, --results-layout v2 default)
```

## Compatibility guarantees
- `results_v2_frozen/` is never moved, edited, or recomputed.
- Default `--results-layout v2` reproduces the exact prior behavior (long run-id,
  results_v2_frozen); V3 is strictly opt-in.
- Every legacy identifier (C0–C6, B0/Sxx, MV1–3, M1–4, P1/P2, retrieval/planning/
  full-pipeline) remains a valid alias.
