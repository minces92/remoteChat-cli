#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
비밀번호 해시 생성 유틸리티
사용법: python generate_password_hash.py <password>
또는 대화형 모드: python generate_password_hash.py
"""

import bcrypt
import sys

def hash_password(password):
    """비밀번호를 bcrypt로 해시화합니다."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def main():
    if len(sys.argv) > 1:
        # 명령줄 인자로 비밀번호 제공
        password = sys.argv[1]
        hashed = hash_password(password)
        print(f"\n비밀번호 해시:")
        print(f"{hashed}\n")
        print(f".env 파일에 다음과 같이 추가하세요:")
        print(f"ALLOWED_USERS=username:{hashed}\n")
    else:
        # 대화형 모드
        print("=" * 50)
        print("비밀번호 해시 생성 유틸리티")
        print("=" * 50)
        
        username = input("\n사용자 이름을 입력하세요: ").strip()
        if not username:
            print("사용자 이름이 필요합니다.")
            return
        
        password = input("비밀번호를 입력하세요: ").strip()
        if not password:
            print("비밀번호가 필요합니다.")
            return
        
        hashed = hash_password(password)
        
        print("\n" + "=" * 50)
        print("생성된 해시:")
        print("=" * 50)
        print(f"\n{hashed}\n")
        print("=" * 50)
        print(".env 파일 설정 예시:")
        print("=" * 50)
        print(f"\nALLOWED_USERS={username}:{hashed}\n")
        print("또는 여러 사용자를 추가하려면:")
        print(f"ALLOWED_USERS={username}:{hashed},username2:hashed_password2\n")

if __name__ == '__main__':
    main()

