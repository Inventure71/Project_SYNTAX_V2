"""
Utility functions for the agent system.
"""
import os
import json
import re
from typing import Dict, List, Any, Tuple, Set


def debug_print(message: str, level: str = "INFO") -> None:
    """Print debug messages with timestamps and levels."""
    import datetime
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def safe_read_file(file_path: str) -> Tuple[str, bool]:
    """Safely read a file and return content or error status."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, True
    except Exception as e:
        debug_print(f"Failed to read file {file_path}: {e}", "ERROR")
        return "", False


def safe_write_file(file_path: str, content: str) -> bool:
    """Safely write content to a file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        debug_print(f"Failed to write file {file_path}: {e}", "ERROR")
        return False


def fix_same_line_statements(code: str) -> str:
    """
    Automatically fix multiple statements on the same line by detecting
    excessive whitespace and splitting into separate lines.
    """
    import re
    
    lines = code.split('\n')
    fixed_lines = []
    
    for line in lines:
        # Normalize inline blocks like "if condition: do_something" to separate lines
        if ":" in line:
            match = re.match(r"^(\s*)(?:def|for|if|elif|else|while|try|except|class|with|finally)\b.*:\s+\S", line)
            if match:
                indent_str = match.group(1)
                colon_index = line.find(":")
                before = line[:colon_index + 1]
                after = line[colon_index + 1:]
                fixed_lines.append(before.rstrip())
                trailing = after.strip()
                if trailing:
                    fixed_lines.append(f"{indent_str}    {trailing}")
                continue

        # Check for excessive whitespace (20+ spaces) between code segments
        if re.search(r'[^\s][ ]{20,}[^\s]', line):
            # Split by large whitespace blocks
            parts = re.split(r'([ ]{20,})', line)
            
            # Get the base indentation from the first part
            base_indent = len(line) - len(line.lstrip())
            base_indent_str = ' ' * base_indent
            
            # Add first part
            if parts[0].strip():
                fixed_lines.append(parts[0].rstrip())
            
            # Add remaining parts on separate lines with same indentation
            for i in range(2, len(parts), 2):
                if parts[i].strip():
                    fixed_lines.append(base_indent_str + parts[i].strip())
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def extract_json_from_text(text: str) -> Dict[str, Any]:
    """Extract JSON from text that may contain markdown formatting."""
    try:
        # Look for JSON block
        if "```json" in text:
            json_start = text.find("```json") + 7
            json_end = text.find("```", json_start)
            json_str = text[json_start:json_end].strip()
            return json.loads(json_str)
        elif "{" in text and "}" in text:
            # Try to find JSON object
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            json_str = text[json_start:json_end]
            return json.loads(json_str)
    except Exception as e:
        debug_print(f"Failed to extract JSON from text: {e}", "WARNING")

    # Fallback: create simple structure from text
    return {
        "weapon_name": "CustomWeapon",
        "high_level_design": text[:200],
        "tasks": [
            {
                "task_number": 1,
                "goal": "Implement weapon based on description",
                "files_to_create": [],
                "files_to_modify": [],
                "what_to_do": ["Create weapon class", "Integrate with game system"],
                "full_plan": text
            }
        ]
    }


def validate_method_signature(code: str, method_name: str, expected_params: List[str]) -> bool:
    """Validate that a method has the expected signature."""
    pattern = rf"def\s+{re.escape(method_name)}\s*\(([^)]*)\)"
    match = re.search(pattern, code)

    if not match:
        return False

    params_str = match.group(1).strip()
    if not params_str:
        return len(expected_params) == 0

    # Parse parameters
    actual_params = []
    for param in params_str.split(','):
        param = param.strip()
        if param and not param.startswith('*'):  # Skip *args, **kwargs
            actual_params.append(param.split('=')[0].split(':')[0].strip())

    return actual_params == expected_params


def check_file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path)


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except:
        return 0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    else:
        return f"{size_bytes // (1024 * 1024)} MB"


def _slugify_identifier(value: str) -> str:
    """Turn a human readable value into a safe snake_case slug."""
    if not value:
        return "effect"
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_{2,}", "_", value)
    return value.strip("_") or "effect"


def _extract_first_string(*candidates: Any) -> str:
    """Return the first non-empty string representation from the candidates."""
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return ""


def _infer_effect_kind(slug: str, data: Dict[str, Any]) -> Tuple[str, Set[str]]:
    """Infer the high-level effect kind and any useful tags from slug/data."""
    tags: Set[str] = set()
    lowered = slug.lower()
    kind_hint = _extract_first_string(
        data.get("type"),
        data.get("category"),
        data.get("effect_type"),
        data.get("mode"),
        data.get("kind"),
        data.get("behavior"),
    ).lower()

    text_blob = " ".join(
        str(value).lower()
        for key, value in data.items()
        if isinstance(value, (str, int, float))
    )

    def has_keyword(*keywords: str) -> bool:
        return any(keyword in lowered or keyword in kind_hint or keyword in text_blob for keyword in keywords)

    if has_keyword("split"):
        tags.add("splitting")
    if has_keyword("homing", "seeking"):
        tags.add("homing")
    if has_keyword("bounce", "ricochet"):
        tags.add("bouncing")
    if has_keyword("freeze", "slow", "chill"):
        tags.add("freeze")

    if has_keyword("projectile", "pattern", "orbit", "arc", "radius", "spread"):
        return "projectile_behavior", tags

    if has_keyword("status", "debuff", "on_hit", "target", "enemy", "apply"):
        return "impact", tags

    # Fallback: assume status effects default to impact
    return "impact", tags


def normalize_effects(effects: List[Any]) -> List[Dict[str, Any]]:
    """Normalize effect descriptors to a consistent data structure."""
    normalized: List[Dict[str, Any]] = []

    for effect in effects:
        if isinstance(effect, str):
            raw = effect.strip()
            if raw.startswith("impact_"):
                slug = raw[len("impact_"):]
                kind = "impact"
            elif raw.startswith("projectile_behavior_"):
                slug = raw[len("projectile_behavior_"):]
                kind = "projectile_behavior"
            else:
                slug = _slugify_identifier(raw)
                kind = "projectile_behavior" if slug.startswith("projectile_") else "impact"
            tags: Set[str] = set()
            if "split" in slug:
                tags.add("splitting")
            if "homing" in slug:
                tags.add("homing")
            if "bounce" in slug:
                tags.add("bouncing")
            normalized.append({
                "original": effect,
                "kind": kind,
                "name": slug.replace("_", " ").title(),
                "slug": slug,
                "string_id": f"{kind}_{slug}" if not raw.startswith(f"{kind}_") else raw,
                "data": {},
                "tags": sorted(tags),
            })
            continue

        if isinstance(effect, dict):
            name = _extract_first_string(
                effect.get("identifier"),
                effect.get("name"),
                effect.get("effect"),
                effect.get("status"),
            )
            slug = _slugify_identifier(name or effect.get("type", "") or "effect")
            kind, tags = _infer_effect_kind(slug, effect)
            string_id = f"{kind}_{slug}" if kind in {"impact", "projectile_behavior"} else slug
            normalized.append({
                "original": effect,
                "kind": kind,
                "name": name or slug.replace("_", " ").title(),
                "slug": slug,
                "string_id": string_id,
                "data": effect,
                "tags": sorted(tags),
            })
            continue

        # Unsupported type – capture as generic impact effect
        slug = _slugify_identifier(str(effect))
        normalized.append({
            "original": effect,
            "kind": "impact",
            "name": slug.replace("_", " ").title(),
            "slug": slug,
            "string_id": f"impact_{slug}",
            "data": {"value": effect},
            "tags": [],
        })

    return normalized
