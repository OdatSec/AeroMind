"""Sandbox matrix: every scientific axis-combination must map to a UNIQUE raw
directory (no overwrite, no mixing), and a paired campaign must assemble from the
matching A00 clean + attack bundles. All artifacts live under pytest's tmp_path
(auto-deleted); production roots are never touched.

Run: python3 -m pytest tests/test_v3_sandbox_matrix.py
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys import paths as P  # noqa: E402
from uavsys import campaigns as CMP  # noqa: E402
from uavsys import taxonomy as TX  # noqa: E402
from uavsys.evidence.bundle import EvidenceBundle  # noqa: E402

CLEAN = lambda repo: {"commit": "aaaaaaa", "dirty": False}  # noqa: E731

MODELS = ["gpt-oss:20b", "llama3.1:8b"]
ATTACKS = ["A07_FALSE_COMPLETION", "A08_FALSE_SAFETY"]   # + A00_CLEAN control
EVALS = ["RET", "PLAN"]
MEMS = ["MEM003_SPARSE", "MEM060_OPERATIONAL"]
TOPKS = [3, 10]
BUDGETS = [1, 3]
TEMPS = [0.0, 0.1]
DEFENSES = ["D0", "D1"]
SEEDS = [101, 102, 103]


def test_full_matrix_paths_are_unique_no_mixing(tmp_path):
    """2 models x (2 attacks + clean) x 2 evals x 2 mem x 2 topk x 2 budget x
    2 temp x 2 defense x 3 seeds -> every RUN dir distinct; every SCIENTIFIC cell
    (ignoring seed) distinct; clean and attack never share a parent."""
    root = str(tmp_path / "results_v3_raw")
    run_dirs, cell_dirs = set(), set()
    combos = itertools.product(MODELS, ATTACKS + ["A00_CLEAN"], EVALS, MEMS,
                               TOPKS, BUDGETS, TEMPS, DEFENSES)
    n = 0
    for model, attack, ev, mem, tk, bud, tmp, dfn in combos:
        cell = P.v3_raw_run_parent(attack, "T02_MULTI_TARGET", mem, ev, model, dfn,
                                   tk, bud, tmp, 0, root=root)
        cell_parent = os.path.dirname(cell)   # strip seed level -> the scientific cell
        cell_dirs.add(cell_parent)
        for seed in SEEDS:
            d = P.v3_raw_run_parent(attack, "T02_MULTI_TARGET", mem, ev, model, dfn,
                                    tk, bud, tmp, seed, root=root)
            assert d not in run_dirs, f"COLLISION: {d}"
            run_dirs.add(d)
            n += 1
    # unique run dirs == full product count; unique cells == product without seed
    assert n == len(run_dirs) == len(MODELS) * 3 * len(EVALS) * len(MEMS) * \
        len(TOPKS) * len(BUDGETS) * len(TEMPS) * len(DEFENSES) * len(SEEDS)
    assert len(cell_dirs) == len(MODELS) * 3 * len(EVALS) * len(MEMS) * \
        len(TOPKS) * len(BUDGETS) * len(TEMPS) * len(DEFENSES)
    # clean vs attack never share a top-level ATTACK root
    clean_roots = {p for p in cell_dirs if os.sep + "A00_CLEAN" + os.sep in p + os.sep}
    attack_roots = {p for p in cell_dirs if "A00_CLEAN" not in p}
    assert clean_roots and attack_roots and not (clean_roots & attack_roots)


def _make_bundle(root, *, attack, model, ev, mem, tk, bud, tmp, dfn, seed, tmp_path):
    canon = TX.canonical_manifest_ids(attack, "T02_MULTI_TARGET", mem, ev, dfn)
    base = P.v3_raw_run_parent(attack, "T02_MULTI_TARGET", mem, ev, model, dfn,
                               tk, bud, tmp, seed, root=root)
    spec = tmp_path / "spec.yaml"
    if not spec.exists():
        spec.write_text("meta: {}\n")
    b = EvidenceBundle(
        scenario=canon["legacy_aliases"]["attack"][-1], legacy_id="x", layer="L1",
        seed=seed, model=model, config={"CHAT_MODEL": model, "DEFENSE_PROVENANCE_SECRET": "x",
                                        "TOP_K_SCOUT": tk, "TEMPERATURE": tmp, "SEED": seed},
        canonical_ids=canon, short_run_id=True, base_dir=base, results_root=root,
        spec_path=str(spec), git_state_fn=CLEAN)
    b.record_memory([{"id": 1}], [], [{"id": 1}])
    b.record_retrieval([{"agent": "Agent 1"}])
    b.record_metrics({"ccr": 0.0})
    b.set_status("success")
    return b.finalize()


def test_real_bundles_distinct_and_campaign_pairs_clean_with_attack(tmp_path):
    root = str(tmp_path / "results_v3_raw")
    croot = str(tmp_path / "results_v3_campaigns")
    made = []
    # a small real slice: A08 attack + A00 clean, 2 models, RET+PLAN, 2 seeds
    for model in MODELS:
        for ev in EVALS:
            for seed in (101, 102):
                for attack in ("A08_FALSE_SAFETY", "A00_CLEAN"):
                    made.append(_make_bundle(root, attack=attack, model=model, ev=ev,
                                             mem="MEM060_OPERATIONAL", tk=3, bud=1, tmp=0.1,
                                             dfn="D0", seed=seed, tmp_path=tmp_path))
    assert len(made) == len(set(made)) == 16          # all distinct dirs, none overwritten

    # pair the A00 clean bundles with A08 for one (model, eval) cell
    clean = [d for d in made if os.sep + "A00_CLEAN" + os.sep in d
             and os.sep + "model-gpt-oss-20b" + os.sep in d and os.sep + "PLAN" + os.sep in d]
    atk = [d for d in made if os.sep + "A08_FALSE_SAFETY" + os.sep in d
           and os.sep + "model-gpt-oss-20b" + os.sep in d and os.sep + "PLAN" + os.sep in d]
    out = CMP.build_campaign(attack="A08_FALSE_SAFETY", task="T02_MULTI_TARGET",
                             memory="MEM060_OPERATIONAL", evaluation="PLAN",
                             model="gpt-oss:20b", defense="D0", topk=3, budget=1, temp=0.1,
                             clean_bundles=clean, attack_bundles=atk, campaigns_root=croot)
    bi = open(os.path.join(out, "bundle_index.yaml")).read()
    assert "clean_bundles:" in bi and "attack_bundles:" in bi
    summ = json.load(open(os.path.join(out, "campaign_summary.json")))
    assert summ["clean_arm"]["bundles"] == 2 and summ["attack_arm"]["bundles"] == 2
    # campaign nested under the attack's axis hierarchy
    assert os.path.relpath(out, croot).startswith(os.path.join("A08_FALSE_SAFETY", "T02_MULTI_TARGET"))
