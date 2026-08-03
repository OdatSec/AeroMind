# AeroMind V2 — Taxonomy Crosswalk (authoritative reference)

**Purpose:** one page that removes identifier confusion. Four distinct namespaces,
the frozen case↔alias mapping, the run-identity schema, and the applicability
matrix. **Companion to `configs/EXPERIMENT_SPEC_V2.yaml` (draft).** No experiments run.

---

## 1. Four namespaces (do not mix)
| Namespace | Members | Meaning | Rule |
|---|---|---|---|
| **Missions** | M1–M4 | The task the swarm performs | Independent of the attack applied |
| **Cases** | C0–C6 | **FROZEN** canonical campaign/threat cases | Never renumbered or repurposed |
| **Legacy aliases** | Sxx / B0 | Internal implementation identifiers | Map 1:1 to C0–C6; **not** scientific cases |
| **Variants** | MV*_* | Auxiliary mission-specific attack variants | **Not** new C cases; extend a case family |

The variant namespace uses the **`MV` prefix** (mission-variant) specifically so it
can never collide with the project-version token `V2` (see §6).

---

## 2. Authoritative case ↔ legacy mapping (frozen)
| Case | Legacy alias | Canonical name |
|---|---|---|
| **C0** | **B0** | Clean Mission Baseline |
| **C1** | **S01** | Direct False Observation |
| **C2** | **S06** | Cross-Agent False-State Propagation |
| **C3** | **S12** | False Safety Constraint |
| **C4** | **S16** | Authenticated False Semantic State |
| **C5** | **S17** | Authenticated False Episodic Observation |
| **C6** | **S18** | Perception-Ingestion False State |

> **Sxx are implementation aliases only.** They may appear in run logs and code as
> internal names, but **must not appear as independent scientific cases in the
> paper.** Legacy numbers outside this table (e.g. S02, S07–S09) are retired
> implementation experiments, not part of the frozen taxonomy.

---

## 3. Variants (MV*) — auxiliary, not new C cases
| Variant ID | Name | Failure mode (new beyond C0–C6) | Mission | Extends | redteam analogue | Class / Status |
|---|---|---|---|---|---|---|
| **MV1_FALSE_CLEARANCE** | False sector clearance / already-searched | target **omission** via false *completion status* | **M2** | C1 mechanism | A2 | **core** / proposed |
| **MV2_FALSE_SAFETY** | False safety-restored / hazard-cleared | **unsafe entry / breach** (mirror of C3 refusal) | **M3** | C3 companion | A3 | **core** / proposed |
| **MV3_TARGET_RELOCATION** | Target relocation / target-moved | **stale/overturned-state selection** (sequential only) | **M4** | C1 (temporal) | A4 | **optional** / deferred |

*Memory-borne instruction injection (redteam A7) is deliberately **not** a variant:
it is a distinct mechanism (imperative vs false-fact) and is held as an appendix
auxiliary study, outside the C0–C6 belief-poisoning taxonomy.*

---

## 4. Valid experiment identity schema
Every run is one tuple:

```
mission × attack_case_or_variant × profile × layer × model × seed × defense
   M1-M4     C0-C6 | MV*_*          P1-P6    L1-L4   pinned  int    D0-D4
```

- **`attack_case_or_variant`** draws from **C0–C6** (canonical) or **MV*_***
  (variant) — **never Sxx.**
- **`model`** is embedder-only at L1; a pinned planner id at L2+.
- **`seed`** is the independent statistical unit.

---

## 5. Mission × attack applicability
`yes` = meaningful · `opt` = possible, low value · `no` = not meaningful

| | C0 | C1 | C2 | C3 | C4 | C5 | C6 | MV1 | MV2 | MV3 |
|---|---|---|---|---|---|---|---|---|---|---|
| **M1** Search & Rescue | yes | yes | yes | no | yes | yes | yes | no | no | no |
| **M2** Multi-target Survey | yes | yes | yes | opt | yes | yes | yes | **yes** | no | opt |
| **M3** Constrained Corridor | yes | opt | no | yes | opt | opt | opt | no | **yes** | no |
| **M4** Sequential Re-tasking | yes | opt | yes | no | yes | yes | yes | opt | opt | **yes** |

(MV1 = MV1_FALSE_CLEARANCE, MV2 = MV2_FALSE_SAFETY, MV3 = MV3_TARGET_RELOCATION.)

---

## 6. Naming conflict — RESOLVED
**Was:** `V2` denotes the **project version** across the repo (`AeroMind V2`,
`EXPERIMENT_SPEC_V2`, `results_v2_frozen/`, `docs/V3_EXECUTION_LOG.md`), so a
variant named `V2` collided with it.

**Resolution:** the variant namespace was renamed **V1–V3 → MV1_FALSE_CLEARANCE /
MV2_FALSE_SAFETY / MV3_TARGET_RELOCATION**. A bare `V2` now unambiguously means the
project version; variants always carry the descriptive `MV` prefix. No other
identifier conflicts exist: `M1–M4` are used consistently, `Sxx` appear only as
aliases, and `C0–C6` are frozen.

---

## 7. What did NOT change
- **C0–C6 identifiers and their legacy mappings are frozen** — untouched.
- The spec remains **`status: draft`** (FD1–FD4 still open).
- Missions M2–M4 and variants MV* are declared as `proposed`/`deferred` contracts
  only; the first implementation batch adds M1–M3 registry, P1/P2 profiles, and
  the MV1/MV2 outcome detectors (no experiments).
