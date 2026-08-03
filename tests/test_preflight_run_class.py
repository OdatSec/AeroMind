"""Preflight run-class: bundles written under an env-REDIRECTED V3 sandbox root
must be labeled validity="preflight" (valid=False) and NEVER "production", even
when every integrity gate passes. Campaign/paper statistics exclude non-production
bundles by default. Production validity is allowed only under the real repo-anchored
results_v3_raw/ root.

Run: python3 -m pytest tests/test_preflight_run_class.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys import paths as P  # noqa: E402
from uavsys import campaigns as CMP  # noqa: E402
from uavsys.evidence.bundle import EvidenceBundle  # noqa: E402

CLEAN = lambda repo: {"commit": "aaaaaaa", "dirty": False}  # noqa: E731


def _spec(tmp):
    s = tmp / "spec.yaml"
    if not s.exists():
        s.write_text("meta: {}\n")
    return str(s)


def _bundle(base, results_root, tmp, *, run_class=None):
    b = EvidenceBundle(
        scenario="C1", legacy_id="S01", layer="L1", seed=42, model="gpt-oss:20b",
        config={"CHAT_MODEL": "gpt-oss:20b", "DEFENSE_PROVENANCE_SECRET": "x"},
        base_dir=str(base), results_root=str(results_root), spec_path=_spec(tmp),
        run_class=run_class, git_state_fn=CLEAN)
    b.record_memory([{"id": 1}], [], [{"id": 1}])
    b.record_retrieval([{"agent": "Agent 1"}])
    b.record_metrics({"ccr": 0.0})
    b.set_status("success")
    return b.finalize()


def test_canonical_root_helper_repo_anchored_not_redirected(tmp_path, monkeypatch):
    """is_canonical_production_root is the REAL repo root regardless of env redirect."""
    monkeypatch.setenv("AEROMIND_V3_RAW_ROOT", str(tmp_path / "sbox"))
    assert P.v3_raw_is_redirected() is True
    real_v3 = os.path.join(P.REPO_ROOT, P.RESULTS_V3_RAW_NAME)
    assert P.is_canonical_production_root(os.path.join(real_v3, "x"))
    assert P.is_canonical_production_root(os.path.join(P.RESULTS_ROOT, "x"))
    assert not P.is_canonical_production_root(str(tmp_path / "sbox" / "x"))  # sandbox != canonical


def test_redirected_sandbox_bundle_is_preflight_not_production(tmp_path, monkeypatch):
    """Env-redirected sandbox root -> validity=preflight, valid=False (all gates pass)."""
    sandbox = tmp_path / "sbox_raw"
    monkeypatch.setenv("AEROMIND_V3_RAW_ROOT", str(sandbox))
    base = sandbox / "A01_FALSE_OBSERVATION" / "seed-0042"
    out = _bundle(base, sandbox, tmp_path)               # run_class auto-detected
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["validity"] == "preflight" and m["valid"] is False
    assert m["run_class"] == "preflight"
    # integrity gates still recorded honestly
    assert m["dirty_start"] is False and m["commit_start"] == "aaaaaaa"


def test_no_env_tmp_root_stays_production(tmp_path, monkeypatch):
    """Without the env redirect, a bundle under its results_root is production (unchanged)."""
    monkeypatch.delenv("AEROMIND_V3_RAW_ROOT", raising=False)
    root = tmp_path / "results_v3_raw"
    out = _bundle(root / "A00_CLEAN" / "seed-0042", root, tmp_path)
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["validity"] == "production" and m["valid"] is True
    assert m["run_class"] == "production"


def test_explicit_run_class_forces_preflight_without_env(tmp_path, monkeypatch):
    """run_class='preflight' downgrades to preflight even with no env redirect."""
    monkeypatch.delenv("AEROMIND_V3_RAW_ROOT", raising=False)
    root = tmp_path / "results_v3_raw"
    out = _bundle(root / "A00_CLEAN" / "seed-0043", root, tmp_path, run_class="preflight")
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["validity"] == "preflight" and m["valid"] is False


def _mk_manifest_bundle(dirpath, seed, validity):
    os.makedirs(dirpath, exist_ok=True)
    json.dump({"run_id": os.path.basename(dirpath), "seed": seed,
               "scenario": "A01_FALSE_OBSERVATION", "outcome": "success",
               "validity": validity, "valid": validity == "production",
               "canonical": {"attack": "A01_FALSE_OBSERVATION", "task": "T01_SEARCH_RESCUE"}},
              open(os.path.join(dirpath, "manifest.json"), "w"))
    json.dump({"valid_plan": True, "planner_outcome": "success",
               "coordinate_adoption": False, "target_omission_rate": 0.0,
               "unsafe_entry": None},
              open(os.path.join(dirpath, "parsed_actions.json"), "w"))


def test_campaign_excludes_preflight_bundles_by_default(tmp_path):
    """Paper stats exclude non-production bundles by default; count is recorded."""
    croot = tmp_path / "camp"
    prod = [str(tmp_path / f"prod{s}") for s in (1, 2)]
    pref = [str(tmp_path / f"pref{s}") for s in (1, 2)]
    for i, d in enumerate(prod, 1): _mk_manifest_bundle(d, 100 + i, "production")
    for i, d in enumerate(pref, 1): _mk_manifest_bundle(d, 200 + i, "preflight")

    out = CMP.build_campaign(
        attack="A01_FALSE_OBSERVATION", task="T01_SEARCH_RESCUE", memory="MEM060_OPERATIONAL",
        evaluation="PLAN", model="gpt-oss:20b", defense="D0", topk=3, budget=1, temp=0.1,
        clean_bundles=prod, attack_bundles=pref, campaigns_root=str(croot))
    summ = json.load(open(os.path.join(out, "campaign_summary.json")))
    # production clean kept (2); preflight attack all excluded (0)
    assert summ["clean_arm"]["bundles"] == 2 and summ["attack_arm"]["bundles"] == 0
    assert summ["bundle_selection"]["production_only"] is True
    assert summ["bundle_selection"]["excluded_non_production"] == 2
    assert summ["bundle_selection"]["attack_excluded"] == 2


def test_campaign_can_opt_in_to_non_production(tmp_path):
    """include_non_production=True assembles a labeled pre-production validation campaign."""
    croot = tmp_path / "camp"
    pref = [str(tmp_path / f"p{s}") for s in (1, 2)]
    for i, d in enumerate(pref, 1): _mk_manifest_bundle(d, 200 + i, "preflight")
    out = CMP.build_campaign(
        attack="A01_FALSE_OBSERVATION", task="T01_SEARCH_RESCUE", memory="MEM060_OPERATIONAL",
        evaluation="PLAN", model="gpt-oss:20b", defense="D0", topk=3, budget=1, temp=0.1,
        clean_bundles=[], attack_bundles=pref, campaigns_root=str(croot),
        include_non_production=True)
    summ = json.load(open(os.path.join(out, "campaign_summary.json")))
    assert summ["attack_arm"]["bundles"] == 2
    assert summ["bundle_selection"]["production_only"] is False
    assert summ["bundle_selection"]["excluded_non_production"] == 0
