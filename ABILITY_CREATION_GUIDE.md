# Ability Creation Workflow Guide

This document explains the complete workflow for creating new abilities using the AI agent.

## Overview

The ability creation system follows a strict workflow:

```
User Description → Plan → Implement → Verify
```

Each phase has specific responsibilities and checks to ensure abilities work correctly for ALL characters (player and AI enemies).

## The Complete Workflow

### Phase 1: User Describes the Ability

**What happens:**
- User provides natural language description of the desired ability
- Description can be simple or detailed

**Example descriptions:**
```
"Create a freeze ability that slows enemies by 50% for 3 seconds"

"I want a shield that makes me invincible for 2 seconds with cooldown of 10 seconds"

"Create a speed boost ability that doubles movement speed for 5 seconds"
```

**Best practices:**
- Specify the effect (freeze, boost, shield, etc.)
- Include duration and magnitude
- Mention cooldown if desired
- Clarify if it should affect self, others, or both

### Phase 2: Agent Plans the Implementation

**What the agent does:**
1. **Analyzes the requirement** using Gemini's thinking capability
2. **Identifies necessary components**:
   - Does it need new character states? (e.g., frozen, shielded)
   - Does it need new objects? (e.g., freeze projectile, shield bubble)
   - Does it need visual effects?
   - Which files need modification?

3. **Creates a task breakdown** (3-6 tasks typically):
   ```json
   {
     "task_1": "Add freeze_state to Cow base class",
     "task_2": "Create FreezeAbility class",
     "task_3": "Add freeze effect visual indicator",
     "task_4": "Integrate with projectile system"
   }
   ```

4. **Ensures universal applicability**:
   - ✅ Can player use on AI?
   - ✅ Can AI use on player?
   - ✅ Can AI use on other AI?

**Output:** Structured plan with tasks, files, and approach

### Phase 3: Task-by-Task Implementation

**What the agent does:**

For each task in the plan:

1. **Reads relevant files**
   - Gets current code context
   - Understands existing patterns
   - Identifies integration points

2. **Generates complete code**
   - NOT snippets - full file contents
   - Follows existing code style
   - Includes proper imports and docstrings
   - Ensures DRY and SOLID principles

3. **Writes the code**
   - Creates new files if needed
   - Overwrites modified files
   - Reports success/failure

4. **Moves to next task**
   - Each task builds on previous ones
   - State is maintained across tasks

**Example task implementation:**

```
Task 1: Add freeze state to Cow base class
Files to modify: Game/Character/cow.py

What it does:
- Adds self.is_frozen = False
- Adds self.freeze_end_time = 0
- Adds apply_freeze(duration_ms) method
- Adds update_freeze() to be called in update()
- Modifies movement to check if frozen
```

### Phase 4: Verification

**What the agent does:**

1. **Reads back all modified/created files**
2. **Checks for:**
   - Syntax correctness
   - Follows base class pattern
   - Universal applicability (works for any character)
   - DRY principles (no code duplication)
   - SOLID principles (proper abstraction)
   - Integration correctness (properly hooks into existing systems)

3. **Reports issues or success**
   - If issues found: Lists specific problems
   - If verified: Confirms implementation is complete

**Possible verification outcomes:**
- ✅ **VERIFIED**: Everything is correct and ready to use
- ⚠️ **ISSUES FOUND**: Lists problems that need fixing

## Universal Design Requirements

### Critical Rule: Abilities Must Work Bidirectionally

**WHY:** In battle royale, AI enemies must be able to use abilities too!

**Example: Freeze Ability**

❌ **WRONG** - Only works for player:
```python
class FreezeAbility(Ability):
    def _activate(self, arena, **kwargs):
        # Gets mouse cursor - only player has this!
        target = get_entity_at_mouse()  # ❌ AI can't use this
        target.freeze()
```

✅ **CORRECT** - Works for any character:
```python
class FreezeAbility(Ability):
    def _activate(self, arena, **kwargs):
        # Uses character's aim direction
        aim = self._character.aim_direction
        # Spawns freeze projectile that affects anyone it hits
        arena.spawn_freeze_projectile(
            self._character.position, 
            aim,
            owner=self._character
        )
```

### How the Agent Ensures Universality

1. **Effect States on Base Class**
   - Adds frozen, stunned, burning states to `Cow` class
   - Any character can be affected

2. **Object-Based Effects**
   - Creates effect objects (FreezeProjectile, BurnField)
   - Objects affect any character they touch

3. **Character-Agnostic Design**
   - Uses position, aim_direction (all characters have these)
   - Avoids player-specific inputs (mouse, keyboard)

## Integration Points

### Where Abilities Hook Into the Game

1. **Character.Cow**
   - `ability_manager`: Manages character's abilities
   - `add_ability(id, ability)`: Register new ability
   - `use_ability(id, arena)`: Trigger ability
   - `update(arena)`: Called every frame, updates abilities

2. **Arena**
   - Provides world context
   - Spawns objects (projectiles, effects)
   - Access to all characters for targeting
   - Access to environment (grass fields, obstacles)

3. **Input System**
   - `main.py`: Maps keys to ability IDs
   - `handle_key_event`: Processes ability activation
   - AI can trigger abilities programmatically

## Example: Complete Ability Creation

### User Request
```
"Create a dash ability that teleports the character forward 150 pixels with a 3 second cooldown"
```

### Agent's Plan
```json
{
  "ability_name": "DashAbility",
  "high_level_design": "Instant movement ability that moves character in aim direction",
  "universal_considerations": "Uses character's aim_direction, works for any character",
  "tasks": [
    {
      "task_number": 1,
      "goal": "Create DashAbility class",
      "files_to_create": ["Game/Abilities/dash.py"],
      "what_to_do": [
        "Inherit from Ability base class",
        "Implement _activate to move character",
        "Handle bounds checking with arena"
      ]
    },
    {
      "task_number": 2,
      "goal": "Add example integration in main.py",
      "files_to_modify": ["main.py"],
      "what_to_do": [
        "Import DashAbility",
        "Add to player in create_game",
        "Show how to bind to key"
      ]
    }
  ]
}
```

### Implementation Task 1
```python
# FILE: Game/Abilities/dash.py
from pygame import Vector2
from Game.Abilities.ability import Ability

class DashAbility(Ability):
    def __init__(self, dash_distance: float = 150.0, cooldown_ms: int = 3000):
        super().__init__(
            name="Dash",
            cooldown_ms=cooldown_ms,
            duration_ms=0,
            energy_cost=10
        )
        self.dash_distance = dash_distance
    
    def _activate(self, arena, **kwargs):
        if self._character is None:
            return
        
        # Use aim direction (universal - all characters have this)
        aim_dir = self._character.aim_direction
        if aim_dir.length() > 0:
            dash_vector = aim_dir.normalize() * self.dash_distance
        else:
            dash_vector = Vector2(self.dash_distance, 0)
        
        # Move character
        self._character.position += dash_vector
        
        # Clamp to world bounds
        if arena and hasattr(arena, 'world_dimensions'):
            world_w, world_h = arena.world_dimensions
            margin = 25
            self._character.position.x = max(margin, min(world_w - margin, 
                                                          self._character.position.x))
            self._character.position.y = max(margin, min(world_h - margin, 
                                                          self._character.position.y))
```

### Verification
```
✅ Syntax correct
✅ Follows Ability base class pattern
✅ Uses universal properties (aim_direction, position)
✅ Works for any character (player or AI)
✅ Handles edge cases (bounds checking)
✅ Proper docstrings and imports

VERIFIED: Implementation is complete and correct
```

## Usage in Your Code

### Running the Workflow
```python
from Agent.agent_main import AgentMain

# Initialize agent with request limiting
# max_requests_before_auth: Number of API calls before asking user permission
agent = AgentMain(use_gemini=True, max_requests_before_auth=10)

# Create ability
result = agent.create_ability_workflow(
    "Create a freeze ability that slows enemies by 50% for 3 seconds"
)

# Check result
if result["success"]:
    print("Ability created!")
    print(f"Files modified: {result['files']}")
else:
    print("Failed:", result["errors"])
```

### Request Limiting (Safety Feature)

The agent includes a **request limit** to prevent excessive API calls:

```python
# Default: 10 requests before asking permission
agent = AgentMain(use_gemini=True, max_requests_before_auth=10)

# More permissive: 20 requests
agent = AgentMain(use_gemini=True, max_requests_before_auth=20)

# Very cautious: 3 requests
agent = AgentMain(use_gemini=True, max_requests_before_auth=3)
```

**What happens when limit is reached:**
1. Workflow pauses
2. Shows warning about API usage
3. Asks: "Continue with more requests? (yes/no)"
4. If yes: Resets counter and continues
5. If no: Stops workflow gracefully

**Why this matters:**
- Prevents runaway API costs
- Gives you control over long-running operations
- Protects against potential infinite loops

### Using Created Abilities
```python
# In main.py or wherever you create characters
from Game.Abilities.your_new_ability import YourNewAbility

# Add to player
player.add_ability("new_ability", YourNewAbility())

# Bind to key (in convert_key_to_string)
if key[pygame.K_g]:
    keys.append("ability_new")

# Handle in game loop
if "ability_new" in keys:
    player.use_ability("new_ability", arena)
```

### AI Using Abilities
```python
# AI can trigger abilities programmatically
class SmartAI(Cow):
    def update(self, arena):
        super().update(arena)
        
        # Use ability when appropriate
        if self.should_use_ability():
            self.use_ability("dash", arena)
```

## Troubleshooting

### "Ability doesn't work for AI"
- Check if ability uses player-specific inputs (mouse position, etc.)
- Ensure it uses universal properties (position, aim_direction)
- Verify AI can trigger it programmatically

### "Files not being created"
- Check file paths in plan
- Ensure write permissions
- Check for syntax errors in generated code

### "Verification fails"
- Read the issues listed
- Check if ability follows base class pattern
- Ensure universal applicability

## Best Practices

1. **Describe Clearly**: More detail = better result
2. **Think Universal**: Always consider AI usage
3. **Use Examples**: Reference existing abilities (Dash)
4. **Iterate**: If first attempt isn't perfect, refine description
5. **Test Both Ways**: Test player using on AI AND AI using on player

## Advanced: Custom Effect States

For abilities with lasting effects (freeze, burn, stun):

```python
# The agent will add to Cow base class:
class Cow:
    def __init__(self, ...):
        # ... existing code ...
        self.status_effects = {}  # Track active effects
    
    def apply_effect(self, effect_type, duration_ms, magnitude):
        self.status_effects[effect_type] = {
            'end_time': pygame.time.get_ticks() + duration_ms,
            'magnitude': magnitude
        }
    
    def update_effects(self):
        now = pygame.time.get_ticks()
        expired = [k for k, v in self.status_effects.items() 
                   if now > v['end_time']]
        for effect in expired:
            del self.status_effects[effect]
```

This ensures any character can be affected by any effect!

---

## Summary

The workflow ensures:
- ✅ Clear planning before implementation
- ✅ Task-by-task development with context
- ✅ Universal design (works for ALL characters)
- ✅ Verification before marking complete
- ✅ Follows DRY and SOLID principles
- ✅ Integrates properly with existing systems

**Result:** Production-ready abilities that enhance gameplay for everyone!
