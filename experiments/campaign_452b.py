"""452B campaign aggregation (top-k x poison-budget), memory fixed = MEM060_OPERATIONAL.

Reads production RET bundles from results_v3_raw/ (symmetric k in {3,5,10,20} — k=3 reused
from 452A; plus the exact asymmetric scout3/sup5 baseline), pairs A01 with the matched A00
control at the SAME top-k label + seed, and writes results_v3_campaigns/452B_topk_budget/.
Reports CCR/MTR/RIS, per-role CCR (scout vs supervisor), poison-presence, malicious-rank,
corrected clean-displacement, seed-as-unit bootstrap CIs. Pure aggregation; no runs.
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

MEM = "MEM060_OPERATIONAL"
SEEDS = list(range(101, 111))
# symmetric cells (skip budget>k as redundant saturation) + the asymmetric baseline
SYM = {"03": [1, 2, 3], "05": [1, 2, 3, 5], "10": [1, 2, 3, 5], "20": [1, 2, 3, 5]}
ASYM_LABEL = "s03-p05"
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452B_topk_budget")


def _ci(vals, iters=2000, a=0.05):
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return (None, None, None)
    m = statistics.fmean(vals)
    if len(set(vals)) == 1 or len(vals) < 2:
        return (round(m, 4), round(min(vals), 4), round(max(vals), 4))
    rng = random.Random(0)
    d = sorted(statistics.fmean(rng.choices(vals, k=len(vals))) for _ in range(iters))
    return (round(m, 4), round(d[int(a / 2 * iters)], 4), round(d[int((1 - a / 2) * iters)], 4))


def _topk_label(path):
    for seg in path.split(os.sep):
        if seg.startswith("topk-"):
            return seg[len("topk-"):]
    return None


def _index():
    """(topk_label, attack, budget, seed) -> {metrics, trace}; production only."""
    idx = {}
    for m in glob.glob(P.RESULTS_V3_RAW + f"/**/{MEM}/RET/**/manifest.json", recursive=True):
        d = os.path.dirname(m)
        man = json.load(open(m))
        if man.get("validity") != "production":
            continue
        can = man.get("canonical") or {}
        atk, seed, bud = can.get("attack"), man.get("seed"), man.get("budget")
        if atk not in ("A00_CLEAN", "A01_FALSE_OBSERVATION"):
            continue
        label = _topk_label(os.path.relpath(d, P.RESULTS_V3_RAW))
        met = json.load(open(os.path.join(d, "metrics.json")))
        tr = [json.loads(l) for l in open(os.path.join(d, "retrieval_trace.jsonl")) if l.strip()]
        idx[(label, atk, bud, seed)] = {"met": met, "trace": tr}
    return idx


def _role_ccr(trace):
    scout = [r.get("ccr") for r in trace if r.get("agent") in ("Agent 1", "Agent 2")]
    sup = [r.get("ccr") for r in trace if r.get("agent") == "Supervisor"]
    return (statistics.fmean(scout) if scout else None, sup[0] if sup else None)


def _cell(idx, label, bud):
    a1 = [idx.get((label, "A01_FALSE_OBSERVATION", bud, s)) for s in SEEDS]
    ccr = [x["met"]["rates"]["ccr"] for x in a1 if x]
    mtr = [x["met"]["rates"]["mtr"] for x in a1 if x]
    ris = [x["met"]["rates"]["ris"] for x in a1 if x]
    mrank = [x["met"].get("retrieval_competition", {}).get("malicious_rank_min") for x in a1 if x]
    present = [1.0 if x["met"]["rates"]["ccr"] > 0 else 0.0 for x in a1 if x]
    roles = [_role_ccr(x["trace"]) for x in a1 if x]
    scout_ccr = [r[0] for r in roles if r[0] is not None]
    sup_ccr = [r[1] for r in roles if r[1] is not None]
    disp = []
    for s in SEEDS:
        a = idx.get((label, "A01_FALSE_OBSERVATION", bud, s))
        c = idx.get((label, "A00_CLEAN", 0, s))
        if a and c:
            disp.append(sum(paired_clean_displacement(c["met"], a["met"]).values()))
    return {"n": len([x for x in a1 if x]), "ccr": _ci(ccr), "mtr": _ci(mtr), "ris": _ci(ris),
            "poison_presence_rate": round(statistics.fmean(present), 4) if present else None,
            "malicious_rank_min": _ci([r for r in mrank if r is not None]),
            "scout_ccr": _ci(scout_ccr), "supervisor_ccr": _ci(sup_ccr),
            "clean_displacement_total": _ci(disp)}


def main():
    idx = _index()
    os.makedirs(OUT, exist_ok=True)
    summary = {"campaign": "452B_topk_budget", "validity": "production", "memory": MEM,
               "seeds": SEEDS, "ci_method": "percentile bootstrap seed-as-unit (PROVISIONAL, pending Dr. Qian)",
               "symmetric": {}, "asymmetric_baseline": {}}
    rows = []
    for label, buds in SYM.items():
        for b in buds:
            c = _cell(idx, label, b)
            summary["symmetric"][f"topk-{label}|budget-{b}"] = c
            rows.append(["sym", label, b, c["n"], *c["ccr"], c["poison_presence_rate"],
                         *c["malicious_rank_min"], c["scout_ccr"][0], c["supervisor_ccr"][0],
                         *c["clean_displacement_total"]])
    # asymmetric baseline (scout3/sup5, budget 3)
    ca = _cell(idx, ASYM_LABEL, 3)
    summary["asymmetric_baseline"] = ca
    rows.append(["asym", ASYM_LABEL, 3, ca["n"], *ca["ccr"], ca["poison_presence_rate"],
                 *ca["malicious_rank_min"], ca["scout_ccr"][0], ca["supervisor_ccr"][0],
                 *ca["clean_displacement_total"]])
    with open(os.path.join(OUT, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "per_cell.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["kind", "topk", "budget", "n", "ccr_mean", "ccr_lo", "ccr_hi",
                    "poison_presence", "mrank_mean", "mrank_lo", "mrank_hi",
                    "scout_ccr_mean", "supervisor_ccr_mean", "disp_mean", "disp_lo", "disp_hi"])
        w.writerows(rows)
    print("wrote", OUT)
    print(f"{'topk':10s} {'bud':>3s} {'CCR':>8s} {'scout':>6s} {'sup':>6s} {'presence':>8s} {'mrank':>6s}")
    for label, buds in SYM.items():
        for b in buds:
            c = summary["symmetric"][f"topk-{label}|budget-{b}"]
            print(f"topk-{label:5s} {b:>3} {c['ccr'][0]:>8} {str(c['scout_ccr'][0]):>6} {str(c['supervisor_ccr'][0]):>6} {c['poison_presence_rate']:>8} {c['malicious_rank_min'][0]:>6}")
    print(f"ASYM s03-p05  3 {ca['ccr'][0]:>8} {ca['scout_ccr'][0]:>6} {ca['supervisor_ccr'][0]:>6} {ca['poison_presence_rate']:>8} {ca['malicious_rank_min'][0]:>6}")


if __name__ == "__main__":
    main()
