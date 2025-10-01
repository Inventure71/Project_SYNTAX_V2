"""Tool for locating files that contain a line matching a search string."""

from __future__ import annotations

import os
import re
from typing import List, Tuple

from Agent.Helpers.check_file_permission import check_file_permission

_ALLOWED_EXTENSIONS = {
    ".py",
    ".txt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".conf",
    ".csv",
    ".xml",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
}


def _normalise(text: str, case_sensitive: bool) -> str:
    """Return text stripped of whitespace for relaxed matching."""

    processed = re.sub(r"\s+", "", text)
    return processed if case_sensitive else processed.lower()


def find(
    search_text: str,
    start_path: str = "Game",
    case_sensitive: bool = False,
    max_results_per_file: int = 20,
) -> str:
    """Find files that contain lines matching the provided search text.

    Args:
        search_text: The text to search for. Whitespace is ignored when matching.
        start_path: Directory to start the search from (defaults to the project Game folder).
        case_sensitive: Whether the comparison should be case sensitive (defaults to False).
        max_results_per_file: Maximum number of matching lines to report per file.

    Returns:
        A human-readable summary of files and line numbers containing matches. If no
        matches are found, a descriptive message is returned instead.
    """

    if not search_text or not search_text.strip():
        return "Search text must not be empty."

    root = os.path.abspath(start_path)
    if not os.path.exists(root):
        return f"Start path '{start_path}' does not exist."

    normalised_query = _normalise(search_text, case_sensitive)
    matches: List[Tuple[str, List[Tuple[int, str]]]] = []

    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            _, ext = os.path.splitext(filename)
            if _ALLOWED_EXTENSIONS and ext not in _ALLOWED_EXTENSIONS:
                continue

            absolute_path = os.path.join(dirpath, filename)
            relative_path = os.path.relpath(absolute_path, os.getcwd())

            if not check_file_permission(relative_path):
                continue

            file_matches: List[Tuple[int, str]] = []
            try:
                with open(absolute_path, "r", encoding="utf-8") as handle:
                    for index, raw_line in enumerate(handle, start=1):
                        normalised_line = _normalise(raw_line, case_sensitive)
                        if normalised_query in normalised_line:
                            file_matches.append((index, raw_line.rstrip("\n")))
                            if len(file_matches) >= max_results_per_file:
                                break
            except (UnicodeDecodeError, OSError):
                continue

            if file_matches:
                matches.append((relative_path, file_matches))

    if not matches:
        return f"No matches found for '{search_text}'."

    summary_lines: List[str] = [
        f"Matches for '{search_text}' (ignoring whitespace{' and case' if not case_sensitive else ''}):"
    ]
    for path, occurrences in sorted(matches, key=lambda item: item[0]):
        summary_lines.append(f"- {path}")
        for line_no, text in occurrences:
            summary_lines.append(f"    L{line_no}: {text.strip()}")
        if len(occurrences) >= max_results_per_file:
            summary_lines.append("    … (additional matches omitted)")

    return "\n".join(summary_lines)


__all__ = ["find"]
