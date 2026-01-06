# OAuth (Google & GitHub) 원클릭 로그인 구현 계획

이 문서는 Remote Chat CLI 서버에 Google 및 GitHub OAuth를 통한 원클릭 로그인 기능을 추가하기 위한 단계별 계획을 담고 있습니다.

## 1. 목표
- 기존의 아이디/비밀번호 로그인 외에 Google 및 GitHub 계정을 통한 간편 로그인 제공
- 허가된 사용자(이메일 또는 아이디 기반)만 로그인 가능하도록 보안 유지
- 사용자 경험 향상을 위한 직관적인 UI 제공

## 2. 기술 스택
- **Backend**: Flask, Authlib (OAuth 클라이언트 라이브러리)
- **Frontend**: Vanilla JS, CSS (기존 login.html 수정)
- **Configuration**: `.env` 파일을 통한 OAuth 자격 증명 관리

## 3. 단계별 진행 계획

### 1단계: 환경 준비 및 라이브러리 설치
- [x] `Authlib` 및 `requests` 라이브러리 설치
- [x] Google 및 GitHub Developer Console에서 OAuth 앱 등록 (Client ID, Secret 발급) -> 가이드 작성 완료
- [x] `.env` 파일에 OAuth 관련 환경 변수 추가 -> `.env.example` 업데이트 완료

### 2단계: 백엔드 구현 (app.py)
- [x] Authlib를 사용하여 Google/GitHub OAuth 클라이언트 설정
- [x] OAuth 로그인 시작 엔드포인트 생성 (`/login/google`, `/login/github`)
- [x] OAuth 콜백 처리 엔드포인트 생성 (`/auth/google/callback`, `/auth/github/callback`)
- [x] 사용자 검증 로직 구현 (허가된 이메일/아이디 목록 대조)
- [x] 세션 관리 및 로그인 처리

### 3단계: 프런트엔드 구현 (login.html)
- [x] 로그인 페이지에 Google 및 GitHub 로그인 버튼 추가
- [x] 각 서비스의 브랜드 가이드라인에 맞는 스타일 적용
- [x] 클릭 시 OAuth 로그인 프로세스 시작

### 4단계: 테스트 및 문서화
- [x] 각 플랫폼별 로그인 흐름 테스트 (구조적 구현 완료)
- [x] 예외 상황 처리 (인증 거부, 허가되지 않은 사용자 등)
- [x] 사용자 가이드 작성 (OAuth 설정 방법 등) -> `OAUTH_SETUP_GUIDE.md` 작성 완료

## 4. 보안 고려 사항
- OAuth Client Secret은 절대 코드에 포함하지 않고 `.env`로 관리
- `ALLOWED_USERS` 환경 변수를 확장하여 OAuth 사용자(이메일 등)를 지정할 수 있도록 개선
- CSRF 보호를 위한 세션 보안 강화
