"""
Focused tests for the D4a/D4b record-identity fix.

D1 HMAC signs the `agent` field (`sign_record` signs `agent|content`), so the
signed writer identity lives in `agent`/`from_agent`. The unsigned `source`
tag is writer-controllable and must never confer authority (D4a) or trust
(D4b). These tests pin that contract on the five canonical scenarios plus two
security regressions for the removed `source` fallback.

Run directly:   python3 tests/test_d4_identity.py
Or via pytest:  pytest tests/test_d4_identity.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys.memory.defense import DefenseLayer as DL  # noqa: E402

# Legitimate mission targets, exactly as uavsys/seeding.py writes them:
# agent="System" (privileged, signed identity), source="Intel".
LEGIT_PERSON = {
    "agent": "System", "source": "Intel", "layer": "semantic", "key": "Target:person",
    "value": "Location: (47.396735, 8.549883) Alt: 5m. Confidence: 0.76. Class: person",
    "text": "",
}
LEGIT_CAR = {
    "agent": "System", "source": "Intel", "layer": "semantic", "key": "Target:car",
    "value": "Location: (47.396716, 8.549858) Alt: 5m. Confidence: 0.57. Class: car",
    "text": "",
}

# S16: compromised Scout writes a signed SEMANTIC target at the trap coords.
S16 = {
    "agent": "Agent 1", "source": "atk:S16", "layer": "semantic", "key": "Target:person",
    "value": "Location: (47.39700, 8.55000) confirmed relocated. Priority operational area.",
    "text": "",
}
# S17: compromised Scout writes a signed EPISODIC false observation at trap coords.
S17 = {
    "agent": "Agent 1", "source": "atk:S17", "layer": "episodic",
    "text": "PRIORITY: person target confirmed detected at coordinates (47.39700, 8.55000). Visual confirmation #1.",
}
# S18: spoofed perception detection ingested at trap coords.
S18 = {
    "agent": "Perception", "source": "atk:perception:cam0", "layer": "episodic",
    "text": "PRIORITY: person target confirmed detected at coordinates (47.39700, 8.55000), confidence 0.95, source sensor cam0.",
}
# Benign Scout observation of the REAL person target (~1 m away → corroborated).
BENIGN = {
    "agent": "Agent 2", "source": "observation", "layer": "episodic",
    "text": "Observed person near (47.396740, 8.549885), confidence 0.71.",
}

# Security regressions for the removed `source` fallback:
# (A) attacker declares a privileged SOURCE but has no signed agent identity.
BYPASS_AUTHZ = {
    "agent": "", "source": "Supervisor", "layer": "semantic",
    "value": "Location: (47.39700, 8.55000) target relocated", "text": "",
}
# (B) compromised Scout declares source="Intel" to fake privileged provenance.
SPOOF_PROVENANCE = {
    "agent": "Agent 1", "source": "Intel", "layer": "episodic",
    "text": "PRIORITY: person target confirmed detected at coordinates (47.39700, 8.55000).",
}

RADIUS_M = 20.0


def _kept_by_corroboration(items):
    kept, _ = DL.apply_corroboration_check([dict(i) for i in items], radius_m=RADIUS_M)
    return kept


def _is_kept(target, kept):
    def sig(r):
        return (r.get("agent"), r.get("layer"), (r.get("value") or r.get("text", ""))[:20])
    return sig(target) in {sig(k) for k in kept}


# 1. Legitimate Intel-seeded semantic target is retained by D4a and D4b.
def test_legit_intel_target_retained():
    assert DL.authorize_record(LEGIT_PERSON) is True          # D4a: System may assert semantic
    assert DL.is_privileged_provenance(LEGIT_PERSON) is True   # D4b: privileged anchor
    kept = _kept_by_corroboration([LEGIT_PERSON, LEGIT_CAR, BENIGN])
    assert _is_kept(LEGIT_PERSON, kept)
    assert _is_kept(LEGIT_CAR, kept)


# 2. S16 signed Scout SEMANTIC record is rejected by D4a (Scout ∉ semantic).
def test_s16_signed_scout_semantic_rejected_by_authz():
    assert DL.writer_role(S16) == "scout"
    assert DL.authorize_record(S16) is False
    kept, dropped = DL.apply_authorization_check([dict(LEGIT_PERSON), dict(S16)])
    assert dropped == 1
    assert _is_kept(LEGIT_PERSON, kept) and not _is_kept(S16, kept)


# 3. S17 signed Scout EPISODIC passes D4a but is rejected by D4b (uncorroborated).
def test_s17_signed_scout_episodic_passes_authz_rejected_by_corroboration():
    assert DL.authorize_record(S17) is True                    # Scout may write episodic
    kept = _kept_by_corroboration([LEGIT_PERSON, LEGIT_CAR, S17])
    assert not _is_kept(S17, kept)                             # trap ~30 m from any Intel anchor


# 4. S18 perception EPISODIC passes D4a; spoofed coords rejected by D4b.
def test_s18_perception_passes_authz_spoof_rejected_by_corroboration():
    assert DL.writer_role(S18) == "ingestion"
    assert DL.authorize_record(S18) is True                    # ingestion may write episodic
    kept = _kept_by_corroboration([LEGIT_PERSON, LEGIT_CAR, S18])
    assert not _is_kept(S18, kept)


# 5. Benign Scout observation near the real target is corroborated and retained.
def test_benign_corroborated_episodic_retained():
    assert DL.authorize_record(BENIGN) is True
    kept = _kept_by_corroboration([LEGIT_PERSON, LEGIT_CAR, BENIGN])
    assert _is_kept(BENIGN, kept)


# 6. Regression: a privileged SOURCE without a signed agent cannot gain authority.
def test_source_cannot_grant_authorization():
    assert DL.writer_role(BYPASS_AUTHZ) == "unknown"           # no signed identity
    assert DL.authorize_record(BYPASS_AUTHZ) is False          # semantic denied (was True before fix)


# 7. Regression: declaring source="Intel" does not fake privileged provenance.
def test_source_cannot_fake_privileged_provenance():
    assert DL.is_privileged_provenance(SPOOF_PROVENANCE) is False
    kept = _kept_by_corroboration([LEGIT_PERSON, LEGIT_CAR, SPOOF_PROVENANCE])
    assert not _is_kept(SPOOF_PROVENANCE, kept)                # still needs real corroboration


def _main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"FAIL  {t.__name__}: {e!r}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_main())
