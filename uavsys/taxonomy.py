"""Canonical V3 taxonomy + backward-compatible alias resolution.

THE single source of truth for the Final Campaign V3 identifiers. Legacy names
(C0-C6, B0/Sxx, MV1-3, M1-4, P1/P2, retrieval/planning/full-pipeline) remain valid
as **aliases only**. V3 manifests and reports use the canonical IDs and also record
the legacy alias when applicable.

Nothing here runs experiments or touches results_v2_frozen/. It is pure mapping.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# ── Attacks (A00-A09) ────────────────────────────────────────────────────────
# canonical -> {c_id (paper C-case or None), runner (SCENARIO_MAP key), status, name}
ATTACKS: Dict[str, dict] = {
    "A00_CLEAN":                  {"c_id": "C0", "runner": "B0",  "status": "implemented", "name": "Clean baseline"},
    "A01_FALSE_OBSERVATION":      {"c_id": "C1", "runner": "S01", "status": "implemented", "name": "Direct false observation"},
    "A02_SHARED_MEMORY_EXPOSURE": {"c_id": "C2", "runner": "S06", "status": "implemented", "name": "Shared-memory exposure (NOT propagation)"},
    "A03_FALSE_RESTRICTION":      {"c_id": "C3", "runner": "S12", "status": "implemented", "name": "False safety constraint"},
    "A04_SIGNED_CONFLICT":        {"c_id": "C4", "runner": "S16", "status": "implemented", "name": "Authenticated false semantic state"},
    "A05_SIGNED_FALSE_OBSERVATION": {"c_id": "C5", "runner": "S17", "status": "implemented", "name": "Authenticated false episodic observation"},
    "A06_PERCEPTION_FALSE_STATE": {"c_id": "C6", "runner": "S18", "status": "implemented", "name": "Perception-ingestion false state"},
    "A07_FALSE_COMPLETION":       {"c_id": None, "runner": "MV1_FALSE_CLEARANCE", "status": "implemented", "name": "False completion / already-cleared", "required_task": "T02_MULTI_TARGET"},
    "A08_FALSE_SAFETY":           {"c_id": None, "runner": "MV2_FALSE_SAFETY",    "status": "implemented", "name": "False safety-restored", "required_task": "T03_RESTRICTED_ZONE"},
    "A09_TARGET_RELOCATION":      {"c_id": None, "runner": "MV3_TARGET_RELOCATION", "status": "deferred",    "name": "Target relocation", "required_task": "T04_RETASKING"},
}

# ── Tasks (T01-T04) -> mission id ────────────────────────────────────────────
TASKS: Dict[str, dict] = {
    "T01_SEARCH_RESCUE": {"runner": "M1", "status": "implemented", "name": "Search & Rescue"},
    "T02_MULTI_TARGET":  {"runner": "M2", "status": "implemented", "name": "Multi-target Survey"},
    "T03_RESTRICTED_ZONE": {"runner": "M3", "status": "implemented", "name": "Constrained Corridor"},
    "T04_RETASKING":     {"runner": "M4", "status": "deferred",    "name": "Sequential Re-tasking"},
}

# ── Memory configurations -> profile id ──────────────────────────────────────
MEMORY: Dict[str, dict] = {
    "MEM003_SPARSE":      {"runner": "P1", "status": "implemented", "name": "Sparse baseline (3 records)"},
    "MEM060_OPERATIONAL": {"runner": "P2", "status": "implemented", "name": "Operational mixture (60 records)"},
    "MEM200_DENSE":       {"runner": "P3", "status": "planned",     "name": "Dense-similar (200 records)"},
    "MEM1000_LARGE":      {"runner": "P4", "status": "planned",     "name": "Large (1000 records)"},
}
# Semantic suffixes that may extend a memory id (documented, not exhaustive).
MEMORY_SUFFIXES = ("_STALE", "_CONFLICTING", "_MIXED")

# ── Evaluation modes -> runner --mode ────────────────────────────────────────
EVALUATIONS: Dict[str, dict] = {
    "RET":  {"runner": "retrieval",     "layer": "L1", "status": "implemented", "name": "Retrieval"},
    "PLAN": {"runner": "planning",      "layer": "L2", "status": "implemented", "name": "Planner"},
    "MULTI": {"runner": None,           "layer": "L3", "status": "planned",     "name": "Logical multi-agent (no runner yet)"},
    "SITL": {"runner": "full-pipeline", "layer": "L4", "status": "implemented", "name": "PX4-SITL closed-loop (not run)"},
}

# ── Defenses (D0-D4) ─────────────────────────────────────────────────────────
DEFENSES = ("D0", "D1", "D2", "D3", "D4")

_KINDS = {"attack": ATTACKS, "task": TASKS, "memory": MEMORY, "evaluation": EVALUATIONS}


def _canonical_index(table: Dict[str, dict]) -> Dict[str, str]:
    """alias(lowered) -> canonical, including canonical->itself, c_id, and runner key."""
    idx: Dict[str, str] = {}
    for canon, meta in table.items():
        for a in (canon, meta.get("c_id"), meta.get("runner")):
            if a:
                idx[a.lower()] = canon
    return idx


_INDEX = {k: _canonical_index(v) for k, v in _KINDS.items()}


def resolve(kind: str, token: str) -> str:
    """Return the canonical id for any accepted alias of `kind`.

    kind in {attack, task, memory, evaluation}. For memory, an unknown base with a
    known-suffix stripped still resolves (e.g. MEM060_OPERATIONAL_STALE -> canonical
    base MEM060_OPERATIONAL) so semantic variants map to their base config.
    """
    if kind not in _INDEX:
        raise KeyError(f"Unknown taxonomy kind {kind!r}; expected {sorted(_INDEX)}")
    t = (token or "").strip()
    hit = _INDEX[kind].get(t.lower())
    if hit:
        return hit
    if kind == "memory":
        for suf in MEMORY_SUFFIXES:
            if t.upper().endswith(suf):
                base = t[: -len(suf)]
                hit = _INDEX["memory"].get(base.lower())
                if hit:
                    return hit
    raise KeyError(f"Unknown {kind} id/alias {token!r}; known canonical: "
                   f"{sorted(_KINDS[kind])}")


def runner_value(kind: str, token: str) -> Optional[str]:
    """Internal runner value (SCENARIO_MAP key / mission / profile / --mode) for an
    id or alias. None means the canonical id has no runner yet (e.g. MULTI, A09)."""
    return _KINDS[kind][resolve(kind, token)].get("runner")


def status(kind: str, token: str) -> str:
    return _KINDS[kind][resolve(kind, token)]["status"]


def is_canonical(kind: str, token: str) -> bool:
    return token in _KINDS[kind]


def legacy_aliases(kind: str, token: str) -> List[str]:
    """The legacy aliases recorded alongside a canonical id (c_id + runner key)."""
    meta = _KINDS[kind][resolve(kind, token)]
    out = [a for a in (meta.get("c_id"), meta.get("runner")) if a]
    return out


def required_task(attack: str) -> Optional[str]:
    """The canonical task an attack is LOCKED to (variants), or None (broad)."""
    return ATTACKS[resolve("attack", attack)].get("required_task")


def validate_attack_task(attack: str, task: str) -> None:
    """Raise ValueError if the attack×task combination violates a canonical lock.

    Variants (A07/A08/A09) are locked to exactly one task (e.g. A08_FALSE_SAFETY ->
    T03_RESTRICTED_ZONE). A00-A06 are broadly applicable and pass. Called before any
    path is built or any run executes, so an invalid combination creates NO directory.
    """
    a = resolve("attack", attack)
    t = resolve("task", task)
    req = ATTACKS[a].get("required_task")
    if req and t != req:
        raise ValueError(
            f"Invalid attack/task combination: {a} is locked to {req}, got {t}. "
            f"(No path is created and no run is executed.)")


def canonical_manifest_ids(attack: str, task: str, memory: str,
                           evaluation: str, defense: str) -> dict:
    """The canonical + legacy identity block recorded in every V3 manifest."""
    if defense not in DEFENSES:
        raise KeyError(f"Unknown defense {defense!r}; expected {DEFENSES}")
    return {
        "attack": resolve("attack", attack),
        "task": resolve("task", task),
        "memory": resolve("memory", memory),
        "evaluation": resolve("evaluation", evaluation),
        "defense": defense,
        "legacy_aliases": {
            "attack": legacy_aliases("attack", attack),
            "task": legacy_aliases("task", task),
            "memory": legacy_aliases("memory", memory),
            "evaluation": legacy_aliases("evaluation", evaluation),
        },
    }
