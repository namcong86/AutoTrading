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

InvestTotalMoney = 5000
leverage = 2  # 레버리지 5배 설정
fee = 0.001  # 바이낸스 선물 수수료(0.05%) 보수적으로 0.1% 적용

# 투자 종목 설정 - 1000PEPE와 DOGE 각각 50%씩 투자
InvestCoinList = [
    # {'ticker': 'ETH/USDT', 'rate': 0.2, 'start_date': {'year': 2020, 'month': 9, 'day': 15}},
    # {'ticker': 'XRP/USDT', 'rate': 0.2, 'start_date': {'year': 2020, 'month': 9, 'day': 15}},
    # {'ticker': 'SOL/USDT', 'rate': 0.2, 'start_date': {'year': 2020, 'month': 9, 'day': 15}},
    # {'ticker': 'ADA/USDT', 'rate': 0.2, 'start_date': {'year': 2020, 'month': 9, 'day': 15}},
    {'ticker': 'DOGE/USDT', 'rate': 0.2, 'start_date': {'year': 2020, 'month': 9, 'day': 15}}
]

ResultList = []
TotalResultDict = {}
MonthlyTryCnt = {}


for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    # 헤지 모드 및 레버리지 설정 (백테스팅에서는 시뮬레이션용)
    try:
        binanceX.set_margin_mode('hedged', coin_ticker)
        binanceX.set_leverage(leverage, coin_ticker)
    except Exception as e:
        print(f"헤지 모드/레버리지 설정 오류: {e}")

    InvestMoney = InvestTotalMoney * coin_data['rate']  # 종목당 할당 투자금
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney
    TotalBuyAmt = 0
    TotalPureMoney = 0
    AvgPrice = 0
    coin_MonthlyTryCnt = {}

    # 각 코인마다 시작 날짜를 다르게 설정
    start_date = coin_data['start_date']
    df = GetOhlcv2(binanceX, coin_ticker, '1d', start_date['year'], start_date['month'], start_date['day'], 0, 0)
    print(f"Data length: {len(df)}, Start: {df.index[0]}, End: {df.index[-1]}")  # 디버깅: 데이터 범위 출력

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
    df['rsi_Ema'] = df['rsi'].ewm(span=14, adjust=False).mean()
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
    

    df = df[:len(df)]
    df.dropna(inplace=True)

    IsBuy = False
    TryCnt = 0
    SuccessCnt = 0
    FailCnt = 0
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
    TotalMoneyList = []
    ma1, ma2, ma3 = 3, 12, 24
    BUY_PRICE = 0

    for i in range(len(df)):
        if FirstDateStr == "":
            FirstDateStr = df.iloc[i].name

        IsSellToday = False
        NowOpenPrice = df['open'].iloc[i]
        
        # 경계 체크
        if i > 0:
            PrevOpenPrice = df['open'].iloc[i-1]
            PrevClosePrice = df['close'].iloc[i-1]
        else:
            PrevOpenPrice = NowOpenPrice
            PrevClosePrice = NowOpenPrice
        
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

            # 매도 조건 - 모든 코인에 동일하게 적용
            if i >= 2 and ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or 
                (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2]) or 
                RevenueRate < 0):
                IsSellGo = True
            if i >= 2 and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
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
                coin_MonthlyTryCnt[month_key] = coin_MonthlyTryCnt.get(month_key, 0) + 1
                if RevenueRate > 0:
                    SuccessCnt += 1
                else:
                    FailCnt += 1
                IsBuy = False
                IsSellToday = True
            else:
                daily_price_change = (df['close'].iloc[i-1] - BUY_PRICE) / BUY_PRICE * leverage if i > 0 else 0
                RealInvestMoney = TotalPureMoney * (1.0 + daily_price_change)
                InvestMoney = RealInvestMoney + RemainInvestMoney

        if not IsBuy and i > 2 and not IsSellToday:
            if not IsFirstDateSet:
                FirstDateIndex = i-1
                IsFirstDateSet = True

            IsBuyGo = False
            InvestGoMoney = 0
            IsMaDone = False
            # MACD 조건
            macd_3ago = df['macd'].iloc[i-3]-df['macd_signal'].iloc[i-3]
            macd_2ago = df['macd'].iloc[i-2]-df['macd_signal'].iloc[i-2]
            macd_1ago = df['macd'].iloc[i-1]-df['macd_signal'].iloc[i-1]
            macd_positive = macd_1ago > 0
            macd_3to2_down = macd_3ago > macd_2ago
            macd_2to1_down = macd_2ago > macd_1ago
            macd_condition = not (macd_3to2_down and macd_2to1_down)

            # 전일캔들이 윗꼬리가 긴 도지형캔들이면 매수x
            prev_high = df['high'].iloc[i-1]
            prev_low = df['low'].iloc[i-1]
            prev_open = df['open'].iloc[i-1]
            prev_close = df['close'].iloc[i-1]
            upper_shadow = prev_high - max(prev_open, prev_close)
            candle_length = prev_high - prev_low
            upper_shadow_ratio = (upper_shadow / candle_length) if candle_length > 0 else 0
            

            # 매수 조건 - 모든 코인에 동일하게 적용
            if (df['50ma'].iloc[i-2] < df['50ma'].iloc[i-1] and 
                df['open'].iloc[i-1] < df['close'].iloc[i-1] and 
                df['open'].iloc[i-2] < df['close'].iloc[i-2] and 
                df['close'].iloc[i-2] < df['close'].iloc[i-1] and 
                df['high'].iloc[i-2] < df['high'].iloc[i-1] and 
                df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and 
                df['30ma_slope'].iloc[i-1] > DiffValue and 
                df['rsi_Ema'].iloc[i-2] < df['rsi_Ema'].iloc[i-1] and 
                (macd_positive and macd_condition) and 
                (upper_shadow_ratio <= 0.6)):
                    BUY_PRICE = NowOpenPrice
                    IsMaDone = True

            if IsMaDone:
                Rate = 1.0
                InvestGoMoney = RemainInvestMoney * Rate * (1.0 - (fee*leverage))
                IsBuyGo = True

            # if IsMaDone:
            #     Rate = 1.0 
            #     InvestGoMoney = RemainInvestMoney * Rate * (1.0 - (fee*leverage))
            #     IsBuyGo = True


            if IsBuyGo:
                if 'value_ma' in df.columns and i > 0 and pd.notna(df['value_ma'].iloc[i-1]) and InvestGoMoney > df['value_ma'].iloc[i-1] / 100:
                    InvestGoMoney = df['value_ma'].iloc[i-1] / 100
                if InvestGoMoney < 100:
                    InvestGoMoney = 100
                BuyAmt = float(InvestGoMoney*leverage / BUY_PRICE)  # 수량 계산
                NowFee = (BuyAmt * BUY_PRICE) * fee  # 수수료 계산
                TotalBuyAmt += BuyAmt
                TotalPureMoney += (InvestGoMoney)
                # 레버리지 반영된 금액을 RealInvestMoney에 저장
                RealInvestMoney = (InvestGoMoney)
                InvestMoney= RealInvestMoney
                
                RemainInvestMoney -= (InvestGoMoney)  # 원금만 차감
                RemainInvestMoney -= NowFee  # 수수료 차감
                AvgPrice = BUY_PRICE

                print(f"{coin_ticker} {df.iloc[i].name} 회차 >>>> 매수수량: {BuyAmt} 누적수량: {TotalBuyAmt} 평단: {round(AvgPrice,4)} >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고: {round(RemainInvestMoney,)} + {round(RealInvestMoney,2)} = {round(InvestMoney,2)} 매수가격: {round(BUY_PRICE,4)}\n")
                IsBuy = True
                print("\n")

        # Append updated InvestMoney to TotalMoneyList
        TotalMoneyList.append(InvestMoney)
        
    # MonthlyTryCnt 딕셔너리에 각 코인의 거래 횟수 합치기
    for month, count in coin_MonthlyTryCnt.items():
        MonthlyTryCnt[month] = MonthlyTryCnt.get(month, 0) + count

    if len(TotalMoneyList) > 0:
        # 인덱스와 값 길이 확인 및 조정
        if len(TotalMoneyList) != len(df.index):
            print(f"주의: {coin_ticker}의 TotalMoneyList({len(TotalMoneyList)})와 인덱스({len(df.index)}) 길이가 일치하지 않습니다.")
            # 길이 맞추기
            min_len = min(len(TotalMoneyList), len(df.index))
            TotalMoneyList = TotalMoneyList[:min_len]
            df_index = df.index[:min_len]
        else:
            df_index = df.index
            
        # 결과 저장
        TotalResultDict[coin_ticker] = {"money_list": TotalMoneyList, "index": df_index}
        
        resultData = dict()
        resultData['Ticker'] = coin_ticker
        # 데이터프레임 생성
        result_df = pd.DataFrame({"Total_Money": TotalMoneyList}, index=df_index)
        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
        result_df['Cum_Ror'] = result_df['Ror'].cumprod()
        result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
        
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        pprint.pprint(result_df)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        
        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)
        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex] if FirstDateIndex < len(result_df) else result_df['Total_Money'].iloc[0]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] = (df['open'].iloc[-1] / df['open'].iloc[FirstDateIndex if FirstDateIndex < len(df) else 0] - 1.0) * 100.0
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] - 1.0) * 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0
        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
        resultData['FailCnt'] = FailCnt
        ResultList.append(resultData)
        
        for idx, row in result_df.iterrows():
            print(idx, " ", row['Total_Money'], " ", row['Cum_Ror'])

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
    
    # 모든 티커의 데이터프레임 생성
    all_dfs = []
    for ticker, data in TotalResultDict.items():
        ticker_df = pd.DataFrame({"Total_Money": data["money_list"]}, index=data["index"])
        all_dfs.append((ticker, ticker_df))
    
    # 공통 인덱스 찾기 (수정된 부분)
    common_index = None
    for _, ticker_df in all_dfs:
        if common_index is None:
            common_index = set(ticker_df.index)
        else:
            common_index = common_index.intersection(set(ticker_df.index))
    
    common_index = sorted(list(common_index))
    
    if not common_index:
        print("공통 인덱스를 찾을 수 없습니다. 각 티커의 날짜 범위가 겹치지 않습니다.")
    else:
        print(f"공통 인덱스 기간: {common_index[0]} ~ {common_index[-1]}, 총 {len(common_index)}일")
        
        # 공통 날짜만 사용해 합산
        final_money_dict = {date: 0 for date in common_index}
        
        for ticker, ticker_df in all_dfs:
            try:
                filtered_df = ticker_df.loc[common_index]
                for date, row in filtered_df.iterrows():
                    final_money_dict[date] += row['Total_Money']
            except Exception as e:
                print(f"티커 {ticker} 처리 중 오류 발생: {e}")
                continue
        
        # 결과 데이터프레임 생성
        FinalTotalMoneyList = [final_money_dict[date] for date in common_index]
        result_df = pd.DataFrame({"Total_Money": FinalTotalMoneyList}, index=common_index)
        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
        result_df['Cum_Ror'] = result_df['Ror'].cumprod()
        result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
        result_df.index = pd.to_datetime(result_df.index)

        # 월별 통계
        monthly_stats = result_df.resample('ME').agg({
            'Total_Money': ['first', 'last']
        })
        monthly_stats.columns = ['Start_Money', 'End_Money']
        monthly_stats['Return'] = ((monthly_stats['End_Money'] / monthly_stats['Start_Money']) - 1) * 100
        monthly_stats['Trades'] = 0
        
        for month, count in MonthlyTryCnt.items():
            try:
                # 월말 날짜를 찾기
                month_parts = month.split('-')
                if len(month_parts) >= 2:
                    year = int(month_parts[0])
                    month_num = int(month_parts[1])
                    # 해당 월의 마지막 날 찾기
                    if month_num == 12:
                        next_year = year + 1
                        next_month = 1
                    else:
                        next_year = year
                        next_month = month_num + 1
                    
                    last_day = datetime.datetime(next_year, next_month, 1) - datetime.timedelta(days=1)
                    last_day_str = last_day.strftime('%Y-%m-%d')
                    
                    # 해당 날짜에 거래 횟수 추가
                    if last_day_str in monthly_stats.index:
                        monthly_stats.loc[last_day_str, 'Trades'] = count
            except Exception as e:
                print(f"월별 통계 계산 중 오류: {e} (월: {month})")
                continue
                
        monthly_stats = monthly_stats[['Return', 'End_Money', 'Trades']]
        monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
        monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
        monthly_stats['잔액 (USDT)'] = monthly_stats['잔액 (USDT)'].round(2)

        # 연도별 통계
        yearly_stats = result_df.resample('YE').agg({
            'Total_Money': ['first', 'last']
        })
        yearly_stats.columns = ['Start_Money', 'End_Money']
        yearly_stats['Return'] = ((yearly_stats['End_Money'] / yearly_stats['Start_Money']) - 1) * 100
        yearly_stats['Trades'] = 0
        
        # 연도별 거래 횟수 집계
        for month, count in MonthlyTryCnt.items():
            try:
                year = month.split('-')[0]
                year_end = f"{year}-12-31"
                if year_end in yearly_stats.index:
                    yearly_stats.loc[year_end, 'Trades'] += count
            except Exception as e:
                print(f"연도별 통계 계산 중 오류: {e} (월: {month})")
                continue
                
        yearly_stats = yearly_stats[['Return', 'End_Money', 'Trades']]
        yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
        yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
        yearly_stats['잔액 (USDT)'] = yearly_stats['잔액 (USDT)'].round(2)
        yearly_stats.index = yearly_stats.index.strftime('%Y')

        # 최종 결과 출력
        try:
            TotalOri = result_df['Total_Money'].iloc[0]
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
        except Exception as e:
            print(f"최종 결과 출력 중 오류: {e}")

        # 그래프 생성
        try:
            fig, axs = plt.subplots(2, 1, figsize=(10, 10))
            axs[0].plot(result_df.index, result_df['Cum_Ror'] * 100, label='Strategy (5x Leverage)')
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
        except Exception as e:
            print(f"그래프 생성 중 오류: {e}")