"""P2b frozen hardening templates: stronger competitor is benign; adaptives redirect to trap. Hermetic."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from uavsys.memory_composition_p2b import stronger_competitor, ADAPTIVES, TRAP, spec_hash


def test_stronger_competitor_is_benign_query_aligned():
    c = stronger_competitor(0)
    # query-aligned vocabulary
    for kw in ("search", "missing person", "target", "scanning", "report"):
        assert kw in c.lower()
    # benign: NO trap coords, NO false "confirmed/located at coordinates"
    assert f"({TRAP[0]}, {TRAP[1]})" not in c and "confirmed" not in c.lower()


def test_three_adaptives_redirect_to_trap_and_are_distinct():
    texts = [fn(0) for fn in ADAPTIVES.values()]
    assert len(ADAPTIVES) == 3
    for t in texts:
        assert f"({TRAP[0]}, {TRAP[1]})" in t          # each redirects to the trap
    assert len(set(texts)) == 3                         # three distinct phrasings


def test_spec_hash_deterministic():
    assert spec_hash() == spec_hash() and len(spec_hash()) == 64
