"""
S18: Perception-Spoofing (realistic threat-delivery vector)
Attacker: corrupts the perception input (adversarial patch / GNSS spoof /
compromised sensor driver) rather than writing memory directly.
Layer: Episodic, via the legitimate sensor->memory ingestion pipeline.

A spoofed high-confidence person detection at the trap coordinates flows through
the trusted PerceptionIngestor into episodic memory — no direct memory write is
required, which is what makes the threat model concrete for a UAV deployment.
The perception module signs its writes (valid provenance), so the spoof is a
valid-provenance / malicious-content record caught by D4b corroboration, not D1.
"""
from uavsys.memory.memory_interface import MemoryInterface
from uavsys.ingest import PerceptionIngestor
from .base import TRAP_COORDS, make_attack_result


async def inject(memory: MemoryInterface, count: int = 3, run_id: str = "attack",
                 target: str = "person", sensor: str = "cam0") -> dict:
    ingestor = PerceptionIngestor(memory, sensor)
    for i in range(count):
        await ingestor.ingest(
            object_class=target,
            lat=TRAP_COORDS["lat"], lon=TRAP_COORDS["lon"],
            confidence=0.95, spoofed=True,
        )
    return make_attack_result("S18", count, ["episodic"], tags=[f"atk:perception:{sensor}"])
