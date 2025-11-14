#-*-coding:utf-8 -*-
'''



코드 설명 참고 영상
https://youtu.be/TYj_fq4toAw?si=b3H8B_o8oU3roIWF


관련 포스팅  
https://blog.naver.com/zacra/223325119533

최근 마지막 수정 포스팅
https://blog.naver.com/zacra/223805709477

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

TotalMoeny = myUpbit.GetTotalMoney(balances) #총 원금
TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

print("TotalMoeny", TotalMoeny)
print("TotalRealMoney", TotalRealMoney)
#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.7 #투자 비중은 자금사정에 맞게 수정하세요!

##########################################################################
InvestTotalMoney = TotalMoeny * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
##########################################################################

print("InvestTotalMoney", InvestTotalMoney)


######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["KRW-BTC","KRW-ETH"]
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()


############################# FixV ####################################
InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.4     #전략에 의해 사고파는 비중 40%
InvestDataDict['fix_rate'] = 0.1 #고정 비중 10% 할당!
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.4      #전략에 의해 사고파는 비중 40%
InvestDataDict['fix_rate'] = 0.1  #고정 비중 10% 할당!
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



    ############################# FixV ####################################
    #체크한 기록이 없는 처음이라면 
    if BotDataDict.get(coin_ticker+"_HAS") == None:
        

        StrategyBuyDict = dict()

        #파일 경로입니다.
        strategybuy_file_path = "/var/autobot/UpbitNewStrategyBuy.json"
        try:
            #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
            with open(strategybuy_file_path, 'r') as json_file:
                StrategyBuyDict = json.load(json_file)

            #여기까지 탔다면 기존에 저 파일에 저장된 내용이 있다는 것! 그것을 읽어와서 세팅한다!
            BotDataDict[coin_ticker+"_HAS"] = StrategyBuyDict[coin_ticker]

        except Exception as e:

            if myUpbit.IsHasCoin(balances,coin_ticker) == True: 

                #보유하고 있다면 일단 전략에 의해 매수했다고 가정하자!
                BotDataDict[coin_ticker+"_HAS"] = True
                
            else:
                
                BotDataDict[coin_ticker+"_HAS"] = False
                
        #파일에 저장
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)



    InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
    
    ############################# FixV ####################################
    InvestFixMoney = InvestTotalMoney * coin_data['fix_rate'] #설정된 투자금에 맞게 투자!
    
#'''
##########################################################################################################

    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    
    #코인별 할당된 모든 금액을 투자하는 올인 전략이니만큼 수수료를 감안하여 투자금 설정!
    InvestMoneyCell = InvestMoney * 0.995
    print("InvestMoneyCell: ", InvestMoneyCell)


    df_day = pyupbit.get_ohlcv(coin_ticker,interval="day")
    time.sleep(0.05)
    ############# 이동평균선! ###############
    for ma in range(3,80):
        df_day[str(ma) + 'ma'] = df_day['close'].rolling(ma).mean()
    ########################################
    
    Ma3_before = df_day['3ma'].iloc[-3]
    Ma3 = df_day['3ma'].iloc[-2]   
    Ma12 = df_day['12ma'].iloc[-2]   
    Ma24 = df_day['24ma'].iloc[-2] 
    
    Ma7_before = df_day['7ma'].iloc[-3]   
    Ma7 = df_day['7ma'].iloc[-2]   
    Ma10_before = df_day['10ma'].iloc[-3]   
    Ma10 = df_day['10ma'].iloc[-2]   
    Ma19_before = df_day['19ma'].iloc[-3]  
    Ma19 = df_day['19ma'].iloc[-2] 
    
    Ma53 = df_day['53ma'].iloc[-2] 
    
    
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()

    Ma_Last = Ma24
    if coin_ticker == 'KRW-ETH': 
        Ma_Last = Ma19

    Ma16 = df_day['16ma'].iloc[-2] 
    Ma73 = df_day['73ma'].iloc[-2] 
    
    Ma40 = df_day['40ma'].iloc[-2] 

    Ma52 = df_day['52ma'].iloc[-2] 
    

    Ma30_before = df_day['30ma'].iloc[-3] 
    Ma30 = df_day['30ma'].iloc[-2]


    Ma50_before = df_day['50ma'].iloc[-3] 
    Ma50 = df_day['50ma'].iloc[-2]
    
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
    #if myUpbit.IsHasCoin(balances,coin_ticker) == True: 
    ############################# FixV ####################################
    if BotDataDict[coin_ticker+"_HAS"] == True and myUpbit.IsHasCoin(balances,coin_ticker) == True:
        print("전략으로 매수한 경우!")

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
                if ((df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) or (df_day['open'].iloc[-2] > df_day['close'].iloc[-2] and df_day['open'].iloc[-3] > df_day['close'].iloc[-3])  )  :
                    IsSellGo = True

                if RsiMa_before < RsiMa and Ma3_before < Ma3:
                    IsSellGo = False




            BotDataDict[coin_ticker+"_DATE_CHECK"] = day_n
            #파일에 저장
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)



        #도지 캔들 패턴 체크
        prev_high_low_gap = abs(df_day['high'].iloc[-3] - df_day['low'].iloc[-3])
        prev_open_close_gap = abs(df_day['open'].iloc[-3] - df_day['close'].iloc[-3])

        #윗꼬리와 아래꼬리 길이 계산
        upper_tail = df_day['high'].iloc[-2] - max(df_day['open'].iloc[-2], df_day['close'].iloc[-2])
        lower_tail = min(df_day['open'].iloc[-2], df_day['close'].iloc[-2]) - df_day['low'].iloc[-2]


        #시가와 종가의 갭이 고가와 저가의 갭의 40% 이하면서 윗꼬리가 더 길 경우..
        if (prev_high_low_gap > 0 and (prev_open_close_gap / prev_high_low_gap) <= 0.4) and upper_tail > lower_tail:
                
            #저전저가보다 이전종가가 낮으면서 수익률이 0보다 작다면..
            if df_day['low'].iloc[-3] > df_day['close'].iloc[-2] and revenue_data['revenue_rate'] < 0:
                IsSellGo = True

        #저장된 매수날짜와 오늘 날짜가 같다면.. 오늘 돌파 매수던 시가 매수던 매수가 된 상황이니깐 오늘은 매도 하면 안된다.
        if BotDataDict[coin_ticker+"_BUY_DATE"] == day_str:
            IsSellGo = False


        if IsSellGo == True:

            myUpbit.CancelCoinOrder(upbit,coin_ticker)
            time.sleep(0.2)
            
            ############################# FixV ####################################
            #매도 하되 고정 비율 만큼은 남기도록 매도한다
            AllAmt = upbit.get_balance(coin_ticker) #현재 수량
            
            SellAmt = AllAmt * (1.0 - (coin_data['fix_rate']/(coin_data['rate']+coin_data['fix_rate'])))

            balances = myUpbit.SellCoinMarket(upbit,coin_ticker,SellAmt)

            if IsDolpaCut == True:
                msg = coin_ticker + " 업비트 안전 전략 봇 : 조건을 하향 돌파 불만족하여 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                line_alert.SendMessage(msg)
            else:
                            
                msg = coin_ticker + " 업비트 안전 전략 봇 : 조건을 불만족하여 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                line_alert.SendMessage(msg)


            ############################# FixV ####################################
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



        IsAdditionalCondition = False
        
        if coin_ticker == 'KRW-ETH':
            if (df_day['5ma'].iloc[-3] <= df_day['5ma'].iloc[-2] and df_day['5ma'].iloc[-2] <= PrevClose) and (df_day['24ma'].iloc[-3] <= df_day['24ma'].iloc[-2] and df_day['24ma'].iloc[-2] <= PrevClose):
                IsAdditionalCondition = True
                    


        else:
            if (df_day['3ma'].iloc[-3] <= df_day['3ma'].iloc[-2] and df_day['3ma'].iloc[-2] <= PrevClose) and (df_day['33ma'].iloc[-3] <= df_day['33ma'].iloc[-2] and df_day['33ma'].iloc[-2] <= PrevClose):
                IsAdditionalCondition = True
                
                
        #도지 캔들 패턴 체크
        prev_high_low_gap = abs(df_day['high'].iloc[-2] - df_day['low'].iloc[-2])
        prev_open_close_gap = abs(df_day['open'].iloc[-2] - df_day['close'].iloc[-2])



        #시가와 종가의 갭이 고가와 저가의 갭의 10% 이하라면 도지 캔들로 판단
        if (prev_high_low_gap > 0 and (prev_open_close_gap / prev_high_low_gap) <= 0.1) :
            IsMaDone = False


        #저장된 매도날짜와 오늘 날짜가 같다면.. 매도가 된 상황이니깐 오늘은 매수 하면 안된다.
        if BotDataDict[coin_ticker+"_SELL_DATE"] == day_str:
            IsMaDone = False



        if IsMaDone == True and IsAdditionalCondition == True :

            myUpbit.CancelCoinOrder(upbit,coin_ticker)
            time.sleep(0.2)
            
            
            
            Rate = 1.0
            ########################################################################################################
            ''' 이 부분을 주석처리 하면 감산 로직이 제거 됩니다 
            if coin_ticker == 'KRW-ETH':
                if Ma30_before > Ma30 or Ma52 > df_day['close'].iloc[-2]:
                    Rate *= 0.5

            else:
    
                if Ma50_before > Ma50 or Ma40 > df_day['close'].iloc[-2]:
                    Rate *= 0.5
            '''
            ########################################################################################################



            BuyGoMoney = InvestMoneyCell * Rate

            if BuyGoMoney >= df_day['value_ma'].iloc[-2] / 2000:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 2000

            BuyMoney = BuyGoMoney 



            ############################# DANTA #############################
            #현재 투자 평가금을 구한다!
            NowMoney = myUpbit.GetCoinNowRealMoney(balances,coin_ticker)
            
            #해당 코인에 할당된 금액!!!
            TargetTotalMoney = InvestTotalMoney * (coin_data['rate'] + coin_data['fix_rate'])
            # TargetTotalMoney 이걸 넘기면 안된다!!!
            
            #투자로 정해진 금액보다 살금액 + 현재 투자금이 더 크다면?
            if TargetTotalMoney < (BuyMoney + NowMoney):
                BuyMoney = TargetTotalMoney - NowMoney #살 금액을 정해진 금액에서 현재 투자금의 차액으로 정해준다!!!           

            #투자로 정해진 금액보다 살금액 + 현재 투자금이 더 작다면?? 비중이 모자라다 채워주자! 그 갭만큼!!
            elif TargetTotalMoney > (BuyMoney + NowMoney):
                BuyMoney += (TargetTotalMoney - (BuyMoney + NowMoney))


            #######################################################################################
            #원화 잔고를 가져온다
            won = float(upbit.get_balance("KRW"))
            print("# Remain Won :", won)
            time.sleep(0.004)
            
            #
            if BuyMoney > won:
                BuyMoney = won*0.99

            if BuyMoney >= minmunMoney:
                    
                balances = myUpbit.BuyCoinMarket(upbit,coin_ticker,BuyMoney)

                

                ############################# FixV ####################################
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
            


    
    ############################# FixV ####################################
    if coin_data['fix_rate'] > 0:

        #내가 가진 잔고 데이터를 다 가져온다.
        balances = upbit.get_balances()

        RealMoney = myUpbit.GetCoinNowRealMoney(balances,coin_ticker)
        
        #잔고가 없다면 고정 비중만큼 매수한다!
        if myUpbit.IsHasCoin(balances,coin_ticker) == False: 
            
            #고정 비중 만큼 매수한다!!!!
            InvestMoneyCell = InvestFixMoney * 0.995

            Rate = 1.0
            BuyGoMoney = InvestMoneyCell * Rate

            #투자금 거래대금 10일 평균의 1/2000수준으로 제한!
            if BuyGoMoney >= df_day['value_ma'].iloc[-2] / 2000:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 2000

            BuyMoney = BuyGoMoney 

            #원화 잔고를 가져온다
            won = float(upbit.get_balance("KRW"))
            print("# Remain Won :", won)
            time.sleep(0.004)
            
            #
            if BuyMoney > won:
                BuyMoney = won*0.99

            balances = myUpbit.BuyCoinMarket(upbit,coin_ticker,BuyMoney)


            msg = coin_ticker + " 업비트 안전 전략 봇 :  고정비중이 없어 투자!!"
            print(msg)
            line_alert.SendMessage(msg)
        



    ############################# DANTA #############################
    '''
    단타 로직은 임의로 만든 것으로 자신만의 단타 전략이 있으신 분은
    이렇게 응용할 수 있다의 참고용으로 체크하세요 ^^!
    '''
    #####추가 단타 및 매수 파트#####
    NowMoney = myUpbit.GetCoinNowRealMoney(balances,coin_ticker)
    TargetTotalMoney = InvestTotalMoney * (coin_data['rate'] + coin_data['fix_rate'])
    
    InvestAddMoney = TargetTotalMoney / 100 #단타로 매수할 금액 숫자를 줄이면 단타 매매당 금액이 커진다!
        

    if InvestAddMoney < minmunMoney:
        InvestAddMoney = minmunMoney
        

    IsAddOK = False
    
    print(" InvestAddMoney ", InvestAddMoney)
    
    RemainMoney = 0
    
    
    #전략으로 매매한 경우.. 감산에 의해 현금 비중이 있다면 
    if BotDataDict[coin_ticker+"_HAS"] == True:

        #코인에 할당된 금액에 현재 투자된 금액을 빼서 남은 할당 금액을 구한다.
        RemainMoney = TargetTotalMoney - NowMoney
        
        #그 남은 금액이 단타매수할 금액보다 크다면 단타 매매 가능!!
        if RemainMoney >= InvestAddMoney:
            IsAddOK = True
            

    #전략이 아직 매매하지 않은 경우!!!
    else:
        
        #고정비중만 있는 경우다.
        #현재 비트 50% 이더 50%인데 단타 및 매수로 25%까지 활용하도록 금액 세팅!
        #즉 고정비중 10%를 감안하면 25%까지 15%의 현금을 가지고 단타 매매를 한다!
        RemainMoney = (TargetTotalMoney * 0.5) - NowMoney
        
        if RemainMoney >= InvestAddMoney:
            IsAddOK = True
            
            
    if IsAddOK == True:
        
        #15분봉 기준 단타 매매 예시
        if min_n % 15 == 0:

            df_15 = pyupbit.get_ohlcv(coin_ticker,interval="minute15")
            time.sleep(0.05)
                
            ########## RSI 지표 구하는 로직! ##########
            period = 14

            delta = df_15["close"].diff()
            up, down = delta.copy(), delta.copy()
            up[up < 0] = 0
            down[down > 0] = 0
            _gain = up.ewm(com=(period - 1), min_periods=period).mean()
            _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
            RS = _gain / _loss

            df_15['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
            ########################################

            Ma20 = myUpbit.GetMA(df_15,20,-2) 
            
            Ma5_before2 = myUpbit.GetMA(df_15,5,-4)  
            Ma5_before = myUpbit.GetMA(df_15,5,-3)  
            Ma5 = myUpbit.GetMA(df_15,5,-2)  
            
            
            
            IsBuyGo = False
            
            #RSI지표가 30이하에서 빠져나온게 이전 캔들에서 확정되었을 때 
            if df_15['rsi'].iloc[-4] >= df_15['rsi'].iloc[-3] and df_15['rsi'].iloc[-3] <= df_15['rsi'].iloc[-2] and df_15['rsi'].iloc[-3] <= 30 and df_15['rsi'].iloc[-2] > 30:
                IsBuyGo = True
            
            #20일선 아래 5일선이 있는데 5일선이 하락하다 위로 꺾인 순간!
            if Ma5 < Ma20 and Ma5_before2 >= Ma5_before and Ma5_before <= Ma5:
                IsBuyGo = True
                
            
            if IsBuyGo == True:
                #원화 잔고를 가져온다
                won = float(upbit.get_balance("KRW"))
                print("# Remain Won :", won)
                time.sleep(0.004)
                
         
                
                if InvestAddMoney > won:
                    InvestAddMoney = won*0.99

                balances = myUpbit.BuyCoinMarket(upbit,coin_ticker,InvestAddMoney)


                msg = coin_ticker + " 업비트 안전 전략 봇 : 15분봉 기준 매매 고고!!!"
                print(msg)
                line_alert.SendMessage(msg)
                
                

                try:
                    NowCurrentPrice = pyupbit.get_current_price(coin_ticker)
                    TargetPrice = NowCurrentPrice * (1.005) #목표 수익률은 0.5%!!! 
                    myUpbit.SellCoinLimit(upbit,coin_ticker,TargetPrice,(float(InvestAddMoney) / float(NowCurrentPrice)))
                    msg = coin_ticker + " 업비트 안전 전략 봇 : 15분봉 기준 매매 익절 주문!"
                    print(msg)
                    line_alert.SendMessage(msg)
                    
                except Exception as e:
                    
                    msg = coin_ticker + " 업비트 안전 전략 봇 : " + str(e)
                    print(msg)
                    line_alert.SendMessage(msg)
                                        
                            
    





