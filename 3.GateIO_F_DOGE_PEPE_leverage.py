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
import telegram_alert
import logging
import hashlib
import hmac
import requests
import datetime

# Gate.io API 키 (실제 키로 교체하고 보안상 환경변수 사용 권장)
GateIO_AccessKey = "07a0ba2f6ed018fcb0fde7d08b58b40c"
GateIO_SecretKey = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"

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
    botdata_file_path = "/var/AutoBot/json/GateIO_F_DOGE_PEPE_Data.json"
else:
    botdata_file_path = "./GateIO_F_DOGE_PEPE_Data.json"

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

InvestCoinList = [
    {'ticker': 'DOGE/USDT:USDT', 'rate': 0.5},
    {'ticker': 'PEPE/USDT:USDT', 'rate': 0.5}
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
    logger.info(f"\n---- Processing coin: {coin_ticker}")

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
            logger.info(f"Raw account data for {coin_ticker}: {account}")
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

    try:
        current_position_list = exchange.fetch_positions(symbols=[coin_ticker], params={'type': 'swap'})
        if current_position_list:
            for pos_info in current_position_list:
                if pos_info['symbol'] == coin_ticker and pos_info['side'] == 'long':
                    amt_b = float(pos_info['contracts'])
                    unrealizedProfit = float(pos_info['unrealizedPnl'])
                    break

    except Exception as e:
        logger.error(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")
        telegram_alert.SendMessage(f"{first_String} {coin_ticker} 포지션 조회 오류: {e}")

    # 지표용 일봉 데이터 조회
    df = get_ohlcv_gateio(exchange, coin_ticker, '1d', limit=100)
    if df.empty or len(df) < 50:
        logger.warning(f"{coin_ticker} 데이터 부족으로 건너뜜. (가져온 데이터 수: {len(df)})")
        continue
    df['value'] = df['close'] * df['volume']

    # RSI 계산
    period = 14
    delta = df['close'].diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    gain = up.ewm(com=period-1, min_periods=period).mean()
    loss = down.ewm(com=period-1, min_periods=period).mean()
    if loss.eq(0).any():
        RS = pd.Series([float('inf') if l == 0 and g > 0 else 0 if l == 0 and g == 0 else g / l for g, l in zip(gain, loss)], index=gain.index)
    else:
        RS = gain / loss
    df['rsi'] = 100 - (100 / (1 + RS))
    df['rsi_ma'] = df['rsi'].rolling(14).mean()

    # MACD 계산
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # 이동평균선
    for ma_val in [3, 7, 12, 24, 30, 50]:
        df[f'{ma_val}ma'] = df['close'].rolling(ma_val).mean()
    df['value_ma'] = df['value'].rolling(10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    
    required_length_for_iloc = 5
    df.dropna(inplace=True)
    if len(df) < required_length_for_iloc:
        logger.warning(f"{coin_ticker} 지표 계산 후 데이터 부족으로 건너뜜. (남은 데이터 수: {len(df)})")
        continue

    now_price = get_coin_now_price_gateio(exchange, coin_ticker)
    if now_price is None:
        logger.warning(f"{coin_ticker} 현재 가격 조회 실패로 건너뜜.")
        continue
        
    DiffValue = -2

    # --- 매도 로직 (포지션 보유 시) ---
    if abs(amt_b) > 0:
        logger.info(f"{coin_ticker} 포지션이 있어 매도 조건 확인 중. 현재 포지션 수량: {amt_b}")
        cond_high_low = (df['high'].iloc[-3] > df['high'].iloc[-2] and df['low'].iloc[-3] > df['low'].iloc[-2])
        cond_open_close = (df['open'].iloc[-2] > df['close'].iloc[-2] and df['open'].iloc[-3] > df['close'].iloc[-3])
        cond_revenue = (unrealizedProfit < 0)
        cond_cancel = (df['rsi_ma'].iloc[-3] < df['rsi_ma'].iloc[-2] and df['3ma'].iloc[-3] < df['3ma'].iloc[-2])
        
        analysis_msg = (f"{first_String}  매도조건 분석 ({coin_ticker}): high_low={cond_high_low}, "
                         f"open_close={cond_open_close}, revenue<0={cond_revenue}, "
                         f"cancel_by_rsi_ma={cond_cancel}")
        logger.info(analysis_msg)
        telegram_alert.SendMessage(analysis_msg)

        sell_triggered = (cond_high_low or cond_open_close or cond_revenue) and not cond_cancel
        
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

        analysis_msg = (f"{first_String} 매수조건 분석 ({coin_ticker}): 연속양봉={cond_o1 and cond_o2}, "
                        f"종가증가={cond_close_inc}, 고점증가={cond_high_inc}, "
                        f"7이평증가={cond_7ma}, 50이평증가={cond_50ma}, 30이평기울기={cond_slope}, "
                        f"RSI증가={cond_rsi_inc} ({df['rsi_ma'].iloc[-3]:.2f}->{df['rsi_ma'].iloc[-2]:.2f}), "
                        f"MACD={cond_MACD}, 도지캔들={cond_doji}")
        logger.info(analysis_msg)
        telegram_alert.SendMessage(analysis_msg)
        
        buy_triggered = cond_o1 and cond_o2 and cond_close_inc and cond_high_inc and cond_7ma and cond_50ma and cond_slope and cond_rsi_inc and cond_MACD and cond_doji
        
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