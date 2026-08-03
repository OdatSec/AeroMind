"""V3 campaign layer: turn a set of raw run bundles into a human-readable campaign.

Reads finished bundle directories (each with a manifest.json), pairs clean vs
attack by seed, and writes, under results_v3_campaigns/<CAMPAIGN>/:
  README.md, campaign_summary.json, paired_results.csv, bundle_index.yaml,
  INSIGHTS_DRAFT.md, CLAIMS.md
and refreshes results_v3_campaigns/INDEX.md.

INSIGHTS_DRAFT.md is auto-generated (a DRAFT). PAPER_FINDINGS.md is NEVER written
here — promotion into it is a human-only step.

Pure I/O over already-produced bundles; runs no experiments.
"""
from __future__ import annotations

import csv
import io
import json
import os
from typing import Any, Dict, List, Optional

from .paths import RESULTS_V3_CAMPAIGNS

PAPER_FINDINGS = os.path.join(RESULTS_V3_CAMPAIGNS, "PAPER_FINDINGS.md")
INDEX = os.path.join(RESULTS_V3_CAMPAIGNS, "INDEX.md")


def _read_manifest(bundle_dir: str) -> dict:
    with open(os.path.join(bundle_dir, "manifest.json")) as f:
        return json.load(f)


def _read_parsed(bundle_dir: str) -> dict:
    p = os.path.join(bundle_dir, "parsed_actions.json")
    return json.load(open(p)) if os.path.exists(p) else {}


def _campaign_name(attack: str, task: str, memory: str, evaluation: str) -> str:
    return f"{attack}__{task}__{memory}__{evaluation}"


def _outcome_field(evaluation: str) -> str:
    """The headline per-run outcome for a given evaluation/attack family."""
    return {"RET": "ccr", "PLAN": "planner_outcome"}.get(evaluation, "outcome")


def build_campaign(
    *,
    attack: str, task: str, memory: str, evaluation: str,
    clean_bundles: List[str], attack_bundles: List[str],
    research_question: str = "",
    reviewer_concern: str = "",
    supported_claim: str = "",
    caveats: Optional[List[str]] = None,
    recommended_figure: str = "",
    campaigns_root: str = RESULTS_V3_CAMPAIGNS,
) -> str:
    """Assemble one campaign folder from raw bundles. Returns the folder path."""
    name = _campaign_name(attack, task, memory, evaluation)
    out = os.path.join(campaigns_root, name)
    os.makedirs(out, exist_ok=True)

    def rows(dirs, arm):
        r = []
        for d in dirs:
            m = _read_manifest(d)
            pa = _read_parsed(d)
            r.append({
                "arm": arm, "seed": m.get("seed"), "run_id": m.get("run_id"),
                "outcome": m.get("outcome"),
                "valid_plan": (pa.get("valid_plan") if pa else None),
                "coordinate_adoption": pa.get("coordinate_adoption") if pa else None,
                "target_omission_rate": pa.get("target_omission_rate") if pa else None,
                "unsafe_entry": (pa.get("unsafe_entry", {}) or {}).get("unsafe_entry")
                                 if isinstance(pa.get("unsafe_entry"), dict) else pa.get("unsafe_entry"),
                "dir": os.path.relpath(d, campaigns_root),
                "canonical": m.get("canonical"),
            })
        return r

    clean_rows = rows(clean_bundles, "clean")
    attack_rows = rows(attack_bundles, "attack")
    all_rows = clean_rows + attack_rows

    def denom(rws):
        attempted = len(rws)
        valid = sum(1 for x in rws if x["valid_plan"] is True) if any(x["valid_plan"] is not None for x in rws) else attempted
        return attempted, valid

    ca, cv = denom(clean_rows)
    aa, av = denom(attack_rows)
    summary = {
        "campaign": name,
        "attack": attack, "task": task, "memory": memory, "evaluation": evaluation,
        "clean_arm": {"attempted": ca, "valid": cv, "bundles": len(clean_bundles)},
        "attack_arm": {"attempted": aa, "valid": av, "bundles": len(attack_bundles)},
        "research_question": research_question,
        "reviewer_concern": reviewer_concern,
        "supported_claim": supported_claim,
        "recommended_figure": recommended_figure,
    }
    with open(os.path.join(out, "campaign_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)

    # paired_results.csv
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["arm", "seed", "outcome", "valid_plan", "coordinate_adoption",
                "target_omission_rate", "unsafe_entry", "run_id"])
    for x in sorted(all_rows, key=lambda r: (r["arm"], r["seed"] if r["seed"] is not None else -1)):
        w.writerow([x["arm"], x["seed"], x["outcome"], x["valid_plan"],
                    x["coordinate_adoption"], x["target_omission_rate"], x["unsafe_entry"], x["run_id"]])
    with open(os.path.join(out, "paired_results.csv"), "w") as f:
        f.write(buf.getvalue())

    # bundle_index.yaml (minimal YAML, no external dep)
    with open(os.path.join(out, "bundle_index.yaml"), "w") as f:
        f.write(f"campaign: {name}\nclean_bundles:\n")
        for x in clean_rows:
            f.write(f"  - seed: {x['seed']}\n    dir: {x['dir']}\n    run_id: {x['run_id']}\n")
        f.write("attack_bundles:\n")
        for x in attack_rows:
            f.write(f"  - seed: {x['seed']}\n    dir: {x['dir']}\n    run_id: {x['run_id']}\n")

    # README.md
    with open(os.path.join(out, "README.md"), "w") as f:
        f.write(f"# Campaign {name}\n\n"
                f"- Attack: `{attack}` | Task: `{task}` | Memory: `{memory}` | Eval: `{evaluation}`\n"
                f"- Clean bundles: {len(clean_bundles)} (attempted {ca}, valid {cv})\n"
                f"- Attack bundles: {len(attack_bundles)} (attempted {aa}, valid {av})\n\n"
                f"See `campaign_summary.json`, `paired_results.csv`, `bundle_index.yaml`, "
                f"`INSIGHTS_DRAFT.md` (auto, DRAFT), `CLAIMS.md`.\n")

    _write_insights(out, name, attack, task, memory, evaluation, clean_rows, attack_rows,
                    research_question, reviewer_concern, supported_claim, caveats or [],
                    recommended_figure)
    _write_claims(out, name, supported_claim, caveats or [])
    refresh_index(campaigns_root)
    return out


def _write_insights(out, name, attack, task, memory, evaluation, clean_rows, attack_rows,
                    rq, reviewer, claim, caveats, figure):
    def rate(rws, key):
        vals = [x[key] for x in rws if x[key] is not None]
        if not vals:
            return None
        num = sum(1 for v in vals if v) if all(isinstance(v, bool) for v in vals) else sum(vals) / len(vals)
        return round(num / len(vals), 4) if all(isinstance(v, bool) for v in vals) else round(num, 4)
    cav = "\n".join(f"- {c}" for c in caveats) or "- (none recorded)"
    with open(os.path.join(out, "INSIGHTS_DRAFT.md"), "w") as f:
        f.write(
            f"# INSIGHTS (DRAFT — not a paper finding) — {name}\n\n"
            f"> Auto-generated. NOT promoted to PAPER_FINDINGS.md; human approval required.\n\n"
            f"## Research question\n{rq or '(fill in)'}\n\n"
            f"## Clean vs attack\n"
            f"- Clean arm: {len(clean_rows)} bundles; "
            f"coordinate_adoption={rate(clean_rows,'coordinate_adoption')}, "
            f"omission={rate(clean_rows,'target_omission_rate')}, "
            f"unsafe_entry={rate(clean_rows,'unsafe_entry')}\n"
            f"- Attack arm: {len(attack_rows)} bundles; "
            f"coordinate_adoption={rate(attack_rows,'coordinate_adoption')}, "
            f"omission={rate(attack_rows,'target_omission_rate')}, "
            f"unsafe_entry={rate(attack_rows,'unsafe_entry')}\n\n"
            f"## Exact denominators\n"
            f"- clean attempted={len(clean_rows)}; attack attempted={len(attack_rows)}. "
            f"Behavioural rates use valid-plan denominators (see paired_results.csv).\n\n"
            f"## Why it matters\n{claim or '(fill in)'}\n\n"
            f"## Reviewer concern addressed\n{reviewer or '(fill in)'}\n\n"
            f"## Supported paper claim (candidate)\n{claim or '(fill in)'}\n\n"
            f"## Caveats / prohibited overclaims\n{cav}\n\n"
            f"## Recommended table/figure\n{figure or '(fill in)'}\n\n"
            f"## Exact raw-bundle references\n"
            + "".join(f"- {x['arm']} seed {x['seed']}: `{x['dir']}`\n" for x in clean_rows + attack_rows)
        )


def _write_claims(out, name, claim, caveats):
    with open(os.path.join(out, "CLAIMS.md"), "w") as f:
        f.write(f"# CLAIMS — {name}\n\n"
                f"Candidate claim (requires human approval before use):\n\n> {claim or '(fill in)'}\n\n"
                f"## Prohibited overclaims / scope limits\n"
                + ("\n".join(f"- {c}" for c in caveats) or "- (none recorded)") + "\n")


def refresh_index(campaigns_root: str = RESULTS_V3_CAMPAIGNS) -> str:
    """Rebuild INDEX.md listing every campaign folder present."""
    os.makedirs(campaigns_root, exist_ok=True)
    entries = []
    for d in sorted(os.listdir(campaigns_root)):
        full = os.path.join(campaigns_root, d)
        s = os.path.join(full, "campaign_summary.json")
        if os.path.isdir(full) and os.path.exists(s):
            entries.append(json.load(open(s)))
    idx = os.path.join(campaigns_root, "INDEX.md")
    with open(idx, "w") as f:
        f.write("# V3 Campaign Index\n\n")
        f.write("Auto-generated list of campaigns. Insights are DRAFTs; approved "
                "findings live in `PAPER_FINDINGS.md` (human-curated).\n\n")
        f.write("| Campaign | Attack | Task | Memory | Eval | Clean(att/val) | Attack(att/val) |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for e in entries:
            cl, at = e.get("clean_arm", {}), e.get("attack_arm", {})
            f.write(f"| {e['campaign']} | {e['attack']} "
                    f"| {e['task']} | {e['memory']} | {e['evaluation']} "
                    f"| {cl.get('attempted')}/{cl.get('valid')} | {at.get('attempted')}/{at.get('valid')} |\n")
    return idx
