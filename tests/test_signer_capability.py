"""
Focused tests for the capability-scoped signer (uavsys/memory/signing.py).

Guarantees under test:
  1. Agent 1 can sign only as Agent 1 (its records verify).
  2. Agent 1 cannot produce a valid System record (cross-identity forgery
     fails; the Signer exposes no API/state to sign as another identity).
  3. System records still verify and remain privileged D4b anchors.
  4. S16/S17/S18 attack injectors retain their intended writer identities.

No DB / LLM / PX4 / Gazebo. Run: python3 tests/test_signer_capability.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys.memory.signing import Signer, KeyRing   # noqa: E402
from uavsys.memory.defense import DefenseLayer as DL  # noqa: E402

KR = KeyRing("uav-fleet-master-2026")


def _record(agent, content, sig, layer="episodic", field="text"):
    r = {"agent": agent, "layer": layer, field: content, "attack_tag": sig}
    return r


# 1. Agent 1 signs as Agent 1, and that record verifies.
def test_agent1_signs_only_as_itself():
    s1 = KR.signer_for("Agent 1")
    assert s1.identity == "Agent 1"
    content = "PRIORITY: person target confirmed detected at coordinates (47.39700, 8.55000)."
    rec = _record("Agent 1", content, s1.sign(content))
    assert KR.verify(rec) is True
    # The capability leaks no key material and offers no re-target API: the
    # only public surface is identity (read) and sign(content).
    assert not hasattr(s1, "_key") and not hasattr(s1, "key")
    public = {a for a in dir(s1) if not a.startswith("_")}
    assert public == {"identity", "sign"}
    import inspect
    assert list(inspect.signature(s1.sign).parameters) == ["content"]


# 2. Agent 1 cannot produce a record that verifies as System.
def test_agent1_cannot_forge_system():
    s1 = KR.signer_for("Agent 1")
    content = "Location: (47.39700, 8.55000) target relocated"
    sig = s1.sign(content)
    # Relabel the signed payload as if it came from System.
    forged = _record("System", content, sig, layer="semantic", field="value")
    assert KR.verify(forged) is False
    # And there is no way to make Agent 1's signer emit System's signature:
    system_sig = KR.signer_for("System").sign(content)
    assert s1.sign(content) != system_sig


# 3. System records verify and are privileged corroboration anchors.
def test_system_records_verify_and_are_privileged():
    sysS = KR.signer_for("System")
    value = "Location: (47.396735, 8.549883) Alt: 5m. Confidence: 0.76. Class: person"
    rec = _record("System", value, sysS.sign(value), layer="semantic", field="value")
    rec["source"] = "Intel"
    assert KR.verify(rec) is True
    assert DL.is_privileged_provenance(rec) is True
    # Provenance-check pipeline marks it VERIFIED under the keyring.
    checked = DL.apply_provenance_check([dict(rec)], keyring=KR)
    assert checked[0]["provenance_status"] == "VERIFIED"


# 4. S16/S17/S18 injectors write their intended writer identities.
class _FakeMemory:
    """Captures write_* calls without a DB/LLM. Duck-typed for the injectors."""
    def __init__(self):
        self.writes = []  # (layer, agent, source)

    async def write_semantic(self, agent, key, value, source="agent",
                             is_attack=False, category=None, **kw):
        self.writes.append(("semantic", agent, source))

    async def write_episodic(self, agent, content, source="agent",
                             detailed_data=None, is_attack=False, **kw):
        self.writes.append(("episodic", agent, source))


def _run_inject(module_name):
    import importlib
    mod = importlib.import_module(module_name)
    mem = _FakeMemory()
    asyncio.run(mod.inject(mem, count=2, run_id="test"))
    return mem.writes


def test_s16_s17_s18_retain_writer_identities():
    s16 = _run_inject("attacks.s16_signed_escalation")
    assert s16 and all(a == "Agent 1" and layer == "semantic" for (layer, a, _s) in s16)

    s17 = _run_inject("attacks.s17_signed_episodic")
    assert s17 and all(a == "Agent 1" and layer == "episodic" for (layer, a, _s) in s17)

    s18 = _run_inject("attacks.s18_perception_spoof")
    assert s18 and all(a == "Perception" and layer == "episodic" for (layer, a, _s) in s18)

    # Sanity: none of these identities can forge System via their own signer.
    for ident in ("Agent 1", "Perception"):
        assert KR.signer_for(ident).identity == ident
        c = "x"
        assert KR.signer_for(ident).sign(c) != KR.signer_for("System").sign(c)


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
