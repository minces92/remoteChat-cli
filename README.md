# Remote Chat CLI

A simple web-based UI to interact with command-line LLM tools (like Gemini, Claude) in different project contexts. This application allows you to manage conversations separately for each project directory.

## Features

- **Project-Based Context**: Each subdirectory inside a base directory (`C:\developer\` by default) is treated as a separate project.
- **Web Interface**: A user-friendly web UI to select projects and chat.
- **CLI Tool Integration**: Executes LLM commands (`gemini-cli`, `claude`, etc.) within the selected project's directory.
- **Conversation History**: Saves chat history for each project in a local SQLite database (`chat_history.db`).
- **Secure by Design**: The server manages all paths, preventing the client from accessing arbitrary directories.
- **Authentication**: Login system with configurable user accounts stored in `.env` file.
- **Login Protection**: Account lockout after 5 failed login attempts (requires server restart to unlock).

## Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Vanilla JavaScript
- **Database**: SQLite

## Requirements

- Python 3.x
- Flask
- python-dotenv
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
    pip install -r requirements.txt
    ```
    또는 개별 설치:
    ```bash
    pip install Flask python-dotenv
    ```

5.  **환경 변수 설정**:
    - `.env.example` 파일을 `.env`로 복사합니다:
      ```bash
      copy .env.example .env
      ```
    - 비밀번호 해시 생성:
      ```bash
      python generate_password_hash.py <password>
      ```
      예시:
      ```bash
      python generate_password_hash.py admin123
      ```
    - `.env` 파일을 열어 허가된 사용자 계정을 설정합니다:
      ```
      ALLOWED_USERS=username1:hashed_password1,username2:hashed_password2
      MAX_LOGIN_ATTEMPTS=5
      ```
      **중요**: 비밀번호는 평문이 아닌 해시값을 사용해야 합니다.
    - **보안**: `.env` 파일은 보안상 중요한 정보를 포함하므로 절대 공유하지 마세요.
    - **비밀번호 변경**: 비밀번호 변경 방법은 `CHANGE_PASSWORD.md` 파일을 참조하세요.
    - **필수 설정**: `.env` 파일에 `ALLOWED_USERS`가 설정되어 있지 않으면 로그인이 불가능합니다. 하드코딩된 기본 계정은 제거되었습니다.

6.  **Run the Server**:
    - Simply double-click the `run_server.bat` file.
    - Or, run this command in your terminal:
      ```bash
      python app.py
      ```

7.  **Access the Application**:
    - Open your web browser and navigate to `http://127.0.0.1:5000`.

## API Endpoints

- `GET /api/projects`: Returns a list of all project folders.
- `POST /api/select-project`: Sets the active project for the session.
- `POST /api/query`: Executes the CLI command with the user's message and saves the conversation.
- `GET /api/history`: Retrieves the chat history for a specified project.

## 보안

- **보안 감사**: 보안 취약점 및 개선 사항은 `SECURITY_AUDIT.md`를 참조하세요.
- **보안 개선 투두리스트**: 보안 개선 작업 목록은 `SECURITY_TODO.md`를 참조하세요.

---
This project was initiated with the help of an AI assistant.
"# remoteChat-cli" 
