# 보안 개선 투두리스트

이 문서는 `SECURITY_AUDIT.md`에서 식별된 보안 취약점을 해결하기 위한 작업 목록입니다.

## 🔴 높은 우선순위 (즉시 개선 필요)

### ✅ 1. 하드코딩된 비밀번호 제거
- [x] `load_allowed_users()` 함수에서 하드코딩된 계정 제거
- [x] .env 파일 필수로 변경
- [x] .env 파일이 없을 때 경고 메시지 출력
- **상태**: 완료
- **파일**: `app.py`

### 2. 세션 키를 환경 변수로 관리
- [ ] `.env.example`에 `SECRET_KEY` 추가
- [ ] `app.py`에서 환경 변수에서 SECRET_KEY 로드
- [ ] 고정된 키 생성 스크립트 제공 (선택사항)
- [ ] 문서화
- **예상 작업 시간**: 30분
- **파일**: `app.py`, `.env.example`

```python
# 구현 예시
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    print("WARNING: SECRET_KEY not set. Generating random key (sessions will be invalidated on restart).")
    SECRET_KEY = os.urandom(24).hex()
app.secret_key = SECRET_KEY
```

### 3. 계정별 잠금 메커니즘 구현
- [ ] 데이터베이스에 `account_locks` 테이블 생성
- [ ] 계정별 잠금 상태 저장
- [ ] 시간 기반 자동 해제 (예: 30분 후)
- [ ] `increment_login_attempts()` 함수 수정
- [ ] `is_account_locked()` 함수 수정
- [ ] 잠금 해제 API 엔드포인트 추가 (관리자용)
- **예상 작업 시간**: 2-3시간
- **파일**: `app.py`

```sql
CREATE TABLE account_locks (
    username TEXT PRIMARY KEY,
    locked_until DATETIME,
    attempt_count INTEGER DEFAULT 0,
    last_attempt DATETIME
)
```

### 4. 로그인 시도 추적을 데이터베이스로 이동
- [ ] 데이터베이스에 `login_attempts` 테이블 생성
- [ ] IP 주소와 사용자명 모두 추적
- [ ] 영구 저장으로 변경
- [ ] 서버 재시작 후에도 유지
- [ ] 오래된 시도 기록 정리 (예: 24시간 이상)
- **예상 작업 시간**: 2-3시간
- **파일**: `app.py`

```sql
CREATE TABLE login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    ip_address TEXT,
    timestamp DATETIME NOT NULL,
    success INTEGER DEFAULT 0
)
```

### 5. 입력 검증 강화
- [ ] 메시지 길이 제한 (예: 최대 10000자)
- [ ] 사용자명 길이 및 형식 검증
- [ ] 프로젝트 ID 검증 강화
- [ ] SQL Injection 방어 재확인
- [ ] XSS 방어를 위한 입력 sanitization
- **예상 작업 시간**: 2-3시간
- **파일**: `app.py`

```python
# 구현 예시
MAX_MESSAGE_LENGTH = 10000
MAX_USERNAME_LENGTH = 50

def validate_message(message):
    if len(message) > MAX_MESSAGE_LENGTH:
        return False, f"Message too long (max {MAX_MESSAGE_LENGTH} characters)"
    # 추가 검증...
    return True, None
```

## 🟡 중간 우선순위 (단기 개선)

### 6. HTTPS 설정
- [ ] SSL/TLS 인증서 획득
- [ ] Flask 애플리케이션에 SSL 설정 추가
- [ ] HTTP에서 HTTPS로 리다이렉트
- [ ] 문서화
- **예상 작업 시간**: 1-2시간
- **참고**: 프로덕션 환경에서만 필요

### 7. CORS 정책 설정
- [ ] Flask-CORS 라이브러리 추가
- [ ] 허용된 도메인 설정
- [ ] 개발/프로덕션 환경별 설정
- **예상 작업 시간**: 30분
- **파일**: `app.py`, `requirements.txt`

### 8. 에러 메시지 일반화
- [ ] 프로덕션/개발 환경 구분
- [ ] 프로덕션에서 상세 에러 메시지 숨김
- [ ] 로그 파일에만 상세 정보 기록
- **예상 작업 시간**: 1-2시간
- **파일**: `app.py`

```python
# 구현 예시
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

def get_error_message(error, detail):
    if DEBUG_MODE:
        return f"{error}: {detail}"
    return error  # 일반적인 메시지만 반환
```

### 9. 세션 타임아웃 구현
- [ ] 세션 만료 시간 설정 (예: 30분)
- [ ] 비활성 시간 추적
- [ ] 자동 로그아웃 기능
- [ ] 프론트엔드에 세션 만료 경고
- **예상 작업 시간**: 2-3시간
- **파일**: `app.py`, `templates/index.html`

### 10. Rate Limiting 추가
- [ ] Flask-Limiter 라이브러리 추가
- [ ] API 엔드포인트별 제한 설정
- [ ] 로그인 시도 제한 강화
- [ ] IP 기반 제한
- **예상 작업 시간**: 1-2시간
- **파일**: `app.py`, `requirements.txt`

```python
# 구현 예시
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/query', methods=['POST'])
@limiter.limit("10 per minute")
@login_required
def handle_query():
    # ...
```

## 🟢 낮은 우선순위 (장기 개선)

### 11. 보안 로깅 시스템
- [ ] 로그인 실패 기록
- [ ] 의심스러운 활동 모니터링
- [ ] 로그 파일 관리
- [ ] 로그 분석 도구 통합
- **예상 작업 시간**: 3-4시간
- **파일**: `app.py`, 새 로깅 모듈

### 12. 비밀번호 정책 구현
- [ ] 최소 길이 요구사항 (예: 8자)
- [ ] 복잡도 검증 (대소문자, 숫자, 특수문자)
- [ ] `generate_password_hash.py`에 검증 추가
- [ ] 문서화
- **예상 작업 시간**: 1-2시간
- **파일**: `generate_password_hash.py`, `app.py`

### 13. Content Security Policy (CSP) 헤더
- [ ] CSP 헤더 설정
- [ ] XSS 공격 방어
- [ ] 테스트 및 검증
- **예상 작업 시간**: 1-2시간
- **파일**: `app.py`

### 14. 2단계 인증 (2FA) 지원
- [ ] TOTP 라이브러리 추가
- [ ] QR 코드 생성
- [ ] 인증 코드 검증
- [ ] 사용자 설정 UI
- **예상 작업 시간**: 5-8시간
- **파일**: 여러 파일

### 15. 비밀번호 변경 히스토리
- [ ] 이전 비밀번호 해시 저장
- [ ] 재사용 방지 검증
- [ ] 비밀번호 변경 API 개선
- **예상 작업 시간**: 2-3시간
- **파일**: `app.py`

## 📊 진행 상황 추적

### 완료된 항목
- ✅ 하드코딩된 비밀번호 제거

### 진행 중인 항목
- 없음

### 대기 중인 항목
- 모든 높은 우선순위 항목 (2-5)
- 모든 중간 우선순위 항목 (6-10)
- 모든 낮은 우선순위 항목 (11-15)

## 📝 작업 시 주의사항

1. **테스트**: 각 보안 개선 사항을 구현한 후 충분한 테스트 수행
2. **문서화**: 변경사항을 문서에 반영
3. **백업**: 데이터베이스 스키마 변경 전 백업
4. **단계적 배포**: 한 번에 하나씩 구현하고 테스트
5. **보안 감사**: 주요 변경 후 보안 감사 재실시

## 🔄 정기 검토

이 투두리스트는 다음 시점에 검토해야 합니다:
- 주요 보안 개선 완료 시
- 새로운 취약점 발견 시
- 3개월마다 정기 검토

---

**마지막 업데이트**: 2024년
**다음 검토 예정일**: 3개월 후

