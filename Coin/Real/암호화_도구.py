#-*-coding:utf-8 -*-
'''
Upbit API 키 암호화 도구

사용법:
1. 아래 access_key와 secret_key에 새로 발급받은 API 키를 입력하세요
2. 이 파일을 실행하면 암호화된 키가 출력됩니다
3. 출력된 암호화 키를 my_key.py의 upbit_access, upbit_secret에 복사하세요
'''

from cryptography.fernet import Fernet
import ende_key

# ============================================
# 여기에 새로 발급받은 Upbit API 키를 입력하세요
# ============================================
access_key = "EYNqzB1k2echWMLnmUSZWf1O03U8fiPUMQX9OHL83eeWGotYgoq1dJaDQYleh8Wa"
secret_key = "PW2cxdCPGSJXMhiEgT2aABt0NikxOntPVOzMxgAYkWe4DxSU1xIzPJgZfnujf28h"

# ============================================
# 암호화 실행
# ============================================
cipher_suite = Fernet(ende_key.ende_key)

# Access Key 암호화
encrypted_access = cipher_suite.encrypt(access_key.encode())
print("="*80)
print("암호화된 Access Key:")
print(encrypted_access.decode())
print()

# Secret Key 암호화
encrypted_secret = cipher_suite.encrypt(secret_key.encode())
print("암호화된 Secret Key:")
print(encrypted_secret.decode())
print("="*80)

print("\n위의 암호화된 키들을 복사해서 my_key.py 파일의")
print("upbit_access = \"...\"")
print("upbit_secret = \"...\"")
print("에 각각 넣어주시면 됩니다!")
