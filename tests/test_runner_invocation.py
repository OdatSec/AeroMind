"""
Reproducibility: the mode-runners must be runnable by DIRECT path from the repo
root (python experiments/<runner>.py ...) without an exported PYTHONPATH, i.e.
`from uavsys...` must resolve via the in-file sys.path bootstrap.

We invoke each runner by path with PYTHONPATH stripped and `--output results/...`,
which fails fast at the legacy-path guard (assert_writable) — that point is
AFTER the `from uavsys.paths import` line, so reaching it proves the import
resolved. No Ollama / DB / experiment work is performed. Also asserts the guard
message appears (import resolved) and the uavsys ModuleNotFoundError does not.

Run: python3 -m pytest tests/test_runner_invocation.py
"""
import os
import subprocess
import sys

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.mark.parametrize("runner", [
    "experiments/experiment_runner.py",
    "experiments/s12_runner.py",
    "experiments/s15_runner.py",
])
def test_direct_script_invocation_resolves_uavsys(runner):
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)   # emulate an operator who forgot PYTHONPATH
    r = subprocess.run(
        [sys.executable, runner, "--scenario", "B0", "--mode", "retrieval",
         "--seeds", "42", "--defense", "off",
         "--output", "results/should_be_blocked_by_guard"],
        cwd=REPO, env=env, capture_output=True, text=True, timeout=60,
    )
    out = r.stdout + r.stderr
    # The fix: the deferred `from uavsys.paths import` must resolve.
    assert "No module named 'uavsys'" not in out, out[-800:]
    # And execution reached the path guard that lives just after that import,
    # proving we got past it without touching Ollama/DB.
    assert "Refusing to write under" in out, out[-800:]
