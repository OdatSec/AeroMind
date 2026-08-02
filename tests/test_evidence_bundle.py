"""
Tests for the evidence-bundle writer (uavsys/evidence/bundle.py).

All integrity rules are exercised hermetically via an injected git_state_fn and a
temp results-root, so tests never touch the real repo state or results_v2_frozen/.
No DB / LLM / PX4. Run: python3 -m pytest tests/test_evidence_bundle.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.evidence.bundle import EvidenceBundle, required_files, ABORTED_OUTCOMES  # noqa: E402

CLEAN = lambda repo: {"commit": "aaaaaaa", "dirty": False}  # noqa: E731
DIRTY = lambda repo: {"commit": "aaaaaaa", "dirty": True}   # noqa: E731


def _spec(tmp_path):
    p = tmp_path / "EXPERIMENT_SPEC_V2.yaml"
    p.write_text("meta:\n  spec_version: test\n")
    return str(p)


def _bundle(tmp_path, *, base_dir, results_root, git=CLEAN, layer="L1",
            allow_dirty=False, config=None):
    return EvidenceBundle(
        scenario="C1", legacy_id="S01", layer=layer, seed=42, model="gpt-oss:20b",
        defense_level="D0",
        config=config or {"CHAT_MODEL": "gpt-oss:20b", "DEFENSE_PROVENANCE_SECRET": "topsecret"},
        resolved_params={"mode": "retrieval", "k": 3},
        embedder={"name": "nomic-embed-text", "tag": "x", "digest": "d", "dim": 768},
        configured={"memory_profile": "sparse", "top_k": 3, "poison_budget": 3},
        base_dir=str(base_dir), results_root=str(results_root),
        spec_path=_spec(tmp_path), allow_dirty=allow_dirty, git_state_fn=git,
    )


def _fill_L1(b):
    b.record_memory(before=[{"id": 1}], injected=[{"id": 2, "source": "atk:S01"}], after=[{"id": 1}, {"id": 2}])
    b.record_retrieval([{"agent": "Agent 1", "matches": 3}])
    b.record_metrics({"ccr": 0.82, "casr": 1.0})


# ---- required-files policy ----
def test_required_files_success_vs_aborted():
    assert "metrics.json" in required_files("L1", "success")
    assert "planner_context.json" in required_files("L2", "success")
    # Aborted outcomes require only the base set (no planner/telemetry).
    for oc in ABORTED_OUTCOMES:
        assert required_files("L1", oc) == set(required_files("L1", oc)) & {
            "manifest.json", "config.yaml", "environment.json", "status.json", "checksums.sha256"}


# ---- development bundle (outside results root) ----
def test_dev_bundle_is_marked_invalid_and_complete(tmp_path):
    prod = tmp_path / "prod"; dev = tmp_path / "dev"
    prod.mkdir(); dev.mkdir()
    b = _bundle(tmp_path, base_dir=dev, results_root=prod, git=DIRTY, allow_dirty=True)
    _fill_L1(b)
    b.set_status("success")
    out = b.finalize()
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["valid"] is False and m["validity"] == "development-only"
    for f in ("manifest.json", "config.yaml", "environment.json", "status.json",
              "checksums.sha256", "metrics.json", "memory_after.jsonl"):
        assert os.path.exists(os.path.join(out, f))


# ---- production happy path ----
def test_production_success_writes_all_L1_files_atomically(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN)
    _fill_L1(b)
    b.set_status("success")
    out = b.finalize()
    assert out.startswith(str(prod))
    m = json.load(open(os.path.join(out, "manifest.json")))
    assert m["valid"] is True and m["validity"] == "production"
    assert m["config_hash"] and m["spec_hash"] and m["resolved_params"]["k"] == 3
    # no staging dir left behind
    assert not any(name.endswith(tuple(f".staging-{i}" for i in [])) for name in os.listdir(prod))
    assert [n for n in os.listdir(prod) if ".staging-" in n] == []


# ---- production integrity gates ----
def test_production_refuses_dirty_at_start(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    with pytest.raises(RuntimeError, match="dirty tree"):
        _bundle(tmp_path, base_dir=prod, results_root=prod, git=DIRTY)


def test_production_refuses_commit_change_during_run(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    calls = {"n": 0}
    def moving(repo):
        calls["n"] += 1
        return {"commit": "aaaaaaa" if calls["n"] == 1 else "bbbbbbb", "dirty": False}
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=moving)
    _fill_L1(b); b.set_status("success")
    with pytest.raises(RuntimeError, match="commit changed during run"):
        b.finalize()
    assert [n for n in os.listdir(prod) if ".staging-" in n] == []   # staging cleaned
    assert os.listdir(prod) == []                                     # no final dir


def test_production_refuses_dirty_at_finalize(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    calls = {"n": 0}
    def dirtying(repo):
        calls["n"] += 1
        return {"commit": "aaaaaaa", "dirty": calls["n"] != 1}
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=dirtying)
    _fill_L1(b); b.set_status("success")
    with pytest.raises(RuntimeError, match="became dirty"):
        b.finalize()


def test_allow_dirty_forbidden_under_results_root(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    with pytest.raises(ValueError, match="forbidden under the V2 results root"):
        _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN, allow_dirty=True)


# ---- outcome- and layer-dependent completeness ----
def test_incomplete_success_bundle_is_rejected(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN)
    b.record_memory([{"id": 1}], [], [{"id": 1}])   # missing retrieval_trace + metrics
    b.set_status("success")
    with pytest.raises(RuntimeError, match="Incomplete bundle"):
        b.finalize()
    assert os.listdir(prod) == []


def test_aborted_run_produces_complete_failure_bundle(tmp_path):
    """A timeout with no planner/metrics artifacts still finalizes and stays counted."""
    prod = tmp_path / "prod"; prod.mkdir()
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN, layer="L2")
    b.set_status("timeout", detail={"stage": "planner"})
    out = b.finalize()                                # must NOT raise
    st = json.load(open(os.path.join(out, "status.json")))
    assert st["outcome"] == "timeout" and st["included_in_denominator"] is True


def test_L2_success_requires_planner_files(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN, layer="L2")
    _fill_L1(b)                                       # no planner artifacts
    b.set_status("success")
    with pytest.raises(RuntimeError, match="Incomplete bundle"):
        b.finalize()


# ---- collision-safe ids + secret redaction + checksums ----
def test_run_ids_are_collision_safe(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    a = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN)
    c = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN)
    assert a.run_id != c.run_id                        # unique suffix despite same identity


def test_secret_redacted_and_checksums_valid(tmp_path):
    import hashlib
    prod = tmp_path / "prod"; prod.mkdir()
    b = _bundle(tmp_path, base_dir=prod, results_root=prod, git=CLEAN)
    _fill_L1(b); b.set_status("success")
    out = b.finalize()
    cfg = open(os.path.join(out, "config.yaml")).read()
    assert "topsecret" not in cfg and "<redacted>" in cfg
    # verify every checksum line matches the file on disk
    for line in open(os.path.join(out, "checksums.sha256")):
        digest, name = line.strip().split("  ", 1)
        data = open(os.path.join(out, name), "rb").read()
        assert hashlib.sha256(data).hexdigest() == digest
