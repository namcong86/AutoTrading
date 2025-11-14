# -*- coding: utf-8 -*-
'''


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다. 

해당 전략 추가 개선한 버전 안내
https://blog.naver.com/zacra/223577385295

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504


관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅
https://blog.naver.com/zacra/223559959653

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import KIS_API_Helper_KR as KisKR

import pprint

import line_alert


#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL


#포트폴리오 이름
PortfolioName = "이동평균자산배분전략_KR"

InvestStockList = list()

InvestStockList.append({"stock_code":"133690", "small_ma":5 , "big_ma":34, "invest_rate":0.4}) #TIGER 미국나스닥100
InvestStockList.append({"stock_code":"069500", "small_ma":3 , "big_ma":103, "invest_rate":0.2}) #KODEX 200
InvestStockList.append({"stock_code":"148070", "small_ma":8 , "big_ma":71, "invest_rate":0.1}) #KOSEF 국고채10년
InvestStockList.append({"stock_code":"305080", "small_ma":20 , "big_ma":61, "invest_rate":0.1}) #TIGER 미국채10년선물
InvestStockList.append({"stock_code":"132030", "small_ma":15 , "big_ma":89, "invest_rate":0.2}) #KODEX 골드선물(H)



    


#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()


#계좌 잔고를 가지고 온다!
Balance = KisKR.GetBalance()


print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")
#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.5


#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : ", TotalMoney)


##########################################################




##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
#pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################


for stock_info in InvestStockList:
    
    stock_code = stock_info['stock_code']
    
    small_ma = stock_info['small_ma']
    big_ma = stock_info['big_ma']
    
    stock_target_rate = stock_info['invest_rate']
    


    stock_name = KisKR.GetStockName(stock_code)
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


    
    
    df = Common.GetOhlcv("KR", stock_code,250)

    df['prevOpen'] = df['open'].shift(1)
    df['prevClose'] = df['close'].shift(1)
    
    ############# 이동평균선! ###############

    df[str(small_ma) + 'ma'] = df['close'].rolling(small_ma).mean()
    df[str(big_ma)+ 'ma'] = df['close'].rolling(big_ma).mean()
        
    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!
    
    
    print("---stock_code---", stock_code , " len ",len(df))
    #pprint.pprint(df)
    
    #보유중이 아니다
    if stock_amt == 0:
        
        msg = stock_name + "("+stock_code + ") 현재 매수하지 않고 현금 보유 상태! 목표할당비중:" + str(stock_target_rate*100) + "%"
        print(msg) 
        
        if df[str(small_ma) + 'ma'].iloc[-2] > df[str(big_ma) + 'ma'].iloc[-2] and df[str(small_ma) + 'ma'].iloc[-3] < df[str(small_ma) + 'ma'].iloc[-2]:
            print("비중 만큼 매수!!")
            if IsMarketOpen == True:
                
                msg = stock_name + "("+stock_code + ") 상승추세가 확인되었는데 보유수량이 없어 비중만큼 매수!!!!"
                print(msg) 
                line_alert.SendMessage(msg)
                                    
                BuyMoney = TotalMoney * stock_target_rate

                CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                
                #매수할 수량을 계산한다!
                BuyAmt = int(BuyMoney / CurrentPrice)
                
                
                CurrentPrice *= 1.01 #현재가의 1%위의 가격으로 지정가 매수.. (그럼 1% 위 가격보다 작은 가격의 호가들은 모두 체결되기에 제한있는 시장가 매수 효과)
                pprint.pprint(KisKR.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice))
                
                
                
                
    #보유중이다
    else:
        
        
        msg = stock_name + "("+stock_code + ") 현재 매수하여 보유 상태! 목표할당비중:" + str(stock_target_rate*100) + "%"
        print(msg) 
        
        if df[str(small_ma) + 'ma'].iloc[-2] < df[str(big_ma) + 'ma'].iloc[-2] and df[str(small_ma) + 'ma'].iloc[-3] > df[str(small_ma) + 'ma'].iloc[-2]:
            print("보유 수량 만큼 매도!!")
            if IsMarketOpen == True:
                
                msg = stock_name + "("+stock_code + ") 하락세가 확인되었는데 보유수량이 있어 매도!!!!"
                print(msg) 
                line_alert.SendMessage(msg)


                CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                CurrentPrice *= 0.99 #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
                pprint.pprint(KisKR.MakeSellLimitOrder(stock_code,abs(stock_amt),CurrentPrice))
                