import pygame
from pygame import Vector2
from Game.Objects.projectile import Projectile
from Game.layers import LAYER_MIDAIR

class SpiralProjectile(Projectile):
    # Angular velocity for the spiral (degrees per frame)
    SPIRAL_RATE = 10
    LIFETIME = 300.0

    def __init__(self, start_pos, direction, speed, damage, sprite, owner):
        # Use "placeholder.png"
        # Use passed sprite, speed, and damage.
        super().__init__(
            start_pos=start_pos,
            direction=direction,
            speed=speed,
            radius=6,
            max_distance=SpiralProjectile.LIFETIME,
            sprite=sprite,
            damage=damage,
            owner=owner
        )

        # Scale the sprite
        self.sprite = pygame.transform.scale(self.sprite, (self.radius * 2, self.radius * 2))

    def update(self):
        if not self.alive:
            return

        # Rotate the velocity vector to create the spiral effect.
        self.velocity.rotate_ip(SpiralProjectile.SPIRAL_RATE) 

        # Apply the movement and update distance/lifetime check.
        self.position += self.velocity
        self.distance_traveled += self.velocity.length()
        
        if self.distance_traveled >= self.max_distance:
            self.alive = False


    def on_character_hit(self, target, arena):
        target.take_damage(self.damage)
        self.alive = False
