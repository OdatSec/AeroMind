"""
Regression tests for memory-record identity: (layer, id), never a bare id.

Row ids are per-table AUTOINCREMENT, so ids collide across layers (semantic id=1
and episodic id=1 are different records). The C1 smoke bundle exposed this: a
bare-id delta reported 1 injected record when 3 were actually injected, because
episodic ids 1,2 collided with pre-existing semantic ids 1,2.

No DB / LLM / PX4. Run: python3 -m pytest tests/test_record_identity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.experiment_runner import (  # noqa: E402
    record_key, flatten_snapshot, injected_delta,
)

# Exactly the shape observed in the C1 smoke run.
BEFORE_SNAP = {
    "semantic": [{"id": 1, "layer": "semantic", "source": "Intel"},
                 {"id": 2, "layer": "semantic", "source": "Intel"}],
    "procedural": [{"id": 1, "layer": "procedural", "source": "Doctrine"}],
    "episodic": [],
    "coordination": [],
}
AFTER_SNAP = {
    "semantic": [{"id": 1, "layer": "semantic", "source": "Intel"},
                 {"id": 2, "layer": "semantic", "source": "Intel"}],
    "procedural": [{"id": 1, "layer": "procedural", "source": "Doctrine"}],
    # Injected S01 payload: episodic ids 1,2,3 — 1 and 2 COLLIDE with semantic ids.
    "episodic": [{"id": 1, "layer": "episodic", "source": "atk:S01"},
                 {"id": 2, "layer": "episodic", "source": "atk:S01"},
                 {"id": 3, "layer": "episodic", "source": "atk:S01"}],
    "coordination": [],
}


def test_record_key_is_layer_and_id():
    assert record_key({"layer": "episodic", "id": 1}) == ("episodic", 1)
    # Same id, different layers => different records.
    assert record_key({"layer": "episodic", "id": 1}) != record_key({"layer": "semantic", "id": 1})


def test_flatten_snapshot_stamps_layer_from_key():
    flat = flatten_snapshot({"episodic": [{"id": 7}]})   # record missing 'layer'
    assert flat[0]["layer"] == "episodic"
    assert record_key(flat[0]) == ("episodic", 7)


def test_injected_delta_captures_all_three_with_colliding_ids():
    """The C1 regression: all three injected S01 records must be captured even
    though episodic ids 1,2 collide with pre-existing semantic ids 1,2."""
    before = flatten_snapshot(BEFORE_SNAP)
    after = flatten_snapshot(AFTER_SNAP)
    injected = injected_delta(before, after)

    assert len(injected) == 3, injected
    assert {record_key(r) for r in injected} == {("episodic", 1), ("episodic", 2), ("episodic", 3)}
    assert all(r["source"] == "atk:S01" for r in injected)
    # The delta must equal the attack-tagged set for this scenario.
    assert {record_key(r) for r in injected} == {
        record_key(r) for r in after if str(r.get("source", "")).startswith("atk:")}


def test_bare_id_delta_would_undercount_proving_the_bug():
    """Documents the defect the fix removes: a bare-id delta finds only 1 of 3."""
    before = flatten_snapshot(BEFORE_SNAP)
    after = flatten_snapshot(AFTER_SNAP)
    bare_ids = {r.get("id") for r in before}
    bare_delta = [r for r in after if r.get("id") not in bare_ids]
    assert len(bare_delta) == 1                     # the historical wrong answer
    assert len(injected_delta(before, after)) == 3  # the fixed answer


def test_no_injection_yields_empty_delta():
    flat = flatten_snapshot(BEFORE_SNAP)
    assert injected_delta(flat, flat) == []
