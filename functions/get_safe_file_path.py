import os

def get_safe_file_path(working_directory, file_path):
    abs_working_directory = os.path.abspath(working_directory)
    abs_file_path = os.path.abspath(os.path.join(working_directory, file_path))
    try:
        if os.path.commonpath(
            [abs_working_directory, abs_file_path]
        ) != abs_working_directory:
            return None
    except ValueError:
        return None
    return abs_file_path