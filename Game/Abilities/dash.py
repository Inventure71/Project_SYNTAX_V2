"""
Dash Ability - Example implementation

Allows the character to quickly dash in their current aim direction.
"""

from pygame import Vector2
from Game.Abilities.ability import Ability


class DashAbility(Ability):
    """
    Dash ability that propels the character forward in their aim direction.
    """
    
    def __init__(self, dash_distance: float = 150.0, cooldown_ms: int = 3000, 
                 energy_cost: int = 20):
        """
        Initialize the dash ability.
        
        Args:
            dash_distance: How far to dash in pixels
            cooldown_ms: Cooldown time in milliseconds
            energy_cost: Stamina cost to use
        """
        super().__init__(
            name="Dash",
            cooldown_ms=cooldown_ms,
            duration_ms=0,  # Instant effect
            energy_cost=energy_cost
        )
        self.dash_distance = dash_distance
    
    def _activate(self, arena, **kwargs):
        """
        Execute the dash movement.
        
        Args:
            arena: Game arena (for bounds checking)
            **kwargs: Not used
        """
        if self._character is None:
            return
        
        # Get the character's aim direction
        aim_dir = getattr(self._character, 'aim_direction', Vector2(1, 0))
        
        # Normalize and scale by dash distance
        if aim_dir.length() > 0:
            dash_vector = aim_dir.normalize() * self.dash_distance
        else:
            # Default to right if no aim direction
            dash_vector = Vector2(self.dash_distance, 0)
        
        # Apply the dash to character position
        if hasattr(self._character, 'position'):
            self._character.position += dash_vector
            
            # Clamp to world bounds if arena is available
            if arena is not None and hasattr(arena, 'world_dimensions'):
                world_w, world_h = arena.world_dimensions
                # Keep character within bounds (with some margin for character size)
                margin = getattr(self._character, 'rect', None)
                if margin:
                    margin = max(margin.width, margin.height) // 2
                else:
                    margin = 25
                
                self._character.position.x = max(margin, min(world_w - margin, 
                                                              self._character.position.x))
                self._character.position.y = max(margin, min(world_h - margin, 
                                                              self._character.position.y))
