"""
Utility functions for the agent system.
"""
import os
import json
import re
from typing import Dict, List, Any, Tuple


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
