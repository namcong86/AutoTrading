import ccxt
import requests
import telegram_alert
import time
import pyupbit
import myUpbit   #우리가 만든 함수들이 들어있는 모듈
from datetime import datetime

#업비트 키
Upbit_AccessKey = "AYneBweCn6FFMeWtTO0Cxq0XJxU7rCZ6WpzUsvNk"
Upbit_ScretKey = "BV0gy2txNyF9Brv594YXxcRYs3EQZe9TaWMtN14Z"

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)

# Binance API 인증 정보
Binance_api_key = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_api_secret = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"

# OKX API 인증 정보
OKX_api_key = "16de0caf-ae2c-46cb-9109-764687da4441"
OKX_api_secret = "B5444AB8DA31B45411069CFB3CB764A0"
OKX_passphrase = "Dmz52425!"

# Bybit API 인증 정보  
Bybit_api_key = "31CXXwbnMdY8z6Jpsa"
Bybit_api_secret = "oKIcjUl60b629L5jMFGTQoysR9jZc3wQPvWh"

# 비트겟 API 키, 비밀 키, 패스프레이즈 입력
Bitget_api_key = 'bg_d889b4731194d8ee2c0ad6f4f282bb51'
Bitget_api_secret = 'dd16406741024149b9767a6c973d9f170761abfe8433da5e867cc3d55eb42b15'
Bitget_api_passphrase = 'namcong86'  # 패스프레이즈

# Binance_ccxt 객체 생성
Binance_exchange = ccxt.binance({
    "apiKey": Binance_api_key,
    "secret": Binance_api_secret,
    "enableRateLimit": True,  # API 호출 속도 제한 준수
})

# OKX_ccxt 객체 생성
OKX_exchange = ccxt.okx({
    "apiKey": OKX_api_key,
    "secret": OKX_api_secret,
    "password": OKX_passphrase,
    "enableRateLimit": True,  # API 호출 속도 제한 준수 
})

# Bybit_ccxt 객체 생성
Bybit_exchange = ccxt.bybit({
    "apiKey": Bybit_api_key,
    "secret": Bybit_api_secret,
    "enableRateLimit": True,  # API 호출 속도 제한 준수
})

# 비트겟 인스턴스 생성
Bitget_exchange = ccxt.bitget({
    'apiKey': Bitget_api_key,
    'secret': Bitget_api_secret,
    'password': Bitget_api_passphrase,  # 패스프레이즈 필수
})

# 전체 자산(Equity) 조회 함수
def get_binance_total_equity():
    try:
        
        # 선물 잔액 가져오기 (Futures)
        futures_balance = Binance_exchange.fetch_balance({'type': 'future'})

        # 선물 자산 (USDT 기준)
        total_futures_balance = futures_balance['total'].get('USDT', 0)

        # 선물의 미실현 수익 포함 (미실현 수익이 equity에 포함됨)
        total_equity = total_futures_balance

        return round(total_equity, 2)  # 소수점 2자리까지 반올림
    except Exception as e:
        print(f"Error: {e}")
        return None

# 전체 자산(Equity) 조회 함수
def get_okx_total_equity():
    try:
        
        # 선물 잔액 가져오기 (Futures)
        futures_balance = OKX_exchange.fetch_balance({'type': 'future'})

        # 선물 자산 (USDT 기준)
        total_futures_balance = futures_balance['total'].get('USDT', 0)
    
        # 선물의 미실현 수익 포함 (미실현 수익이 equity에 포함됨)
        total_equity = total_futures_balance

        return round(total_equity, 2)  # 소수점 2자리까지 반올림
    except Exception as e:
        print(f"Error: {e}")
        return None
    

# 총 자산(Equity) 조회 함수
def get_bybit_total_equity():
    try:
        
        # 선물 잔액 가져오기 (Futures)
        futures_balance = Bybit_exchange.fetch_balance({'type': 'future'})

        # 선물 자산 (USDT 기준)
        total_futures_balance = futures_balance['total'].get('USDT', 0)

        # 선물 미실현 수익 가져오기 (unrealized profit)
        futures_positions = Bybit_exchange.fetch_positions()  # 선물 포지션 조회
        unrealized_profit = 0
        
        # 모든 선물 포지션에서 미실현 수익 합산
        for position in futures_positions:
            unrealized_profit += float(position['unrealizedPnl'])  # 미실현 수익 합산

        # 선물의 미실현 수익 포함 (미실현 수익이 equity에 포함됨)
        total_equity = total_futures_balance + unrealized_profit

        return round(total_equity, 2)  # 소수점 2자리까지 반올림
    except Exception as e:
        print(f"Error: {e}")
        return None
    

# 잔액 조회 함수 (현물 및 선물 마켓 합산)
def get_bitget_total_balance():
    try:
        # 현물 잔액 가져오기
        spot_balance = Bitget_exchange.fetch_balance({'type': 'spot'})
        # 선물 잔액 가져오기
        futures_balance = Bitget_exchange.fetch_balance({'type': 'future'})
        
        # 현물 마켓의 총 잔액 (USDT 기준)
        total_spot_balance = sum(amount for currency, amount in spot_balance['total'].items() if currency == 'USDT')
        
        # 선물 마켓의 총 잔액 (USDT 기준)
        total_futures_balance = sum(amount for currency, amount in futures_balance['total'].items() if currency == 'USDT')

        # 현물과 선물 잔액 합산
        total_balance = total_spot_balance + total_futures_balance

        return round(total_balance, 2)  # 소수점 2자리까지 반올림
    except Exception as e:
        print(f"Error: {e}")
        return None
    

def get_exchange_rate():
    base_currency = "USD"  # 기준 통화
    target_currency = "KRW"  # 대상 통화
    url = f"https://open.er-api.com/v6/latest/{base_currency}"  # API 엔드포인트
    try:
        response = requests.get(url, timeout=10)  # 10초 제한
        response.raise_for_status()  # HTTP 에러 확인
        data = response.json()

        if data.get("result") == "success":
            rate = data["rates"].get(target_currency)
            if rate:
                rounded_rate = round(rate)  # 소수점 첫째 자리에서 반올림하여 정수로 변환
                return rounded_rate
            else:
                print(f"Error: '{target_currency}' 통화가 응답 데이터에 없습니다.")
        else:
            print(f"API Error: {data.get('error-type', 'Unknown error')}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rate: {e}")



binance_JAN = get_binance_total_equity()
time.sleep(1)
okx_JAN = get_okx_total_equity()
time.sleep(1)
bybit_JAN = get_bybit_total_equity()
time.sleep(1)
bitget_JAN = get_bitget_total_balance()
time.sleep(1)

balances = upbit.get_balances()
TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

time.sleep(1)

total_JAN = round((binance_JAN + okx_JAN + bybit_JAN + bitget_JAN) * get_exchange_rate()) + round(TotalRealMoney) 

# 현재 날짜와 시간 구하기
now = datetime.now()


print(f"선물: {round((binance_JAN + okx_JAN + bybit_JAN + bitget_JAN) * get_exchange_rate())}")
print(f"현물: {round(TotalRealMoney)}")
print(f"TOTAL잔액: {total_JAN}")
telegram_alert.SendMessage(f"{now.strftime('%Y-%m-%d %H:%M')} 총금액=> {total_JAN:,} 원")
