"""452A Part 2 L3: poison-blind assignment, genuinely-different allocations, equal query
budget, attacked-subtask schedule, and exposure metrics (Supervisor separated, Scout 0
excluded from cross-Scout). Hermetic — no DB/LLM/embedder.

Run: python3 -m pytest tests/test_l3_452a_part2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.l3 import subtasks as ST  # noqa: E402
from uavsys.l3.assignment import assign, scouts, POLICIES  # noqa: E402
from uavsys.l3.exposure import metrics, COMPROMISED  # noqa: E402

SCOUTS = [2, 4, 8, 16]


# ---- poison-blindness & determinism ----
def test_assign_is_poison_blind_and_deterministic():
    import inspect
    params = list(inspect.signature(assign).parameters)
    assert params == ["policy", "scout_count", "seed"]           # NO poison/attack arg
    for pol in POLICIES:
        a = assign(pol, 4, 101)
        assert a == assign(pol, 4, 101)                          # deterministic == identical A00/A01 map


def test_attacked_schedule_independent_of_policy_and_deterministic():
    for seed in range(101, 111):
        vals = {ST.attacked_subtask(seed)}
        assert ST.attacked_subtask(seed) == ST.attacked_subtask(seed)
        assert len(vals) == 1 and ST.attacked_subtask(seed) in ST.SUBTASK_IDS
    assert ST.attacked_subtask(101) == "S1" and ST.attacked_subtask(102) == "S9"


# ---- genuinely different allocations (not ID relabel) ----
def test_fixed_vs_random_differ_in_which_subtask_each_scout_gets():
    f = assign("fixed", 4, 103)["blocks"]
    r = assign("random", 4, 103)["blocks"]
    assert f != r                                                # different subtask->scout allocation


def test_dynamic_replicates_priority_and_displaces_lowest():
    a = assign("dynamic", 4, 105)
    assert a["replicated"] == ST.PRIORITY_SUBTASK                # S1 replicated
    assert a["displaced"] is not None and a["displaced"] != ST.PRIORITY_SUBTASK
    holders = [s for s, b in a["blocks"].items() if ST.PRIORITY_SUBTASK in b]
    assert len(holders) == 2                                     # S1 now on two scouts
    assert len(a["covered_subtasks"]) == 15                      # one subtask dropped


# ---- equal fleet query budget & coverage ----
@pytest.mark.parametrize("n", SCOUTS)
def test_equal_query_budget_across_policies(n):
    totals = {pol: sum(len(q) for q in assign(pol, n, 107)["queries"].values()) for pol in POLICIES}
    assert set(totals.values()) == {17}                          # 16 subtask queries + 1 overview, all policies


def test_coverage_fixed_random_full_dynamic_drops_one():
    assert len(assign("fixed", 8, 108)["covered_subtasks"]) == 16
    assert len(assign("random", 8, 108)["covered_subtasks"]) == 16
    assert len(assign("dynamic", 8, 108)["covered_subtasks"]) == 15


# ---- fleet sizing ----
@pytest.mark.parametrize("n", SCOUTS)
def test_fleet_sizes(n):
    sc = scouts(n)
    assert len(sc) == n and sc[0] == COMPROMISED                 # Scout 0 = compromised writer


# ---- metrics: Supervisor separated, Scout 0 excluded from cross-Scout ----
def test_metrics_separate_supervisor_and_exclude_compromised():
    a = assign("fixed", 4, 101)                                  # attacked = S1
    attacked = ST.attacked_subtask(101)
    # exposed: the scout holding S1, plus Scout 0(compromised), plus supervisor
    holder = next(s for s, b in a["blocks"].items() if attacked in b)
    exposed = {holder: True, "Scout 0": True, "Supervisor": True}
    m = metrics(a, exposed, attacked)
    assert m["denominators"]["cross_scout"] == 3                 # scout_count-1 = 3 (excl Scout 0)
    assert isinstance(m["supervisor_exposure"], bool)           # supervisor is a separate binary
    assert m["total_fleet_blast_radius_count"] >= 1
    assert m["attacked_subtask"] == "S1"
    # cross_scout_exposure excludes Scout 0 from the numerator base
    assert 0.0 <= m["cross_scout_exposure"] <= 1.0
