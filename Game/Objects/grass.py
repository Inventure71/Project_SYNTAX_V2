import pygame


class GrassField:
    def __init__(self, rect, color=(60, 150, 90), alpha=90):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.alpha = alpha

    def update(self):
        pass

    def draw(self, surface):
        # Draw a semi-transparent patch to indicate grass
        grass_surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        r, g, b = self.color
        grass_surface.fill((r, g, b, self.alpha))
        surface.blit(grass_surface, self.rect.topleft)

    def handle_event(self, event):
        pass




