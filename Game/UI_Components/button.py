from Game.constants import UI_DARK_2, UI_DARK, UI_STROKE, WHITE

import pygame


class Button:
    def __init__(self, rect, text, font, event_handler=None):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hover = False
        self.event_handler = event_handler

    def draw(self, surf):
        pygame.draw.rect(surf, UI_DARK_2 if self.hover else UI_DARK, self.rect, border_radius=10)
        pygame.draw.rect(surf, UI_STROKE, self.rect, width=2, border_radius=10)
        txt = self.font.render(self.text, True, WHITE)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.event_handler:
                    self.event_handler()
                return True
        return False