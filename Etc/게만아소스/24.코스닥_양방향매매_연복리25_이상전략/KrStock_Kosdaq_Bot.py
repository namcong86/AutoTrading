#-*-coding:utf-8 -*-
'''

관련 포스팅

연복리 25%의 코스닥 지수 양방향 매매 전략!
https://blog.naver.com/zacra/223078498415

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


BOT_NAME = Common.GetNowDist() + "_MyKosdaq_ETF_Bot"


#포트폴리오 이름
PortfolioName = "게만아 코스닥 지수 양방향 매매 전략!"


#시간 정보를 읽는다
time_info = time.gmtime()


print("time_info.tm_mon", time_info.tm_mon)





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


InvestStockList = ['233740','251340'] #KODEX 코스닥150레버리지,  KODEX 코스닥150선물인버스

InverseStockCode = '251340' # KODEX 코스닥150선물인버스


InvestStockList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "233740" # KODEX 코스닥150레버리지
InvestDataDict['rate'] = 0.7
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "251340" # KODEX 코스닥150선물인버스
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



    Isheaven = False

    if 5 <= time_info.tm_mon and time_info.tm_mon <= 10:
        Isheaven = False
        print("5월~10월 지옥 상황")

    else:
        Isheaven = True
        print("11월~4월 천국 상황")


    for stock_data in InvestStockList:

        stock_code = stock_data['ticker']



        InvestMoney = TotalMoney * stock_data['rate']


        #일봉 정보를 가지고 온다!
        df_day = Common.GetOhlcv("KR",stock_code)

        #5, 10, 18선으로 투자
        Ma5 = Common.GetMA(df_day,5,-2)   #전일 종가 기준 5일 이동평균선
        Ma10 = Common.GetMA(df_day,10,-2)   #전일 종가 기준 10일 이동평균선
        Ma18 = Common.GetMA(df_day,18,-2) #전일 종가 기준 18일 이동평균선

        Ma30_before = Common.GetMA(df_day,30,-3) # 전전일 종가 기준 30일 이동평균선
        Ma30 = Common.GetMA(df_day,30,-2) # 전일 종가 기준 30일 이동평균선

        PrevClose = df_day['close'].iloc[-2] #전일 종가!


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


        print("Ma5: ", Ma5)
        print("Ma10: ", Ma10)
        print("Ma18: ", Ma18)
        print("Ma30: ", Ma30)
        print("PrevClose: ", PrevClose)

        #잔고가 있다 즉 매수된 상태다!
        if stock_amt > 0:


            IsSellGo = False
            

            if InverseStockCode == stock_code: #인버스

                #인버스에서 11-4는 지옥일테니깐
                if Isheaven == True:

                    #30일선 아래면 or 조건으로 이평조건 하나만 불만족해도 팔아 재낀다
                    if PrevClose < Ma30 :
                        if  PrevClose < Ma5 or PrevClose < Ma10 or PrevClose < Ma18 : 
                            IsSellGo = True 

                    #30일선 위라면 기존대로..
                    else:
                        if  PrevClose < Ma5 and PrevClose < Ma10 and PrevClose < Ma18 : 
                            IsSellGo = True

                #인버스에서 5-10 기간은 천국일테니깐 잘 안팔게 and로 유지
                else:
                    if  PrevClose < Ma5 and PrevClose < Ma10 and PrevClose < Ma18 : 
                        IsSellGo = True


            else: # 2배 레버리지 

                #11-4천국에는 레버리지는 잘 안팔게 and로 유지
                if Isheaven == True:
                    if  PrevClose < Ma5 and PrevClose < Ma10 and PrevClose < Ma18 : 
                        IsSellGo = True

                #레버리지에서 5-10 기간은 지옥이니깐 
                else:
                    #하락장이면 or로 팔아재낀다.
                    if PrevClose < Ma30 and Ma30_before > Ma30  and Ma5 < Ma10 < Ma18  :
                        if  PrevClose < Ma5 or PrevClose < Ma10 or PrevClose < Ma18 : 
                            IsSellGo = True 

                    #아닐 경우는 and로 유지
                    else:
                        if  PrevClose < Ma5 and PrevClose < Ma10 and PrevClose < Ma18 : 
             
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

            if InverseStockCode == stock_code: #인버스

                #11-4 천국에는 인버스는 타이트하게 잡는다!
                if Isheaven == True:
                    if PrevClose > Ma5 and PrevClose > Ma10  and PrevClose > Ma18 :
                        if PrevClose > Ma30 and Ma30_before < Ma30  and Ma5 > Ma10 > Ma18 :
                            IsBuyGo = True
                else:
                    #10-5 지옥에는 인버스는 살짝 느슨하게 잡는다.
                    if PrevClose > Ma5 and PrevClose > Ma10  and PrevClose > Ma18 :
                        if Ma30_before < Ma30 :
                            IsBuyGo = True

            else: #레버리지 

                #11-4 천국에는 레버리지는 기존 조건 만족하면 잡는다.
                if Isheaven == True:
                    if PrevClose > Ma5 and PrevClose > Ma10  and PrevClose > Ma18 :
                        IsBuyGo = True
                
                else:
                    #10-5 지옥에는 레버리지는 살짝 타이트하게 잡는다.
                    if PrevClose > Ma5 and PrevClose > Ma10  and PrevClose > Ma18 :
                        if PrevClose > Ma30  :
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




