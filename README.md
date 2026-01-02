# Remote Chat CLI

A simple web-based UI to interact with command-line LLM tools (like Gemini, Claude) in different project contexts. This application allows you to manage conversations separately for each project directory.

## Features

- **Project-Based Context**: Each subdirectory inside a base directory (`C:\developer\` by default) is treated as a separate project.
- **Web Interface**: A user-friendly web UI to select projects and chat.
- **CLI Tool Integration**: Executes LLM commands (`gemini-cli`, `claude`, etc.) within the selected project's directory.
- **Conversation History**: Saves chat history for each project in a local SQLite database (`chat_history.db`).
- **Secure by Design**: The server manages all paths, preventing the client from accessing arbitrary directories.

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: SQLite

## Requirements

- Python 3.x
- Flask (`pip install Flask`)
- An LLM command-line tool (e.g., `gemini-cli`, `claude`) installed and accessible in your system's PATH.

## Setup and Run

1.  **Clone the Repository**:
    ```bash
    git clone <repository-url>
    cd remoteChat-cli
    ```

2.  **Create Project Directories**:
    - This application scans the `C:\developer\` directory. Create some subfolders there to represent your projects.
    - Example: `C:\developer\project-alpha`, `C:\developer\project-beta`.
    - *To change this path, edit the `BASE_DIR` variable in `app.py`.*

3.  **Set Up a Virtual Environment (Recommended)**:
    ```bash
    # Create a virtual environment
    python -m venv venv

    # Activate it
    .\venv\Scripts\activate
    ```

4.  **Install Dependencies**:
    ```bash
    pip install Flask
    ```

5.  **Run the Server**:
    - Simply double-click the `run_server.bat` file.
    - Or, run this command in your terminal:
      ```bash
      python app.py
      ```

6.  **Access the Application**:
    - Open your web browser and navigate to `http://127.0.0.1:5000`.

## API Endpoints

- `GET /api/projects`: Returns a list of all project folders.
- `POST /api/select-project`: Sets the active project for the session.
- `POST /api/query`: Executes the CLI command with the user's message and saves the conversation.
- `GET /api/history`: Retrieves the chat history for a specified project.

---
This project was initiated with the help of an AI assistant.
