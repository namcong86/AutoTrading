# -*- coding:utf-8 -*-
"""
파일이름: Final_GateIO_F_Grid_Danta_Operational.py
설명: [최종 수정] 볼린저밴드, RSI, MACD, ADX를 이용한 롱/숏 그리드 매매 전략
      - 테스트 스크립트 기반 로직에서 일부 동적 기능(밸런싱, 동적RSI) 제외
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
import telegram_alert # telegram_alert.py 파일이 필요합니다.

# ==============================================================================
# 1. 기본 설정 및 API 키
# ==============================================================================
# Gate.io API 키 (실제 키로 교체하고 보안상 환경변수 사용을 권장합니다)
GATEIO_ACCESS_KEY = "07a0ba2f6ed018fcb0fde7d08b58b40c"
GATEIO_SECRET_KEY = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"

# 알림 첫 문구
FIRST_STRING = "4.GateIO 단타 그리드봇"

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_grid_danta_v_final.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ==============================================================================
# 2. 전략 및 거래 설정 (테스트 스크립트 기반)
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
MAX_SHORT_BUY_COUNT = 5      # 최대 숏 분할매수 횟수
SHORT_ENTRY_RSI = 75         # 숏 포지션 진입을 위한 RSI 조건 값 (고정)

# 롱 포지션이 숏 포지션보다 이 횟수 이상 많고, 특정 조건 만족 시 추가 롱 진입 방지
LONG_ENTRY_LOCK_SHORT_COUNT_DIFF = 7

# --- 아래 3개 변수는 사용하지 않음 ---
# SHORT_RSI_ADJUSTMENT = 5
# SHORT_LONG_BALANCE_DIFF_ON_LONG_EXIT = 4
# SHORT_ENTRY_LOCK_LONG_COUNT_DIFF = 3

pcServerGb = socket.gethostname()
# 상태 저장 파일
if pcServerGb == "AutoBotCong":
    BOT_DATA_FILE_PATH = "/var/AutoBot/json/GateIO_F_Grid_Danta_FinalData.json"
else:
    BOT_DATA_FILE_PATH = "./GateIO_F_Grid_Danta_FinalData.json"


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
# 4. 데이터 처리 및 보조지표 계산 함수 (테스트 스크립트 기반)
# ==============================================================================
def fetch_ohlcv(ticker, timeframe, limit=300):
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

def add_secondary_timeframe_indicators(df_base, ticker, secondary_timeframe='1d'):
    """주어진 타임프레임으로 데이터를 리샘플링하고 지표를 원본 데이터프레임에 병합합니다."""
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

def get_rsi_level(rsi):
    """RSI 값에 따른 레벨을 반환합니다. (테스트 로직)"""
    if 20 < rsi <= 25: return 1
    if 15 < rsi <= 20: return 2
    if 10 < rsi <= 15: return 3
    if rsi <= 10: return 4
    return 0

def get_buy_amount(base_amount, rsi_value, entry_count):
    """RSI 레벨과 진입 차수에 따라 최종 매수 증거금을 계산합니다."""
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
        return balance.get('free', {}).get(settle_currency, 0)
    except Exception as e:
        logger.error(f"잔고 조회 오류: {e}")
        return 0

def get_average_price(entries):
    """진입 목록으로부터 평균 가격을 계산합니다."""
    if not entries:
        return 0
    total_quantity = sum(e['quantity'] for e in entries)
    if total_quantity == 0:
        return 0
    total_value = sum(e['price'] * e['quantity'] for e in entries)
    return total_value / total_quantity

def calculate_order_amount(ticker, usdt_amount, price, leverage):
    """주문할 계약(contract) 수량을 계산합니다."""
    market = exchange.market(ticker)
    contract_size = float(market.get('contractSize', 1))
    position_value_usdt = usdt_amount * leverage
    coin_amount = position_value_usdt / price
    contract_amount = coin_amount / contract_size
    return contract_amount

# ==============================================================================
# 6. 메인 실행 로직 (최종 수정 로직 적용)
# ==============================================================================
def run_bot():
    """봇의 메인 실행 로직입니다."""
    logger.info("===== 봇 실행 시작 (최종 수정 로직 적용) =====")

    for coin_ticker in INVEST_COIN_LIST:
        logger.info(f"\n--- [{coin_ticker}] 처리 시작 ---")
        
        # 1. 상태 데이터 초기화
        if coin_ticker not in BotDataDict:
            BotDataDict[coin_ticker] = {
                "long": {"entries": [], "buy_blocked_by_macd": False, "last_buy_timestamp": None},
                "short": {"entries": [], "sell_blocked_by_macd": False, "last_buy_timestamp": None}
            }
        
        long_pos_data = BotDataDict[coin_ticker]['long']
        short_pos_data = BotDataDict[coin_ticker]['short']

        # 2. 데이터 및 지표 계산
        df = fetch_ohlcv(coin_ticker, TIMEFRAME)
        if df.empty or len(df) < 50: 
            logger.warning(f"[{coin_ticker}] 지표 계산을 위한 데이터가 부족합니다 (가져온 데이터 수: {len(df)}). 건너뜁니다.")
            continue
        
        df = calculate_indicators(df)
        df = calculate_adx(df)
        if USE_SHORT_STRATEGY:
            df = add_secondary_timeframe_indicators(df, coin_ticker, SHORT_CONDITION_TIMEFRAME)
        df.dropna(inplace=True)

        if len(df) < 3:
            logger.warning(f"[{coin_ticker}] 지표 계산 후 데이터가 부족하여 건너뜁니다.")
            continue
            
        prev_candle = df.iloc[-2]
        prev_prev_candle = df.iloc[-3]
        current_price = df['close'].iloc[-1]
        logger.info(f"[{coin_ticker}] 현재 가격: {current_price:.5f}, 이전 봉 RSI: {prev_candle['rsi']:.2f}, MACD Hist: {prev_candle['macd_histogram']:.4f}")

        cash = get_available_balance()
        long_avg_price = get_average_price(long_pos_data['entries'])
        
        # MACD 잠금 해제 로직
        if USE_MACD_BUY_LOCK:
            if long_pos_data['buy_blocked_by_macd'] and prev_candle['macd_histogram'] > 0:
                long_pos_data['buy_blocked_by_macd'] = False
                logger.info("[롱] MACD 히스토그램 양수 전환. 매수 잠금 해제.")
            if USE_SHORT_STRATEGY and short_pos_data['sell_blocked_by_macd'] and prev_candle['macd_histogram'] < 0:
                short_pos_data['sell_blocked_by_macd'] = False
                logger.info("[숏] MACD 히스토그램 음수 전환. 매도 잠금 해제.")

        # 3. 롱 포지션 청산(Exit) 로직 (부분/전체 익절)
        if len(long_pos_data['entries']) > 0:
            entries_to_sell_indices = []
            sell_reason = ""
            
            is_ma_cross_up = prev_candle['high'] > prev_candle['ma30'] and prev_prev_candle['close'] < prev_prev_candle['ma30']
            is_bb_upper_break = prev_candle['close'] > prev_candle['bb_upper']

            if is_ma_cross_up:
                entries_to_sell_indices = [i for i, e in enumerate(long_pos_data['entries']) if e['price'] < prev_candle['ma30']]
                if entries_to_sell_indices: sell_reason = "30MA 상향 돌파 (부분 익절)"
            elif is_bb_upper_break:
                if current_price > long_avg_price:
                    entries_to_sell_indices = list(range(len(long_pos_data['entries'])))
                    sell_reason = "BB 상단 돌파 (전체 익절)"
                else: 
                    entries_to_sell_indices = [i for i, e in enumerate(long_pos_data['entries']) if current_price > e['price']]
                    if entries_to_sell_indices: sell_reason = "BB 상단 돌파 (부분 익절)"

            if entries_to_sell_indices:
                try:
                    sold_entries = [long_pos_data['entries'][i] for i in entries_to_sell_indices]
                    total_contracts_to_sell = sum(e['quantity'] for e in sold_entries)
                    
                    exchange.create_market_sell_order(coin_ticker, total_contracts_to_sell, {'reduceOnly': True})
                    
                    msg = f"✅ [LONG EXIT] {coin_ticker} 포지션 청산. 사유: {sell_reason}"
                    logger.info(msg)
                    telegram_alert.SendMessage(FIRST_STRING + msg)

                    for i in sorted(entries_to_sell_indices, reverse=True):
                        del long_pos_data['entries'][i]
                    
                    save_bot_data()
                    
                    # [밸런싱 로직] -> 제거됨

                except Exception as e:
                    logger.error(f"[{coin_ticker}] 롱 포지션 청산 주문 실패: {e}")
            else:
                logger.info(f"[{coin_ticker}] 롱 포지션 청산 조건 미충족. 대기합니다.")

        # 4. 롱 포지션 신규 진입 로직 (조건부 진입 및 숏 동시 정리)
        if len(long_pos_data['entries']) < MAX_LONG_BUY_COUNT:
            base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
            should_buy = False
            if base_buy_cond:
                if len(long_pos_data['entries']) == 0:
                    should_buy = True
                else:
                    last_buy_time_str = long_pos_data.get('last_buy_timestamp')
                    if last_buy_time_str:
                         last_buy_time = datetime.datetime.fromisoformat(last_buy_time_str)
                         reset_check_df = df[df.index > last_buy_time]
                         if not reset_check_df.empty and (reset_check_df['rsi'] > 25).any():
                             should_buy = True
                             logger.info("[롱 추가진입 조건] RSI 리셋 확인됨.")
                    if not should_buy and get_rsi_level(prev_candle['rsi']) > get_rsi_level(long_pos_data['entries'][-1]['trigger_rsi']):
                        should_buy = True
                        logger.info("[롱 추가진입 조건] RSI 레벨 심화 확인됨.")
            
            if should_buy:
                is_prev_day_close_below_ma = prev_candle.get('prev_tf_close_below_ma30', False)
                long_short_diff = len(long_pos_data['entries']) - len(short_pos_data['entries'])
                if is_prev_day_close_below_ma and long_short_diff >= LONG_ENTRY_LOCK_SHORT_COUNT_DIFF:
                    should_buy = False
                    logger.info(f"[롱 진입 잠금] 일봉 MA하락 및 롱/숏 개수차({long_short_diff})로 인해 진입이 잠깁니다.")

            if should_buy and not long_pos_data.get('buy_blocked_by_macd', False):
                if USE_SHORT_STRATEGY and len(short_pos_data['entries']) > 0:
                    entries_to_close_s_indices = [i for i, e in enumerate(short_pos_data['entries']) if e['price'] > current_price]
                    if entries_to_close_s_indices:
                        try:
                            closing_shorts = [short_pos_data['entries'][i] for i in entries_to_close_s_indices]
                            total_s_contracts_to_buy = sum(e['quantity'] for e in closing_shorts)
                            exchange.create_market_buy_order(coin_ticker, total_s_contracts_to_buy, {'reduceOnly': True})

                            msg = f"↔️ [연계 EXIT] 롱 진입 전, 수익중인 숏 포지션 {len(closing_shorts)}개 정리."
                            logger.info(msg)
                            telegram_alert.SendMessage(FIRST_STRING + msg)

                            for i in sorted(entries_to_close_s_indices, reverse=True):
                                del short_pos_data['entries'][i]
                        except Exception as e:
                            logger.error(f"[{coin_ticker}] 롱 진입 전 숏 포지션 정리 주문 실패: {e}")

                try:
                    exchange.set_leverage(LEVERAGE, coin_ticker)
                    base_amount = cash * BASE_BUY_RATE
                    next_entry_num = len(long_pos_data['entries']) + 1
                    buy_collateral = get_buy_amount(base_amount, prev_candle['rsi'], next_entry_num) if USE_ADDITIVE_BUYING else base_amount

                    if cash < buy_collateral:
                        logger.warning(f"[{coin_ticker}] 롱 진입 시도 실패: 잔고 부족")
                    else:
                        amount_to_buy = calculate_order_amount(coin_ticker, buy_collateral, current_price, LEVERAGE)
                        exchange.create_market_buy_order(coin_ticker, amount_to_buy)

                        now_iso = datetime.datetime.now().isoformat()
                        long_pos_data['entries'].append({
                            "price": current_price, "quantity": amount_to_buy,
                            "timestamp": now_iso, "trigger_rsi": prev_candle['rsi']
                        })
                        long_pos_data['last_buy_timestamp'] = now_iso
                        
                        if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] < 0:
                            long_pos_data['buy_blocked_by_macd'] = True
                            logger.info("[롱] MACD 히스토그램 음수. 매수 잠금 활성화.")
                        
                        save_bot_data()

                        msg = f"📈 [LONG ENTRY] {coin_ticker} {next_entry_num}차 매수. 가격: {current_price:.5f}, RSI: {prev_candle['rsi']:.2f}"
                        logger.info(msg)
                        telegram_alert.SendMessage(FIRST_STRING + msg)
                except Exception as e:
                    logger.error(f"[{coin_ticker}] 롱 포지션 진입 주문 실패: {e}")
            else:
                logger.info(f"[{coin_ticker}] 롱 포지션 진입 조건을 충족하지 못했습니다.")
        
        # 5. 숏 포지션 신규 진입 로직 (고정 RSI, 조건부 진입)
        if USE_SHORT_STRATEGY and len(short_pos_data['entries']) < MAX_SHORT_BUY_COUNT:
            # [숏 진입 잠금 로직] -> 제거됨
            
            cond_tf_close = prev_candle.get('prev_tf_close_below_ma30', False)
            cond_tf_macd = prev_candle.get('prev_tf_macd_hist_neg', False)
            cond_tf_ma_rising = not prev_candle.get('prev_tf_ma30_3day_rising', False)
            short_cond_tf = cond_tf_close and cond_tf_macd and cond_tf_ma_rising
            
            # [동적 RSI 계산] -> 제거됨. 고정 RSI 사용
            current_short_entry_rsi = SHORT_ENTRY_RSI
            short_cond_15m = prev_candle['rsi'] >= current_short_entry_rsi

            should_short = False
            if short_cond_tf and short_cond_15m:
                if len(short_pos_data['entries']) == 0:
                    should_short = True
                else:
                    last_short_time_str = short_pos_data.get('last_buy_timestamp')
                    if last_short_time_str:
                        last_short_time = datetime.datetime.fromisoformat(last_short_time_str)
                        reset_check_s_df = df[df.index > last_short_time]
                        if not reset_check_s_df.empty and (reset_check_s_df['rsi'] < current_short_entry_rsi).any():
                            should_short = True
                            logger.info("[숏 추가진입 조건] RSI 리셋 확인됨.")

            if should_short and not short_pos_data.get('sell_blocked_by_macd', False):
                try:
                    exchange.set_leverage(LEVERAGE, coin_ticker)
                    sell_collateral = cash * BASE_BUY_RATE

                    if cash < sell_collateral:
                        logger.warning(f"[{coin_ticker}] 숏 진입 시도 실패: 잔고 부족")
                    else:
                        amount_to_sell = calculate_order_amount(coin_ticker, sell_collateral, current_price, LEVERAGE)
                        exchange.create_market_sell_order(coin_ticker, amount_to_sell)

                        now_iso = datetime.datetime.now().isoformat()
                        short_pos_data['entries'].append({
                            "price": current_price, "quantity": amount_to_sell,
                            "timestamp": now_iso, "trigger_rsi": prev_candle['rsi']
                        })
                        short_pos_data['last_buy_timestamp'] = now_iso

                        if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] > 0:
                            short_pos_data['sell_blocked_by_macd'] = True
                            logger.info("[숏] MACD 히스토그램 양수. 매도 잠금 활성화.")

                        save_bot_data()
                        
                        next_entry_num = len(short_pos_data['entries'])
                        msg = f"📉 [SHORT ENTRY] {coin_ticker} {next_entry_num}차 매도. 가격: {current_price:.5f}, RSI: {prev_candle['rsi']:.2f}"
                        logger.info(msg)
                        telegram_alert.SendMessage(FIRST_STRING + msg)
                except Exception as e:
                    logger.error(f"[{coin_ticker}] 숏 포지션 진입 주문 실패: {e}")
            else:
                logger.info(f"[{coin_ticker}] 숏 포지션 진입 조건을 충족하지 못했습니다.")

        logger.info(f"--- [{coin_ticker}] 처리 완료 ---")
        time.sleep(1) 

    logger.info("===== 봇 실행 종료 =====")

if __name__ == '__main__':
    run_bot()