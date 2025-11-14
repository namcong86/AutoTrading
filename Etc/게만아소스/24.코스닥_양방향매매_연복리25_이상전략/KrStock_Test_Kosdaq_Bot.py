'''


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아낄 수 있어요!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅

연복리 25%의 코스닥 지수 양방향 매매 전략!
https://blog.naver.com/zacra/223078498415
위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^





'''

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR

import pandas as pd
import pprint
import matplotlib.pyplot as plt

#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL



#이렇게 직접 금액을 지정해도 된다!!
TotalMoney = 10000000

print("테스트하는 총 금액: ", format(round(TotalMoney), ','))


InvestStockList = ['233740','251340'] #KODEX 코스닥150레버리지,  KODEX 코스닥150선물인버스

InverseStockCode = '251340' # KODEX 코스닥150선물인버스


InvestStockList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "233740" # KODEX 코스닥150레버리지
InvestDataDict['rate'] = 0.7
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "251340" # KODEX 코스닥150선물인버스
InvestDataDict['rate'] = 0.3
InvestStockList.append(InvestDataDict)




ResultList = list()

TotalResultDict= dict()

for stock_data in InvestStockList:

    stock_code = stock_data['ticker']

    print("\n----stock_code: ", stock_code)

    stock_name = KisKR.GetStockName(stock_code)

    InvestMoney = TotalMoney * stock_data['rate']

    print(stock_name, " 종목당 할당 투자금:", InvestMoney)


    #일봉 정보를 가지고 온다!
    df = Common.GetOhlcv("KR",stock_code, 1645) #310이 얼추 1년...  500, 1000등의 숫자를 넣어 테스트 해보자!

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
    for ma in range(3,31):
        df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)


    IsBuy = False #매수 했는지 여부
    BUY_PRICE = 0  #매수한 금액! 

    TryCnt = 0      #매매횟수
    SuccesCnt = 0   #익절 숫자
    FailCnt = 0     #손절 숫자


    fee = 0.0015 #수수료+세금+슬리피지를 매수매도마다 0.15%로 세팅!
    IsFirstDateSet = False
    FirstDateStr = ""
    FirstDateIndex = 0

    #df = df[:len(df)-100] #최근 100거래일을 빼고 싶을 때

    ########################
    ########################
    #######이평선 설정 ########
    ma1 = 5  
    ma2 = 10 
    ma3 = 18


    #######################
    ########################
    ########################

    TotalMoneyList = list()

    #'''


    for i in range(len(df)):


        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]
        

        DateStr = str(df.iloc[i].name)

        Isheaven = False
        #11-4 천국 상승장에는 
        if '-11-' in DateStr or '-12-' in DateStr  or '-01-' in DateStr  or '-02-' in DateStr or '-03-' in DateStr  or '-04-' in DateStr:
            Isheaven = True


        
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            InvestMoney = InvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))

            IsSellGo = False
            





            if InverseStockCode == stock_code: #인버스

                #인버스에서 11-4는 지옥일테니깐
                if Isheaven == True:

                    #30일선 아래면 or 조건으로 이평조건 하나만 불만족해도 팔아 재낀다
                    if PrevClosePrice < df['30ma'].iloc[i-1] :
                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                            IsSellGo = True 

                    #30일선 위라면 기존대로..
                    else:
                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                            IsSellGo = True

                #인버스에서 5-10 기간은 천국일테니깐 잘 안팔게 and로 유지
                else:
                    if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                        IsSellGo = True


            else: # 2배 레버리지 

                #11-4천국에는 레버리지는 잘 안팔게 and로 유지
                if Isheaven == True:
                    if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                        IsSellGo = True

                #레버리지에서 5-10 기간은 지옥이니깐 
                else:
                    #하락장이면 or로 팔아재낀다.
                    if PrevClosePrice < df['30ma'].iloc[i-1] and df['30ma'].iloc[i-2] > df['30ma'].iloc[i-1]  and df[str(ma1)+'ma'].iloc[i-1] < df[str(ma2)+'ma'].iloc[i-1] < df[str(ma3)+'ma'].iloc[i-1]  :
                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                            IsSellGo = True 

                    #아닐 경우는 and로 유지
                    else:
                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                            IsSellGo = True



                        
            
            if IsSellGo == True:  #데드 크로스!

                #진입(매수)가격 대비 변동률
                Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                RevenueRate = (Rate - fee)*100.0 #수익률 계산

                InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                print(stock_name, "(",stock_code, ") ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
                print("\n\n")


                TryCnt += 1

                if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    SuccesCnt += 1
                else:
                    FailCnt += 1


                IsBuy = False #매도했다

        if IsBuy == False and i >= 2:

            if IsFirstDateSet == False:
                FirstDateStr = df.iloc[i].name
                FirstDateIndex = i-1
                IsFirstDateSet = True


            IsBuyGo = False

            if InverseStockCode == stock_code: #인버스

                #11-4 천국에는 인버스는 타이트하게 잡는다!
                if Isheaven == True:
                    if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                        if PrevClosePrice > df['30ma'].iloc[i-1] and df['30ma'].iloc[i-2] < df['30ma'].iloc[i-1]  and df[str(ma1)+'ma'].iloc[i-1] > df[str(ma2)+'ma'].iloc[i-1] > df[str(ma3)+'ma'].iloc[i-1] :
                            IsBuyGo = True
                else:
                    #10-5 지옥에는 인버스는 살짝 느슨하게 잡는다.
                    if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                        if df['30ma'].iloc[i-2] < df['30ma'].iloc[i-1] :
                            IsBuyGo = True

            else: #레버리지 

                #11-4 천국에는 레버리지는 기존 조건 만족하면 잡는다.
                if Isheaven == True:
                    if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                        IsBuyGo = True
                
                else:
                    #10-5 지옥에는 레버리지는 살짝 타이트하게 잡는다.
                    if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                        if PrevClosePrice > df['30ma'].iloc[i-1]  :
                            IsBuyGo = True

        


            if IsBuyGo == True:  #골든 크로스!


                BUY_PRICE = NowOpenPrice 

                InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                print(stock_name, "(",stock_code, ") ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
                IsBuy = True #매수했다

        
        TotalMoneyList.append(InvestMoney)

    #####################################################
    #####################################################
    #####################################################
    #'''
    
   


    #결과 정리 및 데이터 만들기!!
    if len(TotalMoneyList) > 0:

        print("TotalMoneyList -> ", len(TotalMoneyList))

        TotalResultDict[stock_code] = TotalMoneyList

        resultData = dict()

        
        resultData['Ticker'] = stock_code
        resultData['TickerName'] = stock_name
   
        

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
        resultData['SuccesCnt'] = SuccesCnt
        resultData['FailCnt'] = FailCnt

        
        ResultList.append(resultData)



        for idx, row in result_df.iterrows():
            print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
            



#데이터를 보기좋게 프린트 해주는 로직!
print("\n\n--------------------")
TotalHoldRevenue = 0
#TotalMDD= 0

InvestCnt = float(len(ResultList))

for result in ResultList:

    print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")
    print(result['TickerName'], " (",result['Ticker'],")" )
    print("최초 금액:", round(result['OriMoney'],2) , " 최종 금액:", round(result['FinalMoney'],2))
    print("수익률:", round(result['RevenueRate'],2) , "%")
    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['TryCnt'] > 0:
        print("성공:", result['SuccesCnt'] , " 실패:", result['FailCnt']," -> 승률: ", round(result['SuccesCnt']/result['TryCnt'] * 100.0,2) ," %")


    TotalHoldRevenue += result['OriRevenueHold']

    #TotalMDD += (result['MDD'] * result['rate']*10  )



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
        

    TotalOri = result_df['Total_Money'].iloc[1]
    TotalFinal = result_df['Total_Money'].iloc[-1]

    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 #MDD를 종합적으로 계산!


    print("---------- 총 결과 ----------")
    print("최초 금액:", TotalOri , " 최종 금액:", TotalFinal, "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) 평균 MDD:",  round(TotalMDD,2),"%")
    print("------------------------------")
    print("####################################")


