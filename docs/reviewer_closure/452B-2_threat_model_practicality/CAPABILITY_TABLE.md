# Attacker-Capability Table — realistic write paths into shared UAV memory

Re-designs the paper's single "can write to shared memory" assumption into graded tiers, each tied to a
**documented real-world vector**. Executed tiers carry production evidence; TC-indirect is cited, not run.

| Tier | Capability | Repo attack | Real-world vector (reference) | Direct write? | Passes auth? | Result (this study) |
|---|---|---|---|---|---|---|
| TC0 | unauthenticated direct write | A01 | the paper's baseline assumption (what B1 calls "bad design") | yes | no | RET CCR 1.0; caught by D1+D2 |
| TC1 | signed semantic (insider key) | A04 | compromised in-fleet node / key theft | yes | **yes** | RET CCR 1.0 (D0+D1) |
| TC2 | signed episodic (insider key) | A05 | compromised in-fleet node / key theft | yes | **yes** | RET CCR 1.0; **PLAN adoption 1.0** |
| **TC3** | **perception ingestion (spoofed sensor)** | **A06** | **GNSS spoofing / adversarial patch / compromised sensor driver — documented real UAV attacks** | **no** | via legit pipeline | **RET CCR 1.0; PLAN adoption 1.0** |
| TC-indirect | query-only / indirect injection | (cited) | MINJA (query-only memory injection); Greshake (indirect prompt injection); InjecAgent (tool output) | no | n/a | cited, not executed here |

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
The attack requires **at most TC3 capability — a documented, low-capability, realistic UAV vector** — and
also survives TC1/TC2 authentication. It does not need the strong "unauthenticated write" assumption B1/C1
objected to.
