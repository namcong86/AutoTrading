'''

!!!!! 다운로드 한 코드를 어딘가에 공개하거나 공유하는 것은 범죄 행위입니다. 유의해 주세요!!!!!!

매월 자동매매 계좌 공개를 하고 있어요!
https://m.site.naver.com/1ojdd

참고하세요 :)

'''


import myBithumb
import pandas as pd
import time
import json

import line_alert 

BOT_NAME = "MyDoubleMaStrategy_1d4h_Bithumb"

#포트폴리오 이름
PortfolioName = "더블이동평균코인전략_1d4h_빗썸"

limitDiv = 2000 #10일 거래대금 평균의 1/2000을 주문 상한으로 정의!


#리밸런싱이 가능한지 여부를 판단! (즉 매매여부 판단 )
Is_Rebalance_Go = False


#최소 매수 금액
minmunMoney = 5500

#내가 가진 잔고 데이터를 다 가져온다.
balances = myBithumb.GetBalances()

TotalMoney = myBithumb.GetTotalMoney(balances) #총 원금 (총 투자원금+ 남은 원화)
TotalRealMoney = myBithumb.GetTotalRealMoney(balances) #총 평가금액

print("TotalMoney", TotalMoney)
print("TotalRealMoney", TotalRealMoney)
#투자 비중 -> 1.0 : 100%  0.5 : 50%   0.1 : 10%
InvestRate = 0.5 #투자 비중은 자금사정에 맞게 수정하세요!
##########################################################################
InvestTotalMoney = TotalMoney * InvestRate 
##########################################################################

print("InvestTotalMoney:", InvestTotalMoney)



#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################


InvestCoinList = list()
InvestCoinList.append({"coin_ticker":"KRW-BTC", "small_ma":7 , "big_ma":42, "invest_rate":0.5}) 
InvestCoinList.append({"coin_ticker":"KRW-ETH", "small_ma":12 , "big_ma":27, "invest_rate":0.5}) 


#####################################################################################################################################
#####################################################################################################################################
#####################################################################################################################################



#이평선 정보를 읽어온다
CoinFindMaList = list()

#파일 경로입니다.
coinfindma_file_path = "/var/autobot/FindDoubleMaList_Bithumb.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(coinfindma_file_path, 'r') as json_file:
        CoinFindMaList = json.load(json_file)

except Exception as e:
    print("Exception ", e)
    
    

#이평선 정보를 읽어온다
CoinFindMa4hList = list()

#파일 경로입니다.
coinfind4hma_file_path = "/var/autobot/FindDoubleMaList_Bithumb_4h.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(coinfind4hma_file_path, 'r') as json_file:
        CoinFindMa4hList = json.load(json_file)

except Exception as e:
    print("Exception ", e)


##########################################################



#현재 투자중 상태인 리스트! 
CoinInvestList = list()

#파일 경로입니다.
invest_file_path = "/var/autobot/"+BOT_NAME+"_CoinInvestList.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(invest_file_path, 'r') as json_file:
        CoinInvestList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")
    
    
    
#현재 투자중 상태인 리스트! 
CoinInvest_4h_List = list()

#파일 경로입니다.
invest_4h_file_path = "/var/autobot/"+BOT_NAME+"_CoinInvest_List_4h.json"
try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(invest_4h_file_path, 'r') as json_file:
        CoinInvest_4h_List = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")


##########################################################



#투자 코인 리스트
MyPortfolioList = list()

#리밸런싱 즉 이번에 매매를 해야 되는 코인리스트!
Rebalance_coin = list()

for coin_info in InvestCoinList:

    coin_ticker = coin_info['coin_ticker']
    
    #각 Invest_1d_Rate +  Invest_4h_Rate의 값이 최소0에서 최대 1.0이 된다!
    Invest_1d_Rate = 0
    Invest_4h_Rate = 0
    
    
    
    asset = dict()
    asset['coin_ticker'] = coin_ticker       #종목코드
    
    ####################################################################################################
    ####################################################################################################
    ####################################################################################################
    time.sleep(0.2)
    df = myBithumb.GetOhlcv(coin_ticker,'1d',300)
    
    #거래대금 10일 평균 계산
    df['value_ma'] = df['value'].rolling(window=10).mean()
    asset['value10ma'] = float(df['value_ma'].iloc[-2])
    
    small_ma = coin_info['small_ma']
    big_ma = coin_info['big_ma']
    
    #일봉 기준 이평선 가져오기!
    for maData in CoinFindMaList:
        if maData['coin_ticker'] == coin_ticker:
            #pprint.pprint(maData)
            if maData['RevenueRate'] > 0:
                small_ma,big_ma = maData['ma_str'].split()
            break

    print(small_ma, big_ma)

    df['small_ma'] = df['close'].rolling(int(small_ma)).mean()
    df['big_ma'] = df['close'].rolling(int(big_ma)).mean()
    
    PrevClosePrice = df['close'].iloc[-2]
    df.dropna(inplace=True) #데이터 없는건 날린다!
    

    if coin_ticker not in CoinInvestList:
        if (PrevClosePrice >= df['small_ma'].iloc[-2] and df['small_ma'].iloc[-3] <= df['small_ma'].iloc[-2]) and (PrevClosePrice >= df['big_ma'].iloc[-2] and df['big_ma'].iloc[-3] <= df['big_ma'].iloc[-2]):
            Invest_1d_Rate = 0.5
            
            CoinInvestList.append(coin_ticker)
                    
            #파일에 저장
            with open(invest_file_path, 'w') as outfile:
                json.dump(CoinInvestList, outfile)
            
            Rebalance_coin.append(coin_ticker)
            Is_Rebalance_Go = True
            
    if coin_ticker in CoinInvestList and myBithumb.IsHasCoin(balances,coin_ticker) == True and myBithumb.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney:
        Invest_1d_Rate = 0.5
        if (PrevClosePrice < df['small_ma'].iloc[-2] and df['small_ma'].iloc[-3] > df['small_ma'].iloc[-2]) or (PrevClosePrice < df['big_ma'].iloc[-2] and df['big_ma'].iloc[-3] > df['big_ma'].iloc[-2]):
            Invest_1d_Rate = 0

            CoinInvestList.remove(coin_ticker)
            #파일에 저장
            with open(invest_file_path, 'w') as outfile:
                json.dump(CoinInvestList, outfile)
                
            Rebalance_coin.append(coin_ticker)
            Is_Rebalance_Go = True
                
    ####################################################################################################
    ####################################################################################################
    ####################################################################################################
    
    time.sleep(0.2)
    df = myBithumb.GetOhlcv(coin_ticker,'4h',300)
    small_ma = coin_info['small_ma']
    big_ma = coin_info['big_ma']
    
    #일봉 기준 이평선 가져오기!
    for maData in CoinFindMa4hList:
        if maData['coin_ticker'] == coin_ticker:
            #pprint.pprint(maData)
            if maData['RevenueRate'] > 0:
                small_ma,big_ma = maData['ma_str'].split()
            break


    df['small_ma'] = df['close'].rolling(int(small_ma)).mean()
    df['big_ma'] = df['close'].rolling(int(big_ma)).mean()
    
    PrevClosePrice = df['close'].iloc[-2]
    df.dropna(inplace=True) #데이터 없는건 날린다!
    

    if coin_ticker not in CoinInvest_4h_List:
        if (PrevClosePrice >= df['small_ma'].iloc[-2] and df['small_ma'].iloc[-3] <= df['small_ma'].iloc[-2]) and (PrevClosePrice >= df['big_ma'].iloc[-2] and df['big_ma'].iloc[-3] <= df['big_ma'].iloc[-2]):
            Invest_4h_Rate = 0.5
            
            CoinInvest_4h_List.append(coin_ticker)
                    
            #파일에 저장
            with open(invest_4h_file_path, 'w') as outfile:
                json.dump(CoinInvest_4h_List, outfile)
                
            Rebalance_coin.append(coin_ticker)
            Is_Rebalance_Go = True
            
    if coin_ticker in CoinInvest_4h_List and myBithumb.IsHasCoin(balances,coin_ticker) == True and myBithumb.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney:
        Invest_4h_Rate = 0.5
        if (PrevClosePrice < df['small_ma'].iloc[-2] and df['small_ma'].iloc[-3] > df['small_ma'].iloc[-2]) or (PrevClosePrice < df['big_ma'].iloc[-2] and df['big_ma'].iloc[-3] > df['big_ma'].iloc[-2]):
            Invest_4h_Rate = 0

            CoinInvest_4h_List.remove(coin_ticker)
            #파일에 저장
            with open(invest_4h_file_path, 'w') as outfile:
                json.dump(CoinInvest_4h_List, outfile)
                
            Rebalance_coin.append(coin_ticker)
            Is_Rebalance_Go = True
    ####################################################################################################
    ####################################################################################################
    ####################################################################################################
    
    asset['coin_target_rate'] = coin_info['invest_rate'] * (Invest_1d_Rate +  Invest_4h_Rate)
    asset['coin_rebalance_amt'] = 0  #리밸런싱 수량

    

    print(coin_ticker, "일봉 기준으로 세팅된 투자 비중:", Invest_1d_Rate)
    print(coin_ticker, "4시간봉 기준으로 세팅된 투자 비중:", Invest_4h_Rate)
    print(coin_ticker, "최종 투자 비중:", (Invest_1d_Rate +  Invest_4h_Rate), ", 포트폴리오 대비 투자 비중:",asset['coin_target_rate'])
    
    '''
    NowCoinTotalMoney = myBithumb.GetCoinNowRealMoney(balances,coin_ticker)
    
    if myBithumb.IsHasCoin(balances,coin_ticker) == True and NowCoinTotalMoney>= minmunMoney:
        
        TargetTotalMoney = InvestTotalMoney * 0.995

        #현재 코인의 총 매수금액
        
        
        print(NowCoinTotalMoney, " / ", TargetTotalMoney)

        Rate = NowCoinTotalMoney / TargetTotalMoney
        print("--------------> coin_ticker rate : ", Rate, asset['coin_target_rate'] )

        
        #코인 목표 비중과 현재 비중이 다르다.
        if Rate != asset['coin_target_rate']:

            #갭을 구한다!!!
            GapRate =  asset['coin_target_rate'] - Rate
            print("--------------> coin_ticker Gaprate : ", GapRate)


            GapMoney = TargetTotalMoney * abs(GapRate)
            
            if GapMoney >= minmunMoney and abs(GapRate) >= (asset['coin_target_rate'] / 10.0): 
                
                print(coin_ticker, "목표 비중에 10%이상 차이가 발생하여 리밸런싱!!")
                
                Rebalance_coin.append(coin_ticker)
                Is_Rebalance_Go = True
    '''
                
    
    print("일봉 기준 매수 코인..")
    print(CoinInvestList)
    print("4h 기준 매수 코인..")
    print(CoinInvest_4h_List)
    
    
    MyPortfolioList.append(asset)





Rebalance_coin = list(set(Rebalance_coin)) #중복제거

strResult = "-- 현재 포트폴리오 상황 --\n"

#매수된 자산의 총합!
total_coin_money = 0

#현재 평가금액 기준으로 각 자산이 몇 주씩 매수해야 되는지 계산한다 (포트폴리오 비중에 따라) 이게 바로 리밸런싱 목표치가 됩니다.
for coin_info in MyPortfolioList:

    #내코인 코드
    coin_ticker = coin_info['coin_ticker']
    

    #현재가!
    CurrentPrice = myBithumb.GetCurrentPrice(coin_ticker)
    time.sleep(0.2)



 

    print("##### coin_ticker: ", coin_ticker)

    
    #매수할 자산 보유할 자산의 비중을 넣어준다!
    coin_target_rate = float(coin_info['coin_target_rate']) 


        
    coin_eval_totalmoney = myBithumb.GetCoinNowRealMoney(balances,coin_ticker)
        
    #코인의 총 평가금액을 더해준다
    total_coin_money += coin_eval_totalmoney

    #현재 비중
    coin_now_rate = 0
    coin_amt = myBithumb.GetCoinAmount(balances,coin_ticker)
    
    
    #잔고에 있는 경우 즉 이미 매수된 코인의 경우
    if myBithumb.IsHasCoin(balances,coin_ticker) == True:


        coin_now_rate = round((coin_eval_totalmoney / InvestTotalMoney),3)

        print("---> NowRate:", round(coin_now_rate * 100.0,2), "%")
        
        if coin_ticker in Rebalance_coin:

            if coin_target_rate == 0:
                
                
                
                coin_info['coin_rebalance_amt'] = -coin_amt
                print("!!!!!!!!! SELL")
                
            else:
                #목표한 비중이 다르다면!!
                if coin_now_rate != coin_target_rate:


                    #갭을 구한다!!!
                    GapRate = coin_target_rate - coin_now_rate


                    #그래서 그 갭만큼의 금액을 구한다
                    GapMoney = InvestTotalMoney * abs(GapRate) 
                    #현재가로 나눠서 몇주를 매매해야 되는지 계산한다
                    GapAmt = GapMoney / CurrentPrice


                    #갭이 음수라면! 비중이 더 많으니 팔아야 되는 상황!!! 
                    if GapRate < 0:

                        coin_info['coin_rebalance_amt'] = -GapAmt

                    #갭이 양수라면 비중이 더 적으니 사야되는 상황!
                    else:  
                        coin_info['coin_rebalance_amt'] = GapAmt




    #잔고에 없는 경우
    else:

        if coin_ticker in Rebalance_coin:
            print("---> NowRate: 0%")
            if coin_target_rate > 0:
                
            
                # 비중대로 매수할 총 금액을 계산한다 
                BuyMoney = InvestTotalMoney * coin_target_rate


                #매수할 수량을 계산한다!
                BuyAmt = BuyMoney / CurrentPrice


                coin_info['coin_rebalance_amt'] = BuyAmt


        
        
        
        

    #메시지랑 로그를 만들기 위한 문자열 
    line_data = (">> " + coin_ticker + " << \n비중: " + str(round(coin_now_rate * 100.0,2)) + "/" + 
                 str(round(coin_target_rate * 100.0,2)) + "% \n총평가금액: " + 
                 str(round(coin_eval_totalmoney,2)) + "\n현재보유수량: " + 
                 str(coin_amt) + "\n리밸런싱수량: " + 
                 str(coin_info['coin_rebalance_amt']))
    
    # 코인을 보유하고 있을 때만 수익률 표시
    if myBithumb.IsHasCoin(balances,coin_ticker) and myBithumb.GetCoinNowRealMoney(balances,coin_ticker) >= minmunMoney:
        revenue_rate = myBithumb.GetRevenueRate(balances,coin_ticker)
        line_data += "\n수익률: " + str(round(revenue_rate,2)) + "%"
        
    line_data += "\n----------------------\n"


    if Is_Rebalance_Go == True:
        line_alert.SendMessage(line_data)
    strResult += line_data



##########################################################

print("--------------리밸런싱 해야 되는 수량-------------")

data_str = "\n" + PortfolioName + "\n" +  strResult + "\n포트폴리오할당금액: " + str(round(InvestTotalMoney,2)) + "\n매수한자산총액: " + str(round(total_coin_money,2))

#결과를 출력해 줍니다!
print(data_str)


if Is_Rebalance_Go == True:
    line_alert.SendMessage("\n포트폴리오할당금액: " + str(round(InvestTotalMoney,2)) + "\n매수한자산총액: " + str(round(total_coin_money,2)))




print("--------------------------------------------")


#'''
#리밸런싱이 가능한 상태
if Is_Rebalance_Go == True:

    line_alert.SendMessage(PortfolioName + " 리밸런싱 시작!!")

    print("------------------리밸런싱 시작  ---------------------")


    print("--------------매도 (리밸런싱 수량이 마이너스인거)---------------------")

    for coin_info in MyPortfolioList:

        #내코인 코드
        coin_ticker = coin_info['coin_ticker']
        rebalance_amt = coin_info['coin_rebalance_amt']

        #리밸런싱 수량이 마이너스인 것을 찾아 매도 한다!
        if rebalance_amt < 0:
            
            #매도 전 수익률 계산
            revenue_rate = myBithumb.GetRevenueRate(balances,coin_ticker)
            
            balances = myBithumb.SellCoinMarket(coin_ticker,abs(rebalance_amt))
            
            line_alert.SendMessage(PortfolioName + " " + coin_ticker + " " + str(abs(rebalance_amt))+ "개 매도! 수익률:" + str(round(revenue_rate,2)) + "%")
            



    print("--------------------------------------------")


    print("--------------매수 ---------------------")

    for coin_info in MyPortfolioList:

        #내코인 코드
        coin_ticker = coin_info['coin_ticker']
        rebalance_amt = coin_info['coin_rebalance_amt']

        #리밸런싱 수량이 플러스인 것을 찾아 매수 한다!
        if rebalance_amt > 0:
                    
            CurrentPrice = myBithumb.GetCurrentPrice(coin_ticker)
            
            BuyMoney = abs(rebalance_amt) * CurrentPrice
            
            #거래대금 제한 로직 추가
            Value10Ma = coin_info['value10ma']
            if BuyMoney > Value10Ma / limitDiv:
                BuyMoney = Value10Ma / limitDiv

            #원화 잔고를 가져온다
            won = myBithumb.GetCoinAmount(balances,"KRW")
            print("# Remain Won :", won)
            time.sleep(0.004)
            
            #
            if BuyMoney > won:
                BuyMoney = won * 0.99 #수수료 및 슬리피지 고려


            if BuyMoney >= minmunMoney:

                balances = myBithumb.BuyCoinMarket(coin_ticker,BuyMoney)

                line_alert.SendMessage(PortfolioName + " " + coin_ticker + " " + str(abs(rebalance_amt))+ "개 매수!")
            


    line_alert.SendMessage(PortfolioName + "  리밸런싱 완료!!")
    print("------------------리밸런싱 끝---------------------")

#'''