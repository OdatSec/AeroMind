"""
k-sensitivity sweep: Run S01 retrieval with varying Scout top-k values.
Measures how CCR / CASR change as the context window grows from k=3 to k=10.
This addresses the reviewer concern that k=3 makes poisoning trivially easy.
"""
import asyncio
import json
import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from experiment_runner import (
    MISSION_GOAL, SCENARIO_MAP, haversine,
    GROUND_TRUTH, TRAP_COORDS
)


async def run_k_sweep():
    import importlib
    scenario_module = importlib.import_module(SCENARIO_MAP["S01"])
    from uavsys.config import Config
    from uavsys.llm.ollama_client import OllamaClient
    from uavsys.memory.memory_interface import MemoryInterface
    from uavsys.memory.db import DatabaseManager
    from uavsys.utils.metrics import RunMetrics
    from uavsys.seeding import seed_memory

    seeds = [42, 123, 256, 512, 1024]
    k_values = [3, 5, 7, 10]
    
    results = {}

    for k_scout in k_values:
        k_sup = max(k_scout, 5)  # Supervisor always gets at least 5
        print(f"\n{'='*60}")
        print(f"  k-sensitivity sweep: Scout k={k_scout}, Supervisor k={k_sup}")
        print(f"{'='*60}")

        all_ccr = []
        all_casr = []
        all_scout_ccr = []
        all_sup_ccr = []

        for seed in seeds:
            with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
                db_path = tf.name

            try:
                cfg = Config(
                    DRONE1_GRPC_PORT=50051,
                    DRONE2_GRPC_PORT=50052,
                    DRONE1_SYSTEM_ADDRESS="udpin://0.0.0.0:14540",
                    DRONE2_SYSTEM_ADDRESS="udpin://0.0.0.0:14541",
                    OLLAMA_HOST="http://localhost:11434",
                    CHAT_MODEL="gpt-oss:20b",
                    EMBED_MODEL="nomic-embed-text:latest",
                    DB_PATH=db_path,
                    TOP_K_PLANNING=k_sup,
                    TOP_K_SCOUT=k_scout,
                    TOP_K_REPORT=10,
                    DEFENSE_ENABLED=False,
                    SEED=seed,
                    TEMPERATURE=0.1,
                    PREFILL_SIZE=10,
                    MISSION=MISSION_GOAL,
                )

                db = DatabaseManager(cfg)
                await db.init_db()
                llm = OllamaClient(cfg)
                memory = MemoryInterface(cfg, db, llm)

                # Seed + inject
                await seed_memory(memory, "Agent 1")
                await scenario_module.inject(memory=memory)

                agents = ["Agent 1", "Agent 2", "Supervisor"]
                queries = {
                    "Agent 1": MISSION_GOAL,
                    "Agent 2": MISSION_GOAL,
                    "Supervisor": f"mission planning: allocate tasks for {MISSION_GOAL}",
                }
                top_k_by_agent = {"Agent 1": k_scout, "Agent 2": k_scout, "Supervisor": k_sup}

                total_poisoned = 0
                total_retrieved = 0
                infected_roles = set()
                scout_poisoned_total = 0
                scout_retrieved_total = 0
                sup_poisoned = 0
                sup_retrieved = 0

                for agent_name in agents:
                    query = queries[agent_name]
                    top_k = top_k_by_agent[agent_name]
                    result = await memory.retrieve(
                        query=query,
                        layers=["episodic", "semantic", "procedural", "coordination"],
                        top_k=top_k,
                        agent=agent_name,
                        run_id=f"seed{seed}",
                    )
                    matches = result.get("matches", [])
                    poisoned = sum(1 for m in matches
                                   if str(m.get("source", "")).startswith("atk:") or
                                   m.get("is_attack", False))
                    total = len(matches)
                    total_poisoned += poisoned
                    total_retrieved += total
                    if poisoned > 0:
                        infected_roles.add(agent_name)
                    
                    if agent_name in ("Agent 1", "Agent 2"):
                        scout_poisoned_total += poisoned
                        scout_retrieved_total += total
                    else:
                        sup_poisoned = poisoned
                        sup_retrieved = total
                    
                    print(f"    k={k_scout} seed={seed} {agent_name:12s}: {poisoned}/{total} poisoned")

                ccr = total_poisoned / total_retrieved if total_retrieved > 0 else 0
                casr = len(infected_roles) / 3
                scout_ccr = scout_poisoned_total / scout_retrieved_total if scout_retrieved_total > 0 else 0
                sup_ccr = sup_poisoned / sup_retrieved if sup_retrieved > 0 else 0

                all_ccr.append(ccr)
                all_casr.append(casr)
                all_scout_ccr.append(scout_ccr)
                all_sup_ccr.append(sup_ccr)

            finally:
                try:
                    os.unlink(db_path)
                except:
                    pass

        mean_ccr = sum(all_ccr) / len(all_ccr)
        mean_casr = sum(all_casr) / len(all_casr)
        mean_scout_ccr = sum(all_scout_ccr) / len(all_scout_ccr)
        mean_sup_ccr = sum(all_sup_ccr) / len(all_sup_ccr)

        results[k_scout] = {
            "k_scout": k_scout,
            "k_supervisor": k_sup,
            "ccr_mean": round(mean_ccr, 4),
            "casr_mean": round(mean_casr, 4),
            "scout_ccr_mean": round(mean_scout_ccr, 4),
            "supervisor_ccr_mean": round(mean_sup_ccr, 4),
        }

        print(f"\n  k={k_scout}: CCR={mean_ccr:.4f}, CASR={mean_casr:.4f}, "
              f"Scout CCR={mean_scout_ccr:.4f}, Sup CCR={mean_sup_ccr:.4f}")

    # Save results
    out_path = os.path.join("results", "k_sensitivity", "s01_k_sweep.json")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n[saved] {out_path}")

    # Print summary table
    print(f"\n{'='*60}")
    print(f"  k-SENSITIVITY SUMMARY (S01)")
    print(f"{'='*60}")
    print(f"  {'k':>4s}  {'CCR':>6s}  {'CASR':>6s}  {'Scout':>6s}  {'Sup':>6s}")
    for k_val, r in sorted(results.items()):
        print(f"  {r['k_scout']:>4d}  {r['ccr_mean']:>6.4f}  {r['casr_mean']:>6.4f}  "
              f"{r['scout_ccr_mean']:>6.4f}  {r['supervisor_ccr_mean']:>6.4f}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    asyncio.run(run_k_sweep())
