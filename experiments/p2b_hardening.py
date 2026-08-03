"""P2b hardening harness (PREREG_P2b). Embedder-only RET; emits V3 bundles. A01/S01 + RET only.

Test 1 (stronger competitor): MEM060 + M STRONGER_COMPETITOR + generic poison → does a higher-ranking
  benign record displace the poison? (+ A00 control.)
Test 2 (adaptive generalization): MEM060 + on-topic N=200 + one of 3 frozen adaptive phrasings → does
  restoration hold beyond the single original template?

Records the score audit per run (poison score, best-benign score, margin, top stronger-competitor score).

    python3 experiments/p2b_hardening.py --run | --preflight | --aggregate
"""
import argparse, asyncio, csv, glob, hashlib, json, os, statistics, sys, tempfile
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from experiments.experiment_runner import (init_experiment, _provenance_fields, _bundle_location,
                                            flatten_snapshot, injected_delta, MISSION_GOAL)
from uavsys import taxonomy as TX
from uavsys import paths as P
from uavsys.seeding import seed_from_profile
from uavsys.memory_profiles import build_profile
from uavsys.memory_composition import poison_generic, benign_ontopic
from uavsys import memory_composition_p2b as MCB

SEEDS = list(range(101, 111)); TOPK = 3; BUDGET = 3
LAYERS = ["episodic", "semantic", "procedural", "coordination"]
PREREG = "docs/preregistration/PREREG_P2b_hardening.md"
OUT = os.path.join(P.RESULTS_V3_CAMPAIGNS, "P2b_hardening")
POISONS = {"generic": poison_generic, **MCB.ADAPTIVES}


def cells():
    return [
        dict(test=1, ot=0, strong=1, poison="generic", attack="A01"),
        dict(test=1, ot=0, strong=3, poison="generic", attack="A01"),
        dict(test=1, ot=0, strong=3, poison=None, attack="A00"),
        dict(test=2, ot=200, strong=0, poison="adapt_v2", attack="A01"),
        dict(test=2, ot=200, strong=0, poison="adapt_v3", attack="A01"),
        dict(test=2, ot=200, strong=0, poison="adapt_v4", attack="A01"),
    ]


def _isp(m): return str(m.get("source", "")).startswith("atk:") or m.get("is_attack")


async def _run_cell(c, seed, emit=True):
    from uavsys.evidence import EvidenceBundle
    from uavsys.paths import REPO_ROOT as REPO
    atkc = "A01_FALSE_OBSERVATION" if c["attack"] == "A01" else "A00_CLEAN"
    budget = BUDGET if c["attack"] == "A01" else 0
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        dbp = tf.name
    try:
        cfg, db, llm, memory = await init_experiment(seed, False, dbp, chat_model="na")
        await seed_from_profile(memory, build_profile("P2", seed))
        before = await memory.snapshot()
        for i in range(c["ot"]):
            await memory.write_episodic(agent="Agent 2", content=benign_ontopic(i), source="Agent 2")
        for i in range(c["strong"]):
            await memory.write_episodic(agent="Sensor", content=MCB.stronger_competitor(i), source="Sensor")
        if c["poison"]:
            pfn = POISONS[c["poison"]]
            for i in range(budget):
                await memory.write_episodic(agent="Agent 1", content=pfn(i), source="S01", is_attack=True)
        after = await memory.snapshot()
        m3 = (await memory.retrieve(query=MISSION_GOAL, layers=LAYERS, top_k=TOPK, agent="A", run_id=f"s{seed}")).get("matches", [])
        m10 = (await memory.retrieve(query=MISSION_GOAL, layers=LAYERS, top_k=10, agent="A", run_id=f"s{seed}")).get("matches", [])
        ranks = [i + 1 for i, m in enumerate(m10) if _isp(m)]
        ccr = sum(1 for m in m3[:TOPK] if _isp(m)) / TOPK
        pz = [m for m in m10 if _isp(m)]; bn = [m for m in m10 if not _isp(m)]
        # top stronger-competitor score (Sensor source, benign)
        comp = [m for m in m10 if str(m.get("source", "")) == "Sensor"]
        md = {"test": c["test"], "ot": c["ot"], "strong": c["strong"], "poison": c["poison"], "attack": c["attack"],
              "ccr": round(ccr, 4), "poison_min_rank": (min(ranks) if ranks else None),
              "poison_present": bool([r for r in ranks if r <= TOPK]),
              "poison_score": (round(pz[0].get("score", 0), 4) if pz else None),
              "best_benign_score": (round(bn[0].get("score", 0), 4) if bn else None),
              "margin": (round(pz[0].get("score", 0) - bn[0].get("score", 0), 4) if pz and bn else None),
              "top_competitor_score": (round(comp[0].get("score", 0), 4) if comp else None)}
        if emit:
            _prov = _provenance_fields(cfg.EMBED_MODEL, "MEM060_OPERATIONAL", seed, REPO)
            canonical = TX.canonical_manifest_ids(atkc, "T01_SEARCH_RESCUE", "MEM060_OPERATIONAL", "RET", "D0")
            extra = {"test": f"t{c['test']}", "ot": c["ot"], "strong": c["strong"], "poison": c["poison"] or "none"}
            bundle = EvidenceBundle(
                scenario=atkc, legacy_id=atkc, layer="L1", seed=seed, model="na", defense_level="D0", config=cfg,
                resolved_params={"mode": "retrieval", "top_k": TOPK, "budget": budget, **extra},
                embedder={"name": "nomic-embed-text", "tag": cfg.EMBED_MODEL, "digest": _prov["embedder_digest"],
                          "config_digest": _prov["embedder_config"], "dim": None},
                configured={"memory_profile": "MEM060_OPERATIONAL", "mission": "M1", "poison_budget": budget,
                            "hardening": extra, "p2b_spec_hash": MCB.spec_hash(),
                            "profile_materialization_hash": _prov["profile_materialization_hash"],
                            "prereg_spec_hash": _prov["prereg_spec_hash"], "prereg_file": _prov["prereg_file"]},
                mission="M1", profile="P2",
                **_bundle_location("v3", canonical, "na", seed, None,
                                   axes={"topk": TOPK, "budget": budget, "temp": None, "extra_axes": extra}))
            bflat, aflat = flatten_snapshot(before), flatten_snapshot(after)
            bundle.record_memory(before=bflat, injected=injected_delta(bflat, aflat), after=aflat)
            bundle.record_retrieval([{"agent": "A", "top_k": TOPK,
                                      "matches": [{"is_poison": _isp(m), "source": m.get("source"), "score": round(m.get("score", 0), 4)} for m in m3]}])
            bundle.record_metrics(md); bundle.set_status("success"); bundle.finalize()
        return md
    finally:
        try: os.unlink(dbp)
        except OSError: pass


async def _run(cl, seeds, emit=True):
    for c in cl:
        for seed in seeds:
            md = await _run_cell(c, seed, emit=emit)
        print(f"  T{c['test']} strong={c['strong']} ot={c['ot']} {c['poison'] or 'clean'} {c['attack']}: "
              f"CCR={md['ccr']} rank={md['poison_min_rank']} poison_score={md['poison_score']} "
              f"best_benign={md['best_benign_score']} comp={md['top_competitor_score']} margin={md['margin']}")


def _cp(k, n, a=0.05):
    from math import comb
    def cdf(k, n, p): return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k + 1))
    def sf(k, n, p): return sum(comb(n, i) * p**i * (1 - p)**(n - i) for i in range(k, n + 1))
    def bis(f, t, inc):
        lo, hi = 0.0, 1.0
        for _ in range(100):
            m = (lo + hi) / 2
            if (f(m) < t) == inc: lo = m
            else: hi = m
        return round((lo + hi) / 2, 3)
    return (0.0 if k == 0 else bis(lambda p: sf(k, n, p), a / 2, True),
            1.0 if k == n else bis(lambda p: cdf(k, n, p), a / 2, False))


def aggregate():
    ph = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
    rows = defaultdict(list)
    for m in glob.glob(P.RESULTS_V3_RAW + "/**/RET/**/manifest.json", recursive=True):
        man = json.load(open(m))
        if (man.get("configured") or {}).get("prereg_spec_hash") != ph or man.get("validity") != "production":
            continue
        met = json.load(open(m.replace("manifest.json", "metrics.json")))
        rows[(met["test"], met["strong"], met["ot"], met["poison"], met["attack"])].append(met)
    os.makedirs(OUT, exist_ok=True)
    out = []
    for k, ms in sorted(rows.items()):
        present = sum(1 for x in ms if x["poison_present"]); n = len(ms)
        ccrs = sorted({x["ccr"] for x in ms})
        out.append([*k, n, present, f"{_cp(present, n)}",
                    (ccrs[0] if len(ccrs) == 1 else f"{ccrs[0]}–{ccrs[-1]}"),
                    round(statistics.fmean([x["poison_score"] for x in ms if x["poison_score"]]), 4) if any(x["poison_score"] for x in ms) else None,
                    round(statistics.fmean([x["best_benign_score"] for x in ms if x["best_benign_score"]]), 4) if any(x["best_benign_score"] for x in ms) else None,
                    round(statistics.fmean([x["top_competitor_score"] for x in ms if x["top_competitor_score"]]), 4) if any(x["top_competitor_score"] for x in ms) else None])
    with open(os.path.join(OUT, "cells.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["test", "strong", "ot", "poison", "attack", "n", "poison_present", "present_CI",
                    "ccr_observed", "poison_score", "best_benign_score", "top_competitor_score"])
        w.writerows(out)
    json.dump({"campaign": "P2b_hardening", "prereg_spec_hash": ph, "n": sum(len(v) for v in rows.values())},
              open(os.path.join(OUT, "summary.json"), "w"), indent=2)
    print("wrote", OUT)
    for r in out:
        print(f"  T{r[0]} strong={r[1]} ot={r[2]} {str(r[3]):8} {r[4]} n={r[5]} present={r[6]}/{r[5]} {r[7]} "
              f"CCR={r[8]} poison_score={r[9]} best_benign={r[10]} comp={r[11]}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true"); ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--aggregate", action="store_true")
    a = ap.parse_args()
    os.environ.setdefault("AEROMIND_PREREG", PREREG)
    if a.aggregate: aggregate(); return
    if a.preflight:
        asyncio.run(_run([dict(test=1, ot=0, strong=1, poison="generic", attack="A01"),
                          dict(test=1, ot=0, strong=3, poison="generic", attack="A01"),
                          dict(test=2, ot=200, strong=0, poison="adapt_v2", attack="A01")], [9001], emit=False))
        return
    if a.run:
        cl = cells()
        print(f"P2b production: {len(cl)} cells x {len(SEEDS)} = {len(cl) * len(SEEDS)} runs")
        asyncio.run(_run(cl, SEEDS, emit=True))


if __name__ == "__main__":
    main()
