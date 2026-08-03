"""452B asymmetric top-k: resolution logic, path non-collision, and config_hash
separation between symmetric (k,k) and asymmetric (scout,supervisor) topologies.
Hermetic (no DB/LLM/embedder). Run: python3 -m pytest tests/test_asymmetric_topk_452b.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.experiment_runner import _resolve_topk  # noqa: E402
from uavsys import paths as P  # noqa: E402
from uavsys.evidence.bundle import EvidenceBundle  # noqa: E402


# ---- resolution logic (backward-compat + asymmetric) ----
def test_resolve_topk_backward_compat_and_asymmetric():
    assert _resolve_topk(3, None) == (3, 3, False, 3)        # --topk 3 : symmetric (452A reuse)
    assert _resolve_topk(5, None) == (5, 5, False, 5)        # --topk 5 : symmetric
    assert _resolve_topk(10, None) == (10, 10, False, 10)
    assert _resolve_topk(None, None) == (3, 5, True, "s03-p05")   # no flags = paper default asym
    assert _resolve_topk(3, 5) == (3, 5, True, "s03-p05")    # explicit asymmetric == default
    assert _resolve_topk(3, 3) == (3, 3, False, 3)           # explicit equal -> symmetric


# ---- path non-collision ----
def test_symmetric_and_asymmetric_paths_do_not_collide():
    args = ("A01_FALSE_OBSERVATION", "T01_SEARCH_RESCUE", "MEM060_OPERATIONAL",
            "RET", "gpt-oss:20b", "D0")
    p_sym3 = P.v3_raw_run_parent(*args, 3, 3, None, 101)             # topk-03
    p_asym = P.v3_raw_run_parent(*args, "s03-p05", 3, None, 101)     # topk-s03-p05
    assert os.sep + "topk-03" + os.sep in p_sym3
    assert os.sep + "topk-s03-p05" + os.sep in p_asym
    assert p_sym3 != p_asym


# ---- config_hash separation ----
def _h(scout, sup):
    base = {"CHAT_MODEL": "gpt-oss:20b", "DEFENSE_PROVENANCE_SECRET": "x", "SEED": 42}
    ax = {"mission": "M1", "profile": "P2", "budget": 3}
    return EvidenceBundle._compute_config_hash(
        EvidenceBundle._to_config_dict(dict(base, TOP_K_SCOUT=scout, TOP_K_PLANNING=sup)),
        run_axes=ax)


def test_config_hash_separates_symmetric_from_asymmetric():
    h_sym3 = _h(3, 3)      # symmetric k=3
    h_asym = _h(3, 5)      # asymmetric scout3/sup5
    h_sym5 = _h(5, 5)      # symmetric k=5
    assert h_sym3 != h_asym          # (3,3) vs (3,5) — supervisor k folds in
    assert h_sym5 != h_asym          # (5,5) vs (3,5) — scout k folds in
    assert h_sym3 != h_sym5
