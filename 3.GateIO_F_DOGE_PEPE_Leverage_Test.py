# -*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Gate.io ccxt 버전 (수정됨)
pip3 install --upgrade ccxt==4.2.19 (또는 최신 안정 버전)
이렇게 버전을 맞춰주세요! (ccxt 버전은 호환성에 따라 조절 필요)
봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요! (Gate.io 계정 설정)
https://blog.naver.com/zacra/222662884649 (참고용 바이낸스 헤지모드 설명)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

관련 포스팅
https://blog.naver.com/zacra/223449598379
위 포스팅을 꼭 참고하세요!!!
'''

import ccxt
import time
import pandas as pd
import datetime
import re
import os
import socket # <<< 코드 추가

# GUI 및 차트 연동을 위한 라이브러리
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import font_manager, rc

# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 폰트 및 마이너스 기호 설정 (최종 수정본) ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
try:
    # 1. 한글 폰트 경로 설정
    if os.name == 'nt': # Windows OS
        font_path = "c:/Windows/Fonts/malgun.ttf"
    elif os.name == 'posix': # Mac OS
        font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    else:
        font_path = None

    if font_path and os.path.exists(font_path):
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        mpl.rcParams['font.family'] = font_name
    else:
        # 폰트가 없는 경우 기본값으로 DejaVu Sans 사용
        mpl.rcParams['font.family'] = 'DejaVu Sans'
        print("지정된 한글 폰트를 찾을 수 없어 기본 폰트로 설정됩니다.")

    # 2. 마이너스 기호 및 수학 기호 설정
    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

except Exception as e:
    print(f"폰트 설정 중 오류 발생: {e}")
    # 예외 발생 시 안전한 기본값으로 재설정
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================


# --- 함수 및 기본 설정 ---

def ms_to_utc_str(timestamp_ms):
    return datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def GetOhlcv2(exchange_obj, ticker_symbol, time_period, year=2019, month=1, day=1, hour=0, minute=0):
    start_date_dt = datetime.datetime(year, month, day, hour, minute, tzinfo=datetime.timezone.utc)
    current_since_ms = int(start_date_dt.timestamp() * 1000)
    all_ohlcv_data = []
    now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    if time_period == '1d': calculated_interval_ms = 24 * 60 * 60 * 1000
    elif time_period == '1h': calculated_interval_ms = 60 * 60 * 1000
    elif time_period == '5m': calculated_interval_ms = 5 * 60 * 1000
    else: calculated_interval_ms = 24 * 60 * 60 * 1000
    while True:
        if current_since_ms >= now_ms:
            print(f"요청 시작 시간 {ms_to_utc_str(current_since_ms)} ({ticker_symbol})이 현재 또는 미래입니다. 데이터 수집을 중단합니다.")
            break
        try:
            ohlcv_batch = exchange_obj.fetch_ohlcv(ticker_symbol, time_period, since=current_since_ms)
            if not ohlcv_batch:
                print(f"{ticker_symbol}의 {ms_to_utc_str(current_since_ms)} UTC 이후 데이터가 없습니다.")
                break
            all_ohlcv_data.extend(ohlcv_batch)
            if len(ohlcv_batch) > 1:
                calculated_interval_ms = ohlcv_batch[1][0] - ohlcv_batch[0][0]
            last_candle_ts = ohlcv_batch[-1][0]
            next_fetch_since_ms = last_candle_ts + calculated_interval_ms
            print(f"Get Data for {ticker_symbol}... Last: {ms_to_utc_str(last_candle_ts)}, Next since: {ms_to_utc_str(next_fetch_since_ms)} UTC")
            if next_fetch_since_ms >= now_ms:
                print(f"{ticker_symbol}의 다음 'since' ({ms_to_utc_str(next_fetch_since_ms)})가 미래입니다. 추가 가져오기를 중단합니다.")
                break
            current_since_ms = next_fetch_since_ms
            time.sleep(getattr(exchange_obj, 'rateLimit', 300) / 1000)
        except Exception as e:
            print(f"데이터 수집 중 오류 발생 {ticker_symbol}: {e}")
            break
    if not all_ohlcv_data:
        return pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df = pd.DataFrame(all_ohlcv_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df = df.set_index('datetime').sort_index()
    df = df[~df.index.duplicated(keep='first')]
    return df

# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 매매 조건 함수 (신규 추가 및 정리) ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
def is_doji_candle(open_price, close_price, high_price, low_price):
    """캔들이 도지 형태인지 확인하는 함수"""
    candle_range = high_price - low_price
    if candle_range == 0: return False
    body_size = abs(open_price - close_price)
    return body_size / candle_range <= 0.1

def check_sell_conditions(df_coin, i, RevenueRate):
    """매도 조건들을 확인하고 매도 여부를 bool 값으로 반환하는 함수"""
    
    # --- 기본 매도 조건 ---
    # 조건 1: 전전일 대비 전일 고점과 저점이 모두 하락
    cond_sell_price_fall = (df_coin['high'].iloc[i-2] > df_coin['high'].iloc[i-1] and 
                            df_coin['low'].iloc[i-2] > df_coin['low'].iloc[i-1])
    
    # 조건 2: 2거래일 연속 음봉
    cond_sell_two_red = (df_coin['open'].iloc[i-1] > df_coin['close'].iloc[i-1] and 
                         df_coin['open'].iloc[i-2] > df_coin['close'].iloc[i-2])
    
    # 조건 3: 현재 수익률이 마이너스
    cond_sell_is_losing = (RevenueRate < 0)
    
    # --- 매도 보류 조건 ---
    # 예외 1: 강한 상승 추세일 경우 매도 보류 (RSI MA와 3일 이평선 동시 상승)
    except_sell_strong_up = (df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and 
                             df_coin['3ma'].iloc[i-2] < df_coin['3ma'].iloc[i-1])
    
    # --- 추가 매도 조건 ---
    # 조건 4: 2거래일 연속 도지 캔들 발생
    is_doji_1 = is_doji_candle(df_coin['open'].iloc[i-1], df_coin['close'].iloc[i-1], df_coin['high'].iloc[i-1], df_coin['low'].iloc[i-1])
    is_doji_2 = is_doji_candle(df_coin['open'].iloc[i-2], df_coin['close'].iloc[i-2], df_coin['high'].iloc[i-2], df_coin['low'].iloc[i-2])
    cond_sell_dojis = (is_doji_1 and is_doji_2)

    # --- 최종 결정 ---
    # 기본 매도 조건 중 하나라도 만족하고, 매도 보류 조건이 아닐 경우
    sell_main_condition = (cond_sell_price_fall or cond_sell_two_red or cond_sell_is_losing) and not except_sell_strong_up
    
    # 기본 매도 조건 또는 추가 매도 조건을 만족하면 최종 매도 결정
    should_sell = sell_main_condition or cond_sell_dojis
    
    return should_sell

def check_buy_conditions(df_coin, i):
    """매수 조건들을 확인하고 매수 여부를 bool 값으로 반환하는 함수"""
    
    # --- 기본 매수 조건 ---
    # 조건 1: 2거래일 연속 양봉
    cond_buy_two_green = (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and 
                          df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2])
    
    # 조건 2: 전일 종가 및 고가가 전전일보다 높음
    cond_buy_price_up = (df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and 
                         df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1])
    
    # 조건 3: 단기 이평선(7, 20) 상승 추세
    cond_buy_short_ma_up = (df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and 
                            df_coin['20ma'].iloc[i-2] <= df_coin['20ma'].iloc[i-1])
    
    # 조건 4: 중기 이평선(30) 기울기가 급격한 하락이 아님
    cond_buy_mid_ma_stable = (df_coin['30ma_slope'].iloc[i-1] > -2)
    
    # 조건 5: RSI 이동평균 상승 추세
    cond_buy_rsi_up = (df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1])
    
    # --- 필터링 조건 ---
    # 필터 1: 전일 급등(50% 이상 상승)하지 않았을 것
    filter_no_sudden_surge = (df_coin['change'].iloc[i-1] < 0.5)

    # 필터 2: 200일 이평선 위에 있을 경우 추가 조건 검사
    is_above_200ma = df_coin['close'].iloc[i-1] > df_coin['200ma'].iloc[i-1]
    
    # 200일선 위에서의 추가 필터 기본값 설정 (200일선 아래일 경우 항상 통과)
    filter_ma50_not_declining = True
    cond_no_long_upper_shadow = True
    cond_body_over_15_percent = True
    
    if is_above_200ma:
        # 필터 2-1: 50일 이평선이 하락하고 있지 않음
        filter_ma50_not_declining = (df_coin['50ma'].iloc[i-2] <= df_coin['50ma'].iloc[i-1])
        
        # 필터 2-2: 긴 윗꼬리 방지 (윗꼬리가 몸통+아랫꼬리보다 작거나 같아야 함)
        prev_candle = df_coin.iloc[i-1]
        upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
        body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
        cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
        
        # 필터 2-3: 캔들 몸통이 전체 캔들 길이의 15% 이상
        candle_range = prev_candle['high'] - prev_candle['low']
        candle_body = abs(prev_candle['open'] - prev_candle['close'])
        if candle_range > 0:
            cond_body_over_15_percent = (candle_body >= candle_range * 0.15)

    # --- 최종 결정 ---
    # 모든 기본 조건과 필터링 조건을 만족해야 매수
    should_buy = (
        cond_buy_two_green and
        cond_buy_price_up and
        cond_buy_short_ma_up and
        cond_buy_mid_ma_stable and
        cond_buy_rsi_up and
        filter_no_sudden_surge and
        filter_ma50_not_declining and
        cond_no_long_upper_shadow and
        cond_body_over_15_percent
    )
    
    return should_buy
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================

GateIO_AccessKey = "YOUR_GATEIO_API_KEY"
GateIO_SecretKey = "YOUR_GATEIO_SECRET_KEY"
exchange = ccxt.gateio({'apiKey': GateIO_AccessKey, 'secret': GateIO_SecretKey, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
InvestTotalMoney = 5000
leverage = 2.5
fee = 0.001
InvestCoinList = [
    # {'ticker': 'DOGE/USDT', 'rate': 0.15, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'ADA/USDT',  'rate': 0.15, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'XLM/USDT', 'rate': 0.14, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'XRP/USDT', 'rate': 0.14, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'HBAR/USDT', 'rate': 0.14, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'ETH/USDT', 'rate': 0.14, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    # {'ticker': 'SOL/USDT', 'rate': 0.14, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},

    {'ticker': 'DOGE/USDT', 'rate': 0.12, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'ADA/USDT',  'rate': 0.12, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'XLM/USDT', 'rate': 0.1, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'XRP/USDT', 'rate': 0.1, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'HBAR/USDT', 'rate': 0.1, 'start_date': {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'ETH/USDT', 'rate': 0.1, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'PEPE/USDT', 'rate': 0.1, 'start_date':  {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'BONK/USDT', 'rate': 0.1, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'SHIB/USDT', 'rate': 0.08, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
    {'ticker': 'FLOKI/USDT', 'rate': 0.08, 'start_date':  {'year': 2020, 'month': 7, 'day': 1}},
]
dfs = {}
for coin_data in InvestCoinList:
    ticker = coin_data['ticker']
    start_date_params = coin_data['start_date']
    print(f"Fetching data for {ticker} from {start_date_params['year']}-{start_date_params['month']}-{start_date_params['day']}...")
    df = GetOhlcv2(exchange, ticker, '1d', start_date_params['year'], start_date_params['month'], start_date_params['day'], 0, 0)
    if df.empty:
        print(f"No data for {ticker}, skipping...")
        continue
    period_rsi = 14
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period_rsi - 1), min_periods=period_rsi).mean()
    _loss = down.abs().ewm(com=(period_rsi - 1), min_periods=period_rsi).mean()
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df['rsi_ma'] = df['rsi'].rolling(14).mean()
    df['rsi_5ma'] = df['rsi'].rolling(5).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['value'] = df['close'] * df['volume']
    ma_dfs = []
    for ma in range(3, 81):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)
    ma_df_combined = pd.concat(ma_dfs, axis=1)
    df = pd.concat([df, ma_df_combined], axis=1)
    df['200ma'] = df['close'].rolling(200).mean()
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    df['200ma_slope'] = ((df['200ma'] - df['200ma'].shift(10)) / df['200ma'].shift(10)) * 100
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['20ma_for_bb'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bollinger_upper'] = df['20ma_for_bb'] + (df['stddev'] * 2)
    df['bollinger_lower'] = df['20ma_for_bb'] - (df['stddev'] * 2)
    df.dropna(inplace=True)
    if not df.empty: dfs[ticker] = df

if not dfs:
    print("No data loaded for any coin. Exiting.")
    exit()

valid_tickers = [coin['ticker'] for coin in InvestCoinList if coin['ticker'] in dfs]
common_dates = set(dfs[valid_tickers[0]].index)
for ticker in valid_tickers[1:]:
    common_dates = common_dates.intersection(set(dfs[ticker].index))
common_dates = sorted(list(common_dates))
cash_balance = InvestTotalMoney
current_cycle_investment_base = InvestTotalMoney
positions = {}
total_equity_list, cash_only_equity_list, modified_equity_list = [], [], []
last_cash_only_equity = InvestTotalMoney
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in valid_tickers}
balance_logs, trade_logs = [], []
cycle_count = 1
was_in_position = False

# --- 백테스팅 루프 ---
for date in common_dates:
    current_data = {ticker: dfs[ticker].loc[date] for ticker in valid_tickers if date in dfs[ticker].index}
    if len(current_data) != len(valid_tickers): continue
    sold_today_tickers = set()

    # 1. 보유 중인 포지션 매도 조건 확인
    for ticker in list(positions.keys()):
        if ticker not in current_data: continue
        position = positions[ticker]
        margin, entry_price, pos_leverage = position['margin'], position['entry_price'], position['leverage']
        current_price = current_data[ticker]['open']
        if date not in dfs[ticker].index: continue
        i = dfs[ticker].index.get_loc(date)
        if i >= 2:
            df_coin = dfs[ticker]
            RevenueRate = ((current_price - entry_price) / entry_price * pos_leverage - fee) * 100.0
            
            # 매도 조건 확인 함수 호출
            if check_sell_conditions(df_coin, i, RevenueRate):
                # 매도 실행
                cash_balance += margin * (1 + RevenueRate / 100.0)
                log_msg = f"[사이클 {cycle_count}] {ticker} {date} >>> 매도: Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)
                if RevenueRate > 0: CoinStats[ticker]['SuccessCnt'] += 1
                else: CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                sold_today_tickers.add(ticker)
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1

    # 모든 포지션이 종료되면, 현재 현금 잔고를 다음 사이클의 투자 기분 금액으로 설정
    if not positions: current_cycle_investment_base = cash_balance
    
    # 2. 신규 매수 조건 확인
    buy_signals_today_specs = []
    for coin_candidate_spec in InvestCoinList:
        ticker = coin_candidate_spec['ticker']
        if ticker not in positions and ticker not in sold_today_tickers and ticker in dfs and date in dfs[ticker].index:
            df_coin = dfs[ticker]
            i = df_coin.index.get_loc(date)
            if i > 2:
                # 매수 조건 확인 함수 호출
                if check_buy_conditions(df_coin, i):
                    buy_signals_today_specs.append(coin_candidate_spec)

    # 3. 매수 신호가 나온 종목들 실제 매수 진행
    if buy_signals_today_specs:
        for coin_spec_to_buy in buy_signals_today_specs:
            ticker = coin_spec_to_buy['ticker']
            buy_price = current_data[ticker]['open']
            investment_for_this_coin = current_cycle_investment_base * coin_spec_to_buy['rate']
            if cash_balance >= investment_for_this_coin and investment_for_this_coin > 0:
                positions[ticker] = {'margin': investment_for_this_coin, 'entry_price': buy_price, 'quantity': (investment_for_this_coin * leverage) / buy_price, 'leverage': leverage}
                cash_balance -= investment_for_this_coin
                log_msg = f"[사이클 {cycle_count}] {ticker} {date} >>> 매수: Entry {buy_price:.8f}, 투자금 {investment_for_this_coin:.2f}, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)

    # 4. 일일 자산 기록
    daily_total_equity = cash_balance
    for ticker, position in positions.items():
        if ticker not in current_data: continue
        daily_total_equity += position['margin'] + (current_data[ticker]['close'] - position['entry_price']) * position['quantity']
    total_equity_list.append({'date': date, 'Total_Equity': daily_total_equity})
    if not positions: last_cash_only_equity = cash_balance
    cash_only_equity_list.append({'date': date, 'Cash_Only_Equity': last_cash_only_equity})
    daily_modified_equity = cash_balance
    for ticker, position in positions.items(): daily_modified_equity += position['margin']
    modified_equity_list.append({'date': date, 'Modified_Equity': daily_modified_equity})
    log_msg = f"--- {date.strftime('%Y-%m-%d')} | 일일 정산 --- 총자산: {daily_total_equity:,.0f} USDT"
    balance_logs.append(log_msg)

    # 5. 사이클 카운트
    if len(positions) > 0: was_in_position = True
    if len(positions) == 0 and was_in_position:
        if trade_logs and trade_logs[-1] != "": trade_logs.append("")
        cycle_count += 1
        was_in_position = False

# --- 결과 분석 및 데이터프레임 생성 ---
result_df = pd.DataFrame(total_equity_list).set_index('date')
result_df = result_df.join(pd.DataFrame(cash_only_equity_list).set_index('date')).join(pd.DataFrame(modified_equity_list).set_index('date'))
def calculate_mdd(df, column_name):
    prefix = column_name.replace('_Equity', '')
    ror_col, cum_ror_col, hw_col, dd_col, mdd_col = f'{prefix}_Ror', f'{prefix}_Cum_or', f'{prefix}_Highwatermark', f'{prefix}_Drawdown', f'{prefix}_MaxDrawdown'
    if df.empty or len(df) < 2: return df
    df[ror_col] = df[column_name].pct_change().fillna(0) + 1
    df[cum_ror_col] = df[ror_col].cumprod()
    df[hw_col] = df[cum_ror_col].cummax()
    df[dd_col] = (df[cum_ror_col] / df[hw_col]) - 1
    df[mdd_col] = df[dd_col].cummin()
    return df
result_df = calculate_mdd(result_df, 'Total_Equity')
result_df = calculate_mdd(result_df, 'Cash_Only_Equity')
result_df = calculate_mdd(result_df, 'Modified_Equity')
parsed_trades = []
for log in trade_logs:
    if "매수:" in log or "매도:" in log:
        match = re.search(r'\[사이클 \d+\] (.*?) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) >>> (매수|매도): (Entry|Exit) ([\d\.]+)?,?', log)
        if match:
            ticker, date_str, trade_type, _, price_str = match.groups()
            price = float(price_str)
            parsed_trades.append({'ticker': ticker.strip(), 'date': pd.to_datetime(date_str), 'type': trade_type, 'price': price})
trade_df = pd.DataFrame(parsed_trades)

# --- GUI 차트 앱 클래스 ---
class ChartApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("백테스팅 결과 분석 (고도화 버전)")
        self.geometry("1800x1000")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.all_trade_logs_parsed = self.parse_trade_logs(trade_logs)
        self.currently_displayed_logs = self.all_trade_logs_parsed[:]
        self.chart_artists = {}
        self.highlight_plot = None
        self.sort_info = {'col': None, 'reverse': False}
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)
        left_panel = ttk.Frame(main_pane, width=600)
        left_panel.pack_propagate(False)
        main_pane.add(left_panel, weight=1)
        filter_frame = ttk.LabelFrame(left_panel, text="로그 필터")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(filter_frame, text="코인:").grid(row=0, column=0, padx=(5,2), pady=5, sticky='w')
        self.filter_ticker_var = tk.StringVar()
        self.filter_ticker_entry = ttk.Entry(filter_frame, textvariable=self.filter_ticker_var, width=15)
        self.filter_ticker_entry.grid(row=0, column=1, padx=(0,5), pady=5, sticky='w')
        ttk.Label(filter_frame, text="종류:").grid(row=0, column=2, padx=(5,2), pady=5, sticky='w')
        self.filter_type_var = tk.StringVar()
        self.filter_type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var, values=['', '매수', '매도'], width=8)
        self.filter_type_combo.grid(row=0, column=3, padx=(0,5), pady=5, sticky='w')
        apply_button = ttk.Button(filter_frame, text="적용", command=self.apply_filters_and_sort)
        apply_button.grid(row=0, column=4, padx=5, pady=5)
        clear_button = ttk.Button(filter_frame, text="초기화", command=self.clear_filters)
        clear_button.grid(row=0, column=5, padx=5, pady=5)
        self.filter_ticker_entry.bind('<Return>', lambda e: self.apply_filters_and_sort())
        log_frame = ttk.Frame(left_panel)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        cols = ('Cycle', 'Ticker', 'DateTime', 'Type', 'Price', 'Detail')
        self.log_tree = ttk.Treeview(log_frame, columns=cols, show='headings')
        for col in cols:
            self.log_tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))
            width = {'Cycle': 50, 'Ticker': 100, 'DateTime': 130, 'Type': 50, 'Price': 100}.get(col, 200)
            anchor = 'e' if col == 'Price' else 'center' if col != 'Detail' else 'w'
            self.log_tree.column(col, width=width, anchor=anchor)
        v_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        h_scroll = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_tree.xview)
        self.log_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.log_tree.pack(fill=tk.BOTH, expand=True)
        chart_frame = ttk.Frame(main_pane)
        main_pane.add(chart_frame, weight=3)
        self.tab_control = ttk.Notebook(chart_frame)
        self.tab_control.pack(expand=1, fill="both")
        self.add_overall_tab()
        for ticker in valid_tickers: self.add_coin_tab(ticker)
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.log_tree.bind("<<TreeviewSelect>>", self.on_log_select)
        self.repopulate_log_tree()

    def apply_filters_and_sort(self):
        ticker_filter = self.filter_ticker_var.get().upper()
        type_filter = self.filter_type_var.get()
        current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
        tab_ticker_filter = None
        if current_tab_text != '📊 종합 결과': tab_ticker_filter = current_tab_text
        logs = self.all_trade_logs_parsed
        if tab_ticker_filter: logs = [log for log in logs if log['ticker'] == tab_ticker_filter]
        if ticker_filter: logs = [log for log in logs if ticker_filter in log['ticker'].upper()]
        if type_filter: logs = [log for log in logs if log['type'] == type_filter]
        self.currently_displayed_logs = logs
        if self.sort_info['col']:
            key_map = {'Cycle': 'cycle', 'Ticker': 'ticker', 'DateTime': 'datetime', 'Type': 'type', 'Price': 'price', 'Detail': 'detail'}
            sort_key = key_map.get(self.sort_info['col'])
            if sort_key in ['price', 'cycle']: self.currently_displayed_logs.sort(key=lambda x: x[sort_key], reverse=self.sort_info['reverse'])
            else: self.currently_displayed_logs.sort(key=lambda x: str(x[sort_key]), reverse=self.sort_info['reverse'])
        self.repopulate_log_tree()

    def clear_filters(self):
        self.filter_ticker_var.set(""); self.filter_type_var.set(""); self.apply_filters_and_sort()

    def sort_by_column(self, col):
        if self.sort_info['col'] == col: self.sort_info['reverse'] = not self.sort_info['reverse']
        else: self.sort_info['col'] = col; self.sort_info['reverse'] = False
        self.apply_filters_and_sort()

    def repopulate_log_tree(self):
        self.log_tree.delete(*self.log_tree.get_children())
        for log in self.currently_displayed_logs:
            self.log_tree.insert('', 'end', values=(log['cycle'], log['ticker'], log['datetime'].strftime('%Y-%m-%d %H:%M'), log['type'], f"{log['price']:.8f}", log['detail']))

    def on_tab_changed(self, event):
        self.remove_highlight(); self.apply_filters_and_sort()

    def parse_trade_logs(self, raw_logs):
        parsed = []
        for log in raw_logs:
            if not log or ">>>" not in log: continue
            match = re.search(r'\[사이클 (\d+)\] (.*?) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) >>> (매수|매도): (?:Entry|Exit) ([\d\.]+), (.*)', log)
            if match:
                cycle, ticker, date_str, trade_type, price_str, detail = match.groups()
                parsed.append({'cycle': int(cycle), 'ticker': ticker.strip(), 'datetime': pd.to_datetime(date_str), 'type': trade_type, 'price': float(price_str), 'detail': detail.strip()})
        return parsed

    def on_log_select(self, event):
        self.remove_highlight()
        selected_items = self.log_tree.selection()
        if not selected_items: return
        item_values = self.log_tree.item(selected_items[0], 'values')
        log_ticker, log_datetime_str, log_type, log_price_str = item_values[1], item_values[2], item_values[3], item_values[4]
        log_price = float(log_price_str)
        log_datetime = pd.to_datetime(log_datetime_str)
        current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
        ticker_key = 'overall' if current_tab_text == '📊 종합 결과' else current_tab_text
        if ticker_key != 'overall' and ticker_key != log_ticker:
            for i, tab_id in enumerate(self.tab_control.tabs()):
                if self.tab_control.tab(tab_id, "text") == log_ticker: self.tab_control.select(i); ticker_key = log_ticker; break
        if ticker_key not in self.chart_artists: return
        artists = self.chart_artists[ticker_key]
        ax, canvas = artists['ax'], artists['canvas']
        y_coord = log_price
        if ticker_key == 'overall':
            try:
                nearest_position = result_df.index.get_indexer([log_datetime], method='nearest')[0]
                closest_date = result_df.index[nearest_position]
                y_coord = result_df.loc[closest_date, 'Total_Equity']
            except Exception: return
        self.highlight_plot = ax.plot(log_datetime, y_coord, marker='^' if log_type == '매수' else 'v', color='cyan', markersize=15, markeredgecolor='black', zorder=10)[0]
        canvas.draw()

    def remove_highlight(self):
        if self.highlight_plot:
            self.highlight_plot.remove(); self.highlight_plot = None
            try:
                current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                ticker_key = 'overall' if current_tab_text == '📊 종합 결과' else current_tab_text
                if ticker_key in self.chart_artists: self.chart_artists[ticker_key]['canvas'].draw()
            except Exception: pass

    def on_closing(self):
        self.quit(); self.destroy()

    def create_chart_frame(self, parent_tab):
        frame = ttk.Frame(parent_tab)
        frame.pack(fill='both', expand=True)
        fig = Figure(dpi=100)
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
        toolbar = NavigationToolbar2Tk(canvas, frame)
        toolbar.update()
        return fig, canvas

    def add_overall_tab(self):
        overall_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(overall_tab, text='📊 종합 결과')
        fig, canvas = self.create_chart_frame(overall_tab)
        axs = fig.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [2, 2, 1]})
        fig.tight_layout(pad=3.0)
        equity_line = result_df['Total_Equity']

        axs[0].plot(equity_line.index, equity_line, label=f'Strategy ({leverage}x Leverage)', color='blue')
        axs[0].set_title('Overall Performance (Linear Scale)', fontsize=12)
        axs[0].set_ylabel('Total Equity (USDT)')
        axs[0].grid(True, which='both', linestyle='--', linewidth=0.5)
        axs[0].legend()
        axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        axs[1].plot(equity_line.index, equity_line, label=f'Strategy ({leverage}x Leverage)', color='black')
        axs[1].set_yscale('log')
        axs[1].set_title('Overall Performance (Log Scale)', fontsize=12)
        axs[1].set_ylabel('Total Equity (USDT)')
        axs[1].grid(True, which='both', linestyle='--', linewidth=0.5)
        axs[1].legend()
        axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))

        axs[2].fill_between(result_df.index, result_df['Total_Drawdown'] * 100, 0, color='skyblue', alpha=0.3, label='MDD')
        axs[2].plot(result_df.index, result_df['Cash_Only_Drawdown'] * 100, color='mediumseagreen')
        axs[2].plot(result_df.index, result_df['Modified_Drawdown'] * 100, color='orange')
        axs[2].set_title('Drawdown (3 Methods)', fontsize=12)
        axs[2].set_ylabel('Drawdown (%)'); axs[2].grid(True); axs[2].legend()
        axs[2].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

        self.chart_artists['overall'] = {'fig': fig, 'canvas': canvas, 'ax': axs[1]}
        canvas.draw()

    def add_coin_tab(self, ticker):
        coin_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(coin_tab, text=ticker)
        fig, canvas = self.create_chart_frame(coin_tab)
        axs = fig.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [2, 2, 1]})
        fig.tight_layout(pad=3.0)
        coin_df = dfs[ticker]
        coin_trades = trade_df[trade_df['ticker'] == ticker]

        # ======================== ▼▼▼ 이 부분 교체 ▼▼▼ ========================
        # 1. 가격 차트를 선형(기본값)으로 그립니다.
        axs[0].plot(coin_df.index, coin_df['close'], label=f'{ticker} Price', color='black', alpha=0.8)

        # 2. Y축의 숫자 라벨을 모두 제거합니다.
        axs[0].set_yticklabels([])

        # 3. 매수/매도 시그널을 그립니다.
        if not coin_trades.empty:
            buy_trades = coin_trades[coin_trades['type'] == '매수']
            sell_trades = coin_trades[coin_trades['type'] == '매도']
            axs[0].plot(buy_trades['date'], buy_trades['price'], '^', color='green', markersize=8, label='Buy')
            axs[0].plot(sell_trades['date'], sell_trades['price'], 'v', color='red', markersize=8, label='Sell')

        # 4. 차트 제목을 '(Linear Scale)'로 변경합니다.
        axs[0].set_title(f'Price Chart & Trades (Linear Scale)', fontsize=12)
        axs[0].set_ylabel(f'Price (USDT)')
        axs[0].grid(True, which='both')
        axs[0].legend()
        # ======================== ▲▲▲ 이 부분 교체 ▲▲▲ ========================

        rate_info = next((item for item in InvestCoinList if item["ticker"] == ticker), None)
        initial_capital = InvestTotalMoney * rate_info['rate'] if rate_info else 0
        ticker_trades = coin_trades.copy().reset_index(drop=True)

        # 1. 거래 종료 기준 (Step Chart) Equity
        equity_points = [(result_df.index[0], initial_capital)]
        current_equity_realized = initial_capital
        buy_price_realized = 0.0
        for i in range(len(ticker_trades)):
            trade = ticker_trades.loc[i]
            if trade['type'] == '매수' and buy_price_realized == 0:
                buy_price_realized = trade['price']
            elif trade['type'] == '매도' and buy_price_realized > 0:
                sell_price = trade['price']
                trade_return = (sell_price / buy_price_realized - 1) * leverage
                current_equity_realized *= (1 + trade_return)
                equity_points.append((trade['date'], current_equity_realized))
                buy_price_realized = 0.0

        point_dates = [p[0] for p in equity_points]
        point_equities = [p[1] for p in equity_points]
        equity_series_realized = pd.Series(point_equities, index=point_dates).reindex(result_df.index).ffill()
        equity_series_realized.fillna(initial_capital, inplace=True)
        realized_df = pd.DataFrame({'Equity': equity_series_realized})
        realized_df = calculate_mdd(realized_df, 'Equity')

        # 2. 일일 평가 기준 (Fluctuating Chart) Equity
        equity_series_daily = pd.Series(index=result_df.index, dtype=float)
        current_equity_daily = initial_capital
        is_in_position = False
        trade_dates = ticker_trades['date'].dt.normalize()
        for i, date in enumerate(equity_series_daily.index):
            trades_today = ticker_trades[trade_dates == date.normalize()]
            if is_in_position and date in coin_df.index and i > 0:
                prev_date = equity_series_daily.index[i - 1]
                if prev_date in coin_df.index:
                    exit_price = coin_df.loc[date]['open'] if not trades_today.empty and trades_today.iloc[0]['type'] == '매도' else coin_df.loc[date]['close']
                    price_change = (exit_price / coin_df.loc[prev_date]['close']) - 1
                    current_equity_daily *= (1 + price_change * leverage)
            if not trades_today.empty:
                is_in_position = True if trades_today.iloc[0]['type'] == '매수' else False
            equity_series_daily[date] = current_equity_daily
        daily_df = pd.DataFrame({'Equity': equity_series_daily}).dropna()
        daily_df = calculate_mdd(daily_df, 'Equity')

        # --- 개별 성과 차트 (선형 & 로그) ---
        ax_linear = axs[1]
        equity_to_plot = realized_df['Equity']
        line1, = ax_linear.plot(equity_to_plot.index, equity_to_plot, color='purple', drawstyle='steps-post', linestyle='-', label=f'{ticker} (Linear)')
        ax_linear.set_title('Individual Performance (Realized PnL)', fontsize=12)
        ax_linear.set_ylabel('Equity (USDT) - Linear')
        ax_linear.grid(True)
        ax_linear.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax_log = ax_linear.twinx()
        line2, = ax_log.plot(equity_to_plot.index, equity_to_plot, color='darkviolet', drawstyle='steps-post', linestyle=':', label=f'{ticker} (Log)')
        ax_log.set_yscale('log')
        ax_log.set_ylabel('Equity (USDT) - Log')
        ax_log.get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        ax_linear.legend(handles=[line1, line2], loc='upper left')

        # --- [오류 수정 및 스타일 변경] 두 가지 Drawdown 함께 표시 ---
        axs[2].plot(realized_df.index, realized_df['Equity_Drawdown'] * 100, label='DD (거래 종료)', color='darkorange', linestyle='-')
        axs[2].plot(daily_df.index, daily_df['Equity_Drawdown'] * 100, label='DD (일일 평가)', color='green', linestyle=':')
        axs[2].set_title('Individual Drawdown Comparison', fontsize=12)
        axs[2].set_ylabel('Drawdown (%)'); axs[2].grid(True); axs[2].legend()
        axs[2].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))

        self.chart_artists[ticker] = {'fig': fig, 'canvas': canvas, 'ax': axs[0]}
        canvas.draw()


# --- 메인 실행 블록 ---
if __name__ == "__main__":
    print("백테스팅 계산 완료. 결과 분석 및 차트를 준비합니다...")
    print("\n\n" + "="*50 + "\n--- 일일 잔액 로그 ---\n" + "="*50)
    for log in balance_logs: print(log)
    print("\n\n" + "="*50 + "\n--- 매수/매도 로그 ---\n" + "="*50)
    if not trade_logs: print("거래 내역이 없습니다.")
    else:
        for log in trade_logs: print(log)
    print("="*50)

    # <<< 코드 수정 시작 >>>
    if result_df.empty:
        print("결과 데이터가 없어 차트를 생성할 수 없습니다.")
    else:
        pcServerGb = socket.gethostname()
        if pcServerGb != "AutoBotCong":
            # PC 환경 (AutoBotCong이 아닌 경우) -> GUI 실행
            app = ChartApp()
            app.mainloop()
            print("\n차트 창이 닫혔습니다. 최종 통계 결과를 출력합니다.")
        else:
            # 서버 환경 (AutoBotCong인 경우) -> GUI 생략
            print("\n서버 환경이므로 GUI를 생략하고 최종 통계 결과를 바로 출력합니다.")

        # 최종 통계 결과는 GUI 실행 여부와 관계없이 항상 출력
        TotalOri, TotalFinal = result_df['Total_Equity'].iloc[0], result_df['Total_Equity'].iloc[-1]
        TotalMDD, CashOnlyMDD, ModifiedMDD = result_df['Total_MaxDrawdown'].min()*100, result_df['Cash_Only_MaxDrawdown'].min()*100, result_df['Modified_MaxDrawdown'].min()*100
        weekly_equity_df = result_df['Total_Equity'].resample('W-SUN').last().to_frame()
        weekly_equity_df = calculate_mdd(weekly_equity_df, 'Total_Equity')
        monthly_equity_for_mdd_df = result_df['Total_Equity'].resample('ME').last().to_frame()
        monthly_equity_for_mdd_df = calculate_mdd(monthly_equity_for_mdd_df, 'Total_Equity')
        WeeklyMDD = weekly_equity_df['Total_MaxDrawdown'].min()*100 if not weekly_equity_df.empty else 0
        MonthlyMDD = monthly_equity_for_mdd_df['Total_MaxDrawdown'].min()*100 if not monthly_equity_for_mdd_df.empty else 0
        monthly_stats = result_df.resample('ME').agg({'Total_Equity': 'last'}); monthly_stats.rename(columns={'Total_Equity': 'End_Equity'}, inplace=True)
        monthly_stats['Prev_Month_End_Equity'] = monthly_stats['End_Equity'].shift(1).fillna(TotalOri)
        monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Prev_Month_End_Equity']) - 1) * 100; monthly_stats['Trades'] = 0
        for month_key_str, count in MonthlyTryCnt.items():
            for idx in monthly_stats.index:
                if idx.strftime('%Y-%m') == month_key_str: monthly_stats.loc[idx, 'Trades'] = count; break
        monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]; monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']; monthly_stats.index = monthly_stats.index.strftime('%Y-%m')
        yearly_stats = result_df.resample('YE').agg({'Total_Equity': ['first', 'last']}); yearly_stats.columns = ['Start_Equity', 'End_Equity']
        yearly_stats['Return'] = ((yearly_stats['End_Equity'] / yearly_stats['Start_Equity']) - 1) * 100; yearly_stats['Trades'] = 0
        for month_key_str, count in MonthlyTryCnt.items():
            year_str = month_key_str.split('-')[0]
            for idx in yearly_stats.index:
                if idx.strftime('%Y') == year_str: yearly_stats.loc[idx, 'Trades'] += count; break
        yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]; yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']; yearly_stats.index = yearly_stats.index.strftime('%Y')
        print("\n---------- 코인별 거래 통계 ----------")
        total_success_all, total_fail_all = 0, 0
        for ticker_stat in valid_tickers:
            stats = CoinStats[ticker_stat]
            success, fail = stats['SuccessCnt'], stats['FailCnt']
            total_success_all += success; total_fail_all += fail; total_trades = success + fail
            win_rate = (success / total_trades * 100) if total_trades > 0 else 0
            print(f"{ticker_stat} >>> 성공: {success} 실패: {fail} -> 승률: {round(win_rate, 2)}%")
        total_trades_all = total_success_all + total_fail_all
        overall_win_rate = (total_success_all / total_trades_all * 100) if total_trades_all > 0 else 0
        print(f"총 합계 >>> 성공: {total_success_all} 실패: {total_fail_all} -> 승률: {round(overall_win_rate, 2)}%")
        print("------------------------------")
        print("\n---------- 총 결과 ----------")
        print(f"최초 금액: {format(round(TotalOri), ',')} USDT, 최종 금액: {format(round(TotalFinal), ',')} USDT")
        print(f"총 수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
        print(f"MDD 1 (일일 시가평가 기준): {round(TotalMDD, 2)}%")
        print(f"MDD 2 (포지션 없을 시 잔액 기준): {round(CashOnlyMDD, 2)}%")
        print(f"MDD 3 (포지션 원금 + 잔액 기준): {round(ModifiedMDD, 2)}%")
        print(f"MDD 4 (주간 잔액 기준): {round(WeeklyMDD, 2)}%")
        print(f"MDD 5 (월간 잔액 기준): {round(MonthlyMDD, 2)}%")
        print("------------------------------")
        print("\n---------- 월별 통계 ----------")
        print(monthly_stats.to_string())
        print("\n---------- 년도별 통계 ----------")
        print(yearly_stats.to_string())
        print("------------------------------")
    # <<< 코드 수정 종료 >>>