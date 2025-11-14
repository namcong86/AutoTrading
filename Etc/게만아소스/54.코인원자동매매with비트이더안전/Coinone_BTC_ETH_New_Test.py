#-*-coding:utf-8 -*-
'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다.  

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504

관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅 
https://blog.naver.com/zacra/223508324003

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^




##############################################################
코인원 앱 -> 하단 더보기 -> 이벤트 코드 -> 등록하기 -> ZABOBSTUDIO 
##############################################################


'''

import myCoinone

import pandas as pd
import pprint
import matplotlib.pyplot as plt




InvestTotalMoney = 1000000 #그냥 1백만원으로 박아서 테스팅 해보기!!!


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "BTC"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "ETH"
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



TotalResultDict= dict()


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



    #일봉 정보를 가지고 온다! 800
    #사실 분봉으로 테스트 해보셔도 됩니다. 저는 일봉으로~^^
    df = myCoinone.GetOhlcv(coin_ticker,'1d',1718) 
   

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
    df['rsi_ma'] = df['rsi'].rolling(10).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close']-df['prev_close'])/df['prev_close']
    

    ############# 이동평균선! ###############
    #for ma in range(3,81):
    #    df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
        
    ma_dfs = []

    # 이동 평균 계산
    for ma in range(3, 81):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)

    # 이동 평균 데이터 프레임을 하나로 결합
    ma_df_combined = pd.concat(ma_dfs, axis=1)

    # 원본 데이터 프레임과 결합
    df = pd.concat([df, ma_df_combined], axis=1)


    ########################################
    
    
    
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)


    df = df[:len(df)-1]

    pprint.pprint(df)
    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)


    IsBuy = False #매수 했는지 여부

    TryCnt = 0      #매매횟수
    SuccessCnt = 0   #익절 숫자
    FailCnt = 0     #손절 숫자

    fee = 0.002 #수수료+세금+슬리피지를 매수매도마다 0.2%로 세팅!

    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0

   

    TotalMoneyList = list()

    AvgPrice = 0

    

    #######이평선 설정 ########
    ma1 = 6  
    ma2 = 10 
    ma3 = 19


    BUY_PRICE = 0
    IsDolpaDay = False
    
    for i in range(len(df)):

        if FirstDateStr == "":
            FirstDateStr = df.iloc[i].name



        IsSellToday = False

        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]

        
    
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!


            IsSellGo = False

            SellPrice = NowOpenPrice
            
            #이더리움의 경우
            if coin_ticker == 'ETH':

                #RSI지표가 70이상인 과매수 구간에서 단기 이평선을 아래로 뚫으면 돌파매도 처리!!
                CutPrice = df[str(ma1)+'ma'].iloc[i-1]
                
                if  df['rsi'].iloc[i-1] >= 70 and df['low'].iloc[i] <= CutPrice and NowOpenPrice > CutPrice :
                    SellPrice = CutPrice
                    IsSellGo = True
                    IsDolpaCut = True

           

            #단 그 전날 돌파로 매매한 날이라면 매수한 가격대비 수익률을 더해야 하니깐.
            if IsDolpaDay == True:
                RealInvestMoney = RealInvestMoney * (1.0 + ((SellPrice - BUY_PRICE) / BUY_PRICE))
                IsDolpaDay = False
            else:
                RealInvestMoney = RealInvestMoney * (1.0 + ((SellPrice - PrevOpenPrice) / PrevOpenPrice))


            InvestMoney = RealInvestMoney + RemainInvestMoney 

            Rate = 0
            RevenueRate = 0
            
            if AvgPrice > 0:
            
                #진입(매수)가격 대비 변동률
                Rate = (SellPrice - AvgPrice) / AvgPrice

                RevenueRate = (Rate - fee)*100.0 #수익률 계산


            #이더리움의 경우
            if coin_ticker == 'ETH':

                #50일선 위에 있는 상승장
                if  PrevClosePrice > df['50ma'].iloc[i-1]:
                
                    #5일선, 10일선 둘다 밑으로 내려가면 매도!!
                    if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1]:
                        IsSellGo = True

                #50일선 아래있는 하락장
                else:
                  
                    # 5일선 밑으로 내려가거나 전일 캔들 기준 고가도 하락하고 저가도 하락했다면 매도!
                    if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] or (df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) :
                        IsSellGo = True

            #비트코인의 경우
            else:
                #전일 캔들 기준 고가도 하락하고 저가도 하락했거나 2연속 음봉이거나 수익률이 0보다 작아지면 매도!!
                if ((df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1]) or (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2])  ) or RevenueRate < 0 :
                    IsSellGo = True

            
                if df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1]:
                    IsSellGo = False




            if IsSellGo == True :

                SellAmt = TotalBuyAmt

                InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                TotalBuyAmt = 0
                TotalPureMoney = 0

                RealInvestMoney = 0
                RemainInvestMoney = InvestMoney
                AvgPrice = 0


                print(coin_ticker ," ", df.iloc[i].name, " >>>>>>>모두 매도!!:", SellAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매도!  \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 매도가:", round(SellPrice,2),"\n\n")



                TryCnt += 1

                if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    SuccessCnt += 1
                else:
                    FailCnt += 1



                InvestMoney = RealInvestMoney + RemainInvestMoney 

                IsBuy = False 
                IsSellToday = True


       
        if IsBuy == False and i > 2 and IsSellToday == False: 

            
            if IsFirstDateSet == False:
                FirstDateIndex = i-1
                IsFirstDateSet = True


            IsBuyGo = False
            
            InvestGoMoney = 0



            #이평선 조건을 만족하는지
            IsMaDone = False
            

            if coin_ticker == 'ETH':

                #3개의 이평선 중 가장 높은 값을 구한다!
                DolPaSt = max(df[str(ma1)+'ma'].iloc[i-1],df[str(ma2)+'ma'].iloc[i-1],df[str(ma3)+'ma'].iloc[i-1])

                
                #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때
                #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
                if DolPaSt == df[str(ma3)+'ma'].iloc[i-1] and df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt:

                    #단 RSI지표가 증가! RSI 10일 평균지표도 증가할 때 돌파매수!
                    if  df['rsi'].iloc[i-2] < df['rsi'].iloc[i-1] and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] :

                        #그렇다면 그 돌파 가격에 매수를 했다고 가정한다.
                        BUY_PRICE = DolPaSt
                        IsDolpaDay = True
                        IsMaDone = True
            

                #그 밖의 경우
                else:
                    ##3개의 이동평균선 위에 있고 RSI지표가 증가! RSI 10일 평균지표도 증가한다면 매수!
                    if  PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] and df['rsi'].iloc[i-2] < df['rsi'].iloc[i-1] and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1]:
                        BUY_PRICE = NowOpenPrice
                        IsDolpaDay = False
                        IsMaDone = True



                if IsMaDone == False:


                    DolpaRate = 0.7

                    if df[str(ma3)+'ma'].iloc[i-2] < PrevClosePrice:
                        DolpaRate = 0.6

                    if df[str(ma1)+'ma'].iloc[i-2] < df[str(ma1)+'ma'].iloc[i-1] and df[str(ma2)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-1] and df[str(ma3)+'ma'].iloc[i-2] < df[str(ma3)+'ma'].iloc[i-1] and df[str(ma3)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-1] < df[str(ma1)+'ma'].iloc[i-1]:
                        DolpaRate = 0.5


                    DolPaSt = NowOpenPrice + (( df['high'].iloc[i-1] - df['low'].iloc[i-1]) * DolpaRate)

                    if df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df[str(ma1)+'ma'].iloc[i-2] < df[str(ma1)+'ma'].iloc[i-1]:
                        BUY_PRICE = DolPaSt
                        IsDolpaDay = True
                        IsMaDone = True




            #비트코인일 때
            else:

                
                #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때
                #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
                DolPaSt = max(df[str(ma1)+'ma'].iloc[i-1],df[str(ma2)+'ma'].iloc[i-1],df[str(ma3)+'ma'].iloc[i-1])

                if DolPaSt == df[str(ma3)+'ma'].iloc[i-1] and df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt:

                    #비트코인은 추가 조건 체크 없이 그냥 돌파했으면 매수!
                    BUY_PRICE = DolPaSt
                    IsDolpaDay = True
                    IsMaDone = True
                else:
                

                    #2연속 양봉이면서 고가도 증가되는데 5일선이 증가되고 있으면서 10일선,60일선 위에 있을 때 비트 매수!
                    if df['open'].iloc[i-1] < df['close'].iloc[i-1] and df['open'].iloc[i-2] < df['close'].iloc[i-2] and df['close'].iloc[i-2] < df['close'].iloc[i-1]   and df['high'].iloc[i-2] < df['high'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1] and df['20ma'].iloc[i-1] < df['close'].iloc[i-1] and df['70ma'].iloc[i-1] < df['close'].iloc[i-1] :
                        
                        BUY_PRICE = NowOpenPrice
                        IsDolpaDay = False
                        IsMaDone = True


                if IsMaDone == False:


                    DolpaRate = 0.7

                    DolPaSt = NowOpenPrice + (((max(df['high'].iloc[i-1],df['high'].iloc[i-2])- min(df['low'].iloc[i-1],df['low'].iloc[i-2])) * DolpaRate))

                    if df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt and df[str(ma2)+'ma'].iloc[i-2] < PrevClosePrice and df['low'].iloc[i-2] < df['low'].iloc[i-1] and df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df[str(ma3)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-1] < df[str(ma1)+'ma'].iloc[i-1] :
                        BUY_PRICE = DolPaSt
                        IsDolpaDay = True
                        IsMaDone = True








            if IsMaDone == True  :
 
                Rate = 1.0

                ########################################################################################################
                #''' #이 부분을 주석처리 하면 감산 로직이 제거 됩니다 
                #50일선이 감소중이거나 50일선 밑에 있다면 투자비중 절반으로 줄여줌!
                if df['50ma'].iloc[i-2] > df['50ma'].iloc[i-1] or df['50ma'].iloc[i-1] > df['close'].iloc[i-1]:
                    Rate *= 0.5

                #'''
                ########################################################################################################


                InvestGoMoney = RemainInvestMoney*Rate * (1.0 - fee) #수수료를 제외한 금액을 투자한다!
                IsBuyGo = True




            if IsBuyGo == True :

                #투자금 거래대금 10일 평균의 1/2000수준으로 제한!
                #'''
                if InvestGoMoney > df['value_ma'].iloc[i-1] / 2000:
                    InvestGoMoney = df['value_ma'].iloc[i-1]/ 2000

                if InvestGoMoney < 10000:
                    InvestGoMoney = 10000
                #'''

                BuyAmt = float(InvestGoMoney /  BUY_PRICE) #매수 가능 수량을 구한다!

                NowFee = (BuyAmt*BUY_PRICE) * fee

                TotalBuyAmt += BuyAmt
                TotalPureMoney += (BuyAmt*BUY_PRICE)

                RealInvestMoney += (BuyAmt*BUY_PRICE) #실제 들어간 투자금


                RemainInvestMoney -= (BuyAmt*BUY_PRICE) #남은 투자금!
                RemainInvestMoney -= NowFee

                InvestMoney = RealInvestMoney + RemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                
                AvgPrice = BUY_PRICE

                if IsDolpaDay == True:

                    print(coin_ticker ," ", df.iloc[i].name,  "회차 >>>> !!!돌파!!! 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 매수가격:", round(BUY_PRICE,2),"\n")
                
                else:

                    print(coin_ticker ," ", df.iloc[i].name,  "회차 >>>> 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 매수가격:", round(BUY_PRICE,2),"\n")
                
                IsBuy = True #매수했다
                print("\n")


        InvestMoney = RealInvestMoney + RemainInvestMoney 
        TotalMoneyList.append(InvestMoney)
        

    #####################################################
    #####################################################
    #####################################################
    #'''
  


    #결과 정리 및 데이터 만들기!!
    if len(TotalMoneyList) > 0:
        TotalResultDict[coin_ticker] = TotalMoneyList
        resultData = dict()

        
        resultData['Ticker'] = coin_ticker


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


    #'''
    # Create a figure with subplots for the two charts
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))

    # Plot the return chart
    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy')
    axs[0].set_ylabel('Cumulative Return (%)')
    axs[0].set_title('Return Comparison Chart')
    axs[0].legend()

    # Plot the MDD and DD chart on the same graph
    axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
    axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
    axs[1].set_ylabel('Drawdown (%)')
    axs[1].set_title('Drawdown Comparison Chart')
    axs[1].legend()

    # Show the plot
    plt.tight_layout()
    plt.show()
        
    #'''
    
    
    
    TotalOri = result_df['Total_Money'].iloc[1]
    TotalFinal = result_df['Total_Money'].iloc[-1]

    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 #MDD를 종합적으로 계산!


    print("---------- 총 결과 ----------")
    print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) 평균 MDD:",  round(TotalMDD,2),"%")
    print("------------------------------")
    print("####################################")









