from logging.handlers import RotatingFileHandler
import math
import os
import random
import sys

import pygame
from Agent.agent_main import AgentMain
from Game.Arena.arena import Arena
from Game.Character.cow import Cow
from Game.Character.ai_cow import AICow
from Game.UI_Components.menu import Menu
import logging

from Game.constants import BORDER, FONT
from Game.examples import WORLD_H, WORLD_W
import Game.constants as C

handler = RotatingFileHandler(
    "logs.log", maxBytes=2000, backupCount=1
)

logging.basicConfig(
    handlers=[handler],
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

def convert_key_to_string(key):
    keys = []
    if key[pygame.K_d]:
        keys.append("right")
    if key[pygame.K_a]:
        keys.append("left")
    if key[pygame.K_w]:
        keys.append("up")
    if key[pygame.K_s]:
        keys.append("down")
    # Camera zoom controls (keyboard)
    if key[pygame.K_e] or key[pygame.K_EQUALS]:
        keys.append("zoom_in")
    if key[pygame.K_q] or key[pygame.K_MINUS]:
        keys.append("zoom_out")
    if key[pygame.K_SPACE]:
        keys.append("eat")
    return keys

if __name__ == "__main__":
    #agent_main = AgentMain()
    #agent_main.run()
    #agent_main.test()

    camera_size = (900, 600)
    world_size = (WORLD_W, WORLD_H)
    
    pygame.init()
    screen = pygame.display.set_mode(camera_size)
    pygame.display.set_caption("Test")

    world_surf = pygame.Surface(world_size).convert_alpha()

    FONT = pygame.font.SysFont(None, 22)
    BIG_FONT = pygame.font.SysFont(None, 28)
    # Propagate fonts to constants module for other modules to use
    C.FONT = FONT
    C.BIGFONT = BIG_FONT
    clock = pygame.time.Clock()

    """
    menu = Menu((0, 0, 900, 600), "Menu", FONT)
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            menu.handle_event(event)
        menu.draw(screen)
        pygame.display.flip()
        pygame.time.wait(10)
        """

    arena = Arena((0,0, camera_size[0], camera_size[1]), world_size, screen, world_surf, "Arena")

    player = Cow((0, 0, 50, 50), "muuu", (WORLD_W * 0.5, WORLD_H * 0.5), camera_display_size=camera_size, world_display_size=world_size, ammo_find_probability=0.2, move_step=4)

    arena.add_new_character(player)
    # Spawn some AI cows
    npc1 = AICow((0, 0, 50, 50), "npc1", (WORLD_W * 0.5 + 120, WORLD_H * 0.5), camera_display_size=camera_size, world_display_size=world_size, ammo_find_probability=0.1, move_step=3)
    npc2 = AICow((0, 0, 50, 50), "npc2", (WORLD_W * 0.5 - 160, WORLD_H * 0.5 + 80), camera_display_size=camera_size, world_display_size=world_size, ammo_find_probability=0.1, move_step=3)
    arena.add_new_character(npc1)
    arena.add_new_character(npc2)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            arena.handle_event(event)


        keys = convert_key_to_string(pygame.key.get_pressed())
        arena.handle_key_event(keys)
        
        arena.step()
        
        pygame.display.flip()
        pygame.time.wait(10)




