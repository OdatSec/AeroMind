# AeroMind V2 Results — Provenance & Rules

This directory holds **all** evidence for the AeroMind V2 campaign. It is the
**only** writable results root (enforced in code by `uavsys/paths.py`).

## Origin
- Legacy RAID results were produced **before** the V2 campaign and now live,
  unchanged, under `results_legacy_raid/` as **read-only evidence**.
- The V2 results branch (`revision/v2`) is based on commit
  `24ffb50bb2c1eb8219be72b28cdf686ab983d95f`; this migration was recorded at
  commit `1ee3ba3f53b5b03b35a118c2c73ff0224fee7f45`.

## Non-negotiable rules
1. **Never mix legacy and V2 results.** `results_legacy_raid/` (legacy) and
   `results_v2_frozen/` (V2) must not appear together in the same table, plot,
   or aggregate. Legacy values are for reproduction comparison only.
2. **Legacy is read-only.** Do not write into, edit, or delete anything under
   `results_legacy_raid/`. V2 code is guarded to refuse writes there.
3. **All new V2 runs write only here**, under `results_v2_frozen/`.
4. **No result is valid unless it was generated from committed code** with a
   recorded **commit hash** and **config hash** in its run bundle. Results from
   uncommitted or unversioned code are not admissible evidence.

## Layout (created lazily by runs)
`results_v2_frozen/attacks/<scenario>/<mode>.json`, plus per-campaign
subdirectories (e.g. `agent_scaling/`, `k_sensitivity/`). Raw run bundles are
git-ignored; only this document is tracked.
