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

https://blog.naver.com/zacra/223367928639

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''

import ccxt
import time
import pandas as pd
import pprint
       
import myBinance
import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키

import datetime
import matplotlib.pyplot as plt




#분봉/일봉 캔들 정보를 가져온다 시작점을 정의하는 함수로 변경!
def GetOhlcv2(binance, Ticker, period, year=2020, month=1, day=1, hour=0, minute=0):
    date_start = datetime.datetime(year, month, day, hour, minute)
    date_start_ms = int(date_start.timestamp() * 1000)

    final_list = []

    # OHLCV 데이터를 최대 한도(1000)만큼의 청크로 가져옵니다.
    while True:
        # OHLCV 데이터를 가져옵니다.
        ohlcv_data = binance.fetch_ohlcv(Ticker, period, since=date_start_ms)

        # 데이터가 없으면 루프를 중단합니다.
        if not ohlcv_data:
            break

        # 가져온 데이터를 최종 리스트에 추가합니다.
        final_list.extend(ohlcv_data)

        # 다음 가져오기를 위해 시작 날짜를 업데이트합니다.
        date_start = datetime.datetime.utcfromtimestamp(ohlcv_data[-1][0] / 1000)
        date_start_ms = ohlcv_data[-1][0] + (ohlcv_data[1][0] - ohlcv_data[0][0])

        print("Get Data...",str(date_start_ms))
        # 요청 간의 짧은 시간 대기를 위해 sleep을 포함합니다.
        time.sleep(0.2)

    # 최종 리스트를 DataFrame으로 변환합니다.
    df = pd.DataFrame(final_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    return df


#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)


#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Binance_AccessKey = simpleEnDecrypt.decrypt(my_key.binance_access)
Binance_ScretKey = simpleEnDecrypt.decrypt(my_key.binance_secret)


# binance 객체 생성
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey, 
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})


################################################################################
#투자할 코인 리스트
InvestCoinList = ['BTC/USDT','BTCDOM/USDT']

#투자 원금
InvestTotalMoney = 5000

fee = 0.001 #수수료+세금+슬리피지를 매수매도마다 0.1%로 세팅!
################################################################################

OriMoneySt = InvestTotalMoney/len(InvestCoinList)

ResultList = list()
TotalResultDict= dict()



for coin_ticker in InvestCoinList:    
    InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!


    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)


    #롱
    LongInvestMoney = InvestMoney 

    
    LongInvestMoneyCell = LongInvestMoney 
    LongRealInvestMoney = 0
    LongRemainInvestMoney = LongInvestMoney

    LongTotalBuyAmt = 0 #매수 수량
    LongTotalPureMoney = 0 #매수 금액



    #일봉 정보를 가지고 온다!
    #df = myBinance.GetOhlcv(binanceX,coin_ticker, '1d') #1m/3m/5m/15m/30m/1h/4h/1d
    #BTCDOM 상장일을 고려해 데이터를 가져온다
    df = GetOhlcv2(binanceX,coin_ticker, '1d', 2021, 7, 4, 0, 0) #1m/3m/5m/15m/30m/1h/4h/1d


    print("Len!!!!!!!! ",len(df))

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
    for ma in range(3,121):
        df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
    ########################################

   

    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)



    IsBuy = False #롱 포지션 여부
    BUY_PRICE = 0  #매수한 가격! 
    LongAvgPrice = 0


    IsFirstDateSet = False
    FirstDateStr = ""



    TotalMoneyList = list()


    ################# 이평선 설정 ##############
    ma1 = 5  
    ma2 = 10 
    ma3 = 20
    ########################################




    TryCnt = 0      #매매횟수
    SuccessCnt = 0   #익절 숫자
    FailCnt = 0     #손절 숫자

    TodaySell = False


    BUY_PRICE = 0
    IsDolpaDay = False

    SELL_PRICE = 0
    
   
    for i in range(len(df)):

        
        
        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        PrevClosePrice = df['close'].iloc[i-1]
        
        LongRevenue = 0

        TodaySell = False
        
        if IsBuy == True :


            #투자금 수익률 반영!
            if IsDolpaDay == True:
                LongRealInvestMoney = LongRealInvestMoney * (1.0 + ((NowOpenPrice - BUY_PRICE) / BUY_PRICE))
                
                IsDolpaDay = False
            else:
                LongRealInvestMoney = LongRealInvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))


            LongInvestMoney = LongRealInvestMoney + LongRemainInvestMoney 


            #진입(매수)가격 대비 변동률
            LongRate = (NowOpenPrice - LongAvgPrice) / LongAvgPrice

            LongRevenueRate = (LongRate - fee)*100.0 #수익률 계산

            LongRevenue = LongRevenueRate


            print(coin_ticker ," ", df.iloc[i].name, " 롱 투자금 수익률: ", round(LongRevenueRate,2) , "%")


            IsSellGo = False



            #30일선 위에 있는 상승장
            if  PrevClosePrice > df['30ma'].iloc[i-1]:
                if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] and df['rsi'].iloc[i-1] < 55:
                    IsSellGo = True

            #30일선 아래있는 하락장
            else:
                if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and df['rsi'].iloc[i-1] < 55:
                    IsSellGo = True
            


            if IsSellGo == True:

                SellAmt = LongTotalBuyAmt

                LongInvestMoney = LongRemainInvestMoney + (LongRealInvestMoney * (1.0 - fee))  #수수료 및 세금, 슬리피지 반영!

                LongTotalBuyAmt = 0
                LongTotalPureMoney = 0

                LongRealInvestMoney = 0
                LongRemainInvestMoney = LongInvestMoney
                LongAvgPrice = 0


                print(coin_ticker ," ", df.iloc[i].name," >>>>>>> 롱 모두 종료!!:", SellAmt ,"누적수량:",LongTotalBuyAmt," 평단: ",round(LongAvgPrice,2),">>>>>>>> 종료!  \n투자금 수익률: ", round(LongRevenueRate,2) , "%", " ,종목 잔고:",round(LongRemainInvestMoney,2), "+",round(LongRealInvestMoney,2), "=",round(LongInvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n\n")


                TryCnt += 1

                if LongRevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    SuccessCnt += 1
                else:
                    FailCnt += 1



                IsBuy = False

                LongInvestMoney = LongRealInvestMoney + LongRemainInvestMoney 
                TodaySell = True


       
        if IsBuy == False :


            if IsFirstDateSet == False:
                FirstDateStr = df.iloc[i].name
                IsFirstDateSet = True

            #3개의 이평선 중 가장 높은 값을 구한다!
            DolPaSt = max(df[str(ma1)+'ma'].iloc[i-1],df[str(ma2)+'ma'].iloc[i-1],df[str(ma3)+'ma'].iloc[i-1])

            #이평선 조건을 만족하는지
            IsBuyGo = False


            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때 즉 5일,10일,21일선 중 21일선일 때
            #오늘 고가를 체크해 그 전일 이평선 값을 넘은 적이 있다면.. 전일 이평선 값을 그 날 돌파했다는 이야기다.
            if DolPaSt == df[str(ma3)+'ma'].iloc[i-1] and df['high'].iloc[i] >= DolPaSt and NowOpenPrice < DolPaSt:
                
       
                #그렇다면 그 돌파 가격에 매수를 했다고 가정한다.
                BUY_PRICE = DolPaSt
                IsDolpaDay = True
                IsBuyGo = True

            #그 밖의 경우는 기존 처럼 
            else:
                if  PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] and df['rsi'].iloc[i-1] < 70 and df['rsi'].iloc[i-2] < df['rsi'].iloc[i-1]:
                    BUY_PRICE = NowOpenPrice
                    IsDolpaDay = False
                    IsBuyGo = True



            if IsBuyGo == True:


                
                #첫 매수를 진행한다!!!!
                LongInvestMoneyCell = LongInvestMoney

                            
                BuyAmt = float(LongInvestMoneyCell  /  BUY_PRICE) #매수 가능 수량을 구한다!

                NowFee = (BuyAmt*BUY_PRICE) * fee

                LongTotalBuyAmt += BuyAmt
                LongTotalPureMoney += (BuyAmt*BUY_PRICE)

                LongRealInvestMoney += (BuyAmt*BUY_PRICE) #실제 들어간 투자금


                LongRemainInvestMoney -= (BuyAmt*BUY_PRICE) #남은 투자금!
                LongRemainInvestMoney -= NowFee

                LongInvestMoney = LongRealInvestMoney + LongRemainInvestMoney  #실제 잔고는 실제 들어간 투자금 + 남은 투자금!


                LongAvgPrice = BUY_PRICE


                print(coin_ticker ," ", df.iloc[i].name, " >>>> 롱 오픈수량:", BuyAmt ,"누적수량:",LongTotalBuyAmt," 평단: ",round(NowOpenPrice,2)," >>>>>>> 롱 시작! \n투자금 수익률: 0% ,종목 잔고:",round(LongRemainInvestMoney,2), "+",round(LongRealInvestMoney,2), "=",round(LongInvestMoney,2)  , " 현재가:", round(NowOpenPrice,2),"\n")
                IsBuy = True #매수했다
                


        TotalMoneyList.append(LongInvestMoney)

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

        resultData['OriMoney'] = OriMoneySt
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[0] - 1.0) * 100.0 
        resultData['RevenueRate'] =  round(((resultData['FinalMoney'] - resultData['OriMoney']) / resultData['OriMoney']) * 100,2) 
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0


        resultData['TryCnt'] = TryCnt
        resultData['SuccessCnt'] = SuccessCnt
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
    print("최초 금액: $", str(format(round(result['OriMoney']), ',')) , " 최종 금액: $", str(format(round(result['FinalMoney']), ','))  )
    print("수익률:", round(result['RevenueRate'],2) , "%")
    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['TryCnt'] > 0:
        print("성공:", result['SuccessCnt'] , " 실패:", result['FailCnt']," -> 승률: ", round(result['SuccessCnt']/result['TryCnt'] * 100.0,2) ," %")

 

    TotalHoldRevenue += result['OriRevenueHold']


    print("\n--------------------\n")



if len(TotalResultDict) > 0:
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



    TotalOri = InvestTotalMoney
    TotalFinal = result_df['Total_Money'].iloc[-1]

    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 #MDD를 종합적으로 계산!


    print("---------- 총 결과 ----------")
    print("최초 금액:", TotalOri , " 최종 금액:", TotalFinal, "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) MDD:",  round(TotalMDD,2),"%")
    print("------------------------------")
    print("####################################")












