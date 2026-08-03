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
# each attack paired with a task it is allowed on (variants are task-locked);
# A00 clean pairs with each attack's task so the campaign arms match.
ATTACK_TASKS = [("A07_FALSE_COMPLETION", "T02_MULTI_TARGET"),
                ("A08_FALSE_SAFETY", "T03_RESTRICTED_ZONE")]
EVALS = ["RET", "PLAN"]
MEMS = ["MEM003_SPARSE", "MEM060_OPERATIONAL"]
TOPKS = [3, 10]
BUDGETS = [1, 3]
TEMPS = [0.0, 0.1]
DEFENSES = ["D0", "D1"]
SEEDS = [101, 102, 103]


def test_full_matrix_paths_are_unique_no_mixing(tmp_path):
    """2 models x (2 attacks + matching clean) x 2 evals x 2 mem x 2 topk x
    2 budget x 2 temp x 2 defense x 3 seeds -> every RUN dir distinct; every
    SCIENTIFIC cell (ignoring seed) distinct; clean and attack never share a
    parent. Attacks use their LOCKED task (invalid combos are rejected elsewhere)."""
    root = str(tmp_path / "results_v3_raw")
    # (attack, task) pairs: each attack on its task + A00 clean on the same task.
    at_pairs = [(a, t) for (a, t) in ATTACK_TASKS] + [("A00_CLEAN", t) for (_, t) in ATTACK_TASKS]
    run_dirs, cell_dirs = set(), set()
    combos = itertools.product(MODELS, at_pairs, EVALS, MEMS, TOPKS, BUDGETS, TEMPS, DEFENSES)
    n = 0
    for model, (attack, task), ev, mem, tk, bud, tmp, dfn in combos:
        cell = os.path.dirname(P.v3_raw_run_parent(attack, task, mem, ev, model, dfn,
                                                   tk, bud, tmp, 0, root=root))
        cell_dirs.add(cell)
        for seed in SEEDS:
            d = P.v3_raw_run_parent(attack, task, mem, ev, model, dfn, tk, bud, tmp, seed, root=root)
            assert d not in run_dirs, f"COLLISION: {d}"
            run_dirs.add(d)
            n += 1
    total_cells = len(MODELS) * len(at_pairs) * len(EVALS) * len(MEMS) * \
        len(TOPKS) * len(BUDGETS) * len(TEMPS) * len(DEFENSES)
    assert n == len(run_dirs) == total_cells * len(SEEDS)
    assert len(cell_dirs) == total_cells
    clean_roots = {p for p in cell_dirs if os.sep + "A00_CLEAN" + os.sep in p + os.sep}
    attack_roots = {p for p in cell_dirs if "A00_CLEAN" not in p}
    assert clean_roots and attack_roots and not (clean_roots & attack_roots)


def _make_bundle(root, *, attack, task, model, ev, mem, tk, bud, tmp, dfn, seed, tmp_path):
    canon = TX.canonical_manifest_ids(attack, task, mem, ev, dfn)
    base = P.v3_raw_run_parent(attack, task, mem, ev, model, dfn,
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
    # a small real slice: A08 attack + A00 clean, both on A08's LOCKED task (T03),
    # 2 models, RET+PLAN, 2 seeds
    TASK = "T03_RESTRICTED_ZONE"
    for model in MODELS:
        for ev in EVALS:
            for seed in (101, 102):
                for attack in ("A08_FALSE_SAFETY", "A00_CLEAN"):
                    made.append(_make_bundle(root, attack=attack, task=TASK, model=model, ev=ev,
                                             mem="MEM060_OPERATIONAL", tk=3, bud=1, tmp=0.1,
                                             dfn="D0", seed=seed, tmp_path=tmp_path))
    assert len(made) == len(set(made)) == 16          # all distinct dirs, none overwritten

    # pair the A00 clean bundles with A08 for one (model, eval) cell
    clean = [d for d in made if os.sep + "A00_CLEAN" + os.sep in d
             and os.sep + "model-gpt-oss-20b" + os.sep in d and os.sep + "PLAN" + os.sep in d]
    atk = [d for d in made if os.sep + "A08_FALSE_SAFETY" + os.sep in d
           and os.sep + "model-gpt-oss-20b" + os.sep in d and os.sep + "PLAN" + os.sep in d]
    out = CMP.build_campaign(attack="A08_FALSE_SAFETY", task=TASK,
                             memory="MEM060_OPERATIONAL", evaluation="PLAN",
                             model="gpt-oss:20b", defense="D0", topk=3, budget=1, temp=0.1,
                             clean_bundles=clean, attack_bundles=atk, campaigns_root=croot)
    bi = open(os.path.join(out, "bundle_index.yaml")).read()
    assert "clean_bundles:" in bi and "attack_bundles:" in bi
    summ = json.load(open(os.path.join(out, "campaign_summary.json")))
    assert summ["clean_arm"]["bundles"] == 2 and summ["attack_arm"]["bundles"] == 2
    # campaign nested under the attack's axis hierarchy
    assert os.path.relpath(out, croot).startswith(os.path.join("A08_FALSE_SAFETY", TASK))


def test_topk_temp_overrides_change_path_and_hash(tmp_path):
    """--topk / --temp participate in BOTH the path and the config-hash: two runs
    differing only in topk (or temp) land in different dirs AND get different hashes."""
    root = str(tmp_path / "results_v3_raw")
    # path axis: topk-03 vs topk-10, temp-0.1 vs temp-0.7
    p3 = P.v3_raw_run_parent("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE", "MEM060_OPERATIONAL",
                             "PLAN", "gpt-oss:20b", "D0", 3, 1, 0.1, 42, root=root)
    p10 = P.v3_raw_run_parent("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE", "MEM060_OPERATIONAL",
                              "PLAN", "gpt-oss:20b", "D0", 10, 1, 0.1, 42, root=root)
    pt = P.v3_raw_run_parent("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE", "MEM060_OPERATIONAL",
                             "PLAN", "gpt-oss:20b", "D0", 3, 1, 0.7, 42, root=root)
    assert "topk-03" in p3 and "topk-10" in p10 and p3 != p10
    assert "temp-0.7" in pt and pt != p3
    # config-hash: TOP_K_SCOUT / TEMPERATURE are Config fields -> different hash
    from uavsys.evidence.bundle import EvidenceBundle
    base = {"CHAT_MODEL": "gpt-oss:20b", "DEFENSE_PROVENANCE_SECRET": "x", "SEED": 42}
    ax = {"mission": "M1", "profile": "P2", "budget": 1}
    h_k3 = EvidenceBundle._compute_config_hash(EvidenceBundle._to_config_dict(dict(base, TOP_K_SCOUT=3, TEMPERATURE=0.1)), run_axes=ax)
    h_k10 = EvidenceBundle._compute_config_hash(EvidenceBundle._to_config_dict(dict(base, TOP_K_SCOUT=10, TEMPERATURE=0.1)), run_axes=ax)
    h_t7 = EvidenceBundle._compute_config_hash(EvidenceBundle._to_config_dict(dict(base, TOP_K_SCOUT=3, TEMPERATURE=0.7)), run_axes=ax)
    assert h_k3 != h_k10 and h_k3 != h_t7        # topk and temp both change the fingerprint
