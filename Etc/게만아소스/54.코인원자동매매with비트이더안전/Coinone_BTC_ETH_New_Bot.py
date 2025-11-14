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
https://blog.naver.com/zacra/223508324003

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^





##############################################################
코인원 앱 -> 하단 더보기 -> 이벤트 코드 -> 등록하기 -> ZABOBSTUDIO 
##############################################################

'''

import myCoinone
import time

import pandas as pd
import json
import line_alert




#시간 정보를 읽는다
time_info = time.gmtime()

day_n = time_info.tm_mday

hour_n = time_info.tm_hour
min_n = time_info.tm_min

print("hour_n:", hour_n)
print("min_n:", min_n)

day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)




#봇 상태를 저장할 파일
BotDataDict = dict()

#파일 경로입니다.
botdata_file_path = "/var/autobot/CoinoneSafe_Data.json"
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
balances = myCoinone.GetBalances()

TotalMoney = myCoinone.GetTotalMoney(balances) #총 원금
TotalRealMoney = myCoinone.GetTotalRealMoney(balances) #총 평가금액

print("TotalMoney", TotalMoney)
print("TotalRealMoney", TotalRealMoney)
#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.7 #투자 비중은 자금사정에 맞게 수정하세요!

##########################################################################
InvestTotalMoney = TotalMoney * InvestRate #총 투자원금+ 남은 원화 기준으로 투자!!!!
##########################################################################

print("InvestTotalMoney", InvestTotalMoney)


######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["BTC","ETH"]
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "BTC"
InvestDataDict['rate'] = 0.5
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "ETH"
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


    ############################# FixV ####################################
    #체크한 기록이 없는 처음이라면 
    if BotDataDict.get(coin_ticker+"_HAS") == None:
        

        if myCoinone.IsHasCoin(balances,coin_ticker) == True and myCoinone.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney: 

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

    df_day = myCoinone.GetOhlcv(coin_ticker,'1d')
    time.sleep(0.1)

    
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()


    Ma3_before = myCoinone.GetMA(df_day,3,-3) 
    Ma3 = myCoinone.GetMA(df_day,3,-2)  


    Ma5_before = myCoinone.GetMA(df_day,5,-3) 


    Ma5 = myCoinone.GetMA(df_day,5,-2)   

    Ma6_before = myCoinone.GetMA(df_day,6,-3) 
    Ma6 = myCoinone.GetMA(df_day,6,-2)   

    Ma10_before = myCoinone.GetMA(df_day,10,-3)   
    Ma10 = myCoinone.GetMA(df_day,10,-2)   
    
    Ma19_before = myCoinone.GetMA(df_day,19,-3) 
    Ma19 = myCoinone.GetMA(df_day,19,-2) 
    Ma20 = myCoinone.GetMA(df_day,20,-2) 

    Ma_Last = Ma19
    


    Ma50_before = myCoinone.GetMA(df_day,50,-3) 
    Ma50 = myCoinone.GetMA(df_day,50,-2)

    Ma60 = myCoinone.GetMA(df_day,60,-2)

    
    Ma70 = myCoinone.GetMA(df_day,70,-2)
    
    Rsi_before = myCoinone.GetRSI(df_day,14,-3) 
    Rsi = myCoinone.GetRSI(df_day,14,-2) 


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
    NowCurrentPrice = myCoinone.GetCurrentPrice(coin_ticker)


    #잔고가 있는 경우.
    if BotDataDict[coin_ticker+"_HAS"] == True and myCoinone.IsHasCoin(balances,coin_ticker) == True and myCoinone.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney:
        print("잔고가 있는 경우!")

        #수익금과 수익률을 구한다!
        revenue_data = myCoinone.GetRevenueMoneyAndRate(balances,coin_ticker)



        IsSellGo = False


    
        IsDolpaCut = False

        #이더리움의 경우
        if coin_ticker == 'ETH':

            #RSI지표가 70이상인 과매수 구간에서 단기 이평선을 아래로 뚫으면 돌파매도 처리!!
            CutPrice = Ma6
            
            if df_day['rsi'].iloc[-2] >= 70 and NowCurrentPrice <= CutPrice and df_day['open'].iloc[-1] > CutPrice :
                IsSellGo = True
                IsDolpaCut = True

        if BotDataDict[coin_ticker+"_DATE_CHECK"] != day_n:

            msg = coin_ticker + "현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
            print(msg)
            line_alert.SendMessage(msg)


            time.sleep(1.0)
                
            #이더리움의 경우
            if coin_ticker == 'ETH':
                #50일선 위에 있는 상승장
                if PrevClose > Ma50:

                    #6일선, 10일선 둘다 밑으로 내려가면 매도!!
                    if Ma6 > PrevClose and Ma10 > PrevClose:

                        IsSellGo = True

                #50일선 아래에 있는 하락장
                else:
                    
                    # 5일선 밑으로 내려가거나 전일 캔들 기준 고가도 하락하고 저가도 하락했다면 매도!
                    if Ma6 > PrevClose or (df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) :
                        IsSellGo = True

            #비트코인의 경우
            else:
                #전일 캔들 기준 고가도 하락하고 저가도 하락했거나 2연속 음봉이거나 수익률이 0보다 작아지면 매도!!
                if ((df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) or (df_day['open'].iloc[-2] > df_day['close'].iloc[-2] and df_day['open'].iloc[-3] > df_day['close'].iloc[-3])  ) or revenue_data['revenue_rate'] < 0 :
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

            AllAmt = myCoinone.GetCoinAmount(balances,coin_ticker) 

            balances = myCoinone.SellCoinMarket(coin_ticker,AllAmt)

            if IsDolpaCut == True:
                msg = coin_ticker + " 코인원 안전 전략 봇 : 조건을 하향 돌파 불만족하여 모두 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                line_alert.SendMessage(msg)
            else:
                            
                msg = coin_ticker + " 코인원 안전 전략 봇 : 조건을 불만족하여 모두 매도처리 했어요!! 현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
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


        #3개의 이평선 중 가장 높은 값을 구한다!
        DolPaSt = max(Ma6,Ma10,Ma_Last)
        
        if coin_ticker == 'ETH':
            
            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때
            #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
            if DolPaSt == Ma_Last and NowCurrentPrice >= DolPaSt:
            
                #단 RSI지표가 증가! RSI 10일 평균지표도 증가할 때 돌파매수!
                if Rsi_before < Rsi and RsiMa_before < RsiMa:
                    IsMaDone = True
                    

            #그 밖의 경우
            else:
                #5,10,20선 위에 있고 RSI지표가 증가! RSI 10일 평균지표도 증가한다면 매수!
                if PrevClose > Ma6 and PrevClose > Ma10 and PrevClose > Ma_Last and Rsi_before < Rsi  and RsiMa_before < RsiMa:
                    IsMaDone = True


            if IsMaDone == False:

                print("변돌 체크!")

                DolpaRate = 0.7

                if Ma_Last < PrevClose:
                    DolpaRate = 0.6

                if Ma6_before < Ma6 and Ma10_before < Ma10 and  Ma19_before < Ma19 and Ma19 < Ma10 < Ma6:
                    DolpaRate = 0.5


                DolPaSt = df_day['open'].iloc[-1] + (( df_day['high'].iloc[-2] - df_day['low'].iloc[-2]) * DolpaRate)

                if NowCurrentPrice >= DolPaSt and RsiMa_before < RsiMa and Ma6_before < Ma6:

                    IsMaDone = True



        #비트코인일 때       
        else:
            

            #가장 높은 이평선의 값이 가장 긴 기간의 이평선일때
            #그 전일 이평선 값을 현재가가 넘었다면 돌파 매수를 한다!!!
            if DolPaSt == Ma_Last and NowCurrentPrice >= DolPaSt:

                #비트코인은 추가 조건 체크 없이 그냥 돌파했으면 매수!
                IsMaDone = True
                    
            else:
                #2연속 양봉이면서 고가도 증가되는데 5일선이 증가되고 있으면서 10일선,70일선 위에 있을 때 비트 매수!
                if df_day['open'].iloc[-2] < df_day['close'].iloc[-2] and df_day['open'].iloc[-3] < df_day['close'].iloc[-3] and df_day['close'].iloc[-3] < df_day['close'].iloc[-2]  and df_day['high'].iloc[-3] < df_day['high'].iloc[-2] and Ma3_before < Ma3 and Ma20 < df_day['close'].iloc[-2] and Ma70 < df_day['close'].iloc[-2] :
                        
                    IsMaDone = True
                    

            if IsMaDone == False:
                print("변돌 체크!")

                DolpaRate = 0.7

                DolPaSt = df_day['open'].iloc[-1] + ( ( max(df_day['high'].iloc[-3],df_day['high'].iloc[-2]) - min(df_day['low'].iloc[-3],df_day['low'].iloc[-2]) ) * DolpaRate)

                if NowCurrentPrice >= DolPaSt and RsiMa_before < RsiMa and df_day['low'].iloc[-3] < df_day['low'].iloc[-2] and Ma10 < PrevClose and Ma19 < Ma10 < Ma3:
                    IsMaDone = True


        #저장된 매도날짜와 오늘 날짜가 같다면.. 매도가 된 상황이니깐 오늘은 매수 하면 안된다.
        if BotDataDict[coin_ticker+"_SELL_DATE"] == day_str:
            IsMaDone = False



        if IsMaDone == True :

            Rate = 1.0

            ########################################################################################################
            #''' 이 부분을 주석처리 하면 감산 로직이 제거 됩니다 
            if Ma50_before > Ma50 or Ma50 > df_day['close'].iloc[-2]:
                Rate *= 0.5
            #'''
            ########################################################################################################


            BuyGoMoney = InvestMoneyCell * Rate

            #투자금 거래대금 10일 평균의 1/2000수준으로 제한!
            if BuyGoMoney >= df_day['value_ma'].iloc[-2] / 2000:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 2000

            BuyMoney = BuyGoMoney 

            #원화 잔고를 가져온다
            won = myCoinone.GetCoinAmount(balances,"KRW")
            print("# Remain Won :", won)
            time.sleep(0.004)
            
            #
            if BuyMoney > won:
                BuyMoney = won * 0.99 #수수료 및 슬리피지 고려


            if BuyMoney >= minmunMoney:

                balances = myCoinone.BuyCoinMarket(coin_ticker,BuyMoney)
                
                BotDataDict[coin_ticker+"_HAS"] = True

                #매수했다면 매수 날짜를 기록한다.
                BotDataDict[coin_ticker+"_BUY_DATE"] = day_str
                #파일에 저장
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)


                
                msg = coin_ticker + " 코인원 안전 전략 봇 :  조건 만족 하여 매수!! " + str(BuyMoney) + "원어치 매수!"

                print(msg)
                line_alert.SendMessage(msg)


        else:
            #매일 아침 9시 정각에..
            if hour_n == 0 and min_n == 0:
                msg = coin_ticker + " 코인원 안전 전략 봇 :  조건 만족하지 않아 현금 보유 합니다!"
                print(msg)
                line_alert.SendMessage(msg)
            













