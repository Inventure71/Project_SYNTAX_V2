# SYNTAX V2 Game Overview

This project is a top-down arena shooter built on Pygame. The main gameplay loop lives in `main.py`, which boots the Pygame display, instantiates an `Arena`, creates player `Cow` characters, and advances the simulation until one character remains.

## Core Gameplay Objects

- **Arena (`Game/Arena/arena.py`)**
  - Owns the world state: characters, projectiles, loot objects, obstacles, grass fields, and golden fields.
  - `update()` advances every entity, resolves projectile collisions, clamps characters inside the world bounds, and auto-equips pickups for unarmed players.
  - `spawn_projectile(start_pos, direction, speed, sprite, damage, owner)` is the single entry point for firing. Custom weapons can set `weapon.projectile_class`; otherwise the base `Projectile` class is used. Projectiles must manage their own `alive` flag.
  - Loot pools (e.g., the golden field) are configured inside this file and expect new weapons to register imports and to append instantiated weapons to the `weapons_pool` list.

- **Cow (`Game/Character/cow.py`)**
  - Represents a player avatar: tracks position, movement, zoom, health/stamina, ammo, and equipped weapon.
  - Effect handling uses the pattern `self.is_<effect>` plus `apply_<effect>(...)` methods. `apply_` methods are triggered by projectiles and should schedule timers or state in `_update_effects()` if the effect needs expiration logic.
  - The cow delegates abilities through `AbilityManager` and enforces rendering via a configurable renderer. Always keep one statement per line when editing this file.

- **Weapon Base (`Game/Weapons/weapon.py`)**
  - The `Weapon` class defines shared attributes (`name`, `damage`, `projectile_speed`, `fire_rate`, `ammo_per_shot`, `floor_image_name`, etc.) plus helper methods for spawning projectiles and retrieving sprites.
  - Custom weapons must inherit from `Weapon`, set core attributes in `__init__`, optionally override `fire()` for special behaviour, and provide a factory function `create_<weapon>()` returning an instance. Use `placeholder.png` for both floor and projectile sprites.

- **Projectile Base (`Game/Objects/projectile.py`)**
  - Encapsulates movement and collision basics. Projectiles update their position in `update()` and signal destruction by setting `self.alive = False`.
  - Custom projectiles should inherit from this class, override `update()` for motion tweaks, and implement `on_character_hit(self, target, arena)` to apply damage/effects and dispose of the projectile.

- **Supporting Objects**
  - `Game/Objects/weapon_pickup.py` wraps weapons for the world, `Game/Objects/golden_field.py` periodically spawns pickups, and `Game/Objects/obstacle.py` handles collision volumes.
  - Abilities live under `Game/Abilities/` and are managed by the cow’s `AbilityManager`.

## Implementation Conventions

- **Formatting**: Absolutely one statement per line. Keep indentation at four spaces and maintain blank lines between methods.
- **Images**: New content must use `placeholder.png` for both floor and projectile images unless explicitly replaced after art is delivered.
- **Effect Naming**: Status/on-hit effects follow the `impact_<slug>` convention. When introducing a new status effect, add `self.is_<slug>` fields plus `apply_<slug>(...)` methods in `Cow`. Projectile-only behaviours fall under `projectile_behavior_<slug>` and should drive logic inside the projectile class.
- **Arena Integration**: Every new weapon must (a) register an import at the top of `Game/Arena/arena.py` and (b) append an instance to the `weapons_pool` list so it can drop in the golden field.
- **Projectile Lifecycle**: Use `arena.spawn_projectile(...)` with parameters in this exact order: `start_pos, direction, speed, sprite, damage, owner`. When a projectile should disappear, set `self.alive = False`—never call `self.kill()`.
- **File Access Tools**: When coding via the automation agent, always read files with `read_file(path, line_count=True)` before editing, apply changes using `write_into_file`/`write_over_file`, and re-read to verify.

Keep this document in mind whenever you generate or modify gameplay code so that weapons, projectiles, and effects remain consistent with the existing systems.
