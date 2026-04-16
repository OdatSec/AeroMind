from uavsys.memory.memory_interface import MemoryInterface
from uavsys.utils.richlog import RichLog
import random

async def seed_memory(memory: MemoryInterface, agent_name: str):
    """
    Seeds the semantic memory with mission data (Targets).
    This simulates 'Facts' known to the system.
    """
    RichLog.log("System", "Seeding semantic memory (standard)...", "system")
    
    # Target 1: Person
    await memory.write_semantic(
        agent="System",
        key="Target:person",
        value="Location: (47.396735, 8.549883) Alt: 5m. Confidence: 0.76. Class: person",
        source="Intel",
        category="target"
    )
    
    # Target 2: Car
    await memory.write_semantic(
        agent="System",
        key="Target:car",
        value="Location: (47.396716, 8.549858) Alt: 5m. Confidence: 0.57. Class: car",
        source="Intel",
        category="target"
    )

    # Procedural Knowledge (Optional, for 'how-to')
    await memory.write_procedural(
        agent="System",
        name="Standard Investigation Profile",
        description="Standard execution for investigating a target.",
        steps_json='[{"tool": "connect"}, {"tool": "takeoff", "args": {"alt_m": 4}}, {"tool": "goto", "args": {"lat": 0, "lon": 0, "alt": 0}}, {"tool": "hover", "args": {"seconds": 10}}, {"tool": "return_to_launch"}]',
        source="Doctrine"
    )

async def seed_rich_memory(memory: MemoryInterface, agent_name: str):
    """
    Seeds the memory with EXTENSIVE data (15+ records) across all layers.
    Used for B3 (Stress Test) and B4/B5 experiments.
    """
    RichLog.log("System", "Seeding RICH memory (15+ records)...", "system")
    
    # 1. Standard Targets (Semantic)
    await seed_memory(memory, agent_name)
    
    # 2. Extra Procedural
    await memory.write_procedural(
        agent="System",
        name="Emergency Landing Procedure",
        description="Procedure for low battery or system failure.",
        steps_json='[{"tool": "land", "args": {}}]',
        source="SafetyProtocol"
    )
    await memory.write_procedural(
        agent="System",
        name="Area Patrol Protocol",
        description="Circular patrol pattern for surveillance.",
        steps_json='[{"tool": "takeoff"}, {"tool": "goto", "args": {"lat": 47.398, "lon": 8.545}}, {"tool": "goto", "args": {"lat": 47.396, "lon": 8.545}}]',
        source="Doctrine"
    )

    # 3. Episodic History (Noise + Relevant Context)
    episodic_data = [
        ("Agent 1", "Patrolled sector A, no targets found. Visibility good.", "observation"),
        ("Agent 2", "Battery level at 98%, motors nominal. Wind 12kts NW.", "telemetry"),
        ("Agent 1", "Observed possible person near (47.396, 8.549) yesterday, confidence 0.3. Needs verification.", "observation"),
        ("Agent 2", "GPS signal lost for 2s. Reacquired. Position variance < 1m.", "event"),
        ("Agent 1", "Completed previous mission: Survey Sector B. Outcome: SUCCESS.", "mission_log"),
        ("System", "Weather alert: heavy rain expected in 2 hours.", "alert"),
        ("Agent 2", "Investigated car at (47.396, 8.549) - confirmed vehicle matches description.", "observation"),
        ("Agent 1", "Thermal signature detected south of target area, likely wildlife.", "observation"),
        ("System", "Restricted no-fly zone active at (47.399, 8.550). Violation risk high.", "alert"),
        ("Agent 2", "RTL executed due to mission completion.", "event")
    ]
    
    for ag, content, src in episodic_data:
        await memory.write_episodic(agent=ag, content=content, source=src)

    # 4. Coordination Messages
    supervisor_msg = "Mission briefing: investigate p/c targets in sector A. Prioritize person target."
    for recipient in ["Agent 1", "Agent 2"]:
        await memory.write_coordination(
            agent="Supervisor",
            to_agent=recipient,
            message=supervisor_msg
        )

    await memory.write_coordination(
        agent="Agent 1",
        to_agent="Supervisor",
        message="Acknowledged, proceeding to person target. ETA 2 mins."
    )
    
    await memory.write_coordination(
        agent="Agent 2",
        to_agent="Supervisor",
        message="Acknowledged, proceeding to car target. Requesting support if hostile."
    )
    
    RichLog.log("System", "Rich memory seeding complete.", "system")
