from logging.handlers import RotatingFileHandler
import math
import os
import random
import sys

import pygame
from Agent.Helpers.handle_backup import save_backup
from Agent.agent_main import AgentMain
from Game.Arena.arena import Arena
from Game.Character.cow import Cow
from Game.Character.ai_cow import AICow
from Game.Character.combat_ai_cow import CombatAICow
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
    if key[pygame.K_p]:
        keys.append("poop")
    # Ability keys
    if key[pygame.K_f]:
        keys.append("ability_dash")
    return keys

def create_game(camera_size, world_size, screen, world_surf, num_ai_players=5):
    """
    Create a new game instance with the specified number of AI players.
    
    Args:
        camera_size: Camera display size
        world_size: World dimensions
        screen: Pygame screen surface
        world_surf: World surface for rendering
        num_ai_players: Number of AI bots to spawn
        
    Returns:
        Tuple of (arena, player)
    """
    arena = Arena((0, 0, camera_size[0], camera_size[1]), world_size, screen, world_surf, "Arena")
    
    # Create player at center
    player = Cow(
        (0, 0, 50, 50), 
        "Player", 
        (WORLD_W * 0.5, WORLD_H * 0.5), 
        camera_display_size=camera_size, 
        world_display_size=world_size, 
        ammo_find_probability=0.2, 
        move_step=4
    )
    
    # Add dash ability to player
    from Game.Abilities.dash import DashAbility
    player.add_ability("dash", DashAbility(dash_distance=150, cooldown_ms=3000, energy_cost=10))
    
    arena.add_new_character(player)
    
    # Spawn AI players around the map
    import random
    for i in range(num_ai_players):
        # Random spawn position with some margin from edges
        spawn_x = random.randint(100, world_size[0] - 100)
        spawn_y = random.randint(100, world_size[1] - 100)
        
        # Use combat AI for more interesting battles
        npc = CombatAICow(
            (0, 0, 50, 50), 
            f"Bot_{i+1}", 
            (spawn_x, spawn_y), 
            camera_display_size=camera_size, 
            world_display_size=world_size, 
            ammo_find_probability=0.15,  # Slightly better ammo find rate
            move_step=3,
            starting_ammo=2  # Give them some starting ammo
        )
        arena.add_new_character(npc)
    
    return arena, player

if __name__ == "__main__":

    save_backup()

    # Configuration
    NUM_AI_PLAYERS = 5  # Change this to adjust difficulty
    camera_size = (900, 600)
    world_size = (WORLD_W, WORLD_H)
    
    pygame.init()
    screen = pygame.display.set_mode(camera_size)
    pygame.display.set_caption("SYNTAX V2 - Battle Royale")

    world_surf = pygame.Surface(world_size).convert_alpha()

    FONT = pygame.font.SysFont(None, 22)
    BIG_FONT = pygame.font.SysFont(None, 28)
    # Propagate fonts to constants module for other modules to use
    C.FONT = FONT
    C.BIGFONT = BIG_FONT
    clock = pygame.time.Clock()

    # Create initial game
    arena, player = create_game(camera_size, world_size, screen, world_surf, NUM_AI_PLAYERS)

    # Main game loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Handle restart
                if event.key == pygame.K_r and arena.game_over:
                    arena, player = create_game(camera_size, world_size, screen, world_surf, NUM_AI_PLAYERS)
                # Handle quit
                elif event.key == pygame.K_ESCAPE and arena.game_over:
                    running = False
            
            if not arena.game_over:
                arena.handle_event(event)

        # Only process keys if game is not over
        if not arena.game_over:
            keys = convert_key_to_string(pygame.key.get_pressed())
            
            # Handle ability activation
            if "ability_dash" in keys and player and not player.is_dead():
                player.use_ability("dash", arena)
            
            arena.handle_key_event(keys)
        
        arena.step()
        
        pygame.display.flip()
        clock.tick(60)  # 60 FPS

    pygame.quit()
    sys.exit()




