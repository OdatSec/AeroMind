"""Poison-blind task assignment (452A Part 2).

assign(policy, scout_count, seed) is a pure function of (policy, scout_count, seed) and the
CLEAN subtask pool ONLY. It takes NO attack/poison argument, so the SAME map is produced for
the A00 and A01 arms of a cell. fixed / random / dynamic per PREREG_452A_part2; equal total
fleet query budget across policies (dynamic swaps, never adds).
"""
from __future__ import annotations

import random
from typing import Dict, List

from .subtasks import SUBTASK_IDS, PRIORITY_SUBTASK, Q_OVERVIEW, query_for

POLICIES = ("fixed", "random", "dynamic")


def scouts(scout_count: int) -> List[str]:
    return [f"Scout {i}" for i in range(scout_count)]


def assign(policy: str, scout_count: int, seed: int) -> Dict:
    """Return the assignment map (poison-blind). Keys: blocks {agent:[subtask_ids]},
    queries {agent:[query_str]}, displaced, replicated, scouts, supervisor."""
    if policy not in POLICIES:
        raise ValueError(f"unknown policy {policy!r}; expected {POLICIES}")
    sc = scouts(scout_count)
    if policy == "random":
        order = SUBTASK_IDS[:]
        random.Random(seed).shuffle(order)
    else:                                      # fixed and dynamic start from the fixed order
        order = SUBTASK_IDS[:]
    blocks: Dict[str, List[str]] = {s: [] for s in sc}
    for i, sid in enumerate(order):            # round-robin partition (disjoint)
        blocks[sc[i % scout_count]].append(sid)

    displaced = replicated = None
    if policy == "dynamic":
        # Poison-BLIND priority: replicate the clean primary-target subtask to a second scout,
        # displacing that scout's lowest-priority (highest-index) subtask. Equal query budget.
        holder = next(s for s in sc if PRIORITY_SUBTASK in blocks[s])
        second = sc[(sc.index(holder) + 1) % scout_count]
        if second == holder:                   # scout_count == 1 guard (not used here; scouts>=2)
            second = holder
        lowest = max(blocks[second], key=lambda x: int(x[1:]))
        if lowest != PRIORITY_SUBTASK:
            blocks[second].remove(lowest)
            blocks[second].append(PRIORITY_SUBTASK)
            displaced, replicated = lowest, PRIORITY_SUBTASK

    queries = {s: [query_for(x) for x in blocks[s]] for s in sc}
    queries["Supervisor"] = [Q_OVERVIEW]
    covered = sorted({x for b in blocks.values() for x in b}, key=lambda x: int(x[1:]))
    return {"policy": policy, "scout_count": scout_count, "seed": seed, "scouts": sc,
            "supervisor": "Supervisor", "blocks": blocks, "queries": queries,
            "displaced": displaced, "replicated": replicated, "covered_subtasks": covered}
