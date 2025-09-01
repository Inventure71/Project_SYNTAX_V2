import pygame
from Game.constants import UI_DARK_2, UI_STROKE
from Game.layers import ALL_LAYERS


class Obstacle:
    def __init__(self, rect, base_health=100000, color=UI_DARK_2, blocking_mask: int = ALL_LAYERS):
        self.rect = pygame.Rect(rect)
        self.max_health = int(base_health)
        self.health = int(base_health)
        self.color = color
        self.blocking_mask = int(blocking_mask)

    def update(self):
        pass

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=6)
        pygame.draw.rect(surface, UI_STROKE, self.rect, width=1, border_radius=6)

    def handle_event(self, event):
        pass

    def apply_damage(self, amount: float):
        # Damage API present but not used yet
        new_health = self.health - float(amount)
        self.health = max(0, int(new_health))

    def is_destroyed(self) -> bool:
        return self.health <= 0

    # Layers API
    def blocks_layer(self, layer: int) -> bool:
        return (self.blocking_mask & int(layer)) != 0


