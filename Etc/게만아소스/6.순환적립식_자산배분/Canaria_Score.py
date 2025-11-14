# -*- coding: utf-8 -*-
'''

-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-


관련 포스팅

앞으로 30년간 주식시장이 하락해도 수익나는 미친 전략 - 순환적립식 투자 + 자산배분을 카나리아 자산들을 통해 스마트하게 개선하기!
https://blog.naver.com/zacra/222969725781

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import json


#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL



CanariaScoreDict = dict()

canaria_file_path = "/var/autobot/CanariaScore.json"
try:
    with open(canaria_file_path, 'r') as json_file:
        CanariaScoreDict = json.load(json_file)

except Exception as e:
    print("Exception by First")

'''
카나리아 자산

SPY : 미국 주식
VEA : 선진국 주식
VWO : 개발도상국 주식
BND : 미국 혼합채권

'''
StockCodeList = ["SPY","VEA","VWO","BND"]

Avg_Period = 10

Sum_Avg_MomenTum = 0
print("------------------------")
for stock_code in StockCodeList:

    df = Common.GetOhlcv("US",stock_code,200)
    Now_Price = Common.GetCloseData(df,-1) #현재가

   # print("Now_Price", Now_Price)

    Up_Count = 0
    Start_Num = -20
    for i in range(1,int(Avg_Period)+1):
        
        CheckPrice = Common.GetCloseData(df,Start_Num)
       # print(CheckPrice, "  <<-  df[-", Start_Num,"]")

        if Now_Price >= CheckPrice:
          #  print("UP!")
            Up_Count += 1.0


        Start_Num -= 20

    avg_momentum_score = Up_Count/Avg_Period

    CanariaScoreDict[stock_code] = avg_momentum_score

    Sum_Avg_MomenTum += avg_momentum_score

    print(stock_code, "10개월 평균 모멘텀 ", CanariaScoreDict[stock_code])


CanariaScoreDict['TOTAL_AVG'] = (Sum_Avg_MomenTum / len(StockCodeList))
print("------------------------")
print("모든 카나리아 자산의 10개월 평균 모멘텀의 평균 ", CanariaScoreDict['TOTAL_AVG'])
print("------------------------")
with open(canaria_file_path, 'w') as outfile:
    json.dump(CanariaScoreDict, outfile)