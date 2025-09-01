import pygame


class WeaponPickup:
    def __init__(self, weapon, center_pos):
        self.weapon = weapon
        w, h = getattr(weapon, 'floor_rect_size', (16, 8))
        cx, cy = int(center_pos[0]), int(center_pos[1])
        self.rect = pygame.Rect(0, 0, int(w), int(h))
        self.rect.center = (cx, cy)
        self.alive = True

    def update(self):
        pass

    def draw(self, surface):
        if not self.alive:
            return
        color = getattr(self.weapon, 'floor_color', (210, 230, 255))
        pygame.draw.rect(surface, color, self.rect, border_radius=4)
        pygame.draw.rect(surface, (40, 46, 58), self.rect, width=1, border_radius=4)

    def handle_event(self, event):
        pass




