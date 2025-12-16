# -*- coding: utf-8 -*-
'''

관련 포스팅

https://blog.naver.com/zacra/223403166183
위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

'''
import sys
import os
import socket

# 서버/로컬 환경 판단 및 경로 설정
pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    # 운영 서버
    sys.path.insert(0, "/var/AutoBot/Common")
else:
    # 로컬 PC
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))

import KIS_Common as Common
import pandas as pd
import KIS_API_Helper_KR as KisKR
import time
import json
import pprint
from datetime import datetime, timedelta
import builtins

# 원본 print 함수 저장 및 타임스탬프 포함 print 함수 정의
_original_print = builtins.print

def timestamped_print(*args, **kwargs):
    """타임스탬프가 포함된 로그 출력 함수"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

# 전역 print 함수를 타임스탬프 버전으로 교체
builtins.print = timestamped_print

import telegram_alert



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("REAL") #REAL or VIRTUAL


BOT_NAME = Common.GetNowDist() + "_MySnowNBotKr"


#시간 정보를 읽는다
time_info = time.gmtime()
#년월 문자열을 만든다 즉 2022년 9월이라면 2022_9 라는 문자열이 만들어져 strYM에 들어간다!
strYM = str(time_info.tm_year) + "_" + str(time_info.tm_mon)
print("ym_st: " , strYM)



#포트폴리오 이름
PortfolioName = "Snow전략_KR"



#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


#리밸런싱이 가능한지 여부를 판단!
Is_Rebalance_Go = False


#파일에 저장된 년월 문자열 (ex> 2022_9)를 읽는다
YMDict = dict()

#파일 경로입니다.
import socket
pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    asset_tym_file_path = "/var/AutoBot/json/8.Snow_Kr_Bot_Data.json"
else:
    asset_tym_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', '8.Snow_Kr_Bot_Data.json')

try:
    with open(asset_tym_file_path, 'r') as json_file:
        YMDict = json.load(json_file)

except Exception as e:
    print("Exception by First")


#만약 키가 존재 하지 않는다 즉 아직 한번도 매매가 안된 상태라면
if YMDict.get("ym_st") == None:

    #리밸런싱 가능! (리밸런싱이라기보다 첫 매수해야 되는 상황!)
    Is_Rebalance_Go = True
    
#매매가 된 상태라면! 매매 당시 혹은 리밸런싱 당시 년월 정보(ex> 2022_9) 가 들어가 있다.
else:
    #그럼 그 정보랑 다를때만 즉 달이 바뀌었을 때만 리밸런싱을 해야 된다
    if YMDict['ym_st'] != strYM:
        #리밸런싱 가능!
        Is_Rebalance_Go = True


#강제 리밸런싱 수행!
#Is_Rebalance_Go = True



#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()

if IsMarketOpen == True:
    print("Market Is Open!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
    if Is_Rebalance_Go == True:
        telegram_alert.SendMessage(f"""🔔 ━━━━━━━━━━━━━━━━━━━━
📌 {PortfolioName}
━━━━━━━━━━━━━━━━━━━━
📅 기간: {strYM}
🏛️ 장 상태: 개장
✅ 리밸런싱 가능
━━━━━━━━━━━━━━━━━━━━""")
else:
    print("Market Is Close!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!
    if Is_Rebalance_Go == True:
        telegram_alert.SendMessage(f"""🔔 ━━━━━━━━━━━━━━━━━━━━
📌 {PortfolioName}
━━━━━━━━━━━━━━━━━━━━
📅 기간: {strYM}
🏛️ 장 상태: 폐장
❌ 리밸런싱 불가능
━━━━━━━━━━━━━━━━━━━━""")




#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


#계좌 잔고를 가지고 온다!
Balance = KisKR.GetBalance()


print("--------------내 보유 잔고---------------------")

pprint.pprint(Balance)

print("--------------------------------------------")

# Balance가 None인 경우 처리 (토큰 발급 실패 등)
if Balance is None:
    err_msg = "[8.Snow_Kr] ❌ 잔고 조회 실패! 토큰 발급 오류 가능성이 있습니다. 서버 및 API 키를 확인하세요."
    print(err_msg)
    telegram_alert.SendMessage(err_msg)
    sys.exit(1)

#총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.5


#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("총 포트폴리오에 할당된 투자 가능 금액 : $", TotalMoney)


##########################################################



#투자 주식 리스트
MyPortfolioList = list()


StockCodeList = ["TIP","102110","148070","133690","305080","132030","261220","153130","261240"]

for stock_code in StockCodeList:

    asset = dict()
    asset['stock_code'] = stock_code         #종목코드
    asset['stock_target_rate'] = 0     #비중..
    asset['stock_rebalance_amt'] = 0  #리밸런싱 수량
    MyPortfolioList.append(asset)





##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################



print("--------------리밸런싱 계산 ---------------------")




stock_df_list = []

for stock_code in StockCodeList:
    
    #################################################################
    #################################################################
    df = None
    if stock_code == "TIP":
        df = Common.GetOhlcv("US", stock_code,300) 
    else:
        df = Common.GetOhlcv("KR", stock_code,300) 

    #################################################################
    #################################################################



    df['prevClose'] = df['close'].shift(1)

    df['1month'] = df['close'].shift(20)
    df['3month'] = df['close'].shift(60)
    df['6month'] = df['close'].shift(120)
    df['9month'] = df['close'].shift(180)
    df['12month'] = df['close'].shift(240)

    #1개월 수익률 + 3개월 수익률 + 6개월 수익률 + 9개월 수익률 + 12개월 수익률
    df['Momentum'] = ( ((df['prevClose'] - df['1month'])/df['1month']) + ((df['prevClose'] - df['3month'])/df['3month']) + ((df['prevClose'] - df['6month'])/df['6month']) + ((df['prevClose'] - df['9month'])/df['6month'])  + ((df['prevClose'] - df['12month'])/df['12month']) ) / 5.0
    
    #12개월 모멘텀
    df['Momentum_12'] = (df['prevClose'] - df['12month'])/df['12month']
    
    #12개월 이동평균 모멘텀
    df['Ma_Momentum'] = (df['prevClose'] / df['close'].rolling(240).mean().shift(1)) - 1.0


    df.dropna(inplace=True) #데이터 없는건 날린다!


    data_dict = {stock_code: df}


    stock_df_list.append(data_dict)
        
    print("---stock_code---", stock_code , " len ",len(df))
    
    pprint.pprint(df)




combined_df = pd.concat([list(data_dict.values())[0].assign(stock_code=stock_code) for data_dict in stock_df_list for stock_code in data_dict])
combined_df.sort_index(inplace=True)
pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))



date = combined_df.iloc[-1].name

################################################################################################
################################################################################################
################################################################################################
#TIP이 미국시장 ETF여서 날짜의 차이가 있다는 걸 감안한 코드...
tip_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "TIP")] 


FindDate = date
while len(tip_data) == 0:


    #날짜 정보를 획득
    date_format = "%Y-%m-%d %H:%M:%S"
    date_object = None

    try:
        date_object = datetime.strptime(str(FindDate), date_format)
    
    except Exception as e:
        try:
            date_format = "%Y%m%d"
            date_object = datetime.strptime(str(FindDate), date_format)

        except Exception as e2:
            date_format = "%Y-%m-%d"
            date_object = datetime.strptime(str(FindDate), date_format)
            

            
    FindDate = date_object - timedelta(days=1)

    tip_data = combined_df[(combined_df.index == FindDate.strftime("%Y-%m-%d")) & (combined_df['stock_code'] == "TIP")] 

    print("Check...",FindDate.strftime("%Y-%m-%d"))

################################################################################################
################################################################################################
################################################################################################


#채권을 제외한 공격자산의 11개월 모멘텀 높은거 1개 픽!!!!
exclude_stock_codes = ["TIP","153130","261240"] #공격자산에 포함되면 안되는 종목들 즉 안전자산들을 넣으면 된다!
pick_momentum_top = combined_df.loc[(combined_df.index == date)  & (~combined_df['stock_code'].isin(exclude_stock_codes)) ].groupby('stock_code')['Ma_Momentum'].max().nlargest(2)

#공격자산을 제외한 채권들중 모멘텀 스코어가 높은거 상위 TOP 1개를 리턴!
exclude_stock_codes = ["TIP","133690","102110","148070","132030","261220","305080"] #안전자산에 포함되면 안되는 종목들 즉 공격자산들을 넣으면 된다!
pick_bond_momentum_top = combined_df.loc[(combined_df.index == date) & (~combined_df['stock_code'].isin(exclude_stock_codes))].groupby('stock_code')['Momentum_12'].max().nlargest(1)



if len(tip_data) == 1 :



    #안전 자산 비중 정하기!
    SafeRate = 0
    AtkRate = 0
        
    AtkOkList = list()


    #TIP 모멘텀 양수 장이 좋다!
    if tip_data['Momentum'].values[0] > 0 :
        
        #공격자산에 100% 투자한다!
        AtkRate = 1.0
        
        for stock_code in pick_momentum_top.index:
                
            stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

            if len(stock_data) == 1:

                AtkOkList.append(stock_code)

    
    #TIP 모멘텀 음수 장이 안좋아!
    else:
        #안전자산에 100% 투자한다!
        SafeRate = 1.0




    #리밸런싱 수량을 확정한다!
    for stock_info in MyPortfolioList:

        stock_code = stock_info['stock_code']

        stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 

        
        if len(stock_data) == 1:
            
            IsRebalanceGo = False

            NowClosePrice = stock_data['close'].values[0]

            #안전 자산 비중이 있는 경우!! 안전자산에 투자!!!
            if SafeRate > 0:
                
                for stock_code_b in pick_bond_momentum_top.index:
                        
                    if stock_code_b == stock_code:
                        
                        #BIL보다 높은 것만 투자!
                        if stock_data['Momentum_12'].values[0] > 0 :
                            
                            stock_info['stock_target_rate'] += (SafeRate/len(pick_bond_momentum_top.index))
                            print("방어자산! ", stock_code)
                            
                        break


            #선택된 공격자산이라면!!
            if stock_code in AtkOkList:

                stock_info['stock_target_rate'] +=  (AtkRate/len(pick_momentum_top.index))
                print("공격자산! ", stock_code)
       
    





strResult = "-- 현재 포트폴리오 상황 --\n"

#매수된 자산의 총합!
total_stock_money = 0

#현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
for stock_info in MyPortfolioList:

    #내주식 코드
    stock_code = stock_info['stock_code']


    if stock_code == "TIP":
        continue



    #매수할 자산 보유할 자산의 비중을 넣어준다!
    stock_target_rate = float(stock_info['stock_target_rate']) 


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
    print("stock_code:", stock_code)

    print("#####" , KisKR.GetStockName(stock_code) ," stock_code: ", stock_code)

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
                
            #목표한 비중이 다르다면!!
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

                        stock_info['stock_rebalance_amt'] = -GapAmt

                    #갭이 양수라면 비중이 더 적으니 사야되는 상황!
                    else:  
                        stock_info['stock_rebalance_amt'] = GapAmt



    #잔고에 없는 경우
    else:

        print("---> NowRate: 0%")
        if stock_target_rate > 0:

            #잔고가 없다면 첫 매수다! 비중대로 매수할 총 금액을 계산한다 
            BuyMoney = TotalMoney * stock_target_rate

            #매수할 수량을 계산한다!
            BuyAmt = int(BuyMoney / CurrentPrice)


            stock_info['stock_rebalance_amt'] = BuyAmt


        
        
    #라인 메시지랑 로그를 만들기 위한 문자열 
    line_data =  (">> " + KisKR.GetStockName(stock_code) + "(" + stock_code + ") << \n비중: " + str(round(stock_now_rate * 100.0,2)) + "/" + str(round(stock_target_rate * 100.0,2)) 
    + "% \n수익: " + str(format(round(stock_revenue_money), ',')) + "("+ str(round(stock_revenue_rate,2)) 
    + "%) \n총평가금액: " + str(format(round(stock_eval_totalmoney), ',')) 
    + "\n리밸런싱수량: " + str(stock_info['stock_rebalance_amt']) + "\n----------------------\n")

    #만약 아래 한번에 보내는 라인메시지가 짤린다면 아래 주석을 해제하여 개별로 보내면 됩니다
    if Is_Rebalance_Go == True:
        telegram_alert.SendMessage(line_data)
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
if Is_Rebalance_Go == True:
    telegram_alert.SendMessage(f"""📊 ━━━━━━━━━━━━━━━━━━━━
📌 포트폴리오 요약
━━━━━━━━━━━━━━━━━━━━
💰 할당금액: {format(round(TotalMoney), ',')}원
📈 매수자산총액: {format(round(total_stock_money), ',')}원
━━━━━━━━━━━━━━━━━━━━""")



print("--------------------------------------------")

##########################################################
#리밸런싱이 가능한 상태여야 하고 매수 매도는 장이 열려있어야지만 가능하다!!!
if Is_Rebalance_Go == True and IsMarketOpen == True:


    #혹시 이 봇을 장 시작하자 마자 돌린다면 20초르 쉬어준다.
    #그 이유는 20초는 지나야 오늘의 일봉 정보를 제대로 가져오는데
    #tm_hour가 0은 9시, 1은 10시를 뜻한다. 수능 등 10시에 장 시작하는 경우르 대비!
    if time_info.tm_hour in [0,1] and time_info.tm_min == 0:
        time.sleep(20.0)
        
    telegram_alert.SendMessage(f"""🚀 ━━━━━━━━━━━━━━━━━━━━
📌 {PortfolioName}
━━━━━━━━━━━━━━━━━━━━
📅 기간: {strYM}
🔄 상태: 리밸런싱 시작
━━━━━━━━━━━━━━━━━━━━""")

    print("------------------리밸런싱 시작  ---------------------")
    #이제 목표치에 맞게 포트폴리오를 조정하면 되는데
    #매도를 해야 돈이 생겨 매수를 할 수 있을 테니
    #먼저 매도를 하고
    #그 다음에 매수를 해서 포트폴리오를 조정합니다!

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
            

            #지정가 괴리율 등을 반영해 매도하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요!
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

            Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,rebalance_amt,"DAY_END_TRY_ETF")
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


            #지정가 괴리율 등을 반영해 매수하고 싶다면 아래 로직 사용! 주식 클래스 완강 필요!
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


            Common.AutoLimitDoAgain(BOT_NAME,"KR",stock_code,FinalPrice,rebalance_amt,"DAY_END_TRY_ETF")
            '''
                   

    print("--------------------------------------------")

    #########################################################################################################################
    #첫 매수던 리밸런싱이던 매매가 끝났으면 이달의 리밸런싱은 끝이다. 해당 달의 년달 즉 22년 9월이라면 '2022_9' 라는 값을 파일에 저장해 둔다! 
    #파일에 저장하는 부분은 여기가 유일!!!!
    YMDict['ym_st'] = strYM
    with open(asset_tym_file_path, 'w') as outfile:
        json.dump(YMDict, outfile)
    #########################################################################################################################
        
    telegram_alert.SendMessage(f"""✅ ━━━━━━━━━━━━━━━━━━━━
📌 {PortfolioName}
━━━━━━━━━━━━━━━━━━━━
📅 기간: {strYM}
🎉 상태: 리밸런싱 완료
━━━━━━━━━━━━━━━━━━━━""")
    print("------------------리밸런싱 끝---------------------")

