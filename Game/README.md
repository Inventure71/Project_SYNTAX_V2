# SYNTAX V2 - Battle Royale Developer Guide

### High-level Concept
- **Genre**: Battle Royale with top-down camera and large scrolling world.
- **Goal**: Last cow standing. Players and AI roam, loot, grow/shrink via eating/pooping, and fight using weapons and projectiles.
- **Core Loop**:
  - Explore the world (WASD, camera follows).
  - **Eat** in fields to grow and roll for ammo (grass) or roll for weapon drops (golden).
  - **Equip** weapons by walking over pickups when unarmed.
  - **Aim & Shoot** with the mouse; projectiles collide with obstacles and characters.
  - **Manage size**: Eating grows you (more max HP, slower). Pooping shrinks you (less max HP, faster). Positioning and timing matter.

### Controls
- **Move**: WASD (or arrow keys via mapping).
- **Zoom**: E / + to zoom in, Q / - to zoom out, or mouse wheel.
- **Eat**: Hold Space (only inside grass or golden fields). Slows movement while active.
- **Shoot**: Left-click (if a weapon is equipped and ammo sufficient). Aims toward cursor in world space.
- **Poop**: P to shrink and create a temporary ground object.

### World & Camera
- Large world off-screen surface; the player camera crops and scales a region to the main window.
- Camera is clamped to world bounds. Player is also clamped and cannot leave bounds.
- `Arena.render_cameras_per_player(index)` builds the per-player camera view; input and aiming convert screen-space to world-space for accurate shooting.

### Layer System (Heights)
- Layers are bit flags defined in `Game/layers.py`:
  - 1) underground
  - 2) ground (cows)
  - 3) mid-air (projectiles)
  - 4) air
- Obstacles define a blocking mask to specify which layers they affect. Collisions respect these masks.
- Projectiles travel in the **mid-air** layer and collide with any obstacle that blocks mid-air.

### Entities and Responsibilities
- `Game/Arena/arena.py`:
  - Generates world content (grass, golden fields, obstacles) with randomized positions and properties.
  - Holds lists for `characters`, `objects`, `grass_fields`, `golden_fields`, `obstacles`, `projectiles`.
  - Frame loop: `update()` → `draw()` → `render_cameras_per_player()` → `draw_ui()`.
  - Resolves projectile collisions, pushes characters out of blocking obstacles, clamps to bounds.
  - Handles pickup collisions: cows without a weapon auto-equip on contact; pickups are consumed.
  - Input handling: sets “eating intent” when in fields, invokes cow `eat()` on grass or rolls weapon drops on golden fields, triggers poop spawn, and handles mouse-based shooting/aiming.
- `Game/Character/cow.py`:
  - Player/AI base class with health, stamina, ammo, size-scaling, zoom, aiming, and movement.
  - Eating/pooping with cooldowns; eating attempts ammo find; size scaling modifies speed and max HP.
  - Weapon API: `equip_weapon`, `has_weapon`, `get_weapon`, ammo consumption checked by weapon.
  - Rendering: cow and weapon overlay oriented to aim direction.
- `Game/Character/ai_cow.py`:
  - Simple wandering AI extending `Cow` (random direction changes over time).
- `Game/Objects/*.py`:
  - `grass.py` → semi-transparent green patches; eating here can yield ammo.
  - `golden_field.py` → semi-transparent gold patches; eating here never grants ammo, rolls a weapon pickup drop chance near the field center.
  - `obstacle.py` → healthful blocking objects respecting layer masks; currently not destructible in gameplay.
  - `weapon_pickup.py` → floor item that equips on contact if the cow has no weapon.
  - `projectile.py` → mid-air bullets with speed, max distance, damage, and optional sprite.
  - `poop.py` → temporary ground object spawned by cows; currently placeholder for future effects and times out.
- `Game/Weapons/weapon.py`:
  - Data-driven weapon with `ammo_per_shot`, `projectile_speed`, `damage`, and optional floor/projectile sprites.
  - Methods: `can_fire(ammo)`, `consume_ammo(ammo)`, and sprite helpers.

### Battle Royale Mechanics to Keep
- **Last cow standing** framing; health reaches 0 → cow is dead (rendered dead sprite when applicable).
- **Eating slows movement** by `eating_slowdown_pct` while active.
- **Grass vs Golden parity**:
  - Grass fields: eating attempts to find ammo via per-cow probability (`Cow.ammo_find_probability`).
  - Golden fields: eating never gives ammo; instead, roll `GoldenField.drop_probability` to spawn a weapon pickup (e.g., Bow).
- **Weapons and Ammo**:
  - Engine supports any number of weapon types; define as many `Weapon` instances as desired. The equip/shoot/pickup/projectile pipeline is type-agnostic.
  - You can hold at most one active weapon per cow by default. If unarmed and you touch a pickup, you auto-equip it.
  - Shooting consumes ammo according to weapon `ammo_per_shot`. Shots only occur if `can_fire(ammo)`.
  - Projectiles belong to mid-air, collide with blocking obstacles, and can damage other characters on hit.
- **Size Scaling**:
  - Eating grows you: increases `size_scale` up to `max_scale`; recalculates `max_health` and preserves health ratio; reduces speed via scale factor.
  - Poop shrinks you: decreases `size_scale` down to `min_scale`; reduces `max_health` accordingly; speed effectively increases back toward base.
- **Obstacle Blocking**:
  - Collisions resolve by minimal push vectors, repeated a few iterations to separate overlaps.
  - Only obstacles with masks including the cow’s layer will block.
- **Bounds**:
  - Characters are clamped to world bounds every frame; camera and projectiles also guard against leaving the world.

### UI and Aiming
- HUD shows ammo, weapon name, and HP for the primary player.
- Mouse movement updates the cow’s `aim_direction`; left-click casts to world space and spawns a projectile.

### Extending the Game
- **New Fields**: create a new object class with `update/draw` and add to `Arena` generation; use rect overlap checks for interaction.
- **New Weapons**: create unlimited weapon types by instantiating `Weapon` with desired parameters and sprites. To extend drops, maintain a weapon drop pool (list of weapon factories or configs) and choose randomly when `Arena` spawns golden-field pickups.
- **New Abilities/Objects**: implement an object with `on_character_collide(character, arena)` to define effects.
- **Destructible Obstacles**: wire `apply_damage` and consume when `is_destroyed()`; ensure layer masks are honored.
- **AI Variants**: subclass `Cow` and override `update()` to add behaviors (e.g., chase, avoid, team play).

### File Guide
- `Game/Arena/arena.py`: world generation, update/draw loop, collisions, UI, input mapping, pickups, projectile management.
- `Game/Character/cow.py`: movement, zoom, size scaling, health, eating/pooping, weapon handling, rendering, aiming.
- `Game/Character/ai_cow.py`: simple wandering AI.
- `Game/Objects/grass.py`, `golden_field.py`, `obstacle.py`, `projectile.py`, `weapon_pickup.py`, `poop.py`.
- `Game/Weapons/weapon.py`: weapon specification and sprites.
- `Game/layers.py`: layer constants and helpers.
- `Game/assets.py`: image loader with simple cache.

### Invariants / Rules to Preserve
- 4-layer system with bitmask-based blocking; projectiles in mid-air collide accordingly.
- Golden fields never drop ammo; they only roll weapon pickups.
- Eating slows movement by configured percentage and triggers growth.
- Player and AI cannot leave world bounds or pass through blocking obstacles.
- Weapon auto-equip only when the cow has no weapon; pickups are consumed on equip.
- Screen-to-world aiming for accurate projectile direction and spawn.
- Any number of weapon types can be defined; default gameplay assumes one active weapon per cow.
