from flask import Flask, jsonify, request, render_template, session, redirect, url_for
from functools import wraps
import os
import subprocess
import sqlite3
import json
import shutil
from datetime import datetime
from dotenv import load_dotenv
import bcrypt
import socket
import threading
import time
import re
from authlib.integrations.flask_client import OAuth
import requests

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
# BASE_DIR은 .env 파일에서 가져옵니다. 없으면 기본값 사용
BASE_DIR = os.getenv('BASE_DIR', 'C:\\developer\\')
# 경로가 끝에 백슬래시가 없으면 추가
if BASE_DIR and not BASE_DIR.endswith(os.sep):
    BASE_DIR += os.sep
DB_FILE = "chat_history.db"
SERVER_PORT = int(os.getenv('SERVER_PORT', '5000'))  # 서버 포트
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')  # 관리자 사용자명

# --- Authentication Configuration ---
# 허가된 사용자 목록은 .env 파일에서 로드됩니다.
# 형식: ALLOWED_USERS=username1:hashed_password1,username2:hashed_password2
# 비밀번호는 bcrypt로 해시화되어 저장되어야 합니다.
# 해시 생성은 generate_password_hash.py 스크립트를 사용하세요.

def hash_password(password):
    """비밀번호를 bcrypt로 해시화합니다."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    """입력된 비밀번호가 해시된 비밀번호와 일치하는지 확인합니다."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def load_allowed_users():
    """
    환경 변수에서 허가된 사용자 목록을 로드합니다.
    .env 파일에 ALLOWED_USERS가 설정되어 있지 않으면 빈 딕셔너리를 반환합니다.
    """
    users_str = os.getenv('ALLOWED_USERS', '').strip()
    
    if not users_str:
        # .env 파일에 설정이 없으면 빈 딕셔너리 반환 (보안상 하드코딩된 계정 제거)
        print("WARNING: ALLOWED_USERS is not set in .env file. No users will be able to log in.")
        print("Please set ALLOWED_USERS in .env file. See .env.example for format.")
        return {}
    
    users = {}
    # 형식: username1:hashed_password1,username2:hashed_password2
    for user_hash in users_str.split(','):
        user_hash = user_hash.strip()
        if not user_hash:
            continue
        if ':' in user_hash:
            username, hashed_password = user_hash.split(':', 1)
            username = username.strip()
            hashed_password = hashed_password.strip()
            if username and hashed_password:
                users[username] = hashed_password
        else:
            print(f"WARNING: Invalid user format in ALLOWED_USERS: {user_hash}. Expected format: username:hashed_password")
    
    if not users:
        print("WARNING: No valid users found in ALLOWED_USERS. Please check your .env file.")
    
    return users

ALLOWED_USERS = load_allowed_users()  # username: hashed_password 딕셔너리
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))  # 최대 로그인 시도 횟수

def load_allowed_oauth_users():
    """환경 변수에서 허가된 OAuth 사용자 목록을 로드합니다."""
    users_str = os.getenv('ALLOWED_OAUTH_USERS', '').strip()
    if not users_str:
        return []
    return [u.strip() for u in users_str.split(',') if u.strip()]

ALLOWED_OAUTH_USERS = load_allowed_oauth_users()

app = Flask(__name__)
# It is recommended to use a more secure and persistent secret key in a real environment.
app.secret_key = os.urandom(24)

# --- OAuth Setup ---
oauth = OAuth(app)

# Google OAuth 설정
google_client_id = os.getenv('GOOGLE_CLIENT_ID')
google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
if google_client_id and google_client_secret:
    oauth.register(
        name='google',
        client_id=google_client_id,
        client_secret=google_client_secret,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

# GitHub OAuth 설정
github_client_id = os.getenv('GITHUB_CLIENT_ID')
github_client_secret = os.getenv('GITHUB_CLIENT_SECRET')
if github_client_id and github_client_secret:
    oauth.register(
        name='github',
        client_id=github_client_id,
        client_secret=github_client_secret,
        access_token_url='https://github.com/login/oauth/access_token',
        access_token_params=None,
        authorize_url='https://github.com/login/oauth/authorize',
        authorize_params=None,
        api_base_url='https://api.github.com/',
        client_kwargs={'scope': 'user:email'},
    )

# --- Login Attempt Tracking ---
# 서버 메모리에 저장 (서버 재시작 시 초기화됨)
login_attempts = {}  # IP 주소별 시도 횟수
account_locked = False  # 전체 계정 잠금 상태

# --- Database Setup ---
def init_db():
    """Initializes the database and creates the history table if it doesn\'t exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projectId TEXT NOT NULL,
            sessionId TEXT,
            timestamp DATETIME NOT NULL,
            cli TEXT NOT NULL,
            user_message TEXT NOT NULL,
            assistant_message TEXT NOT NULL
        )
    ''')
    # sessionId 컬럼이 없으면 추가 (기존 데이터베이스 마이그레이션)
    try:
        cursor.execute('ALTER TABLE history ADD COLUMN sessionId TEXT')
    except sqlite3.OperationalError:
        pass  # 컬럼이 이미 존재하는 경우
    conn.commit()
    conn.close()

# --- Authentication Helper Functions ---
def get_client_ip():
    """클라이언트 IP 주소를 가져옵니다."""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

def is_account_locked():
    """계정이 잠겨있는지 확인합니다."""
    return account_locked

def increment_login_attempts():
    """로그인 시도 횟수를 증가시킵니다."""
    global account_locked
    client_ip = get_client_ip()
    
    if client_ip not in login_attempts:
        login_attempts[client_ip] = 0
    
    login_attempts[client_ip] += 1
    
    # 전체 시도 횟수가 MAX_LOGIN_ATTEMPTS를 초과하면 잠금
    total_attempts = sum(login_attempts.values())
    if total_attempts >= MAX_LOGIN_ATTEMPTS:
        account_locked = True
    
    return login_attempts[client_ip]

def reset_login_attempts():
    """로그인 성공 시 시도 횟수를 초기화합니다."""
    global account_locked
    client_ip = get_client_ip()
    if client_ip in login_attempts:
        del login_attempts[client_ip]
    # 모든 시도가 초기화되면 잠금 해제
    if not login_attempts:
        account_locked = False

def get_login_attempts():
    """현재 로그인 시도 횟수를 반환합니다."""
    client_ip = get_client_ip()
    return login_attempts.get(client_ip, 0)

def is_admin():
    """현재 세션이 관리자인지 확인합니다."""
    username = session.get('username')
    return username == ADMIN_USERNAME

def admin_required(f):
    """관리자 권한이 필요한 엔드포인트를 보호하는 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('authenticated'):
            return jsonify({"error": "인증이 필요합니다."}), 401
        if not is_admin():
            return jsonify({"error": "관리자 권한이 필요합니다."}), 403
        return f(*args, **kwargs)
    return decorated_function

def is_port_in_use(port):
    """포트가 사용 중인지 확인합니다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return False
        except OSError:
            return True

def kill_process_on_port(port):
    """특정 포트를 사용하는 프로세스를 종료합니다."""
    try:
        # Windows에서 포트를 사용하는 프로세스 찾기
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            shell=True
        )
        
        # 포트를 사용하는 PID 찾기
        pid = None
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) > 4:
                    pid = parts[-1]
                    break
        
        if pid:
            # 프로세스 종료
            subprocess.run(
                ['taskkill', '/F', '/PID', pid],
                capture_output=True,
                shell=True
            )
            time.sleep(2)  # 프로세스 종료 대기
            return True
        return False
    except Exception as e:
        print(f"Error killing process on port {port}: {e}")
        return False

def restart_server():
    """서버를 재시작합니다."""
    try:
        # 현재 작업 디렉토리 확인
        current_dir = os.path.dirname(os.path.abspath(__file__))
        restart_bat = os.path.join(current_dir, 'restart_server.bat')
        run_bat = os.path.join(current_dir, 'run_server.bat')
        
        # restart_server.bat이 있으면 사용, 없으면 run_server.bat 사용
        bat_file = restart_bat if os.path.exists(restart_bat) else run_bat
        
        if not os.path.exists(bat_file):
            return False, "서버 재시작 스크립트를 찾을 수 없습니다."
        
        # 포트가 사용 중이면 프로세스 종료
        if is_port_in_use(SERVER_PORT):
            print(f"Port {SERVER_PORT} is in use. Killing process...")
            kill_process_on_port(SERVER_PORT)
            time.sleep(1)
        
        # 배치 파일을 새 창에서 실행 (서버가 종료되기 전에 응답 반환)
        subprocess.Popen(
            ['cmd', '/c', 'start', bat_file],
            cwd=current_dir,
            shell=True
        )
        
        return True, "서버 재시작이 시작되었습니다."
    except Exception as e:
        return False, f"서버 재시작 중 오류 발생: {str(e)}"

def login_required(f):
    """인증이 필요한 페이지를 보호하는 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'authenticated' not in session or not session['authenticated']:
            # API 요청인 경우 JSON 응답 반환
            if request.path.startswith('/api/'):
                return jsonify({"error": "인증이 필요합니다.", "authenticated": False}), 401
            # 일반 페이지 요청인 경우 로그인 페이지로 리다이렉트
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Helper Functions ---
def find_command(command_name):
    """
    Finds the full path to a command by checking:
    1. System PATH using shutil.which()
    2. Windows npm global paths (if applicable)
    3. Common Windows locations
    
    Returns the full path if found, otherwise returns None.
    """
    # First, try shutil.which() which checks PATH
    command_path = shutil.which(command_name)
    if command_path:
        return command_path
    
    # On Windows, also check for .cmd and .bat extensions
    if os.name == 'nt':
        for ext in ['.cmd', '.bat', '.exe']:
            command_path = shutil.which(command_name + ext)
            if command_path:
                return command_path
        
        # Check common npm global installation paths on Windows
        npm_paths = [
            os.path.join(os.environ.get('APPDATA', ''), 'npm', command_name + '.cmd'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'npm', command_name + '.cmd'),
        ]
        
        for path in npm_paths:
            if os.path.isfile(path):
                return path
    
    return None

def get_projects():
    """Scans the base directory for subdirectories and returns them as a list of projects."""
    projects = []
    if not os.path.isdir(BASE_DIR):
        return []
    for item in os.listdir(BASE_DIR):
        full_path = os.path.join(BASE_DIR, item)
        if os.path.isdir(full_path):
            # 프로젝트에 run_server.bat이 있는지 확인
            run_server_bat = os.path.join(full_path, 'run_server.bat')
            restart_server_bat = os.path.join(full_path, 'restart_server.bat')
            has_server = os.path.exists(run_server_bat) or os.path.exists(restart_server_bat)
            
            # 프로젝트의 포트 정보 확인 (app.py나 .env에서)
            port = get_project_port(full_path)
            
            projects.append({
                "id": item,
                "name": item,
                "path": full_path,
                "has_server": has_server,
                "port": port
            })
    return projects

def get_project_port(project_path):
    """
    프로젝트 폴더에서 포트 정보를 찾습니다.
    규칙:
    1. .env 파일: SERVER_PORT=XXXX 또는 PORT=XXXX
    2. app.py 파일: app.run(port=XXXX), PORT = XXXX, 또는 # @port: XXXX 주석
    """
    def read_file_safe(file_path):
        for encoding in ['utf-8', 'cp949', 'latin-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return f.read()
            except Exception:
                continue
        return None

    # 1. .env 파일 확인
    env_file = os.path.join(project_path, '.env')
    if os.path.exists(env_file):
        content = read_file_safe(env_file)
        if content:
            # @port: XXXX 주석 확인
            match = re.search(r'@port:\s*(\d+)', content)
            if match:
                return int(match.group(1))
            
            # 정규표현식으로 직접 찾기 (dotenv_values 대신)
            match = re.search(r'(?:SERVER_PORT|PORT)\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))

    # 2. app.py 파일 확인
    app_py = os.path.join(project_path, 'app.py')
    if os.path.exists(app_py):
        content = read_file_safe(app_py)
        if content:
            # @port: XXXX 주석 확인 (가장 우선순위 높음)
            match = re.search(r'@port:\s*(\d+)', content)
            if match:
                return int(match.group(1))
            
            # app.run(port=XXXX) 또는 app.run(..., port=XXXX, ...)
            match = re.search(r'port\s*=\s*(\d+)', content)
            if match:
                return int(match.group(1))
            
            # SERVER_PORT = XXXX 또는 PORT = XXXX 패턴 찾기 (int() 감싸기 포함)
            match = re.search(r'(?:SERVER_PORT|PORT)\s*=\s*(?:int\()?(\d+)', content)
            if match:
                return int(match.group(1))
            
            # 마지막 수단: 파일 전체에서 "port" 단어 근처의 숫자 찾기
            # 예: "port": 5000, "port" : 5000 등
            match = re.search(r'port["\']?\s*[:=]\s*(\d{4,5})', content, re.IGNORECASE)
            if match:
                return int(match.group(1))
    
    return None

def restart_project_server(project_id):
    """특정 프로젝트의 서버를 재시작합니다."""
    project_path = get_project_path(project_id)
    if not project_path:
        return False, "프로젝트 경로를 찾을 수 없습니다."
    
    restart_bat = os.path.join(project_path, 'restart_server.bat')
    run_bat = os.path.join(project_path, 'run_server.bat')
    
    # restart_server.bat이 있으면 사용, 없으면 run_server.bat 사용
    bat_file = restart_bat if os.path.exists(restart_bat) else run_bat
    
    if not os.path.exists(bat_file):
        return False, f"프로젝트 '{project_id}'에 서버 재시작 스크립트를 찾을 수 없습니다."
    
    try:
        # 배치 파일을 새 창에서 실행 (포트 기반 종료 없이 스크립트에 위임)
        subprocess.Popen(
            ['cmd', '/c', 'start', bat_file],
            cwd=project_path,
            shell=True
        )
        return True, f"프로젝트 '{project_id}'의 서버 재시작이 시작되었습니다."
    except Exception as e:
        return False, f"서버 재시작 중 오류 발생: {str(e)}"

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

# --- Authentication API Endpoints ---
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    """로그인 API 엔드포인트"""
    global account_locked
    
    # 계정이 잠겨있는지 확인
    if account_locked:
        return jsonify({
            "success": False,
            "error": "계정이 잠겼습니다. 서버를 재시작해야 합니다.",
            "locked": True
        }), 403
    
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        attempts = increment_login_attempts()
        return jsonify({
            "success": False,
            "error": "아이디와 비밀번호를 입력해주세요.",
            "attempts": attempts,
            "locked": account_locked
        }), 400
    
    # 사용자 인증 확인 (해시된 비밀번호 비교)
    if username in ALLOWED_USERS and verify_password(password, ALLOWED_USERS[username]):
        # 로그인 성공
        reset_login_attempts()
        session['authenticated'] = True
        session['username'] = username
        return jsonify({
            "success": True,
            "message": "로그인 성공"
        })
    else:
        # 로그인 실패
        attempts = increment_login_attempts()
        locked = account_locked
        
        error_msg = "아이디 또는 비밀번호가 올바르지 않습니다."
        if locked:
            error_msg = "5회 이상 로그인에 실패하여 계정이 잠겼습니다. 서버를 재시작해야 합니다."
        
        return jsonify({
            "success": False,
            "error": error_msg,
            "attempts": attempts,
            "locked": locked
        }), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    """로그아웃 API 엔드포인트"""
    session.clear()
    return jsonify({"success": True, "message": "로그아웃되었습니다."})

# --- OAuth Routes ---

@app.route('/login/google')
def login_google():
    """Google OAuth 로그인 시작"""
    if not google_client_id:
        return "Google OAuth가 설정되지 않았습니다.", 400
    redirect_uri = url_for('auth_google', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def auth_google():
    """Google OAuth 콜백 처리"""
    try:
        token = oauth.google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            # OpenID Connect를 지원하지 않는 경우 직접 정보 요청
            resp = oauth.google.get('https://www.googleapis.com/oauth2/v3/userinfo')
            user_info = resp.json()
        
        email = user_info.get('email')
        
        if email in ALLOWED_OAUTH_USERS:
            reset_login_attempts()
            session['authenticated'] = True
            session['username'] = email
            session['oauth_provider'] = 'google'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=f"허가되지 않은 이메일입니다: {email}")
    except Exception as e:
        print(f"Google Auth Error: {e}")
        return redirect(url_for('login'))

@app.route('/login/github')
def login_github():
    """GitHub OAuth 로그인 시작"""
    if not github_client_id:
        return "GitHub OAuth가 설정되지 않았습니다.", 400
    redirect_uri = url_for('auth_github', _external=True)
    return oauth.github.authorize_redirect(redirect_uri)

@app.route('/auth/github/callback')
def auth_github():
    """GitHub OAuth 콜백 처리"""
    try:
        token = oauth.github.authorize_access_token()
        resp = oauth.github.get('user')
        user_info = resp.json()
        
        # GitHub은 사용자명 또는 이메일로 확인 가능
        username = user_info.get('login')
        
        # 이메일 확인 (비공개 이메일인 경우 추가 요청 필요할 수 있음)
        email_resp = oauth.github.get('user/emails')
        emails = email_resp.json()
        primary_email = next((e['email'] for e in emails if e['primary']), None)
        
        if username in ALLOWED_OAUTH_USERS or primary_email in ALLOWED_OAUTH_USERS:
            reset_login_attempts()
            session['authenticated'] = True
            session['username'] = username or primary_email
            session['oauth_provider'] = 'github'
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error=f"허가되지 않은 사용자입니다: {username or primary_email}")
    except Exception as e:
        print(f"GitHub Auth Error: {e}")
        return redirect(url_for('login'))

@app.route('/api/auth/status', methods=['GET'])
def api_auth_status():
    """인증 상태 및 로그인 시도 횟수 확인 API"""
    attempts = get_login_attempts()
    return jsonify({
        "authenticated": session.get('authenticated', False),
        "attempts": attempts,
        "locked": account_locked,
        "remaining": max(0, MAX_LOGIN_ATTEMPTS - attempts),
        "is_admin": is_admin() if session.get('authenticated') else False
    })

@app.route('/api/server/restart', methods=['POST'])
@admin_required
def api_restart_server():
    """서버 재시작 API (관리자만 접근 가능)"""
    try:
        success, message = restart_server()
        if success:
            # 재시작이 시작되면 잠시 후 응답 (서버가 종료되기 전에)
            return jsonify({
                "success": True,
                "message": message,
                "warning": "서버가 재시작됩니다. 몇 초 후 페이지를 새로고침하세요."
            })
        else:
            return jsonify({
                "success": False,
                "error": message
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 재시작 중 오류: {str(e)}"
        }), 500

@app.route('/api/server/status', methods=['GET'])
@login_required
def api_server_status():
    """서버 상태 확인 API"""
    port_in_use = is_port_in_use(SERVER_PORT)
    return jsonify({
        "port": SERVER_PORT,
        "port_in_use": port_in_use,
        "is_admin": is_admin()
    })

@app.route('/api/projects/<project_id>/server/status', methods=['GET'])
@login_required
def api_project_server_status(project_id):
    """프로젝트별 서버 상태 확인 API"""
    project_path = get_project_path(project_id)
    if not project_path:
        return jsonify({"error": "프로젝트를 찾을 수 없습니다."}), 404
    
    port = get_project_port(project_path)
    port_in_use = is_port_in_use(port) if port else False
    
    run_server_bat = os.path.join(project_path, 'run_server.bat')
    restart_server_bat = os.path.join(project_path, 'restart_server.bat')
    has_server = os.path.exists(run_server_bat) or os.path.exists(restart_server_bat)
    
    return jsonify({
        "project_id": project_id,
        "has_server": has_server,
        "port": port,
        "port_in_use": port_in_use,
        "is_admin": is_admin()
    })

@app.route('/api/projects/<project_id>/server/restart', methods=['POST'])
@admin_required
def api_restart_project_server(project_id):
    """프로젝트별 서버 재시작 API (관리자만 접근 가능)"""
    try:
        success, message = restart_project_server(project_id)
        if success:
            return jsonify({
                "success": True,
                "message": message,
                "warning": "서버가 재시작됩니다. 몇 초 후 상태를 확인하세요."
            })
        else:
            return jsonify({
                "success": False,
                "error": message
            }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"서버 재시작 중 오류: {str(e)}"
        }), 500

# --- API Endpoints ---
@app.route('/api/projects', methods=['GET'])
@login_required
def list_projects():
    """Returns the list of projects."""
    projects = get_projects()
    return jsonify(projects)

@app.route('/api/select-project', methods=['POST'])
@login_required
def select_project():
    """Saves the selected project ID to the session. projectId가 None이면 BASE_DIR 사용."""
    data = request.json
    project_id = data.get('projectId')
    
    # project_id가 None이면 BASE_DIR 사용 (프로젝트 선택 해제)
    if project_id is None:
        session['selected_project_id'] = None
        return jsonify({"message": "BASE_DIR에서 실행하도록 설정되었습니다."})
    
    # 유효한 project_id인지 확인
    if not get_project_path(project_id):
        return jsonify({"error": "Invalid project ID"}), 400
    
    session['selected_project_id'] = project_id
    return jsonify({"message": f"Project '{project_id}' selected."})

@app.route('/api/query', methods=['POST'])
@login_required
def handle_query():
    """
    Executes a CLI command in the specified project directory and returns the result.
    Saves the conversation to the history.
    """
    import uuid
    
    data = request.json
    project_id = data.get('projectId')  # None일 수 있음 (프로젝트 선택 안 함)
    cli_tool = data.get('cli')
    message = data.get('message')
    model = data.get('model') # Gemini 모델 버전
    session_id = data.get('sessionId')
    new_session = data.get('newSession', False)

    if not cli_tool or not message:
        return jsonify({"error": "Missing cli or message"}), 400

    # 프로젝트가 선택되지 않았으면 BASE_DIR에서 실행
    if not project_id:
        project_path = BASE_DIR
        project_id = "__root__"  # 데이터베이스 저장용 식별자
    else:
        project_path = get_project_path(project_id)
        if not project_path:
            return jsonify({"error": "Invalid or unauthorized project path"}), 400
    
    # 새 세션이면 새 sessionId 생성
    if new_session or not session_id:
        session_id = str(uuid.uuid4())

    # Determine the command based on the selected CLI tool
    # NOTE: These commands are examples. Adjust them if your CLI tools require different arguments.
    assistant_response = ""
    if cli_tool == 'echo':
        # Echo mode for testing without real CLI tools
        assistant_response = f"Echo: {message}"
    else:
        command_name = None
        if cli_tool == 'gemini':
            # @google/gemini-cli 패키지는 'gemini' 명령어로 설치됨
            command_name = 'gemini'
        elif cli_tool == 'claude':
            command_name = 'claude'
        else:
            return jsonify({"error": "Unsupported CLI tool"}), 400
        
        # Find the full path to the command
        command_path = find_command(command_name)
        if not command_path:
            error_msg = (
                f"Error: The command '{command_name}' was not found. "
                f"Make sure it is installed and in your system's PATH. "
                f"If installed via npm, ensure npm's global bin directory is in your PATH."
            )
            return jsonify({"error": error_msg}), 500
        
        # Build the command with the full path
        if cli_tool == 'gemini':
            # Example for Gemini: gemini --model gemini-1.5-flash prompt "your message"
            command = [command_path]
            if model:
                command.extend(["--model", model])
            command.extend(["prompt", message])
        elif cli_tool == 'claude':
            # Example for Claude: claude prompt "your message"
            command = [command_path, "prompt", message]
        
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
        except FileNotFoundError:
            error_msg = f"Error: The command '{command_path}' was not found. This should not happen if find_command() worked correctly."
            return jsonify({"error": error_msg}), 500
        except subprocess.CalledProcessError as e:
            error_msg = f"CLI command failed with exit code {e.returncode}:\n{e.stderr}"
            return jsonify({"error": error_msg}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Save to database (works for echo, gemini, claude)
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (projectId, sessionId, timestamp, cli, user_message, assistant_message)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (project_id, session_id, datetime.now(), cli_tool, message, assistant_response))
        conn.commit()
        conn.close()

        return jsonify({
            "assistant_message": assistant_response,
            "sessionId": session_id
        })
    except Exception as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Returns the chat history for a given project."""
    project_id = request.args.get('projectId')
    session_id = request.args.get('sessionId')
    
    if not project_id:
        return jsonify({"error": "projectId is required"}), 400

    # Security check is implicitly done by querying with projectId
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if session_id:
        # 특정 세션의 히스토리만 조회
        cursor.execute("SELECT * FROM history WHERE projectId = ? AND sessionId = ? ORDER BY timestamp ASC", 
                      (project_id, session_id))
    else:
        # 전체 히스토리 조회 (기존 동작)
        cursor.execute("SELECT * FROM history WHERE projectId = ? ORDER BY timestamp ASC", (project_id,))
    
    rows = cursor.fetchall()
    conn.close()

    history_list = [dict(row) for row in rows]
    return jsonify(history_list)

@app.route('/api/history/sessions', methods=['GET'])
@login_required
def get_history_sessions():
    """Returns a list of chat sessions for a given project."""
    project_id = request.args.get('projectId')
    
    # project_id가 없으면 "__root__" 사용 (BASE_DIR)
    if not project_id:
        project_id = "__root__"

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 각 세션의 첫 번째 메시지와 타임스탬프를 가져옴
    cursor.execute('''
        SELECT 
            sessionId,
            MIN(timestamp) as timestamp,
            MIN(id) as first_id
        FROM history 
        WHERE projectId = ? AND sessionId IS NOT NULL
        GROUP BY sessionId
        ORDER BY timestamp DESC
    ''', (project_id,))
    
    sessions = cursor.fetchall()
    
    # 각 세션의 첫 메시지 내용 가져오기
    session_list = []
    for session in sessions:
        cursor.execute('''
            SELECT user_message 
            FROM history 
            WHERE id = ?
        ''', (session['first_id'],))
        
        first_msg = cursor.fetchone()
        first_message = first_msg['user_message'] if first_msg else ''
        
        # 메시지가 너무 길면 잘라내기
        if len(first_message) > 100:
            first_message = first_message[:100] + '...'
        
        session_list.append({
            'sessionId': session['sessionId'],
            'timestamp': session['timestamp'],
            'firstMessage': first_message
        })
    
    conn.close()
    return jsonify(session_list)


# --- Frontend Routes ---

@app.route('/favicon.ico')
def favicon():
    """Handles the browser's request for a favicon, preventing 404 errors."""
    return '', 204

@app.route('/login')
def login():
    """로그인 페이지"""
    # 이미 로그인되어 있으면 메인 페이지로 리다이렉트
    if session.get('authenticated'):
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/')
@login_required
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# --- Main Execution ---
if __name__ == '__main__':
    init_db()
    # For development, debug=True is fine. For production, use a proper WSGI server.
    app.run(host='0.0.0.0', port=SERVER_PORT, debug=True)
