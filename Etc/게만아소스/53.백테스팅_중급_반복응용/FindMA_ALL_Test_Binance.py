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

https://blog.naver.com/zacra/223486828128

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
InvestList = ['BTC/USDT','ETH/USDT','SOL/USDT','XRP/USDT']


EnCount = 0     #최근 데이터 삭제! 200으로 세팅하면 200개의 최근 데이터가 사라진다 (즉 과거 시점의 백테스팅 가능)


AllRealTotalList = list()

for coin_ticker in InvestList:


    RealTotalList = list()
    print("\n----coin_ticker: ", coin_ticker)

    #해당 코인 가격을 가져온다.
    coin_price = myBinance.GetCoinNowPrice(binanceX, coin_ticker)


    #일봉 정보를 가지고 온다!
    df = myBinance.GetOhlcv(binanceX,coin_ticker, '1d') #마지막 파라미터에 가져올 데이터 개수를 넣어서 사용가능함! 
    #df = GetOhlcv2(binanceX,coin_ticker, '15m' ,2023, 1, 4, 0, 0) #1m/3m/5m/15m/30m/1h/4h/1d


    ############# 이동평균선! ###############
    #for ma in range(3,121):
    #    df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
        
    ma_dfs = []

    # 이동 평균 계산
    for ma in range(3, 121):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)

    # 이동 평균 데이터 프레임을 하나로 결합
    ma_df_combined = pd.concat(ma_dfs, axis=1)

    # 원본 데이터 프레임과 결합
    df = pd.concat([df, ma_df_combined], axis=1)

    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!
    
    df = df[:len(df)-EnCount]
    pprint.pprint(df)

    print("이평선 조합 체크 중....")
    for ma1 in range(3,51):
        for ma2 in range(20,121):
            
            if ma1 < ma2:
            

                InvestMoney = 1000



                #롱과 숏 절반씩!
                LongInvestMoney = InvestMoney / 2.0  #롱
                ShortInvestMoney = InvestMoney / 2.0 #숏

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

                fee = 0.0015 #수수료+슬리피지를 매수매도마다 0.15%로 세팅!


                TotlMoneyList = list()

                #'''
                #####################################################
                ##########골든 크로스 데드크로스 롱숏 스위칭!##########
                #####################################################
                for i in range(len(df)):


                    NowOpenPrice = df['open'].iloc[i]  
                    PrevOpenPrice = df['open'].iloc[i-1]  
                    
                    
                    
                    if IsBuy == True:
                        price_change_rate = (NowOpenPrice - PrevOpenPrice) / PrevOpenPrice
                        leverage_profit_rate = price_change_rate * set_leverage
                        
                        # 청산 체크
                        if leverage_profit_rate <= -1:  # 100% 손실 = 청산
                            LongInvestMoney = 0
                            IsBuy = False
                        else:
                            LongInvestMoney = LongInvestMoney * (1.0 + leverage_profit_rate)
                                    
                        
                        if df[str(ma1)+'ma'].iloc[i-2] > df[str(ma2)+'ma'].iloc[i-2] and df[str(ma1)+'ma'].iloc[i-1] < df[str(ma2)+'ma'].iloc[i-1]:   #데드 크로스!


                            #진입(매수)가격 대비 변동률
                            Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                            RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                            LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                            #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                            LongTryCnt += 1

                            if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                                LongSuccesCnt += 1
                            else:
                                LongFailCnt += 1


                            IsBuy = False 

                    if IsBuy == False:

                    
                        if i >= 2 and df[str(ma1)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-2] and df[str(ma1)+'ma'].iloc[i-1] > df[str(ma2)+'ma'].iloc[i-1]: #골든 크로스!

                            BUY_PRICE = NowOpenPrice 

                            LongInvestMoney = LongInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                            #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 롱 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])
                            IsBuy = True 


                    ######################################################################################
                    ######################################################################################
                    ######################################################################################
                    if IsSell == True:
                        price_change_rate = (PrevOpenPrice - NowOpenPrice) / PrevOpenPrice
                        leverage_profit_rate = price_change_rate * set_leverage
                        
                        # 청산 체크
                        if leverage_profit_rate <= -1:  # 100% 손실 = 청산
                            ShortInvestMoney = 0
                            IsSell = False
                        else:
                            ShortInvestMoney = ShortInvestMoney * (1.0 + leverage_profit_rate)
                                    
                        
                        if df[str(ma1)+'ma'].iloc[i-2] < df[str(ma2)+'ma'].iloc[i-2] and df[str(ma1)+'ma'].iloc[i-1] > df[str(ma2)+'ma'].iloc[i-1]:  #골든 크로스!


                            #진입(매수)가격 대비 변동률
                            Rate = (SELL_PRICE - NowOpenPrice) / SELL_PRICE

                            RevenueRate = ((Rate * set_leverage) - (fee * set_leverage))*100.0 #수익률 계산

                            ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                            #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 종료!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2)  , " ", df['open'].iloc[i])


                            ShortTryCnt += 1

                            if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                                ShortSuccesCnt += 1
                            else:
                                ShortFailCnt += 1


                            IsSell = False 

                    if IsSell == False:

                    
                        if i >= 2 and df[str(ma1)+'ma'].iloc[i-2] > df[str(ma2)+'ma'].iloc[i-2] and df[str(ma1)+'ma'].iloc[i-1] < df[str(ma2)+'ma'].iloc[i-1]:  #데드 크로스!

                            SELL_PRICE = NowOpenPrice 

                            ShortInvestMoney = ShortInvestMoney * (1.0 - (fee * set_leverage))  #수수료 및 세금, 슬리피지 반영!

                            #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 숏 포지션 시작! ,종목 잔고:", round(LongInvestMoney + ShortInvestMoney,2) , " ", df['open'].iloc[i])
                            IsSell = True 

                    ######################################################################################
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
        
                    #'''
                    print("############ 전체기간 ##########")
                                                
                    print("-- ma1", ma1, " -- ma2 : ", ma2)
                    print("---------- 총 결과 ----------")
                    print("최초 금액:", str(format(round(resultData['OriMoney']), ','))  , " 최종 금액:", str(format(round(resultData['FinalMoney']), ',')), "\n수익률:", format(round(((resultData['FinalMoney'] - resultData['OriMoney']) / resultData['OriMoney']) * 100,2),',') ,"% (단순보유수익률:" ,format(round(resultData['OriRevenueHold'],2),',') ,"%) MDD:",  round(resultData['MDD'],2),"%")
                    print("------------------------------")
                    print("####################################")
                    #'''

                    FinalResultData = dict()
                    FinalResultData['day_str'] = resultData['DateStr']
                    FinalResultData['coin_ticker'] = coin_ticker
                    FinalResultData['ma_str'] = str(ma1) + " " + str(ma2) 
                    FinalResultData['RevenueRate'] = round(((resultData['FinalMoney'] - resultData['OriMoney']) / resultData['OriMoney']) * 100,2)
                    FinalResultData['MDD'] = round(resultData['MDD'],2)

                    RealTotalList.append(FinalResultData)
                    
                    TotlMoneyList.clear()
                    
       
    AllRealTotalList.append(RealTotalList)
    

    
    print(coin_ticker, " 체크 끝!!!!!!!")
    print("#####################################################################")
    
    

print("\n\n\n>>>>>>>>>>>>>>>>>>>최종결과<<<<<<<<<<<<<<<<<<<<<<<<<")
for ResultList in AllRealTotalList:
    
    df_all = pd.DataFrame(ResultList)
    
    print("#####################################################################")
    print("#####################################################################\n")
    Ticker = df_all['coin_ticker'].iloc[-1]
    print("대상 종목 : ", Ticker)
    print("테스트 기간: ", df_all['day_str'].iloc[-1],"\n")
    
    df_all = df_all.drop('day_str', axis=1)
    df_all = df_all.drop('coin_ticker', axis=1)
    
    df_all['RevenueRate_rank'] = df_all['RevenueRate'].rank(ascending=True)
    df_all['MDD_rank'] = df_all['MDD'].rank(ascending=True)
    df_all['Score'] = df_all['RevenueRate_rank'] + df_all['MDD_rank']

    df_all = df_all.sort_values(by="RevenueRate_rank",ascending=False)
    print(">>>>>>>>>> ",Ticker," 수익률 TOP10 >>>>>>>>>>>>>>>>")
    pprint.pprint(df_all.head(10))
    
    df_all = df_all.sort_values(by="MDD_rank",ascending=False)
    print("\n>>>>>>>>>> ",Ticker," MDD TOP10 >>>>>>>>>>>>>>>>")
    pprint.pprint(df_all.head(10))
    
    df_all = df_all.sort_values(by="Score",ascending=False)
    print("\n>>>>>>>>>> ",Ticker," (수익률랭크+MDD랭크)랭킹 TOP10 >>>>>>>>>>>>>>>>")
    pprint.pprint(df_all.head(10))
    
    print("#####################################################################")
    print("#####################################################################\n\n")
    

print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

