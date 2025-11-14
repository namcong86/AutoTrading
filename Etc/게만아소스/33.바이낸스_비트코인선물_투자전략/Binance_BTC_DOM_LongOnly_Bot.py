#-*-coding:utf-8 -*-
'''

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

바이낸스 ccxt 버전
pip3 install --upgrade ccxt==4.2.19
이렇게 버전을 맞춰주세요!

봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요!
https://blog.naver.com/zacra/222662884649

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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

import line_alert #라인 메세지를 보내기 위함!
import json


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




#시간 정보를 읽는다
time_info = time.gmtime()

day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min

print("day_n:", day_n)
print("hour_n:", hour_n)
print("min_n:", min_n)


#오늘 매수가 일어났다면 오늘 매도가 되지 않게 처리하기 위한 파일 저장!
DateDataDict = dict()

#파일 경로입니다.
date_value_file_path = "/var/autobot/BinanceBTC_DOM_DateInfo.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(date_value_file_path, 'r') as json_file:
        DateDataDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")





#오늘 매도 로직이 진행되었는지 날짜 저장 관리 하는 파일
DateDataSellDict = dict()

#파일 경로입니다.
date_sell_value_file_path = "/var/autobot/BinanceBTC_DOM_SellDateInfo.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(date_sell_value_file_path, 'r') as json_file:
        DateDataSellDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")




###################################################
#레버리지!! 1배로 기본 셋! 레버리지를 쓰면 음의 복리로 인해 백테스팅과 다른 결과가 나타날 수 있음!
set_leverage = 1

#총 원금대비 설정 비율 
#아래처럼 0.5 로 셋팅하면 50%가 해당 전략에 할당된다는 이야기!
Invest_Rate = 0.5

InvestCoinList = ["BTC/USDT","BTCDOM/USDT"]
CoinCnt = len(InvestCoinList)


balance = binanceX.fetch_balance(params={"type": "future"})
time.sleep(0.1)
#pprint.pprint(balance)




for ticker in InvestCoinList:

    try: 

        time.sleep(0.2)

        Target_Coin_Ticker = ticker

        Target_Coin_Symbol = ticker.replace("/", "").replace(":USDT","")


        time.sleep(0.05)
        #최소 주문 수량을 가져온다 
        minimun_amount = myBinance.GetMinimumAmount(binanceX,Target_Coin_Ticker)

        print("--- Target_Coin_Ticker:", Target_Coin_Ticker ," minimun_amount : ", minimun_amount)



        #매도 체크한 기록이 없는 처음이라면 
        if DateDataSellDict.get(Target_Coin_Ticker) == None:

            #0으로 초기화!!!!!
            DateDataSellDict[Target_Coin_Ticker] = 0
            #파일에 저장
            with open(date_sell_value_file_path, 'w') as outfile:
                json.dump(DateDataSellDict, outfile)

                    




        amt_s = 0 
        amt_b = 0
        entryPrice_s = 0 #평균 매입 단가. 
        entryPrice_b = 0 #평균 매입 단가. 
        leverage = 0


        isolated = True #격리모드인지 



        print("------")
        #숏잔고
        for posi in balance['info']['positions']:
            if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'SHORT':
                print(posi)
                amt_s = float(posi['positionAmt'])
                entryPrice_s= float(posi['entryPrice'])
                leverage = float(posi['leverage'])
                isolated = posi['isolated']

                break


        #롱잔고
        for posi in balance['info']['positions']:
            if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':
                print(posi)
                amt_b = float(posi['positionAmt'])
                entryPrice_b = float(posi['entryPrice'])
                leverage = float(posi['leverage'])
                isolated = posi['isolated']

                break

        #################################################################################################################

        if set_leverage != leverage:
            try:
                print(binanceX.fapiPrivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage}))
            except Exception as e:
                try:
                    print(binanceX.fapiprivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage}))
                except Exception as e:
                    print("Exception Done OK..")


        #################################################################################################################



        #################################################################################################################
        #영상엔 없지만         
        #교차모드로 셋팅합니다! isolated == True로 격리모드라면 CROSSED 로 교차모드로 바꿔주면 됩니다.
        #################################################################################################################
        if isolated == True:
            try:
                print(binanceX.fapiPrivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'CROSSED'}))
            except Exception as e:
                try:
                    print(binanceX.fapiprivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'CROSSED'}))
                except Exception as e:
                    print("Exception Done OK..")
        #################################################################################################################    

        #현재가를 구하다
        coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)


        #해당 코인에 할당된 금액에 따른 최대 매수수량을 구해본다!
        Max_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(float(balance['USDT']['total']),coin_price,Invest_Rate / CoinCnt)))  * set_leverage 

        Buy_Amt = Max_Amt 
        Long_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker,Buy_Amt))
    
        print("Long_Amt ", Long_Amt)

        df_day = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '1d')


        #5, 10, 20선으로 투자한다고 가정했습니다!
        Ma5 = myBinance.GetMA(df_day,5,-2)   #전일 종가 기준 5일 이동평균선
        Ma10 = myBinance.GetMA(df_day,10,-2)   #전일 종가 기준 10일 이동평균선
        Ma20 = myBinance.GetMA(df_day,20,-2) #전일 종가 기준 20일 이동평균선


        Ma30_before = myBinance.GetMA(df_day,30,-3) 
        Ma30 = myBinance.GetMA(df_day,30,-2)

        Rsi_before = myBinance.GetRSI(df_day,14,-3) 
        Rsi = myBinance.GetRSI(df_day,14,-2) 


        PrevClose = df_day['close'].iloc[-2]


        #롱 포지션이 있다면..
        if abs(amt_b) > 0:

            revenue_rate_b = (coin_price - entryPrice_b) / entryPrice_b * 100.0


            unrealizedProfit_b = 0 #미 실현 손익.

            #롱 잔고
            for posi in balance['info']['positions']:
                if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':

                    unrealizedProfit_b = float(posi['unrealizedProfit'])
                    break


                
            #매도 체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
            if DateDataSellDict[Target_Coin_Ticker] != day_n:

                msg = Target_Coin_Ticker + "현재 롱 수익률 : 약 " + str(round(revenue_rate_b*set_leverage,2)) + "% 수익금 : 약" + str(round(unrealizedProfit_b,2)) + "USDT"
                print(msg)
                line_alert.SendMessage(msg)



                #매도로직 안으로 들어왔다면 날자를 바꿔준다!!
                DateDataSellDict[Target_Coin_Ticker] = day_n
                #파일에 저장
                with open(date_sell_value_file_path, 'w') as outfile:
                    json.dump(DateDataSellDict, outfile)



                IsSellGo = False
                if PrevClose > Ma30:

                    if Ma5 > PrevClose and Ma10 > PrevClose and Ma20 > PrevClose and Rsi < 55:
                        IsSellGo = True

                    
                else:
                    if Ma5 > PrevClose and Rsi < 55:
                        IsSellGo = True


                #저장된 매수날짜와 오늘 날짜가 같다면.. 오늘 돌파 매수던 시가 매수던 매수가 된 상황이니깐 오늘은 매도 하면 안된다.
                if DateDataDict[Target_Coin_Ticker] == day_n:
                    IsSellGo = False


                if IsSellGo == True:

                    #롱 포지션 종료!!
                    params = {
                        'positionSide': 'LONG'
                    }
                    print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b), None, params))
                    
                    msg = Target_Coin_Ticker + " 바이낸스 이평 조합 전략 봇 : 이평선 조건을 불만족하여 롱 포지션 종료했어요!!"
                    print(msg)
                    line_alert.SendMessage(msg)



        else:
            

            #3개의 이평선 중 가장 높은 값을 구한다!
            DolPaSt = max(Ma5,Ma10,Ma20)

            #이평선 조건을 만족하는지
            IsMaDone = False


            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때 즉 5일,10일,21일(or20)선 중 21(or20)일선이 제일 큰 값일때..
            #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
            if DolPaSt == Ma20 and coin_price >= DolPaSt:
                
                IsMaDone = True

            #그 밖의 경우는 기존 처럼 
            else:
                if PrevClose > Ma5 and PrevClose > Ma10  and PrevClose > Ma20 and Rsi < 70 and Rsi_before < Rsi:
                    IsMaDone = True



            if IsMaDone == True :


                #롱 포지션을 잡습니다.
                params = {
                    'positionSide': 'LONG'
                }
                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', Long_Amt, None, params)
                

                
                #매수했다면 매수 날짜를 기록한다.
                DateDataDict[Target_Coin_Ticker] = day_n
                #파일에 저장
                with open(date_value_file_path, 'w') as outfile:
                    json.dump(DateDataDict, outfile)

                
                
                msg = Target_Coin_Ticker + " 바이낸스 이평 조합 전략 봇 : 조건 만족 하여 롱 포지션을 잡았어요!!"

                print(msg)
                line_alert.SendMessage(msg)
                
                
            else:
                #매일 아침 9시 정각에..
                if hour_n == 0 and min_n == 0:
                    msg = Target_Coin_Ticker + " 바이낸스 이평 조합 전략 봇 : 이평선 조건 만족하지 않아 현금 보유 합니다!"
                    print(msg)
                    line_alert.SendMessage(msg)
                






    except Exception as e:
        print("error:", e)








