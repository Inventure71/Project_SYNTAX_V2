import os
from typing import List

from Agent.Helpers.check_file_permission import check_file_permission
from Agent.Tools.helpers_ignore import _read_lines, _write_lines, _write_text, _validate_range, _validate_insert_index, _replace_range_in_place


def write_over_file(file_path: str, content: str) -> None:
    """
    Overwrite a file with `content`.

    It writes the exact `content` bytes to `file_path` using text mode `"w"`, replacing any
    existing contents entirely. Parent directories are created by the underlying helper if
    needed. On any exception, the error is caught and returned as a failure string.

    Args:
        file_path: Path to the target file. Parent directories are created if needed.
        content: Full text to write.

    Returns:
        str: "success" on success; "failure: <error>" if an error occurred.
    """
    try:
        if not check_file_permission(file_path):
            return "failure: File is not allowed to be modified"
        
        _write_text(file_path, content, mode="w")
        return "success"
    except Exception as e:
        return f"failure: {e}"


def append_to_file(file_path: str, content: str) -> None:
    """
    Append `content` to the end of a file.

    It opens the file in text append mode and writes `content` verbatim to the end,
    creating parent directories if necessary (handled by the helper). The function does
    not insert newlines automatically—ensure `content` ends with a newline if desired.
    On any exception, the error is caught and returned as a failure string.

    Args:
        file_path: Path to the target file. Parent directories are created if needed.
        content: Text to append.

    Returns:
        str: "success" on success; "failure: <error>" if an error occurred.
    """
    try:
        if not check_file_permission(file_path):
            return "failure: File is not allowed to be modified"
        
        _write_text(file_path, content, mode="a")
        return "success"
    except Exception as e:
        return f"failure: {e}"


def write_into_file(
    file_path: str,
    content: str,
    line_number_start: int,
    line_number_end: int,
    replace_lines: bool = True,
) -> str:
    """
    Replace a block of lines with new content, anchored at a start line.

    Behavior (0-indexed lines):
    - Remove the entire inclusive range [line_number_start, line_number_end].
    - If `content` is provided (non-empty), insert it starting at `line_number_start`.
      This shifts subsequent lines down as needed.
    - If `content` is empty, leave a single blank line at `line_number_start`.

    Notes:
    - This function is designed for replacing code blocks cleanly (e.g., inserting a new
      function while removing the old block with no off-by-one confusion).
    - Parameter `replace_lines` is ignored and kept for backward compatibility.
    - Newlines in `content` are preserved exactly as provided.
    - Quick usage: to replace lines 10-20 with `new_code`, pass
      `line_number_start=10`, `line_number_end=20`, and `content=new_code`.
      Ensure `new_code` ends with a trailing newline if you want a clean block ending.

    Args:
        file_path: Path to the target file. Parent directories are created if needed.
        content: Text to insert at `line_number_start` after deleting the block. If empty,
                 a single blank line is kept at `line_number_start`.
        line_number_start: 0-indexed first line of the block to replace (inclusive).
        line_number_end: 0-indexed last line of the block to replace (inclusive).
        replace_lines: Ignored (kept for backward compatibility).

    Returns:
        str: "success" on success; "failure: <error>" if an error occurred.
    """
    try:    
        if not check_file_permission(file_path):
            return "failure: File is not allowed to be modified"
        
        lines = _read_lines(file_path)
        total = len(lines)

        if line_number_start < 0:
            return "failure: line_number_start must be >= 0"

        # Normalize indices to allow EOF insertion and clamped end
        if total == 0:
            start = 0 if line_number_start == 0 else None
            if start is None:
                return "failure: Cannot replace in empty file unless line_number_start == 0"
            end = -1  # nothing to delete
        else:
            start = min(line_number_start, total)  # allow insertion at EOF
            # end cannot be before start-1 (so deletion may become empty if start > last index)
            end = max(start - 1, min(line_number_end, total - 1))

        # Remove [start, end] entirely (may be empty if end < start)
        pre = lines[:start]
        post = lines[end + 1:]

        if content and content != "":
            content_lines = content.splitlines(keepends=True)
            new_lines = pre + content_lines + post
        else:
            # No content -> keep a single blank line at start position
            new_lines = pre + ["\n"] + post

        _write_lines(file_path, new_lines)
        return "success"
    except Exception as e:
        return f"failure: {e}"


def clear_lines_between(file_path: str, line_number_start: int, line_number_end: int) -> str:
    """
    Replace the inclusive range [line_number_start, line_number_end] with blank lines.

    Unlike deletion that shifts line numbers upward, this operation **preserves the total
    number of lines** by writing newline placeholders for the removed region. As a result,
    all subsequent line numbers remain unchanged.

    Args:
        file_path: Path to the target file.
        line_number_start: 0-indexed first line to blank.
        line_number_end: 0-indexed last line to blank (inclusive).

    Returns:
        str: "success" on success; "failure: <error>" if an error occurred.
    """
    try:
        if not check_file_permission(file_path):
            return "failure: File is not allowed to be modified"
        
        lines = _read_lines(file_path)
        if not lines:
            raise IndexError("Cannot delete lines in an empty file.")
        _validate_range(line_number_start, line_number_end, len(lines))
        blanks = ["\n"] * (line_number_end - line_number_start + 1)
        new_lines = _replace_range_in_place(lines, line_number_start, line_number_end, blanks)
        _write_lines(file_path, new_lines)
        return "success"
    except Exception as e:
        return f"failure: {e}"


def create_file(file_path: str, content: str) -> str:
    """
    Create a new file at `file_path` with `content`.

    Args:
        file_path: Path to the new file. Parent directories are created if needed.
        content: Initial file contents.

    Returns:
        str: "success" on success; "failure: <error>" if an error occurred.
    """
    try:
        if not check_file_permission(file_path):
            return "failure: File is not allowed to be modified"

        if os.path.exists(file_path):
            return "failure: File already exists"

        # 'x' creates the file and fails if it already exists; underlying helper ensures parent dirs
        _write_text(file_path, content, mode="x")
        return "success"
    except FileExistsError:
        return "failure: File already exists"
    except Exception as e:
        return f"failure: {e}"
