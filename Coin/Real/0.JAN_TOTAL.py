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

# ==============================================================================
#  거래소 활성화 설정 (Control Panel)
# ==============================================================================
# True로 설정된 거래소만 조회합니다.
# 사용하지 않는 거래소는 False로 변경하여 비활성화하세요.
# 예: 바이낸스 계열만 사용하려면 다른 모든 거래소를 False로 설정합니다.
# ------------------------------------------------------------------------------
EXCHANGE_CONFIG = {
    "Binance":      True,
    "Binance_sub1": True,
    "Binance_sub2": True,
    "Binance_sub3": True,
    "OKX":          False,
    "Bybit":        False,
    "Bitget":       False,
    "MEXC":         False,
    "Upbit":        False,  # 업비트도 여기서 활성화/비활성화 가능
}

# ==============================================================================
# API 키 설정
# ==============================================================================
# 업비트 키
Upbit_AccessKey = "AYneBweCn6FFMeWtTO0Cxq0XJxU7rCZ6WpzUsvNk"
Upbit_ScretKey = "BV0gy2txNyF9Brv594YXxcRYs3EQZe9TaWMtN14Z"

# Binance API 인증 정보 (기존 계정)
Binance_api_key = "3L5mMgSFzt8HlPt6daAIzLxRTqFPaA1ItKMYNgNdgNkBOtBmlUMDzefQAK1UMs4J"
Binance_api_secret = "CXNpmRpSGpH9BXjkIbqKMtp1icekWPsTyIEhC0OcPrzclKnai9ATzrH3BVHUI9zL"

# Binance API 인증 정보 (서브 계정 1)
Binance_api_key_sub1 = "qXIylTz7Qh2nrVh1kPJQTXX9Fm0G8Tot86Lgqzm652mTdnEj7DrbJO6KT261fQJk"
Binance_api_secret_sub1 = "DarhAG7HjLW7OJBe814q42io5UOYB9dzhwQlbijuz5m5gN9mREA5wfbeGT7H0PwI"

# Binance API 인증 정보 (서브 계정 2)
Binance_api_key_sub2 = "lkDPjRCIHmp3olbPKYABO9yN3IXriiK1ikcyN8CyukNV6GDwqs3CfHfTuH1d0sOB"
Binance_api_secret_sub2 = "TECfDyTTtYwCJbaC2k949ey08KsnB7X9dGOqteAaeIyZbT62bbj2uKKA4ygZCBTj"

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
    "OKX": ccxt.okx({
        "apiKey": OKX_api_key, "secret": OKX_api_secret, "password": OKX_passphrase, "enableRateLimit": True,
    }),
    "Bybit": ccxt.bybit({
        "apiKey": Bybit_api_key, "secret": Bybit_api_secret, "enableRateLimit": True,
    }),
    "Bitget": ccxt.bitget({
        'apiKey': Bitget_api_key, 'secret': Bitget_api_secret, 'password': Bitget_api_passphrase,
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

# 환율 조회
exchange_rate = get_exchange_rate()
print(f"Exchange Rate (USD to KRW): {exchange_rate}")

# 총 자산 계산
exchange_total_usdt = sum(exchange_balances.values())
total_JAN = round(exchange_total_usdt * exchange_rate) + round(TotalRealMoney)
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
print(f"TOTAL잔액: {total_JAN:,} KRW")

# --- 텔레그램 알림 (동적) ---
try:
    # 메시지 헤더
    telegram_message = f"{now.strftime('%Y-%m-%d %H:%M')}"
    # 활성화된 거래소별 잔액 추가
    telegram_message += "".join(telegram_report_lines)
    # 총 금액 추가
    telegram_message += f"\n\n 총금액=> {total_JAN:,} 원"

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

lines = [f"{coin} {int(amt)}" for coin, amt in sorted_balances]
message = "⛳ 현물 코인별 합산 잔액\n" + "\n".join(lines)
telegram_alert.SendMessage(message)

# 스프레드시트 데이터 갱신
try:
    gspreadJsonPath = dict()
    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong" :
        #서버: 
        gspreadJsonPath = "/var/AutoBot/json/autobot.json"
    else:
        #PC
        gspreadJsonPath = "C:\\AutoTrading\\AutoTrading\\json\\autobot.json"

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