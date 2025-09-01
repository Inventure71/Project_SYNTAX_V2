import sys
from Game.constants import UI_DARK_2, UI_DARK, UI_STROKE, WHITE, FONT
from Game.UI_Components.button import Button
import pygame


class Menu:
    def __init__(self, rect, text):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = FONT
        self.hover = False
        self.buttons = [Button((0, 0, 100, 100), "Button 1", self.font, self.print_hello)]

    def print_hello(self):
        print("Hello")

    def background(self, surf):
        pygame.draw.rect(surf, WHITE, self.rect, border_radius=10)
        pygame.draw.rect(surf, UI_STROKE, self.rect, width=2, border_radius=10)

    def draw(self, surf):
        self.background(surf)
        for button in self.buttons:
            button.draw(surf)

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)