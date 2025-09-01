import os
from typing import Dict, Optional

from Agent.Tools.helpers_ignore import print_tree


def get_project_structure(complex_mode: bool = False) -> str:
    """
    Build a hierarchical view of the project folders and files as a nested dictionary.

    Directories are represented as dictionaries (mapping names to nested entries).
    Files are represented with a value of None.

    Returns:
        string: { <root_name>: { <entry>: (None | dict), ... } }
    """
    try:
        root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

        ignore_exact = {".git", "__pycache__", ".DS_Store", "node_modules", ".venv"}

        def build_tree(current_path: str) -> Dict[str, Optional[dict]]:
            tree: Dict[str, Optional[dict]] = {}
            try:
                entries = sorted(os.listdir(current_path))
            except OSError:
                return tree

            for name in entries:
                if name in ignore_exact or name.startswith("."):
                    continue

                full_path = os.path.join(current_path, name)
                if os.path.isdir(full_path):
                    tree[name] = build_tree(full_path)
                else:
                    tree[name] = None
            return tree

        tree = build_tree(root_path)
        if complex_mode:
            view_tree = print_tree(tree)
            return f"{os.path.basename(root_path)}: {tree}\nASHII_TREE: {view_tree}"
        else:
            return f"{os.path.basename(root_path)}: {tree}"
    except Exception as e:
        print(f"Error getting project structure: {e}")
        return f"Error getting project structure: {e}"



if __name__ == "__main__":
    tree = get_project_structure(complex_mode=True)
    print(tree)

