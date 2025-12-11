import ccxt
import socket
import requests
import time
import pyupbit
from datetime import datetime
import sys
import os

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    sys.path.insert(0, "/var/AutoBot/Common")
    sys.path.insert(0, "/var/AutoBot/Stock/Common")  # 주식 Common 경로 추가
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'Stock', 'Common'))  # 주식 Common 경로 추가
import telegram_alert
import myUpbit  # 우리가 만든 함수들이 들어있는 모듈
import myBinance
import ende_key
import my_key
from datetime import datetime
from collections import defaultdict
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 주식 계좌 관련 모듈 import
try:
    import KIS_Common as KisCommon
    import KIS_API_Helper_KR as KisKR
    import KIS_API_Helper_US as KisUS
    STOCK_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"주식 모듈 임포트 실패 (주식 잔액 조회 비활성화): {e}")
    STOCK_MODULES_AVAILABLE = False

# ==============================================================================
# 암복호화 클래스 객체 생성
# ==============================================================================
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# ==============================================================================
#  거래소 활성화 설정 (Control Panel)
# ==============================================================================
# True로 설정된 거래소만 조회합니다.
# 사용하지 않는 거래소는 False로 변경하여 비활성화하세요.
# 예: 바이낸스 계열만 사용하려면 다른 모든 거래소를 False로 설정합니다.
# ------------------------------------------------------------------------------
EXCHANGE_CONFIG = {
    "Upbit":        True,   # 업비트
    "Binance":      True,   # 바이낸스 메인
    "Binance_sub1": True,   # 바이낸스 서브1
    "Binance_sub2": True,   # 바이낸스 서브2
    "Binance_sub3": True,   # 바이낸스 서브3
    "GateIO":       True,   # GateIO 메인
    "GateIO_sub1":  True,   # GateIO 서브1
    "Bitget":       True,   # 비트겟 메인
    "Bitget_sub1":  True,   # 비트겟 서브1
    "OKX":          False,  # OKX (비활성화)
    "Bybit":        False,  # Bybit (비활성화)
    "MEXC":         False,  # MEXC (비활성화)
}

# ==============================================================================
#  주식 계좌 활성화 설정 (Control Panel) - 전략 6,7,8,9번 대응
# ==============================================================================
# True로 설정된 계좌만 조회합니다.
# 현재 모든 주식 전략(6,7,8,9번)이 동일한 REAL 계좌를 공유합니다.
#   - 전략 6번, 8번: 한국 주식 실제 계좌 (Stock_KR)
#   - 전략 7번, 9번: 미국 주식 실제 계좌 (Stock_US)
# 추후 REAL2 계좌 분리 시 설정 추가 예정
# ------------------------------------------------------------------------------
STOCK_ACCOUNT_CONFIG = {
    "Stock_KR":   True,    # 한국 주식 계좌 (전략 6번, 8번 공용)
    "Stock_US":   True,    # 미국 주식 계좌 (전략 7번, 9번 공용)
}

# ==============================================================================
# API 키 설정 (my_key.py에서 암호화된 키를 복호화하여 사용)
# ==============================================================================

# 업비트 키
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

# Binance API (메인 계정)
Binance_api_key = simpleEnDecrypt.decrypt(my_key.binance_access_M)
Binance_api_secret = simpleEnDecrypt.decrypt(my_key.binance_secret_M)

# Binance API (서브 계정 1)
Binance_api_key_sub1 = simpleEnDecrypt.decrypt(my_key.binance_access_S1)
Binance_api_secret_sub1 = simpleEnDecrypt.decrypt(my_key.binance_secret_S1)

# Binance API (서브 계정 2)
Binance_api_key_sub2 = simpleEnDecrypt.decrypt(my_key.binance_access_S2)
Binance_api_secret_sub2 = simpleEnDecrypt.decrypt(my_key.binance_secret_S2)

# Binance API (서브 계정 3)
Binance_api_key_sub3 = simpleEnDecrypt.decrypt(my_key.binance_access_S3)
Binance_api_secret_sub3 = simpleEnDecrypt.decrypt(my_key.binance_secret_S3)

# GateIO API (메인 계정)
GateIO_api_key = simpleEnDecrypt.decrypt(my_key.gateio_access_M)
GateIO_api_secret = simpleEnDecrypt.decrypt(my_key.gateio_secret_M)

# GateIO API (서브 계정 1)
GateIO_api_key_sub1 = simpleEnDecrypt.decrypt(my_key.gateio_access_S1)
GateIO_api_secret_sub1 = simpleEnDecrypt.decrypt(my_key.gateio_secret_S1)

# Bitget API (메인 계정)
Bitget_api_key = simpleEnDecrypt.decrypt(my_key.bitget_access_M)
Bitget_api_secret = simpleEnDecrypt.decrypt(my_key.bitget_secret_M)
Bitget_api_passphrase = simpleEnDecrypt.decrypt(my_key.bitget_passphrase_M)

# Bitget API (서브 계정 1)
Bitget_api_key_sub1 = simpleEnDecrypt.decrypt(my_key.bitget_access_S1)
Bitget_api_secret_sub1 = simpleEnDecrypt.decrypt(my_key.bitget_secret_S1)
Bitget_api_passphrase_sub1 = simpleEnDecrypt.decrypt(my_key.bitget_passphrase_S1)

# OKX API (비활성화 상태)
OKX_api_key = simpleEnDecrypt.decrypt(my_key.okx_access_M)
OKX_api_secret = simpleEnDecrypt.decrypt(my_key.okx_secret_M)
OKX_passphrase = simpleEnDecrypt.decrypt(my_key.okx_passphrase_M)

# Bybit API (비활성화 상태)
Bybit_api_key = simpleEnDecrypt.decrypt(my_key.bybit_access_M)
Bybit_api_secret = simpleEnDecrypt.decrypt(my_key.bybit_secret_M)

# MEXC API (비활성화 상태)
MEXC_api_key = simpleEnDecrypt.decrypt(my_key.mexc_access_M)
MEXC_api_secret = simpleEnDecrypt.decrypt(my_key.mexc_secret_M)

# ==============================================================================
# 거래소 객체 생성
# ==============================================================================

# 업비트 객체
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey) if EXCHANGE_CONFIG.get("Upbit") else None

# 모든 해외거래소 ccxt 객체를 담을 딕셔너리
all_exchanges = {
    "Binance": ccxt.binance({
        "apiKey": Binance_api_key, "secret": Binance_api_secret, "enableRateLimit": True,
    }),
    "Binance_sub1": ccxt.binance({
        "apiKey": Binance_api_key_sub1, "secret": Binance_api_secret_sub1, "enableRateLimit": True,
    }),
    "Binance_sub2": ccxt.binance({
        "apiKey": Binance_api_key_sub2, "secret": Binance_api_secret_sub2, "enableRateLimit": True,
    }),
    "Binance_sub3": ccxt.binance({
        "apiKey": Binance_api_key_sub3, "secret": Binance_api_secret_sub3, "enableRateLimit": True,
    }),
    "GateIO": ccxt.gateio({
        "apiKey": GateIO_api_key, "secret": GateIO_api_secret, "enableRateLimit": True,
    }),
    "GateIO_sub1": ccxt.gateio({
        "apiKey": GateIO_api_key_sub1, "secret": GateIO_api_secret_sub1, "enableRateLimit": True,
    }),
    "Bitget": ccxt.bitget({
        'apiKey': Bitget_api_key, 'secret': Bitget_api_secret, 'password': Bitget_api_passphrase, "enableRateLimit": True,
    }),
    "Bitget_sub1": ccxt.bitget({
        'apiKey': Bitget_api_key_sub1, 'secret': Bitget_api_secret_sub1, 'password': Bitget_api_passphrase_sub1, "enableRateLimit": True,
    }),
    "OKX": ccxt.okx({
        "apiKey": OKX_api_key, "secret": OKX_api_secret, "password": OKX_passphrase, "enableRateLimit": True,
    }),
    "Bybit": ccxt.bybit({
        "apiKey": Bybit_api_key, "secret": Bybit_api_secret, "enableRateLimit": True,
    }),
    "MEXC": ccxt.mexc({
        "apiKey": MEXC_api_key, "secret": MEXC_api_secret, "enableRateLimit": True,
    }),
}

# 활성화된 해외거래소만 선택하여 `exchanges` 딕셔너리 생성
exchanges = {name: obj for name, obj in all_exchanges.items() if EXCHANGE_CONFIG.get(name)}

EXCLUDE_COINS = {
    "BTC", "ETH", "BNB", "TRX", "ATOM", "DOGE", "DOT",
    "ETHW", "STRK", "KAITO", "XRP", "LTC", "IP"
}

# (이하 함수 정의는 기존 코드와 동일하게 유지)
# 거래소별 현물 잔액 조회 함수
def get_spot_balance(exchange, name):
    try:
        print(f"Fetching {name} spot balance...")
        
        # 거래소별 특화된 현물 잔액 조회 방식
        if name in ["Binance", "Binance_sub1", "Binance_sub2", "Binance_sub3"]:
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
            
        elif name in ["GateIO", "GateIO_sub1"]:
            balance = exchange.fetch_balance(params={"type": "spot"})
        elif name in ["Bitget", "Bitget_sub1"]:
            try:
                balance = exchange.fetch_balance(params={"type": "spot"})
            except Exception as spot_err:
                print(f"{name}: 현물 조회 오류 (권한 없음?) - 스킵. {spot_err}")
                return 0
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
        if name in ["Binance", "Binance_sub1", "Binance_sub2", "Binance_sub3"]:
            balance = exchange.fetch_balance(params={"type": "future"})
        elif name == "OKX":
            balance = exchange.fetch_balance(params={"type": "future"})
        elif name in ["GateIO", "GateIO_sub1"]:
            balance = exchange.fetch_balance(params={"type": "swap"})
        elif name in ["Bitget", "Bitget_sub1"]:
            balance = exchange.fetch_balance(params={"type": "swap"})
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
                return 1300  # 기본값 설정
        else:
            print(f"API Error: {data.get('error-type', 'Unknown error')}")
            return 1300  # 기본값 설정
    except requests.exceptions.RequestException as e:
        print(f"Error fetching exchange rate: {e}")
        return 1300  # 에러 발생 시 기본값 설정

# 개별 거래소 현물 코인 USDT 환산 잔액 조회 함수
def get_spot_coin_balances(exchange, name):
    balances = {}
    try:
        # CCXT 통일: spot 지갑에서만 조회
        raw = exchange.fetch_balance(params={"type": "spot"})
        for coin, amt in raw.get("total", {}).items():
            if amt and amt > 0:
                balances[coin] = amt
    except Exception as e:
        print(f"{name} spot balance fetch error: {e}")
        return {}

    usdt_dict = {}
    for coin, amt in balances.items():
        if coin == "USDT":
            usdt_dict["USDT"] = amt
        else:
            try:
                ticker = f"{coin}/USDT"
                price  = exchange.fetch_ticker(ticker)["last"]
                usdt_dict[coin] = amt * price
            except Exception:
                # 환산 불가 코인은 스킵
                continue
    return usdt_dict

# 모든 거래소에서 가져온 현물 잔액을 코인별로 합산
def aggregate_spot_balances():
    total = defaultdict(float)
    # 활성화된 거래소(`exchanges`)만 순회
    for name, exchange in exchanges.items():
        for coin, usdt_amt in get_spot_coin_balances(exchange, name).items():
            total[coin] += usdt_amt
    return total

# ==============================================================================
# 주식 계좌 잔액 조회 함수 (한국투자증권 API)
# ==============================================================================
def get_stock_balance_kr(mode="REAL"):
    """
    한국 주식 계좌 잔액 조회
    mode: "REAL" (실제 계좌) 또는 "VIRTUAL" (모의 계좌)
    반환값: 총 평가금액 (KRW)
    """
    if not STOCK_MODULES_AVAILABLE:
        print("주식 모듈이 로드되지 않아 한국 주식 잔액 조회 불가")
        return 0
    
    try:
        print(f"Fetching Korea Stock ({mode}) balance...")
        KisCommon.SetChangeMode(mode)
        time.sleep(1)  # API 레이트 리밋 방지
        
        balance = KisKR.GetBalance()
        if isinstance(balance, dict):
            total_money = float(balance.get('TotalMoney', 0))
            print(f"Korea Stock ({mode}) Total: {total_money:,.0f} KRW")
            return total_money
        else:
            print(f"Korea Stock ({mode}) Balance Error: {balance}")
            return 0
    except Exception as e:
        print(f"Korea Stock ({mode}) Balance Error: {e}")
        return 0

def get_stock_balance_us(mode="REAL"):
    """
    미국 주식 계좌 잔액 조회
    mode: "REAL" (실제 계좌) 또는 "VIRTUAL" (모의 계좌)
    반환값: 총 평가금액 (USD)
    """
    if not STOCK_MODULES_AVAILABLE:
        print("주식 모듈이 로드되지 않아 미국 주식 잔액 조회 불가")
        return 0
    
    try:
        print(f"Fetching US Stock ({mode}) balance...")
        KisCommon.SetChangeMode(mode)
        time.sleep(1)  # API 레이트 리밋 방지
        
        balance = KisUS.GetBalance("USD")
        if isinstance(balance, dict):
            total_money = float(balance.get('TotalMoney', 0))
            print(f"US Stock ({mode}) Total: {total_money:,.2f} USD")
            return total_money
        else:
            print(f"US Stock ({mode}) Balance Error: {balance}")
            return 0
    except Exception as e:
        print(f"US Stock ({mode}) Balance Error: {e}")
        return 0

def get_all_stock_balances():
    """
    활성화된 모든 주식 계좌의 잔액을 조회
    반환값: {계좌명: 금액} 딕셔너리
    """
    stock_balances = {}
    
    # 한국 주식 계좌 (전략 6번, 8번 공용)
    if STOCK_ACCOUNT_CONFIG.get("Stock_KR"):
        kr_balance = get_stock_balance_kr("REAL")
        if kr_balance > 0:
            stock_balances["Stock_KR"] = {"amount": kr_balance, "currency": "KRW"}
        time.sleep(1)
    
    # 미국 주식 계좌 (전략 7번, 9번 공용)
    if STOCK_ACCOUNT_CONFIG.get("Stock_US"):
        us_balance = get_stock_balance_us("REAL")
        if us_balance > 0:
            stock_balances["Stock_US"] = {"amount": us_balance, "currency": "USD"}
    
    return stock_balances

# ==============================================================================
# 메인 로직 시작
# ==============================================================================

print("===== 자산 조회 시작 =====")

# 자산 조회 결과를 저장할 딕셔너리
exchange_balances = {}
exchange_total_usdt = 0

# 활성화된 해외 거래소의 자산 조회
for name, exchange_obj in exchanges.items():
    balance = get_exchange_total_balance(exchange_obj, name)
    exchange_balances[name] = balance
    time.sleep(2) # API 레이트 리밋 방지

# 업비트 현물 자산 조회
TotalRealMoney = 0
if EXCHANGE_CONFIG.get("Upbit") and upbit:
    try:
        print("Fetching Upbit balance...")
        balances = upbit.get_balances()
        TotalRealMoney = myUpbit.GetTotalRealMoney(balances)  # 총 평가금액
        print(f"Upbit Total: {TotalRealMoney:,.0f} KRW")
    except Exception as e:
        print(f"Upbit Error: {e}")
        TotalRealMoney = 0
else:
    print("Upbit is disabled in the configuration.")

time.sleep(1)

# ==============================================================================
# 주식 계좌 잔액 조회 (전략 6,7,8,9번)
# ==============================================================================
stock_balances = {}
stock_total_krw = 0

if STOCK_MODULES_AVAILABLE and any(STOCK_ACCOUNT_CONFIG.values()):
    print("\n----- 주식 계좌 조회 시작 -----")
    stock_balances = get_all_stock_balances()
    print("----- 주식 계좌 조회 완료 -----\n")
else:
    print("주식 계좌 조회가 비활성화되었거나 모듈을 사용할 수 없습니다.")

# 환율 조회
exchange_rate = get_exchange_rate()
print(f"Exchange Rate (USD to KRW): {exchange_rate}")

# 주식 잔액 KRW 환산
for account_name, info in stock_balances.items():
    if info['currency'] == 'USD':
        krw_value = info['amount'] * exchange_rate
    else:  # KRW
        krw_value = info['amount']
    stock_total_krw += krw_value
    stock_balances[account_name]['krw_value'] = krw_value

# 총 자산 계산 (코인 + 주식)
exchange_total_usdt = sum(exchange_balances.values())
coin_total_krw = round(exchange_total_usdt * exchange_rate) + round(TotalRealMoney)
total_JAN = coin_total_krw + round(stock_total_krw)
now = datetime.now()

# --- 최종 결과 출력 (동적) ---
print("\n===== 최종 결과 =====")
telegram_report_lines = []
for name, balance in exchange_balances.items():
    krw_value = round(balance * exchange_rate)
    print_line = f"{name} Balance: {round(balance)} USDT (≈ {krw_value:,} KRW)"
    telegram_line = f"\n {name}: {round(balance):,} USDT (≈ {krw_value:,} KRW)"
    print(print_line)
    telegram_report_lines.append(telegram_line)

print("-" * 20)
print(f"\n선물+현물(해외거래소): {round(exchange_total_usdt)} USDT ({round(exchange_total_usdt * exchange_rate):,} KRW)")
if EXCHANGE_CONFIG.get("Upbit"):
    print(f"현물(업비트): {round(TotalRealMoney):,} KRW")

# 주식 잔액 출력
if stock_balances:
    print("-" * 20)
    print("주식 계좌:")
    for account_name, info in stock_balances.items():
        if info['currency'] == 'USD':
            print(f"  {account_name}: {info['amount']:,.2f} USD (≈ {round(info['krw_value']):,} KRW)")
        else:
            print(f"  {account_name}: {round(info['amount']):,} KRW")
    print(f"주식 총합: {round(stock_total_krw):,} KRW")

print("-" * 20)
print(f"코인 총합: {coin_total_krw:,} KRW")
print(f"TOTAL잔액 (코인+주식): {total_JAN:,} KRW")

# --- 텔레그램 알림 ---
try:
    # 거래소별 최대 금액 길이 계산
    max_balance_str = f"{round(total_JAN):,}"  # 가장 큰 금액 기준
    max_balance_len = len(max_balance_str)
    
    # 깔끔한 리스트 형식 (오른쪽 정렬)
    telegram_message = f"📊 {now.strftime('%Y-%m-%d %H:%M')} 자산 현황\n"
    telegram_message += "=" * 35 + "\n"
    telegram_message += "💎 코인\n"
    
    # 거래소별 잔액
    for name, balance in exchange_balances.items():
        bal = round(balance)
        # sub 계정 이름 변환 (Binance_sub1 → Binance1)
        display_name = name.replace("_sub", "")
        
        # 고정 너비로 정렬 (거래소명: 10자, 금액: 오른쪽 정렬)
        bal_str = f"{bal:,}" if bal > 0 else "0"
        telegram_message += f"• {display_name:<10} {bal_str:>15}\n"
    
    telegram_message += "-" * 35 + "\n"
    exchange_total_str = f"{round(exchange_total_usdt):,}"
    telegram_message += f"💰 해외 합계    {exchange_total_str:>15} $\n"
    
    if EXCHANGE_CONFIG.get("Upbit") and TotalRealMoney > 0:
        upbit_str = f"{round(TotalRealMoney):,}"
        telegram_message += f"🇰🇷 업비트      {upbit_str:>15} 원\n"
    
    coin_total_str = f"{coin_total_krw:,}"
    telegram_message += f"📈 코인 합계    {coin_total_str:>15} 원\n"
    
    # 주식 계좌 섹션
    if stock_balances:
        telegram_message += "=" * 35 + "\n"
        telegram_message += "📊 주식\n"
        
        for account_name, info in stock_balances.items():
            # 표시 이름 간소화
            if account_name == "Stock_KR":
                display_name = "한국 주식"
            elif account_name == "Stock_US":
                display_name = "미국 주식"
            else:
                display_name = account_name
            
            if info['currency'] == 'USD':
                amt_str = f"{round(info['amount']):,} $"
            else:
                amt_str = f"{round(info['amount']):,}"
            
            telegram_message += f"• {display_name:<10} {amt_str:>15}\n"
        
        telegram_message += "-" * 35 + "\n"
        stock_total_str = f"{round(stock_total_krw):,}"
        telegram_message += f"📊 주식 합계    {stock_total_str:>15} 원\n"
    
    telegram_message += "=" * 35 + "\n"
    total_str = f"{total_JAN:,}"
    telegram_message += f"🏆 총자산      {total_str:>15} 원"

    telegram_alert.SendMessage(telegram_message)
    print("텔레그램 알림 전송 완료")
except Exception as e:
    print(f"텔레그램 알림 전송 실패: {e}")


# --- 현물 코인별 합산 잔액 및 스프레드시트 업데이트 ---
aggregated = aggregate_spot_balances()

sorted_balances = sorted(
    ((coin, amt) for coin, amt in aggregated.items() if coin not in EXCLUDE_COINS and amt > 100),
    key=lambda x: x[1],
    reverse=True
)

print("\n⛳ 현물 코인별 합산 잔액 (콘솔 출력) - 내림차순")
for coin, amt in sorted_balances:
    print(f"{coin} {int(amt)}")

# 텔레그램 알림 제거 (콘솔만 출력)
# lines = [f"{coin} {int(amt)}" for coin, amt in sorted_balances]
# message = "⛳ 현물 코인별 합산 잔액\n" + "\n".join(lines)
# telegram_alert.SendMessage(message)

# 스프레드시트 데이터 갱신
try:
    gspreadJsonPath = dict()
    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong" :
        #서버: 
        gspreadJsonPath = "/var/AutoBot/json/autobot.json"
    else:
        #PC
        gspreadJsonPath = os.path.join(os.path.dirname(__file__), '..', 'json', 'autobot.json')

    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(gspreadJsonPath, scope)
    client = gspread.authorize(creds)
    sheet = client.open("코인투자").worksheet("예치")

    start_row = 24
    coin_names = [[coin] for coin, _ in sorted_balances]
    amounts = [[int(amount)] for _, amount in sorted_balances]

    clear_range_end_row = start_row + 29
    clear_values = [['', ''] for _ in range(30)]
    sheet.update(range_name=f"A{start_row}:B{clear_range_end_row}", values=clear_values)

    if sorted_balances:
        end_row_a = start_row + len(coin_names) - 1
        sheet.update(range_name=f"A{start_row}:A{end_row_a}", values=coin_names)
        end_row_b = start_row + len(amounts) - 1
        sheet.update(range_name=f"B{start_row}:B{end_row_b}", values=amounts)
    print("Google Sheet 업데이트 완료")
except Exception as e:
    print(f"Google Sheet 업데이트 실패: {e}")


print("===== 자산 조회 완료 =====")