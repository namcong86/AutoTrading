#-*-coding:utf-8 -*-
'''


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$




관련 포스팅
    

이평 조합 전략 수익률과 MDD 개선하기!
https://blog.naver.com/zacra/223083723474


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



InvestTotalMoney = 5000000 #그냥 5백만원으로 박아서 테스팅 해보기!!!


######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["KRW-BTC","KRW-ETH",'KRW-ADA','KRW-DOT','KRW-POL']
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)




#'''
##########################################################################################################


ResultList = list()

######################################## 1. 균등 분할 투자 ###########################################################
'''
for coin_ticker in InvestCoinList:    
    InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!
'''
##########################################################################################################

######################################## 2. 차등 분할 투자 ###################################################
    #'''
for coin_data in InvestCoinList:

    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
    #'''
##########################################################################################################



    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)


    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney

    TotalBuyAmt = 0 #매수 수량
    TotalPureMoney = 0 #매수 금액



    #일봉 정보를 가지고 온다!
    #사실 분봉으로 테스트 해보셔도 됩니다. 저는 일봉으로~^^
    df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=6000, period=0.3) #day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
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
    #for ma in range(3,31):
    #    df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
        
    ma_dfs = []

    # 이동 평균 계산
    for ma in range(3, 31):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)

    # 이동 평균 데이터 프레임을 하나로 결합
    ma_df_combined = pd.concat(ma_dfs, axis=1)

    # 원본 데이터 프레임과 결합
    df = pd.concat([df, ma_df_combined], axis=1)
    ########################################



    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)


    IsBuy = False #매수 했는지 여부

    TryCnt = 0      #매매횟수
    SuccessCnt = 0   #익절 숫자
    FailCnt = 0     #손절 숫자

    fee = 0.0035 #수수료+세금+슬리피지를 매수매도마다 0.35%로 세팅!

    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0

   

    TotlMoneyList = list()

    AvgPrice = 0

    
   #df = df[:len(df)-3000]

    #######이평선 설정 ########
    ma1 = 5  
    ma2 = 10 
    ma3 = 21 

    for i in range(len(df)):

        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]

        
    
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            RealInvestMoney = RealInvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))


            InvestMoney = RealInvestMoney + RemainInvestMoney 

            Rate = 0
            RevenueRate = 0
            
            if AvgPrice > 0:
            
                #진입(매수)가격 대비 변동률
                Rate = (NowOpenPrice - AvgPrice) / AvgPrice

                RevenueRate = (Rate - fee)*100.0 #수익률 계산



            IsSellGo = False




            #30일선 위에 있는 상승장
            if  PrevClosePrice > df['30ma'].iloc[i-1]:
                #RSI지표가 55보다 아래여야 판다!
                if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] and df['rsi'].iloc[i-1] < 55:
                    IsSellGo = True

            #30일선 아래있는 하락장
            else:
                #RSI지표가 55보다 아래여야 판다!
                if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and df['rsi'].iloc[i-1] < 55:
                    IsSellGo = True
            



            if IsSellGo == True :

                SellAmt = TotalBuyAmt

                InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                TotalBuyAmt = 0
                TotalPureMoney = 0

                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                AvgPrice = 0


                print(coin_ticker ," ", df.iloc[i].name, " >>>>>>>모두 매도!!:", SellAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매도!  \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n\n")



                TryCnt += 1

                if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    SuccessCnt += 1
                else:
                    FailCnt += 1



                InvestMoney = RealInvestMoney + RemainInvestMoney 

                IsBuy = False 


                            

       
        if IsBuy == False and i > 20: #이평조합 전략과 비교를 위해 20일 이후에 시작!(20분할이라고 가정!)

            if IsFirstDateSet == False:
                FirstDateStr = df.iloc[i].name
                FirstDateIndex = i-1
                IsFirstDateSet = True

            IsBuyGo = False
            
            InvestGoMoney = 0

         
            #3개 이평선보다 전일 종가가 위에 있을 때, 전일 RSI지표가 70보다 작을때, 전일 RSI지표가 증가 되었을 때만
            if  PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1]  and df['rsi'].iloc[i-1] < 70 and df['rsi'].iloc[i-2] < df['rsi'].iloc[i-1]:

                Rate = 1.0

                #투자 비중 조절!!
                #if df['30ma'].iloc[i-1] < df['30ma'].iloc[i-2]:
                #    Rate -= 0.2


                InvestGoMoney = RemainInvestMoney*Rate * (1.0 - fee) #수수료를 제외한 금액을 투자한다!
                IsBuyGo = True




            if IsBuyGo == True :


                BuyAmt = float(InvestGoMoney /  NowOpenPrice) #매수 가능 수량을 구한다!

                NowFee = (BuyAmt*NowOpenPrice) * fee

                TotalBuyAmt += BuyAmt
                TotalPureMoney += (BuyAmt*NowOpenPrice)

                RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금


                RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
                RemainInvestMoney -= NowFee

                InvestMoney = RealInvestMoney + RemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                
                AvgPrice = NowOpenPrice

                print(coin_ticker ," ", df.iloc[i].name,  "회차 >>>> 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(NowOpenPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")
                IsBuy = True #매수했다
                print("\n")


        InvestMoney = RealInvestMoney + RemainInvestMoney 
        TotlMoneyList.append(InvestMoney)

    #####################################################
    #####################################################
    #####################################################
    #'''
  


    #결과 정리 및 데이터 만들기!!
    if len(TotlMoneyList) > 0:

        resultData = dict()

        
        resultData['Ticker'] = coin_ticker


        result_df = pd.DataFrame({ "Total_Money" : TotlMoneyList}, index = df.index)

        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
        result_df['Cum_Ror'] = result_df['Ror'].cumprod()

        result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        pprint.pprint(result_df)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        result_df.index = pd.to_datetime(result_df.index)
        # Create a figure with subplots for the two charts
        fig, axs = plt.subplots(2, 1, figsize=(10, 10))

        # Plot the return chart
        axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy')
        axs[0].set_ylabel('Cumulative Return (%)')
        axs[0].set_title(coin_ticker + ' Return Comparison Chart')
        axs[0].legend()

        # Plot the MDD and DD chart on the same graph
        axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
        axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
        axs[1].set_ylabel('Drawdown (%)')
        axs[1].set_title(coin_ticker + ' Drawdown Comparison Chart')
        axs[1].legend()

        # Show the plot
        plt.tight_layout()
        plt.show()
        
    
        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[FirstDateIndex] - 1.0) * 100.0 
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0


        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
        resultData['FailCnt'] = FailCnt

        ResultList.append(resultData)



        for idx, row in result_df.iterrows():
            print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
            





#데이터를 보기좋게 프린트 해주는 로직!
print("\n\n--------------------")
TotalOri = 0
TotalFinal = 0
TotalHoldRevenue = 0
TotalMDD= 0

InvestCnt = float(len(ResultList))

for result in ResultList:

    print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")
    print(result['Ticker'] )
    print("최초 금액: ", str(format(round(result['OriMoney']), ',')) , " 최종 금액: ", str(format(round(result['FinalMoney']), ','))  )
    print("수익률:", format(round(result['RevenueRate'],2),',') , "%")
    print("단순 보유 수익률:", format(round(result['OriRevenueHold'],2),',') , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['TryCnt'] > 0:
        print("성공:", result['SuccessCnt'] , " 실패:", result['FailCnt']," -> 승률: ", round(result['SuccessCnt']/result['TryCnt'] * 100.0,2) ," %")


    TotalOri += result['OriMoney']
    TotalFinal += result['FinalMoney']

    TotalHoldRevenue += result['OriRevenueHold']
    TotalMDD += result['MDD']

    print("\n--------------------\n")

if TotalOri > 0:
    print("####################################")
    print("---------- 총 결과 ----------")
    print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", format(round(((TotalFinal - TotalOri) / TotalOri) * 100,2),',') ,"% (단순보유수익률:" ,format(round(TotalHoldRevenue/InvestCnt,2),',') ,"%) 평균 MDD:",  round(TotalMDD/InvestCnt,2),"%")
    print("------------------------------")
    print("####################################")










