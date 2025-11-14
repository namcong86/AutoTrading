# -*- coding: utf-8 -*-
'''
-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-

My_US_BAA_typeA.py 는 방어자산 선정후에 BIL보다 모멘텀이 낮으면 그냥 현금(달러)보유하는 전략이고
My_US_BAA_typeB.py 는 방어자산 선정후에 BIL보다 모멘텀이 낮으면 BIL을 보유하는 전략입니다!


관련 포스팅

연 복리 20%가 넘는 동적 자산배분 BAA 공격형 전략 자동화 하기 (천 만원이 30년 뒤 23억이 되는 마법)
https://blog.naver.com/zacra/222979124069

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import KIS_API_Helper_US as KisUS
import time
import json
import pprint

import line_alert



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL


BOT_NAME = Common.GetNowDist() + "_MyBBABot"


#시간 정보를 읽는다
time_info = time.gmtime()
#년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
strYM = str(time_info.tm_year) + "_" + str(time_info.tm_mon)
print("ym_st: " , strYM)



#포트폴리오 이름
PortfolioName = "동적자산배분전략_BAA"




#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


#리밸런싱이 가능한지 여부를 판단!
Is_Rebalance_Go = False


#파일에 저장된 년월 문자열 (ex> 2022_9)를 읽는다
YMDict = dict()

'''
################## 변경된 점 #####################
'''
#파일 경로입니다.
asset_tym_file_path = "/var/autobot/" + BOT_NAME + ".json"
'''
################################################
'''
try:
    with open(asset_tym_file_path, 'r') as json_file:
        YMDict = json.load(json_file)

except Exception as e:
    print("Exception by First")


#만약 키가 존재 하지 않는다 즉 아직 한번도 매매가 안된 상태라면
if YMDict.get("ym_st") == None:

    #리밸런싱 가능! (리밸런싱이라기보다 첫 매수해야 되는 상황!)
    Is_Rebalance_Go = True
    
#매매가 된 상태라면! 매매 당시 혹은 리밸런싱 당시 년월 정보(ex> 2022_9) 가 들어가 있다.
else:
    #그럼 그 정보랑 다를때만 즉 달이 바뀌었을 때만 리밸런싱을 해야 된다
    if YMDict['ym_st'] != strYM:
        #리밸런싱 가능!
        Is_Rebalance_Go = True


#강제 리밸런싱 수행!
#Is_Rebalance_Go = True



#마켓이 열렸는지 여부~!
IsMarketOpen = KisUS.IsMarketOpen()

if IsMarketOpen == True:
    print("Market Is Open!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
    if Is_Rebalance_Go == True:
        line_alert.SendMessage(PortfolioName + " (" + strYM + ") 장이 열려서 포트폴리오 리밸런싱 가능!!")
else:
    print("Market Is Close!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
    if Is_Rebalance_Go == True:
        line_alert.SendMessage(PortfolioName + " (" + strYM + ") 장이 닫혀서 포트폴리오 리밸런싱 불가능!!")




#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


#계좌 잔고를 가지고 온다!
Balance = KisUS.GetBalance()


print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")
#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.5


#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : $", TotalMoney)





'''

공격형 자산 :

QQQ 
VWO
VEA
BND

안전 자산:

TIP
PDBC
BIL
IEF
TLT
LQD
BND

카나리아 자산:

SPY
VEA
VWO
BND


'''

##########################################################

#위험 자산 투자시 상위 몇 개를 투자할지
RiskAssetCnt = 1

#안전 자산 투자시 상위 몇 개를 투자할지
SafeAssetCnt = 3


#투자 주식 리스트
MyPortfolioList = list()


RiskCodeList = ['QQQ','VWO','VEA','BND']

for stock_code in RiskCodeList:

    asset = dict()
    asset['stock_code'] = stock_code         #종목코드
    asset['stock_type'] = "RISK"         #공격형(RISK) 자산인지 안전형(SAFE) 자산인지 카나리아(BIRD) 자산인지 여부
    asset['stock_momentum_score'] = 0    #모멘텀 스코어
    asset['stock_target_rate'] = 0   #포트폴리오 목표 비중
    asset['stock_rebalance_amt'] = 0     #리밸런싱 해야 되는 수량
    MyPortfolioList.append(asset)



SafeCodeList = ['TIP','PDBC','BIL','IEF','TLT','LQD','BND']

for stock_code in SafeCodeList:

    asset = dict()
    asset['stock_code'] = stock_code          #종목코드
    asset['stock_type'] = "SAFE"         #공격형(RISK) 자산인지 안전형(SAFE) 자산인지 카나리아(BIRD) 자산인지 여부
    asset['stock_momentum_score'] = 0    #모멘텀 스코어
    asset['stock_target_rate'] = 0   #포트폴리오 목표 비중
    asset['stock_rebalance_amt'] = 0     #리밸런싱 해야 되는 수량
    MyPortfolioList.append(asset)


BirdCodeList = ['SPY','VEA','VWO','BND']

for stock_code in BirdCodeList:

    asset = dict()
    asset['stock_code'] = stock_code         #종목코드
    asset['stock_type'] = "BIRD"         #공격형(RISK) 자산인지 안전형(SAFE) 자산인지 카나리아(BIRD) 자산인지 여부
    asset['stock_momentum_score'] = 0    #모멘텀 스코어
    asset['stock_target_rate'] = 0   #포트폴리오 목표 비중
    asset['stock_rebalance_amt'] = 0     #리밸런싱 해야 되는 수량
    MyPortfolioList.append(asset)






##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisUS.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################




print("--------------리밸런싱 계산 ---------------------")


print("-------------- 모멘텀 스코어 계산 ---------------------")

#모든 자산의 모멘텀 스코어 구하기! 
for stock_info in MyPortfolioList:
    print("....")
    stock_code = stock_info['stock_code']
    stock_type = stock_info['stock_type']

    df = Common.GetOhlcv("US",stock_code)


    Now_Price = Common.GetCloseData(df,-1) #현재가
    One_Price = Common.GetCloseData(df,-20) #한달 전
    Three_Price = Common.GetCloseData(df,-60) #3달전
    Six_Price = Common.GetCloseData(df,-120) #6달전
    Twelve_Price = Common.GetCloseData(df,-240) #1년전

    CurrentMa1Y = Common.GetMA(df,240,-1) #12개월 이동평균


    print(stock_code, Now_Price, One_Price, Three_Price, Six_Price, Twelve_Price)

    ###################################################################################################
    #유튜브 영상과 블로그(수정했음) 내용과 다르게 공격자산도 12개월 이평선 기준으로 투자 종목을 정하는 것으로 밝혀져 수정합니다!!
    ###################################################################################################
    #공격자산 / 안전자산의 모멘텀 스코어는 현재가/12개월 이동평균
    MomentumScore = Now_Price/CurrentMa1Y
    
    if stock_type == 'BIRD':
        # 12*1개월 수익률, 4*3개월 수익률, 2*6개월 수익률, 1*12개월 수익률의 합!!
        MomentumScore = (((Now_Price - One_Price) / One_Price) * 12.0) + (((Now_Price - Three_Price) / Three_Price) * 4.0) + (((Now_Price - Six_Price) / Six_Price) * 2.0) + (((Now_Price - Twelve_Price) / Twelve_Price) * 1.0)



    stock_info['stock_momentum_score'] = MomentumScore

    print(stock_code," -> MomentumScore: ",MomentumScore)






print("-------------- 투자 자산과 비중 결정 ---------------------")

RiskList = list() #공격 자산 리스트
SafeList = list() #안전 자산 리스트

#카나리아 자산이 
BirdAssetMinusCnt = 0

for stock_info in MyPortfolioList:

    pprint.pprint(stock_info)

    #카나리아 자산인데 
    if stock_info['stock_type'] == "BIRD":
        #모멘텀 스코어가 마이너스다? 그럼 숫자를 증가시켜주자!
        if stock_info['stock_momentum_score'] < 0:
            BirdAssetMinusCnt += 1

    elif stock_info['stock_type'] == "RISK":

        RiskList.append(stock_info)

    elif stock_info['stock_type'] == "SAFE":

        SafeList.append(stock_info)





#안전 자산 중 가장 모멘텀 스코어가 높은거를 SafeAssetCnt개 만큼 순서대로 구한다!
Safedata = sorted(SafeList, key=lambda stock_info: (stock_info['stock_momentum_score']), reverse= True)
pprint.pprint(Safedata)


SafeTopStockCodeList = list()

for i in range(0,SafeAssetCnt):
    SafeTopStockCodeList.append(Safedata[i]['stock_code'])





#위험 자산 중 가장 모멘텀 스코어가 높은 상위 RiskAssetCnt개를 구한다.
Riskdata = sorted(RiskList, key=lambda stock_info: (stock_info['stock_momentum_score']), reverse= True)
pprint.pprint(Riskdata)

RiskTopStockCodeList = list()

for i in range(0,RiskAssetCnt):
    RiskTopStockCodeList.append(Riskdata[i]['stock_code'])





###############################
#최종 투자해야 자산 코드 리스트!!
FinalSelectedList = list()
###############################

BIL_ADD_RATE = 0 #BIL에 투자할 비중 
IS_FINAL_IN_BIL = False #BIL이 TOP3에 들었는지 여부

for stock_info in MyPortfolioList:

    stock_code = stock_info['stock_code']

    if BirdAssetMinusCnt == 0:

        if stock_info['stock_type'] == "RISK":
            #가장 수익률 높은 위험자산 리스트에 포함이 되어 있다면!
            if Common.CheckStockCodeInList(RiskTopStockCodeList,stock_code) == True:
                FinalSelectedList.append(stock_code) #최종 선택에 넣어준다!
                stock_info['stock_target_rate'] = 100.0 / float(RiskAssetCnt) 

    else:
        if stock_info['stock_type'] == "SAFE":
            #가장 수익률 높은 안전자산 리스트에 포함이 되어 있다면!
            if Common.CheckStockCodeInList(SafeTopStockCodeList,stock_code) == True:
                

                df = Common.GetOhlcv("US",stock_code)
                CurrentMa1Y = Common.GetMA(df,240,-1)
                CurrentPrice = KisUS.GetCurrentPrice(stock_code)

                Target_rate = 100.0 / float(SafeAssetCnt)

                print("--" , stock_code)
                print("CurrentMa1Y " , CurrentMa1Y)
                print("CurrentPrice " , CurrentPrice)
                if CurrentMa1Y <= CurrentPrice:
                    stock_info['stock_target_rate'] = Target_rate
                    FinalSelectedList.append(stock_code) #최종 선택에 넣어준다!

                    if stock_code == "BIL": #BIL이 포함되었다!
                        IS_FINAL_IN_BIL = True

                else:
                    stock_info['stock_target_rate'] = 0

                    BIL_ADD_RATE += Target_rate


if BIL_ADD_RATE > 0:

    for stock_info in MyPortfolioList:
        stock_code = stock_info['stock_code']
        if stock_code == "BIL":
            stock_info['stock_target_rate'] += BIL_ADD_RATE

    #BIL이 포함되어 있지 않았다면 최종 자산에 추가해준다!
    if IS_FINAL_IN_BIL == False:
        FinalSelectedList.append(stock_code) 




print("----RiskTopStockCodeList ASSET!-----")
pprint.pprint(RiskTopStockCodeList)
print("----SafeTopStockCodeList ASSET!-----")
pprint.pprint(SafeTopStockCodeList)
    

print("----FINAL SELECTED ASSET!-----")
pprint.pprint(FinalSelectedList)
print("-----------------------------")





strResult = "-- 현재 포트폴리오 상황 --\n"

#매수된 자산의 총합!
total_stock_money = 0

#현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
for stock_info in MyPortfolioList:

    #내주식 코드
    stock_code = stock_info['stock_code']
    #매수할 자산 보유할 자산의 비중을 넣어준다!
    stock_target_rate = float(stock_info['stock_target_rate']) / 100.0


    #기준이 된 카나리아 자산 ETF는 아무것도 안한다
    if stock_info['stock_type'] == "BIRD":
        continue

    #위험자산에 투자 해야 하는 상태
    if BirdAssetMinusCnt == 0:
        #위험자산에 BND가 속해 있다면 비중에 따라 매수매도가 될테니깐 안전자산 체크시 매도를 피합니다!
        if 'BND' in RiskTopStockCodeList and stock_info['stock_type'] == "SAFE" and stock_code == "BND":
            continue
    #안전자산에 투자 해야 하는 상태
    else:
        #안전자산에 BND가 속해 있다면 비중에 따라 매수매도가 될테니깐 위험자산 체크시 매도를 피합니다!
        if 'BND' in SafeTopStockCodeList and stock_info['stock_type'] == "RISK" and stock_code == "BND":
            continue


    #현재가!
    CurrentPrice = KisUS.GetCurrentPrice(stock_code)


    
    stock_name = ""
    stock_amt = 0 #수량
    stock_avg_price = 0 #평단
    stock_eval_totalmoney = 0 #총평가금액!
    stock_revenue_rate = 0 #종목 수익률
    stock_revenue_money = 0 #종목 수익금

 

    #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
    for my_stock in MyStockList:
        if my_stock['StockCode'] == stock_code:
            stock_name = my_stock['StockName']
            stock_amt = int(my_stock['StockAmt'])
            stock_avg_price = float(my_stock['StockAvgPrice'])
            stock_eval_totalmoney = float(my_stock['StockNowMoney'])
            stock_revenue_rate = float(my_stock['StockRevenueRate'])
            stock_revenue_money = float(my_stock['StockRevenueMoney'])

            break

    print("##### stock_code: ", stock_code)

    #주식의 총 평가금액을 더해준다
    total_stock_money += stock_eval_totalmoney

    #현재 비중
    stock_now_rate = 0

    #잔고에 있는 경우 즉 이미 매수된 주식의 경우
    if stock_amt > 0:


        stock_now_rate = round((stock_eval_totalmoney / TotalMoney),3)

        print("---> NowRate:", round(stock_now_rate * 100.0,2), "%")

        #최종 선택된 자산리스트에 포함되어 있다면 비중대로 보유해야 한다! 리밸린싱!
        if Common.CheckStockCodeInList(FinalSelectedList,stock_code) == True:


            #목표한 비중이 다르다면!!
            if stock_now_rate != stock_target_rate:


                #갭을 구한다!!!
                GapRate = stock_target_rate - stock_now_rate


                #그래서 그 갭만큼의 금액을 구한다
                GapMoney = TotalMoney * abs(GapRate) 
                #현재가로 나눠서 몇주를 매매해야 되는지 계산한다
                GapAmt = GapMoney / CurrentPrice

                #수량이 1보다 커야 리밸러싱을 할 수 있다!! 즉 그 전에는 리밸런싱 불가 
                if GapAmt >= 1.0:

                    GapAmt = int(GapAmt)

                    #갭이 음수라면! 비중이 더 많으니 팔아야 되는 상황!!! 
                    if GapRate < 0:

                        #팔아야 되는 상황에서는 현재 주식수량에서 매도할 수량을 뺀 값이 1주는 남아 있어야 한다
                        #그래야 포트폴리오 상에서 아예 사라지는 걸 막는다!
                        if stock_amt - GapAmt >= 1:
                            stock_info['stock_rebalance_amt'] = -GapAmt

                    #갭이 양수라면 비중이 더 적으니 사야되는 상황!
                    else:  
                        stock_info['stock_rebalance_amt'] = GapAmt


        #선택된 자산이 아니라면 전 수량 다 팔아야 한다
        else:
            stock_info['stock_rebalance_amt'] = -stock_amt



    #잔고에 없는 경우
    else:

        #최종 선택된 자산리스트에 포함되어 있다면 비중대로 매수해야 한다!
        if Common.CheckStockCodeInList(FinalSelectedList,stock_code) == True:

            print("---> NowRate: 0%")

            #잔고가 없다면 첫 매수다! 비중대로 매수할 총 금액을 계산한다 
            BuyMoney = TotalMoney * stock_target_rate


            #매수할 수량을 계산한다!
            BuyAmt = int(BuyMoney / CurrentPrice)

            #포트폴리오에 들어간건 일단 무조건 1주를 사주자... 아니라면 아래 2줄 주석처리
        # if BuyAmt <= 0:
            #    BuyAmt = 1

            stock_info['stock_rebalance_amt'] = BuyAmt

        #선택된 최종 자산이 아니라면 아무것도 안하면 된다!
        else:
            print("Do nothing")
        

        
        
        
        
        
    #라인 메시지랑 로그를 만들기 위한 문자열 
    line_data =  (">> " + stock_code + " << \n비중: " + str(round(stock_now_rate * 100.0,2)) + "/" + str(round(stock_target_rate * 100.0,2)) 
    + "% \n수익: $" + str(stock_revenue_money) + "("+ str(round(stock_revenue_rate,2)) 
    + "%) \n총평가금액: $" + str(round(stock_eval_totalmoney,2)) 
    + "\n리밸런싱수량: " + str(stock_info['stock_rebalance_amt']) + "\n----------------------\n")

    #만약 아래 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
    if Is_Rebalance_Go == True:
        line_alert.SendMessage(line_data)
    strResult += line_data



##########################################################

print("--------------리밸런싱 해야 되는 수량-------------")

data_str = "\n" + PortfolioName + "\n" +  strResult + "\n포트폴리오할당금액: $" + str(round(TotalMoney,2)) + "\n매수한자산총액: $" + str(round(total_stock_money,2))

#결과를 출력해 줍니다!
print(data_str)

#영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
#if Is_Rebalance_Go == True:
#    line_alert.SendMessage(data_str)
    
#만약 위의 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
if Is_Rebalance_Go == True:
    line_alert.SendMessage("\n포트폴리오할당금액: $" + str(round(TotalMoney,2)) + "\n매수한자산총액: $" + str(round(total_stock_money,2)))




print("--------------------------------------------")

##########################################################


#리밸런싱이 가능한 상태여야 하고 매수 매도는 장이 열려있어야지만 가능하다!!!
if Is_Rebalance_Go == True and IsMarketOpen == True:

    line_alert.SendMessage(PortfolioName + " (" + strYM + ") 리밸런싱 시작!!")

    print("------------------리밸런싱 시작  ---------------------")
    #이제 목표치에 맞게 포트폴리오를 조정하면 되는데
    #매도를 해야 돈이 생겨 매수를 할 수 있을 테니
    #먼저 매도를 하고
    #그 다음에 매수를 해서 포트폴리오를 조정합니다!

    print("--------------매도 (리밸런싱 수량이 마이너스인거)---------------------")

    for stock_info in MyPortfolioList:

        #내주식 코드
        stock_code = stock_info['stock_code']
        rebalance_amt = stock_info['stock_rebalance_amt']

        #리밸런싱 수량이 마이너스인 것을 찾아 매도 한다!
        if rebalance_amt < 0:
                    
            #현재가!
            CurrentPrice = KisUS.GetCurrentPrice(stock_code)
            


            #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
            CurrentPrice *= 0.99
            pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,abs(rebalance_amt),CurrentPrice))

            #######################################################
            #지정가로 하려면 아래 함수 활용! 주식 클래스 완강 필요!
            #Common.AutoLimitDoAgain(BOT_NAME,"US",stock_code,CurrentPrice,rebalance_amt,"DAY_END")


    print("--------------------------------------------")


    #3초 정도 쉬어준다
    time.sleep(3.0)



    print("--------------매수 ---------------------")

    for stock_info in MyPortfolioList:

        #내주식 코드
        stock_code = stock_info['stock_code']
        rebalance_amt = stock_info['stock_rebalance_amt']

        #리밸런싱 수량이 플러스인 것을 찾아 매수 한다!
        if rebalance_amt > 0:
                    
            #현재가!
            CurrentPrice = KisUS.GetCurrentPrice(stock_code)

            #현재가의 1%위의 가격으로 지정가 매수.. (그럼 1% 위 가격보다 작은 가격의 호가들은 모두 체결되기에 제한있는 시장가 매수 효과)
            CurrentPrice *= 1.01
            pprint.pprint(KisUS.MakeBuyLimitOrder(stock_code,rebalance_amt,CurrentPrice))
            
            #######################################################
            #지정가로 하려면 아래 코드로 매수! 주식 클래스 완강 필요!
            #Common.AutoLimitDoAgain(BOT_NAME,"US",stock_code,CurrentPrice,rebalance_amt,"DAY_END")


    print("--------------------------------------------")

    #########################################################################################################################
    #첫 매수던 리밸런싱이던 매매가 끝났으면 이달의 리밸런싱은 끝이다. 해당 달의 년달 즉 22년 9월이라면 '2022_9' 라는 값을 파일에 저장해 둔다! 
    #파일에 저장하는 부분은 여기가 유일!!!!
    YMDict['ym_st'] = strYM
    with open(asset_tym_file_path, 'w') as outfile:
        json.dump(YMDict, outfile)
    #########################################################################################################################
        
    line_alert.SendMessage(PortfolioName + " (" + strYM + ") 리밸런싱 완료!!")
    print("------------------리밸런싱 끝---------------------")

