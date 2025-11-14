#-*-coding:utf-8 -*-
'''


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
코드 참고 영상!
https://youtu.be/YdEdM-oC0kc
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다. 

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504

관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅

코스닥 코스피 양방향으로 투자하는 전략! 초전도체 LK99에 버금가는 발견!!
https://blog.naver.com/zacra/223177598281

Safe_ 안전 전략 포스팅!!
https://blog.naver.com/zacra/223179856793


위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''

import KIS_Common as Common
import KIS_API_Helper_KR as KisKR
import time
import pprint
import pandas as pd
import json
from datetime import datetime


import line_alert



#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL


BOT_NAME = Common.GetNowDist() + "_MyKospidaq_Bot"


#포트폴리오 이름
PortfolioName = "게만아 코스피닥 매매 전략!"


#시간 정보를 읽는다
time_info = time.gmtime()

day_n = time_info.tm_mday

day_str = str(time_info.tm_mon) + "-" + str(time_info.tm_mday)

print(day_str)



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


##########################################################

print("--------------내 보유 주식---------------------")
#그리고 현재 이 계좌에서 보유한 주식 리스트를 가지고 옵니다!
MyStockList = KisKR.GetMyStockList()
pprint.pprint(MyStockList)
print("--------------------------------------------")
##########################################################




#실제 투자 종목!!!
InvestStockList = ["122630","252670","233740","251340"]

NowInvestMoney = 0

for stock_code in InvestStockList:
    stock_name = ""
    stock_amt = 0 #수량
    stock_avg_price = 0 #평단

    #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
    for my_stock in MyStockList:
        if my_stock['StockCode'] == stock_code:
            stock_name = my_stock['StockName']
            stock_amt = int(my_stock['StockAmt'])
            stock_avg_price = float(my_stock['StockAvgPrice'])

            
            NowInvestMoney += (stock_amt*stock_avg_price)
            break



###################################################################
###################################################################
KospidaqStrategyList = list()
#파일 경로입니다.
data_file_path = "/var/autobot/KrStock_" + BOT_NAME + ".json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(data_file_path, 'r') as json_file:
        KospidaqStrategyList = json.load(json_file)

except Exception as e:
    print("Init....")

    for stock_code in InvestStockList:

        KospidaqStrategyData = dict()
        KospidaqStrategyData['StockCode'] = stock_code #대상 종목 코드
        KospidaqStrategyData['StockName'] = KisKR.GetStockName(stock_code) #종목 이름
        KospidaqStrategyData['Status'] = "REST" #상태 READY(돌파를체크해야하는 준비상태), INVESTING(돌파해서 투자중), INVESTING_TRY(매수 주문 들어감) REST(조건불만족,투자안함,돌파체크안함) 
        KospidaqStrategyData['DayStatus'] = "NONE" #오늘 매수(BUY)하는 날인지 매도(SELL)하는 날인지 대상이 아닌지 (NONE) 체크
        KospidaqStrategyData['TargetPrice'] = 0 #돌파가격
        KospidaqStrategyData['TryBuyCnt'] = 0 #매수시도하고자 하는 수량!

        KospidaqStrategyList.append(KospidaqStrategyData)

    #파일에 저장
    with open(data_file_path, 'w') as outfile:
        json.dump(KospidaqStrategyList, outfile)


###################################################################
###################################################################
DateData = dict()
#파일 경로입니다.
date_file_path = "/var/autobot/KrStock_" + BOT_NAME + "_Date.json"

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(date_file_path, 'r') as json_file:
        DateData = json.load(json_file)

except Exception as e:
    print("Init....")

    DateData['Date'] = "00" #오늘날짜

    #파일에 저장
    with open(date_file_path, 'w') as outfile:
        json.dump(DateData, outfile)

###################################################################
###################################################################



###################################################################

#오늘 코스피 시가매매 로직이 진행되었는지 날짜 저장 관리 하는 파일
DateSiGaLogicDoneDict = dict()

#파일 경로입니다.
siga_logic_file_path = "/var/autobot/KrStock_" + BOT_NAME + "_TodaySigaLogicDoneDate.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(siga_logic_file_path, 'r') as json_file:
        DateSiGaLogicDoneDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

###################################################################




###################################################################
###################################################################
#리스트에서 데이터를 리턴!
def GetKospidaqStrategyData(stock_code,KospidaqStrategyList):
    ResultData = None
    for KospidaqStrategyData in KospidaqStrategyList:
        if KospidaqStrategyData['StockCode'] == stock_code:
            ResultData = KospidaqStrategyData
            break
    return ResultData



#투자개수
def GetKospidaqInvestCnt(KospidaqStrategyList):
    
    MyStockList = KisKR.GetMyStockList()

    InvestCnt = 0
        
    for KospidaqStrategyData in KospidaqStrategyList:
        stock_code = KospidaqStrategyData['StockCode']
        
        stock_amt = 0
        #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
        for my_stock in MyStockList:
            if my_stock['StockCode'] == stock_code:
                stock_amt = int(my_stock['StockAmt'])
                break
            
        if stock_amt > 0:
            InvestCnt += 1
            
        
    return InvestCnt




#내 계좌의 총 평가금액에서 해당 봇에게 할당할 총 금액비율 1.0 = 100%  0.5 = 50%
InvestRate = 0.3

#기준이 되는 내 총 평가금액에서 투자비중을 곱해서 나온 포트폴리오에 할당된 돈!!
TotalMoney = float(Balance['TotalMoney']) * InvestRate

print("전략에 투자하는 총 금액: ", format(round(TotalMoney), ','))

InvestMoney = TotalMoney
RemainInvestMoney = TotalMoney - NowInvestMoney

print("현재 남은 금액! (투자금 제외): ", format(round(RemainInvestMoney), ','))




DivNum = len(InvestStockList)


#마켓이 열렸는지 여부~!
IsMarketOpen = KisKR.IsMarketOpen()

IsLP_OK = True
#정각 9시 5분 전에는 LP유동성 공급자가 없으니 매매를 피하고자.
if time_info.tm_hour == 0: #9시인데
    if time_info.tm_min < 6: #6분보다 적은 값이면 --> 6분부터 LP가 활동한다고 하자!
        IsLP_OK = False
        
#장이 열렸고 LP가 활동할때 매수!!!
if IsMarketOpen == True and IsLP_OK == True: 

    #혹시 이 봇을 장 시작하자 마자 돌린다면 20초르 쉬어준다.
    #그 이유는 20초는 지나야 오늘의 일봉 정보를 제대로 가져오는데
    #tm_hour가 0은 9시, 1은 10시를 뜻한다. 수능 등 10시에 장 시작하는 경우르 대비!
    if time_info.tm_hour in [0,1] and time_info.tm_min in [0,1]:
        time.sleep(20.0)
        

    print("Market Is Open!!!!!!!!!!!")
    #영상엔 없지만 리밸런싱이 가능할때만 내게 메시지를 보내자!



    #데이터를 조합한다.
    stock_df_list = []

    gugan_lenth = 7
    
    for stock_code in InvestStockList:
        df = Common.GetOhlcv("KR", stock_code,200)

        period = 14

        delta = df["close"].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss

        df['RSI'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")

        df['prevRSI'] = df['RSI'].shift(1)
        df['prevRSI2'] = df['RSI'].shift(2)
        

        df['high_'+str(gugan_lenth)+'_max'] = df['high'].rolling(window=gugan_lenth).max().shift(1)
        df['low_'+str(gugan_lenth)+'_min'] = df['low'].rolling(window=gugan_lenth).min().shift(1)


        df['prevVolume'] = df['volume'].shift(1)
        df['prevVolume2'] = df['volume'].shift(2)
        df['prevVolume3'] = df['volume'].shift(3)

        df['prevClose'] = df['close'].shift(1)
        df['prevOpen'] = df['open'].shift(1)

        df['prevHigh'] = df['high'].shift(1)
        df['prevHigh2'] = df['high'].shift(2)

        df['prevLow'] = df['low'].shift(1)
        df['prevLow2'] = df['low'].shift(2)

        df['Disparity20'] = df['prevClose'] / df['prevClose'].rolling(window=20).mean() * 100.0
        
        df['Disparity11'] = df['prevClose'] / df['prevClose'].rolling(window=11).mean() * 100.0


        df['ma3_before'] = df['close'].rolling(3).mean().shift(1)
        df['ma6_before'] = df['close'].rolling(6).mean().shift(1)
        df['ma19_before'] = df['close'].rolling(19).mean().shift(1)


        df['ma10_before'] = df['close'].rolling(10).mean().shift(1)

        df['ma20_before'] = df['close'].rolling(20).mean().shift(1)
        df['ma20_before2'] = df['close'].rolling(20).mean().shift(2)
        df['ma60_before'] = df['close'].rolling(60).mean().shift(1)
        df['ma60_before2'] = df['close'].rolling(60).mean().shift(2)

        df['ma120_before'] = df['close'].rolling(120).mean().shift(1)



        df['prevChangeMa'] = df['change'].shift(1).rolling(window=20).mean()

        #10일마다 총 100일 평균모멘텀스코어
        specific_days = list()

        for i in range(1,11):
            st = i * 10
            specific_days.append(st)

        for day in specific_days:
            column_name = f'Momentum_{day}'
            df[column_name] = (df['prevClose'] > df['close'].shift(day)).astype(int)
            
        df['Average_Momentum'] = df[[f'Momentum_{day}' for day in specific_days]].sum(axis=1) / 10


        df.dropna(inplace=True) #데이터 없는건 날린다!


        data_dict = {stock_code: df}
        stock_df_list.append(data_dict)
        print("---stock_code---", stock_code , " len ",len(df))
        pprint.pprint(df)




        #시가매매 체크한 기록이 없는 맨 처음이라면 
        if DateSiGaLogicDoneDict.get(stock_code) == None:

            #0으로 초기화!!!!!
            DateSiGaLogicDoneDict[stock_code] = 0
            #파일에 저장
            with open(siga_logic_file_path, 'w') as outfile:
                json.dump(DateSiGaLogicDoneDict, outfile)

                    

    # Combine the OHLCV data into a single DataFrame
    combined_df = pd.concat([list(data_dict.values())[0].assign(stock_code=stock_code) for data_dict in stock_df_list for stock_code in data_dict])

    # Sort the combined DataFrame by date
    combined_df.sort_index(inplace=True)

    pprint.pprint(combined_df)
    print(" len(combined_df) ", len(combined_df))


    date = combined_df.iloc[-1].name

    all_stocks = combined_df.loc[combined_df.index == date].groupby('stock_code')['close'].max().nlargest(DivNum)
    

    Kosdaq_Long_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "233740")]
    Kosdaq_Short_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "251340")]
    #Kospi_Long_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "122630")]
    #Kospi_Short_Data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "252670")]
    
    

    #날짜가 다르다면 날이 바뀐거다
    if day_str != DateData['Date']:
            
            
        line_alert.SendMessage(PortfolioName + "  장이 열려서 매매 가능!!")




        # 일봉 정보 가지고 오는 모듈이 달라지면 에러가 나므로 예외처리
        date_format = "%Y-%m-%d %H:%M:%S"
        date_object = None

        try:
            date_object = datetime.strptime(str(date), date_format)
        
        except Exception as e:
            try:
                date_format = "%Y%m%d"
                date_object = datetime.strptime(str(date), date_format)

            except Exception as e2:
                date_format = "%Y-%m-%d"
                date_object = datetime.strptime(str(date), date_format)
                

        # 요일 가져오기 (0: 월요일, 1: 화요일,2 수요일 3 목요일 4 금요일 5 토요일 ..., 6: 일요일)
        weekday = date_object.weekday()
        print("--weekday--", weekday, time_info.tm_wday)





        #가장 최근 데이터의 날짜의 요일과 봇이 실행되는 요일은 같아야 한다.
        #이게 다르다면 아직 최근 데이터의 날자가 갱신 안되었단 이야기인데 이는 9시 정각이나..(20초 딜레이가 필요) 수능등으로 장 오픈시간이 지연되었을때 다를 수 있다. 그때는 매매하면 안된다
        if weekday == time_info.tm_wday:


            DateData['Date'] = day_str #오늘 맨처음 할일 (종목 선정 및 돌파가격 설정, 상태 설정)을 끝냈으니 날짜를 넣어 다음날 다시 실행되게 한다.
            with open(date_file_path, 'w') as outfile:
                json.dump(DateData, outfile)

            #기본적으로 날이 바뀌었기 때문에 데이 조건(BUY_DAY,SELL_DAY)를 모두 초기화 한다!
            for KospidaqStrategyData in KospidaqStrategyList:
                KospidaqStrategyData['DayStatus'] = "NONE"

                #그리고 투자중 상태는 SELL_DAY로 바꿔준다!!
                if KospidaqStrategyData['Status'] == "INVESTING":
                    KospidaqStrategyData['DayStatus'] = "SELL_DAY"

                    msg = KospidaqStrategyData['StockName'] + "  투자중 상태에요! 조건을 만족하면 매도로 트레이딩 종료 합니다.!!"
                    print(msg)
                    line_alert.SendMessage(msg)


        
            for stock_code in  all_stocks.index:
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

                #해당 정보를 읽는다.
                KospidaqStrategyData = GetKospidaqStrategyData(stock_code,KospidaqStrategyList)

                #만약 정보가 없다면 새로 추가된 종목이니 새로 저장한다!!!
                if KospidaqStrategyData == None:

                    KospidaqStrategyData = dict()
                    KospidaqStrategyData['StockCode'] = stock_code #대상 종목 코드
                    KospidaqStrategyData['StockName'] = KisKR.GetStockName(stock_code) #종목 이름
                    KospidaqStrategyData['Status'] = "REST" #상태 READY(돌파를체크해야하는 준비상태), INVESTING(돌파해서 투자중), REST(조건불만족,투자안함,돌파체크안함) 
                    KospidaqStrategyData['DayStatus'] = "NONE" #오늘 매수하는 날인지 매도하는 날인지 체크
                    KospidaqStrategyData['TargetPrice'] = 0 #돌파가격
                    KospidaqStrategyData['TryBuyCnt'] = 0 #매수시도하고자 하는 수량!

                    KospidaqStrategyList.append(KospidaqStrategyData)

                #코스닥 전략...돌파 매매..
                if stock_code in ["233740","251340"]:
                    
                        
                    PrevClosePrice = stock_data['prevClose'].values[0] 
                    
                    DolpaRate = 0.4

                    # KODEX 코스닥150선물인버스
                    if stock_code == "251340":

                        DolpaRate = 0.4

                    #KODEX 코스닥150레버리지
                    else: 

                        if PrevClosePrice > stock_data['ma60_before'].values[0]:
                            DolpaRate = 0.3
                        else:
                            DolpaRate = 0.4


                    
                    ##########################################################################
                    #갭 상승 하락을 이용한 돌파값 조절!
                    # https://blog.naver.com/zacra/223277173514 이 포스팅을 체크!!!!
                    ##########################################################################
                    Gap = ((abs(stock_data['open'].values[0] - PrevClosePrice) / PrevClosePrice)) * 100.0

                    GapSt = (Gap*0.025)

                    if GapSt > 1.0:
                        GapSt = 1.0
                    if GapSt < 0:
                        GapSt = 0.1

                    if PrevClosePrice > stock_data['open'].values[0] and Gap >= 3.0:
                        DolpaRate *= (1.0 + GapSt)

                    if PrevClosePrice < stock_data['open'].values[0] and Gap >= 3.0:
                        DolpaRate *= (1.0 - GapSt)


        
                    DolPaPrice = stock_data['open'].values[0] + ((stock_data['prevHigh'].values[0] - stock_data['prevLow'].values[0]) * DolpaRate)


                    #어제 무슨 이유에서건 매수 실패했다면 일단 REST로!
                    if KospidaqStrategyData['Status'] == "INVESTING_TRY":
                        KospidaqStrategyData['Status'] = "REST"
                        KospidaqStrategyData['DayStatus'] = "NONE"

                    #어제 무슨 이유에서건 매도 실패했다면 투자중 상태로 변경!
                    if KospidaqStrategyData['Status'] == "SELL_DONE_CHECK":
                        KospidaqStrategyData['Status'] = "INVESTING"
                        KospidaqStrategyData['DayStatus'] = "SELL_DAY"



                    
                    if KospidaqStrategyData['Status'] != "INVESTING": #투자 상태가 아니라면 조건을 체크하여 매수시도할 수 있다!
                        
                        IsBuyReady = True #일단 무조건 True 만약 필터하고자 하면 False로 하고 조건만족시 True로 바꾸면 된다.
                        

                        KospidaqStrategyData['StockCode'] = stock_code #대상 종목 코드
                        KospidaqStrategyData['StockName'] = KisKR.GetStockName(stock_code)


                        if stock_code == "251340":
                            if stock_data['prevClose'].values[0] <= stock_data['ma20_before'].values[0]:
                                IsBuyReady = False 
        

                        else: #레버리지

                            if stock_data['prevLow'].values[0] > stock_data['open'].values[0] and stock_data['prevClose'].values[0] < stock_data['ma10_before'].values[0]:
                                IsBuyReady = False 
                                
                        # 추가 개선 로직 https://blog.naver.com/zacra/223326173552 이 포스팅 참고!!!!
                        IsJung = False    
                        if stock_data['ma10_before'].values[0] > stock_data['ma20_before'].values[0] > stock_data['ma60_before'].values[0] > stock_data['ma120_before'].values[0]:
                            IsJung = True
                            
                        if IsJung == False:
                            
                                    
                            high_price = stock_data['high_'+str(gugan_lenth)+'_max'].values[0] 
                            low_price =  stock_data['low_'+str(gugan_lenth)+'_min'].values[0] 
                            
                            Gap = (high_price - low_price) / 4
                            
                            
                            MaximunPrice = low_price + Gap * 3.0
                            
                            
                            if stock_data['open'].values[0] > MaximunPrice:
                                IsBuyReady = False
                                
                                
                                
                        #기본 필터 통과!! 돌파가격을 정하고 READY상태로 변경
                        if IsBuyReady == True:
                            print("IS Ready!!!")
                            KospidaqStrategyData['TargetPrice'] = DolPaPrice #돌파가격

                            KospidaqStrategyData['Status'] = "READY"
                            KospidaqStrategyData['DayStatus'] = "BUY_DAY"


                            msg = KospidaqStrategyData['StockName'] + " 돌파하면 매수합니다!!!"
                            print(msg)
                            line_alert.SendMessage(msg)

                        #기본 필터 통과 실패 매수 안함! 
                        else:
                            print("No Ready")
            
                            KospidaqStrategyData['Status'] = "REST"
                            KospidaqStrategyData['DayStatus'] = "NONE"


                            msg = KospidaqStrategyData['StockName'] + "  조건을 불만족하여 오늘 돌파매수는 쉽니다!!!"
                            print(msg)
                            line_alert.SendMessage(msg)
                        
                #코스피 전략.... 시가 매매
                else:
                    

                    #어제 무슨 이유에서건 매수 실패했다면 일단 REST로!
                    if KospidaqStrategyData['Status'] == "INVESTING_TRY":
                        KospidaqStrategyData['Status'] = "REST"
                        KospidaqStrategyData['DayStatus'] = "NONE"

                    #어제 무슨 이유에서건 매도 실패했다면 투자중 상태로 변경!
                    if KospidaqStrategyData['Status'] == "SELL_DONE_CHECK":
                        KospidaqStrategyData['Status'] = "INVESTING"
                        KospidaqStrategyData['DayStatus'] = "SELL_DAY"

                    

                    if KospidaqStrategyData['Status'] != "INVESTING": #투자 상태가 아니라면 조건을 체크하여 매수시도할 수 있다!
                        


                        KospidaqStrategyData['StockCode'] = stock_code #대상 종목 코드
                        KospidaqStrategyData['StockName'] = KisKR.GetStockName(stock_code)

                        KospidaqStrategyData['Status'] = "READY"
                        KospidaqStrategyData['DayStatus'] = "BUY_DAY"


                        msg = KospidaqStrategyData['StockName'] + " 조건을 만족했다면 매수합니다!!!"
                        print(msg)
                        line_alert.SendMessage(msg)




                #파일에 저장
                with open(data_file_path, 'w') as outfile:
                    json.dump(KospidaqStrategyList, outfile)
        else:

            if time_info.tm_min == 0 or time_info.tm_min == 30:
                msg = "요일이 다르게 나왔어요! 좀 더 기다려봐요!"
                print(msg)
                line_alert.SendMessage(msg)
                

    if day_str == DateData['Date']: #오늘 할일을 한다!


        for KospidaqStrategyData in KospidaqStrategyList:
            pprint.pprint(KospidaqStrategyData)

            stock_code = KospidaqStrategyData['StockCode']
            
            stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

            if len(stock_data) == 1:
                
                NowOpenPrice = stock_data['open'].values[0]
                PrevOpenPrice = stock_data['prevOpen'].values[0] 
                PrevClosePrice = stock_data['prevClose'].values[0] 


                #현재가!
                CurrentPrice = KisKR.GetCurrentPrice(stock_code)        
                


                IsSellAlready = False   
                #해당 ETF가 매도하는 날 상태이다!
                if KospidaqStrategyData['DayStatus'] == "SELL_DAY":

                    #제대로 매도되었는지 확인!
                    if KospidaqStrategyData['Status'] == "SELL_DONE_CHECK":
                        stock_amt = 0 #수량

                        
                        #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
                        for my_stock in MyStockList:
                            if my_stock['StockCode'] == stock_code:
                                stock_amt = int(my_stock['StockAmt'])
                                break

                        print("stock_amt : ", stock_amt)

                        if stock_amt == 0:
                            KospidaqStrategyData['Status'] = "REST" 
                            KospidaqStrategyData['DayStatus'] = "NONE"

                            msg = KospidaqStrategyData['StockName']  + " 모두 매도된 것이 확인 되었습니다!"
                            print(msg)
                            line_alert.SendMessage(msg)


                                            
                            #파일에 저장
                            with open(data_file_path, 'w') as outfile:
                                json.dump(KospidaqStrategyList, outfile)

                        else:

                            KisKR.CancelAllOrders(KospidaqStrategyData['StockCode'],"ALL")

                            data = KisKR.MakeSellMarketOrder(KospidaqStrategyData['StockCode'],stock_amt)


                            msg = KospidaqStrategyData['StockName']  + " 모두 매도한 줄 알았는데 실패했나봐요 다시 시도합니다.\n" + str(data)
                            print(msg)
                            line_alert.SendMessage(msg)



                    #만약 투자중이라면 조건을 체크!
                    if KospidaqStrategyData['Status'] == "INVESTING": #투자중 상태


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
                            
                        #코스닥 전략...돌파 매매..
                        if stock_code in ["233740","251340"]:
                            
                                    
                            if stock_amt > 0:
                                

                                CutRate = 0.4

                                if stock_code == "251340":
                                    CutRate = 0.4

                                else:

                                    if PrevClosePrice > stock_data['ma60_before'].values[0]:
                                        CutRate = 0.4
                                    else:
                                        CutRate = 0.3


                                
                                CutPrice = stock_data['open'].values[0] - ((stock_data['prevHigh'].values[0] - stock_data['prevLow'].values[0]) * CutRate)
                                
                                

                                CurrentPrice = KisKR.GetCurrentPrice(stock_code)  

                                if CurrentPrice <= CutPrice or stock_data['low'].values[0] <= CutPrice :
                                    
                                    
                                    
                                    pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,stock_amt))
                                    
                                    KospidaqStrategyData['Status'] = "SELL_DONE_CHECK" 

                                    msg = KospidaqStrategyData['StockName']  + " 모두 시장가 매도!!! " + str(stock_revenue_money) + " 수익 확정!! 수익률:" + str(stock_revenue_rate) + "%"
                                    print(msg)
                                    line_alert.SendMessage(msg)

                                    IsSellAlready = True
                                    


                                
                            else:
                                KospidaqStrategyData['Status'] = "REST" 
                                KospidaqStrategyData['DayStatus'] = "NONE"


                                msg = KospidaqStrategyData['StockName']  + " 매수했다고 기록되었는데 물량이 없네요? 암튼 초기화 했어요 다음날 다시 전략 시작합니다!"
                                print(msg)
                                line_alert.SendMessage(msg)
                        #코스피
                        else:
                            
                            if stock_amt > 0:
                                
                                IsSellGo = False

                                if stock_code == "252670":
                                    
                                    if stock_data['Disparity11'].values[0] > 105:
                                        #
                                        if  PrevClosePrice < stock_data['ma3_before'].values[0]: 
                                            IsSellGo = True

                                    else:
                                        #
                                        if PrevClosePrice < stock_data['ma6_before'].values[0] and PrevClosePrice < stock_data['ma19_before'].values[0] : 
                                            IsSellGo = True

                                else:
                                    print("")
                                    
                        
                                    total_volume = (stock_data['prevVolume'].values[0]+ stock_data['prevVolume2'].values[0] +stock_data['prevVolume3'].values[0]) / 3.0

                                    Disparity = stock_data['Disparity20'].values[0] 

                                    if (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0] or stock_data['prevVolume'].values[0] < total_volume) and (Disparity < 98 or Disparity > 105):
                                        print("hold..")
                                    else:
                                        IsSellGo = True

                    
                                if IsSellGo == True:
                                    
                                    pprint.pprint(KisKR.MakeSellMarketOrder(stock_code,stock_amt))
                                    
                                    KospidaqStrategyData['Status'] = "SELL_DONE_CHECK" 

                                    msg = KospidaqStrategyData['StockName']  + " 모두 시장가 매도!!! " + str(stock_revenue_money) + " 수익 확정!! 수익률:" + str(stock_revenue_rate) + "%"
                                    print(msg)
                                    line_alert.SendMessage(msg)

                                    IsSellAlready = True



                                
                            else:
                                KospidaqStrategyData['Status'] = "REST" 
                                KospidaqStrategyData['DayStatus'] = "NONE"


                                msg = KospidaqStrategyData['StockName']  + " 매수했다고 기록되었는데 물량이 없네요? 암튼 초기화 했어요 다음날 다시 전략 시작합니다!"
                                print(msg)
                                line_alert.SendMessage(msg)


                    


                else:
                    #해당 ETF가 매수하는 날 상태이다!
                    if KospidaqStrategyData['DayStatus'] == "BUY_DAY":              
                        
                        #매수 시도가 진행 되었다. 매수 완료 되었는지 체크
                        if KospidaqStrategyData['Status'] == "INVESTING_TRY":
                            
                            MyStockList = KisKR.GetMyStockList()

                            stock_amt = 0 #수량

                            
                            #내가 보유한 주식 리스트에서 매수된 잔고 정보를 가져온다
                            for my_stock in MyStockList:
                                if my_stock['StockCode'] == KospidaqStrategyData['StockCode']:
                                    stock_amt = int(my_stock['StockAmt'])
                                    break
                                
                            #실제로 1주라도 매수가 되었다면 투자중 상태로 변경!!!
                            if stock_amt > 0:
                                KospidaqStrategyData['Status'] = "INVESTING"
                                KospidaqStrategyData['DayStatus'] = "NONE"
                                
                                msg = KospidaqStrategyData['StockName'] + " 투자중이에요!!"
                                print(msg)
                                line_alert.SendMessage(msg)


                            #아니라면 알림으로 알려준다!!
                            else:

                                
                                msg = KospidaqStrategyData['StockName'] + "  조건을 만족하여 매수 시도했는데 아직 1주도 매수되지 않았어요! 감산해서 매수시도 합니다! "
                                print(msg)
                                line_alert.SendMessage(msg)


                                if KospidaqStrategyData.get('TryBuyCnt') == None:
                                    KospidaqStrategyData['TryBuyCnt'] = 1


                                KospidaqStrategyData['TryBuyCnt'] = int(KospidaqStrategyData['TryBuyCnt'] * 0.7)

                                if KospidaqStrategyData['TryBuyCnt'] > 1:
                                    returnData = KisKR.MakeBuyMarketOrder(KospidaqStrategyData['StockCode'],KospidaqStrategyData['TryBuyCnt'],True) #30%감소된 수량으로 매수 시도!!


                                    msg = KospidaqStrategyData['StockName'] + "  매수 시도!!! " + str(returnData)
                                    print(msg)
                                    line_alert.SendMessage(msg)

                                
                                else:

                                    KospidaqStrategyData['Status'] = "REST"
                                    KospidaqStrategyData['DayStatus'] = "NONE"
                                    

                                    msg = KospidaqStrategyData['StockName'] + "  매수 실패!!! "
                                    print(msg)
                                    line_alert.SendMessage(msg)



                            
                        #상태를 체크해서 READY라면 돌파시 매수한다!
                        if KospidaqStrategyData['Status'] == "READY" and GetKospidaqInvestCnt(KospidaqStrategyList) < 2:
                            
                            
                            
                            print("돌파 체크중...")
                            
                            
                            #코스닥 전략...돌파 매매..
                            if stock_code in ["233740","251340"]:
                                
                    
                                DolpaRate = 0.4

                                # KODEX 코스닥150선물인버스
                                if stock_code == "251340":

                                    DolpaRate = 0.4

                                #KODEX 코스닥150레버리지
                                else: 

                                    if PrevClosePrice > stock_data['ma60_before'].values[0]:
                                        DolpaRate = 0.3
                                    else:
                                        DolpaRate = 0.4


                                ##########################################################################
                                #갭 상승 하락을 이용한 돌파값 조절!
                                # https://blog.naver.com/zacra/223277173514 이 포스팅을 체크!!!!
                                ##########################################################################
                                Gap = ((abs(stock_data['open'].values[0] - PrevClosePrice) / PrevClosePrice)) * 100.0

                                GapSt = (Gap*0.025)

                                if GapSt > 1.0:
                                    GapSt = 1.0
                                if GapSt < 0:
                                    GapSt = 0.1

                                if PrevClosePrice > stock_data['open'].values[0] and Gap >= 3.0:
                                    DolpaRate *= (1.0 + GapSt)

                                if PrevClosePrice < stock_data['open'].values[0] and Gap >= 3.0:
                                    DolpaRate *= (1.0 - GapSt)


                    
                                DolPaPrice = stock_data['open'].values[0] + ((stock_data['prevHigh'].values[0] - stock_data['prevLow'].values[0]) * DolpaRate)



                                KospidaqStrategyData['TargetPrice'] = DolPaPrice


                                #돌파가격보다 현재가가 높다? 돌파한거다 매수한다!
                                if CurrentPrice >= KospidaqStrategyData['TargetPrice'] or stock_data['high'].values[0] >= KospidaqStrategyData['TargetPrice']  :

                                    Rate = 1.0
                                    if len(Kosdaq_Long_Data) == 1 and len(Kosdaq_Short_Data) == 1:
                                    
                                        IsLongStrong = False
                                        
                                        if Kosdaq_Long_Data['Average_Momentum'].values[0] > Kosdaq_Short_Data['Average_Momentum'].values[0]:
                                            IsLongStrong = True
                                            
                                        IsLongStrong2 = False
                                        
                                        if Kosdaq_Long_Data['prevChangeMa'].values[0] > Kosdaq_Short_Data['prevChangeMa'].values[0]:
                                            IsLongStrong2 = True
                                            
                                            
                                        if IsLongStrong == True and IsLongStrong2 == True:
                                            
                                            if stock_code == "233740":
                                                Rate = 1.3
                                            else:
                                                Rate = 0.7
                                                
                                        elif IsLongStrong == False and IsLongStrong2 == False:
                                                
                                            if stock_code == "233740":
                                                Rate = 0.7
                                            else:
                                                Rate = 1.3
                                                

                                
                                            
                                    InvestMoneyCell = (InvestMoney / len(InvestStockList)) * Rate
            
                
                                    #할당된 투자금이 남은돈보다 많다면 남은 돈만큼으로 세팅!
                                    if RemainInvestMoney < InvestMoneyCell:
                                        InvestMoneyCell = RemainInvestMoney

                                        
                                        
                                    BuyAmt = int(InvestMoneyCell / CurrentPrice)
                                    

                                    #최소 2주는 살 수 있도록!
                                    if BuyAmt < 2:
                                        BuyAmt = 2

                                    KospidaqStrategyData['TryBuyCnt'] = BuyAmt #매수할 수량을..저장!
                                    ######## 시장가 지정가 나눠서 고고 ##########    
                                    #SliceAmt = int(BuyAmt / 2)

                                    #절반은 시장가로 바로고!
                                    #KisKR.MakeBuyMarketOrder(KospidaqStrategyData['StockCode'],SliceAmt,True) 
                                    
                                    #절반은 돌파가격 지정가로!
                                    #KisKR.MakeBuyLimitOrder(KospidaqStrategyData['StockCode'],SliceAmt,KospidaqStrategyData['TargetPrice'])

                                    
                                    ######## 시장가 1번에 고고 ##########
                                    #시장가로 바로고!
                                    KisKR.MakeBuyMarketOrder(KospidaqStrategyData['StockCode'],BuyAmt,True) 
                                    
                                    
                                    RemainInvestMoney -= InvestMoneyCell
                                    
                                    KospidaqStrategyData['Status'] = "INVESTING_TRY"

                        


                                    msg = KospidaqStrategyData['StockName'] + "  조건을 만족하여 매수!!! 투자 시작!! "
                                    print(msg)
                                    line_alert.SendMessage(msg)


                    
                                else:
                                    print("아직 돌파 안함..")
                                
                                
                            #코스피 전략...시가 매매
                            else:
                                print("")

                                                    
                                #체크 날짜가 다르다면 맨 처음이거나 날이 바뀐것이다!!
                                if DateSiGaLogicDoneDict[stock_code] != day_n:
                                    
                                        
                                    IsBuyGo = False
                                    if stock_code == "252670":

                                        #이거변경
                                        if PrevClosePrice > stock_data['ma3_before'].values[0]  and PrevClosePrice > stock_data['ma6_before'].values[0]  and PrevClosePrice > stock_data['ma19_before'].values[0] and stock_data['prevRSI'].values[0] < 70 and stock_data['prevRSI2'].values[0] < stock_data['prevRSI'].values[0]:
                                            if (stock_data['prevVolume2'].values[0] < stock_data['prevVolume'].values[0]) and (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0]) and PrevClosePrice > stock_data['ma60_before'].values[0] and stock_data['ma60_before2'].values[0] < stock_data['ma60_before'].values[0]  and stock_data['ma3_before'].values[0]  > stock_data['ma6_before'].values[0]  > stock_data['ma19_before'].values[0]  :
                                                IsBuyGo = True

                                    else:

                                        Disparity = stock_data['Disparity20'].values[0] 
                                        
                                        if (stock_data['prevLow2'].values[0] < stock_data['prevLow'].values[0]) and (Disparity < 98 or Disparity > 106) and stock_data['prevRSI'].values[0] < 80 :
                                            IsBuyGo = True
                        
                                        
                                    if IsBuyGo == True:
                                        
                        
                                        Rate = 1.0
                                        
    
                                                
                                        InvestMoneyCell = (InvestMoney / len(InvestStockList)) * Rate
                
                
                                            
                                        BuyAmt = int(InvestMoneyCell / CurrentPrice)
                                        
                                        

                                        #최소 2주는 살 수 있도록!
                                        if BuyAmt < 2:
                                            BuyAmt = 2

                                        KospidaqStrategyData['TryBuyCnt'] = BuyAmt #매수할 수량을..저장!
                                        
                                        ######## 시장가 지정가 나눠서 고고 ##########    
                                        #SliceAmt = int(BuyAmt / 2)

                                        #절반은 시장가로 바로고!
                                        #KisKR.MakeBuyMarketOrder(KospidaqStrategyData['StockCode'],SliceAmt,True) 
                                        
                                        #절반은 돌파가격 지정가로!
                                        #KisKR.MakeBuyLimitOrder(KospidaqStrategyData['StockCode'],SliceAmt,CurrentPrice)

                                        
                                        ######## 시장가 1번에 고고 ##########
                                        #시장가로 바로고!
                                        KisKR.MakeBuyMarketOrder(KospidaqStrategyData['StockCode'],BuyAmt,True) 
                                        
                                        
                                        
                                        RemainInvestMoney -= InvestMoneyCell
                                        
                                        KospidaqStrategyData['Status'] = "INVESTING_TRY" 
                            


                                        msg = KospidaqStrategyData['StockName'] + "  조건을 만족하여 매수!!! 투자 시작!! "
                                        print(msg)
                                        line_alert.SendMessage(msg)


                            

                                    #시가 매수 로직 안으로 들어왔다면 날자를 바꿔준다!!
                                    DateSiGaLogicDoneDict[stock_code] = day_n
                                    #파일에 저장
                                    with open(siga_logic_file_path, 'w') as outfile:
                                        json.dump(DateSiGaLogicDoneDict, outfile)   

        #파일에 저장
        with open(data_file_path, 'w') as outfile:
            json.dump(KospidaqStrategyList, outfile)
else:
    print("Market Is Close!!!!!!!!!!!")

    #line_alert.SendMessage(PortfolioName + "  장이 열려있지 않아요!")


pprint.pprint(DateData)
pprint.pprint(KospidaqStrategyList)





