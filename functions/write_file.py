import os
from google.genai import types
from functions.get_safe_file_path import get_safe_file_path

def write_file(working_directory, file_path, content):
    abs_file_path = get_safe_file_path(working_directory, file_path)
    if abs_file_path is None:
        return f"Error: {file_path} is not in the working directory"
    parent_dir = os.path.dirname(abs_file_path)
    if not os.path.isdir(parent_dir):
        try:
            os.makedirs(parent_dir)
        except Exception as e:
            return f"Could not create parent dirs: {parent_dir} = {e}"

    try:
        old_content = ""
        if os.path.exists(abs_file_path):
            with open(abs_file_path, "r", encoding="utf-8") as f:
                old_content += f.read()

        with open(abs_file_path, "w", encoding="utf-8") as f:
            f.write(content)
        modified = old_content != content
        return f"Successfully wrote to {file_path} ({len(content)} characters written)", modified
    except Exception as e:
        return f"Failed to write to file: {file_path}, {e}", False

schema_write_file = types.FunctionDeclaration(
    name = "write_file",
    description = "Overwrites an existing file or writes to a new file if it doesn't exist and creates required parent dirs safely, constrained to the working directory.",
    parameters = types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "file_path" : types.Schema(
                type = types.Type.STRING,
                description = " The path to the file to write."
            ),
            "content" : types.Schema(
                type = types.Type.STRING,
                description = "The content to write to the file as a string."
            )
        }
    )
)