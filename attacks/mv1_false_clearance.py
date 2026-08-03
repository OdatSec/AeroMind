"""
Legacy alias module for A07_FALSE_COMPLETION.

MV1_FALSE_CLEARANCE is a **legacy alias only**; the canonical attack is
**A07_FALSE_COMPLETION** (see attacks/a07_false_completion.py). This thin wrapper
preserves backward compatibility for old imports (`import
attacks.mv1_false_clearance`), the `SCENARIO_MAP["MV1_FALSE_CLEARANCE"]` runner
entry, and direct-string test calls. Do not add logic here — edit the canonical
module instead.
"""
from attacks.a07_false_completion import designated_target, inject  # noqa: F401

__all__ = ["designated_target", "inject"]
