# OAuth 설정 가이드 (Google & GitHub)

Remote Chat CLI 서버에서 Google 및 GitHub 원클릭 로그인을 사용하기 위한 설정 방법입니다.

## 1. Google OAuth 설정

1. [Google Cloud Console](https://console.cloud.google.com/)에 접속합니다.
2. 새 프로젝트를 생성하거나 기존 프로젝트를 선택합니다.
3. **API 및 서비스 > 사용자 인증 정보**로 이동합니다.
4. **사용자 인증 정보 만들기 > OAuth 클라이언트 ID**를 선택합니다.
5. 애플리케이션 유형을 **웹 애플리케이션**으로 선택합니다.
6. **승인된 리디렉션 URI**에 다음을 추가합니다:
   - `http://localhost:5000/auth/google/callback` (로컬 테스트용)
   - 실제 서버 주소를 사용하는 경우: `http://your-domain.com/auth/google/callback`
7. 생성된 **클라이언트 ID**와 **클라이언트 보안 비밀번호**를 복사하여 `.env` 파일에 저장합니다.

## 2. GitHub OAuth 설정

1. GitHub에 로그인하고 **Settings > Developer settings > OAuth Apps**로 이동합니다.
2. **New OAuth App**을 클릭합니다.
3. **Homepage URL**에 서버 주소를 입력합니다 (예: `http://localhost:5000`).
4. **Authorization callback URL**에 다음을 추가합니다:
   - `http://localhost:5000/auth/github/callback`
5. **Register application**을 클릭합니다.
6. 생성된 **Client ID**와 **Client Secret**을 복사하여 `.env` 파일에 저장합니다.

## 3. .env 파일 설정

`.env` 파일에 다음과 같이 정보를 입력합니다:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret

# OAuth 허용 사용자 목록 (이메일 또는 GitHub 아이디)
ALLOWED_OAUTH_USERS=user@gmail.com,github_username
```

## 4. 서버 재시작

설정을 마친 후 서버를 재시작하면 로그인 페이지에 Google 및 GitHub 로그인 버튼이 나타납니다.
허가된 사용자 목록(`ALLOWED_OAUTH_USERS`)에 포함된 계정으로만 로그인이 가능합니다.
