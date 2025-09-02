import os
import json


# Default: enable whitelist mode so tools may only access files under specific roots
WHITELIST_MODE = True
WHITELIST_DIRS = ["Game"]  # relative to workspace root (cwd at tool runtime)


def _load_blocklist():
    try:
        with open("Agent/Prompts/blocked_files.json", "r") as f:
            return json.load(f)
    except Exception:
        return {"files": []}


blocked_files = _load_blocklist()


def _is_blocked_by_blacklist(file_path: str) -> bool:
    sections = file_path.split("/")
    for path in sections:
        if path in blocked_files.get("files", []):
            return True
    return False


def _is_in_whitelist(file_path: str) -> bool:
    file_abs = os.path.abspath(file_path)
    cwd = os.path.abspath(os.getcwd())
    for rel_dir in WHITELIST_DIRS:
        allowed_root = os.path.abspath(os.path.join(cwd, rel_dir))
        if file_abs == allowed_root or file_abs.startswith(allowed_root + os.sep):
            return True
    return False


def check_file_permission(file_path: str) -> bool:
    """
    Returns True if the given path is permitted for tool operations.

    Behavior:
    - If WHITELIST_MODE is True: the path must be under one of WHITELIST_DIRS (relative to cwd)
      and not match any blacklist token in blocked_files.json.
    - If WHITELIST_MODE is False: only the blacklist is enforced.
    """
    if WHITELIST_MODE:
        return _is_in_whitelist(file_path) and (not _is_blocked_by_blacklist(file_path))
    return not _is_blocked_by_blacklist(file_path)