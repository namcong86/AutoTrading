#-*-coding:utf-8 -*-
'''

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

해당 컨텐츠는 제가 직접 투자 하기 위해 이 전략을 추가 개선해서 더 좋은 성과를 보여주는 개인 전략이 존재합니다. 

해당 전략 추가 개선한 버전 안내
https://blog.naver.com/zacra/223577385295

게만아 추가 개선 개인 전략들..
https://blog.naver.com/zacra/223196497504


관심 있으신 분은 위 포스팅을 참고하세요!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$


$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$



관련 포스팅
https://blog.naver.com/zacra/223559959653


위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'Common'))

import KIS_Common as Common

import pandas as pd
import pprint
import matplotlib.pyplot as plt
import socket

from datetime import datetime

# GUI 및 차트 연동을 위한 라이브러리
import tkinter as tk
from tkinter import ttk
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib import font_manager

# 폰트 설정
try:
    if os.name == 'nt': # Windows OS
        font_path = "c:/Windows/Fonts/malgun.ttf"
    elif os.name == 'posix': # Mac OS
        font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    else:
        font_path = None

    if font_path and os.path.exists(font_path):
        font_name = font_manager.FontProperties(fname=font_path).get_name()
        mpl.rcParams['font.family'] = font_name
    else:
        mpl.rcParams['font.family'] = 'DejaVu Sans'

    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'

except Exception as e:
    print(f"폰트 설정 중 오류 발생: {e}")
    mpl.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    mpl.rcParams['mathtext.fontset'] = 'dejavusans'


#계좌 선택.. "VIRTUAL" 는 모의 계좌!
Common.SetChangeMode("VIRTUAL") 


#####################################################
TestArea = "US" #한국이라면 KR 미국이라면 US로 변경하세요 ^^
#####################################################

fee = 0.0015 #수수료+세금+슬리피지를 매수매도마다 0.15%로 기본 세팅!

TotalMoney = 10000000 #한국 계좌의 경우 시작 투자금 1000만원으로 가정!

if TestArea == "US": #미국의 경우는
    TotalMoney = 10000 #시작 투자금 $10000로 가정!


GetCount = 2000  #얼마큼의 데이터를 가져올 것인지
CutCount = 0     #최근 데이터 삭제! 200으로 세팅하면 200개의 최근 데이터가 사라진다




InvestStockList = list()

#'''
InvestStockList.append({"stock_code":"QQQ", "small_ma":3 , "big_ma":132, "invest_rate":0.5}) 
InvestStockList.append({"stock_code":"TLT", "small_ma":13 , "big_ma":53, "invest_rate":0.25}) 
InvestStockList.append({"stock_code":"GLD", "small_ma":17 , "big_ma":78, "invest_rate":0.25}) 
#'''



'''
InvestStockList.append({"stock_code":"133690", "small_ma":5 , "big_ma":34, "invest_rate":0.4}) #TIGER 미국나스닥100
InvestStockList.append({"stock_code":"069500", "small_ma":3 , "big_ma":103, "invest_rate":0.2}) #KODEX 200
InvestStockList.append({"stock_code":"148070", "small_ma":8 , "big_ma":71, "invest_rate":0.1}) #KOSEF 국고채10년
InvestStockList.append({"stock_code":"305080", "small_ma":20 , "big_ma":61, "invest_rate":0.1}) #TIGER 미국채10년선물
InvestStockList.append({"stock_code":"132030", "small_ma":15 , "big_ma":89, "invest_rate":0.2}) #KODEX 골드선물(H)
'''




IS_BUY_AND_HOLD = False #이평선 매매안하고 그냥 저 비중 그대로 가져갔을 때의 테스팅 결과 보기


stock_df_list = []

for stock_info in InvestStockList:
    
    stock_code = stock_info['stock_code']
    
    df = Common.GetOhlcv(TestArea, stock_code,GetCount)

    df['prevOpen'] = df['open'].shift(1)
    df['prevClose'] = df['close'].shift(1)
    
    ############# 이동평균선! ###############
    '''
    for ma in range(3,201):
        df[str(ma) + 'ma_before'] = df['close'].rolling(ma).mean().shift(1)
        df[str(ma) + 'ma_before2'] = df['close'].rolling(ma).mean().shift(2)
    '''
        
    ma_dfs = []

    # 이동 평균 계산
    for ma in range(3, 201):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma_before').shift(1)
        ma_dfs.append(ma_df)
        
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma_before2').shift(2)
        ma_dfs.append(ma_df)
    # 이동 평균 데이터 프레임을 하나로 결합
    ma_df_combined = pd.concat(ma_dfs, axis=1)

    # 원본 데이터 프레임과 결합
    df = pd.concat([df, ma_df_combined], axis=1)

    df['max_ma'] = df['close'].rolling(200).mean()
    ########################################

    df.dropna(inplace=True) #데이터 없는건 날린다!

    df = df[:len(df)-CutCount]
   
    data_dict = {stock_code: df}
    stock_df_list.append(data_dict)
    print("---stock_code---", stock_code , " len ",len(df))
    pprint.pprint(df)


combined_df = pd.concat([list(data_dict.values())[0].assign(stock_code=stock_code) for data_dict in stock_df_list for stock_code in data_dict])
combined_df.sort_index(inplace=True)

pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))




InvestMoney = TotalMoney
RemainInvestMoney = InvestMoney


IsBuy = False #매수 했는지 여부
BUY_PRICE = 0  #매수한 금액! 

TryCnt = 0      #매매횟수
SuccesCnt = 0   #익절 숫자
FailCnt = 0     #손절 숫자


TotalMoneyList = list()

NowInvestList = list()



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


    #매도했다면 투자 리스트에서 제거해주기 위해
    items_to_remove = list()


    #투자중인 종목을 순회하며 처리!
    for investData in NowInvestList:

        stock_code = investData['stock_code'] 
        
        stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)] 


        if len(stock_data) == 1:
    
            #################################################################################################################
            NowClosePrice = stock_data['close'].values[0]
            PrevClosePrice = stock_data['prevClose'].values[0] 


            if investData['InvestMoney'] > 0:
                investData['InvestMoney'] = investData['InvestMoney'] *  (1.0 + ((NowClosePrice - PrevClosePrice ) / PrevClosePrice))
            #################################################################################################################
            
            if IS_BUY_AND_HOLD == True:
                continue

            small_ma = investData['small_ma']
            big_ma = investData['big_ma'] 
            
            if stock_data[str(small_ma)+'ma_before'].values[0] < stock_data[str(big_ma)+'ma_before'].values[0] and stock_data[str(small_ma)+'ma_before2'].values[0] > stock_data[str(small_ma)+'ma_before'].values[0]:

                

                RealSellMoney = investData['InvestMoney']

                ReturnMoney = RealSellMoney

                investData['InvestMoney'] = 0

                RemainInvestMoney += (ReturnMoney * (1.0 - fee))


                NowInvestMoney = 0
                for iData in NowInvestList:
                    NowInvestMoney += iData['InvestMoney']

                InvestMoney = RemainInvestMoney + NowInvestMoney


                print(investData['stock_code'], str(date),  " >>>>>>>>>>>>>>>>> 모두 매도!(리밸런싱) 매도금액:", round(RealSellMoney,2) ,  " 매도가:",NowClosePrice)

                items_to_remove.append(investData)


    #리스트에서 제거
    for item in items_to_remove:
        NowInvestList.remove(item)


    #매수된 수량이 총 포트폴리오 개수보다 적다면 매수한 종목이 있다!
    if len(NowInvestList) < len(InvestStockList):


        for stock_info in InvestStockList:
            
            stock_code = stock_info['stock_code']
            
            small_ma = stock_info['small_ma']
            big_ma = stock_info['big_ma']
            
            invest_rate = stock_info['invest_rate']
            

            
            IsAlReadyInvest = False
            for investData in NowInvestList:
                if stock_code == investData['stock_code']: 
                    IsAlReadyInvest = True
                    break    

            #이미 투자중인 종목이 아니라면..
            if IsAlReadyInvest == False:

                #해당 날짜에 해당 종목 데이터를 가져온다
                stock_data = combined_df[(combined_df.index == date) & (combined_df['stock_code'] == stock_code)]
                
                if len(stock_data) == 1:
                    
                    if stock_data[str(small_ma)+'ma_before'].values[0] > stock_data[str(big_ma)+'ma_before'].values[0] and stock_data[str(small_ma)+'ma_before2'].values[0] < stock_data[str(small_ma)+'ma_before'].values[0] :
                            
                        
                        NowClosePrice = stock_data['close'].values[0]

                        InvestGoMoney =  (InvestMoney * invest_rate) 
                        

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
                            InvestData['small_ma'] = small_ma
                            InvestData['big_ma'] = big_ma

                            NowInvestList.append(InvestData)


                            NowInvestMoney = 0
                            for iData in NowInvestList:
                                NowInvestMoney += iData['InvestMoney']

                            InvestMoney = RemainInvestMoney + NowInvestMoney


                            print(stock_code , str(date), " >>>>>>>>>>>>>>>>> 매수! ,매수금액:", round(RealInvestMoney,2) , " 매수가:",NowClosePrice)

                    

    NowInvestMoney = 0

    for iData in NowInvestList:
        NowInvestMoney += iData['InvestMoney']



    
    InvestMoney = RemainInvestMoney + NowInvestMoney



    InvestCoinListStr = ""
    print("\n\n------------------------------------\n")
    for iData in NowInvestList:
        InvestCoinListStr += (">>>" + iData['stock_code']  + "<\n")
    print("------------------------------------")

    print(InvestCoinListStr, "---> 투자대상 : ", len(NowInvestList))
    #pprint.pprint(NowInvestList)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>--))", str(date), " 잔고:",str(InvestMoney) , "=" , str(RemainInvestMoney) , "+" , str(NowInvestMoney), "\n\n" )
    

    TotalMoneyList.append(InvestMoney)
                    


#결과 정리 및 데이터 만들기!!
if len(TotalMoneyList) > 0:

    resultData = dict()

    
    resultData['Ticker'] = stock_code


    
    #전략 성과 구하기
    result_df = pd.DataFrame({ "Total_Money" : TotalMoneyList}, index = df.index)

    result_df['Ror'] = result_df['Total_Money'].pct_change() + 1
    result_df['Cum_Ror'] = result_df['Ror'].cumprod()

    result_df['Highwatermark'] =  result_df['Cum_Ror'].cummax()
    result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
    result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()
    #print("\n\n\n\n")
    #pprint.pprint(result_df)


    resultData['DateStr'] = str(result_df.iloc[0].name) + " ~ " + str(result_df.iloc[-1].name)

    resultData['StartMoney'] = TotalMoney
    resultData['FinalMoney'] = result_df['Total_Money'].iloc[-1]
    resultData['RevenueRate'] = ((result_df['Cum_Ror'].iloc[-1] -1.0)* 100.0)
    resultData['MDD'] = result_df['MaxDrawdown'].min() * 100.0

    resultData['TryCnt'] = TryCnt
    resultData['SuccesCnt'] = SuccesCnt
    resultData['FailCnt'] = FailCnt
    



    result_df.index = pd.to_datetime(result_df.index)

    # GUI 차트 클래스 정의
    class ChartApp(tk.Tk):
        def __init__(self):
            super().__init__()
            self.title("MA Strategy 백테스팅 결과 분석")
            self.geometry("1400x900")
            self.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.chart_artists = {}
            self.create_widgets()

        def create_widgets(self):
            main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
            main_pane.pack(fill=tk.BOTH, expand=True)
            
            left_panel = ttk.Frame(main_pane)
            main_pane.add(left_panel, weight=1)
            
            # 통계 정보 표시
            stats_frame = ttk.LabelFrame(left_panel, text="전략 통계", padding=10)
            stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            stats_text = tk.Text(stats_frame, wrap=tk.WORD, height=20)
            stats_scroll = ttk.Scrollbar(stats_frame, orient="vertical", command=stats_text.yview)
            stats_text.configure(yscrollcommand=stats_scroll.set)
            stats_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            stats_text.pack(fill=tk.BOTH, expand=True)
            
            # 통계 정보 작성
            currency = "USD" if TestArea == "US" else "KRW"
            stats_info = f"""========== 전략 성과 ==========

테스트 기간: {resultData['DateStr'].replace("00:00:00","")}

최초 금액: {format(int(round(resultData['StartMoney'],0)), ',')} {currency}
최종 금액: {format(int(round(resultData['FinalMoney'],0)), ',')} {currency}
전략 수익률: {format(round(resultData['RevenueRate'],2), ',')}%
MDD: {round(resultData['MDD'],2)}%

========== 투자 종목 ==========

"""
            for stock_info in InvestStockList:
                stats_info += f"{stock_info['stock_code']} - 단기이평: {stock_info['small_ma']}일, 장기이평: {stock_info['big_ma']}일, 비중: {stock_info['invest_rate']*100}%\n"
            
            stats_text.insert('1.0', stats_info)
            stats_text.config(state=tk.DISABLED)
            
            chart_frame = ttk.Frame(main_pane)
            main_pane.add(chart_frame, weight=3)
            
            self.tab_control = ttk.Notebook(chart_frame)
            self.tab_control.pack(expand=1, fill="both")
            
            self.add_overall_tab()
            
        def on_closing(self):
            self.quit(); self.destroy()

        def create_chart_frame(self, parent_tab):
            frame = ttk.Frame(parent_tab)
            frame.pack(fill='both', expand=True)
            fig = Figure(dpi=100)
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.get_tk_widget().pack(side='top', fill='both', expand=True)
            toolbar = NavigationToolbar2Tk(canvas, frame)
            toolbar.update()
            return fig, canvas

        def add_overall_tab(self):
            overall_tab = ttk.Frame(self.tab_control)
            self.tab_control.add(overall_tab, text='📊 종합 결과')
            fig, canvas = self.create_chart_frame(overall_tab)
            axs = fig.subplots(2, 1, sharex=True, gridspec_kw={'height_ratios': [2, 1]})
            fig.tight_layout(pad=3.0)
            
            currency = "USD" if TestArea == "US" else "KRW"
            axs[0].plot(result_df.index, result_df['Total_Money'], label='Strategy', color='blue')
            axs[0].set_title('Overall Performance (Linear Scale)', fontsize=12)
            axs[0].set_ylabel(f'Total Money ({currency})')
            axs[0].grid(True, which='both', linestyle='--', linewidth=0.5)
            axs[0].legend()
            axs[0].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:,.0f}'))
            
            axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD', color='red', linewidth=2)
            axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown', color='orange', alpha=0.5)
            axs[1].set_title('Drawdown Comparison', fontsize=12)
            axs[1].set_ylabel('Drawdown (%)')
            axs[1].grid(True)
            axs[1].legend()
            axs[1].get_yaxis().set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}%'))
            
            self.chart_artists['overall'] = {'fig': fig, 'canvas': canvas, 'ax': axs[0]}
            canvas.draw()

    # 서버 환경 체크 및 GUI 실행
    pcServerGb = socket.gethostname()
    if pcServerGb != "AutoBotCong":
        app = ChartApp()
        app.mainloop()
        print("\n차트 창이 닫혔습니다. 최종 통계 결과를 출력합니다.")
    else:
        print("\n서버 환경이므로 GUI를 생략하고 최종 통계 결과를 바로 출력합니다.")

    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> ")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")
    print("테스트 기간: ",resultData['DateStr'].replace("00:00:00",""))
    print("\n---------------전략 성과---------------")
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n")
    print("최초 금액: ", format(int(round(resultData['StartMoney'],0)), ',') , " 최종 금액: ",  format(int(round(resultData['FinalMoney'],0)), ',') )
    print("전략 수익률:", format(round(resultData['RevenueRate'],2), ',') , "%  MDD:", round(resultData['MDD'],2) , "%\n")
    print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
    print("-----------------------------------------------\n")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>\n")