# Stock Common 폴더

이 폴더는 Real과 Test 폴더에서 공통으로 사용하는 모듈들을 포함합니다.

## 포함된 파일들

- **KIS_API_Helper_KR.py**: 한국투자증권 한국 주식 API 헬퍼 함수
- **KIS_API_Helper_US.py**: 한국투자증권 미국 주식 API 헬퍼 함수
- **KIS_Common.py**: 공통 유틸리티 함수 및 설정
- **myStockInfo.yaml**: API 키 및 계좌 정보 설정 파일
- **telegram_alert.py**: 텔레그램 알림 기능

## 사용 방법

Real 또는 Test 폴더의 스크립트에서 다음과 같이 import 합니다:

```python
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Common'))

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import KIS_API_Helper_US as KisUS
import telegram_alert
```

## 주의사항

- `myStockInfo.yaml` 파일에 실제 API 키와 계좌 정보를 입력해야 합니다.
- 이 파일들은 Real과 Test에서 공유되므로 수정 시 주의가 필요합니다.
