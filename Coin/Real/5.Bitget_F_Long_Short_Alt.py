# -*- coding:utf-8 -*-
"""
파일이름: 5.Bitget_F_Long_Short_Alt.py
설명: Bitget 선물 롱/숏 양방향 알트코인 전략 (운영용)
      대상 코인: ETH, XRP, BNB, SOL, TRX, DOGE, ADA, HYPE
"""
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import json
import logging
import sys
import os
import socket
import telegram_alert

# ==============================================================================
# 1. 기본 설정 및 API 키
# ==============================================================================
# Bitget API 키 (실제 키로 교체 필요)
BITGET_ACCESS_KEY = "your_bitget_access_key"
BITGET_SECRET_KEY = "your_bitget_secret_key"
BITGET_PASSPHRASE = "your_bitget_passphrase"

# 알림 첫 문구
FIRST_STRING = "5.Bitget 롱숏 알트"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bitget_long_short_alt.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 2. 전략 및 거래 설정
# ==============================================================================
TIMEFRAME = '15m'             # 15분봉 데이터 사용
LEVERAGE = 8                  # 레버리지
INVEST_COIN_LIST = [
    "ETH/USDT:USDT",
    "XRP/USDT:USDT",
    "BNB/USDT:USDT",
    "SOL/USDT:USDT",
    "TRX/USDT:USDT",
    "DOGE/USDT:USDT",
    "ADA/USDT:USDT",
    "HYPE/USDT:USDT"
]
FEE_RATE = 0.0006             # 거래 수수료

# 기본 진입 금액 비율
BASE_BUY_RATE = 0.02

# 전략 스위치
USE_ADDITIVE_BUYING = False
USE_MACD_BUY_LOCK = True
USE_SHORT_STRATEGY = True
SHORT_CONDITION_TIMEFRAME = '1d'
MAX_LONG_BUY_COUNT = 10
MAX_SHORT_BUY_COUNT = 5
SHORT_ENTRY_RSI = 75
LONG_ENTRY_LOCK_SHORT_COUNT_DIFF = 6

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    BOT_DATA_FILE_PATH = "/var/AutoBot/json/Bitget_F_Long_Short_Alt_Data.json"
else:
    BOT_DATA_FILE_PATH = "./Bitget_F_Long_Short_Alt_Data.json"

# ==============================================================================
# 3. CCXT 초기화
# ==============================================================================
try:
    exchange = ccxt.bitget({
        'apiKey': BITGET_ACCESS_KEY,
        'secret': BITGET_SECRET_KEY,
        'password': BITGET_PASSPHRASE,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',
            'defaultSettle': 'usdt'
        }
    })
    logger.info("Bitget 거래소 연결 성공")
except Exception as e:
    logger.error(f"Bitget 거래소 연결 실패: {e}")
    sys.exit(1)

# 상태 데이터 딕셔너리
BotDataDict = {}

def load_bot_data():
    """JSON 파일에서 봇 상태 데이터를 로드합니다."""
    global BotDataDict
    try:
        if os.path.exists(BOT_DATA_FILE_PATH):
            with open(BOT_DATA_FILE_PATH, 'r') as f:
                BotDataDict = json.load(f)
            logger.info(f"봇 상태 데이터 로드 완료: {BOT_DATA_FILE_PATH}")
        else:
            BotDataDict = {}
            logger.info("기존 상태 데이터 파일이 없어 새로 시작합니다.")
    except Exception as e:
        logger.error(f"봇 상태 데이터 로드 오류: {e}")
        BotDataDict = {}

def save_bot_data():
    """현재 봇 상태 데이터를 JSON 파일로 저장합니다."""
    try:
        with open(BOT_DATA_FILE_PATH, 'w') as f:
            json.dump(BotDataDict, f, indent=2)
        logger.info("봇 상태 데이터 저장 완료")
    except Exception as e:
        logger.error(f"봇 상태 데이터 저장 오류: {e}")

load_bot_data()

# ==============================================================================
# 4. 데이터 및 지표 계산 함수
# ==============================================================================
def fetch_ohlcv(ticker, timeframe, limit=500):
    """지정된 티커와 타임프레임의 OHLCV 데이터를 가져옵니다."""
    try:
        ohlcv = exchange.fetch_ohlcv(ticker, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        logger.error(f"[{ticker}] OHLCV 데이터 가져오기 오류: {e}")
        return pd.DataFrame()

def calculate_indicators(df, window=14):
    """RSI, 볼린저밴드, MACD, 이동평균선을 계산합니다."""
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # 볼린저밴드
    df['bb_middle'] = df['close'].rolling(window=20).mean()
    std = df['close'].rolling(window=20).std()
    df['bb_upper'] = df['bb_middle'] + (std * 2)
    df['bb_lower'] = df['bb_middle'] - (std * 2)

    # MACD
    ema_fast = df['close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']

    # 이동평균선
    df['ma30'] = df['close'].rolling(window=30).mean()

    return df

def calculate_adx(df, window=14):
    """ADX 지표를 계산합니다."""
    df['h-l'] = df['high'] - df['low']
    df['h-pc'] = abs(df['high'] - df['close'].shift(1))
    df['l-pc'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['h-l', 'h-pc', 'l-pc']].max(axis=1)

    df['pdm'] = df['high'].diff()
    df['mdm'] = -df['low'].diff()
    df['pdm'] = df['pdm'].where((df['pdm'] > df['mdm']) & (df['pdm'] > 0), 0)
    df['mdm'] = df['mdm'].where((df['mdm'] > df['pdm']) & (df['mdm'] > 0), 0)

    df['pdi'] = (df['pdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100
    df['mdi'] = (df['mdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100
    
    with np.errstate(divide='ignore', invalid='ignore'):
        df['dx'] = (abs(df['pdi'] - df['mdi']) / (df['pdi'] + df['mdi'])) * 100
    df['dx'] = df['dx'].fillna(0)
    df['adx'] = df['dx'].ewm(alpha=1/window, adjust=False).mean()
    return df

def add_secondary_timeframe_indicators(df_base, ticker, secondary_timeframe='1d'):
    """상위 타임프레임 지표를 추가합니다."""
    df_secondary = fetch_ohlcv(ticker, secondary_timeframe, limit=100)
    if df_secondary.empty:
        return df_base.assign(prev_tf_close_below_ma30=False, prev_tf_macd_hist_neg=False, prev_tf_ma30_3day_rising=False, prev_tf_adx=0)

    df_secondary['ma30'] = df_secondary['close'].rolling(window=30).mean()
    ema_fast_sec = df_secondary['close'].ewm(span=12, adjust=False).mean()
    ema_slow_sec = df_secondary['close'].ewm(span=26, adjust=False).mean()
    macd_sec = ema_fast_sec - ema_slow_sec
    df_secondary['macd_histogram'] = macd_sec - macd_sec.ewm(span=9, adjust=False).mean()
    df_secondary['ma30_3day_rising'] = (df_secondary['ma30'].diff(1) > 0) & (df_secondary['ma30'].diff(2) > 0) & (df_secondary['ma30'].diff(3) > 0)
    df_secondary = calculate_adx(df_secondary, window=14)

    latest_secondary_candle = df_secondary.iloc[-2]

    df_base['prev_tf_close_below_ma30'] = latest_secondary_candle['close'] < latest_secondary_candle['ma30']
    df_base['prev_tf_macd_hist_neg'] = latest_secondary_candle['macd_histogram'] < 0
    df_base['prev_tf_ma30_3day_rising'] = latest_secondary_candle['ma30_3day_rising']
    df_base['prev_tf_adx'] = latest_secondary_candle['adx']
    
    return df_base

# ==============================================================================
# 5. 거래 실행 함수
# ==============================================================================
def get_available_balance(settle_currency='USDT'):
    """선물 계좌의 가용 잔고를 조회합니다."""
    try:
        balance = exchange.fetch_balance(params={'type': 'swap', 'settle': settle_currency.lower()})
        return balance.get('free', {}).get(settle_currency, 0)
    except Exception as e:
        logger.error(f"잔고 조회 오류: {e}")
        return 0

def get_average_price(entries):
    """진입 목록의 평균 가격을 계산합니다."""
    if not entries:
        return 0
    total_quantity = sum(e['quantity'] for e in entries)
    if total_quantity == 0:
        return 0
    total_value = sum(e['price'] * e['quantity'] for e in entries)
    return total_value / total_quantity

def calculate_order_amount(ticker, usdt_amount, price, leverage):
    """주문할 계약 수량을 계산합니다."""
    market = exchange.market(ticker)
    contract_size = float(market.get('contractSize', 1))
    position_value_usdt = usdt_amount * leverage
    coin_amount = position_value_usdt / price
    contract_amount = coin_amount / contract_size
    return contract_amount

def set_margin_mode_cross(ticker):
    """마진 모드를 CROSS로 설정합니다."""
    try:
        exchange.set_margin_mode('cross', ticker, params={'settle': 'usdt'})
        logger.info(f"[{ticker}] 마진 모드 CROSS 설정 완료")
    except Exception as e:
        logger.warning(f"[{ticker}] 마진 모드 설정 오류: {e}")

# ==============================================================================
# 6. 메인 실행 로직 (로직은 추후 구현)
# ==============================================================================
def run_bot():
    """봇의 메인 실행 로직입니다."""
    logger.info("===== Bitget 롱숏 알트 봇 실행 시작 =====")

    for coin_ticker in INVEST_COIN_LIST:
        logger.info(f"\n--- [{coin_ticker}] 처리 시작 ---")
        
        # 상태 데이터 초기화
        if coin_ticker not in BotDataDict:
            BotDataDict[coin_ticker] = {
                "long": {"entries": [], "buy_blocked_by_macd": False, "last_buy_timestamp": None},
                "short": {"entries": [], "sell_blocked_by_macd": False, "last_buy_timestamp": None}
            }
        
        long_pos_data = BotDataDict[coin_ticker]['long']
        short_pos_data = BotDataDict[coin_ticker]['short']

        # TODO: 전략 로직 구현
        # 1. 데이터 및 지표 계산
        # 2. 롱 포지션 청산 로직
        # 3. 롱 포지션 진입 로직
        # 4. 숏 포지션 청산 로직
        # 5. 숏 포지션 진입 로직

        logger.info(f"[{coin_ticker}] 로직 구현 대기중...")
        
        logger.info(f"--- [{coin_ticker}] 처리 완료 ---")
        time.sleep(1)

    logger.info("===== 봇 실행 종료 =====")

if __name__ == '__main__':
    run_bot()
