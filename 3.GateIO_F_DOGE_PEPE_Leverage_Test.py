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

# GUI 및 차트 연동을 위한 라이브러리
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

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

GateIO_AccessKey = "YOUR_GATEIO_API_KEY"
GateIO_SecretKey = "YOUR_GATEIO_SECRET_KEY"
exchange = ccxt.gateio({'apiKey': GateIO_AccessKey, 'secret': GateIO_SecretKey, 'enableRateLimit': True, 'options': {'defaultType': 'swap'}})
InvestTotalMoney = 5000
leverage = 7
fee = 0.001
InvestCoinList = [

    # {'ticker': 'DOGE/USDT', 'rate': 0.25, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    # {'ticker': 'ADA/USDT',  'rate': 0.15, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    # {'ticker': 'XLM/USDT', 'rate': 0.15, 'start_date':  {'year': 2021, 'month': 7, 'day': 1}},
    # {'ticker': 'XRP/USDT', 'rate': 0.15, 'start_date':  {'year': 2021, 'month': 7, 'day': 1}},
    # {'ticker': 'HBAR/USDT', 'rate': 0.15, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    # {'ticker': 'ETH/USDT',  'rate': 0.15, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},

    # {'ticker': 'DOGE/USDT', 'rate': 0.25, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'ADA/USDT',  'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'XLM/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'XRP/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'HBAR/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'PEPE/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'BONK/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},

    {'ticker': 'DOGE/USDT', 'rate': 0.2, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'ADA/USDT',  'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XLM/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XRP/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'HBAR/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'ETH/USDT', 'rate': 0.1, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    {'ticker': 'PEPE/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'BONK/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'SHIB/USDT', 'rate': 0.05, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    {'ticker': 'FLOKI/USDT', 'rate': 0.05, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},

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
    # ... (지표 계산 로직은 원본과 동일)
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

    # 1. 보유 중인 코인의 매도 조건 확인
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
            
            # 캔들 모양 정의
            def is_doji_candle(open_price, close_price, high_price, low_price):
                candle_range = high_price - low_price
                if candle_range == 0: return False
                return (abs(open_price - close_price) / candle_range) <= 0.1
            
            is_doji_1 = is_doji_candle(df_coin['open'].iloc[i-1], df_coin['close'].iloc[i-1], df_coin['high'].iloc[i-1], df_coin['low'].iloc[i-1])
            is_doji_2 = is_doji_candle(df_coin['open'].iloc[i-2], df_coin['close'].iloc[i-2], df_coin['high'].iloc[i-2], df_coin['low'].iloc[i-2])
            
            # ==========================================================
            # ▼▼▼ 매도 조건 가독성 개선 ▼▼▼
            # ==========================================================

            # 조건 A-1: 하락 장악형 패턴 (전일봉이 전전일봉의 고점/저점 하회)
            cond_sell_price_fall = (df_coin['high'].iloc[i-2] > df_coin['high'].iloc[i-1] and 
                                    df_coin['low'].iloc[i-2] > df_coin['low'].iloc[i-1])

            # 조건 A-2: 이틀 연속 음봉
            cond_sell_two_red = (df_coin['open'].iloc[i-1] > df_coin['close'].iloc[i-1] and 
                                 df_coin['open'].iloc[i-2] > df_coin['close'].iloc[i-2])

            # 조건 A-3: 현재 손실 중
            cond_sell_is_losing = (RevenueRate < 0)

            # 예외 조건: 강한 상승 추세일 경우 매도 보류 (RSI와 3일선 동시 상승)
            except_sell_strong_up = (df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and 
                                     df_coin['3ma'].iloc[i-2] < df_coin['3ma'].iloc[i-1])

            # 조건 B: 이틀 연속 도지 캔들 발생 (시장 방향성 불확실)
            cond_sell_dojis = (is_doji_1 and is_doji_2)
            
            # 최종 매도 판단
            sell_main_condition = (cond_sell_price_fall or cond_sell_two_red or cond_sell_is_losing) and not except_sell_strong_up
            
            if sell_main_condition or cond_sell_dojis:
                cash_balance += margin * (1 + RevenueRate / 100.0)
                log_msg = f"[사이클 {cycle_count}] {ticker} {date} >>> 매도: Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)
                if RevenueRate > 0: CoinStats[ticker]['SuccessCnt'] += 1
                else: CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                sold_today_tickers.add(ticker)
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
    
    if not positions: current_cycle_investment_base = cash_balance
    
    # 2. 매수 신호 확인 및 실행
    buy_signals_today_specs = []
    for coin_candidate_spec in InvestCoinList:
        ticker = coin_candidate_spec['ticker']
        if ticker not in positions and ticker not in sold_today_tickers and ticker in dfs and date in dfs[ticker].index:
            df_coin = dfs[ticker]
            i = df_coin.index.get_loc(date)
            if i > 2:
                # ==========================================================
                # ▼▼▼ 매수 조건 가독성 개선 ▼▼▼
                # ==========================================================

                # 기본 조건 1: 이틀 연속 양봉이며, 가격과 고점이 상승하는 추세
                cond_buy_two_green = (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and 
                                      df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2])
                cond_buy_price_up = (df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and
                                     df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1])

                # 기본 조건 2: 단기 이평선(7, 20) 상승 추세
                cond_buy_short_ma_up = (df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and
                                        df_coin['20ma'].iloc[i-2] <= df_coin['20ma'].iloc[i-1])

                # 기본 조건 3: 중기 이평선(30) 기울기가 급격히 하락하지 않음
                cond_buy_mid_ma_stable = (df_coin['30ma_slope'].iloc[i-1] > -2)

                # 기본 조건 4: RSI 모멘텀 상승
                cond_buy_rsi_up = (df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1])

                # 필터링 조건 1: 전일 거래량이 터지며 급등한 코인 제외
                filter_no_sudden_surge = (df_coin['change'].iloc[i-1] < 0.5)

                # 필터링 조건 2: 200일선 위에 있을 경우, 추가 조건 확인
                is_above_200ma = df_coin['close'].iloc[i-1] > df_coin['200ma'].iloc[i-1]
                filter_ma50_not_declining = True  # 기본값
                
                if is_above_200ma:
                    # 50일 이평선이 하락 추세가 아닐 것
                    filter_ma50_not_declining = (df_coin['50ma'].iloc[i-2] <= df_coin['50ma'].iloc[i-1])

                # 최종 매수 판단
                if (cond_buy_two_green and 
                    cond_buy_price_up and 
                    cond_buy_short_ma_up and 
                    cond_buy_mid_ma_stable and 
                    cond_buy_rsi_up and
                    filter_no_sudden_surge and 
                    filter_ma50_not_declining):
                    buy_signals_today_specs.append(coin_candidate_spec)

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
    
    # 3. 일일 자산 가치 계산 (이하 로직은 동일)
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
    ror_col, cum_ror_col, hw_col, dd_col, mdd_col = f'{prefix}_Ror', f'{prefix}_Cum_Ror', f'{prefix}_Highwatermark', f'{prefix}_Drawdown', f'{prefix}_MaxDrawdown'
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

# --- GUI 차트 앱 클래스 (필터/정렬 기능 추가 최종 버전) ---
class ChartApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("백테스팅 결과 분석 (고도화 버전)")
        self.geometry("1800x1000")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- 데이터 및 상태 변수 초기화 ---
        self.all_trade_logs_parsed = self.parse_trade_logs(trade_logs)
        self.currently_displayed_logs = self.all_trade_logs_parsed[:]
        self.chart_artists = {}
        self.highlight_plot = None
        self.sort_info = {'col': None, 'reverse': False}

        # --- 메인 레이아웃 ---
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill=tk.BOTH, expand=True)

        # --- 좌측 패널 (필터 + 로그) ---
        left_panel = ttk.Frame(main_pane, width=600)
        left_panel.pack_propagate(False)
        main_pane.add(left_panel, weight=1)

        # 필터 프레임
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


        # 로그 트리뷰
        log_frame = ttk.Frame(left_panel)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
        
        cols = ('Cycle', 'Ticker', 'DateTime', 'Type', 'Price', 'Detail')
        self.log_tree = ttk.Treeview(log_frame, columns=cols, show='headings')
        
        # 컬럼 및 정렬 커맨드 설정
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

        # --- 우측 패널 (차트) ---
        chart_frame = ttk.Frame(main_pane)
        main_pane.add(chart_frame, weight=3)
        self.tab_control = ttk.Notebook(chart_frame)
        self.tab_control.pack(expand=1, fill="both")

        self.add_overall_tab()
        for ticker in valid_tickers:
            self.add_coin_tab(ticker)
        
        # --- 이벤트 바인딩 및 초기화 ---
        self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
        self.log_tree.bind("<<TreeviewSelect>>", self.on_log_select)
        self.repopulate_log_tree()

    def apply_filters_and_sort(self):
        # 1. 필터 적용
        ticker_filter = self.filter_ticker_var.get().upper()
        type_filter = self.filter_type_var.get()
        
        current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
        tab_ticker_filter = None
        if current_tab_text != '📊 종합 결과':
            tab_ticker_filter = current_tab_text

        logs = self.all_trade_logs_parsed
        
        if tab_ticker_filter:
            logs = [log for log in logs if log['ticker'] == tab_ticker_filter]
        if ticker_filter:
            logs = [log for log in logs if ticker_filter in log['ticker'].upper()]
        if type_filter:
            logs = [log for log in logs if log['type'] == type_filter]
            
        self.currently_displayed_logs = logs
        
        # 2. 현재 정렬 상태 유지
        if self.sort_info['col']:
            key_map = {'Cycle': 'cycle', 'Ticker': 'ticker', 'DateTime': 'datetime', 'Type': 'type', 'Price': 'price', 'Detail': 'detail'}
            sort_key = key_map.get(self.sort_info['col'])
            
            # 데이터 타입에 맞는 정렬
            if sort_key in ['price', 'cycle']:
                 self.currently_displayed_logs.sort(key=lambda x: x[sort_key], reverse=self.sort_info['reverse'])
            else:
                 self.currently_displayed_logs.sort(key=lambda x: str(x[sort_key]), reverse=self.sort_info['reverse'])

        # 3. 뷰 리프레시
        self.repopulate_log_tree()

    def clear_filters(self):
        self.filter_ticker_var.set("")
        self.filter_type_var.set("")
        self.apply_filters_and_sort()

    def sort_by_column(self, col):
        if self.sort_info['col'] == col:
            self.sort_info['reverse'] = not self.sort_info['reverse']
        else:
            self.sort_info['col'] = col
            self.sort_info['reverse'] = False
        
        self.apply_filters_and_sort() # 필터 상태를 유지하며 정렬

    def repopulate_log_tree(self):
        self.log_tree.delete(*self.log_tree.get_children())
        for log in self.currently_displayed_logs:
            self.log_tree.insert('', 'end', values=(
                log['cycle'], log['ticker'], log['datetime'].strftime('%Y-%m-%d %H:%M'),
                log['type'], f"{log['price']:.8f}", log['detail']
            ))

    def on_tab_changed(self, event):
        self.remove_highlight()
        self.apply_filters_and_sort()

    # --- 이하 다른 메서드들은 이전과 거의 동일 ---

    def parse_trade_logs(self, raw_logs):
        parsed = []
        for log in raw_logs:
            if not log or ">>>" not in log: continue
            match = re.search(r'\[사이클 (\d+)\] (.*?) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) >>> (매수|매도): (?:Entry|Exit) ([\d\.]+), (.*)', log)
            if match:
                cycle, ticker, date_str, trade_type, price_str, detail = match.groups()
                parsed.append({
                    'cycle': int(cycle), 'ticker': ticker.strip(),
                    'datetime': pd.to_datetime(date_str), 'type': trade_type,
                    'price': float(price_str), 'detail': detail.strip()
                })
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
                if self.tab_control.tab(tab_id, "text") == log_ticker:
                    self.tab_control.select(i)
                    ticker_key = log_ticker
                    break
        
        if ticker_key not in self.chart_artists: return
        artists = self.chart_artists[ticker_key]
        ax, canvas = artists['ax'], artists['canvas']

        y_coord = log_price
        if ticker_key == 'overall':
            target_date = log_datetime
            try:
                nearest_position = result_df.index.get_indexer([target_date], method='nearest')[0]
                closest_date = result_df.index[nearest_position]
                y_coord = result_df.loc[closest_date, 'Total_Cum_Ror'] * InvestTotalMoney
            except Exception as e:
                print(f"차트 하이라이트 중 오류 발생: {e}")
                return

        self.highlight_plot = ax.plot(log_datetime, y_coord, 
                                      marker='^' if log_type == '매수' else 'v', 
                                      color='cyan', markersize=15, 
                                      markeredgecolor='black', zorder=10)[0]
        canvas.draw()

    def remove_highlight(self):
        if self.highlight_plot:
            self.highlight_plot.remove()
            self.highlight_plot = None
            try:
                current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                ticker_key = 'overall' if current_tab_text == '📊 종합 결과' else current_tab_text
                if ticker_key in self.chart_artists:
                    self.chart_artists[ticker_key]['canvas'].draw()
            except Exception: pass

    def on_closing(self):
        self.quit()
        self.destroy()

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
        axs = fig.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        fig.tight_layout(pad=3.0)
        
        equity_line = result_df['Total_Cum_Ror'] * InvestTotalMoney
        axs[0].plot(equity_line.index, equity_line, label=f'Strategy ({leverage}x Leverage)', color='black')
        axs[0].set_yscale('log')
        
        if not trade_df.empty:
            buy_trades = trade_df[trade_df['type'] == '매수']
            sell_trades = trade_df[trade_df['type'] == '매도']
            buy_dates = buy_trades['date'][buy_trades['date'].isin(equity_line.index)]
            sell_dates = sell_trades['date'][sell_trades['date'].isin(equity_line.index)]
            buy_y = equity_line.reindex(buy_dates, method='nearest')
            sell_y = equity_line.reindex(sell_dates, method='nearest')
            buy_plot = axs[0].plot(buy_dates, buy_y, '^', color='green', markersize=6, label='Buy Signal')
            sell_plot = axs[0].plot(sell_dates, sell_y, 'v', color='red', markersize=6, label='Sell Signal')
            self.chart_artists['overall'] = {'fig': fig, 'canvas': canvas, 'ax': axs[0], 'buy_plot': buy_plot[0], 'sell_plot': sell_plot[0]}
        
        axs[0].set_title('Overall Performance (Log Scale)', fontsize=12)
        axs[0].set_ylabel('Total Equity (USDT)')
        axs[0].grid(True, which='both', linestyle='--', linewidth=0.5)
        axs[0].legend()
        axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
        
        axs[1].fill_between(result_df.index, result_df['Total_Drawdown'] * 100, 0, color='skyblue', alpha=0.3, label='DD (Daily)')
        axs[1].plot(result_df.index, result_df['Cash_Only_Drawdown'] * 100, label='DD (Cash When Flat)', color='mediumseagreen')
        axs[1].plot(result_df.index, result_df['Modified_Drawdown'] * 100, label='DD (Principal + Cash)', color='orange')
        axs[1].set_title('Drawdown (3 Methods)', fontsize=12)
        axs[1].set_ylabel('Drawdown (%)')
        axs[1].grid(True)
        axs[1].legend()
        axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        canvas.draw()

    def add_coin_tab(self, ticker):
        coin_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(coin_tab, text=ticker)
        fig, canvas = self.create_chart_frame(coin_tab)
        axs = fig.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        fig.tight_layout(pad=3.0)
        
        coin_df = dfs[ticker]
        coin_trades = trade_df[trade_df['ticker'] == ticker]
        
        axs[0].plot(coin_df.index, coin_df['close'], label=f'{ticker} Price', color='black', alpha=0.8)
        if not coin_trades.empty:
            buy_trades = coin_trades[coin_trades['type'] == '매수']
            sell_trades = coin_trades[coin_trades['type'] == '매도']
            buy_plot = axs[0].plot(buy_trades['date'], buy_trades['price'], '^', color='green', markersize=8, label='Buy')
            sell_plot = axs[0].plot(sell_trades['date'], sell_trades['price'], 'v', color='red', markersize=8, label='Sell')
            self.chart_artists[ticker] = {'fig': fig, 'canvas': canvas, 'ax': axs[0], 'buy_plot': buy_plot[0], 'sell_plot': sell_plot[0]}

        axs[0].set_title(f'Price Chart & Trades', fontsize=12)
        axs[0].set_ylabel(f'Price (USDT)'); axs[0].grid(True); axs[0].legend()

        single_coin_equity = pd.Series(index=result_df.index, dtype=float)
        single_coin_equity.iloc[0] = InvestTotalMoney
        last_equity, in_position = InvestTotalMoney, False
        for i in range(1, len(result_df.index)):
            date, prev_date = result_df.index[i], result_df.index[i-1]
            trade_on_date = coin_trades[coin_trades['date'].dt.date == date.date()]
            if in_position and date in coin_df.index and prev_date in coin_df.index:
                last_equity *= coin_df.loc[date]['open'] / coin_df.loc[prev_date]['close']
            if not trade_on_date.empty:
                if trade_on_date['type'].iloc[0] == '매수': in_position = True
                elif trade_on_date['type'].iloc[0] == '매도': in_position = False
            single_coin_equity.loc[date] = last_equity
        
        single_coin_df = pd.DataFrame({'Total_Equity': single_coin_equity}).dropna()
        single_coin_df = calculate_mdd(single_coin_df, 'Total_Equity')
        
        axs[1].fill_between(single_coin_df.index, single_coin_df['Total_Drawdown'] * 100, 0, color='skyblue', alpha=0.3, label='Drawdown')
        axs[1].plot(single_coin_df.index, single_coin_df['Total_MaxDrawdown'] * 100, label='MDD', color='blue', linestyle=':')
        axs[1].set_title('Individual Performance & MDD', fontsize=12)
        axs[1].set_ylabel('Drawdown (%)'); axs[1].grid(True); axs[1].legend()
        axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
        canvas.draw()


# --- 메인 실행 블록 ---
if __name__ == "__main__":
    print("백테스팅 계산 완료. 결과 분석 및 차트를 준비합니다...")

    # --- 기존 로그 출력 부분 (복원) ---
    print("\n\n" + "="*50)
    print("--- 일일 잔액 로그 ---")
    print("="*50)
    for log in balance_logs:
        print(log)
    print("\n\n" + "="*50)
    print("--- 매수/매도 로그 ---")
    print("="*50)
    if not trade_logs:
        print("거래 내역이 없습니다.")
    else:
        for log in trade_logs:
            print(log)
    print("="*50)

    # --- 차트 윈도우 실행 ---
    if result_df.empty:
        print("결과 데이터가 없어 차트를 생성할 수 없습니다.")
    else:
        app = ChartApp()
        app.mainloop()

    # --- 최종 통계 결과 출력 (복원) ---
    print("\n차트 창이 닫혔습니다. 최종 통계 결과를 출력합니다.")
    if not result_df.empty:
        TotalOri = result_df['Total_Equity'].iloc[0]
        TotalFinal = result_df['Total_Equity'].iloc[-1]
        TotalMDD = result_df['Total_MaxDrawdown'].min() * 100.0
        CashOnlyMDD = result_df['Cash_Only_MaxDrawdown'].min() * 100.0
        ModifiedMDD = result_df['Modified_MaxDrawdown'].min() * 100.0
        weekly_equity_df = result_df['Total_Equity'].resample('W-SUN').last().to_frame()
        weekly_equity_df = calculate_mdd(weekly_equity_df, 'Total_Equity')
        monthly_equity_for_mdd_df = result_df['Total_Equity'].resample('ME').last().to_frame()
        monthly_equity_for_mdd_df = calculate_mdd(monthly_equity_for_mdd_df, 'Total_Equity')
        WeeklyMDD = weekly_equity_df['Total_MaxDrawdown'].min() * 100.0 if not weekly_equity_df.empty else 0
        MonthlyMDD = monthly_equity_for_mdd_df['Total_MaxDrawdown'].min() * 100.0 if not monthly_equity_for_mdd_df.empty else 0
        monthly_stats = result_df.resample('ME').agg({'Total_Equity': 'last'})
        monthly_stats.rename(columns={'Total_Equity': 'End_Equity'}, inplace=True)
        monthly_stats['Prev_Month_End_Equity'] = monthly_stats['End_Equity'].shift(1).fillna(TotalOri)
        monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Prev_Month_End_Equity']) - 1) * 100
        monthly_stats['Trades'] = 0
        for month_key_str, count in MonthlyTryCnt.items():
            for idx in monthly_stats.index:
                if idx.strftime('%Y-%m') == month_key_str:
                    monthly_stats.loc[idx, 'Trades'] = count
                    break
        monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]
        monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
        monthly_stats.index = monthly_stats.index.strftime('%Y-%m')
        yearly_stats = result_df.resample('YE').agg({'Total_Equity': ['first', 'last']})
        yearly_stats.columns = ['Start_Equity', 'End_Equity']
        yearly_stats['Return'] = ((yearly_stats['End_Equity'] / yearly_stats['Start_Equity']) - 1) * 100
        yearly_stats['Trades'] = 0
        for month_key_str, count in MonthlyTryCnt.items():
            year_str = month_key_str.split('-')[0]
            for idx in yearly_stats.index:
                if idx.strftime('%Y') == year_str:
                    yearly_stats.loc[idx, 'Trades'] += count
                    break
        yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]
        yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
        yearly_stats.index = yearly_stats.index.strftime('%Y')

        print("\n---------- 코인별 거래 통계 ----------")
        total_success_all, total_fail_all = 0, 0
        for ticker_stat in valid_tickers:
            stats = CoinStats[ticker_stat]
            success, fail = stats['SuccessCnt'], stats['FailCnt']
            total_success_all += success
            total_fail_all += fail
            total_trades = success + fail
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
    else:
        print("결과 DataFrame이 비어있어 최종 결과를 표시할 수 없습니다.")