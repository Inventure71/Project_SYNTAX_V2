"""
Refactored Agent Main - Modular Design
"""
import json
import os
from typing import Dict, List, Any

from Agent.chatGPT import ChatGPT
from Agent.gemini_client import GeminiClient
from Agent.Tools.get_project_structure import get_project_structure
from Agent.Tools.helpers_ignore import collect_directory_files_and_contents
from Agent.Prompts.system_prompts import global_system_prompt

# Import our new modules
from Agent.Modules.utils import (
    debug_print,
    safe_read_file,
    safe_write_file,
    extract_json_from_text,
    format_file_size,
    normalize_effects,
    fix_same_line_statements,
)
from Agent.Modules.validation import validate_weapon_implementation, validate_projectile_behavior, run_python_syntax_check
from Agent.Modules.fixing import fix_weapon_issues, fix_simulation_issues
from Agent.Modules.simulation_testing import run_game_simulation_tests


class AgentMain:
    def __init__(self, use_gemini: bool = True, max_requests_before_auth: int = 10):
        """
        Initialize the agent with either Gemini or ChatGPT backend.

        Args:
            use_gemini: If True, use Gemini API; if False, use ChatGPT
            max_requests_before_auth: Maximum API requests before asking user to continue
        """
        self.use_gemini = use_gemini

        if use_gemini:
            self.gemini = GeminiClient()
            self.active_client = self.gemini
        else:
            self.chatGPT = ChatGPT()
            self.chatGPT.switch_model("gpt-5-mini", True)
            self.active_client = self.chatGPT

        # Project structure
        self.project_structure_simple = None
        self.project_structure_complex = None
        self.project_structure_complex_with_files = None

        # Request limiting
        self.max_requests_before_auth = max_requests_before_auth
        self.request_count = 0

        self.backup_dir = "Backup/Agent_Backups"
        self.current_backup_id = None

        self.update_project_structure()
        debug_print("✅ Agent initialized successfully", "INFO")

    def update_project_structure(self):
        """Update cached project structure information."""
        debug_print("📁 Updating project structure", "DEBUG")
        self.project_structure_simple = get_project_structure(False)
        self.project_structure_complex = get_project_structure(True)
        self.project_structure_complex_with_files = collect_directory_files_and_contents("Game")
        debug_print("✅ Project structure updated", "DEBUG")

    def _combine_system_prompts(self, specific_prompt: str) -> str:
        """Combine global system prompt with specific prompt."""
        return f"{global_system_prompt}\n\n{'='*70}\n# SPECIFIC TASK INSTRUCTIONS\n{'='*70}\n\n{specific_prompt}"

    def _check_request_limit(self) -> bool:
        """Check if we've hit the request limit."""
        self.request_count += 1
        if self.request_count >= self.max_requests_before_auth:
            debug_print(f"⚠️  Request limit reached ({self.request_count}/{self.max_requests_before_auth})", "WARNING")
            user_input = input("Continue with more API requests? (y/n): ").strip().lower()
            if user_input == 'y':
                self.request_count = 0  # Reset counter
                return True
            else:
                debug_print("❌ User stopped workflow", "INFO")
                return False
        return True

    def _create_backup(self, description: str = "agent_changes") -> str:
        """Create a backup of important files before making changes."""
        debug_print(f"💾 Creating backup: {description}", "INFO")

        import shutil
        from datetime import datetime

        # Create backup directory if it doesn't exist
        os.makedirs(self.backup_dir, exist_ok=True)

        # Generate backup ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{timestamp}_{description}"
        backup_path = os.path.join(self.backup_dir, backup_id)
        os.makedirs(backup_path, exist_ok=True)

        # Files/directories to backup
        backup_targets = [
            "Game/Character/cow.py",
            "Game/Abilities",
            "Game/Weapons",
            "Game/Objects",
            "main.py"
        ]

        backed_up = []
        for target in backup_targets:
            if os.path.exists(target):
                dest = os.path.join(backup_path, target)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                if os.path.isfile(target):
                    shutil.copy2(target, dest)
                else:
                    shutil.copytree(target, dest, dirs_exist_ok=True)
                backed_up.append(target)
                debug_print(f"  ✓ Backed up: {target}", "DEBUG")

        self.current_backup_id = backup_id
        debug_print(f"📦 Backup created: {backup_id} ({len(backed_up)} items)", "INFO")
        return backup_id

    def _restore_backup(self, backup_id: str) -> bool:
        """Restore files from a backup."""
        debug_print(f"♻️  Restoring backup: {backup_id}", "INFO")

        backup_path = os.path.join(self.backup_dir, backup_id)

        if not os.path.exists(backup_path):
            debug_print(f"❌ Backup not found: {backup_id}", "ERROR")
            return False

        try:
            import shutil
            
            # Restore each file/directory
            restored = []
            for item in os.listdir(backup_path):
                src = os.path.join(backup_path, item)
                dest = item

                if os.path.isfile(src):
                    shutil.copy2(src, dest)
                else:
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(src, dest)

                restored.append(item)
                debug_print(f"  ✓ Restored: {item}", "DEBUG")

            debug_print(f"✅ Backup restored: {len(restored)} items", "INFO")
            return True

        except Exception as e:
            debug_print(f"❌ Failed to restore backup: {e}", "ERROR")
            return False

    # Backward-compatible public methods
    def restore_backup(self, backup_id: str = None) -> bool:
        """Public wrapper to match legacy API."""
        return self._restore_backup(backup_id or self.current_backup_id)

    def list_backups(self) -> list:
        """List available backups (legacy compatibility)."""
        debug_print("📦 Listing available backups", "INFO")
        if not os.path.exists(self.backup_dir):
            debug_print("❌ No backup directory found", "ERROR")
            return []
        try:
            backups = []
            for item in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, item)
                if os.path.isdir(backup_path):
                    backups.append(item)
            backups.sort(reverse=True)
            debug_print(f"✅ Found {len(backups)} backups", "INFO")
            return backups
        except Exception as e:
            debug_print(f"❌ Error listing backups: {e}", "ERROR")
            return []

    def create_weapon_workflow(self, weapon_description: str) -> Dict[str, Any]:
        """
        Main workflow for creating a weapon with comprehensive validation and testing.
        """
        debug_print("="*70, "INFO")
        debug_print("🎮 SYNTAX V2 - WEAPON CREATION WORKFLOW", "INFO")
        debug_print("="*70, "INFO")

        results = {
            "success": False,
            "files_created": [],
            "files_modified": [],
            "errors": [],
            "weapon_plan": None,
            "syntax_checks": None,
            "validation": None,
            "simulation_tests": None,
            "final_validation": None
        }

        try:
            debug_print(f"🔍 Weapon description: {weapon_description[:100]}...", "INFO")

            # Step 1: Create backup
            debug_print("\n💾 Creating backup...", "INFO")
            backup_id = self._create_backup("weapon_creation")
            results["backup_id"] = backup_id

            # Step 2: Analyze weapon requirements
            debug_print("\n📋 Analyzing weapon requirements...", "INFO")
            weapon_plan = self._analyze_weapon_requirements(weapon_description)
            results["weapon_plan"] = weapon_plan

            debug_print(f"📊 Analysis Complete: {weapon_plan.get('weapon_name', 'Unknown')}", "INFO")
            debug_print(f"   Effects: {weapon_plan.get('effects', [])}", "INFO")

            # Step 3: Modify Cow class for character effects
            if weapon_plan.get("effects"):
                debug_print(f"\n🔧 Modifying Cow class for effects: {weapon_plan.get('effects', [])}", "INFO")
                cow_modified = self._modify_cow_class_for_effects(weapon_plan)
                if cow_modified:
                    results["files_modified"].append("Game/Character/cow.py")
                    debug_print("  ✓ Added effect support to Cow class", "INFO")

            # Step 4: Create weapon file
            debug_print("\n🔨 Creating weapon file...", "INFO")
            weapon_file = self._create_weapon_file_with_effects(weapon_plan)
            if weapon_file:
                results["files_created"].append(weapon_file)
                debug_print(f"  ✓ Created: {weapon_file}", "INFO")

            # Step 5: Create projectile (always needed, even without special effects)
            debug_print("\n✨ Creating projectile...", "INFO")
            projectile_file = self._create_effect_projectile(weapon_plan)
            if projectile_file:
                results["files_created"].append(projectile_file)
                debug_print(f"  ✓ Created: {projectile_file}", "INFO")

            # Step 6: Add weapon to loot pool
            debug_print("\n🎮 Adding weapon to game loot pool...", "INFO")
            arena_modified = self._add_weapon_to_loot_pool(weapon_plan)
            if arena_modified:
                results["files_modified"].append("Game/Arena/arena.py")
                debug_print("  ✓ Added to golden field loot pool", "INFO")

            # Stage 7: Syntax and static validation
            debug_print("\n🧪 Running syntax and static validation phase...", "INFO")

            effect_infos = normalize_effects(weapon_plan.get("effects", []))

            relevant_files = set()
            for path_candidate in results.get("files_created", []) + results.get("files_modified", []):
                if path_candidate:
                    relevant_files.add(path_candidate)
            if weapon_file:
                relevant_files.add(weapon_file)
            if projectile_file:
                relevant_files.add(projectile_file)
            if any(effect_info["kind"] == "impact" for effect_info in effect_infos):
                relevant_files.add("Game/Character/cow.py")

            relevant_files = sorted(relevant_files)

            max_syntax_attempts = 5
            syntax_passed = False

            for attempt in range(1, max_syntax_attempts + 1):
                debug_print(f"\n🧪 Syntax/static check attempt {attempt}/{max_syntax_attempts}", "INFO")
                syntax_results = run_python_syntax_check(relevant_files)
                validation_results = validate_weapon_implementation(weapon_plan, results)

                results["syntax_checks"] = syntax_results
                results["validation"] = validation_results

                combined_errors = []
                if syntax_results.get("has_errors"):
                    combined_errors.extend(syntax_results.get("errors", []))
                if validation_results.get("has_errors"):
                    combined_errors.extend(validation_results.get("errors", []))

                if not combined_errors:
                    syntax_passed = True
                    debug_print("  ✅ Syntax and static validation passed", "INFO")
                    break

                debug_print(f"  ⚠️  {len(combined_errors)} issues detected during syntax/static validation", "WARNING")
                for error in combined_errors[:5]:
                    debug_print(f"     - {error}", "WARNING")

                fix_success = fix_weapon_issues(
                    weapon_plan,
                    {**validation_results, "syntax_errors": syntax_results.get("errors", []), "errors": combined_errors},
                    agent=self,
                )

                if not fix_success:
                    debug_print("  ❌ Automatic fix attempt failed for syntax/static issues.", "ERROR")
                    break

            if not syntax_passed:
                results["success"] = False
                results["errors"].append("Syntax/static validation phase failed. Review detected issues.")
                debug_print("\n❌ Aborting workflow due to unresolved syntax/static issues.", "ERROR")
                return results

            # Stage 8: Simulation testing (only proceed when syntax passes)
            debug_print("\n🎮 Running game simulation phase...", "INFO")
            max_simulation_fix_attempts = 5
            simulation_passed = False

            for attempt in range(1, max_simulation_fix_attempts + 1):
                debug_print(f"\n🎮 Simulation attempt {attempt}/{max_simulation_fix_attempts}", "INFO")
                simulation_results = run_game_simulation_tests(weapon_plan)
                results["simulation_tests"] = simulation_results

                if not simulation_results.get("has_errors"):
                    debug_print("  ✅ All simulation tests passed!", "INFO")
                    simulation_passed = True
                    break

                debug_print(f"  ⚠️  {len(simulation_results.get('errors', []))} runtime issues detected", "WARNING")
                for error in simulation_results.get("errors", [])[:3]:
                    debug_print(f"     - {error}", "WARNING")

                fix_success = fix_simulation_issues(weapon_plan, simulation_results, agent=self)
                if not fix_success:
                    debug_print("  ❌ Automatic fix attempt failed for simulation issues.", "ERROR")
                    break

                debug_print("\n🔄 Re-running simulation tests after fixes...", "INFO")
                simulation_results = run_game_simulation_tests(weapon_plan)
                results["simulation_tests"] = simulation_results

                if not simulation_results.get("has_errors"):
                    debug_print("  ✅ All simulation tests passed!", "INFO")
                    simulation_passed = True
                    break

            if not simulation_passed:
                results["success"] = False
                results["errors"].append("Simulation phase failed. Review detected runtime issues.")
                debug_print("\n❌ Aborting workflow due to unresolved simulation issues.", "ERROR")
                return results

            # Stage 9: Comprehensive AI validation (only after simulation succeeds)
            previous_file_map = self._build_previous_file_map(backup_id, relevant_files)
            debug_print("\n🔬 Running comprehensive AI validation phase...", "INFO")
            max_final_attempts = 10
            final_passed = False
            final_validation = None

            for attempt in range(1, max_final_attempts + 1):
                debug_print(f"\n🔬 Validation attempt {attempt}/{max_final_attempts}", "INFO")
                final_validation = self._comprehensive_ai_validation(
                    weapon_plan,
                    results,
                    previous_file_map=previous_file_map,
                )

                results["final_validation"] = final_validation

                if final_validation.get("all_checks_passed"):
                    debug_print("  ✅ Comprehensive validation passed!", "INFO")
                    final_passed = True
                    break

                remaining_issues = final_validation.get("remaining_issues", [])
                debug_print(f"  ⚠️  {len(remaining_issues)} issues found during comprehensive validation", "WARNING")
                for issue in remaining_issues[:5]:
                    debug_print(f"     - {issue}", "WARNING")

                fix_result = self._comprehensive_ai_fixing(
                    weapon_plan,
                    remaining_issues,
                    previous_file_map=previous_file_map,
                )

                if not fix_result.get("all_fixed"):
                    final_validation["remaining_issues"] = fix_result.get("remaining_issues", remaining_issues)
                    debug_print("  ❌ Comprehensive fix attempt did not resolve all issues.", "ERROR")
                    if attempt == max_final_attempts:
                        break
                else:
                    debug_print("  🔄 Re-running comprehensive validation after fixes...", "INFO")

            if not final_passed:
                results["success"] = False
                results["errors"].append("Comprehensive AI validation failed after automatic fixes.")
                debug_print("\n❌ Aborting workflow due to unresolved comprehensive validation issues.", "ERROR")
                return results

            results["success"] = True

        except Exception as e:
            debug_print(f"\n❌ Workflow failed: {e}", "ERROR")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()

        debug_print("\n" + "="*60, "INFO")
        
        # Ensure required fields are present
        if "weapon_name" not in results and weapon_plan:
            results["weapon_name"] = weapon_plan.get("weapon_name", "Unknown Weapon")
        if "backup_id" not in results:
            results["backup_id"] = backup_id if backup_id else "N/A"
        if "files_created" not in results:
            results["files_created"] = []
        
        return results

    def _build_previous_file_map(self, backup_id: str, files: List[str]) -> Dict[str, str]:
        """Map current file paths to their backup counterparts."""
        if not backup_id:
            return {}

        previous_map: Dict[str, str] = {}
        backup_root = os.path.join(self.backup_dir, backup_id)

        for rel_path in files:
            if not rel_path:
                continue
            previous_path = os.path.join(backup_root, rel_path)
            if os.path.exists(previous_path):
                previous_map[rel_path] = previous_path

        return previous_map

    def _analyze_weapon_requirements(self, weapon_description: str) -> Dict[str, Any]:
        """Analyze weapon requirements and create a plan using AI."""
        debug_print("🤖 Analyzing weapon requirements with AI", "INFO")
        
        if not self._check_request_limit():
            raise Exception("Request limit reached")
        
        analysis_prompt = f"""Analyze this weapon description and create a detailed plan:

WEAPON DESCRIPTION: {weapon_description}

Create a weapon plan with the following structure:
{{
    "weapon_name": "Display Name",
    "weapon_class_name": "ClassName", 
    "effects": [],
    "damage": 10.0,
    "speed": 16.0,
    "ammo_per_shot": 1,
    "description": "Brief description"
}}

Return ONLY valid JSON, no other text."""

        try:
            response = self.active_client.ask_with_tools(
                prompt=analysis_prompt,
                system_prompt=self._combine_system_prompts("You are a game design expert. Analyze weapon requests and create balanced, fun weapon plans.")
            )

            weapon_plan = extract_json_from_text(response)
            if not weapon_plan:
                weapon_plan = {
                    "weapon_name": "Custom Weapon",
                    "weapon_class_name": "CustomWeapon",
                    "effects": [],
                    "damage": 10.0,
                    "speed": 16.0,
                    "ammo_per_shot": 1,
                    "description": weapon_description
                }
            
            return weapon_plan
        except Exception as e:
            debug_print(f"Error analyzing weapon: {e}", "ERROR")
            return {
                "weapon_name": "Custom Weapon",
                "weapon_class_name": "CustomWeapon",
                "effects": [],
                "damage": 10.0,
                "speed": 16.0,
                "ammo_per_shot": 1,
                "description": weapon_description
            }

    def _modify_cow_class_for_effects(self, weapon_plan: Dict[str, Any]) -> bool:
        """Modify Cow class to support weapon effects using AI."""
        debug_print("🔧 Modifying Cow class for effects", "INFO")
        
        effects = weapon_plan.get("effects", [])
        normalized_effects = normalize_effects(effects)
        impact_effects = [effect for effect in normalized_effects if effect["kind"] == "impact"]

        if not impact_effects:
            debug_print("No character effects requiring Cow updates", "DEBUG")
            return False
        
        if not self._check_request_limit():
            return False
        
        effect_lines = []
        for effect in impact_effects:
            effect_lines.append(
                f"- {effect['name']} (slug: {effect['slug']}) => {json.dumps(effect['original'], default=str)}"
            )
        effects_block = "\n".join(effect_lines)

        prompt = f"""Add support for these effects to the Cow class:

Impact Effects:
{effects_block}

Requirements:
1. Call read_file("Game/Character/cow.py", line_count=True) to inspect the existing class.
2. Add or update state variables (self.is_<effect> = False) for each impact effect.
3. Add or update apply_<effect>(self, duration, **kwargs) methods so projectiles can trigger them.
4. Ensure code style matches the file and keep one statement per line.

Use read_file and write_into_file tools for every change."""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
            cow_file = "Game/Character/cow.py"
            if os.path.exists(cow_file):
                content, success = safe_read_file(cow_file)
                if success:
                    fixed_content = fix_same_line_statements(content)
                    if fixed_content != content:
                        debug_print("🧹 Auto-formatting Cow class to remove inline statements", "DEBUG")
                        safe_write_file(cow_file, fixed_content)
            return True
        except Exception as e:
            debug_print(f"Error modifying Cow class: {e}", "ERROR")
            return False

    def _create_weapon_file_with_effects(self, weapon_plan: Dict[str, Any]) -> str:
        """Create weapon file using AI with tools."""
        debug_print("🔨 Creating weapon file", "INFO")
        
        if not self._check_request_limit():
            return None
        
        weapon_class_name = weapon_plan.get("weapon_class_name", "CustomWeapon")
        weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
        normalized_effects = normalize_effects(weapon_plan.get("effects", []))
        effect_lines = [
            f"- {effect['name']} ({effect['kind']}) => {json.dumps(effect['original'], default=str)}"
            for effect in normalized_effects
        ]
        effects_block = "\n".join(effect_lines) if effect_lines else "(no special effects)"

        prompt = f"""Create a weapon class file based on this plan:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

EFFECT SUMMARY:
{effects_block}

🚨 CRITICAL FORMATTING: Each statement MUST be on its own line. NO multiple statements on same line!

REQUIREMENTS:
1. Call read_file("Game/Weapons/weapon.py", line_count=True) to study existing patterns. Read any other relevant files before editing.
2. Create a new weapon class that inherits from Weapon
3. Pass weapon_plan["description"] to the base initializer via the description= parameter
4. Use "placeholder.png" for all images
5. Implement custom fire patterns if needed
6. Save to: {weapon_file}
7. 🚨 MANDATORY: Add factory function at the end:
   def create_{weapon_class_name.lower()}():
       \"\"\"Factory function to create a {weapon_class_name} weapon instance.\"\"\"
       return {weapon_class_name}()

Use read_file to see examples, then write_over_file to create the new weapon."""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
            
            # Post-process: Fix any same-line issues
            if os.path.exists(weapon_file):
                from Agent.Modules.utils import fix_same_line_statements
                content, success = safe_read_file(weapon_file)
                if success:
                    fixed_content = fix_same_line_statements(content)
                    if fixed_content != content:
                        debug_print("🔧 Auto-fixing same-line statements in weapon file", "INFO")
                        safe_write_file(weapon_file, fixed_content)
            
            return weapon_file
        except Exception as e:
            debug_print(f"Error creating weapon file: {e}", "ERROR")
            return None

    def _create_effect_projectile(self, weapon_plan: Dict[str, Any]) -> str:
        """Create projectile file using AI with tools."""
        debug_print("✨ Creating effect projectile", "INFO")
        
        if not self._check_request_limit():
            return None
        
        weapon_class_name = weapon_plan.get("weapon_class_name", "CustomWeapon")
        projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
        normalized_effects = normalize_effects(weapon_plan.get("effects", []))
        effect_lines = [
            f"- {effect['name']} ({effect['kind']}) => {json.dumps(effect['original'], default=str)}"
            for effect in normalized_effects
        ]
        effects_block = "\n".join(effect_lines) if effect_lines else "(no special effects)"

        prompt = f"""Create a projectile class file based on this plan:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

EFFECT SUMMARY:
{effects_block}

🚨 CRITICAL FORMATTING: Each statement MUST be on its own line. NO multiple statements on same line!

REQUIREMENTS:
1. Call read_file("Game/Objects/projectile.py", line_count=True) to study base behaviour before writing.
2. Create projectile class inheriting from Projectile
3. Implement on_character_hit(self, target, arena) method
4. Implement update(self) method (no arena parameter!)
5. Use self.alive = False (never self.kill())
6. Save to: {projectile_file}

Use read_file to see examples, then write_over_file to create the new projectile."""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
            
            # Post-process: Fix any same-line issues
            if os.path.exists(projectile_file):
                from Agent.Modules.utils import fix_same_line_statements
                content, success = safe_read_file(projectile_file)
                if success:
                    fixed_content = fix_same_line_statements(content)
                    if fixed_content != content:
                        debug_print("🔧 Auto-fixing same-line statements in projectile file", "INFO")
                        safe_write_file(projectile_file, fixed_content)
            
            return projectile_file
        except Exception as e:
            debug_print(f"Error creating projectile file: {e}", "ERROR")
            return None

    def _add_weapon_to_loot_pool(self, weapon_plan: Dict[str, Any]) -> bool:
        """Add weapon to Arena loot pool using AI."""
        debug_print("🎮 Adding weapon to loot pool", "INFO")
        
        if not self._check_request_limit():
            return False
        
        weapon_class_name = weapon_plan.get("weapon_class_name", "CustomWeapon")
        
        prompt = f"""Add the {weapon_class_name} weapon to the game's loot pool:

🚨 CRITICAL: You MUST put each statement on its OWN line. NO exceptions!

Steps:
1. Read Game/Arena/arena.py
2. Find the weapons_pool list (around line 275-280)
3. Add import at top: from Game.Weapons.{weapon_class_name.lower()} import {weapon_class_name}
4. Add to weapons_pool list: {weapon_class_name}(),
5. Use write_into_file to update ONLY the specific lines

FORMATTING RULES:
- Each statement on its own line
- NO multiple statements on same line
- NO excessive whitespace between statements
- Preserve exact indentation

Example of WRONG:
```python
pickup = WeaponPickup(weapon, (gx + offset, gy))                    self.objects.append(pickup)  # WRONG!
```

Example of CORRECT:
```python
pickup = WeaponPickup(weapon, (gx + offset, gy))
self.objects.append(pickup)
```

Weapon to add: {weapon_class_name} from Game.Weapons.{weapon_class_name.lower()}"""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
            
            # Post-process: Fix any same-line issues
            arena_file = "Game/Arena/arena.py"
            if os.path.exists(arena_file):
                from Agent.Modules.utils import fix_same_line_statements
                content, success = safe_read_file(arena_file)
                if success:
                    fixed_content = fix_same_line_statements(content)
                    if fixed_content != content:
                        debug_print("🔧 Auto-fixing same-line statements in arena.py", "INFO")
                        safe_write_file(arena_file, fixed_content)
            
            return True
        except Exception as e:
            debug_print(f"Error adding weapon to loot pool: {e}", "ERROR")
            return False

    def _comprehensive_ai_validation(self, weapon_plan: Dict[str, Any], results: Dict[str, Any], previous_file_map: Dict[str, str] = None) -> Dict[str, Any]:
        """Run comprehensive AI validation."""
        debug_print("🤖 AI analyzing all code for potential issues...", "INFO")

        if not self._check_request_limit():
            return {"all_checks_passed": False, "remaining_issues": ["Request limit reached"]}

        previous_file_map = previous_file_map or {}

        weapon_class_name = weapon_plan.get("weapon_class_name", "CustomWeapon")
        weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
        projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"

        current_files = set(results.get("files_created", [])) | set(results.get("files_modified", []))
        if weapon_file:
            current_files.add(weapon_file)
        if os.path.exists(projectile_file):
            current_files.add(projectile_file)
        current_files = sorted(path for path in current_files if path)

        if previous_file_map:
            backup_summary = "\n".join(f"{path} -> {backup_path}" for path, backup_path in previous_file_map.items())
        else:
            backup_summary = "No backup snapshots available for comparison."

        prompt = f"""Thoroughly validate the weapon implementation:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

FILES CREATED:
{json.dumps(results.get('files_created', []), indent=2)}

CURRENT FILES TO REVIEW:
{json.dumps(current_files, indent=2)}

BACKUP SNAPSHOTS:
{backup_summary}

Read both the current files and any provided backup versions (use read_file on the backup paths) and check:
1. Correct imports and dependencies
2. Proper method signatures
3. Image references use placeholder.png
4. No syntax errors or runtime regressions
5. Behaviours remain consistent with previous implementation unless intentionally changed

Report any issues found."""

        try:
            from Agent.Prompts.system_prompts import system_prompt_comprehensive_validation
            response = self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(system_prompt_comprehensive_validation)
            )

            if "PASSED" in response or "all validation checks" in response.lower():
                return {"all_checks_passed": True, "remaining_issues": []}
            else:
                issues = [line.strip() for line in response.split('\n') if line.strip() and not line.startswith('#')]
                return {"all_checks_passed": False, "remaining_issues": issues[:5]}
        except Exception as e:
            debug_print(f"Error in comprehensive validation: {e}", "ERROR")
            return {"all_checks_passed": False, "remaining_issues": [str(e)]}

    def _comprehensive_ai_fixing(self, weapon_plan: Dict[str, Any], issues: List[str], previous_file_map: Dict[str, str] = None) -> Dict[str, Any]:
        """Run comprehensive AI fixing."""
        debug_print("🤖 AI fixing issues...", "INFO")

        if not self._check_request_limit():
            return {"all_fixed": False, "remaining_issues": issues}

        previous_file_map = previous_file_map or {}
        if previous_file_map:
            backup_summary = "\n".join(f"{path} -> {backup_path}" for path, backup_path in previous_file_map.items())
        else:
            backup_summary = "No backup snapshots available for comparison."

        prompt = f"""Fix these issues in the weapon implementation:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

ISSUES TO FIX:
{chr(10).join(f"{i+1}. {issue}" for i, issue in enumerate(issues))}

BACKUP SNAPSHOTS:
{backup_summary}

Use read_file and write_into_file to fix each issue. When a backup path is provided, compare the backup and current versions before applying changes to avoid regressions."""

        try:
            from Agent.Prompts.system_prompts import system_prompt_comprehensive_fixing
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(system_prompt_comprehensive_fixing)
            )
            return {"all_fixed": True, "remaining_issues": []}
        except Exception as e:
            debug_print(f"Error in comprehensive fixing: {e}", "ERROR")
            return {"all_fixed": False, "remaining_issues": issues}
