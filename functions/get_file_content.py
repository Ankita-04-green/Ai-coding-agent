import os
from google.genai import types
from config import MAX_CHARS
from functions.get_safe_file_path import get_safe_file_path

def get_file_content(working_directory, file_path, start_line = None, end_line = None):
    abs_file_path = get_safe_file_path(working_directory, file_path)
    if abs_file_path is None:
        return f"Error: {file_path} is not in the working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file"

    file_content_string = ""
    try:
        with open(abs_file_path, "r") as f:
            if start_line is None:
                file_content_string = f.read(MAX_CHARS + 1)
                if len(file_content_string) > MAX_CHARS:
                    file_content_string = file_content_string[:MAX_CHARS]
                    file_content_string += (
                        f"\n[...File {file_path} truncated at 10000 characters]"
                    )

                return file_content_string

            result = []
            for line_number, line in enumerate(f, start = 1):
                if line_number < start_line:
                    continue
                if end_line is not None and line_number > end_line:
                    break
                result.append(f"{line_number}: {line.rstrip()}")
            return "".join(line + "\n" for line in result)
        
    except Exception as e:
        return f"Exception reading file: {e}"

schema_get_file_content = types.FunctionDeclaration(
    name = "get_file_content",
    description = "Gets the contents of the given file as a string, constrained to the working directory.",
    parameters = types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "file_path" : types.Schema(
                type = types.Type.STRING,
                description = " The path to the file, from the working directory."
            ),
            "start_line": types.Schema(
                type = types.Type.INTEGER,
                description = "The first line to read. Use this when only a specific section of a file is needed."
            ),
            "end_line": types.Schema(
                type = types.Type.INTEGER,
                description = "The last line to read. Use this when only a specific section of a file is needed."
            )
        },
        required = ["file_path"]
    )
)