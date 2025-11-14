#-*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

바이낸스 ccxt 버전
pip3 install --upgrade ccxt==4.2.19
이렇게 버전을 맞춰주세요!

봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요!
https://blog.naver.com/zacra/222662884649

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

관련 포스팅

https://blog.naver.com/zacra/

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고

주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^


'''


import ccxt

import myBinance
import ende_key  #암복호화키
import my_key    #업비트 시크릿 액세스키

import time
import pandas as pd
import pprint
import datetime



def GetOhlcv2(binance, Ticker, period, year=2020, month=1, day=1, hour=0, minute=0):
    date_start = datetime.datetime(year, month, day, hour, minute)
    date_start_ms = int(date_start.timestamp() * 1000)

    final_list = []

    # OHLCV 데이터를 최대 한도(1000)만큼의 청크로 가져옵니다.
    while True:
        # OHLCV 데이터를 가져옵니다.
        ohlcv_data = binance.fetch_ohlcv(Ticker, period, since=date_start_ms)

        # 데이터가 없으면 루프를 중단합니다.
        if not ohlcv_data:
            break

        # 가져온 데이터를 최종 리스트에 추가합니다.
        final_list.extend(ohlcv_data)

        # 다음 가져오기를 위해 시작 날짜를 업데이트합니다.
        date_start = datetime.datetime.utcfromtimestamp(ohlcv_data[-1][0] / 1000)
        date_start_ms = ohlcv_data[-1][0] + (ohlcv_data[1][0] - ohlcv_data[0][0])

        # 요청 간의 짧은 시간 대기를 위해 sleep을 포함합니다.
        time.sleep(0.2)

    # 최종 리스트를 DataFrame으로 변환합니다.
    df = pd.DataFrame(final_list, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df.set_index('datetime', inplace=True)
    
    return df





#암복호화 클래스 객체를 미리 생성한 키를 받아 생성한다.
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)


#암호화된 액세스키와 시크릿키를 읽어 복호화 한다.
Binance_AccessKey = simpleEnDecrypt.decrypt(my_key.binance_access)
Binance_ScretKey = simpleEnDecrypt.decrypt(my_key.binance_secret)


# binance 객체 생성
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey, 
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

tickers_prev = binanceX.fetch_tickers()

Tickers = list()

for ticker, coin_Data in tickers_prev.items():
    if "/USDT" in ticker and "-" not in ticker:
        print(ticker ,"added")
        Tickers.append(ticker)
        
        
print("len(Tickers) : ",len(Tickers))
            

pprint.pprint(Tickers)


coin_df_list = []

for ticker in Tickers:

    try:

        print("----->", ticker ,"<-----")
        df = GetOhlcv2(binanceX,ticker, '1d' ,2018, 6, 1, 0, 0) 
        
        
        df['value'] = df['close'] * df['volume']

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



        df['box5_max'] = df['high'].rolling(5).max().shift(1)
        df['box5_min'] = df['low'].rolling(5).min().shift(1)      
        df['box5_max2'] = df['high'].rolling(5).max().shift(2)
        df['box5_min2'] = df['low'].rolling(5).min().shift(2)  
        
        df['box10_max'] = df['high'].rolling(10).max().shift(1)
        df['box10_min'] = df['low'].rolling(10).min().shift(1)      
        df['box10_max2'] = df['high'].rolling(10).max().shift(2)
        df['box10_min2'] = df['low'].rolling(10).min().shift(2)  
        
        df['box20_max'] = df['high'].rolling(20).max().shift(1)
        df['box20_min'] = df['low'].rolling(20).min().shift(1)      
        df['box20_max2'] = df['high'].rolling(20).max().shift(2)
        df['box20_min2'] = df['low'].rolling(20).min().shift(2)  
        
        

        df['prevChangeMa'] = df['prevChange'].rolling(window=20).mean()


        df['Disparity5'] = df['prevClose'] / df['prevClose'].rolling(window=5).mean() * 100.0
        df['Disparity20'] = df['prevClose'] / df['prevClose'].rolling(window=20).mean() * 100.0

        df['ma3_before'] = df['close'].rolling(3).mean().shift(1)
        df['ma3_before2'] = df['close'].rolling(3).mean().shift(2)


        df['ma5_before'] = df['close'].rolling(5).mean().shift(1)
        df['ma5_before2'] = df['close'].rolling(5).mean().shift(2)

        df['ma10_before'] = df['close'].rolling(10).mean().shift(1)
        df['ma10_before2'] = df['close'].rolling(10).mean().shift(2)

        df['ma20_before'] = df['close'].rolling(20).mean().shift(1)
        df['ma20_before2'] = df['close'].rolling(20).mean().shift(2)


        df['ma60_before'] = df['close'].rolling(60).mean().shift(1)
        df['ma60_before2'] = df['close'].rolling(60).mean().shift(2)
        

        df['ma120_before'] = df['close'].rolling(120).mean().shift(1)
        df['ma120_before2'] = df['close'].rolling(120).mean().shift(2)

        df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
        

        df['prevCloseW'] = df['close'].shift(7)
        df['prevChangeW'] = (df['prevClose'] - df['prevCloseW']) / df['prevCloseW']
 
        
        df.dropna(inplace=True) #데이터 없는건 날린다!

    
        pprint.pprint(df)
        data_dict = {ticker: df}
        coin_df_list.append(data_dict)

        time.sleep(0.2)

    except Exception as e:
        print("Exception ", e)


# Combine the OHLCV data into a single DataFrame
combined_df = pd.concat([list(data_dict.values())[0].assign(ticker=ticker) for data_dict in coin_df_list for ticker in data_dict])

# Sort the combined DataFrame by date
combined_df.sort_index(inplace=True)


pprint.pprint(combined_df)
print(" len(combined_df) ", len(combined_df))


combined_df.to_csv("./BinanceDataAll.csv", index=True) 

print("Save Done!!")