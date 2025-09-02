import pygame


class Poop:
    def __init__(self, center_pos, size=(18, 12), ttl_ms: int = 8000, color=(130, 90, 40), amount_percent: float = 0.15):
        self.rect = pygame.Rect(0, 0, int(size[0]), int(size[1]))
        self.rect.center = (int(center_pos[0]), int(center_pos[1]))
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.ttl_ms = int(ttl_ms)
        self.alive = True
        self.amount_percent = float(amount_percent)

    def update(self):
        if not self.alive:
            return
        now = pygame.time.get_ticks()
        if now - self.spawn_time >= self.ttl_ms:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return
        pygame.draw.rect(surface, self.color, self.rect, border_radius=3)
        pygame.draw.rect(surface, (30, 24, 18), self.rect, width=1, border_radius=3)

    def handle_event(self, event):
        pass

    # For future abilities, this callback will be used by the arena on collision
    def on_character_collide(self, character, arena):
        # Placeholder for future effects (e.g., slowing, damage, etc.)
        return


