'''


관련 포스팅
https://blog.naver.com/zacra/223744333599
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
import myBithumb
import time
import random
import json
import line_alert
import fcntl

#from tendo import singleton 
#me = singleton.SingleInstance()

DIST = "빗썸"

balances = myBithumb.GetBalances()

#최소 금액 
minimumMoney = 5000


auto_order_file_path = "/var/autobot/Bithumb_SplitTrader_AutoOrderList.json"
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




items_to_remove = list()


#저장된 분할 매매 데이터를 순회한다 
for AutoSplitData in AutoOrderList:
    
    #매도를 먼저 한다!!
    if AutoSplitData['OrderType'] == "Sell":
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
                

        

            SellVolume = AutoSplitData['SplitSellVolume']
            nowPrice = myBithumb.GetCurrentPrice(AutoSplitData['Ticker'])
            time.sleep(0.2)

            AllVolume = myBithumb.GetCoinAmount(balances,AutoSplitData['Ticker']) #현재 보유 수량
            time.sleep(0.2)


            if AllVolume * nowPrice < minimumMoney:

                msg = DIST + " " + AutoSplitData['Ticker'] + " 현재 보유 수량이 최소 주문 금액보다 적어서 매도 주문을 취소합니다."
                print(msg)
                line_alert.SendMessage(msg)

                if IsLastOrder == False:
                    items_to_remove.append(AutoSplitData)

            else:

                #마지막 주문이라면 매도했을 때 남은 금액이 5000원 이하라면 자투리로 판단 모두 매도한다.   
                if IsLastOrder == True:
                    
                    if 'LastSellAll' in AutoSplitData and AutoSplitData['LastSellAll'] == True:
                        SellVolume = AllVolume
                    else:
                        #남은 수량과 매도 수량의 차이를 구한다.
                        GapVolume = abs(AllVolume - SellVolume)
                    
                        #마지막 주문이라면 매도했을 때 남은 금액이 5000원 이하라면 자투리로 판단 모두 매도한다.   
                        if GapVolume * nowPrice <= minimumMoney:
                            SellVolume = AllVolume



                #매도!
                balances = myBithumb.SellCoinMarket(AutoSplitData['Ticker'], SellVolume)
                time.sleep(0.2)
                


                msg = DIST + " " + AutoSplitData['Ticker'] + " " + str(AutoSplitData['OrderVolume']) + "개 (" + str(nowPrice*AutoSplitData['OrderVolume']) +")원어치 " + str(AutoSplitData['SplitCount']) + "분할 매도 중입니다.\n"
                msg += str(AutoSplitData['OrderCnt']) + "번째 매도 수량: " + str(AutoSplitData['SplitSellVolume']) + "개 (" + str(nowPrice*AutoSplitData['SplitSellVolume']) +")원어치 매도 주문 완료!"
                if IsLastOrder == True:
                    msg += " 마지막 매도까지 모두 완료!"
                    
                print(msg)
                line_alert.SendMessage(msg)




#저장된 분할 매매 데이터를 순회한다 
for AutoSplitData in AutoOrderList:
    
    #매수를 후에 한다!
    if AutoSplitData['OrderType'] == "Buy":
            
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
                

            

            #원화 잔고를 가져온다
            won = myBithumb.GetCoinAmount(balances,"KRW")
            print("# Remain Won :", won)
            time.sleep(0.004)

            if AutoSplitData['SplitBuyMoney'] > won:
                AutoSplitData['SplitBuyMoney'] = won * 0.99 #수수료 


            if AutoSplitData['SplitBuyMoney'] < minimumMoney:
                msg = DIST + " " + AutoSplitData['Ticker'] + " 현재 보유 원화가 최소 주문 금액보다 적어서 매수 주문을 취소합니다."
                print(msg)
                line_alert.SendMessage(msg)

                if IsLastOrder == False:
                    items_to_remove.append(AutoSplitData)
            else:

                balances = myBithumb.BuyCoinMarket(AutoSplitData['Ticker'], AutoSplitData['SplitBuyMoney'])
                time.sleep(0.2)

                msg = DIST + " " + AutoSplitData['Ticker'] + " " + str(AutoSplitData['OrderMoney']) + "를 " + str(AutoSplitData['SplitCount']) + "분할 매수 중입니다.\n"
                msg += str(AutoSplitData['OrderCnt']) + "번째 매수 금액: " + str(AutoSplitData['SplitBuyMoney']) + " 매수 주문 완료!"
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
