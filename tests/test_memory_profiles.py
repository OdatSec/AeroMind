"""Tests for the deterministic memory-profile builder (P1, P2).

No DB / LLM / PX4. Run: python3 -m pytest tests/test_memory_profiles.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.memory_profiles import build_profile, profile_size, P2_COMPOSITION  # noqa: E402
from attacks.base import GROUND_TRUTH_TARGETS  # noqa: E402


def test_p1_is_sparse_three_records_with_targets():
    p1 = build_profile("P1")
    assert len(p1) == 3
    sem = {r.key: r for r in p1 if r.layer == "semantic"}
    assert "Target:person" in sem and "Target:car" in sem
    assert str(GROUND_TRUTH_TARGETS["person"]["lat"]) in sem["Target:person"].value
    assert any(r.layer == "procedural" for r in p1)
    assert all(not str(r.source).startswith("atk:") for r in p1)   # benign only


def test_p2_size_matches_declared_composition():
    assert profile_size("P2") == sum(P2_COMPOSITION.values()) == 60
    p2 = build_profile("P2")
    by_layer = {}
    for r in p2:
        by_layer[r.layer] = by_layer.get(r.layer, 0) + 1
    # semantic = targets(2) + facts(2) + state(8) = 12
    assert by_layer["semantic"] == 12
    assert by_layer["procedural"] == P2_COMPOSITION["procedural"]
    assert by_layer["coordination"] == P2_COMPOSITION["coordination"]
    assert by_layer["episodic"] == P2_COMPOSITION["episodic_history"]


def test_p2_contains_the_real_targets():
    p2 = build_profile("P2")
    keys = {r.key for r in p2 if r.layer == "semantic"}
    assert "Target:person" in keys and "Target:car" in keys


def test_determinism_same_seed_identical():
    a = build_profile("P2", seed=42)
    b = build_profile("P2", seed=42)
    assert a == b                       # frozen dataclasses -> value equality


def test_different_seed_changes_content_not_size():
    a = build_profile("P2", seed=42)
    c = build_profile("P2", seed=7)
    assert len(a) == len(c) == 60
    assert a != c                       # generated chatter/history differs


def test_p2_is_benign_only():
    assert all(not str(r.source).startswith("atk:") for r in build_profile("P2"))


def test_unknown_profile_raises():
    with pytest.raises(KeyError, match="Unknown profile"):
        build_profile("P9")
