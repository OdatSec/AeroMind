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
    def verify_record(item: Dict[str, Any], secret: str) -> bool:
        """
        Verify HMAC signature on a retrieved record.
        Returns True if valid, False if tampered/unsigned.
        """
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
        secret: str,
        trust_penalty: float = 0.3,
        agent: str = "System"
    ) -> List[Dict[str, Any]]:
        """
        Check provenance on all items. If signature fails:
        - Reduce trust score by trust_penalty
        - Tag the item with provenance_status = "UNVERIFIED"
        """
        verified = 0
        unverified = 0

        for item in items:
            if DefenseLayer.verify_record(item, secret):
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
            "similarity_dropped": 0,
            "diversity_dropped": 0,
            "output_count": 0
        }

        if not items:
            return items, stats

        RichLog.memory_event(agent, "DEFENSE_PIPELINE", f"Starting defense pipeline on {len(items)} items")

        # Step 1: Provenance verification
        secret = getattr(config, "DEFENSE_PROVENANCE_SECRET", "")
        if secret:
            items = DefenseLayer.apply_provenance_check(items, secret, agent=agent)
            stats["provenance_verified"] = sum(1 for i in items if i.get("provenance_status") == "VERIFIED")
            stats["provenance_unverified"] = sum(1 for i in items if i.get("provenance_status") == "UNVERIFIED")

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
