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
