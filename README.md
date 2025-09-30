# SYNTAX V2 - Battle Royale with AI-Powered Ability Creation

A top-down battle royale game where you can create custom abilities using AI agents powered by Google's Gemini API.

## Features

### ✅ Working MVP
- **Battle Royale Gameplay**: Last cow standing wins
- **Player vs AI Combat**: Battle against intelligent AI bots
- **Dynamic World**: Large scrolling world with grass fields, golden fields, and obstacles
- **Weapon System**: Pick up weapons, collect ammo, and shoot projectiles
- **Size Mechanics**: Eat to grow (more HP, slower), poop to shrink (less HP, faster)
- **Ability System**: Extensible ability framework (includes Dash as example)
- **AI-Powered Creation**: Use natural language to create new abilities via Gemini API

### 🎮 Gameplay Controls
- **WASD**: Move
- **Mouse**: Aim
- **Left Click**: Shoot (if weapon equipped)
- **Space**: Eat (when in grass/golden fields)
- **P**: Poop (shrink and drop object)
- **F**: Use Dash ability
- **E/Q**: Zoom in/out
- **R**: Restart (when game over)
- **ESC**: Quit (when game over)

## Installation

### Prerequisites
```bash
# Python 3.8+
pip install -r requirements.txt
```

### Environment Setup
Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_key_here  # Optional, for future ChatGPT integration
```

Get your Gemini API key from: https://ai.google.dev/

## Running the Game

### Start the Battle Royale Game
```bash
python main.py
```

Configuration in `main.py`:
- `NUM_AI_PLAYERS = 5` - Change this to adjust number of AI opponents

### Create New Abilities
```bash
python test_ability_creation.py
```

This launches the ability creation workflow where you can describe abilities in natural language.

**Safety Feature:** The agent includes a request limit (default: 10 API calls) before asking for your permission to continue. This prevents excessive API usage and costs.

## Architecture

### Core Systems

#### 1. **Game Engine** (`Game/`)
- **Arena**: World management, collision detection, victory conditions
- **Character/Cow**: Base character class with health, movement, abilities
- **Character/CombatAICow**: Intelligent AI that seeks resources and attacks enemies
- **Objects**: Projectiles, weapon pickups, grass fields, golden fields, obstacles
- **Weapons**: Weapon system with ammo, damage, projectile sprites
- **Abilities**: Extensible ability system with base class and examples

#### 2. **AI Agent System** (`Agent/`)
- **AgentMain**: Orchestrates the ability creation workflow
- **GeminiClient**: Google Gemini API integration
- **ChatGPT**: OpenAI integration (kept for future use)
- **Tools**: File operations, project structure analysis

#### 3. **Ability Creation Workflow**

```
User Description
      ↓
   Planning Phase
   (Analyzes requirements, creates task breakdown)
      ↓
   Implementation Phase
   (Generates code, modifies files task-by-task)
      ↓
   Verification Phase
   (Checks correctness, ensures universality)
      ↓
   Complete!
```

### Key Design Principles

1. **DRY (Don't Repeat Yourself)**: Reusable components and services
2. **SOLID Principles**: 
   - Single Responsibility: Each class has one clear purpose
   - Open/Closed: Extend via inheritance/composition, don't modify core
   - Dependency Inversion: Depend on abstractions (Ability base class)
3. **Universal Design**: Abilities work for ALL characters (player + AI)
4. **Layer System**: 4-layer collision system (underground, ground, mid-air, air)

## Creating Custom Abilities

### Example: Freeze Ability

```python
# Describe what you want
ability_description = """
Create a freeze ability that slows down enemies when they are hit.
The freeze effect should last 3 seconds and reduce movement speed by 50%.
It should work on any character.
"""

# Run the workflow
from Agent.agent_main import AgentMain
agent = AgentMain(use_gemini=True)
result = agent.create_ability_workflow(ability_description)
```

### The Agent Will:
1. **Plan**: Break down the ability into tasks
   - Task 1: Add freeze state to Cow base class
   - Task 2: Create FreezeAbility class
   - Task 3: Create freeze projectile or effect object
   - Task 4: Integrate with Arena collision system

2. **Implement**: Generate complete code for each task
   - Modifies `Game/Character/cow.py` to add freeze state
   - Creates `Game/Abilities/freeze.py` with ability logic
   - Updates relevant systems

3. **Verify**: Check that everything works
   - Syntax validation
   - Universal applicability (works on any character)
   - Integration correctness

### Universal Ability Design

**Critical**: Abilities must work bidirectionally:
- ✅ Player can use on AI enemies
- ✅ AI enemies can use on player
- ✅ AI can use on other AI

The agent ensures this by:
- Adding effect states to the base `Cow` class
- Creating object-based effects when appropriate
- Making abilities character-agnostic

## Project Structure

```
Project_SYNTAX_V2/
├── Agent/
│   ├── agent_main.py          # Main agent orchestrator
│   ├── gemini_client.py       # Gemini API client
│   ├── chatGPT.py             # OpenAI client
│   ├── Helpers/               # Utility functions
│   ├── Prompts/               # System prompts
│   └── Tools/                 # File operations
├── Game/
│   ├── Abilities/             # Ability system
│   │   ├── ability.py         # Base classes
│   │   └── dash.py            # Example ability
│   ├── Arena/
│   │   └── arena.py           # World manager
│   ├── Character/
│   │   ├── cow.py             # Base character
│   │   ├── ai_cow.py          # Simple AI
│   │   └── combat_ai_cow.py  # Combat AI
│   ├── Objects/               # Game objects
│   ├── Weapons/               # Weapon system
│   └── README.md              # Game design doc
├── main.py                    # Game entry point
├── test_ability_creation.py   # Ability creation demo
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Battle Royale Mechanics

### Victory Conditions
- **Win**: Be the last cow alive
- **Lose**: Your health reaches 0
- **Draw**: All cows die simultaneously (rare)

### Resource Management
- **Ammo**: Found by eating in grass fields (probability-based)
- **Weapons**: Dropped in golden fields when eating (probability-based)
- **Health**: Increases when growing, decreases when taking damage

### Size Scaling
- **Eating**: Grows size → More max HP, slower movement
- **Pooping**: Shrinks size → Less max HP, faster movement
- Strategic trade-off between tankiness and mobility

### AI Behavior
Combat AI (`CombatAICow`) uses state machine:
- **Wander**: Default state, explores the map
- **Seek Field**: Low ammo/no weapon → seeks grass/golden fields
- **Attack**: Has weapon + ammo + enemy in range → shoots
- **Flee**: Low health + enemy nearby → runs away

## Development

### Adding a New Ability Manually

1. Create ability class in `Game/Abilities/your_ability.py`:
```python
from Game.Abilities.ability import Ability

class YourAbility(Ability):
    def __init__(self):
        super().__init__(
            name="Your Ability",
            cooldown_ms=3000,
            duration_ms=0,
            energy_cost=10
        )
    
    def _activate(self, arena, **kwargs):
        # Implementation here
        pass
```

2. Add to character in `main.py`:
```python
from Game.Abilities.your_ability import YourAbility
player.add_ability("your_ability", YourAbility())
```

3. Bind to key in `convert_key_to_string()` and handle in game loop

### Extending the Agent

The agent system is modular. To extend:
- Add new tools in `Agent/Tools/`
- Modify prompts in `Agent/Prompts/`
- Add verification steps in `agent_main.py`

## Troubleshooting

### Game won't start
- Check pygame installation: `pip install pygame>=2.5.0`
- Verify Python version: 3.8+

### Ability creation fails
- Check GEMINI_API_KEY in `.env`
- Ensure internet connection
- Check API quota/limits

### AI doesn't fight
- Combat AI needs starting ammo to be effective
- Verify weapon pickups are spawning in golden fields
- Check projectile collision system

## Future Enhancements

- [ ] Multiplayer support (multiple real players)
- [ ] More AI personalities
- [ ] Ability combos
- [ ] Power-up objects
- [ ] Environmental hazards
- [ ] Automatic testing for created abilities
- [ ] Visual ability effects
- [ ] Sound effects

## Credits

Built with:
- **Pygame**: Game engine
- **Google Gemini**: AI ability creation
- **OpenAI**: Alternative AI backend

## License

This project is for educational purposes.
