

from ast import List
import re
from Agent.Tools.get_project_structure import get_project_structure
from Agent.Tools.helpers_ignore import collect_directory_files_and_contents
from Agent.chatGPT import ChatGPT
from Agent.gemini_client import GeminiClient

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
            projectile_only_effects = ["projectile_behavior_zigzag", "projectile_behavior_homing", 
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
        floor_image_name=None,
        floor_image_scale=(28, 28),
        projectile_image_name=None,
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
        floor_image_name=None,
        floor_image_scale=(28, 28),
        projectile_image_name=None,
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
```

### 2. Effect Application
In the `on_character_hit` method:
1. Apply damage first
2. Check if target is alive
3. Apply each effect using the character's apply_effectname() method
4. Pass correct parameters based on effect type

### 3. Effect Type Patterns

**CHARACTER EFFECTS** (applied to target in on_character_hit):
- **Movement effects** (knockback): `target.apply_knockback(vector_x, vector_y, duration_ms)`
- **Status effects** (freeze, slow): `target.apply_freeze(duration_ms, slow_percent)`
- **Simple effects** (stun, burn): `target.apply_stun(duration_ms)`

**PROJECTILE BEHAVIORS** (implemented in projectile class itself):
- **projectile_behavior_zigzag**: Override update() to move in sine wave pattern
- **projectile_behavior_homing**: Override update() to track nearest target
- **impact_splitting**: In on_character_hit(), spawn 3 new projectiles in random directions
- **impact_explosion**: In on_character_hit(), damage all nearby characters
- **piercing**: Set self.can_pierce = True, don't set alive = False on hit

### 4. Examples

**Example 1: Character Effect (Freeze)**
```python
class FreezeProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (100, 150, 255), 4, 2400.0, sprite, damage, owner)
    
    def on_character_hit(self, target, arena):
        if hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        if not hasattr(target, 'is_dead') or not target.is_dead():
            if hasattr(target, 'apply_freeze'):
                target.apply_freeze(3000, 0.5)
        self.alive = False
```

**Example 2: Zigzag Behavior**
```python
class ZigzagProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (255, 200, 0), 4, 2400.0, sprite, damage, owner)
        self.time = 0
    
    def update(self, arena):
        import math
        # Zigzag motion
        perpendicular = Vector2(-self.velocity.y, self.velocity.x).normalize()
        offset = math.sin(self.time * 0.2) * 3.0
        self.position += self.velocity + perpendicular * offset
        self.time += 1
        self.distance_traveled += self.speed
        if self.distance_traveled >= self.max_distance:
            self.alive = False
```

**Example 3: Impact Splitting**
```python
class SplittingProjectile(Projectile):
    def __init__(self, position, direction, speed=16.0, damage=10.0, sprite=None, owner=None):
        super().__init__(position, direction, speed, (255, 150, 50), 4, 2400.0, sprite, damage, owner)
    
    def on_character_hit(self, target, arena):
        if hasattr(target, 'take_damage'):
            target.take_damage(self.damage)
        # Spawn 3 smaller projectiles
        import random
        from Game.Objects.projectile import Projectile
        for _ in range(3):
            angle = random.uniform(0, 2 * 3.14159)
            direction = Vector2(math.cos(angle), math.sin(angle))
            arena.spawn_projectile(self.position.copy(), direction, self.speed * 0.8, 
                                 damage=self.damage * 0.5, owner=self.owner)
        self.alive = False
```

Output ONLY the complete class definition. NO explanations."""

        # Build effect info string
        effect_info_str = ""
        for effect in effect_types:
            details = effect_details.get(effect, {})
            effect_info_str += f"\n   - {effect}: {details}"

        prompt = f"""Create a custom projectile class for weapon: {weapon_name}

**Base Projectile Class:**
```python
{projectile_str}
```

**Effects to apply:**{effect_info_str}

**Effect Details:**
{effect_details}

Generate the COMPLETE custom projectile class with:
1. Proper super().__init__() call (with color and radius!)
2. on_character_hit() method that applies all effects correctly
3. Proper parameter passing for each effect type

Use appropriate colors based on effects (e.g., blue for freeze, red for burn, etc.)."""

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
        
        # Find the weapon pickup spawn location (in handle_key_event, golden field section)
        # Look for: pickup = WeaponPickup(Weapon(name="Bow"...
        bow_pattern = r'(pickup = WeaponPickup\(Weapon\(name="Bow"[^)]+\), \(gx \+ offset, gy\)\))'
        
        match = re.search(bow_pattern, arena_content)
        if match:
            # Replace single weapon with random choice from pool
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
                
                # Verify projectile has on_character_hit method
                if "def on_character_hit" in proj_code:
                    validation["checks_passed"].append("Custom projectile has on_character_hit")
                else:
                    validation["errors"].append("Custom projectile missing on_character_hit method")
                    validation["has_errors"] = True
                
                # Verify projectile implements required behaviors
                # For projectile-only behaviors, check implementation differently
                projectile_only_effects = ["projectile_behavior_zigzag", "projectile_behavior_homing", 
                                           "projectile_behavior_bouncing", "impact_splitting", 
                                           "impact_explosion", "piercing"]
                
                for effect in effect_types:
                    if effect in projectile_only_effects:
                        # Check for behavior implementation (update method, impact handling, etc.)
                        if "zigzag" in effect and ("sin(" in proj_code or "cos(" in proj_code or "update" in proj_code):
                            validation["checks_passed"].append(f"Projectile implements {effect} behavior")
                        elif "splitting" in effect and ("spawn" in proj_code or "split" in proj_code):
                            validation["checks_passed"].append(f"Projectile implements {effect} behavior")
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
        projectile_only_effects = ["projectile_behavior_zigzag", "projectile_behavior_homing", 
                                   "projectile_behavior_bouncing", "impact_splitting", 
                                   "impact_explosion", "piercing"]
        character_effects = [e for e in effect_types if e not in projectile_only_effects]
        
        if character_effects:
            try:
                from Agent.Tools.read_file import read_file
                cow_lines = read_file("Game/Character/cow.py", line_count=False)
                cow_code = "".join(cow_lines) if isinstance(cow_lines, list) else cow_lines
                
                for effect in character_effects:
                    # Check state variable
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
        Attempt to fix issues found during validation.
        
        Returns:
            True if all issues fixed
        """
        weapon_name = weapon_plan.get("weapon_name", "CustomWeapon")
        has_effects = weapon_plan.get("has_effects", False)
        effect_types = weapon_plan.get("effect_types", [])
        
        fixed_count = 0
        
        for error in validation_results["errors"]:
            try:
                # Handle missing effect methods in Cow
                if "Cow missing" in error and "apply_" in error:
                    effect = error.split("apply_")[1].split(" ")[0]
                    print(f"  Fixing: Adding {effect} to Cow class...")
                    success = self._add_effects_to_cow([effect])
                    if success:
                        fixed_count += 1
                        print(f"    ✓ Added {effect} effect")
                
                # Handle missing effect application in projectile
                elif "Projectile doesn't apply" in error or "may not fully implement" in error:
                    effect = error.split("apply")[1].split("effect")[0].strip() if "apply" in error else error.split("implement")[1].split("(")[0].strip()
                    print(f"  Fixing: Updating projectile for {effect}...")
                    # Delete old projectile first
                    import os
                    proj_file = f"Game/Objects/{weapon_name.lower()}_projectile.py"
                    if os.path.exists(proj_file):
                        os.remove(proj_file)
                    # Recreate projectile with all effects
                    projectile_file = self._create_effect_projectile(weapon_plan)
                    if projectile_file:
                        fixed_count += 1
                        print(f"    ✓ Updated projectile")
                
                # Handle syntax errors
                elif "Syntax error" in error:
                    print(f"  ⚠️  Cannot auto-fix syntax error: {error}")
                
            except Exception as e:
                print(f"  ⚠️  Failed to fix '{error}': {e}")
        
        print(f"\n  Fixed {fixed_count}/{len(validation_results['errors'])} issues")
        
        # Re-validate
        new_validation = self._validate_weapon_implementation(weapon_plan, {})
        return not new_validation["has_errors"]
    
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