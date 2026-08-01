"""
Hermetic runner-level integration test for the opt-in L1 evidence path.

Mocks init_experiment and the memory object (no live embeddings / DB / LLM), so
we test the WIRING: that run_retrieval_mode captures memory_before at its true
timepoint (post-seed / pre-inject), writes a complete L1 bundle, and finalizes.

Run: python3 -m pytest tests/test_runner_evidence_integration.py
"""
import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.experiment_runner as R  # noqa: E402
from uavsys.memory.memory_interface import RetrievalInfrastructureError  # noqa: E402


class FakeMemory:
    """Records call order; snapshot() returns benign-only before injection and
    benign+attack after, so the before/after timepoints are distinguishable."""
    def __init__(self):
        self.events = []
        self._injected = False

    # seeding writes (called by real seed_memory)
    async def write_semantic(self, **k): self.events.append("seed_write")
    async def write_procedural(self, **k): self.events.append("seed_write")
    async def write_coordination(self, *a, **k): self.events.append("seed_write")

    # attack injection writes (called by the real s01 module)
    async def write_episodic(self, **k):
        self.events.append("inject_write")
        self._injected = True

    async def retrieve(self, **k):
        self.events.append("retrieve")
        return {"matches": [{"source": "atk:S01", "layer": "episodic", "score": 0.9,
                             "text": "trap", "is_attack": True}]}

    async def snapshot(self):
        self.events.append("snapshot")
        benign = [{"id": 1, "source": "Intel", "layer": "semantic"}]
        if self._injected:
            return {"semantic": benign, "episodic": [{"id": 9, "source": "atk:S01"}]}
        return {"semantic": benign, "episodic": []}


def _fake_cfg():
    return SimpleNamespace(EMBED_MODEL="nomic-embed-text:latest", CHAT_MODEL="gpt-oss:20b",
                           DEFENSE_PROVENANCE_SECRET="topsecret")


def test_runner_l1_evidence_bundle_and_true_timepoints(monkeypatch, tmp_path):
    mem = FakeMemory()

    async def fake_init(seed, defense_enabled, db_path, chat_model=None, defense_overrides=None):
        return _fake_cfg(), object(), object(), mem

    monkeypatch.setattr(R, "init_experiment", fake_init)

    out_dir = tmp_path / "out"
    ev_dir = tmp_path / "evidence"      # OUTSIDE results_v2_frozen -> dev bundle (dirty OK)

    asyncio.run(R.run_retrieval_mode(
        "S01", [42], defense_enabled=False, output_dir=str(out_dir),
        emit_evidence=True, evidence_dir=str(ev_dir)))

    # A bundle folder was produced.
    bundles = [d for d in os.listdir(ev_dir) if os.path.isdir(os.path.join(ev_dir, d))]
    assert len(bundles) == 1, bundles
    bdir = os.path.join(ev_dir, bundles[0])

    # All L1 success files present.
    for f in ("manifest.json", "config.yaml", "environment.json", "status.json",
              "checksums.sha256", "memory_before.jsonl", "injected_records.jsonl",
              "memory_after.jsonl", "retrieval_trace.jsonl", "metrics.json"):
        assert os.path.exists(os.path.join(bdir, f)), f

    # True timepoints: the FIRST snapshot (memory_before) happened AFTER seeding
    # and BEFORE any injection write.
    first_snap = mem.events.index("snapshot")
    first_inject = mem.events.index("inject_write")
    assert "seed_write" in mem.events[:first_snap]
    assert first_snap < first_inject, mem.events

    # memory_before has NO attack record; injected is the real delta; after has it.
    before = [json.loads(l) for l in open(os.path.join(bdir, "memory_before.jsonl")) if l.strip()]
    injected = [json.loads(l) for l in open(os.path.join(bdir, "injected_records.jsonl")) if l.strip()]
    after = [json.loads(l) for l in open(os.path.join(bdir, "memory_after.jsonl")) if l.strip()]
    assert all(not str(r.get("source", "")).startswith("atk:") for r in before)
    assert any(str(r.get("source", "")).startswith("atk:") for r in injected)
    assert {r["id"] for r in before}.issubset({r["id"] for r in after})

    m = json.load(open(os.path.join(bdir, "manifest.json")))
    assert m["scenario"] == "C1" and m["legacy_id"] == "S01" and m["layer"] == "L1"
    assert m["validity"] == "development-only"      # ev_dir is outside the results root


def test_runner_failure_produces_failure_bundle(monkeypatch, tmp_path):
    """If retrieval raises after bundle creation, a failure bundle is finalized
    (kept in the denominator) rather than leaving an orphan staging dir."""
    mem = FakeMemory()

    async def boom(**k):
        raise RuntimeError("retrieval exploded")
    mem.retrieve = boom  # type: ignore

    async def fake_init(seed, defense_enabled, db_path, chat_model=None, defense_overrides=None):
        return _fake_cfg(), object(), object(), mem

    monkeypatch.setattr(R, "init_experiment", fake_init)
    ev_dir = tmp_path / "evidence"

    import pytest
    with pytest.raises(RuntimeError, match="retrieval exploded"):
        asyncio.run(R.run_retrieval_mode(
            "S01", [42], defense_enabled=False, output_dir=str(tmp_path / "out"),
            emit_evidence=True, evidence_dir=str(ev_dir)))

    bundles = [d for d in os.listdir(ev_dir) if os.path.isdir(os.path.join(ev_dir, d))]
    assert len(bundles) == 1
    bdir = os.path.join(ev_dir, bundles[0])
    assert not any(".staging-" in d for d in os.listdir(ev_dir))   # no orphan staging
    st = json.load(open(os.path.join(bdir, "status.json")))
    assert st["outcome"] == "infrastructure_failure"
    assert st["included_in_denominator"] is True


def test_embedding_failure_classified_infra_with_error_recorded(monkeypatch, tmp_path):
    """A RetrievalInfrastructureError (embedding down) must produce an
    infrastructure_failure bundle that records the error — never a silent
    success with empty matches."""
    mem = FakeMemory()

    async def embed_down(**k):
        raise RetrievalInfrastructureError("Retrieval embedding failed for 'Agent 1': ollama down")
    mem.retrieve = embed_down  # type: ignore

    async def fake_init(seed, defense_enabled, db_path, chat_model=None, defense_overrides=None):
        return _fake_cfg(), object(), object(), mem
    monkeypatch.setattr(R, "init_experiment", fake_init)
    ev_dir = tmp_path / "evidence"

    import pytest
    with pytest.raises(RetrievalInfrastructureError):
        asyncio.run(R.run_retrieval_mode(
            "S01", [42], defense_enabled=False, output_dir=str(tmp_path / "out"),
            emit_evidence=True, evidence_dir=str(ev_dir)))

    bdir = os.path.join(ev_dir, [d for d in os.listdir(ev_dir)
                                 if os.path.isdir(os.path.join(ev_dir, d))][0])
    st = json.load(open(os.path.join(bdir, "status.json")))
    assert st["outcome"] == "infrastructure_failure"
    assert st["included_in_denominator"] is True
    assert "embedding failed" in json.dumps(st["detail"]).lower()
    assert not any(".staging-" in d for d in os.listdir(ev_dir))


def test_legitimate_zero_match_is_success(monkeypatch, tmp_path):
    """Embedding OK but retrieval returns no items = a legitimate zero-match
    result -> success bundle (distinguished from an infrastructure failure)."""
    mem = FakeMemory()

    async def zero_match(**k):
        mem.events.append("retrieve")
        return {"matches": []}          # no error, just nothing retrieved
    mem.retrieve = zero_match  # type: ignore

    async def fake_init(seed, defense_enabled, db_path, chat_model=None, defense_overrides=None):
        return _fake_cfg(), object(), object(), mem
    monkeypatch.setattr(R, "init_experiment", fake_init)
    ev_dir = tmp_path / "evidence"

    asyncio.run(R.run_retrieval_mode(
        "S01", [42], defense_enabled=False, output_dir=str(tmp_path / "out"),
        emit_evidence=True, evidence_dir=str(ev_dir)))

    bdir = os.path.join(ev_dir, [d for d in os.listdir(ev_dir)
                                 if os.path.isdir(os.path.join(ev_dir, d))][0])
    st = json.load(open(os.path.join(bdir, "status.json")))
    assert st["outcome"] == "success"
    assert os.path.exists(os.path.join(bdir, "retrieval_trace.jsonl"))
    assert os.path.exists(os.path.join(bdir, "metrics.json"))
