#-*-coding:utf-8 -*-
'''
Gate.io 버전 - 페이지네이션 구현으로 1500개 데이터 가져오기, MDD만 저가 기반으로 계산
'''

import ccxt
import time
import pandas as pd
import pprint
import datetime
import matplotlib.pyplot as plt

# Gate.io API 관련 함수
def get_gate_io_exchange(api_key, secret_key):
    """Gate.io 거래소 객체를 생성합니다."""
    return ccxt.gateio({
        'apiKey': api_key,
        'secret': secret_key,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future'  # 선물 거래 설정
        }
    })

# 페이지네이션을 활용하여 분봉/일봉 캔들 정보를 가져오는 함수
def GetOhlcv2(exchange, Ticker, period='1d', desired_limit=1500):
    """
    페이지네이션을 통해 원하는 개수의 OHLCV 데이터를 가져오는 함수
    API 요청당 최대 1000개로 제한된 경우에도 여러 번 요청하여 원하는 개수를 가져옵니다.
    """
    try:
        all_data = []
        since = None
        per_request_limit = 1000  # Gate.io API 당 최대 요청 가능 수량
        
        while len(all_data) < desired_limit:
            ohlcv_data = exchange.fetch_ohlcv(Ticker, period, since=since, limit=per_request_limit)
            
            if not ohlcv_data or len(ohlcv_data) == 0:
                print(f"더 이상 가져올 데이터가 없습니다. 총 {len(all_data)}개 데이터 로드.")
                break
            
            since = ohlcv_data[-1][0] + 1
            
            if all_data and ohlcv_data[0][0] == all_data[-1][0]:
                ohlcv_data = ohlcv_data[1:]
            
            all_data.extend(ohlcv_data)
            print(f"부분 데이터 {len(ohlcv_data)}개 로드, 현재 총 {len(all_data)}개")
            
            if len(ohlcv_data) < per_request_limit:
                break
                
            time.sleep(0.5)
            
            if len(all_data) >= desired_limit:
                all_data = all_data[:desired_limit]
                break
                
        print(f"데이터 {len(all_data)}개 로드 완료")
        
        if len(all_data) == 0:
            return pd.DataFrame()
            
        df = pd.DataFrame(all_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return pd.DataFrame()

# Gate.io 객체 생성
GateIO_AccessKey = "YOUR_GATE_IO_API_KEY"  # Gate.io API 키로 변경 필요
GateIO_SecretKey = "YOUR_GATE_IO_SECRET_KEY"  # Gate.io 시크릿 키로 변경 필요
gateio = get_gate_io_exchange(GateIO_AccessKey, GateIO_SecretKey)

InvestTotalMoney = 5000
leverage = 5  # 레버리지 5배 설정
fee = 0.002  # Gate.io 선물 수수료는 약 0.2% 적용

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'DOGE_USDT', 'rate': 1}
]

ResultList = []
TotalResultDict = {}

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    try:
        print(f"백테스트에서는 레버리지 설정 시뮬레이션만 진행 (실제 API 호출 안함)")
    except Exception as e:
        print(f"레버리지 설정 오류 (백테스트에서는 무시 가능): {e}")

    InvestMoney = InvestTotalMoney * coin_data['rate']
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney
    TotalBuyAmt = 0
    TotalPureMoney = 0
    AvgPrice = 0
    MonthlyTryCnt = {}

    df = GetOhlcv2(gateio, coin_ticker, '1d', 1500)
    
    if df.empty:
        print(f"{coin_ticker} 데이터를 가져올 수 없습니다. 다음 코인으로 진행합니다.")
        continue
        
    print(f"Data length: {len(df)}, Start: {df.index[0]}, End: {df.index[-1]}")

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
    df['value'] = df['volume']

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

    df = df[:len(df)]
    df = df.dropna()

    IsBuy = False
    TryCnt = 0
    SuccessCnt = 0
    FailCnt = 0
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
    BUY_PRICE = 0
    
    all_dates = df.index.tolist()
    TotalMoneyList = [InvestMoney] * len(all_dates)

    for i in range(len(df)):
        if i < 3:
            continue
            
        if FirstDateStr == "":
            FirstDateStr = df.iloc[i].name

        IsSellToday = False
        NowOpenPrice = df['open'].iloc[i]
        PrevOpenPrice = df['open'].iloc[i-1] if i > 0 else NowOpenPrice
        PrevClosePrice = df['close'].iloc[i-1] if i > 0 else NowOpenPrice
        current_date = df.index[i]
        month_key = current_date.strftime('%Y-%m')

        if IsBuy:
            IsSellGo = False
            SellPrice = NowOpenPrice

            InvestMoney = RealInvestMoney + RemainInvestMoney

            Rate = 0
            RevenueRate = 0
            if AvgPrice > 0:
                Rate = (SellPrice - AvgPrice) / AvgPrice * leverage
                RevenueRate = (Rate - fee) * 100.0

            # 저가 기반 자산 가치 계산
            daily_price_change = (df['close'].iloc[i-1] - BUY_PRICE) / BUY_PRICE * leverage
            RealInvestMoney = TotalPureMoney * (1.0 + daily_price_change)

            #print(f"로그좀 보자{i}  {df['high'].iloc[i-2]}::::::{df['high'].iloc[i-1]}")

            if ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or 
                RevenueRate < 0):
                IsSellGo = True
                
            if df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
                IsSellGo = False
                
            if IsSellGo:
                price_change = (SellPrice - BUY_PRICE) / BUY_PRICE * leverage
                RealInvestMoney = TotalPureMoney * (1.0 + price_change)
                SellAmt = TotalBuyAmt
                InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))
                TotalBuyAmt = 0
                TotalPureMoney = 0
                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                AvgPrice = 0
                print(f"{coin_ticker} {df.iloc[i].name} >>>>>>>모두 매도!!: {SellAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,4)} >>>>>>> 매도! \n투자금 수익률: {round(RevenueRate,2)}% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매도가: {round(SellPrice,4)}\n\n")
                TryCnt += 1
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
                if RevenueRate > 0:
                    SuccessCnt += 1
                else:
                    FailCnt += 1
                IsBuy = False
                IsSellToday = True
            else:
                InvestMoney = RealInvestMoney + RemainInvestMoney

        if not IsBuy and i > 2 and not IsSellToday:
            if not IsFirstDateSet:
                FirstDateIndex = i
                IsFirstDateSet = True

            IsBuyGo = False
            InvestGoMoney = 0
            IsMaDone = False

            DolPaSt = max(df[str(3)+'ma'].iloc[i-1], df[str(12)+'ma'].iloc[i-1], df[str(24)+'ma'].iloc[i-1])
            if  df['open'].iloc[i-1] < df['close'].iloc[i-1] and df['open'].iloc[i-2] < df['close'].iloc[i-2] and df['close'].iloc[i-2] < df['close'].iloc[i-1] and df['high'].iloc[i-2] < df['high'].iloc[i-1] and df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and df['50ma'].iloc[i-2] < df['50ma'].iloc[i-1] and df['30ma_slope'].iloc[i-1] > DiffValue and df['rsi_ma'].iloc[i] > df['rsi_ma'].iloc[i-1]:
                BUY_PRICE = NowOpenPrice
                IsMaDone = True
                
            if IsMaDone:
                Rate = 1.0
                InvestGoMoney = RemainInvestMoney * Rate * (1.0 - (fee*leverage))
                IsBuyGo = True

            if IsBuyGo:
                if InvestGoMoney > df['value_ma'].iloc[i-1] / 10:
                    InvestGoMoney = df['value_ma'].iloc[i-1] / 10
                if InvestGoMoney < 100:
                    InvestGoMoney = 100
                BuyAmt = float(InvestGoMoney*leverage / BUY_PRICE)
                NowFee = (BuyAmt * BUY_PRICE) * fee
                TotalBuyAmt += BuyAmt
                TotalPureMoney += (InvestGoMoney)
                RealInvestMoney = (InvestGoMoney)
                InvestMoney = RealInvestMoney
                
                RemainInvestMoney -= (InvestGoMoney)
                RemainInvestMoney -= NowFee
                AvgPrice = BUY_PRICE

                print(f"{coin_ticker} {df.iloc[i].name} 회차 >>>> 매수수량: {BuyAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,4)} >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고: {round(RemainInvestMoney,)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매수가격: {round(BUY_PRICE,4)}\n")
                IsBuy = True
                print("\n")

        TotalMoneyList[i] = InvestMoney

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
        
        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)
        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] = (df['open'].iloc[-1] / df['open'].iloc[FirstDateIndex] - 1.0) * 100.0
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] - 1.0) * 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0
        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
        resultData['FailCnt'] = FailCnt
        ResultList.append(resultData)
        
        print(f"TotalMoneyList 길이: {len(TotalMoneyList)}, df.index 길이: {len(df.index)}")
        
        for idx, row in result_df.iterrows():
            print(idx, " ", row['Total_Money'], " ", row['Cum_Ror'])

# 결과 출력 및 그래프 생성
print("\n\n--------------------")
TotalOri = 0
TotalFinal = 0
TotalHoldRevenue = 0
TotalMDD = 0
InvestCnt = float(len(ResultList))

for result in ResultList:
    print(f"--->>> {result['DateStr'].replace('00:00:00','')} <<<---")
    print(result['Ticker'])
    print(f"최초 금액: {str(format(round(result['OriMoney']), ','))} 최종 금액: {str(format(round(result['FinalMoney']), ','))}")
    print(f"수익률: {format(round(result['RevenueRate'],2),',')}%")
    print(f"단순 보유 수익률: {format(round(result['OriRevenueHold'],2),',')}%")
    print(f"MDD: {round(result['MDD'],2)}%")
    if result['TryCnt'] > 0:
        print(f"성공: {result['SuccessCnt']} 실패: {result['FailCnt']} -> 승률: {round(result['SuccessCnt']/result['TryCnt'] * 100.0,2)}%")
    TotalHoldRevenue += result['OriRevenueHold']
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

    # 그래프 그리기
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))
    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy (5x Leverage, Low-based MDD)')
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

    TotalOri = result_df['Total_Money'].iloc[1]
    TotalFinal = result_df['Total_Money'].iloc[-1]
    TotalMDD = result_df['MaxDrawdown'].min() * 100.0
    print("---------- 총 결과 ----------")
    print(f"최초 금액: {str(format(round(TotalOri), ','))} 최종 금액: {str(format(round(TotalFinal), ','))}\n수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100,2)}% (단순보유수익률: {round(TotalHoldRevenue/InvestCnt,2)}%) 평균 MDD: {round(TotalMDD,2)}%")
    print("------------------------------")
    print("####################################")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
    print("####################################")