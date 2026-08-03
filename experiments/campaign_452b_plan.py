"""452B PLAN adoption aggregation (planner coordinate-adoption vs planner_k).

Reads the 80 production PLAN bundles (MEM060_OPERATIONAL, budget 3 / control 0) from
results_v3_raw/, groups by planner_k (= top_k_scout) x attack, and writes
results_v3_campaigns/452B_PLAN_adoption/. Reports valid-plan rate, adoption-among-valid,
intent-to-treat adoption (both denominators), A00-vs-A01 delta, planner-retrieval CCR, and
the planner_outcome breakdown, with seed-as-unit bootstrap CIs. Pure aggregation; no runs.
"""
import csv
import glob
import json
import os
import random
import statistics
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys import paths as P  # noqa: E402

MEM = "MEM060_OPERATIONAL"
KS = [3, 5, 10, 20]
SEEDS = list(range(101, 111))
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452B_PLAN_adoption")


def _ci(vals, it=2000, a=0.05):
    vals = [float(v) for v in vals]
    if not vals:
        return (None, None, None)
    m = statistics.fmean(vals)
    if len(set(vals)) == 1:
        return (round(m, 4), round(m, 4), round(m, 4))
    r = random.Random(0)
    d = sorted(statistics.fmean(r.choices(vals, k=len(vals))) for _ in range(it))
    return (round(m, 4), round(d[int(a / 2 * it)], 4), round(d[int((1 - a / 2) * it)], 4))


def _index():
    cells = {}
    for m in glob.glob(P.RESULTS_V3_RAW + f"/**/{MEM}/PLAN/**/manifest.json", recursive=True):
        d = os.path.dirname(m)
        man = json.load(open(m))
        if man.get("validity") != "production":
            continue
        k = man.get("configured", {}).get("top_k_scout")
        atk = (man.get("canonical") or {}).get("attack")
        pa = json.load(open(os.path.join(d, "parsed_actions.json")))
        met = json.load(open(os.path.join(d, "metrics.json")))
        cells.setdefault((k, atk), []).append({
            "valid": pa.get("valid_plan") is True,
            "adopt": pa.get("coordinate_adoption") is True,
            "outcome": pa.get("planner_outcome"),
            "ccr": met["rates"]["ccr"]})
    return cells


def _cell(rows):
    n = len(rows)
    valids = [r for r in rows if r["valid"]]
    among_valid = [1.0 if r["adopt"] else 0.0 for r in valids]
    itt = [1.0 if r["adopt"] else 0.0 for r in rows]                 # failures count as non-adoption
    return {"n_attempted": n, "n_valid": len(valids),
            "valid_plan_rate": round(len(valids) / n, 4) if n else None,
            "adoption_among_valid": _ci(among_valid) if among_valid else (None, None, None),
            "itt_adoption": _ci(itt),
            "ccr": _ci([r["ccr"] for r in rows])[0],
            "planner_outcomes": dict(Counter(r["outcome"] for r in rows))}


def main():
    cells = _index()
    os.makedirs(OUT, exist_ok=True)
    summary = {"campaign": "452B_PLAN_adoption", "validity": "production", "memory": MEM,
               "budget": 3, "temp": 0.0, "seeds": SEEDS,
               "ci_method": "percentile bootstrap seed-as-unit (PROVISIONAL, pending Dr. Qian)",
               "denominators": "adoption_among_valid = adoptions/valid_plans; itt_adoption = adoptions/attempted(=10)",
               "cells": {}}
    rows = []
    for k in KS:
        a1 = _cell(cells.get((k, "A01_FALSE_OBSERVATION"), []))
        a0 = _cell(cells.get((k, "A00_CLEAN"), []))
        delta_itt = round(a1["itt_adoption"][0] - a0["itt_adoption"][0], 4)
        summary["cells"][f"planner_k-{k}"] = {"A01": a1, "A00": a0, "itt_delta_A01_minus_A00": delta_itt}
        rows.append([k, "A01", a1["n_attempted"], a1["n_valid"], a1["valid_plan_rate"],
                     *a1["adoption_among_valid"], *a1["itt_adoption"], a1["ccr"],
                     json.dumps(a1["planner_outcomes"])])
        rows.append([k, "A00", a0["n_attempted"], a0["n_valid"], a0["valid_plan_rate"],
                     *a0["adoption_among_valid"], *a0["itt_adoption"], a0["ccr"],
                     json.dumps(a0["planner_outcomes"])])
    with open(os.path.join(OUT, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "per_cell.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["planner_k", "arm", "n_attempted", "n_valid", "valid_plan_rate",
                    "adopt_valid_mean", "adopt_valid_lo", "adopt_valid_hi",
                    "itt_mean", "itt_lo", "itt_hi", "ccr", "planner_outcomes"])
        w.writerows(rows)
    print("wrote", OUT)
    print(f"{'k':>3} {'arm':4} {'valid_rate':>10} {'adopt/valid':>18} {'ITT':>18} {'CCR':>6}")
    for k in KS:
        c = summary["cells"][f"planner_k-{k}"]
        for arm in ("A01", "A00"):
            x = c[arm]
            print(f"{k:>3} {arm:4} {x['valid_plan_rate']:>10} {str(x['adoption_among_valid']):>18} {str(x['itt_adoption']):>18} {x['ccr']:>6}")


if __name__ == "__main__":
    main()
