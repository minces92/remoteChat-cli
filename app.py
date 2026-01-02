from flask import Flask, jsonify, request, render_template, session
import os
import subprocess
import sqlite3
import json
from datetime import datetime

# --- Configuration ---
# WARNING: Do not change this path unless you are sure. This is the root directory for projects.
BASE_DIR = "C:\\developer\\"
DB_FILE = "chat_history.db"

app = Flask(__name__)
# It is recommended to use a more secure and persistent secret key in a real environment.
app.secret_key = os.urandom(24)

# --- Database Setup ---
def init_db():
    """Initializes the database and creates the history table if it doesn\'t exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projectId TEXT NOT NULL,
            timestamp DATETIME NOT NULL,
            cli TEXT NOT NULL,
            user_message TEXT NOT NULL,
            assistant_message TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# --- Helper Functions ---
def get_projects():
    """Scans the base directory for subdirectories and returns them as a list of projects."""
    projects = []
    if not os.path.isdir(BASE_DIR):
        return []
    for item in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, item)
        if os.path.isdir(full_path):
            projects.append({
                "id": item,
                "name": item,
                "path": full_path
            })
    return projects

def get_project_path(project_id):
    """
    Gets the full path for a project ID and performs a security check.
    Returns the path if valid, otherwise None.
    """
    if not project_id or '..' in project_id or '/' in project_id or '\\' in project_id:
        return None
        
    project_path = os.path.join(BASE_DIR, project_id)
    
    # Security Check: Ensure the path is a subdirectory of BASE_DIR
    if not os.path.commonpath([BASE_DIR]) == os.path.commonpath([BASE_DIR, project_path]) or not os.path.isdir(project_path):
        return None
        
    return project_path

# --- API Endpoints ---
@app.route('/api/projects', methods=['GET'])
def list_projects():
    """Returns the list of projects."""
    projects = get_projects()
    return jsonify(projects)

@app.route('/api/select-project', methods=['POST'])
def select_project():
    """Saves the selected project ID to the session."""
    data = request.json
    project_id = data.get('projectId')
    if not project_id or not get_project_path(project_id):
        return jsonify({"error": "Invalid project ID"}), 400
    
    session['selected_project_id'] = project_id
    return jsonify({"message": f"Project '{project_id}' selected."})

@app.route('/api/query', methods=['POST'])
def handle_query():
    """
    Executes a CLI command in the specified project directory and returns the result.
    Saves the conversation to the history.
    """
    data = request.json
    project_id = data.get('projectId')
    cli_tool = data.get('cli')
    message = data.get('message')

    if not all([project_id, cli_tool, message]):
        return jsonify({"error": "Missing projectId, cli, or message"}), 400

    project_path = get_project_path(project_id)
    if not project_path:
        return jsonify({"error": "Invalid or unauthorized project path"}), 400

    # Determine the command based on the selected CLI tool
    # NOTE: These commands are examples. Adjust them if your CLI tools require different arguments.
    command = []
    if cli_tool == 'gemini':
        # Example for Gemini: gemini-cli prompt "your message"
        command = ["gemini-cli", "prompt", message]
    elif cli_tool == 'claude':
         # Example for Claude: claude prompt "your message"
        command = ["claude", "prompt", message]
    else:
        return jsonify({"error": "Unsupported CLI tool"}), 400
    
    try:
        # Execute the command
        result = subprocess.run(
            command,
            cwd=project_path,
            capture_output=True,
            text=True,
            check=True,  # Raises CalledProcessError for non-zero exit codes
            encoding='utf-8'
        )
        assistant_response = result.stdout.strip()

        # Save to database
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (projectId, timestamp, cli, user_message, assistant_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (project_id, datetime.now(), cli_tool, message, assistant_response))
        conn.commit()
        conn.close()

        return jsonify({"assistant_message": assistant_response})

    except FileNotFoundError:
        error_msg = f"Error: The command '{command[0]}' was not found. Make sure it is installed and in your system\'s PATH."
        return jsonify({"error": error_msg}), 500
    except subprocess.CalledProcessError as e:
        error_msg = f"CLI command failed with exit code {e.returncode}:\n{e.stderr}"
        return jsonify({"error": error_msg}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns the chat history for a given project."""
    project_id = request.args.get('projectId')
    if not project_id:
        return jsonify({"error": "projectId is required"}), 400

    # Security check is implicitly done by querying with projectId
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM history WHERE projectId = ? ORDER BY timestamp ASC", (project_id,))
    rows = cursor.fetchall()
    conn.close()

    history_list = [dict(row) for row in rows]
    return jsonify(history_list)


# --- Frontend Route ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# --- Main Execution ---
if __name__ == '__main__':
    init_db()
    # For development, debug=True is fine. For production, use a proper WSGI server.
    app.run(debug=True, port=5000)
