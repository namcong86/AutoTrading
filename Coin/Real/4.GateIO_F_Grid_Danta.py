# -*- coding:utf-8 -*-
"""
파일이름: 4.GateIO_F_Grid_Danta.py
설명: RSI 기반 롱숏 분할매매 전략 (운영)
      - 일봉 이평선(120/20) 기준 3영역(LONG/MIDDLE/SHORT) 구분
      - RSI(14) 기반 진입 (25 이하 롱, 75 이상 숏)
      - 분할 익절 (5/10/20/30/50%)
      - 영역 변화에 따른 청산
"""
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import json
import sys
import os
import socket
import builtins
from datetime import datetime as dt_class
from enum import Enum

# 원본 print 함수 저장 및 타임스탬프 포함 print 함수 정의
_original_print = builtins.print

def timestamped_print(*args, **kwargs):
    """타임스탬프가 포함된 로그 출력 함수"""
    timestamp = dt_class.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

# 전역 print 함수를 타임스탬프 버전으로 교체
builtins.print = timestamped_print

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    sys.path.insert(0, "/var/AutoBot/Common")
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))

import telegram_alert
import myBinance
import ende_key
import my_key

# ==============================================================================
# 1. 기본 설정 및 API 키
# ==============================================================================
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

GATEIO_ACCESS_KEY = simpleEnDecrypt.decrypt(my_key.gateio_access_M)
GATEIO_SECRET_KEY = simpleEnDecrypt.decrypt(my_key.gateio_secret_M)

FIRST_STRING = "4.GateIO RSI 롱숏"

# ==============================================================================
# 2. 전략 설정
# ==============================================================================
TIMEFRAME = '15m'                     # 15분봉
LEVERAGE = 7
FEE_RATE = 0.001                      # 거래 수수료 (0.1%)

# 코인 리스트
COIN_LIST = ['BTC/USDT:USDT','ETH/USDT:USDT', 'XRP/USDT:USDT', 'DOGE/USDT:USDT', 'ADA/USDT:USDT']

# RSI 설정
RSI_LENGTH = 14
RSI_LONG_ENTRY = 25                   # 롱 진입 RSI
RSI_SHORT_ENTRY = 75                  # 숏 진입 RSI
RSI_LONG_RESET = 35                   # 롱 리셋 RSI
RSI_SHORT_RESET = 65                  # 숏 리셋 RSI

# 일봉 이평선 설정 (영역 구분용)
DAILY_MA_LONG = 120                   # 장기 이평선
DAILY_MA_SHORT = 20                   # 단기 이평선

# 분할 진입 설정
MAX_ENTRY_COUNT = 10                  # 최대 진입 회차

# 중립구간 50% 투자 옵션
HALF_INVEST_IN_MIDDLE = True

# 익절 설정 (레버리지 미적용 수익률 기준)
TAKE_PROFIT_ENABLED = True
TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 10},
    {'profit_pct': 10, 'sell_pct': 20},
    {'profit_pct': 20, 'sell_pct': 30},
    {'profit_pct': 30, 'sell_pct': 50},
    {'profit_pct': 50, 'sell_pct': 70},
]

# 월간 수익 알림 설정
FORCE_MONTHLY_REPORT = False

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    BOT_DATA_FILE_PATH = "/var/AutoBot/json/4.GateIO_F_Grid_Danta_Data.json"
else:
    BOT_DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'json', '4.GateIO_F_Grid_Danta_Data.json')

# ==============================================================================
# 3. 영역 타입 정의
# ==============================================================================
class ZoneType(Enum):
    LONG = 'LONG'       # 두 이평선 위
    MIDDLE = 'MIDDLE'   # 두 이평선 사이
    SHORT = 'SHORT'     # 두 이평선 아래

# ==============================================================================
# 4. CCXT 및 상태 파일 초기화
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
    print(f"[ERROR] 거래소 연결 실패: {e}")
    sys.exit()

try:
    with open(BOT_DATA_FILE_PATH, 'r') as f:
        content = f.read().strip()
        if content:
            BotDataDict = json.loads(content)
        else:
            BotDataDict = {}
            print(f"상태 파일이 비어있어 새로 생성합니다: {BOT_DATA_FILE_PATH}")
except FileNotFoundError:
    BotDataDict = {}
    print(f"상태 파일을 찾을 수 없어 새로 생성합니다: {BOT_DATA_FILE_PATH}")
    # 파일이 없을 경우 디렉토리 생성 및 빈 파일 저장
    os.makedirs(os.path.dirname(BOT_DATA_FILE_PATH), exist_ok=True)
    with open(BOT_DATA_FILE_PATH, 'w') as f:
        json.dump(BotDataDict, f, indent=4)
except json.JSONDecodeError:
    BotDataDict = {}
    print(f"상태 파일 JSON 파싱 오류, 새로 생성합니다: {BOT_DATA_FILE_PATH}")
    with open(BOT_DATA_FILE_PATH, 'w') as f:
        json.dump(BotDataDict, f, indent=4)

def save_bot_data():
    """상태 데이터를 JSON 파일에 저장합니다."""
    with open(BOT_DATA_FILE_PATH, 'w') as f:
        json.dump(BotDataDict, f, indent=4)

# ==============================================================================
# 5. 데이터 처리 및 보조지표 계산 함수
# ==============================================================================
def fetch_ohlcv(ticker, timeframe, limit=300):
    """OHLCV 데이터를 가져옵니다."""
    try:
        ohlcv = exchange.fetch_ohlcv(ticker, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"[ERROR] [{ticker}] OHLCV 데이터 조회 오류: {e}")
        return pd.DataFrame()

def calculate_rsi(df, period=14):
    """RSI 계산"""
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=period-1, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=period-1, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_zone(prev_close, ma_short, ma_long):
    """직전 일봉 종가 기준으로 영역 판단"""
    if pd.isna(ma_short) or pd.isna(ma_long):
        return ZoneType.MIDDLE
    
    upper_ma = max(ma_short, ma_long)
    lower_ma = min(ma_short, ma_long)
    
    if prev_close > upper_ma:
        return ZoneType.LONG
    elif prev_close < lower_ma:
        return ZoneType.SHORT
    else:
        return ZoneType.MIDDLE

def get_allowed_directions(zone):
    """영역별 진입 가능한 방향 반환"""
    if zone == ZoneType.LONG:
        return ['long']
    elif zone == ZoneType.SHORT:
        return ['short']
    else:
        return ['long', 'short']

def should_close_by_zone_change(pos_data, direction, current_zone):
    """영역 변화에 따른 청산 여부 판단"""
    start_zone_str = pos_data.get('start_zone')
    if not start_zone_str:
        return False
    
    start_zone = ZoneType(start_zone_str)
    visited_zone_str = pos_data.get('visited_zone')
    visited_zone = ZoneType(visited_zone_str) if visited_zone_str else None
    
    if direction == 'long':
        if start_zone == ZoneType.LONG:
            return current_zone == ZoneType.MIDDLE
        elif start_zone == ZoneType.MIDDLE:
            if current_zone == ZoneType.SHORT:
                return True
            if visited_zone == ZoneType.LONG and current_zone == ZoneType.MIDDLE:
                return True
    else:  # short
        if start_zone == ZoneType.SHORT:
            return current_zone == ZoneType.MIDDLE
        elif start_zone == ZoneType.MIDDLE:
            if current_zone == ZoneType.LONG:
                return True
            if visited_zone == ZoneType.SHORT and current_zone == ZoneType.MIDDLE:
                return True
    
    return False

# ==============================================================================
# 6. 거래 실행 및 관리 함수
# ==============================================================================
def get_available_balance(settle_currency='USDT'):
    """선물 계좌의 가용 잔고를 조회합니다."""
    try:
        balance = exchange.fetch_balance(params={'type': 'swap', 'settle': settle_currency.lower()})
        return balance.get('free', {}).get(settle_currency, 0)
    except Exception as e:
        print(f"[ERROR] 잔고 조회 오류: {e}")
        return 0

def get_total_equity():
    """총 자산 (가용잔고 + 포지션 가치) 조회"""
    try:
        balance = exchange.fetch_balance(params={'type': 'swap', 'settle': 'usdt'})
        return balance.get('total', {}).get('USDT', 0)
    except Exception as e:
        print(f"[ERROR] 총 자산 조회 오류: {e}")
        return get_available_balance()

def get_average_price(entries):
    """진입 목록으로부터 평균 가격을 계산합니다."""
    if not entries:
        return 0
    total_quantity = sum(e['quantity'] for e in entries)
    if total_quantity == 0:
        return 0
    total_value = sum(e['price'] * e['quantity'] for e in entries)
    return total_value / total_quantity

def get_total_quantity(entries):
    """진입 목록으로부터 총 수량을 계산합니다."""
    if not entries:
        return 0
    return sum(e['quantity'] for e in entries)

def get_total_collateral(entries):
    """진입 목록으로부터 총 담보금을 계산합니다."""
    if not entries:
        return 0
    return sum(e.get('collateral', 0) for e in entries)

def calculate_order_amount(ticker, usdt_amount, price, leverage):
    """주문할 계약(contract) 수량을 계산합니다."""
    market = exchange.market(ticker)
    contract_size = float(market.get('contractSize', 1))
    position_value_usdt = usdt_amount * leverage
    coin_amount = position_value_usdt / price
    contract_amount = coin_amount / contract_size
    return contract_amount

def get_actual_position(ticker):
    """거래소에서 실제 포지션 정보를 조회합니다."""
    try:
        positions = exchange.fetch_positions([ticker])
        result = {'long': 0, 'short': 0}
        for pos in positions:
            if pos['symbol'] == ticker:
                contracts = abs(float(pos.get('contracts', 0) or 0))
                if pos.get('side') == 'long':
                    result['long'] = contracts
                elif pos.get('side') == 'short':
                    result['short'] = contracts
        return result
    except Exception as e:
        print(f"[WARNING] [{ticker}] 실제 포지션 조회 실패: {e}")
        return None

# ==============================================================================
# 7. 메인 실행 로직
# ==============================================================================
def run_bot():
    """봇의 메인 실행 로직입니다."""
    print("===== 4 RSI 롱숏 분할매매 봇 실행 시작 =====")
    
    t = time.gmtime()
    hour_n = t.tm_hour
    min_n = t.tm_min
    day_n = t.tm_mday
    month_n = t.tm_mon
    
    # 월초 수익금 알림 (1일 오전 9시 = UTC 0시)
    if FORCE_MONTHLY_REPORT or (day_n == 1 and hour_n == 0 and min_n <= 5):
        now = dt_class.now()
        if month_n == 1:
            last_year = now.year - 1
            last_month_num = 12
        else:
            last_year = now.year
            last_month_num = month_n - 1
        
        current_balance = get_available_balance()
        profit_msg = f"📊 [{FIRST_STRING}] 월간 현황\n"
        profit_msg += f"• 기간: {last_year}-{last_month_num:02d}\n"
        profit_msg += f"• 현재 잔액: {current_balance:.2f} USDT"
        telegram_alert.SendMessage(profit_msg)
        print(profit_msg)
    
    for coin_ticker in COIN_LIST:
        print(f"\n--- [{coin_ticker}] 처리 시작 ---")
        
        # 1. 상태 데이터 초기화
        if coin_ticker not in BotDataDict:
            BotDataDict[coin_ticker] = {
                "long": {
                    "entries": [],
                    "start_zone": None,
                    "visited_zone": None,
                    "rsi_reset": True,
                    "tp_triggered": [False] * len(TAKE_PROFIT_LEVELS)
                },
                "short": {
                    "entries": [],
                    "start_zone": None,
                    "visited_zone": None,
                    "rsi_reset": True,
                    "tp_triggered": [False] * len(TAKE_PROFIT_LEVELS)
                }
            }
        
        long_pos_data = BotDataDict[coin_ticker]['long']
        short_pos_data = BotDataDict[coin_ticker]['short']
        
        # 오전 9시 일일 현황 알림
        daily_alert_key = f"{coin_ticker}_DAILY_ALERT_DAY"
        if hour_n == 0 and min_n <= 5 and BotDataDict.get(daily_alert_key) != day_n:
            long_count = len(long_pos_data['entries'])
            short_count = len(short_pos_data['entries'])
            long_avg = get_average_price(long_pos_data['entries'])
            short_avg = get_average_price(short_pos_data['entries'])
            
            status_msg = f"📊 [{FIRST_STRING}] 일일 현황\n"
            status_msg += f"• 코인: {coin_ticker}\n"
            status_msg += f"• 롱 포지션: {long_count}회차"
            if long_count > 0:
                status_msg += f" (평단: {long_avg:.6f})"
            status_msg += f"\n• 숏 포지션: {short_count}회차"
            if short_count > 0:
                status_msg += f" (평단: {short_avg:.6f})"
            status_msg += f"\n✅ 정상 작동 중"
            
            telegram_alert.SendMessage(status_msg)
            BotDataDict[daily_alert_key] = day_n
            save_bot_data()
        
        # 2. 시간봉 데이터 및 지표 계산
        df = fetch_ohlcv(coin_ticker, TIMEFRAME)
        if df.empty or len(df) < 50:
            print(f"[WARNING] [{coin_ticker}] 데이터가 부족합니다. 건너뜁니다.")
            continue
        
        df['rsi'] = calculate_rsi(df, RSI_LENGTH)
        df.dropna(inplace=True)
        
        if len(df) < 3:
            print(f"[WARNING] [{coin_ticker}] 지표 계산 후 데이터가 부족합니다.")
            continue
        
        prev_candle = df.iloc[-2]
        current_price = df['close'].iloc[-1]
        prev_rsi = prev_candle['rsi']
        
        # RSI 유효성 검사 (극단값은 진입 불가)
        rsi_valid = (
            not pd.isna(prev_rsi) and 
            prev_rsi > 1 and 
            prev_rsi < 99
        )
        
        print(f"[{coin_ticker}] 현재가: {current_price:.6f}, 이전 RSI: {prev_rsi:.2f}")
        
        # 3. 일봉 데이터로 영역 판단
        daily_df = fetch_ohlcv(coin_ticker, '1d', limit=150)
        current_zone = ZoneType.MIDDLE
        
        if not daily_df.empty and len(daily_df) >= DAILY_MA_LONG:
            daily_df['ma_short'] = daily_df['close'].rolling(window=DAILY_MA_SHORT).mean()
            daily_df['ma_long'] = daily_df['close'].rolling(window=DAILY_MA_LONG).mean()
            
            # 직전 일봉 (완성된 캔들) 사용
            last_daily = daily_df.iloc[-2]
            current_zone = get_zone(last_daily['close'], last_daily['ma_short'], last_daily['ma_long'])
        
        print(f"[{coin_ticker}] 현재 영역: {current_zone.value}")
        
        cash = get_available_balance()
        total_equity = get_total_equity()
        n_coins = len(COIN_LIST)
        
        # 4. 방문 영역 업데이트 (MIDDLE 시작 포지션용)
        if len(long_pos_data['entries']) > 0:
            if long_pos_data.get('start_zone') == 'MIDDLE':
                if current_zone in [ZoneType.LONG, ZoneType.SHORT]:
                    long_pos_data['visited_zone'] = current_zone.value
                    save_bot_data()
        
        if len(short_pos_data['entries']) > 0:
            if short_pos_data.get('start_zone') == 'MIDDLE':
                if current_zone in [ZoneType.LONG, ZoneType.SHORT]:
                    short_pos_data['visited_zone'] = current_zone.value
                    save_bot_data()
        
        # 5. 영역 변화에 따른 청산 체크
        if len(long_pos_data['entries']) > 0:
            if should_close_by_zone_change(long_pos_data, 'long', current_zone):
                try:
                    actual_pos = get_actual_position(coin_ticker)
                    if actual_pos and actual_pos['long'] > 0:
                        total_contracts = sum(e['quantity'] for e in long_pos_data['entries'])
                        close_contracts = min(total_contracts, actual_pos['long'])
                        
                        if close_contracts > 0:
                            avg_price = get_average_price(long_pos_data['entries'])
                            pnl_rate = (current_price - avg_price) / avg_price * LEVERAGE
                            total_collateral = get_total_collateral(long_pos_data['entries'])
                            pnl = total_collateral * pnl_rate
                            
                            exchange.create_market_sell_order(coin_ticker, close_contracts, {'reduceOnly': True})
                            
                            # 청산 후 가용잔액 조회
                            new_balance = get_available_balance()
                            
                            msg = f"💰 [{FIRST_STRING}] 롱 전체청산 (영역변화)\n"
                            msg += f"• 코인: {coin_ticker}\n"
                            msg += f"• 청산가: ${current_price:.6f}\n"
                            msg += f"• 수익률: {pnl_rate*100:+.2f}%\n"
                            msg += f"• 수익금: ${pnl:+.2f}\n"
                            msg += f"• 가용잔액: ${new_balance:.2f}"
                            print(msg)
                            telegram_alert.SendMessage(msg)
                            
                            # 포지션 초기화
                            long_pos_data['entries'] = []
                            long_pos_data['start_zone'] = None
                            long_pos_data['visited_zone'] = None
                            long_pos_data['rsi_reset'] = True
                            long_pos_data['tp_triggered'] = [False] * len(TAKE_PROFIT_LEVELS)
                            save_bot_data()
                except Exception as e:
                    print(f"[ERROR] [{coin_ticker}] 롱 청산 실패: {e}")
        
        if len(short_pos_data['entries']) > 0:
            if should_close_by_zone_change(short_pos_data, 'short', current_zone):
                try:
                    actual_pos = get_actual_position(coin_ticker)
                    if actual_pos and actual_pos['short'] > 0:
                        total_contracts = sum(e['quantity'] for e in short_pos_data['entries'])
                        close_contracts = min(total_contracts, actual_pos['short'])
                        
                        if close_contracts > 0:
                            avg_price = get_average_price(short_pos_data['entries'])
                            pnl_rate = (avg_price - current_price) / avg_price * LEVERAGE
                            total_collateral = get_total_collateral(short_pos_data['entries'])
                            pnl = total_collateral * pnl_rate
                            
                            exchange.create_market_buy_order(coin_ticker, close_contracts, {'reduceOnly': True})
                            
                            new_balance = get_available_balance()
                            
                            msg = f"💰 [{FIRST_STRING}] 숏 전체청산 (영역변화)\n"
                            msg += f"• 코인: {coin_ticker}\n"
                            msg += f"• 청산가: ${current_price:.6f}\n"
                            msg += f"• 수익률: {pnl_rate*100:+.2f}%\n"
                            msg += f"• 수익금: ${pnl:+.2f}\n"
                            msg += f"• 가용잔액: ${new_balance:.2f}"
                            print(msg)
                            telegram_alert.SendMessage(msg)
                            
                            short_pos_data['entries'] = []
                            short_pos_data['start_zone'] = None
                            short_pos_data['visited_zone'] = None
                            short_pos_data['rsi_reset'] = True
                            short_pos_data['tp_triggered'] = [False] * len(TAKE_PROFIT_LEVELS)
                            save_bot_data()
                except Exception as e:
                    print(f"[ERROR] [{coin_ticker}] 숏 청산 실패: {e}")
        
        # 6. 익절 체크
        if TAKE_PROFIT_ENABLED:
            # 롱 익절
            if len(long_pos_data['entries']) > 0:
                avg_price = get_average_price(long_pos_data['entries'])
                profit_pct = (current_price - avg_price) / avg_price * 100
                
                for i, tp in enumerate(TAKE_PROFIT_LEVELS):
                    if not long_pos_data['tp_triggered'][i] and profit_pct >= tp['profit_pct']:
                        try:
                            actual_pos = get_actual_position(coin_ticker)
                            if actual_pos and actual_pos['long'] > 0:
                                total_qty = get_total_quantity(long_pos_data['entries'])
                                close_qty = total_qty * (tp['sell_pct'] / 100)
                                close_qty = min(close_qty, actual_pos['long'])
                                
                                if close_qty > 0:
                                    total_collateral = get_total_collateral(long_pos_data['entries'])
                                    close_collateral = total_collateral * (tp['sell_pct'] / 100)
                                    pnl_rate = (current_price - avg_price) / avg_price * LEVERAGE
                                    pnl = close_collateral * pnl_rate
                                    
                                    exchange.create_market_sell_order(coin_ticker, close_qty, {'reduceOnly': True})
                                    
                                    long_pos_data['tp_triggered'][i] = True
                                    
                                    # 부분 청산 반영
                                    ratio = 1 - (tp['sell_pct'] / 100)
                                    for entry in long_pos_data['entries']:
                                        entry['quantity'] *= ratio
                                        entry['collateral'] = entry.get('collateral', 0) * ratio
                                    
                                    save_bot_data()
                                    
                                    msg = f"💰 [{FIRST_STRING}] 롱 익절 TP{i+1} ({tp['sell_pct']}%)\n"
                                    msg += f"• 코인: {coin_ticker}\n"
                                    msg += f"• 가격: ${current_price:.6f}\n"
                                    msg += f"• 수익률: {pnl_rate*100:+.2f}%\n"
                                    msg += f"• 수익금: ${pnl:+.2f}"
                                    print(msg)
                                    telegram_alert.SendMessage(msg)
                        except Exception as e:
                            print(f"[ERROR] [{coin_ticker}] 롱 익절 실패: {e}")
            
            # 숏 익절
            if len(short_pos_data['entries']) > 0:
                avg_price = get_average_price(short_pos_data['entries'])
                profit_pct = (avg_price - current_price) / avg_price * 100
                
                for i, tp in enumerate(TAKE_PROFIT_LEVELS):
                    if not short_pos_data['tp_triggered'][i] and profit_pct >= tp['profit_pct']:
                        try:
                            actual_pos = get_actual_position(coin_ticker)
                            if actual_pos and actual_pos['short'] > 0:
                                total_qty = get_total_quantity(short_pos_data['entries'])
                                close_qty = total_qty * (tp['sell_pct'] / 100)
                                close_qty = min(close_qty, actual_pos['short'])
                                
                                if close_qty > 0:
                                    total_collateral = get_total_collateral(short_pos_data['entries'])
                                    close_collateral = total_collateral * (tp['sell_pct'] / 100)
                                    pnl_rate = (avg_price - current_price) / avg_price * LEVERAGE
                                    pnl = close_collateral * pnl_rate
                                    
                                    exchange.create_market_buy_order(coin_ticker, close_qty, {'reduceOnly': True})
                                    
                                    short_pos_data['tp_triggered'][i] = True
                                    
                                    ratio = 1 - (tp['sell_pct'] / 100)
                                    for entry in short_pos_data['entries']:
                                        entry['quantity'] *= ratio
                                        entry['collateral'] = entry.get('collateral', 0) * ratio
                                    
                                    save_bot_data()
                                    
                                    msg = f"💰 [{FIRST_STRING}] 숏 익절 TP{i+1} ({tp['sell_pct']}%)\n"
                                    msg += f"• 코인: {coin_ticker}\n"
                                    msg += f"• 가격: ${current_price:.6f}\n"
                                    msg += f"• 수익률: {pnl_rate*100:+.2f}%\n"
                                    msg += f"• 수익금: ${pnl:+.2f}"
                                    print(msg)
                                    telegram_alert.SendMessage(msg)
                        except Exception as e:
                            print(f"[ERROR] [{coin_ticker}] 숏 익절 실패: {e}")
        
        # 7. RSI 리셋 체크
        if not long_pos_data.get('rsi_reset', True) and prev_rsi > RSI_LONG_RESET:
            long_pos_data['rsi_reset'] = True
            save_bot_data()
        if not short_pos_data.get('rsi_reset', True) and prev_rsi < RSI_SHORT_RESET:
            short_pos_data['rsi_reset'] = True
            save_bot_data()
        
        # 8. 진입 조건 체크
        allowed = get_allowed_directions(current_zone)
        entry_count_long = len(long_pos_data['entries'])
        entry_count_short = len(short_pos_data['entries'])
        
        # 진입 금액 계산 (총자산 / 코인수 / 최대회차)
        base_entry_amount = total_equity / n_coins / MAX_ENTRY_COUNT
        
        # 롱 진입
        if 'long' in allowed and entry_count_long < MAX_ENTRY_COUNT and rsi_valid:
            if prev_rsi <= RSI_LONG_ENTRY:
                can_enter = False
                if entry_count_long == 0:
                    can_enter = True
                elif long_pos_data.get('rsi_reset', True):
                    can_enter = True
                
                if can_enter:
                    try:
                        is_middle = (current_zone == ZoneType.MIDDLE)
                        collateral = base_entry_amount
                        if is_middle and HALF_INVEST_IN_MIDDLE:
                            collateral *= 0.5
                        
                        if cash >= collateral:
                            leverage_params = {'settle': 'usdt', 'marginMode': 'cross'}
                            exchange.set_leverage(LEVERAGE, coin_ticker, params=leverage_params)
                            
                            amount = calculate_order_amount(coin_ticker, collateral, current_price, LEVERAGE)
                            exchange.create_market_buy_order(coin_ticker, amount)
                            
                            now_iso = datetime.datetime.now().isoformat()
                            long_pos_data['entries'].append({
                                "price": current_price,
                                "quantity": amount,
                                "collateral": collateral,
                                "timestamp": now_iso,
                                "trigger_rsi": prev_rsi
                            })
                            long_pos_data['rsi_reset'] = False
                            
                            if entry_count_long == 0:
                                long_pos_data['start_zone'] = current_zone.value
                                long_pos_data['visited_zone'] = None
                            
                            # 매 진입마다 TP 리셋 (새 평단가 기준으로 TP1부터 다시)
                            long_pos_data['tp_triggered'] = [False] * len(TAKE_PROFIT_LEVELS)
                            
                            save_bot_data()
                            
                            new_avg = get_average_price(long_pos_data['entries'])
                            new_qty = get_total_quantity(long_pos_data['entries'])
                            zone_info = " [중립구간 50%]" if is_middle and HALF_INVEST_IN_MIDDLE else ""
                            
                            msg = f"📈 [{FIRST_STRING}] 롱 진입 ({entry_count_long+1}차){zone_info}\n"
                            msg += f"• 코인: {coin_ticker}\n"
                            msg += f"• 가격: ${current_price:.6f}\n"
                            msg += f"• 수량: {amount:.4f}\n"
                            msg += f"• 금액: ${collateral:.2f}\n"
                            msg += f"• RSI: {prev_rsi:.2f}\n"
                            msg += f"• 영역: {current_zone.value}\n"
                            msg += f"• 평단가: ${new_avg:.6f}\n"
                            msg += f"• 총수량: {new_qty:.4f}"
                            print(msg)
                            telegram_alert.SendMessage(msg)
                        else:
                            print(f"[WARNING] [{coin_ticker}] 롱 진입 실패: 잔고 부족")
                    except Exception as e:
                        print(f"[ERROR] [{coin_ticker}] 롱 진입 실패: {e}")
        
        # 숏 진입
        if 'short' in allowed and entry_count_short < MAX_ENTRY_COUNT and rsi_valid:
            if prev_rsi >= RSI_SHORT_ENTRY:
                can_enter = False
                if entry_count_short == 0:
                    can_enter = True
                elif short_pos_data.get('rsi_reset', True):
                    can_enter = True
                
                if can_enter:
                    try:
                        is_middle = (current_zone == ZoneType.MIDDLE)
                        collateral = base_entry_amount
                        if is_middle and HALF_INVEST_IN_MIDDLE:
                            collateral *= 0.5
                        
                        if cash >= collateral:
                            leverage_params = {'settle': 'usdt', 'marginMode': 'cross'}
                            exchange.set_leverage(LEVERAGE, coin_ticker, params=leverage_params)
                            
                            amount = calculate_order_amount(coin_ticker, collateral, current_price, LEVERAGE)
                            exchange.create_market_sell_order(coin_ticker, amount)
                            
                            now_iso = datetime.datetime.now().isoformat()
                            short_pos_data['entries'].append({
                                "price": current_price,
                                "quantity": amount,
                                "collateral": collateral,
                                "timestamp": now_iso,
                                "trigger_rsi": prev_rsi
                            })
                            short_pos_data['rsi_reset'] = False
                            
                            if entry_count_short == 0:
                                short_pos_data['start_zone'] = current_zone.value
                                short_pos_data['visited_zone'] = None
                            
                            # 매 진입마다 TP 리셋 (새 평단가 기준으로 TP1부터 다시)
                            short_pos_data['tp_triggered'] = [False] * len(TAKE_PROFIT_LEVELS)
                            
                            save_bot_data()
                            
                            new_avg = get_average_price(short_pos_data['entries'])
                            new_qty = get_total_quantity(short_pos_data['entries'])
                            zone_info = " [중립구간 50%]" if is_middle and HALF_INVEST_IN_MIDDLE else ""
                            
                            msg = f"📉 [{FIRST_STRING}] 숏 진입 ({entry_count_short+1}차){zone_info}\n"
                            msg += f"• 코인: {coin_ticker}\n"
                            msg += f"• 가격: ${current_price:.6f}\n"
                            msg += f"• 수량: {amount:.4f}\n"
                            msg += f"• 금액: ${collateral:.2f}\n"
                            msg += f"• RSI: {prev_rsi:.2f}\n"
                            msg += f"• 영역: {current_zone.value}\n"
                            msg += f"• 평단가: ${new_avg:.6f}\n"
                            msg += f"• 총수량: {new_qty:.4f}"
                            print(msg)
                            telegram_alert.SendMessage(msg)
                        else:
                            print(f"[WARNING] [{coin_ticker}] 숏 진입 실패: 잔고 부족")
                    except Exception as e:
                        print(f"[ERROR] [{coin_ticker}] 숏 진입 실패: {e}")
        
        print(f"--- [{coin_ticker}] 처리 완료 ---")
        time.sleep(1)
    
    print("===== 봇 실행 종료 =====")

if __name__ == '__main__':
    run_bot()
