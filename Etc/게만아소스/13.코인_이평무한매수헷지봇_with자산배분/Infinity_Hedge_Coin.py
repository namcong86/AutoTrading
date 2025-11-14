'''

관련 포스팅

코인 선물을 자산배분 처럼 투자? 이평무한매수헷지 전략 (비트코인 도미넌스)
https://blog.naver.com/zacra/223009649644

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

BOT_NAME = "INFINITY_HEDGE_BOT"

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


#선물 마켓에서 거래중인 모든 코인을 가져옵니다.
#Tickers = binanceX.fetch_tickers()

Tickers = ['BTC/USDT','ETH/USDT','BTCDOM/USDT']
#총 원금대비 설정 비율 
#아래처럼 0.5 로 셋팅하면 50%가 해당 전략에 할당된다는 이야기!
Invest_Rate = 0.5


#테스트를 위해 비트코인만 일단 체크해봅니다. 
#LovelyCoinList = ['BTC/USDT']

#매매 대상 코인 개수 
CoinCnt = len(Tickers) #len(LovelyCoinList)





#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
############# 해당 전략으로 매수할 종목 데이터 리스트 ####################
InfinityMaDataList = list()
#파일 경로입니다.
bot_file_path = "/var/autobot/Coin_" + BOT_NAME + ".json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(bot_file_path, 'r') as json_file:
        InfinityMaDataList = json.load(json_file)

except Exception as e:
    print("Exception by First")
################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#







###################################################
#설정할 레버리지!
set_leverage = 1

#########################-트레일링스탑 적용-#######################
TraillingStop = 1.0 / float(set_leverage)
TraillingStopRate = TraillingStop / 100.0


#타임프레임!
time_frame_st = 'd' # m: 분봉 h: 시간봉 d:일봉
now_time_frame = 1 # 분봉:1,3,5,15,30  시간봉:1,4  일봉:1


balance = binanceX.fetch_balance(params={"type": "future"})
time.sleep(0.1)

#pprint.pprint(balance)

MoneyDict = dict()

#파일 경로입니다.
money_file_path = "/var/autobot/Coin_" + BOT_NAME + "_Money.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(money_file_path, 'r') as json_file:
        MoneyDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")


#현재 평가금액을 구합니다.
TotalRealMoney =  float(balance['total']['USDT'])

print("TotalRealMoney ", TotalRealMoney)



if MoneyDict.get('TotalRealMoney') == None:
    MoneyDict['TotalRealMoney'] = TotalRealMoney

    with open(money_file_path, 'w') as outfile:
        json.dump(MoneyDict, outfile)   

    line_alert.SendMessage("!!!!!!!!!!!!!! First !!!!!! " + str(MoneyDict['TotalRealMoney']))



print("$$$$$$$$ MoneyDict['TotalRealMoney']", MoneyDict['TotalRealMoney'])


print("$$$$$$$$ TotalRealMoney", TotalRealMoney)


#시간 정보를 가져옵니다. 아침 9시의 경우 서버에서는 hour변수가 0이 됩니다.
time_info = time.gmtime()
hour = time_info.tm_hour
min = time_info.tm_min
print("TIME" , hour, ":" ,min)



#이전에 저장된 가격에서 3%이상 증가되었다면!!
if MoneyDict['TotalRealMoney'] * 1.005 <= TotalRealMoney :

    #그리고 저장!!!
    MoneyDict['TotalRealMoney'] = TotalRealMoney

    with open(money_file_path, 'w') as outfile:
        json.dump(MoneyDict, outfile)   

    line_alert.SendMessage("$$$$$$$$!!!!!!!!!!!!!! 0.5% UPUP!!!!!!  USDT:" + str(balance['total']['USDT']))

else:
    
        
    if min == 0:
        line_alert.SendMessage("$$$$$$$$!!!!!!!!!!!!!!NOW STATUS !!!!!!  USDT:" + str(balance['total']['USDT']))
        




#모든 선물 거래가능한 코인을 가져온다.
for ticker in Tickers:

    try: 

        if "/USDT" in ticker:
            Target_Coin_Ticker = ticker


            Target_Coin_Symbol = ticker.replace("/", "").replace(":USDT", "")


            amt_s = 0 
            amt_b = 0
            entryPrice_s = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.
            entryPrice_b = 0 #평균 매입 단가. 따라서 물을 타면 변경 된다.


            isolated = False #격리모드인지 

                            

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



      

      


                
            #종목 데이터
            PickCoinInfo = None

            #저장된 종목 데이터를 찾는다
            for CoinInfo in InfinityMaDataList:
                if CoinInfo['Ticker'] == Target_Coin_Ticker:
                    PickCoinInfo = CoinInfo
                    break



            if PickCoinInfo == None:
            
                #잔고가 없다 즉 처음이다!!!
                if abs(amt_b) == 0 and abs(amt_s) == 0:

                    InfinityDataDict = dict()
                    
                    InfinityDataDict['Ticker'] = Target_Coin_Ticker #종목 코드

                    InfinityDataDict['Round'] = 0    #현재 회차

                    InfinityDataDict['Long_WaterAmt'] = 0 #물탄 수량!
                    InfinityDataDict['Long_WaterPrice'] = 0 #물탄 가격!
                    InfinityDataDict['LossMoney'] = 0 #물탄 수량을 팔때 손해본 금액

                    InfinityDataDict['Short_Danta_Amt'] = 0 #숏 단타 수량!
                    InfinityDataDict['Short_Danta_Price'] = 0 #숏 단타 가격!
                    InfinityDataDict['Hedge_Amt'] = 0 #헤지 모드로 들어간 수량!


                    InfinityDataDict['IsTralling'] = 'N' 
                    InfinityDataDict['IsReady'] = 'Y'


                    InfinityMaDataList.append(InfinityDataDict) #데이터를 추가 한다!


                    msg = Target_Coin_Ticker + " 바이낸스 양방향 이평무한매수양방향봇 첫 시작!!!!"
                    print(msg) 
                    line_alert.SendMessage(msg) 


                    #파일에 저장
                    with open(bot_file_path, 'w') as outfile:
                        json.dump(InfinityMaDataList, outfile)
                        

        
            time.sleep(0.2)
            print("Target_Coin_Ticker" , Target_Coin_Ticker)

            

            time.sleep(0.05)
            #최소 주문 수량을 가져온다 
            minimun_amount = myBinance.GetMinimumAmount(binanceX,Target_Coin_Ticker)

            print("--- Target_Coin_Ticker:", Target_Coin_Ticker ," minimun_amount : ", minimun_amount)




            print(balance['USDT'])
            print("Total Money:",float(balance['USDT']['total']))
            print("Remain Money:",float(balance['USDT']['free']))


            leverage = 0  #레버리지

            #해당 코인 가격을 가져온다.
            coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)



            #해당 코인에 할당된 금액에 따른 최대 매수수량을 구해본다!
            Max_Amt = (float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(float(balance['USDT']['total']),coin_price,Invest_Rate))) * set_leverage) / float(CoinCnt)

            print("Max_Amt:", Max_Amt)

                                        
            Buy_Amt = Max_Amt / 60.0

            Buy_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker,Buy_Amt))


            #최소 주문 수량보다 작다면 이렇게 셋팅!
            if Buy_Amt < minimun_amount:
                Buy_Amt = minimun_amount



            #################################################################################################################
            #레버리지 셋팅
            if leverage != set_leverage:
                    
                try:
                    print(binanceX.fapiPrivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage}))
                except Exception as e:
                    print("Exception:", e)

            #################################################################################################################


            #################################################################################################################
            #교차 모드로 설정
            if isolated == True:
                try:
                    print(binanceX.fapiPrivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'CROSSED'}))
                except Exception as e:
                    print("Exception:", e)
            #################################################################################################################  





            #이제 데이터(InfinityMaDataList)는 확실히 있을 테니 본격적으로 트레이딩을 합니다!
            for CoinInfo in InfinityMaDataList:

                if CoinInfo['Ticker'] == Target_Coin_Ticker :

                    IsTime = False
                    
                    if time_frame_st == 'm': #분봉
                        if min % now_time_frame == 0:
                            IsTime = True
                    elif time_frame_st == 'h': #시간봉
                        if min == 0 and hour % now_time_frame == 0:
                            IsTime = True
                    else:
                        if min == 0 and hour == 0: #일봉
                            IsTime = True
                            
                    
                    #정해진 주기마다!!
                    if IsTime == True or CoinInfo.get("IsUpCandle") == None:

                        df = myBinance.GetOhlcv(binanceX,Target_Coin_Ticker, str(now_time_frame) + time_frame_st)



                        Now_Price = df['close'].iloc[-1]

                        CoinInfo['Now_Price'] = float(Now_Price)

                        #5일 이평선
                        CoinInfo['Ma5_before3'] = myBinance.GetMA(df,5,-4)
                        CoinInfo['Ma5_before'] = myBinance.GetMA(df,5,-3)
                        CoinInfo['Ma5'] = myBinance.GetMA(df,5,-2)

                        print("MA5",CoinInfo['Ma5_before3'], "->", CoinInfo['Ma5_before'], "-> ",CoinInfo['Ma5'])

                        #20일 이평선
                        CoinInfo['Ma20_before'] = myBinance.GetMA(df,20,-3)
                        CoinInfo['Ma20'] = myBinance.GetMA(df,20,-2)

                        print("MA20", CoinInfo['Ma20_before'], "-> ",CoinInfo['Ma20'])
                        

                        #양봉 캔들인지 여부
                        CoinInfo['IsUpCandle'] = 0

                        #시가보다 종가가 크다면 양봉이다
                        if df['open'].iloc[-2] <= df['close'].iloc[-2]:
                            CoinInfo['IsUpCandle'] = 1

                        print("IsUpCandle : ", CoinInfo['IsUpCandle'])


                        CoinInfo['Now_RSI'] = myBinance.GetRSI(df,14,-2)
                        CoinInfo['Before_Low'] = df['low'].iloc[-2]
                        CoinInfo['Before_High'] = df['high'].iloc[-2]
                        
                    

                        CoinInfo['IsReady'] = 'Y'

                        #파일에 저장
                        with open(bot_file_path, 'w') as outfile:
                            json.dump(InfinityMaDataList, outfile)

                    pprint.pprint(CoinInfo)



                        


                    ############ 매도 파트.... ##############
                    unrealizedProfit_s = 0 #미 실현 손익.
                    unrealizedProfit_s_f = 0
                    unrealizedProfit_b = 0 #미 실현 손익.
                    unrealizedProfit_b_f = 0

                    print("------")
                    #숏잔고
                    for posi in balance['info']['positions']:
                        if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'SHORT':

                            unrealizedProfit_s = posi['unrealizedProfit']
                            break


                    #롱 잔고
                    for posi in balance['info']['positions']:
                        if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':

                            unrealizedProfit_b = posi['unrealizedProfit']
                            break


                    #해당 코인 가격을 가져온다.
                    coin_price = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)

                    TotalRevenue = 0



                    if abs(amt_b) > 0:
                            

                            
                        unrealizedProfit_b_f = float(unrealizedProfit_b) * 0.70
                        if float(unrealizedProfit_b) < 0:
                            unrealizedProfit_b_f = float(unrealizedProfit_b) * 1.3

                        TotalRevenue += (float(unrealizedProfit_b_f) - float(CoinInfo['LossMoney'])) 


                    if abs(amt_s) > 0:
                    


                        unrealizedProfit_s_f = float(unrealizedProfit_s) * 0.70
                        if float(unrealizedProfit_s) < 0:
                            unrealizedProfit_s_f = float(unrealizedProfit_s) * 1.3


                        TotalRevenue += float(unrealizedProfit_s_f)





                    print(" ---- TotalRevenue:", TotalRevenue)
                    if min % 15 == 0:
                        line_alert.SendMessage(Target_Coin_Ticker + " 현재손익:" + str(TotalRevenue))


                    #트레일링 스탑 종료되었는지 체크!
                    if CoinInfo['IsTralling'] == 'Y' and abs(amt_b) <= minimun_amount:

                        #주문 정보를 읽어온다.
                        orders = binanceX.fetch_orders(Target_Coin_Ticker)

                        IsOrder = False
                        for order in orders:

                            if order['status'] == "open" and order['info']['positionSide'] == "LONG" and order['side'] == "sell":
                                IsOrder = True
                                break

                        if IsOrder == False:

                            msg = Target_Coin_Ticker + " 이평무한매수양방향봇 [롱] 트레일링 스탑도 종료!! (최종 [" + str(CoinInfo['Round']) + "] 라운드까지 진행)"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                            CoinInfo['Round'] = 0    #현재 회차

                            CoinInfo['Long_WaterAmt'] = 0 #물탄 수량!
                            CoinInfo['Long_WaterPrice'] = 0
                            
                            CoinInfo['LossMoney'] = 0 #물탄 수량을 팔때 손해본 금액

                            CoinInfo['Short_Danta_Amt'] = 0 #숏 단타 수량!
                            CoinInfo['Short_Danta_Price'] = 0
                            
                            CoinInfo['Hedge_Amt'] = 0 #헤지 모드로 들어간 수량!
                            CoinInfo['IsTralling'] = 'N' 
                            CoinInfo['IsReady'] = 'N'



                    #1회차 이상 매수된 상황이라면 익절 조건을 체크해서 익절 처리 해야 한다!
                    if CoinInfo['Round'] > 0 and abs(amt_b) > 0:





                        coin_eval_totalmoney = coin_price * abs(amt_b) #롱 코인 평가금!

                        #롱 수익율을 구한다!
                        revenue_rate_b = (coin_price - entryPrice_b) / entryPrice_b * 100.0


                        #목표 수익률을 구한다! 
                        '''
                        1회 :  10% + 1%
                        10회  8.5% + 1%
                        20회  7%
                        30회  5.5%
                        40회 : 4%
                        '''
                        TargetRate = (10.0 - CoinInfo['Round']*0.15) / float(set_leverage) / 100.0

                        #현재총평가금액은 물타기 손실금액을 반영한게 아니다.
                        #손실액이 현재 평가금액 대비 비중이 얼마인지 체크한다. 
                        PlusRate = float(CoinInfo['LossMoney']) / coin_eval_totalmoney

                        #숏 손익/ 롱 평가금 대비 비중을 구한다. 
                        ShortRate = (float(unrealizedProfit_s_f) / coin_eval_totalmoney) * -1.0
                        

                        #그래서 목표수익률이랑 손실액을 커버하기 위한 수익률을 더해준다! + 트레일링 스탑 기준도 더해서 수익 확보!
                        FinalRate = TargetRate + PlusRate + TraillingStopRate + ShortRate


                        


                        print("TargetRate:", TargetRate , "+ PlusRate:" ,PlusRate , "+ TraillingStopRate:", TraillingStopRate,"+ ShortRate:", ShortRate,"  -> FinalRate:" , FinalRate)
                        print("목표 수익률 : ", round(FinalRate*100.0,2) ,"% 현재 ",Target_Coin_Ticker," 수익률 : " ,  revenue_rate_b, "%")
                        #수익화할 가격을 구한다!
                        RevenuePrice = entryPrice_b * (1.0 + FinalRate) 

                        
                        print("목표 가격 : ", RevenuePrice ," 현재 가격 : ", coin_price)

                        #목표한 수익가격보다 현재가가 높다면 익절처리할 순간이다!
                        if coin_price >= RevenuePrice and (float(unrealizedProfit_b_f) + float(unrealizedProfit_s_f)) > 0:
                            
                            if abs(amt_s) > 0:

                                params = {
                                    'positionSide': 'SHORT'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', abs(amt_s), None, params)
                                

                                msg = Target_Coin_Ticker + " 이평무한매수봇 숏 모두 정리!!!!  [" + str(float(unrealizedProfit_s_f)) + "] 손익 확정!"
                                print(msg) 
                                line_alert.SendMessage(msg) 



                            if abs(amt_b) < minimun_amount * 2.0:
                                    


                                params = {
                                    'positionSide': 'LONG'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b), None, params)
                                

                                msg = Target_Coin_Ticker + " 이평무한매수봇 모두 팔아서 수익확정!!!!  [" + str(float(unrealizedProfit_b_f)) + "] 수익 조으다! (현재 [" + str(CoinInfo['Round']) + "] 라운드까지 진행되었고 모든 수량 매도 처리! )"
                                print(msg) 
                                line_alert.SendMessage(msg) 

    
                                CoinInfo['Round'] = 0    #현재 회차

                                CoinInfo['Long_WaterAmt'] = 0 #물탄 수량!
                                CoinInfo['Long_WaterPrice'] = 0
                                CoinInfo['LossMoney'] = 0 #물탄 수량을 팔때 손해본 금액

                                CoinInfo['Short_Danta_Amt'] = 0 #숏 단타 수량!
                                CoinInfo['Short_Danta_Price'] = 0

                                CoinInfo['Hedge_Amt'] = 0 #헤지 모드로 들어간 수량!
                                CoinInfo['IsTralling'] = 'N' 
                                CoinInfo['IsReady'] = 'N'


                                #파일에 저장
                                with open(bot_file_path, 'w') as outfile:
                                    json.dump(InfinityMaDataList, outfile)

                                
                            else:

                                #절반은 바로 팔고 절반은 트레일링 스탑으로 처리한다!!!
                                HalfAmt = float(binanceX.amount_to_precision(Target_Coin_Ticker,(abs(amt_b) * 0.5)))


                                params = {
                                    'positionSide': 'LONG'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', HalfAmt, None, params)


                                myBinance.create_trailing_sell_order_Long(binanceX,Target_Coin_Ticker,abs(amt_b) - HalfAmt,None,TraillingStop)

                            

                                msg = Target_Coin_Ticker + " 이평무한매수봇 절반 팔아서 수익확정!!!!  [" + str(float(unrealizedProfit_b_f)*0.5) + "] 수익 조으다! (현재 [" + str(CoinInfo['Round']) + "] 라운드까지 진행되었고 절반 익절 후 트레일링 스탑 시작!!)"
                                print(msg) 
                                line_alert.SendMessage(msg) 

                                CoinInfo['IsTralling'] = 'Y' #트레일링 스탑 시작!

                                #파일에 저장
                                with open(bot_file_path, 'w') as outfile:
                                    json.dump(InfinityMaDataList, outfile)




                    #매수는 타임 프레임마다!!
                    if CoinInfo['IsReady'] == 'Y' and CoinInfo['IsTralling'] =='N':






                        #######################################################################
                        if CoinInfo['Ma20'] > CoinInfo['Now_Price']: #20선 밑에 있다면 1/4의 금액만큼 헷징들어간다! 

                            if CoinInfo['Hedge_Amt'] == 0 and CoinInfo['Round'] >= 4:


                                BuyRound = float(CoinInfo['Round'])/4.0 #물탈 회수

                                ShortBuyAmt = Buy_Amt * BuyRound

                                if ShortBuyAmt < minimun_amount:
                                    ShortBuyAmt = minimun_amount

                                AbleAmt = (Buy_Amt * 10.0) - CoinInfo['Short_Danta_Amt']

                                if AbleAmt < ShortBuyAmt:
                                    ShortBuyAmt = AbleAmt


                                CoinInfo['Hedge_Amt'] = ShortBuyAmt


                                params = {
                                    'positionSide': 'SHORT'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', ShortBuyAmt, None, params)



                                CoinInfo['Hedge_Amt'] = data['amount']

                                msg = Target_Coin_Ticker + " 헤징 시작!!!!"
                                print(msg) 
                                line_alert.SendMessage(msg) 
                                ###########################################################################################
                            
                                
                        else:
                            if CoinInfo['Hedge_Amt'] != 0 and  CoinInfo['Ma20'] < CoinInfo['Now_Price'] and abs(amt_s) > 0:


                                if CoinInfo['Hedge_Amt'] > abs(amt_s):
                                    CoinInfo['Hedge_Amt'] = abs(amt_s)


                                params = {
                                    'positionSide': 'SHORT'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', CoinInfo['Hedge_Amt'], None, params)
                                #print(binanceX.create_market_sell_order(Target_Coin_Ticker, CoinInfo['Long_WaterAmt'], params))
                                


                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if unrealizedProfit_s_f < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                    LossMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Hedge_Amt'] / float(abs(amt_s)))
                                    CoinInfo['LossMoney'] += LossMoney

                                    msg = Target_Coin_Ticker + " 헤징을 풉니다. 그 수량만큼 매도합니다 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Hedge_Amt'] / float(abs(amt_s)))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if CoinInfo['LossMoney'] > 0:
                                        CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다



                                    msg = Target_Coin_Ticker + " 헤징을 풉니다. 그 수량만큼 매도합니다 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 


                                CoinInfo['Hedge_Amt'] = 0 #팔았으니 0으로 초기화!







                        if CoinInfo['Round'] >= 40:

                            if CoinInfo['Ma5_before'] > CoinInfo['Ma5']:


                                HalfAmt = abs(amt_b) * 0.5


                                params = {
                                    'positionSide': 'LONG'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', HalfAmt, None, params)
                                #print(binanceX.create_market_sell_order(Target_Coin_Ticker, HalfAmt, params))
                                

                                CoinInfo['Round'] = 21 #라운드는 절반을 팔았으니깐 21회로 초기화

                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if unrealizedProfit_b_f < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                    LossMoney = abs(unrealizedProfit_b_f) * (float(HalfAmt) / float(abs(amt_b)))
                                    CoinInfo['LossMoney'] += LossMoney

                                    msg = Target_Coin_Ticker + "롱 40회가 소진되어 절반 손절합니다! 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 롱 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(unrealizedProfit_b_f) * (float(HalfAmt) / float(abs(amt_b)))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if CoinInfo['LossMoney'] > 0:
                                        CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다


                                    msg = Target_Coin_Ticker + "롱 40회가 소진되어 절반 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 



                        IsLongBuyGo = False #매수 하는지!

                        #라운드에 따라 매수 조건이 다르다!
                        if CoinInfo['Round'] <= 10-1:

        
                            #여기는 무조건 매수
                            IsLongBuyGo = True
       

                        elif CoinInfo['Round'] <= 20-1:


                            #현재가가 5일선 위에 있을 때만 매수
                            if CoinInfo['Ma5'] < CoinInfo['Now_Price']:
                                IsLongBuyGo = True             


                        elif CoinInfo['Round'] <= 30-1:

                            #20선 5일선 위에 있을때만!
                            if CoinInfo['Ma20'] < CoinInfo['Now_Price'] and CoinInfo['Ma5'] < CoinInfo['Now_Price']:
                                IsLongBuyGo = True


                        elif CoinInfo['Round'] <= 40-1:

                            #현재가가 5/20일선 위에 있고 그리고 5일선, 20일선 둘다 증가추세에 있을 때만 매수
                            if CoinInfo['Ma20'] < CoinInfo['Now_Price'] and CoinInfo['Ma5'] < CoinInfo['Now_Price'] and CoinInfo['Ma5_before'] < CoinInfo['Ma5'] and CoinInfo['Ma20_before'] < CoinInfo['Ma20']:
                                IsLongBuyGo = True





                        #한 회차 매수 한다!!
                        if IsLongBuyGo == True:

 
                            CoinInfo['Round'] += 1 #라운드 증가!


                            params = {
                                'positionSide': 'LONG'
                            }
                            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', Buy_Amt, None, params)
                            #print(binanceX.create_market_buy_order(Target_Coin_Ticker, BuyAmt, params))
                            

                            msg = Target_Coin_Ticker + " 롱 이평무한매수양방향봇 " + str(CoinInfo['Round']) + "회차 매수 완료!"
                            print(msg) 
                            line_alert.SendMessage(msg) 






               

                        #########################################################################################


                        #위 로직 완료하면 N으로 바꾸고 다음 타임 프레임 기다림!
                        CoinInfo['IsReady'] = 'N' 

                        #파일에 저장
                        with open(bot_file_path, 'w') as outfile:
                            json.dump(InfinityMaDataList, outfile)
                        
                            


                    ####################################################################################
                    ################## 위 정규 매수 로직과는 별개로 특별 물타기 로직을 체크하고 제어한다! #############

                    #이평선이 꺾여서 특별히 물탄 경우 수량이 0이 아닐꺼고 즉 여기는  물을 탄 상태이다!
                    if CoinInfo['Long_WaterAmt'] != 0 and abs(amt_b) > 0:

                        if CoinInfo['Long_WaterAmt'] > abs(amt_b):
                            CoinInfo['Long_WaterAmt'] = abs(amt_b)


                        TargetRate = ((CoinInfo['Before_High'] / CoinInfo['Before_Low']) - 1.0)

                        #2%
                        if TargetRate < 0.02 / float(set_leverage):
                            TargetRate = 0.02 / float(set_leverage)

                        #5%
                        if TargetRate > 0.05 / float(set_leverage):
                            TargetRate = 0.05 / float(set_leverage)


                        RevenuePrice = CoinInfo['Long_WaterPrice'] * (1.0 + TargetRate)

                        if RevenuePrice <= coin_price:

                            params = {
                                'positionSide': 'LONG'
                            }
                            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', CoinInfo['Long_WaterAmt'], None, params)
                            #print(binanceX.create_market_sell_order(Target_Coin_Ticker, CoinInfo['Long_WaterAmt'], params))
                            


                            #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                            if unrealizedProfit_b_f < 0:
                                #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                LossMoney = abs(unrealizedProfit_b_f) * (CoinInfo['Long_WaterAmt'] / float(abs(amt_b)))
                                CoinInfo['LossMoney'] += LossMoney

                                msg = Target_Coin_Ticker + "롱 평단을 확 낮추기 위한 이평무한매수양방향봇 물탔는데 익절구간이라 그 수량만큼 매도합니다 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                print(msg) 
                                line_alert.SendMessage(msg) 

                            #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                            else:

                                #이득본 금액도 계산해보자
                                RevenuMoney = abs(unrealizedProfit_b_f) * (CoinInfo['Long_WaterAmt'] / float(abs(amt_b)))

                                #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                if CoinInfo['LossMoney'] > 0:
                                    CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다



                                msg = Target_Coin_Ticker + "롱 평단을 확 낮추기 위한 이평무한매수양방향봇 물탔는데 익절구간이라 그 수량만큼 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                print(msg) 
                                line_alert.SendMessage(msg) 


                            CoinInfo['Long_WaterAmt'] = 0 #팔았으니 0으로 초기화!
                            CoinInfo['Long_WaterPrice'] = 0


                        else:
    
                            CutPrice = CoinInfo['Long_WaterPrice'] * (1.0 - TargetRate*0.8)


                            if CutPrice >= coin_price:

                                params = {
                                    'positionSide': 'LONG'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', CoinInfo['Long_WaterAmt'], None, params)
                                #print(binanceX.create_market_sell_order(Target_Coin_Ticker, CoinInfo['Long_WaterAmt'], params))
                                


                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if unrealizedProfit_b_f < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                    LossMoney = abs(unrealizedProfit_b_f) * (CoinInfo['Long_WaterAmt'] / float(abs(amt_b)))
                                    CoinInfo['LossMoney'] += LossMoney

                                    msg = Target_Coin_Ticker + "롱 평단을 확 낮추기 위한 이평무한매수양방향봇 물탔는데 손절구간이라 그 수량만큼 매도합니다 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(unrealizedProfit_b_f) * (CoinInfo['Long_WaterAmt'] / float(abs(amt_b)))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if CoinInfo['LossMoney'] > 0:
                                        CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다



                                    msg = Target_Coin_Ticker + "롱 평단을 확 낮추기 위한 이평무한매수양방향봇 물탔는데 손절구간이라 그 수량만큼 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 
                                    

                                CoinInfo['Long_WaterAmt'] = 0 #팔았으니 0으로 초기화!
                                CoinInfo['Long_WaterPrice'] = 0


                    else:
                        #고가를 돌파했다면 물타기 고고!!!!
                        if CoinInfo['Before_High'] < coin_price and CoinInfo['Now_RSI'] < 50 and CoinInfo['Ma5'] < CoinInfo['Ma20'] and CoinInfo['Before_Low'] < CoinInfo['Ma5'] and CoinInfo['Round'] >= 4 and CoinInfo['Long_WaterAmt'] == 0:


                            BuyRound = float(CoinInfo['Round'])/4.0 #물탈 회수

                            WaterAmt = Buy_Amt * BuyRound

                            if WaterAmt < minimun_amount:
                                WaterAmt = minimun_amount


                            params = {
                                'positionSide': 'LONG'
                            }
                            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', WaterAmt, None, params)
                            
                            #data = binanceX.create_market_buy_order(Target_Coin_Ticker, BuyAmt, params)


                            CoinInfo['Long_WaterAmt'] = float(data['amount'])
                            CoinInfo['Long_WaterPrice'] = float(data['price'])

                            msg = Target_Coin_Ticker + "  변곡이 발생! 평단을 확 낮추기 위한 이평무한매수양방향봇 물을 탑니다!! 롱 [" + str(BuyRound) + "] 회차 만큼의 수량을 추가 했어요!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                    
                    #파일에 저장
                    with open(bot_file_path, 'w') as outfile:
                        json.dump(InfinityMaDataList, outfile)







                    #이평선이 꺾여서 특별히 물탄 경우 수량이 0이 아닐꺼고 즉 여기는  물을 탄 상태이다!
                    if CoinInfo['Short_Danta_Amt'] != 0 and abs(amt_s) > 0:

                        if CoinInfo['Short_Danta_Amt'] > abs(amt_s):
                            CoinInfo['Short_Danta_Amt'] = abs(amt_s)


                        TargetRate = ((CoinInfo['Before_High'] / CoinInfo['Before_Low']) - 1.0)

                        #1.5%
                        if TargetRate < 0.015/ float(set_leverage):
                            TargetRate = 0.015/ float(set_leverage)
                        #3%
                        if TargetRate > 0.03/ float(set_leverage):
                            TargetRate = 0.03/ float(set_leverage)

                        RevenuePrice = CoinInfo['Short_Danta_Price'] * (1.0 - TargetRate)

                        if RevenuePrice >= coin_price:

                            params = {
                                'positionSide': 'SHORT'
                            }
                            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', CoinInfo['Short_Danta_Amt'], None, params)


                            #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                            if unrealizedProfit_s_f < 0:
                                #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                LossMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Short_Danta_Amt'] / float(abs(amt_s)))
                                CoinInfo['LossMoney'] += LossMoney

                                msg = Target_Coin_Ticker + " 숏 단타! 익절구간이라 그 수량만큼 매도합니다 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                print(msg) 
                                line_alert.SendMessage(msg) 

                            #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                            else:

                                #이득본 금액도 계산해보자
                                RevenuMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Short_Danta_Amt'] / float(abs(amt_s)))

                                #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                if CoinInfo['LossMoney'] > 0:
                                    CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다



                                msg = Target_Coin_Ticker + "숏 단타! 익절구간이라 그 수량만큼 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                print(msg) 
                                line_alert.SendMessage(msg) 


                            CoinInfo['Short_Danta_Amt'] = 0 #팔았으니 0으로 초기화!
                            CoinInfo['Short_Danta_Price'] = 0


                        else:
    
                            CutPrice = CoinInfo['Short_Danta_Price'] * (1.0 + TargetRate*0.8)

                            if CutPrice <= coin_price:

                                params = {
                                    'positionSide': 'SHORT'
                                }
                                data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', CoinInfo['Short_Danta_Amt'], None, params)


                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if unrealizedProfit_s_f < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                    LossMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Short_Danta_Amt'] / float(abs(amt_s)))
                                    CoinInfo['LossMoney'] += LossMoney

                                    msg = Target_Coin_Ticker + " 숏 단타! 손절구간이라 그 수량만큼 매도합니다! 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(CoinInfo['LossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(unrealizedProfit_s_f) * (CoinInfo['Short_Danta_Amt'] / float(abs(amt_s)))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if CoinInfo['LossMoney'] > 0:
                                        CoinInfo['LossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다



                                    msg = Target_Coin_Ticker + " 숏 단타! 손절구간이라 그 수량만큼 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 
                                    

                                CoinInfo['Short_Danta_Amt'] = 0 #팔았으니 0으로 초기화!
                                CoinInfo['Short_Danta_Price'] = 0


                    else:
                        #저가를 돌파했다면 단타 고고
                        if CoinInfo['Before_Low'] > coin_price and CoinInfo['Now_RSI'] > 50 and CoinInfo['Ma5'] > CoinInfo['Ma20'] and CoinInfo['Before_High'] > CoinInfo['Ma5'] and CoinInfo['Round'] >= 4 and CoinInfo['Short_Danta_Amt'] == 0:



                            BuyRound = float(CoinInfo['Round'])/5.0 #물탈 회수

                            ShortBuyAmt = Buy_Amt * BuyRound


                            if ShortBuyAmt < minimun_amount:
                                ShortBuyAmt = minimun_amount

                            AbleAmt = (Buy_Amt * 10.0) - CoinInfo['Hedge_Amt']

                            if AbleAmt < ShortBuyAmt:
                                ShortBuyAmt = AbleAmt


                            CoinInfo['Short_Danta_Amt'] = ShortBuyAmt


                            params = {
                                'positionSide': 'SHORT'
                            }
                            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', ShortBuyAmt, None, params)
                            
                            #data = binanceX.create_market_buy_order(Target_Coin_Ticker, BuyAmt, params)


                            CoinInfo['Short_Danta_Amt'] = float(data['amount'])
                            CoinInfo['Short_Danta_Price'] = float(data['price'])

                            msg = Target_Coin_Ticker + "  변곡이 발생! 숏 단타!!!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                    
                    #파일에 저장
                    with open(bot_file_path, 'w') as outfile:
                        json.dump(InfinityMaDataList, outfile)
                            

                    ####################################################################################


    except Exception as e:
        print("Exception:", e)



pprint.pprint(InfinityMaDataList)




