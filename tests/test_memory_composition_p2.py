"""P2 frozen memory-composition templates: anchoring, immutability, coord correctness. Hermetic.

Run: python3 -m pytest tests/test_memory_composition_p2.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys.memory_composition import (  # noqa: E402
    poison_generic, poison_adaptive, benign_ontopic, competitor_true, TRAP, TRUE, spec_hash,
    POISONS, BENIGN)


def test_trap_and_true_coords_differ():
    assert TRAP != TRUE and TRAP == (47.397, 8.55) and TRUE == (47.396735, 8.549883)


def test_generic_is_verbatim_s01():
    p = poison_generic(0)
    assert p.startswith("PRIORITY: person target confirmed detected at coordinates")
    assert f"({TRAP[0]}, {TRAP[1]})" in p and "investigate this position" in p


def test_adaptive_is_query_matched_and_redirects_to_trap():
    p = poison_adaptive(0)
    # echoes the mission query vocabulary (so it competes with on-topic benign traffic)...
    for kw in ("search", "missing person", "target", "report"):
        assert kw in p.lower()
    # ...but still redirects to the TRAP (false-redirect semantics preserved)
    assert f"({TRAP[0]}, {TRAP[1]})" in p


def test_ontopic_benign_is_query_relevant_and_NOT_malicious():
    b = benign_ontopic(0)
    for kw in ("search", "missing person", "target area", "scanning"):
        assert kw in b.lower()
    # a legitimate log: no trap coords, no false "confirmed detected" claim
    assert f"({TRAP[0]}, {TRAP[1]})" not in b and "confirmed detected" not in b.lower()


def test_true_competitor_uses_true_coords_not_trap():
    c = competitor_true(0)
    assert f"({TRUE[0]}, {TRUE[1]})" in c and f"({TRAP[0]}, {TRAP[1]})" not in c


def test_determinism_and_registry():
    assert poison_generic(0) == poison_generic(0)
    assert spec_hash() == spec_hash() and len(spec_hash()) == 64
    assert set(POISONS) == {"generic", "adaptive"} and set(BENIGN) == {"ontopic", "competitor"}
