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

# 암호화된 액세스키와 시크릿키 복호화
GateIO_AccessKey = simpleEnDecrypt.decrypt(my_key.gateio_access)
GateIO_SecretKey = simpleEnDecrypt.decrypt(my_key.gateio_secret)

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

# 로깅 설정 (2.Gateio_F_BTC_New.py 에서 복사 및 수정)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('trading_bot_doge_pepe.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

exchange = ccxt.gateio({
    'apiKey': GateIO_AccessKey,
    'secret': GateIO_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'createMarketBuyOrderRequiresPrice': False,
    }
})

# Gate.io Futures API 객체 생성 (2.Gateio_F_BTC_New.py 에서 복사)
gateio_api = GateioFuturesAPI(GateIO_AccessKey, GateIO_SecretKey)

pcServerGb = socket.gethostname()
if pcServerGb == "AutoBotCong":
    botdata_file_path = "/var/AutoBot/json/3.GateIO_F_DOGE_PEPE_Leverage_Data.json"
else:
    botdata_file_path = os.path.join(os.path.dirname(__file__), '..', 'json', '3.GateIO_F_DOGE_PEPE_Leverage_Data.json')

try:
    with open(botdata_file_path, 'r') as f:
        BotDataDict = json.load(f)
except FileNotFoundError:
    BotDataDict = {}
    logger.info(f"BotDataDict file not found. Creating new file: {botdata_file_path}")
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)
except json.JSONDecodeError:
    BotDataDict = {}
    logger.warning(f"Warning: {botdata_file_path} contained invalid JSON. Initializing with empty data.")
    with open(botdata_file_path, 'w') as outfile:
        json.dump(BotDataDict, outfile, indent=4)


if len(sys.argv) > 1:
    set_leverage = int(sys.argv[1])
else:
    set_leverage = 3

InvestRate = 1
fee = 0.001

#알림 첫문구
first_String = f"3.GateIO DOGE+PEPE {set_leverage}배 "

t = time.gmtime()
hour_n = t.tm_hour
min_n = t.tm_min
day_n = t.tm_mday
day_str = f"{t.tm_year}{t.tm_mon:02d}{t.tm_mday:02d}"

if hour_n == 0 and min_n <= 2:
    start_msg = f"{first_String} 시작"
    telegram_alert.SendMessage(start_msg)
    logger.info(start_msg)


# 투자 코인 리스트 (Bitget과 동일 10종) - Gate.io 심볼 형식에 맞춰 기입
InvestCoinList = [
    {'ticker': 'DOGE_USDT', 'rate': 0.12},
    {'ticker': 'ADA_USDT', 'rate': 0.12},
    {'ticker': 'XLM_USDT', 'rate': 0.10},
    {'ticker': 'XRP_USDT', 'rate': 0.10},
    {'ticker': 'HBAR_USDT', 'rate': 0.10},
    {'ticker': 'ETH_USDT', 'rate': 0.10},
    {'ticker': 'PEPE_USDT', 'rate': 0.10},
    {'ticker': 'BONK_USDT', 'rate': 0.10},
    {'ticker': 'FLOKI_USDT', 'rate': 0.08},
    {'ticker': 'SHIB_USDT', 'rate': 0.08},
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
        logger.error(f"Error fetching OHLCV for {ticker}: {e}")
        return pd.DataFrame()

def get_coin_now_price_gateio(exchange_obj, ticker):
    """Gate.io에서 현재 코인 가격을 가져옵니다."""
    try:
        return exchange_obj.fetch_ticker(ticker)['last']
    except Exception as e:
        logger.error(f"Error fetching ticker for {ticker}: {e}")
        return None

def get_amount_gateio(exchange_obj, ticker, buy_money_usd, price, leverage):
    """
    매수 금액 (USD), 가격, 레버리지를 바탕으로 매수할 '계약 수'를 계산합니다.
    Gate.io의 'quanto_multiplier'를 고려하여 CCXT의 precision을 통해
    거래소에서 요구하는 정확한 계약 수량을 반환합니다.
    """
    if price is None or price == 0: return 0

    # 해당 코인의 market 정보를 가져옵니다.
    market_info = exchange_obj.market(ticker)
    
    # quanto_multiplier를 가져오되, 없으면 기본값 1을 사용 (대부분의 코인은 1)
    # Gate.io API는 string으로 반환할 수 있으므로 float으로 변환
    contractSize = float(market_info.get('contractSize', '1'))
    
    # 레버리지 적용된 포지션 가치 (USDT)
    leveraged_position_value = buy_money_usd * leverage 
    
    # 예상 코인 수량 (레버리지 적용된 가치를 현재 코인 가격으로 나눔)
    estimated_coin_amount = leveraged_position_value / price

    # 이 코인 수량을 contractSize 나누어 '계약 수'를 계산합니다.
    # Gate.io에서 create_market_buy_order는 이 '계약 수'를 인자로 받습니다.
    amount_in_contracts = estimated_coin_amount / contractSize

    # CCXT의 amount_to_precision을 사용하여 거래소의 정밀도에 맞춰 조정된 '계약 수'를 얻습니다.
    # 이 값이 실제 주문에 사용될 '계약 수'입니다.
    final_order_amount = amount_in_contracts
    
    return final_order_amount


# --- 전체 포지션 존재 여부 확인 (루프 시작 전 한 번) ---
all_current_positions = []
try:
    # 모든 마켓 정보를 미리 로드하여 get_amount_gateio에서 사용할 수 있도록 함
    exchange.load_markets() 
    all_current_positions = exchange.fetch_positions(symbols=[cd['ticker'] for cd in InvestCoinList])
    all_current_positions = [p for p in all_current_positions if p.get('contracts') is not None and abs(p['contracts']) > 0]
except Exception as e:
    logger.error(f"포지션 정보 조회 중 오류: {e}")


is_any_bot_position_active = bool(all_current_positions)


# --- 메인 루프 ---
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
                logger.info(f"Found USDT balance for {coin_ticker} in Perpetual Futures (Gate.io API): {total_usdt}")
                break
            else:
                logger.warning(f"No USDT balance found for {coin_ticker} in Gate.io API response. Retrying...")
                if attempt == max_retries - 1:
                    logger.error(f"No USDT balance available for {coin_ticker} after retries. Cannot proceed with trading.")
                    total_usdt = 0
                    break
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Error fetching balance for {coin_ticker} (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logger.error(f"Cannot proceed for {coin_ticker} without balance information.")
                total_usdt = 0
                break
            time.sleep(retry_delay)
    
    if total_usdt == 0:
        logger.warning(f"{coin_ticker} 잔고가 없어 다음 코인으로 넘어갑니다.")
        continue # 잔고가 없으면 해당 코인 스킵

    # 포지션 정보 (LONG)
    amt_b = 0.0
    unrealizedProfit = 0.0
    position_info = None

    try:
        current_position_list = exchange.fetch_positions(symbols=[coin_ticker], params={'type': 'swap'})
        if current_position_list:
            for pos_info in current_position_list:
                if pos_info['symbol'] == coin_ticker and pos_info['side'] == 'long':
                    amt_b = float(pos_info['contracts'])
                    unrealizedProfit = float(pos_info['unrealizedPnl'])
                    position_info = pos_info
                    break

    except Exception as e:
        logger.error(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")
        telegram_alert.SendMessage(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")

    # 지표용 일봉 데이터 조회
    df = get_ohlcv_gateio(exchange, coin_ticker, '1d', limit=260)  # 200MA 계산 대비
    if df.empty or len(df) < 60:
        logger.warning(f"{coin_ticker} 데이터 부족으로 건너뜜. (가져온 데이터 수: {len(df)})")
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
    df['Disparity_Index_ma'] = df['close'].rolling(window=15).mean()
    df['disparity_index'] = (df['close'] / df['Disparity_Index_ma']) * 100
    
    df.dropna(inplace=True)
    if len(df) < 60:
        logger.warning(f"{coin_ticker} 지표 계산 후 데이터 부족으로 건너뜜. (남은 데이터 수: {len(df)})")
        continue

    now_price = get_coin_now_price_gateio(exchange, coin_ticker)
    if now_price is None:
        logger.warning(f"{coin_ticker} 현재 가격 조회 실패로 건너뜜.")
        continue
    
    DiffValue = -2  # 30MA 기울기 기준

    # --- 매도 로직 (포지션 보유 시) ---
    if abs(amt_b) > 0:
        logger.info(f"{coin_ticker} 포지션이 있어 매도 조건 확인 중. 현재 포지션 수량: {amt_b}")

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

        alert_msg = (
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
        telegram_alert.SendMessage(alert_msg)

        if BotDataDict.get(coin_ticker + '_DATE_CHECK') == day_n:
            sell_triggered = False
            logger.info(f"{coin_ticker} 금일 이미 거래 발생하였습니다.")

        if sell_triggered:
            try:
                sell_params = {'reduceOnly': True, 'settle': 'usdt'}
                exchange.create_order(coin_ticker, 'market', 'sell', abs(amt_b), None, params=sell_params)
                
                exec_msg = f"{first_String} 조건 만족하여 매도 ({coin_ticker}) (참고 미실현수익: {unrealizedProfit:.2f} USDT)"
                logger.info(exec_msg)
                telegram_alert.SendMessage(exec_msg)
                
                BotDataDict[coin_ticker + '_SELL_DATE'] = day_str
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)
            except Exception as e:
                err_msg = f"{first_String} {coin_ticker} 매도 주문 실패: {e}"
                logger.error(err_msg)
                telegram_alert.SendMessage(err_msg)
    # --- 매수 로직 (포지션 없음) ---
    else:
        logger.info(f"{coin_ticker} 포지션이 없어 매수 조건 확인 중.")

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

        # 텔레그램 알림 (Bitget 형식)
        alert_msg = (
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
        telegram_alert.SendMessage(alert_msg)
        
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
                    exchange.set_leverage(set_leverage, coin_ticker, params={'type': 'swap', 'marginMode': 'cross'})
                    logger.info(f"{coin_ticker} 레버리지 {set_leverage}배, 교차 마진(Cross) 설정 완료.")
                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"{coin_ticker} 레버리지 설정 오류: {e}. 주문은 시도됩니다.")

                try:
                    # now_price는 현재 코인 1개당 USDT 가격입니다.
                    # amount_to_buy는 get_amount_gateio로부터 반환된 '계약 수'입니다.
                    amount_to_buy = get_amount_gateio(exchange, coin_ticker, BuyMargin, now_price, set_leverage)

                    if amount_to_buy <= 0:
                        logger.error(f"{coin_ticker} 계산된 매수 수량이 0 이하입니다. 매수 주문을 생성하지 않습니다.")
                    else:
                        market_info = exchange.market(coin_ticker)
                        contractSize = float(market_info.get('contractSize', '1')) # string -> float

                        # exchange.create_market_buy_order 함수는 두 번째 인자로 '계약 수'를 받습니다.
                        exchange.create_market_buy_order(coin_ticker, amount_to_buy, params={'type': 'swap'})

                        BotDataDict[coin_ticker + '_BUY_DATE'] = day_str
                        BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n
                        BotDataDict[coin_ticker + '_LAST_MARGIN_USDT'] = float(BuyMargin)
                        with open(botdata_file_path, 'w') as f:
                            json.dump(BotDataDict, f)

                        # 로그 메시지에 실제 매수될 '코인 수량' (계약 수 * contractSize)을 표시합니다.
                        actual_bought_coin_quantity = amount_to_buy * contractSize
                         
                        exec_msg = (f"{first_String} 조건 만족하여 매수({coin_ticker}) "
                                    f"(증거금: {BuyMargin:.2f} USDT, "
                                    f"예상 포지션 가치: {BuyMargin * set_leverage:.2f} USDT, " 
                                    f"매수 계약 수: {amount_to_buy:.6f}, "
                                    f"실제 매수 코인 수: {actual_bought_coin_quantity:.2f})")
                        logger.info(exec_msg)
                        telegram_alert.SendMessage(exec_msg)
                except Exception as e:
                    err_msg = f"{coin_ticker} 매수 주문 실패: {e}"
                    logger.error(err_msg)
                    telegram_alert.SendMessage(err_msg)
            else:
                logger.info(f"{coin_ticker} 금일 이미 매수 또는 거래 제한일. 매수 건너뛰었습니다. BUY_DATE: {BotDataDict.get(coin_ticker + '_BUY_DATE')}, DATE_CHECK: {BotDataDict.get(coin_ticker + '_DATE_CHECK')}")

        else:
            if hour_n == 0 and min_n <= 2 and BotDataDict.get(coin_ticker + '_DATE_CHECK') != day_n:
                warn_msg = f"{first_String} 조건 만족하지 않아 현금 보유 합니다({coin_ticker})"
                logger.info(warn_msg)
                telegram_alert.SendMessage(warn_msg)
                
                BotDataDict[coin_ticker + '_DATE_CHECK'] = day_n 
                with open(botdata_file_path, 'w') as f:
                    json.dump(BotDataDict, f)

# --- 루프 종료 후 작업 ---
if hour_n == 0 and min_n <= 2:
    end_msg = f"{first_String} 종료 "
    telegram_alert.SendMessage(end_msg)
    logger.info(end_msg)