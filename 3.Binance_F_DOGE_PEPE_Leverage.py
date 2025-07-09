# -*- coding:utf-8 -*-
'''
Binance 선물 다계정 운영 봇 (DOGE + 1000PEPE 50:50, 매수/매도 조건 동일) - 수정된 버전
'''
import ccxt
import time
import pandas as pd
import json
import socket
import sys
import myBinance
import telegram_alert

# --- [추가] 다계정 정보 설정 ---
# 각 계정의 이름, API 키, 레버리지를 리스트에 딕셔너리 형태로 추가합니다.
ACCOUNT_LIST = [
    {
        "name": "Main",
        "access_key": "3L5mMgSFzt8HlPt6daAIzLxRTqFPaA1ItKMYNgNdgNkBOtBmlUMDzefQAK1UMs4J",  # 메인 계정 Access Key
        "secret_key": "CXNpmRpSGpH9BXjkIbqKMtp1icekWPsTyIEhC0OcPrzclKnai9ATzrH3BVHUI9zL",  # 메인 계정 Secret Key
        "leverage": 3  # 메인 계정 레버리지
    },
    {
        "name": "Sub1",
        "access_key": "qXIylTz7Qh2nrVh1kPJQTXX9Fm0G8Tot86Lgqzm652mTdnEj7DrbJO6KT261fQJk",
        "secret_key": "DarhAG7HjLW7OJBe814q42io5UOYB9dzhwQlbijuz5m5gN9mREA5wfbeGT7H0PwI",
        "leverage": 5  # 서브 계정 1 레버리지
    },
    {
        "name": "Sub2",
        "access_key": "HbC79j9E1f8fZUXe7YK5DcgOxG3rcgbd1lSt3r17BJmqga5EbHVbNwIux1Rm6K3q",
        "secret_key": "lM3RhPOesjwyLLpECpwUuijOZLUpVZEqdRKDmRSPE6WbadQltXRtNIrfY6rnRCMg",
        "leverage": 7  # 서브 계정 2 레버리지
    },
    {
        "name": "Sub3",
        "access_key": "EYNqzB1k2echWMLnmUSZWf1O03U8fiPUMQX9OHL83eeWGotYgoq1dJaDQYleh8Wa",
        "secret_key": "PW2cxdCPGSJXMhiEgT2aABt0NikxOntPVOzMxgAYkWe4DxSU1xIzPJgZfnujf28h",
        "leverage": 10  # 서브 계정 3 레버리지
    }
]

# 투자 종목: DOGE, 1000PEPE - 50:50 비중
INVEST_COIN_LIST = [
    {'ticker': 'DOGE/USDT', 'rate': 0.5},
    {'ticker': '1000PEPE/USDT', 'rate': 0.3},
    {'ticker': '1000BONK/USDT', 'rate': 0.2}
]

INVEST_RATE = 1
FEE = 0.001

# --- [추가] 핵심 거래 로직을 함수로 분리 ---
def execute_trading_logic(account_info):
    '''
    하나의 계정에 대한 전체 매수/매도 로직을 수행하는 함수
    '''
    account_name = account_info['name']
    access_key = account_info['access_key']
    secret_key = account_info['secret_key']
    set_leverage = account_info['leverage']

    # 알림 첫문구 설정
    first_String = f"[3.Binance {account_name}] DOGE+PEPE {set_leverage}배 "

    # 바이낸스 객체 생성
    try:
        binanceX = ccxt.binance({
            'apiKey': access_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {'defaultType': 'future'}
        })
    except Exception as e:
        print(f"[{account_name}] ccxt 객체 생성 실패: {e}")
        telegram_alert.SendMessage(f"[{account_name}] ccxt 객체 생성 실패. 이 계정을 건너뜁니다.")
        return

    # --- [수정] 계정별 데이터 파일 경로 설정 ---
    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong":
        botdata_file_path = f"/var/AutoBot/json/BinanceF_DOGE_PEPE_Data_{account_name}.json"
    else:
        botdata_file_path = f"./BinanceF_DOGE_PEPE_Data_{account_name}.json"

    try:
        with open(botdata_file_path, 'r') as f:
            BotDataDict = json.load(f)
    except FileNotFoundError:
        BotDataDict = {}
    except Exception as e:
        print(f"[{account_name}] 데이터 파일 로드 오류: {e}")
        BotDataDict = {}


    t = time.gmtime()
    hour_n = t.tm_hour
    min_n = t.tm_min
    day_n = t.tm_mday
    day_str = f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"

    if hour_n == 0 and min_n <= 2:
        start_msg = f"{first_String} 시작"
        telegram_alert.SendMessage(start_msg)

    # --- 스크립트 실행 시점의 투자 기준금 설정 ---
    try:
        balance = binanceX.fetch_balance(params={"type": "future"})
        time.sleep(0.1)
        initial_usdt_balance = float(balance['USDT']['free'])
        print(f"[{account_name}] 스크립트 시작. 투자 기준금: {initial_usdt_balance:.2f} USDT")
    except Exception as e:
        print(f"[{account_name}] 잔고 조회 실패, 이 계정의 거래를 건너뜁니다: {e}")
        telegram_alert.SendMessage(f"{first_String} 잔고 조회 실패, 봇 종료")
        return

    # --- [수정] 현재 모든 포지션 정보를 한번에 가져오기 ---
    all_positions = []
    try:
        balance_check = binanceX.fetch_balance(params={"type": "future"})
        all_positions = [pos for pos in balance_check['info']['positions'] if float(pos['positionAmt']) != 0]
    except Exception as e:
        print(f"[{account_name}] 전체 포지션 정보 조회 오류: {e}")
        return # 포지션 조회가 안되면 거래를 진행하기 어려우므로 종료

    # --- 메인 루프 시작 ---
    for coin_data in INVEST_COIN_LIST:
        coin_ticker = coin_data['ticker']
        
        # BotData 기본 키 초기화
        for key in ["_BUY_DATE", "_SELL_DATE", "_DATE_CHECK"]:
            full_key = coin_ticker + key
            if full_key not in BotDataDict:
                BotDataDict[full_key] = "" if key != "_DATE_CHECK" else 0
        with open(botdata_file_path, 'w') as f:
            json.dump(BotDataDict, f, indent=4)

        # --- [수정] 미리 가져온 포지션 정보 사용 ---
        amt_b = 0
        unrealizedProfit = 0.0
        coin_symbol_for_pos = coin_ticker.replace("/", "")
        for pos in all_positions:
            if pos['symbol'] == coin_symbol_for_pos:
                amt_b = float(pos['positionAmt'])
                unrealizedProfit = float(pos['unrealizedProfit'])
                break

        # 지표용 일봉 데이터 조회 및 계산 (기존 코드와 동일)
        df = myBinance.GetOhlcv(binanceX, coin_ticker, '1d')
        df['value'] = df['close'] * df['volume']
        period = 14
        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = (-delta).clip(lower=0)
        gain = up.ewm(com=period-1, min_periods=period).mean()
        loss = down.ewm(com=period-1, min_periods=period).mean()
        RS = gain / loss.replace(0, 1e-9)
        df['rsi'] = 100 - (100 / (1 + RS))
        df['rsi_ma'] = df['rsi'].rolling(14).mean()
        ema12 = df['close'].ewm(span=12, adjust=False).mean()
        ema26 = df['close'].ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        for ma in [3, 7, 12, 24, 30, 50]:
            df[f'{ma}ma'] = df['close'].rolling(ma).mean()
        df['value_ma'] = df['value'].rolling(10).mean().shift(1)
        df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
        df.dropna(inplace=True)

        now_price = myBinance.GetCoinNowPrice(binanceX, coin_ticker)
        DiffValue = -2
        params = {'positionSide': 'LONG'}

        # --- 매도 로직 (기존 코드와 동일, 알림 메시지만 수정) ---
        if abs(amt_b) > 0:
            cond_high_low = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
            cond_open_close = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
            cond_revenue = (unrealizedProfit < 0)
            cond_cancel = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])
            
            analysis_msg = (f"{first_String}  매도조건 분석 ({coin_ticker}): high_low={cond_high_low}, "
                            f"open_close={cond_open_close}, revenue<0={cond_revenue}, "
                            f"cancel_by_rsi_ma={cond_cancel}")
            if account_name == "Main":
                print(analysis_msg)
                telegram_alert.SendMessage(analysis_msg)

            sell = (cond_high_low or cond_open_close or cond_revenue) and not cond_cancel
            if BotDataDict.get(coin_ticker + '_DATE_CHECK') == day_n:
                sell = False

            if sell:
                try:
                    binanceX.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params)
                    exec_msg = f"{first_String} {coin_ticker} 조건 만족하여 매도!! (미실현 수익: {unrealizedProfit:.2f} USDT)"
                    print(exec_msg)
                    telegram_alert.SendMessage(exec_msg)
                    BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
                    BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                    with open(botdata_file_path, 'w') as f:
                        json.dump(BotDataDict, f, indent=4)
                except Exception as e:
                    print(f"[{account_name}] 매도 주문 실패 for {coin_ticker}: {e}")
        
        # --- 매수 로직 (기존 코드와 동일, 알림 메시지만 수정) ---
        else:
            macd_3ago = df['macd'].iloc[-4]-df['macd_signal'].iloc[-4]
            macd_2ago = df['macd'].iloc[-3]-df['macd_signal'].iloc[-3]
            macd_1ago = df['macd'].iloc[-2]-df['macd_signal'].iloc[-2]
            macd_positive = macd_1ago > 0
            macd_3to2_down = macd_3ago > macd_2ago
            macd_2to1_down = macd_2ago > macd_1ago
            macd_condition = not (macd_3to2_down and macd_2to1_down)
            
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
            cond_80rsi = (df['rsi'].iloc[-2] < 80)

            analysis_msg = (f"{first_String} 매수조건 분석 ({coin_ticker}): 연속양봉={cond_o1 and cond_o2}, "
                            f"종가증가={cond_close_inc}, 고점증가={cond_high_inc}, "
                            f"7이평증가={cond_7ma}, 50이평증가={cond_50ma}, 30이평기울기={cond_slope}, "
                            f"RSI증가={cond_rsi_inc} ({df['rsi_ma'].iloc[-3]:.2f}->{df['rsi_ma'].iloc[-2]:.2f}), "
                            f"MACD={cond_MACD}, 도지캔들={cond_doji}, RSI80이하={cond_80rsi}")
            if account_name == "Main":
                print(analysis_msg)
                telegram_alert.SendMessage(analysis_msg)

            buy = cond_o1 and cond_o2 and cond_close_inc and cond_high_inc and cond_7ma and cond_50ma and cond_slope and cond_rsi_inc and cond_MACD and cond_doji and cond_80rsi
            if buy:
                if BotDataDict.get(coin_ticker + '_BUY_DATE') != day_str and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                    
                    # --- [수정] 투자금 계산 로직 변경 ---
                    total_coin_count = len(INVEST_COIN_LIST)
                    
                    # 현재 포지션에 있는 코인 목록 (심볼 기준)
                    position_symbols = [pos['symbol'] for pos in all_positions]
                    
                    # INVEST_COIN_LIST에 정의된 코인 중 현재 포지션이 있는 코인의 수
                    num_open_positions = 0
                    for c in INVEST_COIN_LIST:
                        if c['ticker'].replace('/', '') in position_symbols:
                            num_open_positions += 1

                    # N-1개 코인이 포지션에 있고, 현재 코인은 포지션이 없을 때 (현재 코드는 amt_b == 0 인 분기)
                    if num_open_positions == (total_coin_count - 1):
                        # 사용 가능한 현금 전부를 투자금으로 설정
                        InvestMoney = initial_usdt_balance
                        print(f"[{account_name}] >>> 마지막 코인({coin_ticker}) 진입: 모든 가용 현금({InvestMoney:.2f})을 사용합니다.")
                    else:
                        # 기존 규칙: 사이클 기준 자본과 코인별 비율로 투자금 설정
                        InvestMoney = initial_usdt_balance * INVEST_RATE * coin_data['rate']
                        print(f"[{account_name}] {coin_ticker} 매수 조건 충족! 투자금 계산 -> 기준금: {initial_usdt_balance:.2f}, 비율: {coin_data['rate']}, 최종 투자금: {InvestMoney:.2f} USDT")
                    # --- [수정] 로직 종료 ---

                    BuyMoney = InvestMoney * (1.0 - FEE * set_leverage)
                    cap = df['value_ma'].iloc[-2] / 10
                    BuyMoney = min(max(BuyMoney, 10), cap)
                    amount = float(binanceX.amount_to_precision(coin_ticker, myBinance.GetAmount(BuyMoney, now_price, 1.0))) * set_leverage

                    market_symbol = coin_ticker.replace("/", "")
                    try:
                        binanceX.set_margin_mode('cross', market_symbol)
                        binanceX.set_leverage(set_leverage, market_symbol)
                        print(f"[{account_name}] {market_symbol} 마진모드: cross, 레버리지: {set_leverage} 설정 완료")
                    except Exception as e:
                        print(f"[{account_name}] 마진모드/레버리지 세팅 오류: {e}")

                    try:
                        binanceX.create_order(coin_ticker, 'market', 'buy', amount, None, params)
                        BotDataDict[coin_ticker + '_BUY_DATE'] = day_str
                        BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                        with open(botdata_file_path, 'w') as f:
                            json.dump(BotDataDict, f, indent=4)
                        exec_msg = f"{first_String} {coin_ticker} 조건 만족하여 매수!!"
                        print(exec_msg)
                        telegram_alert.SendMessage(exec_msg)
                    except Exception as e:
                        print(f"[{account_name}] 매수 주문 실패 for {coin_ticker}: {e}")
            else:
                if hour_n == 0 and min_n <= 2 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                    warn_msg = f"{first_String} {coin_ticker} : 조건 만족하지 않아 현금 보유 합니다!"
                    print(warn_msg)
                    telegram_alert.SendMessage(warn_msg)
                    BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                    with open(botdata_file_path, 'w') as f:
                        json.dump(BotDataDict, f, indent=4)
    
    if hour_n == 0 and min_n <= 2:
        end_msg = f"{first_String} 종료"
        telegram_alert.SendMessage(end_msg)

# --- [추가] 메인 실행부 ---
if __name__ == '__main__':
    print("===== 다계정 자동매매 봇 시작 =====")
    for account in ACCOUNT_LIST:
        print(f"\n--- {account['name']} 거래 시작 (레버리지: {account['leverage']}배) ---")
        execute_trading_logic(account)
    print("\n===== 모든 계정 거래 실행 완료 =====")