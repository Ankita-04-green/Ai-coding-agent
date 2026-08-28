import os
from google.genai import types
from functions.get_safe_file_path import get_safe_file_path

def search_file(working_directory, file_path, query):
    abs_file_path = get_safe_file_path(working_directory, file_path)
    if abs_file_path is None:
        return f"Error: {file_path} is not in the working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file"

    try:
        matches = []
        with open(abs_file_path, "r", encoding="utf-8") as f:
            for line_number, line in enumerate(f, start = 1):
                if query.lower() in line.lower():
                    matches.append(f"Line {line_number}: {line.rstrip()}")
                if len(matches) >= 50:
                    break

        if not matches:
            return f"No matches found for '{query}' in {file_path}"

        result = "\n".join(matches)
        if len(matches) >= 50:
            result += "\n[Search results limited to 50 matches]"
        return result

    except Exception as e:
        return f"Exception searching file: {e}"

schema_search_file = types.FunctionDeclaration(
    name = "search_file",
    description = "Searches for a text string in a file and returns the line numbers and matching lines. Use this to locate relevant code before reading a large file.",
    parameters = types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "file_path": types.Schema(
                type = types.Type.STRING,
                description = "The path to the file from the working directory."
            ),
            "query": types.Schema(
                type = types.Type.STRING,
                description = "The text, function name, class name, variable name, error message, or other code to search for."
            )
        },
        required = ["file_path", "query"]
    )
)