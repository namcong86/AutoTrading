'''

관련 포스팅

TQQQ 투자 전략! 닷컴 버블, 금융 위기 포함해서 백테스팅해보기 (레버리지 투자 전략 검증하기 feat.ChatGPT)
https://blog.naver.com/zacra/223102715455

위 포스팅을 꼭 참고하세요!!! 

'''
import KIS_Common as Common
import KIS_API_Helper_US as KisUS
import json
import pprint
import line_alert
import time


Common.SetChangeMode("VIRTUAL")



BOT_NAME = Common.GetNowDist() + "_3xBothStrategyBot"


##############################################################################
##########################투자 비중 설정 방법 A ##################################
##############################################################################
'''
df = Common.GetOhlcv("US","QQQ", 250)

Ma200_before2 = Common.GetMA(df,200,-3)
Ma200_before = Common.GetMA(df,200,-2)


Status = "MIDDLE"
if Ma200_before < df['close'].iloc[-2] and Ma200_before2 < Ma200_before:
    Status = "UP"
elif Ma200_before > df['close'].iloc[-2] and Ma200_before2 > Ma200_before:
    Status = "DOWN"
else:
    Status = "MIDDLE"



#투자할 종목!

InvestStockList = list()


#3배 레버리지 ETF

InvestDataDict = dict()
InvestDataDict['ticker'] = "TQQQ" 

if Status == "UP":
    InvestDataDict['rate'] = 0.4
elif Status == "DOWN":
    InvestDataDict['rate'] = 0.3
else:
    InvestDataDict['rate'] = 0.35


InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXL" 

if Status == "UP":
    InvestDataDict['rate'] = 0.4
elif Status == "DOWN":
    InvestDataDict['rate'] = 0.3
else:
    InvestDataDict['rate'] = 0.35

InvestStockList.append(InvestDataDict)


#3배 인버스 ETF

InvestDataDict = dict()
InvestDataDict['ticker'] = "SQQQ" 

if Status == "UP":
    InvestDataDict['rate'] = 0.1
elif Status == "DOWN":
    InvestDataDict['rate'] = 0.2
else:
    InvestDataDict['rate'] = 0.15

InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXS" 

if Status == "UP":
    InvestDataDict['rate'] = 0.1
elif Status == "DOWN":
    InvestDataDict['rate'] = 0.2
else:
    InvestDataDict['rate'] = 0.15

InvestStockList.append(InvestDataDict)
'''


##############################################################################
##############################################################################
##############################################################################


##############################################################################
##############################################################################
#################위 A코드를 사용하거나 아래 B코드를 사용하세요 ^^ #########################
##############################################################################
##############################################################################



##############################################################################
##########################투자 비중 설정 방법 B ##################################
##############################################################################

#'''

InvestStockList = list()

#3배 레버리지 ETF

InvestDataDict = dict()
InvestDataDict['ticker'] = "TQQQ" 
InvestDataDict['rate'] = 0.35
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXL" 
InvestDataDict['rate'] = 0.35
InvestStockList.append(InvestDataDict)

#3배 인버스 ETF

InvestDataDict = dict()
InvestDataDict['ticker'] = "SQQQ" 
InvestDataDict['rate'] = 0.15
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "SOXS" 
InvestDataDict['rate'] = 0.15
InvestStockList.append(InvestDataDict)

#'''

##############################################################################
##############################################################################
##############################################################################

##############################################################################
################################투자 비중 설정 끝!################################
##############################################################################

pprint.pprint(InvestStockList)


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
############# 해당 전략으로 매수한 종목 데이터 리스트 ####################
InfinityUpgradeDataList = list()
#파일 경로입니다.
bot_file_path = "/var/autobot/UsStock_" + BOT_NAME + ".json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(bot_file_path, 'r') as json_file:
        InfinityUpgradeDataList = json.load(json_file)

except Exception as e:
    print("Exception by First")
################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#


#계좌 잔고를 가지고 온다!
Balance = KisUS.GetBalance()



print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")
#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.4

#기준이 되는 내 총 평가금액
TotalMoney = float(Balance['TotalMoney']) * InvestRate
print("TotalMoney:", str(format(round(TotalMoney), ',')))


print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisUS.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
    

#마켓이 열렸는지 여부~!
IsMarketOpen = KisUS.IsMarketOpen()

#장이 열렸을 때!
if IsMarketOpen == True:


    for stock_data in InvestStockList:

        stock_code = stock_data['ticker']

        print("\n----stock_code: ", stock_code)

        #각 종목당 투자할 금액! 
        StockMoney = TotalMoney * stock_data['rate']
        print("StockMoney:", str(format(round(StockMoney), ',')))

        #주식(ETF) 정보~
        stock_name = ""
        stock_amt = 0 #수량
        stock_avg_price = 0 #평단
        stock_eval_totalmoney = 0 #총평가금액!
        stock_revenue_rate = 0 #종목 수익률
        stock_revenue_money = 0 #종목 수익금


        #매수된 상태라면 정보를 넣어준다!!!
        for my_stock in MyStockList:
            if my_stock['StockCode'] == stock_code:
                stock_name = my_stock['StockName']
                stock_amt = int(my_stock['StockAmt'])
                stock_avg_price = float(my_stock['StockAvgPrice'])
                stock_eval_totalmoney = float(my_stock['StockNowMoney'])
                stock_revenue_rate = float(my_stock['StockRevenueRate'])
                stock_revenue_money = float(my_stock['StockRevenueMoney'])

                break
                

        #현재가
        CurrentPrice = KisUS.GetCurrentPrice(stock_code)

            
        #종목 데이터
        PickStockInfo = None

        #저장된 종목 데이터를 찾는다
        for StockInfo in InfinityUpgradeDataList:
            if StockInfo['StockCode'] == stock_code:
                PickStockInfo = StockInfo
                break

        #PickStockInfo 이게 없다면 매수되지 않은 처음 상태이거나 이전에 손으로 매수한 종목인데 해당 봇으로 돌리고자 할 때!
        if PickStockInfo == None:
            #잔고가 없다 즉 처음이다!!!
            if stock_amt == 0:

                if stock_code == 'TQQQ' or stock_code == 'SOXL':

                    InfinityDataDict = dict()
                    
                    InfinityDataDict['StockCode'] = stock_code #종목 코드
                    InfinityDataDict['MaxRound'] = 40 #맥스 회차!
                    InfinityDataDict['Round'] = 0    #현재 회차
                    InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그

                    InfinityUpgradeDataList.append(InfinityDataDict) #데이터를 추가 한다!

                else: #인버스 SQQQ SOXS의 경우,,

                    InfinityDataDict = dict()
                    
                    InfinityDataDict['StockCode'] = stock_code #종목 코드
                    InfinityDataDict['MaxRound'] = 1 #맥스 회차!
                    InfinityDataDict['Round'] = 0     #현재 회차
                    InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그

                    InfinityUpgradeDataList.append(InfinityDataDict) #데이터를 추가 한다!


                msg = stock_code + " 양방향3배전략봇 첫 시작!!!!"
                print(msg) 
                line_alert.SendMessage(msg) 
                
            #데이터가 없는데 잔고가 있다? 이미 이 봇으로 트레이딩 하기전에 매수된 종목!
            else:
                print("Exist")

                if stock_code == 'TQQQ' or stock_code == 'SOXL':


                    #캔들 데이터를 읽는다 분할 수를 정하기 위해!!!
                    df = Common.GetOhlcv("US",stock_code, 1000)

                    Ma200_before = Common.GetMA(df,200,-2)
                    Ma100_before = Common.GetMA(df,100,-2)
                    Ma60_before = Common.GetMA(df,60,-2)
                    Ma20_before = Common.GetMA(df,20,-2)
                
                    MaxRound = 40

                    if Ma200_before > df['close'].iloc[-2]: #200일선 아래에 있을 땐 35분할
                        MaxRound = 35
                        
                    else: # 200일선 위에 있을 땐 

                        
                        st_num = 55
                        
                        if stock_code == 'TQQQ':
                            st_num = 54
                            
                                
                        MaxRound = st_num
                    
            
                        if Ma100_before <= df['close'].iloc[-2]:
                            MaxRound -= 15


                        if Ma60_before <= df['close'].iloc[-2]:
                            MaxRound -= 8


                        if Ma20_before <= df['close'].iloc[-2]:
                            MaxRound -= 7     


                        if MaxRound == st_num:
                            MaxRound = 35    



                    InfinityDataDict = dict()
                    
                    InfinityDataDict['StockCode'] = stock_code #종목 코드
                    InfinityDataDict['MaxRound'] = MaxRound #맥스 회차!
                    
                    #분할된 투자금!
                    StMoney = StockMoney / InfinityDataDict['MaxRound']
                    InfinityDataDict['Round'] = int(stock_eval_totalmoney / StMoney)    #현재 회차 - 매수된 금액을 분할된 단위 금액으로 나누면 회차가 나온다!
                    InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그


                    InfinityUpgradeDataList.append(InfinityDataDict) #데이터를 추가 한다!

                else: #인버스 SQQQ SOXS의 경우,,

                    InfinityDataDict = dict()
                    
                    InfinityDataDict['StockCode'] = stock_code #종목 코드
                    InfinityDataDict['MaxRound'] = 1 #맥스 회차!
                    InfinityDataDict['Round'] = 1    #현재 회차 
                    InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그

                    InfinityUpgradeDataList.append(InfinityDataDict) #데이터를 추가 한다!


                msg = stock_code + " 기존에 매수한 종목을 양방향3배전략봇으로 변경해서 트레이딩 첫 시작!!!! " + str(InfinityDataDict['Round']) + "회차로 세팅 완료!"
                print(msg) 
                line_alert.SendMessage(msg) 

            #파일에 저장
            with open(bot_file_path, 'w') as outfile:
                json.dump(InfinityUpgradeDataList, outfile)
                

        #이제 데이터(InfinityUpgradeDataList)는 확실히 있을 테니 본격적으로 트레이딩을 합니다!
        for StockInfo in InfinityUpgradeDataList:

            if StockInfo['StockCode'] == stock_code:
                


                #어떤 이유에서 매수 실패했거나 수동으로 종목 매도한 경우 보유 수량이 0일텐데 만약 그렇다면 봇에서도 0으로 데이터를 변경해준다!
                if stock_amt == 0 and StockInfo['Round'] > 0 :
                    StockInfo['Round'] = 0

                    msg = stock_code + " 양방향3배전략봇 " + str(StockInfo['Round']) + "회차 매수 되었다고 되어있지만 매수수량이 1개도 없는 것으로 파악!!! 매수시 로그 확인 필요! 봇에서는 매수 안되었다고 셋!"
                    print(msg) 
                    line_alert.SendMessage(msg) 


                #매수는 장이 열렸을 때 1번만 해야 되니깐! 안의 로직을 다 수행하면 N으로 바꿔준다! 
                if StockInfo['IsReady'] == 'Y' :


                    #캔들 데이터를 읽는다
                    df = Common.GetOhlcv("US",stock_code, 1000)

                    #5일 이평선
                    Ma5_before2 = Common.GetMA(df,5,-3)
                    Ma5_before = Common.GetMA(df,5,-2)
                    Ma5 = Common.GetMA(df,5,-1)

                    print("MA5 ", Ma5_before, "-> ",Ma5)

                    #200일 이평선
                    Ma200_before2 = Common.GetMA(df,200,-3)
                    Ma200_before = Common.GetMA(df,200,-2)
                    Ma200 = Common.GetMA(df,200,-1)

                    print("MA200 ",Ma200)

                    
                    #RSI14
                    Rsi14= Common.GetRSI(df,14,-2)
                    
                    
                    Ma100_before = Common.GetMA(df,100,-2)
                    Ma60_before2 = Common.GetMA(df,60,-3)
                    Ma60_before = Common.GetMA(df,60,-2)
                    
                    Ma20_before2 = Common.GetMA(df,20,-3)
                    Ma20_before = Common.GetMA(df,20,-2)
                    
                    
                    #3일 이평선
                    Ma3_before2 = Common.GetMA(df,3,-3)
                    Ma3_before = Common.GetMA(df,3,-2)
                    
                
                                
                    Disparity5 = (df['close'].iloc[-2]/Common.GetMA(df,5,-2))*100.0 #전일 종가 기준 5선 이격도
                            
                    #레버리지의 경우!
                    if stock_code == 'TQQQ' or stock_code == 'SOXL':

                        

                        #1회차 이상 매수된 상황이라면 익절 조건을 체크해서 익절 처리 해야 한다!
                        if StockInfo['Round'] > 0 :
                            


                            #목표 수익률을 구한다! 
                            TargetRate = 10.0  / 100.0

                            FinalRate = TargetRate 

                            #수익화할 가격을 구한다!
                            RevenuePrice = stock_avg_price * (1.0 + FinalRate) 
                            
                            if CurrentPrice >= RevenuePrice or StockInfo['Round'] >= StockInfo['MaxRound']:

                                
                                st_disparity = 102
                                
                                if stock_code == 'TQQQ':
                                    st_disparity = 103


                                #목표한 수익가격보다 현재가가 높다면 익절처리할 순간이다!
                                if CurrentPrice >= RevenuePrice and Disparity5 > st_disparity:
                                    
            
                                    #현재가보다 아래에 매도 주문을 넣음으로써 시장가로 매도효과!
                                    pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,stock_amt,CurrentPrice*0.99))


                                    msg = stock_code + " 양방향3배전략봇 모두 팔아서 수익확정!!!!  [" + str(stock_revenue_money) + "] 수익 조으다! (현재 [" + str(StockInfo['Round']) + "] 라운드까지 진행되었고 모든 수량 매도 처리! )"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                    #전량 매도 모두 초기화! 
                                    StockInfo['Round'] = 0


                                    #파일에 저장
                                    with open(bot_file_path, 'w') as outfile:
                                        json.dump(InfinityUpgradeDataList, outfile)
                                        
                                        
                                else:
                                    
                                    
                                    if StockInfo['Round'] >= StockInfo['MaxRound']: #쿼터 손절 들어간다!
                                        
                                        CutR = 8.0

                                        if Ma60_before2 > Ma60_before and Ma20_before2 > Ma20_before:
                                            CutR = 6.0


                                        StockInfo['Round'] -= int(StockInfo['Round']/CutR)
                                        CutAmt = int(stock_amt / CutR)

                                        pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,CutAmt,CurrentPrice*0.99))


                                        msg = stock_code + " 양방향3배전략봇 일부 손절!!!!  [" + str(stock_revenue_money/CutR) + "] 손익 확정! (현재 [" + str(StockInfo['Round']) + "] 라운드로 셋!)"
                                        print(msg) 
                                        line_alert.SendMessage(msg) 


                                        #파일에 저장
                                        with open(bot_file_path, 'w') as outfile:
                                            json.dump(InfinityUpgradeDataList, outfile)
                                            
                                            
                            else:
                                


                                if StockInfo['Round'] < StockInfo['MaxRound']:
                                    
                                    IsBuyGo = False
                                    
                                    ##########################################################################################
                                    ##########################################################################################
                                    ############### 블로그 내용 수정 예정이지만 매수는 100일선 아래에서 3일선이 증가될때로 변경 되었습니다 ################
                                    ##########################################################################################
                                    ##########################################################################################
                        
                                    if Ma100_before > df['close'].iloc[-2]: #어제 종가가 100일선보다 작은 하락장!

                                        if Ma3_before2 < Ma3_before: #전일까지 3일선이 증가했다면 그때만 매수!!
                                            IsBuyGo = True

                                    else: #200일선 위에 있는 상승장엔 기존 처럼 매일 매수!
                                        
                                        IsBuyGo = True
                

                                    if Rsi14 >= 80: 
                                        IsBuyGo = False

                            
                                    st_disparity = 97
                                    
                                    if stock_code == 'SOXL':
                                        st_disparity = 108
                                        
                        
                                    #200일선 위에 있다가 아래로 종가가 떨어지면... (추가적으로 이격도 체크)
                                    if (Ma200_before2 < df['close'].iloc[-3] and Ma200_before > df['close'].iloc[-2]) and Disparity5 < st_disparity:
                                    

                                        #현재가보다 아래에 매도 주문을 넣음으로써 시장가로 매도효과!
                                        pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,stock_amt,CurrentPrice*0.99))


                                        msg = stock_code + " 양방향3배전략봇 하락장 진입!!!!!  [" + str(stock_revenue_money) + "] 손익 확정!! (현재 [" + str(StockInfo['Round']) + "] 라운드까지 진행되었고 모든 수량 매도 처리! )"
                                        print(msg) 
                                        line_alert.SendMessage(msg) 

                                        #전량 매도 모두 초기화! 
                                        StockInfo['Round'] = 0


                                        #파일에 저장
                                        with open(bot_file_path, 'w') as outfile:
                                            json.dump(InfinityUpgradeDataList, outfile)
                                            
                                        IsBuyGo = False
                                            
                        

                                    #한 회차 매수 한다!!
                                    if IsBuyGo == True:

                                        StockInfo['Round'] += 1 #라운드 증가!


                                        time.sleep(10.0)
                        
                                        #분할된 투자금!
                                        StMoney = StockMoney / StockInfo['MaxRound']


                                        BuyAmt = int(StMoney / CurrentPrice)
                                        
                                        #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                                        if BuyAmt < 1:
                                            BuyAmt = 1

                                        #시장가 주문을 넣는다!
                                        #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수!
                                        pprint.pprint(KisUS.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice*1.01))


                                        msg = stock_code + " 양방향3배전략봇 " + str(StockInfo['Round']) + "회차 매수 완료!"
                                        print(msg) 
                                        line_alert.SendMessage(msg) 
        
                    
                    else: #인버스의 경우
                        
                        #1회차 이상 매수된 상황이라면 인버스의 경우 조건 체크해서 매도한다.
                        if StockInfo['Round'] > 0 :

                            IsSellGo = False
                            
                            if  (Disparity5 > 102 or Disparity5 < 98):

                                IsSellGo = True
                                
                            if IsSellGo == True:

                                #현재가보다 아래에 매도 주문을 넣음으로써 시장가로 매도효과!
                                pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,stock_amt,CurrentPrice*0.99))


                                msg = stock_code + " 양방향3배전략봇 모두 정리!!!!!  [" + str(stock_revenue_money) + "] 손익 확정!! (현재 [" + str(StockInfo['Round']) + "] 라운드까지 진행되었고 모든 수량 매도 처리! )"
                                print(msg) 
                                line_alert.SendMessage(msg) 

                                #전량 매도 모두 초기화! 
                                StockInfo['Round'] = 0


                                #파일에 저장
                                with open(bot_file_path, 'w') as outfile:
                                    json.dump(InfinityUpgradeDataList, outfile)
         

                    #레버리지의 경우!
                    if stock_code == 'TQQQ' or stock_code == 'SOXL':

                        
                        if StockInfo['Round'] == 0 and Ma5_before < df['close'].iloc[-2] and Ma200_before < df['close'].iloc[-2] : #전일 종가가 5일선 위에 있을 때만 
                            

                            if Ma200_before > df['close'].iloc[-2]: #200일선 아래에 있을 땐 35분할
                                StockInfo['MaxRound'] = 35
                                
                            else: # 200일선 위에 있을 땐 

                                
                                st_num = 55
                                
                                if stock_code == 'TQQQ':
                                    st_num = 54
                                    
                                        
                                StockInfo['MaxRound'] = st_num
                            
                
                                if Ma100_before <= df['close'].iloc[-2]:
                                    StockInfo['MaxRound'] -= 15


                                if Ma60_before <= df['close'].iloc[-2]:
                                    StockInfo['MaxRound'] -= 8


                                if Ma20_before <= df['close'].iloc[-2]:
                                    StockInfo['MaxRound'] -= 7     


                                if StockInfo['MaxRound'] == st_num:
                                    StockInfo['MaxRound'] = 35    

                    
                            
                            StockInfo['Round'] += 1 #라운드 증가!

            
                            #분할된 투자금!
                            StMoney = StockMoney / StockInfo['MaxRound']


                            BuyAmt = int(StMoney / CurrentPrice)
                            
                            #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                            if BuyAmt < 1:
                                BuyAmt = 1

                            #시장가 주문을 넣는다!
                            #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수!
                            pprint.pprint(KisUS.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice*1.01))



                            time.sleep(10.0)
                            msg = stock_code + " 양방향3배전략봇 " + str(StockInfo['Round']) + "회차 매수 완료!"
                            print(msg) 
                            line_alert.SendMessage(msg) 

                    #인버스의 경우        
                    else:


                        IsBuyGo = False

                        if Ma20_before > df['close'].iloc[-2]:

                            if (df['low'].iloc[-3] < df['low'].iloc[-2]) and df['open'].iloc[-2] < df['close'].iloc[-2] :

                                if stock_code == 'SOXS':
                                    if df['volume'].iloc[-3] < df['volume'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3] and Disparity5 < 102:
                                        IsBuyGo = True
                                else:
                                    if df['open'].iloc[-3] > df['close'].iloc[-3] and Disparity5 < 103:
                                        IsBuyGo = True

                        if stock_code == 'SOXS':
                            if  min(df['open'].iloc[-4],df['close'].iloc[-4]) < min(df['open'].iloc[-3],df['close'].iloc[-3]) < min(df['open'].iloc[-2],df['close'].iloc[-2]) and df['open'].iloc[-2] < df['close'].iloc[-2] and Disparity5 < 102:
                                IsBuyGo = True


                        if IsBuyGo == True:    

                            StockInfo['Round'] = 1 #인버스는 무조건 1이다!

            
                            #분할된 투자금!
                            StMoney = StockMoney


                            BuyAmt = int(StMoney / CurrentPrice)
                            
                            #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                            if BuyAmt < 1:
                                BuyAmt = 1




                            time.sleep(10.0)
                            #시장가 주문을 넣는다!
                            #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수!
                            data = KisUS.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice*1.01)


                            msg = stock_code + " 양방향3배전략봇 " + str(StockInfo['Round']) + "회차 매수 완료! \n" + str(data)
                            print(msg) 
                            line_alert.SendMessage(msg) 



                            
                    #위 로직 완료하면 N으로 바꿔서 오늘 매수는 안되게 처리!
                    StockInfo['IsReady'] = 'N' 

                #파일에 저장
                with open(bot_file_path, 'w') as outfile:
                    json.dump(InfinityUpgradeDataList, outfile) 


                    
                break

else:

        
    #장이 끝나고 다음날 다시 매수시도 할수 있게 Y로 바꿔줍니당!
    for StockInfo in InfinityUpgradeDataList:
        StockInfo['IsReady'] = 'Y'


    #파일에 저장
    with open(bot_file_path, 'w') as outfile:
        json.dump(InfinityUpgradeDataList, outfile)
        
        
pprint.pprint(InfinityUpgradeDataList)