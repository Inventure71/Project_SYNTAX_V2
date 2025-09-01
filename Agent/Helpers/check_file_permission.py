import os
import json

with open("Agent/Prompts/blocked_files.json", "r") as f:
    blocked_files = json.load(f)


def check_file_permission(file_path):
    sections = file_path.split("/")

    for path in sections:
        if path in blocked_files["files"]:
            return False
    return True