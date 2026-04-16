"""
Attack Scenario Registry — maps S01–S15 to their inject() functions.

Usage:
    from attacks import SCENARIOS, get_scenario
    
    inject_fn = get_scenario("S01")
    result = await inject_fn(memory, count=3, run_id="exp_001")
"""

from typing import Callable, Dict, Optional

# Import all scenario modules
from . import s01_false_observation
from . import s02_fact_corruption
from . import s03_skill_hijack
from . import s04_task_misrouting
from . import s05_prompt_injection
from . import s06_contagion
from . import s07_stealth_insert
from . import s08_volume_flood
from . import s09_recency_exploit
from . import s10_amplification
from . import s11_authority_spoof
from . import s12_virtual_nfz
from . import s13_skill_arbitration
from . import s14_policy_hijack
from . import s15_cascade


# Registry: scenario_id -> inject function
SCENARIOS: Dict[str, Callable] = {
    "S01": s01_false_observation.inject,
    "S02": s02_fact_corruption.inject,
    "S03": s03_skill_hijack.inject,
    "S04": s04_task_misrouting.inject,
    "S05": s05_prompt_injection.inject,
    "S06": s06_contagion.inject,
    "S07": s07_stealth_insert.inject,
    "S08": s08_volume_flood.inject,
    "S09": s09_recency_exploit.inject,
    "S10": s10_amplification.inject,
    "S11": s11_authority_spoof.inject,
    "S12": s12_virtual_nfz.inject,
    "S13": s13_skill_arbitration.inject,
    "S14": s14_policy_hijack.inject,
    "S15": s15_cascade.inject,
}

# Backward-compatible aliases for existing experiment_runner.py
LEGACY_ALIASES: Dict[str, str] = {
    "displacement": "S08",
    "contagion": "S06",
    "trojan_plan": "S03",
    "false_flag": "S12",
}


def get_scenario(scenario_id: str) -> Optional[Callable]:
    """
    Get the inject function for a scenario ID.
    Accepts S01-S15 or legacy names (displacement, contagion, etc.)
    """
    # Check legacy aliases first
    if scenario_id in LEGACY_ALIASES:
        scenario_id = LEGACY_ALIASES[scenario_id]
    
    return SCENARIOS.get(scenario_id.upper())


def list_scenarios() -> list:
    """List all available scenario IDs with their module names."""
    return [
        {"id": sid, "module": fn.__module__, "doc": fn.__doc__[:80] if fn.__doc__ else ""}
        for sid, fn in SCENARIOS.items()
    ]
