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
import KIS_API_Helper_KR as KisKR
import time
import json
import random
import fcntl
import line_alert

#from tendo import singleton 
#me = singleton.SingleInstance()

#장이 열린지 여부 판단을 위한 계좌 정보로 현재 자동매매중인 계좌명 아무거나 넣으면 됩니다.
Common.SetChangeMode("REAL") #즉 다계좌 매매로 REAL, REAL2, REAL3 여러개를 자동매매 해도 한개만 여기 넣으면 됨!

IsMarketOpen = KisKR.IsMarketOpen()

auto_order_file_path = "/var/autobot/KIS_KR_SplitTrader_AutoOrderList.json"
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


#장이 열린 상황에서만!
if IsMarketOpen == True:
    print("장이 열린 상황")

    items_to_remove = list()

    #저장된 분할 매매 데이터를 순회한다 
    for AutoSplitData in AutoOrderList:
        
        #매도를 먼저 한다!
        if AutoSplitData['OrderType'] == "Sell":
            print(AutoSplitData)

            #계좌 세팅!
            Common.SetChangeMode(AutoSplitData['AccountType'])

            DIST = Common.GetNowDist()


            #시간 카운트를 증가시킨다.
            AutoSplitData['TimeCnt'] += 1
            #시간 카운트가 시간 텀보다 크거나 같으면 주문을 처리한다.
            if AutoSplitData['TimeCnt'] >= AutoSplitData['TimeTerm']:
                AutoSplitData['TimeCnt'] = 0
                AutoSplitData['OrderCnt'] += 1

                IsLastOrder = False
                if AutoSplitData['OrderCnt'] >= AutoSplitData['SplitCount']:
                    IsLastOrder = True
                    items_to_remove.append(AutoSplitData)
                    
                nowPrice = KisKR.GetCurrentPrice(AutoSplitData['stock_code'])

                SellVolume = AutoSplitData['SplitSellVolume']

                MyStockList = KisKR.GetMyStockList()

                # 보유 주식 수량을 가져옵니다.
                stock_amt = 0
                for my_stock in MyStockList:
                    if my_stock['StockCode'] == AutoSplitData['stock_code']:
                        stock_amt = int(my_stock['StockAmt'])
                        
                IsAllSell = False

                if SellVolume > stock_amt:
                    SellVolume = stock_amt
                    IsAllSell = True
                    
                    if IsLastOrder == False:
                        items_to_remove.append(AutoSplitData)

                
                #마지막 주문이고 LastSellAll이 True라면 모두 매도한다.  
                if IsLastOrder == True:
                    if 'LastSellAll' in AutoSplitData and AutoSplitData['LastSellAll'] == True:
                        SellVolume = stock_amt
                

                # 매도!
                data = KisKR.MakeSellMarketOrder(AutoSplitData['stock_code'], SellVolume)
                print(data)
                time.sleep(0.2)

                msg = DIST + " " + AutoSplitData['stock_code'] + " " + KisKR.GetStockName(AutoSplitData['stock_code']) + " " +  str(AutoSplitData['OrderVolume']) + "개 (" + str(nowPrice*AutoSplitData['OrderVolume']) +")원어치 " + str(AutoSplitData['SplitCount']) + "분할 매도 중입니다.\n"
                msg += str(AutoSplitData['OrderCnt']) + "번째 매도 수량: " + str(SellVolume) + "개 (" + str(nowPrice*SellVolume) +")원어치 매도 주문 완료!"
                if IsAllSell == True:
                    msg += " (남은 분할 수가 있지만 수량 부족으로 모두 매도 완료!)"

                if IsLastOrder == True:
                    msg += " 마지막 매도까지 모두 완료!"

                print(msg)
                line_alert.SendMessage(msg)



    
    #저장된 분할 매매 데이터를 순회한다 
    for AutoSplitData in AutoOrderList:
        
        #매수를 후에 한다!
        if AutoSplitData['OrderType'] == "Buy":
            print(AutoSplitData)

            #계좌 세팅!
            Common.SetChangeMode(AutoSplitData['AccountType'])

            DIST = Common.GetNowDist()


            #시간 카운트를 증가시킨다.
            AutoSplitData['TimeCnt'] += 1
            #시간 카운트가 시간 텀보다 크거나 같으면 주문을 처리한다.
            if AutoSplitData['TimeCnt'] >= AutoSplitData['TimeTerm']:
                AutoSplitData['TimeCnt'] = 0
                AutoSplitData['OrderCnt'] += 1

                IsLastOrder = False
                if AutoSplitData['OrderCnt'] >= AutoSplitData['SplitCount']:
                    IsLastOrder = True
                    items_to_remove.append(AutoSplitData)
                    
                nowPrice = KisKR.GetCurrentPrice(AutoSplitData['stock_code'])

                #계좌 잔고를 가지고 온다!
                Balance = KisKR.GetBalance()

                RemainMoney = float(Balance['RemainMoney'])


                if AutoSplitData['SplitBuyVolume'] * nowPrice > RemainMoney:
                    AutoSplitData['SplitBuyVolume'] = int((RemainMoney * 0.7) / nowPrice) #수수료 및 슬리피지 시장가 고려

                #첫번째 매수!
                data = KisKR.MakeBuyMarketOrder(AutoSplitData['stock_code'],AutoSplitData['SplitBuyVolume'])
                print(data)
                time.sleep(0.2)

                msg = DIST + " " + AutoSplitData['stock_code'] + " " + KisKR.GetStockName(AutoSplitData['stock_code']) + " " + str(AutoSplitData['OrderVolume']) + "주 현재가 기준 약(" + str(nowPrice*AutoSplitData['OrderVolume']) +")원어치 " + str(AutoSplitData['SplitCount']) + "분할 매수 중입니다.\n"
                msg += str(AutoSplitData['OrderCnt']) + "번째 : " + str(AutoSplitData['SplitBuyVolume']) + "주 매수 주문 완료!"
                if IsLastOrder == True:
                    msg += " 마지막 매수까지 모두 완료!"
                    
                print(msg)
                line_alert.SendMessage(msg)
            
           

    #리스트에서 제거
    for item in items_to_remove:
        try:
            AutoOrderList.remove(item)
        except Exception as e:
            print(e)


    time.sleep(random.random()*0.1)
    #파일에 저장
    with open(auto_order_file_path, 'w') as outfile:
        fcntl.flock(outfile, fcntl.LOCK_EX)
        json.dump(AutoOrderList, outfile)
        fcntl.flock(outfile, fcntl.LOCK_UN)
