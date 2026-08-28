import os
import subprocess
from google.genai import types
from functions.get_safe_file_path import get_safe_file_path

def run_python_file(working_directory: str, file_path: str, args = None):
    if args is None:
        args = []
    abs_file_path = get_safe_file_path(working_directory, file_path)
    abs_working_directory = os.path.abspath(working_directory)
    if abs_file_path is None:
        return f"Error: {file_path} is not in working directory"
    if not os.path.isfile(abs_file_path):
        return f"Error: {file_path} is not a file"
    if not file_path.endswith(".py"):
        return f"Error: {file_path} is not a python file"

    try:
        final_args = ["python", file_path]
        final_args.extend(args)
        output = subprocess.run(
            final_args,
            cwd = abs_working_directory,
            timeout = 30,
            capture_output = True
        )
        final_string =  f"""
STDOUT: {output.stdout}
STDERR: {output.stderr}
"""
        if output.stdout == "" and output.stderr == "":
            final_string = "No output produced.\n"
        if output.returncode != 0:
            final_string += f"Process exited with code {output.returncode}"
        return final_string
        
    except Exception as e:
        return f"Error: executing Python file: {e}"

schema_run_python_file = types.FunctionDeclaration(
    name = "run_python_file",
    description = "Runs a python file with the python interpreter. Accepts additional CLI args as an optional array.",
    parameters = types.Schema(
        type = types.Type.OBJECT,
        properties = {
            "file_path" : types.Schema(
                type = types.Type.STRING,
                description = " The path to the file, from the working directory."
            ),
            "args" : types.Schema(
                type = types.Type.ARRAY,
                description = "An optional array of string to be used as the CLI args for the Python file.",
                items = types.Schema(
                    type = types.Type.STRING
                )
            )
        }
    )
)