#-*-coding:utf-8 -*-
'''

KrStock_Get_DateGugan_T.py에서 구한 값을 기반으로 테스팅!!!

관련 포스팅

연복리 25%의 코스닥 지수 양방향 매매 전략!
https://blog.naver.com/zacra/223078498415

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^




'''
import KIS_Common as Common

import pandas as pd
import pprint
import json

#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL




#이렇게 직접 금액을 지정해도 된다!!
TotalMoney = 10000000

print("테스트하는 총 금액: ", format(round(TotalMoney), ','))


InvestStockList = ['233740','251340'] #KODEX 코스닥150레버리지,  KODEX 코스닥150선물인버스

InverseStockCode = '251340' # KODEX 코스닥150선물인버스


InvestStockList = list()

InvestDataDict = dict()
InvestDataDict['ticker'] = "233740" # KODEX 코스닥150레버리지
InvestDataDict['rate'] = 0.7
InvestStockList.append(InvestDataDict)

InvestDataDict = dict()
InvestDataDict['ticker'] = "251340" # KODEX 코스닥150선물인버스
InvestDataDict['rate'] = 0.3
InvestStockList.append(InvestDataDict)




InvestTotalMoney = 5000000 #그냥 5백만원으로 박아서 테스팅 해보기!!!

RealTotalList = list()

df_data = dict() #일봉 데이타를 저장할 구조



StCount = 0
EnCount = 0


#KrStock_Get_DateGugan_T.py에서 구한 값으로 아래 상승장,횡보장,하락장을 채운다!!!!
#전체,상승,횡보,상승장 구간의 성과를 모두 구한다!
for GUBUN in range(1,5):

    if GUBUN == 2: #상승장
        StCount = 1630
        EnCount = 1290
    elif GUBUN == 3: #횡보장
        StCount = 610
        EnCount = 320
    elif GUBUN == 4: #하락장
        StCount = 380
        EnCount = 130
    else: #전체기간
        StCount = 1645
        EnCount = 0

    for stock_data in InvestStockList:

        stock_code = stock_data['ticker']
        df = Common.GetOhlcv("KR",stock_code, StCount)

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
        for ma in range(3,31):
            df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()

        ########################################

        df.dropna(inplace=True) #데이터 없는건 날린다!


        df = df[:len(df)-EnCount]



        pprint.pprint(df)


        df_data[stock_code] = df




    DivNum = 0
    target_period = 0

    for ma1 in range(3,6):
        for ma2 in range(3,11):
            for ma3 in range(3,21):

                if ma1 < ma2 < ma3:


                    ResultList = list()


                    TotalResultDict= dict()
                    for stock_data in InvestStockList:

                        stock_code = stock_data['ticker']


                        InvestMoney = TotalMoney * stock_data['rate']
        
                        df = df_data[stock_code]                    

                        IsBuy = False #매수 했는지 여부
                        BUY_PRICE = 0  #매수한 가격! 

                        TryCnt = 0      #매매횟수
                        SuccesCnt = 0   #익절 숫자
                        FailCnt = 0     #손절 숫자


                        fee = 0.0015 #수수료를 매수매도마다 0.15%로 세팅!

                        IsFirstDateSet = False
                        FirstDateStr = ""
                        FirstDateIndex = 0


                        TotalMoneyList = list()

                        for i in range(len(df)):


                            NowOpenPrice = df['open'].iloc[i]  
                            PrevOpenPrice = df['open'].iloc[i-1]  
                            PrevClosePrice = df['close'].iloc[i-1]
                            

                            DateStr = str(df.iloc[i].name)

                            Isheaven = False

                            #11-4 천국 상승장에는 
                            if '-11-' in DateStr or '-12-' in DateStr  or '-01-' in DateStr  or '-02-' in DateStr or '-03-' in DateStr  or '-04-' in DateStr:
                                Isheaven = True


                            
                            if IsBuy == True:

                                #투자중이면 매일매일 수익률 반영!
                                InvestMoney = InvestMoney * (1.0 + ((NowOpenPrice - PrevOpenPrice) / PrevOpenPrice))

                                IsSellGo = False
                                




                                if InverseStockCode == stock_code: #인버스

                                    #인버스에서 11-4는 지옥일테니깐
                                    if Isheaven == True:

                                        #30일선 아래면 or 조건으로 이평조건 하나만 불만족해도 팔아 재낀다
                                        if PrevClosePrice < df['30ma'].iloc[i-1] :
                                            if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                                IsSellGo = True 

                                        #30일선 위라면 기존대로..
                                        else:
                                            if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                                IsSellGo = True

                                    #인버스에서 5-10 기간은 천국일테니깐 잘 안팔게 and로 유지
                                    else:
                                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                            IsSellGo = True


                                else: # 2배 레버리지 

                                    #11-4천국에는 레버리지는 잘 안팔게 and로 유지
                                    if Isheaven == True:
                                        if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                            IsSellGo = True

                                    #레버리지에서 5-10 기간은 지옥이니깐 
                                    else:
                                        #하락장이면 or로 팔아재낀다.
                                        if PrevClosePrice < df['30ma'].iloc[i-1] and df['30ma'].iloc[i-2] > df['30ma'].iloc[i-1]  and df[str(ma1)+'ma'].iloc[i-1] < df[str(ma2)+'ma'].iloc[i-1] < df[str(ma3)+'ma'].iloc[i-1]  :
                                            if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] or PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                                IsSellGo = True 

                                        #아닐 경우는 and로 유지
                                        else:
                                            if  PrevClosePrice < df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma2)+'ma'].iloc[i-1] and PrevClosePrice < df[str(ma3)+'ma'].iloc[i-1] : 
                                                IsSellGo = True


                                            
                                
                                if IsSellGo == True:  #데드 크로스!

                                    #진입(매수)가격 대비 변동률
                                    Rate = (NowOpenPrice - BUY_PRICE) / BUY_PRICE

                                    RevenueRate = (Rate - fee)*100.0 #수익률 계산

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(stock_name, "(",stock_code, ") ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매도!  수익률: ", round(RevenueRate,2) , "%", " ,종목 잔고:", round(InvestMoney,2)  , " ", df['open'].iloc[i])
                                    #print("\n\n")


                                    TryCnt += 1

                                    if RevenueRate > 0: #수익률이 0보다 크다면 익절한 셈이다!
                                        SuccesCnt += 1
                                    else:
                                        FailCnt += 1


                                    IsBuy = False #매도했다

                            if IsBuy == False and i >= 2:

                                if IsFirstDateSet == False:
                                    FirstDateStr = df.iloc[i].name
                                    FirstDateIndex = i-1
                                    IsFirstDateSet = True


                                IsBuyGo = False




                                if InverseStockCode == stock_code: #인버스

                                    #11-4 천국에는 인버스는 타이트하게 잡는다!
                                    if Isheaven == True:
                                        if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                                            if PrevClosePrice > df['30ma'].iloc[i-1] and df['30ma'].iloc[i-2] < df['30ma'].iloc[i-1]  and df[str(ma1)+'ma'].iloc[i-1] > df[str(ma2)+'ma'].iloc[i-1] > df[str(ma3)+'ma'].iloc[i-1] :
                                                IsBuyGo = True
                                    else:
                                        #10-5 지옥에는 인버스는 살짝 느슨하게 잡는다.
                                        if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                                            if df['30ma'].iloc[i-2] < df['30ma'].iloc[i-1] :
                                                IsBuyGo = True

                                else: #레버리지 

                                    #11-4 천국에는 레버리지는 기존 조건 만족하면 잡는다.
                                    if Isheaven == True:
                                        if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                                            IsBuyGo = True
                                    
                                    else:
                                        #10-5 지옥에는 레버리지는 살짝 타이트하게 잡는다.
                                        if PrevClosePrice > df[str(ma1)+'ma'].iloc[i-1] and PrevClosePrice > df[str(ma2)+'ma'].iloc[i-1]  and PrevClosePrice > df[str(ma3)+'ma'].iloc[i-1] :
                                            if PrevClosePrice > df['30ma'].iloc[i-1]  :
                                                IsBuyGo = True

                            



                                if IsBuyGo == True:  #골든 크로스!


                                    BUY_PRICE = NowOpenPrice 

                                    InvestMoney = InvestMoney * (1.0 - fee)  #수수료 및 세금, 슬리피지 반영!

                                    #print(stock_name, "(",stock_code, ") ", df.iloc[i].name, " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,종목 잔고:", round(InvestMoney,2) , " ", df['open'].iloc[i])
                                    IsBuy = True #매수했다

                            
                            TotalMoneyList.append(InvestMoney)

                            

                        #결과 정리 및 데이터 만들기!!
                        if len(TotalMoneyList) > 0:



                            TotalResultDict[stock_code] = TotalMoneyList

                            resultData = dict()



                            
                            resultData['Ticker'] = stock_code
                            #resultData['TickerName'] = stock_name


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
     
                    TotalHoldRevenue = 0


                    InvestCnt = float(len(ResultList))

                    for result in ResultList:


                        #print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")
                        TotalHoldRevenue += result['OriRevenueHold']
   
                        #print("\n--------------------\n")



                    if len(ResultList) > 0:
                        print("####################################")
                        

                        # 딕셔너리의 리스트들의 길이를 가져옴
                        length = len(list(TotalResultDict.values())[0])

                        # 종합 리스트 초기화
                        FinalTotalMoneyList = [0] * length

                        # 딕셔너리에서 리스트를 가져와 합산
                        for my_list in TotalResultDict.values():
                            # 리스트의 각 요소를 합산
                            for i, value in enumerate(my_list):
                                FinalTotalMoneyList[i] += value


                                
                        result_df = pd.DataFrame({ "Total_Money" : FinalTotalMoneyList}, index = df.index)

                        result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
                        result_df['Cum_Ror'] = result_df['Ror'].cumprod()

                        result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
                        result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
                        result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
                        #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                        #print("len(result_df): ", len(result_df))
                        #for idx, row in result_df.iterrows():
                        #    print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
                            


                        #print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

                        TotalOri = result_df['Total_Money'].iloc[1]
                        TotalFinal = result_df['Total_Money'].iloc[-1]

                        TotalMDD = result_df['MaxDrawdown'].min() * 100.0




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
                        print("최초 금액:", str(format(round(TotalOri), ','))  , " 최종 금액:", str(format(round(TotalFinal), ',')), "\n수익률:", format(round(((TotalFinal - TotalOri) / TotalOri) * 100,2),',') ,"% (단순보유수익률:" ,format(round(TotalHoldRevenue/InvestCnt,2),',') ,"%) 평균 MDD:",  round(TotalMDD,2),"%")
                        print("------------------------------")
                        print("####################################")

                        ResultData = dict()

                        ResultData['ma_str'] = str(ma1) + " " + str(ma2) + " " + str(ma3)
                        ResultData['RevenueRate'] = round(((TotalFinal - TotalOri) / TotalOri) * 100,2)
                        ResultData['MDD'] = round(TotalMDD,2)


                        RealTotalList.append(ResultData)

                    ResultList.clear()





    print("\n\n>>>>>>>>>>>>>수익률 높은 순으로!<<<<<<<<<<<")

    test_file_path = ""

    if GUBUN == 2: #상승장
        test_file_path = "/var/autobot/BackTest_Up_krstock.json"
        print("############ 상승장 ##########")
    elif GUBUN == 3: #횡보장
        test_file_path = "/var/autobot/BackTest_Wave_krstock.json"
        print("############ 횡보장 ##########")
    elif GUBUN == 4: #하락장
        test_file_path = "/var/autobot/BackTest_Down_krstock.json"
        print("############ 하락장 ##########")
    else: #전체기간
        test_file_path = "/var/autobot/BackTest_All_krstock.json"
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
