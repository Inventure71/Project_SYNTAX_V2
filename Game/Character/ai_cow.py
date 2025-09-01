import random
import pygame
from pygame import Vector2
from Game.Character.cow import Cow


class AICow(Cow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._wander_timer = 0
        self._wander_dir = Vector2(0, 0)

    def update(self):
        super().update()
        # Simple wandering: pick a direction every ~0.5s
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

