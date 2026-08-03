"""P1 threat-model-realism campaign aggregation (Reviewers 452B-B1, 452C-C1).

Reads the P1 production bundles (filtered by the P1 prereg hash): RET across attacks
{A00,A01,A04,A05,A06} x defenses {D0,D1} x seeds, and PLAN {A05,A06} x {gpt-oss,qwen} x seeds.
RET metric = CCR (poison share of top-k). PLAN metric = coordinate_adoption (planner routes a
goto waypoint to the TRAP; the canonical planner-hijack field, same as the paper's CHR and 452B-1)
read from parsed_actions.json -- NOT rates.asr (a different propagation metric). Runs the accept
gate. Pure aggregation; runs nothing.
"""
import csv
import glob
import hashlib
import json
import os
import statistics
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uavsys import paths as P  # noqa: E402

PREREG = "docs/preregistration/PREREG_P1_threat_model_realism.md"
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "452B-2_threat_model_practicality")
WRITE_PATH = {"A00_CLEAN": "clean control", "A01_FALSE_OBSERVATION": "unauthenticated direct write",
              "A04_SIGNED_CONFLICT": "signed (valid insider key)",
              "A05_SIGNED_FALSE_OBSERVATION": "signed (valid insider key)",
              "A06_PERCEPTION_FALSE_STATE": "legitimate perception ingestion (no direct write)"}


def _p1hash():
    return hashlib.sha256(open(PREREG, "rb").read()).hexdigest()


def collect():
    ph = _p1hash()
    ret = defaultdict(list)   # (attack, defense) -> [ccr]
    plan = defaultdict(list)  # (attack, model) -> [(adopt, valid)]
    seen = {"RET": set(), "PLAN": set()}
    for m in glob.glob(P.RESULTS_V3_RAW + "/**/manifest.json", recursive=True):
        man = json.load(open(m))
        if (man.get("configured") or {}).get("prereg_spec_hash") != ph or man.get("validity") != "production":
            continue
        d = os.path.dirname(m)
        can = man.get("canonical") or {}
        atk, ev, dfn = can.get("attack"), can.get("evaluation"), can.get("defense")
        seed, model = man.get("seed"), man.get("model")
        if ev == "RET":
            met = json.load(open(os.path.join(d, "metrics.json")))
            ret[(atk, dfn)].append(met.get("rates", {}).get("ccr"))
            seen["RET"].add((atk, dfn, seed))
        elif ev == "PLAN":
            pa = json.load(open(os.path.join(d, "parsed_actions.json")))
            plan[(atk, model)].append((bool(pa.get("coordinate_adoption")), bool(pa.get("valid_plan"))))
            seen["PLAN"].add((atk, model, seed))
    return ret, plan, seen, ph


def accept_gate(ret, plan, seen):
    p = []
    if len(seen["RET"]) != 100:
        p.append(f"expected 100 RET runs, found {len(seen['RET'])}")
    if len(seen["PLAN"]) != 40:
        p.append(f"expected 40 PLAN runs, found {len(seen['PLAN'])}")
    for dfn in ("D0", "D1"):
        c = ret.get(("A00_CLEAN", dfn), [])
        if any(x != 0.0 for x in c):
            p.append(f"A00 control CCR != 0 at {dfn}")
    return p


def main():
    audit = "--audit" in sys.argv
    ret, plan, seen, ph = collect()
    os.makedirs(OUT, exist_ok=True)
    problems = accept_gate(ret, plan, seen)
    ret_rows = []
    for (atk, dfn), v in sorted(ret.items()):
        vv = [x for x in v if x is not None]
        ret_rows.append([atk, dfn, len(vv), round(statistics.fmean(vv), 4) if vv else None, WRITE_PATH.get(atk, "")])
    plan_rows = []
    for (atk, model), v in sorted(plan.items()):
        adopt = statistics.fmean([1.0 if a else 0.0 for a, _ in v]) if v else None
        valid = statistics.fmean([1.0 if q else 0.0 for _, q in v]) if v else None
        plan_rows.append([atk, model, len(v), round(adopt, 3) if adopt is not None else None,
                          round(valid, 3) if valid is not None else None])
    with open(os.path.join(OUT, "ret_by_attack_defense.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["attack", "defense", "n", "ccr_mean", "write_path"]); w.writerows(ret_rows)
    with open(os.path.join(OUT, "plan_adoption.csv"), "w", newline="") as f:
        w = csv.writer(f); w.writerow(["attack", "model", "n", "coordinate_adoption", "valid_plan"]); w.writerows(plan_rows)
    json.dump({"campaign": "452B-2_threat_model_practicality", "prereg_spec_hash": ph,
               "n_ret": len(seen["RET"]), "n_plan": len(seen["PLAN"]), "accept_gate_problems": problems,
               "note": "PLAN metric = parsed_actions.coordinate_adoption (canonical planner-hijack), NOT rates.asr"},
              open(os.path.join(OUT, "summary.json"), "w"), indent=2)
    print("wrote", OUT)
    print(f"RET runs={len(seen['RET'])}/100  PLAN runs={len(seen['PLAN'])}/40  accept-gate problems={len(problems)}")
    if audit:
        for x in problems:
            print("  PROBLEM:", x)
    print("\n=== RET: CCR by attack x defense (write path) ===")
    for r in ret_rows:
        print(f"  {r[0]:32} {r[1]:3} n={r[2]:2} CCR={r[3]}   [{r[4]}]")
    print("\n=== PLAN: planner coordinate_adoption by attack x model ===")
    for r in plan_rows:
        print(f"  {r[0]:32} {r[1]:14} n={r[2]:2} adoption={r[3]}  valid_plan={r[4]}")


if __name__ == "__main__":
    main()
