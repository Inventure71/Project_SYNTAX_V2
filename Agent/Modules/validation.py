"""
Validation logic for the agent system.
"""
import os
import re
import py_compile
from typing import Dict, List, Any, Tuple

from .utils import debug_print, safe_read_file, validate_method_signature, normalize_effects


def check_formatting_issues(code: str, filename: str) -> List[str]:
    """
    Check for common formatting issues like multiple statements on the same line.
    """
    issues = []
    lines = code.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        
        # Check for excessive whitespace followed by code (indicatessame-line statements)
        if '        ' in line and not line.strip().startswith('#'):
            # Find positions of excessive whitespace
            parts = re.split(r'( {8,})', line)
            if len(parts) > 2:
                # More than one code segment with large gaps
                first_code = parts[0].strip()
                remaining = ''.join(parts[2:]).strip()
                
                if first_code and remaining and not remaining.startswith('#'):
                    issues.append(f"{filename}:{line_num} - Multiple statements on same line (excessive whitespace detected)")
        
        # Check for specific patterns that indicate same-line statements
        suspicious_patterns = [
            (r'\)[ ]{5,}\w+', 'Code after closing bracket with excessive spaces'),
            (r'\][ ]{5,}\w+', 'Code after closing bracket with excessive spaces'),
            (r'[a-zA-Z0-9_][ ]{10,}[a-zA-Z0-9_]', 'Code with excessive spacing between identifiers'),
        ]
        
        for pattern, description in suspicious_patterns:
            if re.search(pattern, line):
                issues.append(f"{filename}:{line_num} - {description}")

        # Detect inline statements after a control-flow colon (e.g., "if x: do_y")
        if re.match(r"^\s*(def|for|if|elif|else|while|try|except|class|with|finally)\b.*:\s+\S", line):
            issues.append(
                f"{filename}:{line_num} - Inline code after colon; split into separate lines"
            )
    
    return issues


def run_python_syntax_check(file_paths: List[str]) -> Dict[str, Any]:
    """
    Compile Python files to detect syntax errors before runtime.
    """
    results = {
        "files_checked": [],
        "errors": [],
        "has_errors": False
    }

    for file_path in file_paths:
        if not os.path.exists(file_path):
            debug_print(f"Skipping syntax check for missing file: {file_path}", "DEBUG")
            continue

        results["files_checked"].append(file_path)
        try:
            py_compile.compile(file_path, doraise=True)
            debug_print(f"✅ Syntax check passed: {file_path}", "DEBUG")
        except py_compile.PyCompileError as e:
            results["has_errors"] = True
            line_info = getattr(e, 'lineno', '?')
            message = f"{file_path}:{line_info} - {e.msg}"
            results["errors"].append(message)
            debug_print(f"❌ Syntax error detected: {message}", "ERROR")
        except Exception as e:
            results["has_errors"] = True
            message = f"{file_path} - {e}"
            results["errors"].append(message)
            debug_print(f"❌ Unexpected syntax check failure: {message}", "ERROR")

    return results




def check_factory_function(weapon_file: str, weapon_class_name: str) -> Tuple[bool, str]:
    """
    Check if the weapon file has the required factory function.
    Returns (has_factory, error_message)
    """
    content, success = safe_read_file(weapon_file)
    if not success:
        return False, f"Could not read weapon file: {weapon_file}"
    
    factory_func_name = f"create_{weapon_class_name.lower()}"
    factory_pattern = rf"^def {factory_func_name}\(\):"
    
    if not re.search(factory_pattern, content, re.MULTILINE):
        return False, f"Missing factory function: {factory_func_name}()"
    
    return True, ""


def validate_weapon_implementation(weapon_plan: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate weapon implementation for common issues.
    """
    debug_print("🔍 Starting weapon implementation validation", "INFO")

    validation = {
        "checks_passed": [],
        "warnings": [],
        "errors": [],
        "has_errors": False
    }

    try:
        weapon_name = weapon_plan.get("weapon_name", "UnknownWeapon")
        weapon_class_name = weapon_plan.get("weapon_class_name", weapon_name)
        effects = weapon_plan.get("effects", [])
        normalized_effects = normalize_effects(effects)
        effect_debug_list = [effect_info["string_id"] for effect_info in normalized_effects]

        debug_print(
            f"Validating weapon: {weapon_name} with effects: {effect_debug_list}",
            "INFO"
        )

        # Check weapon file
        weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
        debug_print(f"Checking weapon file: {weapon_file}", "DEBUG")

        if not os.path.exists(weapon_file):
            validation["errors"].append(f"Weapon file {weapon_file} not found")
            validation["has_errors"] = True
            debug_print(f"❌ Weapon file missing: {weapon_file}", "ERROR")
        else:
            debug_print(f"✅ Weapon file exists: {weapon_file}", "DEBUG")

        # Check projectile file if effects exist
        if normalized_effects:
            projectile_file = f"Game/Objects/{weapon_class_name.lower()}_projectile.py"
            debug_print(f"Checking projectile file: {projectile_file}", "DEBUG")

            if not os.path.exists(projectile_file):
                validation["errors"].append(f"Projectile file {projectile_file} not found")
                validation["has_errors"] = True
                debug_print(f"❌ Projectile file missing: {projectile_file}", "ERROR")
            else:
                debug_print(f"✅ Projectile file exists: {projectile_file}", "DEBUG")

        # Validate weapon file content
        if os.path.exists(weapon_file):
            weapon_code, success = safe_read_file(weapon_file)
            if success:
                debug_print("Reading weapon file content for validation", "DEBUG")

                # Check for create_weapon function
                if f"def create_{weapon_class_name.lower()}()" not in weapon_code:
                    validation["errors"].append(f"Weapon file missing create_{weapon_class_name.lower()} function")
                    validation["has_errors"] = True
                    debug_print(f"❌ Missing create function in weapon file", "ERROR")

                # Check for placeholder image usage
                if "placeholder.png" not in weapon_code:
                    validation["errors"].append("Weapon should use 'placeholder.png' for floor_image_name and projectile_image_name")
                    validation["has_errors"] = True
                    debug_print(f"❌ Weapon not using placeholder.png", "ERROR")

                expected_description = weapon_plan.get("description")
                if isinstance(expected_description, str) and expected_description.strip():
                    normalized_description = expected_description.strip()
                    potential_patterns = {
                        normalized_description,
                        normalized_description.replace('"', '\\"'),
                        normalized_description.replace("'", "\\'"),
                    }
                    if not any(pattern in weapon_code for pattern in potential_patterns):
                        validation["errors"].append(
                            "Weapon description from plan is not present in weapon implementation"
                        )
                        validation["has_errors"] = True
                        debug_print("❌ Weapon description not found in implementation", "ERROR")

                # Check for multiple statements on same line
                formatting_issues = check_formatting_issues(weapon_code, weapon_file)
                if formatting_issues:
                    for issue in formatting_issues:
                        validation["errors"].append(issue)
                        validation["has_errors"] = True
                        debug_print(f"❌ Formatting issue: {issue}", "ERROR")

        # Validate projectile file content if effects exist
        if normalized_effects and os.path.exists(projectile_file):
            proj_code, success = safe_read_file(projectile_file)
            if success:
                debug_print("Reading projectile file content for validation", "DEBUG")

                # Check for proper class inheritance
                expected_class = f"class {weapon_class_name}Projectile(Projectile):"
                if expected_class not in proj_code:
                    validation["errors"].append(f"Projectile class should be named {weapon_class_name}Projectile")
                    validation["has_errors"] = True
                    debug_print(f"❌ Incorrect projectile class name", "ERROR")

                # Check method signatures
                if "def on_character_hit(self, target, arena):" not in proj_code:
                    validation["errors"].append("Projectile missing on_character_hit(self, target, arena) method")
                    validation["has_errors"] = True
                    debug_print(f"❌ Missing on_character_hit method", "ERROR")

                if "def update(self):" not in proj_code:
                    validation["errors"].append("Projectile missing update(self) method")
                    validation["has_errors"] = True
                    debug_print(f"❌ Missing update method", "ERROR")

                # Check for self.alive = False usage
                if "self.alive = False" not in proj_code:
                    validation["warnings"].append("Projectile should use self.alive = False for destruction")
                    debug_print(f"⚠️  Projectile may not use proper destruction", "WARNING")

                # Check for self.kill() usage (should not exist)
                if "self.kill()" in proj_code:
                    validation["errors"].append("Projectile uses self.kill() instead of self.alive = False")
                    validation["has_errors"] = True
                    debug_print(f"❌ Projectile incorrectly uses self.kill()", "ERROR")

                # Check effect implementations
                for effect_info in normalized_effects:
                    descriptor = effect_info["string_id"]
                    kind = effect_info["kind"]
                    slug = effect_info["slug"]
                    tags = effect_info["tags"]

                    debug_print(f"Checking effect implementation: {descriptor}", "DEBUG")

                    if kind == "projectile_behavior":
                        if "splitting" in tags or "split" in slug:
                            if "arena.spawn_projectile" not in proj_code:
                                validation["errors"].append(
                                    f"Projectile missing spawn_projectile call for {descriptor}"
                                )
                                validation["has_errors"] = True
                                debug_print(
                                    f"❌ Missing spawn_projectile for {descriptor}",
                                    "ERROR"
                                )
                        else:
                            if "update" not in proj_code.lower():
                                validation["errors"].append(
                                    f"Projectile missing behavior implementation for {descriptor}"
                                )
                                validation["has_errors"] = True
                                debug_print(
                                    f"❌ Missing behavior implementation for {descriptor}",
                                    "ERROR"
                                )
                    elif kind == "impact":
                        if f"apply_{slug}" not in proj_code:
                            validation["errors"].append(
                                f"Projectile doesn't apply {descriptor} effect"
                            )
                            validation["has_errors"] = True
                            debug_print(
                                f"❌ Missing effect application for {descriptor}",
                                "ERROR"
                            )
                    else:
                        debug_print(
                            f"ℹ️  No validation rules for effect kind '{kind}' ({descriptor})",
                            "DEBUG"
                        )

                if "pygame.math." in proj_code:
                    validation["errors"].append(
                        "Projectile uses pygame.math module for math helpers; use math or Vector2 instead"
                    )
                    validation["has_errors"] = True
                    debug_print(
                        "❌ Projectile referenced pygame.math helpers (unsupported)",
                        "ERROR"
                    )

        # Check Cow class for effect support - ONLY for impact_ effects (character effects)
        cow_file = "Game/Character/cow.py"
        if os.path.exists(cow_file):
            cow_code, success = safe_read_file(cow_file)
            if success:
                debug_print("Checking Cow class for character effect support", "DEBUG")

                for effect_info in normalized_effects:
                    if effect_info["kind"] != "impact":
                        debug_print(
                            f"✓ Skipping Cow check for projectile-only effect: {effect_info['string_id']}",
                            "DEBUG"
                        )
                        continue

                    effect_name = effect_info["slug"]
                    debug_print(
                        f"Checking Cow class for {effect_name} character effect support",
                        "DEBUG"
                    )

                    if f"self.is_{effect_name}" not in cow_code:
                        validation["errors"].append(
                            f"Cow missing is_{effect_name} state variable"
                        )
                        validation["has_errors"] = True
                        debug_print(
                            f"❌ Cow missing state variable for {effect_name}",
                            "ERROR"
                        )

                    if f"def apply_{effect_name}" not in cow_code:
                        validation["errors"].append(
                            f"Cow missing apply_{effect_name} method"
                        )
                        validation["has_errors"] = True
                        debug_print(
                            f"❌ Cow missing apply method for {effect_name}",
                            "ERROR"
                        )

        debug_print(f"Validation complete: {len(validation['checks_passed'])} checks passed, {len(validation['warnings'])} warnings, {len(validation['errors'])} errors", "INFO")

    except Exception as e:
        debug_print(f"Error during validation: {e}", "ERROR")
        validation["errors"].append(f"Validation failed: {e}")
        validation["has_errors"] = True

    return validation


def validate_projectile_behavior(proj_code: str, effect: str) -> Dict[str, Any]:
    """Validate specific projectile behavior implementations."""
    debug_print(f"Validating projectile behavior: {effect}", "DEBUG")

    validation = {
        "implemented": False,
        "correct": False,
        "details": []
    }

    try:
        if effect == "homing":
            # Check for homing logic in update method
            if "nearest_target" in proj_code or "track" in proj_code or "target" in proj_code:
                validation["implemented"] = True
                validation["details"].append("Projectile implements homing behavior")
                debug_print("✅ Homing behavior detected", "DEBUG")
            else:
                validation["details"].append("No homing logic found in projectile")
                debug_print("❌ No homing logic found", "DEBUG")

        elif "splitting" in effect:
            # Check for splitting logic
            if "arena.spawn_projectile" in proj_code:
                validation["implemented"] = True
                validation["details"].append("Projectile implements splitting behavior")

                # Check for correct number of projectiles
                if "range(" in proj_code:
                    validation["correct"] = True
                    validation["details"].append("Correct number of projectiles spawned")
                    debug_print("✅ Splitting behavior correctly implemented", "DEBUG")
                else:
                    validation["details"].append("May not spawn correct number of projectiles")
                    debug_print("⚠️  Splitting behavior may be incorrect", "WARNING")
            else:
                validation["details"].append("No projectile spawning found")
                debug_print("❌ No splitting logic found", "DEBUG")

        elif "impact_" in effect:
            # Character effect application
            effect_name = effect.replace("impact_", "")
            if f"apply_{effect_name}" in proj_code:
                validation["implemented"] = True
                validation["correct"] = True
                validation["details"].append(f"Projectile applies {effect_name} effect")
                debug_print(f"✅ Effect application found for {effect_name}", "DEBUG")
            else:
                validation["details"].append(f"No {effect_name} effect application found")
                debug_print(f"❌ No effect application for {effect_name}", "DEBUG")

    except Exception as e:
        debug_print(f"Error validating projectile behavior {effect}: {e}", "ERROR")
        validation["details"].append(f"Validation error: {e}")

    return validation
