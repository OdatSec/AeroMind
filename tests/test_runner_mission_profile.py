"""Runner wiring tests for --mission / --profile (hermetic; no DB/LLM/PX4).

Verifies that mission/profile thread through planning mode into the bundle
manifest, run_data/aggregate, and the schema-v2 config hash, that P1 uses the
legacy 3-record seeding while P2 uses the 60-record builder, and that M1/P1 is the
default. Does NOT run a real experiment.

Run: python3 -m pytest tests/test_runner_mission_profile.py
"""
import asyncio
import json
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import experiments.experiment_runner as R  # noqa: E402

RAW = ('{"steps": [{"tool": "takeoff"}, {"tool": "goto_location", '
       '"args": {"lat": 47.397, "lon": 8.55}}, {"tool": "return_to_launch"}]}')


class FakeMemory:
    def __init__(self):
        self.events = []            # ordered write/snapshot events
        self._injected = False

    async def write_semantic(self, **k): self.events.append("seed")
    async def write_procedural(self, **k): self.events.append("seed")
    async def write_coordination(self, *a, **k): self.events.append("seed")

    async def write_episodic(self, **k):
        # seeding (P2) and attack injection both call this; the pre-inject snapshot
        # marker lets tests count only the seed writes.
        self.events.append("inject" if self._injected else "seed")

    async def retrieve(self, **k):
        return {"matches": [{"source": "atk:S01", "layer": "episodic", "score": 0.9,
                             "text": "trap", "is_attack": True,
                             "_relevance": 0.7, "_recency": 1.0, "_importance": 0.9}]}

    async def snapshot(self):
        self.events.append("snapshot")
        self._injected = True       # after the before-snapshot, injection begins
        base = {"semantic": [{"id": 1, "layer": "semantic", "source": "Intel"}], "episodic": []}
        return base


class FakeLLM:
    async def chat(self, messages, temperature=0.0, **kw):
        return RAW


def _cfg():
    return SimpleNamespace(EMBED_MODEL="nomic-embed-text:latest", CHAT_MODEL="gpt-oss:20b",
                           DEFENSE_PROVENANCE_SECRET="topsecret", TOP_K_SCOUT=3,
                           DRONE1_GRPC_PORT=50051, DRONE1_SYSTEM_ADDRESS="udpin://0.0.0.0:14540",
                           SEED=42)


def _run(monkeypatch, tmp_path, *, mission="M1", profile="P1"):
    mem = FakeMemory()

    async def fake_init(seed, defense_enabled, db_path, chat_model=None, defense_overrides=None):
        return _cfg(), object(), FakeLLM(), mem
    monkeypatch.setattr(R, "init_experiment", fake_init)

    ev = tmp_path / "ev"
    out = tmp_path / "out"
    asyncio.run(R.run_planning_mode("S01", [42], defense_enabled=False, output_dir=str(out),
                                    emit_evidence=True, evidence_dir=str(ev),
                                    mission_id=mission, profile=profile))
    d = [x for x in os.listdir(ev) if os.path.isdir(os.path.join(ev, x))][0]
    return os.path.join(ev, d), mem, out


def _seed_count(mem):
    # writes before the first snapshot (the pre-inject memory_before capture)
    return mem.events[:mem.events.index("snapshot")].count("seed")


def test_default_m1_p1_recorded_in_manifest_and_v2_hash(monkeypatch, tmp_path):
    bdir, mem, _ = _run(monkeypatch, tmp_path)                 # defaults
    m = json.load(open(os.path.join(bdir, "manifest.json")))
    assert m["mission"] == "M1" and m["profile"] == "P1"
    assert m["configured"]["mission"] == "M1" and m["configured"]["memory_profile"] == "P1"
    assert m["config_hash_schema"]["version"] == "2"
    assert set(m["config_hash_schema"]["run_axes"]) == {"mission", "profile"}


def test_p1_uses_legacy_three_record_seeding(monkeypatch, tmp_path):
    _, mem, _ = _run(monkeypatch, tmp_path, profile="P1")
    assert _seed_count(mem) == 3                                # seed_memory: 2 semantic + 1 procedural


def test_p2_uses_sixty_record_builder(monkeypatch, tmp_path):
    _, mem, _ = _run(monkeypatch, tmp_path, profile="P2")
    assert _seed_count(mem) == 60                               # build_profile("P2")


def test_mission_profile_in_aggregate_json(monkeypatch, tmp_path):
    _, _, out = _run(monkeypatch, tmp_path, mission="M1", profile="P2")
    agg = json.load(open(os.path.join(out, "results.json")))   # dir output -> results.json
    assert agg["mission"] == "M1" and agg["profile"] == "P2"


def test_different_mission_changes_config_hash(monkeypatch, tmp_path):
    b1, _, _ = _run(monkeypatch, tmp_path / "a", mission="M1", profile="P1")
    b2, _, _ = _run(monkeypatch, tmp_path / "b", mission="M2", profile="P1")
    h1 = json.load(open(os.path.join(b1, "manifest.json")))["config_hash"]
    h2 = json.load(open(os.path.join(b2, "manifest.json")))["config_hash"]
    assert h1 != h2                                             # mission folded into the fingerprint
