import os

def read_file(file_path, line_count: bool = False):
    """
    Read and return the contents of a file with optional line numbering.

    Args:
        file_path (str): The relative path (from the project root) to the file to read, 
            including the file name and extension. Only specific file types are supported 
            (e.g., .py, .txt, .md, .json, .yaml, .xml, .html, .css, .js, .ts, .vue, .php, 
            .sql, .csv, .ini, .conf, .log).
        line_count (bool, optional): If True, return the file contents as a single string 
            with each line prefixed by its line number. If False (default), return a list 
            of file lines.

    Returns:
        str | list[str]: 
            - A numbered string of file contents if `line_count=True`.
            - A list of file lines if `line_count=False`.
            - An error message string if the file does not exist, is not a file, 
              or has an unsupported extension.
    """

    if not os.path.exists(file_path):
        return f"File {file_path} does not exist."

    if not os.path.isfile(file_path):
        return f"File {file_path} is not a file."

    if not file_path.endswith((
        ".py", ".txt", ".md", ".json", ".yaml", ".yml", ".xml", ".html", ".css",
        ".js", ".ts", ".jsx", ".tsx", ".vue", ".php", ".sql", ".csv", ".ini", ".conf", ".log"
    )):
        return f"File {file_path} is not a valid file type."

    with open(file_path, "r") as file:

        if line_count:
            lines = [f"{i}. {line.rstrip()}" for i, line in enumerate(file.readlines())]
            lines = "\n".join(lines)
            return lines
        else:
            return file.readlines()


if __name__ == "__main__":
    
    print(read_file("Agent/Tools/read_file.py", line_count=True))