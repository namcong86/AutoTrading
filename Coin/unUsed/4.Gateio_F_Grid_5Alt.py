#-*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Gate.io ccxt 버전
pip3 install --upgrade ccxt==4.2.19
이렇게 버전을 맞춰주세요!
봇은 단일 포지션 모드에서 동작합니다.
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

관련 포스팅 참고:
https://blog.naver.com/zacra/223449598379
주식/코인 자동매매 FAQ:
https://blog.naver.com/zacra/223203988739
'''

import ccxt
import time
import pandas as pd
import json
import socket
import sys
import logging
import datetime
import telegram_alert  # 바이낸스 코드에서 사용된 텔레그램 알림 모듈 (사용자가 별도로 설정 필요)
import hashlib
import hmac
import base64
import requests

# Gate.io Futures API 클래스
class GateioFuturesAPI:
    def __init__(self, api_key, api_secret, url='https://api.gateio.ws'):
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = url
        
    def _generate_signature(self, method, url, query_string='', body=''):
        t = time.time()
        m = hashlib.sha512()
        m.update((body or '').encode('utf-8'))
        hashed_payload = m.hexdigest()
        
        signing_str = method + '\n' + url + '\n' + query_string + '\n' + hashed_payload + '\n' + str(int(t))
        sign = hmac.new(self.api_secret.encode('utf-8'), signing_str.encode('utf-8'), hashlib.sha512).hexdigest()
        
        return {'KEY': self.api_key, 'Timestamp': str(int(t)), 'SIGN': sign}
    
    def get_futures_account(self, settle='usdt'):
        endpoint = f'/api/v4/futures/{settle}/accounts'
        method = 'GET'
        headers = self._generate_signature(method, endpoint)
        
        url = f"{self.url}{endpoint}"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error fetching futures account: {response.status_code} - {response.text}")
            return None

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_1d.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Gate.io 객체 생성
Gateio_AccessKey = "07a0ba2f6ed018fcb0fde7d08b58b40c"
Gateio_SecretKey = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"
gateio = ccxt.gate({
    'apiKey': Gateio_AccessKey,
    'secret': Gateio_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

# Gate.io Futures API 객체 생성
gateio_api = GateioFuturesAPI(Gateio_AccessKey, Gateio_SecretKey)

# 봇 상태 저장 파일
BotDataDict = dict()
pcServerGb = socket.gethostname()

if pcServerGb == "AutoBotCong":
    botdata_file_path = "/var/AutoBot/json/GateioF_1d_Data.json"
else:
    botdata_file_path = "C:\\AutoTrading\\AutoTrading\\json\\GateioF_1d_Data.json"

# JSON 파일 로드 및 초기화
try:
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)
except FileNotFoundError:
    logger.info(f"BotDataDict file not found. Creating new file: {botdata_file_path}")
    BotDataDict = {}
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)
except json.JSONDecodeError as e:
    logger.error(f"BotDataDict JSON decode error: {e}. Reinitializing file with empty dict.")
    BotDataDict = {}
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)
except Exception as e:
    logger.error(f"BotDataDict load error: {e}. Reinitializing file with empty dict.")
    BotDataDict = {}
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)

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
if (hour_n == 0 and min_n <= 2):
    msg = "2.Gate.io 일봉 단타봇 정상 시작 되었습니다."
    logger.info(msg)
    telegram_alert.SendMessage(msg)

InvestRate = 1.0  # 투자 비율
fee = 0.002  # 백테스팅 코드의 수수료(0.03%) 적용

# 잔고 조회
max_retries = 3
retry_delay = 5  # 초 단위

for attempt in range(max_retries):
    try:
        # Gate.io Futures API를 통해 잔고 조회
        account = gateio_api.get_futures_account(settle='usdt')
        logger.info(f"Raw account data: {account}")
        time.sleep(0.1)

        TotalMoney = 0
        if account and 'available' in account:
            TotalMoney = float(account['available'])
            logger.info("Found USDT balance in Perpetual Futures (Gate.io API).")
        else:
            logger.warning("No USDT balance found in Gate.io API response.")

        if TotalMoney == 0:
            logger.warning("No USDT balance available in Perpetual Futures. Retrying...")
            if attempt == max_retries - 1:
                logger.error("No USDT balance available after retries in Perpetual Futures. Cannot proceed with trading.")
                sys.exit(1)
            time.sleep(retry_delay)
            continue

        logger.info(f"Total Money: {TotalMoney}")
        InvestTotalMoney = TotalMoney * InvestRate
        logger.info(f"Invest Total Money: {InvestTotalMoney}")
        break
    except Exception as e:
        logger.error(f"Error fetching balance (attempt {attempt + 1}/{max_retries}): {e}")
        if attempt == max_retries - 1:
            logger.error("Cannot proceed without balance information. Exiting program.")
            sys.exit(1)
        time.sleep(retry_delay)

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'BTC/USDT:USDT', 'rate': 1.0}
]

# 최소 주문 수량 확인 함수
def GetMinimumAmount(exchange, ticker):
    try:
        markets = exchange.fetch_markets()
        for market in markets:
            if market['symbol'] == ticker:
                return float(market['limits']['amount']['min'])
        logger.error(f"Cannot find minimum amount for {ticker}")
        return 0.001  # 기본값 (BTC 기준)
    except Exception as e:
        logger.error(f"Error fetching minimum amount for {ticker}: {e}")
        return 0.001

# 현재가 조회 함수
def GetCoinNowPrice(exchange, ticker):
    try:
        ticker_data = exchange.fetch_ticker(ticker)
        return float(ticker_data['last'])
    except Exception as e:
        logger.error(f"Error fetching current price for {ticker}: {e}")
        return 0

# 일봉 데이터 가져오기 함수
def GetOhlcvRealTime(exchange, ticker, period='1d', limit=100):
    try:
        ohlcv = exchange.fetch_ohlcv(ticker, period, limit=limit, params={'future': True})
        df = pd.DataFrame(ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        logger.error(f"Error fetching OHLCV for {ticker}: {e}")
        return None

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    logger.info(f"\n---- Processing coin: {coin_ticker}")

    Target_Coin_Ticker = coin_ticker
    Target_Coin_Symbol = coin_ticker.replace("/", "").replace(":USDT", "")

    # 포지션 정보 조회
    amt_b = 0
    entryPrice_b = 0
    leverage = 0
    positions = gateio.fetch_positions([Target_Coin_Ticker], params={'type': 'swap'})

    for pos in positions:
        if pos['symbol'] == Target_Coin_Ticker:
            # 'dual_long' 포지션 찾기 (로그에서 보이는 값으로 판단)
            if pos['info'].get('mode') == 'dual_long':
                logger.info(f"포지션정보 {pos}")
                amt_b = float(pos['info']['value']) if pos['info'].get('value') else 0
                entryPrice_b = float(pos['info']['entry_price']) if pos['info'].get('entry_price') else 0
                leverage = float(pos['info']['leverage']) if pos['info'].get('leverage') else 0
                break


    # 레버리지 설정
    if set_leverage != leverage:
        try:
            gateio.set_leverage(set_leverage, Target_Coin_Ticker, params={'type': 'swap'})
            logger.info(f"Set leverage to {set_leverage} for {Target_Coin_Ticker}")
        except Exception as e:
            logger.error(f"Error setting leverage: {e}")

    # 최소 주문 수량
    minimun_amount = GetMinimumAmount(gateio, Target_Coin_Ticker)
    logger.info(f"최소주문가능수량 {Target_Coin_Ticker}: {minimun_amount}")

    # BotDataDict 초기화
    if BotDataDict.get(coin_ticker + "_BUY_DATE") is None:
        BotDataDict[coin_ticker + "_BUY_DATE"] = ""
    if BotDataDict.get(coin_ticker + "_SELL_DATE") is None:
        BotDataDict[coin_ticker + "_SELL_DATE"] = ""
    if BotDataDict.get(coin_ticker + "_DATE_CHECK") is None:
        BotDataDict[coin_ticker + "_DATE_CHECK"] = 0
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)

    InvestMoney = InvestTotalMoney * coin_data['rate']
    logger.info(f"{coin_ticker} Invest Money: {InvestMoney}")
    InvestMoneyCell = InvestMoney * (1 - fee)
    logger.info(f"Invest Money Cell (after fee): {InvestMoneyCell}")

    # 일봉 데이터 가져오기
    df = GetOhlcvRealTime(gateio, coin_ticker, '1d', 100)
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
    NowCurrentPrice = GetCoinNowPrice(gateio, Target_Coin_Ticker)
    IsDolpaDay = False
    DiffValue = -0.8  # 백테스팅 코드에서 사용된 값

    # 잔고가 있는 경우 (매도 로직)
    if abs(amt_b) > 0:
        logger.info("포지션이 있어 매도 조건 확인 중")
        revenue_rate_b = (NowCurrentPrice - entryPrice_b) / entryPrice_b * 100.0

        logger.info(f"revenue_rate_b: {revenue_rate_b}")

        unrealizedProfit_b = 0
        for pos in positions:
            if pos['symbol'] == Target_Coin_Ticker and pos['side'] == 'long':
                unrealizedProfit_b = float(pos['unrealizedPnl'])
                break

        if BotDataDict[coin_ticker + "_DATE_CHECK"] != day_n:
            msg = f"2.Gate.io 일봉 단타봇 현재수익률: {round(revenue_rate_b * set_leverage, 2)}% 수익금: {format(round(unrealizedProfit_b,2), ',')} USDT"
            logger.info(msg)
            telegram_alert.SendMessage(msg)
            BotDataDict[coin_ticker + "_DATE_CHECK"] = day_n
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile, indent=4)

        IsSellGo = False
        IsDolpaCut = False
        if ((df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2]) or
            (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3]) or
            (revenue_rate_b * set_leverage < 0.5)):
            IsSellGo = True
        # if df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2]:
        #     IsSellGo = False
        # 강제 청산 조건
        current_account = gateio_api.get_futures_account(settle='usdt')
        current_balance = float(current_account['isolated_position_margin']) if current_account and 'isolated_position_margin' in current_account else 0
        # if current_balance < TotalMoney / 3:
        #     IsSellGo = True
        #     IsDolpaCut = True

        if BotDataDict[coin_ticker + "_BUY_DATE"] == day_str:
            IsSellGo = False

        if IsSellGo:
            logger.info(f"아오: {amt_b}")
            order = gateio.create_market_sell_order(Target_Coin_Ticker, current_balance, params={'type': 'swap','reduce_only': True})
            msg = f"2.Gate.io 일봉 단타봇 매도! => 수익률: {round(revenue_rate_b * set_leverage, 2)}% 수익금: {format(round(unrealizedProfit_b,2), ',')} USDT"
            logger.info(msg)
            telegram_alert.SendMessage(msg)
            BotDataDict[coin_ticker + "_SELL_DATE"] = day_str
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile, indent=4)
            amt_b = 0  # 포지션 초기화

    # 잔고가 없는 경우 (매수 로직)
    else:
        logger.info("포지션이 없어 매수 조건 확인 중")
        IsMaDone = False
        BUY_PRICE = 0
        ma1, ma2, ma3 = 3, 12, 24

        if df is None or len(df) < 3:
            logger.error("Dataframe is not properly initialized or insufficient data for buy conditions.")
            time.sleep(60)
            continue

        print(f"df['open'].iloc[-2] < df['close'].iloc[-2]: {df['open'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['open'].iloc[-3] < df['close'].iloc[-3]: {df['open'].iloc[-3] < df['close'].iloc[-3]}")
        print(f"df['close'].iloc[-3] < df['close'].iloc[-2]: {df['close'].iloc[-3] < df['close'].iloc[-2]}")
        print(f"df['high'].iloc[-3] < df['high'].iloc[-2]: {df['high'].iloc[-3] < df['high'].iloc[-2]}")
        print(f"df['7ma'].iloc[-3] < df['7ma'].iloc[-2]: {df['7ma'].iloc[-3] < df['7ma'].iloc[-2]}")
        print(f"df['16ma'].iloc[-2] < df['close'].iloc[-2]: {df['16ma'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['53ma'].iloc[-2] < df['close'].iloc[-2]: {df['53ma'].iloc[-2] < df['close'].iloc[-2]}")
        print(f"df['30ma_slope'].iloc[-2] > DiffValue: {df['30ma_slope'].iloc[-2] > DiffValue}")
        print(f"df['rsi_5ma'].iloc[-1] > df['rsi_5ma'].iloc[-2]: {df['rsi_5ma'].iloc[-1] > df['rsi_5ma'].iloc[-2]}")

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
                BuyGoMoney = InvestMoneyCell * Rate
                if BuyGoMoney > df['value_ma'].iloc[-2] / 500:
                    BuyGoMoney = df['value_ma'].iloc[-2] / 500
                if BuyGoMoney < 50:
                    BuyGoMoney = 50
                BuyMoney = BuyGoMoney

                print("하하하하",BuyGoMoney)
                Buy_Amt = float(BuyMoney / NowCurrentPrice) * set_leverage
                print("하하하하2",minimun_amount)
                print("하하하하3",Buy_Amt)
                print("하하하하4",set_leverage)
                if 0.001 > Buy_Amt:
                    Buy_Amt = 0.001
                order = gateio.create_market_buy_order(Target_Coin_Ticker, float(BuyGoMoney/2), params={'type': 'swap'})
                msg = f"2.Gate.io 일봉 단타봇 포지션롱 진입! => 수량: {Buy_Amt} 가격: {BUY_PRICE}"
                logger.info(msg)
                telegram_alert.SendMessage(msg)
                BotDataDict[coin_ticker + "_BUY_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile, indent=4)
                amt_b = Buy_Amt  # 포지션 업데이트

if (hour_n == 0 and min_n <= 2):
    msg = "2.Gate.io 일봉 단타봇 정상 종료 되었습니다."
    logger.info(msg)
    telegram_alert.SendMessage(msg)