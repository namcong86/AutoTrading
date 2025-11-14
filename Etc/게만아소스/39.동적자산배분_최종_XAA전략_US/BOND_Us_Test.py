'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅


채권 동적 자산배분 활용기
https://blog.naver.com/zacra/223202898685

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
TotalMoney = 10000000
FirstInvestMoney = TotalMoney

fee = 0.0025 #수수료+세금+슬리피지를 매수매도마다 0.25%로 세팅!

print("테스트하는 총 금액: ", format(round(TotalMoney), ','))
##################################################################
    
#################################################################
#전략 백테스팅 시작 년도 지정!!!
StartYear = 2015

#RebalanceSt = "%Y" #년도별 리밸런싱
RebalanceSt = "%Y%m" #월별 리밸런싱
#################################################################



InvestStockList = ["BIL","TLT","HYG","LQD","IEF","EMB","TIP","BNDX","BWX"]


StockDataList = list()

for stock_code in InvestStockList:
    print("..",stock_code,"..")
    stock_data = dict()
    stock_data['stock_code'] = stock_code
    stock_data['stock_name'] = stock_code#KisKR.GetStockName(stock_code)
    stock_data['target_rate'] = 0
    stock_data['InvestDayCnt'] = 0
    StockDataList.append(stock_data)

pprint.pprint(StockDataList)

def IncreaseInvestDayCnt(stock_code, StockDataList):
    for stock_data in StockDataList:
        if stock_code == stock_data['stock_code']:
            stock_data['InvestDayCnt'] += 1
            break

#사실 미국에선 사용하지 않지만 한국에선 유용하니깐 그냥 내비두장~
def GetStockName(stock_code, StockDataList):
    result_str = stock_code
    for stock_data in StockDataList:
        if stock_code == stock_data['stock_code']:
            result_str = stock_data['stock_name']
            break

    return result_str
    


NowInvestList = list() #투자중인 항목의 리스트



stock_df_list = []

for stock_code in InvestStockList:
    
    #################################################################
    #################################################################
    df = Common.GetOhlcv("US", stock_code,3900) 
    #################################################################
    #################################################################


    df['prevClose'] = df['close'].shift(1)

    df['6month'] = df['close'].shift(120)

    df['Momentum'] = ((df['prevClose'] - df['6month'])/df['6month']) 


   

    df.dropna(inplace=True) #데이터 없는건 날린다!

    #df = df[:len(df)-1]
    data_dict = {stock_code: df}


    stock_df_list.append(data_dict)
        
    print("---stock_code---", stock_code , " len ",len(df))
    
    pprint.pprint(df)


    #모든 항목의 데이터를 만들어 놓는다!
    InvestData = dict()

    InvestData['stock_code'] = stock_code
    InvestData['InvestMoney'] = 0
    InvestData['InvestRate'] = 0
    InvestData['RebalanceAmt'] = 0
    InvestData['EntryMonth'] = 0
    InvestData['IsRebalanceGo'] = False


    NowInvestList.append(InvestData)



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



    bil_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "BIL")] 


    pick_safe_momentum_top = combined_df.loc[(combined_df.index == date)].groupby('stock_code')['Momentum'].max().nlargest(3)


    checkall = combined_df.loc[(combined_df.index == date)].groupby('stock_code')['close'].max().nlargest(len(NowInvestList))


    if len(checkall) == len(NowInvestList) and int(date_object.strftime("%Y")) >= StartYear:

        SafeRate = 1.0


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
                    IncreaseInvestDayCnt(stock_code, StockDataList)
                #################################################################################################################


                IsReblanceDay = False
                #################################################################################################################
                #이 부분이 월별 리밸런싱을 가능하게 하는 부분~ 
                if investData['EntryMonth'] != date_object.strftime(RebalanceSt):

                    investData['EntryMonth'] = date_object.strftime(RebalanceSt)

                    IsReblanceDay = True

                #################################################################################################################
                

                if IsReblanceDay == True: 

                    investData['IsRebalanceGo'] = True
                    investData['RebalanceAmt'] = 0
                    investData['InvestRate'] = 0
                        


        

        #################################################################################################################
        ##################### 리밸런싱 할때 투자 비중을 맞춰주는 작업 #############################

  

        NowInvestMoney = 0

        for iData in NowInvestList:
            NowInvestMoney += iData['InvestMoney']

        
        InvestMoney = RemainInvestMoney + NowInvestMoney



        #리밸런싱 수량을 확정한다!
        for investData in NowInvestList:


            if investData['IsRebalanceGo'] == True:

                stock_code = investData['stock_code']

                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 

                
                if len(stock_data) == 1:
                    
                    IsRebalanceGo = False

                    NowClosePrice = stock_data['close'].values[0]

      

                    for stock_code_b in pick_safe_momentum_top.index:
                            
                        if stock_code_b == stock_code:

                            if stock_data['Momentum'].values[0] >= bil_data['Momentum'].values[0]:

                                investData['InvestRate'] += (SafeRate/len(pick_safe_momentum_top.index))
                
                                GapInvest = (InvestMoney * investData['InvestRate'])  - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!

                                investData['RebalanceAmt'] += int(GapInvest / NowClosePrice)
                                IsRebalanceGo = True
                                
                            break
    

                    if IsRebalanceGo == False:

                        if investData['InvestMoney'] > 0:

                            GapInvest = (InvestMoney * investData['InvestRate']) - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!
                            investData['RebalanceAmt'] += int(GapInvest / NowClosePrice)






        #실제 매도!!
        for investData in NowInvestList:


            if investData['IsRebalanceGo'] == True:


                stock_code = investData['stock_code']
                
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 

                if len(stock_data) == 1:

                    NowClosePrice = stock_data['close'].values[0]

                    if investData['RebalanceAmt'] < 0:


                        SellAmt = abs(investData['RebalanceAmt'])

                        RealSellMoney = SellAmt * NowClosePrice


                        GapInvest = (InvestMoney * investData['InvestRate']) - investData['InvestMoney']

                        #팔아야할 금액이 현재 투자금보다 크다면!!! 모두 판다! 혹은 실제 팔아야할 계산된 금액이 투자금보다 크다면 모두 판다!!
                        if abs(GapInvest) > investData['InvestMoney'] or RealSellMoney > investData['InvestMoney'] or investData['InvestRate'] == 0:
                            
                            RealSellMoney = investData['InvestMoney']

                            ReturnMoney = RealSellMoney

                            investData['InvestMoney'] = 0

                            RemainInvestMoney += (ReturnMoney * (1.0 - fee))
                            

                            print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 모두 매도!(리밸런싱) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)
                            
                        else:

                            if SellAmt > 0 :

                                ReturnMoney = RealSellMoney

                                investData['InvestMoney'] -= RealSellMoney

                                RemainInvestMoney += (ReturnMoney * (1.0 - fee))

                                investData['IsRebalanceGo'] = False
                                

                                print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 일부 매도!(리밸런싱) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)


                        investData['EntryMonth'] = date_object.strftime(RebalanceSt)
                        investData['IsRebalanceGo'] = False

                



        #실제 매수!!
        for investData in NowInvestList:


            if investData['IsRebalanceGo'] == True:


                stock_code = investData['stock_code']
                
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 

                if len(stock_data) == 1:

                    NowClosePrice = stock_data['close'].values[0]

                    if investData['RebalanceAmt'] > 0:


                        if IsFirstDateSet == False:
                            FirstDateStr = str(date)
                            IsFirstDateSet = True


                        BuyAmt = investData['RebalanceAmt']


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


                            print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 매수!(리밸런싱) 매수금액:", round(RealBuyMoney,2) ,  " 매수가:",NowClosePrice)
                            
                

                        investData['EntryMonth'] = date_object.strftime(RebalanceSt)
                        investData['IsRebalanceGo'] = False

                    
        for investData in NowInvestList:


            if investData['IsRebalanceGo'] == True:

                investData['EntryMonth'] = date_object.strftime(RebalanceSt)
                investData['IsRebalanceGo'] = False


    
    NowInvestMoney = 0

    for iData in NowInvestList:
        NowInvestMoney += iData['InvestMoney']

    
    InvestMoney = RemainInvestMoney + NowInvestMoney



    InvestCoinListStr = ""
    print("\n\n------------------------------------\n")
    for iData in NowInvestList:
        InvestCoinListStr += (">>>" + GetStockName(iData['stock_code'], StockDataList)  + "-> 목표투자비중:" + str(iData['InvestRate']*100) + "%-> 실제투자비중:" + str(iData['InvestMoney']/InvestMoney*100)  +"%\n -->실제투자금:" + str(format(int(round(iData['InvestMoney'],0)), ',')) +"\n\n")
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
        print(stock_data['stock_name'] , " (", stock_data['stock_code'],") 투자일수: ",stock_data['InvestDayCnt'])

    print("---------- 총 결과 ----------")
    print("최초 금액:", format(int(round(result['OriMoney'],0)), ',') , " 최종 금액:", format(int(round(result['FinalMoney'],0)), ','), " \n수익률:", round(((round(result['FinalMoney'],2) - round(result['OriMoney'],2) ) / round(result['OriMoney'],2) ) * 100,2) ,"% MDD:",  round(result['MDD'],2),"%")

    print("------------------------------")
    print("####################################")
