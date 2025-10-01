"""Runtime-editable weapon simulation test suite."""

from __future__ import annotations

import importlib
import io
import traceback
from typing import Any, Callable, Dict, List, Optional

import pygame
from pygame import Vector2


def _default_debug(message: str, level: str = "INFO") -> None:
    print(f"[{level}] {message}")


class WeaponSimulationTestSuite:
    """Collection of runtime-editable simulation tests for generated weapons."""

    def __init__(
        self,
        weapon_plan: Dict[str, Any],
        debug_printer: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        self.weapon_plan = weapon_plan
        self.debug = debug_printer or _default_debug

        self.results: Dict[str, Any] = {
            "tests_run": [],
            "tests_passed": [],
            "errors": [],
            "has_errors": False,
        }

        self.test_screen: Optional[pygame.Surface] = None
        self.Arena = None
        self.Cow = None
        self.create_weapon_func = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run(self) -> Dict[str, Any]:
        """Execute all simulation tests and return aggregated results."""

        self._log("📋 Test scenarios:", "INFO")
        self._log("     1. Weapon pickup", "INFO")
        self._log("     2. Finding ammo", "INFO")
        self._log("     3. Shooting nothing", "INFO")
        self._log("     4. Shooting player", "INFO")

        try:
            self._initialize_environment()
            if not self._import_weapon_factory():
                return self.results

            self._run_weapon_pickup()
            self._run_finding_ammo()
            self._run_shooting_nothing()
            self._run_shooting_player()
        except Exception as exc:  # pragma: no cover - safety net
            raw_trace = traceback.format_exc()
            detailed_error = (
                "Simulation test suite failed with "
                f"{exc.__class__.__name__}: {exc}\n"
                f"Traceback:\n{raw_trace.strip()}"
            )
            self.results["errors"].append(detailed_error)
            self.results["has_errors"] = True
            self._log(f"❌ Simulation test suite failed: {exc}", "ERROR")
            self._log(f"Traceback details for simulation suite:\n{raw_trace}", "DEBUG")
        finally:
            pygame.quit()
            self._log("✅ Pygame quit", "DEBUG")

        return self.results

    # ------------------------------------------------------------------
    # Environment helpers
    # ------------------------------------------------------------------
    def _initialize_environment(self) -> None:
        weapon_name = self.weapon_plan.get("weapon_name", "TestWeapon")
        self._log(f"Setting up simulation environment for weapon: {weapon_name}", "INFO")

        pygame.init()
        self._log("✅ Pygame initialized", "DEBUG")

        self.test_screen = pygame.display.set_mode((100, 100), pygame.HIDDEN)
        self._log("✅ Test screen created", "DEBUG")

        from Game.Arena.arena import Arena  # Lazy import to avoid circular deps
        from Game.Character.cow import Cow

        self.Arena = Arena
        self.Cow = Cow

    def _import_weapon_factory(self) -> bool:
        weapon_name = self.weapon_plan.get("weapon_name", "TestWeapon")
        weapon_class_name = self.weapon_plan.get("weapon_class_name", weapon_name)
        weapon_module_path = f"Game.Weapons.{weapon_class_name.lower()}"

        self._log(f"Attempting to import weapon: {weapon_class_name}", "DEBUG")
        try:
            weapon_module = importlib.import_module(weapon_module_path)
            factory_name = f"create_{weapon_class_name.lower()}"
            self.create_weapon_func = getattr(weapon_module, factory_name)
            self._log(f"✅ Weapon imported successfully: {weapon_class_name}", "INFO")
            return True
        except Exception as exc:
            self.results["errors"].append(f"Failed to import weapon: {exc}")
            self.results["has_errors"] = True
            self._log(f"❌ Failed to import weapon: {exc}", "ERROR")
            return False

    # ------------------------------------------------------------------
    # Individual tests
    # ------------------------------------------------------------------
    def _run_weapon_pickup(self) -> None:
        test_name = "weapon_pickup"
        self._start_test(test_name)

        try:
            self._log(f"Creating test cow for {test_name}", "DEBUG")
            test_cow = self.Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000),
            )

            self._log("Creating weapon instance", "DEBUG")
            weapon = self.create_weapon_func()
            self._validate_weapon_description(weapon)

            self._log("Equipping weapon on cow", "DEBUG")
            test_cow.equip_weapon(weapon)

            self._log("Triggering handle_event for weapon control", "DEBUG")
            if hasattr(test_cow, "handle_event"):
                test_event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 500)
                )
                test_cow.handle_event(test_event)

            self._log("Validating weapon equip", "DEBUG")
            if not test_cow.has_weapon():
                raise Exception("Cow did not equip weapon")
            if test_cow.get_weapon().name != weapon.name:
                raise Exception(
                    f"Weapon name mismatch: {test_cow.get_weapon().name} != {weapon.name}"
                )

            self._record_success(test_name)
        except Exception as exc:
            self._record_failure(test_name, exc)

    def _run_finding_ammo(self) -> None:
        test_name = "finding_ammo"
        self._start_test(test_name)

        try:
            self._log(f"Creating test cow for {test_name}", "DEBUG")
            test_cow = self.Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000),
                starting_ammo=0,
            )
            self._log("Equipping weapon on cow", "DEBUG")
            weapon = self.create_weapon_func()
            self._validate_weapon_description(weapon)
            test_cow.equip_weapon(weapon)

            self._log("Simulating ammo finding", "DEBUG")
            initial_ammo = test_cow.ammo
            test_cow.ammo += 10

            self._log("Validating ammo increase", "DEBUG")
            if test_cow.ammo <= initial_ammo:
                raise Exception("Ammo did not increase")

            self._record_success(test_name)
        except Exception as exc:
            self._record_failure(test_name, exc)

    def _run_shooting_nothing(self) -> None:
        test_name = "shooting_nothing"
        self._start_test(test_name)

        try:
            self._log("Creating arena for shooting test", "DEBUG")

            with io.StringIO():  # Suppress pygame output
                self._log("Creating arena with hidden display", "DEBUG")
                arena = self.Arena(
                    screen_dimensions=(0, 0, 800, 600),
                    world_screen_dimensions=(2000, 2000),
                    screen=self.test_screen,
                    world_screen=self.test_screen,
                    text=None,
                )

                self._log("Creating player cow", "DEBUG")
                player = self.Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Player",
                    starting_position=(500, 500),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                    starting_ammo=10,
                )

                self._log("Equipping weapon", "DEBUG")
                weapon = self.create_weapon_func()
                self._validate_weapon_description(weapon)
                player.equip_weapon(weapon)
                arena.characters.append(player)

                self._log("Triggering handle_event for firing test", "DEBUG")
                if hasattr(player, "handle_event"):
                    fire_event = pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, button=1, pos=(500, 500)
                    )
                    player.handle_event(fire_event)

                self._log("Firing weapon via weapon.fire", "DEBUG")
                initial_projectile_count = len(arena.projectiles)
                direction = Vector2(100, 0)
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                projectiles = weapon.fire(player.position, direction, player)

                if isinstance(projectiles, list):
                    arena.projectiles.extend(projectiles)
                elif projectiles:
                    arena.projectiles.append(projectiles)

                self._log("Validating projectile spawn", "DEBUG")
                if len(arena.projectiles) <= initial_projectile_count:
                    raise Exception("weapon.fire did not return any projectiles")

                self._log("Running arena updates", "DEBUG")
                for _ in range(10):
                    arena.update()

            self._record_success(test_name)
        except Exception as exc:
            self._record_failure(test_name, exc)

    def _run_shooting_player(self) -> None:
        test_name = "shooting_player"
        self._start_test(test_name)

        try:
            self._log("Creating arena for player vs player test", "DEBUG")

            with io.StringIO():
                self._log("Creating arena", "DEBUG")
                arena = self.Arena(
                    screen_dimensions=(0, 0, 800, 600),
                    world_screen_dimensions=(2000, 2000),
                    screen=self.test_screen,
                    world_screen=self.test_screen,
                    text=None,
                )

                self._log("Creating player and target cows", "DEBUG")
                player = self.Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Player",
                    starting_position=(500, 500),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                    starting_ammo=10,
                )

                target = self.Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="Target",
                    starting_position=(550, 500),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                )

                self._log("Equipping weapon", "DEBUG")
                weapon = self.create_weapon_func()
                self._validate_weapon_description(weapon)
                player.equip_weapon(weapon)
                arena.characters.append(player)
                arena.characters.append(target)

                self._log("Triggering handle_event for combat scenario", "DEBUG")
                if hasattr(player, "handle_event"):
                    attack_event = pygame.event.Event(
                        pygame.MOUSEBUTTONDOWN, button=1, pos=(550, 500)
                    )
                    player.handle_event(attack_event)

                self._log("Recording initial target health", "DEBUG")
                initial_health = target.health

                self._log("Shooting at target", "DEBUG")
                direction = Vector2(50, 0)
                if direction.length_squared() > 0:
                    direction = direction.normalize()
                projectiles = weapon.fire(player.position, direction, player)

                if isinstance(projectiles, list):
                    arena.projectiles.extend(projectiles)
                elif projectiles:
                    arena.projectiles.append(projectiles)

                self._log("Running arena updates to detect hit", "DEBUG")
                for _ in range(30):
                    arena.update()
                    if target.health < initial_health:
                        self._log(
                            "✅ Target took damage - hit detection working", "INFO"
                        )
                        break

                self._log("Validating damage application", "DEBUG")
                if target.health >= initial_health:
                    raise Exception(
                        "Target did not take damage "
                        f"(health: {target.health} >= {initial_health})"
                    )

            self._record_success(test_name)
        except Exception as exc:
            self._record_failure(test_name, exc)

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _start_test(self, name: str) -> None:
        self.results["tests_run"].append(name)
        self._log(f"🏃 Running test: {name}", "INFO")

    def _record_success(self, name: str) -> None:
        self.results["tests_passed"].append(name)
        self._log(f"✅ {name} passed", "INFO")

    def _record_failure(self, name: str, error: Exception) -> None:
        raw_trace = traceback.format_exc()
        detailed_error = self._format_exception_details(name, error, raw_trace)
        self.results["errors"].append(detailed_error)
        self.results["has_errors"] = True
        self._log(f"❌ {name} failed: {error}", "ERROR")
        self._log(f"Traceback details for {name}:\n{raw_trace}", "DEBUG")

    def _validate_weapon_description(self, weapon: Any) -> None:
        expected_description = self.weapon_plan.get("description")
        if isinstance(expected_description, str) and expected_description.strip():
            actual_description = getattr(weapon, "description", "")
            if actual_description.strip() != expected_description.strip():
                raise Exception(
                    "Weapon description mismatch: "
                    f"expected '{expected_description.strip()}' "
                    f"got '{actual_description.strip()}'"
                )

    def _format_exception_details(
        self, test_name: str, error: Exception, raw_trace: Optional[str] = None
    ) -> str:
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
                if (
                    "Project_SYNTAX_V2" in line
                    or "Game/" in line
                    or "Game\\" in line
                ):
                    relevant_chunks.append("\n".join(snippet))
            i += 1

        if not relevant_chunks:
            relevant_chunks = ["\n".join(trace_lines[-4:])]

        formatted_lines.append("Relevant traceback frames:")
        formatted_lines.extend(relevant_chunks)
        return "\n".join(formatted_lines)

    def _log(self, message: str, level: str = "INFO") -> None:
        self.debug(message, level)

