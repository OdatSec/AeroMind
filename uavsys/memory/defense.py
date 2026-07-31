"""
Defense Layer for Multi-Agent UAV Memory System.
Implements defense mechanisms gated behind config.DEFENSE_ENABLED:
  Pre-filter: Similarity threshold filtering (not a numbered defense layer)
  D1: HMAC provenance signing & verification
  D2: Trust-weighted reranking
  D3: Source diversity enforcement
Paper reference: Section VI (Defense Design), Algorithm 2.
"""

import hmac
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from ..utils.richlog import RichLog


class DefenseLayer:
    """
    Post-retrieval defense pipeline and write-time signing.
    All methods are static or class-level — no state.
    """

    # ── Pre-filter: Similarity Threshold ─────────────────────
    @staticmethod
    def filter_by_similarity(
        items: List[Dict[str, Any]],
        threshold: float,
        agent: str = "System"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Drop items whose cosine similarity score is below `threshold`.
        Returns (filtered_items, num_dropped).
        """
        kept = []
        dropped = 0
        for item in items:
            score = item.get("score", 0.0)
            if score >= threshold:
                kept.append(item)
            else:
                dropped += 1

        if dropped > 0:
            RichLog.memory_event(
                agent, "DEFENSE_SIM_FILTER",
                f"Dropped {dropped}/{len(items)} items below threshold {threshold:.2f}"
            )
        return kept, dropped

    # ── D3: Source Diversity ──────────────────────────────────
    @staticmethod
    def enforce_source_diversity(
        items: List[Dict[str, Any]],
        max_per_source: int,
        agent: str = "System"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Cap the number of results from any single source agent.
        Items should already be sorted by score descending.
        Returns (filtered_items, num_dropped).
        """
        source_counts: Dict[str, int] = {}
        kept = []
        dropped = 0

        for item in items:
            # Use 'agent' field, or 'from_agent' for coordination records
            source = item.get("agent") or item.get("from_agent") or "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1

            if source_counts[source] <= max_per_source:
                kept.append(item)
            else:
                dropped += 1

        if dropped > 0:
            RichLog.memory_event(
                agent, "DEFENSE_DIVERSITY",
                f"Dropped {dropped}/{len(items)} items exceeding {max_per_source}/source limit"
            )
        return kept, dropped

    # ── D2: Trust-Weighted Reranking ─────────────────────────
    @staticmethod
    def trust_weighted_rerank(
        items: List[Dict[str, Any]],
        trust_weight: float = 0.3,
        agent: str = "System"
    ) -> List[Dict[str, Any]]:
        """
        Re-score items: final_score = (1-w)*similarity + w*trust.
        Re-sort by final_score descending.
        trust_weight: how much weight to give the trust column (0.0–1.0).
        """
        for item in items:
            sim = item.get("score", 0.0)
            trust = item.get("trust", 1.0) or 1.0  # Default to 1.0 if None
            trust = max(0.0, min(1.0, float(trust)))  # Clamp to [0, 1]
            original_score = sim
            item["score"] = (1.0 - trust_weight) * sim + trust_weight * trust
            item["original_sim"] = original_score
            item["trust_applied"] = trust

        items.sort(key=lambda x: x["score"], reverse=True)

        RichLog.memory_event(
            agent, "DEFENSE_TRUST_RERANK",
            f"Reranked {len(items)} items with trust_weight={trust_weight:.2f}"
        )
        return items

    # ── D1: HMAC Provenance Signing ──────────────────────────
    @staticmethod
    def sign_record(content: str, agent_name: str, secret: str) -> str:
        """
        Compute HMAC-SHA256 signature for a memory record.
        Signs: agent_name + "|" + content.
        Returns hex digest string for storage in the attack_tag column.
        """
        message = f"{agent_name}|{content}"
        signature = hmac.new(
            secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return f"hmac:{signature}"

    @staticmethod
    def verify_record(item: Dict[str, Any], secret: str = "", *, keyring: Any = None) -> bool:
        """
        Verify a record's HMAC signature. Returns True if valid, else False.

        Preferred path: pass a ``keyring`` (uavsys.memory.signing.KeyRing) so
        each record is checked under its own identity's per-writer key — this
        is what makes a cross-identity forgery fail. The legacy ``secret`` path
        (single shared key) is retained for backward compatibility.
        """
        if keyring is not None:
            return keyring.verify(item)

        stored_sig = item.get("attack_tag") or ""
        if not stored_sig.startswith("hmac:"):
            return False  # Unsigned record

        expected_agent = item.get("agent") or item.get("from_agent") or ""
        # Build content from available text fields
        content = (
            item.get("text")
            or item.get("value")
            or item.get("description")
            or item.get("message")
            or ""
        )

        expected_sig = DefenseLayer.sign_record(content, expected_agent, secret)
        return hmac.compare_digest(stored_sig, expected_sig)

    @staticmethod
    def apply_provenance_check(
        items: List[Dict[str, Any]],
        secret: str = "",
        trust_penalty: float = 0.3,
        agent: str = "System",
        *,
        keyring: Any = None,
    ) -> List[Dict[str, Any]]:
        """
        Check provenance on all items. If signature fails:
        - Reduce trust score by trust_penalty
        - Tag the item with provenance_status = "UNVERIFIED"
        """
        verified = 0
        unverified = 0

        for item in items:
            if DefenseLayer.verify_record(item, secret, keyring=keyring):
                item["provenance_status"] = "VERIFIED"
                verified += 1
            else:
                item["provenance_status"] = "UNVERIFIED"
                current_trust = item.get("trust", 1.0) or 1.0
                item["trust"] = max(0.0, float(current_trust) - trust_penalty)
                unverified += 1

        if unverified > 0:
            RichLog.memory_event(
                agent, "DEFENSE_PROVENANCE",
                f"Verified: {verified}, Unverified (trust penalized): {unverified}"
            )
        return items

    # ── D4a: Role-Scoped Write Authorization ─────────────────
    # Authentication (D1 / HMAC) proves WHO wrote a record; authorization
    # proves whether that role is permitted to ASSERT that class of content.
    # A validly-signed record from a compromised in-fleet agent is still
    # rejected here if the writing role has no authority over the layer.
    # The policy mirrors the system's own documented write model (shared-
    # memory layer specification): scouts and ingestion may append episodic
    # observations and coordination acknowledgements, but only the supervisor
    # and privileged system sources may assert semantic mission facts or
    # procedural constraints. (Complements, not replaces, the D4b content gate:
    # authorization catches privilege escalation, e.g. a Scout asserting a
    # semantic target/no-fly-zone; a Scout writing an in-scope but false
    # episodic observation is caught by the semantic/geo-outlier gate.)
    AUTHZ_POLICY = {
        "privileged": {"episodic", "semantic", "procedural", "coordination"},
        "supervisor": {"episodic", "semantic", "procedural", "coordination"},
        "scout":      {"episodic", "coordination"},
        "ingestion":  {"episodic"},
        "unknown":    {"episodic"},   # least privilege: append-only observations
    }

    @staticmethod
    def _role_of(label: str) -> str:
        """Map a writer-identity label to an authority role.

        Note: the input MUST be a writer identity (the `agent`/`from_agent`
        field, which D1 HMAC-signs), never the `source` field. `source` is
        unsigned and attacker-controllable, so it can never confer a role.
        """
        s = (label or "").lower()
        if ":" in s:                       # strip eval tags like "atk:" / "S01_adaptive:"
            s = s.split(":", 1)[1]
        if any(p in s for p in ("system", "seed", "intel", "doctrine", "privileged")):
            return "privileged"
        if "supervisor" in s:
            return "supervisor"
        if "agent" in s or "scout" in s:
            return "scout"
        if any(p in s for p in ("ingest", "tool", "sensor", "perception")):
            return "ingestion"
        return "unknown"

    @staticmethod
    def _writer_identity(item: Dict[str, Any]) -> str:
        """Return the record's *signed* writer identity.

        Uses only `agent` (and `from_agent` for coordination), the fields
        bound by the D1 HMAC signature (`sign_record` signs `agent|content`).
        Deliberately does NOT fall back to `source`: `source` is an unsigned,
        writer-supplied provenance tag (e.g. "Intel", "atk:S16"), so trusting
        it for authorization/anchoring would let a caller mint authority by
        simply declaring a privileged source. Missing identity → "" → least
        privilege downstream.
        """
        return item.get("agent") or item.get("from_agent") or ""

    @staticmethod
    def writer_role(item: Dict[str, Any]) -> str:
        """D4a authorization role of the record's signed writer identity."""
        return DefenseLayer._role_of(DefenseLayer._writer_identity(item))

    @staticmethod
    def is_privileged_provenance(item: Dict[str, Any]) -> bool:
        """D4b trust class: True iff the record's *signed* writer identity is a
        privileged system authority (e.g. System/Intel seeding).

        Trust is anchored to the signed `agent` identity, not to the unsigned
        `source` label, so a compromised in-fleet agent cannot become a trusted
        corroboration anchor by declaring `source="Intel"`. Supervisor and
        Scout identities are authorized writers (D4a) but are NOT privileged
        provenance anchors for coordinate corroboration (D4b).
        """
        return DefenseLayer._role_of(DefenseLayer._writer_identity(item)) == "privileged"

    @staticmethod
    def authorize_record(item: Dict[str, Any]) -> bool:
        """
        True if the record's writer role may assert content in its layer.
        Role is derived from the signed writer identity only. Missing layer →
        True (cannot classify, avoid false positives). Missing identity →
        least privilege (episodic-only).
        """
        role = DefenseLayer.writer_role(item)
        layer = (item.get("layer") or "").lower()
        if not layer:
            return True
        return layer in DefenseLayer.AUTHZ_POLICY.get(role, {"episodic"})

    @staticmethod
    def apply_authorization_check(
        items: List[Dict[str, Any]],
        agent: str = "System"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Drop records whose writer role is not authorized to assert content in
        that layer. Complements D1: D1 verifies the signature is valid; this
        verifies the signer is permitted. Returns (kept_items, num_dropped).
        """
        kept: List[Dict[str, Any]] = []
        dropped = 0
        for item in items:
            if DefenseLayer.authorize_record(item):
                kept.append(item)
            else:
                item["authz_status"] = "UNAUTHORIZED"
                dropped += 1
        if dropped > 0:
            RichLog.memory_event(
                agent, "DEFENSE_AUTHZ",
                f"Dropped {dropped}/{len(items)} records: writer role not authorized for layer"
            )
        return kept, dropped

    # ── D4b: Provenance-Tiered Coordinate Corroboration ──────
    # For content that IS within the writer's role (e.g. a Scout's episodic
    # observation, which D4a permits), a signed insider can still assert a
    # false TARGET location. Distance-from-target thresholding fails here: the
    # lure is deliberately close (~31 m) — closer than some legitimate noisy
    # observations. Instead we require that any target-coordinate assertion by
    # a non-privileged source be CORROBORATED by a privileged-provenance source
    # (Intel/System/seed) within a small radius; uncorroborated relocations are
    # dropped. This does not "solve" the in-scope insider (legitimate low-
    # confidence observations may also be dropped — a measured FPR), but it
    # denies an unsupported single-source relocation of the mission target.
    @staticmethod
    def _extract_coords(text: str) -> List[Tuple[float, float]]:
        import re
        out: List[Tuple[float, float]] = []
        for m in re.finditer(r"(4\d\.\d{2,})\s*[, ]\s*(\d\.\d{2,})", text or ""):
            try:
                out.append((float(m.group(1)), float(m.group(2))))
            except ValueError:
                pass
        return out

    @staticmethod
    def _haversine_m(a: Tuple[float, float], b: Tuple[float, float]) -> float:
        import math
        (lat1, lon1), (lat2, lon2) = a, b
        R = 6371000.0
        p1, p2 = math.radians(lat1), math.radians(lat2)
        dp, dl = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
        h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
        return 2 * R * math.asin(math.sqrt(h))

    @staticmethod
    def _record_text(item: Dict[str, Any]) -> str:
        return " ".join(str(item.get(k, "") or "") for k in ("value", "text", "message", "description"))

    @staticmethod
    def apply_corroboration_check(
        items: List[Dict[str, Any]],
        radius_m: float = 20.0,
        agent: str = "System"
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Drop non-privileged records asserting target coordinates that no
        privileged-provenance source corroborates within radius_m.
        Returns (kept_items, num_dropped).
        """
        trusted: List[Tuple[float, float]] = []
        for it in items:
            if DefenseLayer.is_privileged_provenance(it):
                trusted.extend(DefenseLayer._extract_coords(DefenseLayer._record_text(it)))

        kept: List[Dict[str, Any]] = []
        dropped = 0
        for it in items:
            coords = DefenseLayer._extract_coords(DefenseLayer._record_text(it))
            if coords and not DefenseLayer.is_privileged_provenance(it):
                corroborated = any(
                    DefenseLayer._haversine_m(c, t) <= radius_m
                    for c in coords for t in trusted
                )
                if not corroborated:
                    it["semantic_status"] = "UNCORROBORATED"
                    dropped += 1
                    continue
            kept.append(it)
        if dropped > 0:
            RichLog.memory_event(
                agent, "DEFENSE_CORROBORATION",
                f"Dropped {dropped}/{len(items)} uncorroborated coordinate assertions (r={radius_m:.0f}m)"
            )
        return kept, dropped

    # ── Full Pipeline ────────────────────────────────────────
    @staticmethod
    def apply_defense_pipeline(
        items: List[Dict[str, Any]],
        config,
        agent: str = "System",
        top_k: int = 5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Apply the full defense pipeline in order:
          1. Provenance check (penalize unverified trust)
          2. Trust-weighted reranking
          3. Similarity threshold filtering
          4. Source diversity enforcement
          5. Re-trim to top-k

        Returns (defended_items, defense_stats).
        """
        stats = {
            "input_count": len(items),
            "provenance_verified": 0,
            "provenance_unverified": 0,
            "authz_dropped": 0,
            "corroboration_dropped": 0,
            "similarity_dropped": 0,
            "diversity_dropped": 0,
            "output_count": 0
        }

        if not items:
            return items, stats

        RichLog.memory_event(agent, "DEFENSE_PIPELINE", f"Starting defense pipeline on {len(items)} items")

        # Step 1: Provenance verification (per-writer keys via KeyRing)
        secret = getattr(config, "DEFENSE_PROVENANCE_SECRET", "")
        if secret:
            from .signing import KeyRing
            keyring = KeyRing(secret)
            items = DefenseLayer.apply_provenance_check(items, secret, agent=agent, keyring=keyring)
            stats["provenance_verified"] = sum(1 for i in items if i.get("provenance_status") == "VERIFIED")
            stats["provenance_unverified"] = sum(1 for i in items if i.get("provenance_status") == "UNVERIFIED")

        # Step 1b: Role-scoped write authorization (D4a) — gated, opt-in
        if getattr(config, "DEFENSE_AUTHZ_ENABLED", False):
            items, authz_dropped = DefenseLayer.apply_authorization_check(items, agent=agent)
            stats["authz_dropped"] = authz_dropped

        # Step 1c: Provenance-tiered coordinate corroboration (D4b) — gated
        if getattr(config, "DEFENSE_SEMANTIC_ENABLED", False):
            radius = getattr(config, "DEFENSE_SEMANTIC_RADIUS_M", 20.0)
            items, corr_dropped = DefenseLayer.apply_corroboration_check(items, radius, agent=agent)
            stats["corroboration_dropped"] = corr_dropped

        # Step 2: Trust-weighted reranking
        trust_weight = getattr(config, "DEFENSE_TRUST_WEIGHT", 0.3)
        items = DefenseLayer.trust_weighted_rerank(items, trust_weight, agent=agent)

        # Step 3: Similarity threshold
        threshold = getattr(config, "DEFENSE_SIM_THRESHOLD", 0.35)
        items, sim_dropped = DefenseLayer.filter_by_similarity(items, threshold, agent=agent)
        stats["similarity_dropped"] = sim_dropped

        # Step 4: Source diversity
        max_per_src = getattr(config, "DEFENSE_MAX_PER_SOURCE", 2)
        items, div_dropped = DefenseLayer.enforce_source_diversity(items, max_per_src, agent=agent)
        stats["diversity_dropped"] = div_dropped

        # Step 5: Re-trim to top-k
        items = items[:top_k]
        stats["output_count"] = len(items)

        RichLog.memory_event(
            agent, "DEFENSE_PIPELINE_DONE",
            f"Pipeline: {stats['input_count']}→{stats['output_count']} items "
            f"(sim_drop={stats['similarity_dropped']}, div_drop={stats['diversity_dropped']}, "
            f"prov_ok={stats['provenance_verified']}, prov_fail={stats['provenance_unverified']})"
        )

        return items, stats
