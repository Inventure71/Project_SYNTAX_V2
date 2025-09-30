"""
Rainbow Cow Bliss Ray - Custom Weapon with Effects

A device firing harmless, high-velocity euphoria beams designed to temporarily incapacitate targets by overwhelming them with sheer bliss. Deals minimal structural damage.

Effects: stun, charm
"""

from Game.Weapons.weapon import Weapon
from Game.Objects.rainbowgun_projectile import RainbowGunProjectile


def create_rainbowgun() -> Weapon:
    """
    Factory function to create a Rainbow Cow Bliss Ray.
    
    This weapon applies effects: stun, charm
    
    Returns:
        Configured Weapon instance
    """
    weapon = Weapon(
        name="Rainbow Cow Bliss Ray",
        ammo_per_shot=1,
        projectile_speed=15.0,
        damage=1.0,
        floor_image_name=None,
        floor_image_scale=(28, 28),
        projectile_image_name=None,
        projectile_image_scale=(18, 6)
    )
    
    # Store effect info for custom projectile
    weapon.effect_types = ['stun', 'charm']
    weapon.effect_details = {'stun': {'duration_ms': 4000, 'description': 'Target is incapacitated by overwhelming positive feelings, unable to move or attack.'}, 'charm': {'flavor': "A wave of harmless, euphoria-inducing light that makes targets feel 'in heaven'. Especially effective on bovine enemies.", 'visual_fx': 'Multicolored light arcs and sparkling dust.'}}
    weapon.projectile_class = RainbowGunProjectile
    
    return weapon


# Quick access instance
RAINBOWGUN = create_rainbowgun()
