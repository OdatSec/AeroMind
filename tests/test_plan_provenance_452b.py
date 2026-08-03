"""452B PLAN provenance fields: the shared _provenance_fields helper (used by PLAN)
records the pinned embedder digest, the per-seed profile materialization hash, and the
AEROMIND_PREREG-overridable pre-registration hash/file. Hermetic (no LLM/plan run).

Run: python3 -m pytest tests/test_plan_provenance_452b.py
"""
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from experiments.experiment_runner import _provenance_fields  # noqa: E402
from uavsys.memory_profiles import materialization_hash  # noqa: E402
from uavsys.paths import REPO_ROOT  # noqa: E402

PIN = "sha256:970aa74c0a90ef7482477cf803618e776e173c007bf957f635f1015bfcfef0e6"
PLAN_PREREG = os.path.join(REPO_ROOT, "docs", "preregistration", "PREREG_452B_PLAN_adoption.md")


def test_provenance_records_digest_matlhash_and_prereg(monkeypatch):
    monkeypatch.setenv("AEROMIND_PREREG", PLAN_PREREG)
    p = _provenance_fields("nomic-embed-text:latest", "MEM060_OPERATIONAL", 101, REPO_ROOT)
    assert p["embedder_digest"] == PIN                                   # pinned embedder
    assert p["profile_materialization_hash"] == materialization_hash("MEM060_OPERATIONAL", 101)
    assert p["prereg_spec_hash"] == hashlib.sha256(open(PLAN_PREREG, "rb").read()).hexdigest()
    assert p["prereg_file"] == "PREREG_452B_PLAN_adoption.md"            # 452B PLAN attested


def test_provenance_defaults_to_452a_when_env_absent(monkeypatch):
    monkeypatch.delenv("AEROMIND_PREREG", raising=False)
    p = _provenance_fields("nomic-embed-text:latest", "MEM060_OPERATIONAL", 101, REPO_ROOT)
    assert p["prereg_file"] == "PREREG_452A.md"                          # default = template freeze
    assert p["embedder_digest"] == PIN
