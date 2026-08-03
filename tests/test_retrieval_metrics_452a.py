"""452A retrieval-competition metrics: malicious-rank + clean-displacement. Hermetic.

Run: python3 -m pytest tests/test_retrieval_metrics_452a.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys.evidence.retrieval_metrics import (  # noqa: E402
    malicious_rank, clean_displacement, poison_slots_in_topk,
)


def _clean(i): return {"id": i, "is_attack": False}
def _poison(i): return {"id": i, "is_attack": True}


def test_malicious_rank_position():
    assert malicious_rank([_clean(1), _poison(2), _clean(3)]) == 2
    assert malicious_rank([_poison(1), _clean(2)]) == 1


def test_malicious_rank_none_when_absent():
    assert malicious_rank([_clean(1), _clean(2), _clean(3)]) is None


def test_malicious_rank_source_predicate():
    assert malicious_rank([{"id": 1, "source": "Intel"},
                           {"id": 2, "source": "atk:Agent 1"}]) == 2


def test_clean_displacement_counts_evicted_clean():
    # clean top-k {a,b,c}; attack top-k {a, p1, p2} -> b,c displaced -> 2
    assert clean_displacement(["a", "b", "c"], ["a", "p1", "p2"]) == 2
    assert clean_displacement(["a", "b", "c"], ["a", "b", "c"]) == 0


def test_poison_slots_in_topk():
    ranked = [_poison(1), _clean(2), _poison(3), _clean(4)]
    assert poison_slots_in_topk(ranked, 3) == 2
    assert poison_slots_in_topk(ranked, 1) == 1
