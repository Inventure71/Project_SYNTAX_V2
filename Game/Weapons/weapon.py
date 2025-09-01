from Game.assets import load_image


class Weapon:
    def __init__(self, name: str, ammo_per_shot: int = 1, projectile_speed: float = 16.0, floor_rect_size=(18, 8), floor_color=(210, 230, 255), floor_image_name: str | None = None, floor_image_scale: tuple | None = None, projectile_image_name: str | None = None, projectile_image_scale: tuple | None = None):
        self.name = name
        self.ammo_per_shot = int(ammo_per_shot)
        self.projectile_speed = float(projectile_speed)
        # Visuals when on the floor
        self.floor_rect_size = tuple(floor_rect_size)
        self.floor_color = tuple(floor_color)
        self.floor_image_name = floor_image_name
        self.floor_image_scale = floor_image_scale
        self.projectile_image_name = projectile_image_name
        self.projectile_image_scale = projectile_image_scale
        self._floor_sprite = None
        self._projectile_sprite = None

    def can_fire(self, ammo_available: int) -> bool:
        return ammo_available >= self.ammo_per_shot

    def consume_ammo(self, ammo_available: int) -> int:
        if self.can_fire(ammo_available):
            return ammo_available - self.ammo_per_shot
        return ammo_available

    # Asset helpers
    def get_floor_sprite(self):
        if self.floor_image_name is None:
            return None
        if self._floor_sprite is None:
            self._floor_sprite = load_image(self.floor_image_name, self.floor_image_scale)
        return self._floor_sprite

    def get_projectile_sprite(self):
        if self.projectile_image_name is None:
            return None
        if self._projectile_sprite is None:
            self._projectile_sprite = load_image(self.projectile_image_name, self.projectile_image_scale)
        return self._projectile_sprite



