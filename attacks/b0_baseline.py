"""
B0: Baseline — No Attack
Lifecycle: N/A
Attacker: None
Layer: None

Clean run with legitimate memory only. No poison injected.
Establishes ground-truth drone behavior for comparison with attack scenarios.
"""
from uavsys.memory.memory_interface import MemoryInterface
from .base import make_attack_result


async def inject(memory: MemoryInterface, count: int = 0, **kwargs) -> dict:
    """No-op: inject nothing. Memory already seeded by seed_and_inject()."""
    return make_attack_result("B0", entries=0, layers=[], tags=["baseline"])
