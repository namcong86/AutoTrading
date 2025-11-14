'''


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다. 

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504

관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅
https://blog.naver.com/zacra/223281275891

 
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
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime

#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") #REAL or VIRTUAL

##################################################################
#이렇게 직접 금액을 지정
TotalMoney = 10000
FirstInvestMoney = TotalMoney

fee = 0.0025 #수수료+세금+슬리피지를 매수매도마다 0.25%로 세팅!

print("테스트하는 총 금액: ", format(round(TotalMoney), ','))
##################################################################
    
#################################################################
#전략 백테스팅 시작 년도 지정!!!
StartYear = 2017

#RebalanceSt = "%Y" #년도별 리밸런싱
RebalanceSt = "%Y%m" #월별 리밸런싱
#################################################################


TaxAdd = False #양도세 반영 여부!
MoneyForTaxCalc = 0 #양도세 계산을 위한 손익을 저장할 변수
FreeTax = 2100 #환율을 1200원으로 퉁쳐서 $2100 가 면세 기준!

#################################################################


InvestStockList = ["TQQQ","BIL","SCHD"]


StockDataList = list()

for stock_code in InvestStockList:
    print("..",stock_code,"..")
    stock_data = dict()
    stock_data['stock_code'] = stock_code
    stock_data['stock_name'] = stock_code#KisKR.GetStockName(stock_code)

    if stock_code == "TQQQ":
        stock_data['target_rate'] = 0.5
    elif stock_code == "BIL":
        stock_data['target_rate'] = 0.3
    elif stock_code == "SCHD":
        stock_data['target_rate'] = 0.2


    StockDataList.append(stock_data)

pprint.pprint(StockDataList)


def GetTargetRate(stock_code, StockDataList):
    result = 1.0/float(len(StockDataList))
    for stock_data in StockDataList:
        if stock_code == stock_data['stock_code']:
            result = stock_data['target_rate']
            break

    return result


#사실 미국에선 사용하지 않지만 한국에선 유용하니깐 그냥 내비두장~
def GetStockName(stock_code, StockDataList):
    result_str = stock_code
    for stock_data in StockDataList:
        if stock_code == stock_data['stock_code']:
            result_str = stock_data['stock_name']
            break

    return result_str
    


stock_df_list = []

for stock_code in InvestStockList:
    
    #################################################################
    #################################################################
    df = Common.GetOhlcv("US", stock_code,3300) 
    #################################################################
    #################################################################

    df['prevClose'] = df['close'].shift(1)


    df['80ma_Before'] = df['close'].rolling(80).mean().shift(2) 
    df['80ma'] = df['close'].rolling(80).mean().shift(1) 

    df['120ma_Before'] = df['close'].rolling(120).mean().shift(2) 
    df['120ma'] = df['close'].rolling(120).mean().shift(1) 

   
    df.dropna(inplace=True) #데이터 없는건 날린다!

    #df = df[:len(df)-1]
    data_dict = {stock_code: df}


    stock_df_list.append(data_dict)
        
    print("---stock_code---", stock_code , " len ",len(df))
    
    pprint.pprint(df)




#섹터ETF들의 통합 데이터
combined_df = pd.concat([list(data_dict.values())[0].assign(stock_code=stock_code) for data_dict in stock_df_list for stock_code in data_dict])
combined_df.sort_index(inplace=True)
pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))




IsBuy = False #매수 했는지 여부
BUY_PRICE = 0  #매수한 금액! 


IsFirstDateSet = False
FirstDateStr = ""


NowInvestCode = ""
InvestMoney = TotalMoney
RemainInvestMoney = InvestMoney



ResultList = list()

TotalMoneyList = list()

NowInvestList = list() #투자중인 항목의 리스트



i = 0
# Iterate over each date
for date in combined_df.index.unique():
    
    #날짜 정보를 획득
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
            

    i += 1

    IsRebalnceDayforTax = False
    
    #투자중인 종목을 순회하며 처리!
    for investData in NowInvestList:

        stock_code = investData['stock_code'] 
        
    

        stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 


        if len(stock_data) == 1:
    
            #################################################################################################################
            #매일매일의 등락률을 반영한다!
            NowClosePrice = 0
            PrevClosePrice = 0

            NowClosePrice = stock_data['close'].values[0]
            PrevClosePrice = stock_data['prevClose'].values[0] 


            if investData['InvestMoney'] > 0:
                investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((NowClosePrice - PrevClosePrice ) / PrevClosePrice))
            #################################################################################################################


            IsReblanceDay = False
            #################################################################################################################
            #이 부분이 월별 리밸런싱을 가능하게 하는 부분~ 
            if investData['EntryMonth'] != date_object.strftime(RebalanceSt):

                investData['EntryMonth'] = date_object.strftime(RebalanceSt)

                IsReblanceDay = True
                IsRebalnceDayforTax = True

            #################################################################################################################
            

            if IsReblanceDay == True: 

                investData['IsRebalanceGo'] = True


                Rate = 1.0

                #'''
                if stock_data['120ma'].values[0] > stock_data['prevClose'].values[0]:
                    Rate *= 0.5

                if stock_data['80ma_Before'].values[0] > stock_data['80ma'].values[0]:
                    Rate *= 0.5

                
                #'''
            
                TargetRate = GetTargetRate(investData['stock_code'],StockDataList)
                #'''


                investData['InvestRate'] = TargetRate * Rate
                    

        

    if IsRebalnceDayforTax == True:

        if TaxAdd == True:
            #리밸런싱 하는 날이 1월 이라면 양도세를 반영하고 초기화 시켜준다!
            if int(date_object.strftime("%m")) == 1:
                MoneyForTaxCalc -= FreeTax
                

                print("지난 한해 동안 $", MoneyForTaxCalc," 손익확정을 했어요!")
                
                #공제후에도 남은 수익에 대해선 양도세22를 계산해 감산하자!!
                if MoneyForTaxCalc > 0:
                    OMG_Tax = MoneyForTaxCalc * 0.22
                    RemainInvestMoney -= OMG_Tax #남은 투자금에서 감산!!!
                    print(str(date), "--양도세 $",OMG_Tax , "차감 되었어요 ㅠ.ㅜ")
                else:
                    print(str(date), "--양도세 없어요! 불행인지 다행인지...^^")
                    
                    
                MoneyForTaxCalc = 0 #새해가 되었으니 초기화!!
                

    #################################################################################################################
    ##################### 리밸런싱 할때 투자 비중을 맞춰주는 작업 #############################





    
    #월초여서 이미 투자중인 항목의 리밸런싱이 필요한 경우 진행! 먼저 매도부터!
    for investData in NowInvestList:

        if investData['IsRebalanceGo'] == True:

            stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == investData['stock_code'])] 

            if len(stock_data) == 1:

               
    
                InvestMoneyCellForReblanceTargetMoney  = (InvestMoney * investData['InvestRate']) 
    
                GapInvest = InvestMoneyCellForReblanceTargetMoney - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!


                if GapInvest < 0:
                    
                    
                    
                    GapInvest = abs(GapInvest)

                    NowClosePrice = stock_data['close'].values[0]

                    SellAmt = int(GapInvest / NowClosePrice)

                    RealSellMoney = SellAmt * NowClosePrice
                    
                    
                    
                    RevenueRate = (NowClosePrice - investData['AvgPrice']) / investData['AvgPrice'] #손익률을 구한다!


                    #팔아야할 금액이 현재 투자금보다 크다면!!! 모두 판다! 혹은 실제 팔아야할 계산된 금액이 투자금보다 크다면 모두 판다!!
                    if GapInvest > investData['InvestMoney'] or RealSellMoney > investData['InvestMoney'] or investData['InvestRate'] == 0:

                        RealSellMoney = investData['InvestMoney']

                        ReturnMoney = RealSellMoney

                        investData['InvestMoney'] = 0

                        RemainInvestMoney += (ReturnMoney * (1.0 - fee))

                        investData['IsRebalanceGo'] = False
                        

                        investData['AvgPrice'] = 0
                        investData['TotAmt'] = 0
                        
                        #모두 팔때는 매도 금액 x 수익률이 손익금
                        if TaxAdd == True:
                            MoneyForTaxCalc += RealSellMoney * RevenueRate
                        
                        

                        print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 모두 매도!(리밸런싱) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)
                        
                    else:


                        if SellAmt > 0 :

                            ReturnMoney = RealSellMoney

                            investData['InvestMoney'] -= RealSellMoney

                            RemainInvestMoney += (ReturnMoney * (1.0 - fee))

                            investData['IsRebalanceGo'] = False

                            investData['TotAmt'] -= SellAmt

                            #일부 팔때는 (매도금액 x 매도수량) - (평균매입단가 x 매도수량)
                            if TaxAdd == True:
                                MoneyForTaxCalc += (RealSellMoney - (investData['AvgPrice']*SellAmt))
                            
                            print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 일부 매도!(리밸런싱) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)


                        
    #월초여서 이미 투자중인 항목의 리밸런싱이 필요한 경우 진행! 매수!
    for investData in NowInvestList:

        if investData['IsRebalanceGo'] == True: #리밸런싱 마지막 매수단계이니깐
            investData['IsRebalanceGo'] = False #리밸런싱은 무조건 종료!

            

            stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == investData['stock_code'])] 

            if len(stock_data) == 1:




                InvestMoneyCellForReblanceTargetMoney  = (InvestMoney * investData['InvestRate']) 

   
        
                GapInvest = InvestMoneyCellForReblanceTargetMoney - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!


                if GapInvest > 0:
                    GapInvest = abs(GapInvest)

                    NowClosePrice = stock_data['close'].values[0]

                    BuyAmt = int(GapInvest / NowClosePrice)

                    if BuyAmt > 0:


                        NowFee = (BuyAmt*NowClosePrice) * fee

                        #매수해야 되는데 남은돈이 부족하다면 수량을 하나씩 감소시켜 만족할 때 매수한다!!
                        while RemainInvestMoney < (BuyAmt*NowClosePrice) + NowFee:
                            if RemainInvestMoney > NowClosePrice:
                                BuyAmt -= 1
                                NowFee = (BuyAmt*NowClosePrice) * fee
                            else:
                                break
                        
                        if BuyAmt > 0 and RemainInvestMoney > NowClosePrice:
                            RealBuyMoney = BuyAmt * NowClosePrice

                            investData['InvestMoney'] += RealBuyMoney

                            RemainInvestMoney -= (BuyAmt*NowClosePrice) #남은 투자금!
                            RemainInvestMoney -= NowFee


                            investData['TotAmt'] += BuyAmt
                            investData['AvgPrice'] = ((investData['AvgPrice'] * (investData['TotAmt']-BuyAmt)) + (BuyAmt*NowClosePrice)) / investData['TotAmt']

                            print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 일부 매수!(리밸런싱) 매수금액:", round(RealBuyMoney,2) ,  " 매수가:",NowClosePrice)
    

    if len(NowInvestList) < len(InvestStockList):


        for stock_code in InvestStockList:

            
            IsAlReadyInvest = False
            for investData in NowInvestList:
                if stock_code == investData['stock_code']: 
                    IsAlReadyInvest = True
                    break    


            

            if IsAlReadyInvest == False:

        
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

                if len(stock_data) == 1:
                        
                    NowClosePrice = stock_data['close'].values[0]


                    IsBuyGo = True

                    #매수하되 지정한 년도부터 매수한다!!
                    if IsBuyGo == True  and len(NowInvestList) < len(InvestStockList) and int(date_object.strftime("%Y")) >= StartYear:
                        
                        if IsFirstDateSet == False:
                            FirstDateStr = str(date)
                            IsFirstDateSet = True

                        Rate = 1.0

                        #'''
                        if stock_data['120ma'].values[0] > stock_data['prevClose'].values[0]:
                            Rate *= 0.5

                        if stock_data['80ma_Before'].values[0] > stock_data['80ma'].values[0]:
                            Rate *= 0.5
                        #'''


                        TargetRate = GetTargetRate(stock_code,StockDataList)
        
                        InvestGoMoney =  (InvestMoney * TargetRate * Rate) 
                        

                        if InvestGoMoney == 0:


                            InvestData = dict()

                            InvestData['stock_code'] = stock_code
                            InvestData['InvestMoney'] = 0
                            InvestData['InvestRate'] = 0
                            InvestData['FirstMoney'] = 0
                            InvestData['AvgPrice'] = 0
                            InvestData['TotAmt'] = 0
                            InvestData['EntryMonth'] = date_object.strftime(RebalanceSt)
                            InvestData['IsRebalanceGo'] = False
                            InvestData['Date'] = str(date)



                            NowInvestList.append(InvestData)


                            NowInvestMoney = 0
                            for iData in NowInvestList:
                                NowInvestMoney += iData['InvestMoney']

                            InvestMoney = RemainInvestMoney + NowInvestMoney


                            print(GetStockName(stock_code, StockDataList), "(",stock_code, ") ", str(date), " " ,i, " >>>>>>>>>>>>>>>>> 매수대상! 아직 매수 안함! ")



                        else:
        

                            BuyAmt = int(InvestGoMoney /  NowClosePrice) #매수 가능 수량을 구한다!

                            NowFee = (BuyAmt*NowClosePrice) * fee

                            #매수해야 되는데 남은돈이 부족하다면 수량을 하나씩 감소시켜 만족할 때 매수한다!!
                            while RemainInvestMoney < (BuyAmt*NowClosePrice) + NowFee:
                                if RemainInvestMoney > NowClosePrice:
                                    BuyAmt -= 1
                                    NowFee = (BuyAmt*NowClosePrice) * fee
                                else:
                                    break
                            
                            if BuyAmt > 0:

                                RealInvestMoney = (BuyAmt*NowClosePrice) #실제 들어간 투자금

                                RemainInvestMoney -= (BuyAmt*NowClosePrice) #남은 투자금!
                                RemainInvestMoney -= NowFee


                                InvestData = dict()

                                InvestData['stock_code'] = stock_code
                                InvestData['InvestMoney'] = RealInvestMoney
                                InvestData['InvestRate'] = TargetRate * Rate
                                InvestData['FirstMoney'] = RealInvestMoney
                                InvestData['AvgPrice'] = NowClosePrice
                                InvestData['TotAmt'] = BuyAmt
                                InvestData['EntryMonth'] = date_object.strftime(RebalanceSt)
                                InvestData['IsRebalanceGo'] = False
                                InvestData['Date'] = str(date)



                                NowInvestList.append(InvestData)


                                NowInvestMoney = 0
                                for iData in NowInvestList:
                                    NowInvestMoney += iData['InvestMoney']

                                InvestMoney = RemainInvestMoney + NowInvestMoney


                                print(GetStockName(stock_code, StockDataList), "(",stock_code, ") ", str(date), " " ,i, " >>>>>>>>>>>>>>>>> 매수! ,매수금액:", round(RealInvestMoney,2) ,  " 매수가:",NowClosePrice)



    
    NowInvestMoney = 0

    for iData in NowInvestList:
        NowInvestMoney += iData['InvestMoney']



    
    InvestMoney = RemainInvestMoney + NowInvestMoney



    InvestCoinListStr = ""
    print("\n\n------------------------------------\n")
    for iData in NowInvestList:
        InvestCoinListStr += (">>>" + GetStockName(iData['stock_code'], StockDataList)  + "-> 투자비중:" + str(iData['InvestRate']*100) +"%<<<\n")
    print("------------------------------------")

    print(InvestCoinListStr, "---> 투자대상 : ", len(NowInvestList))
    #pprint.pprint(NowInvestList)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>--))", str(date), " 잔고:",str(InvestMoney) , "=" , str(RemainInvestMoney) , "+" , str(NowInvestMoney), "\n\n" )
    

    TotalMoneyList.append(InvestMoney)

    #####################################################
    #####################################################
    #####################################################
    #'''
    
   


#결과 정리 및 데이터 만들기!!
if len(TotalMoneyList) > 0:

    print("TotalMoneyList -> ", len(TotalMoneyList))


    resultData = dict()

    # Create the result DataFrame with matching shapes
    result_df = pd.DataFrame({"Total_Money": TotalMoneyList}, index=combined_df.index.unique())

    result_df['Ror'] = np.nan_to_num(result_df['Total_Money'].pct_change()) + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()
    result_df['Highwatermark'] = result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    pprint.pprint(result_df)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    resultData['DateStr'] = str(FirstDateStr) + " ~ " + str(result_df.iloc[-1].name)

    resultData['OriMoney'] = FirstInvestMoney
    resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
    resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)

    resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0


    ResultList.append(resultData)

    result_df.index = pd.to_datetime(result_df.index)


    # Create a figure with subplots for the two charts
    fig, axs = plt.subplots(2, 1, figsize=(10, 10))

    # Plot the return chart
    axs[0].plot(result_df['Cum_Ror'] * 100, label='Strategy')
    axs[0].set_ylabel('Cumulative Return (%)')
    axs[0].set_title('Return Comparison Chart')
    axs[0].legend()

    # Plot the MDD and DD chart on the same graph
    axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
    axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
    axs[1].set_ylabel('Drawdown (%)')
    axs[1].set_title('Drawdown Comparison Chart')
    axs[1].legend()

    # Show the plot
    plt.tight_layout()
    plt.show()
        
    


    for idx, row in result_df.iterrows():
        print(idx, " " , row['Total_Money'], " "  , row['Cum_Ror'])
        



#데이터를 보기좋게 프린트 해주는 로직!
print("\n\n--------------------")


for result in ResultList:

    print("--->>>",result['DateStr'].replace("00:00:00",""),"<<<---")

    for stock_data in StockDataList:
        print(stock_data['stock_name'] , " (", stock_data['stock_code'],")")

    print("---------- 총 결과 ----------")
    print("최초 금액:", format(int(round(result['OriMoney'],0)), ',') , " 최종 금액:", format(int(round(result['FinalMoney'],0)), ','), " \n수익률:", round(((round(result['FinalMoney'],2) - round(result['OriMoney'],2) ) / round(result['OriMoney'],2) ) * 100,2) ,"% MDD:",  round(result['MDD'],2),"%")

    print("------------------------------")
    print("####################################")
