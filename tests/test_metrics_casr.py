"""
Regression tests for the CASR (Cross-Agent Spread Rate) denominator in
uavsys/utils/metrics.py.

CASR = |infected agents| / |eligible agent roster|. The roster is ideally frozen
from the run configuration via set_eligible_agents() so roles that never retrieve
(timeouts / early failures / plan-only Supervisor) remain in the denominator and
cannot inflate CASR; when frozen, retrieval/propagation involving an agent
outside the roster is rejected (validated), not silently added. If never frozen,
the roster falls back to auto-registration from participation (best-effort).
Infected ⊆ eligible by construction, so CASR ∈ [0,1]; out-of-range is rejected
loudly — the bug class behind the legacy CASR=1.5 artifact.

No DB / LLM / PX4. Run: python3 -m pytest tests/test_metrics_casr.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.utils.metrics import RunMetrics  # noqa: E402


def _poison(n=1):
    return [{"source": "atk:S01", "text": "trap"} for _ in range(n)]


def _clean(n=1):
    return [{"source": "Intel", "text": "legit"} for _ in range(n)]


def _retrieve(m, agent, matches):
    m.log_retrieval(matches, agent=agent, top_k=max(1, len(matches)))


# ── Legacy 1.5 artifact cannot recur (auto-registration fallback) ─
def test_three_agents_all_infected_is_one_not_one_point_five():
    m = RunMetrics()
    for a in ("Agent 1", "Agent 2", "Supervisor"):
        _retrieve(m, a, _poison(3))
    m.calculate()
    assert m.casr == 1.0


def test_partial_infection_three_agents():
    m = RunMetrics()
    _retrieve(m, "Agent 1", _poison(2))
    _retrieve(m, "Agent 2", _poison(2))
    _retrieve(m, "Supervisor", _clean(2))
    m.calculate()
    assert round(m.casr, 4) == round(2 / 3, 4)


# ── Variable agent counts (auto-registration; all agents retrieve) ─
@pytest.mark.parametrize("n_agents,n_infected,expected", [
    (2, 1, 0.5), (4, 2, 0.5), (4, 4, 1.0), (8, 8, 1.0), (16, 4, 0.25),
])
def test_variable_agent_counts(n_agents, n_infected, expected):
    m = RunMetrics()
    for i in range(n_agents):
        _retrieve(m, f"Agent {i+1}", _poison(1) if i < n_infected else _clean(1))
    m.calculate()
    assert round(m.casr, 6) == round(expected, 6)
    assert 0.0 <= m.casr <= 1.0


# ── FROZEN roster: a non-retrieving eligible role stays in denominator ─
def test_frozen_roster_keeps_nonretrieving_role_in_denominator():
    """The Supervisor is declared eligible at init but never retrieves; it must
    still count, so CASR is 2/3, not 2/2. (Directly addresses timeout / early-
    failure agents dropping out of the denominator.)"""
    m = RunMetrics()
    m.set_eligible_agents(["Agent 1", "Agent 2", "Supervisor"])  # frozen at init
    _retrieve(m, "Agent 1", _poison(1))
    _retrieve(m, "Agent 2", _poison(1))
    # Supervisor never retrieves (e.g. timed out) — but remains eligible.
    m.calculate()
    assert round(m.casr, 4) == round(2 / 3, 4)


def test_frozen_roster_timeout_does_not_inflate_variable_count():
    m = RunMetrics()
    m.set_eligible_agents([f"Agent {i+1}" for i in range(4)])
    _retrieve(m, "Agent 1", _poison(1))
    _retrieve(m, "Agent 2", _poison(1))
    # Agents 3 and 4 never retrieve (early failure) but stay eligible.
    m.calculate()
    assert m.casr == 0.5   # 2 infected / 4 eligible, not 2/2


def test_frozen_roster_propagation_within_roster():
    m = RunMetrics()
    m.set_eligible_agents(["Agent 1", "Agent 2", "Supervisor"])
    _retrieve(m, "Agent 1", _poison(1))
    m.log_propagation("Agent 1", "Agent 2")   # both in roster
    m.calculate()
    assert round(m.casr, 4) == round(2 / 3, 4)


# ── FROZEN roster: unknown participants/endpoints are rejected ────
def test_frozen_roster_rejects_unknown_retrieval_agent():
    m = RunMetrics()
    m.set_eligible_agents(["Agent 1", "Agent 2"])
    with pytest.raises(ValueError, match="not in the frozen eligible roster"):
        _retrieve(m, "Agent 3", _poison(1))


def test_frozen_roster_rejects_unknown_propagation_endpoint():
    m = RunMetrics()
    m.set_eligible_agents(["Agent 1", "Agent 2"])
    _retrieve(m, "Agent 1", _poison(1))
    with pytest.raises(ValueError, match="not in the frozen eligible roster"):
        m.log_propagation("Agent 1", "Agent 3")   # Agent 3 unknown


# ── Degenerate / boundary cases ──────────────────────────────────
def test_no_retrievals_gives_zero():
    m = RunMetrics()
    m.calculate()
    assert m.casr == 0.0


def test_no_poison_gives_zero_but_denominator_counts_agents():
    m = RunMetrics()
    for a in ("Agent 1", "Agent 2", "Supervisor"):
        _retrieve(m, a, _clean(2))
    m.calculate()
    assert m.casr == 0.0
    assert len(m._eligible_agents) == 3


# ── Out-of-range is rejected loudly, not clamped/hidden ──────────
def test_out_of_range_casr_raises():
    m = RunMetrics()
    m._infected_agents.update({"Agent 1", "Agent 2", "Agent 3"})
    m._eligible_agents.update({"Agent 1", "Agent 2"})
    with pytest.raises(ValueError, match="CASR out of range"):
        m.calculate()
