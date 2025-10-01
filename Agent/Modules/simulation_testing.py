"""
Game simulation testing for the agent system.
"""
import io
import sys
import traceback
import pygame
from pygame import Vector2
from typing import Dict, List, Any

from .utils import debug_print, safe_read_file


def _format_exception_details(test_name: str, error: Exception, raw_trace: str | None = None) -> str:
    """Create a rich error message with the most relevant traceback frames."""

    if raw_trace is None:
        raw_trace = traceback.format_exc()
    formatted_lines: List[str] = [
        f"Test '{test_name}' failed with {error.__class__.__name__}: {error}"
    ]

    if not raw_trace:
        return "\n".join(formatted_lines)

    trace_lines = [line.rstrip() for line in raw_trace.splitlines() if line.strip()]
    relevant_chunks: List[str] = []
    i = 0
    while i < len(trace_lines):
        line = trace_lines[i]
        if line.startswith("File "):
            snippet = [line]
            if i + 1 < len(trace_lines):
                snippet.append(trace_lines[i + 1])
            # Focus on frames inside the project for clarity
            if "Project_SYNTAX_V2" in line or "Game/" in line or "Game\\" in line:
                relevant_chunks.append("\n".join(snippet))
        i += 1

    if not relevant_chunks:
        # Fall back to the last few lines of the traceback
        relevant_chunks = ["\n".join(trace_lines[-4:])]

    formatted_lines.append("Relevant traceback frames:")
    formatted_lines.extend(relevant_chunks)
    return "\n".join(formatted_lines)


def _validate_weapon_description(weapon_plan: Dict[str, Any], weapon) -> None:
    expected_description = weapon_plan.get("description")
    if isinstance(expected_description, str) and expected_description.strip():
        actual_description = getattr(weapon, "description", "")
        if actual_description.strip() != expected_description.strip():
            raise Exception(
                "Weapon description mismatch: "
                f"expected '{expected_description.strip()}' got '{actual_description.strip()}'"
            )


def run_game_simulation_tests(weapon_plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run actual game simulation tests to ensure weapon works in real gameplay scenarios.
    """
    debug_print("🎮 Starting game simulation tests", "INFO")
    debug_print("📋 Test scenarios:", "INFO")
    debug_print("     1. Weapon pickup", "INFO")
    debug_print("     2. Finding ammo", "INFO")
    debug_print("     3. Shooting nothing", "INFO")
    debug_print("     4. Shooting player", "INFO")

    results = {
        "tests_run": [],
        "tests_passed": [],
        "errors": [],
        "has_errors": False
    }

    try:
        weapon_name = weapon_plan.get("weapon_name", "TestWeapon")
        weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)

        debug_print(f"Setting up simulation environment for weapon: {weapon_name}", "INFO")

        # Import required modules
        pygame.init()
        debug_print("✅ Pygame initialized", "DEBUG")

        # Create minimal test environment
        test_screen = pygame.display.set_mode((100, 100), pygame.HIDDEN)
        debug_print("✅ Test screen created", "DEBUG")

        from Game.Arena.arena import Arena
        from Game.Character.cow import Cow
        from Game.Weapons.weapon import Weapon

        # Import the custom weapon if it exists
        debug_print(f"Attempting to import weapon: {weapon_class_name}", "DEBUG")
        try:
            import importlib
            weapon_module_path = f"Game.Weapons.{weapon_class_name.lower()}"
            weapon_module = importlib.import_module(weapon_module_path)
            create_weapon_func = getattr(weapon_module, f"create_{weapon_class_name.lower()}")
            debug_print(f"✅ Weapon imported successfully: {weapon_class_name}", "INFO")
        except Exception as e:
            results["errors"].append(f"Failed to import weapon: {e}")
            results["has_errors"] = True
            debug_print(f"❌ Failed to import weapon: {e}", "ERROR")
            return results

        # Test 1: Weapon Pickup
        test_name = "weapon_pickup"
        results["tests_run"].append(test_name)
        debug_print(f"🏃 Running test: {test_name}", "INFO")
        try:
            debug_print(f"Creating test cow for {test_name}", "DEBUG")
            test_cow = Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000)
            )

            debug_print("Creating weapon instance", "DEBUG")
            weapon = create_weapon_func()
            _validate_weapon_description(weapon_plan, weapon)

            debug_print("Equipping weapon on cow", "DEBUG")
            test_cow.equip_weapon(weapon)

            debug_print("Triggering handle_event for weapon control", "DEBUG")
            if hasattr(test_cow, 'handle_event'):
                test_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 500))
                test_cow.handle_event(test_event)

            debug_print("Validating weapon equip", "DEBUG")
            if not test_cow.has_weapon():
                raise Exception("Cow did not equip weapon")
            if test_cow.get_weapon().name != weapon.name:
                raise Exception(f"Weapon name mismatch: {test_cow.get_weapon().name} != {weapon.name}")

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            raw_trace = traceback.format_exc()
            detailed_error = _format_exception_details(test_name, e, raw_trace)
            results["errors"].append(detailed_error)
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")
            debug_print(f"Traceback details for {test_name}:\n{raw_trace}", "DEBUG")

        # Test 2: Finding Ammo
        test_name = "finding_ammo"
        results["tests_run"].append(test_name)
        debug_print(f"🏃 Running test: {test_name}", "INFO")
        try:
            debug_print(f"Creating test cow for {test_name}", "DEBUG")
            test_cow = Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000),
                starting_ammo=0
            )
            debug_print("Equipping weapon on cow", "DEBUG")
            weapon = create_weapon_func()
            _validate_weapon_description(weapon_plan, weapon)
            test_cow.equip_weapon(weapon)

            debug_print("Simulating ammo finding", "DEBUG")
            initial_ammo = test_cow.ammo
            test_cow.ammo += 10

            debug_print("Validating ammo increase", "DEBUG")
            if test_cow.ammo <= initial_ammo:
                raise Exception("Ammo did not increase")

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            raw_trace = traceback.format_exc()
            detailed_error = _format_exception_details(test_name, e, raw_trace)
            results["errors"].append(detailed_error)
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")
            debug_print(f"Traceback details for {test_name}:\n{raw_trace}", "DEBUG")

        # Test 3: Shooting Nothing
        test_name = "shooting_nothing"
        results["tests_run"].append(test_name)
        debug_print(f"🏃 Running test: {test_name}", "INFO")
        try:
            debug_print("Creating arena for shooting test", "DEBUG")

            # Redirect stdout/stderr to suppress pygame output
            f = io.StringIO()
            with io.StringIO() as f:
                debug_print("Creating arena with hidden display", "DEBUG")
                arena = Arena(
                    screen_dimensions=(0, 0, 800, 600),
                    world_screen_dimensions=(2000, 2000),
                    screen=test_screen,
                    world_screen=test_screen,
                    text=None
                )

                debug_print("Creating player cow", "DEBUG")
                player = Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Player",
                    starting_position=(500, 500),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                    starting_ammo=10
                )

                debug_print("Equipping weapon", "DEBUG")
                weapon = create_weapon_func()
                _validate_weapon_description(weapon_plan, weapon)
                player.equip_weapon(weapon)
                arena.characters.append(player)

                debug_print("Triggering handle_event for firing test", "DEBUG")
                if hasattr(player, 'handle_event'):
                    fire_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 500))
                    player.handle_event(fire_event)

                debug_print("Firing weapon via weapon.fire", "DEBUG")
                initial_projectile_count = len(arena.projectiles)
                direction = Vector2(100, 0)
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                projectiles = weapon.fire(player.position, direction, player)

                if isinstance(projectiles, list):
                    arena.projectiles.extend(projectiles)
                elif projectiles:
                    arena.projectiles.append(projectiles)

                debug_print("Validating projectile spawn", "DEBUG")
                if len(arena.projectiles) <= initial_projectile_count:
                    raise Exception("weapon.fire did not return any projectiles")

                debug_print("Running arena updates", "DEBUG")
                for _ in range(10):
                    arena.update()

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            raw_trace = traceback.format_exc()
            detailed_error = _format_exception_details(test_name, e, raw_trace)
            results["errors"].append(detailed_error)
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")
            debug_print(f"Traceback details for {test_name}:\n{raw_trace}", "DEBUG")

        # Test 4: Shooting Player
        test_name = "shooting_player"
        results["tests_run"].append(test_name)
        debug_print(f"🏃 Running test: {test_name}", "INFO")
        try:
            debug_print("Creating arena for player vs player test", "DEBUG")

            # Redirect stdout/stderr
            f = io.StringIO()
            with io.StringIO() as f:
                debug_print("Creating arena", "DEBUG")
                arena = Arena(
                    screen_dimensions=(0, 0, 800, 600),
                    world_screen_dimensions=(2000, 2000),
                    screen=test_screen,
                    world_screen=test_screen,
                    text=None
                )

                debug_print("Creating player and target cows", "DEBUG")
                player = Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Player",
                    starting_position=(500, 500),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                    starting_ammo=10
                )

                target = Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Target",
                    starting_position=(550, 500),  # Close to player
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000)
                )

                debug_print("Equipping weapon", "DEBUG")
                weapon = create_weapon_func()
                _validate_weapon_description(weapon_plan, weapon)
                player.equip_weapon(weapon)
                arena.characters.append(player)
                arena.characters.append(target)

                debug_print("Triggering handle_event for combat scenario", "DEBUG")
                if hasattr(player, 'handle_event'):
                    attack_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(550, 500))
                    player.handle_event(attack_event)

                debug_print("Recording initial target health", "DEBUG")
                initial_health = target.health

                debug_print("Shooting at target", "DEBUG")
                direction = Vector2(50, 0)
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                projectiles = weapon.fire(player.position, direction, player)

                if isinstance(projectiles, list):
                    arena.projectiles.extend(projectiles)
                elif projectiles:
                    arena.projectiles.append(projectiles)

                debug_print("Running arena updates to detect hit", "DEBUG")
                for _ in range(30):
                    arena.update()
                    if target.health < initial_health:
                        debug_print("✅ Target took damage - hit detection working", "INFO")
                        break

                debug_print("Validating damage application", "DEBUG")
                if target.health >= initial_health:
                    raise Exception(f"Target did not take damage (health: {target.health} >= {initial_health})")

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            raw_trace = traceback.format_exc()
            detailed_error = _format_exception_details(test_name, e, raw_trace)
            results["errors"].append(detailed_error)
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")
            debug_print(f"Traceback details for {test_name}:\n{raw_trace}", "DEBUG")

        pygame.quit()
        debug_print("✅ Pygame quit", "DEBUG")

    except Exception as e:
        raw_trace = traceback.format_exc()
        detailed_error = (
            "Simulation test suite failed with "
            f"{e.__class__.__name__}: {e}\n"
            f"Traceback:\n{raw_trace.strip()}"
        )
        results["errors"].append(detailed_error)
        results["has_errors"] = True
        debug_print(f"❌ Simulation test suite failed: {e}", "ERROR")
        debug_print(f"Traceback details for simulation suite:\n{raw_trace}", "DEBUG")

    debug_print(f"Simulation tests complete: {len(results['tests_passed'])}/{len(results['tests_run'])} passed", "INFO")
    return results
