# -*- coding: utf-8 -*-
'''

-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-

관련 포스팅

지수 추종 ETF 투자 보다 수익률이 좋은 알파를 추구하는 자산배분 투자 방법 - 핵심위성 + 섹터모멘텀
https://blog.naver.com/zacra/222954263002

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^



'''
import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import time
import json
import pprint

import line_alert


#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL



BOT_NAME = Common.GetNowDist() + "_MyKr_SectorBot"



#시간 정보를 읽는다
time_info = time.gmtime()


#혹시 이 봇을 장 시작하자 마자 돌린다면 20초르 쉬어준다.
#그 이유는 20초는 지나야 오늘의 일봉 정보를 제대로 가져오는데
#tm_hour가 0은 9시, 1은 10시를 뜻한다. 수능 등 10시에 장 시작하는 경우르 대비!
if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
    time.sleep(20.0)
    
#년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
strYM = str(time_info.tm_year) + "_" + str(time_info.tm_mon)
print("ym_st: " , strYM)


print("time_info.tm_mon", time_info.tm_mon)

#포트폴리오 이름
PortfolioName = "게만아 한국 지수 추종 섹터 ETF 전략!"




#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################




#리밸런싱이 가능한지 여부를 판단!
Is_Rebalance_Go = False


#파일에 저장된 년월 문자열 (ex> 2022_9)를 읽는다
YMDict = dict()

#파일 경로입니다.
static_asset_tym_file_path = "/var/autobot/" + BOT_NAME + ".json"

try:
    with open(static_asset_tym_file_path, 'r') as json_file:
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
IsMarketOpen = KisKR.IsMarketOpen()

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



#####################################################################################################################################

#계좌 잔고를 가지고 온다!
Balance = KisKR.GetBalance()
#####################################################################################################################################

'''-------통합 증거금 사용자는 아래 코드도 사용할 수 있습니다! -----------'''
#통합증거금 계좌 사용자 분들중 만약 미국계좌랑 통합해서 총자산을 계산 하고 포트폴리오 비중에도 반영하고 싶으시다면 아래 코드를 사용하시면 되고 나머지는 동일합니다!!!
#Balance = Common.GetBalanceKrwTotal()

'''-----------------------------------------------------------'''
#####################################################################################################################################




print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")
#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.1

#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : ", format(round(TotalMoney), ','))

InvestCnt = 10 #총 10개의 ETF에 분산투자한다!

KOSPI200_ETF = "069660"



##########################################################

#투자 주식 리스트
MyPortfolioList = list()


'''

TIGER 200 건설 "139220"
TIGER 200 경기소비재 "139290"
TIGER 200 금융 "139270"
TIGER 200 에너지화학 "139250"
TIGER 200 중공업 "139230"
KODEX 기계장비 "102960"
TIGER 200 철강소재 "139240"
KBSTAR 200커뮤니케이션서비스 "315480"
KODEX 헬스케어 "266420"
KODEX 200IT TR "363580"
TIGER 경기방어 "139280"
KODEX 반도체 "091160"
TIGER 소프트웨어 "157490"
KODEX 은행 "091170"
KODEX 증권 "102970"
KODEX 보험 "140700"
TIGER 화장품 "228790"
KBSTAR 2차전지액티브 "422420"
KBSTAR 게임테마 "300640"
KODEX 미디어&엔터테인먼트 "266360"
TIGER KRX바이오K-뉴딜 "364970"
KODEX 운송 "140710"
KODEX 자동차 "091180"
TIGER 방송통신 "098560"
TIGER 200 생활소비재 "227560"
KBSTAR 수출주 "140570"
TIGER Fn메타버스 "400970"
KBSTAR Fn수소경제테마 "367770"
TIGER 여행레저 "228800"
TIGER 중국소비테마 "150460"
KODEX K-신재생에너지액티브 "385510"
KBSTAR Fn컨택트대표 "388280"
KODEX K-로봇액티브 "445290"
KODEX K-친환경선박액티브 "445150"
ARIRANG 우주항공&UAM iSelect "421320"


'''
StockCodeList = ["139220","139290","139270","139250","139230","102960","139240","315480","266420","363580","139280","091160","102970","140700","228790","422420","300640","266360","364970","140710","091180","098560","227560","140570","400970","367770","228800","150460","385510","388280","445290","445150","421320"]


for stock_code in StockCodeList:

    asset = dict()
    asset['stock_code'] = stock_code          #종목코드
    asset['stock_type'] = "SECTOR"
    asset['stock_target_rate'] = 5.0    #포트폴리오 목표 비중 총 10개니깐 5%씩 할당된다.
    asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량

    MyPortfolioList.append(asset)

# KOSEF 200 ETF를 넣어둔다!
asset = dict()
asset['stock_code'] = KOSPI200_ETF          #종목코드
asset['stock_type'] = "KOSPI200"
asset['stock_target_rate'] = 50.0   
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량

MyPortfolioList.append(asset)

##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################



#모든 자산의 모멘텀 스코어 구하기! 
for stock_info in MyPortfolioList:
    
    stock_code = stock_info['stock_code']
    stock_type = stock_info['stock_type']

    df = Common.GetOhlcv("KR",stock_code)


    Now_Price = Common.GetCloseData(df,-1) #현재가
    One_Price = Common.GetCloseData(df,-20) #한달 전
    Three_Price = Common.GetCloseData(df,-60) #3달전
    Six_Price = Common.GetCloseData(df,-120) #6달전
    Twelve_Price = Common.GetCloseData(df,-240) #1년전


    print(stock_code, Now_Price, One_Price, Three_Price, Six_Price, Twelve_Price)

    # 12*1개월 수익률, 4*3개월 수익률, 2*6개월 수익률, 1*12개월 수익률의 합!!
    MomentumScore = (((Now_Price - One_Price) / One_Price) * 12.0) + (((Now_Price - Three_Price) / Three_Price) * 4.0) + (((Now_Price - Six_Price) / Six_Price) * 2.0) + (((Now_Price - Twelve_Price) / Twelve_Price) * 1.0)

    stock_info['stock_momentum_score'] = MomentumScore

    print(KisKR.GetStockName(stock_code) , stock_code," -> MomentumScore: ",MomentumScore)

    Avg_Period = 10.0 #10개월의 평균 모멘텀을 구한다

    #이건 평균 모멘텀을 구하기에 상장된지 얼마 안된 ETF이다.
    if len(df) < Avg_Period * 20:

        #10개 이하면 즉 상장된지 10일도 안지났다? 절대모멘텀은 0.75로 가정하고 비중 조절!!!
        if len(df) < (Avg_Period+1):
            stock_info['stock_target_rate'] *= 0.75
            print("#>> 10개이하라 50%만 투자!!")

        else:

            #있는 데이터 개수를 Avg_Period(10)으로 나눠서 평균 모멘텀을 계산한다!
            Up_Count = 0
            
            CellVal = int(len(df)/Avg_Period)

            Start_Num = -CellVal

            for i in range(1,int(Avg_Period)+1):
                CheckPrice = Common.GetCloseData(df,Start_Num)

                if Now_Price >= CheckPrice:
                    Up_Count += 1.0

                Start_Num -= CellVal

            avg_momentum_score = Up_Count/Avg_Period

            print("#>> 10등분 평균 모멘텀 ", avg_momentum_score)

            stock_info['stock_target_rate'] *= (0.33 + avg_momentum_score*0.67)

    else:

        #1달은 20거래일! 10개월 평균 모멘텀을 계산한다!
        Up_Count = 0
        Start_Num = -20
        for i in range(1,int(Avg_Period)+1):
            
            CheckPrice = Common.GetCloseData(df,Start_Num)
            print(CheckPrice, "  <<-  df[-", Start_Num,"]")

            if Now_Price >= CheckPrice:
                print("UP!")
                Up_Count += 1.0


            Start_Num -= 20

        avg_momentum_score = Up_Count/Avg_Period

        print("10개월 평균 모멘텀 ", avg_momentum_score)

        stock_info['stock_target_rate'] *= (0.33 + avg_momentum_score*0.67)


    print("1차 최종 비중: ", stock_info['stock_target_rate'])




#위험 자산 중 가장 모멘텀 스코어가 높은 상위 10개를 구한다.
Stockdata = sorted(MyPortfolioList, key=lambda stock_info: (stock_info['stock_momentum_score']), reverse= True)
pprint.pprint(Stockdata)


#이 리스트에는 모멘텀 스코어가 가장 높은거 10개 들어간다!
FinalSelectedList = list()

TCnt = 10
i = 0
for data in Stockdata:
    
    if i < TCnt:

        if data['stock_code'] == KOSPI200_ETF: #KOSPI200은 제외 하고 TOP10을 구한다.
            continue
        
        AlreadyHas = False
        for stock_code in FinalSelectedList:
            if stock_code == data['stock_code']:
                AlreadyHas = True
                break
            
        if AlreadyHas == False:
            FinalSelectedList.append(data['stock_code'])
            i += 1
            

FinalSelectedList.append(KOSPI200_ETF) #마지막에 KOSPI200 추가해줘서 총 투자대상 11개!




print("---------- 최종 선택 리스트 -------------")
for stock_info in MyPortfolioList:

    stock_code = stock_info['stock_code']
    MomentumScore = stock_info['stock_momentum_score']
    Stock_Name = KisKR.GetStockName(stock_code)

    msg = ""
    if Common.CheckStockCodeInList(FinalSelectedList,stock_code) == True:


        if MomentumScore < 0:

            stock_info['stock_target_rate'] *= 0.5
            msg = Stock_Name +"  모멘텀 스코어가 0보다 작다면 비중을 줄여준다 " + str(stock_info['stock_target_rate'])

        else:

            print(Stock_Name , stock_code," -> MomentumScore: ",MomentumScore)

            msg = "\n------>" +Stock_Name +" 는 다음과 같은 비중으로 투자!!!!!!!!:" + str(stock_info['stock_target_rate']) + "\n"



    else:
        stock_info['stock_target_rate'] = 0
        msg = Stock_Name +" TOP10에 못들어 감.... 투자비중:" + str(stock_info['stock_target_rate'])
                    
    print(msg)
    if Is_Rebalance_Go == True and IsMarketOpen == True:
        line_alert.SendMessage(msg)





TotalRate = 0 
RemainRate = 0 #남은 비중..
for stock_info in MyPortfolioList:

    TotalRate += stock_info['stock_target_rate']

RemainRate = 100.0 - TotalRate
print("남은 현금 비중: ", RemainRate , "%")


print(RemainRate, "% 가 남아")
if Is_Rebalance_Go == True and IsMarketOpen == True and RemainRate > 0:

    print(RemainRate, "% 가 남아서 일단 현금 보유!")

    
    line_alert.SendMessage(PortfolioName + " (" + str(RemainRate) + ") 비중은  일단 현금 보유!")






print("--------------리밸런싱 수량 계산 ---------------------")

strResult = "-- 현재 포트폴리오 상황 --\n"

#매수된 자산의 총합!
total_stock_money = 0

#현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
for stock_info in MyPortfolioList:

    #내주식 코드
    stock_code = stock_info['stock_code']


    stock_target_rate = float(stock_info['stock_target_rate']) / 100.0

    #현재가!
    CurrentPrice = KisKR.GetCurrentPrice(stock_code)

    

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


    print("#####" , KisKR.GetStockName(stock_code) ," stock_code: ", stock_code)
    print("---> TargetRate:", round(stock_target_rate * 100.0,2) , "%")

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


            #목표한 비중가 다르다면!!
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
            
            
        
        
        
        
    #라인 메시지랑 로그를 만들기 위한 문자열 
    line_data =  (">> " + KisKR.GetStockName(stock_code) + "(" + stock_code + ") << \n비중: " + str(round(stock_now_rate * 100.0,2)) + "/" + str(round(stock_target_rate * 100.0,2)) 
    + "% \n수익: " + str(format(round(stock_revenue_money), ',')) + "("+ str(round(stock_revenue_rate,2)) 
    + "%) \n총평가금액: " + str(format(round(stock_eval_totalmoney), ',')) 
    + "\n리밸런싱수량: " + str(stock_info['stock_rebalance_amt']) + "\n----------------------\n")

    #만약 아래 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
    #if Is_Rebalance_Go == True:
    #    line_alert.SendMessage(line_data)
    strResult += line_data



##########################################################

print("--------------리밸런싱 해야 되는 수량-------------")

data_str = "\n" + PortfolioName + "\n" +  strResult + "\n포트폴리오할당금액: " + str(format(round(TotalMoney), ',')) + "\n매수한자산총액: " + str(format(round(total_stock_money), ',') )

#결과를 출력해 줍니다!
print(data_str)

#영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
if Is_Rebalance_Go == True:
    line_alert.SendMessage(data_str)
    
#만약 위의 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
#if Is_Rebalance_Go == True:
#    line_alert.SendMessage("\n포트폴리오할당금액: " + str(format(round(TotalMoney), ',')) + "\n매수한자산총액: " + str(format(round(total_stock_money), ',') ))




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
            
            #이렇게 시장가로 매도 해도 큰 무리는 없어 보인다!       
            pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,abs(rebalance_amt)))


            #나중에 투자금이 커지면 시장가 매도시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
            '''
            CurrentPrice = KisKR.GetCurrentPrice(stock_code)
            CurrentPrice *= 0.99 #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
            pprint.pprint(KisKR.MakeSellLimitOrder(stock_code,abs(rebalance_amt),CurrentPrice))
            '''
            
            #지정가 괴리율 등을 반영해 매도하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요!
            '''

            Nav = KisKR.GetETF_Nav(stock_code)
            CurrentPrice = KisKR.GetCurrentPrice(stock_code)

            FarRate = ((CurrentPrice-Nav) / Nav) * 100.0


            #최근 120일의 괴리율 절대값 평균
            AvgGap = KisKR.GetETFGapAvg(stock_code)

            print(KisKR.GetStockName(stock_code) + "ETF NAV: " , Nav," 현재가:", CurrentPrice, " 괴리율:",FarRate , " 괴리율 절대값 평균:", AvgGap)


            #일단 기본은 현재가로!!!
            FinalPrice = CurrentPrice


            #괴리율이 양수여서 유리할 때나 매도에 불리한 -1% 이하일때는 NAV가격으로 주문!
            #if FarRate >= 0 or (FarRate <= -1.0):
            if FarRate >= 0 or (AvgGap * 1.5) < abs(FarRate):
                FinalPrice = Nav

            Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,rebalance_amt,"DAY_END_TRY_ETF")

            '''


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

            #이렇게 시장가로 매수 해도 큰 무리는 없어 보인다!  
            pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,rebalance_amt))

            #나중에 투자금이 커지면 시장가 매수시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
            '''
            CurrentPrice = KisKR.GetCurrentPrice(stock_code)
            CurrentPrice *= 1.01 #현재가의 1%위의 가격으로 지정가 매수.. (그럼 1% 위 가격보다 작은 가격의 호가들은 모두 체결되기에 제한있는 시장가 매수 효과)
            pprint.pprint(KisKR.MakeBuyLimitOrder(stock_code,abs(rebalance_amt),CurrentPrice))
            '''


            #지정가 괴리율 등을 반영해 매수하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요!
            '''

            Nav = KisKR.GetETF_Nav(stock_code)
            CurrentPrice = KisKR.GetCurrentPrice(stock_code)

            FarRate = ((CurrentPrice-Nav) / Nav) * 100.0
            #최근 120일의 괴리율 절대값 평균
            AvgGap = KisKR.GetETFGapAvg(stock_code)

            print(KisKR.GetStockName(stock_code) + "ETF NAV: " , Nav," 현재가:", CurrentPrice, " 괴리율:",FarRate , " 괴리율 절대값 평균:", AvgGap)

            #일단 기본은 현재가로!!!
            FinalPrice = CurrentPrice


            #괴리율이 음수여서 유리할 때나 매수에 불리한 1% 이상일때는 NAV가격으로 주문!
            if FarRate <= 0 or (FarRate >= 1.0):
            #if FarRate <= 0 or (AvgGap * 1.5) < abs(FarRate):
                FinalPrice = Nav


            Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,rebalance_amt,"DAY_END_TRY_ETF")
            '''



    print("--------------------------------------------")

    #########################################################################################################################
    #첫 매수던 리밸런싱이던 매매가 끝났으면 이달의 리밸런싱은 끝이다. 해당 달의 년달 즉 22년 9월이라면 '2022_9' 라는 값을 파일에 저장해 둔다! 
    #파일에 저장하는 부분은 여기가 유일!!!!
    YMDict['ym_st'] = strYM
    with open(static_asset_tym_file_path, 'w') as outfile:
        json.dump(YMDict, outfile)
    #########################################################################################################################
        
    line_alert.SendMessage(PortfolioName + " (" + strYM + ") 리밸런싱 완료!!")
    print("------------------리밸런싱 끝---------------------")
