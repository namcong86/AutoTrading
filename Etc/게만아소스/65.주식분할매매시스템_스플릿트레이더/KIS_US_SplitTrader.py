'''
관련 포스팅
https://blog.naver.com/zacra/223750328250
https://blog.naver.com/zacra/223763707914

최종 개선
https://blog.naver.com/zacra/223773295093


하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

매월 자동매매 계좌 공개를 하고 있어요!
https://m.site.naver.com/1ojdd

참고하세요 :)

'''
# -*- coding: utf-8 -*-
import KIS_Common as Common
import KIS_API_Helper_US as KisUS
import time
import json
import random
import fcntl
import line_alert

#장이 열린지 여부 판단을 위한 계좌 정보로 현재 자동매매중인 계좌명 아무거나 넣으면 됩니다.
Common.SetChangeMode("REAL") #즉 다계좌 매매로 REAL, REAL2, REAL3 여러개를 자동매매 해도 한개만 여기 넣으면 됨!

IsMarketOpen = KisUS.IsMarketOpen()

auto_order_file_path = "/var/autobot/KIS_US_SplitTrader_AutoOrderList.json"
time.sleep(random.random()*0.1)

#자동 주문 리스트 읽기!
AutoOrderList = list()
try:
    with open(auto_order_file_path, 'r') as json_file:
        fcntl.flock(json_file, fcntl.LOCK_EX)  # 파일 락 설정
        AutoOrderList = json.load(json_file)
        fcntl.flock(json_file, fcntl.LOCK_UN)  # 파일 락 해제
except Exception as e:
    print("Exception by First")


# 분할 매수 주문 함수
def MakeSplitBuyOrder(stock_code, order_volume, split_count=1, time_term=0, Exclusive=False):
    global AutoOrderList  # 전역 변수임을 명시적으로 선언
    global IsMarketOpen
    
    
    SplitCount = split_count

    if IsMarketOpen == False:
        msg = "현재 시장이 마감되었습니다. 주문을 처리하지 않습니다."
        print(msg)
        line_alert.SendMessage(msg)
        return
    

    DIST = Common.GetNowDist()
    
    if Exclusive == True:
        for AutoSplitData in AutoOrderList:
            if AutoSplitData['OrderType'] == "Buy" and AutoSplitData['AccountType'] == DIST:
                if AutoSplitData['stock_code'] == stock_code:
                    
                    msg = DIST + " " + stock_code + " 독점 분할 매수 주문이 실행 중이라 현재 진행 중인 분할 매수가 끝날 때 까지 추가 분할 매수 주문은 처리하지 않습니다."
                    print(msg)
                    line_alert.SendMessage(msg)
                    return
    
    nowPrice = KisUS.GetCurrentPrice(stock_code)
    
    IsCutSplit = False
    
    if SplitCount > 1 and order_volume > SplitCount:
    
        while int(order_volume / SplitCount) < 1:
            SplitCount -= 1
            IsCutSplit = True
            
            if SplitCount <= 1:
                break

    
    SplitBuyVolume = int(order_volume / SplitCount)
    
    if SplitBuyVolume < 1:
        SplitBuyVolume = 1



    #첫번째 매수!
    data = KisUS.MakeBuyLimitOrder(stock_code,SplitBuyVolume,nowPrice*1.01)
    print(data)
    time.sleep(0.2)

    msg = DIST + " " + stock_code + " " + str(order_volume) + "주 현재가 기준 약(" + str(nowPrice*order_volume) +")원어치 " + str(SplitCount) + "분할 매수 중입니다.\n"
    msg += "첫번째 매수 수량: " + str(SplitBuyVolume) + "주 약(" + str(nowPrice*SplitBuyVolume) +")원어치 매수 주문 완료!"
    if IsCutSplit == True:
        msg += " (분할 수량이 최소 주문 수량보다 작아서 분할 수량을 줄였습니다.)"
        
    print(msg)
    line_alert.SendMessage(msg)

    #분할 매수수가 1개 이상인 경우 데이터를 추가해서 이후 분할 매수 주문을 처리할 수 있도록 해준다.
    if split_count > 1:

        AutoSplitData = dict()
        AutoSplitData['AccountType'] = DIST
        AutoSplitData['OrderType'] = "Buy"
        AutoSplitData['stock_code'] = stock_code
        AutoSplitData['OrderVolume'] = order_volume
        AutoSplitData['SplitBuyVolume'] = SplitBuyVolume
        AutoSplitData['SplitCount'] = SplitCount
        AutoSplitData['TimeTerm'] = time_term
        AutoSplitData['TimeCnt'] = 0
        AutoSplitData['OrderCnt'] = 1

        #!!!! 데이터를 리스트에 추가하고 저장하기!!!!
        AutoOrderList.append(AutoSplitData)
        with open(auto_order_file_path, 'w') as outfile:
            fcntl.flock(outfile, fcntl.LOCK_EX)
            json.dump(AutoOrderList, outfile)
            fcntl.flock(outfile, fcntl.LOCK_UN)

# 분할 매도 주문 함수
def MakeSplitSellOrder(stock_code, order_volume, split_count=1, time_term=0, last_sell_all=False, Exclusive=False):
    global AutoOrderList  # 전역 변수임을 명시적으로 선언
    global IsMarketOpen


    SplitCount = split_count
    
    
    
    if IsMarketOpen == False:
        msg = "현재 시장이 마감되었습니다. 주문을 처리하지 않습니다."
        print(msg)
        line_alert.SendMessage(msg)
        return
    
    DIST = Common.GetNowDist()

    if Exclusive == True:
        for AutoSplitData in AutoOrderList:
            if AutoSplitData['OrderType'] == "Sell" and AutoSplitData['AccountType'] == DIST:
                if AutoSplitData['stock_code'] == stock_code:
                    
                    msg = DIST + " " + stock_code + " 독점 분할 매도 주문이 실행 중이라 현재 진행중인 분할 매도가 끝날 때 까지 추가 분할 매도 주문은 처리하지 않습니다."
                    print(msg)
                    line_alert.SendMessage(msg)
                    return
                    
    MyStockList = KisUS.GetMyStockList()
    
    nowPrice = KisUS.GetCurrentPrice(stock_code)
    
    stock_amt = 0 #수량
    

    #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
    for my_stock in MyStockList:
        if my_stock['StockCode'] == stock_code:
            stock_amt = int(my_stock['StockAmt'])
            
            
            
    IsCutSplit = False

    if SplitCount > 1 and order_volume > SplitCount:
        while int(order_volume / SplitCount) < 1:
            SplitCount -= 1
            IsCutSplit = True

            if SplitCount <= 1:
                break

    SplitSellVolume = int(order_volume / SplitCount)

    if SplitSellVolume < 1:
        SplitSellVolume = 1


    IsAllSell = False
    #남은 수량이 분할 매매 수량보다 작다면 남은 수량을 모두 판다!
    if stock_amt <= SplitSellVolume:
        SplitSellVolume = stock_amt
        IsAllSell = True
        

    #첫번째 매도!
    data = KisUS.MakeSellLimitOrder(stock_code,SplitSellVolume,nowPrice*0.99)
    print(data)
    
    if IsAllSell == True:
        msg = DIST + " " + stock_code + " 모두 매도 완료!"
        print(msg)
        line_alert.SendMessage(msg)
    else:
        msg = DIST + " " + stock_code + " " + str(order_volume) + "주 현재가 기준 약(" + str(nowPrice*order_volume) +")원어치 " + str(SplitCount) + "분할 매도 중입니다.\n"
        msg += "첫번째 매도 수량: " + str(SplitSellVolume) + "주 약(" + str(nowPrice*SplitSellVolume) +")원어치 매도 주문 완료!"
        if IsCutSplit == True:
            msg += " (분할 수량이 최소 주문 수량보다 작아서 분할 수량을 줄였습니다.)"
            
        print(msg)
        line_alert.SendMessage(msg)

        if split_count > 1:
            AutoSplitData = dict()
            AutoSplitData['AccountType'] = DIST
            AutoSplitData['OrderType'] = "Sell"
            AutoSplitData['stock_code'] = stock_code
            AutoSplitData['OrderVolume'] = order_volume
            AutoSplitData['SplitSellVolume'] = SplitSellVolume
            AutoSplitData['SplitCount'] = SplitCount
            AutoSplitData['TimeTerm'] = time_term
            AutoSplitData['TimeCnt'] = 0
            AutoSplitData['OrderCnt'] = 1
            AutoSplitData['LastSellAll'] = last_sell_all


            #!!!! 데이터를 리스트에 추가하고 저장하기!!!!
            AutoOrderList.append(AutoSplitData)
            with open(auto_order_file_path, 'w') as outfile:
                fcntl.flock(outfile, fcntl.LOCK_EX)
                json.dump(AutoOrderList, outfile)
                fcntl.flock(outfile, fcntl.LOCK_UN)


