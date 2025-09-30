"""
Combat AI for Battle Royale

This AI will:
- Seek fields to get ammo and weapons
- Attack nearby enemies when it has ammo
- Avoid enemies when low on health or ammo
"""

import random
import pygame
from pygame import Vector2
from Game.Character.cow import Cow
import math


class CombatAICow(Cow):
    """
    An AI that actively participates in battle royale combat.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wander_timer = 0
        self._wander_dir = Vector2(0, 0)
        self._target_position = None
        self._state = "wander"  # wander, seek_field, attack, flee
        self._state_timer = 0
        self._attack_range = 400  # Distance to start attacking
        self._flee_threshold = 0.3  # Flee when health below 30%
        self._ammo_seek_threshold = 3  # Seek ammo when below this
    
    def update(self, arena=None):
        super().update(arena)
        
        if self.is_dead():
            return
        
        # Update state timer
        self._state_timer -= 1
        
        # Decide on AI behavior
        self._update_ai_state(arena)
        
        # Execute behavior
        if self._state == "wander":
            self._do_wander()
        elif self._state == "seek_field":
            self._do_seek_field(arena)
        elif self._state == "attack":
            self._do_attack(arena)
        elif self._state == "flee":
            self._do_flee(arena)
    
    def _update_ai_state(self, arena):
        """Decide what the AI should do based on current situation."""
        if arena is None:
            self._state = "wander"
            return
        
        # Calculate health percentage
        health_pct = self.health / max(1, self.max_health)
        
        # Find nearest enemy
        nearest_enemy = None
        nearest_dist = float('inf')
        for char in arena.characters:
            if char is self or (hasattr(char, 'is_dead') and char.is_dead()):
                continue
            dist = (char.position - self.position).length()
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_enemy = char
        
        # Decision making
        # 1. Flee if low health and enemy nearby
        if health_pct < self._flee_threshold and nearest_dist < self._attack_range:
            if self._state != "flee" or self._state_timer <= 0:
                self._state = "flee"
                self._state_timer = 60  # Flee for ~1 second
        # 2. Attack if have weapon, ammo, and enemy in range
        elif (self.has_weapon() and self.ammo > 0 and 
              nearest_enemy is not None and nearest_dist < self._attack_range):
            self._state = "attack"
            self._target_enemy = nearest_enemy
        # 3. Seek fields if low ammo or no weapon
        elif self.ammo < self._ammo_seek_threshold or not self.has_weapon():
            if self._state != "seek_field" or self._state_timer <= 0:
                self._state = "seek_field"
                self._state_timer = 120  # Seek for ~2 seconds
                self._choose_field_target(arena)
        # 4. Default to wandering
        else:
            self._state = "wander"
    
    def _do_wander(self):
        """Random wandering behavior."""
        self._wander_timer -= 1
        if self._wander_timer <= 0:
            self._wander_timer = random.randint(30, 60)
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            self._wander_dir = Vector2(dx, dy)
        
        # Apply movement
        if self._wander_dir.x > 0:
            self.move_right()
        elif self._wander_dir.x < 0:
            self.move_left()
        if self._wander_dir.y > 0:
            self.move_down()
        elif self._wander_dir.y < 0:
            self.move_up()
    
    def _choose_field_target(self, arena):
        """Pick a nearby field to seek."""
        if arena is None:
            return
        
        # Prioritize golden fields if no weapon, else grass fields
        if not self.has_weapon() and len(arena.golden_fields) > 0:
            # Pick nearest golden field
            nearest = min(arena.golden_fields, 
                         key=lambda f: (Vector2(f.rect.center) - self.position).length())
            self._target_position = Vector2(nearest.rect.center)
        elif len(arena.grass_fields) > 0:
            # Pick nearest grass field
            nearest = min(arena.grass_fields,
                         key=lambda f: (Vector2(f.rect.center) - self.position).length())
            self._target_position = Vector2(nearest.rect.center)
        else:
            self._target_position = None
    
    def _do_seek_field(self, arena):
        """Move toward a target field."""
        if self._target_position is None:
            self._choose_field_target(arena)
        
        if self._target_position is None:
            self._do_wander()
            return
        
        # Move toward target
        direction = self._target_position - self.position
        dist = direction.length()
        
        if dist < 50:  # Close enough, start eating
            self.set_eating_intent(True)
            # Check if we're actually in a field
            if arena:
                char_rect = self.get_world_rect()
                in_field = any(char_rect.colliderect(f.rect) 
                             for f in (arena.grass_fields + arena.golden_fields))
                if in_field:
                    # Simulate eating key press
                    if hasattr(arena, 'grass_fields'):
                        for grass in arena.grass_fields:
                            if char_rect.colliderect(grass.rect):
                                self.eat()
                                break
        else:
            direction = direction.normalize()
            # Move in the direction
            if direction.x > 0.3:
                self.move_right()
            elif direction.x < -0.3:
                self.move_left()
            if direction.y > 0.3:
                self.move_down()
            elif direction.y < -0.3:
                self.move_up()
    
    def _do_attack(self, arena):
        """Attack the target enemy."""
        if not hasattr(self, '_target_enemy') or self._target_enemy is None:
            return
        
        enemy = self._target_enemy
        if hasattr(enemy, 'is_dead') and enemy.is_dead():
            self._target_enemy = None
            return
        
        # Aim at enemy
        direction = enemy.position - self.position
        self.set_aim_direction(direction)
        
        # Try to shoot
        if self.has_weapon() and self.ammo > 0:
            weapon = self.get_weapon()
            if weapon and weapon.can_fire(self.ammo):
                # Spawn projectile through arena
                if arena:
                    start = (int(self.position.x), int(self.position.y))
                    speed = getattr(weapon, 'projectile_speed', 16.0)
                    sprite = None
                    if hasattr(weapon, 'get_projectile_sprite'):
                        sprite = weapon.get_projectile_sprite()
                    damage = getattr(weapon, 'damage', 10.0)
                    arena.spawn_projectile(start, direction, speed, sprite, damage, self)
                    self.ammo = weapon.consume_ammo(self.ammo)
    
    def _do_flee(self, arena):
        """Run away from nearest enemy."""
        if arena is None:
            self._do_wander()
            return
        
        # Find nearest enemy
        nearest_enemy = None
        nearest_dist = float('inf')
        for char in arena.characters:
            if char is self or (hasattr(char, 'is_dead') and char.is_dead()):
                continue
            dist = (char.position - self.position).length()
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_enemy = char
        
        if nearest_enemy is None:
            self._do_wander()
            return
        
        # Run in opposite direction
        flee_dir = (self.position - nearest_enemy.position)
        if flee_dir.length() > 0:
            flee_dir = flee_dir.normalize()
        else:
            flee_dir = Vector2(random.choice([-1, 1]), random.choice([-1, 1]))
        
        if flee_dir.x > 0.3:
            self.move_right()
        elif flee_dir.x < -0.3:
            self.move_left()
        if flee_dir.y > 0.3:
            self.move_down()
        elif flee_dir.y < -0.3:
            self.move_up()
