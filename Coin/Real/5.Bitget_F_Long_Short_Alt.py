# -*- coding:utf-8 -*-
'''
골든크로스/데드크로스 롱숏 전략 - Bitget 운영 봇
- 1시간봉 기준 20이평, 120이평 크로스 매매
- 골든크로스: 롱 진입 (숏 청산)
- 데드크로스: 숏 진입 (롱 청산)
- 5분할 진입, 청산은 일괄
'''
import ccxt
import time
import pandas as pd
import json
import socket
import sys
import os
from datetime import datetime
import builtins

# 원본 print 함수 저장 및 타임스탬프 포함 print 함수 정의
_original_print = builtins.print

def timestamped_print(*args, **kwargs):
    """타임스탬프가 포함된 로그 출력 함수"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
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

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# 암호화된 액세스키와 시크릿키 복호화
Bitget_AccessKey = simpleEnDecrypt.decrypt(my_key.bitget_access_M)
Bitget_SecretKey = simpleEnDecrypt.decrypt(my_key.bitget_secret_M)
Bitget_Passphrase = simpleEnDecrypt.decrypt(my_key.bitget_passphrase_M)

# ==============================================================================
# 설정
# ==============================================================================
# 비트겟 계정 정보
ACCOUNT_LIST = [
    {
        "name": "BitgetMain",
        "access_key": Bitget_AccessKey,
        "secret_key": Bitget_SecretKey,
        "passphrase": Bitget_Passphrase,
        "leverage": 2,  # 레버리지 설정 (정수 1~10)
        "effective_leverage": 1.8  # 실제 주문 시 적용할 배수
    },
]

# 투자 종목 리스트 (사이클 기반 1/N 분배)
INVEST_COIN_LIST = [
    {'ticker': 'ADA/USDT:USDT', 'rate': 0.25},
    {'ticker': 'DOGE/USDT:USDT', 'rate': 0.25},
    {'ticker': 'SOL/USDT:USDT', 'rate': 0.25},
    {'ticker': 'AVAX/USDT:USDT', 'rate': 0.25},
]

# 전략 설정
SHORT_MA = 20            # 단기 이동평균
LONG_MA = 120            # 장기 이동평균
DAILY_MA = 115           # 일봉 장기 이동평균 (방향 필터용)
DAILY_MA_SHORT = 15      # 일봉 단기 이동평균 (듀얼 필터용)
SPLIT_COUNT = 1          # 분할 진입 횟수 (1=일괄진입, 2~5=분할진입)
INVEST_RATE = 0.99       # 전체 자금 중 투자 비율
FEE = 0.0006             # 수수료율 (0.06%)

# 듀얼 이평선 필터 설정 (20일선 + 115일선)
# True: 직전일 종가가 두 선 위 → 롱만, 두 선 아래 → 숏만, 사이 → 둘 다 가능
# False: 기존 115일선만 사용
DAILY_DUAL_MA_FILTER_ENABLED = True

# 부분 익절 설정
TAKE_PROFIT_ENABLED = True    # 부분 익절 로직 활성화 여부 (True: 적용, False: 미적용)

# 익절 레벨 설정 (전 캔들 종가 기준) - TAKE_PROFIT_ENABLED = True일 때만 적용
# profit_pct: 수익률 도달 시, sell_pct: 해당 시점 물량의 몇 %를 익절
TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 10},   # 5% 수익 시 10% 익절
    {'profit_pct': 10, 'sell_pct': 20},  # 10% 수익 시 20% 익절
    {'profit_pct': 20, 'sell_pct': 30},  # 20% 수익 시 30% 익절
    {'profit_pct': 30, 'sell_pct': 50},  # 30% 수익 시 50% 익절
]

# ==============================================================================
# 테스트 모드 설정
# ==============================================================================
# True: 시작/종료/일일요약 알림을 항상 발송 (테스트용)
# False: 오전 9시(한국 기준)에만 알림 발송 (운영용)
TEST_MODE = False

# ==============================================================================
# 헬퍼 함수
# ==============================================================================
def GetOhlcv(exchange, ticker, timeframe='1h', target_rows=150):
    """Bitget: OHLCV 데이터 가져오기 (여러 번 호출하여 충분한 데이터 수집)"""
    try:
        limit = 90  # Bitget은 한번에 90개까지만 반환
        all_ohlcv = []
        end_ms = None
        attempts = 0
        max_attempts = 10  # 최대 10번 시도 (90 * 10 = 900개까지 수집 가능)

        while len(all_ohlcv) < target_rows and attempts < max_attempts:
            params = {'limit': limit}
            if end_ms is not None:
                params['endTime'] = end_ms

            batch = exchange.fetch_ohlcv(ticker, timeframe, limit=limit, params=params)
            if not batch:
                print(f"[{ticker}] GetOhlcv: 배치 데이터 없음 (attempt {attempts})")
                break

            all_ohlcv = batch + all_ohlcv
            end_ms = batch[0][0] - 1
            attempts += 1
            
            print(f"[{ticker}] GetOhlcv: 배치 {attempts}번째, 받은 데이터 {len(batch)}개, 총 누적 {len(all_ohlcv)}개")

            if len(batch) < limit:
                print(f"[{ticker}] GetOhlcv: 더 이상 데이터 없음 (받은 개수 {len(batch)} < limit {limit})")
                break

            time.sleep(0.2)

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df.drop_duplicates(subset='datetime', keep='first', inplace=True)
        df.sort_values('datetime', inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        print(f"[{ticker}] GetOhlcv: 최종 데이터 {len(df)}개 반환")
        return df
    except Exception as e:
        print(f"GetOhlcv 오류 ({ticker}): {e}")
        return pd.DataFrame()


def GetCoinNowPrice(exchange, ticker):
    """현재 가격 조회"""
    try:
        return exchange.fetch_ticker(ticker)['last']
    except Exception as e:
        print(f"GetCoinNowPrice 오류 ({ticker}): {e}")
        return 0.0


def get_total_equity(exchange, coin_list):
    """총 자산 계산 (가용잔액 + 포지션 평가금액)
    
    API에서 제공하는 총 자산 값을 직접 사용
    """
    try:
        balance = exchange.fetch_balance(params={"type": "swap"})
        # Bitget API에서 제공하는 총 자산 (가용 + 포지션 평가 포함)
        # 'total'에 미실현 손익까지 포함된 값이 있음
        total_equity = float(balance['USDT']['total'])
        available = float(balance['USDT']['free'])
        print(f"총 자산: ${total_equity:.2f} (가용: ${available:.2f}, 포지션: ${total_equity - available:.2f})")
        return total_equity
        
    except Exception as e:
        print(f"총 자산 조회 오류: {e}")
        return 0


def check_golden_cross(df, short_ma, long_ma):
    """골든크로스 확인 (전전봉 vs 전봉 비교 → 전봉 마감 시 크로스 확정)"""
    if len(df) < 3:
        return False
    # 전전봉 MA
    prev2_short = df[f'ma_{short_ma}'].iloc[-3]
    prev2_long = df[f'ma_{long_ma}'].iloc[-3]
    # 전봉 MA
    prev_short = df[f'ma_{short_ma}'].iloc[-2]
    prev_long = df[f'ma_{long_ma}'].iloc[-2]
    
    return prev2_short <= prev2_long and prev_short > prev_long


def check_dead_cross(df, short_ma, long_ma):
    """데드크로스 확인 (전전봉 vs 전봉 비교 → 전봉 마감 시 크로스 확정)"""
    if len(df) < 3:
        return False
    # 전전봉 MA
    prev2_short = df[f'ma_{short_ma}'].iloc[-3]
    prev2_long = df[f'ma_{long_ma}'].iloc[-3]
    # 전봉 MA
    prev_short = df[f'ma_{short_ma}'].iloc[-2]
    prev_long = df[f'ma_{long_ma}'].iloc[-2]
    
    return prev2_short >= prev2_long and prev_short < prev_long


def get_daily_ma_direction(exchange, ticker, daily_ma_period):
    """일봉 이동평균 기준 방향 필터 (듀얼 필터 지원)
    
    DAILY_DUAL_MA_FILTER_ENABLED = True인 경우:
    - 직전일 종가 > 20MA AND 115MA → 'UP' (롱만 가능)
    - 직전일 종가 < 20MA AND 115MA → 'DOWN' (숏만 가능)
    - 직전일 종가가 두 선 사이 → 'BOTH' (롱숏 모두 가능)
    
    DAILY_DUAL_MA_FILTER_ENABLED = False인 경우:
    - 기존 로직: 115MA 위면 'UP', 아래면 'DOWN'
    """
    try:
        # 일봉 데이터를 충분히 가져오기 (MA 계산 + 오늘 캔들 제외 + 여유분)
        df_daily = GetOhlcv(exchange, ticker, '1d', target_rows=daily_ma_period + 30)
        
        print(f"[{ticker}] 일봉 데이터 수집: {len(df_daily)}개")
        
        if df_daily.empty:
            print(f"[{ticker}] 일봉 데이터 없음 - 기본값 UP 반환")
            return 'UP'
        
        # 오늘 캔들(미완성) 제외 - 마지막 행 삭제
        df_daily = df_daily.iloc[:-1]
        print(f"[{ticker}] 오늘 캔들 제외 후: {len(df_daily)}개")
        
        if len(df_daily) < daily_ma_period:
            print(f"[{ticker}] MA 계산을 위한 데이터 부족 ({len(df_daily)} < {daily_ma_period}) - 기본값 UP 반환")
            return 'UP'
        
        # 어제(마감된 캔들)부터 115일간의 MA 계산
        df_daily[f'ma_{daily_ma_period}'] = df_daily['close'].rolling(daily_ma_period).mean()
        
        # 20MA도 계산 (듀얼 필터용)
        df_daily[f'ma_{DAILY_MA_SHORT}'] = df_daily['close'].rolling(DAILY_MA_SHORT).mean()
        
        # 어제(마감된 캔들, 이제는 마지막 인덱스) 종가와 MA 비교
        yesterday_close = df_daily['close'].iloc[-1]
        yesterday_ma_115 = df_daily[f'ma_{daily_ma_period}'].iloc[-1]
        yesterday_ma_20 = df_daily[f'ma_{DAILY_MA_SHORT}'].iloc[-1]
        
        if pd.isna(yesterday_ma_115):
            print(f"[{ticker}] 115MA 값이 NaN - 기본값 UP 반환")
            return 'UP'
        
        # 듀얼 필터 모드
        if DAILY_DUAL_MA_FILTER_ENABLED:
            if pd.isna(yesterday_ma_20):
                # 20MA 없으면 기존 로직 사용
                direction = 'UP' if yesterday_close > yesterday_ma_115 else 'DOWN'
                print(f"[{ticker}] 어제 종가: {yesterday_close:.4f}, 115MA: {yesterday_ma_115:.4f} -> {direction}")
                return direction
            
            # 두 선 중 위/아래 값 구분
            upper_ma = max(yesterday_ma_20, yesterday_ma_115)
            lower_ma = min(yesterday_ma_20, yesterday_ma_115)
            
            if yesterday_close > upper_ma:
                # 종가가 두 선 모두 위에 → 롱만
                direction = 'UP'
            elif yesterday_close < lower_ma:
                # 종가가 두 선 모두 아래 → 숏만
                direction = 'DOWN'
            else:
                # 종가가 두 선 사이 → 롱숏 모두 가능
                direction = 'BOTH'
            
            print(f"[{ticker}] 어제 종가: {yesterday_close:.4f}, 20MA: {yesterday_ma_20:.4f}, 115MA: {yesterday_ma_115:.4f} -> {direction}")
            return direction
        else:
            # 기존 로직: 115MA만 사용
            direction = 'UP' if yesterday_close > yesterday_ma_115 else 'DOWN'
            print(f"[{ticker}] 어제 종가: {yesterday_close:.4f}, {daily_ma_period}MA: {yesterday_ma_115:.4f} -> {direction}")
            return direction
            
    except Exception as e:
        print(f"일봉 MA 조회 오류 ({ticker}): {e}")
        return 'UP'


# ==============================================================================
# 메인 트레이딩 로직
# ==============================================================================
def execute_trading_logic(account_info):
    """하나의 계정에 대한 트레이딩 로직 실행"""
    account_name = account_info['name']
    access_key = account_info['access_key']
    secret_key = account_info['secret_key']
    passphrase = account_info['passphrase']
    set_leverage = account_info['leverage']
    effective_leverage = account_info.get('effective_leverage', set_leverage)

    first_String = f"[5.Bitget 롱숏 {account_name}] {effective_leverage}배 "

    # 비트겟 객체 생성
    try:
        bitgetX = ccxt.bitget({
            'apiKey': access_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'defaultMarginMode': 'cross'
            }
        })
    except Exception as e:
        print(f"[{account_name}] ccxt 객체 생성 실패: {e}")
        telegram_alert.SendMessage(f"[{account_name}] ccxt 객체 생성 실패")
        return

    # 데이터 파일 경로
    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong":
        botdata_file_path = f"/var/AutoBot/json/5.Bitget_F_Long_Short_Alt_Data_{account_name}.json"
    else:
        botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', f'5.Bitget_F_Long_Short_Alt_Data_{account_name}.json')

    # 봇 데이터 로드
    try:
        with open(botdata_file_path, 'r') as f:
            BotDataDict = json.load(f)
    except FileNotFoundError:
        BotDataDict = {}
    except Exception as e:
        print(f"[{account_name}] 데이터 파일 로드 오류: {e}")
        BotDataDict = {}

    t = time.gmtime()
    hour_n = t.tm_hour
    min_n = t.tm_min
    day_n = t.tm_mday

    # 마지막 일일 요약 알림 시간 확인
    last_daily_alert_day = BotDataDict.get('LAST_DAILY_ALERT_DAY', 0)

    # 시작 알림 (TEST_MODE=True 또는 오전 9시 한국 기준)
    if TEST_MODE or (hour_n == 0 and min_n <= 2 and last_daily_alert_day != day_n):
        start_msg = f"{first_String} 시작"
        telegram_alert.SendMessage(start_msg)

    # 잔고 조회
    try:
        balance_check = bitgetX.fetch_balance(params={"type": "swap"})
        time.sleep(0.1)
        current_usdt_balance = float(balance_check['USDT']['free'])

        if current_usdt_balance < 10:
            print(f"[{account_name}] 잔고 부족 ({current_usdt_balance:.2f} USDT)")
            return

        print(f"[{account_name}] 현재 잔고: {current_usdt_balance:.2f} USDT")

    except Exception as e:
        print(f"[{account_name}] 잔고 조회 실패: {e}")
        return

    # 레버리지 설정 (모든 코인에 대해 미리 설정)
    print(f"[{account_name}] 레버리지 {set_leverage}배 설정 중...")
    for coin_data in INVEST_COIN_LIST:
        try:
            bitgetX.set_leverage(set_leverage, coin_data['ticker'], params={'marginCoin': 'USDT'})
            time.sleep(0.1)
        except Exception as e:
            print(f"[{account_name}] {coin_data['ticker']} 레버리지 설정 실패 (이미 설정됨 또는 오류): {e}")
    print(f"[{account_name}] 레버리지 설정 완료")

    # 메인 루프
    for coin_data in INVEST_COIN_LIST:
        coin_ticker = coin_data['ticker']
        coin_rate = coin_data['rate']

        # 키 초기화
        for key in ["_POSITION", "_ENTRY_COUNT", "_ENTRY_PRICE", "_POSITION_SIZE", "_TP_TRIGGERED"]:
            full_key = coin_ticker + key
            if full_key not in BotDataDict:
                if key == "_POSITION":
                    BotDataDict[full_key] = 0  # 0: 없음, 1: 롱, -1: 숏
                elif key == "_ENTRY_COUNT":
                    BotDataDict[full_key] = 0
                elif key == "_TP_TRIGGERED":
                    BotDataDict[full_key] = []  # 이미 실행된 TP 레벨 리스트
                else:
                    BotDataDict[full_key] = 0.0

        # 1시간봉 데이터 가져오기
        df = GetOhlcv(bitgetX, coin_ticker, '1h', target_rows=150)
        if df.empty or len(df) < LONG_MA + 2:
            print(f"[{account_name}] {coin_ticker} 데이터 부족")
            continue

        # 이동평균 계산
        df[f'ma_{SHORT_MA}'] = df['close'].rolling(SHORT_MA).mean()
        df[f'ma_{LONG_MA}'] = df['close'].rolling(LONG_MA).mean()
        df.dropna(inplace=True)

        if len(df) < 2:
            print(f"[{account_name}] {coin_ticker} 지표 계산 후 데이터 부족")
            continue

        now_price = GetCoinNowPrice(bitgetX, coin_ticker)
        if now_price == 0:
            print(f"[{account_name}] {coin_ticker} 현재가 조회 실패")
            continue

        # 현재 포지션 상태
        current_position = BotDataDict.get(coin_ticker + '_POSITION', 0)
        entry_count = BotDataDict.get(coin_ticker + '_ENTRY_COUNT', 0)
        entry_price = BotDataDict.get(coin_ticker + '_ENTRY_PRICE', 0)
        tp_triggered = BotDataDict.get(coin_ticker + '_TP_TRIGGERED', [])

        # 실제 포지션 확인
        try:
            positions = bitgetX.fetch_positions([coin_ticker])
            actual_position = 0
            actual_size = 0
            actual_entry_price = 0
            for pos in positions:
                if pos['symbol'] == coin_ticker and float(pos.get('contracts', 0)) != 0:
                    actual_size = abs(float(pos['contracts']))
                    actual_entry_price = float(pos.get('entryPrice', 0))
                    if pos['side'] == 'long':
                        actual_position = 1
                    elif pos['side'] == 'short':
                        actual_position = -1
            
            # 디버그: 실제 포지션 상태 출력
            print(f"[{account_name}] {coin_ticker} 포지션 조회: actual_position={actual_position}, actual_size={actual_size}, actual_entry_price={actual_entry_price}")
            
            # 실제 포지션이 없으면 JSON 데이터 동기화 (entry_price 포함)
            if actual_position == 0 or actual_size == 0:
                if current_position != 0 or entry_price != 0:
                    print(f"[{account_name}] {coin_ticker} 포지션 없음 감지 - JSON 데이터 동기화")
                    BotDataDict[coin_ticker + '_POSITION'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                    entry_price = 0
            else:
                # 진입가 업데이트 (실제 진입가로 덮어쓰기)
                if actual_entry_price > 0:
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = actual_entry_price
                    entry_price = actual_entry_price
        except Exception as e:
            print(f"[{account_name}] {coin_ticker} 포지션 조회 오류: {e}")
            actual_position = current_position
            actual_size = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0)

        # === 익절 체크 (전 캔들 종가 기준) - TAKE_PROFIT_ENABLED 옵션 확인 ===
        # 실제 포지션이 있는 경우에만 익절 체크 (actual_size가 0이면 스킵)
        if TAKE_PROFIT_ENABLED and actual_position != 0 and actual_size > 0 and entry_price > 0:
            prev_close = df['close'].iloc[-2]  # 전 캔들 종가
            
            # 수익률 계산 (ROE 기준, 레버리지 포함)
            if actual_position == 1:  # 롱
                profit_pct = ((prev_close - entry_price) / entry_price) * 100 * effective_leverage
            else:  # 숏
                profit_pct = ((entry_price - prev_close) / entry_price) * 100 * effective_leverage
            
            # 익절 레벨 체크
            for tp in TAKE_PROFIT_LEVELS:
                tp_profit = tp['profit_pct']
                tp_sell_pct = tp['sell_pct']
                
                # 이미 실행된 레벨은 스킵 (profit_pct를 키로 사용)
                if tp_profit in tp_triggered:
                    continue
                
                # 남은 물량이 없으면 스킵
                if actual_size <= 0:
                    print(f"[{account_name}] {coin_ticker} 익절 스킵: 남은 물량 없음")
                    break
                
                # 수익률 도달 시 익절 실행
                if profit_pct >= tp_profit:
                    sell_amount = actual_size * (tp_sell_pct / 100)
                    if sell_amount > 0:
                        try:
                            # 익절 전 실제 포지션 재확인
                            positions_check = bitgetX.fetch_positions([coin_ticker])
                            real_size = 0
                            real_position = 0
                            for pos in positions_check:
                                if pos['symbol'] == coin_ticker and float(pos.get('contracts', 0)) != 0:
                                    real_size = abs(float(pos['contracts']))
                                    if pos['side'] == 'long':
                                        real_position = 1
                                    elif pos['side'] == 'short':
                                        real_position = -1
                            
                            # 실제 포지션이 없으면 BotDataDict 동기화 후 스킵
                            if real_size == 0 or real_position == 0:
                                print(f"[{account_name}] {coin_ticker} 익절 스킵: 실제 포지션 없음 (BotDataDict 동기화)")
                                BotDataDict[coin_ticker + '_POSITION'] = 0
                                BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                                BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                                BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                                BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                                actual_size = 0
                                actual_position = 0
                                break
                            
                            # 실제 물량에 맞게 sell_amount 조정
                            sell_amount = min(sell_amount, real_size)
                            
                            # 3-3 파일과 동일한 Hedge Mode 청산 로직
                            # Long 청산: side='buy', holdSide='long'
                            # Short 청산: side='sell', holdSide='short'
                            hold_side = 'long' if real_position == 1 else 'short'
                            close_side = 'buy' if real_position == 1 else 'sell'
                            
                            bitgetX.create_order(
                                coin_ticker, 
                                'market', 
                                close_side, 
                                sell_amount, 
                                None, 
                                {'holdSide': hold_side, 'tradeSide': 'close'}
                            )
                            
                            # TP 레벨 기록 (profit_pct를 저장)
                            tp_triggered.append(tp_profit)
                            BotDataDict[coin_ticker + '_TP_TRIGGERED'] = tp_triggered
                            BotDataDict[coin_ticker + '_POSITION_SIZE'] = actual_size - sell_amount
                            
                            # 텔레그램 알림
                            tp_msg = (
                                f"💰 {first_String} {coin_ticker} 부분 익절 ({tp_profit}%)\n"
                                f"- 진입가: ${entry_price:.6f}\n"
                                f"- 전캔들 종가: ${prev_close:.6f}\n"
                                f"- 수익률: {profit_pct:.2f}%\n"
                                f"- 익절 비율: {tp_sell_pct}%\n"
                                f"- 익절 수량: {sell_amount:.6f}\n"
                                f"- 남은 수량: {actual_size - sell_amount:.6f}"
                            )
                            print(tp_msg)
                            telegram_alert.SendMessage(tp_msg)
                            
                            # 포지션 크기 업데이트
                            actual_size -= sell_amount
                            time.sleep(0.2)
                        except Exception as e:
                            error_str = str(e)
                            print(f"[{account_name}] {coin_ticker} {tp_profit}% 익절 실패: {e}")
                            
                            # 22002 에러 (No position to close) 발생 시 BotDataDict 동기화
                            if '22002' in error_str or 'No position to close' in error_str:
                                print(f"[{account_name}] {coin_ticker} 포지션 없음 감지 - BotDataDict 동기화")
                                BotDataDict[coin_ticker + '_POSITION'] = 0
                                BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                                BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                                BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                                BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                                actual_size = 0
                                actual_position = 0
                                # 에러 알림은 동기화 메시지로 대체
                                telegram_alert.SendMessage(f"{first_String} {coin_ticker} {tp_profit}% 익절 실패 - 포지션 없음 (동기화 완료)")
                                break
                            else:
                                telegram_alert.SendMessage(f"{first_String} {coin_ticker} {tp_profit}% 익절 실패: {e}")

        # 골든크로스 확인
        is_golden = check_golden_cross(df, SHORT_MA, LONG_MA)
        # 데드크로스 확인
        is_dead = check_dead_cross(df, SHORT_MA, LONG_MA)
        
        # 총른 로직 (현재 시세 기준)
        if df[f'ma_{SHORT_MA}'].iloc[-1] > df[f'ma_{LONG_MA}'].iloc[-1]:
            cross_status = "🟢 골든"
        else:
            cross_status = "🔴 데드"
        
        # 일봉 MA 방향 (UP: 롱 대기, DOWN: 숏 대기)
        daily_direction = get_daily_ma_direction(bitgetX, coin_ticker, DAILY_MA)
        daily_direction_emoji = "📈" if daily_direction == "UP" else "📉"
        daily_direction_text = f"{daily_direction_emoji} {daily_direction}"
        
        # 현재 포지션 정보
        position_text = '없음'
        if actual_position == 1:
            if entry_price > 0 and now_price > 0:
                position_profit = ((now_price - entry_price) / entry_price) * 100
                position_text = f"🟢 롱 ({position_profit:+.2f}%)"
            else:
                position_text = "🟢 롱"
        elif actual_position == -1:
            if entry_price > 0 and now_price > 0:
                position_profit = ((entry_price - now_price) / entry_price) * 100
                position_text = f"🔴 숏 ({position_profit:+.2f}%)"
            else:
                position_text = "🔴 숏"
        
        # 일일 요약 알림 (TEST_MODE=True 또는 아침 9시 한국 기준)
        if TEST_MODE or (hour_n == 0 and min_n <= 2 and last_daily_alert_day != day_n):
            alert_msg = (
                f"<{first_String} {coin_ticker}>\n"
                f"- 현재가: ${now_price:.6f}\n"
                f"- MA{SHORT_MA}: ${df[f'ma_{SHORT_MA}'].iloc[-1]:.6f}\n"
                f"- MA{LONG_MA}: ${df[f'ma_{LONG_MA}'].iloc[-1]:.6f}\n"
                f"- 일봉{DAILY_MA}MA: {daily_direction_text}\n"
                f"- 크로스형태: {cross_status}\n"
                f"- 현재 포지션: {position_text}"
            )
            telegram_alert.SendMessage(alert_msg)
            BotDataDict['LAST_DAILY_ALERT_DAY'] = day_n

        # === 골든크로스: 숏 청산 후 롱 진입 ===
        if is_golden:
            # 일봉 MA 방향 필터 확인
            daily_direction = get_daily_ma_direction(bitgetX, coin_ticker, DAILY_MA)
            
            # 숏 포지션이면 청산
            if actual_position == -1:
                try:
                    # 숏 청산 (3-3과 동일: side='sell', holdSide='short')
                    bitgetX.create_order(
                        coin_ticker, 'market', 'sell', actual_size,
                        None, {'holdSide': 'short', 'tradeSide': 'close'}
                    )
                    msg = f"{first_String} {coin_ticker} 숏 청산 (골든크로스)"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                    
                    BotDataDict[coin_ticker + '_POSITION'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                    actual_position = 0
                    entry_count = 0
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 숏 청산 실패: {e}")

            # 롱 진입 (분할) - 일봉 필터가 UP 또는 BOTH일 때
            if (actual_position == 0 or (actual_position == 1 and entry_count < SPLIT_COUNT)) and daily_direction in ['UP', 'BOTH']:
                try:
                    # 투자 금액 계산 (동적 할당: 현재 총 자산의 1/N)
                    # 가용잔액 + 포지션 평가금액 기준으로 손실/이익 반영
                    current_equity = get_total_equity(bitgetX, INVEST_COIN_LIST)
                    n_coins = len(INVEST_COIN_LIST)
                    dynamic_allocation = current_equity / n_coins
                    split_invest = dynamic_allocation * INVEST_RATE / SPLIT_COUNT
                    amount = (split_invest * effective_leverage) / now_price

                    # 롱 진입 (Hedge Mode: holdSide='long', tradeSide='open')
                    bitgetX.create_order(
                        coin_ticker, 'market', 'buy', amount,
                        None, {'holdSide': 'long', 'tradeSide': 'open'}
                    )

                    entry_count += 1
                    BotDataDict[coin_ticker + '_POSITION'] = 1
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = entry_count
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0) + amount
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = now_price
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []  # 신규 진입 시 익절 상태 초기화

                    # 상세 진입 알림
                    entry_msg = (
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🟢 {first_String}\n"
                        f"📌 {coin_ticker} 롱 진입\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"💵 진입가격: ${now_price:.6f}\n"
                        f"📊 진입량(코인): {amount:.6f}\n"
                        f"💰 진입량(USDT): ${split_invest:.2f}\n"
                        f"📍 포지션방향: 🟢 LONG\n"
                        f"━━━━━━━━━━━━━━━━━━━━"
                    )
                    print(entry_msg)
                    telegram_alert.SendMessage(entry_msg)
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 롱 진입 실패: {e}")
                    telegram_alert.SendMessage(f"{first_String} {coin_ticker} 롱 진입 실패: {e}")

        # === 데드크로스: 롱 청산 후 숏 진입 ===
        elif is_dead:
            # 일봉 MA 방향 필터 확인
            daily_direction = get_daily_ma_direction(bitgetX, coin_ticker, DAILY_MA)
            
            # 롱 포지션이면 청산
            if actual_position == 1:
                try:
                    # 롱 청산 (3-3과 동일: side='buy', holdSide='long')
                    bitgetX.create_order(
                        coin_ticker, 'market', 'buy', actual_size,
                        None, {'holdSide': 'long', 'tradeSide': 'close'}
                    )
                    msg = f"{first_String} {coin_ticker} 롱 청산 (데드크로스)"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                    
                    BotDataDict[coin_ticker + '_POSITION'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                    actual_position = 0
                    entry_count = 0
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 롱 청산 실패: {e}")

            # 숏 진입 (분할) - 일봉 필터가 DOWN 또는 BOTH일 때
            if (actual_position == 0 or (actual_position == -1 and entry_count < SPLIT_COUNT)) and daily_direction in ['DOWN', 'BOTH']:
                try:
                    # 투자 금액 계산 (동적 할당: 현재 총 자산의 1/N)
                    # 가용잔액 + 포지션 평가금액 기준으로 손실/이익 반영
                    current_equity = get_total_equity(bitgetX, INVEST_COIN_LIST)
                    n_coins = len(INVEST_COIN_LIST)
                    dynamic_allocation = current_equity / n_coins
                    split_invest = dynamic_allocation * INVEST_RATE / SPLIT_COUNT
                    amount = (split_invest * effective_leverage) / now_price

                    # 숏 진입 (Hedge Mode: holdSide='short', tradeSide='open')
                    bitgetX.create_order(
                        coin_ticker, 'market', 'sell', amount,
                        None, {'holdSide': 'short', 'tradeSide': 'open'}
                    )

                    entry_count += 1
                    BotDataDict[coin_ticker + '_POSITION'] = -1
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = entry_count
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0) + amount
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = now_price
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []  # 신규 진입 시 익절 상태 초기화

                    # 상세 진입 알림
                    entry_msg = (
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔴 {first_String}\n"
                        f"📌 {coin_ticker} 숏 진입\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"💵 진입가격: ${now_price:.6f}\n"
                        f"📊 진입량(코인): {amount:.6f}\n"
                        f"💰 진입량(USDT): ${split_invest:.2f}\n"
                        f"📍 포지션방향: 🔴 SHORT\n"
                        f"━━━━━━━━━━━━━━━━━━━━"
                    )
                    print(entry_msg)
                    telegram_alert.SendMessage(entry_msg)
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 숏 진입 실패: {e}")
                    telegram_alert.SendMessage(f"{first_String} {coin_ticker} 숏 진입 실패: {e}")

        # 보트 데이터 저장
        with open(botdata_file_path, 'w') as f:
            json.dump(BotDataDict, f, indent=4)

    # 종료 알림 (TEST_MODE=True 또는 오전 9시 한국 기준)
    if TEST_MODE or (hour_n == 0 and min_n <= 2 and last_daily_alert_day != day_n):
        end_msg = f"{first_String} 종료"
        telegram_alert.SendMessage(end_msg)


# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == '__main__':
    print("===== Bitget 골든/데드크로스 롱숏 봇 시작 =====")
    for account in ACCOUNT_LIST:
        print(f"\n--- {account['name']} 거래 시작 (레버리지: {account['leverage']}배) ---")
        execute_trading_logic(account)
    print("\n===== 모든 계정 거래 실행 완료 =====")
