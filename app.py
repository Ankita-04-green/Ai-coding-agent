import os
import io
import zipfile
import uuid
import json
import threading
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, session, send_file, Response, stream_with_context
from flask_cors import CORS
from agent import run_agent
from conversation import init_db, save_message, get_messages
from queue import Queue

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")
init_db()
CORS(app)

UPLOAD_DIR = "uploaded_projects"

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/chat", methods=["POST"])
def chat():
    prompt = request.form.get("prompt")
    files = request.files.getlist("files")
    new_project = request.form.get("new_project") == "true"
    
    working_directory = None
    project_id = None
    if new_project and files and files[0].filename:
        #creating unique user id in each session
        project_id = str(uuid.uuid4())
        session["project_id"] = project_id

        working_directory = os.path.abspath(os.path.join(UPLOAD_DIR, project_id))

        os.makedirs(working_directory, exist_ok = True)
        for file in files:
            parts = file.filename.replace("\\", "/").split("/")
            relative_path = os.path.join(*parts[1:])
            file_path = os.path.join(working_directory, relative_path)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            print("SAVED:", file_path)

    elif "project_id" in session:
        project_id = session["project_id"]
        working_directory = os.path.abspath(os.path.join(UPLOAD_DIR, project_id))

    # print("WORKING DIRECTORY:", working_directory)
    if not prompt:
        return jsonify({"Error": "Prompt is required"}), 400

    #get conversation
    conversation = []
    if project_id:
        conversation = get_messages(project_id)
        save_message(project_id, "user", prompt)

    def generate():
        status_queue = Queue()

        def status_callback(message):
            status_queue.put(message)

        result = {}
        def run():
            response, project_modified = run_agent(prompt, working_directory, conversation, status_callback=status_callback)
            result["response"] = response
            result["project_modified"] = project_modified

        agent_thread = threading.Thread(target=run)
        agent_thread.start()

        while agent_thread.is_alive():
            try:
                status = status_queue.get(timeout=0.5)
                yield f"data: {json.dumps({
                    'type': 'status',
                    'message': status
                })}\n\n"
            except:
                pass

        while not status_queue.empty():
            status = status_queue.get()
            yield f"data: {json.dumps({
                'type': 'status',
                'message': status
            })}\n\n"
        agent_thread.join()

        response = result.get("response")
        project_modified = result.get("project_modified", False)
        if project_id:
            if response:
                save_message(project_id, "model", response)
            else:
                print("WARNING: No response received, skipping database save.")
        
        yield f"data: {json.dumps({
            'type': 'final',
            'response': response,
            'project_modified': project_modified
        })}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream"
    )
      
    # return jsonify({"response": response, "project_modified": project_modified})

@app.route("/download-project")
def download_project():
    project_id = session.get("project_id")
    if not project_id:
        return {"Error: No project selected"}, 404
    project_dir = os.path.abspath(os.path.join(UPLOAD_DIR, project_id))
    if not os.path.isdir(project_dir):
        return {"Error: Project not found"}, 404
    memory_file = io.BytesIO()

    with zipfile.ZipFile(memory_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(project_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                arcname = os.path.relpath(file_path, project_dir)
                zip_file.write(file_path, arcname)

    memory_file.seek(0)
    return send_file(memory_file, as_attachment = True, download_name="modified_project.zip", mimetype="application/zip")
        

if __name__ == "__main__":
    app.run()
