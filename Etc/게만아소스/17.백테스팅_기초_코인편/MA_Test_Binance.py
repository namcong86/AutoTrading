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

업비트 자동매매, 바이낸스 자동매매 백테스팅으로 돈과 시간 아껴보기!
https://blog.naver.com/zacra/223036092055

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


#레버리지를 올릴 수 있습니다.
#그런데 정확하지 않을 수 있어 레버리지는 1로 고정한 다음에 테스팅하는 것을 권장드립니다!!
set_leverage = 1.0

#테스트할 코인 리스트
InvestCoinList = ['BTC/USDT','ETH/USDT','XRP/USDT','ADA/USDT','SOL/USDT','DOT/USDT','ATOM/USDT','LINK/USDT','SAND/USDT']


InvestTotalMoney = 10000



ResultList = list()

for coin_ticker in InvestCoinList:


    print("\n----coin_ticker: ", coin_ticker)

    #해당 코인 가격을 가져온다.
    coin_price = myBinance.GetCoinNowPrice(binanceX, coin_ticker)

    InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!

    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    #LongInvestMoney = InvestMoney

    #롱과 숏 절반씩!
    LongInvestMoney = InvestMoney / 2.0  #롱
    ShortInvestMoney = InvestMoney / 2.0 #숏


    #일봉 정보를 가지고 온다!
    df = myBinance.GetOhlcv(binanceX,coin_ticker, '1d') #1m/3m/5m/15m/30m/1h/4h/1d
    #df = GetOhlcv2(binanceX,coin_ticker, '15m' ,2023, 1, 4, 0, 0) #1m/3m/5m/15m/30m/1h/4h/1d

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
    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!
    pprint.pprint(df)


    IsBuy = False #롱 포지션 여부
    BUY_PRICE = 0  #매수한 가격! 

    LongTryCnt = 0      #매매횟수
    LongSuccesCnt = 0   #익절 숫자
    LongFailCnt = 0     #손절 숫자


    IsSell = False #숏 포지션 여부
    SELL_PRICE = 0  #매수한 가격! 

    ShortTryCnt = 0      #매매횟수
    ShortSuccesCnt = 0   #익절 숫자
    ShortFailCnt = 0     #손절 숫자


    #df = df[:len(df)-100] #최근 100거래일을 빼고 싶을 때



    fee = 0.0005 #수수료+슬리피지를 포지션 잡을때 마다 0.05%로 세팅!


    TotlMoneyList = list()

    '''
    #####################################################
    ##########골든 크로스 데드크로스 롱숏 스위칭!##########
    #####################################################
    for i in range(len(df)):


        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  
        
        
        
        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            LongInvestMoney = LongInvestMoney * (1.0 + (((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice) * set_leverage))
                        
            
            if df['5ma'].iloc[i-2] > df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] < df['20ma'].iloc[i-1]:  #데드 크로스!


                #진입(매수)가격 대비 변동률
                Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                LongTryCnt += 1

                if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    LongSuccesCnt += 1
                else:
                    LongFailCnt += 1


                IsBuy = False 

        if IsBuy == False:

        
            if i >= 2 and df['5ma'].iloc[i-2] < df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] > df['20ma'].iloc[i-1]:  #골든 크로스!

                BUY_PRICE = NowOpenPrice 

                LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])
                IsBuy = True 


        ######################################################################################
        ######################################################################################
        ######################################################################################
        if IsSell == True:

            #투자중이면 매일매일 수익률 반영!
            ShortInvestMoney = ShortInvestMoney * (1.0 + (((PrevOpenPrice - NowOpenPrice) / PrevOpenPrice) * set_leverage))
                        
            
            if df['5ma'].iloc[i-2] < df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] > df['20ma'].iloc[i-1] :  #골든 크로스!


                #진입(매수)가격 대비 변동률
                Rate = (SELL_PRICE - NowOpenPrice) / SELL_PRICE

                RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                ShortTryCnt += 1

                if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                    ShortSuccesCnt += 1
                else:
                    ShortFailCnt += 1


                IsSell = False 

        if IsSell == False:

        
            if i >= 2 and df['5ma'].iloc[i-2] > df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] < df['20ma'].iloc[i-1]:  #데드 크로스!

                SELL_PRICE = NowOpenPrice 

                ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])
                IsSell = True 

        ######################################################################################
        ######################################################################################
        ######################################################################################


        
        TotlMoneyList.append(LongInvestMoney + ShortInvestMoney)

    #####################################################
    #####################################################
    #####################################################
    '''
    
    #'''
    #####################################################
    ########## 진입후 익절 손절 목표에서 정리 ##########
    #####################################################
    
    TakeProfit = 0.10 / set_leverage   #익절 목표
    StopLossProfit = 0.03 / set_leverage #손절 목표

    for i in range(len(df)):
        
        NowOpenPrice = df['open'].iloc[i]  
        PrevOpenPrice = df['open'].iloc[i-1]  

        if IsBuy == True:

            #투자중이면 매일매일 수익률 반영!
            LongInvestMoney = LongInvestMoney * (1.0 + (((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice) * set_leverage))

            #진입(매수)가격 대비 변동률
            Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

            TakePrice = BUY_PRICE * (1.0 + TakeProfit) #익절가격
            StopPrice = BUY_PRICE * (1.0 - StopLossProfit) #손절가격
            

            #손절가 도달! 손절 처리!
            if NowOpenPrice <= StopPrice: 

                RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])


                LongTryCnt += 1
                LongFailCnt += 1

                IsBuy = False 

            else:

                #수익가 도달! 익절 처리!!
                if NowOpenPrice >= TakePrice: 

                    RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                    LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                    print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                    LongTryCnt += 1
                    LongSuccesCnt += 1

                    IsBuy = False 

        

        if IsBuy == False:

            #골든 크로스!
            if i >= 2 and df['5ma'].iloc[i-2] < df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] > df['20ma'].iloc[i-1]: 

                BUY_PRICE = NowOpenPrice #매수가격 지정!

                LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) )

                IsBuy = True 






        ######################################################################################
        ######################################################################################
        #################################################################
        if IsSell == True:

            #투자중이면 매일매일 수익률 반영!
            ShortInvestMoney = ShortInvestMoney * (1.0 + (((PrevOpenPrice - NowOpenPrice) / PrevOpenPrice) * set_leverage))

            #진입(매수)가격 대비 변동률
            Rate = (SELL_PRICE - NowOpenPrice) / SELL_PRICE

            TakePrice = SELL_PRICE * (1.0 - TakeProfit) #익절가격
            StopPrice = SELL_PRICE * (1.0 + StopLossProfit) #손절가격
            

            #손절가 도달! 손절 처리!
            if NowOpenPrice >= StopPrice: 

                RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])


                ShortTryCnt += 1
                ShortFailCnt += 1

                IsSell = False 

            else:

                #수익가 도달! 익절 처리!!
                if NowOpenPrice <= TakePrice: 

                    RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                    ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                    print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                    ShortTryCnt += 1
                    ShortSuccesCnt += 1

                    IsSell = False 

        

        if IsSell == False:

            #데드 크로스!
            if i >= 2 and df['5ma'].iloc[i-2] > df['20ma'].iloc[i-2] and df['5ma'].iloc[i-1] < df['20ma'].iloc[i-1]: 

                SELL_PRICE = NowOpenPrice #매수가격 지정!

                ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage)) #수수료 및 세금, 슬리피지 반영!

                print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) )

                IsSell = True 
        #################################################################
        ######################################################################################
        ######################################################################################


        TotlMoneyList.append(LongInvestMoney + ShortInvestMoney)
    
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

        resultData['DateStr'] = str(result_df.iloc[0].name) + " ~ " + str(result_df.iloc[-1].name)

        resultData['OriMoney'] = result_df['Total_Money'].iloc[0]
        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[0] - 1.0) * 100.0 
        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

        resultData['LongTryCnt'] = LongTryCnt
        resultData['LongSuccesCnt'] = LongSuccesCnt
        resultData['LongFailCnt'] = LongFailCnt

        resultData['ShortTryCnt'] = ShortTryCnt
        resultData['ShortSuccesCnt'] = ShortSuccesCnt
        resultData['ShortFailCnt'] = ShortFailCnt


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

    print("--->>>",result['DateStr'],"<<<---")
    print(result['Ticker'] )
    print("최초 금액: ", round(result['OriMoney'],2) , " 최종 금액: ", round(result['FinalMoney'],2))
    print("수익률:", round(result['RevenueRate'],2) , "%")
    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
    print("MDD:", round(result['MDD'],2) , "%")

    if result['LongTryCnt'] > 0:
        print("롱 성공:", result['LongSuccesCnt'] , " 실패:", result['LongFailCnt']," -> 승률: ", round(result['LongSuccesCnt']/result['LongTryCnt'] * 100.0,2) ," %")


    if result['ShortTryCnt'] > 0:
        print("숏 성공:", result['ShortSuccesCnt'] , " 실패:", result['ShortFailCnt']," -> 승률: ", round(result['ShortSuccesCnt']/result['ShortTryCnt'] * 100.0,2) ," %")


    TotalOri += result['OriMoney']
    TotalFinal += result['FinalMoney']

    TotalHoldRevenue += result['OriRevenueHold']
    TotalMDD += result['MDD']

    print("\n--------------------\n")

if TotalOri > 0:
    print("####################################")
    print("---------- 총 결과 ----------")
    print("최초 금액:", TotalOri , " 최종 금액:", TotalFinal, "\n수익률:", round(((TotalFinal - TotalOri) / TotalOri) * 100,2) ,"% (단순보유수익률:" ,round(TotalHoldRevenue/InvestCnt,2) ,"%) 평균 MDD:",  round(TotalMDD/InvestCnt,2),"%")
    print("------------------------------")
    print("####################################")






