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


업비트 자동매매 연복리 60%이상의 괴물 전략! - 구간 분할 장기 투자 전략!
https://blog.naver.com/zacra/223052327452

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
InvestCoinList = ["KRW-BTC","KRW-ETH",'KRW-ADA','KRW-DOT','KRW-POL']
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.4
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.3
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ADA"
InvestDataDict['rate'] = 0.1
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-DOT"
InvestDataDict['rate'] = 0.1
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-POL"
InvestDataDict['rate'] = 0.1
InvestCoinList.append(InvestDataDict)
'''
##########################################################################################################


ResultList = list()

######################################## 1. 균등 분할 투자 ###########################################################
#'''
for coin_ticker in InvestCoinList:    
    InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!
#'''
##########################################################################################################

######################################## 2. 차등 분할 투자 ###################################################
    '''
for coin_data in InvestCoinList:

    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
    '''
##########################################################################################################



    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    ####################
    #구간과 원금을 10분할
    DivNum = 10 
    ####################
    ###############################
    #고점 저점을 구할 기준이 되는 기간
    target_period = 60
    ###############################


    InvestMoneyCell = InvestMoney / DivNum
    RealInvestMoney = 0
    RemainInvestMoney = InvestMoney

    TotalBuyAmt = 0 #매수 수량
    TotalPureMoney = 0 #매수 금액



    #일봉 정보를 가지고 온다!
    #사실 분봉으로 테스트 해보셔도 됩니다. 저는 일봉으로~^^
    df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=5000, period=0.3) #day/minute1/minute3/minute5/minute10/minute15/minute30/minute60/minute240/week/month
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
    df['60ma'] = df['close'].rolling(60).mean()
    df['100ma'] = df['close'].rolling(100).mean()
    ########################################



    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)


    IsBuy = False #매수 했는지 여부
    BuyCnt = 0   #익절 숫자
    SellCnt = 0     #손절 숫자

    fee = 0.0035 #수수료+세금+슬리피지를 매수매도마다 0.35%로 세팅!

    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0

   

    TotlMoneyList = list()

    AvgPrice = 0

    
    result_step = 1

   #df = df[:len(df)-3000]

   

    for i in range(len(df)):


        #종가 기준으로 테스트 하려면 open 을 close로 변경!!
        #NowOpenPrice = df['close'].iloc[i]  
        #PrevOpenPrice = df['close'].iloc[i-1]  
        
        
        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        

        
    
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            RealInvestMoney = RealInvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))


            InvestMoney = RealInvestMoney + RemainInvestMoney 
            InvestMoneyCell = InvestMoney / DivNum

            Rate = 0
            RevenueRate = 0
            
            if AvgPrice > 0:
            
                #진입(매수)가격 대비 변동률
                Rate = (NowOpenPrice - AvgPrice) / AvgPrice

                RevenueRate = (Rate - fee)*100.0 #수익률 계산


            #해당 기간동안의 고가와 저가를 리스트에 넣는다.
            high_list = list()
            low_list = list()
            
            for index in range(i-1,i-(target_period+1),-1):
                high_list.append(df['high'].iloc[index])
                low_list.append(df['low'].iloc[index])

            #최고가 최저가를 구한다!
            high_price = float(max(high_list))
            low_price =  float(min(low_list))
            
            #최고가와 최저가의 차이를 DivNum으로 나눈다!
            Gap = (high_price - low_price) / DivNum

            #현재 구간을 구할 수 있다.
            now_step = DivNum

            for step in range(1,DivNum+1):

                if NowOpenPrice < low_price + (Gap * step):
                    now_step = step
                    break
            print("-----------------",now_step,"-------------------\n")
            
        
 

            #스텝(구간)이 다르다!
            if result_step != now_step:

                step_gap = now_step - result_step

                result_step = now_step

                if step_gap >= 1: #스텝이 증가!! 매수!!
                    #20일선 위에 있을 때만!
                    if df['20ma'].iloc[i-1] < df['close'].iloc[i-1]:

                        BuyAmt = float(InvestMoneyCell*abs(step_gap)  /  NowOpenPrice) #매수 가능 수량을 구한다!
                        

                        NowFee = (BuyAmt*NowOpenPrice) * fee


                        #남은 돈이 있다면 매수 한다!!
                        if RemainInvestMoney >= (BuyAmt*NowOpenPrice) + NowFee :

                            TotalBuyAmt += BuyAmt
                            TotalPureMoney += (BuyAmt*NowOpenPrice)

                            RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금

                            RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
                            RemainInvestMoney -= NowFee

                            InvestMoney = RealInvestMoney + RemainInvestMoney #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

                            
                                    
                            AvgPrice = ((AvgPrice * (TotalBuyAmt-BuyAmt)) + (BuyAmt*NowOpenPrice)) / TotalBuyAmt

                            InvestMoneyCell = InvestMoney / DivNum
                            print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, ">>>>>>>매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매수!  \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")

                            BuyCnt += 1
                        else:

                            print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "!!!!!!!!!!해당 수량 매수 금액 부족!!!!!!!!!!!누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")

 
                            InvestMoney = RealInvestMoney + RemainInvestMoney 
                    else:
                        print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "!!!!!!!!!!구간이 증가되 매수해야 하지만 이평선 조건 안맞음!!!!!!!!!!! 누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")

                        InvestMoney = RealInvestMoney + RemainInvestMoney 


                elif step_gap <= -1: #스텝이 감소! 매도!!

                    #5일선 밑에 있을 때만
                    if df['5ma'].iloc[i-1] > df['close'].iloc[i-1] and TotalBuyAmt > 0:

                        SellAmt = float(InvestMoneyCell*abs(step_gap)  /  NowOpenPrice) #매수 가능 수량을 구한다!


                        NowFee = (SellAmt*NowOpenPrice) * fee

                        #남은 수량이 있다면 매도 한다!!
                        if TotalBuyAmt >= abs(SellAmt):

                            #해당 수량을 감소 시키고! 금액도 감소시킨다!
                            TotalBuyAmt -= SellAmt
                            TotalPureMoney -= (SellAmt*NowOpenPrice)
                            
                            RealInvestMoney -= (SellAmt*NowOpenPrice) #실제 들어간 투자금
                            
                            RemainInvestMoney += (SellAmt*NowOpenPrice) #남은 투자금!
                            RemainInvestMoney -= NowFee

                            InvestMoney = RemainInvestMoney + RealInvestMoney
                            

                            InvestMoneyCell = InvestMoney / DivNum
                            print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, " >>>>>>>매도수량:", SellAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매도!  \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n\n")

                            SellCnt += 1
                            
                        else:


                            InvestMoney = RemainInvestMoney + (RealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                            TotalBuyAmt = 0
                            TotalPureMoney = 0

                            RealInvestMoney = 0
                            RemainInvestMoney = InvestMoney
                            AvgPrice = 0


                            InvestMoneyCell = InvestMoney / DivNum
                            print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, " >>>>>>>모두 매도!!:", SellAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2),">>>>>>>> 매도!  \n투자금 수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n\n")

                            SellCnt += 1

                            InvestMoney = RealInvestMoney + RemainInvestMoney 
                    else:
                        print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "!!!!!!!!!!구간이 감수되 매도해야 하지만 이평선 조건 안맞음!!!!!!!!!!! 누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")

                        InvestMoney = RealInvestMoney + RemainInvestMoney 


                else:
                    InvestMoney = RealInvestMoney + RemainInvestMoney 
                    print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "!!!!!!!!!! 누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")



            else:
                InvestMoney = RealInvestMoney + RemainInvestMoney 
                print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "!!!!!!!!!!구간 변동 없음!!!!!!!!!! 누적수량:",TotalBuyAmt," 평단: ",round(AvgPrice,2)," \n투자금 수익률: ", round(RevenueRate,2) , "% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")

            print("\n")

                            

       
        if IsBuy == False and i > target_period:

            if IsFirstDateSet == False:
                FirstDateStr = df.iloc[i].name
                FirstDateIndex = i-1
                IsFirstDateSet = True





            #첫 매수를 진행한다!!!!
            InvestMoneyCell = InvestMoney / DivNum


            
            #기간 동안 고가과 저가를 넣어둔다
            high_list = list()
            low_list = list()
            for index in range(i-1,i-(target_period+1),-1):
                #print(coin_ticker ," ", df.iloc[index].name)
                high_list.append(df['high'].iloc[index])
                low_list.append(df['low'].iloc[index])

            #최고가와 최저가를 구한다
            high_price = float(max(high_list))
            low_price =  float(min(low_list))

            #최고가와 최저가의 차이를 DivNum으로 나눈다
            Gap = (high_price - low_price) / DivNum

            
            #현재 구간을 계산한다!
            for step in range(1,DivNum+1):
                if NowOpenPrice < low_price + (Gap * step):
                    result_step = step
                    break

            print("-----------------",result_step,"-------------------\n")

            BuyAmt = float(InvestMoneyCell /  NowOpenPrice) #매수 가능 수량을 구한다!

            NowFee = (BuyAmt*NowOpenPrice) * fee

            TotalBuyAmt += BuyAmt
            TotalPureMoney += (BuyAmt*NowOpenPrice)

            RealInvestMoney += (BuyAmt*NowOpenPrice) #실제 들어간 투자금


            RemainInvestMoney -= (BuyAmt*NowOpenPrice) #남은 투자금!
            RemainInvestMoney -= NowFee

            InvestMoney = RealInvestMoney + RemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!

            BuyCnt += 1
            
            AvgPrice = NowOpenPrice

            print(coin_ticker ," ", df.iloc[i].name, " 구간" ,result_step, "회차 >>>> 매수수량:", BuyAmt ,"누적수량:",TotalBuyAmt," 평단: ",round(NowOpenPrice,2)," >>>>>>> 매수시작! \n투자금 수익률: 0% ,종목 잔고:",round(RemainInvestMoney,2), "+",round(RealInvestMoney,2), "=",round(InvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")
            IsBuy = True #매수했다
            print("\n")

            
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

        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[FirstDateIndex] - 1.0) * 100.0 
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

        resultData['BuyCnt'] = BuyCnt
        resultData['SellCnt'] = SellCnt

        ResultList.append(resultData)
        
        
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
    print("수익률:", round(result['RevenueRate'],2) , "%")
    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['BuyCnt'] > 0:
        print("매수 횟수 :", result['BuyCnt'] )

    if result['SellCnt'] > 0:
        print("매도 횟수 :", result['SellCnt'] )        


    TotalOri += result['OriMoney']
    TotalFinal += result['FinalMoney']

    TotalHoldRevenue += result['OriRevenueHold']
    TotalMDD += result['MDD']

    print("\n--------------------\n")

if TotalOri > 0:
    print("####################################")
    print("---------- 총 결과 ----------")
    print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) 평균 MDD:",  round(TotalMDD/InvestCnt,2),"%")
    print("------------------------------")
    print("####################################")










