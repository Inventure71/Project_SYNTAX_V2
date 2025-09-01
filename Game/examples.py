import pygame
from pygame.math import Vector2

# --------- Config ---------
SCREEN_W, SCREEN_H = 900, 600
WORLD_W, WORLD_H = 2400, 1800
BG_COLOR = (25, 28, 35)
WHITE = (240, 240, 240)
GREEN = (80, 200, 120)
RED = (220, 80, 90)
YELLOW = (245, 210, 85)
CYAN = (80, 200, 220)
BORDER = (70, 74, 86)
UI_DARK = (50, 54, 64)
UI_DARK_2 = (70, 76, 90)
UI_STROKE = (90, 96, 110)

PLAYER_SPEED = 280.0         # world px / second
BULLET_SPEED = 520.0
ENEMY_SPEED  = 120.0

ZOOM = 1.3  # >1.0 means zoomed-in (see less of the world)

COLLISION_EVENT = pygame.USEREVENT + 1

# --------- Helpers: Camera / Space transforms ---------
def make_camera_rect(center_pos):
    cam_w = int(SCREEN_W / ZOOM)
    cam_h = int(SCREEN_H / ZOOM)
    left = int(center_pos.x - cam_w // 2)
    top  = int(center_pos.y - cam_h // 2)
    # clamp to world bounds
    left = max(0, min(WORLD_W - cam_w, left))
    top  = max(0, min(WORLD_H - cam_h, top))
    return pygame.Rect(left, top, cam_w, cam_h)

def screen_to_world(screen_pos, camera_rect):
    """Convert a point on the screen to world coordinates, based on camera_rect and zoom."""
    sx, sy = screen_pos
    wx = camera_rect.left + (sx / SCREEN_W) * camera_rect.width
    wy = camera_rect.top  + (sy / SCREEN_H) * camera_rect.height
    return Vector2(wx, wy)

def clamp_point_to_world(p, radius=0):
    p.x = max(radius, min(WORLD_W - radius, p.x))
    p.y = max(radius, min(WORLD_H - radius, p.y))
    return p

# --------- UI Button ---------
class Button:
    def __init__(self, rect, text, font):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.hover = False

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
                return True
        return False

# --------- Sprites (world space) ---------
class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.radius = 18
        self.base_img = pygame.Surface((self.radius*2, self.radius*2), pygame.SRCALPHA)
        pygame.draw.circle(self.base_img, GREEN, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.base_img, (0,0,0,50), (self.radius, self.radius), self.radius, width=2)
        self.image = self.base_img.copy()
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)

    def update(self, keys, dt):
        d = Vector2(
            (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT]),
            (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP]),
        )
        if d.length_squared() > 0:
            d = d.normalize()
        self.pos += d * PLAYER_SPEED * dt
        clamp_point_to_world(self.pos, self.radius)
        self.rect.center = self.pos

class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, velocity):
        super().__init__()
        size = 34
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(self.image, RED, (0,0,size,size), border_radius=6)
        pygame.draw.rect(self.image, (0,0,0,50), (0,0,size,size), width=2, border_radius=6)
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.vel = Vector2(velocity)

    def update(self, dt):
        self.pos += self.vel * dt
        # bounce at world bounds
        if self.pos.x < 17 or self.pos.x > WORLD_W - 17:
            self.vel.x *= -1
        if self.pos.y < 17 or self.pos.y > WORLD_H - 17:
            self.vel.y *= -1
        clamp_point_to_world(self.pos, 17)
        self.rect.center = self.pos

class Bullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction):
        super().__init__()
        self.image = pygame.Surface((10,10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (5,5), 5)
        self.rect = self.image.get_rect(center=pos)
        self.pos = Vector2(pos)
        self.vel = direction.normalize() * BULLET_SPEED if direction.length_squared() else Vector2()

    def update(self, dt):
        self.pos += self.vel * dt
        self.rect.center = self.pos
        # kill if outside world
        if not (0 <= self.pos.x <= WORLD_W and 0 <= self.pos.y <= WORLD_H):
            self.kill()

# --------- World helpers ---------
def spawn_enemy(enemies, all_sprites, at=None):
    import random
    if at is None:
        at = (random.randint(80, WORLD_W-80), random.randint(80, WORLD_H-80))
    vel = Vector2(ENEMY_SPEED, 0).rotate(random.uniform(0, 360))
    e = Enemy(at, vel)
    enemies.add(e)
    all_sprites.add(e)
    return e

def draw_crosshair_world(surf, world_pos, size=8):
    x, y = int(world_pos.x), int(world_pos.y)
    pygame.draw.line(surf, CYAN, (x-size, y), (x+size, y), 2)
    pygame.draw.line(surf, CYAN, (x, y-size), (x, y+size), 2)

# --------- Main ---------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Pygame: Large World + Camera Follow + Zoom")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 22)
    bigfont = pygame.font.SysFont(None, 28)

    # Offscreen world surface
    world_surf = pygame.Surface((WORLD_W, WORLD_H)).convert_alpha()

    # Sprites
    player = Player((WORLD_W * 0.5, WORLD_H * 0.5))
    all_sprites = pygame.sprite.Group(player)
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    spawn_enemy(enemies, all_sprites)

    # UI
    button = Button(rect=(16, 14, 170, 42), text="Spawn Enemy", font=bigfont)

    # State
    last_world_click = None
    last_event_msg = "Move with WASD/Arrows. Left-click to shoot."
    running = True

    while running:
        dt = clock.tick(120) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Button first (screen space)
            if button.handle_event(event):
                spawn_enemy(enemies, all_sprites)
                last_event_msg = "Spawned an enemy."

            # Mouse (convert to world if not clicking UI)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if not button.rect.collidepoint(event.pos):
                    # Convert screen click to world coords based on current camera
                    # (we need the camera of THIS frame; compute it from current player position)
                    camera_rect = make_camera_rect(player.pos)
                    world_click = screen_to_world(event.pos, camera_rect)
                    last_world_click = world_click
                    print(f"World click at: {int(world_click.x)}, {int(world_click.y)}")
                    # Fire a bullet from player toward world click
                    direction = world_click - player.pos
                    b = Bullet(player.pos, direction)
                    bullets.add(b)
                    all_sprites.add(b)

            if event.type == COLLISION_EVENT:
                what = event.dict.get("what", "unknown")
                pos = event.dict.get("pos", None)
                if what == "bullet_enemy":
                    last_event_msg = f"Hit! Bullet collided with enemy at {pos}."
                elif what == "player_enemy":
                    last_event_msg = "Ouch! Player touched an enemy."

        # Continuous input
        keys = pygame.key.get_pressed()
        player.update(keys, dt)
        enemies.update(dt)
        bullets.update(dt)

        # Collisions
        hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
        for enemy, _ in hits.items():
            pygame.event.post(pygame.event.Event(
                COLLISION_EVENT, {"what":"bullet_enemy","pos": enemy.rect.center}
            ))
            spawn_enemy(enemies, all_sprites)

        if pygame.sprite.spritecollide(player, enemies, dokill=False):
            pygame.event.post(pygame.event.Event(
                COLLISION_EVENT, {"what":"player_enemy","pos": player.rect.center}
            ))

        # ---------- DRAW TO WORLD ----------
        world_surf.fill(BG_COLOR)

        # World border & a simple grid so you feel the scale
        pygame.draw.rect(world_surf, BORDER, (0,0,WORLD_W,WORLD_H), 8, border_radius=24)
        step = 120
        for x in range(step, WORLD_W, step):
            pygame.draw.line(world_surf, (38, 42, 52), (x, 0), (x, WORLD_H), 1)
        for y in range(step, WORLD_H, step):
            pygame.draw.line(world_surf, (38, 42, 52), (0, y), (WORLD_W, y), 1)

        # Draw sprites (they already store world positions)
        all_sprites.draw(world_surf)

        # Crosshair where you last clicked (in world)
        if last_world_click:
            draw_crosshair_world(world_surf, last_world_click)

        # ---------- CAMERA: crop + scale to screen ----------
        camera_rect = make_camera_rect(player.pos)
        # Using subsurface is fine here (camera is guaranteed within world bounds)
        view = world_surf.subsurface(camera_rect)
        view_scaled = pygame.transform.smoothscale(view, (SCREEN_W, SCREEN_H))
        screen.blit(view_scaled, (0, 0))

        # ---------- UI (screen space) ----------
        button.draw(screen)

        info_lines = [
            "Move: WASD / Arrow Keys   Shoot: Left-click   Button: 'Spawn Enemy'",
            f"World: {WORLD_W}x{WORLD_H}   Zoom: {ZOOM}x   Camera view: {camera_rect.width}x{camera_rect.height}",
            f"Enemies: {len(enemies)}   Bullets: {len(bullets)}   Last: {last_event_msg}",
        ]
        y = SCREEN_H - 66
        for line in info_lines:
            txt = font.render(line, True, WHITE)
            screen.blit(txt, (16, y))
            y += 22

        if last_world_click:
            lx, ly = int(last_world_click.x), int(last_world_click.y)
            click_txt = font.render(f"Last world click: {lx}, {ly}", True, CYAN)
            screen.blit(click_txt, (SCREEN_W - 300, 20))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
