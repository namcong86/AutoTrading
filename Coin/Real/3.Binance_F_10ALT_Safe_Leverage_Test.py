# -*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
바이낸스 ccxt 버전
pip3 install --upgrade ccxt==4.2.19
이렇게 버전을 맞춰주세요!
봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요!
https://blog.naver.com/zacra/222662884649
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
import matplotlib.pyplot as plt

# 시간 변환을 위한 헬퍼 함수 (선택 사항)
def ms_to_utc_str(timestamp_ms):
    return datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

# 분봉/일봉 캔들 정보를 가져오는 함수 (Gate.io 버전 적용)
def GetOhlcv2(exchange_obj, ticker_symbol, time_period, year=2019, month=1, day=1, hour=0, minute=0):
    # 시작 날짜 UTC 기준으로 설정
    start_date_dt = datetime.datetime(year, month, day, hour, minute, tzinfo=datetime.timezone.utc)
    current_since_ms = int(start_date_dt.timestamp() * 1000)
    
    all_ohlcv_data = []
    
    now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    
    calculated_interval_ms = 0
    # period 문자열을 기반으로 기본 interval_ms 미리 추정 (fallback 용)
    if time_period == '1d': calculated_interval_ms = 24 * 60 * 60 * 1000
    elif time_period == '1h': calculated_interval_ms = 60 * 60 * 1000
    elif time_period == '5m': calculated_interval_ms = 5 * 60 * 1000
    else: calculated_interval_ms = 24 * 60 * 60 * 1000 # 알 수 없는 경우 기본값 1일

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

            # 실제 데이터로부터 interval_ms 업데이트
            if len(ohlcv_batch) > 1:
                calculated_interval_ms = ohlcv_batch[1][0] - ohlcv_batch[0][0]

            last_candle_ts = ohlcv_batch[-1][0]
            next_fetch_since_ms = last_candle_ts + calculated_interval_ms

            print(f"Get Data for {ticker_symbol}... Last: {ms_to_utc_str(last_candle_ts)}, Next since: {ms_to_utc_str(next_fetch_since_ms)} UTC")

            if next_fetch_since_ms >= now_ms:
                print(f"{ticker_symbol}의 다음 'since' ({ms_to_utc_str(next_fetch_since_ms)})가 미래입니다. 추가 가져오기를 중단합니다.")
                break
            
            current_since_ms = next_fetch_since_ms
            
            # 바이낸스는 rateLimit이 더 짧으므로 0.2초로 유지
            time.sleep(getattr(exchange_obj, 'rateLimit', 200) / 1000)

        except ccxt.RateLimitExceeded as e:
            print(f"요청 한도 초과 {ticker_symbol}: {e}. 잠시 후 재시도...")
            time.sleep(getattr(exchange_obj, 'rateLimit', 10000) / 1000)
        except ccxt.NetworkError as e:
            print(f"네트워크 오류 {ticker_symbol}: {e}. 5초 후 재시도...")
            time.sleep(5)
        except ccxt.ExchangeError as e:
            error_msg = str(e).lower()
            reason = "기타 거래소 오류"
            if "invalid time range" in error_msg or "invalid_param_value" in error_msg:
                reason = "유효하지 않은 시간 범위"
            print(f"거래소 오류 ({reason}) {ticker_symbol} (since {ms_to_utc_str(current_since_ms)}): {e}. 중단합니다.")
            break
        except Exception as e:
            print(f"예상치 못한 오류 {ticker_symbol} (since {ms_to_utc_str(current_since_ms)}): {e}. 중단합니다.")
            break

    if not all_ohlcv_data:
        print(f"{ticker_symbol}에 대해 가져온 데이터가 없습니다.")
        return pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

    df = pd.DataFrame(all_ohlcv_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df = df.set_index('datetime').sort_index()
    df = df[~df.index.duplicated(keep='first')]
    return df

# 바이낸스 객체 생성
Binance_AccessKey = "3L5mMgSFzt8HlPt6daAIzLxRTqFPaA1ItKMYNgNdgNkBOtBmlUMDzefQAK1UMs4J"
Binance_ScretKey = "CXNpmRpSGpH9BXjkIbqKMtp1icekWPsTyIEhC0OcPrzclKnai9ATzrH3BVHUI9zL"
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey,
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

InvestTotalMoney = 5000
leverage = 3 # 레버리지 5배 설정 (Gate.io와 동일하게)
fee = 0.001

# 투자 종목 설정 (Gate.io와 동일하게, 티커는 바이낸스에 맞게 수정)
InvestCoinList = [

    # {'ticker': 'DOGE/USDT', 'rate': 0.3, 'start_date': {'year': 2022, 'month': 6, 'day': 1}},
    # {'ticker': 'ADA/USDT',  'rate': 0.2, 'start_date': {'year': 2022, 'month': 6, 'day': 1}},
    # {'ticker': 'XLM/USDT', 'rate': 0.15, 'start_date': {'year': 2022, 'month': 6, 'day': 1}},
    # {'ticker': 'XRP/USDT', 'rate': 0.15, 'start_date': {'year': 2022, 'month': 6, 'day': 1}},
    # {'ticker': 'HBAR/USDT', 'rate': 0.2, 'start_date': {'year': 2022, 'month': 6, 'day': 1}},
    # {'ticker': '1000PEPE/USDT', 'rate': 0.125, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},
    # {'ticker': '1000BONK/USDT', 'rate': 0.125, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},

    {'ticker': 'DOGE/USDT', 'rate': 0.1, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'ADA/USDT',  'rate': 0.09, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XLM/USDT', 'rate': 0.09, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XRP/USDT', 'rate': 0.09, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'HBAR/USDT', 'rate': 0.09, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'ETH/USDT', 'rate': 0.09, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    {'ticker': '1000PEPE/USDT', 'rate': 0.09, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},
    {'ticker': '1000BONK/USDT', 'rate': 0.09, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},
    {'ticker': 'SUI/USDT', 'rate': 0.09, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    {'ticker': '1000FLOKI/USDT', 'rate': 0.09, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
    {'ticker': '1000SHIB/USDT', 'rate': 0.09, 'start_date': {'year': 2021, 'month': 7, 'day': 1}},
]


# 데이터 가져오기 및 전처리
dfs = {}
for coin_data in InvestCoinList:
    ticker = coin_data['ticker']
    start_date_params = coin_data['start_date']
    print(f"Fetching data for {ticker} from {start_date_params['year']}-{start_date_params['month']}-{start_date_params['day']}...")
    df = GetOhlcv2(binanceX, ticker, '1d', start_date_params['year'], start_date_params['month'], start_date_params['day'], 0, 0)

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
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    # Disparity Index 계산 (종가 / 15일 이동평균 * 100)
    df['Disparity_Index_ma'] = df['close'].rolling(window=16).mean()
    df['disparity_index'] = (df['close'] / df['Disparity_Index_ma']) * 100

    df.dropna(inplace=True)
    if not df.empty:
        dfs[ticker] = df
    else:
        print(f"DataFrame for {ticker} became empty after dropping NA. Check data and indicator periods.")

if not dfs:
    print("No data loaded for any coin. Exiting.")
    exit()

valid_tickers = [coin['ticker'] for coin in InvestCoinList if coin['ticker'] in dfs]
if not valid_tickers:
    print("No valid data to process after fetching and pre-processing. Exiting.")
    exit()

common_dates = set(dfs[valid_tickers[0]].index)
for ticker in valid_tickers[1:]:
    common_dates = common_dates.intersection(set(dfs[ticker].index))

if not common_dates:
    print("No common dates found for the provided tickers. Check data ranges and availability. Exiting.")
    exit()
common_dates = sorted(list(common_dates))

# 초기 설정 (Gate.io 스크립트 방식 적용)
cash_balance = InvestTotalMoney
current_cycle_investment_base = InvestTotalMoney # 사이클 기준 자본
positions = {}
total_equity_list = []
cash_only_equity_list = []
modified_equity_list = []
last_cash_only_equity = InvestTotalMoney
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in valid_tickers}

# 로그 저장을 위한 리스트 초기화
balance_logs = []
trade_logs = []

# 백테스팅 루프
for date in common_dates:
    current_data = {ticker: dfs[ticker].loc[date] for ticker in valid_tickers if date in dfs[ticker].index}
    if len(current_data) != len(valid_tickers):
        continue
    
    sold_today_tickers = set()

    # 1. 보유 중인 코인의 매도 조건 확인 (Gate.io 로직 적용)
    for ticker in list(positions.keys()):
        if ticker not in current_data: continue

        position = positions[ticker]
        margin = position['margin']
        entry_price = position['entry_price']
        pos_leverage = position['leverage']
        current_price = current_data[ticker]['open']

        if date not in dfs[ticker].index: continue
        i = dfs[ticker].index.get_loc(date)

        if i >= 2:
            df_coin = dfs[ticker]
            RevenueRate = ((current_price - entry_price) / entry_price * pos_leverage - fee) * 100.0

            def is_doji_candle(open_price, close_price, high_price, low_price):
                candle_range = high_price - low_price
                if candle_range == 0:
                    return False
                gap = abs(open_price - close_price)
                return (gap / candle_range) <= 0.1

            is_doji_1 = is_doji_candle(df_coin['open'].iloc[i-1], df_coin['close'].iloc[i-1], df_coin['high'].iloc[i-1], df_coin['low'].iloc[i-1])
            is_doji_2 = is_doji_candle(df_coin['open'].iloc[i-2], df_coin['close'].iloc[i-2], df_coin['high'].iloc[i-2], df_coin['low'].iloc[i-2])

            sell_condition_triggered = False
            if (((df_coin['high'].iloc[i-2] > df_coin['high'].iloc[i-1] and df_coin['low'].iloc[i-2] > df_coin['low'].iloc[i-1]) or
                (df_coin['open'].iloc[i-1] > df_coin['close'].iloc[i-1] and df_coin['open'].iloc[i-2] > df_coin['close'].iloc[i-2]) or
                RevenueRate < 0) and not (i >= 2 and df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and df_coin['3ma'].iloc[i-2] < df_coin['3ma'].iloc[i-1])):
                sell_condition_triggered = True

            if (is_doji_1 and is_doji_2):
                sell_condition_triggered = True

            if sell_condition_triggered:
                # Gate.io 스크립트의 수익 계산 방식은 수수료를 수익률 계산에 포함하므로, 바이낸스 스크립트에서도 동일하게 적용
                # cash_balance += margin * (1 + RevenueRate / 100.0) -> 아래 코드는 이를 풀어서 쓴 것
                price_change = (current_price - entry_price) / entry_price * pos_leverage
                realized_value = margin * (1 + price_change)
                cash_balance += realized_value
                
                log_msg = f"{ticker} {date} >>> 매도: Entry {entry_price:.8f}, Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)

                if RevenueRate > 0:
                    CoinStats[ticker]['SuccessCnt'] += 1
                else:
                    CoinStats[ticker]['FailCnt'] += 1

                del positions[ticker]
                sold_today_tickers.add(ticker)
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
    
    if not positions:
        current_cycle_investment_base = cash_balance

    # 2. 매수 신호 확인 및 실행 (Gate.io 로직 적용)
    buy_signals_today_specs = []
    for coin_candidate_spec in InvestCoinList:
        ticker = coin_candidate_spec['ticker']
        if ticker not in positions and ticker not in sold_today_tickers and ticker in dfs and date in dfs[ticker].index:
            df_coin = dfs[ticker]
            i = df_coin.index.get_loc(date)

            if i > 2:
                prev_day_change = df_coin['change'].iloc[i-1]
                no_sudden_surge = prev_day_change < 0.5
                is_above_200ma = df_coin['close'].iloc[i-1] > df_coin['200ma'].iloc[i-1]

                # ==============================================================================
                # <<< 신규 매수 조건 추가 >>>
                # ==============================================================================
                ma_50_condition = True 
                cond_no_long_upper_shadow = True
                cond_body_over_15_percent = True
                
                if is_above_200ma:
                    # 1. 50일 이평선 하락 아님
                    ma_50_condition = df_coin['50ma'].iloc[i-2] <= df_coin['50ma'].iloc[i-1]

                    # 2. 긴 윗꼬리 없음
                    prev_candle = df_coin.iloc[i-1] # 전일자 캔들
                    upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
                    body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
                    cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
                    
                    # 3. 캔들 몸통이 전체 길이의 15% 이상
                    candle_range = prev_candle['high'] - prev_candle['low']
                    candle_body = abs(prev_candle['open'] - prev_candle['close'])
                    if candle_range > 0:
                        cond_body_over_15_percent = (candle_body >= candle_range * 0.15)
                # ==============================================================================
                
                # Disparity Index 조건 (30일 기준) - 오늘 미포함
                disparity_period = 25
                filter_disparity = False
                
                if i >= disparity_period:
                    recent_disparity = df_coin['disparity_index'].iloc[i-disparity_period:i]
                    yesterday_disparity = df_coin['disparity_index'].iloc[i-1]
                    max_disparity = recent_disparity.max()
                    
                    if yesterday_disparity == max_disparity:
                        filter_disparity = True
                    else:
                        try:
                            max_idx = recent_disparity.idxmax()
                            yesterday_idx = df_coin.index[i-1]
                            if max_idx < yesterday_idx:
                                range_disparity = df_coin.loc[max_idx:yesterday_idx, 'disparity_index']
                                if (range_disparity >= 100).all():
                                    filter_disparity = True
                        except Exception:
                            filter_disparity = False
                else:
                    filter_disparity = True

                # ==============================================================================
                # <<< 최종 매수 결정 로직에 신규 조건 반영 >>>
                # ==============================================================================
                if (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and
                    df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2] and
                    df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and
                    df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1] and
                    df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and                    
                    df_coin['30ma_slope'].iloc[i-1] > -2 and
                    df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and 
                    ma_50_condition and
                    df_coin['20ma'].iloc[i-2] <= df_coin['20ma'].iloc[i-1] and
                    no_sudden_surge and
                    filter_disparity and
                    cond_no_long_upper_shadow and      #<-- 추가
                    cond_body_over_15_percent          #<-- 추가
                    ):
                    buy_signals_today_specs.append(coin_candidate_spec)
                # ==============================================================================

    if buy_signals_today_specs:
        total_coin_count = len(InvestCoinList)

        for coin_spec_to_buy in buy_signals_today_specs:
            ticker = coin_spec_to_buy['ticker']
            buy_price = current_data[ticker]['open']
            
            allocated_investment = current_cycle_investment_base * coin_spec_to_buy['rate']
            investment_for_this_coin = allocated_investment

            num_open_positions = len(positions)
            is_last_coin_to_fill_portfolio = (num_open_positions == (total_coin_count - 1))

            if is_last_coin_to_fill_portfolio and allocated_investment > cash_balance:
                investment_for_this_coin = cash_balance
            
            if cash_balance >= investment_for_this_coin and investment_for_this_coin > 0:
                quantity = (investment_for_this_coin * leverage) / buy_price
                positions[ticker] = {
                    'margin': investment_for_this_coin,
                    'entry_price': buy_price,
                    'quantity': quantity,
                    'leverage': leverage
                }
                cash_balance -= investment_for_this_coin

                log_msg = f"{ticker} {date} >>> 매수: 가격 {buy_price:.8f}, 투자금 {investment_for_this_coin:.2f}, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)

            else:
                log_msg = f"Warning: Not enough cash to open position for {ticker} on {date}. Required: {investment_for_this_coin:.2f}, Available: {cash_balance:.2f}"
                trade_logs.append(log_msg)

    # 3. 일일 자산 가치 계산 (Gate.io 로직 적용)
    daily_total_equity = cash_balance
    for ticker, position in positions.items():
        if ticker not in current_data: continue
        margin = position['margin']
        entry_price = position['entry_price']
        current_close_price = current_data[ticker]['close']
        # 바이낸스 수량은 정수가 아닐 수 있으므로 quantity 직접 사용
        quantity = position['quantity']
        unrealized_pnl = (current_close_price - entry_price) * quantity
        position_current_value = margin + unrealized_pnl
        daily_total_equity += position_current_value
    total_equity_list.append({'date': date, 'Total_Equity': daily_total_equity})

    if not positions:
        last_cash_only_equity = cash_balance
    cash_only_equity_list.append({'date': date, 'Cash_Only_Equity': last_cash_only_equity})

    daily_modified_equity = cash_balance
    for ticker, position in positions.items():
        daily_modified_equity += position['margin']
    modified_equity_list.append({'date': date, 'Modified_Equity': daily_modified_equity})

    log_msg = f"--- {date.strftime('%Y-%m-%d')} | 일일 정산 --- 총자산: {daily_total_equity:,.0f} USDT"
    balance_logs.append(log_msg)

# (이하 결과 분석, 통계, 그래프 출력 로직은 기존과 동일하므로 생략합니다)
# ...
# ...
# ...

# 저장된 로그 출력
print("\n\n" + "="*50)
print("--- 일일 잔액 로그 ---")
print("="*50)
for log in balance_logs:
    print(log)

# ==============================================================================
# ▼▼▼ 오늘 기준 (어제자 마감 캔들) 진입조건 상세 로그 출력 ▼▼▼
# ==============================================================================
print("\n" + "="*70)
print("--- 오늘 기준 진입조건 상세 (어제자 마감 캔들 기준) ---")
print("="*70)

for ticker in valid_tickers:
    if ticker not in dfs:
        continue
    df_coin = dfs[ticker]
    if len(df_coin) < 3:
        print(f"\n[{ticker}] 데이터 부족으로 조건 확인 불가")
        continue
    
    # 마지막 인덱스 (오늘 기준)
    i = len(df_coin) - 1
    last_date = df_coin.index[i]
    
    print(f"\n{'='*50}")
    print(f"[{ticker}] 기준일: {last_date.strftime('%Y-%m-%d')}")
    print(f"{'='*50}")
    
    # --- 기본 매수 조건 ---
    cond_2_pos_candle = (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and 
                        df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2])
    cond_price_up = (df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and 
                     df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1])
    cond_7ma_up = (df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1])
    cond_30ma_slope = (df_coin['30ma_slope'].iloc[i-1] > -2)
    cond_rsi_ma_up = (df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1])
    cond_20ma_up = (df_coin['20ma'].iloc[i-2] <= df_coin['20ma'].iloc[i-1])
    cond_no_surge = (df_coin['change'].iloc[i-1] < 0.5)
    
    # Disparity Index 조건 - 오늘 미포함
    disparity_period = 30
    filter_disparity = False
    disparity_detail = ""
    
    if i >= disparity_period:
        recent_disparity = df_coin['disparity_index'].iloc[i-disparity_period:i]
        yesterday_disparity = df_coin['disparity_index'].iloc[i-1]
        max_disparity = recent_disparity.max()
        
        if yesterday_disparity == max_disparity:
            filter_disparity = True
            disparity_detail = f"전일값({yesterday_disparity:.2f})이 {disparity_period}일 최고값"
        else:
            try:
                max_idx = recent_disparity.idxmax()
                yesterday_idx = df_coin.index[i-1]
                if max_idx < yesterday_idx:
                    range_disparity = df_coin.loc[max_idx:yesterday_idx, 'disparity_index']
                    if (range_disparity >= 100).all():
                        filter_disparity = True
                        disparity_detail = f"최고값~전일 모두 100 이상"
                    else:
                        disparity_detail = f"최고값~전일 중 100 미만 존재"
                else:
                    disparity_detail = f"최고값이 전일 이후"
            except Exception:
                disparity_detail = "계산 오류"
    else:
        filter_disparity = True
        disparity_detail = f"{disparity_period}일 데이터 부족 (통과)"
    
    # 200MA 위치 판단 및 추가 조건
    is_above_200ma = df_coin['close'].iloc[i-1] > df_coin['200ma'].iloc[i-1]
    cond_ma_50 = True
    cond_no_long_upper_shadow = True
    cond_body_over_15_percent = True
    
    if is_above_200ma:
        cond_ma_50 = (df_coin['50ma'].iloc[i-2] <= df_coin['50ma'].iloc[i-1])
        prev_candle = df_coin.iloc[i-1]
        upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
        body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
        cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
        candle_range = prev_candle['high'] - prev_candle['low']
        candle_body = abs(prev_candle['open'] - prev_candle['close'])
        if candle_range > 0:
            cond_body_over_15_percent = (candle_body >= candle_range * 0.15)
    
    # 최종 결정
    buy = (cond_2_pos_candle and cond_price_up and cond_7ma_up and cond_30ma_slope and
           cond_rsi_ma_up and cond_ma_50 and cond_20ma_up and cond_no_surge and
           filter_disparity and cond_no_long_upper_shadow and cond_body_over_15_percent)
    
    def bool_to_str(val):
        return "✅ True" if val else "❌ False"
    
    print(f"▶ 최종 매수 결정: {bool_to_str(buy)}")
    print(f"--------------------")
    print(f" 1. 2연속 양봉: {cond_2_pos_candle}")
    print(f" 2. 전일 종가/고가 상승: {cond_price_up}")
    print(f" 3. 7ma 상승: {cond_7ma_up}")
    print(f" 4. 30ma 기울기 > -2: {cond_30ma_slope}")
    print(f" 5. RSI_MA 상승: {cond_rsi_ma_up}")
    print(f" 6. 50ma 조건 충족: {cond_ma_50}")
    print(f" 7. 20ma 상승: {cond_20ma_up}")
    print(f" 8. 급등 아님: {cond_no_surge}")
    print(f" 9. Disparity Index 조건: {filter_disparity}")
    print(f" 10. 긴 윗꼬리 없음: {cond_no_long_upper_shadow}")
    print(f" 11. 캔들 몸통 15% 이상: {cond_body_over_15_percent}")

print("\n" + "="*70)
# ==============================================================================
# ▲▲▲ 오늘 기준 진입조건 상세 로그 출력 끝 ▲▲▲
# ==============================================================================

print("\n\n" + "="*50)
print("--- 매수/매도 로그 ---")
print("="*50)
if not trade_logs:
    print("거래 내역이 없습니다.")
else:
    for log in trade_logs:
        print(log)
print("="*50)

# 결과 분석 (Gate.io 로직 적용)
if not total_equity_list:
    print("No trades were made or no equity data to process. Exiting.")
    exit()

result_df = pd.DataFrame(total_equity_list)
result_df.set_index('date', inplace=True)

cash_only_df = pd.DataFrame(cash_only_equity_list).set_index('date')
modified_df = pd.DataFrame(modified_equity_list).set_index('date')
result_df = result_df.join(cash_only_df).join(modified_df)

# ==============================================================================
# <<< 코드 수정: 안정성을 위해 calculate_mdd 함수 개선 >>>
# ==============================================================================
def calculate_mdd(df, column_name):
    prefix = column_name.replace('_Equity', '')
    ror_col, cum_ror_col, hw_col, dd_col, mdd_col = f'{prefix}_Ror', f'{prefix}_Cum_Ror', f'{prefix}_Highwatermark', f'{prefix}_Drawdown', f'{prefix}_MaxDrawdown'
    
    # 데이터가 비어 있거나 행이 하나뿐인 경우 처리
    if df.empty or len(df) < 2:
        df[ror_col] = 1.0
        df[cum_ror_col] = df[column_name] / df[column_name].iloc[0] if not df.empty else 1.0
        df[hw_col] = df[cum_ror_col] if not df.empty else 1.0
        df[dd_col] = 0.0
        df[mdd_col] = 0.0
        return df

    df[ror_col] = df[column_name].pct_change().fillna(0) + 1
    df[cum_ror_col] = df[ror_col].cumprod()
    df[hw_col] = df[cum_ror_col].cummax()
    df[dd_col] = (df[cum_ror_col] / df[hw_col]) - 1
    df[mdd_col] = df[dd_col].cummin()
    return df
# ==============================================================================


result_df = calculate_mdd(result_df, 'Total_Equity')
result_df = calculate_mdd(result_df, 'Cash_Only_Equity')
result_df = calculate_mdd(result_df, 'Modified_Equity')

# ==============================================================================
# <<< 코드 추가: 주간/월간 MDD 계산 >>>
# ==============================================================================
# 주간 잔액 (매주 일요일 종가 기준)
weekly_equity_df = result_df['Total_Equity'].resample('W-SUN').last().to_frame()
weekly_equity_df = calculate_mdd(weekly_equity_df, 'Total_Equity')

# 월간 잔액 (매월 말일 종가 기준)
monthly_equity_for_mdd_df = result_df['Total_Equity'].resample('ME').last().to_frame()
monthly_equity_for_mdd_df = calculate_mdd(monthly_equity_for_mdd_df, 'Total_Equity')
# ==============================================================================


result_df.index = pd.to_datetime(result_df.index)

# 월별/연도별 통계 (Gate.io 로직 적용)
monthly_stats = result_df.resample('ME').agg({'Total_Equity': 'last'})
monthly_stats.rename(columns={'Total_Equity': 'End_Equity'}, inplace=True)
monthly_stats['Prev_Month_End_Equity'] = monthly_stats['End_Equity'].shift(1)
initial_equity = result_df['Total_Equity'].iloc[0]
monthly_stats['Prev_Month_End_Equity'] = monthly_stats['Prev_Month_End_Equity'].fillna(initial_equity)
monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Prev_Month_End_Equity']) - 1) * 100

monthly_stats['Trades'] = 0
for month_key_str, count in MonthlyTryCnt.items():
    try:
        month_dt = pd.to_datetime(month_key_str + '-01')
        target_idx = monthly_stats.index[(monthly_stats.index.year == month_dt.year) & (monthly_stats.index.month == month_dt.month)]
        if not target_idx.empty:
             monthly_stats.loc[target_idx[0], 'Trades'] = count
        else:
            for idx in monthly_stats.index:
                if idx.strftime('%Y-%m') == month_key_str:
                    monthly_stats.loc[idx, 'Trades'] = count
                    break
    except Exception as e:
        print(f"월별 통계 거래 횟수 업데이트 중 오류: {e} (월: {month_key_str})")
        continue

monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]
monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
monthly_stats['잔액 (USDT)'] = monthly_stats['잔액 (USDT)'].round(2)
monthly_stats.index = monthly_stats.index.strftime('%Y-%m')

yearly_stats = result_df.resample('YE').agg({'Total_Equity': ['first', 'last']})
yearly_stats.columns = ['Start_Equity', 'End_Equity']
yearly_stats['Return'] = ((yearly_stats['End_Equity'] / yearly_stats['Start_Equity']) - 1) * 100
yearly_stats['Trades'] = 0

for month_key_str, count in MonthlyTryCnt.items():
    try:
        year_str = month_key_str.split('-')[0]
        target_idx = yearly_stats.index[yearly_stats.index.year == int(year_str)]
        if not target_idx.empty:
            yearly_stats.loc[target_idx[0], 'Trades'] += count
        else:
            for idx in yearly_stats.index:
                if idx.strftime('%Y') == year_str:
                    yearly_stats.loc[idx, 'Trades'] += count
                    break
    except Exception as e:
        print(f"연도별 통계 거래 횟수 업데이트 중 오류: {e} (월: {month_key_str})")
        continue

yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]
yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
yearly_stats['잔액 (USDT)'] = yearly_stats['잔액 (USDT)'].round(2)
yearly_stats.index = yearly_stats.index.strftime('%Y')

# 코인별 거래 통계 및 총 합계
print("\n---------- 코인별 거래 통계 ----------")
total_success_all = 0
total_fail_all = 0

for ticker_stat in valid_tickers:
    stats = CoinStats[ticker_stat]
    success = stats['SuccessCnt']
    fail = stats['FailCnt']
    
    total_success_all += success
    total_fail_all += fail
    
    total_trades = success + fail
    win_rate = (success / total_trades * 100) if total_trades > 0 else 0
    print(f"{ticker_stat} >>> 성공: {success} 실패: {fail} -> 승률: {round(win_rate, 2)}%")

total_trades_all = total_success_all + total_fail_all
overall_win_rate = (total_success_all / total_trades_all * 100) if total_trades_all > 0 else 0
print(f"총 합계 >>> 성공: {total_success_all} 실패: {total_fail_all} -> 승률: {round(overall_win_rate, 2)}%")
print("------------------------------")


# 그래프 생성 (Gate.io 로직 적용)
fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
plt.style.use('seaborn-v0_8-whitegrid')

axs[0].plot(result_df.index, result_df['Total_Cum_Ror'] * 100, label=f'Strategy ({leverage}x Leverage)', color='black')
axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Return & Drawdown Comparison')
axs[0].legend(loc='upper left')
axs[0].grid(True)

axs[1].fill_between(result_df.index, result_df['Total_Drawdown'] * 100, 0, color='skyblue', alpha=0.3, label='Drawdown 1 (Daily Mark-to-Market)')
axs[1].plot(result_df.index, result_df['Total_MaxDrawdown'] * 100, label='MDD 1', color='blue', linestyle=':')
axs[1].plot(result_df.index, result_df['Cash_Only_Drawdown'] * 100, label='Drawdown 2 (Cash Balance When Flat)', color='mediumseagreen', linestyle='-')
axs[1].plot(result_df.index, result_df['Cash_Only_MaxDrawdown'] * 100, label='MDD 2', color='darkgreen', linestyle=':')
axs[1].plot(result_df.index, result_df['Modified_Drawdown'] * 100, label='Drawdown 3 (Principal + Cash)', color='orange', linestyle='-')
axs[1].plot(result_df.index, result_df['Modified_MaxDrawdown'] * 100, label='MDD 3', color='darkorange', linestyle=':')
axs[1].set_ylabel('Drawdown (%)')
axs[1].set_title('Drawdown & MDD Comparison (3 Methods)')
axs[1].legend(loc='lower left')
axs[1].grid(True)

plt.xlabel('Date')
plt.tight_layout()
import socket
pcServerGb = socket.gethostname()
if pcServerGb != "AutoBotCong":
    plt.show()
else:
    print("서버 환경이므로 차트 표시를 생략합니다.")


# 최종 결과 출력 (Gate.io 로직 적용)
if not result_df.empty:
    TotalOri = result_df['Total_Equity'].iloc[0]
    TotalFinal = result_df['Total_Equity'].iloc[-1]
    
    TotalMDD = result_df['Total_MaxDrawdown'].min() * 100.0
    CashOnlyMDD = result_df['Cash_Only_MaxDrawdown'].min() * 100.0
    ModifiedMDD = result_df['Modified_MaxDrawdown'].min() * 100.0
    
    # ==============================================================================
    # <<< 코드 추가: 주간/월간 MDD 값 추출 및 결과 출력 >>>
    # ==============================================================================
    WeeklyMDD = weekly_equity_df['Total_MaxDrawdown'].min() * 100.0 if not weekly_equity_df.empty else 0
    MonthlyMDD = monthly_equity_for_mdd_df['Total_MaxDrawdown'].min() * 100.0 if not monthly_equity_for_mdd_df.empty else 0

    print("\n---------- 총 결과 ----------")
    print(f"최초 금액: {format(round(TotalOri), ',')} USDT, 최종 금액: {format(round(TotalFinal), ',')} USDT")
    print(f"총 수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
    print(f"MDD 1 (일일 시가평가 기준): {round(TotalMDD, 2)}%")
    print(f"MDD 2 (포지션 없을 시 잔액 기준): {round(CashOnlyMDD, 2)}%")
    print(f"MDD 3 (포지션 원금 + 잔액 기준): {round(ModifiedMDD, 2)}%")
    print(f"MDD 4 (주간 잔액 기준): {round(WeeklyMDD, 2)}%")
    print(f"MDD 5 (월간 잔액 기준): {round(MonthlyMDD, 2)}%")
    # ==============================================================================
    
    print("------------------------------")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
else:
    print("Result DataFrame is empty. No final results to display.")