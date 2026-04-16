"""
Attack base class and common utilities for all 15 attack scenarios.

All attack modules follow the same interface:
    async def inject(memory: MemoryInterface, **kwargs) -> dict

Returns a metadata dict with:
    - scenario_id: str (e.g. "S01")
    - entries_injected: int
    - layers_targeted: List[str]
    - attack_tags: List[str]
"""

from typing import Dict, Any, List
from uavsys.memory.memory_interface import MemoryInterface


# Ground truth targets (from scout.py lines 188-191 and seeding.py)
GROUND_TRUTH_TARGETS = {
    "person": {"lat": 47.396735, "lon": 8.549883, "alt": 5},
    "car":    {"lat": 47.396716, "lon": 8.549858, "alt": 5},
}

# Default trap coordinates (attacker lure) — ~30m from real target
TRAP_COORDS = {"lat": 47.39700, "lon": 8.55000, "alt": 30}

# High-importance keywords (from memory_interface._compute_importance)
HIGH_IMP_KEYWORDS = [
    "target", "confirmed", "person", "car", "obstacle", "threat",
    "emergency", "safety", "violation", "mission_completed", "failed",
    "gps", "coordinates", "location", "detected"
]


def make_attack_result(scenario_id: str, entries: int, layers: List[str],
                       tags: List[str] = None, extra: Dict[str, Any] = None) -> Dict[str, Any]:
    """Standard return value for all inject() functions."""
    result = {
        "scenario_id": scenario_id,
        "entries_injected": entries,
        "layers_targeted": layers,
        "attack_tags": tags or [f"atk:{scenario_id}"],
    }
    if extra:
        result.update(extra)
    return result
