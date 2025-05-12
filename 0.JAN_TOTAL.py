import ccxt
import requests
import telegram_alert
import time
import pyupbit
import myUpbit  # 우리가 만든 함수들이 들어있는 모듈
from datetime import datetime

# 업비트 키
Upbit_AccessKey = "AYneBweCn6FFMeWtTO0Cxq0XJxU7rCZ6WpzUsvNk"
Upbit_ScretKey = "BV0gy2txNyF9Brv594YXxcRYs3EQZe9TaWMtN14Z"

# 업비트 객체를 만든다
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
Bitget_api_passphrase = 'namcong86'

# MEXC API 인증 정보
MEXC_api_key = "mx0vglCI5rwMRRjnJK"
MEXC_api_secret = "0668415a7f3948a4ae39497a2ab6b39e"

# Binance_ccxt 객체 생성
Binance_exchange = ccxt.binance({
    "apiKey": Binance_api_key,
    "secret": Binance_api_secret,
    "enableRateLimit": True,
})

# OKX_ccxt 객체 생성
OKX_exchange = ccxt.okx({
    "apiKey": OKX_api_key,
    "secret": OKX_api_secret,
    "password": OKX_passphrase,
    "enableRateLimit": True,
})

# Bybit_ccxt 객체 생성
Bybit_exchange = ccxt.bybit({
    "apiKey": Bybit_api_key,
    "secret": Bybit_api_secret,
    "enableRateLimit": True,
})

# 비트겟 인스턴스 생성
Bitget_exchange = ccxt.bitget({
    'apiKey': Bitget_api_key,
    'secret': Bitget_api_secret,
    'password': Bitget_api_passphrase,
})

# MEXC_ccxt 객체 생성
MEXC_exchange = ccxt.mexc({
    "apiKey": MEXC_api_key,
    "secret": MEXC_api_secret,
    "enableRateLimit": True,
})

# 거래소별 현물 잔액 조회 함수
def get_spot_balance(exchange, name):
    try:
        print(f"Fetching {name} spot balance...")
        
        # 거래소별 특화된 현물 잔액 조회 방식
        if name == "Binance":
            balance = exchange.fetch_balance(params={"type": "spot"})
        elif name == "OKX":
            balance = exchange.fetch_balance(params={"type": "spot"})
        elif name == "Bybit":
            # Bybit UNIFIED 계정 정보 조회 방식 적용
            print(f"\nUNIFIED 계정 정보 조회 시도...")
            account_info = exchange.privateGetV5AccountWalletBalance(params={"accountType": "UNIFIED"})
            print(f"응답 키: {list(account_info.keys()) if isinstance(account_info, dict) else type(account_info)}")
            
            total_in_usdt = 0
            
            if 'result' in account_info and 'list' in account_info['result']:
                for wallet in account_info['result']['list']:
                    print(f"지갑 정보: {wallet}")
                    if 'totalWalletBalance' in wallet:
                        total_wallet_balance = float(wallet.get('totalWalletBalance', '0'))
                        print(f"totalWalletBalance: {total_wallet_balance}")
                        total_in_usdt = total_wallet_balance
                        
                        # 개별 코인 정보 출력 (옵션)
                        if 'coin' in wallet and isinstance(wallet['coin'], list):
                            for coin in wallet['coin']:
                                if float(coin.get('free', 0)) > 0:
                                    print(f"{coin.get('coin', '')}: {float(coin.get('free', 0))}")
                                    
            return total_in_usdt
            
        elif name == "Bitget":
            balance = exchange.fetch_balance(params={"type": "spot"})
        elif name == "MEXC":
            balance = exchange.fetch_balance(params={"type": "spot"})
        else:
            balance = exchange.fetch_balance()
        
        # 디버깅을 위한 출력
        print(f"{name} balance response: {balance.keys()}")
        
        # Bybit는 위에서 이미 처리했으므로 skip
        if name == "Bybit":
            return 0
            
        # USDT 잔액 확인
        usdt_balance = balance.get('total', {}).get('USDT', 0)
        print(f"{name} USDT balance: {usdt_balance}")
        
        # 모든 코인의 USDT 환산 총액 계산 (선택 사항)
        total_in_usdt = usdt_balance
        for currency, amount in balance.get('total', {}).items():
            if currency != 'USDT' and amount > 0:
                try:
                    # 해당 코인의 티커 정보 가져오기
                    ticker = f"{currency}/USDT"
                    ticker_price = exchange.fetch_ticker(ticker)
                    coin_in_usdt = amount * ticker_price['last']
                    total_in_usdt += coin_in_usdt
                    print(f"{name} {currency}: {amount} (≈ {coin_in_usdt:.2f} USDT)")
                except Exception as e:
                    print(f"Cannot convert {currency} to USDT: {e}")
        
        return round(total_in_usdt, 2)
    except Exception as e:
        print(f"{name} Spot Balance Error: {str(e)}")
        return 0

# 거래소별 선물 잔액 조회 함수
def get_futures_balance(exchange, name):
    try:
        print(f"Fetching {name} futures balance...")
        
        # Bybit는 이미 UNIFIED 계정에서 모든 잔액을 가져왔으므로 스킵
        if name == "Bybit":
            return 0
            
        # 거래소별 특화된 선물 잔액 조회 방식
        if name == "Binance":
            balance = exchange.fetch_balance(params={"type": "future"})
        elif name == "OKX":
            balance = exchange.fetch_balance(params={"type": "future"})
        elif name == "Bitget":
            balance = exchange.fetch_balance(params={"type": "future"})
        elif name == "MEXC":
            balance = exchange.fetch_balance(params={"type": "future"})
        else:
            return 0
        
        # 디버깅을 위한 출력
        print(f"{name} futures balance response: {balance.keys()}")
        
        # USDT 잔액 확인
        usdt_balance = balance.get('total', {}).get('USDT', 0)
        print(f"{name} futures USDT balance: {usdt_balance}")
        
        return round(usdt_balance, 2)
    except Exception as e:
        print(f"{name} Futures Balance Error: {str(e)}")
        return 0

# 거래소별 미실현 수익 조회 함수
def get_unrealized_pnl(exchange, name):
    try:
        print(f"Fetching {name} unrealized PnL...")
        
        # Bybit는 이미 UNIFIED 계정에서 모든 정보를 가져왔으므로 스킵
        if name == "Bybit":
            return 0
            
        # 거래소별 특화된 포지션 조회 방식
        if name in ["Binance", "OKX", "Bitget", "MEXC"]:
            positions = exchange.fetch_positions()
            unrealized_pnl = sum(float(position.get('unrealizedPnl', 0)) for position in positions)
            print(f"{name} unrealized PnL: {unrealized_pnl}")
            return round(unrealized_pnl, 2)
        else:
            return 0
    except Exception as e:
        print(f"{name} PnL Error: {str(e)}")
        return 0

# 전체 거래소 잔액 조회 함수
def get_exchange_total_balance(exchange, name):
    # 각 부분 따로 조회하여 디버깅 용이하게
    spot_balance = get_spot_balance(exchange, name)
    time.sleep(1)  # API 레이트 리밋 방지
    
    futures_balance = get_futures_balance(exchange, name)
    time.sleep(1)  # API 레이트 리밋 방지
    
    # 총 자산 = 현물 잔액 + 선물 잔액
    total_balance = spot_balance + futures_balance
    print(f"{name} Total Balance: {total_balance} USDT")
    print("-" * 50)
    return total_balance

# 환율 조회 함수
def get_exchange_rate():
    base_currency = "USD"
    target_currency = "KRW"
    url = f"https://open.er-api.com/v6/latest/{base_currency}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            rate = data["rates"].get(target_currency)
            if rate:
                return round(rate)
            else:
                print(f"Error: '{target_currency}' 통화가 응답 데이터에 없습니다.")
                return 1200  # 기본값 설정
        else:
            print(f"API Error: {data.get('error-type', 'Unknown error')}")
            return 1200  # 기본값 설정
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rate: {e}")
        return 1200  # 에러 발생 시 기본값 설정

print("===== 자산 조회 시작 =====")

# API 키가 설정되었는지 확인
if not Binance_api_key or not Binance_api_secret:
    print("바이낸스 API 키가 설정되지 않았습니다.")
if not OKX_api_key or not OKX_api_secret or not OKX_passphrase:
    print("OKX API 키가 설정되지 않았습니다.")
if not Bybit_api_key or not Bybit_api_secret:
    print("Bybit API 키가 설정되지 않았습니다.")
if not Bitget_api_key or not Bitget_api_secret or not Bitget_api_passphrase:
    print("Bitget API 키가 설정되지 않았습니다.")
if not MEXC_api_key or not MEXC_api_secret:
    print("MEXC API 키가 설정되지 않았습니다.")
if not Upbit_AccessKey or not Upbit_ScretKey:
    print("업비트 API 키가 설정되지 않았습니다.")

# 자산 조회
binance_balance = get_exchange_total_balance(Binance_exchange, "Binance")
time.sleep(2)
okx_balance = get_exchange_total_balance(OKX_exchange, "OKX")
time.sleep(2)
bybit_balance = get_exchange_total_balance(Bybit_exchange, "Bybit")
time.sleep(2)
bitget_balance = get_exchange_total_balance(Bitget_exchange, "Bitget")
time.sleep(2)
mexc_balance = get_exchange_total_balance(MEXC_exchange, "MEXC")
time.sleep(2)

# 업비트 현물 자산
try:
    print("Fetching Upbit balance...")
    balances = upbit.get_balances()
    TotalRealMoney = myUpbit.GetTotalRealMoney(balances)  # 총 평가금액
    print(f"Upbit Total: {TotalRealMoney} KRW")
except Exception as e:
    print(f"Upbit Error: {e}")
    TotalRealMoney = 0

time.sleep(1)

# 환율 조회
exchange_rate = get_exchange_rate()
print(f"Exchange Rate (USD to KRW): {exchange_rate}")

# 총 자산 계산 (모든 거래소 현물 + 선물 + 업비트 현물)
print("\n===== 최종 결과 =====")
print(f"Binance Balance: {round(binance_balance)} USDT (≈ {round(binance_balance * exchange_rate):,} KRW)")
print(f"OKX Balance: {round(okx_balance)} USDT (≈ {round(okx_balance * exchange_rate):,} KRW)")
print(f"Bybit Balance: {round(bybit_balance)} USDT (≈ {round(bybit_balance * exchange_rate):,} KRW)")
print(f"Bitget Balance: {round(bitget_balance)} USDT (≈ {round(bitget_balance * exchange_rate):,} KRW)")
print(f"MEXC Balance: {round(mexc_balance)} USDT (≈ {round(mexc_balance * exchange_rate):,} KRW)")

exchange_total = binance_balance + okx_balance + bybit_balance + bitget_balance + mexc_balance
total_JAN = round(exchange_total * exchange_rate) + round(TotalRealMoney)

# 현재 날짜와 시간 구하기
now = datetime.now()

# 출력 및 텔레그램 알림
print(f"\n선물+현물(해외거래소): {round(exchange_total * exchange_rate):,} KRW")
print(f"현물(업비트): {round(TotalRealMoney):,} KRW")
print(f"TOTAL잔액: {total_JAN:,} KRW")

# 텔레그램 알림 보내기
try:
    telegram_alert.SendMessage(f"{now.strftime('%Y-%m-%d %H:%M')} \n 바이낸스: {round(binance_balance):,} USDT (≈ {round(binance_balance * exchange_rate):,} KRW) \n 바이비트: {round(bybit_balance):,} USDT (≈ {round(bybit_balance * exchange_rate):,} KRW), \n 비트겟: {round(bitget_balance):,} USDT (≈ {round(bitget_balance * exchange_rate):,} KRW), \n MEXC: {round(mexc_balance):,} USDT (≈ {round(mexc_balance * exchange_rate):,} KRW),  \n 총금액=> {total_JAN:,} 원")
    print("텔레그램 알림 전송 완료")
except Exception as e:
    print(f"텔레그램 알림 전송 실패: {e}")

print("===== 자산 조회 완료 =====")