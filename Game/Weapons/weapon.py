class Weapon:
    def __init__(self, name: str, ammo_per_shot: int = 1, projectile_speed: float = 16.0, floor_rect_size=(18, 8), floor_color=(210, 230, 255)):
        self.name = name
        self.ammo_per_shot = int(ammo_per_shot)
        self.projectile_speed = float(projectile_speed)
        # Visuals when on the floor
        self.floor_rect_size = tuple(floor_rect_size)
        self.floor_color = tuple(floor_color)

    def can_fire(self, ammo_available: int) -> bool:
        return ammo_available >= self.ammo_per_shot

    def consume_ammo(self, ammo_available: int) -> int:
        if self.can_fire(ammo_available):
            return ammo_available - self.ammo_per_shot
        return ammo_available



