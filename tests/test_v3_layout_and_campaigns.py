"""V3 raw layout, canonical manifest identity, short run dirs, campaign layer +
insights generation, and V2 backward compatibility (hermetic; no DB/LLM/PX4).

Run: python3 -m pytest tests/test_v3_layout_and_campaigns.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys import paths as P  # noqa: E402
from uavsys import taxonomy as TX  # noqa: E402
from uavsys import campaigns as CMP  # noqa: E402
from uavsys.evidence.bundle import EvidenceBundle  # noqa: E402

CLEAN = lambda repo: {"commit": "aaaaaaa", "dirty": False}  # noqa: E731


# ---- hierarchical raw path + short seed dir ----
def test_v3_raw_run_parent_full_axis_hierarchy():
    p = P.v3_raw_run_parent("A08_FALSE_SAFETY", "T03_RESTRICTED_ZONE",
                            "MEM060_OPERATIONAL", "PLAN", "gpt-oss:20b", "D0",
                            3, 1, 0.1, 42)
    rel = os.path.relpath(p, P.RESULTS_V3_RAW).split(os.sep)
    assert rel == ["A08_FALSE_SAFETY", "T03_RESTRICTED_ZONE", "MEM060_OPERATIONAL",
                   "PLAN", "model-gpt-oss-20b", "D0", "topk-03", "budget-01",
                   "temp-0.1", "seed-0042"]      # model- prefix, all axes, zero-padded


def test_v3_conditional_axes_multi_and_sitl():
    multi = P.v3_raw_run_parent("A02_SHARED_MEMORY_EXPOSURE", "T01_SEARCH_RESCUE",
                                "MEM060_OPERATIONAL", "MULTI", "m", "D0",
                                3, None, None, 7, agents=8)
    assert "agents-08" in multi and "temp-na" in multi and "budget-default" in multi
    assert "backend-" not in multi
    sitl = P.v3_raw_run_parent("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE",
                               "MEM060_OPERATIONAL", "SITL", "m", "D0",
                               3, 3, 0.1, 7, backend="px4")
    assert "backend-px4" in sitl and "agents-" not in sitl


def test_invalid_attack_task_fails_loud_and_creates_no_dir(tmp_path):
    """A08 is locked to T03; A08+T02 must raise and create NO directory."""
    root = str(tmp_path / "results_v3_raw")
    with pytest.raises(ValueError, match="locked to T03"):
        P.v3_raw_run_parent("A08_FALSE_SAFETY", "T02_MULTI_TARGET", "MEM060_OPERATIONAL",
                            "PLAN", "gpt-oss:20b", "D0", 3, 1, 0.1, 42, root=root)
    with pytest.raises(ValueError, match="locked to T03"):
        P.v3_campaign_dir("A08_FALSE_SAFETY", "T02_MULTI_TARGET", "MEM060_OPERATIONAL",
                          "PLAN", "gpt-oss:20b", "D0", 3, 1, 0.1, root=root)
    assert not os.path.exists(root)   # nothing was created for the invalid combo


def test_production_roots_include_v3_not_legacy():
    assert P.is_production_root(os.path.join(P.RESULTS_V3_RAW, "x"))
    assert P.is_production_root(os.path.join(P.RESULTS_ROOT, "x"))
    assert not P.is_production_root(os.path.join(P.REPO_ROOT, "results_legacy_raid", "x"))


def _spec(tmp):
    s = tmp / "spec.yaml"; s.write_text("meta: {}\n"); return str(s)


def _bundle(base, results_root, tmp, *, short, canon):
    b = EvidenceBundle(
        scenario="C1", legacy_id="S01", layer="L1", seed=42, model="gpt-oss:20b",
        config={"CHAT_MODEL": "gpt-oss:20b", "DEFENSE_PROVENANCE_SECRET": "x"},
        mission="M2", profile="P2", canonical_ids=canon, short_run_id=short,
        base_dir=str(base), results_root=str(results_root), spec_path=_spec(tmp),
        git_state_fn=CLEAN)
    b.record_memory([{"id": 1}], [], [{"id": 1}])
    b.record_retrieval([{"agent": "Agent 1"}])
    b.record_metrics({"ccr": 0.0})
    b.set_status("success")
    return b.finalize()


def test_v3_bundle_short_run_id_and_canonical_manifest(tmp_path):
    root = tmp_path / "results_v3_raw"; base = root / "A08_FALSE_SAFETY" / "seed-0042"
    canon = TX.canonical_manifest_ids("C1", "M2", "P2", "PLAN", "D0")
    out = _bundle(base, root, tmp_path, short=True, canon=canon)
    run_dir = os.path.basename(out)
    assert run_dir.startswith("run-") and len(run_dir) <= 24    # SHORT dir (run-<8>-<8>=21)
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["validity"] == "production" and m["valid"] is True  # v3 root is production
    assert m["canonical"]["attack"] == "A01_FALSE_OBSERVATION"
    assert m["canonical"]["legacy_aliases"]["attack"] == ["C1", "S01"]
    assert m["config_hash"] and m["run_id"] == run_dir           # full metadata in manifest


def test_v2_bundle_unchanged_long_name_no_canonical(tmp_path):
    """Backward compat: default (no short_run_id, no canonical) keeps the long v2
    run-id and records canonical as null."""
    root = tmp_path / "results_v2_frozen"; root.mkdir()
    out = _bundle(root, root, tmp_path, short=False, canon=None)
    run_dir = os.path.basename(out)
    assert run_dir.startswith("C1__L1__model-gpt-oss-20b__seed0042__")  # legacy long name
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["canonical"] is None and m["validity"] == "production"


# ---- campaign layer + insights + index ----
def _mk_bundle(dirpath, seed, arm, omission):
    os.makedirs(dirpath, exist_ok=True)
    json.dump({"run_id": os.path.basename(dirpath), "seed": seed, "scenario": "A07_FALSE_COMPLETION",
               "outcome": "success", "validity": "production", "valid": True,
               "canonical": {"attack": "A07_FALSE_COMPLETION", "task": "T02_MULTI_TARGET"}},
              open(os.path.join(dirpath, "manifest.json"), "w"))
    json.dump({"valid_plan": True, "planner_outcome": "success",
               "coordinate_adoption": False, "target_omission_rate": omission,
               "unsafe_entry": None},
              open(os.path.join(dirpath, "parsed_actions.json"), "w"))


def test_campaign_build_generates_all_artifacts_and_insights(tmp_path):
    croot = tmp_path / "camp"
    clean = [str(tmp_path / f"clean{s}") for s in (1, 2)]
    atk = [str(tmp_path / f"atk{s}") for s in (1, 2)]
    for i, d in enumerate(clean, 1): _mk_bundle(d, 100 + i, "clean", 0.0)
    for i, d in enumerate(atk, 1): _mk_bundle(d, 100 + i, "attack", round(1 / 6, 4))

    out = CMP.build_campaign(
        attack="A07_FALSE_COMPLETION", task="T02_MULTI_TARGET", memory="MEM060_OPERATIONAL",
        evaluation="PLAN", model="gpt-oss:20b", defense="D0", topk=3, budget=1, temp=0.1,
        clean_bundles=clean, attack_bundles=atk,
        research_question="Does false completion cause target omission?",
        reviewer_concern="452A", supported_claim="False completion -> selective omission.",
        caveats=["n=2 fixture", "single model"], recommended_figure="paired omission bar",
        campaigns_root=str(croot))

    # campaign folder mirrors the raw scientific-axis hierarchy
    rel = os.path.relpath(out, croot).split(os.sep)
    assert rel == ["A07_FALSE_COMPLETION", "T02_MULTI_TARGET", "MEM060_OPERATIONAL",
                   "PLAN", "model-gpt-oss-20b", "D0", "topk-03", "budget-01", "temp-0.1"]
    for fn in ("README.md", "campaign_summary.json", "paired_results.csv",
               "bundle_index.yaml", "INSIGHTS_DRAFT.md", "CLAIMS.md"):
        assert os.path.exists(os.path.join(out, fn)), fn
    ins = open(os.path.join(out, "INSIGHTS_DRAFT.md")).read()
    for sec in ("Research question", "Clean vs attack", "Exact denominators",
                "Reviewer concern", "Supported paper claim", "Caveats", "raw-bundle references"):
        assert sec in ins, sec
    assert "452A" in ins and "n=2 fixture" in ins
    summ = json.load(open(os.path.join(out, "campaign_summary.json")))
    assert summ["clean_arm"]["attempted"] == 2 and summ["attack_arm"]["valid"] == 2
    assert summ["topk"] == 3 and summ["budget"] == 1 and summ["temp"] == 0.1
    # INDEX.md refreshed (walks the nested tree)
    idx = open(os.path.join(croot, "INDEX.md")).read()
    assert "A07_FALSE_COMPLETION" in idx and "topk" in idx


def test_campaign_never_writes_paper_findings(tmp_path):
    croot = tmp_path / "camp"; croot.mkdir()
    CMP.refresh_index(str(croot))
    assert not os.path.exists(os.path.join(croot, "PAPER_FINDINGS.md"))  # human-only, never auto-written


def test_v2_frozen_root_name_unchanged():
    # guardrail: the immutable v2 root name must not have been repurposed
    assert P.RESULTS_ROOT_NAME == "results_v2_frozen"
    assert P.RESULTS_V3_RAW_NAME == "results_v3_raw"


def test_v3_roots_redirectable_via_env_v2_never(monkeypatch, tmp_path):
    """V3 roots honor AEROMIND_V3_* env (sandbox/CI); V2 root is never overridable."""
    import importlib
    sandbox = str(tmp_path / "sbox_raw")
    monkeypatch.setenv("AEROMIND_V3_RAW_ROOT", sandbox)
    monkeypatch.setenv("AEROMIND_V3_CAMPAIGNS_ROOT", str(tmp_path / "sbox_camp"))
    monkeypatch.setenv("AEROMIND_V2_ROOT", str(tmp_path / "should_be_ignored"))
    mod = importlib.reload(P)
    try:
        assert mod.RESULTS_V3_RAW == sandbox
        assert mod.RESULTS_V3_CAMPAIGNS == str(tmp_path / "sbox_camp")
        assert mod.is_production_root(os.path.join(sandbox, "x"))     # sandbox is a production root
        assert mod.RESULTS_ROOT.endswith("results_v2_frozen")        # v2 NOT redirected
    finally:
        for v in ("AEROMIND_V3_RAW_ROOT", "AEROMIND_V3_CAMPAIGNS_ROOT", "AEROMIND_V2_ROOT"):
            monkeypatch.delenv(v, raising=False)
        importlib.reload(P)                                          # restore module for other tests
