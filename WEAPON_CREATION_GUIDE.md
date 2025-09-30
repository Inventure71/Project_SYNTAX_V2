# Weapon Creation Guide

## Overview

Creating weapons is simpler than creating abilities! Weapons only need:
- Name and stats (damage, ammo per shot, projectile speed)
- Optional sprites (weapon icon and projectile image)

## Quick Start

```bash
python test_creation.py
```

Choose option **1. Create Weapon** 🔫

## How It Works

### 1. Describe Your Weapon

Examples:
- "A rainbow gun that does 25 damage but uses 3 ammo per shot"
- "A fast laser gun with very fast projectiles but low damage"
- "A powerful shotgun that does high damage but uses 2 ammo"

### 2. Agent Creates the Weapon

The workflow:
1. **📦 Creates backup** - All files backed up before changes
2. **📋 Generates config** - AI determines stats and properties
3. **🔨 Creates weapon file** - Generates `Game/Weapons/yourweapon.py`
4. **📖 Creates integration guide** - Shows how to use it

### 3. Use the Weapon in Game

The agent creates a usage file showing exactly how to integrate:

**Option A: Spawn as pickup (recommended)**
```python
# In Game/Arena/arena.py, add your weapon to golden field drops
from Game.Weapons.rainbowgun import create_rainbowgun

# Inside handle_key_event where weapons spawn:
weapon = create_rainbowgun()
pickup = WeaponPickup(weapon, (gx + offset, gy))
self.objects.append(pickup)
```

**Option B: Give directly to character**
```python
# In main.py
from Game.Weapons.rainbowgun import create_rainbowgun

player.equip_weapon(create_rainbowgun())
# Or for AI:
npc.equip_weapon(create_rainbowgun())
```

## Weapon Properties

When describing your weapon, you can specify:

| Property | Description | Example |
|----------|-------------|---------|
| **Damage** | How much HP it removes | "does 25 damage" |
| **Ammo per shot** | Ammo consumed per shot | "uses 3 ammo" |
| **Projectile speed** | How fast bullets travel | "very fast projectiles" |
| **Fire rate** | Implied by ammo cost | "rapid fire" or "slow but powerful" |

## Example Weapons

### Rainbow Gun
```
Description: "A rainbow gun that does 25 damage but uses 3 ammo per shot"

Stats:
- Damage: 25
- Ammo per shot: 3
- Projectile speed: 18.0
- High damage, high cost
```

### Laser Gun
```
Description: "A fast laser gun with very fast projectiles but only 5 damage"

Stats:
- Damage: 5
- Ammo per shot: 1
- Projectile speed: 30.0
- Fast and efficient
```

### Shotgun
```
Description: "A powerful shotgun that does 15 damage with slower projectiles"

Stats:
- Damage: 15
- Ammo per shot: 2
- Projectile speed: 12.0
- Balanced power weapon
```

## Backup System 🛡️

**Every weapon creation automatically creates a backup!**

### Restore if Something Goes Wrong

```bash
python test_creation.py
# Choose: 4. Restore Backup
```

Backups include:
- `Game/Character/cow.py`
- `Game/Abilities/`
- `Game/Weapons/`
- `Game/Objects/`
- `main.py`

### List All Backups

```bash
python test_creation.py
# Choose: 3. List Backups
```

## File Structure

After creating a weapon named "RainbowGun":

```
Game/Weapons/
├── weapon.py              # Base weapon class
├── rainbowgun.py          # Your new weapon ✨
└── rainbowgun_usage.txt   # Integration guide
```

The weapon file contains:
```python
from Game.Weapons.weapon import Weapon

def create_rainbowgun() -> Weapon:
    return Weapon(
        name="Rainbow Gun",
        ammo_per_shot=3,
        projectile_speed=18.0,
        damage=25.0,
        # ... sprites and other config
    )

RAINBOWGUN = create_rainbowgun()
```

## Integration into Game

### Method 1: Add to Golden Field Drops (Recommended)

Edit `Game/Arena/arena.py`:

```python
# At the top, import your weapon
from Game.Weapons.rainbowgun import create_rainbowgun

# Find the handle_key_event method, around line 234-246
# where it says "spawn pickup with small offset"

# Add your weapon to the pool:
weapons_pool = [
    create_rainbowgun(),
    Weapon(name="Bow", ...),  # existing bow
]

# Pick random weapon:
weapon = random.choice(weapons_pool)
pickup = WeaponPickup(weapon, (gx + offset, gy))
self.objects.append(pickup)
```

### Method 2: Give to Player at Start

Edit `main.py` in the `create_game` function:

```python
from Game.Weapons.rainbowgun import create_rainbowgun

# After creating player:
player = Cow(...)
player.equip_weapon(create_rainbowgun())  # ✨ Player starts with your weapon!
```

### Method 3: Give to AI

```python
from Game.Weapons.rainbowgun import create_rainbowgun

# When creating AI:
npc = CombatAICow(...)
npc.equip_weapon(create_rainbowgun())
```

## Troubleshooting

### "Weapon created but not in game"
- The weapon file is created, but you need to integrate it
- Follow the integration guide in `Game/Weapons/yourweapon_usage.txt`
- Choose Method 1 (golden field drops) for easiest integration

### "Want to undo weapon creation"
```bash
python test_creation.py
# Choose: 4. Restore Backup
# Select the backup from before weapon creation
```

### "Want custom sprites"
- For now, weapons use default sprites (None)
- To add sprites:
  1. Add image files to `Game/Assets/`
  2. Edit your weapon file
  3. Change `floor_image_name` and `projectile_image_name`

Example:
```python
def create_rainbowgun() -> Weapon:
    return Weapon(
        name="Rainbow Gun",
        floor_image_name="rainbow_gun.png",  # Add your sprite
        floor_image_scale=(32, 32),
        projectile_image_name="rainbow_bullet.png",
        projectile_image_scale=(20, 8),
        # ... other config
    )
```

## Request Limiting

The agent limits API calls for safety:
- Default: 10 requests before asking permission
- You'll see a warning when limit is reached
- Choose "yes" to continue or "no" to stop

## Next Steps

1. **Create your weapon** - Use `test_creation.py`
2. **Test it** - Read the usage guide created
3. **Integrate it** - Add to arena or give to player
4. **Play!** - Run `python main.py`

## Weapon vs Ability

**Use Weapon Creation when:**
- ✅ You want a new shooting weapon
- ✅ Different damage/ammo/speed stats
- ✅ Simple, straightforward implementation

**Use Ability Creation when:**
- ✅ You want special effects (freeze, shield, teleport)
- ✅ Character status changes
- ✅ Complex interactions
- ✅ Need effects to work on any character

---

**Ready to create custom weapons?**
```bash
python test_creation.py
```
