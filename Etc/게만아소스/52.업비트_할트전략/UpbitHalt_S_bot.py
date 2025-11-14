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
https://blog.naver.com/zacra/223473233858
위 포스팅을 꼭 참고하세요!!!

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


 
'''

import myUpbit   #우리가 만든 함수들이 들어있는 모듈
import time
import pyupbit

import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키
import pandas as pd
import pprint
import json

import line_alert





#수익금과 수익률을 리턴해주는 함수 (수수료는 생각안함) myUpbit에 넣으셔서 사용하셔도 됨!
def GetRevenueMoneyAndRate(balances,Ticker):
            

    revenue_data = dict()

    revenue_data['revenue_money'] = 0
    revenue_data['revenue_rate'] = 0

    for value in balances:
        try:
            realTicker = value['unit_currency'] + "-" + value['currency']
            if Ticker == realTicker:
                
                nowPrice = pyupbit.get_current_price(realTicker)
                revenue_data['revenue_money'] = (float(nowPrice) - float(value['avg_buy_price'])) * upbit.get_balance(Ticker)
                revenue_data['revenue_rate'] = (float(nowPrice) - float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
                time.sleep(0.06)
                break

        except Exception as e:
            print("---:", e)

    return revenue_data





#시간 정보를 읽는다
time_info = time.gmtime()

day_n = time_info.tm_mday



#오늘 로직이 진행되었는지 날짜 저장 관리 하는 파일
DateDateTodayDict = dict()

#파일 경로입니다.
today_file_path = "/var/autobot/UpbitHaltInvestToday.json"
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
MaxCoinCnt = 3 #투자 코인 개수!!!


#최소 매수 금액
minmunMoney = 10000
############################################################
############################################################

if DateDateTodayDict['date'] != day_n:
    


    print("15초 정도 쉽니다!")
    time.sleep(15.0) #안전전략등 다른 봇과 돌릴 경우.


    #암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
    simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

    #암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
    Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
    Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

    #업비트 객체를 만든다
    upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)


    #내가 가진 잔고 데이터를 다 가져온다.
    balances = upbit.get_balances()

    TotalMoney = myUpbit.GetTotalMoney(balances) #총 원금
    TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

    print("TotalMoney", TotalMoney)
    print("TotalRealMoney", TotalRealMoney)
    
    
    
    ##########################################################################
    InvestTotalMoney = TotalMoney * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
    ##########################################################################

    print("InvestTotalMoney", InvestTotalMoney)

    InvestCoinMoney = InvestTotalMoney / (MaxCoinCnt) #코인당 투자금!
    

    #해당 전략이 매매하면 안되는 코인리스트.. (다른전략이 투자하는 코인이거나 상폐 예정인 코인들을 여기에 추가!!!)
    OutCoinList = ['KRW-BTC','KRW-ETH']
    
    Tickers = ["KRW-BTC","KRW-ETH","KRW-ADA","KRW-SOL","KRW-DOT","KRW-POL","KRW-XRP","KRW-DOGE","KRW-SHIB","KRW-AVAX","KRW-LINK","KRW-BCH","KRW-APT","KRW-HBAR","KRW-STX","KRW-ATOM","KRW-XLM","KRW-CRO","KRW-ALGO","KRW-SUI","KRW-VET","KRW-AAVE","KRW-TRX"]

    #혹시나 위 코인중 주의가 뜬 것이 있다면 OutCoinList에 추가
    TempTicker = pyupbit.get_tickers("KRW",True) #원화마켓의 모든 데이터!
    for coin_ticker in Tickers:
        for coin_data in TempTicker:
            if coin_ticker == coin_data['market']:
                if coin_data['market_event']['warning'] == True:
                    OutCoinList.append(coin_data['market'])
                    
            

    #투자한 코인을 저장할 리스트!!
    AltInvestList = list()

    #파일 경로입니다.
    invest_file_path = "/var/autobot/UpbitHaltInvestList.json"
    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(invest_file_path, 'r') as json_file:
            AltInvestList = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("Exception by First")



    #코인을 얼마 기간동안 보유하고 있는지를 관리할 파일!
    CoinHasCountDict = dict()

    #파일 경로입니다.
    CoinHasCount_file_path = "/var/autobot/UpbitHaltHasCoinCount.json"
    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(CoinHasCount_file_path, 'r') as json_file:
            CoinHasCountDict = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("..")



            
    stock_df_list = []

    for ticker in Tickers:

        try:

   
            print("----->", ticker ,"<-----")
            df = pyupbit.get_ohlcv(ticker,interval="day") 

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
            df['prevClose2'] = df['close'].shift(2)

            df['prevChange'] = (df['prevClose'] - df['prevClose2']) / df['prevClose2']

            df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)

            df['ma5_before'] = df['close'].rolling(5).mean().shift(1)
            df['ma5_before2'] = df['close'].rolling(5).mean().shift(2)

            df['ma50_before'] = df['close'].rolling(50).mean().shift(1)
            df['ma50_before2'] = df['close'].rolling(50).mean().shift(2)

            df['ma60_before'] = df['close'].rolling(60).mean().shift(1)
            df['ma60_before2'] = df['close'].rolling(60).mean().shift(2)
            

            df['ma120_before'] = df['close'].rolling(120).mean().shift(1)
            df['ma120_before2'] = df['close'].rolling(120).mean().shift(2)


            df['prevCloseW'] = df['close'].shift(7)
            df['prevChangeW'] = (df['prevClose'] - df['prevCloseW']) / df['prevCloseW']
                
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

    pick_coins_top = combined_df.loc[combined_df.index == date].groupby('ticker')['value_ma'].max().nlargest(10)


    ###################################################
    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 시작<--
    #pick_coins_top_change = combined_df.loc[combined_df.index == date].groupby('ticker')['prevChangeW'].max().nlargest(MaxCoinCnt)
    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 끝 <--
    ###################################################
    
    ###################################################
    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 시작!<--
    #'''
    dic_coin_change = dict()

    for ticker in pick_coins_top.index:
        try:
            
                
            if ticker in OutCoinList: 
                continue

            coin_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker)]
            if len(coin_data) == 1:
                    
                dic_coin_change[ticker] = coin_data['prevChangeW'].values[0]

        except Exception as e:
            print("---:",e)

    dic_sorted_coin_change = sorted(dic_coin_change.items(), key = lambda x : x[1], reverse= True)

    pick_coins_top_change = list()
    cnt = 0
    for coin_data in dic_sorted_coin_change:
        cnt += 1
        if cnt <= MaxCoinCnt:
            pick_coins_top_change.append(coin_data[0])
        else:
            break
    #'''
    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 끝 <--

    TodayRemoveList = list()

    items_to_remove = list()

    #투자중 코인!
    for coin_ticker in AltInvestList:
        


        #잔고가 있는 경우.
        if myUpbit.IsHasCoin(balances,coin_ticker) == True: 
            print("")

            #수익금과 수익률을 구한다!
            revenue_data = GetRevenueMoneyAndRate(balances,coin_ticker)

            msg = coin_ticker + "현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
            print(msg)
            line_alert.SendMessage(msg)
            
            #혹시 값이 없다면 0으로 넣어준다!
            if CoinHasCountDict.get(coin_ticker) == None:

                CoinHasCountDict[coin_ticker] = 0
                #파일에 저장
                with open(CoinHasCount_file_path, 'w') as outfile:
                    json.dump(CoinHasCountDict, outfile)
                    
            
            #보유 날자를 증가시켜준다!!!
            CoinHasCountDict[coin_ticker] += 1
            #파일에 저장
            with open(CoinHasCount_file_path, 'w') as outfile:
                json.dump(CoinHasCountDict, outfile)
                
                

            stock_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == coin_ticker)]


            if len(stock_data) == 1 and len(btc_data) == 1:

                IsSell = False


                #매도 조건!!!! 7일 이상 보유중이라면 리밸런싱 대상이 될 수 있다!
                if CoinHasCountDict[coin_ticker] >= 7:
                    
                    IsTopIn = False
                    ###################################################
                    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 시작<--
                    '''
                    for ticker_t in pick_coins_top.index:
                        
                        if ticker_t == coin_ticker:
                            for ticker_t2 in pick_coins_top_change.index:
                            
                                if ticker_t2 == ticker_t:
                                    coin_top_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker_t2)]
                                    if len(coin_top_data) == 1:
                                        IsTopIn = True
                                        break
                    '''
                    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 끝 <--
                    ###################################################
                    
                    ###################################################
                    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 시작!<--
                    #'''
                    if coin_ticker in pick_coins_top_change:
                        IsTopIn = True
                    #'''
                    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 끝 <--
                    ###################################################
                    if IsTopIn == False:
                        IsSell = True
                        
                    

                if btc_data['ma120_before'].values[0]  >  btc_data['prevClose'].values[0]:
                    IsSell = True
                    
                if ((stock_data['ma50_before2'].values[0]  >  stock_data['ma50_before'].values[0] and stock_data['ma50_before'].values[0]  >  stock_data['prevClose'].values[0]) or (stock_data['ma5_before2'].values[0]  >  stock_data['ma5_before'].values[0] and stock_data['ma5_before'].values[0]  >  stock_data['prevClose'].values[0])) :
    
                    IsSell = True


                if IsSell == True:

                    TodayRemoveList.append(coin_ticker)
                    
                    
                    AllAmt = upbit.get_balance(coin_ticker) #현재 수량

                    balances = myUpbit.SellCoinMarket(upbit,coin_ticker,AllAmt)
                                    
                    msg = coin_ticker + " 업비트 할트 투자 봇 : 조건을 불만족하여 모두 매도처리 했어요!!"
                    print(msg)
                    line_alert.SendMessage(msg)

                    items_to_remove.append(coin_ticker)



                    #보유 날자를 초기화
                    CoinHasCountDict[coin_ticker] = 0
                    #파일에 저장
                    with open(CoinHasCount_file_path, 'w') as outfile:
                        json.dump(CoinHasCountDict, outfile)
                
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


    ###################################################
    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 시작<--
    #for ticker in pick_coins_top.index:
    #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 끝 <--
    ###################################################

    ###################################################
    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 시작!<--
    for ticker in pick_coins_top_change:
    #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 끝 <--
    ###################################################
    

        if ticker in OutCoinList: #제외할 코인!
            continue
        
        
        CheckMsg = ticker
        
        CheckMsg += " 거래대금 & 등락률 상위 조건 만족! "
        
        IsAlReadyInvest = False
        for coin_ticker in AltInvestList:
            if ticker == coin_ticker: 
                IsAlReadyInvest = True
                break


        ###################################################
        #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 시작<--
        '''
        IsTOPInChange = False
        for ticker_t in pick_coins_top_change.index:

            if ticker_t == ticker:
                coin_top_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker_t)]
                if len(coin_top_data) == 1:
                    IsTOPInChange = True
                    break
        '''
        #--> A) 거래대금 TOP 과 수익률 TOP 교집합 조합 버전 끝 <--
        ################################################### 

            
        ###################################################
        #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 시작!<--
        IsTOPInChange = True
        #--> B) 거래대금 TOP 중에서 수익률 높은거 뽑는 버전 끝 <--
        ###################################################
        
        


        stock_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == ticker)]

       
        #이미 투자중이 아니면서 조건 만족한 코인들
        if len(stock_data) == 1 and IsAlReadyInvest == False and IsTOPInChange == True: 



            IsBuyGo = False

            #매수 조건 체크!

            if (btc_data['ma60_before2'].values[0]  <  btc_data['ma60_before'].values[0] or btc_data['ma60_before'].values[0]  <  btc_data['prevClose'].values[0])  and (btc_data['ma120_before2'].values[0]  <  btc_data['ma120_before'].values[0] or btc_data['ma120_before'].values[0]  <  btc_data['prevClose'].values[0]) and stock_data['prevChangeW'].values[0] > 0:

                CheckMsg += " 비트코인 조건 만족! "
                if (stock_data['ma50_before2'].values[0]  <=  stock_data['ma50_before'].values[0] and stock_data['ma50_before'].values[0]  <=  stock_data['prevClose'].values[0] and stock_data['ma5_before2'].values[0]  <=  stock_data['ma5_before'].values[0] and stock_data['ma5_before'].values[0]  <=  stock_data['prevClose'].values[0]) :
                    
                    CheckMsg += " 추가 조건 만족! 모든 코인이 투자된 것이 아니라면 매수!! "
                    IsBuyGo = True


            #조건 만족하고 모든 코인이 투자된 것이 아니라면 
            if IsBuyGo == True and len(AltInvestList) < int(MaxCoinCnt) and ticker not in TodayRemoveList:


                if myUpbit.IsHasCoin(balances,ticker) == False: 

                    Rate = 1.0
                    BuyMoney = InvestCoinMoney * Rate

                    #투자금 제한!
                    if BuyMoney > stock_data['value_ma'].values[0] / 2000:
                        BuyMoney = stock_data['value_ma'].values[0] / 2000

                    if BuyMoney < minmunMoney:
                        BuyMoney = minmunMoney



                    #원화 잔고를 가져온다
                    won = float(upbit.get_balance("KRW"))
                    print("# Remain Won :", won)
                    time.sleep(0.04)
                    
                    #
                    if BuyMoney > won:
                        BuyMoney = won * 0.99 #슬리피지 및 수수료 고려

                    balances = myUpbit.BuyCoinMarket(upbit,ticker,BuyMoney)

                    msg = ticker + " 업비트 할트 투자 봇 : 조건 만족 하여 매수!!"
                    print(msg)
                    line_alert.SendMessage(msg)



                    
                    AltInvestList.append(ticker)

                    #파일에 저장
                    with open(invest_file_path, 'w') as outfile:
                        json.dump(AltInvestList, outfile)



                    CoinHasCountDict[ticker] = 0
                    #파일에 저장
                    with open(CoinHasCount_file_path, 'w') as outfile:
                        json.dump(CoinHasCountDict, outfile)
                        
                        

        print(CheckMsg)
        line_alert.SendMessage(CheckMsg)
            
            
    #체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
    DateDateTodayDict['date'] = day_n
    #파일에 저장
    with open(today_file_path, 'w') as outfile:
        json.dump(DateDateTodayDict, outfile)


    msg = " 업비트 할트 투자 봇 : 오늘 로직 끝!!"
    print(msg)
    line_alert.SendMessage(msg)

else:
    print("오늘은 이미 업비트 할트 투자 봇 로직이 끝났어요!!")




