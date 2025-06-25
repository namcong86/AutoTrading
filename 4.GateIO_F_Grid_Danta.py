# -*- coding:utf-8 -*-
"""
파일이름: GateIO_F_Grid_Danta_Operational.py
설명: 볼린저밴드, RSI, MACD, ADX를 이용한 롱/숏 그리드 매매 전략 (운영용)
참조:
  - 전략 로직: 4.GateIO_F_Grid_Danta_Test.py
  - 운영 구조: 3.GateIO_F_DOGE_PEPE_leverage.py
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
import telegram_alert # telegram_alert.py 파일이 필요합니다.

# ==============================================================================
# 1. 기본 설정 및 API 키
# ==============================================================================
# Gate.io API 키 (실제 키로 교체하고 보안상 환경변수 사용을 권장합니다)
GATEIO_ACCESS_KEY = "07a0ba2f6ed018fcb0fde7d08b58b40c"
GATEIO_SECRET_KEY = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"

# 알림 첫 문구
FIRST_STRING = "4.GateIO 그리드봇 "

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_grid_danta.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 2. 전략 및 거래 설정 (백테스트 스크립트 기반)
# ==============================================================================
TIMEFRAME = '15m'             # 15분봉 데이터 사용
LEVERAGE = 10                 # 레버리지
INVEST_COIN_LIST = ["DOGE/USDT:USDT"] # 운영할 코인 목록 (리스트)
FEE_RATE = 0.0005             # 거래 수수료 (시장가 0.05%)

# 기본 진입 금액 비율 (가용 현금 대비)
BASE_BUY_RATE = 0.02 # 예: 0.02 = 가용 현금의 2%를 첫 진입 시 사용

# --- 전략 선택 스위치 ---
USE_ADDITIVE_BUYING = False  # True: RSI/차수별 가산 매수 사용, False: 균등 매수 사용
USE_MACD_BUY_LOCK = True     # True: MACD 히스토그램이 음수일 때 추가 매수 잠금

# 숏 포지션 전략 관련 설정
USE_SHORT_STRATEGY = True    # True: 숏 포지션 전략 사용
SHORT_CONDITION_TIMEFRAME = '1d' # 숏 포지션 진입 조건 확인용 타임프레임
MAX_LONG_BUY_COUNT = 15      # 최대 롱 분할매수 횟수
MAX_SHORT_BUY_COUNT = 10     # 최대 숏 분할매수 횟수
SHORT_ENTRY_RSI = 75         # 숏 포지션 진입을 위한 RSI 조건 값

# 롱 포지션 개수와 ADX에 따른 숏 진입 RSI 조정값
SHORT_RSI_ADJUSTMENT = 0

# 롱 포지션이 숏 포지션보다 이 횟수 이상 많고, 특정 조건 만족 시 추가 롱 진입 방지
LONG_ENTRY_LOCK_SHORT_COUNT_DIFF = 7

# 상태 저장 파일
BOT_DATA_FILE_PATH = "./GateIO_F_Grid_Danta_Data.json"

# ==============================================================================
# 3. CCXT 및 상태 파일 초기화
# ==============================================================================
try:
    exchange = ccxt.gateio({
        'apiKey': GATEIO_ACCESS_KEY,
        'secret': GATEIO_SECRET_KEY,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',
            'createMarketBuyOrderRequiresPrice': False,
        }
    })
    exchange.load_markets()
except Exception as e:
    logger.error(f"거래소 연결 실패: {e}")
    sys.exit()

try:
    with open(BOT_DATA_FILE_PATH, 'r') as f:
        BotDataDict = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    BotDataDict = {}
    logger.info(f"상태 파일을 찾을 수 없거나 비어있어 새로 생성합니다: {BOT_DATA_FILE_PATH}")

def save_bot_data():
    """상태 데이터를 JSON 파일에 저장합니다."""
    with open(BOT_DATA_FILE_PATH, 'w') as f:
        json.dump(BotDataDict, f, indent=4)

# ==============================================================================
# 4. 데이터 처리 및 보조지표 계산 함수 (백테스트 스크립트 기반)
# ==============================================================================
def fetch_ohlcv(ticker, timeframe, limit=200):
    """CCXT를 사용하여 OHLCV 데이터를 가져옵니다."""
    try:
        ohlcv = exchange.fetch_ohlcv(ticker, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        logger.error(f"[{ticker}] OHLCV 데이터 조회 오류: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    """DataFrame에 보조지표(BB, RSI, MACD)를 추가합니다."""
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bb_upper'] = df['ma30'] + 2 * df['stddev']
    df['bb_lower'] = df['ma30'] - 2 * df['stddev']
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=13, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    ema_fast = df['close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    return df

def calculate_adx(df, window=14):
    """ADX 지표를 계산합니다."""
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
    
    df['pdm'] = (df['high'] - df['high'].shift(1))
    df['mdm'] = (df['low'].shift(1) - df['low'])
    df['pdm'] = df['pdm'].where((df['pdm'] > df['mdm']) & (df['pdm'] > 0), 0)
    df['mdm'] = df['mdm'].where((df['mdm'] > df['pdm']) & (df['mdm'] > 0), 0)

    df['pdi'] = (df['pdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100
    df['mdi'] = (df['mdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100
    
    with np.errstate(divide='ignore', invalid='ignore'):
        df['dx'] = (abs(df['pdi'] - df['mdi']) / (df['pdi'] + df['mdi'])) * 100
    df['dx'] = df['dx'].fillna(0)
    df['adx'] = df['dx'].ewm(alpha=1/window, adjust=False).mean()
    return df

def add_secondary_timeframe_indicators(df_base, secondary_timeframe='1d'):
    """주어진 타임프레임으로 데이터를 리샘플링하고 지표를 원본 데이터프레임에 병합합니다."""
    df_secondary = fetch_ohlcv(df_base.name, secondary_timeframe, limit=100)
    if df_secondary.empty:
        return df_base.assign(prev_tf_close_below_ma30=False, prev_tf_macd_hist_neg=False, prev_tf_ma30_3day_rising=False, prev_tf_adx=0)

    df_secondary['ma30'] = df_secondary['close'].rolling(window=30).mean()
    ema_fast_sec = df_secondary['close'].ewm(span=12, adjust=False).mean()
    ema_slow_sec = df_secondary['close'].ewm(span=26, adjust=False).mean()
    macd_sec = ema_fast_sec - ema_slow_sec
    df_secondary['macd_histogram'] = macd_sec - macd_sec.ewm(span=9, adjust=False).mean()
    df_secondary['ma30_3day_rising'] = (df_secondary['ma30'].diff(1) > 0) & (df_secondary['ma30'].diff(2) > 0) & (df_secondary['ma30'].diff(3) > 0)
    df_secondary = calculate_adx(df_secondary, window=14)

    # **가장 최근의 완성된 봉**의 데이터를 사용합니다.
    latest_secondary_candle = df_secondary.iloc[-2]

    df_base['prev_tf_close_below_ma30'] = latest_secondary_candle['close'] < latest_secondary_candle['ma30']
    df_base['prev_tf_macd_hist_neg'] = latest_secondary_candle['macd_histogram'] < 0
    df_base['prev_tf_ma30_3day_rising'] = latest_secondary_candle['ma30_3day_rising']
    df_base['prev_tf_adx'] = latest_secondary_candle['adx']
    
    return df_base

def get_buy_amount(base_amount, rsi_value, entry_count):
    """RSI 레벨과 진입 차수에 따라 최종 매수 증거금을 계산합니다."""
    def get_rsi_level(rsi):
        if 20 < rsi <= 25: return 1
        if 15 < rsi <= 20: return 2
        if 10 < rsi <= 15: return 3
        if rsi <= 10: return 4
        return 0

    rsi_level = get_rsi_level(rsi_value)
    rsi_multiplier = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.3}.get(rsi_level, 1.0)
    entry_multiplier = 1.0
    if 4 <= entry_count <= 6: entry_multiplier = 1.2
    elif 7 <= entry_count <= 10: entry_multiplier = 1.3
    elif entry_count > 10: entry_multiplier = 1.3
    return base_amount * rsi_multiplier * entry_multiplier

# ==============================================================================
# 5. 거래 실행 및 관리 함수
# ==============================================================================
def get_available_balance(settle_currency='USDT'):
    """선물 계좌의 가용 잔고를 조회합니다."""
    try:
        balance = exchange.fetch_balance(params={'type': 'swap', 'settle': settle_currency.lower()})
        return balance['free'][settle_currency]
    except Exception as e:
        logger.error(f"잔고 조회 오류: {e}")
        return 0

def get_current_position(ticker):
    """특정 티커의 현재 롱/숏 포지션 정보를 조회합니다."""
    try:
        positions = exchange.fetch_positions(symbols=[ticker])
        long_pos = None
        short_pos = None
        for p in positions:
            if p['symbol'] == ticker:
                if p['side'] == 'long' and p['contracts'] > 0:
                    long_pos = {'contracts': p['contracts'], 'entryPrice': p['entryPrice']}
                elif p['side'] == 'short' and p['contracts'] > 0:
                    short_pos = {'contracts': p['contracts'], 'entryPrice': p['entryPrice']}
        return long_pos, short_pos
    except Exception as e:
        logger.error(f"[{ticker}] 포지션 조회 오류: {e}")
        return None, None

def calculate_order_amount(ticker, usdt_amount, price, leverage):
    """주문할 계약(contract) 수량을 계산합니다."""
    market = exchange.market(ticker)
    contract_size = float(market.get('contractSize', 1))
    position_value_usdt = usdt_amount * leverage
    coin_amount = position_value_usdt / price
    contract_amount = coin_amount / contract_size
    return contract_amount

# ==============================================================================
# 6. 메인 실행 로직
# ==============================================================================
def run_bot():
    """봇의 메인 실행 로직입니다."""
    logger.info("===== 봇 실행 시작 =====")

    for coin_ticker in INVEST_COIN_LIST:
        logger.info(f"\n--- [{coin_ticker}] 처리 시작 ---")
        
        # 1. 상태 데이터 초기화
        if coin_ticker not in BotDataDict:
            BotDataDict[coin_ticker] = {
                "long": {"entries": [], "buy_blocked_by_macd": False},
                "short": {"entries": [], "sell_blocked_by_macd": False}
            }
        
        long_pos_data = BotDataDict[coin_ticker]['long']
        short_pos_data = BotDataDict[coin_ticker]['short']

        # 2. 데이터 및 지표 계산
        df = fetch_ohlcv(coin_ticker, TIMEFRAME)
        if df.empty or len(df) < 35:
            logger.warning(f"[{coin_ticker}] 지표 계산을 위한 데이터가 부족합니다 (가져온 데이터 수: {len(df)}). 건너뜁니다.")
            continue

        df.name = coin_ticker # 다음 함수에서 사용하기 위해 df에 이름 부여
        df = calculate_indicators(df)
        df = calculate_adx(df)
        if USE_SHORT_STRATEGY:
            df = add_secondary_timeframe_indicators(df, SHORT_CONDITION_TIMEFRAME)
        df.dropna(inplace=True)

        if len(df) < 3:
            logger.warning(f"[{coin_ticker}] 지표 계산 후 데이터가 부족하여 건너뜁니다.")
            continue
            
        prev_candle = df.iloc[-2]
        prev_prev_candle = df.iloc[-3]
        current_price = df['close'].iloc[-1]

        # 3. 포지션 동기화 및 자산 확인
        cash = get_available_balance()
        long_pos_live, short_pos_live = get_current_position(coin_ticker)
        
        # --- (참고) 만약 로컬 데이터와 실제 포지션이 불일치할 경우, 여기서 동기화 로직을 추가할 수 있습니다 ---
        # 예: if long_pos_live is None and len(long_pos_data['entries']) > 0: ...

        # 4. 롱/숏 포지션 청산(Exit) 로직
        # 4-1. 롱 포지션 익절/손절 로직
        if len(long_pos_data['entries']) > 0:
            is_ma_cross_up = prev_candle['high'] > prev_candle['ma30'] and prev_prev_candle['close'] < prev_prev_candle['ma30']
            is_bb_upper_break = prev_candle['close'] > prev_candle['bb_upper']

            if is_ma_cross_up or is_bb_upper_break:
                try:
                    total_contracts_to_sell = sum(e['quantity'] for e in long_pos_data['entries'])
                    sell_params = {'reduceOnly': True}
                    exchange.create_market_sell_order(coin_ticker, total_contracts_to_sell, sell_params)
                    
                    reason = "30MA 상향 돌파" if is_ma_cross_up else "BB 상단 돌파"
                    msg = f"✅ [LONG EXIT] {coin_ticker} 포지션 전체 청산. 사유: {reason}"
                    logger.info(msg)
                    telegram_alert.SendMessage(FIRST_STRING + msg)

                    long_pos_data['entries'].clear()
                    save_bot_data()
                except Exception as e:
                    logger.error(f"[{coin_ticker}] 롱 포지션 청산 주문 실패: {e}")

        # 4-2. 숏 포지션 익절/손절 로직 (롱 로직 대칭으로 구현)
        if len(short_pos_data['entries']) > 0 and USE_SHORT_STRATEGY:
            is_ma_cross_down = prev_candle['low'] < prev_candle['ma30'] and prev_prev_candle['close'] > prev_prev_candle['ma30']
            is_bb_lower_break = prev_candle['close'] < prev_candle['bb_lower']

            if is_ma_cross_down or is_bb_lower_break:
                try:
                    total_contracts_to_buy = sum(e['quantity'] for e in short_pos_data['entries'])
                    buy_params = {'reduceOnly': True}
                    exchange.create_market_buy_order(coin_ticker, total_contracts_to_buy, buy_params)

                    reason = "30MA 하향 돌파" if is_ma_cross_down else "BB 하단 돌파"
                    msg = f"✅ [SHORT EXIT] {coin_ticker} 포지션 전체 청산. 사유: {reason}"
                    logger.info(msg)
                    telegram_alert.SendMessage(FIRST_STRING + msg)

                    short_pos_data['entries'].clear()
                    save_bot_data()
                except Exception as e:
                    logger.error(f"[{coin_ticker}] 숏 포지션 청산 주문 실패: {e}")
        
        # 5. 포지션 진입(Entry) 로직
        # 5-1. 롱 포지션 신규 진입 로직
        if len(long_pos_data['entries']) < MAX_LONG_BUY_COUNT:
            base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
            should_buy = False
            if base_buy_cond:
                if len(long_pos_data['entries']) == 0:
                    should_buy = True
                else:
                    # 추가 매수 조건 (RSI 리셋 또는 더 낮은 RSI)
                    last_entry_rsi = long_pos_data['entries'][-1]['trigger_rsi']
                    if prev_candle['rsi'] < last_entry_rsi - 2: # 간단하게 이전 RSI보다 2 낮을 때 추가 매수
                         should_buy = True
            
            # MACD 잠금 조건 확인
            if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] < 0:
                long_pos_data['buy_blocked_by_macd'] = True
            if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] > 0:
                 long_pos_data['buy_blocked_by_macd'] = False
            
            if should_buy and not long_pos_data['buy_blocked_by_macd']:
                try:
                    # 레버리지 설정
                    exchange.set_leverage(LEVERAGE, coin_ticker)
                    
                    # 매수 금액 계산
                    base_amount = cash * BASE_BUY_RATE
                    next_entry_num = len(long_pos_data['entries']) + 1
                    buy_collateral = get_buy_amount(base_amount, prev_candle['rsi'], next_entry_num) if USE_ADDITIVE_BUYING else base_amount

                    if cash < buy_collateral:
                        logger.warning(f"[{coin_ticker}] 롱 진입 시도 실패: 잔고 부족 (필요: {buy_collateral:.2f}, 보유: {cash:.2f})")
                    else:
                        # 주문 수량 계산 및 실행
                        amount_to_buy = calculate_order_amount(coin_ticker, buy_collateral, current_price, LEVERAGE)
                        exchange.create_market_buy_order(coin_ticker, amount_to_buy)

                        # 상태 저장
                        long_pos_data['entries'].append({
                            "price": current_price, "quantity": amount_to_buy,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "trigger_rsi": prev_candle['rsi']
                        })
                        save_bot_data()

                        msg = f"📈 [LONG ENTRY] {coin_ticker} {next_entry_num}차 매수. 가격: {current_price:.5f}, RSI: {prev_candle['rsi']:.2f}"
                        logger.info(msg)
                        telegram_alert.SendMessage(FIRST_STRING + msg)

                except Exception as e:
                    logger.error(f"[{coin_ticker}] 롱 포지션 진입 주문 실패: {e}")

        # 5-2. 숏 포지션 신규 진입 로직
        if USE_SHORT_STRATEGY and len(short_pos_data['entries']) < MAX_SHORT_BUY_COUNT:
            short_cond_tf = prev_candle.get('prev_tf_close_below_ma30', False) and \
                              prev_candle.get('prev_tf_macd_hist_neg', False) and \
                              not prev_candle.get('prev_tf_ma30_3day_rising', False)
            short_cond_15m = prev_candle['rsi'] >= SHORT_ENTRY_RSI

            if short_cond_tf and short_cond_15m:
                try:
                    # 레버리지 설정
                    exchange.set_leverage(LEVERAGE, coin_ticker)

                    # 매도 금액(증거금) 계산 (균등 분할)
                    sell_collateral = cash * BASE_BUY_RATE

                    if cash < sell_collateral:
                        logger.warning(f"[{coin_ticker}] 숏 진입 시도 실패: 잔고 부족 (필요: {sell_collateral:.2f}, 보유: {cash:.2f})")
                    else:
                        # 주문 수량 계산 및 실행
                        amount_to_sell = calculate_order_amount(coin_ticker, sell_collateral, current_price, LEVERAGE)
                        exchange.create_market_sell_order(coin_ticker, amount_to_sell)

                        # 상태 저장
                        short_pos_data['entries'].append({
                            "price": current_price, "quantity": amount_to_sell,
                            "timestamp": datetime.datetime.now().isoformat(),
                            "trigger_rsi": prev_candle['rsi']
                        })
                        save_bot_data()
                        
                        next_entry_num = len(short_pos_data['entries'])
                        msg = f"📉 [SHORT ENTRY] {coin_ticker} {next_entry_num}차 매도. 가격: {current_price:.5f}, RSI: {prev_candle['rsi']:.2f}"
                        logger.info(msg)
                        telegram_alert.SendMessage(FIRST_STRING + msg)

                except Exception as e:
                    logger.error(f"[{coin_ticker}] 숏 포지션 진입 주문 실패: {e}")

        logger.info(f"--- [{coin_ticker}] 처리 완료 ---")
        time.sleep(1) # API 요청 제한 방지

    logger.info("===== 봇 실행 종료 =====")


if __name__ == '__main__':
    # 프로그램 시작 시 알림
    telegram_alert.SendMessage(FIRST_STRING + "프로그램 시작")
    
    # 이 스크립트를 cron이나 작업 스케줄러에 등록하여 '15분'마다 실행되도록 설정해야 합니다.
    # 예: */15 * * * * python /path/to/GateIO_F_Grid_Danta_Operational.py
    run_bot()