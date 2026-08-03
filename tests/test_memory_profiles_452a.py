"""452A memory profiles: record counts, deterministic generation, materialization
hashes, and identical A00/A01 pre-injection memory. Hermetic (no DB/LLM/embedder).

Run: python3 -m pytest tests/test_memory_profiles_452a.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.memory_profiles import (  # noqa: E402
    build_profile, profile_size, materialization_hash, record_embed_text,
    MEM200_COMPOSITION, EPISODIC_HEAVY_COMPOSITION, BENIGN_HIGHSIM_COMPOSITION,
)

NEW = ["MEM200_DENSE", "MEM060_EPISODIC_HEAVY", "MEM060_BENIGN_HIGHSIM"]
SEEDS = list(range(101, 111))


def _by_layer(recs):
    d = {}
    for r in recs:
        d[r.layer] = d.get(r.layer, 0) + 1
    return d


def _by_cat(recs):
    d = {}
    for r in recs:
        key = r.category or r.layer
        d[key] = d.get(key, 0) + 1
    return d


# ---- record counts ----
def test_total_sizes():
    assert profile_size("MEM200_DENSE", 101) == 200 == sum(MEM200_COMPOSITION.values())
    assert profile_size("MEM060_EPISODIC_HEAVY", 101) == 60 == sum(EPISODIC_HEAVY_COMPOSITION.values())
    assert profile_size("MEM060_BENIGN_HIGHSIM", 101) == 60 == sum(BENIGN_HIGHSIM_COMPOSITION.values())


def test_mem200_layer_and_category_counts():
    r = build_profile("MEM200_DENSE", 101)
    assert _by_layer(r) == {"semantic": 58, "procedural": 12, "coordination": 40, "episodic": 90}
    c = _by_cat(r)
    assert c["target"] == 2 and c["environment"] == 6 and c["state"] == 20 and c["dense_similar"] == 60


def test_episodic_heavy_is_episodic_dominated_same_size():
    r = build_profile("MEM060_EPISODIC_HEAVY", 101)
    bl = _by_layer(r)
    assert bl["episodic"] == 50 and sum(bl.values()) == 60          # 83% episodic, size == operational


def test_benign_highsim_block_present():
    r = build_profile("MEM060_BENIGN_HIGHSIM", 101)
    assert _by_cat(r)["benign_highsim"] == 40 and profile_size("MEM060_BENIGN_HIGHSIM", 101) == 60


# ---- deterministic generation ----
@pytest.mark.parametrize("prof", NEW)
def test_same_seed_byte_identical(prof):
    assert build_profile(prof, 101) == build_profile(prof, 101)     # frozen dataclass equality


@pytest.mark.parametrize("prof", NEW)
def test_different_seed_differs(prof):
    assert materialization_hash(prof, 101) != materialization_hash(prof, 102)


# ---- materialization hashes ----
@pytest.mark.parametrize("prof", NEW)
def test_materialization_hash_stable(prof):
    for s in SEEDS:
        assert materialization_hash(prof, s) == materialization_hash(prof, s)


def test_mem003_static_hash_across_seeds():
    assert materialization_hash("MEM003_SPARSE", 101) == materialization_hash("MEM003_SPARSE", 110)


# ---- identical A00/A01 pre-injection memory ----
@pytest.mark.parametrize("prof", NEW + ["MEM003_SPARSE", "MEM060_OPERATIONAL"])
def test_pre_injection_memory_is_benign_and_shared(prof):
    """The clean pre-injection memory is attack-independent: A00 and A01 both seed the
    SAME profile at a given seed, it contains no poison, and it is deterministic."""
    for s in SEEDS:
        a00 = build_profile(prof, s)
        a01 = build_profile(prof, s)
        assert a00 == a01                                           # identical for both arms
        assert all(not str(r.source).startswith("atk:") for r in a00)   # benign only


# ---- embed-text mirror + backward-compat ----
def test_record_embed_text_shapes():
    r = build_profile("MEM200_DENSE", 101)
    sem = next(x for x in r if x.layer == "semantic")
    epi = next(x for x in r if x.layer == "episodic")
    coord = next(x for x in r if x.layer == "coordination")
    proc = next(x for x in r if x.layer == "procedural")
    assert record_embed_text(sem) == f"{sem.key}: {sem.value}"
    assert record_embed_text(epi) == epi.content
    assert record_embed_text(proc) == f"{proc.name}: {proc.description}"
    assert record_embed_text(coord) == f"Message from {coord.agent} to {coord.to_agent}: {coord.content}"


def test_existing_profiles_unchanged():
    assert profile_size("P1") == 3 and profile_size("MEM003_SPARSE") == 3
    assert profile_size("P2") == 60 and profile_size("MEM060_OPERATIONAL") == 60
    assert build_profile("P2", 42) == build_profile("MEM060_OPERATIONAL", 42)


def test_runner_integration_all_five_profiles_resolve_and_build():
    """Every 452A memory id resolves in the taxonomy AND its runner value builds."""
    from uavsys import taxonomy as TX
    expect = {"MEM003_SPARSE": 3, "MEM060_OPERATIONAL": 60, "MEM200_DENSE": 200,
              "MEM060_EPISODIC_HEAVY": 60, "MEM060_BENIGN_HIGHSIM": 60}
    for name, n in expect.items():
        assert TX.resolve("memory", name) == name
        assert TX.status("memory", name) == "implemented"
        rv = TX.runner_value("memory", name)            # what the runner passes to build_profile
        assert len(build_profile(rv, 101)) == n
        # canonical-name and runner-value materializations agree (P3 == MEM200_DENSE, etc.)
        assert materialization_hash(rv, 101) == materialization_hash(name, 101)
