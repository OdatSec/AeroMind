# PRE-REGISTRATION — P1: threat-model realism / attacker-capability execution (Reviewers 452B-B1, 452C-C1)
# Embedder pinned (nomic-embed-text 970aa74c...). RET/L1 embedder-only + PLAN/L2 on local chat models.
# Frozen BEFORE any run. sha256 recorded in every bundle's prereg_spec_hash.

## Reviewer concern (452B-B1 + 452C-C1, both "biggest concern")
B1: "The attacks assume the adversary can inject or alter records in shared long-term memory before
retrieval ... it's more like a bad design. We all know unauthenticated memory writes are bad. The
paper does not validate how practical this threat model is for actual UAV systems."
C1: "The paper assumes adversarial write access ... but does not show how such access would
realistically arise. Unlike general LLM agents, UAV agents operate in a closed mission-control loop."

## Thesis of this study
Refute "it only works because of unauthenticated direct writes / it's just bad design" by showing,
empirically, that poison achieves retrieval dominance via REALISTIC and even AUTHENTICATED write
paths that already exist in the running system — NOT only via a naive unauthenticated write.

## Attacker-capability tiers (each = a repo attack + a cited real-world vector)  [binding]
- TC0 direct-unauth (baseline = paper S01): naive unauthenticated write. Reference point only.
- TC1 signed-semantic = S16/A04: compromised insider holding a VALID signing key writes a signed
  semantic target fact. Passes D1 (valid signature). Real vector: compromised in-fleet node / key theft.
- TC2 signed-episodic = S17/A05: valid-key signed episodic false observation (in-role). Passes D1+D4a.
- TC3 perception-ingestion = S18/A06: spoofed detection enters episodic memory through the LEGITIMATE
  perception pipeline (uavsys/ingest/perception.py); the attacker NEVER writes memory directly.
  Real vectors: GNSS spoof, adversarial patch, compromised sensor driver (Rodday UAV vulns).
Cited support (add to paper): MINJA (query-only memory injection), Greshake (indirect prompt injection),
InjecAgent (tool-output), AgentPoison; real-world Amazon Bedrock persistent memory poisoning, M365
Copilot zero-click, MCP tool-description compromise. (Indirect/query-only TC is cited, not executed here.)

## Scope statement (binding)
Demonstrates that attacker-controlled records from realistic/authenticated paths cross the retrieval
boundary and (RET) dominate top-k / (PLAN) drive planner adoption. Does NOT compromise PX4, MAVSDK,
the embedder, or the harness. Local chat models only (gpt-oss-20b, qwen2.5:7b); 7-model parity deferred.

## Design matrix
RET/L1 (embedder-only, model-invariant):
    attacks {B0, S01, S16, S17, S18} x defenses {D0, D1, D_full} x seeds 101-110  -> 5x3x10 = 150 runs
PLAN/L2 (local chat models):
    attacks {S17, S18} x defenses {D0, D_full} x models {gpt-oss-20b, qwen2.5:7b} x seeds 101-110
                                                                                   -> 2x2x2x10 = 80 runs
TOTAL = 230 runs.  Task T01; memory MEM060_OPERATIONAL; Scout k=3 / Supervisor k=5 (paper topology).

## Metrics
- RET: CCR, CASR, malicious-rank; plus a write_path_authenticity annotation per attack
  (unauthenticated / signed-valid / legitimate-ingestion).
- PLAN: CHR (planner adoption of trap coords), valid-plan rate.
- Seed-as-unit percentile bootstrap 95% CIs (PROVISIONAL pending Dr. Qian).

## Neutral hypotheses (no direction pre-registered)
- H1: signed-valid records (S16/S17) may or may not achieve retrieval dominance under D1.
- H2: they may or may not be neutralized under D_full (D4a authorization / D4b corroboration).
- H3: perception-ingested spoof (S18) may or may not achieve dominance with NO direct memory write.
Direction is determined empirically. The refutation of B1/C1 holds iff H1 or H3 shows dominance under
D0/D1 (i.e. success without a naive unauthenticated write); if not, we report that honestly.

## Deliverable
`docs/reviewer_closure/452B-2_threat_model_practicality/` closure: capability table (TC0-TC3 success
gradient) + the executed evidence + a claim-to-evidence map. Threat-model section prose is [authors].

## Provenance / integrity
Attack payloads already frozen in repo (attacks/s16,s17,s18 + uavsys/ingest/perception.py); commit
recorded. config_hash (schema v3), prereg_spec_hash, embedder digest, validity=production, accept-gate,
dirty-tree guard. results_v2_frozen/ untouched.
