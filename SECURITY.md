# Security Policy

## Supported Versions

This repository is a research artifact accompanying the RAID 2026 paper. It is
intended for use in controlled simulation environments (PX4 SITL) only.

| Version | Supported |
|---|---|
| main | ✅ |

## Scope

The vulnerabilities documented in this codebase are **intentionally
implemented** as part of the attack evaluation. They demonstrate security
weaknesses in the architectural coupling of shared retrieval memory with
physical actuator dispatch in LLM-driven multi-agent systems.

This artifact is **not** intended for deployment against real UAV hardware,
production systems, or live airspace under any circumstances.

## Reporting Issues

If you discover a security issue or unintended vulnerability in the released
artifact code itself (not the intentionally implemented attack scenarios),
please report it via GitHub Issues or contact the authors directly:

- Ibrahim Odat — ibrahimodat@oakland.edu
- Anyi Liu — anyiliu@oakland.edu
- Yingjiu Li — yingjiul@uoregon.edu

## Responsible Use

By using this artifact, you agree to:
1. Use it only in isolated simulation environments
2. Not deploy any attack scenarios against real systems
3. Attribute the work appropriately in any derivative research
