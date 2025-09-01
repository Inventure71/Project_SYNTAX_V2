# SYNTAX V2 - Game Overview

### Core Mechanics

- Player controls a cow in a large world with a camera view.
- World contains grass fields, golden fields, and obstacles.
- Hold Space to eat while in any field; this slows you down while held.
- Ammo is found randomly only in regular grass fields.
- Golden fields do not grant ammo; they can drop a weapon pickup instead.
- Weapons are picked up by walking over them if you have no active weapon.
- Left-click shoots if a weapon is equipped and ammo is sufficient.

### Layers (Heights)

The game uses four height layers represented by bit flags:
- 1) underground
- 2) ground (cow default)
- 3) mid-air (projectiles)
- 4) air

Obstacles specify a blocking mask to control which layers they affect (some block only ground, some ground+mid-air, some all).

### Movement & Camera

- WASD: move.
- E/+ and Q/-: zoom in/out.
- Space: eat (when inside a field).
- Movement speed is reduced by a percentage while eating (`eating_slowdown_pct`).
- Player is clamped within world bounds.

### Fields

- GrassField: semi-transparent green patches; eating here rolls to find ammo with per-cow probability.
- GoldenField: semi-transparent gold patches; eating here never gives ammo. Instead, a small field-specific probability rolls to drop a weapon pickup near the field center.

### Weapons & Projectiles

- Weapons: `name`, `ammo_per_shot`, `projectile_speed`, and floor display props (`floor_rect_size`, `floor_color`).
- Weapon pickups appear on the floor and are consumed upon collision by cows that do not already have a weapon.
- Projectiles fly in the mid-air layer and are destroyed when hitting obstacles that block mid-air.
- Ammo consumption is per weapon (`ammo_per_shot`).

### Obstacles

- Obstacles have health and a blocking mask.
- They currently cannot be damaged (damage APIs exist but are unused).
- Collision prevents cows from passing through obstacles that block their current layer.

### Extensibility

- Add more field types by creating new objects with draw/update logic and integrating into `Arena`.
- Add new weapons by instantiating `Weapon` with different parameters.
- Adjust cow parameters (speed, ammo find probability, eating slowdown) via `Cow` init.

### File Guide

- `Game/Arena/arena.py`: world generation, update/draw loop, collisions, UI, pickups, projectile management.
- `Game/Character/cow.py`: player avatar, movement, camera, eating, ammo, weapon equip/shoot hooks.
- `Game/Objects/grass.py`, `golden_field.py`, `obstacle.py`, `projectile.py`, `weapon_pickup.py`.
- `Game/Weapons/weapon.py`: weapon definition.
- `Game/layers.py`: layer constants and helpers.

### Rules to Preserve

- 4-layer system; collisions respect layer masks.
- Golden fields never drop ammo; only weapon pickups with a chance.
- Eating slows the cow by a configured percentage.
- Projectiles occupy mid-air and collide with obstacles that block mid-air.
- Player cannot leave world bounds or pass through blocking obstacles.
