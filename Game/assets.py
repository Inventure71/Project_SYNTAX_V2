import os
import pygame


_CACHE = {}


def _assets_dir():
    return os.path.join(os.path.dirname(__file__), "Assets")


def load_image(name: str, scale: tuple | None = None) -> pygame.Surface:
    key = (name, scale)
    if key in _CACHE:
        return _CACHE[key]

    path = os.path.join(_assets_dir(), name)

    # Try to load the requested image
    try:
        surf = pygame.image.load(path).convert_alpha()
    except (pygame.error, FileNotFoundError):
        # Fallback to placeholder image if requested image doesn't exist
        placeholder_path = os.path.join(_assets_dir(), "placeholder.png")
        try:
            surf = pygame.image.load(placeholder_path).convert_alpha()
        except (pygame.error, FileNotFoundError):
            # If even placeholder doesn't exist, create a simple colored surface
            surf = pygame.Surface((32, 32))
            surf.fill((128, 128, 128))  # Gray placeholder

    if scale is not None:
        surf = pygame.transform.smoothscale(surf, (int(scale[0]), int(scale[1])))

    _CACHE[key] = surf
    return surf


