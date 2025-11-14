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

바이낸스 선물 비트 도미 전략 V2
https://blog.naver.com/zacra/223481445047

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


#오늘 매매를 했는지 날짜를 저장해 둔다!
DateDataDict = dict()

#파일 경로입니다.
date_value_file_path = "/var/autobot/BinanceBTC_DOM_DateInfoV2.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(date_value_file_path, 'r') as json_file:
        DateDataDict = json.load(json_file)

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



        #체크한 기록이 없는 처음이라면 
        if DateDataDict.get(Target_Coin_Ticker) == None:

            #0으로 초기화!!!!!
            DateDataDict[Target_Coin_Ticker] = 0
            #파일에 저장
            with open(date_value_file_path, 'w') as outfile:
                json.dump(DateDataDict, outfile)

                    




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

        Buy_Amt = Max_Amt / 2.0 #롱과 숏을 나눠야되니깐!
        Long_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker,Buy_Amt))
        Short_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker,Buy_Amt))

        print("Long_Amt Short_Amt", Long_Amt, Short_Amt)

        df_day = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '1d')



        Ma10 = myBinance.GetMA(df_day,10,-2)  
        Ma10_before = myBinance.GetMA(df_day,10,-3)  
        
        Ma35 = myBinance.GetMA(df_day,35,-2) 
        Ma35_before = myBinance.GetMA(df_day,35,-3)  

        Ma45 = myBinance.GetMA(df_day,45,-2) 
        Ma45_before = myBinance.GetMA(df_day,45,-3)  

        Ma75 = myBinance.GetMA(df_day,75,-2) 
        Ma75_before = myBinance.GetMA(df_day,75,-3)  


        Ma110 = myBinance.GetMA(df_day,110,-2) 
        Ma110_before = myBinance.GetMA(df_day,110,-3)  

        PrevClose = df_day['close'].iloc[-2]



            
        #매도 체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
        if DateDataDict[Target_Coin_Ticker] != day_n:

            #매도로직 안으로 들어왔다면 날자를 바꿔준다!!
            DateDataDict[Target_Coin_Ticker] = day_n
            #파일에 저장
            with open(date_value_file_path, 'w') as outfile:
                json.dump(DateDataDict, outfile)
                
            
    
            #롱 포지션이 있다면..
            if abs(amt_b) > 0:

                revenue_rate_b = (coin_price - entryPrice_b) / entryPrice_b * 100.0


                unrealizedProfit_b = 0 #미 실현 손익.

                #롱 잔고
                for posi in balance['info']['positions']:
                    if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':

                        unrealizedProfit_b = float(posi['unrealizedProfit'])
                        break

                msg = Target_Coin_Ticker + "현재 롱 수익률 : 약 " + str(round(revenue_rate_b*set_leverage,2)) + "% 수익금 : 약" + str(round(unrealizedProfit_b,2)) + "USDT"
                print(msg)
                line_alert.SendMessage(msg)
                
                IsLongCloseGo = False
                if (PrevClose < Ma45 and Ma45_before > Ma45) or (PrevClose < Ma110 and Ma110_before > Ma110):
                    IsLongCloseGo = True
                    
                    
                if IsLongCloseGo == True:
                    
                    #롱 포지션 종료!!
                    params = {
                        'positionSide': 'LONG'
                    }
                    print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b), None, params))
                    
                    msg = Target_Coin_Ticker + " 바이낸스 비트 도미 전략 봇 : 조건을 불만족하여 롱 포지션 종료했어요!!"
                    print(msg)
                    line_alert.SendMessage(msg)
                             
            #롱 포지션이 없다면
            else:
                IsLongOpenGo = False
                if (PrevClose >= Ma45 and Ma45_before <= Ma45) and (PrevClose >= Ma110 and Ma110_before <= Ma110):
                    IsLongOpenGo = True
                    
                if IsLongOpenGo == True:

                    #롱 포지션을 잡습니다.
                    params = {
                        'positionSide': 'LONG'
                    }
                    data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', Long_Amt, None, params)
                


                    msg = Target_Coin_Ticker + " 바이낸스 비트 도미 전략 봇 : 조건 만족 하여 롱 포지션을 잡았어요!!"

                    print(msg)
                    line_alert.SendMessage(msg)
                    
                
            #숏 포지션이 있다면
            if abs(amt_s) > 0:


                unrealizedProfit_s = 0 #미 실현 손익.

                print("------")
                #숏잔고
                for posi in balance['info']['positions']:
                    if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'SHORT':

                        unrealizedProfit_s = float(posi['unrealizedProfit'])
                        break
            
                #숏 수익율을 구한다!
                revenue_rate_s = (entryPrice_s - coin_price) / entryPrice_s * 100.0



                msg = Target_Coin_Ticker + "현재 숏 수익률 : 약 " + str(round(revenue_rate_s*set_leverage,2)) + "% 수익금 : 약" + str(round(unrealizedProfit_s,2)) + "USDT"
                print(msg)
                line_alert.SendMessage(msg)

                
                IsShortCloseGo = False
                
                if Target_Coin_Ticker == "BTCDOM/USDT":
                    if (PrevClose > Ma10 or Ma10_before < Ma10) or (PrevClose > Ma35 or Ma35_before < Ma35):
                        IsShortCloseGo = True
                else:
                    if (PrevClose > Ma35 or Ma35_before < Ma35) or (PrevClose > Ma75 or Ma75_before < Ma75):
                        IsShortCloseGo = True
                    
                if IsShortCloseGo == True:

                    params = {
                        'positionSide': 'SHORT'
                    }
                    print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params))

                    msg = Target_Coin_Ticker + " 바이낸스 비트 도미 전략 봇 : 조건을 불만족하여 숏 포지션 종료했어요!!"

                    print(msg)
                    line_alert.SendMessage(msg)
                    

            #숏 포지션이 없다면
            else:

                IsShortOpenGo = False
                
                if Target_Coin_Ticker == "BTCDOM/USDT":
                    if (PrevClose <= Ma10 and Ma10_before >= Ma10) and (PrevClose <= Ma35 and Ma35_before >= Ma35):
                        IsShortOpenGo = True
                else:
                    if (PrevClose <= Ma35 and Ma35_before >= Ma35) and (PrevClose <= Ma75 and Ma75_before >= Ma75):
                        IsShortOpenGo = True
                    
                    
                    
                if IsShortOpenGo == True:

                    #숏 포지션을 잡습니다.
                    params = {
                        'positionSide': 'SHORT'
                    }
                    data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', Short_Amt, None, params)


                    msg = Target_Coin_Ticker + " 바이낸스 비트 도미 전략 봇 : 조건 만족 하여 숏 포지션을 잡았어요!!"

                    print(msg)
                    line_alert.SendMessage(msg)


    except Exception as e:
        print("error:", e)








