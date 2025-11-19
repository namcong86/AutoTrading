# -*- coding:utf-8 -*-
"""
파일이름: 5.Bitget_F_Long_Short_Alt_Test.py
설명: Bitget 선물 롱/숏 양방향 알트코인 전략 백테스트
      대상 코인: ETH, XRP, BNB, SOL, TRX, DOGE, ADA, HYPE
"""
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os

# ==============================================================================
# 1. 백테스트 환경 설정
# ==============================================================================
COIN_EXCHANGE = "bitget"
TEST_START_DATE = datetime.datetime(2025, 1, 1)
TEST_END_DATE = datetime.datetime.now()
INITIAL_CAPITAL = 100000
TIMEFRAME = '15m'
LEVERAGE = 8
STOP_LOSS_PNL_RATE = -1
INVEST_COIN_LIST = [
    "ETH/USDT",
    "XRP/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "TRX/USDT",
    "DOGE/USDT",
    "ADA/USDT",
    "HYPE/USDT"
]
FEE_RATE = 0.0006

BASE_BUY_RATE = 0.02
USE_DYNAMIC_BASE_BUY_AMOUNT = True
MONTHLY_WITHDRAWAL_RATE = 20

# 전략 스위치
USE_ADDITIVE_BUYING = False
USE_STRATEGIC_EXIT = False
USE_MACD_BUY_LOCK = True
USE_SHORT_STRATEGY = True
SHORT_CONDITION_TIMEFRAME = '1d'
MAX_LONG_BUY_COUNT = 10
MAX_SHORT_BUY_COUNT = 5
SHORT_ENTRY_RSI = 75
SHORT_RSI_ADJUSTMENT = 0
LONG_ENTRY_LOCK_SHORT_COUNT_DIFF = 6

# ==============================================================================
# 2. 데이터 처리 및 보조지표 계산 함수
# ==============================================================================
def load_data(ticker, timeframe, start_date, end_date):
    """로컬 CSV 파일 또는 API에서 데이터를 로드합니다."""
    print(f"--- [{ticker}] 데이터 준비 중 ---")
    csv_df = pd.DataFrame()
    safe_ticker_name = ticker.replace('/', '_').lower()
    csv_file = f"{safe_ticker_name}_{COIN_EXCHANGE}_{timeframe}.csv"

    # CSV 파일 로드 시도
    if os.path.exists(csv_file):
        try:
            print(f"'{csv_file}' 파일에서 데이터를 로드합니다.")
            csv_df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            if csv_df.index.tz is None:
                csv_df.index = csv_df.index.tz_localize('UTC')
            csv_df.index = csv_df.index.tz_convert(None)
        except Exception as e:
            print(f"오류: '{csv_file}' 파일 로드 중 오류 발생: {e}")
            csv_df = pd.DataFrame()

    # 데이터 필요 여부 확인
    fetch_from_api = False
    since = int(start_date.timestamp() * 1000)

    if not csv_df.empty:
        last_date_in_csv = csv_df.index.max()
        if last_date_in_csv < end_date:
            print(f"로컬 데이터가 최신이 아닙니다. API로 추가 데이터를 가져옵니다.")
            timeframe_duration = pd.to_timedelta(timeframe)
            since = int((last_date_in_csv + timeframe_duration).timestamp() * 1000)
            fetch_from_api = True
        else:
            print("로컬 데이터가 최신 상태입니다.")
    else:
        print("로컬 데이터가 없습니다. API로 데이터를 다운로드합니다.")
        fetch_from_api = True

    # API에서 데이터 가져오기
    api_df = pd.DataFrame()
    if fetch_from_api:
        try:
            print(f"API를 통해 {start_date} 이후 데이터를 다운로드합니다...")
            exchange = ccxt.bitget({'enableRateLimit': True})
            all_ohlcv = []
            
            while True:
                ohlcv = exchange.fetch_ohlcv(ticker, timeframe=timeframe, since=since, limit=1000)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + 1
                time.sleep(exchange.rateLimit / 1000)
                if datetime.datetime.fromtimestamp(ohlcv[-1][0] / 1000) >= end_date:
                    break

            if all_ohlcv:
                api_df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                api_df['timestamp'] = pd.to_datetime(api_df['timestamp'], unit='ms')
                api_df.set_index('timestamp', inplace=True)
                api_df = api_df[~api_df.index.duplicated(keep='last')]
                print(f"API를 통해 {len(api_df)}개의 새로운 데이터를 가져왔습니다.")
        except Exception as e:
            print(f"API 데이터 다운로드 오류: {e}")
            api_df = pd.DataFrame()

    # 데이터 병합
    if not csv_df.empty and not api_df.empty:
        df = pd.concat([csv_df, api_df])
        df = df[~df.index.duplicated(keep='last')]
        df.sort_index(inplace=True)
    elif not csv_df.empty:
        df = csv_df
    elif not api_df.empty:
        df = api_df
    else:
        print(f"경고: [{ticker}] 데이터를 가져올 수 없습니다.")
        return pd.DataFrame()

    # 기간 필터링
    df = df[(df.index >= start_date) & (df.index <= end_date)]
    print(f"최종 데이터: {len(df)}개 (기간: {df.index.min()} ~ {df.index.max()})")
    return df

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

def add_secondary_timeframe_indicators(df_base, ticker, secondary_timeframe='1d', start_date=None, end_date=None):
    """상위 타임프레임 지표를 추가합니다."""
    df_secondary = load_data(ticker, secondary_timeframe, start_date, end_date)
    if df_secondary.empty:
        df_base['prev_tf_close_below_ma30'] = False
        df_base['prev_tf_macd_hist_neg'] = False
        df_base['prev_tf_ma30_3day_rising'] = False
        df_base['prev_tf_adx'] = 0
        return df_base

    df_secondary['ma30'] = df_secondary['close'].rolling(window=30).mean()
    ema_fast_sec = df_secondary['close'].ewm(span=12, adjust=False).mean()
    ema_slow_sec = df_secondary['close'].ewm(span=26, adjust=False).mean()
    macd_sec = ema_fast_sec - ema_slow_sec
    df_secondary['macd_histogram'] = macd_sec - macd_sec.ewm(span=9, adjust=False).mean()
    df_secondary['ma30_3day_rising'] = (df_secondary['ma30'].diff(1) > 0) & (df_secondary['ma30'].diff(2) > 0) & (df_secondary['ma30'].diff(3) > 0)
    df_secondary = calculate_adx(df_secondary, window=14)

    df_secondary = df_secondary[['ma30', 'macd_histogram', 'ma30_3day_rising', 'adx']].copy()
    df_secondary.rename(columns={
        'ma30': 'prev_tf_ma30',
        'macd_histogram': 'prev_tf_macd_hist',
        'ma30_3day_rising': 'prev_tf_ma30_3day_rising',
        'adx': 'prev_tf_adx'
    }, inplace=True)

    df_base = df_base.join(df_secondary, how='left')
    df_base.fillna(method='ffill', inplace=True)
    df_base['prev_tf_close_below_ma30'] = df_base['close'] < df_base['prev_tf_ma30']
    df_base['prev_tf_macd_hist_neg'] = df_base['prev_tf_macd_hist'] < 0

    return df_base

# ==============================================================================
# 3. 백테스트 실행 함수 (로직은 추후 구현)
# ==============================================================================
def backtest_strategy():
    """백테스트 전략을 실행합니다."""
    print("===== Bitget 롱숏 알트 백테스트 시작 =====")
    
    results = {}
    
    for ticker in INVEST_COIN_LIST:
        print(f"\n--- [{ticker}] 백테스트 시작 ---")
        
        # TODO: 백테스트 로직 구현
        # 1. 데이터 로드 및 지표 계산
        # 2. 시뮬레이션 루프
        # 3. 성과 분석
        
        print(f"[{ticker}] 백테스트 로직 구현 대기중...")
        results[ticker] = {
            "total_return": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0
        }
    
    print("\n===== 백테스트 종료 =====")
    return results

# ==============================================================================
# 4. 메인 실행
# ==============================================================================
if __name__ == '__main__':
    results = backtest_strategy()
    print("\n===== 백테스트 결과 요약 =====")
    for ticker, result in results.items():
        print(f"{ticker}: {result}")
