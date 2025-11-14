'''

관련 포스팅

금단의 열매! 롱? 숏? 양방향 레버리지 투자로 안정적인 0.5%씩 수익 먹기 가능할까?? (주식 양방향 매매)
https://blog.naver.com/zacra/222988877129

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import json
import pprint
import line_alert
import time

Common.SetChangeMode("VIRTUAL")

#시간 정보를 읽는다
time_info = time.gmtime()

if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
    time.sleep(20.0)
    

BOT_NAME = Common.GetNowDist() + "_InfinityBothSideBot"

#투자할 롱과 숏
LongStockCode = '122630' # KODEX 레버리지(롱)
ShortStockCode = '252670' # KODEX 200선물인버스2X (숏)

#투자할 종목! KODEX 레버리지(롱), 
TargetStockList = [LongStockCode,ShortStockCode]

#모멘텀 계산할 기준되는 종목
StStockCode = "069500" #KODEX 200


#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
############# 해당 전략으로 매수할 종목 데이터 리스트 ####################
InfinityMaDataList = list()
#파일 경로입니다.
bot_file_path = "/var/autobot/KrStock_" + BOT_NAME + ".json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(bot_file_path, 'r') as json_file:
        InfinityMaDataList = json.load(json_file)

except Exception as e:
    print("Exception by First")
################################################################
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#
#$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$#





#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()

#장이 열렸을 때!
if IsMarketOpen == True:



    #시간 정보를 읽는다
    time_info = time.gmtime()
    strday = time_info.tm_mday
    print("strday: " , strday)



    #날짜 정보 
    MomentumInfoDict = dict()

    #파일 경로입니다.
    status_file_path = "/var/autobot/KrStock_" + BOT_NAME + "_MomentumDataInfo.json"
    try:
        with open(status_file_path, 'r') as json_file:
            MomentumInfoDict = json.load(json_file)

    except Exception as e:
        #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
        print("Exception by First")




    #기본적으로는 False
    Calc_Momentum = False

    #만약 키가 존재 하지 않는다 즉 아직 한번도 기준이 되는 종목의 모멘텀이 계산되지 않았다
    if MomentumInfoDict.get("day_st") == None:

        #모멘텀 계산해야함!
        Calc_Momentum = True
        
    #오늘 모멘텀이 계산되었다면 오늘 일 정보가 들어가 있다.
    else:
        #그럼 그 정보랑 다를때만 즉 날이 바뀌었을 때만 모멘텀 계산을 하면 된다.
        if MomentumInfoDict['day_st'] != strday:
            #모멘텀 계산해야함!
            Calc_Momentum = True


    Avg_Period = 10.0 #기본적으로 10개월 or 10일 모메텀

    if Calc_Momentum == True:

        df = Common.GetOhlcv("KR",StStockCode)




        Now_Price = Common.GetCloseData(df,-1) #현재가

        MomentumInfoDict['Now_Price'] = float(Now_Price)

        #5일 이평선
        MomentumInfoDict['Ma5_before3'] = Common.GetMA(df,5,-4)
        MomentumInfoDict['Ma5_before'] = Common.GetMA(df,5,-3)
        MomentumInfoDict['Ma5'] = Common.GetMA(df,5,-2)

        print("MA5",MomentumInfoDict['Ma5_before3'], "->", MomentumInfoDict['Ma5_before'], "-> ",MomentumInfoDict['Ma5'])

        #20일 이평선
        MomentumInfoDict['Ma20_before'] = Common.GetMA(df,20,-3)
        MomentumInfoDict['Ma20'] = Common.GetMA(df,20,-2)

        print("MA20", MomentumInfoDict['Ma20_before'], "-> ",MomentumInfoDict['Ma20'])

        #양봉 캔들인지 여부
        MomentumInfoDict['IsUpCandle'] = 0

        #시가보다 종가가 크다면 양봉이다
        if df['open'].iloc[-2] <= df['close'].iloc[-2]:
            MomentumInfoDict['IsUpCandle'] = 1

        print("IsUpCandle : ", MomentumInfoDict['IsUpCandle'])




        Up_Count = 0
        Start_Num = -20
        for i in range(1,int(Avg_Period)+1):
            
            CheckPrice = Common.GetCloseData(df,Start_Num)
            print(CheckPrice, "  <<-  df[-", Start_Num,"]")

            if Now_Price >= CheckPrice:
                print("UP!")
                Up_Count += 1.0


            Start_Num -= 20

        avg_month_momentum_score = Up_Count/Avg_Period

        print("10개월 평균 모멘텀 ", avg_month_momentum_score)




        Up_Count = 0
        Start_Num = -10
        for i in range(1,int(Avg_Period)+1):
            
            CheckPrice = Common.GetCloseData(df,Start_Num)
            print(CheckPrice, "  <<-  df[-", Start_Num,"]")

            if Now_Price >= CheckPrice:
                print("UP!")
                Up_Count += 1.0


            Start_Num -= 10

        avg_10day_momentum_score = Up_Count/Avg_Period

        print("100일 평균 모멘텀 ", avg_10day_momentum_score)





        Up_Count = 0
        Start_Num = -2
        for i in range(1,int(Avg_Period)+1):
            
            CheckPrice = Common.GetCloseData(df,Start_Num)
            print(CheckPrice, "  <<-  df[-", Start_Num,"]")

            if Now_Price >= CheckPrice:
                print("UP!")
                Up_Count += 1.0


            Start_Num -= 1

        avg_day_momentum_score = Up_Count/Avg_Period

        print("10일 평균 모멘텀 ", avg_day_momentum_score)


        long_momentum_score = (avg_month_momentum_score * 0.3) + (avg_10day_momentum_score * 0.2) + (avg_day_momentum_score * 0.3)
        short_momentum_score = 0.8 - long_momentum_score

        #절대 비중을 더해준다.
        long_momentum_score += 0.1
        short_momentum_score += 0.1

        #결국 롱 스코어와 숏 스코어를 더하면 1.0이 나온다.

        print("롱 모멘텀 스코어:", long_momentum_score , "숏 모멘텀 스코어:", short_momentum_score)

        MomentumInfoDict['long_momentum_score'] = long_momentum_score
        MomentumInfoDict['short_momentum_score'] = short_momentum_score


        MomentumInfoDict['day_st'] = strday

        #파일에 저장
        with open(status_file_path, 'w') as outfile:
            json.dump(MomentumInfoDict, outfile)


    pprint.pprint(MomentumInfoDict)










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
    #총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
    InvestRate = 0.5


    #기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
    TotalMoney = float(Balance['TotalMoney']) * InvestRate
    print("TotalMoney:", str(format(round(TotalMoney), ',')))

    #롱과 숏에 할당된 투자 금액!
    Long_StockMoney = TotalMoney * MomentumInfoDict['long_momentum_score']
    Short_StockMoney = TotalMoney * MomentumInfoDict['short_momentum_score']
    print("Long_StockMoney:", str(format(round(Long_StockMoney), ',')))
    print("Short_StockMoney:", str(format(round(Short_StockMoney), ',')))

    #50분할하여 1회차 투자 금액 확정!
    Long_StMoney = Long_StockMoney / 50.0
    Short_StMoney = Short_StockMoney / 50.0
    print("Long_StMoney:", str(format(round(Long_StMoney), ',')))
    print("Short_StMoney:", str(format(round(Short_StMoney), ',')))



    #타겟 수익 금액! 내 총 금액의 0.5%
    TargetRevenuMoney = (TotalMoney / 200.0)



    print("--------------내 보유 주식---------------------")
    #그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
    MyStockList = KisKR.GetMyStockList()
    pprint.pprint(MyStockList)
    print("--------------------------------------------")
        







    ################################### 매도 판단 파트 ###################################

    TotalRevenue = 0

    #투자할 종목을 순회한다!
    for stock_code in TargetStockList:

        #주식(ETF) 정보~
        stock_name = ""
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

        #매매시 수수료를 보정하기 위해 손실은 늘리고 수익은 줄여준다. (손익확정금의 20%를 수수료및 세금으로 대충 쳐주자!)
        if stock_revenue_money < 0:
            stock_revenue_money *= 1.2
        else:
            stock_revenue_money *= 0.8

                
        TotalRevenue += stock_revenue_money #현재 종목 수익금을 더해준다!!!

        #잔고가 0 이상이라면 데이터를 체크한다!
        if stock_amt > 0:

            #이제 데이터(InfinityMaDataList)는 확실히 있을 테니 본격적으로 트레이딩을 합니다!
            for StockInfo in InfinityMaDataList:

                if StockInfo['StockCode'] == stock_code:
                    TotalRevenue -= float(StockInfo['S_WaterLossMoney'])  #현재 누적된 손실금을 빼준다!
                    break
    

    print("목표 수익 : ", TargetRevenuMoney)
    print("현재 손익 : ", TotalRevenue)

            
            
    IsSellAll = False
    #종목 수익금의 합에 누적손실금을 제한 순 수익값이 목표한 수익금보다 크면!!! 이득을 봤다 모두 팔고 종료!!!
    if TargetRevenuMoney < TotalRevenue:
        IsSellAll = True

        print("목표 수익 달성!! 모두 정리!!")

            


    ################################### 매수 파트 ###################################


    #투자할 종목을 순회한다!
    for stock_code in TargetStockList:


        #주식(ETF) 정보~
        stock_name = ""
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
                

                

        #매매시 수수료를 보정하기 위해 손실은 늘리고 수익은 줄여준다. (손익확정금의 20%를 수수료및 세금으로 대충 쳐주자!)
        if stock_revenue_money < 0:
            stock_revenue_money *= 1.2
        else:
            stock_revenue_money *= 0.8


        #현재가
        CurrentPrice = KisKR.GetCurrentPrice(stock_code)



            
        #종목 데이터
        PickStockInfo = None

        #저장된 종목 데이터를 찾는다
        for StockInfo in InfinityMaDataList:
            if StockInfo['StockCode'] == stock_code:
                PickStockInfo = StockInfo
                break

        #PickStockInfo 이게 없다면 매수되지 않은 처음 상태이거나 이전에 손으로 매수한 종목인데 해당 봇으로 돌리고자 할 때!
        if PickStockInfo == None:
            #잔고가 없다 즉 처음이다!!!
            if stock_amt == 0:

                InfinityDataDict = dict()
                
                InfinityDataDict['StockCode'] = stock_code #종목 코드
                InfinityDataDict['Round'] = 0    #현재 회차
                InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그

                InfinityDataDict['S_WaterAmt'] = 0 #물탄 수량!
                InfinityDataDict['S_WaterLossMoney'] = 0 #물탄 수량을 팔때 손해본 금액

                InfinityMaDataList.append(InfinityDataDict) #데이터를 추가 한다!


                msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  이평무한매수봇 양방향 시작!!!!"
                print(msg) 
                line_alert.SendMessage(msg) 
                
         
            #데이터가 없는데 잔고가 있다? 이미 이 봇으로 트레이딩 하기전에 매수된 종목!
            else:
                print("Exist")

                InfinityDataDict = dict()
                
                InfinityDataDict['StockCode'] = stock_code #종목 코드

                if stock_code == LongStockCode:
                    InfinityDataDict['Round'] = int(stock_eval_totalmoney / Long_StMoney)    #현재 회차 - 매수된 금액을 50분할된 단위 금액으로 나누면 회차가 나온다!
                else:
                    InfinityDataDict['Round'] = int(stock_eval_totalmoney / Short_StMoney)    #현재 회차 - 매수된 금액을 50분할된 단위 금액으로 나누면 회차가 나온다!

                InfinityDataDict['IsReady'] = 'Y' #하루에 한번 체크하고 매수등의 처리를 하기 위한 플래그

                InfinityDataDict['S_WaterAmt'] = 0 #물탄 수량!
                InfinityDataDict['S_WaterLossMoney'] = 0 #물탄 수량을 팔때 손해본 금액


                InfinityMaDataList.append(InfinityDataDict) #데이터를 추가 한다!


                msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  기존에 매수한 종목을 이평무한매수봇으로 변경해서 트레이딩 첫 시작!!!! " + str(InfinityDataDict['Round']) + "회차로 세팅 완료!"
                print(msg) 
                line_alert.SendMessage(msg) 
           

            #파일에 저장
            with open(bot_file_path, 'w') as outfile:
                json.dump(InfinityMaDataList, outfile)
                




        #이제 데이터(InfinityMaDataList)는 확실히 있을 테니 본격적으로 트레이딩을 합니다!
        for StockInfo in InfinityMaDataList:

            if StockInfo['StockCode'] == stock_code:

                if IsSellAll == True:

                    if stock_amt > 0 and StockInfo['Round'] > 0:

                        #모두 정리합니다.
                        pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,stock_amt))


                        msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  이평무한매수봇 모두 팔아서 손익확정!!!!  [" + str(stock_revenue_money) + "] 손익 조으다! (현재 [" + str(StockInfo['Round']) + "] 라운드까지 진행되었고 모든 수량 매도 처리! )"
                        print(msg) 
                        line_alert.SendMessage(msg) 

                        #전량 매도 모두 초기화! 
                        StockInfo['Round'] = 0
                        StockInfo['IsReady'] = 'N' #익절한 날은 매수 안하고 즐기자!
                        StockInfo['S_WaterAmt'] = 0 #물탄 수량 초기화 
                        StockInfo['S_WaterLossMoney'] = 0 #물탄 수량을 팔때 손해본 금액 초기화!

                else:


                    #매수는 장이 열렸을 때 1번만 해야 되니깐! 안의 로직을 다 수행하면 N으로 바꿔준다! 
                    if StockInfo['IsReady'] == 'Y':

                        #롱일 경우!
                        if stock_code == LongStockCode:
                            StockInfo['Round'] = int(stock_eval_totalmoney / Long_StMoney)  
                        else:
                            StockInfo['Round'] = int(stock_eval_totalmoney / Short_StMoney)  



                        Is_Cut_Ok = False

                        if stock_code == LongStockCode:
                             #5일선 밑에 있는 하락세다!!!
                            if MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price'] and StockInfo['Round'] >= 1.0:
                                Is_Cut_Ok = True
                                if MomentumInfoDict['long_momentum_score'] > MomentumInfoDict['short_momentum_score']:
                                    if StockInfo['Round'] < 5.0:
                                        Is_Cut_Ok = False
                        else:
                            #5일선 위에 있는 상승세다!!!
                            if MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price'] and StockInfo['Round'] >= 1.0:
                                Is_Cut_Ok = True
                                if MomentumInfoDict['long_momentum_score'] < MomentumInfoDict['short_momentum_score']:
                                    if StockInfo['Round'] < 5.0:
                                        Is_Cut_Ok = False
                            


                        if Is_Cut_Ok == True:
                                

                            StMoney = Long_StMoney

                            if stock_code == ShortStockCode:
                                StMoney = Short_StMoney


                            SellAmt = float(StMoney) / float(CurrentPrice)
                            
     
                            if SellAmt < 1.0:
                                SellAmt = 1.0

                            StockInfo['Round'] -= 1.0

                            if stock_amt > 0:
    
                                pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,SellAmt))

                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if stock_revenue_money < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 3개를 파는 거라면 실제 확정 손실금은 -100 * (3/10)이 니깐~
                                    LossMoney = abs(stock_revenue_money) * (float(SellAmt) / float(stock_amt))
                                    StockInfo['S_WaterLossMoney'] += LossMoney

                                    msg = stock_code + " 5일선 기준 1회차 매도합니다! 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(StockInfo['S_WaterLossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다!
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(stock_revenue_money) * (float(SellAmt) / float(stock_amt))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if StockInfo['S_WaterLossMoney'] > 0:
                                        StockInfo['S_WaterLossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다

                                        #수익금을 뺐더니 손실금이 음수라면 0으로 처리해 준다!
                                        #if StockInfo['S_WaterLossMoney'] < 0:
                                        #    StockInfo['S_WaterLossMoney'] = 0


                                    msg = stock_code + " 5일선 기준 1회차 매도합니다! ! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 



                                
                        #40회를 넘었다면! 풀매수 상태이다!
                        if StockInfo['Round'] >= 40:

                            Need_Cut = False
                            if stock_code == LongStockCode:
                                #그런데 애시당초 후반부는 5일선이 증가추세일때만 매매 하므로 5일선이 하락으로 바뀌었다면 이때 손절처리를 한다
                                if MomentumInfoDict['Ma5_before'] > MomentumInfoDict['Ma5']:
                                    Need_Cut = True
                            else:
                                #숏은 애시당초 후반부는 5일선이 감소 추세일때만 매매 하므로 5일선이 상승 바뀌었다면 이때 손절처리를 한다
                                if MomentumInfoDict['Ma5_before'] < MomentumInfoDict['Ma5']:
                                    Need_Cut = True

                            
                            if Need_Cut == True:
                                #절반을 손절처리 한다
    
                                #절반은 바로 팔고 절반은 트레일링 스탑으로 처리한다!!!
                                HalfAmt = int(stock_amt * 0.5)

                                #절반만 팝니다!!!!!
                                pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,HalfAmt))

                                StockInfo['Round'] = 21 #라운드는 절반을 팔았으니깐 21회로 초기화

                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if stock_revenue_money < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 5개를 파는 거라면 실제 확정 손실금은 -100 * (5/10)이 니깐~
                                    LossMoney = abs(stock_revenue_money) * (float(HalfAmt) / float(stock_amt))
                                    StockInfo['S_WaterLossMoney'] += LossMoney

                                    msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  40회가 소진되어 절반 손절합니다! 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(StockInfo['S_WaterLossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다! 목표 %에 못 도달했지만 수익권이긴 한 상태.
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(stock_revenue_money) * (float(HalfAmt) / float(stock_amt))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if StockInfo['S_WaterLossMoney'] > 0:
                                        StockInfo['S_WaterLossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다

                                        #수익금을 뺐더니 손실금이 음수라면 0으로 처리해 준다!
                                        #if StockInfo['S_WaterLossMoney'] < 0:
                                        #    StockInfo['S_WaterLossMoney'] = 0


                                    msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  40회가 소진되어 절반 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 


                        '''
                        
                        1~10회:

                        무조건 삽니다

                        11~20회 :

                        5일선 위에 있을 때만!

                        21~30회 :

                        5일선 위에 있고 이전봉이 양봉일때만

                        30~40회 :

                        5일선 위에 있고 이전봉이 양봉이고 
                        5일선 증가, 20일선이 증가했다!

                        '''

                        IsBuyGo = False #매수 하는지!

                        #롱일 경우!
                        if stock_code == LongStockCode:

                            #라운드에 따라 매수 조건이 다르다!
                            if StockInfo['Round'] <= 5-1:

                                #롱 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] > MomentumInfoDict['short_momentum_score']:

                                    #여기는 무조건 매수
                                    IsBuyGo = True
                                
                                else:
                                    #현재가가 5일선 위에 있을 때만 매수
                                    if MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price']:
                                        IsBuyGo = True

                            elif StockInfo['Round'] <= 20-1:


                                #롱 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] > MomentumInfoDict['short_momentum_score']:
                                    #현재가가 5일선 위에 있을 때만 매수
                                    if MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price']:
                                        IsBuyGo = True
                                else:
                                    #현재가가 5일선 / 20일선 위에 있고 이전 봉이 양봉일 때만 매수
                                    if MomentumInfoDict['Ma20'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 1:
                                        IsBuyGo = True                   



                            elif StockInfo['Round'] <= 30-1:


                                #롱 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] > MomentumInfoDict['short_momentum_score']:

                                    #현재가가 5일선 위에 있고 이전 봉이 양봉일 때만 매수
                                    if MomentumInfoDict['Ma20'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 1:
                                        IsBuyGo = True
                                else:

                                    #현재가가 5/20일선 위에 있고 이전 봉이 양봉일때 그리고 5일선, 20일선 둘다 증가추세에 있을 때만 매수
                                    if MomentumInfoDict['Ma20'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 1 and MomentumInfoDict['Ma5_before'] < MomentumInfoDict['Ma5'] and MomentumInfoDict['Ma20_before'] < MomentumInfoDict['Ma20']:
                                        IsBuyGo = True


                            elif StockInfo['Round'] <= 40-1:

                                #현재가가 5/20일선 위에 있고 이전 봉이 양봉일때 그리고 5일선, 20일선 둘다 증가추세에 있을 때만 매수
                                if MomentumInfoDict['Ma20'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] < MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 1 and MomentumInfoDict['Ma5_before'] < MomentumInfoDict['Ma5'] and MomentumInfoDict['Ma20_before'] < MomentumInfoDict['Ma20']:
                                    IsBuyGo = True
                        #숏일 경우
                        else:

                            #라운드에 따라 매수 조건이 다르다!
                            if StockInfo['Round'] <= 5-1:
                                #숏 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] < MomentumInfoDict['short_momentum_score']:

                                    #여기는 무조건 매수
                                    IsBuyGo = True

                                else:
                                    #현재가가 5일선 아래에 있을 때만 매수
                                    if MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price']:
                                        IsBuyGo = True


                            elif StockInfo['Round'] <= 20-1:
                                #숏 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] < MomentumInfoDict['short_momentum_score']:

                                    #현재가가 5일선 아래에 있을 때만 매수
                                    if MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price']:
                                        IsBuyGo = True

                                else:

                                    #현재가가 5/20일선 아래에 있고 이전 봉이 음봉 때만 매수
                                    if MomentumInfoDict['Ma20'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 0:
                                        IsBuyGo = True

                            elif StockInfo['Round'] <= 30-1:
                                #숏 모멘텀이 우세하다면! 기존대로!
                                if MomentumInfoDict['long_momentum_score'] < MomentumInfoDict['short_momentum_score']:

                                    #현재가가 5/20일선 아래에 있고 이전 봉이 음봉 때만 매수
                                    if MomentumInfoDict['Ma20'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 0:
                                        IsBuyGo = True

                                else:

                                    #현재가가 5/20일선 아래에 있고 이전 봉이 음봉 때 그리고 5일선, 20일선 둘다 감소 추세에 있을 때만 매수
                                    if MomentumInfoDict['Ma20'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 0 and MomentumInfoDict['Ma5_before'] > MomentumInfoDict['Ma5'] and MomentumInfoDict['Ma20_before'] > MomentumInfoDict['Ma20']:
                                        IsBuyGo = True

                            elif StockInfo['Round'] <= 40-1:

                                #현재가가 5/20일선 아래에 있고 이전 봉이 음봉 때 그리고 5일선, 20일선 둘다 감소 추세에 있을 때만 매수
                                if MomentumInfoDict['Ma20'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['Ma5'] > MomentumInfoDict['Now_Price'] and MomentumInfoDict['IsUpCandle'] == 0 and MomentumInfoDict['Ma5_before'] > MomentumInfoDict['Ma5'] and MomentumInfoDict['Ma20_before'] > MomentumInfoDict['Ma20']:
                                    IsBuyGo = True



                        #한 회차 매수 한다!!
                        if IsBuyGo == True:

                            StMoney = Long_StMoney

                            if stock_code == ShortStockCode:
                                StMoney = Short_StMoney


                            BuyAmt = float(StMoney) / float(CurrentPrice)
                            
                            #1주보다 적다면 투자금이나 투자비중이 작은 상황인데 일단 1주는 매수하게끔 처리 하자!
                            if BuyAmt < 1.0:
                                BuyAmt = 1

                                StockInfo['Round'] += (float(CurrentPrice)/float(StMoney))
                            else:
                                StockInfo['Round'] += 1 #라운드 증가!

                            #시장가 주문을 넣는다!
                            #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수!
                            pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,int(BuyAmt)))


                            msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  이평무한매수봇 " + str(StockInfo['Round']) + "회차 매수 완료!"
                            print(msg) 
                            line_alert.SendMessage(msg) 





                        ####################################################################################
                        ################## 위 정규 매수 로직과는 별개로 특별 물타기 로직을 체크하고 제어한다! #############

                        #이평선이 꺾여서 특별히 물탄 경우 수량이 0이 아닐꺼고 즉 여기는  물을 탄 상태이다!
                        if StockInfo['S_WaterAmt'] != 0:
                            
                            if stock_amt >= 1:

                                if stock_amt < StockInfo['S_WaterAmt']:
                                    StockInfo['S_WaterAmt'] = stock_amt
                                    
                                #현재가보다 아래에 매도 주문을 넣음으로써 시장가로 매도효과!
                                pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,StockInfo['S_WaterAmt']))

                                #단 현재 수익금이 마이너스 즉 손실 상태라면 손실 금액을 저장해 둔다!
                                if stock_revenue_money < 0:
                                    #손실 금액에서 매도수량/보유수량 즉 예로 10개보유 하고 현재 -100달러인데 3개를 파는 거라면 실제 확정 손실금은 -100 * (3/10)이 니깐~
                                    LossMoney = abs(stock_revenue_money) * (float(StockInfo['S_WaterAmt']) / float(stock_amt))
                                    StockInfo['S_WaterLossMoney'] += LossMoney

                                    msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  평단을 확 낮추기 위한 이평무한매수봇 물탄지 하루가 지나 그 수량만큼 매도합니다! 약 [" + str(LossMoney) + "] 확정손실이 나서 기록했으며 누적 손실은 [" + str(StockInfo['S_WaterLossMoney']) + "] 입니다"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                #이 경우는 이득 본 경우다!
                                else:

                                    #이득본 금액도 계산해보자
                                    RevenuMoney = abs(stock_revenue_money) * (float(StockInfo['S_WaterAmt']) / float(stock_amt))

                                    #혹시나 저장된 손실본 금액이 있다면 줄여 준다! (빠른 탈출을 위해)
                                    if StockInfo['S_WaterLossMoney'] > 0:
                                        StockInfo['S_WaterLossMoney'] -= RevenuMoney #저 데이터는 손실금을 저장하는 곳이니 빼준다

                                        #수익금을 뺐더니 손실금이 음수라면 0으로 처리해 준다!
                                        #if StockInfo['S_WaterLossMoney'] < 0:
                                        #    StockInfo['S_WaterLossMoney'] = 0


                                    msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  평단을 확 낮추기 위한 이평무한매수봇 물탄지 하루가 지나 그 수량만큼 매도합니다! 약 [" + str(RevenuMoney) + "] 확정 수익이 났네요!"
                                    print(msg) 
                                    line_alert.SendMessage(msg) 

                                StockInfo['S_WaterAmt'] = 0 #팔았으니 0으로 초기화!

                            
                        #평단 낮추기위한 물타기 미진행!
                        else:

                            Water_Go = False
                            #롱일 경우!
                            if stock_code == LongStockCode:
                                # 20선밑에 5일선이 있는데 5일선이 위로 꺾여을 때
                                if MomentumInfoDict['Ma5'] < MomentumInfoDict['Ma20'] and MomentumInfoDict['Ma5_before3'] > MomentumInfoDict['Ma5_before'] and MomentumInfoDict['Ma5_before'] < MomentumInfoDict['Ma5']:
                                    Water_Go = True
                            #숏일 경우!
                            else:
                                # 20선위에 5일선이 있는데 5일선이 아래로 꺾여을 때
                                if MomentumInfoDict['Ma5'] > MomentumInfoDict['Ma20'] and MomentumInfoDict['Ma5_before3'] < MomentumInfoDict['Ma5_before'] and MomentumInfoDict['Ma5_before'] > MomentumInfoDict['Ma5']:
                                    Water_Go = True

                           
                            if Water_Go == True and StockInfo['Round'] > 1:

                                '''

                                매수할 회차 = 현재 회차 / 4 + 1

                                '''
                                #즉 10분할 남은 수량을 회차비중별로 차등 물을 탄다
                                #만약 현재 4회차 진입에 이 상황을 만났다면 2분할을 물을 타주고
                                #만약 현재 38회차 진입에 이 상황을 만났다면 10분할로 물을 타줘서
                                #평단을 확확 내려 줍니다!

                                BuyRound = int(StockInfo['Round']/4) + 1 #물탈 회수

                                BuyAmt = int(((TotalMoney/50.0) * BuyRound) / CurrentPrice) #물탈 수량을 구한다!
                                
                                if BuyAmt < 1:
                                    BuyAmt = 1


                                StockInfo['S_WaterAmt'] = BuyAmt

                                #시장가 주문을 넣는다!
                                #현재가보다 위에 매수 주문을 넣음으로써 시장가로 매수!
                                pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,int(BuyAmt)))

                                msg = KisKR.GetStockName(stock_code) + "("+ stock_code  + ")  이평선이 위로 꺾였어요! 평단을 확 낮추기 위한 이평무한매수봇 물을 탑니다!! [" + str(BuyRound) + "] 회차 만큼의 수량을 추가 했어요!"
                                print(msg) 
                                line_alert.SendMessage(msg) 

                        #########################################################################################
                        #########################################################################################


                        #위 로직 완료하면 N으로 바꿔서 오늘 매수는 안되게 처리!
                        StockInfo['IsReady'] = 'N' 

                        #파일에 저장
                        with open(bot_file_path, 'w') as outfile:
                            json.dump(InfinityMaDataList, outfile)
                            
                                


                break


else:

        
    #장이 끝나고 다음날 다시 매수시도 할수 있게 Y로 바꿔줍니당!
    for StockInfo in InfinityMaDataList:
        StockInfo['IsReady'] = 'Y' #

    #파일에 저장
    with open(bot_file_path, 'w') as outfile:
        json.dump(InfinityMaDataList, outfile)
        
        

        
pprint.pprint(InfinityMaDataList)