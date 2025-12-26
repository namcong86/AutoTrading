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

# --- [추가] 다계정 정보 설정 ---
# 각 계정의 이름, API 키, 레버리지를 리스트에 딕셔너리 형태로 추가합니다.
ACCOUNT_LIST = [
    {
        "name": "Main",
        "access_key": simpleEnDecrypt.decrypt(my_key.binance_access_M),
        "secret_key": simpleEnDecrypt.decrypt(my_key.binance_secret_M),
        "leverage": 3  # 메인 계정 레버리지
    },
    {
        "name": "Sub1",
        "access_key": simpleEnDecrypt.decrypt(my_key.binance_access_S1),
        "secret_key": simpleEnDecrypt.decrypt(my_key.binance_secret_S1),
        "leverage": 5  # 서브 계정 1 레버리지
    }
]

# ==============================================================================
# <<< 코드 수정: 투자 종목을 테스트 파일과 동일하게 7종목으로 변경 >>>
# ==============================================================================
INVEST_COIN_LIST = [
    {'ticker': 'DOGE/USDT', 'rate': 0.12},
    {'ticker': 'ADA/USDT',  'rate': 0.12},
    {'ticker': 'XLM/USDT', 'rate': 0.1},
    {'ticker': 'XRP/USDT', 'rate': 0.1},
    {'ticker': 'HBAR/USDT', 'rate': 0.1},
    {'ticker': 'ETH/USDT', 'rate': 0.1},
    {'ticker': '1000PEPE/USDT', 'rate': 1},
    {'ticker': '1000BONK/USDT', 'rate': 1},
    {'ticker': '1000FLOKI/USDT', 'rate': 0.08},
    {'ticker': '1000SHIB/USDT', 'rate': 0.08},
]
# ==============================================================================


INVEST_RATE = 0.99
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
    first_String = f"[3.Binance {account_name}] 7종목 {set_leverage}배 "

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

    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong":
        botdata_file_path = f"/var/AutoBot/json/3.Binance_F_DOGE_PEPE_Leverage_Data_{account_name}.json"
    else:
        botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', f'3.Binance_F_DOGE_PEPE_Leverage_Data_{account_name}.json')

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


    # 모든 코인의 거래 결과를 요약할 딕셔너리
    trading_summary = {}

    cycle_investment_base = 0
    all_positions = []
    try:
        balance_check = binanceX.fetch_balance(params={"type": "future"})
        time.sleep(0.1)
        current_usdt_balance = float(balance_check['USDT']['free'])
        all_positions = [pos for pos in balance_check['info']['positions'] if float(pos['positionAmt']) != 0]

        if len(all_positions) == 0:
            print(f"[{account_name}] 현재 포지션 없음. 투자 기준금을 현재 잔고({current_usdt_balance:.2f} USDT)로 갱신합니다.")
            BotDataDict['INVESTMENT_BASE_USDT'] = current_usdt_balance
            with open(botdata_file_path, 'w') as f:
                json.dump(BotDataDict, f, indent=4)
        
        cycle_investment_base = BotDataDict.get('INVESTMENT_BASE_USDT')

        if cycle_investment_base is None:
            print(f"[{account_name}] 최초 실행. 투자 기준금을 현재 잔고({current_usdt_balance:.2f} USDT)로 설정합니다.")
            BotDataDict['INVESTMENT_BASE_USDT'] = current_usdt_balance
            cycle_investment_base = current_usdt_balance
            with open(botdata_file_path, 'w') as f:
                json.dump(BotDataDict, f, indent=4)
        
        print(f"[{account_name}] 이번 사이클 투자 기준금: {cycle_investment_base:.2f} USDT")

    except Exception as e:
        print(f"[{account_name}] 잔고 조회 또는 기준금 설정 실패, 이 계정의 거래를 건너뜁니다: {e}")
        telegram_alert.SendMessage(f"{first_String} 잔고 조회 실패, 봇 종료")
        return

    # --- 메인 루프 시작 ---
    for coin_data in INVEST_COIN_LIST:
        coin_ticker = coin_data['ticker']
        
        for key in ["_BUY_DATE", "_SELL_DATE", "_DATE_CHECK"]:
            full_key = coin_ticker + key
            if full_key not in BotDataDict:
                BotDataDict[full_key] = "" if key != "_DATE_CHECK" else 0
        with open(botdata_file_path, 'w') as f:
            json.dump(BotDataDict, f, indent=4)

        amt_b = 0
        unrealizedProfit = 0.0
        coin_symbol_for_pos = coin_ticker.replace("/", "")
        for pos in all_positions:
            if pos['symbol'] == coin_symbol_for_pos:
                amt_b = float(pos['positionAmt'])
                unrealizedProfit = float(pos['unrealizedProfit'])
                break

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
        
        df['prev_close'] = df['close'].shift(1)
        df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
        
        for ma in [3, 7, 20, 30, 50, 200]:
            df[f'{ma}ma'] = df['close'].rolling(ma).mean()
        
        df['value_ma'] = df['value'].rolling(10).mean().shift(1)
        df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
        
        # Disparity Index 계산 (종가 / 15일 이동평균 * 100)
        df['Disparity_Index_ma'] = df['close'].rolling(window=15).mean()
        df['disparity_index'] = (df['close'] / df['Disparity_Index_ma']) * 100
        
        df.dropna(inplace=True)

        now_price = myBinance.GetCoinNowPrice(binanceX, coin_ticker)
        params = {'positionSide': 'LONG'}

        if abs(amt_b) > 0:
            # --- 매도 조건 (백테스팅 파일 기준) ---
            RevenueRate = (unrealizedProfit / (cycle_investment_base * coin_data['rate'])) * 100.0 if (cycle_investment_base * coin_data['rate']) > 0 else 0

            def is_doji_candle(open_price, close_price, high_price, low_price):
                candle_range = high_price - low_price
                if candle_range == 0: return False
                gap = abs(open_price - close_price)
                return (gap / candle_range) <= 0.1

            # 개별 조건들 정의
            is_doji_1 = is_doji_candle(df['open'].iloc[-2], df['close'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2])
            is_doji_2 = is_doji_candle(df['open'].iloc[-3], df['close'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3])
            cond_doji = is_doji_1 and is_doji_2

            cond_fall_pattern = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
            cond_2_neg_candle = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
            cond_loss = (RevenueRate < 0)
            cond_not_rising = not (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])

            original_sell_cond = (cond_fall_pattern or cond_2_neg_candle or cond_loss) and cond_not_rising
            
            sell_condition_triggered = original_sell_cond or cond_doji
            
            # ==============================================================================
            # <<< 코드 수정: Main 계정에서만 조건별 True/False 알림 전송 >>>
            # ==============================================================================
            if account_name == "Main":
                alert_msg = (
                    f"<{first_String} {coin_ticker} 매도 조건 검사>\n"
                    f"- 포지션 보유 중 (수익률: {RevenueRate:.2f}%)\n\n"
                    f"▶ 최종 매도 결정: {sell_condition_triggered}\n"
                    f"--------------------\n"
                    f"[기본 매도 조건: {original_sell_cond}]\n"
                    f" ㄴ하락패턴: {cond_fall_pattern}\n"
                    f" ㄴ2연속음봉: {cond_2_neg_candle}\n"
                    f" ㄴ손실중: {cond_loss}\n"
                    f" ㄴ(AND)상승추세아님: {cond_not_rising}\n"
                    f"[추가 매도 조건]\n"
                    f" ㄴ2연속도지: {cond_doji}"
                )
                telegram_alert.SendMessage(alert_msg)
            
            # 거래 요약에 추가 (수익률과 매도조건)
            sell_emoji = "🔴" if sell_condition_triggered else "⚪"
            trading_summary[coin_ticker] = f"{sell_emoji} 수익률: {RevenueRate:.1f}% | 매도: {sell_condition_triggered}"
            # ==============================================================================

            if BotDataDict.get(coin_ticker + '_DATE_CHECK') == day_n:
                sell_condition_triggered = False

            if sell_condition_triggered:
                try:
                    # ==============================================================================
                    # <<< 코드 수정: 실제 매도 주문 주석 처리 >>>
                    binanceX.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params)
                    # ==============================================================================
                    exec_msg = f"{first_String} {coin_ticker} 조건 만족하여 매도!! (미실현 수익: {unrealizedProfit:.2f} USDT)"
                    print(exec_msg)
                    telegram_alert.SendMessage(exec_msg)
                    BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
                    BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                    with open(botdata_file_path, 'w') as f:
                        json.dump(BotDataDict, f, indent=4)
                except Exception as e:
                    print(f"[{account_name}] 매도 주문 실패 for {coin_ticker}: {e}")
        
        else:
            # --- 매수 조건 (백테스팅 파일 기준) ---
            
            # 개별 조건들 정의
            cond_no_surge = df['change'].iloc[-2] < 0.5
            is_above_200ma = df['close'].iloc[-2] > df['200ma'].iloc[-2]
            
            # ==============================================================================
            # <<< 신규 매수 조건 추가 >>>
            # ==============================================================================
            cond_ma_50 = True
            cond_no_long_upper_shadow = True
            cond_body_over_15_percent = True

            if is_above_200ma:
                # 1. 50일 이평선 하락 아님
                cond_ma_50 = (df['50ma'].iloc[-3] <= df['50ma'].iloc[-2])

                # 2. 긴 윗꼬리 없음
                prev_candle = df.iloc[-2] # 전일자 캔들
                upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
                body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
                cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
                
                # 3. 캔들 몸통이 전체 길이의 15% 이상
                candle_range = prev_candle['high'] - prev_candle['low']
                candle_body = abs(prev_candle['open'] - prev_candle['close'])
                if candle_range > 0:
                    cond_body_over_15_percent = (candle_body >= candle_range * 0.15)
            # ==============================================================================

            cond_2_pos_candle = df['open'].iloc[-2] < df['close'].iloc[-2] and df['open'].iloc[-3] < df['close'].iloc[-3]
            cond_price_up = df['close'].iloc[-3] < df['close'].iloc[-2] and df['high'].iloc[-3] < df['high'].iloc[-2]
            cond_7ma_up = df['7ma'].iloc[-3] < df['7ma'].iloc[-2]
            cond_30ma_slope = df['30ma_slope'].iloc[-2] > -2
            cond_rsi_ma_up = df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2]
            cond_20ma_up = df['20ma'].iloc[-3] <= df['20ma'].iloc[-2]
            
            # Disparity Index 조건 (30일 기준) - 오늘 미포함 (전일까지만)
            disparity_period = 30
            filter_disparity = False
            
            if len(df) >= disparity_period + 1:
                # 오늘 미포함: iloc[-disparity_period-1:-1] = 31일전 ~ 전일 (30개)
                recent_disparity = df['disparity_index'].iloc[-disparity_period-1:-1]
                yesterday_disparity = df['disparity_index'].iloc[-2]
                max_disparity = recent_disparity.max()
                
                if yesterday_disparity == max_disparity:
                    filter_disparity = True
                else:
                    try:
                        max_idx = recent_disparity.idxmax()
                        yesterday_idx = df.index[-2]
                        if max_idx < yesterday_idx:
                            range_disparity = df.loc[max_idx:yesterday_idx, 'disparity_index']
                            if (range_disparity >= 100).all():
                                filter_disparity = True
                    except Exception:
                        filter_disparity = False
            else:
                filter_disparity = True
            
            # ==============================================================================
            # <<< 최종 매수 결정 로직에 신규 조건 반영 >>>
            # ==============================================================================
            buy = (
                cond_2_pos_candle and
                cond_price_up and
                cond_7ma_up and
                cond_30ma_slope and
                cond_rsi_ma_up and
                cond_ma_50 and
                cond_20ma_up and
                cond_no_surge and
                filter_disparity and
                cond_no_long_upper_shadow and      #<-- 추가
                cond_body_over_15_percent          #<-- 추가
            )
            # ==============================================================================

            # ==============================================================================
            # <<< 코드 수정: Main 계정에서만 조건별 True/False 알림 전송 (신규 조건 추가) >>>
            # ==============================================================================
            if account_name == "Main":
                # True/False를 이모지로 시각적으로 구분
                def tf_emoji(val):
                    return "✅" if val else "❌"
                
                buy_emoji = "🟢 True" if buy else "🔴 False"
                
                alert_msg = (
                    f"<{first_String} {coin_ticker} 매수 조건 검사>\n"
                    f"- 포지션 없음\n\n"
                    f"▶️ 최종 매수 결정: {buy_emoji}\n"
                    f"--------------------\n"
                    f" 1. 2연속 양봉: {tf_emoji(cond_2_pos_candle)}\n"
                    f" 2. 전일 종가/고가 상승: {tf_emoji(cond_price_up)}\n"
                    f" 3. 7ma 상승: {tf_emoji(cond_7ma_up)}\n"
                    f" 4. 30ma 기울기 > -2: {tf_emoji(cond_30ma_slope)}\n"
                    f" 5. RSI_MA 상승: {tf_emoji(cond_rsi_ma_up)}\n"
                    f" 6. 50ma 조건 충족: {tf_emoji(cond_ma_50)}\n"
                    f" 7. 20ma 상승: {tf_emoji(cond_20ma_up)}\n"
                    f" 8. 급등 아님: {tf_emoji(cond_no_surge)}\n"
                    f" 9. Disparity Index 조건: {tf_emoji(filter_disparity)}\n"
                    f" 10. 긴 윗꼬리 없음: {tf_emoji(cond_no_long_upper_shadow)}\n"
                    f" 11. 캔들 몸통 15% 이상: {tf_emoji(cond_body_over_15_percent)}"
                )
                telegram_alert.SendMessage(alert_msg)
            
            # 거래 요약에 추가 (매수 조건 TRUE/FALSE)
            buy_summary_emoji = "🟢" if buy else "⚪"
            trading_summary[coin_ticker] = f"{buy_summary_emoji} 매수: {buy}"
            # ==============================================================================

            if buy:
                if BotDataDict.get(coin_ticker + '_BUY_DATE') != day_str and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                    
                    total_coin_count = len(INVEST_COIN_LIST)
                    num_open_positions = len(all_positions)

                    if num_open_positions == (total_coin_count - 1):
                        InvestMoney = current_usdt_balance
                    else:
                        InvestMoney = cycle_investment_base * INVEST_RATE * coin_data['rate']

                    BuyMoney = InvestMoney * (1.0 - FEE * set_leverage)
                    cap = df['value_ma'].iloc[-2] / 10
                    BuyMoney = min(max(BuyMoney, 10), cap)
                    amount = float(binanceX.amount_to_precision(coin_ticker, myBinance.GetAmount(BuyMoney, now_price, 1.0))) * set_leverage

                    market_symbol = coin_ticker.replace("/", "")
                    try:
                        binanceX.set_margin_mode('cross', market_symbol)
                        binanceX.set_leverage(set_leverage, market_symbol)
                    except Exception as e:
                        print(f"[{account_name}] 마진모드/레버리지 세팅 오류: {e}")

                    try:
                        # ==============================================================================
                        # <<< 코드 수정: 실제 매수 주문 주석 처리 >>>
                        binanceX.create_order(coin_ticker, 'market', 'buy', amount, None, params)
                        # ==============================================================================
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
                    # 날짜 체크는 모든 계정에서 수행
                    BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                    with open(botdata_file_path, 'w') as f:
                        json.dump(BotDataDict, f, indent=4)
    
    # ===== 거래 결과 요약 알림 (Main 계정에서만) =====
    if account_name == "Main" and trading_summary:
        summary_msg = f"📊 Binance Main 거래 조건 검사 결과\n" + "="*35 + "\n"
        for ticker, status in trading_summary.items():
            summary_msg += f"{ticker}: {status}\n"
        telegram_alert.SendMessage(summary_msg)


# --- [추가] 메인 실행부 ---
if __name__ == '__main__':
    print("===== 다계정 자동매매 봇 시작 =====")
    for account in ACCOUNT_LIST:
        print(f"\n--- {account['name']} 거래 시작 (레버리지: {account['leverage']}배) ---")
        execute_trading_logic(account)
    print("\n===== 모든 계정 거래 실행 완료 =====")