"""
Fixing logic for the agent system.
"""
import os
import json
import re
from typing import Dict, List, Any

from .utils import debug_print, safe_read_file, safe_write_file, extract_json_from_text, normalize_effects, fix_same_line_statements


def fix_weapon_issues(weapon_plan: Dict[str, Any], validation_results: Dict[str, Any], agent=None) -> bool:
    """Fix issues discovered during validation."""
    debug_print("🔧 Starting to fix weapon issues", "INFO")

    validation_errors = list(validation_results.get("errors", []))
    syntax_errors = list(validation_results.get("syntax_errors", []))
    combined_errors = validation_errors + syntax_errors

    debug_print(
        f"Found {len(combined_errors)} issues to fix (validation: {len(validation_errors)}, syntax: {len(syntax_errors)})",
        "INFO"
    )

    if not combined_errors:
        debug_print("✅ No errors to fix", "INFO")
        return True

    if agent is None:
        debug_print("❌ No agent provided, cannot perform AI fixes", "ERROR")
        return False

    weapon_name = weapon_plan.get("weapon_name", "TestWeapon")
    weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)
    normalized_effects = normalize_effects(weapon_plan.get("effects", []))

    # Collect all error information for context
    context_sections: List[str] = []
    if validation_errors:
        context_sections.append("VALIDATION ISSUES:\n" + "\n".join(validation_errors))
    if syntax_errors:
        context_sections.append("SYNTAX ERRORS:\n" + "\n".join(syntax_errors))
    error_context = "\n\n".join(context_sections)
    debug_print(f"Error context: {error_context}", "DEBUG")

    effect_summary_lines = []
    for effect_info in normalized_effects:
        effect_summary_lines.append(
            f"- {effect_info['name']} ({effect_info['kind']}) => {json.dumps(effect_info['original'], default=str)}"
        )
    effects_summary = "\n".join(effect_summary_lines) if effect_summary_lines else "(none)"

    # Read relevant files for context
    weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
    projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
    cow_file = "Game/Character/cow.py"

    tracked_files = {
        "weapon": weapon_file,
        "projectile": projectile_file,
        "cow": cow_file,
    }

    before_snapshots = {}
    for path in tracked_files.values():
        if path and os.path.exists(path):
            content, success = safe_read_file(path)
            if success:
                before_snapshots[path] = content

    debug_print(f"Reading files for context...", "DEBUG")
    code_context = "## WEAPON FILE\n"
    try:
        with open(weapon_file, 'r') as f:
            code_context += f"```python\n{f.read()}\n```\n\n"
        debug_print(f"✅ Read weapon file: {weapon_file}", "DEBUG")
    except Exception as exc:
        debug_print(f"❌ Could not read weapon file: {weapon_file} ({exc})", "ERROR")

    if os.path.exists(projectile_file):
        code_context += "## PROJECTILE FILE\n"
        try:
            with open(projectile_file, 'r') as f:
                code_context += f"```python\n{f.read()}\n```\n\n"
            debug_print(f"✅ Read projectile file: {projectile_file}", "DEBUG")
        except Exception as exc:
            debug_print(f"❌ Could not read projectile file: {projectile_file} ({exc})", "ERROR")

    # Read relevant parts of Cow class (effect methods)
    code_context += "## COW CLASS (Effects Section)\n"
    try:
        with open(cow_file, 'r') as f:
            cow_content = f.read()
            effect_methods = []
            for effect in normalized_effects:
                if effect["kind"] != "impact":
                    continue
                effect_name = effect["slug"]
                if f"apply_{effect_name}" in cow_content:
                    method_start = cow_content.find(f"def apply_{effect_name}")
                    if method_start != -1:
                        method_end = cow_content.find("\n    def ", method_start + 1)
                        if method_end == -1:
                            method_end = len(cow_content)
                        effect_methods.append(cow_content[method_start:method_end])

            if effect_methods:
                code_context += "```python\n" + "\n\n".join(effect_methods) + "\n```\n\n"
        debug_print(f"✅ Read Cow class effect methods", "DEBUG")
    except Exception as exc:
        debug_print(f"❌ Could not read Cow class ({exc})", "ERROR")

    # Create comprehensive system prompt for fixing
    system_prompt = """You are a senior debugging and code-fixing specialist for the SYNTAX V2 game project.

Your mission is to analyze and fix validation errors in generated weapon implementations.

## Critical Instructions

1. **ALWAYS READ FILES FIRST**: Before making any changes, use read_file tool to understand:
   - The current implementation
   - The existing code structure
   - What's actually wrong vs what's expected

2. **UNDERSTAND THE CONTEXT**:
   - Read related files (weapon file, projectile file, character file)
   - Understand the effect system and how effects are applied
   - Check existing working examples for patterns

3. **FIX SYSTEMATICALLY**:
   - Address each error one at a time
   - Verify your understanding before making changes
   - Use write_into_file to make precise, targeted fixes
   - Don't rewrite entire files unless absolutely necessary

4. **VALIDATION APPROACH**:
   - Character effects need: state variable (is_<effect>) and apply method (apply_<effect>) in Cow class
   - Projectile effects are implemented in the projectile's on_character_hit method
   - Projectile-only behaviors (homing, bouncing, splitting, etc.) don't need Cow class modifications
   - ALL weapons MUST use "placeholder.png" for floor_image_name and projectile_image_name
   - Splitting effects MUST spawn the exact number specified in effect_details (e.g., split_count: 3 means spawn 3 projectiles)
   - Use arena.spawn_projectile() with ONLY: start_pos, direction, speed, damage, owner parameters

## Process

1. Read the weapon plan to understand what was intended
2. Read the validation errors to understand what's wrong
3. Read all relevant files to understand current state
4. Fix each error systematically
5. Verify your changes make sense

## Rules

- Don't guess - read files to understand the problem
- Don't duplicate code - reuse existing patterns
- Keep changes minimal and focused
- Follow the existing code style and patterns
- Test your understanding by reading before writing

## Critical Method Signatures (MUST BE EXACT)

### on_character_hit Method
```python
def on_character_hit(self, target, arena):
```
- Takes 2 parameters: `target` and `arena`
- Must apply damage: `target.take_damage(self.damage)`
- Must destroy: `self.alive = False` (NEVER `self.kill()`)

### update Method
```python
def update(self):
```
- Takes NO parameters (only `self`)
- Arena calls with no arguments

## Common Mistakes to Fix

1. **Wrong**: `def on_character_hit(self, target):` → **Right**: `def on_character_hit(self, target, arena):`
2. **Wrong**: `self.kill()` → **Right**: `self.alive = False`
3. **Wrong**: `def update(self, arena):` → **Right**: `def update(self):`
4. **Wrong**: Using non-placeholder images → **Right**: Use "placeholder.png" for all weapons
"""

    # Create the fix prompt
    fix_prompt = f"""Fix the issues found in the weapon implementation.

## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## DETECTED ISSUES
{error_context}

## EFFECT SUMMARY
{effects_summary}

## CURRENT CODE
{code_context}

## YOUR TASK

1. Resolve any syntax failures first so every Python file compiles without errors.
2. Call read_file(path, line_count=True) for every relevant file (weapon, projectile, cow, arena, etc.) to understand the current implementation.
3. Identify the root cause of each remaining validation error.
4. Fix the issues using the available tools (read_file, write_into_file, write_over_file).
5. Focus on:
   - Correct method signatures
   - Proper parameter passing
   - Missing imports or methods
   - Correct image usage
   - Effect implementation

Do not move on until every issue above is resolved."""

    debug_print("🤖 Using AI agent to fix validation issues", "INFO")

    try:
        combined_prompt = agent._combine_system_prompts(system_prompt)
        debug_print("📞 Calling AI to analyze and fix validation errors...", "INFO")
        debug_print("🛠️  Invoking ask_with_tools for validation fixes", "DEBUG")
        response = agent.chat_with_tools(
            prompt=fix_prompt,
            system_prompt=combined_prompt,
            max_iterations=15
        )

        changed_files = []
        for label, path in tracked_files.items():
            if not path:
                continue
            exists_now = os.path.exists(path)
            before_content = before_snapshots.get(path)
            if not before_content and exists_now:
                changed_files.append(path)
                continue
            if before_content and exists_now:
                content, success = safe_read_file(path)
                if success and content != before_content:
                    changed_files.append(path)

        if changed_files:
            formatted_files = []
            for path in sorted(changed_files):
                if path.endswith('.py') and os.path.exists(path):
                    content, success = safe_read_file(path)
                    if success:
                        fixed_content = fix_same_line_statements(content)
                        if fixed_content != content:
                            safe_write_file(path, fixed_content)
                            formatted_files.append(path)
            if formatted_files:
                debug_print(
                    f"🧹 Auto-formatted inline statements in: {', '.join(formatted_files)}",
                    "DEBUG"
                )
            debug_print(
                f"📝 Files updated by fix pass: {', '.join(sorted(changed_files))}",
                "DEBUG"
            )
        else:
            debug_print(
                "⚠️  Fix pass completed but no file changes were detected.",
                "WARNING"
            )

        debug_print("✅ AI completed fixing process", "INFO")
        debug_print(f"AI response summary: {response[:200] if response else 'No text response'}...", "DEBUG")
        return True

    except Exception as e:
        debug_print(f"❌ Error during fixing: {e}", "ERROR")
        import traceback
        debug_print(f"Traceback: {traceback.format_exc()}", "DEBUG")
        return False


def fix_simulation_issues(weapon_plan: Dict[str, Any], simulation_results: Dict[str, Any], agent=None) -> bool:
    """Fix issues discovered during game simulation testing."""
    debug_print("🔧 Analyzing simulation errors", "INFO")
    
    if agent is None:
        debug_print("❌ No agent provided, cannot perform AI fixes", "ERROR")
        return False

    # Collect all error information with detailed formatting for the agent
    raw_errors = simulation_results.get("errors", [])
    if raw_errors:
        error_context = "\n\n".join(
            f"{idx}. {error.strip()}" for idx, error in enumerate(raw_errors, start=1)
        )
    else:
        error_context = "No runtime errors were reported, but a fix was requested."

    debug_print(f"Simulation error context prepared for agent:\n{error_context}", "DEBUG")

    weapon_name = weapon_plan.get("weapon_name", "TestWeapon")
    weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)
    normalized_effects = normalize_effects(weapon_plan.get("effects", []))

    # Read relevant files
    weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
    projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
    cow_file = "Game/Character/cow.py"

    tracked_files = {
        "weapon": weapon_file,
        "projectile": projectile_file,
        "cow": cow_file,
    }

    before_snapshots = {}
    for path in tracked_files.values():
        if path and os.path.exists(path):
            content, success = safe_read_file(path)
            if success:
                before_snapshots[path] = content

    debug_print(f"Reading files for simulation fix context...", "DEBUG")
    code_context = "## WEAPON FILE\n"
    try:
        with open(weapon_file, 'r') as f:
            code_context += f"```python\n{f.read()}\n```\n\n"
        debug_print(f"✅ Read weapon file for simulation fix", "DEBUG")
    except:
        pass

    if os.path.exists(projectile_file):
        code_context += "## PROJECTILE FILE\n"
        try:
            with open(projectile_file, 'r') as f:
                code_context += f"```python\n{f.read()}\n```\n\n"
            debug_print(f"✅ Read projectile file for simulation fix", "DEBUG")
        except:
            pass

    # Read relevant parts of Cow class (effect methods)
    code_context += "## COW CLASS (Effects Section)\n"
    try:
        with open(cow_file, 'r') as f:
            cow_content = f.read()
            # Extract effect-related methods
            effect_methods = []
            for effect in normalized_effects:
                if effect["kind"] != "impact":
                    continue
                effect_name = effect["slug"]
                if f"apply_{effect_name}" in cow_content:
                    # Find and extract the method
                    method_start = cow_content.find(f"def apply_{effect_name}")
                    if method_start != -1:
                        # Find end of method (next def or end of file)
                        method_end = cow_content.find("\n    def ", method_start + 1)
                        if method_end == -1:
                            method_end = len(cow_content)
                        effect_methods.append(cow_content[method_start:method_end])

            if effect_methods:
                code_context += "```python\n" + "\n\n".join(effect_methods) + "\n```\n\n"
        debug_print(f"✅ Read Cow class effect methods for simulation fix", "DEBUG")
    except:
        pass

    system_prompt = """You are a senior game developer fixing runtime issues in weapon implementations.

Your task: Fix runtime errors that occur during game simulation testing.

## Available Tools

Use these tools to fix the issues:
- read_file(file_path): Read file contents
- write_into_file(file_path, content, start_line, end_line): Replace specific lines
- write_over_file(file_path, content): Rewrite entire file (use sparingly)

## Common Runtime Issues

1. **TypeError in apply_ methods**: Wrong number of parameters or keyword arguments
   - Check the method signature in Cow class
   - Ensure projectile calls match the signature exactly

2. **AttributeError**: Missing methods or attributes
   - Check if effect method exists in Cow class
   - Verify method names are correct

3. **Projectile behavior errors**: Projectiles not spawning or behaving correctly
   - Check arena.spawn_projectile() parameters
   - Verify update() and on_character_hit() signatures

4. **Import errors**: Missing imports or wrong module paths
   - Verify all imports are correct
   - Check for circular dependencies

## Instructions

1. Read all relevant files first
2. Identify the root cause of each error
3. Fix each issue systematically
4. Verify your changes make sense

Remember: Be precise and minimal in your fixes."""

    effect_lines = [
        f"- {effect['name']} ({effect['kind']}) => {json.dumps(effect['original'], default=str)}"
        for effect in normalized_effects
    ]
    effects_summary = "\n".join(effect_lines) if effect_lines else "(no special effects)"

    prompt = f"""Fix the runtime issues found during game simulation testing.

## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## SIMULATION ERRORS
{error_context}

## EFFECT SUMMARY
{effects_summary}

## CURRENT CODE
{code_context}

## YOUR TASK

1. Call read_file(path, line_count=True) for every file before editing it (weapon, projectile, cow, arena, etc.).
2. Identify the root cause of each simulation error
3. Fix the issues using the available tools
4. Focus on:
   - Correct method signatures
   - Proper parameter passing
   - Missing imports or methods
   - Correct arena.spawn_projectile() usage

Fix all issues to ensure the weapon works in all test scenarios."""

    debug_print("🤖 Using AI agent to fix simulation issues", "INFO")

    try:
        # Combine system prompt with agent's global prompt
        combined_prompt = agent._combine_system_prompts(system_prompt)
        
        # Call AI to fix issues - MUST use ask_with_tools so AI can actually make changes!
        debug_print("📞 Calling AI to analyze and fix simulation errors...", "INFO")
        debug_print("🛠️  Invoking ask_with_tools for simulation fixes", "DEBUG")
        response = agent.chat_with_tools(
            prompt=prompt,
            system_prompt=combined_prompt,
            max_iterations=15
        )

        changed_files = []
        for label, path in tracked_files.items():
            if not path:
                continue
            exists_now = os.path.exists(path)
            before_content = before_snapshots.get(path)
            if not before_content and exists_now:
                changed_files.append(path)
                continue
            if before_content and exists_now:
                content, success = safe_read_file(path)
                if success and content != before_content:
                    changed_files.append(path)

        if changed_files:
            formatted_files = []
            for path in sorted(changed_files):
                if path.endswith('.py') and os.path.exists(path):
                    content, success = safe_read_file(path)
                    if success:
                        fixed_content = fix_same_line_statements(content)
                        if fixed_content != content:
                            safe_write_file(path, fixed_content)
                            formatted_files.append(path)
            if formatted_files:
                debug_print(
                    f"🧹 Auto-formatted inline statements in: {', '.join(formatted_files)}",
                    "DEBUG"
                )
            debug_print(
                f"📝 Files updated by simulation fix pass: {', '.join(sorted(changed_files))}",
                "DEBUG"
            )
        else:
            debug_print(
                "⚠️  Simulation fix pass completed but no file changes were detected.",
                "WARNING"
            )

        debug_print(f"✅ AI completed simulation fixing process", "INFO")
        debug_print(f"AI response summary: {response[:200] if response else 'No text response'}...", "DEBUG")
        return True

    except Exception as e:
        debug_print(f"❌ Error during simulation fix: {e}", "ERROR")
        import traceback
        debug_print(f"Traceback: {traceback.format_exc()}", "DEBUG")
        return False
