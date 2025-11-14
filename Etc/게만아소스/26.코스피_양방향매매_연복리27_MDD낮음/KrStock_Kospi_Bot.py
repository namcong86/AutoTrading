#-*-coding:utf-8 -*-
'''

관련 포스팅

연복리 26%의 MDD 10~16의 강력한 코스피 지수 양방향 매매 전략!
https://blog.naver.com/zacra/223085637779

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


  


'''

# 상위 폴더의 공통 모듈을 import하기 위한 경로 설정
import sys
import os

# 현재 스크립트의 상위 폴더를 Python 경로에 추가
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # 게만아소스 폴더
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import time
import json
import pprint

import line_alert



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL


BOT_NAME = Common.GetNowDist() + "_MyKospi_ETF_Bot"


#포트폴리오 이름
PortfolioName = "게만아 코스피 지수 양방향 매매 전략!"


#시간 정보를 읽는다
time_info = time.gmtime()


print("time_info.tm_mon", time_info.tm_mon)





#####################################################################################################################################

#계좌 잔고를 가지고 온다!
Balance = KisKR.GetBalance()


print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")


##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################




#내 계좌의 총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.2

#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("전략에 투자하는 총 금액: ", format(round(TotalMoney), ','))


#InvestStockList = ['122630','252670'] #KODEX 레버리지, KODEX 200선물인버스2X

InverseStockCode = '252670' #KODEX 200선물인버스2X

InvestStockList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "122630" #KODEX 레버리지
InvestDataDict['rate'] = 0.7
InvestStockList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "252670"  #KODEX 200선물인버스2X
InvestDataDict['rate'] = 0.3
InvestStockList.append(InvestDataDict)


#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()

if IsMarketOpen == True:
    print("Market Is Open!!!!!!!!!!!")

    #혹시 이 봇을 장 시작하자 마자 돌린다면 20초르 쉬어준다.
    #그 이유는 20초는 지나야 오늘의 일봉 정보를 제대로 가져오는데
    #tm_hour가 0은 9시, 1은 10시를 뜻한다. 수능 등 10시에 장 시작하는 경우르 대비!
    if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
        time.sleep(20.0)
        
    line_alert.SendMessage(PortfolioName + "  장이 열려서 매매 가능!!")



    for stock_data in InvestStockList:

        stock_code = stock_data['ticker']

        InvestMoney = TotalMoney * stock_data['rate']

        #일봉 정보를 가지고 온다!
        df_day = Common.GetOhlcv("KR",stock_code)

        #인버스를 위한 3, 6, 19선으로 투자
        Ma3 = Common.GetMA(df_day,3,-2)   #전일 종가 기준 3일 이동평균선
        Ma6 = Common.GetMA(df_day,6,-2)   #전일 종가 기준 6일 이동평균선
        Ma19 = Common.GetMA(df_day,19,-2)   #전일 종가 기준 19일 이동평균선

        Ma60_before = Common.GetMA(df_day,60,-3) # 전전일 종가 기준 60일 이동평균선
        Ma60 = Common.GetMA(df_day,60,-2) # 전일 종가 기준 60일 이동평균선

        PrevClose = df_day['close'].iloc[-2] #전일 종가!

        Disparity11 = (PrevClose/Common.GetMA(df_day,11,-2))*100.0 #전일 종가 기준 11선 이격도
        Disparity20 = (PrevClose/Common.GetMA(df_day,20,-2))*100.0 #전일 종가 기준 20선 이격도


        Rsi_before = Common.GetRSI(df_day,14,-3) 
        Rsi = Common.GetRSI(df_day,14,-2) 


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

        #잔고에 없는 경우 
        if stock_amt == 0:
            stock_name = KisKR.GetStockName(stock_code)


        print("----stock_code: ", stock_code, " ", stock_name)

        print("종목당 할당 투자금:", InvestMoney)


        print("Ma3: ", Ma3)
        print("Ma6: ", Ma6)
        print("Ma19: ", Ma19)
        print("Ma60: ", Ma60)
        print("PrevClose: ", PrevClose)
        print("Disparity11: ", Disparity11)
        print("Disparity20: ", Disparity20)

        #잔고가 있다 즉 매수된 상태다!
        if stock_amt > 0:


            IsSellGo = False
            


            if InverseStockCode == stock_code: #인버스
    
                if Disparity11 > 105:
                    #
                    if  PrevClose < Ma3: 
                        IsSellGo = True

                else:
                    #
                    if PrevClose < Ma6 and PrevClose < Ma19 : 
                        IsSellGo = True

            else:

                total_volume = (df_day['volume'].iloc[-4] + df_day['volume'].iloc[-3] + df_day['volume'].iloc[-2]) / 3.0

                if (df_day['low'].iloc[-3] < df_day['low'].iloc[-2] or df_day['volume'].iloc[-2] < total_volume) and (Disparity20 < 98 or Disparity20 > 105):
                    print("hold..")
                else:
                    IsSellGo = True


            if IsSellGo == True:
 
                #이렇게 시장가로 매도 해도 큰 무리는 없어 보인다!       
                pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,stock_amt))


                #나중에 투자금이 커지면 시장가 매도시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
                '''
                CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                CurrentPrice *= 0.99 #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
                pprint.pprint(KisKR.MakeSellLimitOrder(stock_code,stock_amt,CurrentPrice))
                '''
                

                #지정가 괴리율 등을 반영해 매도하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요! -  다만 아래 경우 매도가는 시가가 아니게 될 수 있음
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

                Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,stock_amt,"DAY_END_TRY_ETF")
                '''

                msg = stock_name + "  조건을 불만족해 모두 매도!!!" + str(stock_revenue_money) + " 수익 확정!! 수익률:" + str(stock_revenue_rate) + "%"
                print(msg)
                line_alert.SendMessage(msg)

            else:

                msg = stock_name + "  투자중..!!!" + str(stock_revenue_money) + " 수익 중!! 수익률:" + str(stock_revenue_rate) + "%"
                print(msg)
                line_alert.SendMessage(msg)
                    
        #잔고가 없는 경우
        else:


            IsBuyGo = False



            if InverseStockCode == stock_code:

                if PrevClose > Ma3 and PrevClose > Ma6  and PrevClose > Ma19 and Rsi < 70 and Rsi_before < Rsi:
                    if PrevClose > Ma60 and Ma60_before < Ma60  and Ma3 > Ma6 > Ma19 :
                        IsBuyGo = True

            else:

                if df_day['low'].iloc[-3] < df_day['low'].iloc[-2] and Rsi < 80 and (Disparity20 < 98 or Disparity20 > 106) :
                    IsBuyGo = True
            

            if IsBuyGo == True:



                #현재가!
                CurrentPrice = KisKR.GetCurrentPrice(stock_code)


                #매수할 수량을 계산한다!
                BuyAmt = int(InvestMoney / CurrentPrice)

                #최소 1주는 살 수 있도록!
                if BuyAmt <= 0:
                    BuyAmt = 1


        
                #이렇게 시장가로 매수 해도 큰 무리는 없어 보인다!  
                pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,BuyAmt))

                #나중에 투자금이 커지면 시장가 매수시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
                '''
                CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                CurrentPrice *= 1.01 #현재가의 1%위의 가격으로 지정가 매수.. (그럼 1% 위 가격보다 작은 가격의 호가들은 모두 체결되기에 제한있는 시장가 매수 효과)
                pprint.pprint(KisKR.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice))
                '''


                #지정가 괴리율 등을 반영해 매수하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요!  다만 이 경우 매수가는 시가가 아니게 될 수 있음
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


                Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,BuyAmt,"DAY_END_TRY_ETF")
                '''

                msg = stock_name + "  조건을 만족하여 매수!!! 투자 시작!! "
                print(msg)
                line_alert.SendMessage(msg)
            else:

                msg = stock_name + "  조건 불만족!!! 투자 안함."
                print(msg)
                line_alert.SendMessage(msg)

else:
    print("Market Is Close!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!

    line_alert.SendMessage(PortfolioName + "  장이 열려있지 않아요!")




