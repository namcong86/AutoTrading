# -*- coding:utf-8 -*-
'''
Gate.io 선물 운영 봇 (DOGE + PEPE 50:50, 매수/매도 조건 동일)
'''
import ccxt
import time
import pandas as pd
import json
import socket
import sys
import os
import builtins
from datetime import datetime as dt_class

# 원본 print 함수 저장 및 타임스탬프 포함 print 함수 정의
_original_print = builtins.print

def timestamped_print(*args, **kwargs):
    """타임스탬프가 포함된 로그 출력 함수"""
    timestamp = dt_class.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

# 전역 print 함수를 타임스탬프 버전으로 교체
builtins.print = timestamped_print

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    sys.path.insert(0, "/var/AutoBot/Common")
else:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Common'))
import telegram_alert
import logging
import hashlib
import hmac
import requests
import datetime
import myBinance
import ende_key
import my_key 

# 암복호화 클래스 객체 생성
simpleEnDecrypt = myBinance.SimpleEnDecrypt(ende_key.ende_key)

# --- 계정 정보 설정 (Bitget과 동일한 구조) ---
ACCOUNT_LIST = [
    {
        "name": "Sub1",
        "access_key": simpleEnDecrypt.decrypt(my_key.gateio_access_S1),
        "secret_key": simpleEnDecrypt.decrypt(my_key.gateio_secret_S1),
        "leverage": 6
    }
]

# 현재 실행할 계정 (기본값: 첫 번째 계정)
current_account = ACCOUNT_LIST[0]
account_name = current_account["name"]
GateIO_AccessKey = current_account["access_key"]
GateIO_SecretKey = current_account["secret_key"]

# Gate.io Futures API 클래스 (2.Gateio_F_BTC_New.py 에서 복사)
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
            print(f"Error fetching futures account: {response.status_code} - {response.text}")
            return None


logger = logging.getLogger(__name__)

exchange = ccxt.gateio({
    'apiKey': GateIO_AccessKey,
    'secret': GateIO_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'defaultSettle': 'usdt',
        'createMarketBuyOrderRequiresPrice': False,
    }
})

# Gate.io Futures API 객체 생성 (2.Gateio_F_BTC_New.py 에서 복사)
gateio_api = GateioFuturesAPI(GateIO_AccessKey, GateIO_SecretKey)

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    botdata_file_path = f"/var/AutoBot/json/3-2.GateIO_F_10ALT_Safe_Leverage_Data_{account_name}.json"
else:
    botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', f'3-2.GateIO_F_10ALT_Safe_Leverage_Data_{account_name}.json')

try:
    with open(botdata_file_path, 'r') as f:
        BotDataDict = json.load(f)
except FileNotFoundError:
    BotDataDict = {}
    print(f"BotDataDict file not found. Creating new file: {botdata_file_path}")
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)
except json.JSONDecodeError:
    BotDataDict = {}
    print(f"Warning: {botdata_file_path} contained invalid JSON. Initializing with empty data.")
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)


if len(sys.argv) > 1:
    set_leverage = int(sys.argv[1])
else:
    set_leverage = current_account.get("leverage", 7)

InvestRate = 1
fee = 0.001

#알림 첫문구
first_String = f"[3-2.GateIO {account_name}] 10ALT {set_leverage}배 "

t = time.gmtime()
hour_n = t.tm_hour
min_n = t.tm_min
day_n = t.tm_mday
day_str = f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"



# 투자 코인 리스트 (Bitget과 동일 10종) - Gate.io 심볼 형식에 맞춰 기입
InvestCoinList = [
    {'ticker': 'DOGE_USDT', 'rate': 0.1},
    {'ticker': 'ADA_USDT', 'rate': 0.1},
    {'ticker': 'XLM_USDT', 'rate': 0.1},
    {'ticker': 'XRP_USDT', 'rate': 0.1},
    {'ticker': 'HBAR_USDT', 'rate': 0.1},
    {'ticker': 'ETH_USDT', 'rate': 0.1},
    {'ticker': 'PEPE_USDT', 'rate': 0.1},
    {'ticker': 'BONK_USDT', 'rate': 0.1},
    {'ticker': 'FLOKI_USDT', 'rate': 0.1},
    {'ticker': 'SUI_USDT', 'rate': 0.1},
]

# --- Helper Functions (myBinance 대체) ---
def get_ohlcv_gateio(exchange_obj, ticker, timeframe='1d', limit=100):
    """Gate.io에서 OHLCV 데이터를 가져옵니다."""
    try:
        ohlcv = exchange_obj.fetch_ohlcv(ticker, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
    except Exception as e:
        print(f"Error fetching OHLCV for {ticker}: {e}")
        return pd.DataFrame()

def get_coin_now_price_gateio(exchange_obj, ticker):
    """Gate.io에서 현재 코인 가격을 가져옵니다."""
    try:
        return exchange_obj.fetch_ticker(ticker)['last']
    except Exception as e:
        print(f"Error fetching ticker for {ticker}: {e}")
        return None

def get_amount_gateio(exchange_obj, ticker, buy_money_usd, price, leverage):
    """
    매수 금액 (USD), 가격, 레버리지를 바탕으로 매수할 '계약 수'를 계산합니다.
    Gate.io의 'contractSize'를 고려하여 거래소에서 요구하는 정확한 계약 수량을 반환합니다.
    
    Parameters:
    - buy_money_usd: 증거금 (USDT)
    - leverage: 레버리지 (보통 1.0 - 이미 calculate된 상태)
    - price: 현재 코인 가격
    """
    if price is None or price == 0: 
        return 0

    try:
        # 레버리지 적용된 포지션 가치 (USDT)
        # buy_money_usd는 이미 증거금이므로, leverage * buy_money_usd = 포지션의 총 명목가
        leveraged_position_value = buy_money_usd * leverage 
        
        # 예상 코인 수량 (레버리지 적용된 가치를 현재 코인 가격으로 나눔)
        # 이것이 실제 매수할 코인의 개수입니다
        estimated_coin_amount = leveraged_position_value / price

        # Gate.io contractSize는 보통 1이므로, 직접 반환
        # (만약 다른 값이면 곱하기)
        market_info = exchange_obj.market(ticker)
        contract_size_raw = market_info.get('contractSize')
        if contract_size_raw is None:
            contractSize = 1.0
        else:
            contractSize = float(contract_size_raw) if contract_size_raw else 1.0
        
        # 계약 수량 = 코인 수량 / contractSize
        # 예: ETH 0.3개, contractSize=1 → 계약 수 0.3
        amount_in_contracts = estimated_coin_amount / contractSize

        return amount_in_contracts
    except Exception as e:
        print(f"Error calculating amount for {ticker}: {e}")
        return 0


# --- 전체 포지션 존재 여부 확인 (루프 시작 전 한 번) ---
all_current_positions = []
try:
    # 모든 마켓 정보를 미리 로드하여 get_amount_gateio에서 사용할 수 있도록 함
    exchange.load_markets() 
    all_current_positions = exchange.fetch_positions(symbols=[cd['ticker'] for cd in InvestCoinList], params={'settle': 'usdt'})
    all_current_positions = [p for p in all_current_positions if p.get('contracts') is not None and abs(p['contracts']) > 0]
except Exception as e:
    print(f"포지션 정보 조회 중 오류: {e}")


is_any_bot_position_active = bool(all_current_positions)


# --- 메인 루프 ---
# 모든 코인의 거래 결과를 요약할 딕셔너리
trading_summary = {}

for coin_data in InvestCoinList:
    coin_ticker = coin_data['ticker']
    # market_id = exchange.market(coin_ticker)['id'] # 사용되지 않아 주석 처리
    #logger.info(f"\n---- Processing coin: {coin_ticker}")

    # BotData 기본 키 초기화
    for key_suffix in ["_BUY_DATE", "_SELL_DATE", "_DATE_CHECK"]:
        full_key = coin_ticker + key_suffix
        if full_key not in BotDataDict:
            BotDataDict[full_key] = "" if key_suffix != "_DATE_CHECK" else 0
    with open(botdata_file_path, 'w') as f:
        json.dump(BotDataDict, f)

    # 잔고 조회
    total_usdt = 0
    max_retries = 3
    retry_delay = 5 # 초 단위

    for attempt in range(max_retries):
        try:
            account = gateio_api.get_futures_account(settle='usdt')
            #logger.info(f"Raw account data for {coin_ticker}: {account}")
            time.sleep(0.1)

            if account and 'available' in account:
                total_usdt = float(account['available'])
                print(f"Found USDT balance for {coin_ticker} in Perpetual Futures (Gate.io API): {total_usdt}")
                break
            else:
                print(f"No USDT balance found for {coin_ticker} in Gate.io API response. Retrying...")
                if attempt == max_retries - 1:
                    print(f"No USDT balance available for {coin_ticker} after retries. Cannot proceed with trading.")
                    total_usdt = 0
                    break
                time.sleep(retry_delay)
        except Exception as e:
            print(f"Error fetching balance for {coin_ticker} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print(f"Cannot proceed for {coin_ticker} without balance information.")
                total_usdt = 0
                break
            time.sleep(retry_delay)
    
    if total_usdt == 0:
        print(f"{coin_ticker} 잔고가 없어 다음 코인으로 넘어갑니다.")
        continue # 잔고가 없으면 해당 코인 스킵

    # Gate.io cross 모드 미리 설정 (포지션 생성 전)
    try:
        exchange.set_margin_mode('cross', coin_ticker, params={'settle': 'usdt'})
        print(f"{coin_ticker} cross 모드 설정 완료.")
        time.sleep(0.1)
    except Exception as e:
        print(f"{coin_ticker} cross 모드 설정 오류: {e}")

    # 포지션 정보 (LONG)
    amt_b = 0.0
    unrealizedProfit = 0.0
    position_info = None

    try:
        current_position_list = exchange.fetch_positions(symbols=[coin_ticker], params={'settle': 'usdt'})
        print(f"{coin_ticker} 포지션 조회 응답 개수: {len(current_position_list)}")
        if current_position_list:
            for pos_info in current_position_list:
                print(f"{coin_ticker} 포지션 상세 - symbol: {pos_info.get('symbol')}, side: {pos_info.get('side')}, contracts: {pos_info.get('contracts')}")
                # side가 'long'이고 contracts > 0인 경우만 처리
                # 심볼 비교: exchange.market(coin_ticker)['id']로 정확한 심볼 얻기
                pos_symbol = pos_info.get('symbol', '')
                if pos_symbol and pos_info.get('side') == 'long' and float(pos_info.get('contracts', 0)) > 0:
                    amt_b = float(pos_info['contracts'])
                    unrealizedProfit = float(pos_info['unrealizedPnl'])
                    position_info = pos_info
                    print(f"{coin_ticker} 포지션 발견 - 수량: {amt_b}, 미실현 수익: {unrealizedProfit}")
                    break

    except Exception as e:
        print(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")
        telegram_alert.SendMessage(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")

    # 지표용 일봉 데이터 조회
    df = get_ohlcv_gateio(exchange, coin_ticker, '1d', limit=260)  # 200MA 계산 대비
    if df.empty or len(df) < 60:
        print(f"{coin_ticker} 데이터 부족으로 건너뜜. (가져온 데이터 수: {len(df)})")
        continue
    # 거래대금
    df['value'] = df['close'] * df['volume']
    # RSI
    period = 14
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    gain = up.ewm(com=period-1, min_periods=period).mean()
    loss = down.ewm(com=period-1, min_periods=period).mean()
    RS = gain / loss.replace(0, 1e-9)
    df['rsi'] = 100 - (100 / (1 + RS))
    df['rsi_ma'] = df['rsi'].rolling(14, min_periods=14).mean()
    # 변화율
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    # 이동평균선 (Bitget과 동일)
    for ma_val in [3, 7, 20, 30, 50, 200]:
        df[f'{ma_val}ma'] = df['close'].rolling(ma_val, min_periods=ma_val).mean()
    # 거래대금 평균 및 30MA 기울기
    df['value_ma'] = df['value'].rolling(10, min_periods=10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5).replace(0, 1e-9)) * 100
    
    # Disparity Index 계산 (종가 / 15일 이동평균 * 100)
    df['Disparity_Index_ma'] = df['close'].rolling(window=16).mean()
    df['disparity_index'] = (df['close'] / df['Disparity_Index_ma']) * 100
    
    df.dropna(inplace=True)
    if len(df) < 60:
        print(f"{coin_ticker} 지표 계산 후 데이터 부족으로 건너뜜. (남은 데이터 수: {len(df)})")
        continue

    now_price = get_coin_now_price_gateio(exchange, coin_ticker)
    if now_price is None:
        print(f"{coin_ticker} 현재 가격 조회 실패로 건너뜜.")
        continue
    
    DiffValue = -2  # 30MA 기울기 기준

    # --- 매도 로직 (포지션 보유 시) ---
    if abs(amt_b) > 0:
        print(f"{coin_ticker} 포지션이 있어 매도 조건 확인 중. 현재 포지션 수량: {amt_b}")

        # Bitget과 동일한 매도 조건
        def is_doji_candle(o, c, h, l):
            rng = h - l
            if rng == 0:
                return False
            return abs(o - c) / rng <= 0.1

        is_doji_1 = is_doji_candle(df['open'].iloc[-2], df['close'].iloc[-2], df['high'].iloc[-2], df['low'].iloc[-2])
        is_doji_2 = is_doji_candle(df['open'].iloc[-3], df['close'].iloc[-3], df['high'].iloc[-3], df['low'].iloc[-3])
        cond_doji = is_doji_1 and is_doji_2
        cond_fall_pattern = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
        cond_2_neg_candle = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
        cond_loss = (unrealizedProfit < 0)
        cond_not_rising = not (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])
        original_sell_cond = (cond_fall_pattern or cond_2_neg_candle or cond_loss) and cond_not_rising
        sell_triggered = original_sell_cond or cond_doji

        # 텔레그램 알림 (Bitget 형식) - 수익률 계산: 저장된 증거금 또는 포지션 정보로 추정
        try:
            invest_base = float(BotDataDict.get(coin_ticker + '_LAST_MARGIN_USDT', 0.0))
        except Exception:
            invest_base = 0.0
        if invest_base <= 0:
            try:
                market_info = exchange.market(coin_ticker)
                contract_size = float(market_info.get('contractSize', '1'))
                entry_price = None
                if position_info:
                    entry_price = position_info.get('entryPrice') or position_info.get('entry_price')
                if entry_price is None:
                    entry_price = now_price
                notional = abs(amt_b) * contract_size * float(entry_price)
                invest_base = notional / max(int(set_leverage), 1)
            except Exception:
                invest_base = 1.0
        RevenueRate = (unrealizedProfit / max(invest_base, 1e-9)) * 100.0

        # ===== 이전 알림 방식 (로그 출력) =====
        print(
            f"<{first_String} {coin_ticker} 매도 조건 검사>\n"
            f"- 포지션 보유 중 (수익률: {RevenueRate:.2f}%)\n\n"
            f"▶️ 최종 매도 결정: {sell_triggered}\n"
            f"--------------------\n"
            f"[기본 매도 조건: {original_sell_cond}]\n"
            f" ㄴ하락패턴: {cond_fall_pattern}\n"
            f" ㄴ2연속음봉: {cond_2_neg_candle}\n"
            f" ㄴ손실중: {cond_loss}\n"
            f" ㄴ(AND)상승추세아님: {cond_not_rising}\n"
            f"[추가 매도 조건]\n"
            f" ㄴ2연속도지: {cond_doji}"
        )
        
        # ===== 새로운 요약 알림 방식 =====
        # 거래 요약에 추가 (수익률과 매도조건)
        sell_emoji = "🔴" if sell_triggered else "⚪"
        trading_summary[coin_ticker] = f"{sell_emoji} 수익률: {RevenueRate:.1f}% | 매도: {sell_triggered}"

        if BotDataDict.get(coin_ticker + '_DATE_CHECK') == day_n:
            sell_triggered = False
            print(f"{coin_ticker} 금일 이미 거래 발생하였습니다.")

        if sell_triggered:
            try:
                sell_params = {'reduceOnly': True, 'settle': 'usdt'}
                exchange.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params=sell_params)
                
                exec_msg = f"{first_String} 조건 만족하여 매도 ({coin_ticker}) (참고 미실현수익: {unrealizedProfit:.2f} USDT)"
                print(exec_msg)
                telegram_alert.SendMessage(exec_msg)
                
                BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)
            except Exception as e:
                err_msg = f"{first_String} {coin_ticker} 매도 주문 실패: {e}"
                print(err_msg)
                telegram_alert.SendMessage(err_msg)
    # --- 매수 로직 (포지션 없음) ---
    else:
        print(f"{coin_ticker} 포지션이 없어 매수 조건 확인 중.")

        # Bitget과 동일한 매수 조건
        cond_no_surge = df['change'].iloc[-2] < 0.5
        is_above_200ma = df['close'].iloc[-2] > df['200ma'].iloc[-2]
        cond_ma_50 = True
        # 추가 조건 2개
        cond_no_long_upper_shadow = True
        cond_body_over_15_percent = True
        if is_above_200ma:
            cond_ma_50 = (df['50ma'].iloc[-3] <= df['50ma'].iloc[-2])
            prev_candle = df.iloc[-2]
            upper_shadow = prev_candle['high'] - max(prev_candle['open'], prev_candle['close'])
            body_and_lower_shadow = max(prev_candle['open'], prev_candle['close']) - prev_candle['low']
            cond_no_long_upper_shadow = upper_shadow <= body_and_lower_shadow
            candle_range = prev_candle['high'] - prev_candle['low']
            candle_body = abs(prev_candle['open'] - prev_candle['close'])
            if candle_range > 0:
                cond_body_over_15_percent = (candle_body >= candle_range * 0.15)

        cond_2_pos_candle = (df['open'].iloc[-2] < df['close'].iloc[-2]) and (df['open'].iloc[-3] < df['close'].iloc[-3])
        cond_price_up = (df['close'].iloc[-3] < df['close'].iloc[-2]) and (df['high'].iloc[-3] < df['high'].iloc[-2])
        cond_7ma_up = (df['7ma'].iloc[-3] < df['7ma'].iloc[-2])
        cond_30ma_slope = (df['30ma_slope'].iloc[-2] > -2)
        cond_rsi_ma_up = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2])
        cond_20ma_up = (df['20ma'].iloc[-3] <= df['20ma'].iloc[-2])
        
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

        buy_triggered = (
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
            f"▶️ 최종 매수 결정: {buy_triggered}\n"
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
        buy_emoji = "🟢" if buy_triggered else "⚪"
        trading_summary[coin_ticker] = f"{buy_emoji} 매수: {buy_triggered}"
        
        if buy_triggered: 
            if BotDataDict.get(coin_ticker + '_BUY_DATE') != day_str and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n :
                # ------ 투자금액 결정! ------
                if not is_any_bot_position_active:
                    InvestMoney_base = total_usdt * InvestRate * coin_data['rate']
                else:
                    InvestMoney_base = total_usdt * InvestRate
                
                BuyMargin = InvestMoney_base # 이 값은 USDT 기준의 '증거금'입니다.
                
                # cap = df['value_ma'].iloc[-2] / 10 
                # BuyMargin = min(max(BuyMargin, 10.0), cap)

                try:
                    # Gate.io 레버리지 설정 (cross 마진 모드 강제 적용)
                    # CCXT는 'set_leverage' 시 marginMode를 파라미터로 받는 것을 지원합니다.
                    leverage_params = {
                        'settle': 'usdt',
                        # Gate.io의 경우, 마진 모드를 명시적으로 파라미터에 넣어줍니다.
                        'marginMode': 'cross' 
                    }
                    exchange.set_leverage(set_leverage, coin_ticker, params=leverage_params)
                    print(f"{coin_ticker} 레버리지 {set_leverage}배 및 cross 모드 설정 완료.")
                    time.sleep(0.1)

                except Exception as e:
                    print(f"{coin_ticker} 레버리지 설정 오류: {e}. 주문은 계속 시도됩니다.")

                try:
                    # now_price는 현재 코인 1개당 USDT 가격입니다.
                    # amount_to_buy는 get_amount_gateio로부터 반환된 '계약 수'입니다.
                    # BuyMargin은 이미 증거금이므로 레버리지를 set_leverage로 전달
                    amount_to_buy = get_amount_gateio(exchange, coin_ticker, BuyMargin, now_price, set_leverage)

                    # contractSize 확인 로그
                    market_info_debug = exchange.market(coin_ticker)
                    contract_size_debug = market_info_debug.get('contractSize', 1.0)
                    print(f"{coin_ticker} 계약 정보 - contractSize: {contract_size_debug}, 현재가: {now_price:.2f} USDT")
                    print(f"{coin_ticker} 매수 계산 - 증거금: {BuyMargin:.2f} USDT, 레버리지: {set_leverage}배, 포지션 가치: {BuyMargin * set_leverage:.2f} USDT, 진입 계약수: {amount_to_buy:.6f}")

                    if amount_to_buy <= 0:
                        print(f"{coin_ticker} 계산된 매수 수량이 0 이하입니다. 매수 주문을 생성하지 않습니다.")
                    else:
                        market_info = exchange.market(coin_ticker)
                        contract_size_raw = market_info.get('contractSize')
                        if contract_size_raw is None:
                            contractSize = 1.0
                        else:
                            contractSize = float(contract_size_raw) if contract_size_raw else 1.0

                        # Gate.io 선물 매수 주문 (settle 파라미터 필수)
                        exchange.create_order(coin_ticker, 'market', 'buy', amount_to_buy, None, params={'settle': 'usdt'})

                        BotDataDict[coin_ticker + '_BUY_DATE'] = day_str
                        BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                        BotDataDict[coin_ticker + '_LAST_MARGIN_USDT'] = float(BuyMargin)
                        with open(botdata_file_path, 'w') as f:
                            json.dump(BotDataDict, f)

                        # 로그 메시지에 실제 매수될 '코인 수량' (계약 수 * contractSize)을 표시합니다.
                        actual_bought_coin_quantity = amount_to_buy * contractSize
                        
                        # 추가 로그: 진입 수량과 USDT 기준
                        position_notional = amount_to_buy * contractSize * now_price
                        print(f"{coin_ticker} 매수 체결 - 진입수량: {actual_bought_coin_quantity:.6f}개, 포지션 명목가: {position_notional:.2f} USDT, 증거금: {BuyMargin:.2f} USDT, 레버리지: {set_leverage}배")
                         
                        exec_msg = (f"{first_String} 조건 만족하여 매수({coin_ticker}) "
                                    f"(증거금: {BuyMargin:.2f} USDT, "
                                    f"예상 포지션 가치: {BuyMargin * set_leverage:.2f} USDT, " 
                                    f"매수 계약 수: {amount_to_buy:.6f}, "
                                    f"실제 매수 코인 수: {actual_bought_coin_quantity:.2f})")
                        print(exec_msg)
                        telegram_alert.SendMessage(exec_msg)
                except Exception as e:
                    err_msg = f"{coin_ticker} 매수 주문 실패: {e}"
                    print(err_msg)
                    telegram_alert.SendMessage(err_msg)
            else:
                print(f"{coin_ticker} 금일 이미 매수 또는 거래 제한일. 매수 건너뛰었습니다. BUY_DATE: {BotDataDict.get(coin_ticker + '_BUY_DATE')}, DATE_CHECK: {BotDataDict.get(coin_ticker + '_DATE_CHECK')}")

        else:
            if hour_n == 0 and min_n <= 2 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n 
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)

# --- 루프 종료 후 작업 ---
# ===== 거래 결과 요약 알림 =====
if trading_summary:
    summary_msg = f"📊 3-2.GateIO [{account_name}] 거래 조건 검사 결과\n" + "="*35 + "\n"
    for ticker, status in trading_summary.items():
        summary_msg += f"{ticker}: {status}\n"
    telegram_alert.SendMessage(summary_msg)

