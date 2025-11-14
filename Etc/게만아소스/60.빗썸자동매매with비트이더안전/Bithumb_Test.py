
#-*-coding:utf-8 -*-
'''

관련 포스팅 
https://blog.naver.com/zacra/223582852975
위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import myBithumb
import pprint


print("모든 코인 티커 가져오기 ")
tickers = myBithumb.GetTickers()
print(tickers)
print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("잔고 가져오기 ")
balances = myBithumb.GetBalances()

won = myBithumb.GetCoinAmount(balances,"KRW")

print(">>>>" , won ," <<<")


pprint.pprint(balances)
print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("금액 확인 ")
print("GetTotalMoney: ",myBithumb.GetTotalMoney(balances))
print("GetTotalRealMoney: ",myBithumb.GetTotalRealMoney(balances))
print("GetHasCoinCnt ", myBithumb.GetHasCoinCnt(balances))

print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("보유 중인 코인 데이터 체크!")
for ticker in tickers:
    if myBithumb.IsHasCoin(balances,ticker):
        print("has coin!", ticker)
        print("GetAvgBuyPrice: ",myBithumb.GetAvgBuyPrice(balances,ticker))
        print("GetCurrentPrice: ",myBithumb.GetCurrentPrice(ticker))

        print("GetCoinNowMoney ", myBithumb.GetCoinNowMoney(balances,ticker))
        print("GetCoinNowRealMoney ", myBithumb.GetCoinNowRealMoney(balances,ticker))
        print("GetRevenueRate: ",myBithumb.GetRevenueRate(balances,ticker))

        pprint.pprint(myBithumb.GetRevenueMoneyAndRate(balances,ticker))
        print("\n")
        

#'''
print("###################################################################")
print("###################################################################")
print("###################################################################")
print("일봉 정보 가져오기 예시")
df = myBithumb.GetOhlcv("KRW-BTC",'1d',1000) #period: 1d,4h,1h,30m,15m,10m,5m,3m,1m
pprint.pprint(df)


print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")
#'''

'''       
print("시장가 주문 예시") 
balances = myBithumb.BuyCoinMarket("KRW-ETH",10000)

amount = myBithumb.GetCoinAmount(balances,"KRW-ETH")
print("amount ", amount)

balances = myBithumb.SellCoinMarket("KRW-ETH",amount/2.0)
'''

'''
print("지정가 주문 예시") 
amount = myBithumb.GetCoinAmount(balances,"KRW-ETH")
print("amount ", amount)

target_price =float(myBithumb.GetCurrentPrice("KRW-ETH")) * 0.95
myBithumb.BuyCoinLimit("KRW-ETH",target_price,amount)

time.sleep(0.2)
target_price =float(myBithumb.GetCurrentPrice("KRW-ETH")) * 1.05
myBithumb.SellCoinLimit("KRW-ETH",target_price,amount)
'''

'''
print("주문 정보 예시") 
pprint.pprint(myBithumb.GetActiveOrders("KRW-ETH"))
print("---------------\n")
pprint.pprint(myBithumb.CancelCoinOrder("KRW-ETH"))
print("---------------\n")
pprint.pprint(myBithumb.GetActiveOrders("KRW-ETH"))

'''
