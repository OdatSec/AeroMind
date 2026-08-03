"""
Evidence-bundle writer for the AeroMind V2 campaign.

Every V2 run must produce a self-contained, integrity-checked folder so results
are independently verifiable and no run (including failures) is silently lost.
This module is a passive collector: the runner feeds it data it already has; it
does not reach into attack/defense/retrieval/metrics internals.

Integrity guarantees:
  * Git commit + dirty state captured at BOTH construction and finalize. A
    production bundle (written under the V2 results root) is refused if the tree
    is dirty at either point, or if the commit changed mid-run.
  * allow_dirty is for tests/development only: it is REFUSED under the V2 results
    root, and the bundle is marked validity="development-only" / valid=False.
  * Required files depend on the evaluation layer AND the run outcome. An aborted
    outcome (timeout/parse/infra) still yields a complete failure bundle and
    stays countable; it is never rejected for missing planner/telemetry files.
  * Manifest records the experiment-spec hash, the resolved run parameters, and
    the (secret-redacted) config hash.
  * Collision-safe run IDs + atomic finalize (stage dir -> os.replace): parallel
    runs cannot overwrite each other or leave an apparently-complete partial.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Dict, List, Optional

from ..paths import REPO_ROOT, RESULTS_ROOT  # noqa: F401
from ..utils.timeutil import now_iso

# ---- required-file policy (layer x outcome) ----
ALWAYS_REQUIRED = ("manifest.json", "config.yaml", "environment.json",
                   "status.json", "checksums.sha256")
LAYER_ARTIFACTS = {
    "L1": ("memory_before.jsonl", "injected_records.jsonl", "memory_after.jsonl",
           "retrieval_trace.jsonl", "metrics.json"),
    "L2": ("memory_before.jsonl", "injected_records.jsonl", "memory_after.jsonl",
           "retrieval_trace.jsonl", "planner_context.json", "planner_raw_output.txt",
           "parsed_actions.json", "metrics.json"),
    "L3": ("memory_before.jsonl", "injected_records.jsonl", "memory_after.jsonl",
           "metrics.json"),
    "L4": ("memory_before.jsonl", "injected_records.jsonl", "memory_after.jsonl",
           "retrieval_trace.jsonl", "planner_context.json", "planner_raw_output.txt",
           "parsed_actions.json", "telemetry.csv", "trajectory.csv", "metrics.json"),
}
# Outcomes where the pipeline aborted before producing layer artifacts. These
# still produce a COMPLETE bundle (base files only) and remain in the denominator.
ABORTED_OUTCOMES = frozenset({"timeout", "parse_error", "infrastructure_failure",
                              "mock_fallback", "provider_failure"})

_REDACT = ("provenance_secret", "secret", "api_key", "token")

# ---- config fingerprint ----
# Execution-ephemeral fields vary per run (temp DB path, per-run id) and say
# nothing about the scientific configuration. They are EXCLUDED from the hashed
# canonical view so the same configuration always yields the same config_hash,
# while their real values are still recorded verbatim in config.yaml.
EPHEMERAL_CONFIG_FIELDS = ("DB_PATH", "RUN_ID")
# Bumped whenever the canonicalization rule changes; included in the hashed
# payload so fingerprints from different schema versions cannot collide.
# v1: config-only (all bundles accepted before mission/profile existed).
# v2: adds the run axes {mission, profile} — a scientific input that MUST change
#     the fingerprint. v1 bundles on disk are never recomputed under v2, so their
#     stored fingerprints remain valid; new runs that specify a run axis use v2.
CONFIG_HASH_SCHEMA_VERSION = "1"
CONFIG_HASH_SCHEMA_VERSION_WITH_RUN = "2"        # + run axes {mission, profile}
CONFIG_HASH_SCHEMA_VERSION_V3 = "3"              # + poison budget (V3 identity)


def required_files(layer: str, outcome: str) -> set:
    """Files that MUST exist for a complete bundle at this layer/outcome."""
    base = set(ALWAYS_REQUIRED)
    if outcome in ABORTED_OUTCOMES:
        return base
    return base | set(LAYER_ARTIFACTS.get(layer, ()))


def _default_git_state(repo_root: str) -> Dict[str, Any]:
    def _run(args):
        return subprocess.run(["git", "-C", repo_root, *args],
                              capture_output=True, text=True, timeout=10)
    try:
        commit = _run(["rev-parse", "HEAD"]).stdout.strip() or None
        dirty = bool(_run(["status", "--porcelain"]).stdout.strip())
        return {"commit": commit, "dirty": dirty}
    except Exception as e:  # pragma: no cover - git always present here
        return {"commit": None, "dirty": True, "error": str(e)}


def _redact(d: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for k, v in d.items():
        if any(tok in str(k).lower() for tok in _REDACT):
            out[k] = "<redacted>"
        else:
            out[k] = v
    return out


def _sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _capture_environment(embedder: Optional[dict]) -> Dict[str, Any]:
    """Best-effort environment capture; unavailable items record null + reason."""
    def safe(fn):
        try:
            return {"value": fn()}
        except Exception as e:
            return {"value": None, "reason": str(e)}

    env: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": safe(lambda: " ".join(platform.uname())),
    }
    # Key package versions.
    pkgs = {}
    try:
        from importlib.metadata import version, PackageNotFoundError
        for name in ("mavsdk", "ollama", "numpy", "aiosqlite", "openai", "anthropic", "pyyaml"):
            try:
                pkgs[name] = version(name)
            except PackageNotFoundError:
                pkgs[name] = None
    except Exception as e:
        pkgs = {"_error": str(e)}
    env["packages"] = pkgs
    env["embedder"] = embedder or {"value": None, "reason": "not provided"}

    # GPU via nvidia-smi (short timeout; explicit null+reason if unavailable).
    def _gpu():
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,driver_version,memory.total",
             "--format=csv,noheader"],
            capture_output=True, text=True, timeout=5)
        if r.returncode != 0:
            raise RuntimeError(r.stderr.strip() or f"exit {r.returncode}")
        return [line.strip() for line in r.stdout.strip().splitlines() if line.strip()]
    env["gpu"] = safe(_gpu)
    return env


class EvidenceBundle:
    """Collect and atomically write one run's evidence bundle."""

    def __init__(
        self,
        *,
        scenario: str,          # e.g. "C1"
        legacy_id: str,         # e.g. "S01"
        layer: str,             # "L1".."L4"
        seed: int,
        model: str,
        defense_level: str = "D0",
        config: Any = None,     # Config dataclass or dict
        resolved_params: Optional[Dict[str, Any]] = None,  # CLI/run params
        embedder: Optional[Dict[str, Any]] = None,         # {name, tag, digest, dim}
        backend: Optional[Dict[str, Any]] = None,          # {requested, actual}
        configured: Optional[Dict[str, Any]] = None,       # requested/declared inputs
                                                           # (e.g. memory_profile, poison_budget, top_k)
        mission: Optional[str] = None,     # M1-M4 run axis (folds into config_hash v2)
        profile: Optional[str] = None,     # P1-P6 run axis (folds into config_hash v2)
        budget: Optional[Any] = None,      # poison budget run axis (folds into config_hash v3)
        canonical_ids: Optional[Dict[str, Any]] = None,  # V3 canonical + legacy identity block
        short_run_id: bool = False,        # V3 layout: short run-dir name (metadata in manifest)
        base_dir: Optional[str] = None,   # defaults to results_root (production)
        results_root: str = RESULTS_ROOT,
        repo_root: str = REPO_ROOT,
        spec_path: Optional[str] = None,
        allow_dirty: bool = False,
        run_class: Optional[str] = None,   # None=auto; "preflight" forces sandbox class
        git_state_fn: Optional[Callable[[str], Dict[str, Any]]] = None,
    ):
        self.repo_root = repo_root
        self.results_root = os.path.realpath(results_root)
        self._git_state_fn = git_state_fn or _default_git_state
        self.base_dir = os.path.realpath(base_dir or results_root)
        self._production = (self.base_dir == self.results_root or
                            self.base_dir.startswith(self.results_root + os.sep))
        # Run class governs the validity LABEL (independent of the writable-root
        # guards above). A bundle may claim validity="production" only under a REAL
        # repo-anchored production root. A run written under an env-REDIRECTED V3
        # sandbox root is a disposable "preflight" run: real pipeline, but NEVER
        # admissible as production/paper evidence.
        self.run_class = run_class
        if self.run_class is None and self._production:
            from .. import paths as _paths
            if (_paths.v3_raw_is_redirected()
                    and not _paths.is_canonical_production_root(self.base_dir)):
                self.run_class = "preflight"
        self.allow_dirty = allow_dirty

        # Rule: allow_dirty must never mint evidence under the production root.
        if self.allow_dirty and self._production:
            raise ValueError(
                "allow_dirty=True is forbidden under the V2 results root; use a "
                "development/test directory for dirty bundles."
            )

        self.git_start = self._git_state_fn(repo_root)
        # Production bundles refuse dirty code at start (fail loud, before work).
        if self._production and self.git_start.get("dirty"):
            raise RuntimeError(
                "Refusing to start a production evidence bundle from a dirty tree "
                f"(commit {self.git_start.get('commit')}). Commit first."
            )

        self.identity = {
            "scenario": scenario, "legacy_id": legacy_id, "layer": layer,
            "seed": seed, "model": model, "defense_level": defense_level,
        }
        self.embedder = embedder
        self.backend = backend or {}
        # `configured` = what the run REQUESTED/declared (may be None/default).
        # `observed`   = what actually happened, measured from the artifacts.
        # They are kept separate so an unset configured value is never confused
        # with a measured one.
        self.configured = configured or {}
        self.observed: Dict[str, Any] = {}
        self.resolved_params = resolved_params or {}
        self.mission = mission
        self.profile = profile
        self.budget = budget
        self.canonical_ids = canonical_ids
        # Run axes fold into the fingerprint (only when set, so config-only bundles
        # stay byte-identical to accepted v1, and mission/profile-only bundles stay
        # byte-identical to accepted v2). Adding `budget` bumps the schema to v3.
        _axes = {}
        if mission is not None or profile is not None:
            _axes["mission"] = mission
            _axes["profile"] = profile
        if budget is not None:
            _axes["budget"] = budget
        self._run_axes = _axes or None
        # Full config is recorded verbatim; the fingerprint is taken over the
        # canonical view (ephemeral fields removed) so it is reproducible.
        self._config_dict = self._to_config_dict(config)
        self.config_hash = self._compute_config_hash(self._config_dict, run_axes=self._run_axes)
        self.config_hash_schema_version = self._hash_schema_version(self._run_axes)
        self.spec_path = spec_path or os.path.join(repo_root, "configs", "EXPERIMENT_SPEC_V2.yaml")
        self.spec_hash = (_sha256_file(self.spec_path)
                          if os.path.exists(self.spec_path) else None)

        # Collision-safe run id: deterministic prefix + unique suffix. For the V3
        # layout the human-facing identity lives in the directory hierarchy, so a
        # SHORT run id is used (run-<cfg8>-<uuid8>); full metadata stays in the
        # manifest. V2 keeps the long descriptive name (default).
        model_slug = str(model).replace(":", "-").replace("/", "-")
        if short_run_id:
            self.run_id = f"run-{self.config_hash[:8]}-{uuid.uuid4().hex[:8]}"
        else:
            self.run_id = (f"{scenario}__{layer}__model-{model_slug}__seed{int(seed):04d}"
                           f"__{defense_level}__cfg-{self.config_hash[:8]}__{uuid.uuid4().hex[:8]}")
        self.final_dir = os.path.join(self.base_dir, self.run_id)
        self.stage_dir = self.final_dir + f".staging-{uuid.uuid4().hex[:8]}"

        self._files: Dict[str, bytes] = {}   # filename -> bytes (staged in memory)
        self._status: Optional[Dict[str, Any]] = None
        os.makedirs(self.stage_dir, exist_ok=True)

    # ---- helpers ----
    @staticmethod
    def _to_config_dict(config) -> Dict[str, Any]:
        if config is None:
            return {}
        if is_dataclass(config):
            d = asdict(config)
        elif isinstance(config, dict):
            d = dict(config)
        else:
            d = dict(vars(config))   # SimpleNamespace / plain objects
        return _redact(d)

    @staticmethod
    def _compute_config_hash(config_dict: Dict[str, Any], *,
                             run_axes: Optional[Dict[str, Any]] = None) -> str:
        """Fingerprint the canonical config: full config minus ephemeral fields,
        bound to the schema version so rule changes are never silently equal.

        With no run_axes -> schema v1 (identical to all previously accepted
        bundles). With run_axes (mission/profile) -> schema v2, which folds those
        scientific inputs into the fingerprint. The two schemas can never collide
        because the schema_version is inside the hashed payload.
        """
        canonical = {k: v for k, v in config_dict.items()
                     if k not in EPHEMERAL_CONFIG_FIELDS}
        if not run_axes:
            payload = {"schema_version": CONFIG_HASH_SCHEMA_VERSION, "config": canonical}
        else:
            payload = {"schema_version": EvidenceBundle._hash_schema_version(run_axes),
                       "config": canonical,
                       "run_axes": {k: run_axes[k] for k in sorted(run_axes)}}
        return _sha256_bytes(json.dumps(payload, sort_keys=True, default=str).encode())

    @staticmethod
    def _hash_schema_version(run_axes: Optional[Dict[str, Any]]) -> str:
        """v1 no run axes; v2 = {mission, profile}; v3 adds poison budget. Bumping
        the version into the payload means v2 hashes/bundles stay unchanged while a
        budget axis yields a distinct v3 fingerprint."""
        if not run_axes:
            return CONFIG_HASH_SCHEMA_VERSION
        if "budget" in run_axes:
            return CONFIG_HASH_SCHEMA_VERSION_V3
        return CONFIG_HASH_SCHEMA_VERSION_WITH_RUN

    def _add(self, name: str, data: bytes):
        self._files[name] = data

    @staticmethod
    def _jsonl(records: List[dict]) -> bytes:
        return ("".join(json.dumps(r, default=str) + "\n" for r in records)).encode()

    # ---- record API (all optional; presence validated per layer/outcome) ----
    def record_memory(self, before: List[dict], injected: List[dict], after: List[dict]):
        self._add("memory_before.jsonl", self._jsonl(before))
        self._add("injected_records.jsonl", self._jsonl(injected))
        self._add("memory_after.jsonl", self._jsonl(after))
        # Observed (measured) memory facts — never conflated with configured ones.
        self.observed.update({
            "memory_records_before": len(before),
            "injected_records": len(injected),
            "memory_records_after": len(after),
            "attack_tagged_records_after": sum(
                1 for r in after if str(r.get("source", "")).startswith("atk:")),
        })

    def record_retrieval(self, trace: Any):
        self._add("retrieval_trace.jsonl",
                  self._jsonl(trace) if isinstance(trace, list)
                  else (json.dumps(trace, default=str) + "\n").encode())

    def record_planner(self, context: Any, raw: str, parsed: Any):
        self._add("planner_context.json", json.dumps(context, default=str, indent=2).encode())
        self._add("planner_raw_output.txt", str(raw).encode())
        self._add("parsed_actions.json", json.dumps(parsed, default=str, indent=2).encode())

    def record_execution(self, telemetry_csv: str, trajectory_csv: str):
        self._add("telemetry.csv", str(telemetry_csv).encode())
        self._add("trajectory.csv", str(trajectory_csv).encode())

    def record_metrics(self, metrics: Any):
        self._add("metrics.json", json.dumps(metrics, default=str, indent=2).encode())

    @property
    def status_set(self) -> bool:
        return self._status is not None

    def set_status(self, outcome: str, detail: Optional[dict] = None):
        self._status = {"outcome": outcome, "detail": detail or {},
                        "included_in_denominator": True, "ts": now_iso()}

    # ---- finalize ----
    def finalize(self) -> str:
        if self._status is None:
            raise ValueError("set_status(outcome=...) must be called before finalize().")
        outcome = self._status["outcome"]

        git_end = self._git_state_fn(self.repo_root)
        valid = True
        validity = "production"
        if not self._production:
            valid = False
            validity = "development-only"
        elif self.run_class == "preflight":
            # Redirected sandbox run: real pipeline, but NOT admissible as production
            # evidence. Still enforce the production integrity gates below so the run
            # is honestly reproducible; only the label/valid flag differ.
            valid = False
            validity = "preflight"
        if self._production:
            # Production integrity gates (apply to production AND preflight runs).
            if git_end.get("dirty"):
                self._cleanup()
                raise RuntimeError("Refusing to finalize a production bundle: tree "
                                   "became dirty during the run.")
            if git_end.get("commit") != self.git_start.get("commit"):
                self._cleanup()
                raise RuntimeError(
                    f"Refusing to finalize: commit changed during run "
                    f"({self.git_start.get('commit')} -> {git_end.get('commit')}).")

        manifest = {
            "run_id": self.run_id,
            **self.identity,
            "mission": self.mission,
            "profile": self.profile,
            "budget": self.budget,             # poison-budget run axis (in config_hash v3)
            "canonical": self.canonical_ids,   # V3 canonical + legacy identity (None for V2 bundles)
            "validity": validity,
            "valid": valid,
            "run_class": ("preflight" if validity == "preflight" else
                          ("production" if validity == "production" else "development")),
            "commit_start": self.git_start.get("commit"),
            "commit_end": git_end.get("commit"),
            "dirty_start": self.git_start.get("dirty"),
            "dirty_end": git_end.get("dirty"),
            "config_hash": self.config_hash,
            # Fingerprint semantics, so an auditor can recompute config_hash: it
            # covers config.yaml minus the excluded fields, bound to this schema.
            # Under v2 the run axes below are also folded into the fingerprint.
            "config_hash_schema": {
                "version": self.config_hash_schema_version,
                "excluded_fields": list(EPHEMERAL_CONFIG_FIELDS),
                "run_axes": (list(self._run_axes) if self._run_axes else []),
                "note": ("config.yaml records all fields verbatim; excluded fields "
                         "are execution-ephemeral; run_axes (if any) are folded "
                         "into the fingerprint under schema v2"),
            },
            "spec_hash": self.spec_hash,
            "resolved_params": self.resolved_params,
            "embedder": self.embedder,
            "requested_backend": self.backend.get("requested"),
            "actual_backend": self.backend.get("actual"),
            "configured": self.configured,
            "observed": self.observed,
            "outcome": outcome,
            "created": now_iso(),
        }
        self._add("manifest.json", json.dumps(manifest, indent=2).encode())
        self._add("config.yaml", json.dumps(self._config_dict, indent=2, sort_keys=True).encode())
        self._add("environment.json",
                  json.dumps(_capture_environment(self.embedder), indent=2).encode())
        self._add("status.json", json.dumps(self._status, indent=2).encode())

        # Validate completeness for this layer/outcome BEFORE writing checksums.
        need = required_files(self.identity["layer"], outcome)
        missing = [f for f in need if f != "checksums.sha256" and f not in self._files]
        if missing:
            self._cleanup()
            raise RuntimeError(
                f"Incomplete bundle for layer={self.identity['layer']} "
                f"outcome={outcome}: missing {sorted(missing)}.")

        # Write staged files, then checksums over them.
        for name, data in self._files.items():
            with open(os.path.join(self.stage_dir, name), "wb") as f:
                f.write(data)
        lines = []
        for name in sorted(self._files):
            lines.append(f"{_sha256_file(os.path.join(self.stage_dir, name))}  {name}")
        with open(os.path.join(self.stage_dir, "checksums.sha256"), "w") as f:
            f.write("\n".join(lines) + "\n")

        # Atomic publish: staging -> final (fails if final already exists).
        if os.path.exists(self.final_dir):
            self._cleanup()
            raise RuntimeError(f"Refusing to overwrite existing bundle {self.final_dir}.")
        os.replace(self.stage_dir, self.final_dir)
        return self.final_dir

    def _cleanup(self):
        shutil.rmtree(self.stage_dir, ignore_errors=True)
