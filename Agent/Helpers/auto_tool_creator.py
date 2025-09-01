import os
import json
import ast
import re
import textwrap
from typing import Any, Dict, List, Optional, Tuple

# ---------- helpers ---------- 

_BASE_JSON_TYPE_MAP = {
    "str": "string",
    "string": "string",
    "int": "integer",
    "float": "number",
    "bool": "boolean",
    "none": "null",
    "nonetype": "null",
    "path": "string",
    "any": "string",
}

# Accept both with and without trailing colons; include common headers used in Google/NumPy/Sphinx styles
SECTION_HEADERS = (
    "Args", "Arguments", "Parameters", "Returns", "Yields", "Raises", "Examples", "Example", "Notes", "References"
)

def _normalize_type_str(type_str: str) -> str:
    t = type_str.strip()
    if not t:
        return ""
    t = t.replace("typing.", "")
    # Normalize Union/Optional (PEP 604 and typing.Union)
    # e.g., "str | None", "list[str] | None", "Union[str, None]"
    t = re.sub(r"\bNoneType\b", "None", t)
    # Handle typing.Union[...] form
    m = re.match(r"^Union\[(.+)\]$", t)
    if m:
        # choose the first non-None alternative
        parts = [p.strip() for p in m.group(1).split(",")]
        t = next((p for p in parts if p.lower() not in {"none", "nonetype"}), parts[0])
    # Handle PEP 604 A | B form
    if "|" in t:
        parts = [p.strip() for p in t.split("|")]
        t = next((p for p in parts if p.lower() not in {"none", "nonetype"}), parts[0])
    # Basic container normalization
    t = t.replace("List", "list").replace("Dict", "dict").replace("Tuple", "tuple").replace("Set", "set")
    # Handle Optional[T]
    m = re.match(r"^Optional\[(.+)\]$", t)
    if m:
        t = m.group(1).strip()
    return t

def _to_json_type(type_str: Optional[str]) -> str:
    if not type_str:
        return "string"
    t = _normalize_type_str(type_str)
    low = t.lower()
    if low in _BASE_JSON_TYPE_MAP:
        return _BASE_JSON_TYPE_MAP[low]
    # Containers
    if any(k in low for k in ("list[", "list", "sequence", "iterable", "tuple", "set")):
        return "array"
    if any(k in low for k in ("dict", "mapping")):
        return "object"
    # Fallback
    return "string"

def _unparse(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)
    except Exception:
        return None

def _parse_google_args_block(doc: str) -> Dict[str, Dict[str, str]]:
    """
    Parse a Google-style 'Args:' block into:
    { param_name: {"type": "<type or None>", "description": "<desc>"} }
    """
    out: Dict[str, Dict[str, str]] = {}
    if not doc:
        return out

    d = textwrap.dedent(doc)
    # Support headers: Args/Arguments/Parameters (with optional colon)
    header_pattern = r"(?mis)^[ \t]*(Args|Arguments|Parameters)\s*:?[ \t]*\n(.*?)(?=^[ \t]*\w[\w ]*\:?[ \t]*\n|^[ \t]*[A-Z][A-Za-z ]*[\r\n]+[-=]+\s*\n|\Z)"
    m = re.search(header_pattern, d)
    if not m:
        return out

    block = m.group(2)

    # Each param starts like: name (type): description...
    # continuation lines are indented.
    lines = block.splitlines()
    i = 0
    current = None
    while i < len(lines):
        line = lines[i]
        # param header? name (type) : description
        hdr = re.match(r"^(?P<indent>[ \t]*)"  # capture indent
                       r"([A-Za-z_]\w*)\s*(?:\(([^)]+)\))?\s*:\s*(.*)$", line)
        if hdr:
            indent = hdr.group('indent') or ""
            header_indent_len = len(indent.replace("\t", "    "))
            # groups: 2=name, 3=type, 4=desc tail
            name, typ, desc = hdr.group(2), hdr.group(3), hdr.group(4).strip()
            current = name
            out[current] = {"type": (typ.strip() if typ else ""), "description": desc}
            i += 1
            # consume continuation lines only if strictly more indented than header
            while i < len(lines):
                nxt = lines[i]
                if nxt.strip() == "":
                    i += 1
                    continue
                nxt_indent_len = len((len(nxt) - len(nxt.lstrip(' \t'))) * " ")  # placeholder to keep style
                # compute precise indentation with tabs considered as 4 spaces
                raw = nxt[:len(nxt) - len(nxt.lstrip('\t '))]
                nxt_indent_len = len(raw.replace("\t", "    "))
                if nxt_indent_len <= header_indent_len:
                    break
                cont = nxt.strip()
                if cont:
                    out[current]["description"] += (" " if out[current]["description"] else "") + cont
                i += 1
            continue
        i += 1

    return out

def _parse_numpy_args_block(doc: str) -> Dict[str, Dict[str, str]]:
    """Parse a NumPy-style 'Parameters' section into a similar structure.

    Matches blocks like:
    Parameters
    ----------
    x : int
        description...
    y : list[str]
        description line 1
        description line 2
    """
    out: Dict[str, Dict[str, str]] = {}
    if not doc:
        return out

    d = textwrap.dedent(doc)
    pattern = r"(?mis)^[ \t]*Parameters[ \t]*\n[-=]+\s*\n(.*?)(?=^[ \t]*[A-Z][A-Za-z ]*[ \t]*\n[-=]+\s*\n|\Z)"
    m = re.search(pattern, d)
    if not m:
        return out

    block = m.group(1)
    lines = block.splitlines()
    i = 0
    current: Optional[str] = None
    while i < len(lines):
        line = lines[i]
        hdr = re.match(r"^[ \t]*([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*:\s*([^\n]+)$", line)
        if hdr:
            names_part, typ = hdr.group(1), hdr.group(2).strip()
            names = [n.strip() for n in names_part.split(',') if n.strip()]
            # Start descriptions aggregation for this parameter (use first name only)
            current = names[0] if names else None
            if current:
                out[current] = {"type": typ, "description": ""}
            i += 1
            # consume indented description lines
            while i < len(lines) and (lines[i].strip() == "" or re.match(r"^[ \t]{2,}\S", lines[i])):
                if lines[i].strip():
                    out[current]["description"] += (" " if out[current]["description"] else "") + lines[i].strip()
                i += 1
            continue
        i += 1

    return out

def _parse_sphinx_params(doc: str) -> Dict[str, Dict[str, str]]:
    """Parse simple Sphinx-style ':param name: desc' and ':type name: type' pairs."""
    out: Dict[str, Dict[str, str]] = {}
    if not doc:
        return out
    d = textwrap.dedent(doc)
    # Collect descriptions
    for m in re.finditer(r"(?m)^\s*:param\s+([A-Za-z_]\w*)\s*:\s*(.+)$", d):
        name, desc = m.group(1), m.group(2).strip()
        out.setdefault(name, {})["description"] = desc
    # Collect types
    for m in re.finditer(r"(?m)^\s*:type\s+([A-Za-z_]\w*)\s*:\s*(.+)$", d):
        name, typ = m.group(1), m.group(2).strip()
        out.setdefault(name, {})["type"] = typ
    # normalize missing keys
    for k in list(out.keys()):
        out[k].setdefault("type", "")
        out[k].setdefault("description", "")
    return out

def _merge_param_docs(*docs: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    """Merge multiple param-doc maps, preferring earlier maps' non-empty fields."""
    merged: Dict[str, Dict[str, str]] = {}
    for d in docs:
        for name, info in d.items():
            current = merged.setdefault(name, {"type": "", "description": ""})
            if info.get("type") and not current.get("type"):
                current["type"] = info["type"]
            if info.get("description") and not current.get("description"):
                current["description"] = info["description"]
    return merged

def _top_block_description(doc: str) -> str:
    """
    Return the part of the docstring before any well-known section header.
    Preserves paragraphs and bullets; trims outer indentation.
    """
    if not doc:
        return ""
    d = textwrap.dedent(doc).strip("\n")
    # Find the earliest section header position at the start of a line (with or without colon)
    pattern = r"(?m)^\s*(%s)\s*:?\s*$" % "|".join(re.escape(h) for h in SECTION_HEADERS)
    m = re.search(pattern, d)
    if m:
        return d[:m.start()].rstrip()
    return d


# ---------- main extractor ---------- 

def functions_to_tool_schemas(source_code: str) -> List[Dict[str, Any]]:
    """
    Parse Python source and return a list of tool/function JSON schemas:
    {
      "type": "function",
      "name": "...",
      "description": "...",
      "parameters": {
        "type": "object",
        "properties": { "<arg>": {"type": "...", "description": "..."} },
        "required": [ ... ]
      }
    }
    """
    tree = ast.parse(source_code)
    schemas: List[Dict[str, Any]] = []

    # Only consider top-level functions to avoid exporting nested helpers
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        name = node.name
        doc = ast.get_docstring(node) or ""
        summary = _top_block_description(doc)
        # Collect docstring-derived param info from multiple styles
        doc_args_google = _parse_google_args_block(doc)
        doc_args_numpy = _parse_numpy_args_block(doc)
        doc_args_sphinx = _parse_sphinx_params(doc)
        doc_args = _merge_param_docs(doc_args_google, doc_args_numpy, doc_args_sphinx)

        # build argument info from AST
        props: Dict[str, Dict[str, Any]] = {}
        required: List[str] = []

        all_args = []
        # positional-only (py3.8+)
        all_args.extend(getattr(node.args, "posonlyargs", []))
        all_args.extend(node.args.args)

        # skip 'self'/'cls' for methods
        def _skip(n: str) -> bool:
            return n in ("self", "cls")

        # map defaults from the end
        defaults = node.args.defaults or []
        default_map = {}
        if defaults:
            for arg_node, default_node in zip(all_args[-len(defaults):], defaults):
                default_map[arg_node.arg] = _unparse(default_node)

        # regular arguments
        for a in all_args:
            arg_name = a.arg
            if _skip(arg_name):
                continue
            anno = _unparse(a.annotation)
            # fall back to docstring type if missing
            typ = anno or (doc_args.get(arg_name, {}).get("type") or None)
            js_type = _to_json_type(typ)
            desc = (doc_args.get(arg_name, {}).get("description") or "").strip()

            props[arg_name] = {"type": js_type}
            if desc:
                props[arg_name]["description"] = desc

            if arg_name not in default_map:
                required.append(arg_name)

        # *args / **kwargs
        if node.args.vararg is not None:
            var_name = node.args.vararg.arg
            if not _skip(var_name):
                props[var_name] = {"type": "array"}
                vdesc = (doc_args.get(var_name, {}).get("description") or "").strip()
                if vdesc:
                    props[var_name]["description"] = vdesc
        if node.args.kwarg is not None:
            kw_name = node.args.kwarg.arg
            if not _skip(kw_name):
                props[kw_name] = {"type": "object"}
                kdesc = (doc_args.get(kw_name, {}).get("description") or "").strip()
                if kdesc:
                    props[kw_name]["description"] = kdesc

        # keyword-only args
        kw_defaults = node.args.kw_defaults or []
        for a, d in zip(node.args.kwonlyargs, kw_defaults):
            arg_name = a.arg
            anno = _unparse(a.annotation)
            typ = anno or (doc_args.get(arg_name, {}).get("type") or None)
            js_type = _to_json_type(typ)
            desc = (doc_args.get(arg_name, {}).get("description") or "").strip()

            props[arg_name] = {"type": js_type}
            if desc:
                props[arg_name]["description"] = desc
            if d is None:  # no default provided -> required
                required.append(arg_name)

        schema = {
            "type": "function",
            "name": name,
            "description": summary,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": required,
            },
        }
        schemas.append(schema)

    return schemas


# In-memory index of tool locations (computed only during discovery).
# Each entry: {"name": <function_name>, "module": <module_name>, "file": <absolute_path>}
_TOOL_LOCATION_INDEX: List[Dict[str, str]] = []


def get_tool_location_index() -> List[Dict[str, str]]:
    """Return a shallow copy of the last-built tool location index."""
    return list(_TOOL_LOCATION_INDEX)


def identify_tools(directory: str) -> List[Dict[str, Any]]:
    """Scan a directory for Python files and return merged tool schemas for all functions.

    Also records a separate in-memory index mapping function names to their module files.
    The index is rebuilt only when this discovery runs (no extra overhead elsewhere).
    """
    try:
        files = [f for f in os.listdir(directory) if f.endswith(".py")]
    except OSError:
        return []

    files = [
        f for f in files
        if f != "__init__.py" and "__pycache__" not in f and "ignore" not in f
    ]

    all_tools: List[Dict[str, Any]] = []
    # rebuild index
    del _TOOL_LOCATION_INDEX[:]
    for file in files:
        path = os.path.join(directory, file)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        schemas = functions_to_tool_schemas(content)
        all_tools.extend(schemas)
        # capture module/function mapping
        module_name = os.path.splitext(file)[0]
        abs_path = os.path.abspath(path)
        for s in schemas:
            func_name = s.get("name", "")
            if func_name:
                _TOOL_LOCATION_INDEX.append({"name": func_name, "module": module_name, "file": abs_path})
    return all_tools


if __name__ == "__main__":
    tools = identify_tools("Agent/Tools")
    print(json.dumps(tools, indent=2))



