#-*-coding:utf-8 -*-
'''

관련 포스팅

연복리 200에 가까운 이평조합 전략!
https://blog.naver.com/zacra/223074617299

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



#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)





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


time.sleep(1.0)


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

#원화 잔고를 가져온다
won = float(upbit.get_balance("KRW"))
print("# Remain Won :", won)
time.sleep(0.04)


######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["KRW-BTC","KRW-ETH",'KRW-ADA','KRW-DOT','KRW-POL']
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.4
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.4
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ADA"
InvestDataDict['rate'] = 0.1
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-DOT"
InvestDataDict['rate'] = 0.05
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-POL"
InvestDataDict['rate'] = 0.05
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

    InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
#'''
##########################################################################################################

    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

    
    #코인별 할당된 모든 금액을 투자하는 올인 전략이니만큼 수수료를 감안하여 투자금 설정!
    InvestMoneyCell = InvestMoney * 0.995
    print("InvestMoneyCell: ", InvestMoneyCell)


    df_day = pyupbit.get_ohlcv(coin_ticker,interval="day")
    time.sleep(0.05)

    #5, 10, 21선으로 투자한다고 가정했습니다!
    Ma5 = myUpbit.GetMA(df_day,5,-2)   #전일 종가 기준 5일 이동평균선
    Ma10 = myUpbit.GetMA(df_day,10,-2)   #전일 종가 기준 10일 이동평균선
    Ma21 = myUpbit.GetMA(df_day,21,-2) #전일 종가 기준 21일 이동평균선

    PrevClose = df_day['close'].iloc[-2]

    #현재가를 구하다
    NowOpenPrice = pyupbit.get_current_price(coin_ticker)


    #잔고가 있는 경우.
    if myUpbit.IsHasCoin(balances,coin_ticker) == True: 
        print("잔고가 있는 경우!")

        #수익금과 수익률을 구한다!
        revenue_data = GetRevenueMoneyAndRate(balances,coin_ticker)

        msg = coin_ticker + "현재 수익률 : 약 " + str(round(revenue_data['revenue_rate'],2)) + "% 수익금 : 약" + str(format(round(revenue_data['revenue_money']), ',')) + "원"
        print(msg)
        line_alert.SendMessage(msg)

        if Ma5 > PrevClose and Ma10 > PrevClose and Ma21 > PrevClose:

            AllAmt = upbit.get_balance(coin_ticker) #현재 수량

            balances = myUpbit.SellCoinMarket(upbit,coin_ticker,AllAmt)
                            
            msg = coin_ticker + " 이평 조합 전략 봇 : 이평선 조건을 불만족하여 모두 매도처리 했어요!!"
            print(msg)
            line_alert.SendMessage(msg)


    else:
        print("잔고없음")

        if Ma5 < PrevClose and Ma10 < PrevClose and Ma21 < PrevClose:

            BuyMoney = InvestMoneyCell

            #원화 잔고를 가져온다
            won = float(upbit.get_balance("KRW"))
            print("# Remain Won :", won)
            time.sleep(0.04)
            
            #남은 원화보다 매수할 금액이 더 크다면 남은 원화만큼 매수한다.
            if BuyMoney > won:
                BuyMoney = won * 0.99 #수수료 및 슬리피지 감안!

            balances = myUpbit.BuyCoinMarket(upbit,coin_ticker,BuyMoney)

            msg = coin_ticker + " 이평 조합 전략 봇 : 이평선 조건 만족 하여 매수!!"
            print(msg)
            line_alert.SendMessage(msg)
            
        else:
        


            msg = coin_ticker + " 이평 조합 전략 봇 : 이평선 조건 불만족 하여 현금 보유!!"
            print(msg)
            line_alert.SendMessage(msg)
            











