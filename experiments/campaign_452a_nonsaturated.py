"""452A Part 1b non-saturated slice aggregation (profile x poison-budget).

Reads production A01 RET bundles at budgets {1,2} + the reused A00 budget-00 controls
from results_v3_raw/, aggregates by profile x budget (CCR/MTR/RIS/poison-presence/
malicious-rank/corrected clean-displacement + seed-as-unit bootstrap CIs), and writes
results_v3_campaigns/452A_memory_nonsaturated/. Pure aggregation; no experiments run.
"""
import csv
import glob
import json
import os
import random
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys import paths as P  # noqa: E402
from uavsys.evidence.retrieval_metrics import paired_clean_displacement  # noqa: E402

PROFILES = ["MEM003_SPARSE", "MEM060_OPERATIONAL", "MEM200_DENSE",
            "MEM060_EPISODIC_HEAVY", "MEM060_BENIGN_HIGHSIM"]
BUDGETS = [1, 2]
SEEDS = list(range(101, 111))
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452A_memory_nonsaturated")


def _boot_ci(vals, iters=2000, alpha=0.05):
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return (None, None, None)
    mean = statistics.fmean(vals)
    if len(set(vals)) == 1 or len(vals) < 2:
        return (round(mean, 4), round(min(vals), 4), round(max(vals), 4))
    rng = random.Random(0)
    means = sorted(statistics.fmean(rng.choices(vals, k=len(vals))) for _ in range(iters))
    return (round(mean, 4), round(means[int(alpha / 2 * iters)], 4),
            round(means[int((1 - alpha / 2) * iters)], 4))


def _index():
    """(profile, attack, budget, seed) -> {metrics}; production only. A00 => budget 0."""
    idx = {}
    for m in glob.glob(P.RESULTS_V3_RAW + "/**/RET/**/manifest.json", recursive=True):
        d = os.path.dirname(m)
        man = json.load(open(m))
        if man.get("validity") != "production":
            continue
        can = man.get("canonical") or {}
        prof, atk, seed = can.get("memory"), can.get("attack"), man.get("seed")
        bud = man.get("budget")
        if prof in PROFILES and atk in ("A00_CLEAN", "A01_FALSE_OBSERVATION"):
            idx[(prof, atk, bud, seed)] = json.load(open(os.path.join(d, "metrics.json")))
    return idx


def main():
    idx = _index()
    os.makedirs(OUT, exist_ok=True)
    rows = []
    summary = {"campaign": "452A_memory_nonsaturated", "validity": "production",
               "topk": 3, "budgets": BUDGETS, "seeds": SEEDS,
               "ci_method": "percentile bootstrap, seed-as-unit (PROVISIONAL, pending Dr. Qian)",
               "cells": {}}
    for prof in PROFILES:
        for bud in BUDGETS:
            a1 = [idx.get((prof, "A01_FALSE_OBSERVATION", bud, s)) for s in SEEDS]
            ccr = [x["rates"]["ccr"] for x in a1 if x]
            mtr = [x["rates"]["mtr"] for x in a1 if x]
            ris = [x["rates"]["ris"] for x in a1 if x]
            mrank = [x.get("retrieval_competition", {}).get("malicious_rank_min") for x in a1 if x]
            present = [1.0 if (x["rates"]["ccr"] > 0) else 0.0 for x in a1 if x]
            disp = []
            for s in SEEDS:
                a = idx.get((prof, "A01_FALSE_OBSERVATION", bud, s))
                c = idx.get((prof, "A00_CLEAN", 0, s))
                if a and c:
                    disp.append(sum(paired_clean_displacement(c, a).values()))
            cell = {
                "n": len([x for x in a1 if x]),
                "ccr": _boot_ci(ccr), "mtr": _boot_ci(mtr), "ris": _boot_ci(ris),
                "poison_presence_rate": round(statistics.fmean(present), 4) if present else None,
                "malicious_rank_min": _boot_ci([r for r in mrank if r is not None]),
                "clean_displacement_total": _boot_ci(disp),
            }
            summary["cells"][f"{prof}|budget-{bud}"] = cell
            rows.append([prof, bud, cell["n"], *cell["ccr"], cell["poison_presence_rate"],
                         *cell["malicious_rank_min"], *cell["clean_displacement_total"]])
    with open(os.path.join(OUT, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "per_profile_budget.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["profile", "budget", "n", "ccr_mean", "ccr_lo", "ccr_hi",
                    "poison_presence_rate", "mrank_mean", "mrank_lo", "mrank_hi",
                    "disp_mean", "disp_lo", "disp_hi"])
        w.writerows(rows)
    print("wrote", OUT)
    print(f"{'profile':24s} {'bud':>3s} {'CCR':>18s} {'presence':>9s} {'mrank':>14s} {'disp':>16s}")
    for prof in PROFILES:
        for bud in BUDGETS:
            c = summary["cells"][f"{prof}|budget-{bud}"]
            print(f"{prof:24s} {bud:>3} {str(c['ccr']):>18s} {str(c['poison_presence_rate']):>9s} "
                  f"{str(c['malicious_rank_min']):>14s} {str(c['clean_displacement_total']):>16s}")


if __name__ == "__main__":
    main()
