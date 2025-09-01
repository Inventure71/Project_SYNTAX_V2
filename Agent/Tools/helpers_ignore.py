# NOT TO BE USED IN THE AGENT.

from typing import List
import os
from typing import Dict, Optional
from Agent.Tools.read_file import read_file

"""STRUCTURE"""
def print_tree(structure: Dict[str, Optional[dict]], prefix: str = "") -> str:
    """
    NOT TO BE USED IN THE AGENT.
    Print an ASCII tree from the nested dictionary returned by get_project_structure().

    Args:
        structure: The nested dictionary structure.
        prefix: Internal prefix used for pretty printing.
    """
    view_tree = ""

    items = list(structure.items())
    for index, (name, value) in enumerate(items):
        is_last = index == len(items) - 1
        branch = "└── " if is_last else "├── "
        view_tree += f"{prefix}{branch}{name}\n"
        if isinstance(value, dict):
            extension = "    " if is_last else "│   "
            view_tree += print_tree(value, prefix + extension)

    return view_tree


"""FILE READING AND WRITING"""
def _ensure_parent_dir(path: str) -> None:
    """Create the parent directory for `path` if it doesn't exist."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.exists(parent):
        os.makedirs(parent, exist_ok=True)


def _read_lines(path: str) -> List[str]:
    """Read a file as a list of lines (preserving newlines). Return [] if it doesn't exist."""
    if not os.path.exists(path):
        return []
    if not os.path.isfile(path):
        raise IsADirectoryError(f"{path!r} exists but is not a regular file.")
    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def _write_lines(path: str, lines: List[str]) -> None:
    """Write a list of lines to `path` (overwrites)."""
    _ensure_parent_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _write_text(path: str, text: str, mode: str) -> None:
    """Write text to `path` using the given mode ('w' overwrite, 'a' append)."""
    _ensure_parent_dir(path)
    with open(path, mode, encoding="utf-8") as f:
        f.write(text)


def _validate_insert_index(index: int, length: int) -> None:
    if index < 0:
        raise ValueError("Line numbers must be non-negative (0-indexed).")
    if index > length:
        raise IndexError(
            f"Insert index {index} out of range for file with {length} lines "
            f"(use {length} to insert at end)."
        )


def _validate_range(start: int, end: int, length: int) -> None:
    if start < 0 or end < 0:
        raise ValueError("Line numbers must be non-negative (0-indexed).")
    if start > end:
        raise ValueError("line_number_start must be <= line_number_end.")
    if end >= length:
        raise IndexError(
            f"line_number_end {end} out of range for file with {length} lines."
        )


def _replace_range_in_place(lines: List[str], start: int, end: int, replacement: List[str]) -> List[str]:
    """
    Replace the inclusive range [start, end] with `replacement`,
    padding or truncating to preserve total line count (no shifting).
    """
    range_len = end - start + 1
    if len(replacement) < range_len:
        replacement = replacement + ["\n"] * (range_len - len(replacement))
    elif len(replacement) > range_len:
        replacement = replacement[:range_len]
    return lines[:start] + replacement + lines[end + 1:]


"""DIRECTORY UTILITIES"""
def collect_directory_files_and_contents(root_dir: str, include_hidden: bool = False) -> str:
    """
    Recursively collect all supported files under `root_dir` and concatenate their
    relative paths and contents into a single string.

    Files are read using `Agent.Tools.read_file.read_file`, which enforces a whitelist of
    text-based extensions. Unsupported files are skipped.

    Args:
        root_dir: Directory to scan.
        include_hidden: If False (default), skip dot-directories and dot-files.

    Returns:
        A single string in the form:
            === path/from/root.ext ===\n
            <file contents>\n
            === another/file ===\n
            <file contents>\n
    """
    if not os.path.isdir(root_dir):
        raise NotADirectoryError(f"{root_dir!r} is not a directory")

    combined_parts: List[str] = []

    for current_dir, dirnames, filenames in os.walk(root_dir):
        # Ensure deterministic traversal order
        dirnames.sort()
        filenames.sort()

        if not include_hidden:
            dirnames[:] = [d for d in dirnames if not d.startswith('.')]
            filenames = [f for f in filenames if not f.startswith('.')]

        for filename in filenames:
            file_path = os.path.join(current_dir, filename)

            # Delegate reading and extension filtering to read_file()
            content = read_file(file_path, line_count=False)

            # read_file returns either a list of lines or an error message string
            if isinstance(content, list):
                content_text = ''.join(content)
            else:
                # Skip known error messages from read_file
                if (
                    "does not exist" in content
                    or "is not a file" in content
                    or "is not a valid file type" in content
                ):
                    continue
                content_text = content

            rel_path = os.path.relpath(file_path, start=root_dir)
            combined_parts.append(f"=== {rel_path} ===\n{content_text}\n")

    return ''.join(combined_parts)