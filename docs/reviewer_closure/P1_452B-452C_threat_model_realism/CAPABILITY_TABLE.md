# Attacker-Capability Table — realistic entry paths into shared UAV memory

The paper assumed one flat "can write to memory" capability. We instead evaluate **distinct, incomparable
realistic entry paths** — different threat actors, **NOT a weakest→strongest ladder**. "Attacker-direct
write?" = does the *attacker itself* perform a privileged write (a legitimate pipeline writing on the
attacker's behalf is a separate thing, noted per row). Rates are Clopper-Pearson exact 95% CIs.

| Path | Capability (precise) | Repo attack | Real-world vector (reference) | Attacker-direct write? | Passes auth? | Measured result |
|---|---|---|---|---|---|---|
| TC0 | unauthenticated direct write | A01 | the paper's baseline (what B1 calls "bad design") | yes | no | RET CCR 1.0 (10/10, CI [0.69,1.0]); planner NOT measured |
| TC1 | control an **authorized writer** + its key → signed semantic | A04 | compromised in-fleet node / credential theft | yes | **yes** | RET CCR 1.0 (10/10); planner NOT measured |
| TC2 | control an **authorized writer** + its key → signed episodic | A05 | compromised in-fleet node / credential theft | yes | **yes** | RET CCR 1.0; **planner adoption 20/20, CI [0.83,1.0]** |
| TC3 | **corrupt a sensor input** (perception ingress) | A06 | GNSS spoofing / adversarial patch / compromised sensor driver — real UAV attacks; **INGRESS modeled, NOT the RF chain** | no (legit pipeline writes it) | via legit pipeline | RET CCR 1.0; **planner adoption 20/20, CI [0.83,1.0]** |
| TC-reflect | **one low-privilege episodic write** (no privileged/semantic write, no key) → the system's reflection promotes it | P1b | related: MINJA (query-only injection), Greshake (indirect injection) — see note | no privileged write | n/a — no key | **EXECUTED, 40 runs: promotion gpt-oss 10/10 (CI [0.69,1.0]), qwen 1/10 (CI [0.003,0.45]); top-k CCR & planner NOT measured** |

## TC-reflect (P1b) — executed result, 40 runs
The attacker plants **one low-privilege episodic** false observation (this is a write — **not** query-only).
The Supervisor's own `consolidate_memory()` (Park-2023 reflection) retrieves it, the LLM extracts "facts,"
and writes them to **semantic memory** as trusted `reflection:` records — promoting low-trust content into
trusted provenance. We measured **promotion only**.
| model | promotion | 95% CI | laundered source |
|---|--:|---|---|
| gpt-oss:20b | 10/10 (1.0) | [0.69, 1.0] | reflection |
| qwen2.5:7b | 1/10 (0.1) | [0.003, 0.45] | reflection |
| A00 controls (per model) | 0/10 each (0.0) | [0, 0.31] | — |
Strongly **model-dependent** (qwen's reflection JSON often fails to parse). **top-k CCR and planner impact
were NOT measured for this path.**

**Naming note:** the frozen prereg file is `PREREG_P1b_indirect_consolidation.md` and framed this as a
MINJA "query-only" analogue. The *executed* method is a **low-privilege episodic write + reflection
promotion**, which is **not** literally query-only; the closure uses **TC-reflect** and cites MINJA/Greshake
as *related work*, not as the tested method.

## Why the perception path is realistic (TC3)
- GNSS spoofing of UAVs is a **documented real-world attack**; UAVs run a **closed mission-control loop**, so
  the realistic injection is **indirect** through sensor inputs the drone already trusts — no direct memory-write API.
- We model the **ingress point** (a spoofed observation entering memory via the legitimate pipeline). We do
  **not** execute the RF-level GNSS-spoofing chain.

## Real-world anchors (deployed systems)
Amazon Bedrock persistent memory poisoning (survives sessions); M365 Copilot zero-click; MCP tool-description compromise.

## Academic references
MINJA (Dong et al., NeurIPS 2025) · Greshake et al. 2023 · InjecAgent (ACL 2024) · AgentPoison (NeurIPS 2024) ·
PoisonedRAG (USENIX 2025) · Rodday et al. (UAV vulns) · 2026 long-term-memory-security survey.

## Bottom line
Retrieval CCR = 1.0 was measured for the **authorized-writer (A04/A05)** and **modeled perception-ingress
(A06)** paths, as well as the **unauthenticated baseline (A01)**. Separately, **TC-reflect promoted
low-trust episodic content into trusted semantic memory; top-k CCR and planner impact were NOT measured for
that path.** Together these show the attack does **not** require unauthenticated store access — but it does
**not** follow that every path was taken end-to-end: **planner adoption measured for A05/A06 only** (20/20
each); TC-reflect is promotion-only and model-dependent (10/10 gpt-oss, 1/10 qwen); **no physical
execution**; and these are different capabilities, not a ranked ladder.
