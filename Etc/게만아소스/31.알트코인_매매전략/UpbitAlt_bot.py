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




코드 이해하는데 도움 되는 설명 참고 영상!
https://youtu.be/IViI5gofQf4?si=Fnqm4_OmVfLnHCWD





네트워크 등의 일시 문제로 정시(9시)에 실행이 안되거나 오류가 나는 정황이 드물지만 있다는 것이 포착되었습니다.
그런데 하루 1번 실행만 하는 경우 그게 실패해버리면 그날 매매가 안되는 것이니
아래와 같이 아침 9시부터 5분마다 실행하게 변경해서 사용하는 것을 권장해 봅니다!

*/5 0 * * * python3 /var/autobot/UpbitAlt20_bot.py


관련 포스팅

파이썬 업비트 자동매매 알트 코인들로 수익내기
https://blog.naver.com/zacra/223122965642

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

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
            
    #내가 가진 잔고 데이터를 다 가져온다.
    balances = upbit.get_balances()
    time.sleep(0.04)

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
today_file_path = "/var/autobot/UpbitAltInvestTodayX.json"
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




#매도 체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
if DateDateTodayDict['date'] != day_n:



    #암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
    simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

    #암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
    Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
    Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

    #업비트 객체를 만든다
    upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)



    print("15초 정도 쉽니다!")
    time.sleep(15.0)


    #최소 매수 금액
    minmunMoney = 5500

    #내가 가진 잔고 데이터를 다 가져온다.
    balances = upbit.get_balances()

    TotalMoeny = myUpbit.GetTotalMoney(balances) #총 원금
    TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

    print("TotalMoeny", TotalMoeny)
    print("TotalRealMoney", TotalRealMoney)
    #투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
    InvestRate = 0.3 #투자 비중은 자금사정에 맞게 수정하세요!

    ##########################################################################
    InvestTotalMoney = TotalMoeny * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
    ##########################################################################

    print("InvestTotalMoney", InvestTotalMoney)

    MaxCoinCnt = 20 #투자 코인 개수!!!
    InvestCoinMoney = InvestTotalMoney / (MaxCoinCnt + 1) #코인당 투자금!


    #해당 전략이 매매하면 안되는 코인리스트.. (다른전략이 투자하는 코인이거나 상폐 예정인 코인들을 여기에 추가!!!)
    OutCoinList = ['KRW-BTC','KRW-ETH']
    
    Tickers = pyupbit.get_tickers("KRW",True) #원화마켓의 모든 데이터!

    for coin_data in Tickers:
        if coin_data['market_event']['warning'] == True:
            OutCoinList.append(coin_data['market'])
            
            

    #투자한 코인을 저장할 리스트!!
    AltInvestList = list()

    #파일 경로입니다.
    invest_file_path = "/var/autobot/UpbitAltInvestListX.json"
    try:
        #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
        with open(invest_file_path, 'r') as json_file:
            AltInvestList = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("Exception by First")





    Tickers = pyupbit.get_tickers("KRW") #원화마켓의 모든 데이터!


    stock_df_list = []

    for ticker in Tickers:

        try:

            #제외 코인은 굳이 정보를 알 필요가 없다!
            if ticker in OutCoinList:
                continue

            print("----->", ticker ,"<-----")
            df = pyupbit.get_ohlcv(ticker,interval="day") 

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

            df['ma10_before'] = df['close'].rolling(10).mean().shift(1)

            df['ma20_before'] = df['close'].rolling(20).mean().shift(1)

            
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


    pick_coins_top = combined_df.loc[combined_df.index == date].groupby('ticker')['prevValue'].max().nlargest(30).nsmallest((int(MaxCoinCnt))) #거래대금 상위 30개 중 하위 20개

    pick_coins_top_change = combined_df.loc[combined_df.index == date].groupby('ticker')['prevChange'].max().nlargest(30).nsmallest((int(MaxCoinCnt))) #등락률 상위 30개 중 하위 20개




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


            stock_data = combined_df[(combined_df.index == date) & (combined_df['ticker'] == coin_ticker)]


            if len(stock_data) == 1:

                IsSell = False

                if stock_data['ma5_before2'].values[0] > stock_data['ma5_before'].values[0] and stock_data['prevRSI'].values[0] <= 55: 
                    IsSell = True

                if IsSell == True:


                    AllAmt = upbit.get_balance(coin_ticker) #현재 수량

                    balances = myUpbit.SellCoinMarket(upbit,coin_ticker,AllAmt)
                                    
                    msg = coin_ticker + " 알트 투자 봇 : 조건을 불만족하여 모두 매도처리 했어요!!"
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

        #이미 투자중이 아니면서 등락률 상위 11~30위인 코인들이 후보!
        if len(stock_data) == 1 and IsAlReadyInvest == False and IsTOPInChange == True: 

            print("--- 등락률 상위 OK..." ,ticker)

            
            CheckMsg += " 등락률 상위 조건 만족! "
            IsBuyGo = False

            if stock_data['ma5_rsi_before'].values[0] < stock_data['prevRSI'].values[0] and stock_data['prevChange'].values[0] > 0 and stock_data['ma5_before'].values[0] < stock_data['prevClose'].values[0] and stock_data['ma10_before'].values[0] < stock_data['prevClose'].values[0] and stock_data['ma20_before'].values[0] < stock_data['prevClose'].values[0]:

                CheckMsg += " 추가 조건 만족! 모든 코인이 투자된 것이 아니라면 매수!! "
                print("-----OK----")
                IsBuyGo = True

            #조건 만족하고 아직 20개 코인이 투자된 것이 아니라면 
            if IsBuyGo == True and len(AltInvestList) < int(MaxCoinCnt):


                Rate = 1.0

                BuyMoney = InvestCoinMoney * Rate

                #투자금 제한!
                if BuyMoney > stock_data['value_ma'].values[0] / 2000:
                    BuyMoney = stock_data['value_ma'].values[0] / 2000

                if BuyMoney < 10000:
                    BuyMoney = 10000



                #원화 잔고를 가져온다
                won = float(upbit.get_balance("KRW"))
                print("# Remain Won :", won)
                time.sleep(0.04)
                
                #
                if BuyMoney > won:
                    BuyMoney = won * 0.99 #슬리피지 및 수수료 고려

                balances = myUpbit.BuyCoinMarket(upbit,ticker,BuyMoney)

                msg = ticker + " 알트 투자 봇 : 조건 만족 하여 매수!!"
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



    msg = " 업비트 알트 투자 봇 : 오늘 로직 끝!!"
    print(msg)
    line_alert.SendMessage(msg)



else:
    print("오늘은 이미 업비트 알트 봇 로직이 끝났어요!!")









