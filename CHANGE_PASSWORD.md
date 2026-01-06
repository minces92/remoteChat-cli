# 비밀번호 변경 방법

## 개요
이 시스템의 비밀번호는 `.env` 파일에 해시화되어 저장됩니다. 비밀번호를 변경하려면 다음 단계를 따르세요.

## 비밀번호 변경 절차

### 1. 새 비밀번호 해시 생성

터미널에서 다음 명령어를 실행하여 새 비밀번호의 해시를 생성합니다:

```bash
python generate_password_hash.py <새_비밀번호>
```

예시:
```bash
python generate_password_hash.py mynewpassword123
```

출력 예시:
```
비밀번호 해시:
$2b$12$rvu0j3iNbNc6GTj..jAcLO7ekOIFePjfkReGCOK8kbWyV3qGEpxsu

.env 파일에 다음과 같이 추가하세요:
ALLOWED_USERS=username:$2b$12$rvu0j3iNbNc6GTj..jAcLO7ekOIFePjfkReGCOK8kbWyV3qGEpxsu
```

### 2. 대화형 모드 사용 (권장)

사용자 이름과 비밀번호를 함께 입력할 수 있는 대화형 모드를 사용할 수도 있습니다:

```bash
python generate_password_hash.py
```

이 모드에서는:
1. 사용자 이름 입력
2. 비밀번호 입력
3. 생성된 해시와 `.env` 파일 설정 예시가 표시됩니다

### 3. .env 파일 수정

`.env` 파일을 열고 `ALLOWED_USERS` 항목을 수정합니다:

**기존 사용자의 비밀번호 변경:**
```
ALLOWED_USERS=admin:기존_해시,user:새로운_해시
```

**새 사용자 추가:**
```
ALLOWED_USERS=admin:해시1,user:해시2,newuser:해시3
```

**전체 예시:**
```
ALLOWED_USERS=admin:$2b$12$rvu0j3iNbNc6GTj..jAcLO7ekOIFePjfkReGCOK8kbWyV3qGEpxsu,user:$2b$12$RsoUrphubRBpP4CyT.YvYeIpmv7VWo1Cbecel9PyuUYj79fEGKWn6
```

### 4. 서버 재시작

`.env` 파일을 수정한 후에는 **반드시 서버를 재시작**해야 변경사항이 적용됩니다.

```bash
# 서버 중지 (Ctrl+C)
# 서버 재시작
python app.py
```

또는 `run_server.bat` 파일을 사용하는 경우:
- 서버를 중지하고 다시 실행

## 주의사항

1. **해시값 복사**: 해시값을 복사할 때 전체 문자열을 정확히 복사해야 합니다. `$` 기호가 포함되어 있으므로 주의하세요.

2. **서버 재시작 필수**: `.env` 파일을 수정한 후에는 반드시 서버를 재시작해야 합니다. 서버가 실행 중일 때는 변경사항이 적용되지 않습니다.

3. **백업**: 비밀번호를 변경하기 전에 `.env` 파일의 백업을 만드는 것을 권장합니다.

4. **보안**: `.env` 파일은 절대 공유하거나 버전 관리 시스템에 커밋하지 마세요. (이미 `.gitignore`에 포함되어 있습니다)

## 문제 해결

### 해시가 작동하지 않는 경우
- 해시값이 정확히 복사되었는지 확인
- `.env` 파일의 형식이 올바른지 확인 (콜론(:)과 쉼표(,) 사용)
- 서버를 재시작했는지 확인

### 여러 사용자 관리
여러 사용자의 비밀번호를 한 번에 변경하려면:
1. 각 사용자의 새 비밀번호 해시를 생성
2. 쉼표(,)로 구분하여 모두 나열
3. `.env` 파일에 저장
4. 서버 재시작

## 예시: admin 사용자 비밀번호 변경

```bash
# 1. 새 비밀번호 해시 생성
python generate_password_hash.py newadminpass

# 출력:
# 비밀번호 해시:
# $2b$12$새로운해시값...

# 2. .env 파일 수정
# ALLOWED_USERS=admin:$2b$12$새로운해시값...,user:$2b$12$기존해시값...

# 3. 서버 재시작
```


