#-*-coding:utf-8 -*-
'''

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

바이낸스 ccxt 버전
pip3 install --upgrade ccxt==4.2.19
이렇게 버전을 맞춰주세요!

봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요!
https://blog.naver.com/zacra/222662884649

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

관련 포스팅
https://blog.naver.com/zacra/223407795261

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

저는 이 코드를 그대로 사용하지 않고 계속 개선해서 사용하고 있습니다.
https://blog.naver.com/zacra/223431213877
헤지의 세계로 빠져들어 공부해 보세요 ^^!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

'''
import myUpbit   
import myBinance
import ccxt
import pyupbit

import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키
import pandas as pd
import pprint
import json
import line_alert
import time


#시간 정보를 가져옵니다. 아침 9시의 경우 서버에서는 hour변수가 0이 됩니다.
time_info = time.gmtime()
hour_time = time_info.tm_hour
min_time = time_info.tm_min
print(hour_time, min_time)


##############################################################################
#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)


UpbitBalances = upbit.get_balances() #업비트 잔고 읽기!




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


#잔고 데이타 가져오기 
BinanceBalance = binanceX.fetch_balance(params={"type": "future"})       
print(BinanceBalance['USDT'])
##############################################################################

BOT_NAME = "[업비트 위험관리 바이낸스 헤지 봇!] "
##############################################################################
##############################################################################
#헤지 비율! 얼마큼을 헤지할 것인지
#0.8이라면 업비트 100만원어치 평가금의 80%인 80만원만 헤지함(숏 포지션 잡음)
#1.0이면 100% 롱과 같은 금액으로 헤지!
#바이낸스 자금 상황에 따라서 또는 생각하는 헤지 비율에 따라서 조절!
HEDGE_RATE = 0.8

#사용할 레버리지
set_leverage = 20

#환율
EXCHANGE_RATE = 1300


#만약 미국 주식 자동매매를 하시는 분은 아래 코드를 활용하면 현재 환율을 가져올 수 있음!
'''
import KIS_Common as Common
import KIS_API_Helper_US as KisUS

#모의계좌에서 환율이 안나오면 실제 사용하는 미국주식 실계좌로 바꾸세요 (ex. REAL)
Common.SetChangeMode("VIRTUAL") 
ex_rate = KisUS.GetExrt()

if ex_rate != None:
    EXCHANGE_RATE = float(ex_rate)
    
print("설정된 환율 ", EXCHANGE_RATE)
'''
##############################################################################
##############################################################################


#헤지 관리중인 코인 티커가 들어간다!!
HedgeCoinList = list()

#파일 경로입니다.
hedgecoinlist_type_file_path = "/var/autobot/UpbitDefence_HedgeCoinList.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(hedgecoinlist_type_file_path, 'r') as json_file:
        HedgeCoinList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")
    
    
#헤지 관리중인 코인 티커가 들어간다!!
UpTrendCheckDict = dict()

#파일 경로입니다.
uptrendcheck_type_file_path = "/var/autobot/UpbitDefence_UptrendCheck.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(uptrendcheck_type_file_path, 'r') as json_file:
        UpTrendCheckDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")


#바이낸스 수익률 관리 정보가 들어간다!!
RevenueCheckDict = dict()

#파일 경로입니다.
revenuecheck_type_file_path = "/var/autobot/UpbitDefence_RevenueCheck.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(revenuecheck_type_file_path, 'r') as json_file:
        RevenueCheckDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")






##############################################################################
##############################################################################
#### 헤지중인 코인 종료각을 잰다! ####


items_to_remove = list()
    
for binance_ticker in HedgeCoinList:
    
    Target_Coin_Ticker = binance_ticker
    Target_Coin_Symbol = binance_ticker.replace("/", "").replace(":USDT", "")
    
    
    amt_s = 0 
    entryPrice_s = 0 

    print("------")
    #숏잔고
    for posi in BinanceBalance['info']['positions']:
        if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'SHORT':
            print(posi)
            amt_s = float(posi['positionAmt'])
            entryPrice_s= float(posi['entryPrice'])
            break
        
    if abs(amt_s) == 0:
        
        msg = BOT_NAME + Target_Coin_Ticker + " 헤지를 위한 숏포지션 종료가 확인되었어요!!!"
        print(msg)
        line_alert.SendMessage(msg)

        items_to_remove.append(Target_Coin_Ticker)  
        
    else:
        
        coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker) #현재 코인가격
        minimun_amount = myBinance.GetMinimumAmount(binanceX,Target_Coin_Ticker) #최소주문수량
        
        #숏 수익율을 구한다!
        revenue_rate_s = (entryPrice_s - coin_price) / entryPrice_s * 100.0
        print("헤지 중...", Target_Coin_Ticker, " 바이낸스 수익률 : ", revenue_rate_s)
        
        #업비트 티커를 구해보자!
        upbit_ticker = "KRW-"+ binance_ticker.replace("/USDT:USDT", "")
        
        
        #업비트 잔고가 있는경우...
        if myUpbit.IsHasCoin(UpbitBalances,upbit_ticker) == True:
            print("업비트에 롱...")
            
            revenue_rate = myUpbit.GetRevenueRate(UpbitBalances,upbit_ticker)
            print("업비트 수익률 : ", str(round(revenue_rate,2)) + "%")
            
            if revenue_rate > 0:
                print("숏포지션이 있는데 업비트의 롱 포지션 수익률이 수익권이다! 헤지 종료! 숏 포지션 종료!!!")
    
                
                params = {
                    'positionSide': 'SHORT'
                }
                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params))            

        
                msg = BOT_NAME + upbit_ticker + "수익률이 0 이상 수익권!!! 숏 포지션 모두 종료!!"
                print(msg)
                line_alert.SendMessage(msg)
                    
            
            else:
                print("상승 추세를 확인해본다!")
                
                #혹시 모를 예외를 위해 상승추세 데이터가 없으면 READY로 초기화 해준다!!
                if Target_Coin_Ticker not in UpTrendCheckDict.keys():
                    UpTrendCheckDict[Target_Coin_Ticker] = "READY"
                    
                
                if min_time % 15 == 0: 
                    
                    #캔들 데이터를 가지고 온다!
                    df = pyupbit.get_ohlcv(upbit_ticker,interval="minute15") #업비트의 15분봉을 가져온다!
                    #df = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '15m') #바이낸스의 15분봉을 가져온다!
                    
                    IS_TEST = True

                    print("시가:", df['open'].iloc[-2], " 종가:",df['close'].iloc[-2])
                    #이전 캔들이 시가보다 종가가 큰 양봉이었다!!! 
                    if df['close'].iloc[-2] > df['open'].iloc[-2]:
                
                        #10이동평균선!
                        df['ma10'] = df['close'].rolling(window=10).mean()
                        
                        print("MA10:", df['ma10'].iloc[-2])
                        #10이평선보다 이전 종가가 크다!
                        if df['close'].iloc[-2] > df['ma10'].iloc[-2] :

                            #MACD는 보통 12, 26, 9를 사용한다!
                            macd_short, macd_long, macd_signal=12,26,9

                            df["MACD_short"]=df["close"].ewm(span=macd_short).mean()
                            df["MACD_long"]=df["close"].ewm(span=macd_long).mean()
                            
                            df["MACD"]=df["MACD_short"] - df["MACD_long"] #MACD
                            df["Signal"]=df["MACD"].ewm(span=macd_signal).mean() #MACD시그널!
                            
                            
                            print("MACD:", df['MACD'].iloc[-3],"->",df['MACD'].iloc[-2])
                            print("Signal:", df['Signal'].iloc[-3],"->",df['Signal'].iloc[-2])
                            
                            if (df['MACD'].iloc[-2] > df['Signal'].iloc[-2] and df['MACD'].iloc[-3] < df['MACD'].iloc[-2] and df['Signal'].iloc[-3] < df['Signal'].iloc[-2])  :
                                print("!!!! 상승추세 확정 !!!!!")
                                if UpTrendCheckDict[Target_Coin_Ticker] == "READY":
                                    
                                    TotalCutAmt = abs(amt_s)* 0.5
                                    

                                    if float(minimun_amount) > TotalCutAmt:
                                        TotalCutAmt = float(minimun_amount)

                                    TotalCutAmt = binanceX.amount_to_precision(Target_Coin_Ticker,TotalCutAmt)
                                                    
                                    
                                    if abs(amt_s) > float(minimun_amount) * 2.0:
                                            
                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', TotalCutAmt, None, params))            

                                
                                        msg = BOT_NAME + upbit_ticker + "상승추세 확인됨! 전체 포지션의 절반을 정리!!!"  + str(round(revenue_rate_s,2)) + "%"
                                        print(msg)
                                        line_alert.SendMessage(msg)
                                        
                                    else:
                                        
                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params))            

                                
                                        msg = BOT_NAME + upbit_ticker + "상승추세 확인됨! 전체 포지션 정리!!!"  + str(round(revenue_rate_s,2)) + "%"
                                        print(msg)
                                        line_alert.SendMessage(msg)
                                        
                                        
                                    UpTrendCheckDict[Target_Coin_Ticker] = "DONE"

                                    with open(uptrendcheck_type_file_path, 'w') as outfile:
                                        json.dump(UpTrendCheckDict, outfile)     
                                           
                                else:
                                    
                                    #if UpTrendCheckDict[Target_Coin_Ticker] == "DONE":
                                    print("이 부분은 상승추세에 의해 절반 익절을 했는데 계속 상승추세여서 숏포지션을 15분마다 10%씩 줄여주는 부분!")
                            
                                    CloseAmt = abs(amt_s) / 10.0 
                                    
                                    if float(minimun_amount) > CloseAmt:
                                        CloseAmt = float(minimun_amount)
                                        
                                    if abs(amt_s) > float(minimun_amount) * 2.0:
                                        
                                        CloseAmt = float(binanceX.amount_to_precision(Target_Coin_Ticker,CloseAmt))
                                        
                                        #일부 종료!
                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', CloseAmt, None, params))          
                                        

                                        msg = BOT_NAME + Target_Coin_Ticker + " 상승 추세 지속에 의한 일부 정리!!!!!! " + str(round(revenue_rate_s,2)) + "%"
                                        print(msg)
                                        line_alert.SendMessage(msg)
                                        
                                    else:
            
                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params))          
                                        

                                        msg = BOT_NAME + Target_Coin_Ticker + " 상승 추세 지속에 정리로 모두 종료!!!!!!!! " + str(round(revenue_rate_s,2)) + "%"
                                        print(msg)
                                        line_alert.SendMessage(msg)

                else:
   
                    print("캔들이 갱신되지 않아 신규 숏 집입 체크를 하지 않아용 ^^")
                              
                
                if Target_Coin_Ticker not in RevenueCheckDict.keys():
                    RevenueCheckDict[Target_Coin_Ticker] = 1.0

                    with open(revenuecheck_type_file_path, 'w') as outfile:
                        json.dump(RevenueCheckDict, outfile)  
                        
                #상승추세 발견 전! 업비트 코인 매수중.. 숏포지션 수익중... 10%까지 가기 전
                if UpTrendCheckDict[Target_Coin_Ticker] == "READY" and revenue_rate_s > 0 and RevenueCheckDict[Target_Coin_Ticker] <= 10.0:

        
                    #목표 수익률보다 더 크다면 1/20 씩 즉 5%씩 종료!!!
                    if RevenueCheckDict[Target_Coin_Ticker] < revenue_rate_s:
                        
                        RevenueCheckDict[Target_Coin_Ticker] += 1.0
                        
                        with open(revenuecheck_type_file_path, 'w') as outfile:
                            json.dump(RevenueCheckDict, outfile)  
                            
                        CloseAmt = abs(amt_s) / 20.0 
                        
                        if float(minimun_amount) > CloseAmt:
                            CloseAmt = float(minimun_amount)
                            
                        if abs(amt_s) > float(minimun_amount) * 2.0:
                            
                                
                            CloseAmt = float(binanceX.amount_to_precision(Target_Coin_Ticker,CloseAmt))
                                
                            #절반은 바로 종료!
                            params = {
                                'positionSide': 'SHORT'
                            }
                            print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', CloseAmt, None, params))          
                            

                            msg = BOT_NAME + Target_Coin_Ticker + " 숏 수익률 갱신에 의한 일부 익절!!!!!! " + str(round(revenue_rate_s,2)) + "%"
                            print(msg)
                            line_alert.SendMessage(msg)
                            
                        else:
                            print("포지션 수량이 많이 없어서 부분 익절은 생략!!!")
                                    
                            
                      
        else:
            print("숏포지션이 있는데 업비트의 롱 포지션이 없다? 헤지 중단!! 숏 포지션 종료!!!")
            

            params = {
                'positionSide': 'SHORT'
            }
            print(binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params))            

    
            msg = BOT_NAME + upbit_ticker + "매도 확인됨! 숏 포지션 모두 종료!!"
            print(msg)
            line_alert.SendMessage(msg)
            

         
print(len(items_to_remove))
if len(items_to_remove) > 0:
    
    #리스트에서 제거
    for item in items_to_remove:
        HedgeCoinList.remove(item)
        if UpTrendCheckDict[Target_Coin_Ticker] == "DONE":
            UpTrendCheckDict[Target_Coin_Ticker] = "NONE"
        
    #파일에 저장
    with open(hedgecoinlist_type_file_path, 'w') as outfile:
        json.dump(HedgeCoinList, outfile)

    with open(uptrendcheck_type_file_path, 'w') as outfile:
        json.dump(UpTrendCheckDict, outfile)  
        
##############################################################################
##############################################################################







##############################################################################
##############################################################################
#### 헤지할 신규 코인 물색 ####

if min_time % 15 == 0 : #15분봉을 보기에 15분에만 신규로 숏 포지션 잡을 로직이 동작한다!!

    UpbitTickers = pyupbit.get_tickers("KRW") #업비트 모든 코인 리스트 얻기!


    BinanceTickers = list() #바이낸스에 있는 모든 선물 코인 리스트 얻기  

    tickers_prev = binanceX.fetch_tickers()
    for ticker, coin_Data in tickers_prev.items():
        if "/USDT" in ticker and "-" not in ticker:
            #print(ticker ,"added")
            BinanceTickers.append(ticker)
            
            
    #전체를 순회하면서
    for upbit_ticker in UpbitTickers:
        
        #업비트에서 매수된 코인이다!
        if myUpbit.IsHasCoin(UpbitBalances,upbit_ticker) == True:
            
            print("업비트에서 현재 매수(롱) 중인 코인 : ", upbit_ticker)
            
            revenue_rate = myUpbit.GetRevenueRate(UpbitBalances,upbit_ticker)
            print("수익률 : ", str(round(revenue_rate,2)) + "%")
            
            
            if revenue_rate >= 0:
                print("수익률 마이너스만 헤지 대상! 넌 아직 괜찮아 ㅎ")
                
            else:
            
                #업비트에서 매수한 코인의 현재 평가금액 기준!
                UpbitMoney = myUpbit.GetCoinNowRealMoney(UpbitBalances,upbit_ticker)
                #업비트에서 매수한 코인의 매수금액 기준!
                #UpbitMoney = myUpbit.GetCoinNowMoney(UpbitBalances,upbit_ticker)
                print("업비트 금액(헤지 대상 금액) : ", str(round(UpbitMoney,2)) + "원")
            
                
                Temp_Ticker = upbit_ticker.replace("KRW-", "") + "/USDT"
                print("찾기!! ", Temp_Ticker)
                #바이낸스에서 해당하는 코인이 있는지 찾는다!
                for binance_ticker in BinanceTickers:
                    #찾을 티커가 포함된 바이낸스 선물 티커를 찾았다!!
                    if Temp_Ticker in binance_ticker:
                        print("찾았다!", binance_ticker)
                        
                        Target_Coin_Ticker = binance_ticker
                        Target_Coin_Symbol = binance_ticker.replace("/", "").replace(":USDT", "")
                        
                        
                        #캔들 데이터를 가지고 온다!
                        df = pyupbit.get_ohlcv(upbit_ticker,interval="minute15") #업비트의 15분봉을 가져온다!
                        #df = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, '15m') #바이낸스의 15분봉을 가져온다!
                        
                        print("시가:", df['open'].iloc[-2], " 종가:",df['close'].iloc[-2])
                        #이전 캔들이 종가보다 시가가 큰 음봉이었다!!! 
                        if df['close'].iloc[-2] < df['open'].iloc[-2] :
                        
                            #10이동평균선!
                            df['ma10'] = df['close'].rolling(window=10).mean()
                            
                            print("MA10:", df['ma10'].iloc[-2])
                            #10이평선보다 이전 종가가 작았다!
                            if df['close'].iloc[-2] < df['ma10'].iloc[-2] :
                                
                                
                                #MACD는 보통 12, 26, 9를 사용한다!
                                macd_short, macd_long, macd_signal=12,26,9

                                df["MACD_short"]=df["close"].ewm(span=macd_short).mean()
                                df["MACD_long"]=df["close"].ewm(span=macd_long).mean()
                                
                                df["MACD"]=df["MACD_short"] - df["MACD_long"] #MACD
                                df["Signal"]=df["MACD"].ewm(span=macd_signal).mean() #MACD시그널!
                                
                                
                                print("MACD:", df['MACD'].iloc[-3],"->",df['MACD'].iloc[-2])
                                print("Signal:", df['Signal'].iloc[-3],"->",df['Signal'].iloc[-2])
                                
                                if (df['MACD'].iloc[-2] < df['Signal'].iloc[-2] and df['MACD'].iloc[-3] > df['MACD'].iloc[-2] and df['Signal'].iloc[-3] > df['Signal'].iloc[-2]) :
                                    print("!!!! 헤지 확정 !!!!!")
                                    
                                    #잔고 데이타 가져오기 
                                    BinanceBalance = binanceX.fetch_balance(params={"type": "future"})              

                                    amt_s = 0 
                                    entryPrice_s = 0 
                                    leverage = 0
                                    isolated = True #격리모드인지 


                                    print("------")
                                    #숏잔고
                                    for posi in BinanceBalance['info']['positions']:
                                        if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'SHORT':
                                            print(posi)
                                            amt_s = float(posi['positionAmt'])
                                            entryPrice_s= float(posi['entryPrice'])
                                            leverage = float(posi['leverage'])
                                            isolated = posi['isolated']
                                            break


                                    #################################################################################################################
                                    #레버리지 셋팅
                                    if leverage != set_leverage:
                                            
                                        try:
                                            binanceX.fapiPrivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage})
                                        except Exception as e:
                                            try:
                                                binanceX.fapiprivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage})
                                            except Exception as e:
                                                print("Exception..Done")

                                    #################################################################################################################


                                    #################################################################################################################
                                    #격리 모드로 설정
                                    if isolated == False:
                                        try:
                                            binanceX.fapiPrivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'ISOLATED'})
                                        except Exception as e:
                                            try:
                                                binanceX.fapiprivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'ISOLATED'})
                                            except Exception as e:
                                                print("Exception..Done")
                                                

                                    #혹시나 남은 USDT보다 큰 금액이라면 보정해준다!
                                    Remain_usdt = float(BinanceBalance['USDT']['free'])
                                    
                                    if Remain_usdt < 5.0:
                                        msg = BOT_NAME + "헤지하기 위해 남은 바이낸스 잔고가 부족합니다 최소 5USDT 이상이 남아있게 해주세용!"
                                        print(msg)
                                        line_alert.SendMessage(msg)
                                        
                                        break
                                    
                                    
                                    if abs(amt_s) == 0: #숏 포지션이 아직 없어야 한다!
                                        
                                        Hdege_usdt = ((UpbitMoney / EXCHANGE_RATE) / float(set_leverage)) * HEDGE_RATE
                                        print("헤지시 필요한 금액(USDT)", Hdege_usdt)
                                        
                                        
                                        if Remain_usdt < Hdege_usdt:
                                            Hdege_usdt = Remain_usdt * 0.95
                                            
                                        
                                        coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)
                                        
                                        Hedge_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(Hdege_usdt,coin_price,1.0)* float(set_leverage))) 
                                        
                                        
                                        #만약 최소 주문수량의 2배보다 적은 경우 보정!
                                        minimun_amount = myBinance.GetMinimumAmount(binanceX,Target_Coin_Ticker)
                                        if Hedge_Amt < float(minimun_amount) * 2.0:
                                            Hedge_Amt = float(minimun_amount) * 2.0
                                            
                                        print("숏포지션 잡을 총 수량 : ", Hedge_Amt)
                                        
                                        
                                        #숏 포지션을 잡습니다.
                                        params = {
                                            'positionSide': 'SHORT'
                                        }
                                        data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', Hedge_Amt, None, params)


                                        msg = BOT_NAME + upbit_ticker + " 코인을 " + Target_Coin_Ticker + "로 헤지 시작합니다!"
                                        print(msg)
                                        line_alert.SendMessage(msg)
                                        
                                        #헤지한 바이낸스 티커를 저장해 둔다!! 이후 종료를 위해!!!!!!
                                        HedgeCoinList.append(Target_Coin_Ticker)
                                        
                                        with open(hedgecoinlist_type_file_path, 'w') as outfile:
                                            json.dump(HedgeCoinList, outfile)  
                                            
                                            
                                        #상승추세에 의한 종료를 1번으로 제한하기 위해서!!
                                        UpTrendCheckDict[Target_Coin_Ticker] = "READY"
                                        
                                        with open(uptrendcheck_type_file_path, 'w') as outfile:
                                            json.dump(UpTrendCheckDict, outfile)  
                                            
                                            
                                        #익절 관리..
                                        RevenueCheckDict[Target_Coin_Ticker] = 1.0
                                        
                                        with open(revenuecheck_type_file_path, 'w') as outfile:
                                            json.dump(RevenueCheckDict, outfile)  
                                                                    
                             
                        print("=========================================\n")           
                        
                        break
                        
                    
else:
    print("캔들이 갱신되지 않아 신규 숏 집입 체크를 하지 않아용 ^^")              
            
##############################################################################
##############################################################################

