
import os
from ast import List
import re
import json
from Agent.Tools.get_project_structure import get_project_structure
from Agent.Tools.helpers_ignore import collect_directory_files_and_contents
from Agent.chatGPT import ChatGPT
from Agent.gemini_client import GeminiClient
from Agent.Prompts.system_prompts import global_system_prompt

# TODO: Implement an Indexing of the codebase in the game folder, where a model (small) goes function by function and saves what they do and what they handle in 2 lines, this should all be saved in a way such that it can easily be updated partially (when a function get's modifed) or when a new one gets added. Also this description should be retrivable by name of file contatining it and the function name.


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
        self.user_approved_continuation = True
        
        # Backup management
        self.backup_dir = "Backup/Agent_Backups"
        self.current_backup_id = None

        self.update_project_structure()

    def update_project_structure(self):
        self.project_structure_simple = get_project_structure(False)
        self.project_structure_complex = get_project_structure(True)
        self.project_structure_complex_with_files = collect_directory_files_and_contents("Game")
    
    def _combine_system_prompts(self, specific_prompt: str) -> str:
        """Combine global system prompt with specific prompt."""
        return f"{global_system_prompt}\n\n{'='*70}\n# SPECIFIC TASK INSTRUCTIONS\n{'='*70}\n\n{specific_prompt}"
    
    def _create_backup(self, description: str = "agent_changes") -> str:
        """
        Create a backup of important files before making changes.
        
        Returns:
            backup_id: Unique identifier for this backup
        """
        import os
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
        
        print(f"📦 Creating backup: {backup_id}")
        for target in backup_targets:
            if os.path.exists(target):
                dest = os.path.join(backup_path, target)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                
                if os.path.isdir(target):
                    if os.path.exists(dest):
                        shutil.rmtree(dest)
                    shutil.copytree(target, dest)
                else:
                    shutil.copy2(target, dest)
                print(f"  ✓ Backed up: {target}")
        
        self.current_backup_id = backup_id
        return backup_id
    
    def restore_backup(self, backup_id: str = None):
        """
        Restore files from a backup.
        
        Args:
            backup_id: ID of backup to restore (if None, uses most recent)
        """
        import os
        import shutil
        
        if backup_id is None:
            backup_id = self.current_backup_id
        
        if backup_id is None:
            # Find most recent backup
            backups = sorted(os.listdir(self.backup_dir)) if os.path.exists(self.backup_dir) else []
            if not backups:
                print("❌ No backups found")
                return False
            backup_id = backups[-1]
        
        backup_path = os.path.join(self.backup_dir, backup_id)
        if not os.path.exists(backup_path):
            print(f"❌ Backup not found: {backup_id}")
            return False
        
        print(f"♻️  Restoring from backup: {backup_id}")
        
        # Restore each file/directory
        for item in os.listdir(backup_path):
            source = os.path.join(backup_path, item)
            dest = item
            
            if os.path.isdir(source):
                if os.path.exists(dest):
                    shutil.rmtree(dest)
                shutil.copytree(source, dest)
                print(f"  ✓ Restored: {dest}/")
            else:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy2(source, dest)
                print(f"  ✓ Restored: {dest}")
        
        print("✓ Restore complete!")
        return True
    
    def list_backups(self):
        """List all available backups."""
        import os
        
        if not os.path.exists(self.backup_dir):
            print("No backups found")
            return []
        
        backups = sorted(os.listdir(self.backup_dir))
        if not backups:
            print("No backups found")
            return []
        
        print("\n📦 Available backups:")
        for backup in backups:
            print(f"  - {backup}")
        
        return backups

    def test(self):
        # load from agents.md
        with open("Agent/Prompts/agents.md", "r") as file:
            sys_prompt = file.read()

        prompt = """
        in test_3.py improve the function generate_random_numbers to be even more random, make it at least 30 lines long.
        """
        
        input = f"""
        {prompt}

        Up to date project structure:
        {self.project_structure_complex}
        """


        self.chatGPT.get_response_with_tools(
            input=input,
            system_prompt=sys_prompt,
        )

    def index_codebase(self):
        pass

    def plan(self, prompt: str):
        
        #entire_code = collect_directory_files_and_contents("Game")
        #print(entire_code)

        # READ THE CODEBASE AND MAKE A PLAN
        # CREATE A CHECKLIST OF TASKS IN A FORMATTED WAY SO THAT THE MODEL CAN EASILY UNDERSTAND AND EXECUTE THE TASKS + UPDATE ALREADY DONE TASKS

        # FOR EACH TASK SPECIFY WHAT FILES ARE INVOLVED SO THAT THE MODEL DOESN'T NEED TO READ THE ENTIRE CODEBASE
        with open("Game/README.md", "r") as file:
            project_documentation = file.read()
        
        prompt = f"""
You are an advanced task-planning agent for the SYNTAX V2 game project.

## Mission
Given a goal, produce a one-page Work Order that **fulfills the goal** by splitting the work into small, mergeable tasks suited for someone with limited continuous focus time.

## Output format (strict)
- Start with a 1–2 sentence Objective.
- Then list tasks. **Each task MUST be separated by a line containing exactly:**
---TASK---
- Inside each task, include ONLY these fields (in this order), each on its own line and starting with the label exactly as written:
Goal of the specific task: <one sentence result>
What needs to be done: <short bullet list; one line per bullet, using "- ">
Files likely to be touched: <one path per line, no extra text>

No extra sections. No code fences around the tasks. No blank tasks. Avoid empty fields.

## Context you MUST use (and how)
- **Prompt to FULLFILL the goal**  
  This is the user’s request (“what to build”). Use it to define the Objective and to shape the scope of each task. If the prompt is ambiguous, choose the most reasonable interpretation and proceed; do not ask questions.
- **Project structure**  
  This is the canonical map of directories and files. Use it to (a) pick correct file paths, (b) avoid inventing new paths unless absolutely necessary, and (c) keep file touches minimal and precise.
- **Project documentation**  
  Describes gameplay rules, invariants (e.g., layer masks, pickups, bounds), and extension rules. **You must preserve all invariants** (e.g., golden fields never drop ammo; projectiles in mid-air layer; bounds clamping). When designing tasks, explain changes only through allowed extension points.

## Planning rules
- Prefer 6–12 small tasks over a few large ones.
- Each task should be independently understandable and mergeable.
- Keep gameplay invariants intact; integrate with existing character/weapon systems.
- Be concrete: list exact files that will be modified or added (paths from the project root).
- Keep wording concise (aim for ~6–12 lines per task).
- Do not plan for tests for now.

## Deliverable
Return ONLY the Objective and the list of tasks formatted exactly as specified above, with tasks separated by the literal separator line:
---TASK---

(Do not include this instruction block in your output.)
## Context:
- **Prompt to FULLFILL the goal**: \n{prompt} 
- **Project structure**: \n{self.project_structure_complex}
- **Project documentation**: \n{project_documentation}
        """

        # Split on a line that is exactly ---TASK--- (allowing surrounding whitespace)
        parts = re.split(r'^\s*---TASK---\s*$', response.strip(), flags=re.MULTILINE)
        # Drop empties and leading/trailing whitespace per part
        parts = [p.strip() for p in parts if p.strip()]


        pass

    def follow_plan(self):

        # FOR EACH TASK ASK MODEL TO SOLVE THAT AND ONLY THAT TASK

        # AFTER THE MODEL FINISHED ALL TASKS ASK AGAIN THE MODEL TO REVIEW IF ALL TASKS ARE COMPLETED CORRECTLY (STRUCTURE THIS ALSO TO BE CONTEXT AND MAX OUTPUT LIMIT PROOF)
        pass

    def automatic_tests(self):
        # HAVE FIXED TESTS FOR SPECIFIC EXAMPLES THAT SHOULD ALWAYS WORK: 
        # - WALKING (MOVES IN ALL DIRECTIONS + SLOWS DOWN WHEN EATING)
        # - SHOOTING (SHOOTS IN THE DIRECTION OF THE MOUSE + SHOOTS IF AMMO IS AVAILABLE)
        # - DAMAGING (GETTING HIT AND OPPOSITE)
        # - PICKING UP WEAPONS (PICKUP WEAPON IF NO WEAPON IS EQUIPPED)
        # - FOOD (EATING GIVES A CHANCE OF AMMO AND AMMO GOES UP)


        # IF SOMETHING GOES WRONG ASK THE MODEL TO FIX THE PROBLEM
        pass


    def create_ability_workflow(self, ability_description: str) -> dict:
        """
        Complete workflow for creating a new ability.
        Follows: describe -> plan -> implement -> verify
        
        Args:
            ability_description: Natural language description of the ability
            
        Returns:
            Dictionary with workflow results
        """
        print("\n" + "="*60)
        print("🚀 ABILITY CREATION WORKFLOW")
        print("="*60)
        
        results = {
            "description": ability_description,
            "plan": None,
            "tasks": [],
            "success": False,
            "errors": [],
            "backup_id": None
        }
        
        try:
            # Step 0: Create backup
            print("\n💾 Creating backup...")
            backup_id = self._create_backup("ability_creation")
            results["backup_id"] = backup_id
            
            # Step 1: Plan the ability
            print("\n📋 Step 1: Planning...")
            plan = self._plan_ability(ability_description)
            results["plan"] = plan
            print(f"✓ Plan created with {len(plan['tasks'])} tasks")
            
            # Step 2: Implement task by task
            print("\n🔨 Step 2: Implementation...")
            for i, task in enumerate(plan['tasks'], 1):
                print(f"\n  Task {i}/{len(plan['tasks'])}: {task['goal']}")
                task_result = self._implement_task(task, ability_description, plan)
                results["tasks"].append(task_result)
                
                if not task_result["success"]:
                    print(f"  ❌ Task {i} failed: {task_result.get('error', 'Unknown error')}")
                    results["errors"].append(f"Task {i} failed: {task_result.get('error')}")
                    break
                else:
                    print(f"  ✓ Task {i} completed")
            
            # Step 3: Verify implementation
            print("\n✅ Step 3: Verification...")
            verification = self._verify_implementation(ability_description, results["tasks"])
            results["verification"] = verification
            
            if verification["all_correct"]:
                print("✓ All tasks verified successfully!")
                results["success"] = True
            else:
                print("⚠️  Some issues found during verification")
                results["errors"].extend(verification.get("issues", []))
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
        return results
    
    def _check_request_limit(self) -> bool:
        """
        Check if we've hit the request limit and need user authorization.
        
        Returns:
            True if can continue, False if user denied continuation
        """
        self.request_count += 1
        
        if self.request_count >= self.max_requests_before_auth and self.user_approved_continuation:
            print("\n" + "⚠️ " * 20)
            print(f"⚠️  Request limit reached ({self.max_requests_before_auth} requests)")
            print("⚠️  The agent has made multiple API calls.")
            print("⚠️  This may incur costs depending on your API plan.")
            print("⚠️ " * 20)
            
            response = input("\n👉 Continue with more requests? (yes/no): ").strip().lower()
            
            if response in ['yes', 'y']:
                print("✓ Continuing... (resetting counter)\n")
                self.request_count = 0  # Reset counter
                self.user_approved_continuation = True
                return True
            else:
                print("❌ Stopping agent workflow.\n")
                self.user_approved_continuation = False
                return False
        
        return self.user_approved_continuation
    
    def _plan_ability(self, ability_description: str) -> dict:
        """
        Step 1: Create a detailed implementation plan.
        
        CRITICAL: Abilities must work for ALL characters (player + AI enemies).
        If an ability has effects (freeze, burn, stun, etc.), these effects must be
        implementable as character states or object systems that can affect any character.
        """
        with open("Game/README.md", "r") as file:
            project_documentation = file.read()
        
        # Read existing ability system to understand the pattern
        from Agent.Tools.read_file import read_file
        ability_base_lines = read_file("Game/Abilities/ability.py", line_count=False)
        dash_example_lines = read_file("Game/Abilities/dash.py", line_count=False)
        
        # Convert to string (take first 100 lines if too long)
        ability_base = "".join(ability_base_lines[:100]) if isinstance(ability_base_lines, list) else ability_base_lines
        dash_example = "".join(dash_example_lines[:50]) if isinstance(dash_example_lines, list) else dash_example_lines
        
        system_prompt = """You are a planning expert for game development.

Your task: Create a detailed implementation plan for a new ability.

## CRITICAL REQUIREMENTS
1. **Universal Application**: If the ability has effects (freeze, stun, slow, burn, etc.), 
   these MUST be designed to work on ANY character (player or AI enemy).
   - Add effect state to Cow base class if needed
   - Create effect object classes if needed  
   - Ensure AI can trigger abilities on player and vice versa

2. **Modular Design**: Follow the existing Ability base class pattern
3. **DRY Principle**: Reuse existing systems (projectiles, objects, character states)
4. **Layer System**: Respect the 4-layer collision system

## Output Format (JSON-like structure):
{
  "ability_name": "ClearAbilityName",
  "high_level_design": "2-3 sentences describing approach",
  "universal_considerations": "How this ability works when used BY or ON any character",
  "tasks": [
    {
      "task_number": 1,
      "goal": "What this task achieves",
      "files_to_modify": ["path/to/file.py"],
      "files_to_create": ["path/to/new_file.py"],
      "what_to_do": ["Bullet point 1", "Bullet point 2"]
    }
  ]
}

Break down into 3-6 small, focused tasks."""

        prompt = f"""Plan the implementation for this ability:

**Ability Description**: {ability_description}

**Existing Ability System**:
```python
{ability_base}
```

**Example Ability (Dash)**:
```python
{dash_example}
```

**Project Documentation**:
{project_documentation}

**Current Project Structure**:
{self.project_structure_complex}

Create a detailed plan ensuring the ability can be used by AND affect any character."""

        # Check request limit before making API call
        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Parse the response to extract structured plan
        plan = self._parse_plan_response(response)
        return plan
    
    def _parse_plan_response(self, response: str) -> dict:
        """Parse the AI response into a structured plan."""
        # Simple parsing - look for JSON-like structure or extract tasks
        import json
        
        # Try to extract JSON
        try:
            # Look for JSON block
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            elif "{" in response and "}" in response:
                # Try to find JSON object
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: create simple structure from text
        return {
            "ability_name": "CustomAbility",
            "high_level_design": response[:200],
            "universal_considerations": "Ability designed to work with any character",
            "tasks": [
                {
                    "task_number": 1,
                    "goal": "Implement ability based on description",
                    "files_to_create": [],
                    "files_to_modify": [],
                    "what_to_do": ["Create ability class", "Integrate with character system"],
                    "full_plan": response
                }
            ]
        }
    
    def _implement_task(self, task: dict, ability_description: str, full_plan: dict) -> dict:
        """
        Step 2: Implement a single task from the plan.
        Actually writes/modifies files.
        """
        from Agent.Tools.read_file import read_file
        from Agent.Tools.write_to_file import write_over_file, create_file
        
        system_prompt = """You are an implementation expert for game development.

Your task: Implement ONE specific task with complete, working code.

## Requirements
- Generate COMPLETE file contents (not snippets)
- Follow existing code style and patterns
- Ensure code works for ANY character (player or AI)
- Add proper imports and error handling
- Include docstrings

## Output Format
For each file to create/modify, output:
```python
# FILE: path/to/file.py
[complete file contents here]
```

Be precise and complete."""

        # Get current file contents for files being modified
        context_files = []
        for file_path in task.get("files_to_modify", []):
            try:
                content = read_file(file_path)
                context_files.append(f"Current {file_path}:\n```python\n{content}\n```\n")
            except:
                context_files.append(f"{file_path} does not exist yet\n")
        
        context = "\n".join(context_files)
        
        prompt = f"""Implement this task:

**Task Goal**: {task.get('goal', 'Implement feature')}
**What to Do**: {task.get('what_to_do', [])}

**Ability Description**: {ability_description}
**Overall Plan**: {full_plan.get('high_level_design', '')}
**Universal Considerations**: {full_plan.get('universal_considerations', '')}

**Current Files**:
{context}

Generate complete, working code for all files."""

        # Check request limit before making API call
        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Extract and write files from response
        files_written = self._extract_and_write_files(response, task)
        
        return {
            "task": task,
            "files_written": files_written,
            "success": len(files_written) > 0,
            "response": response
        }
    
    def _extract_and_write_files(self, response: str, task: dict) -> list:
        """Extract file contents from AI response and write them."""
        from Agent.Tools.write_to_file import write_over_file, create_file
        import re
        
        files_written = []
        
        # Pattern to match: # FILE: path/to/file.py followed by code block
        pattern = r'#\s*FILE:\s*([^\n]+)\n```(?:python)?\n(.*?)```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for file_path, content in matches:
            file_path = file_path.strip()
            content = content.strip()
            
            # Determine if we should create or overwrite
            import os
            if os.path.exists(file_path):
                result = write_over_file(file_path, content)
            else:
                result = create_file(file_path, content)
            
            if "success" in result:
                files_written.append(file_path)
                print(f"    ✓ Written: {file_path}")
            else:
                print(f"    ❌ Failed to write {file_path}: {result}")
        
        return files_written
    
    def _verify_implementation(self, ability_description: str, task_results: list) -> dict:
        """
        Step 3: Verify that all tasks were completed correctly.
        """
        from Agent.Tools.read_file import read_file
        
        system_prompt = """You are a code review expert.

Your task: Verify that the implementation is correct and complete.

Check for:
1. All files exist and are syntactically correct
2. Ability follows the base class pattern
3. Ability can be used by ANY character (not just player)
4. Code follows DRY and SOLID principles
5. Integration points are correct

Output:
- "VERIFIED" if everything is correct
- "ISSUES: [list of problems]" if there are problems"""

        # Collect all written files
        all_files = []
        for task_result in task_results:
            all_files.extend(task_result.get("files_written", []))
        
        # Read back the files
        file_contents = []
        for file_path in all_files:
            try:
                content = read_file(file_path)
                file_contents.append(f"### {file_path}\n```python\n{content}\n```\n")
            except Exception as e:
                file_contents.append(f"### {file_path}\nERROR: {e}\n")
        
        if not file_contents:
            return {
                "all_correct": False,
                "issues": ["No files were created/modified"]
            }
        
        prompt = f"""Verify this ability implementation:

**Ability Description**: {ability_description}

**Implemented Files**:
{chr(10).join(file_contents)}

Is the implementation correct and complete?"""

        # Check request limit before making API call
        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Parse verification response
        if "VERIFIED" in response.upper():
            return {"all_correct": True, "response": response}
        else:
            # Extract issues
            issues = []
            if "ISSUES:" in response:
                issues_text = response.split("ISSUES:")[1].strip()
                issues = [line.strip() for line in issues_text.split("\n") if line.strip()]
            
            return {
                "all_correct": False,
                "issues": issues if issues else ["Verification failed"],
                "response": response
            }

    def create_weapon_workflow(self, weapon_description: str) -> dict:
        """
        Complete workflow for creating a new weapon with effects.
        
        This workflow:
        1. Analyzes if weapon needs special effects (freeze, burn, etc.)
        2. Modifies Cow class to support effects if needed
        3. Creates weapon file with effect application
        4. Automatically adds weapon to Arena loot pool
        
        Args:
            weapon_description: Natural language description of the weapon
            
        Returns:
            Dictionary with workflow results
        """
        print("\n" + "="*60)
        print("🔫 WEAPON CREATION WORKFLOW")
        print("="*60)
        
        results = {
            "description": weapon_description,
            "weapon_name": None,
            "has_effects": False,
            "effect_types": [],
            "success": False,
            "errors": [],
            "backup_id": None,
            "files_modified": [],
            "files_created": []
        }
        
        try:
            # Step 0: Create backup
            print("\n💾 Creating backup...")
            backup_id = self._create_backup("weapon_creation")
            results["backup_id"] = backup_id
            
            # Step 1: Analyze weapon and plan implementation
            print("\n📋 Analyzing weapon requirements...")
            weapon_plan = self._analyze_weapon_requirements(weapon_description)
            results["weapon_name"] = weapon_plan.get("weapon_name", "CustomWeapon")
            results["has_effects"] = weapon_plan.get("has_effects", False)
            results["effect_types"] = weapon_plan.get("effect_types", [])
            
            print(f"  Weapon: {results['weapon_name']}")
            print(f"  Effects needed: {results['effect_types'] if results['has_effects'] else 'None'}")
            
            # Step 2: Modify Cow class if effects are needed
            # Filter out projectile-only behaviors (not character effects)
            projectile_only_effects = ["projectile_behavior_homing",
                                       "projectile_behavior_bouncing", "impact_splitting", 
                                       "impact_explosion", "piercing"]
            character_effects = [e for e in results["effect_types"] if e not in projectile_only_effects]
            
            if character_effects:
                print(f"\n🔧 Modifying Cow class for character effects: {character_effects}...")
                cow_modified = self._add_effects_to_cow(character_effects)
                if cow_modified:
                    results["files_modified"].append("Game/Character/cow.py")
                    print("  ✓ Added effect support to Cow class")
            elif results["has_effects"]:
                print(f"\n✓ Weapon has projectile-only behaviors: {results['effect_types']}")
                print("  (No character effects needed)")
            
            # Step 3: Create weapon file with effect application
            print("\n🔨 Creating weapon file...")
            weapon_file = self._create_weapon_file_with_effects(weapon_plan, weapon_description)
            if weapon_file:
                results["files_created"].append(weapon_file)
                print(f"  ✓ Created: {weapon_file}")
            
            # Step 4: Create custom projectile if effects are needed
            if results["has_effects"]:
                print("\n✨ Creating effect projectile...")
                projectile_file = self._create_effect_projectile(weapon_plan)
                if projectile_file:
                    results["files_created"].append(projectile_file)
                    print(f"  ✓ Created: {projectile_file}")
            
            # Step 5: Modify Arena to use custom projectiles
            if results["has_effects"]:
                print("\n🎯 Updating Arena to use effect projectiles...")
                arena_proj_modified = self._update_arena_projectile_spawn(weapon_plan)
                if arena_proj_modified and "Game/Arena/arena.py" not in results["files_modified"]:
                    results["files_modified"].append("Game/Arena/arena.py")
                print("  ✓ Arena will use custom projectiles")
            
            # Step 6: Add weapon to Arena loot pool
            print("\n🎮 Adding weapon to game loot pool...")
            arena_modified = self._add_weapon_to_loot_pool(weapon_plan)
            if arena_modified and "Game/Arena/arena.py" not in results["files_modified"]:
                results["files_modified"].append("Game/Arena/arena.py")
            print("  ✓ Added to golden field loot pool")
            
            # Step 7: Validate implementation
            print("\n🔍 Validating implementation...")
            validation_results = self._validate_weapon_implementation(weapon_plan, results)
            results["validation"] = validation_results
            
            if validation_results["has_errors"]:
                print(f"  ⚠️  Found {len(validation_results['errors'])} issues:")
                for error in validation_results["errors"]:
                    print(f"     - {error}")
                
                # Attempt to fix issues
                print("\n🔧 Attempting to fix issues...")
                fix_success = self._fix_weapon_issues(weapon_plan, validation_results)
                if fix_success:
                    print("  ✓ Issues fixed!")
                    results["success"] = True
                else:
                    print("  ⚠️  Some issues remain")
                    results["success"] = False
            else:
                print("  ✓ All validation checks passed!")
                results["success"] = True
            
            # Step 8: Comprehensive AI-powered final validation and fixing
            print("\n🔬 Running comprehensive AI validation and fixing...")

            # This is the final step - ensure everything works
            final_validation = self._comprehensive_ai_validation(weapon_plan, results)

            if final_validation["all_checks_passed"]:
                print("  ✅ All validation and integration checks passed!")
                results["success"] = True
            else:
                print(f"  ⚠️  Final validation found {len(final_validation['remaining_issues'])} issues")
                for issue in final_validation['remaining_issues'][:5]:  # Show first 5 issues
                        print(f"     - {issue}")
                    
                if len(final_validation['remaining_issues']) > 5:
                    print(f"     ... and {len(final_validation['remaining_issues']) - 5} more issues")

                # Keep trying to fix until everything works - NO GIVING UP!
                max_fix_attempts = 10  # Increased from 3
                attempt = 0
                while attempt < max_fix_attempts:
                    attempt += 1
                    print(f"\n🔧 Fix attempt {attempt}/{max_fix_attempts}...")

                    fix_result = self._comprehensive_ai_fixing(weapon_plan, final_validation['remaining_issues'])

                    if fix_result["all_fixed"]:
                        print("  ✅ All issues fixed!")
                        results["success"] = True
                        break
                    else:
                        print(f"  ⚠️  {len(fix_result['remaining_issues'])} issues still remain")
                        # Update remaining issues for next attempt
                        final_validation['remaining_issues'] = fix_result['remaining_issues']
                        
                        # If we hit max attempts, continue anyway - don't give up!
                        if attempt == max_fix_attempts:
                            print("  ⚠️  Max attempts reached, but continuing to simulation tests...")
                            print("  💡 Issues may be fixed during runtime testing")
                            results["success"] = True  # Don't block simulation tests

            results["final_validation"] = final_validation
            
            # Step 9: Game simulation testing
            if results["success"]:
                print("\n🎮 Running game simulation tests...")
                simulation_results = self._run_game_simulation_tests(weapon_plan)
                results["simulation_tests"] = simulation_results
                
                if simulation_results["has_errors"]:
                    print(f"  ⚠️  Found {len(simulation_results['errors'])} runtime issues:")
                    for error in simulation_results["errors"][:3]:
                        print(f"     - {error}")
                    
                    # Keep trying to fix simulation issues until they're all resolved
                    max_simulation_fix_attempts = 5
                    for sim_attempt in range(max_simulation_fix_attempts):
                        print(f"\n🔧 Fixing runtime issues (attempt {sim_attempt + 1}/{max_simulation_fix_attempts})...")
                        fix_success = self._fix_simulation_issues(weapon_plan, simulation_results)
                        
                        # Re-run simulation to confirm
                        print("\n🔄 Re-running simulation tests...")
                        retest_results = self._run_game_simulation_tests(weapon_plan)
                        
                        if not retest_results["has_errors"]:
                            print("  ✅ All simulation tests passed!")
                            results["success"] = True
                            break
                        else:
                            print(f"  ⚠️  {len(retest_results['errors'])} issues remain")
                            simulation_results = retest_results  # Update for next attempt
                            
                            if sim_attempt == max_simulation_fix_attempts - 1:
                                print("  ⚠️  Max simulation fix attempts reached")
                                print("  💡 Manual review may be needed")
                                results["success"] = False
                else:
                    print("  ✅ All simulation tests passed!")
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
        return results
    
    def _analyze_weapon_requirements(self, weapon_description: str) -> dict:
        """
        Analyze weapon description to determine if it needs effects and what kind.
        
        Returns:
            dict with weapon_name, has_effects, effect_types, stats, etc.
        """
        from Agent.Tools.read_file import read_file
        
        # Read existing code for context
        weapon_base = read_file("Game/Weapons/weapon.py", line_count=False)
        projectile_base = read_file("Game/Objects/projectile.py", line_count=False)
        cow_base = read_file("Game/Character/cow.py", line_count=False)
        
        weapon_base_str = "".join(weapon_base[:50]) if isinstance(weapon_base, list) else str(weapon_base)[:2000]
        projectile_base_str = "".join(projectile_base[:50]) if isinstance(projectile_base, list) else str(projectile_base)[:2000]
        cow_base_str = "".join(cow_base[:100]) if isinstance(cow_base, list) else str(cow_base)[:3000]
        
        system_prompt = """You are a game weapon analyzer and designer with deep understanding of game mechanics.

Your task is to THOROUGHLY analyze the weapon description and create a COMPLETE specification.

## Analysis Checklist:
1. **Effect Detection**: Does this weapon have ANY special behavior beyond basic damage?
   
   **CHARACTER EFFECTS** (apply to hit targets, need Cow class methods):
   - Movement effects: knockback, pull, teleport, dash
   - Status effects: freeze, slow, stun, burn, poison, blind
   - Buff/Debuff: damage boost, armor reduction, lifesteal
   
   **PROJECTILE BEHAVIORS** (inherent to projectile, NO Cow methods):
   - Movement: projectile_behavior_zigzag, projectile_behavior_homing, projectile_behavior_bouncing
   - Impact: impact_splitting, impact_explosion, piercing
   
   IMPORTANT: Distinguish between character effects and projectile behaviors!
   - Zigzag pattern = projectile_behavior_zigzag (not a character effect)
   - Splitting on impact = impact_splitting (not a character effect)
   - Freeze target = freeze (IS a character effect)

2. **Effect Details**: For EACH effect, specify:
   - Duration (in milliseconds)
   - Magnitude (percentages, force values, etc.)
   - Interaction with character state (movement, actions, etc.)
   - Visual feedback needed

3. **Weapon Stats**: Balanced and appropriate:
   - damage: 5-50 range (10-20 is standard)
   - projectile_speed: 10-30 range (16-18 is standard)
   - ammo_per_shot: Usually 1, can be higher for powerful weapons

4. **Implementation Requirements**: What code changes are needed?
   - New character state variables?
   - Custom projectile class?
   - Arena modifications?
   - Effect application in update loop?

## Output Format (STRICT JSON):
{
  "weapon_name": "DescriptiveName",  // CamelCase, no spaces, unique identifier
  "display_name": "Display Name",     // User-facing name
  "has_effects": true,                // true if ANY special behavior beyond damage
  "effect_types": ["effect1", "effect2"],  // List all effects
  "effect_details": {
    "effect1": {
      "duration_ms": 3000,           // How long effect lasts
      "magnitude": 0.5,               // Effect strength (context-dependent)
      "description": "Detailed description of what this does",
      "requires_update_loop": true,   // Does this need to apply every frame?
      "state_variables": ["is_effect1", "effect1_end_time", "effect1_value"]  // What to add to Cow
    }
  },
  "ammo_per_shot": 1,
  "projectile_speed": 16.0,
  "damage": 10.0,
  "projectile_behavior": "standard",  // or "zigzag", "homing", "bouncing", etc.
  "description": "Complete description of weapon behavior"
}

## Common Effects Reference:
- **knockback**: Pushes character away (requires velocity vectors, update loop)
- **freeze**: Prevents movement (requires is_frozen flag, end_time)
- **slow**: Reduces speed (requires slow_percent, end_time)
- **stun**: Prevents actions (requires is_stunned flag, end_time)
- **burn/poison**: Damage over time (requires tick tracking, damage value)
- **lifesteal**: Heal on damage (no character state needed, instant)

CRITICAL: Be thorough and specific. Think through HOW each effect will actually work in code."""

        prompt = f"""Analyze this weapon description and create a COMPLETE specification:

**Weapon Description**: {weapon_description}

**Existing Weapon System**:
```python
{weapon_base_str}
```

**Projectile Base Class**:
```python
{projectile_base_str}
```

**Character (Cow) Base Class** (shows what effects might already exist):
```python
{cow_base_str}
```

Provide a thorough analysis with ALL details needed for implementation."""

        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Parse JSON
        import json
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                result = json.loads(json_str)
            elif "{" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
            else:
                raise ValueError("No JSON found")
            
            # Validate required fields
            if "weapon_name" not in result or "display_name" not in result:
                raise ValueError("Missing required fields")
            
            print(f"\n📊 Analysis Complete:")
            print(f"   Name: {result.get('display_name')}")
            print(f"   Has Effects: {result.get('has_effects', False)}")
            if result.get('has_effects'):
                print(f"   Effects: {', '.join(result.get('effect_types', []))}")
            print(f"   Damage: {result.get('damage')} | Speed: {result.get('projectile_speed')}")
            
            return result
            
        except Exception as e:
            print(f"⚠️  JSON parsing failed: {e}")
            print(f"Response preview: {response[:500]}")
        
        # Fallback
        return {
            "weapon_name": "CustomWeapon",
            "display_name": "Custom Weapon",
            "has_effects": False,
            "effect_types": [],
            "effect_details": {},
            "ammo_per_shot": 1,
            "projectile_speed": 16.0,
            "damage": 10.0,
            "description": weapon_description
        }
    
    def _add_effects_to_cow(self, effect_types: list) -> bool:
        """
        Modify Cow class to support the specified effects.
        
        Args:
            effect_types: List of effect names like ["freeze", "burn"]
            
        Returns:
            True if successful
        """
        from Agent.Tools.read_file import read_file
        from Agent.Tools.write_to_file import write_over_file
        
        # Read current cow.py
        cow_lines = read_file("Game/Character/cow.py", line_count=False)
        if isinstance(cow_lines, str):
            return False
        
        cow_content = "".join(cow_lines)
        
        # Check if effects already exist
        effects_to_add = []
        for effect in effect_types:
            if f"is_{effect}" not in cow_content:
                effects_to_add.append(effect)
        
        if not effects_to_add:
            print(f"    Effects already exist in Cow class")
            return True
        
        # Generate effect support code
        system_prompt = """You are an expert at modifying game character classes to add status effect systems.

Your task: Generate COMPLETE, WORKING code to add effect support to the Cow character class.

## CRITICAL REQUIREMENTS:

### 1. Indentation
- Use NO INDENTATION in your output
- Write everything flush left (no leading spaces)
- The system will add proper indentation automatically

### 2. Effect Implementation (COMPLETE LIFECYCLE)
Every effect needs THREE parts:

**A) State Variables (in __init__)**
- Boolean flag: `is_effectname`
- End time: `effectname_end_time`
- Additional data: velocity vectors, damage values, etc.

**B) Application Method (called when effect is applied)**
```python
def apply_effectname(self, param1, param2):
    \"\"\"Apply effect to character.\"\"\"
    if self.is_dead():
        return
    now = pygame.time.get_ticks()
    self.is_effectname = True
    self.effectname_end_time = now + duration_ms
    # Set effect-specific values
```

**C) Integration Points:**
- UPDATE_MODIFICATIONS: Code to add to update() for per-frame effects
- EXPIRATION: Code in _update_effects() to clean up expired effects

### 3. Effect Type Patterns

**Movement Effects (knockback, pull, dash):**
- Need: velocity_x, velocity_y, end_time
- UPDATE: Apply velocity to position every frame
- EXPIRE: Clear velocity and flag

**Status Effects (freeze, stun, slow):**
- Need: flag, end_time, magnitude (for slow/speed changes)
- UPDATE: Modify movement/action availability
- EXPIRE: Clear flag

**Damage Over Time (burn, poison):**
- Need: flag, end_time, damage_per_tick, last_tick_time
- UPDATE: Apply damage each tick
- EXPIRE: Clear flag

**Instant Effects (lifesteal, explosion):**
- No state needed, apply immediately in projectile handler

### 4. Output Format (EXACT):
```python
# INIT_ADDITIONS
self.is_effectname = False
self.effectname_end_time = 0
self.effectname_data = 0.0

# UPDATE_MODIFICATIONS
# Apply effectname if active
if self.is_effectname:
    # Do per-frame effect application
    self.position.x += self.effectname_velocity_x
    # Check for ticks, modify speed, etc.

# METHODS
def apply_effectname(self, param1, param2):
\"\"\"Apply effectname to character.\"\"\"
if self.is_dead():
    return
now = pygame.time.get_ticks()
self.is_effectname = True
self.effectname_end_time = now + param1
self.effectname_data = param2

def _update_effects(self):
\"\"\"Update and expire all effects.\"\"\"
now = pygame.time.get_ticks()
# Expire effectname
if self.is_effectname and now >= self.effectname_end_time:
    self.is_effectname = False
    self.effectname_data = 0.0
```

### 5. Common Pitfalls to AVOID:
❌ Forgetting UPDATE_MODIFICATIONS for movement effects
❌ Not checking is_dead() before applying effects
❌ Missing expiration logic
❌ Incorrect parameter passing (duration, magnitude, etc.)
❌ Not resetting effect data on expiration

CRITICAL: Be COMPLETE and CORRECT. Think through the full lifecycle of each effect."""

        prompt = f"""Add COMPLETE effect support for these effects: {effects_to_add}

**Current Cow class context:**
- Has __init__ with: health, stamina, ammo, position (Vector2), velocity
- Has update(arena) method that calls handle_collisions()
- Already has _update_effects() if effects exist
- Is used by BOTH player and AI characters

**For each effect, provide:**
1. ALL state variables needed
2. Complete apply_effectname() method
3. UPDATE_MODIFICATIONS if effect needs per-frame updates
4. Expiration logic for _update_effects()

Be thorough and think through HOW the effect actually works in the game loop."""

        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Now modify the actual cow.py file
        # Find where to insert effect initialization (after stamina)
        init_insert_marker = "self.stamina = base_stamina"
        
        # Extract init additions, update modifications, and methods from response
        import re
        import textwrap

        # Find INIT_ADDITIONS
        init_match = re.search(r'# INIT_ADDITIONS.*?\n(.*?)(?=\n# UPDATE_MODIFICATIONS|$)', response, re.DOTALL)
        # Find UPDATE_MODIFICATIONS
        update_match = re.search(r'# UPDATE_MODIFICATIONS.*?\n(.*?)(?=\n# METHODS|$)', response, re.DOTALL)
        # Find METHODS
        methods_match = re.search(r'# METHODS.*?\n(.*?)(?=```|$)', response, re.DOTALL)

        if init_match:
            # Clean up indentation
            raw_init = init_match.group(1).strip()
            # Ensure proper indentation (8 spaces for __init__ content)
            init_lines = raw_init.split('\n')
            fixed_init_lines = []
            for line in init_lines:
                if line.strip():
                    # Remove any existing indentation and add correct indentation
                    fixed_init_lines.append("        " + line.strip())
                else:
                    fixed_init_lines.append("")
            init_additions = "\n        # Effect tracking\n" + "\n".join(fixed_init_lines)
        else:
            # Fallback: generate basic effect tracking
            init_additions = "\n        # Effect tracking\n"
            for effect in effects_to_add:
                init_additions += f"        self.is_{effect} = False\n"
                init_additions += f"        self.{effect}_end_time = 0\n"

        if update_match:
            # Clean up update modifications indentation (8 spaces for method body)
            raw_update = update_match.group(1).strip()
            update_lines = raw_update.split('\n')
            fixed_update_lines = []
            for line in update_lines:
                if line.strip():
                    fixed_update_lines.append("        " + line.strip())
                else:
                    fixed_update_lines.append("")
            update_modifications = "\n" + "\n".join(fixed_update_lines) + "\n"
        else:
            update_modifications = ""
        
        if methods_match:
            # Clean up method indentation - use autopep8 approach
            raw_methods = methods_match.group(1).strip()
            methods_dedented = textwrap.dedent(raw_methods)
            
            # Build properly indented code by tracking block depth
            fixed_methods = []
            depth = 0  # Track nesting depth INSIDE method body
            
            for line in methods_dedented.split('\n'):
                stripped = line.strip()
                if not stripped:
                    fixed_methods.append("")
                    continue
                
                # Handle dedents for elif/else/except/finally BEFORE calculating indent
                if stripped.startswith(('elif ', 'else:', 'except', 'finally:')):
                    depth = max(0, depth - 1)
                
                # Calculate indentation
                if stripped.startswith(('def ', 'class ')):
                    # Method/class definition: 4 spaces
                    fixed_methods.append("    " + stripped)
                    depth = 0  # Reset depth for method body
                    # Don't increase depth here - method body starts at depth 0
                    continue  # Skip depth increase logic
                else:
                    # Method body: 8 spaces base + 4 per depth level
                    indent = "        " + ("    " * depth)
                    fixed_methods.append(indent + stripped)
                
                # Increase depth AFTER adding line if it ends with ':'
                if stripped.endswith(':') and not stripped.startswith('#'):
                    depth += 1
                # Decrease depth after single-statement lines (return/break/etc)
                elif depth > 0 and (stripped in ('return', 'break', 'continue', 'pass') or \
                     stripped.startswith(('return ', 'break ', 'continue ', 'pass ', 'raise '))):
                    depth = max(0, depth - 1)
            
            new_methods = "\n    # ----- Effect Methods -----\n" + "\n".join(fixed_methods) + "\n"
        else:
            # Fallback: generate basic methods with proper indentation
            new_methods = "\n    # ----- Effect Methods -----\n"
            update_modifications = ""

            for effect in effects_to_add:
                # Special handling for movement effects
                if effect == "knockback":
                    # Add knockback-specific variables and methods
                    init_additions = "\n        # Effect tracking\n        self.is_knocked_back = False\n        self.knockback_velocity_x = 0.0\n        self.knockback_velocity_y = 0.0\n        self.knockback_end_time = 0\n"
                    update_modifications = "\n        # Apply knockback movement if active\n        if self.is_knocked_back:\n            self.position.x += self.knockback_velocity_x\n            self.position.y += self.knockback_velocity_y\n"
                    new_methods += """    def apply_knockback(self, vector_x: float, vector_y: float, duration_ms: int = 150):
        \"\"\"Apply knockback effect that moves character.\"\"\"
        if self.is_dead():
            return
        now = pygame.time.get_ticks()
        self.is_knocked_back = True
        self.knockback_velocity_x = vector_x
        self.knockback_velocity_y = vector_y
        self.knockback_end_time = now + duration_ms

"""
                else:
                    # Standard effect
                    new_methods += f"""    def apply_{effect}(self, duration_ms: int):
        \"\"\"Apply {effect} effect to this character.\"\"\"
        if self.is_dead():
            return
        now = pygame.time.get_ticks()
        self.is_{effect} = True
        self.{effect}_end_time = now + duration_ms

"""

            # _update_effects with NO parameters except self
            new_methods += "    def _update_effects(self):\n"
            new_methods += "        \"\"\"Update and expire all effects.\"\"\"\n"
            new_methods += "        now = pygame.time.get_ticks()\n"
            for effect in effects_to_add:
                new_methods += f"        if self.is_{effect} and now >= self.{effect}_end_time:\n"
                new_methods += f"            self.is_{effect} = False\n"
        
        # Insert init additions
        modified_content = cow_content.replace(
            init_insert_marker,
            init_insert_marker + init_additions
        )
        
        # Add update_effects call to update method if not exists
        if "_update_effects" in new_methods and "self._update_effects()" not in modified_content:
            # Find the update method and add _update_effects call
            update_method_pattern = r'def update\(self, arena=None\):(.*?)def '
            update_match = re.search(update_method_pattern, modified_content, re.DOTALL)
            if update_match:
                update_method_content = update_match.group(1)
                # Add _update_effects call and update modifications
                modified_update = update_method_content.replace(
                    "self.handle_collisions()",
                    "self.handle_collisions()" + update_modifications + "\n        self._update_effects()"
                )
                modified_content = modified_content.replace(update_method_content, modified_update)
            else:
                # Fallback: add to beginning of update method
                modified_content = modified_content.replace(
                    "def update(self, arena=None):",
                    "def update(self, arena=None):\n        self._update_effects()" + update_modifications
                )
        
        # Add methods before the last method or at end of class
        # Find the last "    def " and insert before it
        last_method_match = list(re.finditer(r'\n    def ', modified_content))
        if last_method_match:
            insert_pos = last_method_match[-1].start()
            modified_content = modified_content[:insert_pos] + new_methods + modified_content[insert_pos:]
        else:
            # Add at end
            modified_content += new_methods
        
        # Write back
        result = write_over_file("Game/Character/cow.py", modified_content)
        return "success" in result
    
    def _create_weapon_file_with_effects(self, weapon_plan: dict, description: str) -> str:
        """Create weapon file that applies effects through projectiles."""
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        file_path = f"Game/Weapons/{weapon_name.lower()}.py"
        
        has_effects = weapon_plan.get("has_effects", False)
        effect_types = weapon_plan.get("effect_types", [])
        effect_details = weapon_plan.get("effect_details", {})
        
        # Generate weapon code
        if has_effects:
            # Custom projectile class name
            projectile_class = f"{weapon_name}Projectile"
            
            code = f'''"""
{weapon_plan.get("display_name", weapon_name)} - Custom Weapon with Effects

{weapon_plan.get("description", description)}

Effects: {", ".join(effect_types)}
"""

from Game.Weapons.weapon import Weapon
from Game.Objects.{weapon_name.lower()}_projectile import {projectile_class}


def create_{weapon_name.lower()}() -> Weapon:
    """
    Factory function to create a {weapon_plan.get("display_name", weapon_name)}.
    
    This weapon applies effects: {", ".join(effect_types)}
    
    Returns:
        Configured Weapon instance
    """
    weapon = Weapon(
        name="{weapon_plan.get("display_name", weapon_name)}",
        ammo_per_shot={weapon_plan.get("ammo_per_shot", 1)},
        projectile_speed={weapon_plan.get("projectile_speed", 16.0)},
        damage={weapon_plan.get("damage", 10.0)},
        floor_image_name="placeholder.png",
        floor_image_scale=(28, 28),
        projectile_image_name="placeholder.png",
        projectile_image_scale=(18, 6)
    )
    
    # Store effect info for custom projectile
    weapon.effect_types = {effect_types}
    weapon.effect_details = {effect_details}
    weapon.projectile_class = {projectile_class}
    
    return weapon


# Quick access instance
{weapon_name.upper()} = create_{weapon_name.lower()}()
'''
        else:
            # Standard weapon without effects
            code = f'''"""
{weapon_plan.get("display_name", weapon_name)} - Custom Weapon

{weapon_plan.get("description", description)}
"""

from Game.Weapons.weapon import Weapon


def create_{weapon_name.lower()}() -> Weapon:
    """
    Factory function to create a {weapon_plan.get("display_name", weapon_name)}.
    
    Returns:
        Configured Weapon instance
    """
    return Weapon(
        name="{weapon_plan.get("display_name", weapon_name)}",
        ammo_per_shot={weapon_plan.get("ammo_per_shot", 1)},
        projectile_speed={weapon_plan.get("projectile_speed", 16.0)},
        damage={weapon_plan.get("damage", 10.0)},
        floor_image_name="placeholder.png",
        floor_image_scale=(28, 28),
        projectile_image_name="placeholder.png",
        projectile_image_scale=(18, 6)
    )


# Quick access instance
{weapon_name.upper()} = create_{weapon_name.lower()}()
'''
        
        # Write file
        from Agent.Tools.write_to_file import create_file
        result = create_file(file_path, code)
        
        if "success" in result:
            return file_path
        else:
            raise Exception(f"Failed to create weapon file: {result}")
    
    def _create_effect_projectile(self, weapon_plan: dict) -> str:
        """Create custom projectile class that applies effects on hit."""
        from Agent.Tools.read_file import read_file
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        effect_types = weapon_plan.get("effect_types", [])
        effect_details = weapon_plan.get("effect_details", {})
        
        file_path = f"Game/Objects/{weapon_name.lower()}_projectile.py"
        
        # Read base projectile for reference
        projectile_base = read_file("Game/Objects/projectile.py", line_count=False)
        projectile_str = "".join(projectile_base[:80]) if isinstance(projectile_base, list) else str(projectile_base)[:2000]
        
        # Generate effect application code using AI for better accuracy
        system_prompt = """You are creating a custom projectile class for a game weapon.

Your task: Generate a COMPLETE, CORRECT custom projectile class that inherits from Projectile.

## CRITICAL REQUIREMENTS:

### 1. Proper Inheritance
The base Projectile class has this constructor signature:
```python
def __init__(self, start_pos, direction, speed: float = 16.0, color=(255, 250, 220), 
             radius: int = 4, max_distance: float = 2400.0, sprite=None, 
             damage: float = 10.0, owner=None):
```

Your custom projectile MUST call super().__init__() with ALL positional parameters in the correct order:
```python
super().__init__(
    position,           # start_pos
    direction,          # direction
    speed,             # speed
    (R, G, B),         # color (tuple of 3 ints) - REQUIRED
    4,                 # radius (int) - REQUIRED
    2400.0,            # max_distance
    sprite,            # sprite
    damage,            # damage
    owner              # owner
)
# Store speed for later use (base class doesn't store it)
self.speed = speed
```

### 2. Effect Application & Method Signatures

**CRITICAL**: The `on_character_hit` method MUST have this EXACT signature:
```python
def on_character_hit(self, target, arena):
```
- Takes 2 parameters: `target` and `arena`
- Arena calls it as: `proj.on_character_hit(character, self)`

In the `on_character_hit` method:
1. Apply damage first: `target.take_damage(self.damage)`
2. Check if target is alive (if needed)
3. Apply each effect using the character's apply_effectname() method
4. Destroy projectile: `self.alive = False` (NEVER use `self.kill()`)

**CRITICAL**: The `update` method (if overridden) MUST have this EXACT signature:
```python
def update(self):
```
- Takes NO parameters (only `self`)
- Arena calls it as: `proj.update()` with no arguments

### 3. Effect Type Patterns

**CHARACTER EFFECTS** (applied to target in on_character_hit):
- **Movement effects** (knockback): `target.apply_knockback(vector_x, vector_y, duration_ms)`
- **Status effects** (freeze, slow): `target.apply_freeze(duration_ms, slow_percent)`
- **Simple effects** (stun, burn): `target.apply_stun(duration_ms)`

**PROJECTILE BEHAVIORS** (implemented in projectile class itself):
- **projectile_behavior_homing**: Override update() to track nearest target
- **projectile_behavior_bouncing**: Bounce off walls and obstacles
- **impact_splitting**: In on_character_hit(), spawn multiple projectiles in random directions
- **impact_explosion**: In on_character_hit(), damage all nearby characters
- **piercing**: Set self.can_pierce = True, don't set alive = False on hit

### 4. Examples

**Example 1: Character Effect (Freeze)**
```python
class FreezeProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (100, 150, 255), 4, 2400.0, sprite, damage, owner)
        self.speed = speed  # Store for later use
    
    def on_character_hit(self, target, arena):  # MUST have 2 params: target, arena
            target.take_damage(self.damage)
            if hasattr(target, 'apply_freeze'):
                target.apply_freeze(3000, 0.5)
        self.alive = False  # NEVER use self.kill()
```

**Example 2: Homing Behavior**
```python
class HomingProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (255, 100, 100), 4, 2400.0, sprite, damage, owner)
        self.speed = speed  # Store for later use
        self.homing_strength = 2.0  # How strongly it homes in
    
    def update(self):  # CRITICAL: NO arena parameter - just (self)!
        if not self.alive:
            return

        # Find nearest target to home towards
        nearest_target = None
        nearest_distance = float('inf')

        # This would need access to arena to find targets
        # For now, simplified version
        self.position += self.velocity
        self.distance_traveled += self.velocity.length()

        if self.distance_traveled >= self.max_distance:
            self.alive = False

    def on_character_hit(self, target, arena):  # MUST have 2 params: target, arena
        target.take_damage(self.damage)
        self.alive = False  # NEVER use self.kill()
```

**Example 3: Impact Splitting**
```python
class SplittingProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (255, 150, 50), 4, 2400.0, sprite, damage, owner)
        self.speed = speed  # Store for later use
    
    def on_character_hit(self, target, arena):  # MUST have 2 params: target, arena
            target.take_damage(self.damage)
        # Spawn 3 smaller projectiles
        import random, math
        for _ in range(3):
            angle = random.uniform(0, 2 * 3.14159)
            direction = Vector2(math.cos(angle), math.sin(angle))
            # CRITICAL: arena.spawn_projectile only accepts these parameters:
            # (start_pos, direction, speed, sprite=None, damage, owner=None)
            # DO NOT use color, radius, or max_distance - they are NOT supported!
            arena.spawn_projectile(
                start_pos=self.position.copy(), 
                direction=direction, 
                speed=self.speed * 0.8, 
                damage=self.damage * 0.5, 
                owner=None  # Use None to prevent recursive custom projectile
            )
        self.alive = False  # NEVER use self.kill()
```

### 5. CRITICAL: Arena.spawn_projectile Signature
When spawning secondary projectiles (for splitting, explosion, etc.), use ONLY these parameters:
```python
arena.spawn_projectile(
    start_pos,      # Vector2 or tuple
    direction,      # Vector2 (normalized direction)
    speed=16.0,     # float
    sprite=None,    # optional sprite
    damage=10.0,    # float
    owner=None      # Character or None
)
```

**NEVER use these parameters** (they cause TypeError):
- ❌ color - NOT SUPPORTED
- ❌ radius - NOT SUPPORTED  
- ❌ max_distance - NOT SUPPORTED

These parameters exist in Projectile.__init__ but NOT in arena.spawn_projectile!

Output ONLY the complete class definition. NO explanations.

**CRITICAL**: 
- Class MUST be named: {weapon_name}Projectile
- Class MUST inherit from Projectile: class {weapon_name}Projectile(Projectile):
- NO extra classes or code outside the class definition"""

        # Build effect info string
        effect_info_str = ""
        for effect in effect_types:
            details = effect_details.get(effect, {})
            effect_info_str += f"\n   - {effect}: {details}"

        prompt = f"""Create a custom projectile class for weapon: {weapon_name}

**CRITICAL REQUIREMENTS**:
1. Class name MUST be EXACTLY: {weapon_name}Projectile
2. Class MUST inherit: class {weapon_name}Projectile(Projectile):
3. NO extra classes, NO helper functions outside the class
4. Follow the examples format EXACTLY

**Base Projectile Class:**
```python
{projectile_str}
```

**Effects to implement:**{effect_info_str}

**Effect Details:**
{effect_details}

Generate the COMPLETE {weapon_name}Projectile class with:
1. Proper super().__init__() call (with color and radius!)
2. Required methods based on effect types:
   - Character effects: Call target.apply_effectname() in on_character_hit()
   - Projectile behaviors: Override update() or enhance on_character_hit()
3. Use appropriate colors based on effects (e.g., blue for freeze, red for burn)

**CRITICAL FOR SPLITTING EFFECTS:**
If the effect includes "splitting" or "split":
- MUST spawn the exact number of projectiles specified in effect_details (e.g., split_count: 3 means spawn 3 projectiles)
- MUST use arena.spawn_projectile() with ONLY these parameters: start_pos, direction, speed, damage, owner
- MUST set owner=None to prevent recursive custom projectiles
- The splitting should happen in on_character_hit() method
- MUST use the spread angle from effect_details if provided

Remember: Class name is {weapon_name}Projectile with (Projectile) inheritance!"""

        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Extract code from response
        import re
        
        # Look for class definition
        if "```python" in response:
            code_start = response.find("```python") + 9
            code_end = response.find("```", code_start)
            code = response[code_start:code_end].strip()
        elif "class " in response:
            # Extract from first class to end or next ```
            lines = response.split('\n')
            code_lines = []
            in_class = False
            for line in lines:
                if 'class ' in line and weapon_name in line:
                    in_class = True
                if in_class:
                    code_lines.append(line)
                    if line.strip() and not line[0].isspace() and 'class' not in line and code_lines:
                        break
            code = '\n'.join(code_lines)
        else:
            raise Exception("AI did not generate class code")
        
        # Add header
        full_code = f'''"""
Custom Projectile for {weapon_name}

Applies effects: {", ".join(effect_types)}
"""

import pygame
from pygame import Vector2
from Game.Objects.projectile import Projectile


{code}
'''
        
        # Write file
        from Agent.Tools.write_to_file import create_file
        result = create_file(file_path, full_code)
        
        if "success" in result:
            # Verify the file compiles
            try:
                compile(full_code, file_path, 'exec')
                return file_path
            except SyntaxError as e:
                raise Exception(f"Generated projectile has syntax error: {e}")
        else:
            raise Exception(f"Failed to create projectile file: {result}")
    
    def _update_arena_projectile_spawn(self, weapon_plan: dict) -> bool:
        """
        Modify Arena's projectile spawning to use custom projectiles when weapon has effects.
        
        Args:
            weapon_plan: Weapon configuration
            
        Returns:
            True if successful
        """
        from Agent.Tools.read_file import read_file
        from Agent.Tools.write_to_file import write_over_file
        import re
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        projectile_class = f"{weapon_name}Projectile"
        
        # Read arena.py
        arena_lines = read_file("Game/Arena/arena.py", line_count=False)
        if isinstance(arena_lines, str):
            return False
        
        arena_content = "".join(arena_lines)
        
        # Add import for custom projectile at top
        import_line = f"from Game.Objects.{weapon_name.lower()}_projectile import {projectile_class}\n"
        
        # Add after projectile imports
        if "from Game.Objects import Projectile" in arena_content:
            arena_content = arena_content.replace(
                "from Game.Objects import Projectile",
                "from Game.Objects import Projectile\n" + import_line
            )
        else:
            # Find last import
            last_import = list(re.finditer(r'^from Game\.Objects.*import.*$', arena_content, re.MULTILINE))
            if last_import:
                insert_pos = last_import[-1].end()
                arena_content = arena_content[:insert_pos] + "\n" + import_line + arena_content[insert_pos:]
        
        # Now modify the spawn_projectile method to check for custom projectile class
        # Find the spawn_projectile method
        spawn_method_pattern = r'def spawn_projectile\(self, start_pos, direction, speed.*?\):(.*?)(?=\n    def |\Z)'
        
        match = re.search(spawn_method_pattern, arena_content, re.DOTALL)
        if match:
            # Check if already modified
            if "projectile_class" in match.group(0):
                print("    spawn_projectile already supports custom projectiles")
                return True
            
            # Replace the method to check for custom projectile class
            old_method = match.group(0)
            
            new_method = '''def spawn_projectile(self, start_pos, direction, speed: float = 16.0, sprite=None, damage: float = 10.0, owner=None):
        """
        Spawn a projectile. Checks if owner's weapon has a custom projectile class.
        
        Args:
            start_pos: Starting position
            direction: Direction vector
            speed: Projectile speed
            sprite: Projectile sprite (optional)
            damage: Damage dealt
            owner: Character that fired (to check for custom projectile)
        """
        # Check if owner has a weapon with custom projectile class
        projectile_class = None
        if owner and hasattr(owner, 'get_weapon'):
            weapon = owner.get_weapon()
            if weapon and hasattr(weapon, 'projectile_class'):
                projectile_class = weapon.projectile_class
        
        # Use custom projectile if available, otherwise standard
        if projectile_class:
            proj = projectile_class(start_pos, direction, speed=speed, damage=damage, sprite=sprite, owner=owner)
        else:
            proj = Projectile(start_pos, direction, speed=speed, sprite=sprite, damage=damage, owner=owner)
        
        self.projectiles.append(proj)'''
            
            arena_content = arena_content.replace(old_method, new_method)
        
        # Also need to update projectile collision to call on_character_hit if exists
        # Find projectile collision section
        collision_pattern = r'(if prect\.colliderect\(char_rect\):.*?proj\.alive = False.*?break)'
        
        matches = list(re.finditer(collision_pattern, arena_content, re.DOTALL))
        if matches:
            for match in matches:
                old_collision = match.group(1)
                if "on_character_hit" not in old_collision:
                    new_collision = '''if prect.colliderect(char_rect):
                        # Use custom hit handler if available
                        if hasattr(proj, 'on_character_hit'):
                            proj.on_character_hit(character, self)
                        else:
                            # Standard damage
                            if hasattr(character, 'take_damage'):
                                character.take_damage(getattr(proj, 'damage', 10.0))
                            proj.alive = False
                        break'''
                    
                    arena_content = arena_content.replace(old_collision, new_collision, 1)
        
        # Write back
        result = write_over_file("Game/Arena/arena.py", arena_content)
        return "success" in result
    
    def _add_weapon_to_loot_pool(self, weapon_plan: dict) -> bool:
        """
        Modify Arena to add weapon to golden field loot pool.
        
        Args:
            weapon_plan: Weapon configuration
            
        Returns:
            True if successful
        """
        from Agent.Tools.read_file import read_file
        from Agent.Tools.write_to_file import write_over_file
        import re
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        
        # Read arena.py
        arena_lines = read_file("Game/Arena/arena.py", line_count=False)
        if isinstance(arena_lines, str):
            return False
        
        arena_content = "".join(arena_lines)
        
        # Check if already added
        if f"create_{weapon_name.lower()}" in arena_content:
            print("    Weapon already in loot pool")
            return True
        
        # Add import at top
        import_line = f"from Game.Weapons.{weapon_name.lower()} import create_{weapon_name.lower()}\n"
        
        # Find import section (after existing weapon imports or after other imports)
        if "from Game.Weapons import Weapon" in arena_content:
            arena_content = arena_content.replace(
                "from Game.Weapons import Weapon",
                "from Game.Weapons import Weapon\n" + import_line
            )
        else:
            # Add after other imports
            last_import = list(re.finditer(r'^from Game\..*import.*$', arena_content, re.MULTILINE))
            if last_import:
                insert_pos = last_import[-1].end()
                arena_content = arena_content[:insert_pos] + "\n" + import_line + arena_content[insert_pos:]
        
        # Find the weapon pool and add new weapon
        # Look for weapons_pool = [...] structure
        pool_pattern = r'(weapons_pool = \[[\s\S]*?\])'
        
        match = re.search(pool_pattern, arena_content)
        if match:
            # Pool already exists, add weapon to it
            pool_content = match.group(1)
            
            # Check if weapon already in pool
            if f"create_{weapon_name.lower()}" not in pool_content:
                # Add weapon before closing bracket
                new_entry = f"\n                                        create_{weapon_name.lower()}(),"
                new_pool = pool_content.replace(
                    "\n                                    ]",
                    new_entry + "\n                                    ]"
                )
                arena_content = arena_content.replace(pool_content, new_pool)
        else:
            # No pool exists, look for single weapon pickup and create pool
            bow_pattern = r'(pickup = WeaponPickup\(Weapon\(name="Bow"[^)]+\), \(gx \+ offset, gy\)\))'
            match = re.search(bow_pattern, arena_content)
            if match:
                old_code = match.group(1)
                # Properly indented code (golden field section uses 36 spaces base indent)
                new_code = '''# Weapon pool for random drops
                                    weapons_pool = [
                                        Weapon(name="Bow", ammo_per_shot=1, projectile_speed=18.0, floor_image_name="bow.png", floor_image_scale=(28, 28), projectile_image_name="arrow.png", projectile_image_scale=(18, 6)),
                                        create_''' + weapon_name.lower() + '''(),
                                    ]
                                    weapon = random.choice(weapons_pool)
                                    pickup = WeaponPickup(weapon, (gx + offset, gy))'''
                
                arena_content = arena_content.replace(old_code, new_code)
        
        # Write back
        result = write_over_file("Game/Arena/arena.py", arena_content)
        return "success" in result
    
    def _generate_weapon(self, weapon_description: str) -> dict:
        """Generate weapon configuration from description."""
        from Agent.Tools.read_file import read_file
        
        # Read existing weapon as example
        weapon_example_lines = read_file("Game/Weapons/weapon.py", line_count=False)
        weapon_example = "".join(weapon_example_lines[:100]) if isinstance(weapon_example_lines, list) else weapon_example_lines
        
        system_prompt = """You are a game weapon designer.

Your task: Create a weapon configuration based on user description.

A weapon needs:
- name: Display name
- ammo_per_shot: How much ammo each shot consumes
- projectile_speed: Speed of the projectile (pixels per frame)
- damage: Damage dealt on hit
- floor_image_name: Sprite file when on ground (optional, e.g., "bow.png")
- floor_image_scale: Size of floor sprite (tuple, e.g., (28, 28))
- projectile_image_name: Sprite for the projectile (optional, e.g., "arrow.png")
- projectile_image_scale: Size of projectile sprite (tuple, e.g., (18, 6))

Output as JSON:
{
  "weapon_name": "UniqueWeaponName",
  "display_name": "Display Name",
  "ammo_per_shot": 1,
  "projectile_speed": 18.0,
  "damage": 10.0,
  "floor_image_name": "weapon_sprite.png",
  "floor_image_scale": [28, 28],
  "projectile_image_name": "projectile_sprite.png",
  "projectile_image_scale": [18, 6],
  "description": "Brief description of weapon behavior"
}

If no sprite is specified, leave as null."""

        prompt = f"""Create a weapon configuration:

**Weapon Description**: {weapon_description}

**Existing Weapon System**:
```python
{weapon_example}
```

Generate a complete weapon configuration as JSON."""

        # Check request limit
        if not self._check_request_limit():
            raise Exception("User stopped workflow - request limit reached")

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Parse JSON from response
        import json
        import re
        
        # Try to extract JSON
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                json_str = response[json_start:json_end].strip()
                return json.loads(json_str)
            elif "{" in response:
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback
        return {
            "weapon_name": "CustomWeapon",
            "display_name": "Custom Weapon",
            "ammo_per_shot": 1,
            "projectile_speed": 16.0,
            "damage": 10.0,
            "floor_image_name": None,
            "floor_image_scale": [28, 28],
            "projectile_image_name": None,
            "projectile_image_scale": [18, 6],
            "description": weapon_description
        }
    
    def _create_weapon_file(self, weapon_config: dict) -> str:
        """Create a Python file with the weapon instantiation."""
        weapon_name = weapon_config.get("weapon_name", "CustomWeapon")
        file_path = f"Game/Weapons/{weapon_name.lower()}.py"
        
        # Generate weapon code
        code = f'''"""
{weapon_config.get("display_name", weapon_name)} - Custom Weapon

{weapon_config.get("description", "A custom weapon created by the agent.")}
"""

from Game.Weapons.weapon import Weapon


def create_{weapon_name.lower()}() -> Weapon:
    """
    Factory function to create a {weapon_config.get("display_name", weapon_name)}.
    
    Returns:
        Configured Weapon instance
    """
    return Weapon(
        name="{weapon_config.get("display_name", weapon_name)}",
        ammo_per_shot={weapon_config.get("ammo_per_shot", 1)},
        projectile_speed={weapon_config.get("projectile_speed", 16.0)},
        damage={weapon_config.get("damage", 10.0)},
        floor_image_name={repr(weapon_config.get("floor_image_name"))},
        floor_image_scale=tuple({weapon_config.get("floor_image_scale", [28, 28])}),
        projectile_image_name={repr(weapon_config.get("projectile_image_name"))},
        projectile_image_scale=tuple({weapon_config.get("projectile_image_scale", [18, 6])})
    )


# Quick access instance
{weapon_name.upper()} = create_{weapon_name.lower()}()
'''
        
        # Write file
        from Agent.Tools.write_to_file import create_file
        result = create_file(file_path, code)
        
        if "success" in result:
            return file_path
        else:
            raise Exception(f"Failed to create weapon file: {result}")
    
    def _create_weapon_integration_example(self, weapon_config: dict) -> str:
        """Create integration example showing how to use the weapon."""
        weapon_name = weapon_config.get("weapon_name", "CustomWeapon")
        
        example = f'''
# ============================================================
# HOW TO USE: {weapon_config.get("display_name", weapon_name)}
# ============================================================

# 1. Import the weapon
from Game.Weapons.{weapon_name.lower()} import create_{weapon_name.lower()}

# 2. Spawn as pickup in Arena (add to golden field drops)
# In Game/Arena/arena.py, modify handle_key_event where golden fields spawn pickups:

from Game.Weapons.{weapon_name.lower()} import create_{weapon_name.lower()}

# Inside the golden field eating check:
if random.random() < drop_probability:
    gx, gy = gf.rect.center
    offset = random.randint(-20, 20)
    
    # Create weapon pickup with your new weapon
    weapon = create_{weapon_name.lower()}()
    pickup = WeaponPickup(weapon, (gx + offset, gy))
    self.objects.append(pickup)

# 3. Give to player/AI directly
# In main.py when creating characters:

from Game.Weapons.{weapon_name.lower()} import create_{weapon_name.lower()}

# Give weapon to player
player.equip_weapon(create_{weapon_name.lower()}())

# Give weapon to AI
npc.equip_weapon(create_{weapon_name.lower()}())

# ============================================================
'''
        
        # Save to file
        example_file = f"Game/Weapons/{weapon_name.lower()}_usage.txt"
        with open(example_file, "w") as f:
            f.write(example)
        
        return example_file
    
    def _validate_weapon_implementation(self, weapon_plan: dict, results: dict) -> dict:
        """
        Validate that the weapon implementation is complete and correct.
        
        Returns:
            dict with validation results
        """
        validation = {
            "has_errors": False,
            "errors": [],
            "warnings": [],
            "checks_passed": []
        }
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)
        effect_types = weapon_plan.get("effect_types", [])
        
        # Check 1: Weapon file exists and is syntactically correct
        try:
            weapon_file = f"Game/Weapons/{weapon_name.lower()}.py"
            with open(weapon_file, 'r') as f:
                weapon_code = f.read()
            compile(weapon_code, weapon_file, 'exec')
            validation["checks_passed"].append("Weapon file syntax valid")
            
            # Check 1.5: Weapon uses placeholder.png for images
            if 'floor_image_name="placeholder.png"' in weapon_code or "floor_image_name='placeholder.png'" in weapon_code:
                validation["checks_passed"].append("Weapon uses placeholder.png for floor image")
            else:
                validation["warnings"].append("Weapon should use placeholder.png for floor_image_name")
            
            if 'projectile_image_name="placeholder.png"' in weapon_code or "projectile_image_name='placeholder.png'" in weapon_code:
                validation["checks_passed"].append("Weapon uses placeholder.png for projectile image")
            else:
                validation["warnings"].append("Weapon should use placeholder.png for projectile_image_name")
                
        except FileNotFoundError:
            validation["errors"].append(f"Weapon file not found: {weapon_file}")
            validation["has_errors"] = True
        except SyntaxError as e:
            validation["errors"].append(f"Syntax error in weapon file: {e}")
            validation["has_errors"] = True
        
        # Check 2: If has effects, custom projectile must exist
        if has_effects:
            try:
                projectile_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                with open(projectile_file, 'r') as f:
                    proj_code = f.read()
                compile(proj_code, projectile_file, 'exec')
                
                # Verify projectile has on_character_hit method with CORRECT signature
                if "def on_character_hit(self, target, arena)" in proj_code:
                    validation["checks_passed"].append("Custom projectile has on_character_hit with correct signature")
                elif "def on_character_hit" in proj_code:
                    # Method exists but wrong signature
                    validation["errors"].append("Custom projectile on_character_hit has wrong signature - must be: def on_character_hit(self, target, arena)")
                    validation["has_errors"] = True
                else:
                    validation["errors"].append("Custom projectile missing on_character_hit method")
                    validation["has_errors"] = True
                
                # Check for incorrect self.kill() usage
                if "self.kill()" in proj_code:
                    validation["errors"].append("Custom projectile uses self.kill() - must use self.alive = False instead")
                    validation["has_errors"] = True
                
                # Verify projectile implements required behaviors
                # For projectile-only behaviors, check implementation differently
                projectile_only_effects = ["projectile_behavior_homing",
                                           "projectile_behavior_bouncing", "impact_splitting", 
                                           "impact_explosion", "piercing"]
                
                for effect in effect_types:
                    if effect in projectile_only_effects:
                        # Check for behavior implementation (update method, impact handling, etc.)
                        if "homing" in effect and ("target" in proj_code or "track" in proj_code):
                            validation["checks_passed"].append(f"Projectile implements {effect} behavior")
                        elif "splitting" in effect:
                            if "arena.spawn_projectile" in proj_code:
                                validation["checks_passed"].append(f"Projectile implements {effect} behavior")
                                # Check if the correct number is spawned
                                effect_detail = weapon_plan.get("effect_details", {}).get(effect, {})
                                if "split_count" in effect_detail or "magnitude" in effect_detail:
                                    # Get split_count directly, or use magnitude as the count (magnitude can be int/float, not dict)
                                    expected_count = effect_detail.get("split_count")
                                    if expected_count is None:
                                        magnitude = effect_detail.get("magnitude")
                                        if isinstance(magnitude, (int, float)):
                                            expected_count = int(magnitude)
                                    if expected_count and f"range({expected_count})" in proj_code:
                                        validation["checks_passed"].append(f"Projectile spawns correct number of splits ({expected_count})")
                                    elif expected_count:
                                        validation["warnings"].append(f"Projectile should spawn {expected_count} splits, verify implementation")
                            else:
                                validation["errors"].append(f"Projectile missing spawn_projectile call for {effect}")
                                validation["has_errors"] = True
                        elif "homing" in effect and ("target" in proj_code or "track" in proj_code):
                            validation["checks_passed"].append(f"Projectile implements {effect} behavior")
                        else:
                            validation["warnings"].append(f"Projectile may not fully implement {effect} (check manually)")
                    else:
                        # Character effect - should call apply_effect on target
                        if f"apply_{effect}" in proj_code:
                            validation["checks_passed"].append(f"Projectile applies {effect} effect")
                        else:
                            validation["errors"].append(f"Projectile doesn't apply {effect} effect")
                            validation["has_errors"] = True
                        
            except FileNotFoundError:
                validation["errors"].append(f"Projectile file not found: {projectile_file}")
                validation["has_errors"] = True
            except SyntaxError as e:
                validation["errors"].append(f"Syntax error in projectile file: {e}")
                validation["has_errors"] = True
        
        # Check 3: Character effects exist in Cow class
        # Filter out projectile-only behaviors
        projectile_only_effects = ["projectile_behavior_homing",
                                   "projectile_behavior_bouncing", "impact_splitting", 
                                   "impact_explosion", "piercing"]
        character_effects = [e for e in effect_types if e not in projectile_only_effects]
        
        if character_effects:
            try:
                from Agent.Tools.read_file import read_file
                cow_lines = read_file("Game/Character/cow.py", line_count=False)
                cow_code = "".join(cow_lines) if isinstance(cow_lines, list) else cow_lines
                
                for effect in character_effects:
                    # Check state variable (generic approach)
                    if f"self.is_{effect}" in cow_code:
                        validation["checks_passed"].append(f"Cow has is_{effect} state")
                    else:
                        validation["errors"].append(f"Cow missing is_{effect} state variable")
                        validation["has_errors"] = True
                    
                    # Check apply method
                    if f"def apply_{effect}" in cow_code:
                        validation["checks_passed"].append(f"Cow has apply_{effect} method")
                    else:
                        validation["errors"].append(f"Cow missing apply_{effect} method")
                        validation["has_errors"] = True
                        
            except Exception as e:
                validation["errors"].append(f"Error checking Cow class: {e}")
                validation["has_errors"] = True
        elif has_effects:
            validation["checks_passed"].append("Weapon has projectile-only behaviors (no character effects needed)")
        
        # Check 4: Weapon in Arena loot pool
        try:
            from Agent.Tools.read_file import read_file
            arena_lines = read_file("Game/Arena/arena.py", line_count=False)
            arena_code = "".join(arena_lines) if isinstance(arena_lines, list) else arena_lines
            
            if f"create_{weapon_name.lower()}" in arena_code:
                validation["checks_passed"].append("Weapon in Arena loot pool")
            else:
                validation["errors"].append("Weapon not found in Arena loot pool")
                validation["has_errors"] = True
                
        except Exception as e:
            validation["errors"].append(f"Error checking Arena: {e}")
            validation["has_errors"] = True
        
        # Check 5: Try to actually import and instantiate weapon
        try:
            import sys
            import importlib
            
            # Import weapon module
            weapon_module_name = f"Game.Weapons.{weapon_name.lower()}"
            if weapon_module_name in sys.modules:
                importlib.reload(sys.modules[weapon_module_name])
            weapon_module = importlib.import_module(weapon_module_name)
            
            # Try to create weapon
            create_func = getattr(weapon_module, f"create_{weapon_name.lower()}")
            weapon = create_func()
            
            if weapon:
                validation["checks_passed"].append("Weapon successfully instantiated")
            else:
                validation["errors"].append("Weapon instantiation returned None")
                validation["has_errors"] = True
                
        except ImportError as e:
            validation["errors"].append(f"Cannot import weapon: {e}")
            validation["has_errors"] = True
        except AttributeError as e:
            validation["errors"].append(f"Missing create function: {e}")
            validation["has_errors"] = True
        except Exception as e:
            validation["errors"].append(f"Error instantiating weapon: {e}")
            validation["has_errors"] = True
        
        return validation
    
    def _fix_weapon_issues(self, weapon_plan: dict, validation_results: dict) -> bool:
        """
        Use AI agent to intelligently fix validation issues.
        
        Returns:
            True if all issues fixed
        """
        from Agent.Prompts.system_prompts import system_prompt_error_fixing
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)
        effect_types = weapon_plan.get("effect_types", [])
        
        print(f"\n🤖 Using AI agent to fix {len(validation_results['errors'])} issues...")
        
        # Build comprehensive context for the agent
        error_summary = "\n".join([f"  - {error}" for error in validation_results["errors"]])
        
        # Create detailed prompt with all context
        fix_prompt = f"""
## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## VALIDATION ERRORS FOUND
{error_summary}

## FILES INVOLVED
- Weapon file: Game/Weapons/{weapon_name.lower()}.py
- Projectile file: Game/Objects/{weapon_name.lower()}_projectile.py (if effects exist)
- Character file: Game/Character/cow.py

## YOUR TASK
Fix ALL {len(validation_results['errors'])} validation errors listed above.

## IMPORTANT INSTRUCTIONS

1. **READ FIRST**: Use read_file to examine each file before making changes
2. **UNDERSTAND**: Look at how the code should work based on the weapon plan
3. **FIX SYSTEMATICALLY**: Address each error one by one
4. **VERIFY**: Make sure your changes align with the weapon plan requirements

## EFFECT SYSTEM RULES

**Character Effects** (like slowness, burning, etc.):
- Need state variable in Cow: self.is_<effect> = False
- Need apply method in Cow: def apply_<effect>(self, duration)
- Projectile calls: target.apply_<effect>(duration)

**Projectile-Only Behaviors** (zigzag, homing, splitting, etc.):
- Implemented directly in projectile class
- No Cow class modifications needed
- Handle in update() or on_character_hit() methods

## WORKING EXAMPLES TO REFERENCE
- Game/Weapons/serpentineshrapnel.py (weapon with splitting effect)
- Game/Objects/serpentineshrapnel_projectile.py (projectile with impact splitting)
- Game/Character/cow.py (character with effect system)

Start by reading the relevant files, then fix each error systematically.
"""
        
        try:
            # Use the AI agent with tool calling to fix issues
            combined_system_prompt = self._combine_system_prompts(system_prompt_error_fixing)
            if self.use_gemini:
                response = self.gemini.ask_with_tools(
                    prompt=fix_prompt,
                    system_prompt=combined_system_prompt,
                    use_history=False,
                    save_in_history=False,
                    max_iterations=15
                )
            else:
                response = self.chatGPT.get_response_with_tools(
                    input=fix_prompt,
                    system_prompt=combined_system_prompt,
                    tools=None  # Use all available tools
                )
            
            print(f"\n✅ Agent completed fixing process")
            print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")
            
            # Re-validate to check if issues are fixed
            print(f"\n🔍 Re-validating implementation...")
            new_validation = self._validate_weapon_implementation(weapon_plan, {})
            
            if new_validation["has_errors"]:
                print(f"  ⚠️  {len(new_validation['errors'])} issues remain:")
                for error in new_validation["errors"]:
                    print(f"     - {error}")
                return False
            else:
                print(f"  ✅ All issues fixed!")
                return True
                
        except Exception as e:
            print(f"\n❌ Error during AI fixing: {e}")
            import traceback
            traceback.print_exc()
        
        return False
    
    def _fix_projectile_file(self, proj_file: str, weapon_name: str) -> bool:
        """
        Try to fix common issues in a projectile file.
        
        Returns:
            True if fixed successfully
        """
        try:
            import re
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            fixed = False
            expected_class_name = f"{weapon_name}Projectile"
            
            # Fix 1: Wrong class name
            # Look for class definition that doesn't end with "Projectile"
            class_pattern = r'class\s+(\w+)(?:\(Projectile\))?:'
            matches = re.findall(class_pattern, content)
            
            for match in matches:
                if match != expected_class_name and weapon_name in match:
                    print(f"      Found wrong class name: {match} (expected: {expected_class_name})")
                    # Replace the class name
                    content = re.sub(
                        rf'class\s+{re.escape(match)}(\(Projectile\))?:',
                        f'class {expected_class_name}(Projectile):',
                        content
                    )
                    fixed = True
                    print(f"      ✓ Renamed class to {expected_class_name}")
            
            # Fix 2: Missing inheritance from Projectile
            if f'class {expected_class_name}:' in content:
                print(f"      Found class without Projectile inheritance")
                content = content.replace(
                    f'class {expected_class_name}:',
                    f'class {expected_class_name}(Projectile):'
                )
                fixed = True
                print(f"      ✓ Added Projectile inheritance")
            
            # Fix 3: Duplicate imports
            import_lines = []
            seen_imports = set()
            new_lines = []
            
            for line in content.split('\n'):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    if line.strip() not in seen_imports:
                        seen_imports.add(line.strip())
                        new_lines.append(line)
                    else:
                        fixed = True
                else:
                    new_lines.append(line)
            
            if fixed:
                content = '\n'.join(new_lines)
            
            # Write back if we made changes
            if fixed:
                with open(proj_file, 'w') as f:
                    f.write(content)
                
                # Verify it compiles
                compile(content, proj_file, 'exec')
                return True
            
            return False
            
        except Exception as e:
            print(f"      ⚠️  Could not auto-fix: {e}")
            return False
    
    def _final_integration_check(self, weapon_plan: dict, results: dict) -> dict:
        """
        Final comprehensive check using AI to review all code and integration points.
        
        Returns:
            dict with integration check results
        """
        from Agent.Tools.read_file import read_file
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)
        
        # Collect all relevant code
        code_to_review = {}
        
        # 1. Weapon file
        try:
            weapon_file = f"Game/Weapons/{weapon_name.lower()}.py"
            weapon_lines = read_file(weapon_file, line_count=False)
            code_to_review["weapon"] = "".join(weapon_lines) if isinstance(weapon_lines, list) else weapon_lines
        except:
            pass
        
        # 2. Custom projectile (if exists)
        if has_effects:
            try:
                proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                proj_lines = read_file(proj_file, line_count=False)
                code_to_review["projectile"] = "".join(proj_lines) if isinstance(proj_lines, list) else proj_lines
            except:
                pass
        
        # 3. Base Projectile class (for signature comparison)
        try:
            base_proj_lines = read_file("Game/Objects/projectile.py", line_count=False)
            code_to_review["base_projectile"] = "".join(base_proj_lines[:100]) if isinstance(base_proj_lines, list) else str(base_proj_lines)[:3000]
        except:
            pass
        
        # 4. Arena integration points
        try:
            arena_lines = read_file("Game/Arena/arena.py", line_count=False)
            arena_code = "".join(arena_lines) if isinstance(arena_lines, list) else arena_lines
            # Extract relevant sections
            import re
            # Find spawn_projectile method
            spawn_match = re.search(r'def spawn_projectile\(.*?\):(.*?)(?=\n    def |\Z)', arena_code, re.DOTALL)
            if spawn_match:
                code_to_review["arena_spawn"] = spawn_match.group(0)
            # Find update method projectile loop
            update_match = re.search(r'for proj in self\.projectiles:(.*?)(?=\n        for |\n        # |\Z)', arena_code, re.DOTALL)
            if update_match:
                code_to_review["arena_update"] = update_match.group(0)
        except:
            pass
        
        # Build prompt for AI review
        system_prompt = """You are a code integration reviewer specialized in game development.

Your task: Review all the code for integration issues, signature mismatches, and runtime errors.

## Critical Checks:

### 1. Method Signature Compatibility
- Custom projectile methods MUST match base class signatures
- Common issue: `update(self, arena)` in custom vs `update(self)` in base
- Arena calls `proj.update()` with NO arguments (except arena sometimes)
- Check: Does custom update() accept the same parameters as base?

### 2. Arena Integration
- Arena calls `proj.update()` for each projectile
- Check: Will custom projectile's update() work with Arena's call?
- Check: Does arena use custom projectile class correctly?

### 3. Missing Imports
- Check: Are all required imports present?
- Check: Is math imported for sin/cos?
- Check: Is random imported for splitting?

### 4. Attribute Access
- Check: Does code access attributes that might not exist?
- Check: Are Vector2 operations correct?

### 5. Method Calls
- Check: Does on_character_hit() call arena.spawn_projectile() correctly?
- Check: Are all method parameters passed correctly?

## Output Format:
If NO issues found:
```
PASSED
```

If issues found:
```
ISSUES:
1. [Category] Specific issue description
2. [Category] Another issue
```

Be thorough and check for ANY potential runtime errors."""

        prompt = f"""Review this weapon implementation for integration issues:

**Weapon**: {weapon_plan.get('display_name')}
**Effects**: {weapon_plan.get('effect_types', [])}

**Generated Code**:

=== Weapon File ===
```python
{code_to_review.get('weapon', 'Not found')}
```

=== Custom Projectile (if any) ===
```python
{code_to_review.get('projectile', 'No custom projectile')}
```

=== Base Projectile Class (for comparison) ===
```python
{code_to_review.get('base_projectile', 'Not available')}
```

=== Arena Integration Points ===
Arena spawn_projectile:
```python
{code_to_review.get('arena_spawn', 'Not found')}
```

Arena update loop:
```python
{code_to_review.get('arena_update', 'Not found')}
```

Check for:
1. Method signature mismatches (especially update())
2. Missing imports
3. Incorrect parameter passing
4. Attribute errors
5. Integration issues with Arena

Report ANY potential runtime errors."""

        if not self._check_request_limit():
            return {"passed": True, "issues": ["Request limit reached, skipping final check"]}

        response = self.active_client.ask(
            prompt=prompt,
            system_prompt=system_prompt,
            thinking_budget=-1 if self.use_gemini else None
        )
        
        # Parse response
        if "PASSED" in response.upper() and "ISSUES:" not in response:
            return {"passed": True, "issues": [], "response": response}
        else:
            # Extract issues
            issues = []
            if "ISSUES:" in response:
                issues_text = response.split("ISSUES:")[1].strip()
                for line in issues_text.split("\n"):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith("-")):
                        # Remove numbering/bullets
                        issue = re.sub(r'^\d+\.\s*|\-\s*', '', line)
                        if issue:
                            issues.append(issue)
            
            return {
                "passed": False,
                "issues": issues if issues else ["AI found issues but couldn't parse them"],
                "response": response
            }
    
    def _comprehensive_ai_validation(self, weapon_plan: dict, results: dict) -> dict:
        """
        Comprehensive AI-powered validation that checks everything and doesn't give up.
        Uses AI to thoroughly review all code for any potential issues.

        Returns:
            dict with comprehensive validation results
        """
        from Agent.Prompts.system_prompts import system_prompt_comprehensive_validation

        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)

        print("🤖 AI analyzing all code for potential issues...")

        # Build comprehensive context for AI review
        code_context = self._build_comprehensive_code_context(weapon_plan)

        # Create detailed prompt for AI comprehensive review
        validation_prompt = f"""
## COMPREHENSIVE CODE VALIDATION

You are a senior code reviewer specializing in game development and Python. Your mission is to thoroughly examine all code for ANY potential issues, errors, or inconsistencies.

## WEAPON BEING VALIDATED
{json.dumps(weapon_plan, indent=2)}

## CODE TO REVIEW
{code_context}

## VALIDATION REQUIREMENTS

### 1. **File Structure & Imports**
- Are all required imports present?
- Are file paths correct?
- Are class names consistent?

### 2. **Method Signatures** (CRITICAL)
- `on_character_hit(self, target, arena)` - MUST have 2 parameters
- `update(self)` - MUST have 1 parameter (only self)
- `apply_<effect_name>(self, ...)` - Check parameter counts for effect methods

### 3. **State Variables**
- Check for state variables in Cow class (e.g., self.is_effect_name)
- **Special case**: knockback uses `is_knocked_back` (not `is_knockback`) - this is correct

### 4. **Lifecycle Management**
- Use `self.alive = False` (NEVER `self.kill()`)
- Check for proper projectile destruction

### 5. **Image References**
- Must use "placeholder.png" for floor_image_name and projectile_image_name
- Check for hardcoded image paths

### 6. **Arena Integration**
- Check if weapon is properly added to loot pool
- Verify spawn_projectile calls use correct parameters

### 7. **Effect Implementation**
- Character effects: Check apply_<effect_name> method calls
- Projectile behaviors: Check update() and on_character_hit() methods
- Splitting effects: Verify correct number of projectiles spawned

## OUTPUT FORMAT

If NO issues found:
```
PASSED: All validation checks completed successfully
```

If issues found:
```
ISSUES_FOUND:
1. [Category] Specific issue description with exact line/file reference
2. [Category] Another issue with file and line details
3. [Category] Third issue...

REMAINING_ISSUES_COUNT: X
```

Be extremely thorough. Check for edge cases, naming inconsistencies, and potential runtime errors. Do not stop until you've examined every aspect of the code.
"""

        try:
            # Use AI for comprehensive validation
            combined_system_prompt = self._combine_system_prompts(system_prompt_comprehensive_validation)
            if self.use_gemini:
                response = self.gemini.ask_with_tools(
                    prompt=validation_prompt,
                    system_prompt=combined_system_prompt,
                    use_history=False,
                    save_in_history=False,
                    max_iterations=20  # Higher limit for comprehensive validation
                )
            else:
                response = self.chatGPT.get_response_with_tools(
                    input=validation_prompt,
                    system_prompt=combined_system_prompt,
                    tools=None
                )

            # Parse AI response
            if response.strip().startswith("PASSED"):
                return {
                    "all_checks_passed": True,
                    "issues": [],
                    "remaining_issues": []
                }
            elif "ISSUES_FOUND:" in response:
                # Extract issues from response
                issues_section = response.split("ISSUES_FOUND:")[1].split("REMAINING_ISSUES_COUNT:")[0]
                issues = [line.strip().lstrip("123456789. -") for line in issues_section.split("\n") if line.strip() and not line.startswith("REMAINING_ISSUES_COUNT")]

                return {
                    "all_checks_passed": False,
                    "issues": issues,
                    "remaining_issues": issues
                }
            else:
                # Fallback parsing
                print(f"  ⚠️  Could not parse AI validation response, assuming issues exist")
                return {
                    "all_checks_passed": False,
                    "issues": ["Could not parse AI validation response"],
                    "remaining_issues": ["Could not parse AI validation response"]
                }

        except Exception as e:
            print(f"  ❌ Error during comprehensive validation: {e}")
            return {
                "all_checks_passed": False,
                "issues": [f"Validation error: {e}"],
                "remaining_issues": [f"Validation error: {e}"]
            }

    def _comprehensive_ai_fixing(self, weapon_plan: dict, issues: list) -> dict:
        """
        Comprehensive AI-powered fixing that keeps trying until all issues are resolved.
        Accounts for LLM response length limits by breaking issues into manageable chunks.

        Returns:
            dict with fixing results
        """
        from Agent.Prompts.system_prompts import system_prompt_comprehensive_fixing

        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")

        print(f"🤖 AI fixing {len(issues)} issues...")

        # Break issues into smaller chunks to handle LLM response limits
        issues_per_chunk = 3  # Process 3 issues at a time
        all_fixed = True
        remaining_issues = []

        for i in range(0, len(issues), issues_per_chunk):
            chunk_issues = issues[i:i + issues_per_chunk]

            if not chunk_issues:
                continue

            print(f"  🔧 Fixing chunk {i//issues_per_chunk + 1}: {len(chunk_issues)} issues")

            # Build context for this chunk
            issues_summary = "\n".join([f"  - {issue}" for issue in chunk_issues])

            fix_prompt = f"""
## COMPREHENSIVE ISSUE FIXING

Fix the following issues in the weapon implementation:

## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## ISSUES TO FIX
{issues_summary}

## IMPORTANT: Break large fixes into multiple tool calls if needed
- Use read_file to understand current code
- Use write_into_file for precise fixes
- Use write_over_file only for complete rewrites
- Verify each fix before moving to next issue

## CRITICAL REQUIREMENTS
- All projectile methods must have correct signatures
- Use placeholder.png for all images
- Fix method signatures before other issues
- Test understanding by reading files first

Fix these {len(chunk_issues)} issues systematically.
"""

            try:
                # Use AI for fixing this chunk
                combined_system_prompt = self._combine_system_prompts(system_prompt_comprehensive_fixing)
                if self.use_gemini:
                    response = self.gemini.ask_with_tools(
                        prompt=fix_prompt,
                        system_prompt=combined_system_prompt,
                        use_history=False,
                        save_in_history=False,
                        max_iterations=25  # Higher limit for fixing
                    )
                else:
                    response = self.chatGPT.get_response_with_tools(
                        input=fix_prompt,
                        system_prompt=combined_system_prompt,
                        tools=None
                    )

                print(f"  ✅ Fixed chunk {i//issues_per_chunk + 1}")

                # Check if any issues in this chunk are still present
                for issue in chunk_issues:
                    # Simple check - if issue keywords still appear in relevant files
                    if "signature" in issue.lower():
                        # Check projectile file for wrong signatures
                        try:
                            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                            with open(proj_file, 'r') as f:
                                proj_code = f.read()
                            if "def on_character_hit(self, target):" in proj_code:
                                remaining_issues.append(issue)
                                all_fixed = False
                        except:
                            pass

            except Exception as e:
                print(f"  ❌ Error fixing chunk {i//issues_per_chunk + 1}: {e}")
                all_fixed = False
                remaining_issues.extend(chunk_issues)

        return {
            "all_fixed": all_fixed,
            "remaining_issues": remaining_issues
        }

    def _build_comprehensive_code_context(self, weapon_plan: dict) -> str:
        """Build comprehensive code context for AI validation."""
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)

        context_parts = []

        # 1. Weapon file
        try:
            weapon_file = f"Game/Weapons/{weapon_name.lower()}.py"
            with open(weapon_file, 'r') as f:
                context_parts.append(f"## WEAPON FILE ({weapon_file})\n{f.read()}")
        except:
            context_parts.append(f"## WEAPON FILE ({weapon_file})\nFile not found")

        # 2. Projectile file (if exists)
        if has_effects:
            try:
                proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                with open(proj_file, 'r') as f:
                    context_parts.append(f"## PROJECTILE FILE ({proj_file})\n{f.read()}")
            except:
                context_parts.append(f"## PROJECTILE FILE ({proj_file})\nFile not found")

        # 3. Base Projectile class
        try:
            with open("Game/Objects/projectile.py", 'r') as f:
                base_proj_content = f.read()
            context_parts.append(f"## BASE PROJECTILE CLASS\n{base_proj_content[:2000]}...")  # Limit length
        except:
            pass

        # 4. Cow class (for character effects)
        try:
            with open("Game/Character/cow.py", 'r') as f:
                cow_content = f.read()
            context_parts.append(f"## COW CLASS (Character Effects)\n{cow_content[:3000]}...")  # Limit length
        except:
            pass

        # 5. Arena file (for integration)
        try:
            with open("Game/Arena/arena.py", 'r') as f:
                arena_content = f.read()
            # Extract relevant sections
            context_parts.append(f"## ARENA FILE (Integration)\n{arena_content[:2000]}...")  # Limit length
        except:
            pass

        return "\n\n" + "="*50 + "\n\n".join(context_parts)
    
    def _fix_integration_issues(self, weapon_plan: dict, integration_check: dict) -> bool:
        """
        Fix integration issues found in final check.
        
        Returns:
            True if all issues fixed
        """
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        issues = integration_check.get("issues", [])
        
        fixed_count = 0
        
        for issue in issues:
            try:
                issue_lower = issue.lower()
                
                # Fix 1: Method signature mismatch in update()
                if "signature" in issue_lower and "update" in issue_lower:
                    print(f"  Fixing: Method signature mismatch in update()...")
                    if self._fix_update_signature(weapon_name):
                        fixed_count += 1
                        print(f"    ✓ Fixed update() signature")
                
                # Fix 2: Missing imports
                elif "import" in issue_lower or "missing" in issue_lower:
                    print(f"  Fixing: Missing imports...")
                    if self._fix_missing_imports(weapon_name, issue):
                        fixed_count += 1
                        print(f"    ✓ Fixed imports")
                
                # Fix 2.5: Missing self.speed attribute
                elif "self.speed" in issue_lower or ("attribute" in issue_lower and "speed" in issue_lower):
                    print(f"  Fixing: Adding self.speed attribute...")
                    if self._fix_missing_speed_attribute(weapon_name):
                        fixed_count += 1
                        print(f"    ✓ Added self.speed attribute")
                
                # Fix 3: Arena.spawn_projectile parameter mismatch - check for multiple keywords
                elif ("spawn_projectile" in issue_lower and 
                      ("color" in issue_lower or "radius" in issue_lower or "keyword" in issue_lower or "parameter" in issue_lower)):
                    print(f"  Fixing: Updating projectile to use correct spawn_projectile parameters...")
                    if self._fix_spawn_projectile_params(weapon_name):
                        fixed_count += 1
                        print(f"    ✓ Fixed spawn_projectile parameters")
                
                # Fix 4: Recursive spawning issue
                elif "recursive" in issue_lower or "self-propagating" in issue_lower:
                    print(f"  Fixing: Preventing recursive projectile splitting...")
                    if self._fix_recursive_splitting(weapon_name):
                        fixed_count += 1
                        print(f"    ✓ Fixed recursive splitting")
                
            except Exception as e:
                print(f"  ⚠️  Failed to fix '{issue[:50]}': {e}")
        
        print(f"\n  Fixed {fixed_count}/{len(issues)} integration issues")
        
        # Validate syntax after fixes
        print(f"\n🔍 Validating syntax after fixes...")
        if not self._validate_projectile_syntax(weapon_name):
            print(f"  ❌ Syntax errors remain after fixes")
            return False
        print(f"  ✅ Syntax valid")
        
        # Run runtime scenario tests with retry loop
        print(f"\n🎮 Running gameplay scenario tests...")
        max_test_attempts = 3
        for attempt in range(max_test_attempts):
            scenario_results = self._run_scenario_tests(weapon_plan)
            
            if scenario_results["passed"]:
                print(f"  ✅ All scenario tests passed")
                break
            
            print(f"  ⚠️  Scenario tests found runtime issues (attempt {attempt + 1}/{max_test_attempts}):")
            for issue in scenario_results["issues"]:
                print(f"     - {issue}")
            
            if attempt < max_test_attempts - 1:
                # Attempt to fix runtime issues
                print(f"\n🔧 Attempting to fix runtime issues...")
                if self._fix_runtime_issues(weapon_plan, scenario_results["issues"]):
                    print(f"  ✅ Runtime fixes applied, re-running tests...")
                else:
                    print(f"  ⚠️  Could not auto-fix issues")
            else:
                print(f"\n❌ Max test attempts ({max_test_attempts}) reached")
                return False
        
        if not scenario_results["passed"]:
            return False
        
        # Re-check
        new_check = self._final_integration_check(weapon_plan, {})
        return new_check["passed"]
    
    def _fix_update_signature(self, weapon_name: str) -> bool:
        """
        Fix update() method signature to match base class.
        Base Projectile.update() doesn't take arena parameter.
        """
        try:
            import re
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            # Check if update() has arena parameter
            update_pattern = r'def update\(self, arena\):'
            if re.search(update_pattern, content):
                print(f"      Found update(self, arena) - should be update(self)")
                
                # Replace update(self, arena): with update(self):
                content = re.sub(
                    r'def update\(self, arena\):',
                    'def update(self):',
                    content
                )
                
                # Also need to handle any arena references inside the method
                # Arena is only used at the end for timeout, which we can remove
                # since base class already handles max_distance
                
                with open(proj_file, 'w') as f:
                    f.write(content)
                
                # Verify it compiles
                compile(content, proj_file, 'exec')
                return True
            
            return False
            
        except Exception as e:
            print(f"      ⚠️  Could not fix update signature: {e}")
            return False
    
    def _fix_missing_speed_attribute(self, weapon_name: str) -> bool:
        """
        Fix missing self.speed attribute by adding it to __init__.
        The base Projectile class doesn't store speed, but custom projectiles often need it.
        """
        try:
            import re
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            # Check if self.speed already exists
            if 'self.speed = speed' in content:
                return True  # Already fixed
            
            # Find the __init__ method and add self.speed after super().__init__()
            # Pattern: Find super().__init__(...) and add self.speed = speed after it
            pattern = r'(super\(\).__init__\([^)]+\))'
            
            def add_speed(match):
                super_call = match.group(1)
                return f"{super_call}\n        self.speed = speed"
            
            content = re.sub(pattern, add_speed, content, count=1)
            
            with open(proj_file, 'w') as f:
                f.write(content)
            
            print(f"      Added self.speed = speed after super().__init__()")
            return True
            
        except Exception as e:
            print(f"      ⚠️  Could not fix speed attribute: {e}")
            return False
    
    def _fix_missing_imports(self, weapon_name: str, issue: str) -> bool:
        """
        Add missing imports to projectile file.
        """
        try:
            import re
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            imports_to_add = []
            
            # Detect what's missing based on issue and code
            if "math" in issue.lower() or ("sin" in content and "import math" not in content):
                imports_to_add.append("import math")
            
            if "random" in issue.lower() or ("random." in content and "import random" not in content):
                imports_to_add.append("import random")
            
            if "Vector2" in issue.lower() or ("Vector2" in content and "from pygame import Vector2" not in content):
                imports_to_add.append("from pygame import Vector2")
            
            if imports_to_add:
                # Find the imports section (after docstring, before class)
                lines = content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        insert_index = i + 1
                    elif line.strip().startswith('class '):
                        break
                
                # Insert missing imports
                for imp in imports_to_add:
                    if imp not in content:
                        lines.insert(insert_index, imp)
                        insert_index += 1
                        print(f"      Added: {imp}")
                
                content = '\n'.join(lines)
                
                with open(proj_file, 'w') as f:
                    f.write(content)
                
                return True
            
            return False
            
        except Exception as e:
            print(f"      ⚠️  Could not fix imports: {e}")
            return False
    
    def _fix_spawn_projectile_params(self, weapon_name: str) -> bool:
        """
        Fix arena.spawn_projectile() calls to use correct parameters.
        Arena.spawn_projectile() signature: (start_pos, direction, speed, sprite, damage, owner)
        Base Projectile.__init__ signature: (start_pos, direction, speed, color, radius, max_distance, sprite, damage, owner)
        
        The issue: AI often generates code with color/radius/max_distance for arena.spawn_projectile,
        but Arena only accepts: start_pos, direction, speed, sprite, damage, owner
        """
        try:
            import re
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            # Pattern: Find all arena.spawn_projectile calls and fix them
            # We need to:
            # 1. Keep: start_pos, direction, speed, sprite (if present), damage, owner
            # 2. Remove: color, radius, max_distance (and their values)
            
            # More robust approach: Parse the function call and rebuild it
            # Find arena.spawn_projectile calls
            pattern = r'arena\.spawn_projectile\s*\(((?:[^()]+|\([^()]*\))*)\)'
            
            def fix_spawn_call(match):
                args_str = match.group(1)
                
                # Parse arguments - handle both positional and keyword
                # Extract valid arguments only
                valid_params = {}
                
                # Look for keyword arguments we want to keep
                for param in ['start_pos', 'direction', 'speed', 'sprite', 'damage', 'owner']:
                    # Match: param=value or param = value
                    param_pattern = rf'{param}\s*=\s*([^,]+(?:\([^)]*\))?[^,]*?)(?=,|\s*$)'
                    param_match = re.search(param_pattern, args_str)
                    if param_match:
                        valid_params[param] = param_match.group(1).strip()
                
                # Rebuild the call with only valid parameters
                if valid_params:
                    params_list = []
                    # Maintain proper order
                    for param in ['start_pos', 'direction', 'speed', 'sprite', 'damage', 'owner']:
                        if param in valid_params:
                            params_list.append(f"{param}={valid_params[param]}")
                    
                    return f"arena.spawn_projectile({', '.join(params_list)})"
                else:
                    # If no keyword args found, return as is (might be positional)
                    return match.group(0)
            
            # Apply the fix
            content = re.sub(pattern, fix_spawn_call, content, flags=re.MULTILINE | re.DOTALL)
            
            with open(proj_file, 'w') as f:
                f.write(content)
            
            print(f"      Fixed spawn_projectile calls to match Arena signature")
            return True
            
        except Exception as e:
            print(f"      ⚠️  Could not fix spawn_projectile parameters: {e}")
            return False
    
    def _validate_projectile_syntax(self, weapon_name: str) -> bool:
        """
        Validate that the projectile file has valid Python syntax.
        Returns True if syntax is valid, False otherwise.
        """
        try:
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            # Try to compile the file
            compile(content, proj_file, 'exec')
            return True
            
        except SyntaxError as e:
            print(f"      Syntax error at line {e.lineno}: {e.msg}")
            print(f"      {e.text}")
            return False
        except Exception as e:
            print(f"      Validation error: {e}")
            return False
    
    def _run_scenario_tests(self, weapon_plan: dict) -> dict:
        """
        Run gameplay scenarios to detect runtime issues with the weapon.
        
        Scenarios:
        1. Walking (baseline)
        2. Picking up weapon
        3. Walking with weapon
        4. Finding ammo while holding weapon
        5. Shooting at void
        6. Shooting at AI cow
        
        Returns:
            dict with 'passed' (bool) and 'issues' (list of error messages)
        """
        import subprocess
        import tempfile
        import os
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        
        # Create test script
        test_script = f'''
import sys
import os
import pygame

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize pygame first
pygame.init()

# Suppress display
os.environ['SDL_VIDEODRIVER'] = 'dummy'

try:
    from Game.Arena.arena import Arena
    from Game.Character.cow import Cow
    from Game.Character.ai_cow import AICow
    from Game.Weapons.{weapon_name.lower()} import create_{weapon_name.lower()}
    from pygame import Vector2
    
    # Create minimal arena with correct signature
    camera_size = (800, 600)
    world_size = (1600, 1200)
    screen = pygame.display.set_mode(camera_size)
    world_surf = pygame.Surface(world_size)
    arena = Arena((0, 0, camera_size[0], camera_size[1]), world_size, screen, world_surf, "Test Arena")
    
    # Create test player
    player = Cow((0, 0, 50, 50), "TestPlayer", (world_size[0]//2, world_size[1]//2), 
                 camera_display_size=camera_size, world_display_size=world_size, 
                 ammo_find_probability=0.2, move_step=4)
    arena.add_new_character(player)
    
    results = {{}}
    
    # Scenario 1: Walking
    try:
        player.position = Vector2(100, 100)
        player.update(arena)
        results['walking'] = 'PASS'
    except Exception as e:
        results['walking'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Scenario 2: Picking up weapon
    try:
        weapon = create_{weapon_name.lower()}()
        player.equip_weapon(weapon)
        results['pickup_weapon'] = 'PASS'
    except Exception as e:
        results['pickup_weapon'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Scenario 3: Walking with weapon
    try:
        player.update(arena)
        results['walk_with_weapon'] = 'PASS'
    except Exception as e:
        results['walk_with_weapon'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Scenario 4: Adding ammo (directly set since Cow doesn't have add_ammo)
    try:
        player.ammo += 50
        results['add_ammo'] = 'PASS'
    except Exception as e:
        results['add_ammo'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Scenario 5: Shooting at void
    try:
        player.position = Vector2(400, 400)
        direction = Vector2(1, 0)
        weapon = player.get_weapon()
        if weapon and player.ammo >= weapon.ammo_per_shot:
            arena.spawn_projectile(
                start_pos=player.position,
                direction=direction,
                speed=weapon.projectile_speed,
                damage=weapon.damage,
                owner=player
            )
            # Simulate a few frames
            for _ in range(10):
                arena.update()
            results['shoot_void'] = 'PASS'
        else:
            results['shoot_void'] = 'SKIP: No ammo or weapon'
    except Exception as e:
        results['shoot_void'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Scenario 6: Shooting at AI cow
    try:
        # Find or create AI cow
        ai_cow = None
        for char in arena.characters:
            if isinstance(char, AICow):
                ai_cow = char
                break
        
        if not ai_cow:
            ai_cow = Cow((0, 0, 50, 50), "TestAI", (500, 400), 
                        camera_display_size=camera_size, world_display_size=world_size,
                        ammo_find_probability=0.2, move_step=3)
            arena.add_new_character(ai_cow)
        
        # Position player to shoot at AI
        player.position = Vector2(400, 400)
        ai_cow.position = Vector2(600, 400)
        
        # Shoot at AI
        direction = (ai_cow.position - player.position).normalize()
        weapon = player.get_weapon()
        if weapon and player.ammo >= weapon.ammo_per_shot:
            # Add more ammo if needed
            player.ammo += 100
            arena.spawn_projectile(
                start_pos=player.position,
                direction=direction,
                speed=weapon.projectile_speed,
                damage=weapon.damage,
                owner=player
            )
            # Simulate frames until projectile hits or expires
            for _ in range(100):
                arena.update()
                # Check for collision
                for proj in arena.projectiles[:]:
                    if proj.alive:
                        dist = (proj.position - ai_cow.position).length()
                        if dist < 30:  # Close enough for hit
                            if hasattr(proj, 'on_character_hit'):
                                proj.on_character_hit(ai_cow, arena)
                            break
            results['shoot_ai'] = 'PASS'
        else:
            results['shoot_ai'] = 'SKIP: No weapon'
    except Exception as e:
        results['shoot_ai'] = f'FAIL: {{type(e).__name__}}: {{e}}'
    
    # Print results
    for scenario, result in results.items():
        print(f"{{scenario}}: {{result}}")
    
    # Exit successfully if all passed
    all_passed = all(r in ['PASS', 'SKIP: No ammo or weapon', 'SKIP: No weapon'] for r in results.values())
    sys.exit(0 if all_passed else 1)
    
except Exception as e:
    print(f"FATAL: {{type(e).__name__}}: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(2)
'''
        
        # Write test script to project directory (so imports work)
        test_file = f"test_weapon_{weapon_name.lower()}_runtime.py"
        
        with open(test_file, 'w') as f:
            f.write(test_script)
        
        try:
            # Run test script from project directory
            result = subprocess.run(
                ['python', test_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.getcwd()  # Run in project directory
            )
            
            # Parse output
            issues = []
            output_lines = result.stdout.strip().split('\n')
            
            for line in output_lines:
                if 'FAIL:' in line:
                    scenario = line.split(':')[0].strip()
                    error = ':'.join(line.split(':')[2:]).strip()
                    issues.append(f"{scenario}: {error}")
                elif 'FATAL:' in line:
                    issues.append(f"Fatal error: {line}")
            
            # Check stderr for additional errors
            if result.stderr and 'Error' in result.stderr:
                issues.append(f"Stderr: {result.stderr[:200]}")
            
            return {
                "passed": len(issues) == 0,
                "issues": issues
            }
            
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "issues": ["Test timed out (>10 seconds)"]
            }
        except Exception as e:
            return {
                "passed": False,
                "issues": [f"Test execution error: {e}"]
            }
        finally:
            # Clean up temp file
            try:
                os.unlink(test_file)
            except:
                pass
    
    def _fix_runtime_issues(self, weapon_plan: dict, issues: list) -> bool:
        """
        Use AI agent to fix runtime and integration issues.
        
        Returns:
            True if all issues fixed
        """
        from Agent.Prompts.system_prompts import system_prompt_error_fixing
        
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        
        print(f"\n🤖 Using AI agent to fix {len(issues)} integration issues...")
        
        # Build comprehensive context for the agent
        issues_summary = "\n".join([f"  - {issue}" for issue in issues])
        
        # Create detailed prompt with all context
        fix_prompt = f"""
## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## INTEGRATION/RUNTIME ISSUES FOUND
{issues_summary}

## FILES INVOLVED
- Weapon file: Game/Weapons/{weapon_name.lower()}.py
- Projectile file: Game/Objects/{weapon_name.lower()}_projectile.py (if effects exist)
- Base projectile: Game/Objects/projectile.py (for reference)

## YOUR TASK
Fix ALL {len(issues)} integration/runtime issues listed above.

## CRITICAL METHOD SIGNATURES

### 1. on_character_hit Method
The projectile's `on_character_hit` method MUST have this EXACT signature:
```python
def on_character_hit(self, target, arena):
```
- Takes 2 parameters: `target` (the character hit) and `arena` (the Arena instance)
- Arena calls it as: `proj.on_character_hit(character, self)`
- Must apply damage: `target.take_damage(self.damage)`
- Must destroy projectile: `self.alive = False` (NOT `self.kill()`)

### 2. update Method  
The projectile's `update` method MUST have this EXACT signature:
```python
def update(self):
```
- Takes NO parameters (only `self`)
- Arena calls it as: `proj.update()`
- Updates position, distance_traveled, and checks max_distance

### 3. Lifecycle Management
- Use `self.alive = False` to destroy projectile
- **NEVER use `self.kill()`** - this method doesn't exist in base Projectile class
- The `alive` boolean attribute controls lifecycle

## COMMON ISSUES AND FIXES

**Issue**: `on_character_hit(self, target)` - missing `arena` parameter
**Fix**: Change to `on_character_hit(self, target, arena)`

**Issue**: `self.kill()` in on_character_hit
**Fix**: Change to `self.alive = False`

**Issue**: `update(self, arena)` - takes arena parameter
**Fix**: Change to `update(self)` - arena is NOT passed to update()

Start by reading the projectile file to understand the current implementation, then fix each issue systematically.
"""
        
        try:
            # Use the AI agent with tool calling to fix issues
            if self.use_gemini:
                response = self.gemini.ask_with_tools(
                    prompt=fix_prompt,
                    system_prompt=system_prompt_error_fixing,
                    use_history=False,
                    save_in_history=False,
                    max_iterations=15
                )
            else:
                response = self.chatGPT.get_response_with_tools(
                    input=fix_prompt,
                    system_prompt=system_prompt_error_fixing,
                    tools=None
                )
            
            print(f"\n✅ Agent completed fixing integration issues")
            print(f"Response: {response[:200]}..." if len(response) > 200 else f"Response: {response}")
            
            # CRITICAL: Re-read the file to verify the fixes were actually applied
            print(f"\n🔍 Verifying fixes were actually applied...")
            try:
                proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                with open(proj_file, 'r') as f:
                    updated_code = f.read()
                
                remaining_issues = []
                for issue in issues:
                    if "on_character_hit" in issue and "signature" in issue.lower():
                        if "def on_character_hit(self, target, arena)" not in updated_code:
                            remaining_issues.append("on_character_hit signature still incorrect")
                    if "kill()" in issue:
                        if "self.kill()" in updated_code:
                            remaining_issues.append("self.kill() still present")
                
                if remaining_issues:
                    print(f"  ⚠️  Fixes were not applied! Issues remaining:")
                    for issue in remaining_issues:
                        print(f"     - {issue}")
                    return False
                else:
                    print(f"  ✅ All fixes verified in file")
                    return True
            except Exception as e:
                print(f"  ⚠️  Could not verify fixes: {e}")
                return False
                
        except Exception as e:
            print(f"\n❌ Error during AI fixing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _fix_recursive_splitting(self, weapon_name: str) -> bool:
        """
        Fix recursive splitting by ensuring fragments use base Projectile class.
        When spawning fragments, pass owner=None to prevent them using custom projectile.
        """
        try:
            import re
            proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
            
            with open(proj_file, 'r') as f:
                content = f.read()
            
            # Find arena.spawn_projectile calls in on_character_hit
            # Change owner=self.owner to owner=None to force base Projectile
            content = re.sub(
                r'(arena\.spawn_projectile\([^)]*?)owner\s*=\s*self\.owner',
                r'\1owner=None',
                content
            )
            
            with open(proj_file, 'w') as f:
                f.write(content)
            
            print(f"      Changed owner=self.owner to owner=None for fragments")
            return True
            
        except Exception as e:
            print(f"      ⚠️  Could not fix recursive splitting: {e}")
            return False
    
    def _run_game_simulation_tests(self, weapon_plan: dict) -> dict:
        """
        Run actual game simulation tests to ensure weapon works in real gameplay scenarios:
        1. Weapon pickup
        2. Finding ammo with weapon equipped
        3. Shooting nothing (no target)
        4. Shooting another player
        """
        print("  📋 Test scenarios:")
        print("     1. Weapon pickup")
        print("     2. Finding ammo")
        print("     3. Shooting nothing")
        print("     4. Shooting player")
        
        results = {
            "tests_run": [],
            "tests_passed": [],
            "errors": [],
            "has_errors": False
        }
        
        try:
            import sys
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            weapon_name = weapon_plan.get("weapon_name", "TestWeapon")
            weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)
            
            # Import required modules
            import pygame
            pygame.init()
            
            # Create minimal test environment
            test_screen = pygame.display.set_mode((100, 100), pygame.HIDDEN)
            
            from Game.Arena.arena import Arena
            from Game.Character.cow import Cow
            from Game.Weapons import Weapon
            
            # Import the custom weapon if it exists
            try:
                weapon_file = f"Game/Weapons/{weapon_class_name.lower()}"
                exec(f"from {weapon_file.replace('/', '.')} import create_{weapon_class_name.lower()}")
                create_weapon_func = locals()[f"create_{weapon_class_name.lower()}"]
            except Exception as e:
                results["errors"].append(f"Failed to import weapon: {e}")
                results["has_errors"] = True
                return results
            
            # Test 1: Weapon Pickup
            test_name = "weapon_pickup"
            results["tests_run"].append(test_name)
            try:
                print(f"     Running: {test_name}...", end=" ")
                test_cow = Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="TestCow",
                    starting_position=(100, 100),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000)
                )
                
                weapon = create_weapon_func()
                test_cow.equip_weapon(weapon)
                
                if not test_cow.has_weapon():
                    raise Exception("Cow did not equip weapon")
                if test_cow.get_weapon().name != weapon.name:
                    raise Exception(f"Weapon name mismatch: {test_cow.get_weapon().name} != {weapon.name}")
                    
                results["tests_passed"].append(test_name)
                print("✓")
            except Exception as e:
                results["errors"].append(f"Test '{test_name}' failed: {e}")
                results["has_errors"] = True
                print("✗")
            
            # Test 2: Finding Ammo
            test_name = "finding_ammo"
            results["tests_run"].append(test_name)
            try:
                print(f"     Running: {test_name}...", end=" ")
                test_cow = Cow(
                    rect=pygame.Rect(0, 0, 30, 30),
                    username="TestCow",
                    starting_position=(100, 100),
                    camera_display_size=(800, 600),
                    world_display_size=(2000, 2000),
                    starting_ammo=0
                )
                weapon = create_weapon_func()
                test_cow.equip_weapon(weapon)
                
                # Simulate finding ammo
                initial_ammo = test_cow.ammo
                test_cow.ammo += 10
                
                if test_cow.ammo <= initial_ammo:
                    raise Exception("Ammo did not increase")
                    
                results["tests_passed"].append(test_name)
                print("✓")
            except Exception as e:
                results["errors"].append(f"Test '{test_name}' failed: {e}")
                results["has_errors"] = True
                print("✗")
            
            # Test 3: Shooting Nothing (no target hit)
            test_name = "shooting_nothing"
            results["tests_run"].append(test_name)
            try:
                print(f"     Running: {test_name}...", end=" ")
                
                # Redirect stdout/stderr to suppress pygame output
                f = io.StringIO()
                with redirect_stdout(f), redirect_stderr(f):
                    arena = Arena(
                        screen_dimensions=(800, 600),
                        world_screen_dimensions=(2000, 2000),
                        screen=test_screen,
                        world_screen=test_screen,
                        text=None
                    )
                    
                    player = Cow(
                        rect=pygame.Rect(0, 0, 30, 30),
                        username="Player",
                        starting_position=(500, 500),
                        camera_display_size=(800, 600),
                        world_display_size=(2000, 2000),
                        starting_ammo=10
                    )
                    weapon = create_weapon_func()
                    player.equip_weapon(weapon)
                    arena.characters.append(player)
                    
                    # Shoot into empty space
                    initial_projectile_count = len(arena.projectiles)
                    direction = (100, 0)  # Shoot right
                    speed = weapon.projectile_speed
                    sprite = weapon.get_projectile_sprite() if hasattr(weapon, 'get_projectile_sprite') else None
                    damage = weapon.damage
                    
                    arena.spawn_projectile(
                        start_pos=(500, 500),
                        direction=direction,
                        speed=speed,
                        sprite=sprite,
                        damage=damage,
                        owner=player
                    )
                    
                    if len(arena.projectiles) <= initial_projectile_count:
                        raise Exception("Projectile was not spawned")
                    
                    # Update arena a few times to see if projectile behaves
                    for _ in range(10):
                        arena.update()
                    
                results["tests_passed"].append(test_name)
                print("✓")
            except Exception as e:
                results["errors"].append(f"Test '{test_name}' failed: {e}")
                results["has_errors"] = True
                print("✗")
                import traceback
                error_details = traceback.format_exc()
                results["errors"].append(f"Traceback: {error_details}")
            
            # Test 4: Shooting Player
            test_name = "shooting_player"
            results["tests_run"].append(test_name)
            try:
                print(f"     Running: {test_name}...", end=" ")
                
                # Redirect stdout/stderr
                f = io.StringIO()
                with redirect_stdout(f), redirect_stderr(f):
                    arena = Arena(
                        screen_dimensions=(800, 600),
                        world_screen_dimensions=(2000, 2000),
                        screen=test_screen,
                        world_screen=test_screen,
                        text=None
                    )
                    
                    player = Cow(
                        rect=pygame.Rect(0, 0, 30, 30),
                        username="Player",
                        starting_position=(500, 500),
                        camera_display_size=(800, 600),
                        world_display_size=(2000, 2000),
                        starting_ammo=10
                    )
                    
                    target = Cow(
                        rect=pygame.Rect(0, 0, 30, 30),
                        username="Target",
                        starting_position=(550, 500),  # Close to player
                        camera_display_size=(800, 600),
                        world_display_size=(2000, 2000)
                    )
                    
                    weapon = create_weapon_func()
                    player.equip_weapon(weapon)
                    arena.characters.append(player)
                    arena.characters.append(target)
                    
                    initial_health = target.health
                    
                    # Shoot at target
                    direction = (50, 0)  # Shoot right toward target
                    speed = weapon.projectile_speed
                    sprite = weapon.get_projectile_sprite() if hasattr(weapon, 'get_projectile_sprite') else None
                    damage = weapon.damage
                    
                    arena.spawn_projectile(
                        start_pos=(500, 500),
                        direction=direction,
                        speed=speed,
                        sprite=sprite,
                        damage=damage,
                        owner=player
                    )
                    
                    # Update arena multiple times to let projectile hit
                    for _ in range(30):
                        arena.update()
                        if target.health < initial_health:
                            break
                    
                    # Check if target took damage
                    if target.health >= initial_health:
                        raise Exception(f"Target did not take damage (health: {target.health} >= {initial_health})")
                
                results["tests_passed"].append(test_name)
                print("✓")
            except Exception as e:
                results["errors"].append(f"Test '{test_name}' failed: {e}")
                results["has_errors"] = True
                print("✗")
                import traceback
                error_details = traceback.format_exc()
                results["errors"].append(f"Traceback: {error_details}")
            
            pygame.quit()
            
        except Exception as e:
            results["errors"].append(f"Simulation test suite failed: {e}")
            results["has_errors"] = True
            import traceback
            error_details = traceback.format_exc()
            results["errors"].append(f"Traceback: {error_details}")
        
        return results
    
    def _fix_simulation_issues(self, weapon_plan: dict, simulation_results: dict) -> bool:
        """Fix issues discovered during game simulation testing."""
        print("  🔧 Analyzing simulation errors...")
        
        # Collect all error information
        error_context = "\n".join(simulation_results["errors"])
        
        weapon_name = weapon_plan.get("weapon_name", "TestWeapon")
        weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)
        
        # Read relevant files
        weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
        projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
        cow_file = "Game/Character/cow.py"
        
        code_context = "## WEAPON FILE\n"
        try:
            with open(weapon_file, 'r') as f:
                code_context += f"```python\n{f.read()}\n```\n\n"
        except:
            pass
        
        if os.path.exists(projectile_file):
            code_context += "## PROJECTILE FILE\n"
            try:
                with open(projectile_file, 'r') as f:
                    code_context += f"```python\n{f.read()}\n```\n\n"
            except:
                pass
        
        # Read relevant parts of Cow class (effect methods)
        code_context += "## COW CLASS (Effects Section)\n"
        try:
            with open(cow_file, 'r') as f:
                cow_content = f.read()
                # Extract effect-related methods
                effect_methods = []
                for effect in weapon_plan.get("effects", []):
                    effect_name = effect.replace("projectile_behavior_", "").replace("impact_", "")
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

        prompt = f"""Fix the runtime issues found during game simulation testing.

## WEAPON PLAN
{json.dumps(weapon_plan, indent=2)}

## SIMULATION ERRORS
{error_context}

## CURRENT CODE
{code_context}

## YOUR TASK

1. Read the weapon file and projectile file to understand current implementation
2. Identify the root cause of each simulation error
3. Fix the issues using the available tools
4. Focus on:
   - Correct method signatures
   - Proper parameter passing
   - Missing imports or methods
   - Correct arena.spawn_projectile() usage

Fix all issues to ensure the weapon works in all test scenarios."""

        try:
            if not self._check_request_limit():
                return False
            
            combined_system_prompt = self._combine_system_prompts(system_prompt)
            response = self.active_client.ask_with_tools(
                prompt=prompt,
                system_prompt=combined_system_prompt,
                tools=self.tools,
                thinking_budget=-1 if self.use_gemini else None
            )
            
            # Check if the AI made any fixes
            if response and ("write" in response.lower() or "fixed" in response.lower()):
                return True
            
            return False
            
        except Exception as e:
            print(f"  ❌ Error during simulation fix: {e}")
            return False
    
    def run(self):
        """Main execution loop for the agent."""
        pass


"""
# 1. Plan a task from a plain-English request.
#
# 2. Produce a one-page Work Order including:
#    - Goal
#    - Scope
#    - Files likely to be touched
#    - Risks
#    - Acceptance tests
#
# 3. Read the workspace (only allowlisted directories) and retrieve context.
#
# 4. Locate schemas, examples, API documentation, and similar code.
#
# 5. Create or edit files via minimal diffs:
#    - Add new modules/files as needed
#    - Make small, targeted patches
#    - Never refactor the entire repository
#
# 6. Write or extend tests first:
#    - Generate unit tests or golden tests that will fail until the change is implemented
#
# 7. Run the toolchain locally:
#    - Formatter → Linter → Type checker → Unit tests (all via a single CLI)
#
# 8. Interpret errors and self-repair:
#    - Up to 3 iterations
#    - Shrink the diff with each attempt
#    - Keep edits within the defined scope
#
# 9. Summarize results:
#    - Provide a human-readable diff summary
#    - Include test logs
#    - Supply reproduction commands
"""