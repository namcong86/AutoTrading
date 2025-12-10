# -*- coding:utf-8 -*-
'''
Binance 선물 운영 봇 (DOGE + 1000PEPE 50:50, 매수/매도 조건 동일)
'''
import ccxt
import time
import pandas as pd
import json
import socket
import sys
import os
from datetime import datetime
import builtins

# 원본 print 함수 저장 및 타임스탬프 포함 print 함수 정의
_original_print = builtins.print

def timestamped_print(*args, **kwargs):
    """타임스탬프가 포함된 로그 출력 함수"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

# 전역 print 함수를 타임스탬프 버전으로 교체
builtins.print = timestamped_print

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    sys.path.insert(0, "/var/AutoBot/Common")
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))
import myBinance
import telegram_alert
import ende_key
import my_key

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# 암호화된 액세스키와 시크릿키 복호화
Binance_AccessKey = simpleEnDecrypt.decrypt(my_key.binance_access_S3)
Binance_ScretKey = simpleEnDecrypt.decrypt(my_key.binance_secret_S3)

binanceX = ccxt.binance({
    'apiKey': Binance_AccessKey,
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    botdata_file_path = "/var/AutoBot/json/2.Binance_F_BTC_Leverage_Data.json"
else:
    botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', '2.Binance_F_BTC_Leverage_Data.json')

try:
    with open(botdata_file_path, 'r') as f:
        BotDataDict = json.load(f)
except:
    BotDataDict = {}

if len(sys.argv) > 1:
    set_leverage = int(sys.argv[1])
else:
    set_leverage = 2.5

InvestRate = 0.01  # 0.1%
fee = 0.001  # 0.2%

#알림 첫문구
first_String = f"2.Binance BTC {set_leverage}배 "

t = time.gmtime()
hour_n = t.tm_hour
min_n = t.tm_min
day_n = t.tm_mday
day_str = f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"

if hour_n == 0 and min_n <= 2:
    start_msg = f"📢 {first_String} 시작"
    telegram_alert.SendMessage(start_msg)

# 투자 종목: BTC- 100 비중
InvestCoinList = [
    {'ticker': 'BTC/USDT', 'rate': 1}
]



# ----- 여기서부터 전체 포지션 체크 변수를 선언 -----


for coin_data in InvestCoinList:

    # balance를 루프 안에서만 가져오면 여러 번 호출하니, 루프 전에 한 번만 호출
    balance = binanceX.fetch_balance(params={"type": "future"})
    time.sleep(0.1)
    total_usdt = float(balance['USDT']['free'])

    coin_ticker = coin_data['ticker']

    # BotData 기본 키 초기화
    for key in ["_BUY_DATE", "_SELL_DATE", "_DATE_CHECK"]:
        full_key = coin_ticker + key
        if full_key not in BotDataDict:
            BotDataDict[full_key] = "" if key != "_DATE_CHECK" else 0
    with open(botdata_file_path, 'w') as f:
        json.dump(BotDataDict, f)

    # 전체 포지션 중 하나라도 존재하면 True
    any_position_exist = False

    # 포지션 정보 (LONG)
    amt_b = 0; unrealizedProfit = 0.0
    for pos in balance['info']['positions']:
        any_position_exist = True
        if pos['symbol'] == coin_ticker.replace("/", ""):
            amt_b = float(pos['positionAmt'])
            unrealizedProfit = float(pos['unrealizedProfit'])
            break

    # 지표용 일봉 데이터 조회
    df = myBinance.GetOhlcv(binanceX, coin_ticker, '1d')
    df['value'] = df['close'] * df['volume']

    # RSI 계산
    period = 14
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    gain = up.ewm(com=period-1, min_periods=period).mean()
    loss = down.ewm(com=period-1, min_periods=period).mean()
    RS = gain / loss
    df['rsi'] = 100 - (100 / (1 + RS))
    df['rsi_ma'] = df['rsi'].rolling(14).mean()

    # MACD 계산
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # 이동평균선
    for ma in [3, 5, 12, 20, 24, 30, 60]:
        df[f'{ma}ma'] = df['close'].rolling(ma).mean()
    df['value_ma'] = df['value'].rolling(10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    df.dropna(inplace=True)

    now_price = myBinance.GetCoinNowPrice(binanceX, coin_ticker)
    DiffValue = -2
    params = {'positionSide': 'LONG'}

    # --- 매도 로직 (포지션 보유 시) ---
    if abs(amt_b) > 0:
        cond_high_low = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
        cond_open_close = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
        cond_revenue = (unrealizedProfit < 0)
        cond_cancel = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])
        analysis_msg = f"📉 매도 조건 분석 ({coin_ticker})\n"
        analysis_msg += f"• 고점저점하락: {'✅' if cond_high_low else '⚪'}\n"
        analysis_msg += f"• 시가종가하락: {'✅' if cond_open_close else '⚪'}\n"
        analysis_msg += f"• 손실상태: {'✅' if cond_revenue else '⚪'}\n"
        analysis_msg += f"• RSI취소조건: {'❗' if cond_cancel else '⚪'}"
        telegram_alert.SendMessage(analysis_msg)
        sell = (cond_high_low or cond_open_close or cond_revenue) and not cond_cancel
        if BotDataDict[coin_ticker + '_DATE_CHECK'] == day_n:
            sell = False
        if sell:
            binanceX.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params)
            
            exec_msg = f"🔴 매도 체결 알림 ({coin_ticker})\n"
            exec_msg += f"• 사유: 매도 조건 만족\n"
            exec_msg += f"• 수익률: {unrealizedProfit:.2f}%"
            
            print(exec_msg)
            telegram_alert.SendMessage(exec_msg)
            BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
            BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
            with open(botdata_file_path, 'w') as f:
                json.dump(BotDataDict, f)
    # --- 매수 로직 (포지션 없음) ---
    else:
        #MACD 조건
        macd_3ago = df['macd'].iloc[-4]-df['macd_signal'].iloc[-4]
        macd_2ago = df['macd'].iloc[-3]-df['macd_signal'].iloc[-3]
        macd_1ago = df['macd'].iloc[-2]-df['macd_signal'].iloc[-2]
        macd_positive = macd_1ago > 0
        macd_3to2_down = macd_3ago > macd_2ago
        macd_2to1_down = macd_2ago > macd_1ago
        macd_condition = not (macd_3to2_down and macd_2to1_down)

        cond_o1 = (df['open'].iloc[-2] < df['close'].iloc[-2])
        cond_o2 = (df['open'].iloc[-3] < df['close'].iloc[-3])
        cond_close_inc = (df['close'].iloc[-3] < df['close'].iloc[-2])
        #cond_high_inc = (df['high'].iloc[-3] < df['high'].iloc[-2])
        cond_5ma = (df['5ma'].iloc[-3] < df['5ma'].iloc[-2])
        cond_5ma_bf = (df['5ma'].iloc[-4] < df['5ma'].iloc[-3])
        cond_20ma = (df['20ma'].iloc[-3] < df['close'].iloc[-2])
        cond_60ma = (df['60ma'].iloc[-3] < df['close'].iloc[-2])
        cond_slope = (df['30ma_slope'].iloc[-2] > DiffValue)
        cond_rsi_inc = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2])
        cond_MACD = (macd_positive and macd_condition)

        analysis_msg = f"📈 매수 조건 분석 ({coin_ticker})\n"
        analysis_msg += f"• 연속양봉: {'✅' if cond_o1 and cond_o2 else '⚪'}\n"
        analysis_msg += f"• 종가상승: {'✅' if cond_close_inc else '⚪'}\n"
        analysis_msg += f"• 5이평상승: {'✅' if cond_5ma else '⚪'}\n"
        analysis_msg += f"• 5이평전전일: {'✅' if cond_5ma_bf else '⚪'}\n"
        analysis_msg += f"• 20이평위: {'✅' if cond_20ma else '⚪'}\n"
        analysis_msg += f"• 60이평위: {'✅' if cond_60ma else '⚪'}\n"
        analysis_msg += f"• 30이평기울기: {'✅' if cond_slope else '⚪'}\n"
        analysis_msg += f"• RSI증가: {'✅' if cond_rsi_inc else '⚪'}\n"
        analysis_msg += f"• MACD조건: {'✅' if cond_MACD else '⚪'}"
        
        telegram_alert.SendMessage(analysis_msg)
        buy = cond_o1 and cond_o2 and cond_close_inc and cond_5ma and cond_5ma_bf and cond_20ma and cond_60ma and cond_slope and cond_rsi_inc and cond_MACD
        if buy:
            if BotDataDict[coin_ticker + '_BUY_DATE'] != day_str:
                # ------ 여기서 투자금액 결정! ------
                if not any_position_exist:
                    InvestMoney = total_usdt * InvestRate * coin_data['rate']
                else:
                    InvestMoney = total_usdt * InvestRate
                # ----------------------------------
                BuyMoney = InvestMoney * (1.0 - fee * set_leverage)
                cap = df['value_ma'].iloc[-2] / 10
                BuyMoney = min(max(BuyMoney, 10), cap)
                amount = float(binanceX.amount_to_precision(coin_ticker, myBinance.GetAmount(BuyMoney, now_price, 1.0))) * set_leverage

                #강제 cross 마진 모드 및 레버리지 변경
                market_symbol = coin_ticker.replace("/", "")
                try:
                    binanceX.set_margin_mode('cross', market_symbol, params={'leverage': 5})
                except Exception as e:
                    print(f"마진모드/레버리지 세팅 오류: {e}")

                try:
                    binanceX.set_leverage(5, market_symbol)
                except Exception as e:
                    print(f"레버리지 세팅 오류: {e}")

                binanceX.create_order(coin_ticker, 'market', 'buy', amount, None, params)
                BotDataDict[coin_ticker + '_BUY_DATE'] = day_str
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)
                exec_msg = f"🟢 매수 체결 알림 ({coin_ticker})\n"
                exec_msg += f"• 매수금액: {BuyMoney:.2f} $\n"
                exec_msg += f"• 레버리지: {set_leverage}배"
                print(exec_msg)
                telegram_alert.SendMessage(exec_msg)
        else:
            if hour_n == 0 and min_n == 0 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                warn_msg = f"💤 관망 모드 ({coin_ticker})\n• 매수 조건을 만족하지 않아 현금을 보유합니다."
                print(warn_msg)
                telegram_alert.SendMessage(warn_msg)
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)

if hour_n == 0 and min_n <= 2:
    end_msg = f"🏁 {first_String} 종료"
    telegram_alert.SendMessage(end_msg)
