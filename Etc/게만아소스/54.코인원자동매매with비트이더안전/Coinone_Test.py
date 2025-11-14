
#-*-coding:utf-8 -*-
'''

관련 포스팅 
https://blog.naver.com/zacra/223508324003

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^




##############################################################
코인원 앱 -> 하단 더보기 -> 이벤트 코드 -> 등록하기 -> ZABOBSTUDIO 
##############################################################


'''
import myCoinone
import pprint


print("모든 코인 티커 가져오기 ")
tickers = myCoinone.GetTickers()
print(tickers)
print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("잔고 가져오기 ")
balances = myCoinone.GetBalances()

won = myCoinone.GetCoinAmount(balances,"KRW")

print(">>>>" , won ," <<<")


pprint.pprint(balances)
print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("금액 확인 ")
print("GetTotalMoney: ",myCoinone.GetTotalMoney(balances))
print("GetTotalRealMoney: ",myCoinone.GetTotalRealMoney(balances))
print("GetHasCoinCnt ", myCoinone.GetHasCoinCnt(balances))

print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")

print("보유 중인 코인 데이터 체크!")
for ticker in tickers:
    if myCoinone.IsHasCoin(balances,ticker):
        print("has coin!", ticker)
        print("GetAvgBuyPrice: ",myCoinone.GetAvgBuyPrice(balances,ticker))
        print("GetCurrentPrice: ",myCoinone.GetCurrentPrice(ticker))

        print("GetCoinNowMoney ", myCoinone.GetCoinNowMoney(balances,ticker))
        print("GetCoinNowRealMoney ", myCoinone.GetCoinNowRealMoney(balances,ticker))
        print("GetRevenueRate: ",myCoinone.GetRevenueRate(balances,ticker))

        pprint.pprint(myCoinone.GetRevenueMoneyAndRate(balances,ticker))
        print("\n")
        

#'''
print("###################################################################")
print("###################################################################")
print("###################################################################")
print("일봉 정보 가져오기 예시")
df = myCoinone.GetOhlcv("BTC",'1d',1000)
pprint.pprint(df)
print("###################################################################")
print("###################################################################")
print("###################################################################\n\n")
#'''

'''       
print("시장가 주문 예시") 
balances = myCoinone.BuyCoinMarket("ETH",10000)

amount = myCoinone.GetCoinAmount(balances,"ETH")
print("amount ", amount)

balances = myCoinone.SellCoinMarket("ETH",amount/2.0)
'''

'''
print("지정가 주문 예시") 
amount = myCoinone.GetCoinAmount(balances,"ETH")
print("amount ", amount)

target_price =float(myCoinone.GetCurrentPrice("ETH")) * 0.95
myCoinone.BuyCoinLimit("ETH",target_price,amount)

time.sleep(0.2)
target_price =float(myCoinone.GetCurrentPrice("ETH")) * 1.05
myCoinone.SellCoinLimit("ETH",target_price,amount)
'''

'''
print("주문 정보 예시") 
pprint.pprint(myCoinone.GetActiveOrders("ETH"))
print("---------------\n")
pprint.pprint(myCoinone.CancelCoinOrder("ETH"))
print("---------------\n")
pprint.pprint(myCoinone.GetActiveOrders("ETH"))

'''
