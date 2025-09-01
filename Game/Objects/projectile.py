import pygame
from pygame import Vector2
from Game.layers import LAYER_MIDAIR


class Projectile:
    def __init__(self, start_pos, direction, speed: float = 16.0, color=(255, 250, 220), radius: int = 4, max_distance: float = 2400.0, sprite=None, damage: float = 10.0, owner=None):
        self.position = Vector2(start_pos)
        dir_vec = Vector2(direction)
        if dir_vec.length() == 0:
            dir_vec = Vector2(1, 0)
        self.velocity = dir_vec.normalize() * float(speed)
        self.color = color
        self.radius = int(radius)
        self.distance_traveled = 0.0
        self.max_distance = float(max_distance)
        self.alive = True
        self.layer = LAYER_MIDAIR
        self.sprite = sprite
        self.damage = float(damage)
        self.owner = owner

    def update(self):
        if not self.alive:
            return
        self.position += self.velocity
        self.distance_traveled += self.velocity.length()
        if self.distance_traveled >= self.max_distance:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        if self.sprite is not None:
            rect = self.sprite.get_rect(center=(int(self.position.x), int(self.position.y)))
            surface.blit(self.sprite, rect)
        else:
            pygame.draw.circle(surface, self.color, (int(self.position.x), int(self.position.y)), self.radius)

    def handle_event(self, event):
        pass


