# -*- coding: utf-8 -*-
'''
관련 포스팅
https://blog.naver.com/zacra/223530451234

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import KIS_Common as Common
import KIS_API_Helper_US as KisUS
import json
import pprint
import line_alert

Common.SetChangeMode("VIRTUAL")


#정보리스트와 차수를 받아서 차수 정보(익절기준,진입기준)을 리턴한다!
def GetSplitMetaInfo(DataList, number):
    
    PickSplitMeta = None
    for infoData in DataList:
        if number == infoData["number"]:
            PickSplitMeta =  infoData
            break
            
    return PickSplitMeta

#파일로 저장관리되는 데이터를 읽어온다(진입가,진입수량)
def GetSplitDataInfo(DataList, number):
    
    PickSplitData = None
    for saveData in DataList:
        if number == saveData["Number"]:
            PickSplitData =  saveData
            break
            
    return PickSplitData



BOT_NAME = Common.GetNowDist() + "_MagicSplitBot"


#투자할 종목! 예시.. 2개 종목 투자.
TargetStockList = ['QQQM','SCHD']


#차수 정보가 들어간 데이터 리스트!
InvestInfoDataList = list()

for stock_code in TargetStockList:
    
    InvestInfoDict = dict()
    InvestInfoDict['stock_code'] = stock_code
    
    SplitInfoList = list()
    
    if stock_code == 'QQQM':

        #1차수 설정!!!
        SplitItem = {"number":1, "target_rate":10.0 , "trigger_rate":None , "invest_money":500}  #차수, 목표수익률, 매수기준 손실률 (1차수는 이 정보가 필요 없다),투자금액
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":2, "target_rate":2.0 , "trigger_rate":-3.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":3, "target_rate":3.0 , "trigger_rate":-4.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":4, "target_rate":3.0 , "trigger_rate":-5.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":5, "target_rate":3.0 , "trigger_rate":-5.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":6, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":7, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)   
        SplitItem = {"number":8, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":9, "target_rate":5.0 , "trigger_rate":-7.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":10, "target_rate":5.0 , "trigger_rate":-7.0 , "invest_money":300} 
        SplitInfoList.append(SplitItem)
         
    elif stock_code == 'SCHD':

        #1차수 설정!!!
        SplitItem = {"number":1, "target_rate":10.0 , "trigger_rate":None , "invest_money":400}  #차수, 목표수익률, 매수기준 손실률 (1차수는 이 정보가 필요 없다),투자금액
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":2, "target_rate":2.0 , "trigger_rate":-3.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":3, "target_rate":3.0 , "trigger_rate":-4.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":4, "target_rate":3.0 , "trigger_rate":-5.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":5, "target_rate":3.0 , "trigger_rate":-5.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":6, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":7, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)   
        SplitItem = {"number":8, "target_rate":4.0 , "trigger_rate":-6.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":9, "target_rate":5.0 , "trigger_rate":-7.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
        SplitItem = {"number":10, "target_rate":5.0 , "trigger_rate":-7.0 , "invest_money":200} 
        SplitInfoList.append(SplitItem)
      
    InvestInfoDict['split_info_list'] = SplitInfoList
    
    
    InvestInfoDataList.append(InvestInfoDict)
    
    
pprint.pprint(InvestInfoDataList)


#'''
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
############# 매수후 진입시점, 수익률 등을 저장 관리할 파일 ####################
MagicNumberDataList = list()
#파일 경로입니다.
bot_file_path = "/var/autobot/UsStock_" + BOT_NAME + ".json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(bot_file_path, 'r') as json_file:
        MagicNumberDataList = json.load(json_file)

except Exception as e:
    print("Exception by First")
################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#'''


print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisUS.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
    

#마켓이 열렸는지 여부~!
IsMarketOpen = KisUS.IsMarketOpen()

#장이 열렸을 때!
if IsMarketOpen == True:


    #투자할 종목을 순회한다!
    for InvestInfo in InvestInfoDataList:
        
        stock_code = InvestInfo['stock_code'] #종목 코드
        
        #종목 정보~
        stock_name = stock_code
        stock_amt = 0 #수량
        stock_avg_price = 0 #평단
        stock_eval_totalmoney = 0 #총평가금액!
        stock_revenue_rate = 0 #종목 수익률
        stock_revenue_money = 0 #종목 수익금


        #매수된 상태라면 정보를 넣어준다!!!
        for my_stock in MyStockList:
            if my_stock['StockCode'] == stock_code:
                stock_name = my_stock['StockName']
                stock_amt = int(my_stock['StockAmt'])
                stock_avg_price = float(my_stock['StockAvgPrice'])
                stock_eval_totalmoney = float(my_stock['StockNowMoney'])
                stock_revenue_rate = float(my_stock['StockRevenueRate'])
                stock_revenue_money = float(my_stock['StockRevenueMoney'])

                break
                


        #현재가
        CurrentPrice = KisUS.GetCurrentPrice(stock_code)


            
        #종목 데이터
        PickMagicDataInfo = None

        #저장된 종목 데이터를 찾는다
        for MagicDataInfo in MagicNumberDataList:
            if MagicDataInfo['StockCode'] == stock_code:
                PickMagicDataInfo = MagicDataInfo
                break

        #PickMagicDataInfo 이게 없다면 매수되지 않은 처음 상태이거나 이전에 손으로 매수한 종목인데 해당 봇으로 돌리고자 할 때!
        if PickMagicDataInfo == None:

            MagicNumberDataDict = dict()
            
            MagicNumberDataDict['StockCode'] = stock_code #종목 코드
            MagicNumberDataDict['StockName'] = stock_name #종목 이름
            MagicNumberDataDict['IsReady'] = True #오늘 장에서 1차 매수 가능한지 플래그!

           
            MagicDataList = list()
            
            #사전에 정의된 데이터!
            for i in range(len(InvestInfo['split_info_list'])):
                MagicDataDict = dict()
                MagicDataDict['Number'] = i+1 # 차수
                MagicDataDict['EntryPrice'] = 0 #진입가격
                MagicDataDict['EntryAmt'] = 0   #진입수량
                MagicDataDict['IsBuy'] = False   #매수 상태인지 여부
                
                MagicDataList.append(MagicDataDict)

            MagicNumberDataDict['MagicDataList'] = MagicDataList
            MagicNumberDataDict['RealizedPNL'] = 0 #종목의 누적 실현손익


            MagicNumberDataList.append(MagicNumberDataDict) #데이터를 추가 한다!


            msg = stock_code + " 매직스플릿 투자 준비 완료!!!!!"
            print(msg) 
            line_alert.SendMessage(msg) 


            #파일에 저장
            with open(bot_file_path, 'w') as outfile:
                json.dump(MagicNumberDataList, outfile)


        #이제 데이터(MagicNumberDataList)는 확실히 있을 테니 본격적으로 트레이딩을 합니다!
        for MagicDataInfo in MagicNumberDataList:
            

            if MagicDataInfo['StockCode'] == stock_code:
                
           
                
                #1차수가 매수되지 않은 상태인지를 체크해서 1차수를 일단 매수한다!!
                for MagicData in MagicDataInfo['MagicDataList']:
                    if MagicData['Number'] == 1: #1차수를 찾아서!
                        if MagicData['IsBuy'] == False and MagicDataInfo['IsReady'] == True: #매수하지 않은 상태라면 매수를 진행한다!
                            
                            #새로 시작하는 거니깐 누적 실현손익 0으로 초기화!
                            MagicDataInfo['RealizedPNL'] = 0
                            
                            #1차수를 봇이 매수 안했는데 잔고에 수량이 있다면?
                            if stock_amt > 0:
                                
                                
                                MagicData['IsBuy'] = True
                                MagicData['EntryPrice'] = stock_avg_price #현재가로 진입했다고 가정합니다!
                                MagicData['EntryAmt'] = stock_amt


                                msg = stock_code + " 매직스플릿 1차 투자를 하려고 했는데 잔고가 있어서 이를 1차투자로 가정하게 세팅했습니다!"
                                print(msg) 
                                line_alert.SendMessage(msg)
                                
                            else:
                    
                                #1차수에 해당하는 정보 데이터를 읽는다.
                                PickSplitMeta = GetSplitMetaInfo(InvestInfo['split_info_list'],1)
                                
                                #투자금을 현재가로 나눠서 매수 가능한 수량을 정한다.
                                BuyAmt = int(PickSplitMeta['invest_money'] / CurrentPrice)
                                
                                #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                                if BuyAmt < 1:
                                    BuyAmt = 1

                                pprint.pprint(KisUS.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice*1.01))
                                
                                MagicData['IsBuy'] = True
                                MagicData['EntryPrice'] = CurrentPrice #현재가로 진입했다고 가정합니다!
                                MagicData['EntryAmt'] = BuyAmt


                                msg = stock_code + " 매직스플릿 1차 투자 완료!"
                                print(msg) 
                                line_alert.SendMessage(msg)
                                
                                
                                                                
                                                                
                                                                
                                #매매가 일어났으니 보유수량등을 리프레시 한다!
                                MyStockList = KisUS.GetMyStockList()
                                #매수된 상태라면 정보를 넣어준다!!!
                                for my_stock in MyStockList:
                                    if my_stock['StockCode'] == stock_code:
                                        stock_amt = int(my_stock['StockAmt'])
                                        stock_avg_price = float(my_stock['StockAvgPrice'])
                                        stock_eval_totalmoney = float(my_stock['StockNowMoney'])
                                        stock_revenue_rate = float(my_stock['StockRevenueRate'])
                                        stock_revenue_money = float(my_stock['StockRevenueMoney'])
                                        break

                            #파일에 저장
                            with open(bot_file_path, 'w') as outfile:
                                json.dump(MagicNumberDataList, outfile)
                    else:
                        if stock_amt == 0: #잔고가 0이라면 2차이후의 차수 매매는 없는거니깐 초기화!
                            MagicData['IsBuy'] = False
                            MagicData['EntryAmt'] = 0
                            MagicData['EntryPrice'] = 0   

                            #파일에 저장
                            with open(bot_file_path, 'w') as outfile:
                                json.dump(MagicNumberDataList, outfile)
                
                #매수된 차수가 있다면 수익률을 체크해서 매도하고, 매수 안된 차수도 체크해서 매수한다.
                for MagicData in MagicDataInfo['MagicDataList']:
                    
                
                    #해당 차수의 정보를 읽어온다.
                    PickSplitMeta = GetSplitMetaInfo(InvestInfo['split_info_list'],MagicData['Number'])
                        
                    #매수된 차수이다.
                    if MagicData['IsBuy'] == True:
                        
                        #현재 수익률을 구한다!
                        CurrentRate = (CurrentPrice - MagicData['EntryPrice']) / MagicData['EntryPrice'] * 100.0
                        
                        print(stock_code, " ", MagicData['Number'], "차 수익률 ", round(CurrentRate,2) , "% 목표수익률", PickSplitMeta['target_rate'], "%")
                        
                        
                        #현재 수익률이 목표 수익률보다 높다면
                        if CurrentRate >= PickSplitMeta['target_rate'] and stock_amt > 0:
                            
                            SellAmt = MagicData['EntryAmt']
                            
                            IsOver = False
                            #만약 매도할 수량이 수동 매도등에 의해서 보유 수량보다 크다면 보유수량으로 정정해준다!
                            if SellAmt > stock_amt:
                                SellAmt = stock_amt
                                IsOver = True
                        
                            
                            pprint.pprint(KisUS.MakeSellLimitOrder(stock_code,SellAmt,CurrentPrice*0.99))
                            
                            
                            MagicData['IsBuy'] = False
                            MagicDataInfo['RealizedPNL'] += (stock_revenue_money * SellAmt/stock_amt)
                            
                            
                            
                            msg = stock_code + " 매직스플릿 "+str(MagicData['Number'])+"차 수익 매도 완료! 차수 목표수익률" + str(PickSplitMeta['target_rate']) +"% 만족" 
                            
                            if IsOver == True:
                                msg = stock_code + " 매직스플릿 "+str(MagicData['Number'])+"차 수익 매도 완료! 차수 목표수익률" + str(PickSplitMeta['target_rate']) +"% 만족 매도할 수량이 보유 수량보다 많은 상태라 모두 매도함!" 


                            #1차수 매도라면 레디값을 False로 바꿔서 오늘 1차 매수가 없도록 한다!
                            if MagicData['Number'] == 1:
                               MagicDataInfo['IsReady'] = False



                            print(msg) 
                            line_alert.SendMessage(msg)
                            
                            

                            #파일에 저장
                            with open(bot_file_path, 'w') as outfile:
                                json.dump(MagicNumberDataList, outfile)
                                
                                
                                
                            #매매가 일어났으니 보유수량등을 리프레시 한다!
                            MyStockList = KisUS.GetMyStockList()
                            #매수된 상태라면 정보를 넣어준다!!!
                            for my_stock in MyStockList:
                                if my_stock['StockCode'] == stock_code:
                                    stock_amt = int(my_stock['StockAmt'])
                                    stock_avg_price = float(my_stock['StockAvgPrice'])
                                    stock_eval_totalmoney = float(my_stock['StockNowMoney'])
                                    stock_revenue_rate = float(my_stock['StockRevenueRate'])
                                    stock_revenue_money = float(my_stock['StockRevenueMoney'])
                                    break
                                
                                
                                
                        
                    #매수아직 안한 차수!
                    else:
                        
                        #이전차수 정보를 읽어온다.
                        PrevMagicData = GetSplitDataInfo(MagicDataInfo['MagicDataList'],MagicData['Number'] - 1)
                        
                        if PrevMagicData['IsBuy'] == True:
                            
                            #이전 차수 수익률을 구한다!
                            prevRate = (CurrentPrice - PrevMagicData['EntryPrice']) / PrevMagicData['EntryPrice'] * 100.0
                                
                                
                            print(stock_code, " ", MagicData['Number'], "차 진입을 위한 ",MagicData['Number']-1,"차 수익률 ", round(prevRate,2) , "% 트리거 수익률", PickSplitMeta['trigger_rate'], "%")

                            #현재 손실률이 트리거 손실률보다 낮다면
                            if prevRate <= PickSplitMeta['trigger_rate']:
                                

                                #투자금을 현재가로 나눠서 매수 가능한 수량을 정한다.
                                BuyAmt = int(PickSplitMeta['invest_money'] / CurrentPrice)
                                
                                #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                                if BuyAmt < 1:
                                    BuyAmt = 1


                                #매수주문 들어감!
                                pprint.pprint(KisUS.MakeBuyLimitOrder(stock_code,BuyAmt,CurrentPrice*1.01))
                                
                                MagicData['IsBuy'] = True
                                MagicData['EntryPrice'] = CurrentPrice #현재가로 진입했다고 가정합니다!
                                MagicData['EntryAmt'] = BuyAmt
  
                                #파일에 저장
                                with open(bot_file_path, 'w') as outfile:
                                    json.dump(MagicNumberDataList, outfile)
                                    
                                    
                                msg = stock_code + " 매직스플릿 "+str(MagicData['Number'])+"차 수익 매수 완료! 이전 차수 손실률" + str(PickSplitMeta['trigger_rate']) +"% 만족" 
                                print(msg) 
                                line_alert.SendMessage(msg)
                                
                                
                                
                                
                                #매매가 일어났으니 보유수량등을 리프레시 한다!
                                MyStockList = KisUS.GetMyStockList()
                                #매수된 상태라면 정보를 넣어준다!!!
                                for my_stock in MyStockList:
                                    if my_stock['StockCode'] == stock_code:
                                        stock_amt = int(my_stock['StockAmt'])
                                        stock_avg_price = float(my_stock['StockAvgPrice'])
                                        stock_eval_totalmoney = float(my_stock['StockNowMoney'])
                                        stock_revenue_rate = float(my_stock['StockRevenueRate'])
                                        stock_revenue_money = float(my_stock['StockRevenueMoney'])
                                        break
                                

else:
    #장이 끝나고 1차수 매매 가능하게 True로 변경
    for StockInfo in MagicNumberDataList:
        StockInfo['IsReady'] = True


    #파일에 저장
    with open(bot_file_path, 'w') as outfile:
        json.dump(MagicNumberDataList, outfile)
        
    

for MagicDataInfo in MagicNumberDataList:
    print(MagicDataInfo['StockName'], "누적 실현 손익:", MagicDataInfo['RealizedPNL'])
    
    
#pprint.pprint(MagicNumberDataList)