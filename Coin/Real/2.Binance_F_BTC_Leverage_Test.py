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
        try:
            ohlcv_data = binance.fetch_ohlcv(Ticker, period, since=date_start_ms, limit=1000)
            if not ohlcv_data:
                break
            
            final_list.extend(ohlcv_data)
            
            last_timestamp_ms = ohlcv_data[-1][0]
            
            # 다음 요청 시작 시간 설정 (마지막 캔들 시간 + 1 인터벌)
            # 캔들 데이터가 1개만 반환된 경우를 대비하여 인터벌을 직접 계산
            if len(ohlcv_data) > 1:
                interval_ms = ohlcv_data[1][0] - ohlcv_data[0][0]
            else: # 인터벌을 period 문자열로부터 추정
                if period == '1d': interval_ms = 24 * 60 * 60 * 1000
                elif period == '1h': interval_ms = 60 * 60 * 1000
                else: interval_ms = 60 * 1000 # 기본 1분
            
            date_start_ms = last_timestamp_ms + interval_ms

            print(f"Get Data for {Ticker}... Last: {datetime.datetime.utcfromtimestamp(last_timestamp_ms / 1000)}")
            
            # 현재 시간보다 미래의 데이터를 요청하지 않도록 방지
            if date_start_ms > int(datetime.datetime.now().timestamp() * 1000):
                break
                
            time.sleep(0.2)

        except Exception as e:
            print(f"Error fetching data for {Ticker}: {e}")
            break


    df = pd.DataFrame(final_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    df = df[~df.index.duplicated(keep='first')] # 중복 인덱스 제거
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

InvestTotalMoney = 5000  # 초기 총 투자 금액
leverage = 2  # 레버리지 2배 설정
fee = 0.001  # 수수료 0.1%

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1, 'start_date': {'year': 2018, 'month': 7, 'day': 1}},
    #{'ticker': 'ETH/USDT', 'rate': 0.5, 'start_date': {'year': 2018, 'month': 7, 'day': 1}}
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
    DiffValue = -2

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
positions = {}
total_equity_list = []
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in [coin['ticker'] for coin in InvestCoinList]}

# 차트용 데이터 및 MDD 계산 변수 추가
peak_equity_on_trade_close = InvestTotalMoney
mdd_on_trade_close = 0.0
trade_drawdown_history = [] 

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

        i = dfs[ticker].index.get_loc(date)
        if i >= 2:
            df = dfs[ticker]
            RevenueRate = ((current_price - entry_price) / entry_price * leverage - fee) * 100.0

            if (((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or
                (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or
                RevenueRate < 0) and not (i >= 2 and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1] )):

                price_change = (current_price - entry_price) / entry_price * leverage
                realized_value = margin * (1 + price_change)
                cash_balance += realized_value * (1 - fee)

                peak_equity_on_trade_close = max(peak_equity_on_trade_close, cash_balance)
                drawdown = (cash_balance - peak_equity_on_trade_close) / peak_equity_on_trade_close
                mdd_on_trade_close = min(mdd_on_trade_close, drawdown)
                trade_drawdown_history.append((date, drawdown * 100.0))

                print(f"{ticker} {date} >>> 매도: 수익률 {round(RevenueRate, 2)}%, 잔액 {round(cash_balance, 2)}")

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
                macd_3ago = df['macd'].iloc[i-3] - df['macd_signal'].iloc[i-3]
                macd_2ago = df['macd'].iloc[i-2] - df['macd_signal'].iloc[i-2]
                macd_1ago = df['macd'].iloc[i-1] - df['macd_signal'].iloc[i-1]
                macd_positive = macd_1ago > 0
                macd_3to2_down = macd_3ago > macd_2ago
                macd_2to1_down = macd_2ago > macd_1ago
                macd_condition = not (macd_3to2_down and macd_2to1_down)

                if (
                    df['open'].iloc[i-1] < df['close'].iloc[i-1] and
                   df['open'].iloc[i-2] < df['close'].iloc[i-2] and
                   df['close'].iloc[i-2] < df['close'].iloc[i-1] and
                   #df['high'].iloc[i-2] < df['high'].iloc[i-1] and
                   df['5ma'].iloc[i-2] < df['5ma'].iloc[i-1] and
                   df['5ma'].iloc[i-3] < df['5ma'].iloc[i-2] and
                   df['20ma'].iloc[i-1] < df['close'].iloc[i-1] and
                   df['60ma'].iloc[i-1] < df['close'].iloc[i-1] and
                   df['30ma_slope'].iloc[i-1] > DiffValue  and
                   (macd_positive and macd_condition)   and
                   df['rsi_ma'].iloc[i-1] > df['rsi_ma'].iloc[i-2]
                   ):
                    
                    buy_price = current_data[ticker]['open']
                    margin = cash_balance * coin_data['rate']
                    if margin > 0:
                        positions[ticker] = {
                            'margin': margin, 'entry_price': buy_price,
                            'quantity': (margin * leverage) / buy_price, 'leverage': leverage}
                        cash_balance -= margin
                        print(f"{ticker} {date} >>> 매수: 투자금 {round(margin, 2)}, 잔액 {round(cash_balance, 2)}")

    # 3. 일일 총 자산 가치 계산
    total_equity = cash_balance
    for ticker, position in positions.items():
        price_change = (current_data[ticker]['close'] - position['entry_price']) / position['entry_price'] * position['leverage']
        total_equity += position['margin'] * (1 + price_change)
    total_equity_list.append(total_equity)

# 결과 분석
result_df = pd.DataFrame({"Total_Equity": total_equity_list}, index=common_dates)
result_df['Ror'] = result_df['Total_Equity'].pct_change() + 1
result_df['Cum_Ror'] = result_df['Ror'].cumprod()
result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

# 거래 종료 시점 Drawdown 데이터프레임 생성
trade_drawdown_df = pd.DataFrame(trade_drawdown_history, columns=['date', 'Trade_Drawdown']).set_index('date')
if not trade_drawdown_df.empty:
    trade_drawdown_df['Trade_MDD'] = trade_drawdown_df['Trade_Drawdown'].cummin()


# 최종 결과 요약표
TotalOri = result_df['Total_Equity'].iloc[0]
TotalFinal = result_df['Total_Equity'].iloc[-1]
TotalReturn = ((TotalFinal - TotalOri) / TotalOri) * 100.0
TotalMDD_daily = result_df['MaxDrawdown'].min() * 100.0
TotalMDD_trade = mdd_on_trade_close * 100.0

# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 월별/년도별 통계 계산 (추가된 부분) ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
# --- 월별 통계 ---
monthly_stats = result_df.resample('ME').agg({'Total_Equity': 'last'})
monthly_stats.rename(columns={'Total_Equity': 'End_Equity'}, inplace=True)
monthly_stats['Prev_Month_End_Equity'] = monthly_stats['End_Equity'].shift(1).fillna(TotalOri)
monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Prev_Month_End_Equity']) - 1) * 100
monthly_stats['Trades'] = 0
for month_key_str, count in MonthlyTryCnt.items():
    try:
        target_idx = monthly_stats.index[monthly_stats.index.strftime('%Y-%m') == month_key_str]
        if not target_idx.empty:
            monthly_stats.loc[target_idx[0], 'Trades'] = count
    except Exception as e:
        print(f"월별 통계 거래 횟수 업데이트 중 오류: {e}")
        continue
monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]
monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
monthly_stats.index = monthly_stats.index.strftime('%Y-%m')

# --- 년도별 통계 ---
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
    except Exception as e:
        print(f"년도별 통계 거래 횟수 업데이트 중 오류: {e}")
        continue
yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]
yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
yearly_stats.index = yearly_stats.index.strftime('%Y')
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================


# 차트 생성
fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
plt.style.use('seaborn-v0_8-whitegrid')
# 1. 누적 수익률 차트
axs[0].plot(result_df.index, result_df['Cum_Ror'] * 100, label='Cumulative Return', color='black')
axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Backtest Result: Cumulative Return & Drawdown', fontsize=16)
axs[0].legend(loc='upper left')
# 2. Drawdown 비교 차트
axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown (Daily Close)', color='lightblue', alpha=0.8)
axs[1].fill_between(result_df.index, result_df['Drawdown'] * 100, 0, color='lightblue', alpha=0.3)
axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD (Daily Close)', color='blue', linestyle='--')
if not trade_drawdown_df.empty:
    axs[1].plot(trade_drawdown_df.index, trade_drawdown_df['Trade_Drawdown'], label='Drawdown (Trade Close)', color='lightcoral', linestyle='-')
    axs[1].plot(trade_drawdown_df.index, trade_drawdown_df['Trade_MDD'], label='MDD (Trade Close)', color='red', linestyle='--')
axs[1].set_ylabel('Drawdown (%)')
axs[1].set_xlabel('Date')
axs[1].legend(loc='lower left')
plt.tight_layout()
plt.show()


# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 최종 결과 출력 (수정된 부분) ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
summary_data = [
    {'항목': '최초 금액', '값': f"{format(round(TotalOri), ',')} USDT"},
    {'항목': '최종 금액', '값': f"{format(round(TotalFinal), ',')} USDT"},
    {'항목': '총 수익률', '값': f"{round(TotalReturn, 2)}%"},
    {'항목': 'MDD (일일 마감 기준)', '값': f"{round(TotalMDD_daily, 2)}%"},
    {'항목': 'MDD (거래 종료 기준)', '값': f"{round(TotalMDD_trade, 2)}%"}
]
summary_df = pd.DataFrame(summary_data).set_index('항목')

print("\n---------- 총 결과 ----------")
print(summary_df.to_string(header=False))
print("------------------------------")

print("\n---------- 월별 통계 ----------")
print(monthly_stats.to_string())
print("\n---------- 년도별 통계 ----------")
print(yearly_stats.to_string())
print("------------------------------")
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================