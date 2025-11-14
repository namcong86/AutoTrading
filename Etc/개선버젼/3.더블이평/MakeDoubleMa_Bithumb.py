#-*-coding:utf-8 -*-
'''

!!!!! 다운로드 한 코드를 어딘가에 공개하거나 공유하는 것은 범죄 행위입니다. 유의해 주세요!!!!!!

매월 자동매매 계좌 공개를 하고 있어요!
https://m.site.naver.com/1ojdd

참고하세요 :)

'''
import myBithumb
import time

import pandas as pd
import pprint

import line_alert
import json


#이평선 정보를 저장할 리스트
CoinFindMaList = list()

#파일 경로입니다.
#coinfindma_file_path = "./FindDoubleMaList_Bithumb.json" #내 PC에서 체크 할때 
coinfindma_file_path = "/var/autobot/FindDoubleMaList_Bithumb.json" #서버에 업로드 할 때!

try:
    #이 부분이 파일을 읽어서 리스트에 넣어주는 로직입니다. 
    with open(coinfindma_file_path, 'r') as json_file:
        CoinFindMaList = json.load(json_file)

except Exception as e:
    #처음에는 파일이 존재하지 않을테니깐 당연히 예외처리가 됩니다!
    print("Exception by First")


CoinFindMaList.clear()

msg = "빗썸 더블 이동평균 최적 이평선 계산 시작!!"
print(msg)
line_alert.SendMessage(msg)


GetCount = 700 #최대 이평선이 200일선이므로 200개가 드랍된다고 가정하면 700을 넣어야 500개의 데이터를 사용할 수 있다!
CutCount = 0


Tickers = ["KRW-BTC","KRW-ETH"]


for ticker in Tickers:
    
    
    InvestTotalMoney = 1000000

    RealTotalList = list()

    df_data = dict() #일봉 데이타를 저장할 구조

    InvestCoinList = list()

    InvestDataDict = dict()
    InvestDataDict['ticker'] = ticker
    InvestCoinList.append(InvestDataDict)
    
    

    W_ticker = ticker
    for coin_data in InvestCoinList:

        coin_ticker = coin_data['ticker']

        ##########################################################################################################

        #일봉 정보를 가지고 온다!
        df = myBithumb.GetOhlcv(coin_ticker,'1d',GetCount+2)


        ############# 이동평균선! ###############
        ma_dfs = []

        # 이동 평균 계산
        for ma in range(3, 201):
            ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
            ma_dfs.append(ma_df)

        # 이동 평균 데이터 프레임을 하나로 결합
        ma_df_combined = pd.concat(ma_dfs, axis=1)

        # 원본 데이터 프레임과 결합
        df = pd.concat([df, ma_df_combined], axis=1)
        ########################################

        df.dropna(inplace=True) #데이터 없는건 날린다!


        df = df[:len(df)-CutCount]



        df_data[coin_ticker] = df


    
    
    for ma1 in range(3,21):
        for ma2 in range(20,201):

            if ma1 < ma2 :


                ResultList = list()


                for coin_data in InvestCoinList:

                    coin_ticker = coin_data['ticker']
                    
                    #print("\n----coin_ticker: ", coin_ticker)

                    InvestMoney = InvestTotalMoney 
                    #'''
                ##########################################################################################################


                    #print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

                    df = df_data[coin_ticker]                    

                    IsBuy = False #매수 했는지 여부
                    BUY_PRICE = 0  #매수한 가격! 

                    TryCnt = 0      #매매횟수
                    SuccesCnt = 0   #익절 숫자
                    FailCnt = 0     #손절 숫자


                    fee = 0.0015 #수수료를 매수매도마다 0.05%로 세팅!

                    IsFirstDateSet = False
                    FirstDateStr = ""
                    FirstDateIndex = 0


                    TotalMoneyList = list()

                    #'''

                    for i in range(len(df)):


                        if i >= 1:
                            
                            NowOpenPrice = df['open'].iloc[i]    
                            PrevOpenPrice = df['open'].iloc[i-1] 
                            PrevClosePrice = df['close'].iloc[i-1]  
                            
                            
                            #매수 상태!
                            if IsBuy == True:

                                #투자금의 등락률을 매일 매일 반영!
                                InvestMoney = InvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))
                                            
                            
                                if (PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and df[str(ma1)+'ma'].iloc[i-2] > df[str(ma1)+'ma'].iloc[i-1])  or (PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and df[str(ma2)+'ma'].iloc[i-2] > df[str(ma2)+'ma'].iloc[i-1]):  #데드 크로스!


                                    #진입(매수)가격 대비 변동률
                                    Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                                    RevenueRate = (Rate - fee)*100.0 #수익률 계산

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
                                    #print("\n\n")

                                    TryCnt += 1 #매매 횟수

                                    if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                                        SuccesCnt += 1 #성공
                                    else:
                                        FailCnt += 1 #실패


                                    IsBuy = False #매도했다

                            #아직 매수전 상태
                            if IsBuy == False:

                                #단기 이동평균선이 장기 이동평균선보다 크고 단기 이동평균선이 증가중일 경우! 매수한다!!
                                if i >= 2 and PrevClosePrice >= df[str(ma1)+'ma'].iloc[i-1] and df[str(ma1)+'ma'].iloc[i-2] <= df[str(ma1)+'ma'].iloc[i-1]  and PrevClosePrice >= df[str(ma2)+'ma'].iloc[i-1] and df[str(ma2)+'ma'].iloc[i-2] <= df[str(ma2)+'ma'].iloc[i-1] :  #골든 크로스!

                                    BUY_PRICE = NowOpenPrice  #매수가격은 시가로 가정!

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
                                    IsBuy = True #매수했다

            
                        TotalMoneyList.append(InvestMoney)  #투자금 변경이력을 리스트에 저장!

                    #####################################################
                    #####################################################
                    #####################################################
                    #'''
    

                    #결과 정리 및 데이터 만들기!!
                    if len(TotalMoneyList) > 0:

                        resultData = dict()

                        
                        resultData['Ticker'] = coin_ticker


                        result_df = pd.DataFrame({ "Total_Money" : TotalMoneyList}, index = df.index)

                        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
                        result_df['Cum_Ror'] = result_df['Ror'].cumprod()

                        result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
                        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
                        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

                        #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                        #pprint.pprint(result_df)
                        #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                        resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

                        resultData['OriMoney'] = result_df['Total_Money'].iloc[FirstDateIndex]
                        resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
                        resultData['OriRevenueHold'] =  (df['open'].iloc[-1]/df['open'].iloc[FirstDateIndex] - 1.0) * 100.0 
                        resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
                        resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

                        resultData['TryCnt'] = TryCnt
                        resultData['SuccesCnt'] = SuccesCnt
                        resultData['FailCnt'] = FailCnt

                        
                        ResultList.append(resultData)



                        #for idx, row in result_df.iterrows():
                        #    print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
                            



                #데이터를 보기좋게 프린트 해주는 로직!
                #print("\n\n--------------------")
                TotalOri = 0
                TotalFinal = 0
                TotalHoldRevenue = 0
                TotalMDD= 0

                InvestCnt = float(len(ResultList))

                for result in ResultList:

                    '''
                    print("--->>>",result['DateStr'],"<<<---")
                    print(result['Ticker'] )
                    print("최초 금액: ", round(result['OriMoney'],2) , " 최종 금액: ", round(result['FinalMoney'],2))
                    print("수익률:", round(result['RevenueRate'],2) , "%")
                    print("단순 보유 수익률:", round(result['OriRevenueHold'],2) , "%")
                    print("MDD:", round(result['MDD'],2) , "%")

                    if result['TryCnt'] > 0:
                        print("성공:", result['SuccesCnt'] , " 실패:", result['FailCnt']," -> 승률: ", round(result['SuccesCnt']/result['TryCnt'] * 100.0,2) ," %")
                    '''
                    TotalOri += result['OriMoney']
                    TotalFinal += result['FinalMoney']

                    TotalHoldRevenue += result['OriRevenueHold']
                    TotalMDD += result['MDD']

                    #print("\n--------------------\n")

                if TotalOri >= 0:

                    if len(df_data[coin_ticker]) >= 2:
                        #'''
                        print("############ 전체기간 ##########")
                                                    
                        print("-- ma1", ma1, " -- ma2 : ", ma2)
                        print("---------- 총 결과 ----------")
                        print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", format(round(((TotalFinal - TotalOri) / TotalOri) * 100,2),',') ,"% (단순보유수익률:" ,format(round(TotalHoldRevenue/InvestCnt,2),',') ,"%) 평균 MDD:",  round(TotalMDD/InvestCnt,2),"%")
                        print("------------------------------")
                        print("####################################")
                        #'''

                        ResultData = dict()

                        ResultData['coin_ticker'] = result['Ticker'] 
                        ResultData['ma_str'] = str(ma1) + " " + str(ma2) 
                        ResultData['RevenueRate'] = round(((TotalFinal - TotalOri) / TotalOri) * 100,2)
                        ResultData['MDD'] = round(TotalMDD/InvestCnt,2)


                        RealTotalList.append(ResultData)
                    else:
                    
                        '''
                        print("############ 전체기간 ##########")
                                                    
                        print("-- ma1", ma1, " -- ma2 : ", ma2)
                        '''

                        ResultData = dict()

                        ResultData['coin_ticker'] = W_ticker
                        ResultData['ma_str'] = "0 0"
                        ResultData['RevenueRate'] = 0
                        ResultData['MDD'] = 0


                        RealTotalList.append(ResultData)

                ResultList.clear()









    df_all = pd.DataFrame(RealTotalList)
        
    
    if len(df_all) > 0:

        df_all['RevenueRate_rank'] = df_all['RevenueRate'].rank(ascending=True)
        df_all['MDD_rank'] = df_all['MDD'].rank(ascending=True)
        df_all['Score'] = df_all['RevenueRate_rank'] + df_all['MDD_rank']

        df_all = df_all.sort_values(by="Score",ascending=False)

    #'''
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    pprint.pprint(df_all.iloc[0])
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    #'''

    RealTotalList.clear()
    
    
    
    if len(df_all) > 0:
        CoinFindMaList.append(df_all.iloc[0].to_dict())

        #파일에 리스트를 저장합니다
        with open(coinfindma_file_path, 'w') as outfile:
            json.dump(CoinFindMaList, outfile)
        time.sleep(0.2)
    
    InvestCoinList.clear()
        
print("----End----")

msg = "빗썸 더블 이동평균 최적 이평선 계산 끝!!"
print(msg)
line_alert.SendMessage(msg)


pprint.pprint(CoinFindMaList)

st_ma_all = ""
for finddata in CoinFindMaList:
    st_ma = finddata['coin_ticker'] + " Ma:" + finddata['ma_str'] + " Revenue:" + str(finddata['RevenueRate']) + "% MDD:" + str(finddata['MDD']) + "\n"
    st_ma_all += st_ma
    
time.sleep(0.2)

msg = st_ma_all
print(msg)
line_alert.SendMessage(msg)

