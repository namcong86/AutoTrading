'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


관련 포스팅
https://blog.naver.com/zacra/223244683902


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
StartYear = 2020

#RebalanceSt = "%Y" #년도별 리밸런싱
RebalanceSt = "%Y%m" #월별 리밸런싱
#################################################################


FixInvestList = ["JEPI","JEPQ","SCHD","VT"]
InvestStockList = ["JEPI","JEPQ","SCHD","VT","QQQ","IYK","VTWO","VWO","VEA","SPTL","VGIT","PDBC","BCI","VNQ","TIP","SGOV","BIL","USHY","VCIT","VWOB","BNDX","BWX","PFIX","RISR"]
                 
                 
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
    df = Common.GetOhlcv("US", stock_code,2000) 
    #################################################################
    #################################################################


    df['prevClose'] = df['close'].shift(1)

    df['1month'] = df['close'].shift(20)
    df['3month'] = df['close'].shift(60)
    df['6month'] = df['close'].shift(120)
    df['12month'] = df['close'].shift(240)

    #1개월 수익률 + 3개월 수익률 + 6개월 수익률 + 12개월 수익률
    df['Momentum'] = ( ((df['prevClose'] - df['1month'])/df['1month']) + ((df['prevClose'] - df['3month'])/df['3month']) + ((df['prevClose'] - df['6month'])/df['6month'])  + ((df['prevClose'] - df['12month'])/df['12month']) ) / 4.0

    #6개월 수익률
    df['Momentum6'] = ((df['prevClose'] - df['6month'])/df['6month']) 


    df['Momentum_ga'] = ( ((df['prevClose'] - df['1month'])/df['1month']) * 12 + ((df['prevClose'] - df['3month'])/df['3month']) * 4  + ((df['prevClose'] - df['6month'])/df['6month']) * 2 + ((df['prevClose'] - df['12month'])/df['12month']) ) 


    df['20ma_Before'] = df['close'].rolling(20).mean().shift(2) 
    df['20ma'] = df['close'].rolling(20).mean().shift(1) 


    df['5ma_Before'] = df['close'].rolling(5).mean().shift(2) 
    df['5ma'] = df['close'].rolling(5).mean().shift(1) 


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

IsAllFix = False

IsTipOkBefore = False

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



    tip_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "TIP")] 
    bil_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "BIL")] 
    sgov_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "SGOV")] 

    vwo_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "VWO")] 
    vea_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "VEA")] 
    vt_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "VT")] 
    

    DivCount = 0

    if IsAllFix == False:

        
        schd_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "SCHD")] 
        jepi_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "JEPI")] 
        jepq_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "JEPQ")] 


        
        if len(vt_data) == 1:
            DivCount += 1.0


        if len(schd_data) == 1:
            DivCount += 1.0


        if len(jepi_data) == 1:
            DivCount += 1.0


        if len(jepq_data) == 1:
            DivCount += 1.0

        if DivCount == 4.0:
            IsAllFix = True

    else:
        DivCount = 4.0

    pfix_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == "PFIX")] 


    #고정 및 안전 자산을 제외한 공격자산의 모멘텀 스코어가 높은거 상위 TOP 4개를 리턴!
    exclude_stock_codes = ["VT","JEPI","JEPQ","SCHD","VCIT","BWX","BNDX","USHY","VWOB","TIP","BIL","SGOV"]
    pick_momentum_top = combined_df.loc[(combined_df.index == date) & (~combined_df['stock_code'].isin(exclude_stock_codes))].groupby('stock_code')['Momentum'].max().nlargest(4)

    ShortExceptEtf = "SGOV"
    if len(sgov_data) == 1: #SGOV가 있다면 BIL을 제외시킨다!
        ShortExceptEtf = "BIL"

    #고정 및 공격 자산을 제외한 안전자산의 모멘텀 스코어가 높은거 상위 TOP 3를 리턴!
    exclude_stock_codes = [ShortExceptEtf,"VT","JEPI","JEPQ","SCHD","QQQ","IYK","VTWO","VWO","VEA","BCI","PDBC","VNQ"]
    pick_bond_momentum_top = combined_df.loc[(combined_df.index == date) & (~combined_df['stock_code'].isin(exclude_stock_codes))].groupby('stock_code')['Momentum6'].max().nlargest(3)


    checkall = combined_df.loc[(combined_df.index == date)].groupby('stock_code')['close'].max().nlargest(len(NowInvestList))


    if len(tip_data) == 1 and len(bil_data) == 1  and int(date_object.strftime("%Y")) >= StartYear: 

 


        #안전 자산 비중 정하기!
        SafeRate = 0
        AtkRate = 0
            
        AtkOkList = list()

        IsTopCheck = False
        Top1Code = ""

        AtkEachRate = 0.70 / 4.0
        SafeAllRate = 0.70
        FixAllRate = 0.3

        if tip_data['Momentum'].values[0] < 0 or tip_data['Momentum_ga'].values[0] < 0 or vwo_data['Momentum_ga'].values[0] < 0 or vea_data['Momentum_ga'].values[0] <  0 or vt_data['Momentum_ga'].values[0] < 0:

            AtkEachRate = 0.85 / 4.0
            SafeAllRate = 0.85
            FixAllRate = 0.15



        #TIP 모멘텀 양수 장이 좋다!
        if tip_data['Momentum'].values[0] > 0:

            for stock_code in pick_momentum_top.index:
                    
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]

                if len(stock_data) == 1:

                    #공격 자산의 모멘텀이 0보다 크면 투자한다!!
                    if stock_data['Momentum'].values[0] >= 0:


                        AtkOkList.append(stock_code)

                        #제일 먼저 체크한 것이 가장 모멘텀 스코어가 큰 자산이니 그 종목 코드를 따로 저장해 둔다!
                        if IsTopCheck == False:
                            IsTopCheck = True
                            Top1Code = stock_code

                    #아니면 투자하지 않는다. 남는 비중을 저장!
                    else:
                        AtkRate += AtkEachRate

        


        #TIP 모멘텀 음수 장이 안좋아!
        else:
            #안전자산에 투자한다!
            SafeRate = SafeAllRate

      
        #공격 자산중 투자안한 비중이 있다면 
        if AtkRate > 0:
            HalfAtkRate = AtkRate * 0.5

            SafeRate += HalfAtkRate #안전 비중에 절반을 나눠준다.
            AtkRate -= HalfAtkRate 

     

    


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
                if investData['EntryMonth'] != date_object.strftime(RebalanceSt) :

                    # 요일 가져오기 (0: 월요일, 1: 화요일,2 수요일 3 목요일 4 금요일 5 토요일 ..., 6: 일요일)
                    #weekday = date_object.weekday()

                    investData['EntryMonth'] = date_object.strftime(RebalanceSt)

                    IsReblanceDay = True

                #################################################################################################################
                

                if IsReblanceDay == True: 
                    


                    investData['IsRebalanceGo'] = True
                    investData['RebalanceAmt'] = 0
                    investData['InvestRate'] = 0

                #'''
                else:

                    if investData['InvestMoney'] > 0 :

                        if stock_data['20ma'].values[0] > stock_data['5ma'].values[0]  and stock_data['20ma_Before'].values[0] < stock_data['5ma_Before'].values[0] and stock_data['5ma'].values[0] > stock_data['prevClose'].values[0]  :
                        

  

                            SellAmt = abs(investData['RebalanceAmt'])*0.5
               
                            if SellAmt <= 4:

                                RealSellMoney = investData['InvestMoney']

                                ReturnMoney = RealSellMoney

                                investData['InvestMoney'] = 0
                                investData['InvestRate'] = 0

                                RemainInvestMoney += (ReturnMoney * (1.0 - fee))
                                

                                print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 이평선! 모두 매도!(손절) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)

                            else:
                


                                RealSellMoney = SellAmt * NowClosePrice


                                ReturnMoney = RealSellMoney

                                investData['InvestMoney'] -= RealSellMoney
                                investData['InvestRate'] *= 0.5

                                RemainInvestMoney += (ReturnMoney * (1.0 - fee))

                                print(investData['stock_code'], str(date), " " ,i, " >>>>>>>>>>>>>>>>> 이평선! 50%씩 매도!(손절) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)


                #'''

        #################################################################################################################
        ##################### 리밸런싱 할때 투자 비중을 맞춰주는 작업 #############################



        NowInvestMoney = 0

        for iData in NowInvestList:
            NowInvestMoney += iData['InvestMoney']

        
        InvestMoney = RemainInvestMoney + NowInvestMoney




        #리밸런싱 수량을 확정한다!
        for investData in NowInvestList:

            
            stock_code = investData['stock_code']



            if investData['IsRebalanceGo'] == True:

                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 

                
                if len(stock_data) == 1:
                    
                    IsRebalanceGo = False

                    NowClosePrice = stock_data['close'].values[0]

                    #안전 자산 비중이 있는 경우!! 안전자산에 투자!!!
                    if SafeRate > 0:
                        
                        for stock_code_b in pick_bond_momentum_top.index:
                                
                            if stock_code_b == stock_code:

                                IsOk = False
                                if len(sgov_data) == 1:
                                    #BIL보다 높은 것만 투자!
                                    if stock_data['Momentum6'].values[0] >= sgov_data['Momentum6'].values[0] :#and stock_data['20ma'].values[0] < stock_data['prevClose'].values[0]:
                                        IsOk = True
                                else:
                                    #BIL보다 높은 것만 투자!
                                    if stock_data['Momentum6'].values[0] >= bil_data['Momentum6'].values[0] :#and stock_data['20ma'].values[0] < stock_data['prevClose'].values[0]:
                                        IsOk = True



                                #BIL보다 높은 것만 투자!
                                if IsOk == True :

                                    investData['InvestRate'] += (SafeRate/len(pick_bond_momentum_top.index))
                    
                                    GapInvest = (InvestMoney * investData['InvestRate'])  - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!

                                    investData['RebalanceAmt'] += int(GapInvest / NowClosePrice)
                                    IsRebalanceGo = True

                                break


                    #선택된 공격자산이라면!! 0.21%씩 투자해준다!
                    if stock_code in AtkOkList:


                        #단 가장 모멘텀 좋은 자산은 아까 위에서 계산한 추가 비중이 있다면 더해준다!
                        if stock_code == Top1Code:

                            investData['InvestRate'] += (AtkEachRate + AtkRate)
                        else:
                            investData['InvestRate'] += AtkEachRate


                        GapInvest = (InvestMoney * investData['InvestRate']) - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!

                        investData['RebalanceAmt'] += int(GapInvest / NowClosePrice)
                        IsRebalanceGo = True

  

                    if stock_code in FixInvestList:
                        investData['InvestRate'] += (FixAllRate/ DivCount)

                        GapInvest = (InvestMoney * investData['InvestRate']) - investData['InvestMoney'] #목표 금액에서 현재 평가금액을 빼서 갭을 구한다!

                        investData['RebalanceAmt'] += int(GapInvest / NowClosePrice)
                        IsRebalanceGo = True   



                    if IsRebalanceGo == False:
                        if stock_code not in FixInvestList:
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


        #혹시나 위에서 처리되지 않은 게 있다면...            
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
    resultData['FinalMoney'] = result_df['Total_Money'][-1]
    resultData['RevenueRate'] = ((result_df['Cum_Ror'][-1] -1.0)* 100.0)

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
