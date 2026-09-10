import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from functions.get_files_info import schema_get_files_info
from functions.get_file_content import schema_get_file_content
from functions.run_python_file import schema_run_python_file
from functions.write_file import schema_write_file
from functions.search_file import schema_search_file
from call_function import call_function

INJECTION_PATTERNS = [
    "ignore previous",
    "ignore all instructions",
    "you are now",
    "disregard your",
    "new instructions:"
]

def detect_injection(message):
    lowered = message.lower()
    for pattern in INJECTION_PATTERNS:
        if pattern in lowered:
            return True
    return False

def run_agent(prompt, working_directory=None, conversation = None, status_callback=None):
    if detect_injection(prompt):
        return "I cannot process that request.", False
    def send_status(message):
        if status_callback:
            status_callback(message)

    load_dotenv()
    api_key_1 = os.environ.get("GEMINI_API_KEY_1")
    api_key_2 = os.environ.get("GEMINI_API_KEY_2")
    client1 = genai.Client(api_key = api_key_1)
    client2 = genai.Client(api_key = api_key_2)
    current_client = client1
    using_fallback = False

    project_modified = False

    system_prompt = """
    You are a helpful AI coding agent. You ONLY help with software development and the user's project.

    For simple conversational messages like "hello", "hi", or "thanks", respond normally without using tools.

    For anything unrelated to software/projects, respond EXACTLY:
    ASK QUESTIONS RELATED TO YOUR PROJECT

    For project-related requests, ALWAYS follow this order:

    1. FIRST show a short bullet-point plan to the user.
    2. THEN execute the plan using tools.
    3. VERIFY the changes when possible.
    4. FINALLY explain what was changed.

    NEVER call a tool before showing the plan.

    You can:
    - For uploaded projects, first use get_file_info to understand the project. Use search_file to locate code relevant to the user's issue, then use get_file_content with the returned line range to inspect the surrounding code. Do not blindly read large files. Verify suspected issues by running the relevant code before modifying files.
    - Create/update files
    - Run Python files with optional arguments
    All paths must be relative to the working directory. The working directory is automatically provided to tools.

    For code changes, keep the final response concise and use Markdown.
    Use:
    ### Summary
    Briefly explain the bug and fix.

    ### Files Changed
    - `path/to/file.py` — what changed

    ### Changes
    Show only relevant changes using a `diff` code block.

    ### Verification
    State what was tested and the result.
    Use Markdown headings, bullet lists, inline code, and fenced code blocks.

    If there is a need to create new file 
    - Display name of the file
    - Where to store it 
    - Content inside it
    - Chnages made to other files due to new file

    Do not invent files, code, results, or test results."""
    #This is a way of getting prompt from console
    # if len(sys.argv) < 2:
    #     print("I need a prompt")
    #     sys.exit(1)
    # prompt = sys.argv[1]

    # verbose_flag = False
    # if len(sys.argv) == 3 and sys.argv[2] == "--verbose":
    #     verbose_flag = True
    messages = []
    if conversation:
        for role, content in conversation:
            messages.append(types.Content(role=role, parts=[types.Part(text=content)]))
    messages.append(
        types.Content(role = "user", parts = [types.Part(text=prompt)]),
    )

    available_functions = types.Tool(
        function_declarations = [
            schema_get_files_info,
            schema_search_file,
            schema_get_file_content,
            schema_run_python_file,
            schema_write_file,
        ]
    )
    
    if working_directory is not None:
        config = types.GenerateContentConfig(
            tools = [available_functions],
            system_instruction = system_prompt
        )
    else:
        config = types.GenerateContentConfig(
            system_instruction = system_prompt
        )

    model = "gemini-3.6-flash"

    max_iters = 11
    for i in range(0, max_iters):
        if i >= max_iters - 2:
            print(f"WARNING: approaching iteration limit ({i}/{max_iters})")

        try:
            response = current_client.models.generate_content(
                model = model,
                contents = messages,
                config = config
            )
        except Exception as e:
              if getattr(e, "code", None) == 429 or "429" in str(e):
                    if not using_fallback:
                        print("Gemini API 1 quota/rate limit reached.")
                        print("Switching to Gemini API 2...")
                        current_client = client2
                        using_fallback = True
                        try:
                            response = current_client.models.generate_content(
                                model=model,
                                contents=messages,
                                config=config
                            )
                        except Exception as fallback_error:
                            print("API 2 also failed:",
                                  fallback_error)

                            return "Something went wrong while contacting the agent.", False
                    else:
                        print("Both Gemini API keys have reached their current quota. Please try again later.")
                        return "Something went wrong while contacting the agent.", False
              else:
                    print("ERROR: ", e)
                    return "An error occurred while contacting the AI service.", False
    
        if response is None:
            print("Response is malformed")
            return "I couldn't get a response from the AI.", False

        # if verbose_flag:
        #     print(f"User prompt: {prompt}")
        #     print(f"Prompt Tokens : {response.usage_metadata.prompt_token_count}")
        #     print(f"Response Tokens : {response.usage_metadata.candidates_token_count}")

        if response.candidates:
            for candidate in response.candidates:
                if candidate is None or candidate.content is None:
                    continue
                print("--------------")
                messages.append(candidate.content)
        
        if response.function_calls:
            for function_call_part in response.function_calls:
                tool_name = function_call_part.name

                status_messages = {
                    "get_file_info": "Inspecting your project files...",
                    "get_file_content": "Reading the relevant file...",
                    "search_file": "Searching your project for the error...",
                    "run_python_file": "Running the code to test the issue...",
                    "write_file": "Applying the fix..."
                }

                status = status_messages.get(tool_name, "Working on your project...")
                send_status(status)

                result, project_modified = call_function(function_call_part, working_directory)
                messages.append(result)
        else:
            #final agent text message
            # print("Agent Response: ", response.text)
            return response.text, project_modified
    else:
        send_status("Finishing the analysis...")
        messages.append(types.Content(role = "user", parts = [types.Part(text = "You've reached the maximum number of steps. Give your best answer with what you have. Do not call any tools.")]))
        final_config = types.GenerateContentConfig(system_instruction=system_prompt + "\nIMPORTANT: this is the final response. Do not call any tools. Return only a text response.")
        try:
            final = current_client.models.generate_content(model=model, contents=messages, config=final_config)
            return final.text, project_modified
        except Exception as e:
            print("Final response generation failed: ", e)
            return "An error occurred while contacting the AI service.", project_modified