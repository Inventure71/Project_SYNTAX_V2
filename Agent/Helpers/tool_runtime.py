import os
import sys
import importlib
import inspect
import traceback
from typing import Any, Dict, List, Optional, Tuple

from Agent.Helpers.auto_tool_creator import get_tool_location_index


def _ensure_sys_path() -> None:
    here = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.abspath(os.path.join(here, "..", ".."))
    if project_root not in sys.path:
        sys.path.append(project_root)
    tools_dir = os.path.abspath(os.path.join(here, "..", "Tools"))
    if tools_dir not in sys.path:
        sys.path.append(tools_dir)


def _resolve_tool_module_and_name(function_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Look up the module name containing the given tool function.

    Returns (module_import_path, function_name) or (None, None) if not found.
    This uses the pre-built location index to avoid scanning/importing at runtime.
    """
    index = get_tool_location_index()
    # Prefer exact name match; if multiple, first wins
    for entry in index:
        if entry.get("name") == function_name:
            module_basename = entry.get("module")
            if not module_basename:
                continue
            # Tools live under Agent.Tools.<module>
            return f"Agent.Tools.{module_basename}", function_name
    return None, None


def _prepare_call_args(fn: Any, args: Any):
    if isinstance(args, (list, tuple)):
        return tuple(args), {}
    if isinstance(args, dict):
        try:
            sig = inspect.signature(fn)
        except (TypeError, ValueError):
            return (), dict(args)
        params = sig.parameters
        accepts_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params.values())
        if accepts_kwargs:
            return (), dict(args)
        allowed = {n for n, p in params.items() if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)}
        filtered = {k: v for k, v in args.items() if k in allowed}
        return (), filtered
    return (args,), {}


def call_function(function_name: str, args: Any) -> Dict[str, Any]:
    """Call a discovered tool by function name using the discovery index.

    Args:
        function_name: Name of the function as exposed in the tool schema.
        args: Mapping for kwargs, sequence for positional args, or a single value.

    Returns:
        A dict with keys:
        - ok: bool
        - result: Any (present when ok)
        - error, error_type, traceback: present when not ok
        - called: fully-qualified function path when resolved
    """
    _ensure_sys_path()
    module_path, func = _resolve_tool_module_and_name(function_name)
    if not module_path:
        return {
            "ok": False,
            "error": f"Function '{function_name}' not found in tool index.",
            "error_type": "FunctionNotFound",
        }

    try:
        mod = importlib.import_module(module_path)
    except Exception as e:
        return {
            "ok": False,
            "error": f"Failed to import module '{module_path}': {e}",
            "error_type": e.__class__.__name__,
            "traceback": traceback.format_exc(),
        }

    if not hasattr(mod, func):
        return {
            "ok": False,
            "error": f"Module '{module_path}' has no attribute '{func}'.",
            "error_type": "AttributeError",
        }

    fn = getattr(mod, func)
    if not callable(fn):
        return {
            "ok": False,
            "error": f"Attribute '{module_path}.{func}' is not callable.",
            "error_type": "TypeError",
        }

    try:
        pos, kw = _prepare_call_args(fn, args)
        result = fn(*pos, **kw)
        return {"ok": True, "result": result, "called": f"{module_path}.{func}"}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "error_type": e.__class__.__name__,
            "traceback": traceback.format_exc(),
            "called": f"{module_path}.{func}",
        }


