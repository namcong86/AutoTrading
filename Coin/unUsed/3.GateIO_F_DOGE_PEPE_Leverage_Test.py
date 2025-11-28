#-*-coding:utf-8 -*-
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
            # (만약 interval_ms가 항상 일정하다고 가정하면, 이 부분은 한 번만 실행되도록 최적화 가능)

            last_candle_ts = ohlcv_batch[-1][0]
            next_fetch_since_ms = last_candle_ts + calculated_interval_ms

            print(f"Get Data for {ticker_symbol}... Last: {ms_to_utc_str(last_candle_ts)}, Next since: {ms_to_utc_str(next_fetch_since_ms)} UTC")

            if next_fetch_since_ms >= now_ms:
                print(f"{ticker_symbol}의 다음 'since' ({ms_to_utc_str(next_fetch_since_ms)})가 미래입니다. 추가 가져오기를 중단합니다.")
                break
            
            current_since_ms = next_fetch_since_ms
            
            # API 요청 간격 조절
            time.sleep(getattr(exchange_obj, 'rateLimit', 300) / 1000) # exchange_obj.rateLimit (밀리초) / 1000, 없으면 0.3초

        except ccxt.RateLimitExceeded as e:
            print(f"요청 한도 초과 {ticker_symbol}: {e}. 잠시 후 재시도...")
            time.sleep(getattr(exchange_obj, 'rateLimit', 10000) / 1000) # 기본 10초 대기
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
    df = df.set_index('datetime').sort_index() # 정렬 추가
    df = df[~df.index.duplicated(keep='first')] # 중복 제거
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
leverage = 3
fee = 0.001
# allocation_percentage is no longer primarily used for single-day buy amount calculation if using coin_spec['rate']
# It was 0.5 in the original script. We will rely on coin_spec['rate'].
# allocation_percentage = 0.5 # This variable becomes less directly used for the modified logic.

InvestCoinList = [
    {'ticker': 'PEPE/USDT', 'rate': 0.5, 'start_date': {'year': 2023, 'month': 3, 'day': 1}},
    {'ticker': 'DOGE/USDT', 'rate': 0.5, 'start_date': {'year': 2023, 'month': 3, 'day': 1}}
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
# MODIFICATION: Initialize current_cycle_investment_base
current_cycle_investment_base = InvestTotalMoney
positions = {}
total_equity_list = []
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in valid_tickers}


# 백테스팅 루프
for date in common_dates:
    current_data = {ticker: dfs[ticker].loc[date] for ticker in valid_tickers if date in dfs[ticker].index}
    if len(current_data) != len(valid_tickers):
        continue

    # 1. 보유 중인 코인의 매도 조건 확인
    tickers_sold_this_day = [] # Track tickers sold to see if all positions close
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

            sell_condition_triggered = False
            if (((df_coin['high'].iloc[i-2] > df_coin['high'].iloc[i-1] and df_coin['low'].iloc[i-2] > df_coin['low'].iloc[i-1]) or
                (df_coin['open'].iloc[i-1] > df_coin['close'].iloc[i-1] and df_coin['open'].iloc[i-2] > df_coin['close'].iloc[i-2]) or
                RevenueRate < 0) and not (i >= 2 and df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and df_coin['3ma'].iloc[i-2] < df_coin['3ma'].iloc[i-1])):
                sell_condition_triggered = True

            if sell_condition_triggered:
                cash_balance += margin * (1 + RevenueRate / 100.0)
                print(f"{ticker} {date} >>> 매도: Entry {entry_price:.8f}, Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}")

                if RevenueRate > 0:
                    CoinStats[ticker]['SuccessCnt'] += 1
                else:
                    CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                tickers_sold_this_day.append(ticker) # Track that a position was closed
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
    
    # MODIFICATION: Update current_cycle_investment_base if all positions are closed AFTER sells
    if not positions: # Check if the positions dictionary is empty
        current_cycle_investment_base = cash_balance
        # print(f"{date} >>> All positions closed. Updating current_cycle_investment_base to: {current_cycle_investment_base:.2f}")


    # 2. 매수 신호 확인 및 실행
    cash_at_start_of_day_for_buy = cash_balance # Capture cash before any buys for this day

    buy_signals_today_specs = [] # Stores the full coin_spec dict for coins with buy signals
    for coin_candidate_spec in InvestCoinList: # Iterate using the full spec from InvestCoinList
        ticker = coin_candidate_spec['ticker']
        if ticker not in positions and ticker in dfs and date in dfs[ticker].index:
            df_coin = dfs[ticker]
            i = df_coin.index.get_loc(date)

            if i > 2: 
                macd_3ago = df_coin['macd'].iloc[i-3] - df_coin['macd_signal'].iloc[i-3]
                macd_2ago = df_coin['macd'].iloc[i-2] - df_coin['macd_signal'].iloc[i-2]
                macd_1ago = df_coin['macd'].iloc[i-1] - df_coin['macd_signal'].iloc[i-1]
                macd_positive = macd_1ago > 0
                macd_3to2_down = macd_3ago > macd_2ago
                macd_2to1_down = macd_2ago > macd_1ago
                macd_condition = not (macd_3to2_down and macd_2to1_down)

                prev_high = df_coin['high'].iloc[i-1]
                prev_low = df_coin['low'].iloc[i-1]
                prev_open = df_coin['open'].iloc[i-1]
                prev_close = df_coin['close'].iloc[i-1]
                upper_shadow = prev_high - max(prev_open, prev_close)
                candle_length = prev_high - prev_low
                upper_shadow_ratio = (upper_shadow / candle_length) if candle_length > 0 else 0

                buy_condition_triggered = False
                if (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and
                    df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2] and
                    df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and
                    df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1] and
                    df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and
                    df_coin['30ma_slope'].iloc[i-1] > -2 and
                    df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and
                    df_coin['50ma'].iloc[i-2] < df_coin['50ma'].iloc[i-1] and
                    (macd_positive and macd_condition) and
                    (upper_shadow_ratio <= 0.6)):
                    buy_condition_triggered = True

                if buy_condition_triggered:
                    buy_signals_today_specs.append(coin_candidate_spec) # Add the coin_spec dictionary

    num_buys_today = len(buy_signals_today_specs)

    if num_buys_today > 0:
        # Determine the investment amount for each trade
        # This outer 'investment_amount_for_each_trade' will be calculated once
        # based on whether it's a single or multiple buy day.
        if num_buys_today > 1:
            # Multiple buys on the same day: allocate based on cash_at_start_of_day_for_buy / num_buys_today
            # This is the original logic user said is fine for same-day buys.
            investment_amount_for_each_trade = cash_at_start_of_day_for_buy / num_buys_today
        else: # num_buys_today == 1
            # Single buy on this day: use current_cycle_investment_base and the coin's specific rate.
            # This is the core of the requested change.
            single_coin_spec = buy_signals_today_specs[0] # Get the spec for the single coin
            coin_specific_rate = single_coin_spec['rate']
            investment_amount_for_each_trade = current_cycle_investment_base * coin_specific_rate
            # print(f"Debug {date} single buy {single_coin_spec['ticker']}: base {current_cycle_investment_base:.2f} * rate {coin_specific_rate} = amount {investment_amount_for_each_trade:.2f}")


        for coin_spec_to_buy in buy_signals_today_specs: # Iterate through the specs of coins to buy
            ticker = coin_spec_to_buy['ticker']
            # The investment_amount_for_each_trade is already determined above based on num_buys_today
            
            buy_price = current_data[ticker]['open']

            if cash_balance >= investment_amount_for_each_trade and investment_amount_for_each_trade > 0:
                quantity = (investment_amount_for_each_trade * leverage) / buy_price
                positions[ticker] = {
                    'margin': investment_amount_for_each_trade, # Use the calculated amount
                    'entry_price': buy_price,
                    'quantity': quantity,
                    'leverage': leverage
                }
                cash_balance -= investment_amount_for_each_trade
                print(f"{ticker} {date} >>> 매수: 가격 {buy_price:.8f}, 투자금 {investment_amount_for_each_trade:.2f}, 현재 총자산 {cash_balance:.2f}")
            else:
                print(f"Warning: Not enough cash to open position for {ticker} on {date}. Required: {investment_amount_for_each_trade:.2f}, Available: {cash_balance:.2f}")


    # 3. 일일 총 자산 가치 계산 (Mark-to-Market, 시가평가)
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


# 결과 분석
if not total_equity_list:
    print("No trades were made or no equity data to process. Exiting.")
    exit()

result_df = pd.DataFrame(total_equity_list)
result_df.set_index('date', inplace=True)

result_df['Ror'] = result_df['Total_Equity'].pct_change().fillna(0) + 1 
result_df['Cum_Ror'] = result_df['Ror'].cumprod()
result_df['Highwatermark'] = result_df['Cum_Ror'].cummax() 
result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()


result_df.index = pd.to_datetime(result_df.index)

monthly_stats = result_df.resample('ME').agg( 
    {'Total_Equity': ['first', 'last']}
)
monthly_stats.columns = ['Start_Equity', 'End_Equity']
monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Start_Equity']) - 1) * 100
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

fig, axs = plt.subplots(2, 1, figsize=(10, 10), sharex=True) 
initial_equity_val = result_df['Total_Equity'].iloc[0]
axs[0].plot(result_df.index, (result_df['Total_Equity'] / initial_equity_val) * 100, label=f'Strategy ({leverage}x Leverage)')

axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Return Comparison Chart')
axs[0].legend()
axs[0].grid(True)

axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
axs[1].set_ylabel('Drawdown (%)')
axs[1].set_title('Drawdown Comparison Chart')
axs[1].legend()
axs[1].grid(True)

plt.xlabel('Date')
plt.tight_layout()
plt.show()

if not result_df.empty:
    TotalOri = result_df['Total_Equity'].iloc[0]
    TotalFinal = result_df['Total_Equity'].iloc[-1]
    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 
    print("\n---------- 총 결과 ----------")
    print(f"최초 금액: {format(round(TotalOri), ',')} USDT, 최종 금액: {format(round(TotalFinal), ',')} USDT")
    print(f"총 수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
    print(f"MDD (최대 손실폭): {round(TotalMDD, 2)}%") 
    print("------------------------------")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
else:
    print("Result DataFrame is empty. No final results to display.")