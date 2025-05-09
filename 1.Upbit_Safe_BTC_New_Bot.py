#-*-coding:utf-8 -*-
'''
코드 설명 참고 영상
https://youtu.be/TYj_fq4toAw?si=b3H8B_o8oU3roIWF

관련 포스팅 
업비트 안전 전략 
https://blog.naver.com/zacra/223170880153
안전 전략 개선!
https://blog.naver.com/zacra/223238532612
전략 수익률 2배로 끌어올리기
https://blog.naver.com/zacra/223456069194

위 포스팅을 꼭 참고하세요!!!

하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고
주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739

그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^
'''

import myUpbit
import time
import pyupbit
import ende_key
import my_key
import pandas as pd
import pprint
import json
import urllib3
import telegram_alert
import socket

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myUpbit.SimpleEnDecrypt(ende_key.ende_key)

# 암호화된 액세스키와 시크릿키 복호화
Upbit_AccessKey = simpleEnDecrypt.decrypt(my_key.upbit_access)
Upbit_ScretKey = simpleEnDecrypt.decrypt(my_key.upbit_secret)

# 업비트 객체 생성
upbit = pyupbit.Upbit(Upbit_AccessKey, Upbit_ScretKey)

# 시간 정보
time_info = time.gmtime()
day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min
day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)
print("hour_n:", hour_n)
print("min_n:", min_n)

if hour_n == 0 and min_n < 5:
    telegram_alert.SendMessage("1.업비트 BTC 안전매매 정상 시작 되었습니다")
    time.sleep(0.04)

# 수익금과 수익률 계산 함수
def GetRevenueMoneyAndRate(balances, Ticker):
    balances = upbit.get_balances()
    time.sleep(0.04)
    revenue_data = dict()
    revenue_data['revenue_money'] = 0
    revenue_data['revenue_rate'] = 0
    for value in balances:
        try:
            realTicker = value['unit_currency'] + "-" + value['currency']
            if Ticker == realTicker:
                nowPrice = pyupbit.get_current_price(realTicker)
                revenue_data['revenue_money'] = (float(nowPrice) - float(value['avg_buy_price'])) * upbit.get_balance(Ticker)
                revenue_data['revenue_rate'] = (float(nowPrice) - float(value['avg_buy_price'])) * 100.0 / float(value['avg_buy_price'])
                time.sleep(0.06)
                break
        except Exception as e:
            print("---:", e)
    return revenue_data


pcServerGb = socket.gethostname()

# 봇 상태 저장 파일
BotDataDict = dict()
if pcServerGb == "AutoBotCong" :
    #서버: 
    botdata_file_path = "/var/AutoBot/json/Upbit_Safe_Data.json"
else:
    #PC
    botdata_file_path = "C:\\AutoTrading\\AutoTrading\\json\\Upbit_Safe_Data.json"


try:
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)
except Exception as e:
    print("Exception by First")

#최소 매수 금액
minmunMoney = 5500

# 잔고 조회
balances = upbit.get_balances()
TotalMoney = myUpbit.GetTotalMoney(balances)
TotalRealMoney = myUpbit.GetTotalRealMoney(balances)
print("TotalMoney", TotalMoney)
print("TotalRealMoney", TotalRealMoney)

# 투자 비중
InvestRate = 1
InvestTotalMoney = TotalMoney * InvestRate
print("InvestTotalMoney", InvestTotalMoney)

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'KRW-BTC', 'rate': 1}
]

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    # BotDataDict 초기화
    if BotDataDict.get(coin_ticker + "_BUY_DATE") is None:
        BotDataDict[coin_ticker + "_BUY_DATE"] = ""
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)
    if BotDataDict.get(coin_ticker + "_SELL_DATE") is None:
        BotDataDict[coin_ticker + "_SELL_DATE"] = ""
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)
    if BotDataDict.get(coin_ticker + "_DATE_CHECK") is None:
        BotDataDict[coin_ticker + "_DATE_CHECK"] = 0
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)
    if BotDataDict.get(coin_ticker + "_HAS") is None:
        BotDataDict[coin_ticker + "_HAS"] = myUpbit.IsHasCoin(balances, coin_ticker)
        with open(botdata_file_path, 'w') as outfile:
            json.dump(BotDataDict, outfile)

    InvestMoney = InvestTotalMoney * coin_data['rate']
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)
    InvestMoneyCell = InvestMoney * 0.995
    print("InvestMoneyCell: ", InvestMoneyCell)

    # 일봉 데이터 가져오기
    df_day = pyupbit.get_ohlcv(coin_ticker, interval="day", count=100)  # 충분한 데이터 확보
    time.sleep(0.05)

    # RSI 계산
    period = 14
    delta = df_day["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    df_day['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df_day['rsi_ma'] = df_day['rsi'].rolling(10).mean()
    df_day['rsi_5ma'] = df_day['rsi'].rolling(5).mean()

    # 이동평균선 계산
    for ma in [3, 7, 12, 16, 24, 30, 73]:
        df_day[str(ma) + 'ma'] = df_day['close'].rolling(ma).mean()
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()
    df_day['30ma_slope'] = ((df_day['30ma'] - df_day['30ma'].shift(5)) / df_day['30ma'].shift(5)) * 100
    df_day.dropna(inplace=True)

    # 현재가
    NowCurrentPrice = pyupbit.get_current_price(coin_ticker)
    IsDolpaDay = False

    # 잔고가 있는 경우
    if BotDataDict[coin_ticker + "_HAS"] and myUpbit.IsHasCoin(balances, coin_ticker):
        print("잔고가 있는 경우!")
        revenue_data = GetRevenueMoneyAndRate(balances, coin_ticker)

        if BotDataDict[coin_ticker + "_DATE_CHECK"] != day_n:
            msg = coin_ticker + " 현재 수익률: 약 " + str(round(revenue_data['revenue_rate'], 2)) + "% 수익금: 약 " + str(format(round(revenue_data['revenue_money']), ',')) + "원"
            print(msg)
            telegram_alert.SendMessage(msg)
            time.sleep(1.0)

            IsSellGo = False
            if coin_ticker == 'KRW-BTC':
                if ((df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) or
                    (df_day['open'].iloc[-2] > df_day['close'].iloc[-2] and df_day['open'].iloc[-3] > df_day['close'].iloc[-3]) or
                    revenue_data['revenue_rate'] < -0.7):
                    IsSellGo = True
                if df_day['rsi_ma'].iloc[-3] < df_day['rsi_ma'].iloc[-2] and df_day['3ma'].iloc[-3] < df_day['3ma'].iloc[-2]:
                    IsSellGo = False

            BotDataDict[coin_ticker + "_DATE_CHECK"] = day_n
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)

            if BotDataDict[coin_ticker + "_BUY_DATE"] == day_str:
                IsSellGo = False

            if IsSellGo:
                AllAmt = upbit.get_balance(coin_ticker)
                balances = myUpbit.SellCoinMarket(upbit, coin_ticker, AllAmt)
                msg = coin_ticker + " 업비트 안전 전략 봇: 조건 불만족하여 모두 매도!! 현재 수익률: 약 " + str(round(revenue_data['revenue_rate'], 2)) + "% 수익금: 약 " + str(format(round(revenue_data['revenue_money']), ',')) + "원"
                print(msg)
                telegram_alert.SendMessage(msg)
                BotDataDict[coin_ticker + "_HAS"] = False
                BotDataDict[coin_ticker + "_SELL_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)

    # 잔고가 없는 경우
    else:
        print("아직 투자하지 않음")
        IsMaDone = False
        BUY_PRICE = 0
        ma1, ma2, ma3 = 3, 12, 24

        if coin_ticker == 'KRW-BTC':
            DolPaSt = max(df_day[str(ma1) + 'ma'].iloc[-2], df_day[str(ma2) + 'ma'].iloc[-2], df_day[str(ma3) + 'ma'].iloc[-2])
            if DolPaSt == df_day[str(ma3) + 'ma'].iloc[-2] and df_day['high'].iloc[-1] >= DolPaSt and df_day['open'].iloc[-1] < DolPaSt:
                if df_day['30ma_slope'].iloc[-2] > -4.0 and df_day['rsi_5ma'].iloc[-1] > df_day['rsi_5ma'].iloc[-2]:
                    BUY_PRICE = DolPaSt
                    IsDolpaDay = True
                    IsMaDone = True
            else: #일반매수 조건은 오전 9시 캔들 마감직후에만 적용 
                if (df_day['open'].iloc[-2] < df_day['close'].iloc[-2] and df_day['open'].iloc[-3] < df_day['close'].iloc[-3] and
                    df_day['close'].iloc[-3] < df_day['close'].iloc[-2] and df_day['high'].iloc[-3] < df_day['high'].iloc[-2] and
                    df_day['7ma'].iloc[-3] < df_day['7ma'].iloc[-2] and df_day['16ma'].iloc[-2] < df_day['close'].iloc[-2] and
                    df_day['73ma'].iloc[-2] < df_day['close'].iloc[-2] and df_day['30ma_slope'].iloc[-2] > -4.0 and
                    df_day['rsi_5ma'].iloc[-1] > df_day['rsi_5ma'].iloc[-2] and (hour_n == 0 and min_n <= 5)):
                    BUY_PRICE = NowCurrentPrice
                    IsDolpaDay = False
                    IsMaDone = True
            if not IsMaDone:
                DolpaRate = 0.7
                DolPaSt = df_day['open'].iloc[-1] + ((max(df_day['high'].iloc[-2], df_day['high'].iloc[-3]) - min(df_day['low'].iloc[-2], df_day['low'].iloc[-3])) * DolpaRate)
                if (df_day['high'].iloc[-1] >= DolPaSt and df_day['open'].iloc[-1] < DolPaSt and df_day[str(ma2) + 'ma'].iloc[-3] < df_day['close'].iloc[-2] and
                    df_day['low'].iloc[-3] < df_day['low'].iloc[-2] and df_day['rsi_ma'].iloc[-3] < df_day['rsi_ma'].iloc[-2] and
                    df_day[str(ma3) + 'ma'].iloc[-3] < df_day[str(ma2) + 'ma'].iloc[-2] < df_day[str(ma1) + 'ma'].iloc[-2] and
                    df_day['30ma_slope'].iloc[-2] > -4.0):
                    BUY_PRICE = DolPaSt
                    IsDolpaDay = True
                    IsMaDone = True

        if BotDataDict[coin_ticker + "_SELL_DATE"] == day_str:
            IsMaDone = False

        print("투자여부:",IsMaDone)

        if IsMaDone:

            print("돌파여부:",IsDolpaDay)

            Rate = 1.0
            BuyGoMoney = InvestMoneyCell * Rate
            if BuyGoMoney > df_day['value_ma'].iloc[-2] / 500:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 500
            if BuyGoMoney < minmunMoney:
                BuyGoMoney = minmunMoney
            BuyMoney = BuyGoMoney
            won = float(upbit.get_balance("KRW"))
            print("# Remain Won:", won)
            time.sleep(0.004)
            if BuyMoney > won:
                BuyMoney = won * 0.99
            if BuyMoney >= minmunMoney:
                balances = myUpbit.BuyCoinMarket(upbit, coin_ticker, BuyMoney)
                BotDataDict[coin_ticker + "_HAS"] = True
                BotDataDict[coin_ticker + "_BUY_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)
                msg = coin_ticker + " 업비트 안전 전략 봇: 조건 만족하여 매수!! " + str(BuyMoney) + "원어치 매수! (돌파:" + str(IsDolpaDay) + ")"
                print(msg)
                telegram_alert.SendMessage(msg)
        else:
            if hour_n == 0 and min_n <= 5:
                msg = coin_ticker + " 업비트 안전 전략 봇: 조건 만족하지 않아 현금 보유 합니다!"
                print(msg)
                telegram_alert.SendMessage(msg)

if hour_n == 0 and min_n < 5:
    telegram_alert.SendMessage("1.업비트 BTC 안전매매 정상 종료되었습니다")