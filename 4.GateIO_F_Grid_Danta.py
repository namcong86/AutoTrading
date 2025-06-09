# -*- coding:utf-8 -*-
'''
파일이름: 4.GateIO_F_Grid_Danta.py
설명: 볼린저밴드와 RSI를 이용한 그리드 매매 전략 (운영용)
'''
import ccxt
import time
import pandas as pd
import json
import logging
import sys
import os
import telegram_alert  # 알림 모듈
from datetime import datetime

# --- 로깅 설정 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('4.GateIO_F_Grid_Danta.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# --- API 설정 (보안을 위해 환경 변수 사용을 권장합니다) ---
GATEIO_ACCESS_KEY = "YOUR_API_KEY"
GATEIO_SECRET_KEY = "YOUR_SECRET_KEY"

# --- ccxt 거래소 객체 생성 ---
exchange = ccxt.gateio({
    'apiKey': GATEIO_ACCESS_KEY,
    'secret': GATEIO_SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'settle': 'usdt'
    }
})

# --- 전역 설정 ---
TIMEFRAME = '5m'       # 사용할 차트의 시간 단위 (5분봉)
LEVERAGE = 10          # 레버리지 
STOP_LOSS_PNL_RATE = -0.5 # 전체 포지션 손절 PNL 비율 (-50%) 
INVEST_COIN_LIST = ['DOGE/USDT:USDT', 'PEPE/USDT:USDT'] # 매매할 코인 목록
JSON_FILE_PATH = "./4.GateIO_F_Grid_Danta_Data.json" # 데이터 관리 파일

# ==============================================================================
# 데이터 관리 모듈 (JSON)
# ==============================================================================
class DataManager:
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self._load_data()

    def _load_data(self):
        """JSON 파일에서 데이터를 로드합니다."""
        try:
            if os.path.exists(self.file_path):
                with open(self.file_path, 'r') as f:
                    return json.load(f)
            return {}
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning(f"{self.file_path} 파일을 찾을 수 없거나 형식이 잘못되었습니다. 새 파일을 생성합니다.")
            return {}

    def _save_data(self):
        """데이터를 JSON 파일에 저장합니다."""
        with open(self.file_path, 'w') as f:
            json.dump(self.data, f, indent=4)

    def get_coin_data(self, ticker):
        """특정 코인의 모든 데이터를 가져옵니다."""
        return self.data.get(ticker, {})

    def initialize_coin_data(self, ticker, total_asset):
        """코인 데이터를 초기화합니다."""
        if ticker not in self.data:
            num_coins = len(INVEST_COIN_LIST)
            allocated_asset = total_asset / num_coins
            base_buy_amount = allocated_asset * 0.01  # 전체 할당 자산의 1% 
            
            self.data[ticker] = {
                "base_buy_amount": base_buy_amount, # 10차 매수까지 기준 금액 
                "current_entry_count": 0,
                "average_price": 0.0,
                "total_quantity": 0.0,
                "final_buy_time": None,
                "entries": [] # { "entry": int, "price": float, "quantity": float, "timestamp": str }
            }
            self._save_data()
            logger.info(f"[{ticker}] 데이터 초기화 완료. 할당 자산: {allocated_asset:.2f} USDT, 1차 기준 매수금: {base_buy_amount:.2f} USDT")

    def add_buy_entry(self, ticker, price, quantity):
        """매수 내역을 추가합니다."""
        coin_data = self.get_coin_data(ticker)
        
        new_count = coin_data['current_entry_count'] + 1
        now_utc = datetime.utcnow().isoformat()

        coin_data['entries'].append({
            "entry": new_count,
            "price": price,
            "quantity": quantity,
            "timestamp": now_utc
        })
        
        coin_data['current_entry_count'] = new_count
        coin_data['final_buy_time'] = now_utc
        
        self.update_position_summary(ticker)
        logger.info(f"[{ticker}] {new_count}차 매수 정보 추가 완료.")

    def process_sell_order(self, ticker, sold_entries_indices):
        """매도 처리 후 데이터를 정리하고 재정렬합니다."""
        coin_data = self.get_coin_data(ticker)
        if not coin_data or not coin_data.get('entries'):
            return

        # 인덱스 기준으로 내림차순 정렬하여 삭제 시 인덱스 꼬임 방지
        sold_entries_indices.sort(reverse=True)
        
        for index in sold_entries_indices:
            del coin_data['entries'][index]

        # 남은 항목들 entry 번호 재정렬 
        for i, entry_info in enumerate(coin_data['entries']):
            entry_info['entry'] = i + 1
        
        coin_data['current_entry_count'] = len(coin_data['entries'])
        
        if coin_data['current_entry_count'] == 0:
            self.reset_position(ticker)
        else:
            self.update_position_summary(ticker)
            
    def update_position_summary(self, ticker):
        """포지션의 평균단가와 총 수량을 업데이트합니다."""
        coin_data = self.get_coin_data(ticker)
        if not coin_data.get('entries'):
            self.reset_position(ticker)
            return

        total_value = sum(e['price'] * e['quantity'] for e in coin_data['entries'])
        total_quantity = sum(e['quantity'] for e in coin_data['entries'])
        
        coin_data['total_quantity'] = total_quantity
        if total_quantity > 0:
            coin_data['average_price'] = total_value / total_quantity
        else:
            coin_data['average_price'] = 0

        self._save_data()

    def reset_position(self, ticker):
        """포지션 전체 종료 후 데이터를 리셋하고 기준 매수금액을 재산정합니다."""
        logger.info(f"[{ticker}] 포지션 전체 종료. 데이터 리셋 및 기준 매수금 재산정 시작.")
        # 기존 데이터 삭제 후 초기화
        del self.data[ticker]
        self._save_data()
        
        try:
            balance = exchange.fetch_balance(params={'settle': 'usdt'})
            total_asset = balance['total']['USDT']
            self.initialize_coin_data(ticker, total_asset) # 기준 매수금 재산정 
        except Exception as e:
            logger.error(f"[{ticker}] 잔고 조회 또는 데이터 재초기화 실패: {e}")


# ==============================================================================
# 보조지표 및 계산 모듈
# ==============================================================================
def get_ohlcv(ticker, timeframe, limit=100):
    """OHLCV 데이터를 가져와 DataFrame으로 반환합니다."""
    try:
        ohlcv = exchange.fetch_ohlcv(ticker, timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        logger.error(f"[{ticker}] OHLCV 데이터 조회 실패: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    """DataFrame에 보조지표를 추가합니다."""
    # 볼린저 밴드 (길이 30) 
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bb_upper'] = df['ma30'] + 2 * df['stddev']
    df['bb_lower'] = df['ma30'] - 2 * df['stddev']
    
    # RSI (길이 14) 
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=13, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df

def get_rsi_level(rsi_value):
    """RSI 값에 따른 레벨을 반환합니다."""
    if 20 < rsi_value <= 25: return 1
    if 15 < rsi_value <= 20: return 2
    if 10 < rsi_value <= 15: return 3
    if rsi_value <= 10: return 4
    return 0 # 매수 불가 레벨

def get_buy_amount(base_amount, rsi_level, entry_count):
    """RSI 레벨과 진입 차수에 따라 최종 매수액(USDT)을 계산합니다."""
    # 1. RSI 레벨에 따른 가산 
    rsi_multiplier = 1.0
    if rsi_level == 2: rsi_multiplier = 1.1
    elif rsi_level == 3: rsi_multiplier = 1.2
    elif rsi_level == 4: rsi_multiplier = 1.3
    
    amount = base_amount * rsi_multiplier
    
    # 2. 진입 차수에 따른 가산 
    entry_multiplier = 1.0
    if 4 <= entry_count <= 6: entry_multiplier = 1.2
    elif 7 <= entry_count <= 10: entry_multiplier = 1.3
    
    final_amount_usd = amount * entry_multiplier
    return final_amount_usd

# ==============================================================================
# 알림 모듈
# ==============================================================================
def send_notification(message):
    """텔레그램으로 알림을 보냅니다."""
    logger.info(message) # 로그에도 동일 내용 출력
    try:
        telegram_alert.SendMessage(message)
    except Exception as e:
        logger.error(f"텔레그램 알림 발송 실패: {e}")

# ==============================================================================
# 메인 로직
# ==============================================================================
def trading_bot_logic():
    data_manager = DataManager(JSON_FILE_PATH)
    
    try:
        balance = exchange.fetch_balance(params={'settle': 'usdt'})
        total_asset = balance['total']['USDT']
    except Exception as e:
        logger.error(f"잔고 조회 실패. 봇을 종료합니다: {e}")
        return

    for ticker in INVEST_COIN_LIST:
        logger.info(f"\n===== {ticker} 처리 시작 =====")
        
        # 1. 코인 데이터 초기화 (없는 경우)
        if ticker not in data_manager.data:
            data_manager.initialize_coin_data(ticker, total_asset)

        coin_data = data_manager.get_coin_data(ticker)
        current_entry_count = coin_data.get('current_entry_count', 0)
        
        # 2. 포지션 정보 조회 및 손절 로직
        position = None
        try:
            positions = exchange.fetch_positions(symbols=[ticker])
            position = next((p for p in positions if p.get('contracts') is not None and abs(p['contracts']) > 0), None)
        except Exception as e:
            logger.error(f"[{ticker}] 포지션 정보 조회 실패: {e}")
            continue

        if position:
            unrealized_pnl = float(position.get('unrealizedPnl', 0))
            entry_price = float(position.get('entryPrice', 0))
            collateral = float(position.get('collateral', 0))

            if collateral > 0 and (unrealized_pnl / collateral) <= STOP_LOSS_PNL_RATE:
                try:
                    # 시장가로 포지션 전체 종료
                    params = {'reduceOnly': True}
                    exchange.create_market_sell_order(ticker, abs(float(position['contracts'])), params)
                    
                    pnl_info = f"미실현 손익: {unrealized_pnl:.2f} USDT, 증거금: {collateral:.2f} USDT"
                    msg = f"🚨 [{ticker}] 손절매 실행 (-50% PNL): 포지션 전체 종료. {pnl_info}"
                    send_notification(msg)
                    
                    data_manager.reset_position(ticker) # 데이터 리셋
                except Exception as e:
                    send_notification(f"🚨 [{ticker}] 손절매 주문 실패: {e}")
                continue # 다음 코인으로

        # 3. 데이터 및 지표 계산
        df = get_ohlcv(ticker, TIMEFRAME, limit=100)
        if df.empty or len(df) < 30:
            logger.warning(f"[{ticker}] 지표 계산을 위한 데이터가 부족합니다. (데이터 수: {len(df)})")
            continue
        
        df = calculate_indicators(df)
        prev_candle = df.iloc[-2] # 전 캔들 기준
        now_price = df['close'].iloc[-1]

        # 4. 매도 조건 확인
        if current_entry_count > 0:
            # 조건 1: 30 이평선 상향 돌파 시 부분 익절 
            if prev_candle['open'] < prev_candle['ma30'] and prev_candle['close'] > prev_candle['ma30']:
                entries_to_sell = [(i, e) for i, e in enumerate(coin_data['entries']) if e['price'] < prev_candle['ma30']]
                
                if entries_to_sell:
                    total_sell_qty = sum(e['quantity'] for i, e in entries_to_sell)
                    try:
                        params = {'reduceOnly': True}
                        exchange.create_market_sell_order(ticker, total_sell_qty, params)
                        
                        sold_indices = [i for i, e in entries_to_sell]
                        sold_entry_nums = [e['entry'] for i, e in entries_to_sell]
                        
                        msg = f"💰 [{ticker}] 부분 익절 (30MA 상향돌파): {sold_entry_nums}차 매도 완료. 수량: {total_sell_qty:.4f}"
                        send_notification(msg)
                        
                        data_manager.process_sell_order(ticker, sold_indices)
                    except Exception as e:
                        send_notification(f"🚨 [{ticker}] 부분 익절 주문 실패: {e}")

            # 조건 2: 볼린저밴드 상단 돌파 
            elif prev_candle['close'] > prev_candle['bb_upper']:
                avg_price = coin_data['average_price']
                
                # 전체 익절 조건
                if now_price > avg_price:
                    try:
                        params = {'reduceOnly': True}
                        exchange.create_market_sell_order(ticker, coin_data['total_quantity'], params)
                        
                        msg = f"💰 [{ticker}] 전체 익절 (BB 상단 돌파): 포지션 전체 종료. 수량: {coin_data['total_quantity']:.4f}"
                        send_notification(msg)
                        
                        data_manager.reset_position(ticker)
                    except Exception as e:
                        send_notification(f"🚨 [{ticker}] 전체 익절 주문 실패: {e}")
                
                # 부분 익절 조건 (전체는 손해지만 개별적으로 익절 가능한 경우)
                else:
                    entries_to_sell = [(i, e) for i, e in enumerate(coin_data['entries']) if now_price > e['price']]
                    if entries_to_sell:
                        total_sell_qty = sum(e['quantity'] for i, e in entries_to_sell)
                        try:
                            params = {'reduceOnly': True}
                            exchange.create_market_sell_order(ticker, total_sell_qty, params)
                            
                            sold_indices = [i for i, e in entries_to_sell]
                            sold_entry_nums = [e['entry'] for i, e in entries_to_sell]
                            
                            msg = f"💰 [{ticker}] 부분 익절 (BB 상단 돌파 - 개별): {sold_entry_nums}차 매도 완료. 수량: {total_sell_qty:.4f}"
                            send_notification(msg)
                            
                            data_manager.process_sell_order(ticker, sold_indices)
                        except Exception as e:
                            send_notification(f"🚨 [{ticker}] BB상단 부분 익절 주문 실패: {e}")
            continue # 매도 로직 실행 후에는 매수 로직 건너뛰기

        # 5. 매수 조건 확인
        if current_entry_count >= 10:
            logger.info(f"[{ticker}] 최대 매수 횟수(10회)에 도달하여 추가 매수를 진행하지 않습니다.")
            continue
            
        prev_rsi = prev_candle['rsi']
        prev_close = prev_candle['close']
        prev_bb_lower = prev_candle['bb_lower']
        
        # 조건: RSI 25 미만 & 종가가 볼밴 하단보다 낮음
        base_buy_condition = prev_rsi < 25 and prev_close < prev_bb_lower
        
        should_buy = False
        if base_buy_condition:
            # 1차 매수 조건 
            if current_entry_count == 0:
                should_buy = True
            
            # 2차 이상 매수 조건 
            else:
                # [1] RSI 리셋 확인
                last_buy_time_str = coin_data.get('final_buy_time')
                if last_buy_time_str:
                    last_buy_time = datetime.fromisoformat(last_buy_time_str.replace('Z', '+00:00'))
                    # 마지막 매수 이후 캔들 데이터 조회
                    candles_after_buy = df[df['timestamp'] > last_buy_time]
                    if not candles_after_buy.empty and (candles_after_buy['rsi'] > 25).any():
                        logger.info(f"[{ticker}] RSI 리셋 확인 (25 이상 상승 후 하락). 매수 조건 충족.")
                        should_buy = True
                
                # [2] RSI 레벨 상승 확인
                if not should_buy:
                    last_entry_rsi_level = get_rsi_level(df[df['timestamp'] == last_buy_time]['rsi'].iloc[0])
                    current_rsi_level = get_rsi_level(prev_rsi)
                    if current_rsi_level > last_entry_rsi_level:
                        logger.info(f"[{ticker}] RSI 레벨 상승 확인 ({last_entry_rsi_level} -> {current_rsi_level}). 매수 조건 충족.")
                        should_buy = True

        if should_buy:
            try:
                # 레버리지 설정 (Cross) 
                exchange.set_leverage(LEVERAGE, ticker, params={'marginMode': 'cross'})

                # 매수 금액 계산
                rsi_level = get_rsi_level(prev_rsi)
                buy_amount_usd = get_buy_amount(
                    base_amount=coin_data['base_buy_amount'],
                    rsi_level=rsi_level,
                    entry_count=current_entry_count + 1
                )
                
                # 레버리지를 적용한 포지션 가치
                position_value = buy_amount_usd * LEVERAGE
                # 실제 주문할 코인 수량 계산
                amount_to_buy = position_value / now_price

                # 시장가 매수 주문
                order = exchange.create_market_buy_order(ticker, amount_to_buy)

                # 데이터 업데이트
                actual_price = float(order['price'])
                actual_quantity = float(order['amount'])
                data_manager.add_buy_entry(ticker, actual_price, actual_quantity)
                
                msg = (f"📈 [{ticker}] 신규 매수 ({current_entry_count + 1}차)\n"
                       f" - 가격: {actual_price:.4f} USDT\n"
                       f" - 수량: {actual_quantity:.4f} {ticker.split('/')[0]}\n"
                       f" - 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                       f" - 사유: RSI {prev_rsi:.2f}, BB하단 터치")
                send_notification(msg)

            except Exception as e:
                send_notification(f"🚨 [{ticker}] 매수 주문 또는 처리 실패: {e}")

if __name__ == '__main__':
    while True:
        try:
            logger.info("===== 자동매매 봇 실행 =====")
            trading_bot_logic()
            logger.info("===== 사이클 종료, 60초 후 재시작 =====")
            time.sleep(60)
        except Exception as e:
            send_notification(f"FATAL: 봇의 메인 루프에서 에러 발생: {e}")
            time.sleep(60)