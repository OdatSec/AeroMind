# Attacker-Capability Table — realistic write paths into shared UAV memory

Re-designs the paper's single "can write to shared memory" assumption into graded tiers, each tied to a
**documented real-world vector**. Executed tiers carry production evidence; TC-indirect is cited, not run.

These are **distinct, incomparable capabilities — NOT a weakest→strongest ladder.** "Attacker-direct write?"
= does the *attacker itself* perform a privileged write (a legitimate pipeline writing on the attacker's
behalf is a separate thing, noted per row).

| Tier | Capability (precise) | Repo attack | Real-world vector (reference) | Attacker-direct write? | Passes auth? | Result (this study) |
|---|---|---|---|---|---|---|
| TC0 | unauthenticated direct write | A01 | the paper's baseline assumption (what B1 calls "bad design") | yes | no | RET CCR 1.0; caught by D1+D2 |
| TC1 | control an **authorized writer** + its key → signed semantic | A04 | compromised in-fleet node / credential theft | yes | **yes** | RET CCR 1.0 (D0+D1); **planner NOT measured** |
| TC2 | control an **authorized writer** + its key → signed episodic | A05 | compromised in-fleet node / credential theft | yes | **yes** | RET CCR 1.0; **planner adoption 20/20** |
| **TC3** | **corrupt a sensor input** (perception ingress) | **A06** | **GNSS spoofing / adversarial patch / compromised sensor driver — real UAV attacks; INGRESS modeled, not the RF chain** | **no** (legit pipeline writes it) | via legit pipeline | **RET CCR 1.0; planner adoption 20/20** |
| **TC-indirect** | **one low-privilege episodic write** (no privileged/semantic write, no key) → system reflection promotes it | **P1b** | **MINJA (query-only injection); Greshake (indirect injection)** | no privileged write | n/a — no key | **promotion 1.0 gpt-oss / 0.1 qwen; top-k CCR & planner NOT measured** |

## TC-indirect executed result (P1b, 40 runs)
The **lowest-capability tier**: the attacker plants **one unsigned low-privilege episodic** false
observation. The Supervisor's own `consolidate_memory()` (Park-2023 reflection) retrieves it, the LLM
extracts "permanent facts," and writes them to **semantic memory** as trusted `reflection:` records —
**laundering the poison into trusted provenance it never had at write time**, with no privileged write, no
signature, no sensor.
| model | promotion_rate | trap_retrieval | laundered source |
|---|--:|--:|---|
| gpt-oss:20b | **1.00** | 1.00 | reflection |
| qwen2.5:7b | **0.10** | 0.10 | reflection |
| A00 controls (both) | 0.00 | 0.00 | — |
Model-dependent (qwen's reflection JSON usually fails to parse → rarely writes facts), analogous to the
paper's S12 model-dependent adoption. On a capable reflection model the laundering is total.

## Why TC3 (perception ingestion) is the "for-sure realistic" flagship
- **GNSS spoofing of UAVs is a demonstrated real-world attack**, not hypothetical.
- It answers 452C-C1 exactly: UAVs run a **closed mission-control loop** (no user chat), so the realistic
  injection is **indirect** — through sensor inputs the drone already trusts — **not** a direct memory-write API.
- The attacker **never writes memory directly and needs no unauthenticated write path**; the legitimate
  perception pipeline writes the attacker-influenced observation as a normal, trusted record.

## Real-world anchors (deployed systems, not just academic)
- **Amazon Bedrock agents:** persistent memory poisoning that survives session boundaries.
- **Microsoft 365 Copilot:** zero-click data exfiltration via injected content.
- **MCP tool-description compromise:** coding agents fully compromised through tool metadata.

## Academic references
MINJA — Dong et al., *Memory injection attacks on LLM agents via query-only interaction*, NeurIPS 2025 ·
Greshake et al., *Not what you've signed up for: indirect prompt injection*, 2023 · InjecAgent (Zhan et
al., ACL 2024) · AgentPoison (Chen et al., NeurIPS 2024) · PoisonedRAG (Zou et al., USENIX 2025) · Rodday
et al., *Exploring security vulnerabilities of UAVs* · plus the 2026 survey on long-term memory security
and *Agent Data Injection Attacks are Realistic Threats*.

## Bottom line
The attack reaches retrieval contamination (CCR 1.0) via **several distinct, independently realistic
paths** — an authorized-writer compromise (A04/A05, which passes authentication), a perception-ingress
path (A06, no attacker-direct write), and a low-privilege-plus-reflection path (TC-indirect) — so it does
**not** require the strong "unauthenticated store access" assumption B1/C1 objected to. It does **not**
follow that every path was taken end-to-end: planner adoption was measured for A05 and A06 only (20/20
each); TC-indirect measured promotion only and is model-dependent (1.0 gpt-oss, 0.1 qwen); no physical
execution; and these tiers are different capabilities, not a ranked ladder.
