"""Layer system for gameplay height levels.

Layers are represented as bit flags so objects can specify multiple blocked levels.
"""

# Bitflags for layers
LAYER_UNDERGROUND = 1 << 0
LAYER_GROUND      = 1 << 1
LAYER_MIDAIR      = 1 << 2
LAYER_AIR         = 1 << 3

ALL_LAYERS = (LAYER_UNDERGROUND | LAYER_GROUND | LAYER_MIDAIR | LAYER_AIR)


def mask_for_layers(*layers: int) -> int:
    mask = 0
    for layer in layers:
        mask |= int(layer)
    return mask


def layer_name(layer: int) -> str:
    if layer == LAYER_UNDERGROUND:
        return "underground"
    if layer == LAYER_GROUND:
        return "ground"
    if layer == LAYER_MIDAIR:
        return "mid-air"
    if layer == LAYER_AIR:
        return "air"
    return f"unknown({layer})"




