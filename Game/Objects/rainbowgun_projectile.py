"""
Custom Projectile for RainbowGun

Applies effects: stun, charm
"""

import pygame
from pygame import Vector2
from Game.Objects.projectile import Projectile


class RainbowGunProjectile(Projectile):
    """
    Custom projectile that applies stun, charm effect(s) on hit.
    """
    
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        # Call parent constructor with correct parameter order
        # Projectile.__init__(start_pos, direction, speed, color, radius, max_distance, sprite, damage, owner)
        super().__init__(position, direction, speed, (255, 200, 255), 4, 2400.0, sprite, damage, owner)
        self.effect_types = ['stun', 'charm']
        self.effect_details = {'stun': {'duration_ms': 4000, 'description': 'Target is incapacitated by overwhelming positive feelings, unable to move or attack.'}, 'charm': {'flavor': "A wave of harmless, euphoria-inducing light that makes targets feel 'in heaven'. Especially effective on bovine enemies.", 'visual_fx': 'Multicolored light arcs and sparkling dust.'}}
    
    def on_character_hit(self, target, arena):
        """
        Called when this projectile hits a character.
        Applies effects in addition to damage.
        
        Args:
            target: The character that was hit
            arena: The game arena
        """
        # Apply damage (standard projectile behavior)
        if hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        
        # Apply effects
        if not hasattr(target, 'is_dead') or not target.is_dead():
            current_time = pygame.time.get_ticks()
            if hasattr(target, 'apply_stun'):
                target.apply_stun(4000, current_time)
            if hasattr(target, 'apply_charm'):
                target.apply_charm(3000, current_time)

        
        # Mark projectile as dead
        self.alive = False
