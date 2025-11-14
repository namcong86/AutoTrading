#-*-coding:utf-8 -*-
'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
백테스팅이 없는 전략은 위험할 수 있어요!
소액으로 테스트하시고 공부용으로 사용하세요 ^^!
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


관련 포스팅
https://blog.naver.com/zacra/223349033981

위 포스팅을 꼭 참고하세요!!!
 
하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

'''
import myUpbit   #우리가 만든 함수들이 들어있는 모듈
import time
import pyupbit

import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키

import line_alert   

import json



#############################################################
# 10초 쉬고 시작! 다른 업비트 봇과 중복 실행을 방지하기 위해서!
#############################################################
time.sleep(10.0)

#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

#업비트 객체를 만든다
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)


#내가 매수할 총 코인 개수
MaxCoinCnt = 10.0

#비트 이더등 따로 투자하고 있거나 제외 시킬 코인을 여기에 추가!!
OutCoinList = ["KRW-BTC","KRW-ETH"]


#내가 가진 잔고 데이터를 다 가져온다.
balances = upbit.get_balances()

TotalMoney = myUpbit.GetTotalMoney(balances) #총 원금

#내 남은 원화(현금)에서 투자하고 싶으면 아래 코드
#TotalMoney = float(upbit.get_balance("KRW"))


#총 투자금 대비 얼마를 투자할지 여기서는 30%
######################################################
InvestMoney = TotalMoney * 0.3
######################################################



#코인당 매수할 매수금액
CoinMoney = InvestMoney / MaxCoinCnt

#4분할 해서 매매를 할 것이기에 코인별 최소 매수 금액은 4만원으로 설정!
if CoinMoney < 40000:
    CoinMoney = 40000



print("-----------------------------------------------")
print ("InvestMoney:", InvestMoney)
print ("CoinMoney:", CoinMoney)



#실재 돌파해서 매수할 코인들이 저장될 파일
DolPaCoinList = list()

#파일 경로입니다.
dolpha_type_file_path = "/var/autobot/UpbitDolPaCoin_New.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(dolpha_type_file_path, 'r') as json_file:
        DolPaCoinList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")




##############################################################
#트레일링 스탑을 위한 정보를 저장할 파일
DolPaRevenueDict = dict()

#파일 경로입니다.
revenue_type_file_path = "/var/autobot/UpbitDolPaRevenue_New.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(revenue_type_file_path, 'r') as json_file:
        DolPaRevenueDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################




##############################################################
#매수한 수량의 1/4를 저장할 파일
DivAmtDict = dict()

#파일 경로입니다.
divmoney_file_path = "/var/autobot/UpbitDolPaDivMoney_New.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(divmoney_file_path, 'r') as json_file:
        DivAmtDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################


##############################################################
#익절, 트레일링 스탑 기준이 되는 비율을 저장할 파일
StopRateDict = dict()

#파일 경로입니다.
stoprate_file_path = "/var/autobot/UpbitDolPaStopRate_New.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(stoprate_file_path, 'r') as json_file:
        StopRateDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################

##############################################################
#트레일링 스탑을 몇번 했는지 기록할 파일
StopCntDict = dict()

#파일 경로입니다.
stopcnt_file_path = "/var/autobot/UpbitDolPaStopCnt_New.json"
try:
    #이 부분이 파일을 읽어서 딕셔너리에 넣어주는 로직입니다. 
    with open(stopcnt_file_path, 'r') as json_file:
        StopCntDict = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")

##############################################################

    


#시간 정보를 가져옵니다. 아침 9시의 경우 서버에서는 hour변수가 0이 됩니다.
time_info = time.gmtime()
hour_n = time_info.tm_hour
min_n = time_info.tm_min
print(hour_n, min_n)




#오늘의 거래대금 탑 코인 30개가 저장되어 있는 파일
top_file_path = "/var/autobot/UpbitTopCoinList.json"

TopCoinList = list()

#파일을 읽어서 리스트를 만듭니다.
try:
    with open(top_file_path, "r") as json_file:
        TopCoinList = json.load(json_file)

except Exception as e:
    TopCoinList = myUpbit.GetTopCoinList("day",30)
    print("Exception by First")



#거래대금 탑 코인 리스트를 1위부터 내려가며 매수 대상을 찾는다.
#전체 원화 마켓의 코인이 아니라 탑 순위 TopCoinList 안에 있는 코인만 체크해서 매수한다는 걸 알아두세요!
for ticker in TopCoinList:
    try: 
        #아웃 코인이라면 스킵한다!
        if myUpbit.CheckCoinInList(OutCoinList,ticker) == True:
            continue

        #이미 매수된 코인이라면 스킵한다!
        if myUpbit.IsHasCoin(balances,ticker) == True:
            continue
        
        
        print("Coin Ticker: ",ticker)

        #변동성 돌파리스트에 없다. 즉 아직 변동성 돌파 전략에 의해 매수되지 않았다.
        if myUpbit.CheckCoinInList(DolPaCoinList,ticker) == False:
            
            time.sleep(0.05)
            df_day = pyupbit.get_ohlcv(ticker,interval="day") #일봉 데이타를 가져온다.
            Ma5_day = myUpbit.GetMA(df_day,5,-1) 
            
            if df_day['open'].iloc[-1] <= df_day['close'].iloc[-1] and Ma5_day <= df_day['close'].iloc[-1]: #현재 일봉이 양봉이면서 5일선 위에 있는 코인만!
            
                
                time.sleep(0.05)
                df = pyupbit.get_ohlcv(ticker,interval="minute30") #30분봉 데이타를 가져온다.

                #현재가
                now_price = float(df['close'].iloc[-1])  

                #10개 캔들의 최고가와 최저가
                df['maxhigh10'] = df['high'].rolling(window=10).max()
                df['minlow10'] = df['low'].rolling(window=10).min()

                #이전 캔들 기준
                high_price_b = df['maxhigh10'].iloc[-2]
                low_price_b =  df['minlow10'].iloc[-2]
                
                #현재 캔들 기준
                high_price = df['maxhigh10'].iloc[-1]
                low_price =  df['minlow10'].iloc[-1]
                
                
                #이전 캔들 기준 구간의 1/4가격
                TargetPrice_b = low_price_b + (high_price_b-low_price_b) * 1.0/4.0
                
                #현재 캔들 기준 구간의 1/4가격
                TargetPrice = low_price + (high_price-low_price) * 1.0/4.0      
                
                
                print(now_price , " > ", min(TargetPrice_b,TargetPrice))
                
                #이전 캔들에서는 기준 구간 1/4을 돌파 못했는데 현재 캔들에서 돌파했다면 매수!!!
                if  len(DolPaCoinList) < MaxCoinCnt and min(TargetPrice_b,TargetPrice) >= df['close'].iloc[-2] and min(TargetPrice_b,TargetPrice) <= df['close'].iloc[-1]:



                    #보유하고 있지 않은 코인 (매수되지 않은 코인)일 경우만 매수한다!
                    if myUpbit.IsHasCoin(balances, ticker) == False:


                        
                        time.sleep(0.05)
                        df_5 = pyupbit.get_ohlcv(ticker,interval="minute5")
                        df_5['maxhigh10'] = df_5['high'].rolling(window=10).max()
                        df_5['minlow10'] = df_5['low'].rolling(window=10).min()
                        df_5['ma10'] = df_5['close'].rolling(window=10).mean()

                                        
                        high_price = df_5['maxhigh10'].iloc[-1]
                        low_price =  df_5['minlow10'].iloc[-1]
                        

                        BoxRate = (high_price - low_price) / low_price * 100.0
                        
        
                                                
                        #박스가 최소 0.5%는 되어야 된다! 그래야 먹을게 있지 ^^
                        #현재 캔들이 양봉이다!
                        if BoxRate >= 0.5 and df_5['open'].iloc[-1] <= df_5['close'].iloc[-1]:
                        

                            BuyMoney = CoinMoney
                            

                            print("!!!!!!!!!!!!!!!DolPa GoGoGo!!!!!!!!!!!!!!!!!!!!!!!!")
                            #시장가 매수를 한다.
                            balances = myUpbit.BuyCoinMarket(upbit,ticker,BuyMoney)
                    


                            #매수된 코인을 DolPaCoinList 리스트에 넣고 이를 파일로 저장해둔다!
                            DolPaCoinList.append(ticker)
                            
                            #파일에 리스트를 저장합니다
                            with open(dolpha_type_file_path, 'w') as outfile:
                                json.dump(DolPaCoinList, outfile)


                            ##############################################################
                            #매수와 동시에 초기 수익율을 넣는다. (당연히 0일테니 0을 넣고)
                            DolPaRevenueDict[ticker] = 0
                            
                            #파일에 딕셔너리를 저장합니다
                            with open(revenue_type_file_path, 'w') as outfile:
                                json.dump(DolPaRevenueDict, outfile)
                            ##############################################################



                                

                            ##############################################################
                            #익절 및 트레링일 스탑 기준이 되는 비율!
                            StopRateDict[ticker] = BoxRate
                            
                            #파일에 딕셔너리를 저장합니다
                            with open(stoprate_file_path, 'w') as outfile:
                                json.dump(StopRateDict, outfile)
                            ##############################################################

                            ##############################################################
                            #스탑 횟수!
                            StopCntDict[ticker] = 0
                            
                            #파일에 딕셔너리를 저장합니다
                            with open(stopcnt_file_path, 'w') as outfile:
                                json.dump(StopCntDict, outfile)
                            ##############################################################


                            ##############################################################
                            #매입 수량
                            coin_volume = upbit.get_balance(ticker)

                            DivAmtDict[ticker] = coin_volume / 4.0
                            
                            #파일에 딕셔너리를 저장합니다
                            with open(divmoney_file_path, 'w') as outfile:
                                json.dump(DivAmtDict, outfile)
                            ##############################################################



                            #평균 매입 단가를 읽어옵니다!
                            avgPrice = myUpbit.GetAvgBuyPrice(balances,ticker)

                            #아까 구한 박스비율의 60%만큼 오르면 1/4익절!
                            target_price =  avgPrice * (1.0 + (StopRateDict[ticker]*0.6/100.0)) #목표 수익 가격

                            #지정가 매도를 주문을 넣는다
                            myUpbit.SellCoinLimit(upbit,ticker,target_price,DivAmtDict[ticker])
                            
                            #아까 구한 박스비율 120% 만큼 오르면 1/4익절!
                            target_price =  avgPrice * (1.0 + (StopRateDict[ticker]*1.2/100.0)) #목표 수익 가격

                            #지정가 매도를 주문을 넣는다
                            myUpbit.SellCoinLimit(upbit,ticker,target_price,DivAmtDict[ticker])
                            


                            #이렇게 매수했다고 메세지를 보낼수도 있다
                            line_alert.SendMessage(ticker + "코인 돌파 매수를 했어요!!! 신난다!")





    except Exception as e:
        print("---:", e)





Tickers = pyupbit.get_tickers("KRW")

for ticker in Tickers:
    try: 
        print("Coin Ticker: ",ticker)

        #변동성 돌파로 매수된 코인이다!!! (실제로 매도가 되서 잔고가 없어도 파일에 쓰여있다면 참이니깐 이 안의 로직을 타게 됨)
        if myUpbit.CheckCoinInList(DolPaCoinList,ticker) == True:


            #실제 매수해 보유 상태인지
            if myUpbit.IsHasCoin(balances, ticker) == True:

                #수익율을 구한다.
                revenue_rate = myUpbit.GetRevenueRate(balances,ticker)

                ##############################################################
                #방금 구한 수익율이 파일에 저장된 수익율보다 높다면 갱신시켜준다!
                if revenue_rate > DolPaRevenueDict[ticker]:

                    #이렇게 딕셔너리에 값을 넣어주면 된다.
                    DolPaRevenueDict[ticker] = revenue_rate
                    
                    #파일에 딕셔너리를 저장합니다
                    with open(revenue_type_file_path, 'w') as outfile:
                        json.dump(DolPaRevenueDict, outfile)

                #그게 아니라면 트레일링 스탑을 체크해야..
                else:
                    
            
                    
                    StopRate = StopRateDict[ticker] * 0.5 #트레일링 스탑은 아까 구간 박스 비율의 50%만큼 떨어지면 일부 스탑!
                    
                    
                    #고점 수익율 - 스탑 수익율 >= 현재 수익율...
                    if (DolPaRevenueDict[ticker] - StopRate) >= revenue_rate :
                        
                        #1번 스탑 했다?
                        if StopCntDict[ticker] >= 1:
                        
                            #모든 주문 취소하고
                            myUpbit.CancelCoinOrder(upbit,ticker)
                            time.sleep(0.2)
                            
                            #모두 판다!
                            Remain_Amt = upbit.get_balance(ticker)
                            
                            #시장가로 모두 매도!
                            balances = myUpbit.SellCoinMarket(upbit,ticker,Remain_Amt)
                            #이렇게 손절했다고 메세지를 보낼수도 있다
                            line_alert.SendMessage(ticker + "코인 모두 팔아 트레이딩 종료합니다! 종료시 수익률:" + str(round(revenue_rate,2)) + "%")
                                

                        else:
                        
                            if revenue_rate < 0 or DolPaRevenueDict[ticker] > StopRate:
                                
                                
                                DolPaRevenueDict[ticker] = revenue_rate #다음 트레일링 스탑을 위해 트레일링 시작 수익률 초기화!!
                                #파일에 딕셔너리를 저장합니다
                                with open(revenue_type_file_path, 'w') as outfile:
                                    json.dump(DolPaRevenueDict, outfile)
                                    
                                    
                                #현재가를 구하다
                                NowCurrentPrice = pyupbit.get_current_price(ticker)
                                Sell_Amt = DivAmtDict[ticker]

                                
                                #시장가로 모두 매도!
                                balances = myUpbit.SellCoinMarket(upbit,ticker,Sell_Amt)
                                #이렇게 손절했다고 메세지를 보낼수도 있다
                                line_alert.SendMessage(ticker + "코인 1/4 팔아 트레일링 스탑! 스탑시 수익률:" + str(round(revenue_rate,2)) + "%")
                                

                                ##############################################################
                                #스탑 횟수!
                                StopCntDict[ticker] += 1
                                
                                #파일에 저장합니다
                                with open(stopcnt_file_path, 'w') as outfile:
                                    json.dump(StopCntDict, outfile)
                                ##############################################################




                

                ##############################################################

            else:
                #전략이 매매했는데 잔고가 없다면?? 모두 매도된 상태! 새 캔들을 위해 파일에서 삭제처리!!
                if min_n == 29 or min_n == 59:

                    #리스트에서 코인을 빼 버린다.
                    DolPaCoinList.remove(ticker)

                    #파일에 리스트를 저장합니다
                    with open(dolpha_type_file_path, 'w') as outfile:
                        json.dump(DolPaCoinList, outfile)
                


    except Exception as e:
        print("---:", e)

