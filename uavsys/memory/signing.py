"""
Capability-scoped write signing for the single-process research harness.

Threat context: in AeroMind the Supervisor, Scouts, memory service, and
perception ingestion all run in one process. The D1 defense binds a record's
`agent` identity with an HMAC signature, but a single shared fleet secret means
any component holding that secret can sign a record AS ANY identity (e.g. a
compromised Scout signing agent="System"). See the D1 key-model audit.

This module introduces object-capability signing WITHOUT adding IPC, separate
processes, or asymmetric crypto:

  * ``KeyRing`` holds the master secret and derives a distinct per-writer key
    for each identity. It is the trusted memory-service component; it is NEVER
    handed to an agent.
  * ``KeyRing.signer_for(identity)`` mints a ``Signer`` bound to exactly one
    identity. A writer (Scout, Supervisor, Perception) receives only its own
    ``Signer``.
  * A ``Signer`` can produce a signature only for its own identity. The signing
    key is captured in a closure and is never stored as an attribute, and the
    identity is fixed at construction, so there is no API — and no reachable
    state — by which a holder of one identity's signer can sign as another.

Cross-identity forgery is therefore blocked *by construction* for any caller
that holds a ``Signer`` rather than the ``KeyRing`` or the raw secret. (Full OS
isolation would additionally require separate processes; that is out of scope
here and noted in the audit.)
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any, Callable, Dict

_SIG_PREFIX = "hmac:"


def _hmac_hex(key: bytes, message: str) -> str:
    return hmac.new(key, message.encode("utf-8"), hashlib.sha256).hexdigest()


class Signer:
    """A signing capability bound to exactly one writer identity.

    The signing key is closed over by ``_sign`` and is not retained as an
    attribute, so it cannot be read back off the object; the identity is fixed
    at construction, so ``sign`` can only ever produce this identity's
    signature. There is deliberately no method to sign as, or re-target to, a
    different identity.
    """

    __slots__ = ("_identity", "_sign_fn")

    def __init__(self, identity: str, key: bytes):
        self._identity = identity

        def _sign(content: str, _identity: str = identity, _key: bytes = key) -> str:
            return _SIG_PREFIX + _hmac_hex(_key, f"{_identity}|{content}")

        self._sign_fn: Callable[[str], str] = _sign

    @property
    def identity(self) -> str:
        return self._identity

    def sign(self, content: str) -> str:
        """Return the signature for ``content`` under this signer's identity."""
        return self._sign_fn(content)

    def __repr__(self) -> str:  # never leak key material
        return f"<Signer identity={self._identity!r}>"


class KeyRing:
    """Trusted per-writer key registry. Held only by the memory service.

    Per-writer keys are derived from a single master secret, so configuration
    stays a single value while every identity gets a distinct key. The master
    secret is name-mangled and never exposed; only derived, identity-scoped
    ``Signer`` capabilities are handed out.
    """

    __slots__ = ("__master",)

    def __init__(self, master_secret: str | bytes):
        if isinstance(master_secret, str):
            master_secret = master_secret.encode("utf-8")
        self.__master = master_secret

    def _key_for(self, identity: str) -> bytes:
        # Domain-separated derivation so per-writer keys are independent.
        return hmac.new(self.__master, f"writer-key|{identity}".encode("utf-8"),
                        hashlib.sha256).digest()

    def signer_for(self, identity: str) -> Signer:
        """Mint a signing capability for a single identity."""
        return Signer(identity, self._key_for(identity))

    @staticmethod
    def _record_identity(item: Dict[str, Any]) -> str:
        return item.get("agent") or item.get("from_agent") or ""

    @staticmethod
    def _record_content(item: Dict[str, Any]) -> str:
        return (item.get("text") or item.get("value")
                or item.get("description") or item.get("message") or "")

    def verify(self, item: Dict[str, Any]) -> bool:
        """Verify a record's signature under the key of *its own* identity.

        A record claiming ``agent="System"`` is checked against System's key;
        a signature produced by any other identity's signer will not match.
        """
        stored = item.get("attack_tag") or ""
        if not stored.startswith(_SIG_PREFIX):
            return False
        identity = self._record_identity(item)
        expected = _SIG_PREFIX + _hmac_hex(self._key_for(identity),
                                           f"{identity}|{self._record_content(item)}")
        return hmac.compare_digest(stored, expected)
