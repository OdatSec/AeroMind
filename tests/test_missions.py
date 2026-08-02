"""Tests for the config-driven mission registry (M1-M3).

No DB / LLM / PX4. Run: python3 -m pytest tests/test_missions.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.missions import MISSIONS, get_mission, list_missions, Mission  # noqa: E402
from uavsys.evidence.outcomes import haversine_m  # noqa: E402
from attacks.base import GROUND_TRUTH_TARGETS  # noqa: E402


def test_registry_has_m1_m2_m3():
    assert list_missions() == ["M1", "M2", "M3"]
    for mid in ("M1", "M2", "M3"):
        assert isinstance(get_mission(mid), Mission)


def test_unknown_mission_raises():
    with pytest.raises(KeyError, match="Unknown mission"):
        get_mission("M9")


def test_m1_objective_matches_runner_mission_goal_backward_compat():
    """M1 must reproduce the runner's current MISSION_GOAL verbatim."""
    import experiments.experiment_runner as R
    assert get_mission("M1").objective == R.MISSION_GOAL


def test_m1_targets_match_ground_truth():
    tg = {t.label: (t.lat, t.lon) for t in get_mission("M1").targets}
    assert tg["person"] == (GROUND_TRUTH_TARGETS["person"]["lat"], GROUND_TRUTH_TARGETS["person"]["lon"])
    assert tg["car"] == (GROUND_TRUTH_TARGETS["car"]["lat"], GROUND_TRUTH_TARGETS["car"]["lon"])


def test_m2_is_multi_target_survey():
    m2 = get_mission("M2")
    assert 4 <= len(m2.targets) <= 6
    assert {"person", "car"}.issubset({t.label for t in m2.targets})
    # survey waypoints must not collide with the trap coords (47.397, 8.55)
    for t in m2.targets:
        assert not (abs(t.lat - 47.397) < 1e-9 and abs(t.lon - 8.55) < 1e-9)


def test_m3_has_genuine_nfz_and_target_is_outside_it():
    m3 = get_mission("M3")
    genuine = [z for z in m3.no_fly_zones if z.genuine]
    assert genuine, "M3 must define at least one genuine no-fly zone"
    # every M3 target must be reachable WITHOUT entering a genuine zone
    for t in m3.targets:
        for z in genuine:
            assert haversine_m(t.lat, t.lon, z.lat, z.lon) > z.radius_m, \
                f"{t.label} lies inside genuine zone {z.label}"


def test_missions_are_subset_of_spec():
    import yaml
    spec = yaml.safe_load(open(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "configs", "EXPERIMENT_SPEC_V2.yaml")))
    assert set(MISSIONS).issubset(set(spec["missions"]))     # M1-M3 declared in spec (which also lists M4)


def test_mission_to_dict_serializable():
    import json
    json.dumps(get_mission("M3").to_dict())     # must not raise
