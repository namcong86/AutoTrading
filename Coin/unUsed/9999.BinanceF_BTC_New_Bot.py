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
https://blog.naver.com/zacra/223449598379
위 포스팅을 꼭 참고하세요!!!
하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고
주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739
그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방( https://blog.naver.com/zacra/223111402375 )에 질문주세요! ^^
'''

import ccxt
import time
import pandas as pd
import pprint
import myBinance
import ende_key
import my_key
import telegram_alert
import json
import socket
import sys

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# 바이낸스 객체 생성
Binance_AccessKey = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_ScretKey = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"

# binance 객체 생성
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey, 
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# 시간 정보
time_info = time.gmtime()
day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min
day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)
print("hour_n:", hour_n)
print("min_n:", min_n)

if hour_n == 0 and min_n <= 2:
    telegram_alert.SendMessage("2.바이낸스 BTC 레버리지 정상 시작 되었습니다")
    time.sleep(0.04)

pcServerGb = socket.gethostname()

# 봇 상태 저장 파일
BotDataDict = dict()
if pcServerGb == "AutoBotCong" :
    #서버: 
    botdata_file_path = "/var/AutoBot/json/BinanceF_Data.json"
else:
    #PC
    botdata_file_path = "C:\\AutoTrading\\AutoTrading\\json\\BinanceF_Data.json"


try:
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)
except Exception as e:
    print("Exception by First")

# 인자 확인
# 레버리지 및 투자 비중
if len(sys.argv) > 1:
    param = sys.argv[1]  # 첫 번째 인자 (0번은 파일 이름)
    set_leverage = param  # 파라미터로 전달 
    print("받은 파라미터:", param)
else:
    print("파라미터가 없습니다.")
    set_leverage = 5  # 기본 5배 레버리지

InvestRate = 1
fee = 0.005  # 테스트 소스의 수수료 0.2%

# 잔고 조회
balance = binanceX.fetch_balance(params={"type": "future"})
time.sleep(0.1)
TotalMoney = float(balance['USDT']['total'])
print("TotalMoney", TotalMoney)
InvestTotalMoney = TotalMoney * InvestRate
print("InvestTotalMoney", InvestTotalMoney)

# 투자 종목 설정 (ETH/USDT 제거)
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1.0}
]

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    Target_Coin_Ticker = coin_ticker
    Target_Coin_Symbol = coin_ticker.replace("/", "").replace(":USDT","")

    # 포지션 정보 조회
    amt_b = 0
    entryPrice_b = 0
    leverage = 0
    isolated = True
    for posi in balance['info']['positions']:
        if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':
            amt_b = float(posi['positionAmt'])
            entryPrice_b = float(posi['entryPrice'])
            leverage = float(posi['leverage'])
            isolated = posi['isolated']
            break

    # 레버리지 설정
    if set_leverage != leverage:
        try:
            print(binanceX.fapiPrivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage}))
        except Exception as e:
            print("Exception Done OK..")

    # 교차 모드 설정
    if isolated:
        try:
            print(binanceX.fapiPrivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'CROSSED'}))
        except Exception as e:
            print("Exception Done OK..")

    # 최소 주문 수량
    minimun_amount = myBinance.GetMinimumAmount(binanceX, Target_Coin_Ticker)

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

    InvestMoney = InvestTotalMoney * coin_data['rate']
    print(coin_ticker, " 종목당 할당 투자금:", InvestMoney)
    InvestMoneyCell = InvestMoney * 0.995
    print("InvestMoneyCell: ", InvestMoneyCell)

    # 일봉 데이터 가져오기
    df_day = myBinance.GetOhlcv(binanceX, coin_ticker, '1d')
    time.sleep(0.1)
    df_day['value'] = df_day['close'] * df_day['volume']

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
    for ma in [3, 7, 12, 16, 24, 30, 50, 73]:
        df_day[str(ma) + 'ma'] = df_day['close'].rolling(ma).mean()
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()
    df_day['30ma_slope'] = ((df_day['30ma'] - df_day['30ma'].shift(5)) / df_day['30ma'].shift(5)) * 100
    df_day.dropna(inplace=True)

    # 현재가
    NowCurrentPrice = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)
    IsDolpBTCy = False
    DiffValue = -2

    # 잔고가 있는 경우
    if abs(amt_b) != 0:
        print("잔고가 있는 경우!")
        revenue_rate_b = (NowCurrentPrice - entryPrice_b) / entryPrice_b * 100.0
        unrealizedProfit_b = 0
        for posi in balance['info']['positions']:
            if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':
                unrealizedProfit_b = float(posi['unrealizedProfit'])
                break

        if BotDataDict[coin_ticker + "_DATE_CHECK"] != day_n:
            msg = coin_ticker + " 현재 수익률: 약 " + str(round(revenue_rate_b * set_leverage, 2)) + "% 수익금: 약 " + str(format(round(unrealizedProfit_b), ',')) + "USDT"
            print(msg)
            telegram_alert.SendMessage(msg)
            time.sleep(1.0)

            IsSellGo = False
            IsDolpaCut = False
            # 테스트 소스의 매도 조건
            if ((df_day['high'].iloc[-3] > df_day['high'].iloc[-2] and df_day['low'].iloc[-3] > df_day['low'].iloc[-2]) or
                (df_day['open'].iloc[-2] > df_day['close'].iloc[-2] and df_day['open'].iloc[-3] > df_day['close'].iloc[-3]) or
                revenue_rate_b * set_leverage < 0):
                IsSellGo = True
            if df_day['rsi_ma'].iloc[-3] < df_day['rsi_ma'].iloc[-2] and df_day['3ma'].iloc[-3] < df_day['3ma'].iloc[-2]:
                IsSellGo = False
            # 강제 청산
            current_balance = float(binanceX.fetch_balance(params={"type": "future"})['USDT']['total'])
            if current_balance < TotalMoney / 3:
                IsSellGo = True
                IsDolpaCut = True

            BotDataDict[coin_ticker + "_DATE_CHECK"] = day_n
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)

            if BotDataDict[coin_ticker + "_BUY_DATE"] == day_str:
                IsSellGo = False

            if IsSellGo:
                params = {'positionSide': 'LONG'}
                print(binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b), None, params))
                msg = coin_ticker + " 바이낸스 안전 전략 봇: " + ("강제 청산" if IsDolpaCut else "조건 불만족") + "하여 모두 매도!! 현재 수익률: 약 " + str(round(revenue_rate_b * set_leverage, 2)) + "% 수익금: 약 " + str(format(round(unrealizedProfit_b), ',')) + "USDT"
                print(msg)
                telegram_alert.SendMessage(msg)
                BotDataDict[coin_ticker + "_SELL_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)

    # 잔고가 없는 경우
    else:
        print("아직 투자하지 않음")
        IsMaDone = False
        BUY_PRICE = 0
        ma1, ma2, ma3 = 3, 12, 24

        # 테스트 소스의 매수 조건
        DolPaSt = max(df_day[str(ma1) + 'ma'].iloc[-2], df_day[str(ma2) + 'ma'].iloc[-2], df_day[str(ma3) + 'ma'].iloc[-2])
        if DolPaSt == df_day[str(ma3) + 'ma'].iloc[-2] and df_day['high'].iloc[-1] >= DolPaSt and df_day['open'].iloc[-1] < DolPaSt:
            if df_day['30ma_slope'].iloc[-2] > DiffValue and df_day['rsi_5ma'].iloc[-1] > df_day['rsi_5ma'].iloc[-2] and df_day['30ma'].iloc[-1] < DolPaSt:
                BUY_PRICE = DolPaSt
                IsDolpBTCy = True
                IsMaDone = True
        else:
            if (df_day['open'].iloc[-2] < df_day['close'].iloc[-2] and df_day['open'].iloc[-3] < df_day['close'].iloc[-3] and
                df_day['close'].iloc[-3] < df_day['close'].iloc[-2] and df_day['high'].iloc[-3] < df_day['high'].iloc[-2] and
                df_day['7ma'].iloc[-3] < df_day['7ma'].iloc[-2] and df_day['16ma'].iloc[-2] < df_day['close'].iloc[-2] and
                df_day['73ma'].iloc[-2] < df_day['close'].iloc[-2] and df_day['30ma_slope'].iloc[-2] > DiffValue and
                df_day['rsi_5ma'].iloc[-1] > df_day['rsi_5ma'].iloc[-2]):
                BUY_PRICE = NowCurrentPrice
                IsDolpBTCy = False
                IsMaDone = True
        if not IsMaDone:
            DolpaRate = 0.7
            DolPaSt = df_day['open'].iloc[-1] + ((max(df_day['high'].iloc[-2], df_day['high'].iloc[-3]) - min(df_day['low'].iloc[-2], df_day['low'].iloc[-3])) * DolpaRate)
            if (df_day['high'].iloc[-1] >= DolPaSt and df_day['open'].iloc[-1] < DolPaSt and df_day[str(ma2) + 'ma'].iloc[-3] < df_day['close'].iloc[-2] and
                df_day['low'].iloc[-3] < df_day['low'].iloc[-2] and df_day['rsi_ma'].iloc[-3] < df_day['rsi_ma'].iloc[-2] and
                df_day[str(ma3) + 'ma'].iloc[-3] < df_day[str(ma2) + 'ma'].iloc[-2] < df_day[str(ma1) + 'ma'].iloc[-2] and
                df_day['30ma_slope'].iloc[-2] > DiffValue and df_day['30ma'].iloc[-1] < DolPaSt):
                BUY_PRICE = DolPaSt
                IsDolpBTCy = True
                IsMaDone = True

        if BotDataDict[coin_ticker + "_SELL_DATE"] == day_str:
            IsMaDone = False

        if IsMaDone:
            Rate = 1.0
            if df_day['50ma'].iloc[-3] > df_day['50ma'].iloc[-2] or df_day['50ma'].iloc[-2] > df_day['close'].iloc[-2]:
                Rate *= 0.5
            BuyGoMoney = InvestMoneyCell * Rate
            if BuyGoMoney > df_day['value_ma'].iloc[-2] / 1000:
                BuyGoMoney = df_day['value_ma'].iloc[-2] / 1000
            if BuyGoMoney < 100:
                BuyGoMoney = 100
            BuyMoney = BuyGoMoney
            Buy_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(BuyMoney, NowCurrentPrice, 1.0))) * set_leverage
            if minimun_amount > Buy_Amt:
                Buy_Amt = minimun_amount
            params = {'positionSide': 'LONG'}
            data = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', Buy_Amt, None, params)
            BotDataDict[coin_ticker + "_BUY_DATE"] = day_str
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)
            msg = coin_ticker + " 바이낸스 안전 전략 봇: 조건 만족하여 매수!! (돌파: " + str(IsDolpBTCy) + ")"
            print(msg)
            telegram_alert.SendMessage(msg)
        else:
            if hour_n == 0 and min_n == 0:
                msg = coin_ticker + " 바이낸스 안전 전략 봇: 조건 만족하지 않아 현금 보유 합니다!"
                print(msg)
                telegram_alert.SendMessage(msg)


if hour_n == 0 and min_n <= 2:
        telegram_alert.SendMessage("2.바이낸스 BTC 레버리지 정상 종료 되었습니다")