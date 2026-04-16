import os
import argparse
import yaml
from dataclasses import dataclass

@dataclass
class Config:
    DRONE1_GRPC_PORT: int
    DRONE2_GRPC_PORT: int
    DRONE1_SYSTEM_ADDRESS: str
    DRONE2_SYSTEM_ADDRESS: str
    OLLAMA_HOST: str
    CHAT_MODEL: str
    EMBED_MODEL: str
    DB_PATH: str
    TOP_K_PLANNING: int
    TOP_K_SCOUT: int
    TOP_K_REPORT: int
    DEFENSE_ENABLED: bool
    SEED: int
    TEMPERATURE: float
    PREFILL_SIZE: int
    # Defense parameters
    DEFENSE_SIM_THRESHOLD: float = 0.35
    DEFENSE_MAX_PER_SOURCE: int = 2
    DEFENSE_TRUST_WEIGHT: float = 0.3
    DEFENSE_PROVENANCE_SECRET: str = ""
    MISSION: str = ""
    RUN_ID: str = "run_001"
    RICH_MEMORY: bool = False
    NO_SEED_TARGETS: bool = False
    KEEP_MEMORY: bool = False
    # Retrieval weights (α, β, γ)
    RETRIEVAL_ALPHA: float = 0.6
    RETRIEVAL_BETA: float = 0.2
    RETRIEVAL_GAMMA: float = 0.2

def load_config() -> Config:
    # Load defaults from YAML
    yaml_config = {}
    try:
        with open("run_config.yaml", "r") as f:
            yaml_config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        pass

    retrieval = yaml_config.get("retrieval", {})

    # Defaults
    default_drone1_grpc = 50051
    default_drone2_grpc = 50052
    default_drone1_sys = "udpin://0.0.0.0:14540"
    default_drone2_sys = "udpin://0.0.0.0:14541"
    
    default_ollama = "http://localhost:11434"
    default_chat = "gpt-oss:20b"
    default_embed = "nomic-embed-text:latest"
    default_db = "./data/memory.db"
    
    default_topk_planning = retrieval.get("top_k_planning", 5)
    default_topk_scout = retrieval.get("top_k_scout", 3)
    default_topk_report = retrieval.get("top_k_report", 10)
    
    default_defense = yaml_config.get("defense_enabled", False)
    default_seed = yaml_config.get("seed", 42)
    default_temp = 0.2
    default_prefill = retrieval.get("prefill_size", 10)
    default_mission = yaml_config.get("mission", "Search sector A and B")

    # Defense parameters from YAML
    defense_cfg = yaml_config.get("defense", {})
    default_sim_threshold = defense_cfg.get("similarity_threshold", 0.35)
    default_max_per_source = defense_cfg.get("max_results_per_source", 2)
    default_trust_weight = defense_cfg.get("trust_weight", 0.3)
    default_provenance_secret = defense_cfg.get("provenance_secret", "")

    # CLI Args override Env Vars which override Defaults
    parser = argparse.ArgumentParser(
        description="Multi-Agent UAV Memory System — Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # E1: Memory-Driven Navigation
  python -m uavsys.demo --model llama3.1:latest --run-id e1_nav

  # E5: Reflection Verification
  python -m uavsys.demo --model gpt-oss:20b --run-id e5_reflect

  # E6: Retrieval Weight Comparison
  python -m uavsys.demo --model llama3.1:latest --run-id e6_cosine --retrieval-weights 1.0,0.0,0.0
  python -m uavsys.demo --model llama3.1:latest --run-id e6_balanced --retrieval-weights 0.6,0.2,0.2

  # E7: Model Comparison
  python -m uavsys.demo --model llama3.1:latest --run-id e7_llama
  python -m uavsys.demo --model gpt-oss:20b --run-id e7_gptoss

  # Control: No target seeding
  python -m uavsys.demo --model llama3.1:latest --run-id e1_control --no-seed-targets
        """
    )
    
    # ── Infrastructure ──
    parser.add_argument("--drone1-grpc", type=int, default=os.getenv("DRONE1_GRPC", default_drone1_grpc))
    parser.add_argument("--drone2-grpc", type=int, default=os.getenv("DRONE2_GRPC", default_drone2_grpc))
    parser.add_argument("--drone1-sys", type=str, default=os.getenv("DRONE1_SYSTEM", default_drone1_sys))
    parser.add_argument("--drone2-sys", type=str, default=os.getenv("DRONE2_SYSTEM", default_drone2_sys))
    
    # ── LLM Configuration ──
    parser.add_argument("--model", type=str, default=os.getenv("CHAT_MODEL", default_chat),
                        help="Exact Ollama model name (e.g. llama3.1:latest, gpt-oss:20b)")
    parser.add_argument("--ollama", type=str, default=os.getenv("OLLAMA_HOST", default_ollama),
                        help="Ollama API host URL")
    parser.add_argument("--embed", type=str, default=os.getenv("EMBED_MODEL", default_embed),
                        help="Embedding model name")
    parser.add_argument("--db", type=str, default=os.getenv("DB_PATH", default_db),
                        help="Path to SQLite memory database")
    
    # ── Experiment Configuration ──
    parser.add_argument("--run-id", type=str, default="run_001",
                        help="Experiment run ID (used for results directory)")
    parser.add_argument("--mission", type=str, default=default_mission,
                        help="Mission description text")
    parser.add_argument("--rich-memory", action="store_true",
                        help="Seed memory with rich/noisy data (15+ records) for stress testing")
    parser.add_argument("--no-seed-targets", action="store_true",
                        help="Skip target seeding — tests behavior without memory (E1 control)")
    parser.add_argument("--defense", action="store_true",
                        help="Enable defense layer (HMAC, filtering)")
    parser.add_argument("--retrieval-weights", type=str, default=None,
                        help="Retrieval scoring weights as α,β,γ (e.g. 0.6,0.2,0.2)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show detailed debug output (memory events, raw plans)")
    parser.add_argument("--keep-memory", action="store_true",
                        help="Do NOT clear memory DB before run (E5: test reflection persistence)")

    args, _ = parser.parse_known_args()

    # Parse retrieval weights if provided
    alpha, beta, gamma = 0.6, 0.2, 0.2
    if args.retrieval_weights:
        try:
            parts = [float(x.strip()) for x in args.retrieval_weights.split(",")]
            if len(parts) == 3:
                alpha, beta, gamma = parts
        except ValueError:
            pass

    # Set verbosity
    from .utils.richlog import set_verbosity
    set_verbosity(2 if args.verbose else 1)

    # CLI flag overrides YAML
    defense_enabled = args.defense if args.defense else default_defense

    return Config(
        DRONE1_GRPC_PORT=args.drone1_grpc,
        DRONE2_GRPC_PORT=args.drone2_grpc,
        DRONE1_SYSTEM_ADDRESS=args.drone1_sys,
        DRONE2_SYSTEM_ADDRESS=args.drone2_sys,
        OLLAMA_HOST=args.ollama,
        CHAT_MODEL=args.model,  # --model is the primary arg now
        EMBED_MODEL=args.embed,
        DB_PATH=args.db,
        TOP_K_PLANNING=int(os.getenv("TOP_K_PLANNING", default_topk_planning)),
        TOP_K_SCOUT=int(os.getenv("TOP_K_SCOUT", default_topk_scout)),
        TOP_K_REPORT=int(os.getenv("TOP_K_REPORT", default_topk_report)),
        DEFENSE_ENABLED=defense_enabled,
        SEED=default_seed,
        TEMPERATURE=default_temp,
        PREFILL_SIZE=default_prefill,
        DEFENSE_SIM_THRESHOLD=default_sim_threshold,
        DEFENSE_MAX_PER_SOURCE=default_max_per_source,
        DEFENSE_TRUST_WEIGHT=default_trust_weight,
        DEFENSE_PROVENANCE_SECRET=default_provenance_secret,
        MISSION=args.mission,
        RUN_ID=args.run_id,
        RICH_MEMORY=args.rich_memory,
        NO_SEED_TARGETS=args.no_seed_targets,
        KEEP_MEMORY=args.keep_memory,
        RETRIEVAL_ALPHA=alpha,
        RETRIEVAL_BETA=beta,
        RETRIEVAL_GAMMA=gamma,
    )
