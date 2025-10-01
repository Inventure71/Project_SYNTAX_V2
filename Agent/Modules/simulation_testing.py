"""Game simulation testing for the agent system."""

from __future__ import annotations

from typing import Any, Dict

from TestWorkspace.weapon_test_suite import WeaponSimulationTestSuite

from .utils import debug_print


def run_game_simulation_tests(weapon_plan: Dict[str, Any]) -> Dict[str, Any]:
    """Run the runtime-editable weapon simulation suite."""

    debug_print("🎮 Starting game simulation tests", "INFO")

    suite = WeaponSimulationTestSuite(weapon_plan, debug_printer=debug_print)
    results = suite.run()

    debug_print(
        f"Simulation tests complete: {len(results['tests_passed'])}/"
        f"{len(results['tests_run'])} passed",
        "INFO",
    )
    return results

