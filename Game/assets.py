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
    surf = pygame.image.load(path).convert_alpha()
    if scale is not None:
        surf = pygame.transform.smoothscale(surf, (int(scale[0]), int(scale[1])))
    _CACHE[key] = surf
    return surf


