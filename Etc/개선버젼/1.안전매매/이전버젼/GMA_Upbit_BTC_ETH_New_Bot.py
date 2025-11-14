#-*-coding:utf-8 -*-
'''



코드 설명 참고 영상
https://youtu.be/TYj_fq4toAw?si=b3H8B_o8oU3roIWF


관련 포스팅 

업비트 안전 전략 
https://blog.naver.com/zacra/223170880153

안전 전략 개선!
https://blog.naver.com/zacra/223238532612

전략 수익률 2배로 끌어올리기
https://blog.naver.com/zacra/223456069194


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
import urllib3
import line_alert


#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)



#시간 정보를 읽는다
time_info = time.gmtime()


day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min

print("hour_n:", hour_n)
print("min_n:", min_n)

day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)






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





#봇 상태를 저장할 파일
BotDataDict = dict()

#파일 경로입니다.
botdata_file_path = "/var/autobot/Upbit_Safe_Data.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")






#최소 매수 금액
minmunMoney = 5500

#내가 가진 잔고 데이터를 다 가져온다.
balances = upbit.get_balances()

TotalMoney = myUpbit.GetTotalMoney(balances) #총 원금
TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

print("TotalMoney", TotalMoney)
print("TotalRealMoney", TotalRealMoney)
#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.7 #투자 비중은 자금사정에 맞게 수정하세요!

##########################################################################
InvestTotalMoney = TotalMoney * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
##########################################################################

print("InvestTotalMoney", InvestTotalMoney)


######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["KRW-BTC","KRW-ETH"]
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)


#'''
##########################################################################################################


######################################## 1. 균등 분할 투자 ###########################################################
'''
for coin_ticker in InvestCoinList:    
    InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!
'''
##########################################################################################################

######################################## 2. 차등 분할 투자 ###################################################
#'''
for coin_data in InvestCoinList:

    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)


    #해당 코인의 저장된 매수날짜가 없다면 디폴트 값으로 ""으로 세팅한다!
    if BotDataDict.get(coin_ticker+"_BUY_DATE") == None:
        BotDataDict[coin_ticker+"_BUY_DATE"] = ""

        #파일에 저장
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)


    #해당 코인의 저장된 매도날짜가 없다면 디폴트 값으로 ""으로 세팅한다!
    if BotDataDict.get(coin_ticker+"_SELL_DATE") == None:
        BotDataDict[coin_ticker+"_SELL_DATE"] = ""

        #파일에 저장
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)




    #체크한 기록이 없는 처음이라면 
    if BotDataDict.get(coin_ticker+"_DATE_CHECK") == None:

        #0으로 초기화!!!!!
        BotDataDict[coin_ticker+"_DATE_CHECK"] = 0
        #파일에 저장
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)


    if BotDataDict.get(coin_ticker+"_HAS") == None:
        

        if myUpbit.IsHasCoin(balances,coin_ticker) == True: 

            #보유하고 있다면 일단 전략에 의해 매수했다고 가정하자!
            BotDataDict[coin_ticker+"_HAS"] = True
            
        else:
            
            BotDataDict[coin_ticker+"_HAS"] = False
            
        #파일에 저장
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)




    InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
#'''
##########################################################################################################

    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    
    #코인별 할당된 모든 금액을 투자하는 올인 전략이니만큼 수수료를 감안하여 투자금 설정!
    InvestMoneyCell = InvestMoney * 0.995
    print("InvestMoneyCell: ", InvestMoneyCell)


    df_day = pyupbit.get_ohlcv(coin_ticker,interval="day")
    time.sleep(0.05)

    Ma3_before = myUpbit.GetMA(df_day,3,-3) 
    Ma3 = myUpbit.GetMA(df_day,3,-2)   
    Ma12 = myUpbit.GetMA(df_day,12,-2)   
    Ma24 = myUpbit.GetMA(df_day,24,-2) 
    
    Ma7_before = myUpbit.GetMA(df_day,7,-3)   
    Ma7 = myUpbit.GetMA(df_day,7,-2)   
    Ma10_before = myUpbit.GetMA(df_day,10,-3)   
    Ma10 = myUpbit.GetMA(df_day,10,-2)   
    Ma19_before = myUpbit.GetMA(df_day,19,-3)  
    Ma19 = myUpbit.GetMA(df_day,19,-2) 
    
    Ma53 = myUpbit.GetMA(df_day,53,-2) 
    
    
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()

    Ma_Last = Ma24
    if coin_ticker == 'KRW-ETH': 
        Ma_Last = Ma19

    Ma16 = myUpbit.GetMA(df_day,16,-2) 
    Ma73 = myUpbit.GetMA(df_day,73,-2) 
    
    Ma40 = myUpbit.GetMA(df_day,40,-2) 

    Ma52 = myUpbit.GetMA(df_day,52,-2) 
    

    Ma30_before = myUpbit.GetMA(df_day,30,-3) 
    Ma30 = myUpbit.GetMA(df_day,30,-2)


    Ma50_before = myUpbit.GetMA(df_day,50,-3) 
    Ma50 = myUpbit.GetMA(df_day,50,-2)
    
    Rsi_before = myUpbit.GetRSI(df_day,14,-3) 
    Rsi = myUpbit.GetRSI(df_day,14,-2) 


    ########## RSI 지표 구하는 로직! ##########
    period = 14

    delta = df_day["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss

    df_day['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    ########################################

    df_day['rsi_ma'] = df_day['rsi'].rolling(10).mean()
    
    RsiMa_before  = df_day['rsi_ma'].iloc[-3]
    RsiMa  = df_day['rsi_ma'].iloc[-2]


    PrevClose = df_day['close'].iloc[-2]

    #현재가를 구하다
    NowCurrentPrice = pyupbit.get_current_price(coin_ticker)


    #잔고가 있는 경우.
    if BotDataDict[coin_ticker+"_HAS"] == True and myUpbit.IsHasCoin(balances,coin_ticker) == True:
        print("잔고가 있는 경우!")

        #수익금과 수익률을 구한다!
        revenue_data = GetRevenueMoneyAndRate(balances,coin_ticker)


        IsSellGo = False


    
        IsDolpaCut = False
        if coin_ticker == 'KRW-ETH':

            CutPrice = Ma7
            


            if df_day['rsi'].iloc[-2] >= 70 and NowCurrentPrice <= CutPrice and df_day['open'].iloc[-1] > CutPrice :
                IsSellGo = True
                IsDolpaCut = True


        if BotDataDict[coin_ticker+"_DATE_CHECK"] != day_n:
            
            msg = coin_ticker + "현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
            print(msg)
            line_alert.SendMessage(msg)

            time.sleep(1.0)

            if coin_ticker == 'KRW-ETH':

                if PrevClose > Ma53:

                    if Ma7 > PrevClose and Ma10 > PrevClose:

                        IsSellGo = True

                    
                else:
                    if Ma7 > PrevClose or (df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) :
                        IsSellGo = True

                
            else:
                if ((df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) or (df_day['open'].iloc[-2] > df_day['close'].iloc[-2] and df_day['open'].iloc[-3] > df_day['close'].iloc[-3])  ) or revenue_data['revenue_rate'] < -0.7  :
                    IsSellGo = True

                if RsiMa_before < RsiMa and Ma3_before < Ma3:
                    IsSellGo = False




            BotDataDict[coin_ticker+"_DATE_CHECK"] = day_n
            #파일에 저장
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)




        #저장된 매수날짜와 오늘 날짜가 같다면.. 오늘 돌파 매수던 시가 매수던 매수가 된 상황이니깐 오늘은 매도 하면 안된다.
        if BotDataDict[coin_ticker+"_BUY_DATE"] == day_str:
            IsSellGo = False


        if IsSellGo == True:

            AllAmt = upbit.get_balance(coin_ticker) #현재 수량

            balances = myUpbit.SellCoinMarket(upbit,coin_ticker,AllAmt)

            if IsDolpaCut == True:
                msg = coin_ticker + " 업비트 안전 전략 봇 : 조건을 하향 돌파 불만족하여 모두 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                line_alert.SendMessage(msg)
            else:
                            
                msg = coin_ticker + " 업비트 안전 전략 봇 : 조건을 불만족하여 모두 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                line_alert.SendMessage(msg)

            BotDataDict[coin_ticker+"_HAS"] = False
            #매도했다면 매도 날짜를 기록한다.
            BotDataDict[coin_ticker+"_SELL_DATE"] = day_str
            #파일에 저장
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)
            


    else:
        print("아직 투자하지 않음")

        #이평선 조건을 만족하는지
        IsMaDone = False

        if coin_ticker == 'KRW-ETH':
            

            #3개의 이평선 중 가장 높은 값을 구한다!
            DolPaSt = max(Ma7,Ma10,Ma_Last)


            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때 
            #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
            if DolPaSt == Ma_Last and NowCurrentPrice >= DolPaSt:
                
            
                if Rsi_before < Rsi and RsiMa_before < RsiMa:
                    IsMaDone = True
                    


            #그 밖의 경우는 기존 처럼 
            else:
                if PrevClose > Ma7 and PrevClose > Ma10  and PrevClose > Ma_Last and Rsi_before < Rsi  and RsiMa_before < RsiMa:
                    IsMaDone = True
                    


            if IsMaDone == False:

                print("변돌 체크!")

                DolpaRate = 0.7

                if Ma_Last < PrevClose:
                    DolpaRate = 0.6

                if Ma7_before < Ma7 and Ma10_before < Ma10 and  Ma19_before < Ma19 and Ma19 < Ma10 < Ma7:
                    DolpaRate = 0.5


                DolPaSt = df_day['open'].iloc[-1] + (( df_day['high'].iloc[-2] - df_day['low'].iloc[-2]) * DolpaRate)

                if NowCurrentPrice >= DolPaSt and RsiMa_before < RsiMa and Ma7_before < Ma7:

                    IsMaDone = True

    

        else:
            

            #3개의 이평선 중 가장 높은 값을 구한다!
            DolPaSt = max(Ma3,Ma12,Ma_Last)


            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때 
            #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
            if DolPaSt == Ma_Last and NowCurrentPrice >= DolPaSt:
            
        
                IsMaDone = True
                    

            #그 밖의 경우는 기존 처럼 
            else:

                if df_day['open'].iloc[-2] < df_day['close'].iloc[-2] and df_day['open'].iloc[-3] < df_day['close'].iloc[-3] and df_day['close'].iloc[-3] < df_day['close'].iloc[-2]   and df_day['high'].iloc[-3] < df_day['high'].iloc[-2] and Ma7_before < Ma7 and Ma16 < df_day['close'].iloc[-2] and Ma73 < df_day['close'].iloc[-2] :
                        
                    IsMaDone = True
                    

            if IsMaDone == False:
                print("변돌 체크!")

                DolpaRate = 0.7

                DolPaSt = df_day['open'].iloc[-1] + ( ( max(df_day['high'].iloc[-3],df_day['high'].iloc[-2]) - min(df_day['low'].iloc[-2],df_day['low'].iloc[-3]) ) * DolpaRate)

                if NowCurrentPrice >= DolPaSt and RsiMa_before < RsiMa and df_day['low'].iloc[-3] < df_day['low'].iloc[-2] and Ma12 < PrevClose and Ma24 < Ma12 < Ma3:
                    IsMaDone = True



        #저장된 매도날짜와 오늘 날짜가 같다면.. 매도가 된 상황이니깐 오늘은 매수 하면 안된다.
        if BotDataDict[coin_ticker+"_SELL_DATE"] == day_str:
            IsMaDone = False



        if IsMaDone == True :

            Rate = 1.0


            ########################################################################################################
            #''' 이 부분을 주석처리 하면 감산 로직이 제거 됩니다 
            if coin_ticker == 'KRW-ETH':
                if Ma30_before > Ma30 or Ma52 > df_day['close'].iloc[-2]:
                    Rate *= 0.5

            else:
    
                if Ma50_before > Ma50 or Ma40 > df_day['close'].iloc[-2]:
                    Rate *= 0.5
            #'''
            ########################################################################################################



            BuyGoMoney = InvestMoneyCell * Rate

            if BuyGoMoney >= df_day['value_ma'].iloc[-2] / 2000:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 2000

            BuyMoney = BuyGoMoney 

            #원화 잔고를 가져온다
            won = float(upbit.get_balance("KRW"))
            print("# Remain Won :", won)
            time.sleep(0.004)
            
            #
            if BuyMoney > won:
                BuyMoney = won *0.99

            
            if BuyMoney >= minmunMoney:

                balances = myUpbit.BuyCoinMarket(upbit,coin_ticker,BuyMoney)

                BotDataDict[coin_ticker+"_HAS"] = True
                #매수했다면 매수 날짜를 기록한다.
                BotDataDict[coin_ticker+"_BUY_DATE"] = day_str
                #파일에 저장
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)
            
                msg = coin_ticker + " 업비트 안전 전략 봇 :  조건 만족 하여 매수!! " + str(BuyMoney) + "원어치 매수!"

                print(msg)
                line_alert.SendMessage(msg)
            
        else:
            #매일 아침 9시 정각에..
            if hour_n == 0 and min_n <= 2:
                msg = coin_ticker + " 업비트 안전 전략 봇 :  조건 만족하지 않아 현금 보유 합니다!"
                print(msg)
                line_alert.SendMessage(msg)
            














