"""452A Part 2 campaign aggregation — logical agent-count x task-assignment (L3 exposure).

Reads the production L3/MULTI bundles from results_v3_raw/ (A00_CLEAN + A01_FALSE_OBSERVATION
x scouts{2,4,8,16} x assignment{fixed,random,dynamic} x seeds 101-110) at the frozen operating
point (MEM060_OPERATIONAL, top-k 3, budget 3, D0, T01), and writes a campaign under
results_v3_campaigns/452A_part2_agents_assignment/.

Manipulation checks (query-opportunity, coverage) are reported SEPARATELY from empirical
outcomes (cross-scout exposure, blast radius, supervisor exposure). Neutral framing: the
assignment effect on the exposure OUTCOME may increase/preserve/reduce; determined empirically.
Production bundles only. Pure aggregation; runs nothing.

Also runs the ACCEPT-GATE audit (invoke with --audit): 240 production bundles present;
A00<->A01 assignment maps identical per cell/seed (poison-blindness); A00 exposure == 0;
attacked_subtask identical across policies per seed; provenance present; no preflight leakage.
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

SCOUTS = [2, 4, 8, 16]
POLICIES = ["fixed", "random", "dynamic"]
SEEDS = list(range(101, 111))
OPPOINT = {"memory": "MEM060_OPERATIONAL", "topk": 3, "budget_a01": 3, "task": "T01_SEARCH_RESCUE"}
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452A_part2_agents_assignment")


def _boot_ci(vals, iters=2000, alpha=0.05):
    """95% percentile bootstrap CI, seed-as-unit. PROVISIONAL pending Dr. Qian."""
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
    """(attack, scout_count, policy, seed) -> {dir, manifest, metrics}; production only,
    at the frozen operating point (MEM060, topk 3, A01 budget 3 / A00 budget 0)."""
    idx = {}
    for m in glob.glob(P.RESULTS_V3_RAW + "/**/MULTI/**/manifest.json", recursive=True):
        d = os.path.dirname(m)
        man = json.load(open(m))
        if man.get("validity") != "production":
            continue
        can = man.get("canonical") or {}
        atk, seed = can.get("attack"), man.get("seed")
        if can.get("memory") != OPPOINT["memory"] or atk not in ("A00_CLEAN", "A01_FALSE_OBSERVATION"):
            continue
        met = json.load(open(os.path.join(d, "metrics.json")))
        sc, pol = met.get("scout_count"), met.get("assignment_policy")
        bud = man.get("budget")
        topk = (man.get("resolved_params") or {}).get("top_k")
        if topk not in (OPPOINT["topk"], None):          # frozen operating point only
            continue
        if atk == "A01_FALSE_OBSERVATION" and bud not in (3,):
            continue
        if atk == "A00_CLEAN" and bud not in (0, None):
            continue
        idx[(atk, sc, pol, seed)] = {"dir": d, "manifest": man, "metrics": met}
    return idx


def aggregate(idx):
    cells = []
    for sc in SCOUTS:
        total = sc + 1
        for pol in POLICIES:
            a1 = [idx.get(("A01_FALSE_OBSERVATION", sc, pol, s)) for s in SEEDS]
            a0 = [idx.get(("A00_CLEAN", sc, pol, s)) for s in SEEDS]
            a1p = [x for x in a1 if x]
            a0p = [x for x in a0 if x]
            g = lambda xs, k: [x["metrics"].get(k) for x in xs]  # noqa: E731
            cell = {
                "scout_count": sc, "total_agents": total, "assignment_policy": pol,
                "n_A01": len(a1p), "n_A00": len(a0p),
                # manipulation checks (by construction; NOT attack-effectiveness)
                "manip_opportunity_fraction": _boot_ci(g(a1p, "scout_target_query_opportunity_fraction")),
                "manip_assignment_coverage": _boot_ci(g(a1p, "assignment_coverage")),
                # empirical outcomes (A01)
                "out_cross_scout_exposure": _boot_ci(g(a1p, "cross_scout_exposure")),
                "out_blast_fraction": _boot_ci(g(a1p, "total_fleet_blast_radius_fraction")),
                "out_blast_count_mean": round(statistics.fmean(g(a1p, "total_fleet_blast_radius_count")), 4) if a1p else None,
                "out_supervisor_exposure_rate": round(statistics.fmean([1.0 if x["metrics"].get("supervisor_exposure") else 0.0 for x in a1p]), 4) if a1p else None,
                "out_targeted_exposure": _boot_ci(g(a1p, "retrieval_exposure_among_targeted_scouts")),
                # control
                "ctrl_A00_blast_fraction_mean": round(statistics.fmean(g(a0p, "total_fleet_blast_radius_fraction")), 4) if a0p else None,
            }
            cells.append(cell)
    return cells


def audit(idx):
    problems = []
    n_prod = len(idx)
    if n_prod != 240:
        problems.append(f"expected 240 production bundles, found {n_prod}")
    for sc in SCOUTS:
        for pol in POLICIES:
            for s in SEEDS:
                a1 = idx.get(("A01_FALSE_OBSERVATION", sc, pol, s))
                a0 = idx.get(("A00_CLEAN", sc, pol, s))
                if not a1 or not a0:
                    problems.append(f"missing bundle sc{sc}/{pol}/seed{s} A01={bool(a1)} A00={bool(a0)}")
                    continue
                # poison-blindness: identical assignment map for A00 and A01 at a cell
                if a1["metrics"].get("assignment_map") != a0["metrics"].get("assignment_map"):
                    problems.append(f"assignment map differs A00 vs A01 at sc{sc}/{pol}/seed{s}")
                # attacked_subtask schedule identical across arms
                if a1["metrics"].get("attacked_subtask") != a0["metrics"].get("attacked_subtask"):
                    problems.append(f"attacked_subtask differs across arms sc{sc}/{pol}/seed{s}")
                # A00 control must show zero exposure
                if a0["metrics"].get("total_fleet_blast_radius_count") not in (0,):
                    problems.append(f"A00 control exposure != 0 at sc{sc}/{pol}/seed{s}")
                # provenance present
                cfg = a1["manifest"].get("configured") or {}
                if not cfg.get("prereg_spec_hash") or not a1["manifest"].get("embedder", {}).get("digest"):
                    problems.append(f"missing provenance (prereg/embedder) sc{sc}/{pol}/seed{s}")
    # attacked_subtask identical across POLICIES for a given seed (schedule is policy-independent)
    for sc in SCOUTS:
        for s in SEEDS:
            vals = {idx[("A01_FALSE_OBSERVATION", sc, p, s)]["metrics"]["attacked_subtask"]
                    for p in POLICIES if idx.get(("A01_FALSE_OBSERVATION", sc, p, s))}
            if len(vals) > 1:
                problems.append(f"attacked_subtask varies across policies sc{sc}/seed{s}: {vals}")
    return problems


def main():
    do_audit = "--audit" in sys.argv
    idx = _index()
    os.makedirs(OUT, exist_ok=True)
    problems = audit(idx)
    cells = aggregate(idx)
    summary = {"campaign": "452A_part2_agents_assignment", "validity": "production",
               "operating_point": OPPOINT, "scope": ("logical retrieval exposure only; NOT planner "
               "adoption, mission failure, physical propagation, or external systems"),
               "ci_method": "percentile bootstrap, seed-as-unit (PROVISIONAL, pending Dr. Qian)",
               "n_production_bundles": len(idx), "accept_gate_problems": problems,
               "cells": cells}
    with open(os.path.join(OUT, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "fleet_by_assignment.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scout_count", "total_agents", "policy", "n_A01", "n_A00",
                    "manip_opportunity_frac", "manip_coverage",
                    "cross_scout_exposure_mean", "cs_lo", "cs_hi",
                    "blast_fraction_mean", "bf_lo", "bf_hi", "blast_count_mean",
                    "supervisor_exposure_rate", "targeted_exposure_mean", "A00_blast_frac"])
        for c in cells:
            w.writerow([c["scout_count"], c["total_agents"], c["assignment_policy"], c["n_A01"], c["n_A00"],
                        c["manip_opportunity_fraction"][0], c["manip_assignment_coverage"][0],
                        *c["out_cross_scout_exposure"], *c["out_blast_fraction"], c["out_blast_count_mean"],
                        c["out_supervisor_exposure_rate"], c["out_targeted_exposure"][0],
                        c["ctrl_A00_blast_fraction_mean"]])
    print("wrote", OUT)
    print(f"production bundles: {len(idx)}/240   accept-gate problems: {len(problems)}")
    if do_audit:
        for p in problems[:40]:
            print("  PROBLEM:", p)
    print()
    hdr = f"{'scouts':>6} {'total':>5} {'policy':>8} | {'opp':>5} {'cov':>5} || {'cross_scout':>22} {'blast_frac':>22} {'sup':>5} {'A00':>4}"
    print(hdr); print("-" * len(hdr))
    for c in cells:
        cs = c["out_cross_scout_exposure"]; bf = c["out_blast_fraction"]
        print(f"{c['scout_count']:>6} {c['total_agents']:>5} {c['assignment_policy']:>8} | "
              f"{c['manip_opportunity_fraction'][0]!s:>5} {c['manip_assignment_coverage'][0]!s:>5} || "
              f"{f'{cs[0]} [{cs[1]},{cs[2]}]':>22} {f'{bf[0]} [{bf[1]},{bf[2]}]':>22} "
              f"{c['out_supervisor_exposure_rate']!s:>5} {c['ctrl_A00_blast_fraction_mean']!s:>4}")


if __name__ == "__main__":
    main()
