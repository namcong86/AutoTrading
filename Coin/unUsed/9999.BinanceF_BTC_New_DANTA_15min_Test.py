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
import pprint
import myBinance
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

InvestTotalMoney = 1000
leverage = 5  # 레버리지 설정 (수익률에만 적용)
fee = 0.0002  # 바이낸스 선물 수수료(0.05%) 0.02% 적용

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1}
]

ResultList = []
TotalResultDict = {}

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    # 헤지 모드 및 레버리지 설정 (백테스팅에서는 시뮬레이션용)
    try:
        binanceX.set_margin_mode('isolated', coin_ticker)
        binanceX.set_leverage(leverage, coin_ticker)
    except Exception as e:
        print(f"헤지 모드/레버리지 설정 오류: {e}")

    InvestMoney = InvestTotalMoney * coin_data['rate']  # 레버리지 초기 금액에 미적용
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney
    TotalBuyAmt = 0
    TotalPureMoney = 0
    AvgPrice = 0
    TotalFee = 0  # 누적 수수료 추적
    TryCnt = 0
    MonthlyTryCnt = {}  # 월별 거래 횟수 기록

    df = GetOhlcv2(binanceX, coin_ticker, '15m', 2023, 1,1, 0, 0)
    df = df[df.index < '2025-04-30']  # 데이터 기간 제한 (2022-02-28까지)
    print(f"Data length: {len(df)}, Start: {df.index[0]}, End: {df.index[-1]}")  # 디버깅: 데이터 범위 출력

    # RSI 지표 계산
    period = 14  # 14 캔들 (약 210분, 3.5시간)
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df['rsi_ma'] = df['rsi'].rolling(10).mean()
    df['rsi_5ma'] = df['rsi'].rolling(5).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['value'] = df['close'] * df['volume']

    # 이동평균선 계산
    ma_dfs = []
    for ma in range(3, 61):  # 범위: 최대 15시간
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)
    ma_df_combined = pd.concat(ma_dfs, axis=1)
    df = pd.concat([df, ma_df_combined], axis=1)
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)  # 10 캔들 (150분)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100  # 30 캔들 (450분)
    DiffValue = -0.8  # 15분봉에 맞게 조정

    df = df[:len(df)-1]
    df.dropna(inplace=True)

    IsBuy = False
    SuccessCnt = 0
    FailCnt = 0
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
    TotalMoneyList = []
    ma1, ma2, ma3 = 3, 12, 24  # 45, 180, 360분
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

            # 레버리지 반영: 수익률에 5배 적용
            if IsDolpaDay:
                price_change = (SellPrice - BUY_PRICE) / BUY_PRICE * leverage
                RealInvestMoney = RealInvestMoney * (1.0 + price_change)
                IsDolpaDay = False
            else:
                price_change = (SellPrice - PrevOpenPrice) / PrevOpenPrice * leverage
                RealInvestMoney = RealInvestMoney * (1.0 + price_change)

            InvestMoney = RealInvestMoney + RemainInvestMoney

            # 청산 조건: 잔고가 초기 자본의 1/3 이하로 떨어지면 강제 청산
            if InvestMoney < InvestTotalMoney / 3:
                print(f"{coin_ticker} {df.iloc[i].name} >>> 강제 청산! 잔고 부족: {round(InvestMoney, 2)}")
                IsSellGo = True
                SellPrice = NowOpenPrice
                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                TotalBuyAmt = 0
                TotalPureMoney = 0
                AvgPrice = 0
                IsBuy = False
                TryCnt += 1
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
                FailCnt += 1
                print(f"DEBUG: Total_Money={InvestMoney:.2f}, RealInvestMoney={RealInvestMoney:.2f}, RemainInvestMoney={RemainInvestMoney:.2f}")  # 디버깅
                continue

            Rate = 0
            RevenueRate = 0
            if AvgPrice > 0:
                Rate = (SellPrice - AvgPrice) / AvgPrice * leverage
                RevenueRate = (Rate - fee) * 100.0

            if coin_ticker == 'BTC/USDT':
                if ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                    (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or 
                    RevenueRate < 0.5):
                    IsSellGo = True
                if df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
                    IsSellGo = False

            if IsSellGo:
                SellAmt = TotalBuyAmt
                SellFee = (RealInvestMoney * fee)
                TotalFee += SellFee
                InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))
                TotalBuyAmt = 0
                TotalPureMoney = 0
                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                AvgPrice = 0
                print(f"{coin_ticker} {df.iloc[i].name} >>>>>>>모두 매도!!: {SellAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,2)} >>>>>>> 매도! \n투자금 수익률: {round(RevenueRate,2)}% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매도가: {round(SellPrice,2)} 누적 수수료: {round(TotalFee,2)}\n\n")
                TryCnt += 1
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1
                if RevenueRate > 0:
                    SuccessCnt += 1
                else:
                    FailCnt += 1
                IsBuy = False
                IsSellToday = True
                print(f"DEBUG: Total_Money={InvestMoney:.2f}, RealInvestMoney={RealInvestMoney:.2f}, RemainInvestMoney={RemainInvestMoney:.2f}, RevenueRate={RevenueRate:.2f}")  # 디버깅

        if not IsBuy and i > 2 and not IsSellToday:
            if not IsFirstDateSet:
                FirstDateIndex = i-1
                IsFirstDateSet = True

            IsBuyGo = False
            InvestGoMoney = 0
            IsMaDone = False

            if coin_ticker == 'BTC/USDT':
                DolPaSt = max(df[str(ma1)+'ma'].iloc[i-1], df[str(ma2)+'ma'].iloc[i-1], df[str(ma3)+'ma'].iloc[i-1])
                #if 
                #     DolPaSt == df[str(ma3)+'ma'].iloc[i-1] and df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt:
                #     if df['30ma_slope'].iloc[i-1] > DiffValue and df['rsi_5ma'].iloc[i] > df['rsi_5ma'].iloc[i-1] and df['30ma'].iloc[i] < DolPaSt:
                #         BUY_PRICE = DolPaSt
                #         IsDolpaDay = True
                #         IsMaDone = True
                # else:
                #     if 
                if  df['open'].iloc[i-1] < df['close'].iloc[i-1] and df['open'].iloc[i-2] < df['close'].iloc[i-2] and df['close'].iloc[i-2] < df['close'].iloc[i-1] and df['high'].iloc[i-2] < df['high'].iloc[i-1] and df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and df['16ma'].iloc[i-1] < df['close'].iloc[i-1] and df['53ma'].iloc[i-1] < df['close'].iloc[i-1] and df['30ma_slope'].iloc[i-1] > DiffValue and df['rsi_5ma'].iloc[i] > df['rsi_5ma'].iloc[i-1]:
                    BUY_PRICE = NowOpenPrice
                    IsDolpaDay = False
                    IsMaDone = True
                # if not IsMaDone:
                #     DolpaRate = 0.7
                #     DolPaSt = NowOpenPrice + (((max(df['high'].iloc[i-1], df['high'].iloc[i-2]) - min(df['low'].iloc[i-1], df['low'].iloc[i-2])) * DolpaRate))
                #     if df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt and df[str(ma2)+'ma'].iloc[i-2] < PrevClosePrice and df['low'].iloc[i-2] < df['low'].iloc[i-1] and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df[str(ma3)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-1] < df[str(ma1)+'ma'].iloc[i-1] and df['30ma_slope'].iloc[i-1] > DiffValue and df['30ma'].iloc[i] < DolPaSt:
                #         BUY_PRICE = DolPaSt
                #         IsDolpaDay = True
                #         IsMaDone = True

            if IsMaDone:
                Rate = 1.0
                # if df['50ma'].iloc[i-2] > df['50ma'].iloc[i-1] or df['50ma'].iloc[i-1] > df['close'].iloc[i-1]:
                #     Rate *= 0.5
                InvestGoMoney = RemainInvestMoney * Rate * (1.0 - fee)
                IsBuyGo = True

            if IsBuyGo:
                if InvestGoMoney > df['value_ma'].iloc[i-1] / 5:
                    InvestGoMoney = df['value_ma'].iloc[i-1] / 5
                if InvestGoMoney < 50:
                    InvestGoMoney = 50
                BuyAmt = float(InvestGoMoney / BUY_PRICE)
                NowFee = (BuyAmt * BUY_PRICE) * fee
                TotalFee += NowFee
                TotalBuyAmt += BuyAmt
                TotalPureMoney += (BuyAmt * BUY_PRICE)
                RealInvestMoney += (BuyAmt * BUY_PRICE)
                RemainInvestMoney -= (BuyAmt * BUY_PRICE)
                RemainInvestMoney -= NowFee
                InvestMoney = RealInvestMoney + RemainInvestMoney
                AvgPrice = BUY_PRICE
                if IsDolpaDay:
                    print(f"{coin_ticker} {df.iloc[i].name} 회차 >>>> !!!돌파!!! 매수수량: {BuyAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,2)} >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매수가격: {round(BUY_PRICE,2)} 누적 수수료: {round(TotalFee,2)}\n")
                else:
                    print(f"{coin_ticker} {df.iloc[i].name} 회차 >>>> 매수수량: {BuyAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,2)} >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고: {round(RemainInvestMoney,2)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매수가격: {round(BUY_PRICE,2)} 누적 수수료: {round(TotalFee,2)}\n")
                IsBuy = True
                print(f"DEBUG: Total_Money={InvestMoney:.2f}, RealInvestMoney={RealInvestMoney:.2f}, RemainInvestMoney={RemainInvestMoney:.2f}")  # 디버깅
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
        # 디버깅: 최대 DD 시점 출력
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

    # 월별 통계 계산
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

    # 추가: 년도별 통계 계산
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
    yearly_stats.index = yearly_stats.index.strftime('%Y')  # 인덱스를 연도(YYYY)로 포맷

    fig, axs = plt.subplots(2, 1, figsize=(10, 10))
    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy (5x Leverage, 15m)')  # 수정: 레버리지 5배 레이블
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
    print(f"최초 금액: {str(format(round(TotalOri), ','))} 최종 금액: {str(format(round(TotalFinal), ','))}\n수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100,2)}% (단순보유수익률: {round(TotalHoldRevenue/InvestCnt,2)}%) 평균 MDD: {round(TotalMDD,2)}% 누적 수수료: {round(TotalFee,2)} USDT")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
    print("####################################")