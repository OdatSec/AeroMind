<![CDATA[<div align="center">

<img src="figures/Figure1.png" alt="AeroMind System Architecture" width="780"/>

# AeroMind: Poisoning the Control Plane of LLM-Driven UAV Agents

[![Paper](https://img.shields.io/badge/RAID%202026-Paper-blue?style=flat-square)](https://github.com/OdatSec/AeroMind)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?style=flat-square&logo=python)](https://python.org)
[![PX4](https://img.shields.io/badge/PX4-SITL-purple?style=flat-square)](https://px4.io)

> **RAID 2026** · Ibrahim Odat¹, Anyi Liu¹, Yingjiu Li²  
> ¹ Oakland University · ² University of Oregon

</div>

---

## Overview

**AeroMind** is a multi-agent UAV autonomy stack built on shared persistent memory, used as a security research testbed to study *control-plane poisoning* of LLM-driven autonomous systems.

Safety-critical multi-agent systems increasingly rely on shared memory to coordinate. Once retrieved records inform planning, that memory becomes **control-plane state** — not passive context. This repository contains the full implementation of the AeroMind Supervisor–Scout UAV stack, all 15 attack scenarios, the retrieval-boundary defense pipeline, and reproducibility artifacts for the RAID 2026 paper.

**Key findings:**
- Three poisoned episodic records are sufficient to redirect both Scout UAVs to adversarial trap coordinates in **every evaluated seed** across **seven LLM backends**
- A single compromised Scout contaminates all peer agents and the Supervisor through shared retrieval (**O(1) attack cost**)
- The provenance + diversity defense reduces physical hijack from **100% → 0%** on validated backends
- Constraint-injection attacks (S12) expose a model-specific safety-handling split across 7 backends

---

## System Architecture

<div align="center">
<img src="figures/Figure2.png" alt="AeroMind Attack Flow" width="720"/>

*End-to-end attack path: from poisoned memory write surface → retrieval dominance → planner adoption → physical UAV misdirection*
</div>

| Component | Role |
|---|---|
| **Supervisor agent** | Decomposes natural-language mission into Scout sub-tasks |
| **Scout agents (×2)** | Retrieve memory → plan flight sequences → execute via MAVSDK |
| **Shared long-term memory** | SQLite + nomic-embed-text vector store across 4 memory layers |
| **Memory layers** | Episodic, Semantic, Coordination, Procedural |
| **Execution backend** | PX4 SITL via MAVSDK (local ports 14540/14541) |

---

## Attack Taxonomy (15 Scenarios)

| ID | Family | Attack Surface | Core Mechanism |
|---|---|---|---|
| **S01** | F1 — Embodied Hijack | Episodic write | False coordinates → physical trap redirect |
| **S02** | F1 — Embodied Hijack | Semantic write | Fact corruption in shared knowledge |
| **S03** | F1 — Embodied Hijack | Procedural write | Skill hijack via malicious procedure |
| **S04** | F1 — Embodied Hijack | Coordination write | Task misrouting between roles |
| **S05** | F1 — Embodied Hijack | Prompt injection | In-context instruction override |
| **S06** | F2 — Cross-Agent | Native write surface | Contagion from one Scout to all peers |
| **S07** | F3 — Temporal | Stealth insert | Low-volume persistent poisoning |
| **S08** | F3 — Temporal | Volume flood | Retrieval dominance via mass injection |
| **S09** | F3 — Temporal | Recency exploit | Timestamp manipulation |
| **S10** | F3 — Temporal | Memory amplification | Cascading record propagation |
| **S11** | F3 — Temporal | Authority spoof | False high-trust source metadata |
| **S12** | F4 — Planning | Constraint injection | Virtual no-fly zone → mission denial |
| **S13** | F4 — Planning | Skill arbitration | Tool-selection manipulation |
| **S14** | F4 — Planning | Policy hijack | Mission policy override |
| **S15** | F4 — Planning | Cascade | Cross-mission temporal persistence |
| **B0** | Baseline | — | Clean-mission control run |

<div align="center">
<img src="figures/Figure3.png" alt="Defense Pipeline" width="720"/>

*Three-layer retrieval-boundary defense: HMAC provenance verification → trust-aware reranking → source-diversity capping*
</div>

---

## Defense Pipeline

The `uavsys/memory/defense.py` module implements a three-component retrieval-boundary defense:

| Layer | Component | Mechanism |
|---|---|---|
| **D1** | Provenance verification | HMAC-SHA256 signature on all memory writes; unverified records are soft-demoted |
| **D2** | Trust-aware reranking | Per-source trust signal combined with embedding similarity during retrieval |
| **D3** | Source-diversity capping | Hard cap on records retrievable from any single source author |

**Results on end-to-end validated backends (GPT-4o, GPT-OSS):**  
Physical trap capture rate: **100% → 0%** · False negative rate on benign missions: **0%**

---

## Repository Structure

```
AeroMind/
│
├── uavsys/                     # Core system package
│   ├── agents/
│   │   ├── supervisor.py       # Supervisor agent: mission decomposition
│   │   ├── scout.py            # Scout agent: retrieval → planning → execution
│   │   └── types.py            # Shared agent type definitions
│   ├── memory/
│   │   ├── db.py               # SQLite + vector memory store
│   │   ├── memory_interface.py # Unified read/write API
│   │   ├── retrieval.py        # Embedding retrieval with reranking
│   │   └── defense.py          # D1/D2/D3 defense pipeline
│   ├── drones/
│   │   ├── mavsdk_client.py    # PX4 SITL drone connection
│   │   └── skills.py           # Primitive flight skill library
│   ├── llm/
│   │   ├── ollama_client.py    # Ollama local LLM interface
│   │   └── prompts.py          # Mission and planning prompt templates
│   ├── utils/
│   │   ├── metrics.py          # CCR / CASR metric computation
│   │   └── richlog.py          # Structured experiment logging
│   ├── config.py               # System-wide configuration
│   ├── seeding.py              # Deterministic seed control
│   └── demo.py                 # End-to-end demo runner
│
├── attacks/                    # All 15 attack implementations (S01–S15 + B0)
│   ├── base.py                 # Abstract attack base class
│   ├── s01_false_observation.py
│   ├── s06_contagion.py
│   ├── s12_virtual_nfz.py
│   └── ...                     # (all scenarios)
│
├── experiments/                # Reproducibility experiment scripts
│   ├── experiment_runner.py    # Main single-scenario runner
│   ├── experiment_runner_swarm.py # Multi-agent swarm experiments
│   ├── k_sensitivity_sweep.py  # Scout retrieval budget k ∈ {3,5,7,10}
│   ├── pool_scaling_experiment.py # Memory pool size 6→200 records
│   ├── agent_scaling_experiment.py # Fleet size 3→50 agents (S01)
│   ├── agent_scaling_s06_experiment.py # Fleet size sweep (S06)
│   ├── adaptive_attacker_experiment.py # Adaptive adversary baseline
│   ├── benign_utility_sweep.py # Clean-mission false-negative audit
│   ├── s12_runner.py           # S12 multi-model sweep
│   ├── s15_runner.py           # S15 cascade scenario
│   └── gpt4o_validation.py     # GPT-4o end-to-end validation
│
├── configs/
│   ├── baseline_configs.yaml   # Named experiment configurations
│   └── defense_sweeps.yaml     # Defense parameter sweep settings
│
├── figures/                    # Paper figures (Figs. 1–3)
│   ├── Figure1.png             # AeroMind system architecture
│   ├── Figure2.png             # End-to-end attack flow
│   └── Figure3.png             # Defense pipeline diagram
│
├── run_config.yaml             # Default runtime configuration
├── requirements.txt            # Python dependencies
├── CITATION.cff                # Citation metadata
└── LICENSE                     # MIT License
```

---

## Setup

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.10 | |
| PX4-Autopilot | v1.14+ | SITL only — no real hardware required |
| Ollama | latest | For local LLM backends |
| MAVSDK-Python | ≥ 1.4.0 | Installed via pip |

### Installation

```bash
git clone https://github.com/OdatSec/AeroMind.git
cd AeroMind
pip install -r requirements.txt
```

### Starting PX4 SITL (two drones)

```bash
# Terminal 1 — Scout 1 (port 14540)
cd PX4-Autopilot && make px4_sitl gazebo

# Terminal 2 — Scout 2 (port 14541)
PX4_SIM_PORT=14541 make px4_sitl gazebo
```

### Running a baseline experiment

```bash
python experiments/experiment_runner.py --scenario B0 --model llama3.1 --seeds 5
```

### Running an attack scenario

```bash
# S01: Direct coordinate hijack (flagship scenario)
python experiments/experiment_runner.py --scenario S01 --model llama3.1 --seeds 5

# S01 with defense enabled
python experiments/experiment_runner.py --scenario S01 --model llama3.1 --seeds 5 --defense

# S06: Cross-agent contagion
python experiments/experiment_runner.py --scenario S06 --model llama3.1 --seeds 5

# S12: Multi-model constraint injection sweep
python experiments/s12_runner.py
```

### Scalability sweeps

```bash
# k-sensitivity (Scout retrieval budget)
python experiments/k_sensitivity_sweep.py

# Memory pool scaling (6 → 200 records)
python experiments/pool_scaling_experiment.py

# Agent-count scaling (3 → 50 agents)
python experiments/agent_scaling_experiment.py
```

---

## Supported LLM Backends

| Backend | Type | Identifier |
|---|---|---|
| GPT-4o | API (OpenAI) | `gpt-4o` |
| GPT-OSS | API (OpenAI) | `gpt-4o-mini` |
| Llama 3.1 8B | Local (Ollama) | `llama3.1` |
| Mistral 7B | Local (Ollama) | `mistral` |
| Mixtral 8×7B | Local (Ollama) | `mixtral8x7b` |
| Qwen 2.5 7B | Local (Ollama) | `qwen2.5` |
| DeepSeek-R1 7B | Local (Ollama) | `deepseek` |

Embedding model: **nomic-embed-text v1.5** (dimensionality 768, context 8192 tokens) via Ollama.

---

## Metrics

| Metric | Full Name | Definition |
|---|---|---|
| **CCR** | Context Contamination Rate | Fraction of a role's retrieved slots occupied by attacker-controlled records |
| **CASR** | Contaminated Agent Success Rate | Fraction of runs in which at least one poisoned record is retrieved by a given role |
| **System CCR** | — | Mean CCR across all agent roles in the system |

---

## Reproducibility

All experiments use deterministic seeding (`uavsys/seeding.py`). Each scenario is reported as a mean over **five independent seeds**. Named configurations for every table and figure in the paper are stored in `configs/baseline_configs.yaml`.

Results are logged as structured JSON to the experiment output directory. Aggregate metrics are computed by `uavsys/utils/metrics.py`.

---

## Citation

If you use AeroMind in your research, please cite:

```bibtex
@inproceedings{odat2026aeromind,
  title     = {{AeroMind}: Poisoning the Control Plane of {LLM}-Driven {UAV} Agents},
  author    = {Odat, Ibrahim and Liu, Anyi and Li, Yingjiu},
  booktitle = {Proceedings of the 19th International Symposium on Research in Attacks,
               Intrusions and Defenses (RAID)},
  year      = {2026},
  note      = {To appear}
}
```

A `CITATION.cff` file is also included for automated citation tools.

---

## Ethics

All experiments were conducted in a fully isolated PX4 Software-In-The-Loop simulation environment. No real UAV hardware, airspace, or network infrastructure was involved at any stage. The attack scenarios disclosed here reflect vulnerabilities in the architectural coupling of shared retrieval memory with physical actuator dispatch; responsible disclosure of design-level vulnerabilities follows standard academic norms. The released artifact is intended to support defensive security research and the design of provenance-aware agentic memory systems.

---

## License

This project is released under the [MIT License](LICENSE).

---

<div align="center">
<sub>Oakland University · University of Oregon · RAID 2026</sub>
</div>
]]>
