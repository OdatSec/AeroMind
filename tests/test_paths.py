"""
Tests for repo-anchored, guarded V2 output paths (uavsys/paths.py) and a repo
invariant that no runtime/experiment code writes into a legacy results root.

No DB / LLM / PX4. Run: python3 -m pytest tests/test_paths.py
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from uavsys.paths import (  # noqa: E402
    REPO_ROOT, RESULTS_ROOT, RESULTS_ROOT_NAME, LEGACY_ROOTS,
    v2_path, default_attack_output, assert_writable,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- repo anchoring (concern 1) ----
def test_results_root_is_absolute_and_under_repo():
    assert os.path.isabs(RESULTS_ROOT)
    assert RESULTS_ROOT == os.path.join(REPO_ROOT, RESULTS_ROOT_NAME)
    assert os.path.realpath(REPO_ROOT) == os.path.realpath(REPO)


def test_v2_path_is_repo_anchored():
    p = v2_path("attacks", "s01", "retrieval.json")
    assert os.path.isabs(p)
    assert p == os.path.join(RESULTS_ROOT, "attacks", "s01", "retrieval.json")


def test_v2_path_independent_of_cwd(tmp_path):
    """Running from another directory must not relocate the results root."""
    before = v2_path("x.json")
    old = os.getcwd()
    try:
        os.chdir(tmp_path)
        assert v2_path("x.json") == before          # still repo-anchored
        assert v2_path("x.json").startswith(REPO_ROOT)
    finally:
        os.chdir(old)


def test_default_attack_output_normalizes_mode_and_scenario():
    assert default_attack_output("S06", "full-pipeline") == \
        os.path.join(RESULTS_ROOT, "attacks", "s06", "full_pipeline.json")


# ---- guard: allow legitimate targets ----
def test_assert_writable_allows_v2_and_nonlegacy_paths():
    for good in (v2_path("x.json"), "results_v2_frozen/agent_scaling",
                 "logs/x.jsonl", "/tmp/out.json"):
        assert assert_writable(good) == good


def test_results_v2_frozen_not_mistaken_for_legacy():
    assert "results_v2_frozen" not in LEGACY_ROOTS
    assert_writable(v2_path("attacks", "s01", "retrieval.json"))


# ---- guard: reject legacy (name-based, cwd-independent) ----
@pytest.mark.parametrize("bad", [
    "results", "results/x.json", "results/attacks/s01/retrieval.json",
    "results_legacy_raid", "results_legacy_raid/y.json", "./results/z",
    "../results/x", "a/b/../../results/x", "",
])
def test_assert_writable_rejects_legacy_and_empty(bad):
    with pytest.raises(ValueError):
        assert_writable(bad)


def test_reject_absolute_legacy_path():
    with pytest.raises(ValueError):
        assert_writable(os.path.join(REPO_ROOT, "results", "x.json"))
    with pytest.raises(ValueError):
        assert_writable(os.path.join(REPO_ROOT, "results_legacy_raid", "x.json"))


def test_reject_relative_legacy_regardless_of_cwd(tmp_path):
    old = os.getcwd()
    try:
        os.chdir(tmp_path)                          # not the repo root
        with pytest.raises(ValueError):
            assert_writable("results/x.json")       # blocked by name guard
        with pytest.raises(ValueError):
            assert_writable("../results/x.json")
    finally:
        os.chdir(old)


def test_reject_symlink_into_legacy(tmp_path):
    """A symlink whose name is innocuous but resolves into the repo's legacy
    results dir must still be rejected (realpath-containment guard)."""
    legacy_dir = os.path.join(REPO_ROOT, "results")
    if not os.path.isdir(legacy_dir):
        pytest.skip("repo legacy results/ dir not present")
    link = tmp_path / "innocuous_link"
    os.symlink(legacy_dir, link)                    # link -> <repo>/results
    with pytest.raises(ValueError):
        assert_writable(os.path.join(str(link), "x.json"))


# ---- repo invariant: no legacy result-write literals remain ----
_LEGACY_WRITE_PATTERNS = [
    re.compile(r"""os\.path\.join\(\s*["']results["']"""),   # join("results", ...)
    re.compile(r"""makedirs\(\s*["']results["']"""),          # makedirs("results")
    re.compile(r"""["']results/"""),                          # "results/..." literal
    re.compile(r"""["']results_legacy_raid[/"']"""),          # writing into legacy_raid
]

def _scan_targets():
    for base in ("uavsys", "experiments"):
        for root, _dirs, files in os.walk(os.path.join(REPO, base)):
            if "__pycache__" in root:
                continue
            for fn in files:
                if fn.endswith(".py"):
                    yield os.path.join(root, fn)


def test_no_legacy_result_write_paths_in_code():
    violations = []
    for path in _scan_targets():
        if os.path.basename(path) == "paths.py":     # legitimately names legacy roots
            continue
        with open(path, encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                for pat in _LEGACY_WRITE_PATTERNS:
                    if pat.search(line):
                        violations.append(f"{os.path.relpath(path, REPO)}:{i}: {line.strip()}")
    assert not violations, "Legacy result-write path(s) found:\n" + "\n".join(violations)
