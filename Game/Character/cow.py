import pygame
import random
import math
from pygame import Vector2
from Game.constants import FONT, YELLOW, ZOOM_STEP, ZOOM_MAX
from Game.layers import LAYER_GROUND
from Game.assets import load_image

class Cow:
    def __init__(self, rect, username, starting_position, base_health: int = 100, base_stamina: int = 100, camera_display_size: int = (0,0), world_display_size: int = (0,0), color=YELLOW, renderer=None, move_step: int = 1, ammo_find_probability: float = 0.2, starting_ammo: int = 0, eating_slowdown_pct: float = 0.4):

        # Visual
        self.rect = pygame.Rect(rect)
        self.font = FONT
        self.color = color

        # Camera
        self.camera_size = camera_display_size
        self.world_size = world_display_size
        self.zoom = 4
        self.zoom_step = ZOOM_STEP
        self.max_zoom = ZOOM_MAX
        self.min_zoom = self._compute_min_zoom()
        self.zoom = max(self.min_zoom, min(self.max_zoom, float(self.zoom)))

        # Setup
        self.username = username

        # Health
        self.max_health = int(base_health)
        self.health = int(base_health)
        self.stamina = base_stamina
        
        # Inventory
        self.ammo = int(starting_ammo)
        self.ammo_find_probability = float(ammo_find_probability)
        
        # Movement
        self.position = Vector2(starting_position)
        self.rotation = 0 
        self.layer_height = 0 # this would be the height from the ground, for example walking is 0 while flying is 1
        self.move_step = move_step
        self.base_move_step = move_step
        self.eating_slowdown_pct = float(eating_slowdown_pct)
        self._is_eating = False
        # Size scaling
        self.size_scale = 1.0
        self.min_scale = 0.6
        self.max_scale = 1.8
        self.scale_health_factor = 0.5   # extra max HP per +1 scale
        self.scale_speed_factor = 0.5    # speed multiplier decrease per +1 scale (applied inversely)
        self.base_rect_size = (self.rect.width, self.rect.height)

        # Eating/Pooping cooldowns and tuning
        self.eat_growth_percent = 0.05
        self.poop_percent = 0.15
        self.eat_cooldown_ms = 500
        self.poop_cooldown_ms = 500
        self._last_eat_ms = 0
        self._last_poop_ms = 0

        # Rendering (pluggable)
        self.renderer = renderer if renderer is not None else self._default_renderer
        
        # Layer the cow currently occupies
        self.layer = LAYER_GROUND

        # Visuals
        self.cow_sprite = None
        try:
            self.cow_sprite = load_image("cow.png", (self.rect.width, self.rect.height))
        except Exception:
            self.cow_sprite = None
        self.dead_sprite = None
        try:
            self.dead_sprite = load_image("dead_cow.png", (self.rect.width, self.rect.height))
        except Exception:
            self.dead_sprite = None

        # Aiming
        self.aim_direction = Vector2(1, 0)

    def create_camera_surface(self):
        cam_w = int(self.camera_size[0] / self.zoom)
        cam_h = int(self.camera_size[1] / self.zoom)
        left = int(self.position[0] - cam_w // 2)
        top  = int(self.position[1] - cam_h // 2)
        # clamp to world bounds
        left = max(0, min(self.world_size[0] - cam_w, left))
        top  = max(0, min(self.world_size[1] - cam_h, top))
        return pygame.Rect(left, top, cam_w, cam_h)

    def handle_collisions(self):
        pass

    def handle_event(self, event):
        if self.is_dead():
            return
        if event.type == pygame.MOUSEWHEEL:
            if event.y > 0:
                self.adjust_zoom(+self.zoom_step)
            elif event.y < 0:
                self.adjust_zoom(-self.zoom_step)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:
                self.adjust_zoom(+self.zoom_step)
            elif event.button == 5:
                self.adjust_zoom(-self.zoom_step)
    
    def handle_key_event(self, key_list):
        if self.is_dead():
            return
        for key in key_list:
            if key == "up":
                self.move_up()
            elif key == "down":
                self.move_down()
            elif key == "left":
                self.move_left()
            elif key == "right":
                self.move_right()
            elif key == "zoom_in":
                self.adjust_zoom(+self.zoom_step)
            elif key == "zoom_out":
                self.adjust_zoom(-self.zoom_step)

    # ----- Movement API -----
    def move_up(self):
        self.position.y -= self._current_move_step()

    def move_down(self):
        self.position.y += self._current_move_step()

    def move_left(self):
        self.position.x -= self._current_move_step()

    def move_right(self):
        self.position.x += self._current_move_step()

    def move_in_direction(self, direction):
        """
        Moves the cow in the direction of the key pressed.
        The direction is a string, and can be "right", "left", "up", or "down".
        """
        if direction == "right":
            self.move_right()
        elif direction == "left":
            self.move_left()
        elif direction == "up":
            self.move_up()
        elif direction == "down":
            self.move_down()

    # ----- Update/Render -----
    def update(self):
        self.handle_collisions()

    def draw(self, world_screen):
        self.rect.center = self.position
        self.renderer(world_screen)
        # Draw weapon overlay if equipped
        if self.has_weapon():
            weapon = self.get_weapon()
            sprite = None
            if hasattr(weapon, "get_floor_sprite"):
                sprite = weapon.get_floor_sprite()
            if sprite is not None:
                # Compute rotation towards aim direction
                dir_vec = Vector2(self.aim_direction)
                if dir_vec.length() == 0:
                    dir_vec = Vector2(1, 0)
                angle = -math.degrees(math.atan2(dir_vec.y, dir_vec.x))
                rotated = pygame.transform.rotate(sprite, angle)
                rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
                world_screen.blit(rotated, rect)

    def _default_renderer(self, world_screen):
        if self.is_dead() and self.dead_sprite is not None:
            rect = self.dead_sprite.get_rect(center=self.rect.center)
            world_screen.blit(self.dead_sprite, rect)
        elif self.cow_sprite is not None:
            rect = self.cow_sprite.get_rect(center=self.rect.center)
            world_screen.blit(self.cow_sprite, rect)
        else:
            pygame.draw.rect(world_screen, self.color, self.rect)

    def set_renderer(self, renderer):
        """Swap the rendering function. Signature: func(surface) -> None"""
        self.renderer = renderer if renderer is not None else self._default_renderer

    # ----- Zoom helpers -----
    def _compute_min_zoom(self):
        cw, ch = self.camera_size
        ww, wh = self.world_size
        if cw <= 0 or ch <= 0 or ww <= 0 or wh <= 0:
            return 0.25
        return max(cw / ww, ch / wh, 0.25)

    def adjust_zoom(self, delta):
        new_zoom = float(self.zoom) + float(delta)
        self.zoom = max(self.min_zoom, min(self.max_zoom, new_zoom))

    # ----- Gameplay actions -----
    def find_ammo(self) -> bool:
        """
        Attempts to find ammo using the configured probability.
        Returns True if ammo was found (and incremented), False otherwise.
        """
        if self.is_dead():
            return False
        if random.random() < self.ammo_find_probability:
            self.ammo += 1
            return True
        return False

    def eat(self) -> bool:
        """
        Eat action, only called when the cow is inside a grass field.
        May find ammo based on probability. Returns True if ammo found.
        """
        if self.is_dead():
            return False
        now = pygame.time.get_ticks()
        if now - self._last_eat_ms < self.eat_cooldown_ms:
            return False
        self._last_eat_ms = now
        grew = self._grow_on_eat()
        ammo_found = self.find_ammo()
        return ammo_found or grew

    def get_world_rect(self) -> pygame.Rect:
        r = self.rect.copy()
        r.center = (int(self.position.x), int(self.position.y))
        return r

    # ----- Speed modifiers -----
    def _current_move_step(self) -> float:
        if self.is_dead():
            return 0.0
        step = float(self.base_move_step)
        # apply scale effect (bigger -> slower)
        step *= max(0.1, 1.0 - (self.size_scale - 1.0) * self.scale_speed_factor)
        if self._is_eating:
            step = step * max(0.0, 1.0 - self.eating_slowdown_pct)
        return step

    # ----- Weapon API -----
    def equip_weapon(self, weapon):
        self.weapon = weapon

    def has_weapon(self) -> bool:
        return getattr(self, "weapon", None) is not None

    def get_weapon(self):
        return getattr(self, "weapon", None)

    def _try_shoot(self):
        if self.is_dead():
            return False
        weapon = self.get_weapon()
        if weapon is None:
            return False
        if not weapon.can_fire(self.ammo):
            return False
        # consume ammo
        self.ammo = weapon.consume_ammo(self.ammo)
        # No projectile logic yet; modular hook here
        return True

    def set_eating_intent(self, active: bool):
        if self.is_dead():
            self._is_eating = False
        else:
            self._is_eating = bool(active)

    def set_aim_direction(self, direction: Vector2):
        if self.is_dead():
            return
        try:
            vec = Vector2(direction)
        except Exception:
            vec = Vector2(1, 0)
        self.aim_direction = vec

    # ----- Size scaling mechanics -----
    def _apply_scale_to_rect(self):
        base_w, base_h = self.base_rect_size
        cx, cy = self.rect.center
        new_w = max(6, int(base_w * self.size_scale))
        new_h = max(6, int(base_h * self.size_scale))
        self.rect.size = (new_w, new_h)
        self.rect.center = (int(cx), int(cy))
        # Rescale sprites if available
        try:
            self.cow_sprite = load_image("cow.png", (self.rect.width, self.rect.height))
        except Exception:
            pass
        try:
            self.dead_sprite = load_image("dead_cow.png", (self.rect.width, self.rect.height))
        except Exception:
            pass

    def _grow_on_eat(self) -> bool:
        old_scale = self.size_scale
        self.size_scale = min(self.max_scale, self.size_scale * (1.0 + self.eat_growth_percent))
        if self.size_scale != old_scale:
            # Increase max health; keep current health ratio
            old_max = self.max_health
            new_max = int(max(1, old_max * (1.0 + self.eat_growth_percent * self.scale_health_factor)))
            ratio = 0 if old_max == 0 else self.health / old_max
            self.max_health = new_max
            self.health = max(1, int(self.max_health * ratio))
            self._apply_scale_to_rect()
            return True
        return False

    def poop(self) -> bool:
        if self.is_dead():
            return False
        now = pygame.time.get_ticks()
        if now - self._last_poop_ms < self.poop_cooldown_ms:
            return False
        self._last_poop_ms = now
        old_scale = self.size_scale
        self.size_scale = max(self.min_scale, self.size_scale * (1.0 - self.poop_percent))
        if self.size_scale != old_scale:
            old_max = self.max_health
            new_max = int(max(1, old_max * (1.0 - self.poop_percent * self.scale_health_factor)))
            ratio = 0 if old_max == 0 else self.health / old_max
            self.max_health = max(1, new_max)
            self.health = max(1, int(self.max_health * ratio))
            self._apply_scale_to_rect()
            return True
        return False

    # ----- Health API -----
    def take_damage(self, amount: float):
        new_hp = max(0, int(self.health - float(amount)))
        self.health = new_hp

    def heal(self, amount: float):
        new_hp = min(self.max_health, int(self.health + float(amount)))
        self.health = new_hp

    def set_health(self, value: float):
        self.health = max(0, min(self.max_health, int(value)))

    def is_dead(self) -> bool:
        return self.health <= 0
