'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


관련 포스팅

미국 주식 양방향 매매 최종판 (TQQQ / SQQQ, SOXL / SOXS) - 하락장에서도 안정적 수익내기
https://blog.naver.com/zacra/223097613599

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

import pandas as pd
import pprint
import matplotlib.pyplot as plt
import time
import FinanceDataReader as fdr
import socket

# GUI 및 차트 연동을 위한 라이브러리
import tkinter as tk
from tkinter import ttk
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import font_manager

# 폰트 설정
try:
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

    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

except Exception as e:
    print(f"폰트 설정 중 오류 발생: {e}")
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL



#이렇게 직접 금액을 지정해도 된다!!
TotalMoney = 10000000

fee = 0.0035 #수수료+세금+슬리피지를 매수매도마다 0.2%로 세팅!


print("테스트하는 총 금액: $", round(TotalMoney))

########################################################################
########################################################################
'''
아래 코드를  통해 투자 비중을 조절해 보세요.
지금은 7:3 비중으로 투자한다고 가정한 설정이겠죠?

만약 인버스만 투자한 결과를 보고 싶다면 레버리지의 비중을 0으로 만들거나 잠시 삭제하고(주석처리) 테스트하시면 됩니다!
'''
########################################################################
########################################################################

InvestStockList = list()

#3배 레버리지 ETF
#'''
InvestDataDict = dict()
InvestDataDict['ticker'] = "TQQQ" 
InvestDataDict['rate'] = 0.35
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXL" 
InvestDataDict['rate'] = 0.35
InvestStockList.append(InvestDataDict)
#'''

#3배 인버스 ETF
#'''
InvestDataDict = dict()
InvestDataDict['ticker'] = "SQQQ" 
InvestDataDict['rate'] = 0.15
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXS" 
InvestDataDict['rate'] = 0.15
InvestStockList.append(InvestDataDict)
#'''

ResultList = list()
AvgPrice = 0


TotalResultDict= dict()


for stock_data in InvestStockList:

    stock_code = stock_data['ticker']

    print("\n----stock_code: ", stock_code)

    stock_name = stock_code

    InvestMoney = TotalMoney * stock_data['rate']
    

    print(stock_name, " 종목당 할당 투자금:", InvestMoney)



    DivNum = 40.0


    InvestMoneyCell = InvestMoney / DivNum
    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney

    BuyCnt = 0 #회차
    TotalBuyAmt = 0 #매수 수량
    TotalPureMoney = 0 #매수 금액


    #일봉 정보를 가지고 온다!
    df = Common.GetOhlcv("US",stock_code, 3500) 

    print(len(df))

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
    ########################################

    
    ############# 이동평균선! ###############
    df['3ma'] = df['close'].rolling(3).mean()
    df['5ma'] = df['close'].rolling(5).mean()
    df['10ma'] = df['close'].rolling(10).mean()
    df['20ma'] = df['close'].rolling(20).mean()
    df['50ma'] = df['close'].rolling(50).mean()
    df['60ma'] = df['close'].rolling(60).mean()
    df['100ma'] = df['close'].rolling(100).mean()
    df['200ma'] = df['close'].rolling(200).mean()
    df['210ma'] = df['close'].rolling(210).mean()
    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)
    
    #df = df[:len(df)-100]


    IsBuy = False #매수 했는지 여부
    SuccesCnt = 0   #익절 숫자
    FailCnt = 0     #손절 숫자


    IsNoCash = False


    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0
   

    TotalMoneyList = list()
    AvgPrice = 0



    for i in range(len(df)):

        #종가 기준으로 테스트 하려면 open 을 close로 변경!!
        #NowOpenPrice = df['close'].iloc[i]  
        #PrevOpenPrice = df['close'].iloc[i-1]  
        
        
        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]
        
        
            
        #매수된 상태라면..
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            RealInvestMoney = RealInvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))



            TargetRate = 10.0 / 100.0 #목표수익률 10%!!!
            

            TakePrice = AvgPrice * (1.0 + TargetRate) #익절가격


            #진입(매수)가격 대비 변동률
            Rate = (NowOpenPrice - AvgPrice) / AvgPrice

            RevenueRate = (Rate - fee)*100.0 #수익률 계산
        
            #TQQQ, SOXL의 경우
            if stock_code == 'TQQQ' or stock_code == 'SOXL':

                #목표 수익을 달성했거나 회차가 다 찼거나.. 남은 현금이 없을 때..
                if (TakePrice <= NowOpenPrice) or BuyCnt >= DivNum or IsNoCash == True:

                            
                    Disparity = (PrevClosePrice/df['5ma'].iloc[i-1])*100.0
                    
                    st_disparity = 102
                    
                    if stock_code == 'TQQQ':
                        st_disparity = 103

                    #목표수익률을 달성했다면 바로 익절! 정리!!
                    if TakePrice <= NowOpenPrice and Disparity > st_disparity :


                        InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                        print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, " >>>>>>>>매도! 누적수량:",TotalBuyAmt,">>>>>>>> 매도! \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2) , " 이전종가:",round(PrevClosePrice,2),"\n\n")
                        print("\n\n")

                        BuyCnt = 0

                        TotalBuyAmt = 0
                        TotalPureMoney = 0

                        RealInvestMoney = 0
                        RemainInvestMoney = InvestMoney
                        AvgPrice = 0



                        SuccesCnt += 1
                        IsBuy = False #매도했다


                    #그게 아니라면 돈이 없거나 40회 다 찬거다.. 1/4 쿼터 손절!!!
                    else:
                        
                        Test_div = 8.0
                        
                        if df['20ma'].iloc[i-2] > df['20ma'].iloc[i-1] and df['60ma'].iloc[i-2] > df['60ma'].iloc[i-1]:
                            Test_div = 6.0
                        
                        BuyCnt = BuyCnt - int(BuyCnt / Test_div)

                        CutAmt = int(TotalBuyAmt / Test_div)


                        NowFee = (CutAmt*NowOpenPrice) * fee

                        #해당 수량을 감소 시키고! 금액도 감소시킨다!
                        TotalBuyAmt -= CutAmt
                        TotalPureMoney -= (CutAmt*NowOpenPrice)
                        
                        RealInvestMoney -= (CutAmt*NowOpenPrice) #실제 들어간 투자금
                        
                        RemainInvestMoney += (CutAmt*NowOpenPrice) #남은 투자금!
                        RemainInvestMoney -= NowFee

                        InvestMoney = RemainInvestMoney + RealInvestMoney

                        #AvgPrice = TotalPureMoney / TotalBuyAmt
                        
                        InvestMoneyCell = InvestMoney / DivNum
                        print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, " >>>>>>>매도수량:", CutAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 쿼터손절!  \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n\n")

                        FailCnt +=1
                        IsNoCash = False
                    
                    
                

                else:
                    #아직 회차가 다 안찼다면! 매일 매수를 진행한다!
                    if BuyCnt < DivNum:


                        
                        ###################### 개선된 점 #######################
                        #########################################################
                        IsBuyGo = False
                        
                        if df['100ma'].iloc[i-1] > df['close'].iloc[i-1]: # 개선된 점 GMA  

                            if df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]: # 개선된 점 GMA  
                                IsBuyGo = True

                        else: #200일선 위에 있는 상승장엔 기존 처럼 매일 매수!
      
                            IsBuyGo = True
                        
                        
                            
                        #########################################################
                        #########################################################


                        if df['rsi'].iloc[i-1] >= 80: # 개선된 점 GMA #RSI 80이상의 과매도 구간에선 회차 매수 안함!!
                            IsBuyGo = False



                        ###################### 개선된 점 #######################
                        #########################################################
                        
                        Disparity = (PrevClosePrice/df['5ma'].iloc[i-1])*100.0
                        
                        st_disparity = 97
                        
                        if stock_code == 'SOXL':
                            st_disparity = 108
                            
                        
                        #200일선 위에 있다가 아래로 종가가 떨어지면... 다음날 시가로 모두 매도!!!
                        if (df['200ma'].iloc[i-2] < df['close'].iloc[i-2]  and df['200ma'].iloc[i-1] > df['close'].iloc[i-1]) and Disparity < st_disparity:
                        

                            InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                            print("-----> !!!CUT!!!!", stock_code ," ", df.iloc[i].name, " " ,BuyCnt, " >>>>>>>>매도! 누적수량:",TotalBuyAmt,">>>>>>>> 매도! \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n\n")
                            print("\n\n")

                            BuyCnt = 0

                            TotalBuyAmt = 0
                            TotalPureMoney = 0

                            RealInvestMoney = 0
                            RemainInvestMoney = InvestMoney
                            AvgPrice = 0



                            FailCnt +=1
                            IsBuy = False #매도했다
                            
                            
                            
                            IsBuyGo = False
                        #########################################################
                        #########################################################
                        
                        
                        
                        if IsBuyGo == True:


                            BuyAmt = float(int(InvestMoneyCell /  NowOpenPrice)) #매수 가능 수량을 구한다!

                            NowFee = (BuyAmt*NowOpenPrice) * fee

                            #남은 돈이 있다면 매수 한다!!
                            if RemainInvestMoney >= (BuyAmt*NowOpenPrice) + NowFee:

                                TotalBuyAmt += BuyAmt
                                TotalPureMoney += (BuyAmt*NowOpenPrice)

                                RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금

                                RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
                                RemainInvestMoney -= NowFee

                                InvestMoney = RealInvestMoney + RemainInvestMoney #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                                BuyCnt += 1



                                AvgPrice = ((AvgPrice * (TotalBuyAmt-BuyAmt)) + (BuyAmt*NowOpenPrice)) / TotalBuyAmt
                                
                                print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, "회차 >>>>>>>매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매수!  \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n")

                            #남은 돈이 없다? 손절이 필요하다!
                            else:
                                InvestMoney = RemainInvestMoney + RealInvestMoney
                                print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, "회차 >>>>>> 누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," >>>>>>>>> 현금 소진상태..  \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n")
                                IsNoCash = True

                        else:
                            InvestMoney = RealInvestMoney + RemainInvestMoney 
                            
            # SQQQ, SOXL의 인버스의 경우
            else:

                IsSellGo = False
                
                Disparity = (PrevClosePrice/df['5ma'].iloc[i-1])*100.0

                if  (Disparity > 102 or Disparity < 98):

                    IsSellGo = True
                    
                if IsSellGo == True:

                    InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                    print("-----> !!!CUT!!!!", stock_code ," ", df.iloc[i].name, " " ,BuyCnt, " >>>>>>>>매도! 누적수량:",TotalBuyAmt,">>>>>>>> 매도! \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n\n")
                    print("\n\n")

                    BuyCnt = 0

                    TotalBuyAmt = 0
                    TotalPureMoney = 0

                    RealInvestMoney = 0
                    RemainInvestMoney = InvestMoney
                    AvgPrice = 0


                    if RevenueRate > 0:
                        SuccesCnt += 1
                    else:
                        FailCnt +=1
                    IsBuy = False #매도했다
                    
                    
            
                                     
        #첫 매수가 진행이 안되었다!
        if IsBuy == False and i > 1:

            if IsFirstDateSet == False:
                FirstDateStr = df.iloc[i].name
                FirstDateIndex = i-1
                IsFirstDateSet = True
                
            if stock_code == 'TQQQ' or stock_code == 'SOXL':
                ###################### 개선된 점 #######################
                #########################################################
                
                    
                if df['5ma'].iloc[i-1] < df['close'].iloc[i-1]: #전일 종가 5일선 위에 있을 때만 
                #########################################################
                #########################################################
                    

                    ###################### 개선된 점 #######################
                    #########################################################
                    if df['200ma'].iloc[i-1] > df['close'].iloc[i-1]: #200일선 아래에 있을 땐 40분할
                        DivNum = 35
                    else: # 개선된 점 GMA  # 200일선 위에 있을 땐 이평선에 따라 분할 차등!
                        
                        st_num = 55
                        
                        if stock_code == 'TQQQ':
                            st_num = 54
                            
                                
                        DivNum = st_num

                        
                        if df['100ma'].iloc[i-1] <= df['close'].iloc[i-1]:
                            DivNum -= 15


                        if df['60ma'].iloc[i-1] <= df['close'].iloc[i-1]:
                            DivNum -= 8


                        if df['20ma'].iloc[i-1] <= df['close'].iloc[i-1]:
                            DivNum -= 7    
                            
                            
                        if DivNum == st_num:
                            DivNum = 35    
                    #########################################################
                    #########################################################
                    
                    


                    #첫 매수를 진행한다!!!!
                    InvestMoneyCell = InvestMoney / DivNum


                    BuyAmt = float(int(InvestMoneyCell /  NowOpenPrice)) #매수 가능 수량을 구한다!

                    NowFee = (BuyAmt*NowOpenPrice) * fee

                    TotalBuyAmt += BuyAmt
                    TotalPureMoney += (BuyAmt*NowOpenPrice)

                    RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금


                    RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
                    RemainInvestMoney -= NowFee

                    InvestMoney = RealInvestMoney + RemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                    BuyCnt += 1
                    
                    AvgPrice = NowOpenPrice

                    print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, "회차 >>>> 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(NowOpenPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n")
                    IsBuy = True #매수했다

                
            else:
                


                IsBuyGo = False

                
                

                Disparity = (PrevClosePrice/df['5ma'].iloc[i-1])*100.0

                if df['20ma'].iloc[i-1] > df['close'].iloc[i-1]:

                    if (df['low'].iloc[i-2] < df['low'].iloc[i-1]) and df['open'].iloc[i-1] < df['close'].iloc[i-1] :

                        if stock_code == 'SOXS':
                            if df['volume'].iloc[i-2] < df['volume'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2] and Disparity < 102:
                                IsBuyGo = True
                        else:
                            if df['open'].iloc[i-2] > df['close'].iloc[i-2] and Disparity < 103:
                                IsBuyGo = True

                                

                if stock_code == 'SOXS':
                    if  min(df['open'].iloc[i-3],df['close'].iloc[i-3]) < min(df['open'].iloc[i-2],df['close'].iloc[i-2]) < min(df['open'].iloc[i-1],df['close'].iloc[i-1]) and df['open'].iloc[i-1] < df['close'].iloc[i-1] and Disparity < 102:
                        IsBuyGo = True



                                
                if IsBuyGo == True:
                    

                    #첫 매수를 진행한다!!!!
                    InvestMoneyCell = InvestMoney * (1.0 - fee)


                    BuyAmt = float(int(InvestMoneyCell /  NowOpenPrice)) #매수 가능 수량을 구한다!

                    NowFee = (BuyAmt*NowOpenPrice) * fee

                    TotalBuyAmt += BuyAmt
                    TotalPureMoney += (BuyAmt*NowOpenPrice)

                    RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금


                    RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
                    RemainInvestMoney -= NowFee

                    InvestMoney = RealInvestMoney + RemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                    BuyCnt += 1
                    
                    AvgPrice = NowOpenPrice

                    print(stock_code ," ", df.iloc[i].name, " " ,BuyCnt, "회차 >>>> 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(NowOpenPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2), " 이전종가:",round(PrevClosePrice,2),"\n")

                    IsBuy = True #매수했다

            
        TotalMoneyList.append(InvestMoney)

    #####################################################
    #####################################################
    #####################################################
    #'''
  


    #결과 정리 및 데이터 만들기!!
    if len(TotalMoneyList) > 0:

        TotalResultDict[stock_code] = TotalMoneyList

        resultData = dict()

        
        resultData['Ticker'] = stock_code


        result_df = pd.DataFrame({ "Total_Money" : TotalMoneyList}, index = df.index)

        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
        result_df['Cum_Ror'] = result_df['Ror'].cumprod()

        result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        pprint.pprint(result_df)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[FirstDateIndex] - 1.0) * 100.0 
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

        resultData['SuccesCnt'] = SuccesCnt
        resultData['FailCnt'] = FailCnt

        
        ResultList.append(resultData)



        for idx, row in result_df.iterrows():
            print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
            



#데이터를 보기좋게 프린트 해주는 로직!
print("\n\n--------------------")

TotalHoldRevenue = 0


InvestCnt = float(len(ResultList))

for result in ResultList:

    print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")
    print(result['Ticker'] )
    print("최초 금액: ", format(round(result['OriMoney'],2),',') , " 최종 금액: ", format(round(result['FinalMoney'],2),','))
    print("수익률:", round(result['RevenueRate'],2) , "%")
    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['SuccesCnt'] > 0:
        print("성공 횟수 :", result['SuccesCnt'] )

    if result['FailCnt'] > 0:
        print("손절 횟수 :", result['FailCnt'] )        


    TotalHoldRevenue += result['OriRevenueHold']


    print("\n--------------------\n")


if len(ResultList) > 0:
    print("####################################")
    

    # 딕셔너리의 리스트들의 길이를 가져옴
    length = len(list(TotalResultDict.values())[0])

    # 종합 리스트 초기화
    FinalTotalMoneyList = [0] * length

    # 딕셔너리에서 리스트를 가져와 합산
    for my_list in TotalResultDict.values():
        # 리스트의 각 요소를 합산
        for i, value in enumerate(my_list):
            FinalTotalMoneyList[i] += value


    result_df = pd.DataFrame({ "Total_Money" : FinalTotalMoneyList}, index = df.index)

    result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()

    result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

    result_df.index = pd.to_datetime(result_df.index)
    
    # GUI 차트 클래스 정의
    class ChartApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("US BothSide 3X 백테스팅 결과 분석")
            self.geometry("1400x900")
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.chart_artists = {}
            self.create_widgets()

        def create_widgets(self):
            main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            main_pane.pack(fill=tk.BOTH, expand=True)
            
            left_panel = ttk.Frame(main_pane)
            main_pane.add(left_panel, weight=1)
            
            # 통계 정보 표시
            stats_frame = ttk.LabelFrame(left_panel, text="전략 통계", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            stats_text = tk.Text(stats_frame, wrap=tk.WORD, height=20)
            stats_scroll = ttk.Scrollbar(stats_frame, orient="vertical", command=stats_text.yview)
            stats_text.configure(yscrollcommand=stats_scroll.set)
            stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            stats_text.pack(fill=tk.BOTH, expand=True)
            
            # 통계 정보 작성
            TotalOri = result_df['Total_Money'].iloc[1]
            TotalFinal = result_df['Total_Money'].iloc[-1]
            TotalMDD = result_df['MaxDrawdown'].min() * 100.0
            
            stats_info = f"""========== 종합 결과 ==========

최초 금액: {format(int(round(TotalOri,0)), ',')}
최종 금액: {format(int(round(TotalFinal,0)), ',')}
수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100,2)}%
단순 보유 수익률: {round(TotalHoldRevenue/InvestCnt,2)}%
평균 MDD: {round(TotalMDD,2)}%

========== 종목별 결과 ==========

"""
            for result in ResultList:
                stats_info += f"""{result['Ticker']}
기간: {result['DateStr'].replace("00:00:00","")}
최초: {format(round(result['OriMoney'],2),',')}  →  최종: {format(round(result['FinalMoney'],2),',')}
수익률: {round(result['RevenueRate'],2)}%
단순 보유 수익률: {round(result['OriRevenueHold'],2)}%
MDD: {round(result['MDD'],2)}%
"""
                if result['SuccesCnt'] > 0:
                    stats_info += f"성공 횟수: {result['SuccesCnt']}\n"
                if result['FailCnt'] > 0:
                    stats_info += f"손절 횟수: {result['FailCnt']}\n"
                stats_info += "\n" + "="*30 + "\n\n"
            
            stats_text.insert('1.0', stats_info)
            stats_text.config(state=tk.DISABLED)
            
            chart_frame = ttk.Frame(main_pane)
            main_pane.add(chart_frame, weight=3)
            
            self.tab_control = ttk.Notebook(chart_frame)
            self.tab_control.pack(expand=1, fill="both")
            
            self.add_overall_tab()
            
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
            axs = fig.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
            fig.tight_layout(pad=3.0)
            
            axs[0].plot(result_df.index, result_df['Total_Money'], label='Strategy', color='blue')
            axs[0].set_title('Overall Performance (Linear Scale)', fontsize=12)
            axs[0].set_ylabel('Total Money (USD)')
            axs[0].grid(True, which='both', linestyle='--', linewidth=0.5)
            axs[0].legend()
            axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD', color='red', linewidth=2)
            axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown', color='orange', alpha=0.5)
            axs[1].set_title('Drawdown Comparison', fontsize=12)
            axs[1].set_ylabel('Drawdown (%)')
            axs[1].grid(True)
            axs[1].legend()
            axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
            
            self.chart_artists['overall'] = {'fig': fig, 'canvas': canvas, 'ax': axs[0]}
            canvas.draw()

    # 서버 환경 체크 및 GUI 실행
    pcServerGb = socket.gethostname()
    if pcServerGb != "AutoBotCong":
        app = ChartApp()
        app.mainloop()
        print("\n차트 창이 닫혔습니다. 최종 통계 결과를 출력합니다.")
    else:
        print("\n서버 환경이므로 GUI를 생략하고 최종 통계 결과를 바로 출력합니다.")

    TotalOri = result_df['Total_Money'].iloc[1]
    TotalFinal = result_df['Total_Money'].iloc[-1]

    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 #MDD를 종합적으로 계산!


    print("---------- 총 결과 ----------")
    print("최초 금액:", format(int(round(TotalOri,0)), ',') , " 최종 금액:",  format(int(round(TotalFinal,0)), ',') , "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) 평균 MDD:",  round(TotalMDD,2),"%")
    
    # 월별 수익률 및 잔액 계산
    print("\n---------- 월별 수익률 및 잔액 ----------")
    monthly_ror = result_df['Ror'].resample('M').apply(lambda x: (x.prod() - 1) * 100)
    monthly_balance = result_df['Total_Money'].resample('M').last()
    for (month_ror, ror), (month_bal, balance) in zip(monthly_ror.items(), monthly_balance.items()):
        if not pd.isna(ror):
            print(f"{month_ror.strftime('%Y-%m')}: 수익률 {ror:>7.2f}%  |  잔액: {format(int(round(balance, 0)), ','):>15}")
    
    # 년도별 수익률 및 잔액 계산
    print("\n---------- 년도별 수익률 및 잔액 ----------")
    yearly_ror = result_df['Ror'].resample('Y').apply(lambda x: (x.prod() - 1) * 100)
    yearly_balance = result_df['Total_Money'].resample('Y').last()
    for (year_ror, ror), (year_bal, balance) in zip(yearly_ror.items(), yearly_balance.items()):
        if not pd.isna(ror):
            print(f"{year_ror.strftime('%Y')}: 수익률 {ror:>7.2f}%  |  잔액: {format(int(round(balance, 0)), ','):>15}")
    
    print("------------------------------")
    print("####################################")
