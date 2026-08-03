"""V3 taxonomy: alias equivalence + canonical resolution (hermetic).

Run: python3 -m pytest tests/test_taxonomy.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys import taxonomy as TX  # noqa: E402


@pytest.mark.parametrize("aliases,canon,runner", [
    (["A00_CLEAN", "C0", "B0"], "A00_CLEAN", "B0"),
    (["A01_FALSE_OBSERVATION", "C1", "S01"], "A01_FALSE_OBSERVATION", "S01"),
    (["A02_SHARED_MEMORY_EXPOSURE", "C2", "S06"], "A02_SHARED_MEMORY_EXPOSURE", "S06"),
    (["A03_FALSE_RESTRICTION", "C3", "S12"], "A03_FALSE_RESTRICTION", "S12"),
    (["A04_SIGNED_CONFLICT", "C4", "S16"], "A04_SIGNED_CONFLICT", "S16"),
    (["A05_SIGNED_FALSE_OBSERVATION", "C5", "S17"], "A05_SIGNED_FALSE_OBSERVATION", "S17"),
    (["A06_PERCEPTION_FALSE_STATE", "C6", "S18"], "A06_PERCEPTION_FALSE_STATE", "S18"),
    (["A07_FALSE_COMPLETION", "MV1_FALSE_CLEARANCE"], "A07_FALSE_COMPLETION", "MV1_FALSE_CLEARANCE"),
    (["A08_FALSE_SAFETY", "MV2_FALSE_SAFETY"], "A08_FALSE_SAFETY", "MV2_FALSE_SAFETY"),
])
def test_attack_alias_equivalence(aliases, canon, runner):
    for a in aliases:
        assert TX.resolve("attack", a) == canon
        assert TX.runner_value("attack", a) == runner


def test_a02_is_exposure_not_propagation():
    assert "EXPOSURE" in "A02_SHARED_MEMORY_EXPOSURE"
    assert "A02_SHARED_MEMORY_PROPAGATION" not in TX.ATTACKS


@pytest.mark.parametrize("aliases,canon,runner", [
    (["T01_SEARCH_RESCUE", "M1"], "T01_SEARCH_RESCUE", "M1"),
    (["T02_MULTI_TARGET", "M2"], "T02_MULTI_TARGET", "M2"),
    (["T03_RESTRICTED_ZONE", "M3"], "T03_RESTRICTED_ZONE", "M3"),
    (["T04_RETASKING", "M4"], "T04_RETASKING", "M4"),
])
def test_task_alias_equivalence(aliases, canon, runner):
    for a in aliases:
        assert TX.resolve("task", a) == canon and TX.runner_value("task", a) == runner


@pytest.mark.parametrize("aliases,canon,runner", [
    (["MEM003_SPARSE", "P1"], "MEM003_SPARSE", "P1"),
    (["MEM060_OPERATIONAL", "P2"], "MEM060_OPERATIONAL", "P2"),
])
def test_memory_alias_equivalence(aliases, canon, runner):
    for a in aliases:
        assert TX.resolve("memory", a) == canon and TX.runner_value("memory", a) == runner


def test_memory_semantic_suffix_resolves_to_base():
    assert TX.resolve("memory", "MEM060_OPERATIONAL_STALE") == "MEM060_OPERATIONAL"
    assert TX.resolve("memory", "MEM200_DENSE_CONFLICTING") == "MEM200_DENSE"


@pytest.mark.parametrize("aliases,canon,runner", [
    (["RET", "retrieval"], "RET", "retrieval"),
    (["PLAN", "planning"], "PLAN", "planning"),
    (["SITL", "full-pipeline"], "SITL", "full-pipeline"),
])
def test_evaluation_alias_equivalence(aliases, canon, runner):
    for a in aliases:
        assert TX.resolve("evaluation", a) == canon and TX.runner_value("evaluation", a) == runner


def test_multi_and_deferred_have_no_runner():
    assert TX.runner_value("evaluation", "MULTI") is None
    assert TX.runner_value("attack", "A09_TARGET_RELOCATION") == "MV3_TARGET_RELOCATION"
    assert TX.status("attack", "A09_TARGET_RELOCATION") == "deferred"
    assert TX.status("evaluation", "MULTI") == "planned"


def test_unknown_id_raises():
    with pytest.raises(KeyError):
        TX.resolve("attack", "A99_NOPE")
    with pytest.raises(KeyError):
        TX.resolve("task", "T99")


def test_task_locks_required_task():
    assert TX.required_task("A08_FALSE_SAFETY") == "T03_RESTRICTED_ZONE"
    assert TX.required_task("A07_FALSE_COMPLETION") == "T02_MULTI_TARGET"
    assert TX.required_task("A09_TARGET_RELOCATION") == "T04_RETASKING"
    assert TX.required_task("A01_FALSE_OBSERVATION") is None   # broad, no lock


def test_validate_attack_task_lock():
    TX.validate_attack_task("A08_FALSE_SAFETY", "T03_RESTRICTED_ZONE")   # ok, no raise
    TX.validate_attack_task("A08_FALSE_SAFETY", "M3")                    # alias ok
    TX.validate_attack_task("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE")  # broad ok
    with pytest.raises(ValueError, match="locked to T03"):
        TX.validate_attack_task("A08_FALSE_SAFETY", "T02_MULTI_TARGET")   # the flagged bad combo
    with pytest.raises(ValueError, match="locked to T02"):
        TX.validate_attack_task("A07_FALSE_COMPLETION", "T03_RESTRICTED_ZONE")


def test_manifest_identity_block():
    ids = TX.canonical_manifest_ids("C1", "M2", "P2", "PLAN", "D0")
    assert ids["attack"] == "A01_FALSE_OBSERVATION"
    assert ids["task"] == "T02_MULTI_TARGET"
    assert ids["memory"] == "MEM060_OPERATIONAL"
    assert ids["evaluation"] == "PLAN"
    assert ids["defense"] == "D0"
    assert ids["legacy_aliases"]["attack"] == ["C1", "S01"]
    with pytest.raises(KeyError):
        TX.canonical_manifest_ids("C1", "M2", "P2", "PLAN", "D9")   # bad defense
