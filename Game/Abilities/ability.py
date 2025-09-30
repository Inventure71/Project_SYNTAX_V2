"""
Base Ability System for SYNTAX V2 Battle Royale

This module provides the foundation for creating custom abilities that can be:
- Attached to characters (Cows)
- Triggered by user input or game events
- Extended by the coding agent to create new abilities

Design Principles:
- Single Responsibility: Each ability does one thing well
- Open/Closed: Easy to extend with new abilities without modifying base class
- Dependency Inversion: Abilities depend on abstractions (character interface)
"""

import pygame
from abc import ABC, abstractmethod


class Ability(ABC):
    """
    Abstract base class for all abilities in the game.
    
    An ability is a special action that a character can perform with a cooldown.
    Examples: Dash, Shield, Speed Boost, Heal, etc.
    """
    
    def __init__(self, name: str, cooldown_ms: int, duration_ms: int = 0, 
                 energy_cost: int = 0):
        """
        Initialize a new ability.
        
        Args:
            name: Display name of the ability
            cooldown_ms: Cooldown time in milliseconds
            duration_ms: How long the ability effect lasts (0 for instant)
            energy_cost: Stamina/energy cost to use the ability
        """
        self.name = name
        self.cooldown_ms = cooldown_ms
        self.duration_ms = duration_ms
        self.energy_cost = energy_cost
        
        self._last_used_ms = 0
        self._active_until_ms = 0
        self._character = None  # Reference to the character using this ability
    
    def set_character(self, character):
        """Bind this ability to a character."""
        self._character = character
    
    def can_use(self) -> bool:
        """
        Check if the ability can be used right now.
        
        Returns:
            True if the ability is off cooldown and character has enough energy
        """
        if self._character is None:
            return False
        
        now = pygame.time.get_ticks()
        if now - self._last_used_ms < self.cooldown_ms:
            return False
        
        # Check if character has enough stamina/energy
        if hasattr(self._character, 'stamina'):
            if self._character.stamina < self.energy_cost:
                return False
        
        # Check if character is alive
        if hasattr(self._character, 'is_dead') and self._character.is_dead():
            return False
        
        return True
    
    def use(self, arena=None, **kwargs) -> bool:
        """
        Attempt to use the ability.
        
        Args:
            arena: Reference to the game arena (for spawning objects, etc.)
            **kwargs: Additional context-specific parameters
            
        Returns:
            True if the ability was successfully used, False otherwise
        """
        if not self.can_use():
            return False
        
        # Consume energy if applicable
        if hasattr(self._character, 'stamina'):
            self._character.stamina = max(0, self._character.stamina - self.energy_cost)
        
        now = pygame.time.get_ticks()
        self._last_used_ms = now
        self._active_until_ms = now + self.duration_ms
        
        # Call the implementation-specific activation
        self._activate(arena, **kwargs)
        return True
    
    @abstractmethod
    def _activate(self, arena, **kwargs):
        """
        Implementation-specific activation logic.
        Override this in subclasses to define what the ability does.
        
        Args:
            arena: The game arena
            **kwargs: Additional parameters
        """
        pass
    
    def update(self, arena=None):
        """
        Called every frame to update ability state.
        Override this for abilities with ongoing effects.
        
        Args:
            arena: The game arena
        """
        pass
    
    def is_active(self) -> bool:
        """Check if the ability is currently active (for duration-based abilities)."""
        if self.duration_ms == 0:
            return False
        now = pygame.time.get_ticks()
        return now < self._active_until_ms
    
    def get_cooldown_remaining(self) -> int:
        """Get remaining cooldown time in milliseconds."""
        now = pygame.time.get_ticks()
        remaining = self.cooldown_ms - (now - self._last_used_ms)
        return max(0, remaining)
    
    def get_cooldown_percentage(self) -> float:
        """Get cooldown progress as a percentage (0.0 to 1.0)."""
        if self.cooldown_ms == 0:
            return 1.0
        remaining = self.get_cooldown_remaining()
        return 1.0 - (remaining / self.cooldown_ms)


class AbilityManager:
    """
    Manages multiple abilities for a character.
    
    Handles ability registration, updates, and provides a unified interface
    for using abilities.
    """
    
    def __init__(self, character):
        """
        Initialize the ability manager.
        
        Args:
            character: The character that owns these abilities
        """
        self.character = character
        self.abilities = {}  # key: ability_id, value: Ability instance
    
    def add_ability(self, ability_id: str, ability: Ability):
        """
        Register a new ability.
        
        Args:
            ability_id: Unique identifier for this ability (e.g., "dash", "shield")
            ability: The ability instance
        """
        ability.set_character(self.character)
        self.abilities[ability_id] = ability
    
    def remove_ability(self, ability_id: str):
        """Remove an ability."""
        if ability_id in self.abilities:
            del self.abilities[ability_id]
    
    def get_ability(self, ability_id: str) -> Ability:
        """Get an ability by ID."""
        return self.abilities.get(ability_id)
    
    def use_ability(self, ability_id: str, arena=None, **kwargs) -> bool:
        """
        Use an ability by ID.
        
        Args:
            ability_id: The ability to use
            arena: Game arena reference
            **kwargs: Additional parameters
            
        Returns:
            True if ability was used successfully
        """
        ability = self.abilities.get(ability_id)
        if ability is None:
            return False
        return ability.use(arena, **kwargs)
    
    def update_all(self, arena=None):
        """Update all abilities (called every frame)."""
        for ability in self.abilities.values():
            ability.update(arena)
    
    def get_all_abilities(self) -> dict:
        """Get all registered abilities."""
        return self.abilities.copy()
