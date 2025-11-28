# -*- coding: utf-8 -*-
import ccxt
import time
import pandas as pd
import pprint
import datetime
import matplotlib.pyplot as plt
import uuid

# Gate.io 객체 생성
Gateio_AccessKey = "07a0ba2f6ed018fcb0fde7d08b58b40c"
Gateio_SecretKey = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"
gateio = ccxt.gate({
    'apiKey': Gateio_AccessKey, 
    'secret': Gateio_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

# CSV 파일에서 데이터 읽고 최신 데이터 API로 가져오기
def load_and_fetch_ohlcv(gateio, ticker, timeframe, csv_file, from_date, to_date):
    try:
        df_csv = pd.read_csv(csv_file, index_col='datetime', parse_dates=True)
        print(f"Loaded {len(df_csv)} candles from {csv_file}")
    except FileNotFoundError:
        print(f"CSV file {csv_file} not found. Fetching all data from API...")
        return fetch_ohlcv_from_api(gateio, ticker, timeframe, from_date, to_date)

    if df_csv.empty:
        print("CSV data is empty. Fetching all data from API...")
        return fetch_ohlcv_from_api(gateio, ticker, timeframe, from_date, to_date)

    df_csv = df_csv[(df_csv.index >= from_date) & (df_csv.index <= min(to_date, df_csv.index[-1]))]
    print(f"Filtered CSV data  data: {len(df_csv)} candles from {from_date} to {min(to_date, df_csv.index[-1])}")

    csv_end = df_csv.index[-1]
    if to_date > csv_end:
        print(f"Fetching additional data from API for {csv_end} to {to_date}...")
        df_api = fetch_ohlcv_from_api(gateio, ticker, timeframe, csv_end, to_date)
        if not df_api.empty:
            df = pd.concat([df_csv, df_api], axis=0)
            df = df.sort_index().drop_duplicates(keep='first')
            print(f"Combined data: {len(df)} candles")
            return df
        else:
            print("No additional API data fetched. Using CSV data only.")
            return df_csv
    else:
        print("Using CSV data only.")
        return df_csv

# API로 데이터 가져오는 함수
def fetch_ohlcv_from_api(gateio, ticker, timeframe, date_start, date_end):
    monthly_dfs = []
    current_date = date_start
    last_timestamp = None

    while current_date < date_end:
        next_month = current_date.month + 1 if current_date.month < 12 else 1
        next_year = current_date.year + 1 if next_month == 1 else current_date.year
        next_date = min(datetime.datetime(next_year, next_month, 1), date_end)

        date_start_ms = int(current_date.timestamp() * 1000)
        date_end_ms = int(next_date.timestamp() * 1000)

        print(f"Fetching data from {current_date} to {next_date}...")

        month_data = []
        previous_timestamp = None
        no_new_data_count = 0
        max_no_new_data = 3

        while date_start_ms < date_end_ms:
            retry_count = 0
            max_retries = 3
            ohlcv_data = None
            while retry_count < max_retries:
                try:
                    ohlcv_data = gateio.fetch_ohlcv(
                        symbol=ticker,
                        timeframe=timeframe,
                        since=date_start_ms,
                        limit=500,
                        params={'future': True}
                    )
                    print(f"  Fetched {len(ohlcv_data)} raw candles starting from {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}")
                    if not ohlcv_data:
                        print("  No more data available.")
                        break

                    filtered_data = []
                    for data in ohlcv_data:
                        if previous_timestamp is None or data[0] > previous_timestamp:
                            filtered_data.append(data)
                            previous_timestamp = data[0]
                        else:
                            print(f"  Skipping old data: {datetime.datetime.utcfromtimestamp(data[0]/1000)} <= {datetime.datetime.utcfromtimestamp(previous_timestamp/1000)}")
                    
                    if not filtered_data:
                        print("  No new data after filtering.")
                        no_new_data_count += 1
                        if no_new_data_count >= max_no_new_data:
                            print(f"  No new data after {max_no_new_data} attempts. Stopping fetch for this period.")
                            break
                        time.sleep(0.2)
                        continue

                    month_data.extend(filtered_data)
                    if len(filtered_data) < 500:
                        print("  Less than 500 candles fetched. Possibly reached end of data.")
                        break

                    date_start_ms = filtered_data[-1][0] + (filtered_data[1][0] - filtered_data[0][0])
                    last_timestamp = filtered_data[-1][0]
                    print(f"  Get Data... {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}")
                    no_new_data_count = 0
                    time.sleep(0.2)
                    break

                except Exception as e:
                    print(f"  데이터 가져오기 오류: {e}")
                    retry_count += 1
                    if retry_count == max_retries:
                        print("  최대 재시도 횟수 초과. 데이터 수집 중단.")
                        break
                    print(f"  재시도 {retry_count}/{max_retries}... 5초 대기")
                    time.sleep(5)

            if retry_count == max_retries or not ohlcv_data or no_new_data_count >= max_no_new_data:
                break

        if month_data:
            print(f"Converting month data to DataFrame for {current_date.strftime('%Y-%m')}...")
            try:
                df_month = pd.DataFrame(month_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                df_month['datetime'] = pd.to_datetime(df_month['datetime'], unit='ms')
                df_month.set_index('datetime', inplace=True)
                df_month = df_month.sort_index().drop_duplicates(keep='first')
                monthly_dfs.append(df_month)
                print(f"Fetched {len(month_data)} candles for {current_date.strftime('%Y-%m')}")
            except Exception as e:
                print(f"월별 DataFrame 생성 중 오류: {e}")
                break
        else:
            print(f"No data fetched for {current_date.strftime('%Y-%m')}")
            break

        if last_timestamp:
            last_date = datetime.datetime.utcfromtimestamp(last_timestamp / 1000)
            if last_date >= date_end:
                print("Last fetched data exceeds end date. Stopping fetch.")
                break

        current_date = next_date
        if current_date < date_end:
            print("Waiting 2 seconds before next request...")
            time.sleep(2)

    if not monthly_dfs:
        print("가져온 데이터가 없습니다.")
        return pd.DataFrame()

    print("Merging monthly DataFrames...")
    try:
        df = pd.concat(monthly_dfs, axis=0)
        df = df.sort_index().drop_duplicates(keep='first')
        print(f"Data fetching completed. Total candles: {len(df)}")
        return df
    except Exception as e:
        print(f"월별 데이터 병합 중 오류: {e}")
        return pd.DataFrame()

InvestTotalMoney = 5000
leverage = 5
fee = 0.001

InvestCoinList = [
    {'ticker': 'DOGE/USDT:USDT', 'rate': 1}
]

from_date = datetime.datetime(2023, 1, 1)
to_date = datetime.datetime(2025, 5, 22)

ResultList = []
TotalResultDict = {}

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    InvestMoney = InvestTotalMoney * coin_data['rate']
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney
    TotalBuyAmt = 0
    TotalPureMoney = 0
    AvgPrice = 0
    TotalFee = 0
    TryCnt = 0
    MonthlyTryCnt = {}

    csv_file = 'DOGE_usdt_1h_2020_to_202504.csv'
    df = load_and_fetch_ohlcv(gateio, coin_ticker, '1h', csv_file, from_date, to_date)
    print(f"Data length: {len(df)}, Start: {df.index[0] if not df.empty else 'N/A'}, End: {df.index[-1] if not df.empty else 'N/A'}")

    if df.empty:
        print("데이터를 가져오지 못했습니다. 프로그램을 종료합니다.")
        continue

    try:
        print("Calculating RSI...")
        period = 14
        delta = df["close"].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss
        df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
        print("Calculating RSI moving averages...")
        df['rsi_ma'] = df['rsi'].rolling(10).mean()
        df['rsi_5ma'] = df['rsi'].rolling(5).mean()
        print("Calculating previous close and change...")
        df['prev_close'] = df['close'].shift(1)
        df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
        print("Calculating value...")
        df['value'] = df['close'] * df['volume']

        print("Calculating moving averages...")
        ma_dfs = []
        for ma in range(3, 61):
            ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
            ma_dfs.append(ma_df)
        ma_df_combined = pd.concat(ma_dfs, axis=1)
        df = pd.concat([df, ma_df_combined], axis=1)
        print("Calculating value moving average...")
        df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
        print("Calculating 30ma slope...")
        df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
        DiffValue = -0.8

        # Converting 4h data to daily timeframe for the 30-day moving average
        print("Converting to daily data and calculating daily moving averages...")
        df_daily = df['close'].resample('D').last().dropna()
        df_daily_30ma = df_daily.rolling(30).mean()
        # Map the daily 30MA back to the 4h dataframe using forward fill
        df['daily_30ma'] = df_daily_30ma.reindex(df.index, method='ffill')

        print("Trimming and cleaning DataFrame...")
        df = df[:len(df)-1]
        df.dropna(inplace=True)
        print("Technical indicators calculated successfully.")
    except Exception as e:
        print(f"기술적 지표 계산 중 오류: {e}")
        continue

    IsBuy = False
    SuccessCnt = 0
    FailCnt = 0
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
    TotalMoneyList = []
    ma1, ma2, ma3 = 3, 12, 24
    BUY_PRICE = 0
    IsDolpaDay = False

    for i in range(len(df)):
        if FirstDateStr == "":
            FirstDateStr = df.iloc[i].name

        IsSellToday = False
        NowOpenPrice = df['open'].iloc[i]
        PrevOpenPrice = df['open'].iloc[i-1]
        PrevClosePrice = df['close'].iloc[i-1]
        current_date = df.index[i]
        month_key = current_date.strftime('%Y-%m')

        if IsBuy:
            IsSellGo = False
            SellPrice = NowOpenPrice

            Rate = 0
            RevenueRate = 0
            if AvgPrice > 0:
                Rate = (SellPrice - AvgPrice) / AvgPrice * leverage
                RevenueRate = (Rate - fee) * 100.0

            if coin_ticker == 'DOGE/USDT:USDT':
                if ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                    (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2])):
                    IsSellGo = True
                if i >= 2 and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
                    IsSellGo = False

                if IsSellGo:
                    price_change = (SellPrice - BUY_PRICE) / BUY_PRICE * leverage
                    RealInvestMoney = RealInvestMoney * (1.0 + price_change)

                    SellAmt = TotalBuyAmt
                    SellPrice = NowOpenPrice
                    SellValue = SellAmt * SellPrice
                    NowFee = SellValue * fee
                    TotalFee += NowFee
                    RealInvestMoney -= NowFee
                    RemainInvestMoney += RealInvestMoney 
                    RealInvestMoney = 0
                    InvestMoney = RemainInvestMoney + RealInvestMoney
                    Rate = (SellPrice - AvgPrice) / AvgPrice * leverage
                    RevenueRate = (Rate - fee * 2) * 100.0
                    TotalBuyAmt = 0
                    TotalPureMoney = 0
                    AvgPrice = 0
                    print(f"{coin_ticker} {df.iloc[i].name} >>>>>>>모두 매도!!: {SellAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,2)} >>>>>>> 매도! \n투자금 수익률: {round(RevenueRate,2)}% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매도가: {round(SellPrice,4)} 누적 수수료: {round(TotalFee,2)}\n\n")
                    TryCnt += 1
                    MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
                    if RevenueRate > 0:
                        SuccessCnt += 1
                    else:
                        FailCnt += 1
                    IsBuy = False
                    IsSellToday = True
                    print(f"DEBUG: Total_Money={InvestMoney:.2f}, RealInvestMoney={RealInvestMoney:.2f}, RemainInvestMoney={RemainInvestMoney:.2f}, RevenueRate={RevenueRate:.2f}")

        if not IsBuy and i > 2 and not IsSellToday:
            if not IsFirstDateSet:
                FirstDateIndex = i-1
                IsFirstDateSet = True

            IsBuyGo = False
            InvestGoMoney = 0
            IsMaDone = False

            if coin_ticker == 'DOGE/USDT:USDT':
                # 추가된 조건: 현재 가격이 일봉 기준 30이평선 위에 있는지 확인
                price_above_daily_30ma = df['close'].iloc[i-1] > df['daily_30ma'].iloc[i-1]
                
                if (df['open'].iloc[i-1] < df['close'].iloc[i-1] and 
                    df['open'].iloc[i-2] < df['close'].iloc[i-2] and 
                    df['close'].iloc[i-2] < df['close'].iloc[i-1] and 
                    df['high'].iloc[i-2] < df['high'].iloc[i-1] and 
                    df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and 
                    df['30ma_slope'].iloc[i-1] > DiffValue and 
                    df['rsi_ma'].iloc[i] > df['rsi_ma'].iloc[i-1] and
                    price_above_daily_30ma):  # 일봉 30이평선 위에 있는지 확인하는 조건 추가
                    BUY_PRICE = NowOpenPrice
                    IsMaDone = True

            if IsMaDone:
                Rate = 1.0
                InvestGoMoney = RemainInvestMoney * Rate * (1.0 - fee)
                IsBuyGo = True

            if IsBuyGo:
                if InvestGoMoney > df['value_ma'].iloc[i-1] / 1:
                    InvestGoMoney = df['value_ma'].iloc[i-1] / 1
                if InvestGoMoney < 50:
                    InvestGoMoney = 50
                BuyAmt = float(InvestGoMoney*leverage / BUY_PRICE)
                NowFee = (BuyAmt * BUY_PRICE) * fee
                TotalFee += NowFee
                TotalBuyAmt += BuyAmt
                TotalPureMoney += (InvestGoMoney)
                RealInvestMoney = (InvestGoMoney)
                RemainInvestMoney -= (InvestGoMoney)
                RemainInvestMoney -= NowFee
                InvestMoney = RealInvestMoney + RemainInvestMoney
                AvgPrice = BUY_PRICE
                print(f"{coin_ticker} {df.iloc[i].name} 회차 >>>> 매수수량: {BuyAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,2)} >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매수가격: {round(BUY_PRICE,4)} 누적 수수료: {round(TotalFee,2)}\n")
                IsBuy = True
                print(f"DEBUG: Total_Money={InvestMoney:.2f}, RealInvestMoney={RealInvestMoney:.2f}, RemainInvestMoney={RemainInvestMoney:.2f}")
                print("\n")

        InvestMoney = RealInvestMoney + RemainInvestMoney
        TotalMoneyList.append(InvestMoney)

    if len(TotalMoneyList) > 0:
        TotalResultDict[coin_ticker] = TotalMoneyList
        resultData = dict()
        resultData['Ticker'] = coin_ticker
        result_df = pd.DataFrame({"Total_Money": TotalMoneyList}, index=df.index)
        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
        result_df['Cum_Ror'] = result_df['Ror'].cumprod()
        result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        pprint.pprint(result_df)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        max_dd_index = result_df['Drawdown'].idxmin()
        print(f"Max DD at {max_dd_index}: Drawdown={result_df.loc[max_dd_index, 'Drawdown']*100:.2f}%, Total_Money={result_df.loc[max_dd_index, 'Total_Money']:.2f}")
        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)
        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] = (df['open'].iloc[-1] / df['open'].iloc[FirstDateIndex] - 1.0) * 100.0
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] - 1.0) * 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0
        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
        resultData['FailCnt'] = FailCnt
        resultData['TotalFee'] = TotalFee
        ResultList.append(resultData)
        for idx, row in result_df.iterrows():
            print(idx, " ", row['Total_Money'], " ", row['Cum_Ror'])

print("\n\n--------------------")
TotalOri = 0
TotalFinal = 0
TotalHoldRevenue = 0
TotalMDD = 0
TotalFee = 0
InvestCnt = float(len(ResultList))

for result in ResultList:
    print(f"--->>> {result['DateStr'].replace('00:00:00','')} <<<---")
    print(result['Ticker'])
    print(f"최초 금액: {str(format(round(result['OriMoney']), ','))} 최종 금액: {str(format(round(result['FinalMoney']), ','))}")
    print(f"수익률: {format(round(result['RevenueRate'],2),',')}%")
    print(f"단순 보유 수익률: {format(round(result['OriRevenueHold'],2),',')}%")
    print(f"MDD: {round(result['MDD'],2)}%")
    print(f"누적 수수료: {round(result['TotalFee'],2)} USDT")
    if result['TryCnt'] > 0:
        print(f"성공: {result['SuccessCnt']} 실패: {result['FailCnt']} -> 승률: {round(result['SuccessCnt']/result['TryCnt'] * 100.0,2)}%")
    TotalHoldRevenue += result['OriRevenueHold']
    TotalFee += result['TotalFee']
    print("\n--------------------\n")

if len(ResultList) > 0:
    print("####################################")
    length = len(list(TotalResultDict.values())[0])
    FinalTotalMoneyList = [0] * length
    for my_list in TotalResultDict.values():
        for i, value in enumerate(my_list):
            FinalTotalMoneyList[i] += value
    result_df = pd.DataFrame({"Total_Money": FinalTotalMoneyList}, index=df.index)
    result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()
    result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
    result_df.index = pd.to_datetime(result_df.index)

    monthly_stats = result_df.resample('ME').agg({
        'Total_Money': ['first', 'last']
    })
    monthly_stats.columns = ['Start_Money', 'End_Money']
    monthly_stats['Return'] = ((monthly_stats['End_Money'] / monthly_stats['Start_Money']) - 1) * 100
    monthly_stats['Trades'] = 0
    for month, count in MonthlyTryCnt.items():
        monthly_stats.loc[month, 'Trades'] = count
    monthly_stats = monthly_stats[['Return', 'End_Money', 'Trades']]
    monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
    monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
    monthly_stats['잔액 (USDT)'] = monthly_stats['잔액 (USDT)'].round(2)

    yearly_stats = result_df.resample('YE').agg({
        'Total_Money': ['first', 'last']
    })
    yearly_stats.columns = ['Start_Money', 'End_Money']
    yearly_stats['Return'] = ((yearly_stats['End_Money'] / yearly_stats['Start_Money']) - 1) * 100
    yearly_stats['Trades'] = 0
    for month, count in MonthlyTryCnt.items():
        year = month.split('-')[0]
        yearly_stats.loc[f'{year}-12-31', 'Trades'] += count
    yearly_stats = yearly_stats[['Return', 'End_Money', 'Trades']]
    yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
    yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
    yearly_stats['잔액 (USDT)'] = yearly_stats['잔액 (USDT)'].round(2)
    yearly_stats.index = yearly_stats.index.strftime('%Y')

    # Enhanced charting section
    fig, axs = plt.subplots(3, 1, figsize=(12, 15), sharex=True)
    
    # Subplot 1: DOGE/USDT Price
    axs[0].plot(df.index, df['close'], label='DOGE/USDT Close Price', color='blue')
    axs[0].plot(df.index, df['daily_30ma'], label='Daily 30MA', color='red', linestyle='--')
    
    # Subplot 1: DOGE/USDT Price
    axs[0].plot(df.index, df['close'], label='DOGE/USDT Close Price', color='blue')
    axs[0].set_title('DOGE/USDT Price (4-Hour)')
    axs[0].set_ylabel('Price (USDT)')
    axs[0].grid(True)
    axs[0].legend()
    
    # Subplot 2: Cumulative Return
    axs[1].plot(result_df.index, result_df['Cum_Ror'] * 100, label='Strategy (5x Leverage, 4h)', color='green')
    axs[1].set_title('Cumulative Return')
    axs[1].set_ylabel('Return (%)')
    axs[1].grid(True)
    axs[1].legend()
    
    # Subplot 3: Drawdown
    axs[2].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown', color='orange')
    axs[2].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='Max Drawdown', color='red')
    axs[2].set_title('Drawdown and Maximum Drawdown')
    axs[2].set_ylabel('Drawdown (%)')
    axs[2].set_xlabel('Date')
    axs[2].grid(True)
    axs[2].legend()
    
    plt.tight_layout()
    plt.show()
    plt.close()

    TotalOri = InvestTotalMoney
    TotalFinal = result_df['Total_Money'].iloc[-1]
    TotalMDD = result_df['MaxDrawdown'].min() * 100.0
    print("---------- 총 결과 ----------")
    print(f"최초 금액: {str(format(round(TotalOri), ','))} 최종 금액: {str(format(round(TotalFinal), ','))}\n수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}% (단순보유수익률: {round(TotalHoldRevenue/InvestCnt,2)}%) 평균 MDD: {round(TotalMDD,2)}% 누적 수수료: {round(TotalFee,2)} USDT")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
    print("####################################")