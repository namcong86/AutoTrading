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
import myBinance
import telegram_alert

# 바이낸스 API 키 (실제 키는 보안상 환경변수 사용 권장)
Binance_AccessKey = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_ScretKey = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"

binanceX = ccxt.binance({
    'apiKey': Binance_AccessKey,
    'secret': Binance_ScretKey,
    'enableRateLimit': True,
    'options': {'defaultType': 'future'}
})

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    botdata_file_path = "/var/AutoBot/json/BinanceF_DOGE_PEPE_Data.json"
else:
    botdata_file_path = "./BinanceF_DOGE_PEPE_Data.json"

try:
    with open(botdata_file_path, 'r') as f:
        BotDataDict = json.load(f)
except:
    BotDataDict = {}

if len(sys.argv) > 1:
    set_leverage = int(sys.argv[1])
else:
    set_leverage = 5

InvestRate = 1  # 0.1%
fee = 0.001  # 0.2%

t = time.gmtime()
hour_n = t.tm_hour
min_n = t.tm_min
day_n = t.tm_mday
day_str = f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"

if hour_n == 0 and min_n <= 2:
    start_msg = f"[BinanceF_DOGE+PEPE] 전략 봇 시작 - 레버리지 {set_leverage}배"
    telegram_alert.SendMessage(start_msg)

# 투자 종목: DOGE, 1000PEPE - 50:50 비중
InvestCoinList = [
    {'ticker': 'DOGE/USDT', 'rate': 0.5},
    {'ticker': '1000PEPE/USDT', 'rate': 0.5}
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
    for ma in [3, 7, 12, 24, 30, 50]:
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
        analysis_msg = (f"{coin_ticker} 매도조건 분석: high_low={cond_high_low}, "
                         f"open_close={cond_open_close}, revenue<0={cond_revenue}, "
                         f"cancel_by_rsi_ma={cond_cancel}")
        telegram_alert.SendMessage(analysis_msg)
        sell = (cond_high_low or cond_open_close or cond_revenue) and not cond_cancel
        if BotDataDict[coin_ticker + '_DATE_CHECK'] == day_n:
            sell = False
        if sell:
            binanceX.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params)
            exec_msg = f"{coin_ticker} 바이낸스 전략 봇: 조건 만족하여 매도!! (수익금: {unrealizedProfit:.2f}%)"
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

        # 전일캔들이 윗꼬리가 긴 도지형캔들이면 매수x
        prev_high = df['high'].iloc[-2]
        prev_low = df['low'].iloc[-2]
        prev_open = df['open'].iloc[-2]
        prev_close = df['close'].iloc[-2]
        upper_shadow = prev_high - max(prev_open, prev_close)
        candle_length = prev_high - prev_low
        upper_shadow_ratio = (upper_shadow / candle_length) if candle_length > 0 else 0

        cond_o1 = (df['open'].iloc[-2] < df['close'].iloc[-2])
        cond_o2 = (df['open'].iloc[-3] < df['close'].iloc[-3])
        cond_close_inc = (df['close'].iloc[-3] < df['close'].iloc[-2])
        cond_high_inc = (df['high'].iloc[-3] < df['high'].iloc[-2])
        cond_7ma = (df['7ma'].iloc[-3] < df['7ma'].iloc[-2])
        cond_50ma = (df['50ma'].iloc[-3] < df['50ma'].iloc[-2])
        cond_slope = (df['30ma_slope'].iloc[-2] > DiffValue)
        cond_rsi_inc = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2])
        cond_MACD = (macd_positive and macd_condition)
        cond_doji = upper_shadow_ratio <= 0.6

        analysis_msg = (f"{coin_ticker} 매수조건 분석: 연속양봉={cond_o1 and cond_o2}, "
                        f"종가증가={cond_close_inc}, 고점증가={cond_high_inc}, "
                        f"7이평증가={cond_7ma}, 50이평증가={cond_50ma}, 30이평기울기={cond_slope}, "
                        f"RSI증가={cond_rsi_inc} ({df['rsi_ma'].iloc[-3]}->{df['rsi_ma'].iloc[-2]}), "
                        f"MACD={cond_MACD}"
                        f"도지캔들={cond_doji}")
        
        telegram_alert.SendMessage(analysis_msg)
        buy = cond_o1 and cond_o2 and cond_close_inc and cond_high_inc and cond_7ma and cond_50ma and cond_slope and cond_rsi_inc and cond_MACD and cond_doji
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
                exec_msg = f"{coin_ticker} 바이낸스 전략 봇: 조건 만족하여 매수!!"
                print(exec_msg)
                telegram_alert.SendMessage(exec_msg)
        else:
            if hour_n == 0 and min_n == 0 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                warn_msg = f"{coin_ticker} 바이낸스 전략 봇: 조건 만족하지 않아 현금 보유 합니다!"
                print(warn_msg)
                telegram_alert.SendMessage(warn_msg)
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)

if hour_n == 0 and min_n <= 2:
    end_msg = f"[BinanceF_DOGE+PEPE] 전략 봇 정상 종료 - 레버리지 {set_leverage}배"
    telegram_alert.SendMessage(end_msg)
