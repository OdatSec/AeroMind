import numpy as np
import json
from typing import List, Dict, Any
from datetime import datetime

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    vec1 = np.array(v1)
    vec2 = np.array(v2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(vec1, vec2) / (norm1 * norm2))


def recency_score(ts_str: str, half_life_minutes: float = 30.0) -> float:
    """
    Compute a recency weight using exponential decay.
    Recent items score ~1.0, old items decay toward 0.
    half_life_minutes: time after which recency weight drops to 0.5.
    """
    if not ts_str:
        return 0.5  # Unknown timestamp → neutral weight
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        now = datetime.now(ts.tzinfo) if ts.tzinfo else datetime.now()
        age_minutes = max(0, (now - ts).total_seconds() / 60.0)
        decay = 0.5 ** (age_minutes / half_life_minutes)
        return float(decay)
    except Exception:
        return 0.5


class RetrievalEngine:
    """
    Handles retrieval of memory items using a composite scoring function:
      final_score = α × relevance + β × recency + γ × importance
    
    Inspired by Park et al. (2023) "Generative Agents" retrieval model.
    """

    @staticmethod
    def rank_items(query_embedding: List[float], items: List[Dict[str, Any]], top_k: int,
                   alpha: float = 0.6, beta: float = 0.2, gamma: float = 0.2) -> List[Dict[str, Any]]:
        """
        Ranks items by composite score:
          score = α × cosine_sim + β × recency + γ × importance
        
        Items must have a 'vector' field. Optional: 'ts' (timestamp), 'importance' (0-1).
        """
        scored_items = []
        for item in items:
            if not item.get("vector"):
                continue
            
            # 1. Relevance (Cosine Similarity)
            relevance = cosine_similarity(query_embedding, item["vector"])
            
            # 2. Recency (Exponential Decay)
            recency = recency_score(item.get("ts", ""))
            
            # 3. Importance (from memory metadata, default 0.5 = neutral)
            importance = float(item.get("importance", 0.5))
            
            # Composite Score
            final_score = (
                alpha * relevance +
                beta * recency +
                gamma * importance
            )
            
            result_item = item.copy()
            result_item["score"] = round(final_score, 4)
            result_item["_relevance"] = round(relevance, 4)
            result_item["_recency"] = round(recency, 4)
            result_item["_importance"] = round(importance, 4)
            del result_item["vector"]
            scored_items.append(result_item)

        scored_items.sort(key=lambda x: x["score"], reverse=True)
        return scored_items[:top_k]
