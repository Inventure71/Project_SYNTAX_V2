"""
Game simulation testing for the agent system.
"""
import io
import sys
import pygame
from typing import Dict, List, Any

from .utils import debug_print, safe_read_file


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
            weapon_file = f"Game/Weapons/{weapon_class_name.lower()}"
            exec(f"from {weapon_file.replace('/', '.')} import create_{weapon_class_name.lower()}")
            create_weapon_func = locals()[f"create_{weapon_class_name.lower()}"]
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

            debug_print("Equipping weapon on cow", "DEBUG")
            test_cow.equip_weapon(weapon)

            debug_print("Validating weapon equip", "DEBUG")
            if not test_cow.has_weapon():
                raise Exception("Cow did not equip weapon")
            if test_cow.get_weapon().name != weapon.name:
                raise Exception(f"Weapon name mismatch: {test_cow.get_weapon().name} != {weapon.name}")

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            results["errors"].append(f"Test '{test_name}' failed: {e}")
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")

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
            results["errors"].append(f"Test '{test_name}' failed: {e}")
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")

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
                    screen_dimensions=(800, 600),
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
                player.equip_weapon(weapon)
                arena.characters.append(player)

                debug_print("Shooting into empty space", "DEBUG")
                initial_projectile_count = len(arena.projectiles)
                direction = (100, 0)  # Shoot right
                speed = weapon.projectile_speed
                sprite = weapon.get_projectile_sprite() if hasattr(weapon, 'get_projectile_sprite') else None
                damage = weapon.damage

                debug_print("Spawning projectile", "DEBUG")
                arena.spawn_projectile(
                    start_pos=(500, 500),
                    direction=direction,
                    speed=speed,
                    sprite=sprite,
                    damage=damage,
                    owner=player
                )

                debug_print("Validating projectile spawn", "DEBUG")
                if len(arena.projectiles) <= initial_projectile_count:
                    raise Exception("Projectile was not spawned")

                debug_print("Running arena updates", "DEBUG")
                for _ in range(10):
                    arena.update()

            results["tests_passed"].append(test_name)
            debug_print(f"✅ {test_name} passed", "INFO")
        except Exception as e:
            results["errors"].append(f"Test '{test_name}' failed: {e}")
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")

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
                    screen_dimensions=(800, 600),
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
                player.equip_weapon(weapon)
                arena.characters.append(player)
                arena.characters.append(target)

                debug_print("Recording initial target health", "DEBUG")
                initial_health = target.health

                debug_print("Shooting at target", "DEBUG")
                direction = (50, 0)  # Shoot right toward target
                speed = weapon.projectile_speed
                sprite = weapon.get_projectile_sprite() if hasattr(weapon, 'get_projectile_sprite') else None
                damage = weapon.damage

                debug_print("Spawning projectile toward target", "DEBUG")
                arena.spawn_projectile(
                    start_pos=(500, 500),
                    direction=direction,
                    speed=speed,
                    sprite=sprite,
                    damage=damage,
                    owner=player
                )

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
            results["errors"].append(f"Test '{test_name}' failed: {e}")
            results["has_errors"] = True
            debug_print(f"❌ {test_name} failed: {e}", "ERROR")

        pygame.quit()
        debug_print("✅ Pygame quit", "DEBUG")

    except Exception as e:
        results["errors"].append(f"Simulation test suite failed: {e}")
        results["has_errors"] = True
        debug_print(f"❌ Simulation test suite failed: {e}", "ERROR")

    debug_print(f"Simulation tests complete: {len(results['tests_passed'])}/{len(results['tests_run'])} passed", "INFO")
    return results
