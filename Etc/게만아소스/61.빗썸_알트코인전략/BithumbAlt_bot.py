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



관련 포스팅
https://blog.naver.com/zacra/223589057576

위 포스팅을 꼭 참고하세요!!!

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


 
'''


import myBithumb
import time

import pandas as pd
import json
import line_alert
import pprint





#시간 정보를 읽는다
time_info = time.gmtime()

day_n = time_info.tm_mday



#오늘 로직이 진행되었는지 날짜 저장 관리 하는 파일
DateDateTodayDict = dict()

#파일 경로입니다.
today_file_path = "/var/autobot/BithumbAltInvestToday.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(today_file_path, 'r') as json_file:
        DateDateTodayDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Init..")
    
    #0으로 초기화!!!!!
    DateDateTodayDict['date'] = 0
    #파일에 저장
    with open(today_file_path, 'w') as outfile:
        json.dump(DateDateTodayDict, outfile)

############################################################
############################################################
#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.3 #투자 비중은 자금사정에 맞게 수정하세요!
MaxCoinCnt = 30 #투자 코인 개수!!!


#사용 이동평균선!
long_ma1 = 5
long_ma2 = 50

#최소 매수 금액
minmunMoney = 10000

#제외할 코인
OutCoinList = ['KRW-USDT','KRW-BTC','KRW-ETH']
############################################################
############################################################

if DateDateTodayDict['date'] != day_n:
    


    print("15초 정도 쉽니다!")
    time.sleep(15.0) #안전전략등 다른 봇과 돌릴 경우.



    #내가 가진 잔고 데이터를 다 가져온다.
    balances = myBithumb.GetBalances()

    TotalMoney = myBithumb.GetTotalMoney(balances) #총 원금
    TotalRealMoney = myBithumb.GetTotalRealMoney(balances) #총 평가금액

    print("TotalMoney", TotalMoney)
    print("TotalRealMoney", TotalRealMoney)
    
    
    
    ##########################################################################
    InvestTotalMoney = TotalMoney * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
    ##########################################################################

    print("InvestTotalMoney", InvestTotalMoney)

    InvestCoinMoney = InvestTotalMoney / (MaxCoinCnt+1) #코인당 투자금!
    

    
    Tickers = myBithumb.GetTickers()
            

    #투자한 코인을 저장할 리스트!!
    AltInvestList = list()

    #파일 경로입니다.
    invest_file_path = "/var/autobot/BithumbAltInvestList.json"
    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(invest_file_path, 'r') as json_file:
            AltInvestList = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("Exception by First")



            
    stock_df_list = []

    for ticker in Tickers:

        try:

   
            print("----->", ticker ,"<-----")
            df = myBithumb.GetOhlcv(ticker,'1d',700)

            df['value'] = df['close'] * df['volume']
            
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
            df['ma5_rsi_before'] = df['RSI'].rolling(5).mean().shift(1)


            df['prevValue'] = df['value'].shift(1)
            df['prevClose'] = df['close'].shift(1)
            df['prevOpen'] = df['open'].shift(1)
            df['prevClose2'] = df['close'].shift(2)

            df['prevChange'] = (df['prevClose'] - df['prevClose2']) / df['prevClose2']

            df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)


            df['prevCloseW'] = df['close'].shift(7)
            df['prevChangeW'] = (df['prevClose'] - df['prevCloseW']) / df['prevCloseW']
                
                

            #이렇게 3일선 부터 200일선을 자동으로 만들 수 있다!
            ma_dfs = []

            # 이동 평균 계산
            for ma in range(3, 201):
                ma_df = df['close'].rolling(ma).mean().rename('ma'+str(ma)+'_before').shift(1)
                ma_dfs.append(ma_df)
                
                ma_df = df['close'].rolling(ma).mean().rename('ma'+str(ma)+'_before2').shift(2)
                ma_dfs.append(ma_df)
            # 이동 평균 데이터 프레임을 하나로 결합
            ma_df_combined = pd.concat(ma_dfs, axis=1)

            # 원본 데이터 프레임과 결합
            df = pd.concat([df, ma_df_combined], axis=1)

            
            df.dropna(inplace=True) #데이터 없는건 날린다!

        

            data_dict = {ticker: df}
            stock_df_list.append(data_dict)

            time.sleep(0.2)

        except Exception as e:
            print("Exception ", e)


    # Combine the OHLCV data into a single DataFrame
    combined_df = pd.concat([list(data_dict.values())[0].assign(ticker=ticker) for data_dict in stock_df_list for ticker in data_dict])

    # Sort the combined DataFrame by date
    combined_df.sort_index(inplace=True)


    pprint.pprint(combined_df)
    print(" len(combined_df) ", len(combined_df))


    combined_df.index = pd.DatetimeIndex(combined_df.index).strftime('%Y-%m-%d %H:%M:%S')

    #가장 최근 날짜를 구해서 가져옴 
    date = combined_df.iloc[-1].name

    btc_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == 'KRW-BTC')]


    pick_coins_top = combined_df.loc[combined_df.index == date].groupby('ticker')['prevValue'].max().nlargest(50).nsmallest((int(MaxCoinCnt))) #거래대금 상위 50개 중 하위 30개

    pick_coins_top_change = combined_df.loc[combined_df.index == date].groupby('ticker')['prevChange'].max().nlargest(50).nsmallest((int(MaxCoinCnt))) #등락률 상위 50개 중 하위 30개




    items_to_remove = list()

    #투자중 코인!
    for coin_ticker in AltInvestList:

        #잔고가 있는 경우.
        if myBithumb.IsHasCoin(balances,coin_ticker) == True and myBithumb.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney: 
            print("")

            #수익금과 수익률을 구한다!
            revenue_data = myBithumb.GetRevenueMoneyAndRate(balances,coin_ticker)

            msg = coin_ticker + "현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
            print(msg)
            line_alert.SendMessage(msg)


            stock_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == coin_ticker)]


            if len(stock_data) == 1:

                IsSell = False

                if btc_data['ma120_before'].values[0]  >  btc_data['prevClose'].values[0]:
                    IsSell = True
                    
   
                if ((stock_data['ma'+str(long_ma1)+'_before2'].values[0]  >  stock_data['ma'+str(long_ma1)+'_before'].values[0] and stock_data['ma'+str(long_ma1)+'_before'].values[0]  >  stock_data['prevClose'].values[0]) or (stock_data['ma'+str(long_ma2)+'_before2'].values[0]  >  stock_data['ma'+str(long_ma2)+'_before'].values[0] and stock_data['ma'+str(long_ma2)+'_before'].values[0]  >  stock_data['prevClose'].values[0])) :
                    IsSell = True

                if IsSell == True:


                    AllAmt = myBithumb.GetCoinAmount(balances,coin_ticker) 

                    balances = myBithumb.SellCoinMarket(coin_ticker,AllAmt)
                                    
                    msg = coin_ticker + " 빗썸 알트 투자 봇 : 조건을 불만족하여 모두 매도처리 했어요!!"
                    print(msg)
                    line_alert.SendMessage(msg)

                    items_to_remove.append(coin_ticker)


        #잔고가 없는 경우
        else:
            #투자중으로 나와 있는데 잔고가 없다? 있을 수 없지만 수동으로 매도한 경우..
            items_to_remove.append(coin_ticker)


    #리스트에서 제거
    for item in items_to_remove:
        AltInvestList.remove(item)


    #파일에 저장
    with open(invest_file_path, 'w') as outfile:
        json.dump(AltInvestList, outfile)


    #거래대금 11~30위 
    for ticker in pick_coins_top.index:

        if ticker in OutCoinList: #제외할 코인!
            continue
        
        CheckMsg = ticker

        print("---거래대금 상위 OK..." ,ticker)

        CheckMsg += " 거래대금 조건 만족! "
        
        IsAlReadyInvest = False
        for coin_ticker in AltInvestList:
            if ticker == coin_ticker: 
                IsAlReadyInvest = True
                break

        IsTOPInChange = False
        for ticker_t in pick_coins_top_change.index:
            if ticker_t == ticker:
                coin_top_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker_t)]
                if len(coin_top_data) == 1:
                    IsTOPInChange = True
                    break




        stock_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker)]


        if len(stock_data) == 1 and IsAlReadyInvest == False and IsTOPInChange == True: 

            print("--- 등락률 상위 OK..." ,ticker)


            
            CheckMsg += " 등락률 상위 조건 만족! "
            IsBuyGo = False

            if (btc_data['ma60_before2'].values[0]  <  btc_data['ma60_before'].values[0] or btc_data['ma60_before'].values[0]  <  btc_data['prevClose'].values[0])  and (btc_data['ma120_before2'].values[0]  <  btc_data['ma120_before'].values[0] or btc_data['ma120_before'].values[0]  <  btc_data['prevClose'].values[0]) and stock_data['prevChangeW'].values[0] > 0:

                CheckMsg += " 비트코인 조건 만족! "
                #거래대금 10억 이상
                if stock_data['prevValue'].values[0] > 1000000000:  


                    CheckMsg += " 거래대금 조건 만족 "
                    if stock_data['prevClose'].values[0] > stock_data['prevOpen'].values[0] and ((stock_data['ma'+str(long_ma1)+'_before2'].values[0]  <=  stock_data['ma'+str(long_ma1)+'_before'].values[0] and stock_data['ma'+str(long_ma1)+'_before'].values[0]  <=  stock_data['prevClose'].values[0]) and (stock_data['ma'+str(long_ma2)+'_before2'].values[0]  <=  stock_data['ma'+str(long_ma2)+'_before'].values[0] and stock_data['ma'+str(long_ma2)+'_before'].values[0]  <=  stock_data['prevClose'].values[0])) :
            
                        CheckMsg += " 추가 조건 만족! 모든 코인이 투자된 것이 아니라면 매수!! "
                        IsBuyGo = True


            #조건 만족하고 아직 20개 코인이 투자된 것이 아니라면 
            if IsBuyGo == True and len(AltInvestList) < int(MaxCoinCnt):


                Rate = 1.0

                BuyMoney = InvestCoinMoney * Rate

                #투자금 제한!
                if BuyMoney > stock_data['value_ma'].values[0] / 2000:
                    BuyMoney = stock_data['value_ma'].values[0] / 2000

                if BuyMoney < minmunMoney:
                    BuyMoney = minmunMoney



                #원화 잔고를 가져온다
                won = myBithumb.GetCoinAmount(balances,"KRW")
                print("# Remain Won :", won)
                time.sleep(0.04)
                
                #
                if BuyMoney > won:
                    BuyMoney = won * 0.99 #슬리피지 및 수수료 고려

                balances = myBithumb.BuyCoinMarket(ticker,BuyMoney)

                msg = ticker + " 빗썸 알트 투자 봇 : 조건 만족 하여 매수!!"
                print(msg)
                line_alert.SendMessage(msg)

                AltInvestList.append(ticker)

                #파일에 저장
                with open(invest_file_path, 'w') as outfile:
                    json.dump(AltInvestList, outfile)


        print(CheckMsg)
        line_alert.SendMessage(CheckMsg)


    #체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
    DateDateTodayDict['date'] = day_n
    #파일에 저장
    with open(today_file_path, 'w') as outfile:
        json.dump(DateDateTodayDict, outfile)


    msg = " 빗썸 알트 투자 봇 : 오늘 로직 끝!!"
    print(msg)
    line_alert.SendMessage(msg)


else:
    print("빗썸 알트 투자 봇 : 오늘 로직 실행 완료되었어요!!")



