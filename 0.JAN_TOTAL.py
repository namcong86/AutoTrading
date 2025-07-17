import ccxt
import socket
import requests
import telegram_alert
import time
import pyupbit
import myUpbit  # 우리가 만든 함수들이 들어있는 모듈
from datetime import datetime
from collections import defaultdict
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# 업비트 키
Upbit_AccessKey = "AYneBweCn6FFMeWtTO0Cxq0XJxU7rCZ6WpzUsvNk"
Upbit_ScretKey = "BV0gy2txNyF9Brv594YXxcRYs3EQZe9TaWMtN14Z"

# 업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)

# Binance API 인증 정보 (기존 계정)
Binance_api_key = "3L5mMgSFzt8HlPt6daAIzLxRTqFPaA1ItKMYNgNdgNkBOtBmlUMDzefQAK1UMs4J"
Binance_api_secret = "CXNpmRpSGpH9BXjkIbqKMtp1icekWPsTyIEhC0OcPrzclKnai9ATzrH3BVHUI9zL"

# Binance API 인증 정보 (서브 계정 1)
Binance_api_key_sub1 = "qXIylTz7Qh2nrVh1kPJQTXX9Fm0G8Tot86Lgqzm652mTdnEj7DrbJO6KT261fQJk"
Binance_api_secret_sub1 = "DarhAG7HjLW7OJBe814q42io5UOYB9dzhwQlbijuz5m5gN9mREA5wfbeGT7H0PwI"

# Binance API 인증 정보 (서브 계정 2)
Binance_api_key_sub2 = "HbC79j9E1f8fZUXe7YK5DcgOxG3rcgbd1lSt3r17BJmqga5EbHVbNwIux1Rm6K3q"
Binance_api_secret_sub2 = "lM3RhPOesjwyLLpECpwUuijOZLUpVZEqdRKDmRSPE6WbadQltXRtNIrfY6rnRCMg"

# Binance API 인증 정보 (서브 계정 3)
Binance_api_key_sub3 = "EYNqzB1k2echWMLnmUSZWf1O03U8fiPUMQX9OHL83eeWGotYgoq1dJaDQYleh8Wa"
Binance_api_secret_sub3 = "PW2cxdCPGSJXMhiEgT2aABt0NikxOntPVOzMxgAYkWe4DxSU1xIzPJgZfnujf28h"

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

# Binance_ccxt 객체 생성 (기존 계정)
Binance_exchange = ccxt.binance({
    "apiKey": Binance_api_key,
    "secret": Binance_api_secret,
    "enableRateLimit": True,
})

# Binance_ccxt 객체 생성 (서브 계정 1)
Binance_exchange_sub1 = ccxt.binance({
    "apiKey": Binance_api_key_sub1,
    "secret": Binance_api_secret_sub1,
    "enableRateLimit": True,
})

# Binance_ccxt 객체 생성 (서브 계정 2)
Binance_exchange_sub2 = ccxt.binance({
    "apiKey": Binance_api_key_sub2,
    "secret": Binance_api_secret_sub2,
    "enableRateLimit": True,
})

# Binance_ccxt 객체 생성 (서브 계정 3)
Binance_exchange_sub3 = ccxt.binance({
    "apiKey": Binance_api_key_sub3,
    "secret": Binance_api_secret_sub3,
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

exchanges = {
    "Binance":   Binance_exchange,
    "OKX":       OKX_exchange,
    "Bybit":     Bybit_exchange,
    "Bitget":    Bitget_exchange,
    "MEXC":      MEXC_exchange,
    "Binance_sub1": Binance_exchange_sub1,  # 서브 계정 1 추가
    "Binance_sub2": Binance_exchange_sub2,  # 서브 계정 2 추가
    "Binance_sub3": Binance_exchange_sub3,  # 서브 계정 3 추가
}

EXCLUDE_COINS = {
    "BTC", "ETH", "BNB", "TRX", "ATOM", "DOGE", "DOT",
    "ETHW", "STRK", "KAITO", "XRP", "LTC", "IP"
}

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
        if name in ["Binance", "Binance_sub1", "Binance_sub2", "Binance_sub3"]:
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
    for name, exchange in exchanges.items():
        for coin, usdt_amt in get_spot_coin_balances(exchange, name).items():
            total[coin] += usdt_amt
    return total


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
binance_balance_sub1 = get_exchange_total_balance(Binance_exchange_sub1, "Binance_sub1")
time.sleep(2)
binance_balance_sub2 = get_exchange_total_balance(Binance_exchange_sub2, "Binance_sub2")
time.sleep(2)
binance_balance_sub3 = get_exchange_total_balance(Binance_exchange_sub3, "Binance_sub3")
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
print(f"Binance_sub1 Balance: {round(binance_balance_sub1)} USDT (≈ {round(binance_balance_sub1 * exchange_rate):,} KRW)")
print(f"Binance_sub2 Balance: {round(binance_balance_sub2)} USDT (≈ {round(binance_balance_sub2 * exchange_rate):,} KRW)")
print(f"Binance_sub3 Balance: {round(binance_balance_sub3)} USDT (≈ {round(binance_balance_sub3 * exchange_rate):,} KRW)")
print(f"OKX Balance: {round(okx_balance)} USDT (≈ {round(okx_balance * exchange_rate):,} KRW)")
print(f"Bybit Balance: {round(bybit_balance)} USDT (≈ {round(bybit_balance * exchange_rate):,} KRW)")
print(f"Bitget Balance: {round(bitget_balance)} USDT (≈ {round(bitget_balance * exchange_rate):,} KRW)")
print(f"MEXC Balance: {round(mexc_balance)} USDT (≈ {round(mexc_balance * exchange_rate):,} KRW)")

exchange_total = binance_balance + binance_balance_sub1 + binance_balance_sub2 + binance_balance_sub3 + okx_balance + bybit_balance + bitget_balance + mexc_balance
total_JAN = round(exchange_total * exchange_rate) + round(TotalRealMoney)

# 현재 날짜와 시간 구하기
now = datetime.now()

# 출력 및 텔레그램 알림
print(f"\n선물+현물(해외거래소): {round(exchange_total * exchange_rate):,} KRW")
print(f"현물(업비트): {round(TotalRealMoney):,} KRW")
print(f"TOTAL잔액: {total_JAN:,} KRW")

# 텔레그램 알림 보내기
try:
    telegram_alert.SendMessage(f"{now.strftime('%Y-%m-%d %H:%M')} \n 바이낸스: {round(binance_balance):,} USDT (≈ {round(binance_balance * exchange_rate):,} KRW) \n 바이낸스_sub1: {round(binance_balance_sub1):,} USDT (≈ {round(binance_balance_sub1 * exchange_rate):,} KRW) \n 바이낸스_sub2: {round(binance_balance_sub2):,} USDT (≈ {round(binance_balance_sub2 * exchange_rate):,} KRW) \n 바이낸스_sub3: {round(binance_balance_sub3):,} USDT (≈ {round(binance_balance_sub3 * exchange_rate):,} KRW) \n 바이비트: {round(bybit_balance):,} USDT (≈ {round(bybit_balance * exchange_rate):,} KRW), \n 비트겟: {round(bitget_balance):,} USDT (≈ {round(bitget_balance * exchange_rate):,} KRW), \n MEXC: {round(mexc_balance):,} USDT (≈ {round(mexc_balance * exchange_rate):,} KRW),  \n 총금액=> {total_JAN:,} 원")
    print("텔레그램 알림 전송 완료")
except Exception as e:
    print(f"텔레그램 알림 전송 실패: {e}")

# --- 기존에 쓰시던 “현재 총잔액 알림” 부분 바로 아래에 추가 ---
aggregated = aggregate_spot_balances()

# 2) 제외 코인 필터링 및 잔액 100 이하 제외 후 내림차순 정렬
# 잔액(amt)이 100을 초과하는 코인만 포함하도록 필터링 조건을 추가합니다.
sorted_balances = sorted(
    ((coin, amt) for coin, amt in aggregated.items() if coin not in EXCLUDE_COINS and amt > 100),
    key=lambda x: x[1],
    reverse=True
)

# 3) 콘솔 출력 (디버깅 & 확인용)
print("⛳ 현물 코인별 합산 잔액 (콘솔 출력) - 내림차순")
for coin, amt in sorted_balances:
    print(f"{coin} {int(amt)}")

# 4) Telegram 메시지 생성 & 전송
lines = [f"{coin} {int(amt)}" for coin, amt in sorted_balances]
message = "⛳ 현물 코인별 합산 잔액\n" + "\n".join(lines)
telegram_alert.SendMessage(message)

# 스프레드시트 데이터 갱신
gspreadJsonPath = dict()
pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong" :
    #서버: 
    gspreadJsonPath = "/var/AutoBot/json/autobot.json"
else:
    #PC
    gspreadJsonPath = "C:\\AutoTrading\\AutoTrading\\json\\autobot.json"

# 구글 스프레드시트 인증
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(gspreadJsonPath, scope)
client = gspread.authorize(creds)

# 스프레드시트 열기 (문서 이름 또는 ID 사용)
sheet = client.open("코인투자").worksheet("예치")  # 예: 'Sheet1' 탭

# A24부터 코인명, B24부터 잔액 입력
start_row = 24  # A24 부터 시작

# 준비: 코인명과 금액을 담은 리스트
coin_names = [[coin] for coin, _ in sorted_balances]
amounts = [[int(amount)] for _, amount in sorted_balances]

# 1. 기존 데이터 초기화
# 최대 30개 행을 지운다고 가정하고, 해당 범위의 값을 비워줍니다.
clear_range_end_row = start_row + 29
clear_values = [['', ''] for _ in range(30)]
sheet.update(range_name=f"A{start_row}:B{clear_range_end_row}", values=clear_values)


# 2. 새로운 데이터 업데이트
# 잔액이 100을 초과하는 코인이 있을 경우에만 업데이트를 진행합니다.
if sorted_balances: # 리스트가 비어있지 않은 경우
    # 코인 이름 업데이트 (A열)
    end_row_a = start_row + len(coin_names) - 1
    sheet.update(range_name=f"A{start_row}:A{end_row_a}", values=coin_names)

    # 코인별 잔액 업데이트 (B열)
    end_row_b = start_row + len(amounts) - 1
    sheet.update(range_name=f"B{start_row}:B{end_row_b}", values=amounts)


print("===== 자산 조회 완료 =====")