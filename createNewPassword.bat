@echo off
chcp 65001 >nul

rem 새 비밀번호 입력 받기
set /p "NEW_PW=새 비밀번호를 입력하세요: "

rem 입력값이 비어있는지 체크
if "%NEW_PW%"=="" (
    echo 비밀번호가 입력되지 않았습니다.
    pause
    exit /b 1
)

rem 파이썬 스크립트 실행
python generate_password_hash.py "%NEW_PW%"

pause
