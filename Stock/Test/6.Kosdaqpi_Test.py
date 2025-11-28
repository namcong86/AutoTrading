'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
코드 참고 영상!
https://youtu.be/YdEdM-oC0kc
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$




$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
 
해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다. 

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504

관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅


코스닥 코스피 양방향으로 투자하는 전략! 초전도체 LK99에 버금가는 발견!!
https://blog.naver.com/zacra/223177598281

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^
 

  
'''

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Common'))

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import pandas as pd
import pprint
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import socket
import re

# GUI 및 차트 연동을 위한 라이브러리
import tkinter as tk
from tkinter import ttk
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import font_manager

# 폰트 설정
try:
    import os
    if os.name == 'nt': # Windows OS
        font_path = "c:/Windows/Fonts/malgun.ttf"
    elif os.name == 'posix': # Mac OS
        font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    else:
        font_path = None

    if font_path and os.path.exists(font_path):
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        mpl.rcParams['font.family'] = font_name
    else:
        mpl.rcParams['font.family'] = 'DejaVu Sans'
        print("지정된 한글 폰트를 찾을 수 없어 기본 폰트로 설정됩니다.")

    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

except Exception as e:
    print(f"폰트 설정 중 오류 발생: {e}")
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL

# 토큰 미리 체크 및 갱신 (백테스팅 시작 전 토큰 확보)
print("=" * 50)
print("토큰 상태 확인 중...")
try:
    token = Common.GetToken(Common.GetNowDist())
    print("토큰 확보 완료!")
except Exception as e:
    print(f"토큰 발급 중 오류 발생: {e}")
    print("API 키 정보를 확인해주세요.")
print("=" * 50)


#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.5

#이렇게 직접 금액을 지정
TotalMoney = 10000000

print("테스트하는 총 금액: ", format(round(TotalMoney), ','))

 
fee = 0.0015 #수수료+세금+슬리피지를 매수매도마다 0.15%로 세팅!
#전략 백테스팅 시작 년도 지정!!!
StartYear = 2017


#투자할 종목!
InvestStockList = ["122630","252670","233740","251340"]




StockDataList = list()

for stock_code in InvestStockList:
    print("..",stock_code,"..")
    stock_data = dict()
    stock_data['stock_code'] = stock_code
    stock_data['stock_name'] = KisKR.GetStockName(stock_code)
    stock_data['try'] = 0
    stock_data['success'] = 0
    stock_data['fail'] = 0
    stock_data['accRev'] = 0

    StockDataList.append(stock_data)

pprint.pprint(StockDataList)



def GetStockName(stock_code, StockDataList):
    result_str = stock_code
    for stock_data in StockDataList:
        if stock_code == stock_data['stock_code']:
            result_str = stock_data['stock_name']
            break

    return result_str
    

stock_df_list = []

gugan_lenth = 7

for stock_code in InvestStockList:
    df = Common.GetOhlcv("KR", stock_code,2200)

    period = 14

    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss

    df['RSI'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")

    df['prevRSI'] = df['RSI'].shift(1)
    df['prevRSI2'] = df['RSI'].shift(2)
    
    df['high_'+str(gugan_lenth)+'_max'] = df['high'].rolling(window=gugan_lenth).max().shift(1)
    df['low_'+str(gugan_lenth)+'_min'] = df['low'].rolling(window=gugan_lenth).min().shift(1)
    
    

    df['prevVolume'] = df['volume'].shift(1)
    df['prevVolume2'] = df['volume'].shift(2)
    df['prevVolume3'] = df['volume'].shift(3)

    df['prevClose'] = df['close'].shift(1)
    df['prevOpen'] = df['open'].shift(1)

    df['prevHigh'] = df['high'].shift(1)
    df['prevHigh2'] = df['high'].shift(2)

    df['prevLow'] = df['low'].shift(1)
    df['prevLow2'] = df['low'].shift(2)

    df['Disparity20'] = df['prevClose'] / df['prevClose'].rolling(window=20).mean() * 100.0
    
    df['Disparity11'] = df['prevClose'] / df['prevClose'].rolling(window=11).mean() * 100.0


    df['ma3_before'] = df['close'].rolling(3).mean().shift(1)
    df['ma6_before'] = df['close'].rolling(6).mean().shift(1)
    df['ma19_before'] = df['close'].rolling(19).mean().shift(1)


    df['ma10_before'] = df['close'].rolling(10).mean().shift(1)

    df['ma20_before'] = df['close'].rolling(20).mean().shift(1)
    df['ma20_before2'] = df['close'].rolling(20).mean().shift(2)
    df['ma60_before'] = df['close'].rolling(60).mean().shift(1)
    df['ma60_before2'] = df['close'].rolling(60).mean().shift(2)

    df['ma120_before'] = df['close'].rolling(120).mean().shift(1)


    df['prevChangeMa'] = df['change'].shift(1).rolling(window=20).mean()
    

    df['prevChangeMa_S'] = df['change'].shift(1).rolling(window=10).mean()

    #10일마다 총 100일 평균모멘텀스코어
    specific_days = list()

    for i in range(1,11):
        st = i * 10
        specific_days.append(st)

    for day in specific_days:
        column_name = f'Momentum_{day}'
        df[column_name] = (df['prevClose'] > df['close'].shift(day)).astype(int)
        
    df['Average_Momentum'] = df[[f'Momentum_{day}' for day in specific_days]].sum(axis=1) / 10


    # Define the list of specific trading days to compare
    specific_days = list()

    for i in range(1,11):
        st = i * 3
        specific_days.append(st)



    # Iterate over the specific trading days and compare the current market price with the corresponding closing prices
    for day in specific_days:
        # Create a column name for each specific trading day
        column_name = f'Momentum_{day}'
        
        # Compare current market price with the closing price of the specific trading day
        df[column_name] = (df['prevClose'] > df['close'].shift(day)).astype(int)

    # Calculate the average momentum score
    df['Average_Momentum3'] = df[[f'Momentum_{day}' for day in specific_days]].sum(axis=1) / 10



    df.dropna(inplace=True) #데이터 없는건 날린다!

   

    data_dict = {stock_code: df}
    stock_df_list.append(data_dict)
    print("---stock_code---", stock_code , " len ",len(df))
    pprint.pprint(df)





# Combine the OHLCV data into a single DataFrame
combined_df = pd.concat([list(data_dict.values())[0].assign(stock_code=stock_code) for data_dict in stock_df_list for stock_code in data_dict])

# Sort the combined DataFrame by date
combined_df.sort_index(inplace=True)

pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))



IsBuy = False #매수 했는지 여부
BUY_PRICE = 0  #매수한 금액! 

TryCnt = 0      #매매횟수
SuccesCnt = 0   #익절 숫자
FailCnt = 0     #손절 숫자



IsFirstDateSet = False
FirstDateStr = ""
FirstDateIndex = 0


NowInvestCode = ""
InvestMoney = TotalMoney


DivNum = len(InvestStockList)

RemainInvestMoney = InvestMoney




ResultList = list()

TotalMoneyList = list()

NowInvestList = list()

# 사이클 기준 MDD 계산을 위한 변수
CycleStartMoney = 0  # 사이클 시작 시 잔액
CycleEndMoneyList = []  # 각 사이클 종료 시 잔액 리스트
CycleReturnRates = []  # 각 사이클의 수익률
CycleEndDates = []  # 각 사이클 종료 날짜

IsCut = False
IsCutCnt = 0

# 매매 로그 및 사이클 기록
trade_logs = []
balance_logs = []
cycle_counter = 0

i = 0
# Iterate over each date
for date in combined_df.index.unique():
 
    #날짜 정보를 획득
    date_format = "%Y-%m-%d %H:%M:%S"
    date_object = None

    try:
        date_object = datetime.strptime(str(date), date_format)
    
    except Exception as e:
        try:
            date_format = "%Y%m%d"
            date_object = datetime.strptime(str(date), date_format)

        except Exception as e2:
            date_format = "%Y-%m-%d"
            date_object = datetime.strptime(str(date), date_format)




    all_stocks = combined_df.loc[combined_df.index == date].groupby('stock_code')['close'].max().nlargest(DivNum)
    
    #######################################################################################################################################
    #횡보장을 정의하기 위한 로직!!
    # https://blog.naver.com/zacra/223225906361 이 포스팅을 정독하세요!!!
    Kosdaq_Long_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "233740")]
    Kosdaq_Short_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "251340")]
    Kospi_Long_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "122630")]
    Kospi_Short_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "252670")]
    
    IsNoWay = False
    if len(Kosdaq_Long_Data) == 1 and len(Kosdaq_Short_Data) == 1 and len(Kospi_Long_Data) == 1 and len(Kospi_Short_Data) == 1:
        if  (Kospi_Long_Data['prevChangeMa_S'].values[0] > 0 and Kospi_Short_Data['prevChangeMa_S'].values[0] > 0) or (Kospi_Long_Data['prevChangeMa_S'].values[0] < 0 and Kospi_Short_Data['prevChangeMa_S'].values[0] < 0)  or (Kosdaq_Long_Data['prevChangeMa_S'].values[0] > 0 and Kosdaq_Short_Data['prevChangeMa_S'].values[0] > 0) or (Kosdaq_Long_Data['prevChangeMa_S'].values[0] < 0 and Kosdaq_Short_Data['prevChangeMa_S'].values[0] < 0) :
            IsNoWay = True
    #######################################################################################################################################



    i += 1


    today_sell_code = list()



    items_to_remove = list()


    Kosdaq_sell_cnt = 0

    Kosdaq_sell_money_furture = 0


    #투자중인 종목들!!
    for investData in NowInvestList:

        stock_code = investData['stock_code'] 
        
        if investData['InvestMoney'] > 0:
            stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

            if len(stock_data) == 1:
                
                ####!!!!코스닥 전략!!!####
                #조건 만족시 매도 한다!
                if stock_code in ["233740","251340"]:
                    
                        
                    NowOpenPrice = stock_data['open'].values[0]
                    PrevOpenPrice = stock_data['prevOpen'].values[0] 
                    PrevClosePrice = stock_data['prevClose'].values[0] 


                    CutRate = 0.4

                    # KODEX 코스닥150선물인버스
                    if stock_code == "251340":
                        CutRate = 0.4

                    # KODEX 코스닥150레버리지
                    else:

                        if PrevClosePrice > stock_data['ma60_before'].values[0]:
                            CutRate = 0.4
                        else:
                            CutRate = 0.3



                    #목표컷 매도가! 시가 - (전일종가 - 전일저가) x CutRate 
                    CutPrice = stock_data['open'].values[0] - ((stock_data['prevHigh'].values[0] - stock_data['prevLow'].values[0]) * CutRate)

                    SellPrice = NowOpenPrice


                    IsSellGo = False


                    #하향 돌파했다면 매도 고고!!
                    if CutPrice >= stock_data['low'].values[0] :
                        IsSellGo = True
                        SellPrice = CutPrice


                    #매일 매일 투자금 반영!
                    if investData['DolPaCheck'] == False:
                        investData['DolPaCheck'] = True
                        investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((SellPrice - investData['BuyPrice'] ) / investData['BuyPrice'] ))
                    else:
                        investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((SellPrice - PrevOpenPrice ) / PrevOpenPrice))


                    #진입(매수)가격 대비 변동률
                    Rate = (SellPrice* (1.0 - fee) - investData['BuyPrice']) / investData['BuyPrice']


                    RevenueRate = (Rate - fee)*100.0 #수익률 계산

                    if IsSellGo == True :

                        Kosdaq_sell_cnt += 1 #코스닥 돌파 매도가 일어난 날!
                        
                        
                        if RevenueRate < 0:
                            IsCut = True
                            IsCutCnt += 1
                        else:
                            IsCut = False
                            IsCutCnt -= 1
                            if IsCutCnt < 0:
                                IsCutCnt = 0

                        ReturnMoney = (investData['InvestMoney'] * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                        if NowOpenPrice > CutPrice:
                            Kosdaq_sell_money_furture += ReturnMoney

                        TryCnt += 1

                        if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                            SuccesCnt += 1
                        else:
                            FailCnt += 1
            
                        #종목별 성과를 기록한다.
                        for stock_data in StockDataList:
                            if stock_code == stock_data['stock_code']:
                                stock_data['try'] += 1
                                if RevenueRate > 0:
                                    stock_data['success'] += 1
                                else:
                                    stock_data['fail'] +=1
                                stock_data['accRev'] += RevenueRate


                        
                        RemainInvestMoney += ReturnMoney
                        investData['InvestMoney'] = 0


                        NowInvestMoney = 0
                        for iData in NowInvestList:
                            NowInvestMoney += iData['InvestMoney']

                        InvestMoney = RemainInvestMoney + NowInvestMoney

                        log_msg = f"[사이클 {cycle_counter}] {GetStockName(stock_code, StockDataList)} ({stock_code}) {str(date)} >>> 매도: Exit {SellPrice * (1.0 - fee):.2f}, 매수가: {investData['BuyPrice']:.2f}, 수익률: {round(RevenueRate,2)}%, 회수금: {round(ReturnMoney,2)}"
                        print(log_msg)
                        trade_logs.append(log_msg)
                                
                        items_to_remove.append(investData)

                        today_sell_code.append(stock_code)

                ####!!!!코스피 전략!!!####
                #조건 만족시 매도 한다!
                else:
                    

                    NowOpenPrice = stock_data['open'].values[0]
                    PrevOpenPrice = stock_data['prevOpen'].values[0] 
                    PrevClosePrice = stock_data['prevClose'].values[0] 


                    SellPrice = NowOpenPrice

 
                    IsSellGo = False

                    #매일 매일 투자금 반영!
                    if investData['DolPaCheck'] == False:
                        investData['DolPaCheck'] = True
                        investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((SellPrice - investData['BuyPrice'] ) / investData['BuyPrice'] ))
                    else:
                        investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((SellPrice - PrevOpenPrice ) / PrevOpenPrice))


                    #진입(매수)가격 대비 변동률
                    Rate = (SellPrice* (1.0 - fee) - investData['BuyPrice']) / investData['BuyPrice']

                    RevenueRate = (Rate - fee)*100.0 #수익률 계산
                    
                    # KODEX 200선물인버스2X
                    if stock_code == "252670":
                        
                        if stock_data['Disparity11'].values[0] > 105:

                            if  PrevClosePrice < stock_data['ma3_before'].values[0]: 
                                IsSellGo = True

                        else:

                            if PrevClosePrice < stock_data['ma6_before'].values[0] and PrevClosePrice < stock_data['ma19_before'].values[0] : 
                                IsSellGo = True

                    # KODEX 레버리지
                    else:

                        total_volume = (stock_data['prevVolume'].values[0]+ stock_data['prevVolume2'].values[0] +stock_data['prevVolume3'].values[0]) / 3.0

                        Disparity = stock_data['Disparity20'].values[0] 

                        if (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0] or stock_data['prevVolume'].values[0] < total_volume) and (Disparity < 98 or Disparity > 105):
                            print("hold..")
                        else:
                            IsSellGo = True
                    

             
             

                    #조건 만족 했다면 매도 고고!
                    if IsSellGo == True :


                        ReturnMoney = (investData['InvestMoney'] * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!


                        TryCnt += 1

                        if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                            SuccesCnt += 1
                        else:
                            FailCnt += 1
            
                        #종목별 성과를 기록한다.
                        for stock_data in StockDataList:
                            if stock_code == stock_data['stock_code']:
                                stock_data['try'] += 1
                                if RevenueRate > 0:
                                    stock_data['success'] += 1
                                else:
                                    stock_data['fail'] +=1
                                stock_data['accRev'] += RevenueRate


                        
                        RemainInvestMoney += ReturnMoney
                        investData['InvestMoney'] = 0


                        #pprint.pprint(NowInvestList)

                        NowInvestMoney = 0
                        for iData in NowInvestList:
                            NowInvestMoney += iData['InvestMoney']

                        InvestMoney = RemainInvestMoney + NowInvestMoney

                        log_msg = f"[사이클 {cycle_counter}] {GetStockName(stock_code, StockDataList)} ({stock_code}) {str(date)} >>> 매도: Exit {SellPrice * (1.0 - fee):.2f}, 매수가: {investData['BuyPrice']:.2f}, 수익률: {round(RevenueRate,2)}%, 회수금: {round(ReturnMoney,2)}"
                        print(log_msg)
                        trade_logs.append(log_msg)
                                
                        items_to_remove.append(investData)

                        today_sell_code.append(stock_code)


    #리스트에서 제거
    for item in items_to_remove:
        NowInvestList.remove(item)
    
    # 사이클 종료 기록 (모든 포지션 청산)
    if len(NowInvestList) == 0 and CycleStartMoney > 0:
        CycleEndMoneyList.append(InvestMoney)
        cycle_return = ((InvestMoney - CycleStartMoney) / CycleStartMoney) * 100
        CycleReturnRates.append(cycle_return)
        CycleEndDates.append(date)  # 종료 날짜 기록
        print(f"[{date}] 🔄 사이클 종료: 시작 잔액 {CycleStartMoney:,.0f} → 종료 잔액 {InvestMoney:,.0f} (수익률: {cycle_return:+.2f}%)")
        cycle_counter += 1  # 사이클 카운터 증가
        CycleStartMoney = 0  # 초기화





    #최대 2개 종목만 투자 가능함! 코스피 매수 조건 체크!
    #즉 코스피 먼저 매수 여부를 판단하여 매수한다!
    if len(NowInvestList) < int(DivNum)/2 and int(date_object.strftime("%Y")) >= StartYear:

        if IsFirstDateSet == False:
            FirstDateStr = str(date)
            FirstDateIndex = i-1
            IsFirstDateSet = True


        for stock_code in all_stocks.index:

            IsAlReadyInvest = False
            for investData in NowInvestList:
                if stock_code == investData['stock_code']: 
                    IsAlReadyInvest = True
                    break    
            
            if stock_code not in today_sell_code and IsAlReadyInvest == False:

                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]
                ####!!!!코스피 전략!!!####
                if stock_code in ["122630","252670"]:
                    

                    PrevClosePrice = stock_data['prevClose'].values[0] 
                    
                    DolPaPrice = stock_data['open'].values[0]


                    IsBuyGo = False
                    
                    
                    
                    # KODEX 200선물인버스2X
                    if stock_code == "252670":


                        if PrevClosePrice > stock_data['ma3_before'].values[0]  and PrevClosePrice > stock_data['ma6_before'].values[0]  and PrevClosePrice > stock_data['ma19_before'].values[0] and stock_data['prevRSI'].values[0] < 70 and stock_data['prevRSI2'].values[0] < stock_data['prevRSI'].values[0]:
                            if (stock_data['prevVolume2'].values[0] < stock_data['prevVolume'].values[0]) and (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0]) and PrevClosePrice > stock_data['ma60_before'].values[0] and stock_data['ma60_before2'].values[0] < stock_data['ma60_before'].values[0]  and stock_data['ma3_before'].values[0]  > stock_data['ma6_before'].values[0]  > stock_data['ma19_before'].values[0]  :
                                IsBuyGo = True

                    # KODEX 레버리지
                    else:

                        Disparity = stock_data['Disparity20'].values[0] 
                        
                        if (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0]) and (Disparity < 98 or Disparity > 106) and stock_data['prevRSI'].values[0] < 80 :
                            IsBuyGo = True

        
                    #조건을 만족했다면 매수 고고!
                    if IsBuyGo == True :



                        Rate = 1.0


                        #InvestGoMoney = (InvestMoney / len(InvestStockList)) * Rate
                        InvestGoMoney = 0



                        if IsNoWay == True:
                            InvestGoMoney = ((RemainInvestMoney - Kosdaq_sell_money_furture) / len(InvestStockList)) * Rate

                        else:
                     
                            if len(NowInvestList) + Kosdaq_sell_cnt == 0:

                                InvestGoMoney = (RemainInvestMoney - Kosdaq_sell_money_furture) * 0.5 * Rate

                            else:
                                InvestGoMoney = (RemainInvestMoney - Kosdaq_sell_money_furture) * Rate
                    
                   
            


                        if Rate > 0:


                            BuyAmt = int(InvestGoMoney /  DolPaPrice) #매수 가능 수량을 구한다!

                            NowFee = (BuyAmt*DolPaPrice) * fee



                            #매수해야 되는데 남은돈이 부족하다면 수량을 하나씩 감소시켜 만족할 때 매수한다!!
                            while (RemainInvestMoney - Kosdaq_sell_money_furture)  < (BuyAmt*DolPaPrice) + NowFee:
                                if (RemainInvestMoney - Kosdaq_sell_money_furture)  > DolPaPrice:
                                    BuyAmt -= 1
                                    NowFee = (BuyAmt*DolPaPrice) * fee
                                else:
                                    break
                            
                            if BuyAmt > 0:



                                RealInvestMoney = (BuyAmt*DolPaPrice) #실제 들어간 투자금

                                RemainInvestMoney -= (BuyAmt*DolPaPrice) #남은 투자금!
                                RemainInvestMoney -= NowFee


                                InvestData = dict()

                                InvestData['stock_code'] = stock_code
                                InvestData['InvestMoney'] = RealInvestMoney
                                InvestData['FirstMoney'] = RealInvestMoney
                                InvestData['BuyPrice'] = DolPaPrice
                                InvestData['DolPaCheck'] = False
                                InvestData['Date'] = str(date)

                                # 사이클 시작 기록 (0개에서 1개로 진입) - 코스피
                                if len(NowInvestList) == 0:
                                    CycleStartMoney = InvestMoney

                                NowInvestList.append(InvestData)


                                NowInvestMoney = 0
                                for iData in NowInvestList:
                                    NowInvestMoney += iData['InvestMoney']

                                InvestMoney = RemainInvestMoney + NowInvestMoney


                                log_msg = f"[사이클 {cycle_counter}] {GetStockName(stock_code, StockDataList)} ({stock_code}) {str(date)} >>> 매수: Entry {DolPaPrice:.2f}, 매수금액: {round(RealInvestMoney,2)}"
                                print(log_msg)
                                trade_logs.append(log_msg)

             
             

    #최대 2개 종목만 투자 가능함! 코스닥 매수 조건 체크!
    if len(NowInvestList) < int(DivNum)/2 and int(date_object.strftime("%Y")) >= StartYear:

        for stock_code in all_stocks.index:

            IsAlReadyInvest = False
            for investData in NowInvestList:
                if stock_code == investData['stock_code']: 
                    IsAlReadyInvest = True
                    break    
            

            if stock_code not in today_sell_code and IsAlReadyInvest == False:

                #코스닥 매도가 일어났는데 현재 또 코스피에 보유중인 종목이 있다면 코스닥 매도는 장중 매도니깐 이때는 매도하지 않음!
                #if Kosdaq_sell_cnt == 1 and len(NowInvestList) == 1:
                #    continue

                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]
                
                ####!!!!코스닥 전략!!!####
                if stock_code in ["233740","251340"]:
                    

                    PrevClosePrice = stock_data['prevClose'].values[0] 

                    DolpaRate = 0.4


                    #KODEX 코스닥150선물인버스
                    if stock_code == "251340":

                        DolpaRate = 0.4

                    #KODEX 코스닥150레버리지
                    else: 

                        if PrevClosePrice > stock_data['ma60_before'].values[0]:
                            DolpaRate = 0.3
                        else:
                            DolpaRate = 0.4

                    ##########################################################################
                    #갭 상승 하락을 이용한 돌파값 조절!
                    # https://blog.naver.com/zacra/223277173514 이 포스팅을 체크!!!!
                    ##########################################################################
                    Gap = ((abs(stock_data['open'].values[0] - PrevClosePrice) / PrevClosePrice)) * 100.0

                    GapSt = (Gap*0.025)

                    if GapSt > 1.0:
                        GapSt = 1.0
                    if GapSt < 0:
                        GapSt = 0.1

                    if PrevClosePrice > stock_data['open'].values[0] and Gap >= 3.0:
                        DolpaRate *= (1.0 + GapSt)

                    if PrevClosePrice < stock_data['open'].values[0] and Gap >= 3.0:
                        DolpaRate *= (1.0 - GapSt)


                    #변동성 돌파 시가 + (전일고가-전일저가)*DolpaRate
                    DolPaPrice = stock_data['open'].values[0] + ((stock_data['prevHigh'].values[0] - stock_data['prevLow'].values[0]) * DolpaRate)



                    IsBuyGo = False

                    DolPaRate = (DolPaPrice - stock_data['open'].values[0]) / stock_data['open'].values[0] * 100

                    #돌파 했다면 매수 고???
                    if DolPaPrice <= stock_data['high'].values[0]  :


                        IsBuyGo = True

                        #추가 필터를 거쳐 아래 조건을 만족하면 매수하지 않는다!

                        #KODEX 코스닥150선물인버스
                        if stock_code == "251340":
                            if stock_data['prevClose'].values[0] <= stock_data['ma20_before'].values[0]:
                                IsBuyGo = False 
        
                        #KODEX 코스닥150레버리지
                        else: 

                            if stock_data['prevLow'].values[0] > stock_data['open'].values[0] and stock_data['prevClose'].values[0] < stock_data['ma10_before'].values[0]:
                                IsBuyGo = False 

                        # 추가 개선 로직 https://blog.naver.com/zacra/223326173552 이 포스팅 참고!!!!
                        IsJung = False    
                        if stock_data['ma10_before'].values[0] > stock_data['ma20_before'].values[0] > stock_data['ma60_before'].values[0] > stock_data['ma120_before'].values[0]:
                            IsJung = True
                            
                        if IsJung == False:
                            
                                    
                            high_price = stock_data['high_'+str(gugan_lenth)+'_max'].values[0] 
                            low_price =  stock_data['low_'+str(gugan_lenth)+'_min'].values[0] 
                            
                            Gap = (high_price - low_price) / 4
                            
                            
                            MaximunPrice = low_price + Gap * 3.0
                            
                            
                            if stock_data['open'].values[0] > MaximunPrice:
                                IsBuyGo = False
            
                        
                            
                            
                    if IsBuyGo == True :
     


                        Rate = 1.0

                        #모멘텀 스코어를 통한 비중 조절!
                        if len(Kosdaq_Long_Data) == 1 and len(Kosdaq_Short_Data) == 1:
                        
                            IsLongStrong = False
                            
                            if Kosdaq_Long_Data['Average_Momentum'].values[0] > Kosdaq_Short_Data['Average_Momentum'].values[0]:
                                IsLongStrong = True
                                
                            IsLongStrong2 = False
                            
                            if Kosdaq_Long_Data['prevChangeMa'].values[0] > Kosdaq_Short_Data['prevChangeMa'].values[0]:
                                IsLongStrong2 = True
                                
                                
                            if IsLongStrong == True and IsLongStrong2 == True:
                                
                                if stock_code == "233740":
                                    Rate = 1.3
                                else:
                                    Rate = 0.7
                                    
                            elif IsLongStrong == False and IsLongStrong2 == False:
                                    
                                if stock_code == "233740":
                                    Rate = 0.7
                                else:
                                    Rate = 1.3
                                    

                                
                        #InvestGoMoney = (InvestMoney / len(InvestStockList)) * Rate
                        InvestGoMoney = 0
                        
                        #############################################################
                        #시스템 손절(?) 관련
                        # https://blog.naver.com/zacra/223225906361 이 포스팅 체크!!!
                        #############################################################
                        AdjustRate = 1.0

                        if IsCut == True and IsCutCnt >= 2:

                            
                            if stock_data['prevOpen'].values[0] > stock_data['prevClose'].values[0] and stock_data['prevHigh2'].values[0] > stock_data['prevHigh'].values[0]:
                                
                                
                                if IsCutCnt >= 4:
                                    AdjustRate = stock_data['Average_Momentum3'].values[0] * 0.5
                                    

                                else:
                                    AdjustRate =  stock_data['Average_Momentum3'].values[0]


                            
                                

                        if IsNoWay == True:
                            InvestGoMoney = ((RemainInvestMoney - Kosdaq_sell_money_furture) / len(InvestStockList)) * Rate * AdjustRate

                        else:
                     
                            if len(NowInvestList) + Kosdaq_sell_cnt == 0:

                                InvestGoMoney = (RemainInvestMoney - Kosdaq_sell_money_furture) * 0.5 * Rate  * AdjustRate

                            else:
                                InvestGoMoney = (RemainInvestMoney - Kosdaq_sell_money_furture) * Rate  * AdjustRate
                    
                   
                        if Rate > 0 and AdjustRate > 0:


                            BuyAmt = int(InvestGoMoney /  DolPaPrice) #매수 가능 수량을 구한다!

                            NowFee = (BuyAmt*DolPaPrice) * fee



                            #매수해야 되는데 남은돈이 부족하다면 수량을 하나씩 감소시켜 만족할 때 매수한다!!
                            while (RemainInvestMoney - Kosdaq_sell_money_furture)  < (BuyAmt*DolPaPrice) + NowFee:
                                if (RemainInvestMoney - Kosdaq_sell_money_furture)  > DolPaPrice:
                                    BuyAmt -= 1
                                    NowFee = (BuyAmt*DolPaPrice) * fee
                                else:
                                    break
                            
                            if BuyAmt > 0:



                                RealInvestMoney = (BuyAmt*DolPaPrice) #실제 들어간 투자금

                                RemainInvestMoney -= (BuyAmt*DolPaPrice) #남은 투자금!
                                RemainInvestMoney -= NowFee


                                InvestData = dict()

                                InvestData['stock_code'] = stock_code
                                InvestData['InvestMoney'] = RealInvestMoney
                                InvestData['FirstMoney'] = RealInvestMoney
                                InvestData['BuyPrice'] = DolPaPrice
                                InvestData['DolPaCheck'] = False
                                InvestData['Date'] = str(date)

                                # 사이클 시작 기록 (0개에서 1개로 진입) - 코스닥
                                if len(NowInvestList) == 0:
                                    CycleStartMoney = InvestMoney

                                NowInvestList.append(InvestData)


                                NowInvestMoney = 0
                                for iData in NowInvestList:
                                    NowInvestMoney += iData['InvestMoney']

                                InvestMoney = RemainInvestMoney + NowInvestMoney


                                log_msg = f"[사이클 {cycle_counter}] {GetStockName(stock_code, StockDataList)} ({stock_code}) {str(date)} >>> 매수: Entry {DolPaPrice:.2f}, 매수금액: {round(RealInvestMoney,2)}"
                                print(log_msg)
                                trade_logs.append(log_msg)

        

       


    
    NowInvestMoney = 0

    for iData in NowInvestList:
        NowInvestMoney += iData['InvestMoney']



    InvestMoney = RemainInvestMoney + NowInvestMoney

    InvestCoinListStr = ""
    #print("\n\n------------------------------------")
    for iData in NowInvestList:
        InvestCoinListStr += GetStockName(iData['stock_code'], StockDataList)  + " "

   # print("------------------------------------\n\n")



    


    print("\n\n>>>>>>>>>>>>", InvestCoinListStr, "---> 투자개수 : ", len(NowInvestList))
    pprint.pprint(NowInvestList)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>--))", str(date), " 잔고:",str(InvestMoney) , "=" , str(RemainInvestMoney) , "+" , str(NowInvestMoney), "\n\n" )
    
    balance_log = f"[{str(date)}] 잔고: {InvestMoney:,.0f} = 현금 {RemainInvestMoney:,.0f} + 투자 {NowInvestMoney:,.0f}"
    balance_logs.append(balance_log)

    TotalMoneyList.append(InvestMoney)

    #####################################################
    #####################################################
    #####################################################
    #'''
    
   


#결과 정리 및 데이터 만들기!!
if len(TotalMoneyList) > 0:

    print("TotalMoneyList -> ", len(TotalMoneyList))


    resultData = dict()

    # Create the result DataFrame with matching shapes
    result_df = pd.DataFrame({"Total_Money": TotalMoneyList}, index=combined_df.index.unique())

    result_df['Ror'] = np.nan_to_num(result_df['Total_Money'].pct_change()) + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()
    result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
    
    # 사이클 기준 MDD 계산
    cycle_mdd = 0
    cycle_max_return = 0
    cumsum_cycle_returns = []
    if len(CycleReturnRates) > 0:
        print(f"\n사이클별 수익률: {CycleReturnRates}")
        cumsum = 0
        for ret in CycleReturnRates:
            cumsum += ret
            cumsum_cycle_returns.append(cumsum)
            if cumsum > cycle_max_return:
                cycle_max_return = cumsum
            dd = cumsum - cycle_max_return
            if dd < cycle_mdd:
                cycle_mdd = dd
        print(f"사이클 기준 MDD: {cycle_mdd:.2f}%")

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    pprint.pprint(result_df)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

    resultData['OriMoney'] = result_df['Total_Money'].iloc[0]
    resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
    resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)

    resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0
    resultData['Cycle_MDD'] = cycle_mdd  # 사이클 기준 MDD

    resultData['TryCnt'] = TryCnt
    resultData['SuccesCnt'] = SuccesCnt
    resultData['FailCnt'] = FailCnt

    
    ResultList.append(resultData)
    
    
    result_df.index = pd.to_datetime(result_df.index)

    # 매매 로그를 DataFrame으로 변환
    trade_list = []
    for log in trade_logs:
        if log and ('매수:' in log or '매도:' in log):
            try:
                ticker_match = re.search(r'\((\d+)\)', log)
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', log)
                price_match = re.search(r'Entry ([\d\.]+)|Exit ([\d\.]+)', log)
                
                if ticker_match and date_match and price_match:
                    ticker = ticker_match.group(1)
                    date_str = date_match.group(0)
                    date = pd.Timestamp(date_str)  # Timestamp로 직접 변환
                    trade_type = '매수' if '매수:' in log else '매도'
                    price = float(price_match.group(1) or price_match.group(2))
                    
                    trade_list.append({
                        'ticker': ticker,
                        'date': date,
                        'type': trade_type,
                        'price': price
                    })
            except Exception as e:
                print(f"Error parsing log: {e}")
                continue
    
    trade_df = pd.DataFrame(trade_list) if trade_list else pd.DataFrame(columns=['ticker', 'date', 'type', 'price'])
    
    # 종목명 매핑
    stock_name_map = {stock_data['stock_code']: stock_data['stock_name'] for stock_data in StockDataList}
    
    # GUI 차트 클래스 정의
    class ChartApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("Kosdaqpi 백테스팅 결과 분석")
            self.geometry("1400x900")
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.chart_artists = {}
            self.all_trade_logs_parsed = self.parse_trade_logs(trade_logs)
            self.currently_displayed_logs = self.all_trade_logs_parsed.copy()
            self.sort_info = {'col': None, 'reverse': False}
            self.highlight_plot = None
            self.create_widgets()

        def create_widgets(self):
            main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            main_pane.pack(fill=tk.BOTH, expand=True)
            left_panel = ttk.Frame(main_pane)
            main_pane.add(left_panel, weight=1)
            filter_frame = ttk.Frame(left_panel)
            filter_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Label(filter_frame, text="종목:").grid(row=0, column=0, padx=(5,2), pady=5, sticky='w')
            self.filter_ticker_var = tk.StringVar()
            self.filter_ticker_entry = ttk.Entry(filter_frame, textvariable=self.filter_ticker_var, width=12)
            self.filter_ticker_entry.grid(row=0, column=1, padx=(0,10), pady=5, sticky='w')
            ttk.Label(filter_frame, text="종류:").grid(row=0, column=2, padx=(5,2), pady=5, sticky='w')
            self.filter_type_var = tk.StringVar()
            self.filter_type_combo = ttk.Combobox(filter_frame, textvariable=self.filter_type_var, values=['', '매수', '매도'], width=8)
            self.filter_type_combo.grid(row=0, column=3, padx=(0,5), pady=5, sticky='w')
            apply_button = ttk.Button(filter_frame, text="적용", command=self.apply_filters_and_sort)
            apply_button.grid(row=0, column=4, padx=5, pady=5)
            clear_button = ttk.Button(filter_frame, text="초기화", command=self.clear_filters)
            clear_button.grid(row=0, column=5, padx=5, pady=5)
            self.filter_ticker_entry.bind('<Return>', lambda e: self.apply_filters_and_sort())
            log_frame = ttk.Frame(left_panel)
            log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0,5))
            cols = ('Cycle', 'Ticker', 'DateTime', 'Type', 'Price', 'Detail')
            self.log_tree = ttk.Treeview(log_frame, columns=cols, show='headings')
            for col in cols:
                self.log_tree.heading(col, text=col, command=lambda _col=col: self.sort_by_column(_col))
                width = {'Cycle': 50, 'Ticker': 100, 'DateTime': 130, 'Type': 50, 'Price': 100}.get(col, 200)
                anchor = 'e' if col == 'Price' else 'center' if col != 'Detail' else 'w'
                self.log_tree.column(col, width=width, anchor=anchor)
            v_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
            h_scroll = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_tree.xview)
            self.log_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
            v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
            self.log_tree.pack(fill=tk.BOTH, expand=True)
            chart_frame = ttk.Frame(main_pane)
            main_pane.add(chart_frame, weight=3)
            self.tab_control = ttk.Notebook(chart_frame)
            self.tab_control.pack(expand=1, fill="both")
            self.add_overall_tab()
            for stock_code in InvestStockList: 
                self.add_stock_tab(stock_code)
            self.tab_control.bind("<<NotebookTabChanged>>", self.on_tab_changed)
            self.log_tree.bind("<<TreeviewSelect>>", self.on_log_select)
            self.repopulate_log_tree()

        def apply_filters_and_sort(self):
            ticker_filter = self.filter_ticker_var.get().upper()
            type_filter = self.filter_type_var.get()
            current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
            tab_ticker_filter = None
            if current_tab_text != '📊 종합 결과': 
                tab_ticker_filter = current_tab_text.split('(')[-1].rstrip(')')
            logs = self.all_trade_logs_parsed
            if tab_ticker_filter: logs = [log for log in logs if log['ticker'] == tab_ticker_filter]
            if ticker_filter: logs = [log for log in logs if ticker_filter in log['ticker'].upper()]
            if type_filter: logs = [log for log in logs if log['type'] == type_filter]
            self.currently_displayed_logs = logs
            if self.sort_info['col']:
                key_map = {'Cycle': 'cycle', 'Ticker': 'ticker', 'DateTime': 'datetime', 'Type': 'type', 'Price': 'price', 'Detail': 'detail'}
                sort_key = key_map.get(self.sort_info['col'])
                if sort_key in ['price', 'cycle']: self.currently_displayed_logs.sort(key=lambda x: x[sort_key], reverse=self.sort_info['reverse'])
                else: self.currently_displayed_logs.sort(key=lambda x: str(x[sort_key]), reverse=self.sort_info['reverse'])
            self.repopulate_log_tree()

        def clear_filters(self):
            self.filter_ticker_var.set(""); self.filter_type_var.set(""); self.apply_filters_and_sort()

        def sort_by_column(self, col):
            if self.sort_info['col'] == col: self.sort_info['reverse'] = not self.sort_info['reverse']
            else: self.sort_info['col'] = col; self.sort_info['reverse'] = False
            self.apply_filters_and_sort()

        def repopulate_log_tree(self):
            self.log_tree.delete(*self.log_tree.get_children())
            for log in self.currently_displayed_logs:
                self.log_tree.insert('', 'end', values=(log['cycle'], stock_name_map.get(log['ticker'], log['ticker']), log['datetime'].strftime('%Y-%m-%d'), log['type'], f"{log['price']:.2f}", log['detail']))

        def on_tab_changed(self, event):
            self.remove_highlight(); self.apply_filters_and_sort()

        def parse_trade_logs(self, raw_logs):
            parsed = []
            for log in raw_logs:
                if not log or ">>>" not in log: continue
                try:
                    match = re.search(r'\[사이클 (\d+)\] .*?\((\d+)\) (\d{4}-\d{2}-\d{2}) >>> (매수|매도): (?:Entry|Exit) ([\d\.]+), (.*)', log)
                    if match:
                        cycle, ticker, date_str, trade_type, price_str, detail = match.groups()
                        parsed.append({
                            'cycle': int(cycle), 
                            'ticker': ticker.strip(), 
                            'datetime': pd.Timestamp(date_str),  # Timestamp로 직접 변환
                            'type': trade_type, 
                            'price': float(price_str), 
                            'detail': detail.strip()
                        })
                except Exception as e:
                    continue
            return parsed

        def on_log_select(self, event):
            self.remove_highlight()
            selected_items = self.log_tree.selection()
            if not selected_items: return
            item_values = self.log_tree.item(selected_items[0], 'values')
            log_name, log_datetime_str, log_type, log_price_str = item_values[1], item_values[2], item_values[3], item_values[4]
            
            # 종목명에서 종목코드 찾기
            log_ticker = None
            for code, name in stock_name_map.items():
                if name in log_name:
                    log_ticker = code
                    break
            if not log_ticker: return
            
            try:
                log_price = float(log_price_str)
                log_datetime = pd.Timestamp(log_datetime_str)  # Timestamp로 직접 변환
                current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                ticker_key = 'overall' if current_tab_text == '📊 종합 결과' else current_tab_text.split('(')[-1].rstrip(')')
                if ticker_key != 'overall' and ticker_key != log_ticker:
                    for i, tab_id in enumerate(self.tab_control.tabs()):
                        tab_text = self.tab_control.tab(tab_id, "text")
                        if log_ticker in tab_text: 
                            self.tab_control.select(i); 
                            ticker_key = log_ticker; 
                            break
                if ticker_key not in self.chart_artists: return
                artists = self.chart_artists[ticker_key]
                ax, canvas = artists['ax'], artists['canvas']
                y_coord = log_price
                if ticker_key == 'overall':
                    try:
                        nearest_position = result_df.index.get_indexer([log_datetime], method='nearest')[0]
                        closest_date = result_df.index[nearest_position]
                        y_coord = result_df.loc[closest_date, 'Total_Money']
                    except Exception: return
                self.highlight_plot = ax.plot(log_datetime, y_coord, marker='^' if log_type == '매수' else 'v', color='cyan', markersize=15, markeredgecolor='black', zorder=10)[0]
                canvas.draw()
            except Exception as e:
                print(f"Error in on_log_select: {e}")
                return

        def remove_highlight(self):
            if self.highlight_plot:
                self.highlight_plot.remove(); self.highlight_plot = None
                try:
                    current_tab_text = self.tab_control.tab(self.tab_control.select(), "text")
                    ticker_key = 'overall' if current_tab_text == '📊 종합 결과' else current_tab_text.split('(')[-1].rstrip(')')
                    if ticker_key in self.chart_artists: self.chart_artists[ticker_key]['canvas'].draw()
                except Exception: pass

        def on_closing(self):
            self.quit(); self.destroy()

        def create_chart_frame(self, parent_tab):
            frame = ttk.Frame(parent_tab)
            frame.pack(fill='both', expand=True)
            fig = Figure(dpi=100)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
            toolbar = NavigationToolbar2Tk(canvas, frame)
            toolbar.update()
            return fig, canvas

        def add_overall_tab(self):
            overall_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(overall_tab, text='📊 종합 결과')
            fig, canvas = self.create_chart_frame(overall_tab)
            axs = fig.subplots(3, 1, sharex=True, gridspec_kw={'height_ratios': [2, 2, 1]})
            fig.tight_layout(pad=3.0)
            
            axs[0].plot(result_df.index, result_df['Total_Money'], label='Strategy (Linear)', color='blue')
            axs[0].set_title('Overall Performance (Linear Scale)', fontsize=12)
            axs[0].set_ylabel('Total Money (KRW)')
            axs[0].grid(True, which='both', linestyle='--', linewidth=0.5)
            axs[0].legend()
            axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            axs[1].plot(result_df.index, result_df['Total_Money'], label='Strategy (Log)', color='black')
            axs[1].set_yscale('log')
            axs[1].set_title('Overall Performance (Log Scale)', fontsize=12)
            axs[1].set_ylabel('Total Money (KRW)')
            axs[1].grid(True, which='both', linestyle='--', linewidth=0.5)
            axs[1].legend()
            axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            axs[2].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD (일별잔액)', color='red', linewidth=2)
            axs[2].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown (일별)', color='orange', alpha=0.5)
            if len(CycleEndDates) > 0 and len(cumsum_cycle_returns) > 0:
                cycle_dd_values = []
                cycle_peak = 0
                for cumret in cumsum_cycle_returns:
                    if cumret > cycle_peak: cycle_peak = cumret
                    dd = cumret - cycle_peak
                    cycle_dd_values.append(dd)
                cycle_dates_dt = pd.to_datetime(CycleEndDates)
                axs[2].step(cycle_dates_dt, cycle_dd_values, where='post', label=f'Drawdown (사이클)', color='purple', linewidth=2, linestyle='--')
                axs[2].axhline(y=cycle_mdd, color='purple', linestyle=':', linewidth=1.5, alpha=0.7, label=f'MDD (사이클): {cycle_mdd:.2f}%')
            axs[2].set_title('Drawdown Comparison', fontsize=12)
            axs[2].set_ylabel('Drawdown (%)')
            axs[2].grid(True)
            axs[2].legend()
            axs[2].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
            
            self.chart_artists['overall'] = {'fig': fig, 'canvas': canvas, 'ax': axs[1]}
            canvas.draw()

        def add_stock_tab(self, stock_code):
            stock_name = stock_name_map.get(stock_code, stock_code)
            stock_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(stock_tab, text=f'{stock_name} ({stock_code})')
            fig, canvas = self.create_chart_frame(stock_tab)
            axs = fig.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [3, 1]})
            fig.tight_layout(pad=3.0)
            
            try:
                stock_df = stock_df_list[InvestStockList.index(stock_code)][stock_code]
                # 인덱스가 datetime 형식인지 확인하고 변환
                if not isinstance(stock_df.index, pd.DatetimeIndex):
                    stock_df.index = pd.to_datetime(stock_df.index)
                
                stock_trades = trade_df[trade_df['ticker'] == stock_code] if not trade_df.empty else pd.DataFrame()
                
                axs[0].plot(stock_df.index, stock_df['close'], label=f'{stock_name} Price', color='black', alpha=0.8)
                axs[0].set_yticklabels([])
                
                if not stock_trades.empty:
                    buy_trades = stock_trades[stock_trades['type'] == '매수']
                    sell_trades = stock_trades[stock_trades['type'] == '매도']
                    if not buy_trades.empty:
                        axs[0].plot(buy_trades['date'], buy_trades['price'], '^', color='green', markersize=8, label='Buy')
                    if not sell_trades.empty:
                        axs[0].plot(sell_trades['date'], sell_trades['price'], 'v', color='red', markersize=8, label='Sell')
                
                axs[0].set_title(f'Price Chart & Trades (Linear Scale)', fontsize=12)
                axs[0].set_ylabel(f'Price (KRW)')
                axs[0].grid(True, which='both')
                axs[0].legend()
                
                axs[1].plot(stock_df.index, stock_df['close'].pct_change().cumsum() * 100, label='Cumulative Return', color='blue')
                axs[1].set_title('Cumulative Return', fontsize=12)
                axs[1].set_ylabel('Return (%)')
                axs[1].grid(True)
                axs[1].legend()
                
                self.chart_artists[stock_code] = {'fig': fig, 'canvas': canvas, 'ax': axs[0]}
                canvas.draw()
            except Exception as e:
                print(f"Error creating chart for {stock_code}: {e}")
                # 에러 발생 시 빈 차트 표시
                axs[0].text(0.5, 0.5, f'Error loading chart for {stock_name}', 
                           ha='center', va='center', transform=axs[0].transAxes)
                axs[0].set_title(f'{stock_name} ({stock_code})', fontsize=12)
                canvas.draw()

    # 서버 환경 체크 및 GUI 실행
    pcServerGb = socket.gethostname()
    if pcServerGb != "AutoBotCong" and len(trade_logs) > 0:
        app = ChartApp()
        app.mainloop()
        print("\n차트 창이 닫혔습니다. 최종 통계 결과를 출력합니다.")
    else:
        if pcServerGb == "AutoBotCong":
            print("\n서버 환경이므로 GUI를 생략하고 최종 통계 결과를 바로 출력합니다.")
        else:
            print("\n거래 내역이 없어 GUI를 생략합니다.")
    
    for idx, row in result_df.iterrows():
        print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
        

    # 월별 수익률 및 잔액 계산
    print("\n\n########## 월별 수익률 및 잔액 ##########")
    monthly_ror = result_df['Ror'].resample('M').apply(lambda x: (x.prod() - 1) * 100)
    monthly_balance = result_df['Total_Money'].resample('M').last()
    for (date_ror, ror), (date_bal, balance) in zip(monthly_ror.items(), monthly_balance.items()):
        if not pd.isna(ror):
            print(f"{date_ror.strftime('%Y-%m')}: 수익률 {ror:>7.2f}%  |  잔액: {format(int(round(balance, 0)), ','):>15}")

    # 연도별 수익률 및 잔액 계산
    print("\n\n########## 연도별 수익률 및 잔액 ##########")
    yearly_ror = result_df['Ror'].resample('Y').apply(lambda x: (x.prod() - 1) * 100)
    yearly_balance = result_df['Total_Money'].resample('Y').last()
    for (date_ror, ror), (date_bal, balance) in zip(yearly_ror.items(), yearly_balance.items()):
        if not pd.isna(ror):
            print(f"{date_ror.strftime('%Y')}년: 수익률 {ror:>7.2f}%  |  잔액: {format(int(round(balance, 0)), ','):>15}")
    print("##########################################\n\n")


#데이터를 보기좋게 프린트 해주는 로직!
print("\n\n--------------------")


for result in ResultList:

    print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")

    for stock_data in StockDataList:
        print(stock_data['stock_name'] , " (", stock_data['stock_code'],")")
        if stock_data['try'] > 0:
            print("성공:", stock_data['success'] , " 실패:", stock_data['fail']," -> 승률: ", round(stock_data['success']/stock_data['try'] * 100.0,2) ," %")
            print("매매당 평균 수익률:", round(stock_data['accRev']/ stock_data['try'],2) )
        print()

    print("---------- 총 결과 ----------")
    print("최초 금액:", format(int(round(TotalMoney,0)), ',') , " 최종 금액:", format(int(round(result['FinalMoney'],0)), ','), " \n수익률:", round(((round(result['FinalMoney'],2) - round(TotalMoney,2) ) / round(TotalMoney,2) ) * 100,2) ,"% MDD:",  round(result['MDD'],2),"%")
    if result['TryCnt'] > 0:
        print("성공:", result['SuccesCnt'] , " 실패:", result['FailCnt']," -> 승률: ", round(result['SuccesCnt']/result['TryCnt'] * 100.0,2) ," %")

    print("------------------------------")
    print("####################################")
