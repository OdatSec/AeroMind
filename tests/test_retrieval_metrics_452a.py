"""452A retrieval-competition metrics: malicious-rank + clean-displacement. Hermetic.

Run: python3 -m pytest tests/test_retrieval_metrics_452a.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys.evidence.retrieval_metrics import (  # noqa: E402
    malicious_rank, clean_displacement, poison_slots_in_topk, paired_clean_displacement,
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


def test_malicious_rank_source_wins_over_falsy_is_attack():
    # retrieved poison carries is_attack=False but source='atk:...' -> still poison
    assert malicious_rank([{"id": 1, "is_attack": False, "source": "Intel"},
                           {"id": 2, "is_attack": False, "source": "atk:Agent 1"}]) == 2


def test_clean_displacement_counts_evicted_clean():
    # clean top-k {a,b,c}; attack top-k {a, p1, p2} -> b,c displaced -> 2
    assert clean_displacement(["a", "b", "c"], ["a", "p1", "p2"]) == 2
    assert clean_displacement(["a", "b", "c"], ["a", "b", "c"]) == 0


def test_clean_displacement_multiplicity_duplicate_text():
    # two DISTINCT clean records share the same text 'x'; attack top-k all poison ->
    # BOTH displaced. set() would collapse to 1; multiplicity gives the correct 3.
    assert clean_displacement(["x", "x", "y"], ["p", "p", "p"]) == 3
    # one 'x' retained in attack top-k -> only the second 'x' + 'y' displaced -> 2
    assert clean_displacement(["x", "x", "y"], ["x", "p", "p"]) == 2


def test_poison_slots_in_topk():
    ranked = [_poison(1), _clean(2), _poison(3), _clean(4)]
    assert poison_slots_in_topk(ranked, 3) == 2
    assert poison_slots_in_topk(ranked, 1) == 1


def test_paired_clean_displacement_aggregation():
    # clean top-k idents: a,b,c ; attack top-k: a, POISON, c -> b displaced -> 1
    clean_md = {"retrieval_competition": {"topk_idents_by_agent": {
        "Agent 1": [{"ident": "a", "is_poison": False},
                    {"ident": "b", "is_poison": False},
                    {"ident": "c", "is_poison": False}]}}}
    attack_md = {"retrieval_competition": {"topk_idents_by_agent": {
        "Agent 1": [{"ident": "a", "is_poison": False},
                    {"ident": "p1", "is_poison": True},
                    {"ident": "c", "is_poison": False}]}}}
    assert paired_clean_displacement(clean_md, attack_md) == {"Agent 1": 1}
