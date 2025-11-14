#-*-coding:utf-8 -*-
'''

관련 포스팅
https://blog.naver.com/zacra/223589057576


하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^

 
'''


import myBithumb


import pandas as pd
import pprint

import time


Tickers = myBithumb.GetTickers()

stock_df_list = []

for ticker in Tickers:

    try:

        print("----->", ticker ,"<-----")
        df = myBithumb.GetOhlcv(ticker,'1d',700) #아래 이평선 구하는 로직으로 200개의 데이터가 드랍되니 참고하여 조절!

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



        df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)

        df['prevCloseW'] = df['close'].shift(7)
        df['prevChangeW'] = (df['prevClose'] - df['prevCloseW']) / df['prevCloseW']
 

        #이렇게 3일선 부터 200일선을 자동으로 만들 수 있다!
        '''
        for ma in range(3,201):
            df['ma'+str(ma)+'_before'] = df['close'].rolling(ma).mean().shift(1)
            df['ma'+str(ma)+'_before2'] = df['close'].rolling(ma).mean().shift(2)
        '''

        ma_dfs = []

        # 이동 평균 계산
        for ma in range(3, 201):
            ma_df = df['close'].rolling(ma).mean().rename('ma'+str(ma)+'_before').shift(1)
            ma_dfs.append(ma_df)
            
            ma_df = df['close'].rolling(ma).mean().rename('ma'+str(ma)+'_before2').shift(2)
            ma_dfs.append(ma_df)
        # 이동 평균 데이터 프레임을 하나로 결합
        ma_df_combined = pd.concat(ma_dfs, axis=1)

        # 원본 데이터 프레임과 결합
        df = pd.concat([df, ma_df_combined], axis=1)
        
        
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


combined_df.to_csv("./BithumbDataAlt.csv", index=True) 

print("Save Done!!")