import json
from ..config import Config
from ..llm.ollama_client import OllamaClient
from ..llm.prompts import SUPERVISOR_SYSTEM, REFLECTION_SYSTEM
from ..memory.memory_interface import MemoryInterface
from ..utils.richlog import RichLog
from .types import SupervisorOutput

class SupervisorAgent:
    def __init__(self, config: Config, llm: OllamaClient, memory: MemoryInterface):
        self.config = config
        self.llm = llm
        self.memory = memory

    async def plan_mission(self, user_mission: str) -> SupervisorOutput:
        RichLog.log("Supervisor", "Analyzing mission...", "supervisor")
        
        # 1. Retrieve relevant context
        # Policy: Supervisor SHOULD retrieve, but ONLY for coordination + episodic.
        context_data = await self.memory.retrieve(
            query=user_mission,
            layers=["coordination", "episodic", "semantic"],
            top_k=self.config.TOP_K_PLANNING,
            agent="Supervisor",
            run_id="planning"
        )
        context_str = json.dumps(context_data)
        
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM},
            {"role": "user", "content": f"Mission: {user_mission}\nContext: {context_str}"}
        ]

        response = await self.llm.chat(messages, temperature=self.config.TEMPERATURE)

        try:
            # Robust JSON extraction
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                cleaned_response = json_match.group(0)
            else:
                cleaned_response = response

            plan_dict = json.loads(cleaned_response)
            
            # Generate Mission ID
            import uuid
            mission_id = str(uuid.uuid4())
            plan_dict["mission_id"] = mission_id
            
            plan = SupervisorOutput(**plan_dict)
            
            # Store plan in coordination memory
            # Attach mission_id to message for filtering
            msg_content = {"content": f"Mission Plan: {json.dumps(plan_dict)}", "mission_id": mission_id}
            await self.memory.write_coordination(
                "Supervisor", "ALL", json.dumps(msg_content), intent="plan"
            )
            return plan
        except Exception as e:
            RichLog.error("Supervisor", f"Failed to parse plan: {e}")
            # Return empty or fallback?
            raise

    async def generate_report(self, mission_id: str, total_agents: int) -> str:
        """Generates a final mission report based on coordination and episodic memory."""
        RichLog.log("Supervisor", "Generating final report...", "supervisor")
        
        # 1. Retrieve coordination events (completion/failure)
        context = await self.memory.retrieve(
            query="mission report", 
            layers=["coordination"], 
            top_k=100,
            agent="Supervisor", 
            run_id="report",
            filters={"mission_id": mission_id}
        )
        
        matches = context.get("matches", [])
        
        completion_events = []
        failed_events = []

        for m in matches:
            try:
                data = m.get("_filter_data") or {}
                if not data:
                    text = m.get("text") or m.get("message")
                    if text and "{" in text:
                        import re
                        json_match = re.search(r"\{.*\}", text, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                
                event = data.get("event")
                if event == "mission_completed":
                    completion_events.append(data)
                elif event == "mission_failed":
                    failed_events.append(data)
            except:
                continue
        
        completed_count = len(completion_events)
        failed_count = len(failed_events)
        
        if failed_count > 0:
            status = "FAILED"
        elif completed_count >= total_agents:
            status = "COMPLETE"
        else:
            status = "IN_PROGRESS / INCOMPLETE"
        
        # 2. Retrieve episodic memory (agent actions, retrieval events)
        episodic_context = await self.memory.retrieve(
            query="goto_location takeoff hover retrieval target",
            layers=["episodic"],
            top_k=20,
            agent="Supervisor",
            run_id="report_episodic"
        )
        
        agent_actions = []
        for m in episodic_context.get("matches", []):
            text = m.get("text") or m.get("message") or ""
            agent = m.get("agent") or "Unknown"
            agent_actions.append({"agent": agent, "action": text[:200]})
        
        # 3. Build rich context for the LLM
        summary_ctx = {
            "mission_id": mission_id,
            "completed": completion_events,
            "failed": failed_events,
            "status": status,
            "agent_actions": agent_actions[:10]  # Top 10 most relevant
        }
        context_str = json.dumps(summary_ctx, indent=2)
        
        prompt = f"""
Context: {context_str}
Mission ID: {mission_id}
Status Logic: Found {completed_count} completions, {failed_count} failures. Expecting {total_agents} agents.
Calculated Status: {status}.

Based on the above, generate a NATURAL LANGUAGE mission report. Include:
1. **Mission Summary**: What was the mission objective.
2. **Agent Actions**: What each agent did (retrieved from memory, flew to coordinates, hovered, returned).
3. **Memory Usage**: Which memory layers were queried (semantic, episodic, procedural) and what was retrieved.
4. **Flight Results**: Where each drone flew and if it arrived successfully.
5. **Conclusion**: Overall mission status and any notable observations.

Write this as a clear, readable report — NOT as JSON.
"""
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm.chat(messages, temperature=0.7)
        RichLog.log("Supervisor", "Final Report Generated.", "supervisor")
        return response

    def evaluate_outcome(self, plan, completion_events: list, failed_events: list) -> dict:
        """
        Evaluate mission outcome against success criteria.
        Returns {criteria_met, criteria_total, success, details}.
        """
        criteria = getattr(plan, "success_criteria", []) or []
        criteria_total = len(criteria)
        
        if criteria_total == 0:
            # No criteria defined — use simple completion check
            all_done = len(completion_events) >= 2 and len(failed_events) == 0
            return {
                "criteria_met": 1 if all_done else 0,
                "criteria_total": 1,
                "success": all_done,
                "details": ["All agents completed" if all_done else "Not all agents completed"]
            }
        
        details = []
        criteria_met = 0
        
        # Build searchable text from all completion events
        completion_text = " ".join(
            json.dumps(e) for e in completion_events
        ).lower()
        
        completed_agents = {str(e.get("agent", "")).lower() for e in completion_events}
        failed_agents = {str(e.get("agent", "")).lower() for e in failed_events}
        all_completed = len(completed_agents) >= 2 and len(failed_agents) == 0
        
        for criterion in criteria:
            criterion_lower = criterion.lower()
            matched = False
            
            # Strategy 1: Check if criterion mentions a specific agent
            agent_specific = False
            for event in failed_events:
                agent_name = str(event.get("agent", "")).lower()
                if agent_name in criterion_lower:
                    agent_specific = True
                    matched = False
                    details.append(f"FAIL: {criterion} — {agent_name} failed")
                    break
            
            if not agent_specific:
                for event in completion_events:
                    agent_name = str(event.get("agent", "")).lower()
                    if agent_name in criterion_lower:
                        agent_specific = True
                        matched = True
                        break
            
            # Strategy 2: General criteria (mentions "both", "all", or no specific agent)
            if not agent_specific:
                general_keywords = ["both", "all agents", "completed", "returned", "investigation",
                                    "identified", "person", "car", "target"]
                keyword_hit = any(kw in criterion_lower for kw in general_keywords)
                
                if keyword_hit:
                    # General criterion — met if all agents completed
                    matched = all_completed
                    if not matched:
                        details.append(f"FAIL: {criterion} — not all agents completed")
                else:
                    # Check if criterion keywords exist in completion text
                    words = [w for w in criterion_lower.split() if len(w) > 3]
                    match_count = sum(1 for w in words if w in completion_text)
                    matched = match_count >= len(words) * 0.5  # 50% keyword match
            
            if matched:
                criteria_met += 1
                if f"FAIL: {criterion}" not in str(details):
                    details.append(f"PASS: {criterion}")
            elif f"FAIL: {criterion}" not in str(details):
                details.append(f"UNKNOWN: {criterion}")
        
        return {
            "criteria_met": criteria_met,
            "criteria_total": criteria_total,
            "success": criteria_met == criteria_total and len(failed_events) == 0,
            "details": details
        }

    async def consolidate_memory(self, agent_name: str, run_id: str = "consolidation"):
        """
        Reflection / Memory Consolidation (Inspired by Park et al. 2023).
        
        Retrieves recent episodic memories for an agent, asks the LLM to
        extract permanent semantic facts, and writes them back to semantic memory.
        
        This creates the Episodic → Semantic feedback loop:
          Raw Experience → Reflected Knowledge
        """
        RichLog.log("Supervisor", f"🔄 Consolidating memories for {agent_name}...", "supervisor")
        
        # 1. Retrieve recent episodic memories for this agent
        episodic_data = await self.memory.retrieve(
            query=f"mission observations and actions by {agent_name}",
            layers=["episodic"],
            top_k=15,
            agent="Supervisor",
            run_id=run_id,
            filters={"agent": agent_name}
        )
        
        matches = episodic_data.get("matches", [])
        if not matches:
            RichLog.log("Supervisor", f"   No episodic memories found for {agent_name}. Skipping.", "supervisor")
            return []
        
        # 2. Format episodic memories for the LLM and collect their IDs for provenance
        memory_text = ""
        episode_ids = []
        for i, m in enumerate(matches, 1):
            text = m.get("text") or m.get("content_json") or str(m)
            ts = m.get("ts", "unknown")
            memory_text += f"  [{i}] ({ts}) {text}\n"
            if m.get("id"):
                episode_ids.append(m["id"])
        
        prompt = f"""Agent: {agent_name}
Recent Episodic Memories (most relevant first):
{memory_text}

Analyze these execution logs and extract permanent semantic facts for future missions.
For each fact, include a "category" field with one of: "target", "environment", "operational".
Output strict JSON as specified."""

        messages = [
            {"role": "system", "content": REFLECTION_SYSTEM},
            {"role": "user", "content": prompt}
        ]
        
        # 3. Call LLM for reflection
        response = await self.llm.chat(messages, temperature=0.3)
        
        # 4. Parse and write semantic facts
        facts_written = []
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                facts = result.get("facts", [])
                summary = result.get("summary", "")
                
                for fact in facts:
                    key = fact.get("key", "unknown")
                    value = fact.get("value", "")
                    category = fact.get("category", "operational")
                    if category not in ("target", "environment", "operational"):
                        category = "operational"
                    if key and value:
                        # Use first episode ID as provenance (comma-separated if multiple)
                        prov_id = episode_ids[0] if episode_ids else None
                        await self.memory.write_semantic(
                            agent="Supervisor",
                            key=f"reflection:{key}",
                            value=value,
                            confidence=0.8,
                            source="reflection",
                            category=category,
                            source_episode_id=prov_id
                        )
                        facts_written.append(f"{key}: {value}")
                        RichLog.log("Supervisor", f"   💡 Fact [{category}]: {key} → {value}", "supervisor")
                
                if summary:
                    RichLog.log("Supervisor", f"   📝 Summary: {summary}", "supervisor")
            else:
                RichLog.log("Supervisor", f"   ⚠️  Could not parse reflection output.", "supervisor")
        except Exception as e:
            RichLog.log("Supervisor", f"   ⚠️  Reflection parse error: {e}", "supervisor")
        
        RichLog.log("Supervisor", f"   ✅ Consolidated {len(facts_written)} facts for {agent_name}.", "supervisor")
        return facts_written
