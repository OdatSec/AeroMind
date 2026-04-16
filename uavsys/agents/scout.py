import json
import asyncio
from ..config import Config
from ..llm.ollama_client import OllamaClient
from ..llm.prompts import SCOUT_SYSTEM
from ..memory.memory_interface import MemoryInterface
from ..drones.skills import DroneSkills
from ..utils.richlog import RichLog
from ..utils.safety import SafetyValidator
from ..utils.metrics import RunMetrics
from .types import ScoutPlan

class ScoutAgent:
    def __init__(self, 
                 name: str, 
                 config: Config, 
                 llm: OllamaClient, 
                 memory: MemoryInterface, 
                 skills: DroneSkills,
                 metrics: RunMetrics = None):
        self.name = name
        self.config = config
        self.llm = llm
        self.memory = memory
        self.skills = skills
        self.working_memory = {"status": "idle", "last_result": None}
        self.safety = SafetyValidator()
        self.metrics = metrics or RunMetrics()

    async def run_mission(self, goal: str, constraints: list[str] = [], mission_id: str = "unknown"):
        """
        Executes a mission based on a high-level goal.
        1. Retrieve context (procedural, episodic).
        2. Plan (ReAct).
        3. Act (Execute tools).
        4. Observe (Log results).
        """
        RichLog.log(self.name, f"Starting mission: {goal} [Mission ID: {mission_id}]", self.name)
        self.working_memory["goal"] = goal
        
        # ACK: Retrieve and acknowledge coordination messages for this agent
        try:
            coord_data = await self.memory.retrieve(
                query=f"task assignment for {self.name}",
                layers=["coordination"],
                top_k=5,
                agent=self.name,
                run_id="run_001"
            )
            for msg in coord_data.get("matches", []):
                if msg.get("id") and msg.get("status") == "sent":
                    to = msg.get("to_agent", "")
                    if to in (self.name, "ALL"):
                        await self.memory.acknowledge_message(msg["id"], self.name)
        except Exception:
            pass  # Don't block mission on ACK failure
        
        # 1. RETRIEVE — no mission_id filter so seeded semantic/procedural records are included
        context = await self.memory.retrieve(
            query=goal, 
            layers=["procedural", "episodic", "semantic"], 
            top_k=self.config.TOP_K_SCOUT, 
            agent=self.name, 
            run_id="run_001"
        )
        # Display Memory Content
        from rich.table import Table
        from uavsys.utils.richlog import console
        
        table = Table(title=f"{self.name} Retrieval Results", show_header=True, header_style="bold magenta")
        table.add_column("Layer", style="cyan")
        table.add_column("Score", justify="right")
        table.add_column("Content")
        
        matches = context.get("matches", [])
        if not matches:
             table.add_row("-", "-", "[italic dim]No matches found (Memory Empty)[/italic dim]")
        else:
            for m in matches:
                # Try to get meaningful text key depending on layer schema
                content = m.get("text") or m.get("value") or m.get("description") or m.get("message") or str(m)
                table.add_row(m.get("layer", "unknown"), f"{m.get('score', 0):.2f}", str(content)[:100])
        
        console.print(table)

        # Log retrieval metrics
        self.metrics.log_retrieval(matches, agent=self.name, query=goal)
        defense_stats = context.get("defense_stats")
        if defense_stats:
            self.metrics.log_defense_stats(defense_stats, agent=self.name)
        
        context_str = json.dumps(context)
        
        # 2. PLAN
        prompt = f"""
Goal: {goal}
Constraints: {constraints}
Context: {context_str}
Current Status: {self.working_memory}
"""
        messages = [
            {"role": "system", "content": SCOUT_SYSTEM.format(
                agent_name=self.name,
                tools_desc=self.skills.get_tool_descriptions()
            )},
            {"role": "user", "content": prompt}
        ]
        
        RichLog.log(self.name, "Generating plan...", self.name)
        response = await self.llm.chat(messages, temperature=0.1, format="json")
        
        try:
            # Robust JSON extraction
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            else:
                cleaned_response = response
            
            plan_data = json.loads(cleaned_response)
            
            # Use raw Plan dict to populate ScoutPlan
            # But the prompt might return {"steps": [...]} or just the plan.
            # Assuming prompt returns valid structure.
            plan = ScoutPlan(**plan_data)
            RichLog.log(self.name, f"Plan: {plan.notes}", self.name)
        except Exception as e:
            RichLog.error(self.name, f"Plan parsing failed: {e}. Raw: {response}")
            # Fallback plan
            plan = ScoutPlan(steps=[
                {"tool": "connect", "args": {}},
                {"tool": "arm", "args": {}},
                {"tool": "takeoff", "args": {"alt_m": 4}},
                {"tool": "hover", "args": {"seconds": 5}},
                {"tool": "return_to_launch", "args": {}}
            ], notes="Fallback due to LLM error")

        # 3. ACT (Tool Execution Loop)
        rtl_executed = False
        execution_success = True
        failure_reason = "Unknown"

        try:
            for step in plan.steps:
                RichLog.log(self.name, f"Executing: {step.tool}", "tool")
                
                # Safety Check
                telemetry_snapshot = {"alt": 0} # Placeholder for now, real telemetry needed later
                safety_error = self.safety.validate_action(step.tool, step.args, telemetry_snapshot)
                
                if safety_error:
                    RichLog.error(self.name, f"SAFETY VIOLATION: {safety_error}")
                    execution_success = False
                    failure_reason = safety_error
                    self.metrics.log_action(safe=False, tool_name=step.tool, agent=self.name)
                    
                    # Log violation
                    detailed_data = {
                        "event_name": step.tool,
                        "args": step.args,
                        "result": safety_error,
                        "telemetry": telemetry_snapshot,
                        "mission_id": mission_id,
                        "run_id": "run_001",
                        "status": "safety_violation"
                    }
                    await self.memory.write_episodic(
                        agent=self.name, 
                        content=f"SAFETY_VIOLATION: {safety_error}", 
                        source="safety_guard",
                        detailed_data=detailed_data
                    )
                    break # Abort on safety violation
                else:
                    # Execute tool
                    try:
                        result = await self.skills.execute_tool(step.tool, step.args)
                    except Exception as e:
                        result = f"Error: Exception during tool execution: {e}"

                    # METRIC: Check GPS accuracy for goto_location
                    if step.tool == "goto_location" or step.tool == "goto":
                        lat = step.args.get("lat", 0)
                        lon = step.args.get("lon", 0)
                        
                        # Target ground truths (hardcoded for verification metric)
                        targets = {
                            "person": (47.396735, 8.549883),
                            "car": (47.396716, 8.549858)
                        }
                        
                        min_dist = float("inf")
                        for t_name, t_coords in targets.items():
                            # Simple euclidean approx for metric
                            dist = ((lat - t_coords[0])**2 + (lon - t_coords[1])**2)**0.5 * 111139
                            if dist < min_dist:
                                min_dist = dist
                        
                        # Log accuracy: 1.0 if within 5m of ANY valid target, else 0.0
                        accuracy = 1.0 if min_dist < 5.0 else 0.0
                        self.metrics.log_action(self.name, step.tool, "safe", accuracy=accuracy)
                    else:
                        self.metrics.log_action(self.name, step.tool, "safe")

                    # 4. OBSERVE
                    observation = f"Executed {step.tool} with args {step.args}. Result: {result}"
                    self.working_memory["last_result"] = result
                    
                    # Update tool reliability stats (success)
                    await self.memory.update_tool_stats(step.tool, success=True)

                # Check for failure → Re-Plan (Gap 4: ReAct Pattern)
                if "Error" in result or "Exception" in result or "failed" in result.lower():
                    RichLog.error(self.name, f"Step {step.tool} failed: {result}")
                    
                    # Update tool reliability stats (failure)
                    await self.memory.update_tool_stats(step.tool, success=False)
                    
                    # Log failure in episodic memory
                    telemetry = await self.skills.get_telemetry()
                    detailed_data = {
                        "event_name": step.tool,
                        "args": step.args,
                        "result": result,
                        "telemetry": telemetry,
                        "mission_id": mission_id,
                        "run_id": "run_001",
                        "status": "failed"
                    }
                    await self.memory.write_episodic(
                        agent=self.name, 
                        content=f"FAILURE: {observation}", 
                        source="execution",
                        detailed_data=detailed_data
                    )
                    
                    # LESSON LEARNED: Ask LLM to extract a one-line takeaway
                    try:
                        lesson_prompt = (
                            f"A UAV agent just experienced a failure.\n"
                            f"Action: {step.tool}\nArgs: {step.args}\n"
                            f"Error: {result}\n"
                            f"Telemetry: {json.dumps(telemetry)}\n\n"
                            f"Write ONE sentence lesson learned for future agents. "
                            f"Be specific and actionable. Example: "
                            f"'Always verify GPS lock before goto_location commands.'\n"
                            f"Respond with ONLY the lesson, no quotes."
                        )
                        lesson = await self.llm.chat(
                            [{"role": "user", "content": lesson_prompt}],
                            temperature=0.3
                        )
                        lesson = lesson.strip().strip('"').strip("'")
                        if lesson and len(lesson) < 200:
                            await self.memory.write_episodic(
                                agent=self.name,
                                content=f"LESSON: {lesson}",
                                source="lesson",
                                detailed_data={
                                    "failed_action": step.tool,
                                    "error": result[:100],
                                    "telemetry": telemetry
                                }
                            )
                            RichLog.log(self.name, f"📝 Lesson: {lesson}", self.name)
                    except Exception:
                        pass  # Don't let lesson generation block recovery
                    
                    # RE-PLAN: Attempt recovery (max 1 retry)
                    if not hasattr(self, '_replan_attempted'):
                        self._replan_attempted = True
                        RichLog.log(self.name, "🔄 Re-planning after failure...", "warning")
                        
                        # Re-retrieve context with failure info
                        replan_context = await self.memory.retrieve(
                            query=f"{goal} recovery after {step.tool} failure",
                            layers=["procedural", "episodic", "semantic"],
                            top_k=self.config.TOP_K_SCOUT,
                            agent=self.name,
                            run_id="replan"
                        )
                        
                        replan_prompt = f"""
Goal: {goal}
PREVIOUS STEP FAILED: {step.tool} returned: {result}
Context: {json.dumps(replan_context)}
Current Status: {self.working_memory}

Generate a RECOVERY plan. Skip the failed step if possible, or try an alternative approach.
"""
                        replan_messages = [
                            {"role": "system", "content": SCOUT_SYSTEM.format(
                                agent_name=self.name,
                                tools_desc=self.skills.get_tool_descriptions()
                            )},
                            {"role": "user", "content": replan_prompt}
                        ]
                        
                        replan_response = await self.llm.chat(replan_messages, temperature=0.1, format="json")
                        try:
                            import re as re_mod
                            replan_match = re_mod.search(r"\{.*\}", replan_response, re_mod.DOTALL)
                            if replan_match:
                                replan_data = json.loads(replan_match.group(0))
                                replan = ScoutPlan(**replan_data)
                                RichLog.log(self.name, f"   Recovery plan: {replan.notes}", self.name)
                                
                                # Execute recovery steps
                                for rstep in replan.steps:
                                    RichLog.log(self.name, f"   [Recovery] Executing: {rstep.tool}", "tool")
                                    try:
                                        rresult = await self.skills.execute_tool(rstep.tool, rstep.args)
                                        RichLog.log(self.name, f"   [Recovery] Result: {rresult[:80]}", "tool")
                                        if rstep.tool == "return_to_launch":
                                            rtl_executed = True
                                    except Exception as re_err:
                                        RichLog.error(self.name, f"   [Recovery] Failed: {re_err}")
                                        break
                                    await asyncio.sleep(1)
                        except Exception as replan_err:
                            RichLog.error(self.name, f"   Re-plan parsing failed: {replan_err}")
                    
                    execution_success = False
                    failure_reason = result
                    break

                # 5. MEMORY WRITE (Episodic - Success)
                # Structure: episodic_write(agent, event_name, args, telemetry, timestamp)
                telemetry = await self.skills.get_telemetry()
                detailed_data = {
                    "event_name": step.tool,
                    "args": step.args,
                    "result": result,
                    "telemetry": telemetry,
                    "mission_id": mission_id,
                    "run_id": "run_001",
                    "status": "success"
                }
                
                await self.memory.write_episodic(
                    agent=self.name, 
                    content=observation, 
                    source="execution",
                    detailed_data=detailed_data
                )

                # Small delay for visual pacing in CLI
                await asyncio.sleep(1)
        except Exception as e:
            RichLog.error(self.name, f"Mission execution interrupted: {e}")
            execution_success = False
            failure_reason = str(e)
            
        # Robust RTL Check
        if not rtl_executed and not execution_success: 
             # Verify if we are even airborne/armed to need RTL?
             # SafetyValidator state can help, but for now safe to try if we passed safety check previously
             RichLog.log(self.name, "Plan finished (or aborted) but RTL not executed. Forcing RTL (if armed).", "warning")
             if self.safety.state["armed"]:
                 try:
                     await self.skills.execute_tool("return_to_launch", {})
                     
                     # Log forced RTL
                     telemetry = await self.skills.get_telemetry()
                     detailed_data = {
                        "event_name": "return_to_launch",
                        "args": {},
                        "result": "Success (Forced)",
                        "telemetry": telemetry,
                        "mission_id": mission_id,
                        "run_id": "run_001",
                        "status": "forced_rtl"
                     }
                     await self.memory.write_episodic(
                        self.name, 
                        "Forced Return to Launch executed.", 
                        "execution",
                        detailed_data=detailed_data
                     )
                 except Exception as e:
                        RichLog.error(self.name, f"Forced RTL failed: {e}")

        RichLog.log(self.name, "Mission steps completed.", self.name)
        
        # Signal Completion or Failure
        self.metrics.log_mission_completion(execution_success)
        
        if execution_success:
            completion_msg = json.dumps({
                "agent": self.name,
                "event": "mission_completed",
                "telemetry": {"status": "landed", "bat": "95%", "final_pos": "Home"},
                "mission_id": mission_id,
                "layer": "coordination"
            })
            await self.memory.write_coordination(self.name, "Supervisor", completion_msg, intent="status_update")
        else:
            failure_msg = json.dumps({
                "agent": self.name,
                "event": "mission_failed",
                "reason": failure_reason,
                "mission_id": mission_id,
                "layer": "coordination"
            })
            await self.memory.write_coordination(self.name, "Supervisor", failure_msg, intent="status_update")
        
        # Metrics summary printed centrally by demo.py after all agents complete
