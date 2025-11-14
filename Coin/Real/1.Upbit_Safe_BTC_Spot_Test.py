#-*-coding:utf-8 -*-
'''
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

코드 설명 참고 영상
https://youtu.be/TYj_fq4toAw?si=b3H8B_o8oU3roIWF

관련 포스팅 
업비트 안전 전략 
https://blog.naver.com/zacra/223170880153
안전 전략 개선!
https://blog.naver.com/zacra/223238532612
전략 수익률 2배로 끌어올리기
https://blog.naver.com/zacra/223456069194

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고
주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^
'''

import pyupbit
import pandas as pd
import pprint
import matplotlib.pyplot as plt

InvestTotalMoney = 1000000  # 그냥 1백만원으로 박아서 테스팅 해보기!!!

######################################## 2. 차등 분할 투자 ###################################################
InvestCoinList = list()
InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 1
InvestCoinList.append(InvestDataDict)

ResultList = list()
TotalResultDict = dict()

# 전체 포트폴리오의 거래 기준 MDD를 위한 변수
g_peak_equity_on_trade_close = InvestTotalMoney
g_mdd_on_trade_close = 0.0
g_trade_drawdown_history = []


for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    InvestMoney = InvestTotalMoney * coin_data['rate']  # 설정된 투자금에 맞게 투자!
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney
    TotalBuyAmt = 0  # 매수 수량
    TotalPureMoney = 0  # 매수 금액
    TryCnt = 0  # 매매횟수
    SuccessCnt = 0  # 익절 숫자
    FailCnt = 0  # 손절 숫자
    MonthlyTryCnt = {}  # 월별 거래 횟수 기록

    # 일봉 정보를 가지고 온다! 
    df = pyupbit.get_ohlcv(coin_ticker, interval="day", count=3600, period=0.3)  # day
    print(f"Data length: {len(df)}, Start: {df.index[0]}, End: {df.index[-1]}")  # 디버깅: 데이터 범위 출력

    ########## RSI 지표 구하는 로직! ##########
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
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']

    ############# 이동평균선! ###############
    for ma in range(3, 80):
        df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
    df['7ma'] = df['close'].rolling(window=7).mean()
    df['16ma'] = df['close'].rolling(window=16).mean()
    df['73ma'] = df['close'].rolling(window=73).mean()
    df['30ma'] = df['close'].rolling(window=30).mean()  # 30일 이평선 추가
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    df = df[:len(df)]
    df.dropna(inplace=True)  # 데이터 없는건 날린다!

    IsBuy = False  # 매수 했는지 여부
    fee = 0.002  # 수수료+세금+슬리피지를 매수매도마다 0.2%로 세팅!
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
    TotalMoneyList = list()
    AvgPrice = 0

    #######이평선 설정 ########
    ma1 = 3  
    ma2 = 12 
    ma3 = 24
    BUY_PRICE = 0
    IsDolpaDay = False
    
    # 개별 종목의 거래 기준 MDD를 위한 변수
    peak_equity_on_trade_close = InvestMoney
    mdd_on_trade_close = 0.0

    for i in range(len(df)):
        if FirstDateStr == "":
            FirstDateStr = df.iloc[i].name

        IsSellToday = False
        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]
        current_date = df.index[i]
        month_key = current_date.strftime('%Y-%m')  # 월별 키 추가

        if IsBuy:
            IsSellGo = False
            SellPrice = NowOpenPrice

            if IsDolpaDay:
                RealInvestMoney = RealInvestMoney * (1.0 + ((SellPrice - BUY_PRICE) / BUY_PRICE))
                IsDolpaDay = False
            else:
                RealInvestMoney = RealInvestMoney * (1.0 + ((SellPrice - PrevOpenPrice) / PrevOpenPrice))

            InvestMoney = RealInvestMoney + RemainInvestMoney 

            Rate = 0
            RevenueRate = 0
            if AvgPrice > 0:
                Rate = (SellPrice - AvgPrice) / AvgPrice
                RevenueRate = (Rate - fee) * 100.0

            if coin_ticker == 'KRW-BTC':
                if ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                    (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or 
                    RevenueRate < -0.7):
                    IsSellGo = True
                if df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
                    IsSellGo = False

            if IsSellGo:
                SellAmt = TotalBuyAmt
                
                # 거래 종료 시점 MDD 계산 로직 추가
                final_equity_after_sell = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))
                
                # 개별 종목 MDD 업데이트
                peak_equity_on_trade_close = max(peak_equity_on_trade_close, final_equity_after_sell)
                drawdown = (final_equity_after_sell - peak_equity_on_trade_close) / peak_equity_on_trade_close
                mdd_on_trade_close = min(mdd_on_trade_close, drawdown)

                # 전체 포트폴리오 MDD 업데이트
                g_peak_equity_on_trade_close = max(g_peak_equity_on_trade_close, final_equity_after_sell)
                g_drawdown = (final_equity_after_sell - g_peak_equity_on_trade_close) / g_peak_equity_on_trade_close
                g_mdd_on_trade_close = min(g_mdd_on_trade_close, g_drawdown)
                g_trade_drawdown_history.append((current_date, g_drawdown * 100.0))
                
                InvestMoney = final_equity_after_sell
                TotalBuyAmt = 0
                TotalPureMoney = 0
                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                AvgPrice = 0
                print(coin_ticker, " ", df.iloc[i].name, " >>>>>>>모두 매도!!:", SellAmt, "누적수량:", TotalBuyAmt, " 평단: ", round(AvgPrice, 2), ">>>>>>> 매도!  \n투자금 수익률: ", round(RevenueRate, 2), "%", " ,종목 잔고:", round(RemainInvestMoney, 2), "+", round(RealInvestMoney, 2), "=", round(InvestMoney, 2), " 매도가:", round(SellPrice, 2), "\n\n")
                TryCnt += 1
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1  # 월별 거래 횟수 증가
                if RevenueRate > 0:
                    SuccessCnt += 1
                else:
                    FailCnt += 1
                InvestMoney = RealInvestMoney + RemainInvestMoney 
                IsBuy = False 
                IsSellToday = True

        if not IsBuy and i > 2 and not IsSellToday:
            if not IsFirstDateSet:
                FirstDateIndex = i - 1
                IsFirstDateSet = True

            IsBuyGo = False
            InvestGoMoney = 0
            IsMaDone = False

            if coin_ticker == 'KRW-BTC':
                DolPaSt = max(df[str(ma1) + 'ma'].iloc[i-1], df[str(ma2) + 'ma'].iloc[i-1], df[str(ma3) + 'ma'].iloc[i-1])
                if DolPaSt == df[str(ma3) + 'ma'].iloc[i-1] and df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt:
                    BUY_PRICE = DolPaSt
                    IsDolpaDay = True
                    IsMaDone = True
                else:
                    if (df['open'].iloc[i-1] < df['close'].iloc[i-1] and 
                        df['open'].iloc[i-2] < df['close'].iloc[i-2] and 
                        df['close'].iloc[i-2] < df['close'].iloc[i-1] and 
                        df['high'].iloc[i-2] < df['high'].iloc[i-1] and 
                        df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and 
                        df['16ma'].iloc[i-1] < df['close'].iloc[i-1] and 
                        df['73ma'].iloc[i-1] < df['close'].iloc[i-1]
                        ):
                        BUY_PRICE = NowOpenPrice
                        IsDolpaDay = False
                        IsMaDone = True
                if not IsMaDone:
                    DolpaRate = 0.7
                    DolPaSt = NowOpenPrice + (((max(df['high'].iloc[i-1], df['high'].iloc[i-2]) - min(df['low'].iloc[i-1], df['low'].iloc[i-2])) * DolpaRate))
                    if (df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt and df[str(ma2) + 'ma'].iloc[i-2] < PrevClosePrice and 
                        df['low'].iloc[i-2] < df['low'].iloc[i-1] and 
                        df[str(ma3) + 'ma'].iloc[i-2] < df[str(ma2) + 'ma'].iloc[i-1] < df[str(ma1) + 'ma'].iloc[i-1]):
                        BUY_PRICE = DolPaSt
                        IsDolpaDay = True
                        IsMaDone = True

            if IsMaDone:
                Rate = 1.0
                InvestGoMoney = RemainInvestMoney * Rate * (1.0 - fee)
                IsBuyGo = True

            if IsBuyGo:
                if InvestGoMoney > df['value_ma'].iloc[i-1] / 500:
                    InvestGoMoney = df['value_ma'].iloc[i-1] / 500
                if InvestGoMoney < 10000:
                    InvestGoMoney = 10000
                BuyAmt = float(InvestGoMoney / BUY_PRICE)
                NowFee = (BuyAmt * BUY_PRICE) * fee
                TotalBuyAmt += BuyAmt
                TotalPureMoney += (BuyAmt * BUY_PRICE)
                RealInvestMoney += (BuyAmt * BUY_PRICE)
                RemainInvestMoney -= (BuyAmt * BUY_PRICE)
                RemainInvestMoney -= NowFee
                InvestMoney = RealInvestMoney + RemainInvestMoney 
                AvgPrice = BUY_PRICE
                if IsDolpaDay:
                    print(coin_ticker, " ", df.iloc[i].name, "회차 >>>> !!!돌파!!! 매수수량:", BuyAmt, "누적수량:", TotalBuyAmt, " 평단: ", round(AvgPrice, 2), " >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:", round(RemainInvestMoney, 2), "+", round(RealInvestMoney, 2), "=", round(InvestMoney, 2), " 매수가격:", round(BUY_PRICE, 2), "\n")
                else:
                    print(coin_ticker, " ", df.iloc[i].name, "회차 >>>> 매수수량:", BuyAmt, "누적수량:", TotalBuyAmt, " 평단: ", round(AvgPrice, 2), " >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:", round(RemainInvestMoney, 2), "+", round(RealInvestMoney, 2), "=", round(InvestMoney, 2), " 매수가격:", round(BUY_PRICE, 2), "\n")
                IsBuy = True
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

        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)
        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] = (df['open'].iloc[-1] / df['open'].iloc[FirstDateIndex] - 1.0) * 100.0 
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] - 1.0) * 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0
        resultData['TradeMDD'] = mdd_on_trade_close * 100.0
        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
        resultData['FailCnt'] = FailCnt
        ResultList.append(resultData)


print("\n\n--------------------")
TotalOri = 0
TotalFinal = 0
TotalHoldRevenue = 0
TotalMDD = 0
InvestCnt = float(len(ResultList))

for result in ResultList:
    print("--->>>", result['DateStr'].replace("00:00:00", ""), "<<<---")
    print(result['Ticker'])
    print("최초 금액: ", str(format(round(result['OriMoney']), ',')), " 최종 금액: ", str(format(round(result['FinalMoney']), ',')))
    print("수익률:", format(round(result['RevenueRate'], 2), ','), "%")
    print("단순 보유 수익률:", format(round(result['OriRevenueHold'], 2), ','), "%")
    print("MDD (일일 마감 기준):", round(result['MDD'], 2), "%")
    print("MDD (거래 종료 기준):", round(result['TradeMDD'], 2), "%")
    if result['TryCnt'] > 0:
        print("성공:", result['SuccessCnt'], " 실패:", result['FailCnt'], " -> 승률: ", round(result['SuccessCnt'] / result['TryCnt'] * 100.0, 2), "%")
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

    trade_drawdown_df = pd.DataFrame(g_trade_drawdown_history, columns=['date', 'Trade_Drawdown']).set_index('date')
    if not trade_drawdown_df.empty:
        trade_drawdown_df['Trade_MDD'] = trade_drawdown_df['Trade_Drawdown'].cummin()

    monthly_stats = result_df.resample('ME').agg({
        'Total_Money': ['first', 'last']
    })
    monthly_stats.columns = ['Start_Money', 'End_Money']
    monthly_stats['Return'] = ((monthly_stats['End_Money'] / monthly_stats['Start_Money']) - 1) * 100
    monthly_stats['Trades'] = 0
    for month, count in MonthlyTryCnt.items():
        monthly_stats.loc[month, 'Trades'] = count
    monthly_stats = monthly_stats[['Return', 'End_Money', 'Trades']]
    monthly_stats.columns = ['수익률 (%)', '잔액 (KRW)', '거래 횟수']
    monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
    monthly_stats['잔액 (KRW)'] = monthly_stats['잔액 (KRW)'].round(2)

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
    yearly_stats.columns = ['수익률 (%)', '잔액 (KRW)', '거래 횟수']
    yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
    yearly_stats['잔액 (KRW)'] = yearly_stats['잔액 (KRW)'].round(2)
    yearly_stats.index = yearly_stats.index.strftime('%Y')

    fig, axs = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    plt.style.use('seaborn-v0_8-whitegrid')
    
    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy (Daily)', color='black')
    axs[0].set_ylabel('Cumulative Return (%)')
    axs[0].set_title('Return Comparison Chart')
    axs[0].legend(loc='upper left')

    axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown (Daily Close)', color='lightblue', alpha=0.8)
    axs[1].fill_between(result_df.index, result_df['Drawdown'] * 100, 0, color='lightblue', alpha=0.3)
    axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD (Daily Close)', color='blue', linestyle='--')

    if not trade_drawdown_df.empty:
        axs[1].plot(trade_drawdown_df.index, trade_drawdown_df['Trade_Drawdown'], label='Drawdown (Trade Close)', color='lightcoral', linestyle='-')
        axs[1].plot(trade_drawdown_df.index, trade_drawdown_df['Trade_MDD'], label='MDD (Trade Close)', color='red', linestyle='--')

    axs[1].set_ylabel('Drawdown (%)')
    axs[1].set_title('Drawdown Comparison Chart')
    axs[1].legend(loc='lower left')
    plt.tight_layout()
    plt.show()
    
    TotalOri = result_df['Total_Money'].iloc[1]
    TotalFinal = result_df['Total_Money'].iloc[-1]
    TotalMDD_daily = result_df['MaxDrawdown'].min() * 100.0
    TotalMDD_trade = g_mdd_on_trade_close * 100.0
    
    print("---------- 총 결과 ----------")
    summary_data = {
        "최초 금액": f"{format(round(TotalOri), ',')} KRW",
        "최종 금액": f"{format(round(TotalFinal), ',')} KRW",
        "총 수익률": f"{round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%",
        "단순 보유 수익률": f"{round(TotalHoldRevenue / InvestCnt, 2)}%",
        "MDD (일일 마감 기준)": f"{round(TotalMDD_daily, 2)}%",
        "MDD (거래 종료 기준)": f"{round(TotalMDD_trade, 2)}%"
    }
    for key, value in summary_data.items():
        print(f"{key}: {value}")
        
    start_date = pd.to_datetime(FirstDateStr)
    end_date = result_df.index[-1]
    years = (end_date - start_date).days / 365.25
    if years > 0:
        CAGR = (pow((TotalFinal / TotalOri), (1 / years)) - 1) * 100
        print("CAGR(연복리수익률):", round(CAGR, 2), "%")
        
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
    print("####################################")