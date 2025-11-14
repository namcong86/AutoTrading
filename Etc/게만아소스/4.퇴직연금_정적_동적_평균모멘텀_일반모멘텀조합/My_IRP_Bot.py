# -*- coding: utf-8 -*-
'''

-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-


퇴직연금 IRP계좌의 매수매도 주문이 불행히도 막혔습니다.
따라서 계산된 수량을 수동매매해야 한다는 점 알려드립니다.
이 포스팅을 체크하세요!!!!
https://blog.naver.com/zacra/223165655107


관련 포스팅

주식 자동매매! 연금 계좌에서 돌리는 완벽 전략!! 정적 자산배분 + 동적 자산배분, 평균 모멘텀 + 상대 모멘텀 
https://blog.naver.com/zacra/222949269705

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^



'''
from cmath import isnan
import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import time
import json
import pprint

import line_alert
import math



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL


BOT_NAME = Common.GetNowDist() + "_MyIRP!"


#시간 정보를 읽는다
time_info = time.gmtime()


if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
    time.sleep(20.0)
    
#년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
strYM = str(time_info.tm_year) + "_" + str(time_info.tm_mon)
print("ym_st: " , strYM)


print("time_info.tm_mon", time_info.tm_mon)

#포트폴리오 이름
PortfolioName = "정적+동적 자산배분전략_IRP!"



#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


#리밸런싱이 가능한지 여부를 판단!
Is_Rebalance_Go = False


#파일에 저장된 년월 문자열 (ex> 2022_9)를 읽는다
YMDict = dict()

#파일 경로입니다.
static_asset_tym_file_path = "/var/autobot/" + BOT_NAME + "_ST.json"
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
InvestRate = 1.0

#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : ", format(round(TotalMoney), ','))
'''

ETF찾기 참고 : https://blog.naver.com/zacra/222867823600
참고로 아시겠지만 ETF의 종목코드는 직접 검색하셔서 알아 내셔야 합니다!


주식   50

미국
TIGER 미국S&P500TR(H) "448290"    10%
KBSTAR 미국S&P500 "379780"        10%


한국
KOSEF 200TR "294400"                   4%

글로벌
KOSEF 인도Nifty50(합성) "200250"         5%
KODEX 차이나CSI300 "283580"             5%
ARIRANG 선진국MSCI(합성 H)  "195970"     6%


배당(리츠)
ARIRANG 고배당주 "161510"              2%
TIGER MKF배당귀족 "445910"             2%
TIGER 미국S&P500배당귀족 "429000"       2%
TIGER 리츠부동산인프라 "341850"           2%
SOL 미국배당 다우존스 "446720"    2% .   /// <- SOL이 더 수수료가 싸짐 ACE 미국고배당S&P "402970"               2%

채권   36

KODEX 200 미국채혼합   "284430"  12%

KOSEF 국고채10년 "148070"               9%
KBSTAR KIS국고채30년Enhanced "385560"   3%
KOSEF 국고채3년 "114470"           3%
TIGER 미국달러단기채권액티브 "329750"  3%

KODEX KOFR금리액티브(합성) "423160"  3%
KOSEF 물가채KIS  "430500"          3%



원자재 및 금     14

KINDEX KRX금현물 "411060" 6%
TIGER 글로벌자원생산기업(합성 H) "276000" 2%
TIGER 구리실물 "160580"        3% 
KBSTAR 미국S&P원유생산기업(합성 H) "219390"   3%







평균 모멘텀으로 비중을 정해서 투자!!!


그렇게 감산된 현금의 절반은 단기자금에 투자!!!

KOSEF 단기자금 "130730"

나머지 절반에 해당하는 비중은..
모멘텀 스코어를 구해서... 상위 탑 12에 보너스 분산투자!

(24분할해서 차등 지급.)
3
3
3
3
2
2
2
2
1
1
1
1
'''




##########################################################

#투자 주식 리스트
MyPortfolioList = list()


'''
주식   50

미국
TIGER 미국S&P500TR(H) "448290"    10%
KBSTAR 미국S&P500 "379780"        10%


'''
asset = dict()
asset['stock_code'] = "448290"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 10    #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "379780"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 10   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)



'''

한국
KOSEF 200TR "294400"                   4%

글로벌
KOSEF 인도Nifty50(합성) "200250"         5%
KODEX 차이나CSI300 "283580"             5%
ARIRANG 선진국MSCI(합성 H)  "195970"     6%


'''

asset = dict()
asset['stock_code'] = "294400"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 4   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)




asset = dict()
asset['stock_code'] = "200250"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 5   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "283580"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 5   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)



asset = dict()
asset['stock_code'] = "195970"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 6   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


'''

배당(리츠)
ARIRANG 고배당주 "161510"              2%
TIGER MKF배당귀족 "445910"             2%
TIGER 미국S&P500배당귀족 "429000"       2%
TIGER 리츠부동산인프라 "329200"           2%
SOL 미국배당 다우존스 "446720"              2%

'''


asset = dict()
asset['stock_code'] = "161510"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "445910"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "429000"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "329200"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "446720"          #종목코드
asset['stock_type'] = "STOCK" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)







'''
채권   36



KODEX 200 미국채혼합   "284430"  12%
KOSEF 국고채10년 "148070"               9%
KBSTAR KIS국고채30년Enhanced "385560"   3%
KOSEF 국고채3년 "114470"           3%
TIGER 미국달러단기채권액티브 "329750"  3%

KODEX KOFR금리액티브(합성) "423160"  3%
KOSEF 물가채KIS  "430500"          3%


'''

asset = dict()
asset['stock_code'] = "284430"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 12   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "148070"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 9   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)



asset = dict()
asset['stock_code'] = "385560"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "114470"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "329750"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "423160"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)



asset = dict()
asset['stock_code'] = "430500"          #종목코드
asset['stock_type'] = "SAFE" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)






'''
원자재 및 금     14

KINDEX KRX금현물 "411060" 6%
TIGER 글로벌자원생산기업(합성 H) "276000" 2%
TIGER 구리실물 "160580"        3% 
KBSTAR 미국S&P원유생산기업(합성 H) "219390"   3%

'''


asset = dict()
asset['stock_code'] = "411060"          #종목코드
asset['stock_type'] = "MAT" 
asset['stock_target_rate'] = 6   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


asset = dict()
asset['stock_code'] = "276000"          #종목코드
asset['stock_type'] = "MAT" 
asset['stock_target_rate'] = 2   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "160580"          #종목코드
asset['stock_type'] = "MAT" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)

asset = dict()
asset['stock_code'] = "219390"          #종목코드
asset['stock_type'] = "MAT" 
asset['stock_target_rate'] = 3   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)


'''
CASH
KOSEF 단기자금 "130730"

'''

asset = dict()
asset['stock_code'] = "130730"          #종목코드
asset['stock_type'] = "CASH" 
asset['stock_target_rate'] = 0   #포트폴리오 목표 비중
asset['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
MyPortfolioList.append(asset)




##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################



MyPortfolioListReal = list()

#모든 자산의 모멘텀 스코어 구하기! 
for stock_info in MyPortfolioList:
    print("....")
    stock_code = stock_info['stock_code']

    print(KisKR.GetStockName(stock_code), " ", stock_code)

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

            stock_info['stock_target_rate'] *= (0.5 + avg_momentum_score/2.0)

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

        stock_info['stock_target_rate'] *= (0.5 + avg_momentum_score/2.0)


    print("1차 최종 비중: ", stock_info['stock_target_rate'])

    #절대 모멘텀 개념을 사용하여 모멘텀 스코어가 마이너스인 건 비중을 0으로 만들어 아예 투자하지 않는 전략도 가능합니다
    if MomentumScore < 0:
        stock_info['stock_target_rate'] = 0


    MyPortfolioListReal.append(stock_info)

    print("----------------------------------------------------")




TotalRate = 0 
RemainRate = 0 #남은 비중..
for stock_info in MyPortfolioList:

    TotalRate += stock_info['stock_target_rate']

RemainRate = 100.0 - TotalRate
print("남은 현금 비중: ", RemainRate , "%")

#이 남은 현금의 45%는 단기자금에 투자 45%는 보너스.. 10%는 그냥 원화 현금 보유..
if RemainRate > 0:
        
    print("-> 남은 현금의 45% 단기자금에 투자!")
    #최종 안전자산인 단기 자금의 비중이 여기서 정해진다!!!
    for stock_info in MyPortfolioList:
        print("....", stock_code)
        stock_code = stock_info['stock_code']

        if stock_info['stock_type'] == "CASH":
            stock_info['stock_target_rate'] = RemainRate * 0.45

    print("-> 남은 현금의 45%는 모멘텀 스코어 높은거 탑 12에 분산 보너스!, 남은 10%는 현금 보유...")


    '''
    모멘텀 스코어를 구해서... 상위 탑 12에 보너스 분산투자!

    (24분할해서 차등 지급.)
    3
    3
    3
    3
    2
    2
    2
    2
    1
    1
    1
    1

    '''

    RateCell = RemainRate * 0.45 / 24.0

    TopCnt = 12


    Alldata = sorted(MyPortfolioListReal, key=lambda stock_info: (stock_info['stock_momentum_score']), reverse= True)
    pprint.pprint(Alldata)

    #이 리스트에는 수익률(모멘텀 점수)가 가장 높은거 12개 들어간다!
    TopStockCodeList = list()

    print("모멘텀 점수가 높은 거 상위 12개!!! ")
    for i in range(0,TopCnt):
        print(KisKR.GetStockName(Alldata[i]['stock_code']) , i+1, "위!!")
        TopStockCodeList.append(Alldata[i]['stock_code'])



    print("-------상위 12개에 차등 보너스!!---------")
    Start_mul = 3.0
    check_i = 0
    for stock in TopStockCodeList:

        for stock_info in MyPortfolioList:
            if stock == stock_info['stock_code']:
                print(KisKR.GetStockName(stock) , " Start_mul ", Start_mul," check_i", check_i, " 추가 비중 ", RateCell*Start_mul)

                if stock_info['stock_momentum_score'] > 0:

                    stock_info['stock_target_rate'] += (RateCell*Start_mul)

                    print("모멘텀 스코어 양수여서 추가 비중 반영!!!!  ")
                else:

                    print("모멘텀 스코어 음수라서 보너스 제외!! 해당 추가 비중은 순수 현금 보유 ")
                
                check_i += 1

                if check_i % 4 == 0:
                    Start_mul -= 1.0
                print("                     ")

                

                

    print("------------------------")







#매수 되었지만 현재 포트폴리오에는 해당되지 않는 종목
PortfolioNotStock = list()

#내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
for my_stock in MyStockList:
    IsInPortFolio = False
    for stock_info in MyPortfolioList:
        #내주식 코드
        stock_code = stock_info['stock_code']
        
        if my_stock['StockCode'] == stock_code:
            IsInPortFolio = True
            break
    
    if IsInPortFolio == False:
        PortfolioNotStock.append(my_stock)

print("--------NOT PORTFOLIO!!-----------------")
for my_stock in PortfolioNotStock:
    print(KisKR.GetStockName(my_stock['StockCode']))

print("--------NOT PORTFOLIO!! End-----------------")


print("--------------리밸런싱 수량 계산 ---------------------")

strResult = "-- 현재 포트폴리오 상황 --\n"

#매수된 자산의 총합!
total_stock_money = 0
TotalRate = 0

#현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
for stock_info in MyPortfolioList:

    #내주식 코드
    stock_code = stock_info['stock_code']

    TotalRate += stock_info['stock_target_rate']

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

    #잔고에 없는 경우
    else:

        
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

print(" TotalRate " ,TotalRate, "%")


print("--------------------------------------------")

##########################################################


#리밸런싱이 가능한 상태여야 하고 매수 매도는 장이 열려있어야지만 가능하다!!!
if Is_Rebalance_Go == True and IsMarketOpen == True:

    line_alert.SendMessage(PortfolioName + " (" + strYM + ") 리밸런싱 시작!!")

    print("------------------리밸런싱 시작  ---------------------")

    #포트폴리오에 제외된 종목은 과감히 시장가로 매도처리!
    for my_stock in PortfolioNotStock:
        
        print(KisKR.GetStockName(my_stock['StockCode']), ".... SELL Because Not PortFolio !!!!!")

        line_alert.SendMessage(KisKR.GetStockName(my_stock['StockCode']) + " 이 종목은 포트폴리오에 포함 안되었으니 모두 직접 매도하세요!!!!!")

        #시장가로 매도 처리!!!!!
        #pprint.pprint(KisKR.MakeSellMarketOrder(my_stock['StockCode'],int(my_stock['StockAmt'])))

        #나중에 투자금이 커지면 시장가 매도시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
        '''
        CurrentPrice = KisKR.GetCurrentPrice(my_stock['StockCode'])
        CurrentPrice *= 0.99 #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
        pprint.pprint(KisKR.MakeSellLimitOrder(my_stock['StockCode'],int(my_stock['StockAmt']),CurrentPrice))
        '''

    #3초 정도 쉬어준다
    time.sleep(3.0)
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

            line_alert.SendMessage(KisKR.GetStockName(stock_code) + " " + str(abs(rebalance_amt)) + "주 직접 매도하세요!")

            #이렇게 시장가로 매도 해도 큰 무리는 없어 보인다!       
            #pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,abs(rebalance_amt)))

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

            line_alert.SendMessage(KisKR.GetStockName(stock_code) + " " + str(rebalance_amt) + "주 직접 매수하세요!")

                    
            #이렇게 시장가로 매수 해도 큰 무리는 없어 보인다!  
            #pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,rebalance_amt))

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

