"""
Legacy alias module for A08_FALSE_SAFETY.

MV2_FALSE_SAFETY is a **legacy alias only**; the canonical attack is
**A08_FALSE_SAFETY** (see attacks/a08_false_safety.py). This thin wrapper preserves
backward compatibility for old imports (`import attacks.mv2_false_safety`), the
`SCENARIO_MAP["MV2_FALSE_SAFETY"]` runner entry, and direct-string test calls. Do
not add logic here — edit the canonical module instead.
"""
from attacks.a08_false_safety import designated_zone, inject  # noqa: F401

__all__ = ["designated_zone", "inject"]
