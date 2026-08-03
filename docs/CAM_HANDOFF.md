# Cam Handoff — Onboarding & Work Contract (AeroMind revision)

**Baseline commit:** `844117b` on `revision/v2` (clean tree, 232 tests green, V3 pipeline preflight-validated).
**Scope window:** Aug 1–21, 2026 (ACM ASIACCS 2027, Cycle 1). See `AeroMind_Execution_Plan_Final_Team_Aligned.pdf` for the full team plan; this document is your onboarding + contract.
**Faculty:** Dr. Qian (defense selection, experiment design, statistics, denominators, technical claims). Dr. Liu (scope, contribution, evidence freeze, final approval).

---

## 0. Your role — read this first

**You are not responsible for building a separate defense for every attack.** That is explicitly *not* the assignment.

You own a single, bounded research-to-prototype package:

1. **Research & compare** candidate defenses for **signed false memory** (the paper's acknowledged open problem — reviewer 452C-4): corroboration, conflict checking, spatial/temporal consistency, and high-impact-action gating. Compare assumptions, required inputs, expected benefit, and failure modes.
2. **Select one bounded design** *with Dr. Qian* (WP4 decision record).
3. **Implement** it behind a fixed interface (WP5).
4. **Evaluate it offline** on signed-false / benign / conflicting / stale / insufficient-corroboration records, and build the shared statistics/CI pipeline.
5. **Independently verify** at least one of Ibrahim's core generalization results from frozen inputs.

**The existing defense code (`uavsys/memory/defense.py`, `configs/defense_sweeps.yaml`) is legacy scaffold / reference only.** It contains a provenance-signing (D1), trust-rerank (D2), source-diversity (D3), role-authorization (D4a), and coordinate-corroboration (D4b) implementation from the *previous* paper. **It is not the final revised-paper defense.** Treat it as prior art to study and (optionally) reuse — not as a spec to preserve.

**Interface-shape decision is confirmed with Dr. Qian in WP4.** The team plan's expressed default (WP5) is that the final defense is **"a separate module after retrieval and before planning."** The legacy code instead runs *inside* the retrieval boundary (via `retrieve(defense_cfg=…)`), which is one reason it is reference-only. Your WP4 task is to **confirm the plan's separate-stage default** — or, if your candidate comparison justifies it, propose operating inside retrieval — and record the decision + rationale with Dr. Qian. Section 2 documents both hook points so either outcome is buildable.

**Final integration (WP6)** evaluates the *selected* defense on **representative attacks**, **benign utility**, and **multiple planners** — not an exhaustive per-attack defense matrix.

---

## 1. Repo architecture & where to start

```
AeroMind/
├── uavsys/
│   ├── memory/
│   │   ├── memory_interface.py   ← retrieval boundary; retrieve(..., defense_cfg=)  ★ your hook
│   │   ├── defense.py            ← LEGACY DefenseLayer (D1/D2/D3/D4a/D4b) — reference only
│   │   ├── signing.py            ← HMAC Signer + keyring (signs `agent|content`)
│   │   └── schema.sql            ← memory record schema (episodic/semantic/procedural/coordination)
│   ├── evidence/
│   │   ├── bundle.py             ← evidence-bundle writer (manifest, config_hash, validity/run_class)
│   │   ├── outcomes.py           ← planner outcome detectors (target_omission, unsafe_entry, haversine)
│   │   └── planner.py            ← coordinate_adoption / constraint_refusal detectors
│   ├── utils/metrics.py          ← retrieval metrics: CCR / MTR / RIS / CASR
│   ├── taxonomy.py               ← SINGLE SOURCE OF TRUTH: attacks/tasks/memory/evals/defenses + locks
│   ├── paths.py                  ← V3 layout, root guards, production vs preflight
│   ├── campaigns.py              ← campaign layer (paired CSV, summary, insights) — paper-stat surface
│   ├── missions.py               ← M1/M2/M3 mission configs + briefing()
│   └── memory_profiles.py        ← deterministic memory builders: build_profile("P1"|"P2")
├── experiments/experiment_runner.py   ← the one runner (canonical CLI: --scenario/--mode/…)
├── configs/defense_sweeps.yaml   ← LEGACY defense configs (D0..D_full) — reference only
├── results_v2_frozen/            ← IMMUTABLE legacy validation evidence + fixtures (78 bundles)
└── docs/
    ├── TAXONOMY_CROSSWALK_V3.md  ← canonical A/T/MEM/EVAL/D IDs (+ legacy S-name aliases)
    ├── TAXONOMY_CROSSWALK.md
    ├── V3_PREFLIGHT_VALIDATION_REPORT.md  ← how the V3 pipeline is validated + preflight discipline
    └── V3_EXECUTION_LOG.md        ← running log; every impl commit appends here
```

**Start here, in order:** (1) this doc; (2) `docs/V3_PREFLIGHT_VALIDATION_REPORT.md`; (3) `docs/TAXONOMY_CROSSWALK_V3.md`; (4) run the Section 6 preflight command; (5) read `uavsys/memory/defense.py` and `signing.py` as reference; (6) read a frozen bundle under `results_v2_frozen/` end-to-end.

**Legacy → canonical name map** (the plan uses S-names; the code is canonical): `B0=A00_CLEAN`, `S01=A01_FALSE_OBSERVATION`, `S06=A02_SHARED_MEMORY_EXPOSURE`, `S12=A03_FALSE_RESTRICTION`, `S16=A04_SIGNED_CONFLICT`, `S17=A05_SIGNED_FALSE_OBSERVATION`, `S18=A06_PERCEPTION_FALSE_STATE`. Signed-false-memory attacks = **A04 / A05** (your primary targets).

---

## 2. The defense input/output contract

### 2.1 The retrieval boundary (hook point A — inside retrieval)

```python
# uavsys/memory/memory_interface.py
async def retrieve(self, *, query: str, layers: list[str], top_k: int,
                   agent: str, run_id: str,
                   filters: Optional[Dict[str, Any]] = None,
                   defense_cfg: Optional[dict] = None) -> dict
```

- **Input** `defense_cfg` — a plain dict. The four keys currently consumed (`uavsys/config.py:75-78`, with defaults):
  - `similarity_threshold` (0.35) — pre-filter floor
  - `max_results_per_source` (2) — D3 source-diversity cap
  - `trust_weight` (0.3) — D2 rerank weight, score = `(1-w)*sim + w*trust`
  - `provenance_secret` ("") — D1 HMAC key (redacted in every bundle; **never** appears in `config_hash`)
- **Output** — a dict of retrieved items; each item carries `agent`/`from_agent` (source), `score` (post-rerank), signed identity fields, and layer/content. This is what the planner consumes.

### 2.2 Legacy `DefenseLayer` (reference implementation of the two-hook pattern)

`uavsys/memory/defense.py` — study, don't preserve:

| Hook | Method | Legacy D-level |
|---|---|---|
| **(1) verify / authorize** (pre-rank) | `verify_record` / `apply_provenance_check` (keyring-based) | D1 (HMAC) |
| | `writer_role` / `authorize_record` / `apply_authorization_check` | D4a (role-scoped write authz) |
| | `is_privileged_provenance` + coordinate corroboration (`_extract_coords`, `_haversine_m`) | D4b (provenance-tiered corroboration) |
| **(2) rerank / filter** (post-similarity) | `filter_by_similarity` | pre-filter |
| | `trust_weighted_rerank` | D2 |
| | `enforce_source_diversity` | D3 |

**Signed-identity semantics you must respect** (`signing.py`): the HMAC signs `agent|content`, so **writer identity is bound by the signature, never by the unsigned `source` field**. A compromised in-fleet agent must not become trusted by declaring `source="Intel"`. Any semantic/corroboration defense you build must key trust off the **signed** identity, exactly as `_writer_identity` / `is_privileged_provenance` do.

### 2.3 Hook point B — separate post-retrieval / pre-planning stage

If you and Dr. Qian choose the "separate module" shape, insert a stage that consumes the `retrieve()` output dict and returns a filtered/annotated dict **before** it reaches the planner (`uavsys/agents/supervisor.py`). Contract: input = retrieved-items dict (§2.1 output); output = same shape (items may be dropped, reranked, or annotated with a `defense_verdict`). Keep it pure and side-effect-free so it is independently testable on frozen snapshots.

### 2.4 FD1 — your first design task (blocking for defended campaigns)

The canonical taxonomy defines `DEFENSES = (D0, D1, D2, D3, D4)` (`taxonomy.py`), but the legacy configs are keyed `D0/D1/D2/D3/D1_D2/D2_D3/D_all/D_authz/D_full` — **canonical `D4` has no single config key.** Before any defended production run, freeze (with Dr. Qian) the mapping: `canonical D-token ↔ config key ↔ DefenseLayer capability`, and register your selected defense as a canonical `D`-token in `taxonomy.py` so it appears in the V3 path + manifest. This is **FD1**; it gates WP6.

### 2.5 Config-hash discipline

Experiment identity = `config_hash` (schema v1 config-only; v2 +mission/profile; v3 +budget; `bundle.py`). If your defense adds a knob that must define experiment identity, it has to be **registered like the budget axis (schema bump)** — do not silently add fields. Ephemeral fields (`DB_PATH`, `RUN_ID`) and all secrets are excluded/redacted; keep it that way.

---

## 3. Existing fixtures & retrieval snapshots

**78 frozen bundles** under `results_v2_frozen/` (see `results_v2_frozen/PROVENANCE.md` for the authoritative inventory). These are **legacy validation fixtures** — use them to develop and offline-test your defense *without waiting for live A04–A06 runs*. When Ibrahim's live attacks are ready, he replaces fixtures with real outputs for the final integrated evaluation.

Each bundle contains what you need for offline defense evaluation:
- `memory_before.jsonl` / `injected_records.jsonl` / `memory_after.jsonl` — full memory state + the poison delta (keyed on `(layer, id)`).
- `retrieval_trace.jsonl` — the exact retrieved set per query (your defense's input snapshot).
- `metrics.json` (RET) / `parsed_actions.json` (PLAN) — outcomes with denominators.
- `manifest.json` — `config_hash`, canonical IDs, `validity`/`run_class`, commit, seed.

**Regenerable memory:** `build_profile("P1")` (3-record sparse baseline) and `build_profile("P2")` (~60-record operational mixture) are deterministic — use them to synthesize controlled conflicting/stale/insufficient-corroboration test inputs for WP5.

**Signed-false-memory fixtures specifically:** the A04 (`S16`) / A05 (`S17`) bundles are your primary offline targets. C5/A05 has an accepted L2 planner smoke (signed-insider adoption).

---

## 4. Deliverables & dates (WP4 / WP5)

### WP4 — Defense design (Aug 1–4) — **your immediate deliverable, due Aug 4**
Three things, delivered together by **August 4**:
1. **Defense design memo** — candidate comparison (corroboration / conflict / spatial-temporal / action-gating): assumptions, required inputs, expected benefit, failure modes; recommend one bounded design.
2. **Interface decision** — confirm the plan's separate-stage default (or justify inside-retrieval), per §2, agreed with Dr. Qian.
3. **Test plan** (+ decision record, which becomes the FD1 input).

*Milestone Aug 4:* your recommendation is reviewed alongside the S16–S18 (A04–A06) traces.

### WP5 — Defense implementation + tooling (Aug 3–10)
- **Defense code** implementing the selected design behind the fixed interface, with **tests** on signed-false / benign / conflicting / stale / insufficient-corroboration records.
- **Offline utility results** (benign recall, false positives, overhead, residual failures).
- **Shared statistics / CI pipeline** — the campaign layer emits `paired_results.csv` + denominators (seed-as-unit) for you to consume; confidence intervals are yours to add. *Recommended method: Wilson / bootstrap CIs — **pending Dr. Qian's approval of the statistical method** (she owns statistical validity and denominators).*
- **Independent verification report**: reproduce ≥1 of Ibrahim's memory/k/agent generalization results from frozen inputs.
- **README** + **one-command reproduction**.
- *Milestone Aug 8:* preliminary defense prototype available. *Aug 10:* defense + CI + verification integration-ready.

### WP6 — Integration (Aug 8–15, with Ibrahim)
- Support integration: no-defense / provenance / semantic-defense comparisons on **≥3 planners** + selected PX4/Gazebo cases; failure analysis; figure regeneration.
- Ibrahim independently verifies ≥1 of your defense results before integration; you independently check ≥1 generalization figure.

---

## 5. Constraints (non-negotiable)

**Attacks / harness.** Do not modify attack code, the taxonomy identity block, or the evidence-bundle writer. Do not tune attacks or require them to succeed — negative results are preserved honestly. Attack authorship is Ibrahim's; you consume their outputs.

**Planner.** Your defense integrates at the retrieval→planner boundary only (§2). Do not alter planner prompting or the supervisor/scout topology.

**Metrics.** Use the defined metrics: RET → CCR/MTR/RIS/CASR (`utils/metrics.py`); PLAN → coordinate_adoption / constraint_refusal / target_omission / unsafe_entry (`evidence/outcomes.py`, `planner.py`). **Denominators are honest:** attempted vs valid-plan are separate; timeout / parsing / infrastructure failures stay in the denominator and are **never** recoded as behavioral outcomes.

**Evidence.** No result enters the paper without config + seed + denominator + raw output + generating script. Seeds are frozen **101–110**; `temp=0.0` unless temperature is the variable under study. `s12` / `s15` runners are pinned — do not touch.

**Production results.** `results_v2_frozen/` is **immutable** — never write, edit, move, or delete anything there, and never set `AEROMIND_V2_ROOT`. Production V3 evidence is admissible **only** under the real repo-anchored `results_v3_raw/`. A run under an env-redirected root (`AEROMIND_V3_RAW_ROOT` / `AEROMIND_V3_CAMPAIGNS_ROOT`) is labeled `validity=preflight` and is **excluded from paper statistics by default** — that is the mode you develop in until FD1 + the spec freeze land. SITL uses `--vehicle-backend px4` (fail-loud; no silent mock).

**Commits.** Branch from the handoff tag (see below); every implementation commit appends to `docs/V3_EXECUTION_LOG.md` with WP + reviewer mapping. Commit only genuine, tested changes.

---

## 6. One preflight reproduction command

Run entirely in a disposable sandbox (writes `validity=preflight` bundles; touches no production). Flags below are verified against `experiment_runner.py --help`.

```bash
cd /path/to/AeroMind
export AEROMIND_V3_RAW_ROOT="$(mktemp -d)/raw"
export AEROMIND_V3_CAMPAIGNS_ROOT="$(mktemp -d)/camp"

python3 experiments/experiment_runner.py \
  --scenario A05_SIGNED_FALSE_OBSERVATION --mode RET \
  --profile MEM060 \
  --model gpt-oss:20b --defense off \
  --seeds 101 --results-layout v3 --evidence-bundle \
  --topk 3 \
  --output "$AEROMIND_V3_RAW_ROOT"

# then confirm the bundle is preflight-labeled (never production):
find "$AEROMIND_V3_RAW_ROOT" -name manifest.json -exec \
  python3 -c "import json,sys;m=json.load(open(sys.argv[1]));print(m['validity'],m['run_class'],m['canonical']['attack'])" {} \;

rm -rf "$AEROMIND_V3_RAW_ROOT" "$AEROMIND_V3_CAMPAIGNS_ROOT"   # dispose sandbox
```

Expected: `preflight preflight A05_SIGNED_FALSE_OBSERVATION`.

**Flag notes (from `--help`):**
- `--evidence-bundle` is **required** — without it no bundle is emitted (only a summary `.json`).
- `--output` here points at the sandbox so nothing lands in `results_v2_frozen/`; leaving it unset would default under `results_v2_frozen/`.
- **Axis-flag naming is counter-intuitive:** `--profile` = the **Memory** axis (`MEM003`/`MEM060`, legacy `P1`/`P2`); `--mission` = the **Task** axis (`T01`–`T04`, legacy `M1`–`M4`, default `M1`/`T01`). A05 has no task lock, so `--mission` is omitted here (default `T01`).
- `--temp` is a **planning-mode** axis only and is ignored in `RET`; use it with `--mode PLAN`. `--topk` applies to retrieval and planning.
- Requires `gpt-oss:20b` in Ollama; swap `--model` for any locally available model.

---

## 7. Files Cam must return

Per the team plan's acceptance rules, deliver a self-contained package:

- [ ] **Defense code / patch** behind the fixed interface (§2), against the handoff tag.
- [ ] **Tests** covering signed-false, benign, conflicting, stale, insufficient-corroboration records.
- [ ] **Configs + seeds** (canonical `D`-token registered per FD1; seeds 101–110).
- [ ] **Raw outputs + CSVs** (offline utility: benign recall, false positives, overhead, residual failures).
- [ ] **Statistics / CI scripts** (confidence intervals; seed-as-unit).
- [ ] **Figures** (defense-ablation + benign-utility) regenerated from scripts.
- [ ] **Independent verification report** reproducing ≥1 generalization result from frozen inputs.
- [ ] **WP4 design memo + decision record** (candidate comparison, selected design, interface choice, FD1 mapping).
- [ ] **README with one-command reproduction.**

---

## 8. First-day checklist

- [ ] Clone at the handoff tag; confirm clean tree and `python3 -m pytest tests/ -q` → all green (232).
- [ ] Read this doc, `V3_PREFLIGHT_VALIDATION_REPORT.md`, `TAXONOMY_CROSSWALK_V3.md`.
- [ ] Run the §6 preflight command; confirm you get a `preflight` bundle and can read its `retrieval_trace.jsonl` / `memory_*.jsonl`.
- [ ] Read `uavsys/memory/defense.py` + `signing.py` (reference) and one frozen A05/A04 bundle end-to-end.
- [ ] Open the interface-shape question (inside-retrieval vs separate stage) — draft the trade-off for the WP4 memo.
- [ ] Draft the FD1 mapping proposal (`D`-token ↔ config ↔ capability; define canonical `D4`).
- [ ] Confirm the constraints in §5 (immutable V2; production only under real `results_v3_raw/`; frozen seeds; honest denominators).
- [ ] Sync with Dr. Qian on candidate-defense scope; sync with Ibrahim on fixture format and the frozen-input set for independent verification.
- [ ] **Note your first hard deadline: the WP4 design memo + interface decision + test plan are due August 4 (§4).**

---

*Questions on the harness, fixtures, or interface → Ibrahim. Defense selection, statistics, denominators, and technical claims → Dr. Qian. Scope and priority → Dr. Liu.*
