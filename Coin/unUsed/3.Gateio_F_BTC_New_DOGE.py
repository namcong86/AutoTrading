#-*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Gate.io ccxt 버전
pip3 install --upgrade ccxt
이렇게 버전을 맞춰주세요!
봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요!
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

관련 포스팅 
https://blog.naver.com/zacra/223449598379
위 포스팅을 꼭 참고하세요!!!
하다가 잘 안되시면 계속 내용이 추가되고 있는 아래 FAQ를 꼭꼭 체크하시고
주식/코인 자동매매 FAQ
https://blog.naver.com/zacra/223203988739
그래도 안 된다면 구글링 해보시고
그래도 모르겠다면 클래스 댓글, 블로그 댓글, 단톡방에 질문주세요! ^^
'''

import ccxt
import time
import pandas as pd
import pprint
import ende_key
import my_key
import telegram_alert
import json
import socket
import sys
import datetime

# 암복호화 클래스 객체 생성 (바이낸스 코드와 동일한 방식으로 가정)
simpleEnDecrypt = None
try:
    import myGateIO
    simpleEnDecrypt = myGateIO.SimpleEnDecrypt(ende_key.ende_key)
except Exception as e:
    print("myGateIO 모듈 또는 SimpleEnDecrypt 클래스를 로드할 수 없습니다:", e)
    print("myGateIO.py 파일을 생성하거나 바이낸스 코드의 myBinance 모듈을 복사해 myGateIO로 수정해주세요.")
    sys.exit(1)

# Gate.io API 관련 함수
def get_gate_io_exchange(api_key, secret_key):
    """Gate.io 거래소 객체를 생성합니다."""
    return ccxt.gateio({
        'apiKey': api_key,
        'secret': secret_key,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'swap',  # Gate.io의 선물 거래 설정 (swap)
            'adjustForTimeDifference': True
        }
    })

# 페이지네이션을 활용하여 분봉/일봉 캔들 정보를 가져오는 함수
def GetOhlcv(exchange, Ticker, period='1d', limit=1000):
    """
    OHLCV 데이터를 가져오는 함수
    """
    try:
        ohlcv_data = exchange.fetch_ohlcv(Ticker, period, limit=limit)
        df = pd.DataFrame(ohlcv_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        print(f"데이터 가져오기 오류: {e}")
        return pd.DataFrame()  # 빈 데이터프레임 반환

# 현재가 조회
def GetCoinNowPrice(exchange, Ticker):
    """코인의 현재가 조회"""
    try:
        ticker = exchange.fetch_ticker(Ticker)
        return float(ticker['last'])
    except Exception as e:
        print(f"현재가 조회 오류: {e}")
        return 0

# 최소 주문 수량 계산 함수
def GetMinimumAmount(exchange, Ticker):
    try:
        market = exchange.market(Ticker)
        return float(market['limits']['amount']['min'])
    except Exception as e:
        print(f"최소 주문 수량 계산 오류: {e}")
        return 0.001  # 기본값 설정

# 주문 수량 계산 함수
def GetAmount(Money, Price, Leverage):
    try:
        return Money * Leverage / Price
    except Exception as e:
        print(f"주문 수량 계산 오류: {e}")
        return 0

# Gate.io API 키 설정
GateIO_AccessKey = ""
GateIO_SecretKey = ""

try:
    # 암호화된 키 정보 불러오기
    if my_key.gateio_access != "":
        GateIO_AccessKey = simpleEnDecrypt.decrypt(my_key.gateio_access).strip()
        GateIO_SecretKey = simpleEnDecrypt.decrypt(my_key.gateio_secret).strip()
except Exception as e:
    print("API 키 복호화 오류:", e)

# Gate.io 객체 생성
gateio = get_gate_io_exchange(GateIO_AccessKey, GateIO_SecretKey)

# 시간 정보
time_info = time.gmtime()
day_n = time_info.tm_mday
hour_n = time_info.tm_hour
min_n = time_info.tm_min
day_str = str(time_info.tm_year) + str(time_info.tm_mon) + str(time_info.tm_mday)
print("hour_n:", hour_n)
print("min_n:", min_n)

if hour_n == 0 and min_n <= 2:
    telegram_alert.SendMessage("Gate.io 레버리지 자동매매 봇 정상 시작 되었습니다")
    time.sleep(0.04)

pcServerGb = socket.gethostname()

# 봇 상태 저장 파일
BotDataDict = dict()
if pcServerGb == "AutoBotCong":
    # 서버
    botdata_file_path = "/var/AutoBot/json/GateIO_Data.json"
else:
    # PC
    botdata_file_path = "C:\\AutoTrading\\AutoTrading\\json\\GateIO_Data.json"

try:
    with open(botdata_file_path, 'r') as json_file:
        BotDataDict = json.load(json_file)
except Exception as e:
    print("Exception by First:", e)

# 인자 확인
# 레버리지 및 투자 비중
if len(sys.argv) > 1:
    param = sys.argv[1]  # 첫 번째 인자 (0번은 파일 이름)
    set_leverage = int(param)  # 파라미터로 전달 
    print("받은 파라미터:", param)
else:
    print("파라미터가 없습니다.")
    set_leverage = 5  # 기본 5배 레버리지

InvestRate = 1
fee = 0.002  # Gate.io 선물 수수료는 약 0.2% 적용

# 잔고 조회
try:
    balance = gateio.fetch_balance(params={"type": "swap"})
    time.sleep(0.1)
    TotalMoney = float(balance['USDT']['total'])
    print("TotalMoney", TotalMoney)
    InvestTotalMoney = TotalMoney * InvestRate
    print("InvestTotalMoney", InvestTotalMoney)
except Exception as e:
    print("잔고 조회 오류:", e)
    sys.exit(1)

# 투자 종목 설정
InvestCoinList = [
    {'ticker': 'DOGE/USDT:USDT', 'rate': 1.0}  # Gate.io의 선물 티커 형식으로 수정
]

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    print("\n----coin_ticker: ", coin_ticker)

    Target_Coin_Ticker = coin_ticker
    # Gate.io 티커 형식에 맞게 Target_Coin_Symbol 추출
    # DOGE/USDT:USDT -> DOGEUSDT
    Target_Coin_Symbol = coin_ticker.replace("/", "").replace(":USDT", "")

    # 포지션 정보 조회
    amt_b = 0
    entryPrice_b = 0
    leverage = 0
    isolated = True
    
    try:
        positions = gateio.fetch_positions([Target_Coin_Ticker])
        for posi in positions:
            if posi['side'] == 'long':  # Gate.io에서는 LONG 대신 long 사용
                amt_b = float(posi['contracts'])
                entryPrice_b = float(posi['entryPrice'])
                leverage = float(posi['leverage'])
                isolated = posi['marginMode'] == 'isolated'
                break
    except Exception as e:
        print("포지션 정보 조회 오류:", e)
        continue  # 다음 코인으로 넘어감

    # 레버리지 설정
    if set_leverage != leverage:
        try:
            print(f"레버리지 설정: {set_leverage}배")
            gateio.set_leverage(set_leverage, Target_Coin_Ticker)
        except Exception as e:
            print("레버리지 설정 오류:", e)

    # 교차 모드 설정 (Gate.io에서 지원하는 경우)
    if isolated:
        try:
            print("교차 모드로 설정 시도")
            # Gate.io API에 맞는 교차 모드 설정 메서드 사용
            # 각 거래소마다 교차 모드 설정 방법이 다르므로 거래소 API 문서 확인 필요
            gateio.set_margin_mode('cross', Target_Coin_Ticker)
        except Exception as e:
            print("교차 모드 설정 오류:", e)

    # 최소 주문 수량
    minimun_amount = GetMinimumAmount(gateio, Target_Coin_Ticker)

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
    df_day = GetOhlcv(gateio, coin_ticker, '1d')
    time.sleep(0.1)
    if df_day.empty:
        print(f"{coin_ticker} 데이터를 가져올 수 없습니다. 다음 코인으로 진행합니다.")
        continue
        
    df_day['value'] = df_day['volume']

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
    df_day['rsi_ma'] = df_day['rsi'].rolling(14).mean()
    df_day['rsi_5ma'] = df_day['rsi'].rolling(5).mean()

    # 이동평균선 계산
    for ma in [3, 7, 12, 16, 24, 30, 50, 73]:
        df_day[str(ma) + 'ma'] = df_day['close'].rolling(ma).mean()
    df_day['value_ma'] = df_day['value'].rolling(window=10).mean()
    df_day['30ma_slope'] = ((df_day['30ma'] - df_day['30ma'].shift(5)) / df_day['30ma'].shift(5)) * 100
    df_day.dropna(inplace=True)

    # 현재가
    NowCurrentPrice = GetCoinNowPrice(gateio, Target_Coin_Ticker)
    if NowCurrentPrice == 0:
        print(f"{Target_Coin_Ticker} 현재가 조회 실패. 다음 코인으로 진행합니다.")
        continue
    
    IsDolpBTCy = False
    DiffValue = -2

    # 잔고가 있는 경우
    if abs(amt_b) > 0:
        print("잔고가 있는 경우!")
        revenue_rate_b = (NowCurrentPrice - entryPrice_b) / entryPrice_b * 100.0
        
        # 미실현 손익 계산
        unrealizedProfit_b = 0
        try:
            positions = gateio.fetch_positions([Target_Coin_Ticker])
            for posi in positions:
                if posi['side'] == 'long':
                    unrealizedProfit_b = float(posi['unrealizedPnl'])
                    break
        except Exception as e:
            print("미실현 손익 계산 오류:", e)

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
            try:
                current_balance = float(gateio.fetch_balance(params={"type": "swap"})['USDT']['total'])
                if current_balance < TotalMoney / 3:
                    IsSellGo = True
                    IsDolpaCut = True
            except Exception as e:
                print("잔고 확인 오류:", e)

            BotDataDict[coin_ticker + "_DATE_CHECK"] = day_n
            with open(botdata_file_path, 'w') as outfile:
                json.dump(BotDataDict, outfile)

            if BotDataDict[coin_ticker + "_BUY_DATE"] == day_str:
                IsSellGo = False

            if IsSellGo:
                try:
                    # Gate.io에서 롱 포지션 청산 (매도)
                    # Gate.io는 포지션 사이드와 주문 타입이 다를 수 있으므로 API 문서 확인 필요
                    print(f"매도 주문 실행: {abs(amt_b)} {Target_Coin_Ticker}")
                    sell_order = gateio.create_order(Target_Coin_Ticker, 'market', 'sell', abs(amt_b))
                    
                    msg = coin_ticker + " Gate.io 안전 전략 봇: " + ("강제 청산" if IsDolpaCut else "조건 불만족") + "하여 모두 매도!! 현재 수익률: 약 " + str(round(revenue_rate_b * set_leverage, 2)) + "% 수익금: 약 " + str(format(round(unrealizedProfit_b), ',')) + "USDT"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                    
                    BotDataDict[coin_ticker + "_SELL_DATE"] = day_str
                    with open(botdata_file_path, 'w') as outfile:
                        json.dump(BotDataDict, outfile)
                except Exception as e:
                    print("매도 주문 오류:", e)

    # 잔고가 없는 경우
    else:
        print("아직 투자하지 않음")
        IsMaDone = False
        BUY_PRICE = 0
        ma1, ma2, ma3 = 3, 12, 24

        print(f"로그좀 보자  {df_day['high'].iloc[-2]}::::::{df_day['high'].iloc[-1]}")

        # 매수 조건
        if (df_day['open'].iloc[-2] < df_day['close'].iloc[-2] and df_day['open'].iloc[-3] < df_day['close'].iloc[-3] and
                df_day['close'].iloc[-3] < df_day['close'].iloc[-2] and df_day['high'].iloc[-3] < df_day['high'].iloc[-2] and
                df_day['7ma'].iloc[-3] < df_day['7ma'].iloc[-2] and df_day['50ma'].iloc[-3] < df_day['50ma'].iloc[-2] and 
                df_day['30ma_slope'].iloc[-2] > DiffValue and df_day['rsi_5ma'].iloc[-1] > df_day['rsi_5ma'].iloc[-2]):
                BUY_PRICE = NowCurrentPrice
                IsDolpBTCy = False
                IsMaDone = True
                

        # 당일 매도 기록이 있으면 매수하지 않음
        if BotDataDict[coin_ticker + "_SELL_DATE"] == day_str:
            IsMaDone = False

        # 매수 조건 만족 시 실행
        if IsMaDone:
            try:
                Rate = 1.0
                # 이동평균선 하락 시 투자 비율 감소
                if df_day['50ma'].iloc[-3] > df_day['50ma'].iloc[-2] or df_day['50ma'].iloc[-2] > df_day['close'].iloc[-2]:
                    Rate *= 0.5
                
                BuyGoMoney = InvestMoneyCell * Rate
                # 거래량 기반 투자 금액 조정
                if BuyGoMoney > df_day['value_ma'].iloc[-2] / 100:
                    BuyGoMoney = df_day['value_ma'].iloc[-2] / 100
                # 최소 투자 금액 설정
                if BuyGoMoney < 100:
                    BuyGoMoney = 100
                    
                BuyMoney = BuyGoMoney
                
                # 구매 수량 계산 (거래소 형식에 맞게 소수점 처리)
                Buy_Amt = float(gateio.amount_to_precision(Target_Coin_Ticker, GetAmount(BuyMoney, NowCurrentPrice, 1.0))) * set_leverage
                
                # 최소 주문 수량 보다 작으면 최소 수량으로 조정
                if minimun_amount > Buy_Amt:
                    Buy_Amt = minimun_amount
                
                # 매수 주문 실행
                print(f"매수 주문 실행: {Buy_Amt} {Target_Coin_Ticker}")
                buy_order = gateio.create_order(Target_Coin_Ticker, 'market', 'buy', Buy_Amt)
                
                # 매수 정보 저장
                BotDataDict[coin_ticker + "_BUY_DATE"] = day_str
                with open(botdata_file_path, 'w') as outfile:
                    json.dump(BotDataDict, outfile)
                
                # 텔레그램 알림
                msg = coin_ticker + " Gate.io 안전 전략 봇: 조건 만족하여 매수!! (돌파: " + str(IsDolpBTCy) + ")"
                print(msg)
                telegram_alert.SendMessage(msg)
                
            except Exception as e:
                print("매수 주문 오류:", e)
        else:
            # 정각에 현금 보유 알림
            if hour_n == 0 and min_n == 0:
                msg = coin_ticker + " Gate.io 안전 전략 봇: 조건 만족하지 않아 현금 보유 합니다!"
                print(msg)
                telegram_alert.SendMessage(msg)

# 프로그램 종료 알림
if hour_n == 0 and min_n <= 2:
    telegram_alert.SendMessage("Gate.io 레버리지 자동매매 봇 정상 종료 되었습니다")