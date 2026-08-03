"""
Centralized, repo-anchored, guarded output locations for the AeroMind V2
evidence campaign.

Legacy RAID results live under ``<repo>/results/`` (git-ignored, read-only
evidence). The V2 campaign must write *only* under ``<repo>/results_v2_frozen/``
so legacy and V2 numbers can never be silently mixed.

Two properties matter:
  1. **Repo-anchored defaults.** ``RESULTS_ROOT`` is an *absolute* path derived
     from this file's location, so running a script from any working directory
     writes to the one results root inside the repo — never a stray
     ``results_v2_frozen/`` elsewhere.
  2. **A guard that cannot be bypassed by path tricks.** ``assert_writable``
     rejects any path that names a legacy root as a component (``results/...``,
     ``../results/...``, absolute ``.../results/...``) *and* any path that,
     after resolving symlinks and ``..`` relative to the current directory,
     actually lands inside the repo's legacy result directories.

Use ``v2_path(...)`` / ``default_attack_output(...)`` for defaults, and wrap any
caller-supplied path in ``assert_writable(...)`` before creating dirs/writing.
"""
from __future__ import annotations

import os

# Absolute repo root = parent of the uavsys/ package that contains this file.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Writable results root (basename + absolute, repo-anchored path).
RESULTS_ROOT_NAME = "results_v2_frozen"
RESULTS_ROOT = os.path.join(REPO_ROOT, RESULTS_ROOT_NAME)

# Final Campaign V3 roots (additive; V2 root above stays immutable & unchanged).
#   results_v3_raw       — hierarchical raw bundles for future runs
#   results_v3_campaigns — human-readable campaign layer (INDEX/README/insights)
RESULTS_V3_RAW_NAME = "results_v3_raw"
RESULTS_V3_RAW = os.path.join(REPO_ROOT, RESULTS_V3_RAW_NAME)
RESULTS_V3_CAMPAIGNS_NAME = "results_v3_campaigns"
RESULTS_V3_CAMPAIGNS = os.path.join(REPO_ROOT, RESULTS_V3_CAMPAIGNS_NAME)

# Every recognized writable PRODUCTION root (evidence bundles may live under any).
# results_v2_frozen keeps its exact guard; results_v3_raw is a NEW production root.
PRODUCTION_ROOTS = (
    os.path.realpath(RESULTS_ROOT),
    os.path.realpath(RESULTS_V3_RAW),
)


def is_production_root(path: str) -> bool:
    """True if `path` is inside any recognized writable production root."""
    real = os.path.realpath(path)
    return any(real == root or real.startswith(root + os.sep) for root in PRODUCTION_ROOTS)

# Read-only / obsolete roots that V2 code must never write into.
LEGACY_ROOTS = ("results", "results_legacy_raid")
# Their absolute, symlink-resolved locations inside the repo.
_LEGACY_ABS_DIRS = tuple(
    os.path.realpath(os.path.join(REPO_ROOT, name)) for name in LEGACY_ROOTS
)


def v2_path(*parts: str) -> str:
    """Return an absolute, repo-anchored path under the V2 results root."""
    return os.path.join(RESULTS_ROOT, *parts)


def default_attack_output(scenario: str, mode: str) -> str:
    """Default per-scenario output file for the experiment runners."""
    mode_dir = mode.replace("-", "_")
    return v2_path("attacks", scenario.lower(), f"{mode_dir}.json")


def _sanitize(part: str) -> str:
    """Filesystem-safe path segment (e.g. 'gpt-oss:20b' -> 'gpt-oss-20b')."""
    return "".join(c if (c.isalnum() or c in "._-") else "-" for c in str(part))


def _axis(value) -> str:
    """Human-readable axis token. Ints zero-pad to 2 (topk-03, budget-10); None ->
    'default' (budget) / 'na' (temp); floats/strings kept verbatim (temp-0.1)."""
    if value is None:
        return "default"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:02d}"
    return _sanitize(value)


def _scientific_axes(attack, task, memory, evaluation, model, defense,
                     topk, budget, temp, agents=None, backend=None,
                     extra_axes=None) -> list:
    """Ordered scientific-axis path segments shared by raw + campaign hierarchies.

    Order: ATTACK / TASK / MEMORY / EVALUATION / model-<MODEL> / DEFENSE /
    topk-NN / budget-NN / temp-VALUE, then evaluation-specific axes when applicable
    (agents-NN for MULTI, backend-NAME for SITL, plus any explicit extra_axes).
    Operational flags/timestamps/hashes/uuids never appear here (manifest only)."""
    segs = [_sanitize(attack), _sanitize(task), _sanitize(memory), _sanitize(evaluation),
            f"model-{_sanitize(model)}", _sanitize(defense),
            f"topk-{_axis(topk)}", f"budget-{_axis(budget)}", f"temp-{'na' if temp is None else _sanitize(temp)}"]
    if agents is not None:
        segs.append(f"agents-{int(agents):02d}")
    if backend:
        segs.append(f"backend-{_sanitize(backend)}")
    for k, v in (extra_axes or {}).items():
        segs.append(f"{_sanitize(k)}-{_axis(v)}")
    return segs


def v3_raw_run_parent(attack, task, memory, evaluation, model, defense,
                      topk, budget, temp, seed, *, agents=None, backend=None,
                      extra_axes=None, root=None) -> str:
    """Parent directory for one V3 raw run bundle (argument-driven, attack-centered):

      results_v3_raw/<ATTACK>/<TASK>/<MEMORY>/<EVALUATION>/model-<MODEL>/<DEFENSE>/
        topk-NN/budget-NN/temp-VALUE/[agents-NN/][backend-NAME/]seed-XXXX/

    The run bundle is a short-named subdir below this (collision-safe run id); full
    metadata (hashes, uuids, commit, provider, flags) lives in the manifest, not the
    path. `root` overrides the raw root (sandbox tests); production is untouched.
    """
    base = root or RESULTS_V3_RAW
    segs = _scientific_axes(attack, task, memory, evaluation, model, defense,
                            topk, budget, temp, agents, backend, extra_axes)
    return os.path.join(base, *segs, f"seed-{int(seed):04d}")


def v3_campaign_dir(attack, task, memory, evaluation, model, defense,
                    topk, budget, temp, *, agents=None, backend=None,
                    extra_axes=None, root=None) -> str:
    """Campaign folder mirroring the same scientific axes (no seed/run levels):

      results_v3_campaigns/<ATTACK>/<TASK>/<MEMORY>/<EVALUATION>/model-<MODEL>/
        <DEFENSE>/topk-NN/budget-NN/temp-VALUE/[agents-NN/][backend-NAME/]
    """
    base = root or RESULTS_V3_CAMPAIGNS
    segs = _scientific_axes(attack, task, memory, evaluation, model, defense,
                            topk, budget, temp, agents, backend, extra_axes)
    return os.path.join(base, *segs)


def assert_writable(path: str) -> str:
    """Return ``path`` unchanged if safe; raise ``ValueError`` if it targets a
    legacy/obsolete results root.

    Blocks, cwd-independently, any path with a legacy-root component, and,
    after resolving symlinks/``..`` against the current directory, any path that
    lands inside the repo's legacy result directories.
    """
    if not path:
        raise ValueError("Refusing to write to an empty output path")

    # (1) Name-based guard — cwd-independent; catches 'results/...',
    #     '../results/...', and absolute '.../results/...'.
    norm = os.path.normpath(path)
    if any(seg in LEGACY_ROOTS for seg in norm.split(os.sep)):
        raise ValueError(
            f"Refusing to write under a legacy/read-only results root: {path!r}. "
            f"V2 outputs must go under {RESULTS_ROOT!r} (use v2_path(...))."
        )

    # (2) Realpath-containment guard — resolves symlinks and '..' relative to the
    #     current directory; catches anything that actually resolves into the
    #     repo's legacy result directories (e.g. via a symlink).
    real = os.path.realpath(path)
    for legacy_abs in _LEGACY_ABS_DIRS:
        if real == legacy_abs or real.startswith(legacy_abs + os.sep):
            raise ValueError(
                f"Refusing to write into legacy results dir (resolved {real!r} "
                f"from {path!r}). V2 outputs must go under {RESULTS_ROOT!r}."
            )
    return path
