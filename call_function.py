from functions.get_files_info import get_files_info
from functions.get_file_content import get_file_content
from functions.run_python_file import run_python_file
from functions.write_file import write_file
from functions.search_file import search_file
from google.genai import types



def call_function(function_call_part, working_directory):
    # if verbose:
    #     print(f"Calling function: {function_call_part.name}({function_call_part.args})")
    # else:
    print(f"Calling function: {function_call_part.name}")
    modified = False
    result = ""
    if function_call_part.name == "get_files_info":
        result = get_files_info(working_directory, **function_call_part.args)
    if function_call_part.name == "search_file":
        result = search_file(working_directory, **function_call_part.args)
    if function_call_part.name == "get_file_content":
        result = get_file_content(working_directory, **function_call_part.args)
    if function_call_part.name == "run_python_file":
        result = run_python_file(working_directory, **function_call_part.args)
    if function_call_part.name == "write_file":
        result, modified = write_file(working_directory, **function_call_part.args)

    if result == "":
        return (types.Content(
            role = "tool",
            parts = [
               types.Part.from_function_response(
                    name = function_call_part.name,
                    response = {"error": f"Unknown function: {function_call_part.name}"},
                )
            ]
        ), modified)
    
    return (types.Content(
        role = "user",
        parts = [
            types.Part.from_function_response(
                name = function_call_part.name,
                response = {"result": result}  
            )
        ]
    ), modified)