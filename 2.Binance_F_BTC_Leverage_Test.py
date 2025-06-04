#-*-coding:utf-8 -*-
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

# 분봉/일봉 캔들 정보를 가져오는 함수
def GetOhlcv2(binance, Ticker, period, year=2019, month=1, day=1, hour=0, minute=0):
    date_start = datetime.datetime(year, month, day, hour, minute)
    date_start_ms = int(date_start.timestamp() * 1000)
    final_list = []

    while True:
        ohlcv_data = binance.fetch_ohlcv(Ticker, period, since=date_start_ms)
        if not ohlcv_data:
            break
        final_list.extend(ohlcv_data)
        date_start = datetime.datetime.utcfromtimestamp(ohlcv_data[-1][0] / 1000)
        date_start_ms = ohlcv_data[-1][0] + (ohlcv_data[1][0] - ohlcv_data[0][0])
        print("Get Data...", str(date_start_ms))
        time.sleep(0.2)

    df = pd.DataFrame(final_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    return df

# 바이낸스 객체 생성
Binance_AccessKey = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_ScretKey = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey, 
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

InvestTotalMoney = 5000  # 초기 총 투자 금액
leverage = 3  # 레버리지 2배 설정
fee = 0.001  # 수수료 0.1%

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1, 'start_date': {'year': 2018, 'month': 7, 'day': 1}}
]

# 데이터 가져오기 및 전처리
dfs = {}
for coin_data in InvestCoinList:
    ticker = coin_data['ticker']
    start_date = coin_data['start_date']
    df = GetOhlcv2(binanceX, ticker, '1d', start_date['year'], start_date['month'], start_date['day'], 0, 0)
    
    # RSI 지표 계산
    period = 14
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df['rsi_ma'] = df['rsi'].rolling(14).mean()
    df['rsi_5ma'] = df['rsi'].rolling(5).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['value'] = df['close'] * df['volume']
    
    # 이동평균선 계산
    ma_dfs = []
    for ma in range(3, 81):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)
    ma_df_combined = pd.concat(ma_dfs, axis=1)
    df = pd.concat([df, ma_df_combined], axis=1)
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    DiffValue = -1
    
    # MACD 계산
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    
    df.dropna(inplace=True)
    dfs[ticker] = df

# 공통 날짜 범위 찾기
common_dates = set(dfs[InvestCoinList[0]['ticker']].index)
for coin_data in InvestCoinList[1:]:
    ticker = coin_data['ticker']
    common_dates = common_dates.intersection(set(dfs[ticker].index))
common_dates = sorted(list(common_dates))

# 초기 설정
cash_balance = InvestTotalMoney
positions = {}  # key: ticker, value: {'margin': margin, 'entry_price': price, 'quantity': qty, 'leverage': leverage}
total_equity_list = []
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in [coin['ticker'] for coin in InvestCoinList]}

# 백테스팅 루프
for date in common_dates:
    current_data = {ticker: dfs[ticker].loc[date] for ticker in [coin['ticker'] for coin in InvestCoinList]}
    
    # 1. 보유 중인 코인의 매도 조건 확인
    for ticker in list(positions.keys()):
        position = positions[ticker]
        margin = position['margin']
        entry_price = position['entry_price']
        leverage = position['leverage']
        current_price = current_data[ticker]['open']
        
        # 매도 조건
        i = dfs[ticker].index.get_loc(date)
        if i >= 2:
            df = dfs[ticker]
            RevenueRate = ((current_price - entry_price) / entry_price * leverage - fee) * 100.0

            
            if (((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or 
                RevenueRate < 0) and not (i >= 2 and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1] )):
                # 매도 실행
                price_change = (current_price - entry_price) / entry_price * leverage
                realized_value = margin * (1 + price_change)
                cash_balance += realized_value * (1 - fee)
                print(f"{ticker} {date} >>> 매도: 수익률 {round(RevenueRate, 2)}%, 잔액 {round(cash_balance, 2)}")
                # 익절/손절 카운트
                if RevenueRate > 0:
                    CoinStats[ticker]['SuccessCnt'] += 1
                else:
                    CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
    
    # 2. 매수 신호 확인 및 실행
    for coin_data in InvestCoinList:
        ticker = coin_data['ticker']
        if ticker not in positions:
            df = dfs[ticker]
            i = df.index.get_loc(date)
            if i > 2:
                # MACD 조건
                macd_3ago = df['macd'].iloc[i-3] - df['macd_signal'].iloc[i-3]
                macd_2ago = df['macd'].iloc[i-2] - df['macd_signal'].iloc[i-2]
                macd_1ago = df['macd'].iloc[i-1] - df['macd_signal'].iloc[i-1]
                macd_positive = macd_1ago > 0
                macd_3to2_down = macd_3ago > macd_2ago
                macd_2to1_down = macd_2ago > macd_1ago
                macd_condition = not (macd_3to2_down and macd_2to1_down)
                
                # 전일 캔들 조건
                prev_high = df['high'].iloc[i-1]
                prev_low = df['low'].iloc[i-1]
                prev_open = df['open'].iloc[i-1]
                prev_close = df['close'].iloc[i-1]
                upper_shadow = prev_high - max(prev_open, prev_close)
                candle_length = prev_high - prev_low
                upper_shadow_ratio = (upper_shadow / candle_length) if candle_length > 0 else 0
                
                if (df['open'].iloc[i-1] < df['close'].iloc[i-1] and 
                   df['open'].iloc[i-2] < df['close'].iloc[i-2] and 
                   df['close'].iloc[i-2] < df['close'].iloc[i-1] and 
                   df['high'].iloc[i-2] < df['high'].iloc[i-1] and 
                   df['5ma'].iloc[i-2] < df['5ma'].iloc[i-1] and 
                   df['5ma'].iloc[i-3] < df['5ma'].iloc[i-2] and
                   df['20ma'].iloc[i-1] < df['close'].iloc[i-1] and 
                   df['60ma'].iloc[i-1] < df['close'].iloc[i-1] and 
                   df['30ma_slope'].iloc[i-1] > DiffValue  and
                   (macd_positive and macd_condition)   and
                   df['rsi_ma'].iloc[i-1] > df['rsi_ma'].iloc[i-2]):
                    # 매수 실행
                    buy_price = current_data[ticker]['open']
                    # 각 코인에 잔액의 50% 투자
                    margin = cash_balance * coin_data['rate']
                    if margin > 0:
                        quantity = (margin * leverage) / buy_price
                        positions[ticker] = {
                            'margin': margin,
                            'entry_price': buy_price,
                            'quantity': quantity,
                            'leverage': leverage
                        }
                        cash_balance -= margin
                        print(f"{ticker} {date} >>> 매수: 투자금 {round(margin, 2)}, 잔액 {round(cash_balance, 2)}")
    
    # 3. 일일 총 자산 가치 계산
    total_equity = cash_balance
    for ticker, position in positions.items():
        margin = position['margin']
        entry_price = position['entry_price']
        current_price = current_data[ticker]['close']
        price_change = (current_price - entry_price) / entry_price * leverage
        position_value = margin * (1 + price_change)
        total_equity += position_value
    total_equity_list.append(total_equity)

# 결과 분석
result_df = pd.DataFrame({"Total_Equity": total_equity_list}, index=common_dates)
result_df['Ror'] = result_df['Total_Equity'].pct_change() + 1
result_df['Cum_Ror'] = result_df['Ror'].cumprod()
result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

# 월별 통계
monthly_stats = result_df.resample('ME').agg({
    'Total_Equity': ['first', 'last']
})
monthly_stats.columns = ['Start_Equity', 'End_Equity']
monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Start_Equity']) - 1) * 100
monthly_stats['Trades'] = 0

for month, count in MonthlyTryCnt.items():
    try:
        year, month_num = map(int, month.split('-'))
        if month_num == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month_num + 1
        last_day = datetime.datetime(next_year, next_month, 1) - datetime.timedelta(days=1)
        last_day_str = last_day.strftime('%Y-%m-%d')
        if last_day_str in monthly_stats.index:
            monthly_stats.loc[last_day_str, 'Trades'] = count
    except Exception as e:
        print(f"월별 통계 계산 중 오류: {e} (월: {month})")
        continue

monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]
monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
monthly_stats['잔액 (USDT)'] = monthly_stats['잔액 (USDT)'].round(2)

# 연도별 통계
yearly_stats = result_df.resample('YE').agg({
    'Total_Equity': ['first', 'last']
})
yearly_stats.columns = ['Start_Equity', 'End_Equity']
yearly_stats['Return'] = ((yearly_stats['End_Equity'] / yearly_stats['Start_Equity']) - 1) * 100
yearly_stats['Trades'] = 0
for month, count in MonthlyTryCnt.items():
    try:
        year = month.split('-')[0]
        year_end = f"{year}-12-31"
        if year_end in yearly_stats.index:
            yearly_stats.loc[year_end, 'Trades'] += count
    except Exception as e:
        print(f"연도별 통계 계산 중 오류: {e} (월: {month})")
        continue

yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]
yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
yearly_stats['잔액 (USDT)'] = yearly_stats['잔액 (USDT)'].round(2)
yearly_stats.index = yearly_stats.index.strftime('%Y')

# 코인별 익절/손절 통계 출력
print("\n---------- 코인별 거래 통계 ----------")
for ticker in CoinStats:
    success = CoinStats[ticker]['SuccessCnt']
    fail = CoinStats[ticker]['FailCnt']
    total_trades = success + fail
    win_rate = (success / total_trades * 100) if total_trades > 0 else 0
    print(f"{ticker} >>> 성공: {success} 실패: {fail} -> 승률: {round(win_rate, 2)}%")
print("------------------------------")

# 그래프 생성
fig, axs = plt.subplots(2, 1, figsize=(10, 10))
axs[0].plot(result_df.index, result_df['Cum_Ror'] * 100, label='Strategy (2x Leverage)')
axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Return Comparison Chart')
axs[0].legend()
axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
axs[1].set_ylabel('Drawdown (%)')
axs[1].set_title('Drawdown Comparison Chart')
axs[1].legend()
plt.tight_layout()
plt.show()

# 최종 결과 출력
TotalOri = result_df['Total_Equity'].iloc[0]
TotalFinal = result_df['Total_Equity'].iloc[-1]
TotalMDD = result_df['MaxDrawdown'].min() * 100.0
print("---------- 총 결과 ----------")
print(f"최초 금액: {format(round(TotalOri), ',')} 최종 금액: {format(round(TotalFinal), ',')}")
print(f"수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
print(f"MDD: {round(TotalMDD, 2)}%")
print("------------------------------")
print("\n---------- 월별 통계 ----------")
#print(monthly_stats.to_string())
print("\n---------- 년도별 통계 ----------")
print(yearly_stats.to_string())
print("------------------------------")