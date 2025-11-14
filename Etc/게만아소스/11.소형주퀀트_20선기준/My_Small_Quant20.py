'''
-*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-
pykrx오류 발생!!
해당 봇의 오류가 발생한다면 아래 포스팅을 참고하여 수정하세요!!!
https://blog.naver.com/zacra/223505969974
-*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*--*-

-*- 백테스팅 코드가 있는 전략들은 패키지 16번 부터 나오기 시작하니 참고하세요!! -*-

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
해당 퀀트 전략은 주식 클래스 챕터5 수강이 필수입니다!
자세한 가이드는 이 포스팅을 끝까지 완독하면 나오니 체크하세요!
https://blog.naver.com/zacra/223086628069
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

관련 포스팅

16년만에 천만원이 25억이 되는 소형주 퀀트 20 이평선 전략! (연복리 40%) - 복잡한 젠포트 안쓰고 자동매매 하기!
https://blog.naver.com/zacra/223000628375

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
import pandas as pd
import pprint
import time
import line_alert

from pykrx import stock

#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL



BOT_NAME = Common.GetNowDist() + "_MyQuant20BotV"


#포트폴리오 이름
PortfolioName = "소형주퀀트_전략_20일선"


#시간 정보를 읽는다
time_info = time.gmtime()

#혹시 이 봇을 장 시작하자 마자 돌린다면 20초르 쉬어준다.
#그 이유는 20초는 지나야 오늘의 일봉 정보를 제대로 가져오는데
#tm_hour가 0은 9시, 1은 10시를 뜻한다. 수능 등 10시에 장 시작하는 경우르 대비!
if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
    time.sleep(20.0)
    

#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################

#전제는 크롭탭 적절한 시간대에 등록하셔서 활용하세요!
# https://blog.naver.com/zacra/222496979835
# 젠포트 테스트가 종가 기준이어서 거의 장 마감인 3시 24분에 리밸런싱!!!
# 24 6 * * 1-5 python3 /var/autobot/My_ISA_Quant20.py




#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()

if IsMarketOpen == True:
    print("Market Is Open!!!!!!!!!!!")

else:
    print("Market Is Close!!!!!!!!!!!")





#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################



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
#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.2

#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : ", format(round(TotalMoney), ','))

#3백만원으로 최소 종목금액 정했을 때.. 매수가능한 종목 개수!
MininumCnt = (TotalMoney / 3000000)

print(" MininumCnt: ", MininumCnt)
#우리가 전략으로 매수할 종목 개수 20개..
TargetCnt = 20

#그런데 미니멈 개수보다 작다면... 미니멈 개수로 맞춰준다!!
if TargetCnt < MininumCnt:
    TargetCnt = MininumCnt



#상태 코드!
StatusCode = "NONE"


MaCheck = dict()
#파일 경로입니다.
ma_file_path = "/var/autobot/KrSmallStock" + BOT_NAME + "MaCheck.json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(ma_file_path, 'r') as json_file:
        MaCheck = json.load(json_file)

except Exception as e:
    StatusCode = "ST_FIRST" #파일자체가 없다면 맨 처음 상태!
    print("Exception by First")


#이전에 이평선 위에 있었는지 아래있었는지 여부~!
IsPrevMaUp = False

#키가 없다면 아직 한번도 이 전략을 통해 매수된 바가 없다!
if MaCheck.get("ma20") == None:
    StatusCode = "ST_FIRST" #키가 없다면 맨 처음 상태!
else:
    IsPrevMaUp = MaCheck['ma20']




#아래 2줄로 활용가능한 지수를 체크할 수 있다!!
#for index_v in stock.get_index_ticker_list(market='KOSDAQ'): #KOSPI 지수도 확인 가능!
#    print(index_v, stock.get_index_ticker_name(index_v))

#20일 이동평균선 위에 있는지 아래에 있는지 여부 
IsNowMaUp = True

try:

    IndexID = "2004" #코스닥 소형지수

    df = Common.GetIndexOhlcvPyKrx(IndexID)
 #   pprint.pprint(df)

    ma20 = Common.GetMA(df,20,-1)
    IndexNow = df['close'].iloc[-1]

    print(stock.get_index_ticker_name(IndexID))
    print("MA 20 : ", ma20)
    print("Now ", IndexNow)

    if ma20 < IndexNow:
        IsNowMaUp = True
    else:
        IsNowMaUp = False

except Exception as e:
    #혹시나 예외가 발생한다면!! 즉 코스닥 소형지수를 못가져온다면...
    #코스닥150 ETF로 대체한다!
    print("EXCPET!! ", str(e))

    df = Common.GetOhlcv("KR", "229200",30) #코스닥150지수!

    df['change_rate'] = df['change'].rolling(20).mean()
    StChangeRate = df['change_rate'][-1]

    ma20 = Common.GetMA(df,19,-1)
    IndexNow = df['close'][-1]

    print("MA 20 : ", ma20)
    print("Now ", IndexNow)

    if ma20 < IndexNow:
        IsNowMaUp = True
    else:
        IsNowMaUp = False

    print("Exception", e)
    
    
#리밸런싱을 진행해야 되는지 여부
NeedRebalance = False

#SR_FIRST 상태가 아니라면!
if StatusCode != "ST_FIRST":
    if IsPrevMaUp == True and IsNowMaUp == False:

        StatusCode = "ST_DOWN"
        NeedRebalance = True

        status_mst = "20일선 아래로 지수가 떨어졌습니다. 전략으로 매수한 모든 종목 매도 합니다!"
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(status_mst)
        line_alert.SendMessage(status_mst)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")


    if IsPrevMaUp == False and IsNowMaUp == True:

        StatusCode = "ST_UP"
        NeedRebalance = True

        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        status_mst = "20일선 위로 지수가 올라왔습니다. 조건에 맞는 종목으로 매수 합니다!"
        print(status_mst)
        line_alert.SendMessage(status_mst)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")



#상태1 ST_FIRST : 처음 매수해야 되는 경우... 20일 이평선 위에 있으면 정상 진행..20일 이평선 아래에 있으면 아무 진행도 하지 않는다. IsNowMaUp 값이 True면 진행 아니면 진행 무!
#상태2 ST_DOWN : 이전 IsPrevMaUp 이 True인데 IsNowMaUp이 False 라면 해당 전략으로 매수한 주식 모두 팔아야 되는 상황! -
#상태3 ST_UP : 이전 IsPrevMaUp이 False인데 IsNowMaUp이 True 라면 해당 전략으로 주식을 다시 사야 되는 상황! 
#상태4 NONE : 위 경우에 해당되지 않는 경우 

print("StatusCode: ", StatusCode)

#리밸런싱이 필요없는 평온(?)한 상황.. 현재 매수하고 있는 종목 데이터를 보여준다!
if StatusCode == "NONE":


    status_mst = "평온한 상황..아무 짓도 하지 않습니다 ㅎ"
    print(status_mst)
    #line_alert.SendMessage(status_mst)


    KRSmallStockSTList = list()
    #파일 경로입니다.
    small_stock_file_path = "/var/autobot/KrSmallStock" + BOT_NAME + "List.json"

    try:
        with open(small_stock_file_path, 'r') as json_file:
            KRSmallStockSTList = json.load(json_file)

    except Exception as e:
        print("Exception by First")


    pprint.pprint(KRSmallStockSTList)




#처음인데 이평선 아래에 있다면... 아무짓도 안해도 된다!!!!
if StatusCode == "ST_FIRST" and IsNowMaUp == False:

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    status_mst = "처음 전략을 실행해 매수해야 하지만 코스닥 소형지수 20일 선 아래여서 동작하지 않습니다!"
    print(status_mst)
    line_alert.SendMessage(status_mst)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

else:

    if StatusCode != "NONE":

        ###################################################################################
        ###################################################################################
        ###################################################################################


        #전략에 투자되거나 투자할 주식 리스트
        MyPortfolioList = list()

        #Final20List -> FinalTopList로 변수명 변경
        FinalTopList = list()



        #소형주 퀀트전략으로 투자하고 있는 주식 종목코드 리스트를 저장할 파일 
        KRSmallStockSTList = list()
        #파일 경로입니다.
        small_stock_file_path = "/var/autobot/KrSmallStock" + BOT_NAME + "List.json"

        try:
            with open(small_stock_file_path, 'r') as json_file:
                KRSmallStockSTList = json.load(json_file)

        except Exception as e:
            print("Exception by First")


        #이전에 투자했던 종목들...
        print("-----Prev--------")
        pprint.pprint(KRSmallStockSTList)
        print("-----------------")



        ##########################################################

        print("--------------내 보유 주식---------------------")
        #그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
        MyStockList = KisKR.GetMyStockList()
        pprint.pprint(MyStockList)
        print("--------------------------------------------")
        ##########################################################




        #매수하고 있는데 20일 선 아래로 떨어진 경우
        if StatusCode == "ST_DOWN":


            #현재 전략으로 매수된 모든 주식을 팔아야 한다!
            for AlReadyHasStock in KRSmallStockSTList:

                stock = dict()
                stock['stock_code'] = AlReadyHasStock['StockCode']         #종목코드
                stock['stock_target_rate'] = 0    #포트폴리오 목표 비중
                stock['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
                print("Old Stock...",stock)

                MyPortfolioList.append(stock)



        #20일선 위에 있는 경우!
        else:


            TargetStockList = list()
            #파일 경로입니다.
            korea_file_path = "/var/autobot/KrStockDataList.json"

            try:
                #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
                with open(korea_file_path, 'r') as json_file:
                    TargetStockList = json.load(json_file)

            except Exception as e:
                print("Exception by First")


            print("TotalStockCodeCnt: " , len(TargetStockList))


            df = pd.DataFrame(TargetStockList)


            df = df[df.StockMarketCap >= 50.0].copy()
        
            df = df[df.StockDistName != "금융"].copy()
            df = df[df.StockDistName != "금융업"].copy()
            df = df[df.StockDistName != "외국증권"].copy()

            df = df[df.StockOperProfit > 0].copy()
            df = df[df.StockROE >= 5.0].copy()

            df = df[df.StockEPS > 0].copy()
            df = df[df.StockBPS > 0].copy()

            df = df[df.StockPBR >= 0.2].copy()
            df = df[df.StockPER >= 2.0].copy()


            df = df.sort_values(by="StockMarketCap")
            pprint.pprint(df)


        



            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")



            
            NowCnt = 0

            for idx, row in df.iterrows():
                
                stockcode = row['StockCode']
                print(stockcode)


                if NowCnt < TargetCnt:

                    stock_amt = 0 #수량

                    #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
                    for my_stock in MyStockList:
                        if my_stock['StockCode'] == stockcode:
                            stock_amt = int(my_stock['StockAmt'])
                            break

                    if stock_amt == 0:

                        print("---------------------------------------------------")
                        FinalTopList.append(row.to_dict())
                        NowCnt += 1
                
                else:
                    break



            pprint.pprint(FinalTopList)
            ###################################################################################
            ###################################################################################
            ###################################################################################



            #종목 개수 20개.
            StockCnt = len(FinalTopList)


            #오늘 뽑은 조건에 맞는 주식들.. 비중이 20%이다!!!
            for PickStock in FinalTopList:
                
                stock = dict()
                stock['stock_code'] = PickStock['StockCode']         #종목코드
                stock['stock_target_rate'] = 100.0 / float(StockCnt)    #포트폴리오 목표 비중
                stock['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량

                MyPortfolioList.append(stock)


            #이전에 뽑아서 저장된 주식들....오늘 뽑은 것과 중복되지 않는 것을 뽑아낸다. 이는 시총 하위 순에서 밀려난 것으로 비중 0으로 모두 팔아줘야 한다!
            for AlReadyHasStock in KRSmallStockSTList:

                #오늘 뽑은 주식과 비교해서..
                Is_Duple = False
                for exist_stock in MyPortfolioList:
                    if exist_stock["stock_code"] == AlReadyHasStock['StockCode']:
                        Is_Duple = True
                        break
                        
                #중복되지 않은 것만 넣어둔다. 비중은 0%이다!!!!
                if Is_Duple == False:

                    stock = dict()
                    stock['stock_code'] = AlReadyHasStock['StockCode']         #종목코드
                    stock['stock_target_rate'] = 0    #포트폴리오 목표 비중
                    stock['stock_rebalance_amt'] = 0     #리밸런싱 해야하는 수량
                    print("Old Stock...",stock)

                    MyPortfolioList.append(stock)




        #현재 체크해야할 투자 종목들..
        pprint.pprint(MyPortfolioList)






        print("--------------리밸런싱 수량 계산 ---------------------")

        strResult = "-- 현재 포트폴리오 상황 --\n"

        #매수된 자산의 총합!
        total_stock_money = 0

        #현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
        for stock_info in MyPortfolioList:

            #내주식 코드
            stock_code = stock_info['stock_code']
            stock_target_rate = float(stock_info['stock_target_rate']) / 100.0

            #현재가!
            CurrentPrice = KisKR.GetCurrentPrice(stock_code)

            

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


            print("#####" , KisKR.GetStockName(stock_code) ," stock_code: ", stock_code)
            print("---> TargetRate:", round(stock_target_rate * 100.0,2) , "%")

            #주식의 총 평가금액을 더해준다
            total_stock_money += stock_eval_totalmoney

            #현재 비중
            stock_now_rate = 0

            #잔고에 있는 경우 즉 이미 매수된 주식의 경우
            if stock_amt > 0:


                stock_now_rate = round((stock_eval_totalmoney / TotalMoney),3)

                print("---> NowRate:", round(stock_now_rate * 100.0,2), "%")
                
                if stock_target_rate == 0:
                    stock_info['stock_rebalance_amt'] = -stock_amt
                    print("!!!!!!!!! SELL")
                    
                else:
                        
                    #목표한 비중가 다르다면!!
                    if stock_now_rate != stock_target_rate:


                        #갭을 구한다!!!
                        GapRate = stock_target_rate - stock_now_rate


                        #그래서 그 갭만큼의 금액을 구한다
                        GapMoney = TotalMoney * abs(GapRate) 
                        #현재가로 나눠서 몇주를 매매해야 되는지 계산한다
                        GapAmt = GapMoney / CurrentPrice

                        #수량이 1보다 커야 리밸러싱을 할 수 있다!! 즉 그 전에는 리밸런싱 불가 
                        if GapAmt >= 1.0:

                            GapAmt = int(GapAmt)

                            #갭이 음수라면! 비중이 더 많으니 팔아야 되는 상황!!!
                            if GapRate < 0:

                                #팔아야 되는 상황에서는 현재 주식수량에서 매도할 수량을 뺀 값이 1주는 남아 있어야 한다
                                #그래야 포트폴리오 상에서 아예 사라지는 걸 막는다!
                                if stock_amt - GapAmt >= 1:
                                    stock_info['stock_rebalance_amt'] = -GapAmt

                            #갭이 양수라면 비중이 더 적으니 사야되는 상황!
                            else:  
                                stock_info['stock_rebalance_amt'] = GapAmt

            #잔고에 없는 경우
            else:

                if stock_target_rate != 0:
                        
                    print("---> NowRate: 0%")

                    #잔고가 없다면 첫 매수다! 비중대로 매수할 총 금액을 계산한다 
                    BuyMoney = TotalMoney * stock_target_rate


                    #매수할 수량을 계산한다!
                    BuyAmt = int(BuyMoney / CurrentPrice)

                    #포트폴리오에 들어간건 일단 무조건 1주를 사주자... 아니라면 아래 2줄 주석처리
                # if BuyAmt <= 0:
                    #    BuyAmt = 1

                    stock_info['stock_rebalance_amt'] = BuyAmt
                
                
                
                
                
                
            #라인 메시지랑 로그를 만들기 위한 문자열 
            line_data =  (">> " + KisKR.GetStockName(stock_code) + "(" + stock_code + ") << \n비중: " + str(round(stock_now_rate * 100.0,2)) + "/" + str(round(stock_target_rate * 100.0,2)) 
            + "% \n수익: " + str(format(round(stock_revenue_money), ',')) + "("+ str(round(stock_revenue_rate,2)) 
            + "%) \n총평가금액: " + str(format(round(stock_eval_totalmoney), ',')) 
            + "\n리밸런싱수량: " + str(stock_info['stock_rebalance_amt']) + "\n----------------------\n")

            #만약 아래 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
            if NeedRebalance == True:
                line_alert.SendMessage(line_data)
            strResult += line_data



        ##########################################################

        print("--------------리밸런싱 해야 되는 수량-------------")

        data_str = "\n" + PortfolioName + "\n" +  strResult + "\n포트폴리오할당금액: " + str(format(round(TotalMoney), ',')) + "\n매수한자산총액: " + str(format(round(total_stock_money), ',') )

        #결과를 출력해 줍니다!
        print(data_str)

        #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
        #if Is_Rebalance_Go == True:
        #    line_alert.SendMessage(data_str)
            
        #만약 위의 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
        if NeedRebalance == True:
            line_alert.SendMessage("\n포트폴리오할당금액: " + str(format(round(TotalMoney), ',')) + "\n매수한자산총액: " + str(format(round(total_stock_money), ',') ))









        print("--------------------------------------------")

        ##########################################################


        #리밸런싱을 진행해야 되거나 맨 처음일 경우인데.. 장이 열렸을 때!!!
        if (NeedRebalance == True or StatusCode == "ST_FIRST") and IsMarketOpen == True:

            line_alert.SendMessage(PortfolioName + "  리밸런싱 시작!!")

            print("------------------리밸런싱 시작  ---------------------")


            print("--------------매도 (리밸런싱 수량이 마이너스인거)---------------------")

            for stock_info in MyPortfolioList:

                #내주식 코드
                stock_code = stock_info['stock_code']
                rebalance_amt = stock_info['stock_rebalance_amt']

                #리밸런싱 수량이 마이너스인 것을 찾아 매도 한다!
                if rebalance_amt < 0:
                            
                    #이렇게 시장가로 매도 해도 큰 무리는 없어 보인다!       
                    pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,abs(rebalance_amt)))


                    #나중에 투자금이 커지면 시장가 매도시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
                    '''
                    CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                    CurrentPrice *= 0.99 #현재가의 1%아래의 가격으로 지정가 매도.. (그럼 1%아래 가격보다 큰 가격의 호가들은 모두 체결되기에 제한있는 시장가 매도 효과)
                    pprint.pprint(KisKR.MakeSellLimitOrder(stock_code,abs(rebalance_amt),CurrentPrice))
                    '''
                    
            print("--------------------------------------------")


            #3초 정도 쉬어준다
            time.sleep(3.0)



            print("--------------매수 ---------------------")

            for stock_info in MyPortfolioList:

                #내주식 코드
                stock_code = stock_info['stock_code']
                rebalance_amt = stock_info['stock_rebalance_amt']

                #리밸런싱 수량이 플러스인 것을 찾아 매수 한다!
                if rebalance_amt > 0:
                            

                    #이렇게 시장가로 매수 해도 큰 무리는 없어 보인다!  
                    pprint.pprint(KisKR.MakeBuyMarketOrder(stock_code,rebalance_amt))

                    #나중에 투자금이 커지면 시장가 매수시 큰 슬리피지가 있을수 있으므로 아래의 코드로 지정가 주문을 날려도 된다 
                    '''
                    CurrentPrice = KisKR.GetCurrentPrice(stock_code)
                    CurrentPrice *= 1.01 #현재가의 1%위의 가격으로 지정가 매수.. (그럼 1% 위 가격보다 작은 가격의 호가들은 모두 체결되기에 제한있는 시장가 매수 효과)
                    pprint.pprint(KisKR.MakeBuyLimitOrder(stock_code,abs(rebalance_amt),CurrentPrice))
                    '''


            print("--------------------------------------------")


            line_alert.SendMessage(PortfolioName + "  리밸런싱 완료!!")

            

            #########################################################################################################################
            if IsNowMaUp == True:
                #이전에 확정된 종목 이번에 선정된 것으로 바꿔치기!
                KRSmallStockSTList = FinalTopList

            else:
                if StatusCode == "ST_DOWN":
                    KRSmallStockSTList = list()

            print("-----Now--------")
            pprint.pprint(KRSmallStockSTList)

            #파일에 저장!!
            with open(small_stock_file_path, 'w') as outfile:
                json.dump(KRSmallStockSTList, outfile)

            print("-----------------")
            #########################################################################################################################


            #현재 20일 이평선 위에 있는지 아래에 있는지 여부를 파일에 저장해 줍니다!!!
            MaCheck['ma20'] = IsNowMaUp

            #파일에 저장!!
            with open(ma_file_path, 'w') as outfile:
                json.dump(MaCheck, outfile)

            print("------------------리밸런싱 끝---------------------")

