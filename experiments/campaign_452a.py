"""452A Part 1 campaign aggregation (memory generalization).

Reads the production RET bundles from results_v3_raw/ (5 profiles x A00/A01 x seeds
101-110), pairs A00<->A01 per seed, and writes a campaign under
results_v3_campaigns/452A_memory_generalization/ with per-profile CCR/MTR/RIS,
malicious-rank, clean-displacement, and seed-as-unit 95% bootstrap CIs. Production
bundles only. Does not run experiments; pure aggregation over frozen inputs.
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
SEEDS = list(range(101, 111))
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452A_memory_generalization")


def _boot_ci(vals, iters=2000, alpha=0.05):
    """95% percentile bootstrap CI, seed-as-unit. Method PROVISIONAL pending
    Dr. Qian's approval (see coverage audit). Degenerate -> (min,max)."""
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return (None, None, None)
    mean = statistics.fmean(vals)
    if len(set(vals)) == 1 or len(vals) < 2:
        return (round(mean, 4), round(min(vals), 4), round(max(vals), 4))
    rng = random.Random(0)
    means = sorted(statistics.fmean(rng.choices(vals, k=len(vals))) for _ in range(iters))
    lo = means[int(alpha / 2 * iters)]
    hi = means[int((1 - alpha / 2) * iters)]
    return (round(mean, 4), round(lo, 4), round(hi, 4))


def _index():
    """(profile, attack, seed) -> {dir, manifest, metrics}; production only."""
    idx = {}
    for m in glob.glob(P.RESULTS_V3_RAW + "/**/RET/**/manifest.json", recursive=True):
        d = os.path.dirname(m)
        man = json.load(open(m))
        if man.get("validity") != "production":
            continue
        can = man.get("canonical") or {}
        prof = can.get("memory")
        atk = can.get("attack")
        seed = man.get("seed")
        if prof in PROFILES and atk in ("A00_CLEAN", "A01_FALSE_OBSERVATION"):
            met = json.load(open(os.path.join(d, "metrics.json")))
            idx[(prof, atk, seed)] = {"dir": d, "manifest": man, "metrics": met}
    return idx


def main():
    idx = _index()
    os.makedirs(OUT, exist_ok=True)
    rows = []
    summary = {"campaign": "452A_memory_generalization", "validity": "production",
               "topk": 3, "budget": 3, "seeds": SEEDS,
               "ci_method": "percentile bootstrap, seed-as-unit (PROVISIONAL, pending Dr. Qian)",
               "profiles": {}}
    for prof in PROFILES:
        a1 = [idx.get((prof, "A01_FALSE_OBSERVATION", s)) for s in SEEDS]
        a0 = [idx.get((prof, "A00_CLEAN", s)) for s in SEEDS]
        present = [s for s, x in zip(SEEDS, a1) if x] + [s for s, x in zip(SEEDS, a0) if x]
        ccr = [x["metrics"]["rates"]["ccr"] for x in a1 if x]
        mtr = [x["metrics"]["rates"]["mtr"] for x in a1 if x]
        ris = [x["metrics"]["rates"]["ris"] for x in a1 if x]
        mrank = [x["metrics"].get("retrieval_competition", {}).get("malicious_rank_min") for x in a1 if x]
        ctrl_ccr = [x["metrics"]["rates"]["ccr"] for x in a0 if x]
        disp = []
        for s in SEEDS:
            c = idx.get((prof, "A00_CLEAN", s)); a = idx.get((prof, "A01_FALSE_OBSERVATION", s))
            if c and a:
                pcd = paired_clean_displacement(c["metrics"], a["metrics"])
                disp.append(sum(pcd.values()))
        summary["profiles"][prof] = {
            "n_A01": len([x for x in a1 if x]), "n_A00": len([x for x in a0 if x]),
            "ccr": _boot_ci(ccr), "mtr": _boot_ci(mtr), "ris": _boot_ci(ris),
            "malicious_rank_min": _boot_ci([r for r in mrank if r is not None]),
            "clean_displacement_total": _boot_ci(disp),
            "control_A00_ccr_mean": round(statistics.fmean(ctrl_ccr), 4) if ctrl_ccr else None,
        }
        rows.append([prof, len([x for x in a1 if x]),
                     *summary["profiles"][prof]["ccr"], *summary["profiles"][prof]["malicious_rank_min"],
                     *summary["profiles"][prof]["clean_displacement_total"],
                     summary["profiles"][prof]["control_A00_ccr_mean"]])
    with open(os.path.join(OUT, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(OUT, "per_profile.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["profile", "n_A01", "ccr_mean", "ccr_lo", "ccr_hi",
                    "mrank_mean", "mrank_lo", "mrank_hi",
                    "displacement_mean", "displacement_lo", "displacement_hi", "A00_ccr_mean"])
        w.writerows(rows)
    print("wrote", OUT)
    print(f"{'profile':24s} {'CCR(A01)':>18s} {'mrank_min':>14s} {'displacement':>16s}  A00_ccr")
    for prof in PROFILES:
        p = summary["profiles"][prof]
        print(f"{prof:24s} {str(p['ccr']):>18s} {str(p['malicious_rank_min']):>14s} "
              f"{str(p['clean_displacement_total']):>16s}  {p['control_A00_ccr_mean']}")


if __name__ == "__main__":
    main()
