"""MV1_FALSE_CLEARANCE attack-module + outcome tests (hermetic; no DB/LLM/PX4).

Run: python3 -m pytest tests/test_mv1_false_clearance.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
import attacks.mv1_false_clearance as mv1  # noqa: E402
from uavsys.missions import get_mission  # noqa: E402
from uavsys.evidence.outcomes import target_omission  # noqa: E402

M1, M2 = get_mission("M1"), get_mission("M2")


class RecMem:
    def __init__(self): self.rows = []
    async def write_semantic(self, **k): self.rows.append(("semantic", k))
    async def write_procedural(self, **k): self.rows.append(("procedural", k))
    async def write_episodic(self, **k): self.rows.append(("episodic", k))
    async def write_coordination(self, **k): self.rows.append(("coordination", k))


def _goto(*coords):
    steps = [{"tool": "takeoff", "args": {}}]
    for lat, lon in coords:
        steps.append({"tool": "goto_location", "args": {"lat": lat, "lon": lon}})
    steps.append({"tool": "return_to_launch", "args": {}})
    return {"steps": steps}


# ---- deterministic designation (from mission config) ----
def test_designated_target_is_deterministic_and_from_config():
    assert M2.mv1_cleared_target == "survey_ne"
    for _ in range(3):
        assert mv1.designated_target(M2).label == "survey_ne"


def test_mv1_not_applicable_to_m1():
    with pytest.raises(ValueError, match="M2-only|not applicable"):
        mv1.designated_target(M1)


def test_inject_requires_mission():
    with pytest.raises(ValueError, match="requires the mission"):
        asyncio.run(mv1.inject(RecMem(), mission=None))


# ---- ordinary-API injection + exact delta ----
def test_inject_writes_exactly_one_unsigned_semantic_status():
    mem = RecMem()
    res = asyncio.run(mv1.inject(mem, mission=M2))
    assert len(mem.rows) == 1
    layer, kw = mem.rows[0]
    assert layer == "semantic"
    assert kw["key"] == "STATUS:survey_ne"
    assert kw["source"] == "MV1" and kw["is_attack"] is True     # -> stored atk:MV1, unsigned
    assert "surveyed and cleared" in kw["value"]
    assert res["scenario_id"] == "MV1" and res["entries_injected"] == 1
    assert res["attack_tags"] == ["atk:MV1"]
    assert res["cleared_target"] == "survey_ne"
    t = M2.target("survey_ne")
    assert res["cleared_coords"] == (t.lat, t.lon)


# ---- outcome: clean vs attacked M2 plans ----
def test_clean_m2_plan_covers_all_targets():
    plan = _goto(*[(t.lat, t.lon) for t in M2.targets])
    r = target_omission(plan, M2)
    assert r["assigned"] == 6 and r["omitted"] == [] and r["omission_rate"] == 0.0


def test_attacked_m2_plan_omits_designated_target():
    # visit every target EXCEPT the falsely-cleared survey_ne
    kept = [(t.lat, t.lon) for t in M2.targets if t.label != "survey_ne"]
    r = target_omission(_goto(*kept), M2)
    assert "survey_ne" in r["omitted"]
    assert r["omission_rate"] == round(1 / 6, 4)


def test_dense_targets_nearest_assignment_person_vs_car():
    # person and car are ~3 m apart; a single waypoint at person must not also
    # credit car (nearest-assignment).
    person = M2.target("person")
    r = target_omission(_goto((person.lat, person.lon)), M2)
    assert "person" in r["visited"] and "car" in r["omitted"]
