#-*-coding:utf-8 -*-
'''

-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-

관련 포스팅

수익 인증!? 업비트 상장된 모든 코인을 매매하자! 에브리씽 에브리웨어 올 앳 원스 업비트 자동매매 전략!
https://blog.naver.com/zacra/223029163144

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

'''
블로그 내용 참고하셔서
수정해서 개선해 보세요~^^!

'''


#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)

#내가 매수할 최대 코인 개수
MaxCoinCnt = 10.0

#최소 매수 금액
minmunMoney = 5500

#내가 가진 잔고 데이터를 다 가져온다.
balances = upbit.get_balances()

TotalMoeny = myUpbit.GetTotalMoney(balances) #총 원금
TotalRealMoney = myUpbit.GetTotalRealMoney(balances) #총 평가금액

#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.1 #투자 비중은 자금사정에 맞게 수정하세요! 검증할때는 소액으로 하는게 옳아요!


InvestMoney = TotalMoeny * InvestRate

#코인당 매수할 최대 매수금액
CoinMaxMoney = InvestMoney / MaxCoinCnt


print("-----------------------------------------------")
print ("Total Money:", myUpbit.GetTotalMoney(balances))
print ("Total Real Money:", myUpbit.GetTotalRealMoney(balances))

print("-----------------------------------------------")
print ("InvestMoney : ", InvestMoney)
print ("CoinMaxMoney : ", CoinMaxMoney)

#################################################
#################################################
#봇이 건드리면 안되는 코인!
OutCoinList = ['KRW-BTC','KRW-ETH']

#유의 코인을 OutCoinList에 추가!!!
Tickers = pyupbit.get_tickers("KRW",True) #원화마켓의 모든 데이터!

for coin_data in Tickers:
    if coin_data['market_event']['warning'] == True:
        OutCoinList.append(coin_data['market'])
        
        
        

Tickers = pyupbit.get_tickers("KRW")

pprint.pprint(Tickers)
print(len(Tickers))
#################################################
#################################################


UpbitMomentumCoinList = list()
#파일 경로입니다.
upbit_momentum_file_path = "/var/autobot/UpbitMomentumCoinList.json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(upbit_momentum_file_path, 'r') as json_file:
        UpbitMomentumCoinList = json.load(json_file)

except Exception as e:
    print("Exception by First")


#종가 데이터를 가지고 오는데 신규 상장되서 이전 데이터가 없다면 데이터가 있는 시점부터 가지고 온다.
def GetCloseData(df,st):
    
    if len(df) < abs(st):
        return df['close'].iloc[-len(df)] 
    else:
        return df['close'].iloc[st] 
        
#모멘텀 스코어를 구해주는 함수!
def GetMomentumScore(df,st_price,gap,period=10.0):

    Avg_Period = period
    Now_Price = st_price

    ResultMomentum = 0.5

    #이건 평균 모멘텀을 구하기에 상장된지 얼마 안된 코인이다.
    #그러면 그 기간내를 Avg_Period 만큼 등분해서 계산
    if len(df) < Avg_Period * gap:

        #캔들이 10개보다 클때! 
        if len(df) > (Avg_Period+1):

            Up_Count = 0
            
            CellVal = int(len(df)/Avg_Period)

            Start_Num = -CellVal

            for i in range(1,int(Avg_Period)+1):
                CheckPrice = GetCloseData(df,Start_Num)

                if Now_Price >= CheckPrice:
                    Up_Count += 1.0

                Start_Num -= CellVal

            ResultMomentum = Up_Count/Avg_Period

    #일반적인 경우라면 그냥 기준에 맞게 계산!
    else:
    
        Up_Count = 0
        Start_Num = -gap
        for i in range(1,int(Avg_Period)+1):
            
            CheckPrice = GetCloseData(df,Start_Num)
            #print(CheckPrice, "  <<-  df[-", Start_Num,"]")

            if Now_Price >= CheckPrice:
                #print("UP!")
                Up_Count += 1.0

            Start_Num -= gap

        ResultMomentum = Up_Count/Avg_Period

    
    return ResultMomentum


#수익금과 수익률을 리턴해주는 함수 (수수료는 생각안함)
def GetRevenueMoneyAndRate(balances,Ticker):
             
    revenue_data = dict()

    revenue_data['revenue_money'] = 0
    revenue_data['revenue_rate'] = 0

    for value in balances:
        try:
            realTicker = value['unit_currency'] + "-" + value['currency']
            if Ticker == realTicker:
                
                nowPrice = pyupbit.get_current_price(realTicker)
                revenue_data['revenue_money'] = (float(nowPrice) - float(value['avg_buy_price'])) * upbit.get_balance(CoinTicker)
                revenue_data['revenue_rate'] = (float(nowPrice) - float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
                time.sleep(0.06)
                break

        except Exception as e:
            print("---:", e)

    return revenue_data




################################################################################
################################################################################
#비트코인 일봉 데이터!
df_btc_day = pyupbit.get_ohlcv("KRW-BTC",interval="day") #비트코인 일봉 데이타를 가져온다.
BTC_nowPrice = pyupbit.get_current_price("KRW-BTC")
BTC_Ma5 = myUpbit.GetMA(df_btc_day,5,-1)

################################################################################
################################################################################



#비트코인 이평선이 5일선 밑으로 내려왔다면 해당 봇이 매수한거 모두 매도 하고 재상승장을 기다린다.
if BTC_Ma5 > BTC_nowPrice:
   
    #먼저 이전에 매수된 코인중에 지금 선택되지 않은 코인을 모두 매도 한다!
    for CoinTicker in UpbitMomentumCoinList:

        #제외할 코인이라면 스킵!!! - 여기에 조건을 걸 필요는 없지만 확실히 하기 위해!
        if myUpbit.CheckCoinInList(OutCoinList,CoinTicker) == True:
            continue
        
        #잔고가 있을테지만 그래도 잔고가 있는지 체크해서
        if myUpbit.IsHasCoin(balances,CoinTicker) == True:
    
            #수익금과 수익률을 구한다!
            revenue_data = GetRevenueMoneyAndRate(balances,CoinTicker)

            #모두 매도처리!!
            balances = myUpbit.SellCoinMarket(upbit,CoinTicker,upbit.get_balance(CoinTicker))
            
            msg = CoinTicker + " 모두 매도!  수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(round(revenue_data['revenue_money'],2)) + "원"
            print(msg)
            line_alert.SendMessage(msg)
            
    UpbitMomentumCoinList.clear()
            
    #파일에 리스트를 저장합니다
    with open(upbit_momentum_file_path, 'w') as outfile:
        json.dump(UpbitMomentumCoinList, outfile)

#비트코인 5일선 위! 상승장!
else:
    

    TempMomentumCoinList = list()

    for ticker in Tickers:

        #제외할 코인이라면 스킵!!!
        if myUpbit.CheckCoinInList(OutCoinList,ticker) == True:
            continue

        try:

            time.sleep(0.04)
            nowPrice = pyupbit.get_current_price(ticker)

            time.sleep(0.04)
            df_day = pyupbit.get_ohlcv(ticker,interval="day") #일봉 데이타를 가져온다.

            time.sleep(0.04)
            df_60min = pyupbit.get_ohlcv(ticker,interval="minute60") #60분봉 데이타를 가져온다.



            before_rsi = 50
            now_rsi = 50

            try:
                before_rsi = myUpbit.GetRSI(df_day,14,-3)
                now_rsi = myUpbit.GetRSI(df_day,14,-2)
            except Exception as e:
                print("Exception ", e)  


            before_hour_rsi = 50
            now_hour_rsi = 50

            try:
                before_hour_rsi = myUpbit.GetRSI(df_60min,14,-3)
                now_hour_rsi = myUpbit.GetRSI(df_60min,14,-2)
            except Exception as e:
                print("Exception ", e)  





            print("---- ", ticker," ----")
            #너무 과매수는 피하자..내 것이 아니야 눌림이 오겠지... 안녕~~! 전일 거래대금 100억 이상만
            if df_day['value'].iloc[-2] >= 10000000000 and before_rsi < now_rsi and now_rsi < 70 and before_hour_rsi < now_hour_rsi and now_hour_rsi < 70:


                momentum_hour = GetMomentumScore(df_60min,nowPrice,1) #1시간
                momentum_4hour = GetMomentumScore(df_60min,nowPrice,4) #4시간
                momentum_day = GetMomentumScore(df_day,nowPrice,1)  #하루
                momentum_month = GetMomentumScore(df_day,nowPrice,20)  #20일을 1달로

                momentum = momentum_hour*0.15 + momentum_4hour*0.35 + momentum_day*0.35 + momentum_month*0.15

                
                print("momentum_hour ", momentum_hour)
                print("momentum_4hour ", momentum_4hour)
                print("momentum_day ", momentum_day)
                print("momentum_month ", momentum_month)
                print("---------------------")


                CoinDataDict = dict()

                CoinDataDict['Ticker'] = ticker

                CoinDataDict['momentum'] = momentum

                CoinDataDict['NowPrice'] = nowPrice
                CoinDataDict['MA5'] = nowPrice
                CoinDataDict['MA10'] = nowPrice
                CoinDataDict['MA20'] = nowPrice

                try:
                    CoinDataDict['MA5'] = myUpbit.GetMA(df_60min,5,-2)
                except Exception as e:
                    print("Exception ", e)  

                try:
                    CoinDataDict['MA10'] = myUpbit.GetMA(df_60min,10,-2)
                except Exception as e:
                    print("Exception ", e)  

                try:
                    CoinDataDict['MA20'] = myUpbit.GetMA(df_60min,20,-2)
                except Exception as e:
                    print("Exception ", e)  
                
                TempMomentumCoinList.append(CoinDataDict)

                pprint.pprint(CoinDataDict)
                print("---------------------\n")
            else:
                print("---- No Check ----\n")

        except Exception as e:
            print("Exception ", e)


    print("---------------\n\n\n")
    pprint.pprint(TempMomentumCoinList)
    print("---------------\n\n\n")

    FinalSelectedList = list()

    '''
    df = pd.DataFrame(TempMomentumCoinList)
    df = df.sort_values(by="momentum", ascending=False)


    pprint.pprint(df.values.tolist())

    print("----------------------------------")
    print("----------------------------------")
    print("----------------------------------")

    '''


    Coindata = sorted(TempMomentumCoinList, key=lambda coin_info: (coin_info['momentum']), reverse= True)

    i = 0
    for data in Coindata:
        
        if i < int(MaxCoinCnt):

            FinalSelectedList.append(data)
            i += 1
            

    print("-----------------최종 선택된 투자 대상 코인-------------------")
    pprint.pprint(FinalSelectedList)


    ################################################################################

    RemoveTicker = list()

    #먼저 이전에 매수된 코인중에 지금 선택되지 않은 코인을 모두 매도 한다!
    for CoinTicker in UpbitMomentumCoinList:

        #제외할 코인이라면 스킵!!! - 여기에 조건을 걸 필요는 없지만 확실히 하기 위해!
        if myUpbit.CheckCoinInList(OutCoinList,CoinTicker) == True:
            continue
        
        try:
            IsAlreadyHas = False
            
            for CoinData in FinalSelectedList:
                if CoinData['Ticker'] == CoinTicker:
                    
                    IsAlreadyHas = True
                    break
                
            #이번에 선택되지 않은 코인은 모두 매도한다!
            if IsAlreadyHas == False:

                #잔고가 있을테지만 그래도 잔고가 있는지 체크해서
                if myUpbit.IsHasCoin(balances,CoinTicker) == True:
                    
                    #수익금과 수익률을 구한다!
                    revenue_data = GetRevenueMoneyAndRate(balances,CoinTicker)

                    #모두 매도처리!!
                    balances = myUpbit.SellCoinMarket(upbit,CoinTicker,upbit.get_balance(CoinTicker))
                    
                    msg = CoinTicker + " 모두 매도!  수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(round(revenue_data['revenue_money'],2)) + "원"
                    print(msg)
                    line_alert.SendMessage(msg)
                    
                    RemoveTicker.append(CoinTicker)
                    

        except Exception as e:
            print("Exception ", e)
            
    ################################################################################
    #선택되지 않아서 매도한 코인은 모두 파일에서 삭제!
    for CoinTicker in RemoveTicker:
        UpbitMomentumCoinList.remove(CoinTicker)
        
    #파일에 리스트를 저장합니다
    with open(upbit_momentum_file_path, 'w') as outfile:
        json.dump(UpbitMomentumCoinList, outfile)
    ################################################################################
        


    #선택된 코인 데이터를 순회한다
    for CoinData in FinalSelectedList:
        
        try:
            
            ticker = CoinData['Ticker']
            
            #제외할 코인이라면 스킵!!! - 여기에 조건을 걸 필요는 없지만 확실히 하기 위해!
            if myUpbit.CheckCoinInList(OutCoinList,ticker) == True:
                continue
                
            #각 코인별 할당 금액에 최종 모멘텀 스코어를 구해서 투자금을 정한다!!
            FinalMoney = CoinMaxMoney * CoinData['momentum']
            
            #5일 이평선 밑이라면 50% 감산!!
            if CoinData['MA5'] > CoinDataDict['NowPrice']:
                FinalMoney *= 0.5

            #10일 이평선 밑이라면 50% 감산!!
            if CoinData['MA10'] > CoinDataDict['NowPrice']:
                FinalMoney *= 0.5

            #20일 이평선 밑이라면 50% 감산!!
            if CoinData['MA20'] > CoinDataDict['NowPrice']:
                FinalMoney *= 0.5


            IsAlreadyHas = False
            
            #선택된 코인이 이전에 매수한적이 있다면 그대로 유지하되 비중만 조절하면 된다.
            for CoinTicker in UpbitMomentumCoinList:
                
                #어 이전에 매수한적 있네!
                if ticker == CoinTicker:

                    #잔고가 있을테지만 그래도 잔고가 있는지 체크해서
                    if myUpbit.IsHasCoin(balances,CoinTicker) == True:

                        #수익금과 수익률을 구한다!
                        revenue_data = GetRevenueMoneyAndRate(balances,CoinTicker)

                        print(">>>>>>>>>>> 이미 이 봇에 의해 매수되었어요! " , ticker, " ", revenue_data)
                        #최종 투자금이 미니멈 머니보다 작다면 모두 매도!!!!
                        if FinalMoney < minmunMoney:


                            #모두 매도처리!!
                            balances = myUpbit.SellCoinMarket(upbit,CoinTicker,upbit.get_balance(CoinTicker))
                            
                            
                            msg = CoinTicker + " 모두 매도!(비중이 최소금보다 작아짐)  수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(round(revenue_data['revenue_money'],2)) + "원"
                            print(msg)
                            line_alert.SendMessage(msg)
                            
                            UpbitMomentumCoinList.remove(ticker)

                            
                        else:
                            
                            NowCoinTotalMoney = myUpbit.GetCoinNowRealMoney(balances,CoinTicker) #코인의 현재 평가금액!
                            
                            GapMoney = FinalMoney - NowCoinTotalMoney
                            
                            
                            if abs(GapMoney) > minmunMoney:
                                
                                #현재 설정된 금액이 이전에 매수한 평가금보다 크다면 추가 매수 해야된다!
                                if GapMoney > 0:
                                    
                                    balances = myUpbit.BuyCoinMarket(upbit,CoinTicker,abs(GapMoney))
                                    
                                    
                                    msg = CoinTicker + " 추가 매수합니다! 모멘텀스코어: " + str(round(CoinData['momentum'],2)) + " 추가 투자금:" + str(abs(round(GapMoney,2))) + " 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(round(revenue_data['revenue_money'],2)) + "원"
                                    print(msg)
                                    line_alert.SendMessage(msg)
                                    
                                #현재 설정된 금액이 이전에 매수한 평가금보다 작다면 추가 매도 해야 된다!
                                else:
                                    
                                    #그 갭만큼 수량을 구해서 
                                    GapAmt = abs(GapMoney) / pyupbit.get_current_price(CoinTicker)
                                            
                                    balances = myUpbit.SellCoinMarket(upbit,CoinTicker,GapAmt)
                                    
                                    
                                    msg = CoinTicker + " 일부 매도 합니다! 모멘텀스코어: " + str(round(CoinData['momentum'],2)) + " 추가 매도금:" + str(abs(round(GapMoney,2))) + " 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(round(revenue_data['revenue_money'],2)) + "원"
                                    print(msg)
                                    line_alert.SendMessage(msg)
                                

                        IsAlreadyHas = True

                    break       
                
            if IsAlreadyHas == False:
                print("비중대로 첫 매수!")

                if FinalMoney > minmunMoney:
                    
                    balances = myUpbit.BuyCoinMarket(upbit,ticker,FinalMoney)
                    
                    
                    msg = ticker + " 매수합니다! 모멘텀스코어: " + str(round(CoinData['momentum'],2)) + " 투자금:" + str(round(FinalMoney,2))
                    print(msg)
                    line_alert.SendMessage(msg)
                    
                    UpbitMomentumCoinList.append(ticker)
                    
                else:
                
                    msg = ticker + " 매수대상이나 비중으로 계산된 투자 금이 너무 작아서 아예 매수하지 않습니다! 모멘텀스코어: " + str(round(CoinData['momentum'],2)) + " 투자금:" + str(round(FinalMoney,2))
                    print(msg)
                    line_alert.SendMessage(msg)

                    UpbitMomentumCoinList.remove(ticker)
                    
                
        except Exception as e:
            print("Exception ", e)
        


    #파일에 리스트를 저장합니다
    with open(upbit_momentum_file_path, 'w') as outfile:
        json.dump(UpbitMomentumCoinList, outfile)

