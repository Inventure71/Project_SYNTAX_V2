

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
        Complete workflow for creating a new weapon.
        Weapons are simpler than abilities - they define damage, ammo, sprites, and projectile behavior.
        
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
            "success": False,
            "errors": [],
            "backup_id": None,
            "files_created": []
        }
        
        try:
            # Step 0: Create backup
            print("\n💾 Creating backup...")
            backup_id = self._create_backup("weapon_creation")
            results["backup_id"] = backup_id
            
            # Step 1: Generate weapon code
            print("\n📋 Generating weapon...")
            weapon_code = self._generate_weapon(weapon_description)
            results["weapon_name"] = weapon_code.get("weapon_name", "CustomWeapon")
            
            # Step 2: Create weapon file
            print("\n🔨 Creating weapon file...")
            weapon_file = self._create_weapon_file(weapon_code)
            if weapon_file:
                results["files_created"].append(weapon_file)
                print(f"  ✓ Created: {weapon_file}")
            
            # Step 3: Add weapon to game (create integration example)
            print("\n🎮 Creating integration example...")
            integration = self._create_weapon_integration_example(weapon_code)
            print(f"  ✓ Weapon can be added in main.py or Arena")
            print(f"  ✓ See: {integration}")
            
            results["success"] = True
            results["integration_example"] = integration
            
        except Exception as e:
            print(f"\n❌ Workflow failed: {e}")
            results["errors"].append(str(e))
            import traceback
            traceback.print_exc()
        
        print("\n" + "="*60)
        return results
    
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