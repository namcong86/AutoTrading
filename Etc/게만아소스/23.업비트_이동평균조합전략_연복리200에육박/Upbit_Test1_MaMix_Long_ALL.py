#-*-coding:utf-8 -*-
'''

Upbit_Get_DateGugan_T.py에서 구한 값을 기반으로 테스팅!!!

관련 포스팅

연복리 200에 가까운 이평조합 전략!
https://blog.naver.com/zacra/223074617299

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^



'''

import pyupbit

import pandas as pd
import pprint
import json



InvestTotalMoney = 5000000 #그냥 5백만원으로 박아서 테스팅 해보기!!!

RealTotalList = list()

df_data = dict() #일봉 데이타를 저장할 구조



######################################## 1. 균등 분할 투자 ###########################################################
#InvestCoinList = ["KRW-BTC","KRW-ETH",'KRW-ADA','KRW-DOT','KRW-POL']
##########################################################################################################


######################################## 2. 차등 분할 투자 ###################################################
#'''
InvestCoinList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-BTC"
InvestDataDict['rate'] = 0.4
InvestCoinList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ETH"
InvestDataDict['rate'] = 0.4
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-ADA"
InvestDataDict['rate'] = 0.1
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-DOT"
InvestDataDict['rate'] = 0.05
InvestCoinList.append(InvestDataDict)


InvestDataDict = dict()
InvestDataDict['ticker'] = "KRW-POL"
InvestDataDict['rate'] = 0.05
InvestCoinList.append(InvestDataDict)
#'''
##########################################################################################################


StCount = 0
EnCount = 0

#Upbit_Get_DateGugan_T.py에서 구한 값으로 아래 상승장,횡보장,하락장을 채운다!!!!

#전체,상승,횡보,상승장 구간의 성과를 모두 구한다!
for GUBUN in range(1,5):

    if GUBUN == 2: #상승장
        StCount = 1150
        EnCount = 730
    elif GUBUN == 3: #횡보장
        StCount = 350
        EnCount = 35
    elif GUBUN == 4: #하락장
        StCount = 570
        EnCount = 290
    else: #전체기간
        StCount = 6000
        EnCount = 0

    ######################################## 1. 균등 분할 투자 ###########################################################
    '''
    for coin_ticker in InvestCoinList:    

    '''
    ##########################################################################################################
    ######################################## 2. 차등 분할 투자 ###################################################
        #'''

    for coin_data in InvestCoinList:

        coin_ticker = coin_data['ticker']
        #'''
    ##########################################################################################################

        #일봉 정보를 가지고 온다!
        df = pyupbit.get_ohlcv(coin_ticker,interval="day",count=StCount, period=0.3)

        ########## RSI 지표 구하는 로직! ##########
        period = 14

        delta = df["close"].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss

        df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
        ########################################

        
        ############# 이동평균선! ###############
        ma_dfs = []

        # 이동 평균 계산
        for ma in range(3, 31):
            ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
            ma_dfs.append(ma_df)

        # 이동 평균 데이터 프레임을 하나로 결합
        ma_df_combined = pd.concat(ma_dfs, axis=1)

        # 원본 데이터 프레임과 결합
        df = pd.concat([df, ma_df_combined], axis=1)
        ########################################

        df.dropna(inplace=True) #데이터 없는건 날린다!


        df = df[:len(df)-EnCount]



        pprint.pprint(df)


        df_data[coin_ticker] = df




    DivNum = 0
    target_period = 0

    for ma1 in range(3,6):
        for ma2 in range(3,11):
            for ma3 in range(3,31):

                if ma1 < ma2 < ma3:


                    ResultList = list()


                    ######################################## 1. 균등 분할 투자 ###########################################################
                    '''
                    for coin_ticker in InvestCoinList:    
                        InvestMoney = InvestTotalMoney / len(InvestCoinList) #테스트 총 금액을 종목 수로 나눠서 각 할당 투자금을 계산한다!
                    '''
                    ##########################################################################################################
                    ######################################## 2. 차등 분할 투자 ###################################################
                        #'''
                    for coin_data in InvestCoinList:

                        coin_ticker = coin_data['ticker']
                        
                        #print("\n----coin_ticker: ", coin_ticker)

                        InvestMoney = InvestTotalMoney * coin_data['rate'] #설정된 투자금에 맞게 투자!
                        #'''
                    ##########################################################################################################


                        #print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)

                        df = df_data[coin_ticker]                    

                        IsBuy = False #매수 했는지 여부
                        BUY_PRICE = 0  #매수한 가격! 

                        TryCnt = 0      #매매횟수
                        SuccesCnt = 0   #익절 숫자
                        FailCnt = 0     #손절 숫자


                        fee = 0.0035 #수수료를 매수매도마다 0.05%로 세팅!

                        #df = df[:len(df)-100] #최근 100거래일을 빼고 싶을 때
                        IsFirstDateSet = False
                        FirstDateStr = ""
                        FirstDateIndex = 0


                        TotlMoneyList = list()

                        #'''
                        #####################################################
                        ##########골든 크로스에서 매수~ 데드크로스에서 매도~!##########
                        #####################################################
                        for i in range(len(df)):


                            NowOpenPrice = df['open'].iloc[i]  
                            PrevOpenPrice = df['open'].iloc[i-1]  
                            PrevClosePrice = df['close'].iloc[i-1]
                            
                            
                            
                            if IsBuy == True:

                                #투자중이면 매일매일 수익률 반영!
                                InvestMoney = InvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))
                                            
                                
                                if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] :  #데드 크로스!


                                    #진입(매수)가격 대비 변동률
                                    Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                                    RevenueRate = (Rate - fee)*100.0 #수익률 계산

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
                                    #print("\n\n")


                                    TryCnt += 1

                                    if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                                        SuccesCnt += 1
                                    else:
                                        FailCnt += 1


                                    IsBuy = False #매도했다

                            if IsBuy == False and i > 20:

                                if IsFirstDateSet == False:
                                    FirstDateStr = df.iloc[i].name
                                    FirstDateIndex = i-1
                                    IsFirstDateSet = True

                                if  PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :  #골든 크로스!


                                    BUY_PRICE = NowOpenPrice 

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(coin_ticker ," ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
                                    IsBuy = True #매수했다

                            
                            TotlMoneyList.append(InvestMoney)

                        #####################################################
                        #####################################################
                        #####################################################
                        #'''
                        
        

                        #결과 정리 및 데이터 만들기!!
                        if len(TotlMoneyList) > 0:

                            resultData = dict()

                            
                            resultData['Ticker'] = coin_ticker


                            result_df = pd.DataFrame({ "Total_Money" : TotlMoneyList}, index = df.index)

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

                    if TotalOri > 0:

                        if GUBUN == 2: #상승장
                            print("############ 상승장 ##########")
                        elif GUBUN == 3: #횡보장
                            print("############ 횡보장 ##########")
                        elif GUBUN == 4: #하락장
                            print("############ 하락장 ##########")
                        else: #전체기간
                            print("############ 전체기간 ##########")
                                                    
                        print("-- ma1", ma1, " -- ma2 : ", ma2, " -- ma3 : ", ma3)
                        print("---------- 총 결과 ----------")
                        print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", format(round(((TotalFinal - TotalOri) / TotalOri) * 100,2),',') ,"% (단순보유수익률:" ,format(round(TotalHoldRevenue/InvestCnt,2),',') ,"%) 평균 MDD:",  round(TotalMDD/InvestCnt,2),"%")
                        print("------------------------------")
                        print("####################################")

                        ResultData = dict()

                        ResultData['ma_str'] = str(ma1) + " " + str(ma2) + " " + str(ma3)
                        ResultData['RevenueRate'] = round(((TotalFinal - TotalOri) / TotalOri) * 100,2)
                        ResultData['MDD'] = round(TotalMDD/InvestCnt,2)


                        RealTotalList.append(ResultData)

                    ResultList.clear()





    print("\n\n>>>>>>>>>>>>>수익률 높은 순으로!<<<<<<<<<<<")

    test_file_path = ""

    if GUBUN == 2: #상승장
        test_file_path = "/var/autobot/BackTest_Up_upbit.json"
        print("############ 상승장 ##########")
    elif GUBUN == 3: #횡보장
        test_file_path = "/var/autobot/BackTest_Wave_upbit.json"
        print("############ 횡보장 ##########")
    elif GUBUN == 4: #하락장
        test_file_path = "/var/autobot/BackTest_Down_upbit.json"
        print("############ 하락장 ##########")
    else: #전체기간
        test_file_path = "/var/autobot/BackTest_All_upbit.json"
        print("############ 전체기간 ##########")


    #파일에 리스트를 저장합니다
    with open(test_file_path, 'w') as outfile:
        json.dump(RealTotalList, outfile)

    df_all = pd.DataFrame(RealTotalList)

    df_all = df_all.sort_values(by="RevenueRate",ascending=False)

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    pprint.pprint(df_all.head(40))
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    RealTotalList.clear()
