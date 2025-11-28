# -*-coding:utf-8 -*-
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
'''

import ccxt
import time
import pandas as pd
import json
import socket
import sys
import logging
import myBinance
import ende_key
import my_key
import telegram_alert
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_15m.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# 바이낸스 객체 생성
Binance_AccessKey = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_ScretKey = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"
binanceX = ccxt.binance(config={
    'apiKey': Binance_AccessKey,
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

# 봇 상태 저장 파일
BotDataDict = dict()
pcServerGb = socket.gethostname()
if pcServerGb == "congsnas":
    botdata_file_path = "/var/AutoBot/json/BinanceF_15m_Data.json"
else:
    botdata_file_path = "C:\\AutoTrading\\AutoTrading\\json\\BinanceF_15m_Data.json"

try:
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)
except Exception as e:
    logger.error(f"BotDataDict load error: {e}")

# 인자 확인 (레버리지 설정)
if len(sys.argv) > 1:
    set_leverage = int(sys.argv[1])
    logger.info(f"Received leverage parameter: {set_leverage}")
else:
    set_leverage = 5
    logger.info("No leverage parameter provided, using default: 5")


# 시간 정보
time_info = time.gmtime()
day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min
day_str = str(time_info.tm_year) + str(time_info.tm_mon).zfill(2) + str(time_info.tm_mday).zfill(2)

    # 봇 시작 알림
if (hour_n == 0 and min_n <= 2) or (hour_n == 10 and min_n <= 2):  #오전9시 오후 6시 마다 알림
    msg = "3.바이낸스 15분 단타봇 정상 시작 되었습니다."
    logger.info(msg)
    telegram_alert.SendMessage(msg)

InvestRate = 1.0  #투자비율
fee = 0.0003  # 백테스팅 코드의 수수료(0.03%) 적용

# 잔고 조회
balance = binanceX.fetch_balance(params={"type": "future"})
time.sleep(0.1)
TotalMoney = float(balance['USDT']['total'])
logger.info(f"Total Money: {TotalMoney}")
InvestTotalMoney = TotalMoney * InvestRate
logger.info(f"Invest Total Money: {InvestTotalMoney}")

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1.0}
]

# 15분봉 데이터 가져오기 함수
def GetOhlcvRealTime(binance, ticker, period='15m', limit=100):
    try:
        ohlcv = binance.fetch_ohlcv(ticker, period, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {ticker}: {e}")
        return None

# 메인 루프
for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    logger.info(f"\n---- Processing coin: {coin_ticker}")

    Target_Coin_Ticker = coin_ticker
    Target_Coin_Symbol = coin_ticker.replace("/", "").replace(":USDT", "")

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
            binanceX.fapiPrivate_post_leverage({'symbol': Target_Coin_Symbol, 'leverage': set_leverage})
            logger.info(f"Set leverage to {set_leverage} for {Target_Coin_Symbol}")
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")

    # 헤지 모드 설정 (CROSSED)
    # if isolated:
    #     try:
    #         binanceX.fapiPrivate_post_margintype({'symbol': Target_Coin_Symbol, 'marginType': 'CROSSED'})
    #         logger.info(f"Set margin type to CROSSED for {Target_Coin_Symbol}")
    #     except Exception as e:
    #         logger.error(f"Error setting margin type: {e}")

    # 최소 주문 수량
    minimun_amount = myBinance.GetMinimumAmount(binanceX, Target_Coin_Ticker)
    logger.info(f"최소주문가능수량 {Target_Coin_Ticker}: {minimun_amount}")

    # BotDataDict 초기화
    if BotDataDict.get(coin_ticker + "_BUY_DATE") is None:
        BotDataDict[coin_ticker + "_BUY_DATE"] = ""
    if BotDataDict.get(coin_ticker + "_SELL_DATE") is None:
        BotDataDict[coin_ticker + "_SELL_DATE"] = ""
    if BotDataDict.get(coin_ticker + "_DATE_CHECK") is None:
        BotDataDict[coin_ticker + "_DATE_CHECK"] = 0
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile)

    InvestMoney = InvestTotalMoney * coin_data['rate']
    logger.info(f"{coin_ticker} Invest Money: {InvestMoney}")
    InvestMoneyCell = InvestMoney * (1 - fee)
    logger.info(f"Invest Money Cell (after fee): {InvestMoneyCell}")


    # 15분봉 데이터 가져오기
    df = GetOhlcvRealTime(binanceX, coin_ticker, '15m', 100)
    if df is None or len(df) < 50:
        logger.error("Insufficient data, retrying...")
        time.sleep(60)
        continue

    # RSI 계산
    period = 14
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period - 1), min_periods=period).mean()
    _loss = down.abs().ewm(com=(period - 1), min_periods=period).mean()
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df['rsi_ma'] = df['rsi'].rolling(10).mean()
    df['rsi_5ma'] = df['rsi'].rolling(5).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['value'] = df['close'] * df['volume']

    # 이동평균선 계산
    for ma in range(3, 61):
        df[str(ma) + 'ma'] = df['close'].rolling(ma).mean()
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    df.dropna(inplace=True)

    # 현재가
    NowCurrentPrice = myBinance.GetCoinNowPrice(binanceX, Target_Coin_Ticker)
    IsDolpaDay = False
    DiffValue = -0.8  # 백테스팅 코드에서 사용된 값

    # 잔고가 있는 경우 (매도 로직)
    if abs(amt_b) > 0:
        logger.info("포지션이 있어 매도 조건 확인 중")
        revenue_rate_b = (NowCurrentPrice - entryPrice_b) / entryPrice_b * 100.0
        unrealizedProfit_b = 0
        for posi in balance['info']['positions']:
            if posi['symbol'] == Target_Coin_Symbol and posi['positionSide'] == 'LONG':
                unrealizedProfit_b = float(posi['unrealizedProfit'])
                break

        if BotDataDict[coin_ticker + "_DATE_CHECK"] != day_n:
            msg = f"3.바이낸스 15분 단타봇 현재수익률: {round(revenue_rate_b * set_leverage, 2)}% 수익금: {format(round(unrealizedProfit_b,2), ',')} USDT"
            logger.info(msg)
            telegram_alert.SendMessage(msg)
            BotDataDict[coin_ticker + "_DATE_CHECK"] = day_n
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)

        IsSellGo = False
        IsDolpaCut = False
        # 백테스팅 매도 조건
        if ((df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2]) or
            (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3]) or
            (revenue_rate_b * set_leverage < 0.5)):
            IsSellGo = True
        if df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2]:
            IsSellGo = False
        # 강제 청산 조건
        current_balance = float(binanceX.fetch_balance(params={"type": "future"})['USDT']['total'])
        if current_balance < TotalMoney / 3:
            IsSellGo = True
            IsDolpaCut = True

        if BotDataDict[coin_ticker + "_BUY_DATE"] == day_str:
            IsSellGo = False

        if IsSellGo:
            params = {'positionSide': 'LONG'}
            order = binanceX.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b), None, params)
            msg = f"3.바이낸스 15분 단타봇 매도! => 수익률: {round(revenue_rate_b * set_leverage, 2)}% 수익금: {format(round(unrealizedProfit_b,2), ',')} USDT"
            logger.info(msg)
            telegram_alert.SendMessage(msg)
            BotDataDict[coin_ticker + "_SELL_DATE"] = day_str
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)
            amt_b = 0  # 포지션 초기화

    # 잔고가 없는 경우 (매수 로직)
    else:
        logger.info("포지션이 없어 매수 조건 확인 중")
        IsMaDone = False
        BUY_PRICE = 0
        ma1, ma2, ma3 = 3, 12, 24

        print(f"df['open'].iloc[-2] < df['close'].iloc[-2]:{df['open'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['open'].iloc[-3] < df['close'].iloc[-3]:{df['open'].iloc[-3] < df['close'].iloc[-3]}")
        print(f"df['close'].iloc[-3] < df['close'].iloc[-2]:{df['close'].iloc[-3] < df['close'].iloc[-2]}")
        print(f"df['high'].iloc[-3] < df['high'].iloc[-2]:{df['high'].iloc[-3] < df['high'].iloc[-2]}")
        print(f"df['7ma'].iloc[-3] < df['7ma'].iloc[-2]:{df['7ma'].iloc[-3] < df['7ma'].iloc[-2]}")
        print(f"df['16ma'].iloc[-2] < df['close'].iloc[-2]:{df['16ma'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['53ma'].iloc[-2] < df['close'].iloc[-2]:{df['53ma'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['30ma_slope'].iloc[-2] > DiffValue:{df['30ma_slope'].iloc[-2] > DiffValue}")
        print(f"df['rsi_5ma'].iloc[-1] > df['rsi_5ma'].iloc[-2]):{df['rsi_5ma'].iloc[-1] > df['rsi_5ma'].iloc[-2]}")


        # 백테스팅 매수 조건
        DolPaSt = max(df[str(ma1) + 'ma'].iloc[-2], df[str(ma2) + 'ma'].iloc[-2], df[str(ma3) + 'ma'].iloc[-2])
        if (df['open'].iloc[-2] < df['close'].iloc[-2] and
            df['open'].iloc[-3] < df['close'].iloc[-3] and
            df['close'].iloc[-3] < df['close'].iloc[-2] and
            df['high'].iloc[-3] < df['high'].iloc[-2] and
            df['7ma'].iloc[-3] < df['7ma'].iloc[-2] and
            df['16ma'].iloc[-2] < df['close'].iloc[-2] and
            df['53ma'].iloc[-2] < df['close'].iloc[-2] and
            df['30ma_slope'].iloc[-2] > DiffValue and
            df['rsi_5ma'].iloc[-1] > df['rsi_5ma'].iloc[-2]):
            BUY_PRICE = NowCurrentPrice
            IsDolpaDay = False
            IsMaDone = True

            if BotDataDict[coin_ticker + "_SELL_DATE"] == day_str:
                IsMaDone = False
            
            if IsMaDone:
                Rate = 1.0
                # if df['50ma'].iloc[-3] > df['50ma'].iloc[-2] or df['50ma'].iloc[-2] > df['close'].iloc[-2]:
                #     Rate *= 0.5
                BuyGoMoney = InvestMoneyCell * Rate
                if BuyGoMoney > df['value_ma'].iloc[-2] / 500:
                    BuyGoMoney = df['value_ma'].iloc[-2] / 500
                if BuyGoMoney < 50:
                    BuyGoMoney = 50
                BuyMoney = BuyGoMoney
                Buy_Amt = float(binanceX.amount_to_precision(Target_Coin_Ticker, myBinance.GetAmount(BuyMoney, NowCurrentPrice, 1.0))) * set_leverage
                if minimun_amount > Buy_Amt:
                    Buy_Amt = minimun_amount
                params = {'positionSide': 'LONG'}
                order = binanceX.create_order(Target_Coin_Ticker, 'market', 'buy', Buy_Amt, None, params)
                msg = f"3.바이낸스 15분 단타봇 포지션롱 진입! => 수량: {Buy_Amt} 가격: {BUY_PRICE}"
                logger.info(msg)
                telegram_alert.SendMessage(msg)
                BotDataDict[coin_ticker + "_BUY_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)
                amt_b = Buy_Amt  # 포지션 업데이트


if (hour_n == 0 and min_n <= 2) or (hour_n == 10 and min_n <= 2):  #오전9시 오후 6시 마다 알림
    msg = "3.바이낸스 15분 단타봇 정상 종료 되었습니다."
    logger.info(msg)
    telegram_alert.SendMessage(msg)