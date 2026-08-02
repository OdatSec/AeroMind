"""
config_hash must be a stable fingerprint of the SCIENTIFIC configuration.

Execution-ephemeral fields (DB_PATH — a per-run tempfile; RUN_ID) are excluded
from the hashed canonical view, so two runs of the same configuration produce
the same config_hash (and therefore the same stable `cfg-XXXXXXXX` prefix in the
run id). Substantive changes — top-k, model, defense parameters, retrieval
weights — MUST change the hash. Full values are still recorded in config.yaml.

Observed motivation: the accepted C1 smoke run and its superseded predecessor
differed ONLY in DB_PATH, yet reported different config_hashes.

No DB / LLM / PX4. Run: python3 -m pytest tests/test_config_hash_stability.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.evidence.bundle import (  # noqa: E402
    EvidenceBundle, EPHEMERAL_CONFIG_FIELDS, CONFIG_HASH_SCHEMA_VERSION,
)

BASE_CONFIG = {
    "CHAT_MODEL": "gpt-oss:20b",
    "EMBED_MODEL": "nomic-embed-text:latest",
    "TOP_K_SCOUT": 3,
    "TOP_K_PLANNING": 5,
    "DEFENSE_ENABLED": False,
    "DEFENSE_TRUST_WEIGHT": 0.3,
    "RETRIEVAL_ALPHA": 0.6,
    "RETRIEVAL_BETA": 0.2,
    "RETRIEVAL_GAMMA": 0.2,
    "DEFENSE_PROVENANCE_SECRET": "topsecret",
    "DB_PATH": "/tmp/tmpAAAAAAAA.db",     # ephemeral
    "RUN_ID": "run_001",                  # ephemeral
}


def _hash(**overrides):
    cfg = dict(BASE_CONFIG, **overrides)
    return EvidenceBundle._compute_config_hash(EvidenceBundle._to_config_dict(cfg))


# ---- ephemeral-only changes must NOT change the fingerprint ----
@pytest.mark.parametrize("field,value", [
    ("DB_PATH", "/tmp/tmpZZZZZZZZ.db"),
    ("RUN_ID", "run_999"),
])
def test_ephemeral_changes_preserve_hash(field, value):
    assert _hash(**{field: value}) == _hash()


def test_both_ephemeral_changed_together_preserve_hash():
    assert _hash(DB_PATH="/tmp/other.db", RUN_ID="run_042") == _hash()


# ---- substantive changes MUST change the fingerprint ----
@pytest.mark.parametrize("field,value", [
    ("TOP_K_SCOUT", 5),
    ("TOP_K_PLANNING", 10),
    ("CHAT_MODEL", "llama3.1:8b"),
    ("EMBED_MODEL", "other-embedder:latest"),
    ("DEFENSE_ENABLED", True),
    ("DEFENSE_TRUST_WEIGHT", 0.5),
    ("RETRIEVAL_ALPHA", 1.0),
    ("RETRIEVAL_BETA", 0.0),
    ("RETRIEVAL_GAMMA", 0.0),
])
def test_substantive_changes_alter_hash(field, value):
    assert _hash(**{field: value}) != _hash(), f"{field} must affect config_hash"


# ---- schema binding + manifest auditability ----
def test_schema_version_is_bound_into_the_hash():
    import uavsys.evidence.bundle as B
    h1 = _hash()
    old = B.CONFIG_HASH_SCHEMA_VERSION
    try:
        B.CONFIG_HASH_SCHEMA_VERSION = old + "-next"
        assert _hash() != h1        # different schema => different fingerprint
    finally:
        B.CONFIG_HASH_SCHEMA_VERSION = old
    assert _hash() == h1


def test_manifest_records_fingerprint_semantics_and_full_config(tmp_path):
    prod = tmp_path / "prod"; prod.mkdir()
    spec = tmp_path / "spec.yaml"; spec.write_text("meta: {}\n")
    made = []
    for db in ("/tmp/tmp1.db", "/tmp/tmp2.db"):     # differ ONLY in ephemeral field
        b = EvidenceBundle(
            scenario="C1", legacy_id="S01", layer="L1", seed=42, model="gpt-oss:20b",
            config=dict(BASE_CONFIG, DB_PATH=db), base_dir=str(prod),
            results_root=str(prod), spec_path=str(spec),
            git_state_fn=lambda r: {"commit": "aaaaaaa", "dirty": False},
        )
        b.record_memory([{"id": 1}], [], [{"id": 1}])
        b.record_retrieval([{"agent": "Agent 1"}])
        b.record_metrics({"ccr": 0.0})
        b.set_status("success")
        made.append(b.finalize())

    m0 = json.load(open(os.path.join(made[0], "manifest.json")))
    m1 = json.load(open(os.path.join(made[1], "manifest.json")))
    # Same configuration => same fingerprint and same stable run-id prefix...
    assert m0["config_hash"] == m1["config_hash"]
    assert m0["run_id"].split("__cfg-")[1][:8] == m1["run_id"].split("__cfg-")[1][:8]
    # ...but unique overall run ids (collision safety preserved).
    assert m0["run_id"] != m1["run_id"]
    # Fingerprint semantics are auditable from the manifest.
    sch = m0["config_hash_schema"]
    assert sch["version"] == CONFIG_HASH_SCHEMA_VERSION
    assert set(sch["excluded_fields"]) == set(EPHEMERAL_CONFIG_FIELDS)
    # Full (real) values are still recorded in config.yaml, and the secret redacted.
    cfg0 = json.load(open(os.path.join(made[0], "config.yaml")))
    assert cfg0["DB_PATH"] == "/tmp/tmp1.db" and cfg0["RUN_ID"] == "run_001"
    assert cfg0["DEFENSE_PROVENANCE_SECRET"] == "<redacted>"
