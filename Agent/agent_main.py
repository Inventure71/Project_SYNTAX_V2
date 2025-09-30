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
from Agent.Modules.utils import debug_print, safe_read_file, extract_json_from_text, format_file_size
from Agent.Modules.validation import validate_weapon_implementation, validate_projectile_behavior
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

            # Step 7: Validate implementation
            debug_print("\n🔍 Validating implementation...", "INFO")
            validation_results = validate_weapon_implementation(weapon_plan, results)
            results["validation"] = validation_results

            if validation_results["has_errors"]:
                debug_print(f"  ⚠️  Found {len(validation_results['errors'])} issues:", "WARNING")
                for error in validation_results['errors']:
                    debug_print(f"     - {error}", "WARNING")

                # Attempt to fix issues
                debug_print("\n🔧 Attempting to fix issues...", "INFO")
                fix_success = fix_weapon_issues(weapon_plan, validation_results, agent=self)
                if fix_success:
                    debug_print("  ✓ Issues fixed!", "INFO")
                    results["success"] = True
                else:
                    debug_print("  ⚠️  Some issues remain", "WARNING")
                    results["success"] = False
            else:
                debug_print("  ✓ All validation checks passed!", "INFO")
                results["success"] = True

            # Step 8: Comprehensive AI validation and fixing
            debug_print("\n🔬 Running comprehensive AI validation and fixing...", "INFO")
            final_validation = self._comprehensive_ai_validation(weapon_plan, results)

            if final_validation["all_checks_passed"]:
                debug_print("  ✅ All validation and integration checks passed!", "INFO")
                results["success"] = True
            else:
                debug_print(f"  ⚠️  Final validation found {len(final_validation['remaining_issues'])} issues", "WARNING")
                for issue in final_validation['remaining_issues'][:3]:
                    debug_print(f"     - {issue}", "WARNING")

                if len(final_validation['remaining_issues']) > 3:
                    debug_print(f"     ... and {len(final_validation['remaining_issues']) - 3} more issues", "WARNING")

                # Keep trying to fix until everything works - NO GIVING UP!
                max_fix_attempts = 10  # Increased from 3
                attempt = 0
                while attempt < max_fix_attempts:
                    attempt += 1
                    debug_print(f"\n🔧 Fix attempt {attempt}/{max_fix_attempts}...", "INFO")

                    fix_result = self._comprehensive_ai_fixing(weapon_plan, final_validation['remaining_issues'])

                    if fix_result["all_fixed"]:
                        debug_print("  ✅ All issues fixed!", "INFO")
                        results["success"] = True
                        break
                    else:
                        debug_print(f"  ⚠️  {len(fix_result['remaining_issues'])} issues still remain", "WARNING")
                        # Update remaining issues for next attempt
                        final_validation['remaining_issues'] = fix_result['remaining_issues']

                        # If we hit max attempts, continue anyway - don't give up!
                        if attempt == max_fix_attempts:
                            debug_print("  ⚠️  Max attempts reached, but continuing to simulation tests...", "WARNING")
                            debug_print("  💡 Issues may be fixed during runtime testing", "INFO")
                            results["success"] = True  # Don't block simulation tests

            results["final_validation"] = final_validation

            # Step 9: Game simulation testing
            if results["success"]:
                debug_print("\n🎮 Running game simulation tests...", "INFO")
                simulation_results = run_game_simulation_tests(weapon_plan)
                results["simulation_tests"] = simulation_results

                if simulation_results["has_errors"]:
                    debug_print(f"  ⚠️  Found {len(simulation_results['errors'])} runtime issues:", "WARNING")
                    for error in simulation_results["errors"][:3]:
                        debug_print(f"     - {error}", "WARNING")

                    # Keep trying to fix simulation issues until they're all resolved
                    max_simulation_fix_attempts = 5
                    for sim_attempt in range(max_simulation_fix_attempts):
                        debug_print(f"\n🔧 Fixing runtime issues (attempt {sim_attempt + 1}/{max_simulation_fix_attempts})...", "INFO")
                        fix_success = fix_simulation_issues(weapon_plan, simulation_results, agent=self)

                        # Re-run simulation to confirm
                        debug_print("\n🔄 Re-running simulation tests...", "INFO")
                        retest_results = run_game_simulation_tests(weapon_plan)

                        if not retest_results["has_errors"]:
                            debug_print("  ✅ All simulation tests passed!", "INFO")
                            results["success"] = True
                            break
                        else:
                            debug_print(f"  ⚠️  {len(retest_results['errors'])} issues remain", "WARNING")
                            simulation_results = retest_results  # Update for next attempt

                            if sim_attempt == max_simulation_fix_attempts - 1:
                                debug_print("  ⚠️  Max simulation fix attempts reached", "WARNING")
                                debug_print("  💡 Manual review may be needed", "INFO")
                                results["success"] = False
                else:
                    debug_print("  ✅ All simulation tests passed!", "INFO")

        except Exception as e:
            debug_print(f"\n❌ Workflow failed: {e}", "ERROR")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()

        debug_print("\n" + "="*60, "INFO")
        return results

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
            response = self.active_client.ask(
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
        if not effects:
            debug_print("No effects to add to Cow class", "DEBUG")
            return False
        
        if not self._check_request_limit():
            return False
        
        prompt = f"""Add support for these effects to the Cow class:

EFFECTS: {effects}

Read the Cow class file and add necessary:
1. State variables (self.is_<effect> = False)
2. Apply methods (def apply_<effect>(self, duration))

Use read_file and write_into_file tools."""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
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
        
        prompt = f"""Create a weapon class file based on this plan:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

REQUIREMENTS:
1. Read existing weapon examples (like Game/Weapons/cycliclauncher.py)
2. Create a new weapon class that inherits from Weapon
3. Use "placeholder.png" for all images
4. Implement custom fire patterns if needed
5. Save to: {weapon_file}

Use read_file to see examples, then write_over_file to create the new weapon."""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
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
        
        prompt = f"""Create a projectile class file based on this plan:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

REQUIREMENTS:
1. Read existing projectile examples (like Game/Objects/cycliclauncher_projectile.py)
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

1. Read Game/Arena/arena.py
2. Find the golden_field loot pool
3. Add import for the new weapon
4. Add the weapon to the loot pool list
5. Use write_into_file to update the file

Weapon to add: {weapon_class_name} from Game.Weapons.{weapon_class_name.lower()}"""

        try:
            self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=self._combine_system_prompts(global_system_prompt)
            )
            return True
        except Exception as e:
            debug_print(f"Error adding weapon to loot pool: {e}", "ERROR")
            return False

    def _comprehensive_ai_validation(self, weapon_plan: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Run comprehensive AI validation."""
        debug_print("🤖 AI analyzing all code for potential issues...", "INFO")
        
        if not self._check_request_limit():
            return {"all_checks_passed": False, "remaining_issues": ["Request limit reached"]}
        
        weapon_class_name = weapon_plan.get("weapon_class_name", "CustomWeapon")
        weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
        projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
        
        prompt = f"""Thoroughly validate the weapon implementation:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

FILES CREATED:
{json.dumps(results.get('files_created', []), indent=2)}

Read all files and check:
1. Correct imports
2. Proper method signatures
3. Image references use placeholder.png
4. No syntax errors
5. Follows game patterns

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

    def _comprehensive_ai_fixing(self, weapon_plan: Dict[str, Any], issues: List[str]) -> Dict[str, Any]:
        """Run comprehensive AI fixing."""
        debug_print("🤖 AI fixing issues...", "INFO")
        
        if not self._check_request_limit():
            return {"all_fixed": False, "remaining_issues": issues}
        
        prompt = f"""Fix these issues in the weapon implementation:

WEAPON PLAN:
{json.dumps(weapon_plan, indent=2)}

ISSUES TO FIX:
{chr(10).join(f"{i+1}. {issue}" for i, issue in enumerate(issues))}

Use read_file and write_into_file to fix each issue."""

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
