# Quick Start Guide

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API key:**
   Create `.env` file:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
   Get key from: https://ai.google.dev/

3. **Run the game:**
   ```bash
   python main.py
   ```

## Game Controls

| Key | Action |
|-----|--------|
| WASD | Move |
| Mouse | Aim |
| Left Click | Shoot |
| Space | Eat (in fields) |
| P | Poop (shrink) |
| F | Dash ability |
| E/Q | Zoom in/out |
| R | Restart (after game over) |
| ESC | Quit (after game over) |

## Create Your First Ability

```bash
python test_ability_creation.py
```

Choose an example or describe your own!

**Example:**
```
"Create a speed boost that doubles movement speed for 5 seconds"
```

The agent will:
1. ✅ Plan the implementation
2. ✅ Create necessary files
3. ✅ Verify everything works

## Ability Creation Workflow

```
1. USER: Describes ability in natural language
        ↓
2. AGENT: Plans implementation (3-6 tasks)
        ↓
3. AGENT: Implements each task (writes actual code)
        ↓
4. AGENT: Verifies implementation
        ↓
5. DONE: Ability ready to use!
```

### Critical Design Rule

**Abilities MUST work for ALL characters:**
- ✅ Player can use on AI enemies
- ✅ AI can use on player  
- ✅ AI can use on other AI

The agent automatically ensures this!

## Project Structure

```
Project_SYNTAX_V2/
├── main.py                    # ← Start here
├── test_ability_creation.py   # ← Create abilities
├── Agent/
│   ├── agent_main.py          # Orchestrates workflow
│   └── gemini_client.py       # Gemini API
├── Game/
│   ├── Abilities/             # Your custom abilities
│   ├── Character/             # Player & AI
│   └── Arena/                 # Game world
└── README.md                  # Full documentation
```

## Next Steps

1. **Play the game** to understand mechanics
2. **Try test_ability_creation.py** to create an ability
3. **Read ABILITY_CREATION_GUIDE.md** for advanced usage
4. **Check Game/README.md** for game design details

## Common Issues

**Game won't start:**
- Install pygame: `pip install pygame`
- Check Python version: 3.8+

**Ability creation fails:**
- Set GEMINI_API_KEY in .env
- Check internet connection
- Verify API quota

**AI doesn't use abilities:**
- AI uses abilities programmatically
- Check CombatAICow class for logic
- Add ability to AI in main.py

## Configuration

Edit `main.py` to customize:
```python
NUM_AI_PLAYERS = 5  # Number of bots
```

## Learn More

- `README.md` - Complete documentation
- `ABILITY_CREATION_GUIDE.md` - Detailed workflow guide
- `Game/README.md` - Game design document

## Support

Check existing abilities for examples:
- `Game/Abilities/dash.py` - Simple movement ability
- Use as template for your own!

---

**Ready to create custom abilities with AI? Start with:**
```bash
python test_ability_creation.py
```
