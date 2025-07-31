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
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 시간 변환을 위한 헬퍼 함수 (선택 사항)
def ms_to_utc_str(timestamp_ms):
    return datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

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

            # 실제 데이터로부터 interval_ms 업데이트 (첫 성공적인 배치 후 한 번 또는 매번)
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

# Gate.io 객체 생성
GateIO_AccessKey = "YOUR_GATEIO_API_KEY"
GateIO_SecretKey = "YOUR_GATEIO_SECRET_KEY"

exchange = ccxt.gateio({
    'apiKey': GateIO_AccessKey,
    'secret': GateIO_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
    }
})

InvestTotalMoney = 5000
leverage = 5
fee = 0.001

InvestCoinList = [
    # {'ticker': 'DOGE/USDT', 'rate': 0.3, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'ADA/USDT',  'rate': 0.2, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'XLM/USDT', 'rate': 0.15, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'XRP/USDT', 'rate': 0.15, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    # {'ticker': 'HBAR/USDT', 'rate': 0.2, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},

    {'ticker': 'DOGE/USDT', 'rate': 0.25, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'ADA/USDT',  'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XLM/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'XRP/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'HBAR/USDT', 'rate': 0.125, 'start_date': {'year': 2022, 'month': 7, 'day': 1}},
    {'ticker': 'PEPE/USDT', 'rate': 0.125, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},
    {'ticker': 'BONK/USDT', 'rate': 0.125, 'start_date': {'year': 2023, 'month': 1, 'day': 1}},
    
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
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

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

# 초기 설정
cash_balance = InvestTotalMoney
current_cycle_investment_base = InvestTotalMoney # 사이클 기준 자본
positions = {}
total_equity_list = []
# MDD 계산을 위한 리스트 초기화
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

    # 1. 보유 중인 코인의 매도 조건 확인
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
                cash_balance += margin * (1 + RevenueRate / 100.0)
                
                log_msg = f"{ticker} {date} >>> 매도: Entry {entry_price:.8f}, Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}"
                trade_logs.append(log_msg)

                if RevenueRate > 0:
                    CoinStats[ticker]['SuccessCnt'] += 1
                else:
                    CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
    
    if not positions:
        current_cycle_investment_base = cash_balance

    # 2. 매수 신호 확인 및 실행
    buy_signals_today_specs = []
    for coin_candidate_spec in InvestCoinList:
        ticker = coin_candidate_spec['ticker']
        if ticker not in positions and ticker in dfs and date in dfs[ticker].index:
            df_coin = dfs[ticker]
            i = df_coin.index.get_loc(date)

            if i > 2:
                prev_day_change = df_coin['change'].iloc[i-1]
                no_sudden_surge = prev_day_change < 0.5

                is_above_200ma = df_coin['close'].iloc[i-1] > df_coin['200ma'].iloc[i-1]

                ma_50_condition = True 
                if is_above_200ma:
                    ma_50_condition = df_coin['50ma'].iloc[i-2] <= df_coin['50ma'].iloc[i-1]

                if (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and
                    df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2] and
                    df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and
                    df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1] and
                    df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and                    
                    df_coin['30ma_slope'].iloc[i-1] > -2 and
                    df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and 
                    ma_50_condition and
                    df_coin['20ma'].iloc[i-2] <= df_coin['20ma'].iloc[i-1] and
                    no_sudden_surge
                    ):
                    buy_signals_today_specs.append(coin_candidate_spec)

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

    # 3. 일일 자산 가치 계산 (3가지 방식)
    daily_total_equity = cash_balance
    for ticker, position in positions.items():
        if ticker not in current_data: continue
        margin = position['margin']
        entry_price = position['entry_price']
        current_close_price = current_data[ticker]['close']
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

# 저장된 로그 출력
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

# 결과 분석
if not total_equity_list:
    print("No trades were made or no equity data to process. Exiting.")
    exit()

result_df = pd.DataFrame(total_equity_list)
result_df.set_index('date', inplace=True)

cash_only_df = pd.DataFrame(cash_only_equity_list).set_index('date')
modified_df = pd.DataFrame(modified_equity_list).set_index('date')
result_df = result_df.join(cash_only_df).join(modified_df)

result_df['Ror'] = result_df['Total_Equity'].pct_change().fillna(0) + 1
result_df['Cum_Ror'] = result_df['Ror'].cumprod()
result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

result_df['Cash_Only_Ror'] = result_df['Cash_Only_Equity'].pct_change().fillna(0) + 1
result_df['Cash_Only_Cum_Ror'] = result_df['Cash_Only_Ror'].cumprod()
result_df['Cash_Only_Highwatermark'] = result_df['Cash_Only_Cum_Ror'].cummax()
result_df['Cash_Only_Drawdown'] = (result_df['Cash_Only_Cum_Ror'] / result_df['Cash_Only_Highwatermark']) - 1
result_df['Cash_Only_MaxDrawdown'] = result_df['Cash_Only_Drawdown'].cummin()

result_df['Modified_Ror'] = result_df['Modified_Equity'].pct_change().fillna(0) + 1
result_df['Modified_Cum_Ror'] = result_df['Modified_Ror'].cumprod()
result_df['Modified_Highwatermark'] = result_df['Modified_Cum_Ror'].cummax()
result_df['Modified_Drawdown'] = (result_df['Modified_Cum_Ror'] / result_df['Modified_Highwatermark']) - 1
result_df['Modified_MaxDrawdown'] = result_df['Modified_Drawdown'].cummin()

result_df.index = pd.to_datetime(result_df.index)

# 월별 수익률 계산
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


yearly_stats = result_df.resample('YE').agg(
    {'Total_Equity': ['first', 'last']}
)
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

print("\n---------- 코인별 거래 통계 ----------")
for ticker_stat in valid_tickers:
    stats = CoinStats[ticker_stat]
    success = stats['SuccessCnt']
    fail = stats['FailCnt']
    total_trades = success + fail
    win_rate = (success / total_trades * 100) if total_trades > 0 else 0
    print(f"{ticker_stat} >>> 성공: {success} 실패: {fail} -> 승률: {round(win_rate, 2)}%")
print("------------------------------")

# ==============================================================================
# <<< 코드 수정: 3가지 MDD를 모두 차트에 표시 >>>
# ==============================================================================
fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
initial_equity_val = result_df['Total_Equity'].iloc[0]

# 상단 차트: 누적 수익률
axs[0].plot(result_df.index, result_df['Cum_Ror'] * 100, label=f'Strategy ({leverage}x Leverage)')
axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Return Comparison Chart')
axs[0].legend()
axs[0].grid(True)

# 하단 차트: 3가지 방식의 최대 낙폭(MDD) 비교
axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD 1 (일일 시가평가)', alpha=0.9)
axs[1].plot(result_df.index, result_df['Cash_Only_MaxDrawdown'] * 100, label='MDD 2 (포지션 없을 시 잔액)', alpha=0.7)
axs[1].plot(result_df.index, result_df['Modified_MaxDrawdown'] * 100, label='MDD 3 (포지션 원금 + 잔액)', alpha=0.7)
axs[1].fill_between(result_df.index, result_df['Drawdown'] * 100, 0, color='red', alpha=0.1, label='Drawdown (일일 시가평가)')


axs[1].set_ylabel('Drawdown (%)')
axs[1].set_title('3가지 방식 최대 낙폭(MDD) 비교')
axs[1].legend()
axs[1].grid(True)

plt.xlabel('Date')
plt.tight_layout()
plt.show()
# ==============================================================================


# 최종 결과에 3가지 MDD 출력
if not result_df.empty:
    TotalOri = result_df['Total_Equity'].iloc[0]
    TotalFinal = result_df['Total_Equity'].iloc[-1]
    
    # 3가지 MDD 계산
    TotalMDD = result_df['MaxDrawdown'].min() * 100.0
    CashOnlyMDD = result_df['Cash_Only_MaxDrawdown'].min() * 100.0
    ModifiedMDD = result_df['Modified_MaxDrawdown'].min() * 100.0

    print("\n---------- 총 결과 ----------")
    print(f"최초 금액: {format(round(TotalOri), ',')} USDT, 최종 금액: {format(round(TotalFinal), ',')} USDT")
    print(f"총 수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
    print(f"MDD 1 (일일 시가평가 기준): {round(TotalMDD, 2)}%")
    print(f"MDD 2 (포지션 없을 시 잔액 기준): {round(CashOnlyMDD, 2)}%")
    print(f"MDD 3 (포지션 원금 + 잔액 기준): {round(ModifiedMDD, 2)}%")
    print("------------------------------")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
else:
    print("Result DataFrame is empty. No final results to display.")