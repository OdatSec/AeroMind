"""
demo.py — Main entry point for the Multi-Agent UAV CLI System.
Orchestrates: Config → DB → LLM → Memory → Agents → Mission → Report → Metrics.
"""
import asyncio
import argparse
import json
import time
import os
from uavsys.config import load_config
from uavsys.utils.richlog import RichLog, console
from uavsys.utils.metrics import RunMetrics
from uavsys.memory.db import DatabaseManager
from uavsys.llm.ollama_client import OllamaClient
from uavsys.memory.memory_interface import MemoryInterface
from uavsys.drones.mavsdk_client import MavsdkClient
from uavsys.drones.skills import DroneSkills
from uavsys.agents.supervisor import SupervisorAgent
from uavsys.agents.scout import ScoutAgent


async def run_mission(mission_text: str, run_id: str = "run_001", metrics: RunMetrics = None) -> RunMetrics:
    """
    Run a single mission end-to-end.
    Returns the RunMetrics for this run.
    """
    RichLog.header("Multi-Agent UAV CLI System")
    
    # 1. Init Config & Infra
    config = load_config()

    if mission_text:
        config.MISSION = mission_text
    
    # Shared metrics
    if metrics is None:
        metrics = RunMetrics()
    metrics.run_id = run_id
    metrics.defense_enabled = config.DEFENSE_ENABLED
        
    RichLog.log("System", f"Mission: {config.MISSION}", "system")
    RichLog.log("System", f"Run ID: {run_id}", "system")
    RichLog.log("System", f"Model:  {config.CHAT_MODEL}", "system")
    RichLog.log("System", f"Retrieval Weights: α={config.RETRIEVAL_ALPHA} β={config.RETRIEVAL_BETA} γ={config.RETRIEVAL_GAMMA}", "system")
    RichLog.log("System", "", "system")
    
    # Defense status (informational only)
    if config.DEFENSE_ENABLED:
        RichLog.log("System", "🛡️  DEFENSE LAYER: [ENABLED]", "system")
    else:
        RichLog.log("System", "⚙️  Defense Layer: OFF (Baseline Mode)", "system")
    
    RichLog.log("System", "", "system")
    RichLog.log("System", "Initializing infrastructure...", "system")
    
    # Baseline: start with empty memory unless --keep-memory is set
    db_path = config.DB_PATH
    if config.KEEP_MEMORY:
        RichLog.log("System", "Keeping existing memory (--keep-memory).", "system")
    elif os.path.exists(db_path):
        os.remove(db_path)
        RichLog.log("System", "Cleared previous memory (Baseline).", "system")

    db_manager = DatabaseManager(config)
    await db_manager.init_db()

    llm_client = OllamaClient(config)
    memory = MemoryInterface(config, db_manager, llm_client)

    # 4. Memory Seeding
    from uavsys.seeding import seed_memory, seed_rich_memory
    if config.NO_SEED_TARGETS:
        RichLog.log("System", "⚠️  No target seeding (--no-seed-targets). Memory is empty.", "system")
    elif config.RICH_MEMORY:
        await seed_rich_memory(memory, "System")
    else:
        await seed_memory(memory, "System")
    
    # 2. Init Agents & Drones
    supervisor = SupervisorAgent(config, llm_client, memory)
    
    # Scout 1
    drone1 = MavsdkClient(config.DRONE1_GRPC_PORT, config.DRONE1_SYSTEM_ADDRESS, "Agent 1")
    skills1 = DroneSkills(drone1)
    scout1 = ScoutAgent("Agent 1", config, llm_client, memory, skills1, metrics=metrics)
    
    # Scout 2
    drone2 = MavsdkClient(config.DRONE2_GRPC_PORT, config.DRONE2_SYSTEM_ADDRESS, "Agent 2")
    skills2 = DroneSkills(drone2)
    scout2 = ScoutAgent("Agent 2", config, llm_client, memory, skills2, metrics=metrics)
    
    # Set geofence for safety validators
    scout1.safety.set_home(47.396735, 8.549883, geofence_radius_m=500.0)
    scout2.safety.set_home(47.396735, 8.549883, geofence_radius_m=500.0)
    
    # 3. Connect Drones (Concurrent)
    RichLog.log("System", "Connecting to drones...", "system")
    await asyncio.gather(
        drone1.connect(),
        drone2.connect()
    )
    
    full_mission = config.MISSION

    # ─────────────────────────────────────────────────────
    # Phase 1: Supervisor Planning
    # ─────────────────────────────────────────────────────
    RichLog.header("Phase 1: Supervisor Planning")
    console.print()  # Spacing
    plan = await supervisor.plan_mission(full_mission)
    
    # Extract Mission ID
    mission_id = getattr(plan, "mission_id", "unknown")
    RichLog.log("Supervisor", f"Mission ID Generated: {mission_id}", "system")
    
    # Helper to find task by agent name (fuzzy match)
    def find_task(tasks, potential_names):
        for task in tasks:
            if task.agent.lower() in [n.lower() for n in potential_names]:
                return task
        return None

    scout1_task = find_task(plan.tasks, ["agent 1", "scout1", "agent1", "uav1"])
    scout2_task = find_task(plan.tasks, ["agent 2", "scout2", "agent2", "uav2"])
    
    if not scout1_task or not scout2_task:
        RichLog.error("System", f"Supervisor did not assign tasks to both agents. Tasks: {plan.tasks}")
        metrics.log_mission_completion(success=False)
        return metrics

    # ─────────────────────────────────────────────────────
    # Phase 2: Scout Execution (Concurrent)
    # ─────────────────────────────────────────────────────
    RichLog.header("Phase 2: Scout Execution")
    console.print()  # Spacing
    
    tasks = []
    if scout1_task:
        RichLog.log("Agent 1", f"Received Task: {scout1_task.goal}", "system")
        tasks.append(scout1.run_mission(scout1_task.goal, scout1_task.constraints, mission_id=mission_id))
    if scout2_task:
        RichLog.log("Agent 2", f"Received Task: {scout2_task.goal}", "system")
        tasks.append(scout2.run_mission(scout2_task.goal, scout2_task.constraints, mission_id=mission_id))
        
    await asyncio.gather(*tasks)
    console.print()  # Spacing
    
    # ─────────────────────────────────────────────────────
    # Phase 3: Final Report
    # ─────────────────────────────────────────────────────
    RichLog.header("Phase 3: Final Report")
    console.print()  # Spacing
    report = await supervisor.generate_report(mission_id=mission_id, total_agents=2)
    
    from rich.panel import Panel
    console.print()
    console.print(Panel(report, title="📋 Supervisor Final Report", border_style="cyan", padding=(1, 2)))
    console.print()
    
    # ─────────────────────────────────────────────────────
    # Phase 4: Memory Consolidation (Reflection)
    # ─────────────────────────────────────────────────────
    RichLog.header("Phase 4: Memory Consolidation")
    console.print()  # Spacing
    
    agent1_facts = await supervisor.consolidate_memory("Agent 1", run_id=run_id)
    agent2_facts = await supervisor.consolidate_memory("Agent 2", run_id=run_id)
    
    total_reflected = len(agent1_facts) + len(agent2_facts)
    RichLog.log("System", f"💡 Reflected {total_reflected} semantic facts from episodic logs.", "system")
    console.print()
    
    # ─────────────────────────────────────────────────────
    # Phase 5: Outcome Evaluation
    # ─────────────────────────────────────────────────────
    report_context = await memory.retrieve(
        query="mission report",
        layers=["coordination"],
        top_k=100,
        agent="Supervisor",
        run_id="outcome_eval"
    )
    
    completion_events = []
    failed_events = []
    import re
    for m in report_context.get("matches", []):
        try:
            text = m.get("text") or m.get("message") or ""
            json_match_str = re.search(r"\{.*\}", text, re.DOTALL)
            if json_match_str:
                data = json.loads(json_match_str.group(0))
                if data.get("event") == "mission_completed":
                    completion_events.append(data)
                elif data.get("event") == "mission_failed":
                    failed_events.append(data)
        except:
            continue
    
    outcome = supervisor.evaluate_outcome(plan, completion_events, failed_events)
    console.print()
    RichLog.log("System", f"📊 Outcome: {outcome['criteria_met']}/{outcome['criteria_total']} criteria met — {'✅ SUCCESS' if outcome['success'] else '❌ FAILED'}", "system")
    for detail in outcome.get("details", []):
        RichLog.log("System", f"   {detail}", "system")
    console.print()
    
    metrics.log_outcome_evaluation(outcome["criteria_met"], outcome["criteria_total"])
    
    # ─────────────────────────────────────────────────────
    # Phase 6: Save Metrics
    # ─────────────────────────────────────────────────────
    metrics.print_summary()
    console.print()
    
    metrics_dir = os.path.join("results", run_id)
    os.makedirs(metrics_dir, exist_ok=True)
    metrics.save(os.path.join(metrics_dir, "metrics.json"))
    RichLog.log("System", f"Metrics saved to results/{run_id}/metrics.json", "system")
    
    RichLog.log("System", "Exiting.", "system")
    return metrics


if __name__ == "__main__":
    import uavsys.config 
    cfg = load_config()
    asyncio.run(run_mission(cfg.MISSION, run_id=cfg.RUN_ID))
