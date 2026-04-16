import json
import logging
from typing import List, Dict, Any, Optional
from ..config import Config
from ..llm.ollama_client import OllamaClient
from .db import DatabaseManager
from .retrieval import RetrievalEngine
from .defense import DefenseLayer
from ..utils.richlog import RichLog
from ..utils.timeutil import now_iso

class MemoryInterface:
    def __init__(self, config: Config, db_manager: DatabaseManager, llm_client: OllamaClient):
        self.config = config
        self.db = db_manager
        self.llm = llm_client

    async def retrieve(self, *, query: str, layers: list[str], top_k: int, agent: str, run_id: str, filters: Optional[Dict[str, Any]] = None, defense_cfg: Optional[dict] = None) -> dict:
        """
        Single choke-point for retrieval.
        filters: Dict of field/value pairs to exact-match against item content (e.g. {"mission_id": "123"}).
        """
        RichLog.memory_event(agent, "RETRIEVE_START", f"Query: '{query}' Layers: {layers} Filters: {filters}")

        # 1. Embed Query
        try:
            query_embedding = (await self.llm.embed([query]))[0]
        except Exception as e:
            RichLog.error(agent, f"Embedding failed: {e}")
            return {"results": [], "error": str(e)}

        results = {}
        
        async with self.db.get_connection() as conn:
            # 2. Fetch candidates
            async def fetch_layer(layer_name: str, table_name: str):
                sql = f"""
                    SELECT t.*, e.vector_json 
                    FROM {table_name} t
                    JOIN embeddings e ON t.embed_id = e.id
                    WHERE t.layer = ?
                """
                cursor = await conn.execute(sql, (layer_name,))
                rows = await cursor.fetchall()
                column_names = [description[0] for description in cursor.description]
                items = []
                for row in rows:
                    item = dict(zip(column_names, row))
                    if item.get("vector_json"):
                        item["vector"] = json.loads(item["vector_json"])
                    
                    # Normalization for filtering
                    item["_filter_data"] = {}
                    if "content_json" in item and item["content_json"]:
                        try:
                            item["_filter_data"].update(json.loads(item["content_json"]))
                        except: pass
                    if "message" in item:
                         try:
                             item["_filter_data"].update(json.loads(item["message"]))
                         except:
                             item["_filter_data"]["message"] = item["message"]
                    
                    items.append(item)
                return items

            all_candidates = []
            for layer in layers:
                if layer in ["episodic", "semantic", "procedural", "coordination"]:
                    table = layer if layer != "coordination" else "coordination"
                    items = await fetch_layer(layer, table)
                    all_candidates.extend(items)

            # Filter candidates 
            filtered_candidates = []
            filter_stats = {"total_candidates": len(all_candidates), "kept": 0, "filtered_out": 0}
            
            if filters:
                for item in all_candidates:
                    match = True
                    for k, v in filters.items():
                        # Check top-level item dict then _filter_data
                        val = item.get(k) or item.get("_filter_data", {}).get(k)
                        if str(val) != str(v): 
                            match = False
                            break
                    if match:
                        filtered_candidates.append(item)
                    else:
                        filter_stats["filtered_out"] += 1
            else:
                filtered_candidates = all_candidates

            filter_stats["kept"] = len(filtered_candidates)

            # 3. Rank with configurable composite weights
            ranked = RetrievalEngine.rank_items(
                query_embedding, filtered_candidates,
                top_k * 3 if self.config.DEFENSE_ENABLED else top_k,
                alpha=getattr(self.config, 'RETRIEVAL_ALPHA', 0.6),
                beta=getattr(self.config, 'RETRIEVAL_BETA', 0.2),
                gamma=getattr(self.config, 'RETRIEVAL_GAMMA', 0.2)
            )

            # 4. Defense Pipeline (if enabled)
            defense_stats = None
            if self.config.DEFENSE_ENABLED and ranked:
                import time as _time
                _t0 = _time.perf_counter()
                ranked, defense_stats = DefenseLayer.apply_defense_pipeline(
                    ranked, self.config, agent=agent, top_k=top_k
                )
                defense_stats["latency_ms"] = round((_time.perf_counter() - _t0) * 1000, 2)

            results["matches"] = ranked
            if defense_stats:
                results["defense_stats"] = defense_stats
            
            # Log retrieval
            if not ranked:
                RichLog.memory_event(agent, "RETRIEVE_DONE", f"No matches. Stats: {filter_stats}")
            else:
                RichLog.memory_event(agent, "RETRIEVE_DONE", f"Found {len(ranked)} matches. Stats: {filter_stats}")

            # 4. Log to JSONL
            try:
                import os
                log_dir = "logs"
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f"retrieval_{run_id}.jsonl")
                
                log_entry = {
                    "ts": now_iso(),
                    "agent": agent,
                    "query": query,
                    "layers": layers,
                    "filters": filters,
                    "top_k": top_k,
                    "filter_stats": filter_stats,
                    "returned_items": []
                }
                
                for item in ranked:
                    log_item = {
                        "layer": item.get("layer", "unknown"),
                        "score": item.get("score", 0.0),
                        "content": str(item.get("text") or item.get("value") or item.get("description") or item.get("message") or "")[:100],
                        "source": item.get("source", "unknown"),
                    }
                    log_entry["returned_items"].append(log_item)
                
                with open(log_file, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
            except Exception as e:
                RichLog.error(agent, f"Logging retrieval failed: {e}")

            return results

    async def _insert_embedding(self, conn, text: str) -> int:
        """Helper to compute and insert embedding, returning its ID."""
        vector = (await self.llm.embed([text]))[0]
        vector_json = json.dumps(vector)
        cursor = await conn.execute(
            "INSERT INTO embeddings (ts, model, text, vector_json) VALUES (?, ?, ?, ?) RETURNING id",
            (now_iso(), self.config.EMBED_MODEL, text, vector_json)
        )
        row = await cursor.fetchone()
        return row[0]

    @staticmethod
    def _compute_importance(content: str) -> float:
        """
        Compute importance score for a memory item using keyword heuristics.
        Inspired by Park et al. (2023) importance scoring.
        Returns 0.1-1.0.
        """
        content_lower = content.lower()
        
        # High importance keywords (0.8-1.0)
        high_keywords = ["target", "confirmed", "person", "car", "obstacle", "threat",
                         "emergency", "safety", "violation", "mission_completed", "failed",
                         "gps", "coordinates", "location", "detected"]
        # Low importance keywords (0.2-0.3)
        low_keywords = ["battery", "connected", "armed", "takeoff", "hover",
                        "telemetry", "heartbeat", "ping"]
        
        high_count = sum(1 for kw in high_keywords if kw in content_lower)
        low_count = sum(1 for kw in low_keywords if kw in content_lower)
        
        if high_count >= 2:
            return 0.9
        elif high_count >= 1:
            return 0.7
        elif low_count >= 2:
            return 0.2
        elif low_count >= 1:
            return 0.3
        else:
            return 0.5  # Neutral

    async def write_episodic(self, agent: str, content: str, source: str = "agent", detailed_data: Optional[dict] = None, is_attack: bool = False):
        """
        detailed_data: Optional dictionary containing telemetry, tool args, etc.
        is_attack: If True, prefix source with 'atk:' for CCR measurement.
        """
        if is_attack:
            source = f"atk:{source}"
        text_for_embed = content
        
        # Compute importance score
        importance = self._compute_importance(content)
        
        # Prepare full content JSON
        content_obj = {"content": content}
        if detailed_data:
            content_obj.update(detailed_data)
        
        content_json_str = json.dumps(content_obj)

        # HMAC signing if defense enabled
        hmac_sig = None
        if self.config.DEFENSE_ENABLED and self.config.DEFENSE_PROVENANCE_SECRET and not is_attack:
            hmac_sig = DefenseLayer.sign_record(content, agent, self.config.DEFENSE_PROVENANCE_SECRET)

        async with self.db.get_connection() as conn:
            embed_id = await self._insert_embedding(conn, text_for_embed)
            await conn.execute(
                """INSERT INTO episodic 
                   (ts, agent, layer, content_json, text, source, trust, importance, attack_tag, embed_id)
                   VALUES (?, ?, 'episodic', ?, ?, ?, 1.0, ?, ?, ?)""",
                (now_iso(), agent, content_json_str, content, source, importance, hmac_sig, embed_id)
            )
            await conn.commit()
        RichLog.memory_event(agent, "WRITE_EPISODIC", f"[imp={importance:.1f}] {content[:50]}..." + (" [SIGNED]" if hmac_sig else ""))

        # Log to JSONL
        try:
            import os
            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            run_id = detailed_data.get("run_id", "run_001") if detailed_data else "run_001"
            log_file = os.path.join(log_dir, f"episodic_{run_id}.jsonl")
            
            log_entry = {
                "ts": now_iso(),
                "agent": agent,
                "event": getattr(detailed_data, "get", lambda x,y: None)("event_name", "unknown") if detailed_data else "unknown",
                "content": content,
                "details": detailed_data or {}
            }
            
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            RichLog.error(agent, f"Logging episodic failed: {e}")

    async def write_semantic(self, agent: str, key: str, value: str, confidence: float = 1.0, source: str = "agent", is_attack: bool = False, category: str = None, source_episode_id: int = None):
        text = f"{key}: {value}"
        if is_attack:
            source = f"atk:{source}"
        
        # Compute importance from content
        importance = self._compute_importance(f"{key} {value}")
        
        hmac_sig = None
        if self.config.DEFENSE_ENABLED and self.config.DEFENSE_PROVENANCE_SECRET and not is_attack:
            hmac_sig = DefenseLayer.sign_record(value, agent, self.config.DEFENSE_PROVENANCE_SECRET)
        async with self.db.get_connection() as conn:
            embed_id = await self._insert_embedding(conn, text)
            await conn.execute(
                """INSERT INTO semantic 
                   (ts, agent, layer, key, value, confidence, source_episode_id, category, source, trust, importance, attack_tag, embed_id)
                   VALUES (?, ?, 'semantic', ?, ?, ?, ?, ?, ?, 1.0, ?, ?, ?)""",
                (now_iso(), agent, key, value, confidence, source_episode_id, category, source, importance, hmac_sig, embed_id)
            )
            await conn.commit()
        cat_tag = f" [{category}]" if category else ""
        prov_tag = f" (from ep:{source_episode_id})" if source_episode_id else ""
        RichLog.memory_event(agent, "WRITE_SEMANTIC", f"[imp={importance:.1f}]{cat_tag}{prov_tag} {key}={value}" + (" [SIGNED]" if hmac_sig else ""))

    # Privileged sources that may write to procedural memory
    PROCEDURAL_ALLOWED_SOURCES = ("System", "Doctrine", "SafetyProtocol")

    async def write_procedural(self, agent: str, name: str, description: str, steps_json: str, source: str = "agent", is_attack: bool = False):
        # IMMUTABILITY: Only privileged sources may write procedural knowledge
        if not is_attack and source not in self.PROCEDURAL_ALLOWED_SOURCES:
            RichLog.error(agent, f"BLOCKED: Procedural write denied for source='{source}' (allowed: {self.PROCEDURAL_ALLOWED_SOURCES})")
            return
        
        text = f"{name}: {description}"
        if is_attack:
            source = f"atk:{source}"
        hmac_sig = None
        if self.config.DEFENSE_ENABLED and self.config.DEFENSE_PROVENANCE_SECRET and not is_attack:
            hmac_sig = DefenseLayer.sign_record(description, agent, self.config.DEFENSE_PROVENANCE_SECRET)
        async with self.db.get_connection() as conn:
            embed_id = await self._insert_embedding(conn, text)
            await conn.execute(
                """INSERT INTO procedural 
                   (ts, agent, layer, name, description, steps_json, source, trust, attack_tag, embed_id)
                   VALUES (?, ?, 'procedural', ?, ?, ?, ?, 1.0, ?, ?)""",
                (now_iso(), agent, name, description, steps_json, source, hmac_sig, embed_id)
            )
            await conn.commit()
        RichLog.memory_event(agent, "WRITE_PROCEDURAL", f"{name}" + (" [SIGNED]" if hmac_sig else ""))

    async def update_tool_stats(self, tool_name: str, success: bool):
        """Increment success/fail counter for a tool. Creates row if first use."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                """INSERT INTO tool_stats (tool_name, success_count, fail_count, total_executions, last_used)
                   VALUES (?, ?, ?, 1, ?)
                   ON CONFLICT(tool_name) DO UPDATE SET
                     success_count = success_count + ?,
                     fail_count = fail_count + ?,
                     total_executions = total_executions + 1,
                     last_used = ?""",
                (tool_name, int(success), int(not success), now_iso(),
                 int(success), int(not success), now_iso())
            )
            await conn.commit()

    async def get_tool_stats(self) -> list:
        """Return tool reliability stats for planning context."""
        async with self.db.get_connection() as conn:
            cursor = await conn.execute(
                "SELECT tool_name, success_count, fail_count, total_executions, last_used FROM tool_stats ORDER BY total_executions DESC"
            )
            rows = await cursor.fetchall()
            return [
                {
                    "tool": r[0],
                    "success": r[1],
                    "fail": r[2],
                    "total": r[3],
                    "reliability": round(r[1] / r[3] * 100, 1) if r[3] > 0 else 0,
                    "last_used": r[4]
                }
                for r in rows
            ]

    async def write_coordination(self, agent: str, to_agent: str, message: str, is_attack: bool = False, intent: str = None, spoof_from_agent: str = None):
        """
        intent: Structured routing tag — one of: plan, status_update, query, warning.
        spoof_from_agent: If is_attack=True and this is set, store this value as
                          from_agent instead of the actual agent. This simulates
                          the paper's threat model where a compromised Scout
                          impersonates Supervisor (S04, S11).
        """
        VALID_INTENTS = ("plan", "status_update", "query", "warning")
        if intent and intent not in VALID_INTENTS:
            intent = None  # Silently drop invalid intents
        
        # Determine the from_agent for DB storage
        effective_from = agent
        if is_attack and spoof_from_agent:
            effective_from = spoof_from_agent
        
        text = f"Message from {effective_from} to {to_agent}: {message}"
        atk_source = f"atk:{agent}" if is_attack else agent
        hmac_sig = None
        if self.config.DEFENSE_ENABLED and self.config.DEFENSE_PROVENANCE_SECRET and not is_attack:
            hmac_sig = DefenseLayer.sign_record(message, agent, self.config.DEFENSE_PROVENANCE_SECRET)
        async with self.db.get_connection() as conn:
            embed_id = await self._insert_embedding(conn, text)
            await conn.execute(
                """INSERT INTO coordination 
                   (ts, agent, layer, from_agent, to_agent, intent, message, status, source, trust, attack_tag, embed_id)
                   VALUES (?, ?, 'coordination', ?, ?, ?, ?, 'sent', ?, 1.0, ?, ?)""",
                (now_iso(), agent, effective_from, to_agent, intent, message, atk_source, hmac_sig, embed_id)
            )
            await conn.commit()
        intent_tag = f" [{intent}]" if intent else ""
        RichLog.memory_event(agent, "WRITE_COORDINATION", f"To {to_agent}:{intent_tag} {message}" + (" [SIGNED]" if hmac_sig else ""))

    async def acknowledge_message(self, message_id: int, by_agent: str):
        """Mark a coordination message as 'received' by the agent."""
        async with self.db.get_connection() as conn:
            await conn.execute(
                "UPDATE coordination SET status = 'received' WHERE id = ?",
                (message_id,)
            )
            await conn.commit()
        RichLog.memory_event(by_agent, "ACK_COORDINATION", f"Message #{message_id} acknowledged")
