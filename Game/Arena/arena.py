import pygame
import random
from Game.constants import GREEN, WHITE, FONT, BORDER
from Game.Objects.grass import GrassField
from Game.Objects.obstacle import Obstacle
from Game.Objects.golden_field import GoldenField
from Game.Weapons import Weapon
from Game.Objects import Projectile
from Game.Objects import WeaponPickup
from Game.layers import LAYER_GROUND

class Arena:
    def __init__(self, screen_dimensions, world_screen_dimensions, screen, world_screen, text):
        # Config variables
        self.grid = True # if should display grid for debugging
        
        self.screen = screen
        self.rect = pygame.Rect(screen_dimensions)


        self.world_screen = world_screen
        self.world_dimensions = world_screen_dimensions # (WORLD_W, WORLD_H)


        self.text = text
        self.font = FONT
        self.hover = False
        self.characters = []
        self.objects = []
        self.grass_fields = []
        self.golden_fields = []
        self.obstacles = []
        self.projectiles = []

        # Generate some world content
        self._generate_world()


    def add_new_character(self, character):
        self.characters.append(character)

    def add_new_object(self, object):
        self.objects.append(object)

    def add_grass_field(self, grass: GrassField):
        self.grass_fields.append(grass)

    def add_obstacle(self, obstacle: Obstacle):
        self.obstacles.append(obstacle)

    def add_golden_field(self, field: GoldenField):
        self.golden_fields.append(field)

    def step(self):
        self.update()
        self.draw()
        self.render_cameras_per_player(0)
        #self.handle_event(event)

    def update(self):
        for character in self.characters:
            if hasattr(character, "update"):
                character.update()
        for object in self.objects:
            if hasattr(object, "update"):
                object.update()
        for grass in self.grass_fields:
            if hasattr(grass, "update"):
                grass.update()
        for gfield in self.golden_fields:
            if hasattr(gfield, "update"):
                gfield.update()
        for obstacle in self.obstacles:
            if hasattr(obstacle, "update"):
                obstacle.update()
        for proj in self.projectiles:
            proj.update()
            # Collide projectiles with obstacles by layer
            if getattr(proj, 'alive', True):
                prect = pygame.Rect(int(proj.position.x) - 2, int(proj.position.y) - 2, 4, 4)
                for obstacle in self.obstacles:
                    if not obstacle.blocks_layer(getattr(proj, 'layer', 0)):
                        continue
                    if prect.colliderect(obstacle.rect):
                        proj.alive = False
                        break
        # prune dead projectiles
        self.projectiles = [p for p in self.projectiles if getattr(p, "alive", True)]

        # Enforce collisions and bounds after movement
        for character in self.characters:
            self._clamp_character_to_world(character)
            self._resolve_character_obstacle_collisions(character)
            # Final clamp to ensure still within bounds after push-out
            self._clamp_character_to_world(character)

        # Player pickup collision: auto-equip if none
        for character in self.characters:
            if hasattr(character, 'has_weapon') and character.has_weapon():
                continue
            if not hasattr(character, 'get_world_rect'):
                continue
            char_rect = character.get_world_rect()
            for obj in self.objects:
                if isinstance(obj, WeaponPickup) and getattr(obj, 'alive', True):
                    if char_rect.colliderect(obj.rect):
                        character.equip_weapon(obj.weapon)
                        obj.alive = False
        # Cleanup consumed pickups
        self.objects = [o for o in self.objects if getattr(o, 'alive', True)]

    def draw(self):
        self.world_screen.fill(GREEN)

        if self.grid:
            pygame.draw.rect(self.world_screen, BORDER, (0,0,self.world_dimensions[0],self.world_dimensions[1]), 8, border_radius=24)

            step = 120
            for x in range(step, self.world_dimensions[0], step):
                pygame.draw.line(self.world_screen, (38, 42, 52), (x, 0), (x, self.world_dimensions[1]), 1)
            for y in range(step, self.world_dimensions[1], step):
                pygame.draw.line(self.world_screen, (38, 42, 52), (0, y), (self.world_dimensions[0], y), 1)

        # Draw environment
        for grass in self.grass_fields:
            grass.draw(self.world_screen)
        for gfield in self.golden_fields:
            gfield.draw(self.world_screen)
        for obstacle in self.obstacles:
            obstacle.draw(self.world_screen)

        #pygame.draw.rect(screen, WHITE, self.rect, border_radius=10)
        for character in self.characters:
            character.draw(self.world_screen)
        for object in self.objects:
            object.draw(self.world_screen)
        for proj in self.projectiles:
            proj.draw(self.world_screen)

    def render_cameras_per_player(self, index):
        camera_rect = self.characters[index].create_camera_surface()
        view = self.world_screen.subsurface(camera_rect)
        view_scaled = pygame.transform.smoothscale(view, (self.rect.width, self.rect.height))
        self.screen.blit(view_scaled, (0, 0))
        
    def draw_ui(self):
        # Basic HUD with ammo count for the first character
        if self.font is None:
            self.font = pygame.font.SysFont(None, 22)
        if len(self.characters) == 0:
            return
        player = self.characters[0]
        ammo = getattr(player, "ammo", None)
        weapon = getattr(player, "weapon", None)
        if ammo is None:
            ammo = 0
        weapon_name = weapon.name if weapon is not None else "None"
        text_surf = self.font.render(f"Ammo: {ammo} | Weapon: {weapon_name}", True, WHITE)
        self.screen.blit(text_surf, (12, 10))
    
    def handle_key_event(self, key_list):
        # First, set eating intent based on current key state and context
        eating_pressed = ("eat" in key_list)
        for character in self.characters:
            # Default no eating intent
            character.set_eating_intent(False) if hasattr(character, "set_eating_intent") else None
            # Compute character's world rect at current position
            if hasattr(character, "rect") and hasattr(character, "position"):
                char_rect = character.rect.copy()
                char_rect.center = (int(character.position.x), int(character.position.y))
            else:
                char_rect = getattr(character, "rect", None)
            if char_rect is None:
                continue
            in_grass = any(char_rect.colliderect(g.rect) for g in self.grass_fields)
            in_golden = any(char_rect.colliderect(g.rect) for g in self.golden_fields)
            if eating_pressed and (in_grass or in_golden):
                if hasattr(character, "set_eating_intent"):
                    character.set_eating_intent(True)

        # Then, pass movement/zoom keys through
        for character in self.characters:
            character.handle_key_event(key_list)

        # Finally, if eat pressed and valid, trigger action once per frame
        if eating_pressed:
            for character in self.characters:
                if hasattr(character, "rect") and hasattr(character, "position"):
                    char_rect = character.rect.copy()
                    char_rect.center = (int(character.position.x), int(character.position.y))
                else:
                    char_rect = getattr(character, "rect", None)
                if char_rect is None:
                    continue
                in_grass = any(char_rect.colliderect(g.rect) for g in self.grass_fields)
                in_golden = any(char_rect.colliderect(g.rect) for g in self.golden_fields)
                if (in_grass or in_golden):
                    # Golden fields do NOT grant ammo. Grass does.
                    if in_golden:
                        # Roll for weapon drop; spawn pickup near the golden field
                        drop_probability = 0.05
                        for gf in self.golden_fields:
                            if char_rect.colliderect(gf.rect):
                                drop_probability = gf.drop_probability
                                # spawn pickup with small offset so it is visible
                                import random
                                if random.random() < drop_probability:
                                    gx, gy = gf.rect.center
                                    offset = random.randint(-20, 20)
                                    pickup = WeaponPickup(Weapon(name="Pea Shooter", ammo_per_shot=1), (gx + offset, gy))
                                    self.objects.append(pickup)
                                break
                    else:
                        if hasattr(character, "eat"):
                            character.eat()

    def handle_event(self, event):
        # Handle shooting in arena to correctly map screen->world coords
        if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, 'button', None) == 1:
            if len(self.characters) > 0:
                player = self.characters[0]
                if hasattr(player, 'has_weapon') and player.has_weapon():
                    weapon = player.get_weapon()
                    if weapon is not None and weapon.can_fire(getattr(player, 'ammo', 0)):
                        # Map screen coords to world coords
                        cam_rect = self.characters[0].create_camera_surface()
                        scale_x = self.rect.width / cam_rect.width
                        scale_y = self.rect.height / cam_rect.height
                        sx, sy = event.pos
                        world_x = cam_rect.left + (sx / scale_x)
                        world_y = cam_rect.top + (sy / scale_y)
                        start = (int(player.position.x), int(player.position.y))
                        direction = (world_x - start[0], world_y - start[1])
                        speed = getattr(weapon, 'projectile_speed', 16.0)
                        self.spawn_projectile(start, direction, speed)
                        # consume ammo
                        player.ammo = weapon.consume_ammo(player.ammo)
        # Forward event to children
        for character in self.characters:
            character.handle_event(event)
        for object in self.objects:
            object.handle_event(event)

    # ------- Helpers -------
    def _generate_world(self, num_grass: int = 10, num_obstacles: int = 14, num_golden: int = 3):
        # Randomly scatter grass fields and obstacles throughout the world
        world_w, world_h = self.world_dimensions
        rng = random.Random(42)

        for _ in range(num_grass):
            w = rng.randint(160, 320)
            h = rng.randint(120, 260)
            x = rng.randint(0, max(0, world_w - w))
            y = rng.randint(0, max(0, world_h - h))
            self.add_grass_field(GrassField((x, y, w, h)))

        for _ in range(num_golden):
            w = rng.randint(140, 240)
            h = rng.randint(100, 200)
            x = rng.randint(0, max(0, world_w - w))
            y = rng.randint(0, max(0, world_h - h))
            p = rng.uniform(0.01, 0.06)
            self.add_golden_field(GoldenField((x, y, w, h), drop_probability=p))

        for _ in range(num_obstacles):
            w = rng.randint(40, 140)
            h = rng.randint(40, 140)
            x = rng.randint(0, max(0, world_w - w))
            y = rng.randint(0, max(0, world_h - h))
            health = rng.randint(5000, 200000)
            # Randomize blocking masks: some block only ground, some all, etc.
            mask_choice = rng.choice([
                # ground only
                (1 << 1),
                # ground + midair
                (1 << 1) | (1 << 2),
                # all layers
                (1 << 0) | (1 << 1) | (1 << 2) | (1 << 3),
            ])
            self.add_obstacle(Obstacle((x, y, w, h), base_health=health, blocking_mask=mask_choice))

    def spawn_projectile(self, start_pos, direction, speed: float = 16.0):
        proj = Projectile(start_pos, direction, speed=speed)
        self.projectiles.append(proj)

    def _clamp_character_to_world(self, character):
        if not hasattr(character, "get_world_rect"):
            return
        char_rect = character.get_world_rect()
        world_rect = pygame.Rect(0, 0, self.world_dimensions[0], self.world_dimensions[1])
        # Clamp in place
        char_rect.clamp_ip(world_rect)
        # Write back to character position
        if hasattr(character, "position"):
            character.position.x = char_rect.centerx
            character.position.y = char_rect.centery

    def _resolve_character_obstacle_collisions(self, character):
        if not hasattr(character, "get_world_rect"):
            return
        char_rect = character.get_world_rect()
        # Iterate a few times in case pushing causes new overlaps
        for _ in range(3):
            collided = False
            for obstacle in self.obstacles:
                # Only block if obstacle blocks the character's current layer
                layer = getattr(character, 'layer', LAYER_GROUND)
                if not obstacle.blocks_layer(layer):
                    continue
                orect = obstacle.rect
                if not char_rect.colliderect(orect):
                    continue
                collided = True
                # Compute minimal translation vector to separate AABB
                overlap_left = char_rect.right - orect.left
                overlap_right = orect.right - char_rect.left
                overlap_top = char_rect.bottom - orect.top
                overlap_bottom = orect.bottom - char_rect.top

                # Choose the smallest push
                pushes = [
                    (abs(overlap_left), (-overlap_left, 0)),     # push left
                    (abs(overlap_right), (overlap_right, 0)),    # push right
                    (abs(overlap_top), (0, -overlap_top)),       # push up
                    (abs(overlap_bottom), (0, overlap_bottom)),  # push down
                ]
                _, (dx, dy) = min(pushes, key=lambda p: p[0])
                char_rect.move_ip(dx, dy)
            if not collided:
                break
        # Write back to character position
        if hasattr(character, "position"):
            character.position.x = char_rect.centerx
            character.position.y = char_rect.centery

    def step(self):
        self.update()
        self.draw()
        self.render_cameras_per_player(0)
        self.draw_ui()