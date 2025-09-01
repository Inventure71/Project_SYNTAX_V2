import pygame


class GoldenField:
    def __init__(self, rect, drop_probability: float = 0.05, color=(220, 180, 40), alpha=110):
        self.rect = pygame.Rect(rect)
        self.drop_probability = float(drop_probability)
        self.color = color
        self.alpha = alpha

    def update(self):
        pass

    def draw(self, surface):
        # Semi-transparent golden patch
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        r, g, b = self.color
        surf.fill((r, g, b, self.alpha))
        surface.blit(surf, self.rect.topleft)

    def handle_event(self, event):
        pass




