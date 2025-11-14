#-*-coding:utf-8 -*-
'''


https://blog.naver.com/zacra/223473233858



하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''


import pyupbit


import pandas as pd
import pprint

import time


Tickers = ["KRW-BTC","KRW-ETH","KRW-ADA","KRW-SOL","KRW-DOT","KRW-POL","KRW-XRP","KRW-DOGE","KRW-SHIB","KRW-AVAX","KRW-LINK","KRW-BCH","KRW-APT","KRW-HBAR","KRW-STX","KRW-ATOM","KRW-XLM","KRW-CRO","KRW-ALGO","KRW-SUI","KRW-VET","KRW-AAVE","KRW-TRX"]


stock_df_list = []

for ticker in Tickers:

    try:

        print("----->", ticker ,"<-----")
        df = pyupbit.get_ohlcv(ticker,interval="day",count=6000, period=0.3) 

        period = 14

        delta = df["close"].diff()
        up, down = delta.copy(), delta.copy()
        up[up < 0] = 0
        down[down > 0] = 0
        _gain = up.ewm(com=(period - 1), min_periods=period).mean()
        _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
        RS = _gain / _loss

        df['RSI'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")

        df['ma5_rsi_before'] = df['RSI'].rolling(5).mean().shift(1)
        df['ma5_rsi_before2'] = df['RSI'].rolling(5).mean().shift(2)

        df['prevRSI'] = df['RSI'].shift(1)
        df['prevRSI2'] = df['RSI'].shift(2)

        df['prevValue'] = df['value'].shift(1)
        df['prevValue2'] = df['value'].shift(2)

        df['prevClose'] = df['close'].shift(1)
        df['prevClose2'] = df['close'].shift(2)

        df['prevOpen'] = df['open'].shift(1)
        df['prevOpen2'] = df['open'].shift(2)

        df['prevLow'] = df['low'].shift(1)
        df['prevLow2'] = df['low'].shift(2)

        df['prevHigh'] = df['high'].shift(1)
        df['prevHigh2'] = df['high'].shift(2)

        df['prevChange'] = (df['prevClose'] - df['prevClose2']) / df['prevClose2'] #전일 종가 기준 수익률
        df['prevChange2'] = df['prevChange'].shift(1)


        df['prevChangeMa'] = df['prevChange'].rolling(window=20).mean()


        df['Disparity5'] = df['prevClose'] / df['prevClose'].rolling(window=5).mean() * 100.0
        df['Disparity20'] = df['prevClose'] / df['prevClose'].rolling(window=20).mean() * 100.0


        df['ma5_before'] = df['close'].rolling(5).mean().shift(1)
        df['ma5_before2'] = df['close'].rolling(5).mean().shift(2)
        
        
        df['ma50_before'] = df['close'].rolling(50).mean().shift(1)
        df['ma50_before2'] = df['close'].rolling(50).mean().shift(2)
        
        
        df['ma60_before'] = df['close'].rolling(60).mean().shift(1)
        df['ma60_before2'] = df['close'].rolling(60).mean().shift(2)
        
        df['ma120_before'] = df['close'].rolling(120).mean().shift(1)
        df['ma120_before2'] = df['close'].rolling(120).mean().shift(2)


        df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)

        df['prevCloseW'] = df['close'].shift(7)
        df['prevChangeW'] = (df['prevClose'] - df['prevCloseW']) / df['prevCloseW']
 

        df.dropna(inplace=True) #데이터 없는건 날린다!

    

        data_dict = {ticker: df}
        stock_df_list.append(data_dict)

        time.sleep(0.2)

    except Exception as e:
        print("Exception ", e)


# Combine the OHLCV data into a single DataFrame
combined_df = pd.concat([list(data_dict.values())[0].assign(ticker=ticker) for data_dict in stock_df_list for ticker in data_dict])

# Sort the combined DataFrame by date
combined_df.sort_index(inplace=True)


pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))


combined_df.to_csv("./UpbitDataHalt.csv", index=True) 

print("Save Done!!")