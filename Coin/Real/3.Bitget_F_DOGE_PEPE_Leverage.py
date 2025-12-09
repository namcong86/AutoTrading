# -*- coding:utf-8 -*-
'''
Bitget 선물 다계정 운영 봇 (DOGE + 1000PEPE 등 포트폴리오, 매수/매도 조건 동일) - Bitget 버전
'''
import ccxt
import time
import pandas as pd
import json
import socket
import sys
import os

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    sys.path.insert(0, "/var/AutoBot/Common")
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))
import datetime
import telegram_alert
import myBinance
import ende_key
import my_key

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# ==============================================================================
# ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼ 헬퍼 함수들 (myBitget 대체) ▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼▼
# ==============================================================================
def GetOhlcv(exchange, ticker, timeframe='1d', target_rows=260):
    """Bitget: fetch OHLCV in multiple batches (90 per call) going backwards with endTime."""
    try:
        limit = 90
        target_rows = max(target_rows, limit * 2)
        all_ohlcv = []
        end_ms = None
        attempts = 0

        while len(all_ohlcv) < target_rows and attempts < 12:
            params = {'limit': limit}
            if end_ms is not None:
                params['endTime'] = end_ms

            log_point = datetime.datetime.fromtimestamp(end_ms / 1000).isoformat() if end_ms else "latest"

            batch = exchange.fetch_ohlcv(ticker, timeframe, limit=limit, params=params)
            if not batch:
                break

            # prepend older data
            all_ohlcv = batch + all_ohlcv
            end_ms = batch[0][0] - 1  # next batch ends before the oldest candle
            attempts += 1

            if len(batch) < limit:
                break

            time.sleep(exchange.rateLimit / 1000 if hasattr(exchange, 'rateLimit') else 0.2)

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df.drop_duplicates(subset='datetime', keep='first', inplace=True)
        df.sort_values('datetime', inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        print(f"데이터 수집 완료: {ticker}, 총 {len(df)}개 행")
        return df
    except Exception as e:
        print(f"GetOhlcv 오류 ({ticker}): {e}")
        return pd.DataFrame()

def GetCoinNowPrice(exchange, ticker):
    try:
        return exchange.fetch_ticker(ticker)['last']
    except Exception as e:
        print(f"GetCoinNowPrice 오류 ({ticker}): {e}")
        return 0.0

def GetAmount(money, price, leverage=1.0):
    if price and price > 0:
        return (money * leverage) / price
    return 0.0
# ==============================================================================
# ▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲▲
# ==============================================================================

# --- [수정] 비트겟 다계정 정보 설정 ---
# 암호화된 키를 복호화하여 사용
ACCOUNT_LIST = [
    {
        "name": "Sub1",
        "access_key": simpleEnDecrypt.decrypt(my_key.bitget_access_S1),
        "secret_key": simpleEnDecrypt.decrypt(my_key.bitget_secret_S1),
        "passphrase": simpleEnDecrypt.decrypt(my_key.bitget_passphrase_S1),
        "leverage": 6  # 서브 계정 1 레버리지
    }
]
# 투자 종목 리스트 - 비트겟 티커명으로 수정
# ====================================================0==========================
INVEST_COIN_LIST = [
    {'ticker': 'DOGE/USDT:USDT', 'rate': 0.12},
    {'ticker': 'ADA/USDT:USDT', 'rate': 0.12},
    {'ticker': 'XLM/USDT:USDT', 'rate': 0.1},
    {'ticker': 'XRP/USDT:USDT', 'rate': 0.1},
    {'ticker': 'HBAR/USDT:USDT', 'rate': 0.1},
    {'ticker': 'ETH/USDT:USDT', 'rate': 0.1},
    {'ticker': 'PEPE/USDT:USDT', 'rate': 0.1},
    {'ticker': '1000BONK/USDT:USDT', 'rate': 0.1},
    {'ticker': 'FLOKI/USDT:USDT', 'rate': 0.08},
    {'ticker': 'SHIB/USDT:USDT', 'rate': 0.08},
]
# ==============================================================================

INVEST_RATE = 1
FEE = 0.0006  # 비트겟 메이커 수수료 0.06%

# --- 핵심 거래 로직을 담은 함수 ---
def execute_trading_logic(account_info):
    '''
    하나의 비트겟 계정에 대한 전체 매수/매도 로직을 수행하는 함수
    '''
    account_name = account_info['name']
    access_key = account_info['access_key']
    secret_key = account_info['secret_key']
    passphrase = account_info['passphrase']
    set_leverage = account_info['leverage']

    first_String = f"[3.Bitget {account_name}] {set_leverage}배 "

    # 비트겟 객체 생성
    try:
        bitgetX = ccxt.bitget({
            'apiKey': access_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'defaultMarginMode': 'cross'
            }
        })
    except Exception as e:
        print(f"[{account_name}] ccxt 객체 생성 실패: {e}")
        telegram_alert.SendMessage(f"[{account_name}] ccxt 객체 생성 실패. 이 계정을 건너뜁니다.")
        return

    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong":
        botdata_file_path = f"/var/AutoBot/json/3.Bitget_F_DOGE_PEPE_Leverage_Data_{account_name}.json"
    else:
        botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', f'3.Bitget_F_DOGE_PEPE_Leverage_Data_{account_name}.json')

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

    cycle_investment_base = 0
    all_positions = []
    
    try:
        # 선물 지갑의 USDT 잔고 조회
        balance_check = bitgetX.fetch_balance(params={"type": "swap"})
        time.sleep(0.1)
        current_usdt_balance = float(balance_check['USDT']['free'])

        # 잔고 부족 체크
        if current_usdt_balance < 10:
            print(f"[{account_name}] 잔고 부족 ({current_usdt_balance:.2f} USDT), 거래 건너뜀")
            telegram_alert.SendMessage(f"{first_String} 잔고 부족, 거래 불가")
            return

        # 포지션 정보 조회
        all_positions_raw = bitgetX.fetch_positions()
        all_positions = [pos for pos in all_positions_raw if float(pos.get('contracts', 0)) != 0]

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
    # 모든 코인의 거래 결과를 요약할 딕셔너리
    trading_summary = {}
    
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
        
        current_pos_side = 'long' # Default
        for pos in all_positions:
            if pos['symbol'] == coin_ticker:
                amt_b = float(pos.get('contracts', 0))
                unrealizedProfit = float(pos.get('unrealizedPnl', 0.0))
                current_pos_side = pos.get('side', 'long')
                break

        # 기술적 지표 계산
        df = GetOhlcv(bitgetX, coin_ticker, '1d', target_rows=200)
        if df.empty:
            print(f"[{account_name}] {coin_ticker} 데이터 조회 실패, 건너뜀")
            telegram_alert.SendMessage(f"{first_String} {coin_ticker} 데이터 조회 실패")
            continue
            
        df['value'] = df['close'] * df['volume']
        
        period = 14
        delta = df['close'].diff()
        up = delta.clip(lower=0)
        down = (-delta).clip(lower=0)
        gain = up.ewm(com=period-1, min_periods=1).mean()
        loss = down.ewm(com=period-1, min_periods=1).mean()
        RS = gain / loss.replace(0, 1e-9)
        df['rsi'] = 100 - (100 / (1 + RS))
        df['rsi_ma'] = df['rsi'].rolling(14, min_periods=1).mean()
        
        df['prev_close'] = df['close'].shift(1)
        df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
        
        for ma in [3, 7, 20, 30, 50, 200]:
            df[f'{ma}ma'] = df['close'].rolling(ma, min_periods=1).mean()
        
        df['value_ma'] = df['value'].rolling(10, min_periods=1).mean().shift(1)
        # 30ma_slope 계산 시 NaN 방지
        df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5).replace(0, 1e-9)) * 100
        df['30ma_slope'] = df['30ma_slope'].fillna(0)  # 초기 NaN을 0으로 채움
        
        # Disparity Index 계산 (종가 / 15일 이동평균 * 100)
        df['Disparity_Index_ma'] = df['close'].rolling(window=15).mean()
        df['disparity_index'] = (df['close'] / df['Disparity_Index_ma']) * 100
        
        df.dropna(inplace=True)

        if len(df) < 60:
            print(f"[{account_name}] {coin_ticker} 유효 데이터 부족 (행 수: {len(df)}), 건너뜀")
            continue

        now_price = GetCoinNowPrice(bitgetX, coin_ticker)
        if now_price == 0:
            print(f"[{account_name}] {coin_ticker} 현재가 조회 실패, 건너뜀")
            telegram_alert.SendMessage(f"{first_String} {coin_ticker} 현재가 조회 실패")
            continue

        # 비트겟 주문 파라미터 (크로스 모드에서는 holdSide 사용 금지)
        params = {}

        if abs(amt_b) > 0:
            # --- 매도 조건 ---
            RevenueRate = (unrealizedProfit / (cycle_investment_base * coin_data['rate'])) * 100.0 if (cycle_investment_base * coin_data['rate']) > 0 else 0

            def is_doji_candle(open_price, close_price, high_price, low_price):
                candle_range = high_price - low_price
                if candle_range == 0: return False
                gap = abs(open_price - close_price)
                return (gap / candle_range) <= 0.1

            is_doji_1 = is_doji_candle(df['open'].iloc[-2], df['close'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2])
            is_doji_2 = is_doji_candle(df['open'].iloc[-3], df['close'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3])
            cond_doji = is_doji_1 and is_doji_2
            cond_fall_pattern = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
            cond_2_neg_candle = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
            cond_loss = (RevenueRate < 0)
            cond_not_rising = not (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])
            original_sell_cond = (cond_fall_pattern or cond_2_neg_candle or cond_loss) and cond_not_rising
            sell_condition_triggered = original_sell_cond or cond_doji
            
            # ===== 이전 알림 방식 (주석 처리) =====
            # alert_msg = (
            #     f"<{first_String} {coin_ticker} 매도 조건 검사>\n"
            #     f"- 포지션 보유 중 (수익률: {RevenueRate:.2f}%)\n\n"
            #     f"▶ 최종 매도 결정: {sell_condition_triggered}\n"
            #     f"--------------------\n"
            #     f"[기본 매도 조건: {original_sell_cond}]\n"
            #     f" ㄴ하락패턴: {cond_fall_pattern}\n"
            #     f" ㄴ2연속음봉: {cond_2_neg_candle}\n"
            #     f" ㄴ손실중: {cond_loss}\n"
            #     f" ㄴ(AND)상승추세아님: {cond_not_rising}\n"
            #     f"[추가 매도 조건]\n"
            #     f" ㄴ2연속도지: {cond_doji}"
            # )
            # telegram_alert.SendMessage(alert_msg)
            
            # ===== 새로운 요약 알림 방식 =====
            # 거래 요약에 추가 (수익률과 매도조건)
            sell_emoji = "🔴" if sell_condition_triggered else "⚪"
            trading_summary[coin_ticker] = f"{sell_emoji} 수익률: {RevenueRate:.1f}% | 매도: {sell_condition_triggered}"

            if BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                if sell_condition_triggered:
                    try:
                        # 실제 매도 주문 실행 (양방향 모드: holdSide만 사용)
                        print(f"[{account_name}] {coin_ticker} 매도 시도 - 포지션 수량: {amt_b} (Side: {current_pos_side})")
                        if amt_b == 0:
                            print(f"[{account_name}] {coin_ticker} 포지션이 없어 매도 건너뜀")
                            continue
                        
                        # Hedge Mode Close Params: holdSide만 명시
                        # Long 포지션 종료: Sell, holdSide='long'
                        # Short 포지션 종료: Buy, holdSide='short'
                        close_side = 'buy' if current_pos_side == 'long' else 'sell'
                        
                        bitgetX.create_order(
                            coin_ticker, 
                            'market', 
                            close_side, 
                            abs(amt_b), 
                            None, 
                            {'holdSide': current_pos_side, 'tradeSide': 'close'}
                        )
                        
                        exec_msg = f"{first_String} {coin_ticker} 조건 만족하여 매도(Close {current_pos_side})!! (미실현 수익: {unrealizedProfit:.2f} USDT)"
                        print(exec_msg)
                        telegram_alert.SendMessage(exec_msg)
                        BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
                        BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                        with open(botdata_file_path, 'w') as f:
                            json.dump(BotDataDict, f, indent=4)
                    except Exception as e:
                        print(f"[{account_name}] 매도 주문 실패 for {coin_ticker}: {e}")
                        telegram_alert.SendMessage(f"[{account_name}] {coin_ticker} 매도 실패: {e}")
        
        else:
            # --- 매수 조건 ---
            cond_no_surge = df['change'].iloc[-2] < 0.5
            is_above_200ma = df['close'].iloc[-2] > df['200ma'].iloc[-2]
            cond_ma_50 = True 
            # Binance와 동일한 추가 조건 2개
            cond_no_long_upper_shadow = True
            cond_body_over_15_percent = True
            if is_above_200ma:
                cond_ma_50 = (df['50ma'].iloc[-3] <= df['50ma'].iloc[-2])
                # 긴 윗꼬리 없음
                prev_candle = df.iloc[-2]
                upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
                body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
                cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
                # 캔들 몸통이 전체 길이의 15% 이상
                candle_range = prev_candle['high'] - prev_candle['low']
                candle_body = abs(prev_candle['open'] - prev_candle['close'])
                if candle_range > 0:
                    cond_body_over_15_percent = (candle_body >= candle_range * 0.15)

            cond_2_pos_candle = df['open'].iloc[-2] < df['close'].iloc[-2] and df['open'].iloc[-3] < df['close'].iloc[-3]
            cond_price_up = df['close'].iloc[-3] < df['close'].iloc[-2] and df['high'].iloc[-3] < df['high'].iloc[-2]
            cond_7ma_up = df['7ma'].iloc[-3] < df['7ma'].iloc[-2]
            cond_30ma_slope = df['30ma_slope'].iloc[-2] > -2
            cond_rsi_ma_up = df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2]
            cond_20ma_up = df['20ma'].iloc[-3] <= df['20ma'].iloc[-2]
            
            # Disparity Index 조건 (30일 기준)
            disparity_period = 30
            filter_disparity = False
            
            if len(df) >= disparity_period:
                recent_disparity = df['disparity_index'].iloc[-disparity_period:]
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
                cond_no_long_upper_shadow and
                cond_body_over_15_percent
            )
            
            # ===== 이전 알림 방식 (로그 출력) =====
            print(
                f"<{first_String} {coin_ticker} 매수 조건 검사>\n"
                f"- 포지션 없음\n\n"
                f"▶ 최종 매수 결정: {buy}\n"
                f"--------------------\n"
                f" 1. 2연속 양봉: {cond_2_pos_candle}\n"
                f" 2. 전일 종가/고가 상승: {cond_price_up}\n"
                f" 3. 7ma 상승: {cond_7ma_up}\n"
                f" 4. 30ma 기울기 > -2: {cond_30ma_slope}\n"
                f" 5. RSI_MA 상승: {cond_rsi_ma_up}\n"
                f" 6. 50ma 조건 충족: {cond_ma_50}\n"
                f" 7. 20ma 상승: {cond_20ma_up}\n"
                f" 8. 급등 아님: {cond_no_surge}\n"
                f" 9. Disparity Index 조건: {filter_disparity}\n"
                f" 10. 긴 윗꼬리 없음: {cond_no_long_upper_shadow}\n"
                f" 11. 캔들 몸통 15% 이상: {cond_body_over_15_percent}"
            )
            
            # ===== 새로운 요약 알림 방식 =====
            # 거래 요약에 추가 (매수 조건 TRUE/FALSE)
            buy_emoji = "🟢" if buy else "⚪"
            trading_summary[coin_ticker] = f"{buy_emoji} 매수: {buy}"

            if buy:
                if BotDataDict.get(coin_ticker + '_BUY_DATE') != day_str and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                    
                    total_coin_count = len(INVEST_COIN_LIST)
                    num_open_positions = len(all_positions)

                    # 마지막 남은 코인일 때만 전체 잔고 사용, 아니면 할당비율 적용
                    if total_coin_count > 1 and num_open_positions == (total_coin_count - 1):
                        InvestMoney = current_usdt_balance
                    else:
                        InvestMoney = cycle_investment_base * INVEST_RATE * coin_data['rate']

                    BuyMoney = InvestMoney * (1.0 - FEE * set_leverage)
                    cap = df['value_ma'].iloc[-2] / 10
                    BuyMoney = min(max(BuyMoney, 10), cap)
                    
                    # 레버리지를 적용한 포지션 가치로 수량 계산
                    position_value = BuyMoney * set_leverage
                    amount = float(bitgetX.amount_to_precision(coin_ticker, GetAmount(position_value, now_price, 1.0)))
                    
                    print(f"[{account_name}] {coin_ticker} 주문 계산:")
                    print(f"  - 할당 증거금: {BuyMoney:.2f} USDT")
                    print(f"  - 레버리지: {set_leverage}배")
                    print(f"  - 포지션 가치: {position_value:.2f} USDT")
                    print(f"  - 현재가: {now_price:.2f} USDT")
                    print(f"  - 주문 수량: {amount:.6f} 개")
                    print(f"  - 실제 필요 금액: {amount * now_price:.2f} USDT")

                    try:
                        # 비트겟 크로스 모드 및 레버리지 설정
                        bitgetX.set_margin_mode('cross', coin_ticker, params={'marginCoin': 'USDT'})
                        time.sleep(0.1)
                        bitgetX.set_leverage(
                            leverage=set_leverage, 
                            symbol=coin_ticker,
                            params={
                                'marginCoin': 'USDT'
                            }
                        )
                        
                    except Exception as e:
                        print(f"[{account_name}] 레버리지 설정 오류: {e}")
                        telegram_alert.SendMessage(f"{first_String} {coin_ticker} 레버리지 설정 오류: {e}")

                    try:
                        # 실제 매수 주문 실행 (양방향 모드: tradeSide='open', holdSide='long')
                        bitgetX.create_order(coin_ticker, 'market', 'buy', amount, None, {'tradeSide': 'open', 'holdSide': 'long'})
                        BotDataDict[coin_ticker + '_BUY_DATE'] = day_str
                        BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                        with open(botdata_file_path, 'w') as f:
                            json.dump(BotDataDict, f, indent=4)
                        exec_msg = f"{first_String} {coin_ticker} 조건 만족하여 매수!! (투자금: {BuyMoney:.2f} USDT, 수량: {amount})"
                        print(exec_msg)
                        telegram_alert.SendMessage(exec_msg)
                    except Exception as e:
                        print(f"[{account_name}] 매수 주문 실패 for {coin_ticker}: {e}")
                        telegram_alert.SendMessage(f"[{account_name}] {coin_ticker} 매수 실패: {e}")
            else:
                if hour_n == 0 and min_n <= 2 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                    if "Main" in account_name:
                        warn_msg = f"{first_String} {coin_ticker} : 조건 만족하지 않아 현금 보유 합니다!"
                        print(warn_msg)
                        telegram_alert.SendMessage(warn_msg)

                    BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                    with open(botdata_file_path, 'w') as f:
                        json.dump(BotDataDict, f, indent=4)
    
    # ===== 거래 결과 요약 알림 =====
    if trading_summary:
        summary_msg = f"📊Bitget_[{account_name}] 거래 조건 검사 결과\n" + "="*35 + "\n"
        for ticker, status in trading_summary.items():
            summary_msg += f"{ticker}: {status}\n"
        telegram_alert.SendMessage(summary_msg)
    
    if hour_n == 0 and min_n <= 2:
        end_msg = f"{first_String} 종료"
        telegram_alert.SendMessage(end_msg)

# --- 메인 실행부 ---
if __name__ == '__main__':
    print("===== Bitget 다계정 자동매매 봇 시작 =====")
    for account in ACCOUNT_LIST:
        print(f"\n--- {account['name']} 거래 시작 (레버리지: {account['leverage']}배) ---")
        execute_trading_logic(account)
    print("\n===== 모든 계정 거래 실행 완료 =====")