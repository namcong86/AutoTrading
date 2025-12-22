# -*- coding:utf-8 -*-
'''
파일이름: 4-2.GateIO_F_Grid_Danta_Test.py
설명: RSI 기반 롱숏 분할매매 전략 백테스트
      - 일봉 이평선(120/20) 기준 3영역(LONG/MIDDLE/SHORT) 구분
      - RSI(14) 기반 진입 (25 이하 롱, 75 이상 숏)
      - 분할 익절 (5/10/20/30/50%)
      - 영역 변화에 따른 청산
'''
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os
import json
from enum import Enum

# ==============================================================================
# 한글 폰트 설정 (Windows)
# ==============================================================================
import matplotlib.font_manager as fm

def set_korean_font():
    font_list = ['Malgun Gothic', 'NanumGothic', 'NanumBarunGothic', 'Gulim', 'Dotum']
    for font_name in font_list:
        try:
            font_path = fm.findfont(fm.FontProperties(family=font_name))
            if font_path and 'ttf' in font_path.lower():
                plt.rcParams['font.family'] = font_name
                plt.rcParams['axes.unicode_minus'] = False
                print(f"[폰트] {font_name} 사용")
                return True
        except:
            continue
    plt.rcParams['axes.unicode_minus'] = False
    return False

set_korean_font()

# ==============================================================================
# 1. 백테스트 환경 설정
# ==============================================================================
COIN_EXCHANGE = "gateio"
TEST_START_DATE = datetime.datetime(2021, 4, 1)
TEST_END_DATE = datetime.datetime.now()
INITIAL_CAPITAL = 10000
TIMEFRAME = '15m'                      # 1시간봉
LEVERAGE = 7
FEE_RATE = 0.0006                     # 거래 수수료 (0.06%)

# 코인 리스트
COIN_LIST = ['ETH/USDT','DOGE/USDT','ADA/USDT','XRP/USDT','TRX/USDT']
#COIN_LIST = ['ETH/USDT']

# RSI 설정
RSI_LENGTH = 14
RSI_LONG_ENTRY = 25                   # 롱 진입 RSI
RSI_SHORT_ENTRY = 75                  # 숏 진입 RSI
RSI_LONG_RESET = 30                   # 롱 리셋 RSI (이 값 위로 갔다가 다시 25 아래로)
RSI_SHORT_RESET = 70                  # 숏 리셋 RSI (이 값 아래로 갔다가 다시 75 위로)

# 일봉 이평선 설정 (영역 구분용)
DAILY_MA_LONG = 120                   # 장기 이평선
DAILY_MA_SHORT = 30                   # 단기 이평선

# 분할 진입 설정
MAX_ENTRY_COUNT = 10                  # 최대 진입 회차

# 중립구간 50% 투자 옵션
HALF_INVEST_IN_MIDDLE = True          # True: 중립구간에서 50% 투자

# 익절 설정 (레버리지 미적용 수익률 기준)
TAKE_PROFIT_ENABLED = True
TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 10},
    {'profit_pct': 10, 'sell_pct': 20},
    {'profit_pct': 20, 'sell_pct': 30},
    {'profit_pct': 30, 'sell_pct': 50},
    {'profit_pct': 50, 'sell_pct': 70},
]

# 연간 출금 설정
ANNUAL_WITHDRAWAL_ENABLED = True
ANNUAL_WITHDRAWAL_RATE = 0.20
ANNUAL_WITHDRAWAL_MONTHS = [1]

# JSON 데이터 경로
DATA_PATH = r'C:\AutoTrading\Coin\json'

# ==============================================================================
# 2. 영역 타입 정의
# ==============================================================================
class ZoneType(Enum):
    LONG = 'LONG'       # 두 이평선 위
    MIDDLE = 'MIDDLE'   # 두 이평선 사이
    SHORT = 'SHORT'     # 두 이평선 아래

# ==============================================================================
# 3. 포지션 관리 클래스
# ==============================================================================
class PositionManager:
    """코인별 포지션 및 영역 상태 관리"""
    
    def __init__(self, symbol, n_coins):
        self.symbol = symbol
        self.n_coins = n_coins
        
        # 롱 포지션 상태
        self.long_entry_count = 0
        self.long_avg_price = 0.0
        self.long_quantity = 0.0
        self.long_collateral = 0.0
        self.long_start_zone = None       # 롱 포지션 시작 영역
        self.long_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        self.long_rsi_reset = True        # RSI 리셋 여부 (진입 가능 상태)
        self.long_visited_zone = None     # MIDDLE 시작 시 방문한 영역 추적
        
        # 숏 포지션 상태
        self.short_entry_count = 0
        self.short_avg_price = 0.0
        self.short_quantity = 0.0
        self.short_collateral = 0.0
        self.short_start_zone = None
        self.short_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        self.short_rsi_reset = True
        self.short_visited_zone = None
    
    def has_long_position(self):
        return self.long_entry_count > 0
    
    def has_short_position(self):
        return self.short_entry_count > 0
    
    def get_long_unrealized_pnl(self, current_price):
        """롱 미실현 손익 (레버리지 미적용 수익률 기준)"""
        if self.long_quantity == 0:
            return 0.0
        return (current_price - self.long_avg_price) * self.long_quantity
    
    def get_short_unrealized_pnl(self, current_price):
        """숏 미실현 손익"""
        if self.short_quantity == 0:
            return 0.0
        return (self.short_avg_price - current_price) * self.short_quantity
    
    def get_long_profit_pct(self, current_price):
        """롱 수익률 (레버리지 미적용)"""
        if self.long_avg_price == 0:
            return 0.0
        return (current_price - self.long_avg_price) / self.long_avg_price * 100
    
    def get_short_profit_pct(self, current_price):
        """숏 수익률 (레버리지 미적용)"""
        if self.short_avg_price == 0:
            return 0.0
        return (self.short_avg_price - current_price) / self.short_avg_price * 100

# ==============================================================================
# 4. 자금 관리 클래스
# ==============================================================================
class FundManager:
    """통합 자금 관리"""
    
    def __init__(self, initial_capital, coin_list):
        self.available_balance = initial_capital
        self.initial_capital = initial_capital
        self.coin_list = coin_list
        self.n_coins = len(coin_list)
        
        # 포지션 매니저 (코인별)
        self.positions = {symbol: PositionManager(symbol, self.n_coins) for symbol in coin_list}
        
        # 거래 기록
        self.trades = []
        self.daily_balance = []
        
        # 출금 기록
        self.withdrawal_history = []
        self.total_withdrawn = 0
        self.last_year_balance = initial_capital
        self.last_withdrawal_date = None
    
    def get_total_equity(self, current_prices):
        """현재 총 자산가치"""
        total = self.available_balance
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                price = current_prices[symbol]
                total += pos.long_collateral + pos.get_long_unrealized_pnl(price)
                total += pos.short_collateral + pos.get_short_unrealized_pnl(price)
        return total
    
    def calculate_entry_amount(self, current_prices, is_middle_zone=False):
        """진입 금액 계산 (총자산 / 코인수 / 최대회차)"""
        equity = self.get_total_equity(current_prices)
        base_amount = equity / self.n_coins / MAX_ENTRY_COUNT
        
        if is_middle_zone and HALF_INVEST_IN_MIDDLE:
            base_amount *= 0.5
        
        return base_amount
    
    def open_long(self, symbol, price, timestamp, current_prices, zone, leverage, rsi=None):
        """롱 포지션 진입"""
        pos = self.positions[symbol]
        is_middle = (zone == ZoneType.MIDDLE)
        
        collateral = self.calculate_entry_amount(current_prices, is_middle)
        position_size = collateral * leverage
        quantity = position_size / price
        fee = position_size * FEE_RATE
        
        if self.available_balance < collateral + fee:
            return False
        
        self.available_balance -= (collateral + fee)
        
        # 평단가 업데이트
        total_value = pos.long_avg_price * pos.long_quantity + price * quantity
        pos.long_quantity += quantity
        pos.long_avg_price = total_value / pos.long_quantity if pos.long_quantity > 0 else 0
        pos.long_collateral += collateral
        pos.long_entry_count += 1
        pos.long_rsi_reset = False
        
        # 첫 진입 시 시작 영역 기록
        if pos.long_entry_count == 1:
            pos.long_start_zone = zone
            pos.long_visited_zone = None
        
        # 매 진입마다 TP 리셋 (새 평단가 기준으로 TP1부터 다시)
        pos.long_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        
        zone_info = " [중립구간 50%]" if is_middle and HALF_INVEST_IN_MIDDLE else ""
        rsi_info = f", RSI {rsi:.2f}" if rsi is not None else ""
        print(f"[{timestamp}] 📈 {symbol} 롱 진입 ({pos.long_entry_count}차){zone_info}: "
              f"가격 ${price:.6f}, 수량 {quantity:.4f}, 금액 ${collateral:.2f}, 영역 {zone.value}{rsi_info}, "
              f"평단가 ${pos.long_avg_price:.6f}, 총수량 {pos.long_quantity:.4f}")
        
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'long',
            'action': 'entry', 'price': price, 'quantity': quantity,
            'collateral': collateral, 'entry_count': pos.long_entry_count,
            'zone': zone.value, 'fee': fee
        })
        
        return True
    
    def open_short(self, symbol, price, timestamp, current_prices, zone, leverage, rsi=None):
        """숏 포지션 진입"""
        pos = self.positions[symbol]
        is_middle = (zone == ZoneType.MIDDLE)
        
        collateral = self.calculate_entry_amount(current_prices, is_middle)
        position_size = collateral * leverage
        quantity = position_size / price
        fee = position_size * FEE_RATE
        
        if self.available_balance < collateral + fee:
            return False
        
        self.available_balance -= (collateral + fee)
        
        # 평단가 업데이트
        total_value = pos.short_avg_price * pos.short_quantity + price * quantity
        pos.short_quantity += quantity
        pos.short_avg_price = total_value / pos.short_quantity if pos.short_quantity > 0 else 0
        pos.short_collateral += collateral
        pos.short_entry_count += 1
        pos.short_rsi_reset = False
        
        # 첫 진입 시 시작 영역 기록
        if pos.short_entry_count == 1:
            pos.short_start_zone = zone
            pos.short_visited_zone = None
        
        # 매 진입마다 TP 리셋 (새 평단가 기준으로 TP1부터 다시)
        pos.short_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        
        zone_info = " [중립구간 50%]" if is_middle and HALF_INVEST_IN_MIDDLE else ""
        rsi_info = f", RSI {rsi:.2f}" if rsi is not None else ""
        print(f"[{timestamp}] 📉 {symbol} 숏 진입 ({pos.short_entry_count}차){zone_info}: "
              f"가격 ${price:.6f}, 수량 {quantity:.4f}, 금액 ${collateral:.2f}, 영역 {zone.value}{rsi_info}, "
              f"평단가 ${pos.short_avg_price:.6f}, 총수량 {pos.short_quantity:.4f}")
        
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'short',
            'action': 'entry', 'price': price, 'quantity': quantity,
            'collateral': collateral, 'entry_count': pos.short_entry_count,
            'zone': zone.value, 'fee': fee
        })
        
        return True
    
    def close_long(self, symbol, price, timestamp, leverage, reason=""):
        """롱 포지션 전체 청산"""
        pos = self.positions[symbol]
        if pos.long_quantity == 0:
            return 0
        
        pnl_rate = (price - pos.long_avg_price) / pos.long_avg_price * leverage
        pnl = pos.long_collateral * pnl_rate
        fee = pos.long_quantity * price * FEE_RATE
        
        self.available_balance += pos.long_collateral + pnl - fee
        
        print(f"[{timestamp}] 💰 {symbol} 롱 전체청산 ({reason}): "
              f"청산가 ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, 수익금 ${pnl:+.2f}, 가용잔액 ${self.available_balance:.2f}")
        
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'long',
            'action': 'close', 'price': price, 'quantity': pos.long_quantity,
            'pnl': pnl, 'pnl_rate': pnl_rate * 100, 'reason': reason, 'fee': fee
        })
        
        # 포지션 초기화
        pos.long_entry_count = 0
        pos.long_avg_price = 0.0
        pos.long_quantity = 0.0
        pos.long_collateral = 0.0
        pos.long_start_zone = None
        pos.long_visited_zone = None
        pos.long_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        pos.long_rsi_reset = True
        
        return pnl
    
    def close_short(self, symbol, price, timestamp, leverage, reason=""):
        """숏 포지션 전체 청산"""
        pos = self.positions[symbol]
        if pos.short_quantity == 0:
            return 0
        
        pnl_rate = (pos.short_avg_price - price) / pos.short_avg_price * leverage
        pnl = pos.short_collateral * pnl_rate
        fee = pos.short_quantity * price * FEE_RATE
        
        self.available_balance += pos.short_collateral + pnl - fee
        
        print(f"[{timestamp}] 💰 {symbol} 숏 전체청산 ({reason}): "
              f"청산가 ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, 수익금 ${pnl:+.2f}, 가용잔액 ${self.available_balance:.2f}")
        
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'short',
            'action': 'close', 'price': price, 'quantity': pos.short_quantity,
            'pnl': pnl, 'pnl_rate': pnl_rate * 100, 'reason': reason, 'fee': fee
        })
        
        # 포지션 초기화
        pos.short_entry_count = 0
        pos.short_avg_price = 0.0
        pos.short_quantity = 0.0
        pos.short_collateral = 0.0
        pos.short_start_zone = None
        pos.short_visited_zone = None
        pos.short_tp_triggered = [False] * len(TAKE_PROFIT_LEVELS)
        pos.short_rsi_reset = True
        
        return pnl
    
    def partial_close_long(self, symbol, price, timestamp, leverage, sell_pct, tp_level):
        """롱 부분 익절"""
        pos = self.positions[symbol]
        if pos.long_quantity == 0:
            return 0
        
        close_qty = pos.long_quantity * (sell_pct / 100)
        close_collateral = pos.long_collateral * (sell_pct / 100)
        
        pnl_rate = (price - pos.long_avg_price) / pos.long_avg_price * leverage
        pnl = close_collateral * pnl_rate
        fee = close_qty * price * FEE_RATE
        
        self.available_balance += close_collateral + pnl - fee
        
        pos.long_quantity -= close_qty
        pos.long_collateral -= close_collateral
        pos.long_tp_triggered[tp_level] = True
        
        print(f"[{timestamp}] 💰 {symbol} 롱 익절 TP{tp_level+1} ({sell_pct}%): "
              f"가격 ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, 수익금 ${pnl:+.2f}")
        
        # 거래 기록 추가
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'long',
            'action': 'partial_close', 'price': price, 'quantity': close_qty,
            'pnl': pnl, 'pnl_rate': pnl_rate * 100, 'reason': f'TP{tp_level+1}', 'fee': fee
        })
        
        return pnl
    
    def partial_close_short(self, symbol, price, timestamp, leverage, sell_pct, tp_level):
        """숏 부분 익절"""
        pos = self.positions[symbol]
        if pos.short_quantity == 0:
            return 0
        
        close_qty = pos.short_quantity * (sell_pct / 100)
        close_collateral = pos.short_collateral * (sell_pct / 100)
        
        pnl_rate = (pos.short_avg_price - price) / pos.short_avg_price * leverage
        pnl = close_collateral * pnl_rate
        fee = close_qty * price * FEE_RATE
        
        self.available_balance += close_collateral + pnl - fee
        
        pos.short_quantity -= close_qty
        pos.short_collateral -= close_collateral
        pos.short_tp_triggered[tp_level] = True
        
        print(f"[{timestamp}] 💰 {symbol} 숏 익절 TP{tp_level+1} ({sell_pct}%): "
              f"가격 ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, 수익금 ${pnl:+.2f}")
        
        # 거래 기록 추가
        self.trades.append({
            'timestamp': timestamp, 'symbol': symbol, 'direction': 'short',
            'action': 'partial_close', 'price': price, 'quantity': close_qty,
            'pnl': pnl, 'pnl_rate': pnl_rate * 100, 'reason': f'TP{tp_level+1}', 'fee': fee
        })
        
        return pnl
    
    def check_take_profit(self, symbol, price, timestamp, leverage):
        """익절 조건 체크"""
        if not TAKE_PROFIT_ENABLED:
            return
        
        pos = self.positions[symbol]
        
        # 롱 익절 체크
        if pos.has_long_position():
            profit_pct = pos.get_long_profit_pct(price)
            for i, tp in enumerate(TAKE_PROFIT_LEVELS):
                if not pos.long_tp_triggered[i] and profit_pct >= tp['profit_pct']:
                    self.partial_close_long(symbol, price, timestamp, leverage, tp['sell_pct'], i)
        
        # 숏 익절 체크
        if pos.has_short_position():
            profit_pct = pos.get_short_profit_pct(price)
            for i, tp in enumerate(TAKE_PROFIT_LEVELS):
                if not pos.short_tp_triggered[i] and profit_pct >= tp['profit_pct']:
                    self.partial_close_short(symbol, price, timestamp, leverage, tp['sell_pct'], i)
    
    def check_annual_withdrawal(self, timestamp, current_prices):
        """연간 출금 체크"""
        if not ANNUAL_WITHDRAWAL_ENABLED:
            return
        
        current_date = timestamp.date() if hasattr(timestamp, 'date') else timestamp
        
        if current_date.day != 1 or current_date.month not in ANNUAL_WITHDRAWAL_MONTHS:
            return
        
        if self.last_withdrawal_date == current_date:
            return
        
        current_equity = self.get_total_equity(current_prices)
        year_profit = current_equity - self.last_year_balance
        
        if year_profit > 0:
            withdrawal = year_profit * ANNUAL_WITHDRAWAL_RATE
            if withdrawal <= self.available_balance:
                self.available_balance -= withdrawal
                self.total_withdrawn += withdrawal
                self.withdrawal_history.append({
                    'date': str(current_date),
                    'amount': withdrawal,
                    'total': self.total_withdrawn
                })
                print(f"\n[출금] {current_date}: 연간 수익 ${year_profit:,.2f}의 {ANNUAL_WITHDRAWAL_RATE*100:.0f}% = ${withdrawal:,.2f} 출금\n")
        
        self.last_year_balance = self.get_total_equity(current_prices)
        self.last_withdrawal_date = current_date
    
    def record_daily_balance(self, timestamp, current_prices):
        """일별 잔액 기록"""
        equity = self.get_total_equity(current_prices)
        self.daily_balance.append({
            'date': timestamp,
            'balance': equity
        })
    
    def get_results(self):
        """결과 반환"""
        return {
            'initial_capital': self.initial_capital,
            'final_balance': self.available_balance,
            'total_withdrawn': self.total_withdrawn,
            'trades': self.trades,
            'daily_balance': pd.DataFrame(self.daily_balance),
            'withdrawal_history': self.withdrawal_history
        }

# ==============================================================================
# 5. 헬퍼 함수들
# ==============================================================================
def get_zone(prev_close, ma_short, ma_long):
    """직전 일봉 종가 기준으로 영역 판단"""
    if pd.isna(ma_short) or pd.isna(ma_long):
        return ZoneType.MIDDLE  # 데이터 부족 시 중립
    
    upper_ma = max(ma_short, ma_long)
    lower_ma = min(ma_short, ma_long)
    
    if prev_close > upper_ma:
        return ZoneType.LONG
    elif prev_close < lower_ma:
        return ZoneType.SHORT
    else:
        return ZoneType.MIDDLE

def get_allowed_directions(zone):
    """영역별 진입 가능한 방향 반환"""
    if zone == ZoneType.LONG:
        return ['long']
    elif zone == ZoneType.SHORT:
        return ['short']
    else:  # MIDDLE
        return ['long', 'short']

def should_close_by_zone_change(pos, direction, current_zone):
    """영역 변화에 따른 청산 여부 판단
    
    규칙:
    - LONG영역 시작 롱: MIDDLE 진입 시 청산
    - SHORT영역 시작 숏: MIDDLE 진입 시 청산
    - MIDDLE 시작 롱: SHORT 진입 시 즉시 청산, LONG 갔다가 MIDDLE 복귀 시 청산
    - MIDDLE 시작 숏: LONG 진입 시 즉시 청산, SHORT 갔다가 MIDDLE 복귀 시 청산
    """
    if direction == 'long':
        start_zone = pos.long_start_zone
        visited = pos.long_visited_zone
        
        if start_zone is None:
            return False
        
        if start_zone == ZoneType.LONG:
            # LONG에서 시작 → MIDDLE 가면 청산
            return current_zone == ZoneType.MIDDLE
        elif start_zone == ZoneType.MIDDLE:
            # MIDDLE에서 시작한 롱
            if current_zone == ZoneType.SHORT:
                return True  # SHORT 영역 직접 진입 시 즉시 청산
            if visited == ZoneType.LONG and current_zone == ZoneType.MIDDLE:
                return True  # LONG 갔다가 MIDDLE 복귀 시 청산
    else:  # short
        start_zone = pos.short_start_zone
        visited = pos.short_visited_zone
        
        if start_zone is None:
            return False
        
        if start_zone == ZoneType.SHORT:
            # SHORT에서 시작 → MIDDLE 가면 청산
            return current_zone == ZoneType.MIDDLE
        elif start_zone == ZoneType.MIDDLE:
            # MIDDLE에서 시작한 숏
            if current_zone == ZoneType.LONG:
                return True  # LONG 영역 직접 진입 시 즉시 청산
            if visited == ZoneType.SHORT and current_zone == ZoneType.MIDDLE:
                return True  # SHORT 갔다가 MIDDLE 복귀 시 청산
    
    return False

def calculate_rsi(df, period=14):
    """RSI 계산"""
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=period-1, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(com=period-1, adjust=False).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# ==============================================================================
# 6. 데이터 로딩
# ==============================================================================
def load_data(symbol, timeframe, start_date, end_date):
    """JSON 파일에서 데이터 로드"""
    safe_name = symbol.replace('/', '_').replace(':', '_').lower()
    coin_name = safe_name.split('_')[0]
    
    json_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_{COIN_EXCHANGE}_{timeframe}.json")
    
    print(f"[{symbol}] 데이터 로드 중: {json_file}")
    
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            # 중복 인덱스 제거
            df = df[~df.index.duplicated(keep='last')]
        except Exception as e:
            print(f"  파일 로드 오류: {e}")
            return pd.DataFrame()
    else:
        # ... (API 다운로드 로직 생략 - 기존과 동일하게 유지하거나 필요시 추가)
        return pd.DataFrame()
    
    # 기간 필터링
    df = df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]
    
    if df.empty:
        return df
        
    # RSI 계산
    df['rsi'] = calculate_rsi(df, RSI_LENGTH)
    
    print(f"  로드 완료: {len(df)}개 캔들")
    return df

# ... (중략) ...

def run_backtest():
    # ... (중략) ...
    
    # 백테스트 루프
    processed = 0
    for current_time in common_index:
        processed += 1
        if processed % 10000 == 0:
            print(f"  처리 중... {processed}/{len(common_index)} ({processed*100//len(common_index)}%)")
        
        # 현재가 수집 (중복 데이터 방지)
        current_prices = {}
        for symbol in data_frames:
            try:
                price_data = data_frames[symbol].loc[current_time]['close']
                # Series로 반환되는 경우 (중복 인덱스) 첫 번째 값 사용
                if isinstance(price_data, pd.Series):
                    price_data = price_data.iloc[0]
                current_prices[symbol] = float(price_data)
            except Exception:
                current_prices[symbol] = 0.0

        # ... (중략) ...
        
        # 일별 잔액 기록
        fund_mgr.record_daily_balance(current_time, current_prices)
    
    # ... (중략) ...

# ==============================================================================
# 8. 결과 분석 및 시각화
# ==============================================================================
def analyze_results(results):
    # ... (중략 - MDD 계산 부분 등) ...
    
    # 그래프 그리기
    if not daily_df.empty and 'balance' in daily_df.columns:
        try:
            fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
            
            # 데이터 추출 및 타입을 강제로 float으로 변환
            dates = daily_df.index.to_numpy()
            
            # balance가 object 타입 등으로 오염되었을 가능성 처리
            balance_vals = pd.to_numeric(daily_df['balance'], errors='coerce').fillna(0).to_numpy()
            
            if 'drawdown' in daily_df.columns:
                drawdown_vals = pd.to_numeric(daily_df['drawdown'], errors='coerce').fillna(0).to_numpy()
            else:
                drawdown_vals = np.zeros(len(balance_vals))
            
            # 잔액 추이
            axes[0].plot(dates, balance_vals, label='잔액', color='blue')
            axes[0].axhline(y=initial_capital, color='gray', linestyle='--', label='초기자본')
            axes[0].set_title('RSI 롱숏 분할매매 전략 - 잔액 추이')
            axes[0].set_ylabel('USDT')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # 드로다운
            axes[1].fill_between(dates, drawdown_vals, 0, color='red', alpha=0.3)
            axes[1].set_title('드로다운')
            axes[1].set_ylabel('%')
            axes[1].set_xlabel('날짜')
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"그래프 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            
    return results

def load_daily_data(symbol):
    """일봉 데이터 로드"""
    safe_name = symbol.replace('/', '_').replace(':', '_').lower()
    coin_name = safe_name.split('_')[0]
    
    json_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_{COIN_EXCHANGE}_1d.json")
    
    if not os.path.exists(json_file):
        # gateio 없으면 bitget 시도
        json_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_bitget_1d.json")
    
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # 이평선 계산
        df['ma_short'] = df['close'].rolling(window=DAILY_MA_SHORT).mean()
        df['ma_long'] = df['close'].rolling(window=DAILY_MA_LONG).mean()
        
        return df
    else:
        print(f"  경고: 일봉 데이터 없음 - {symbol}")
        return None

# ==============================================================================
# 7. 백테스트 실행
# ==============================================================================
def validate_data_availability(coin_list, start_date, timeframe):
    """
    백테스트 시작 전 각 코인의 데이터 가용성 검증
    
    Returns:
        (bool, list): (검증 통과 여부, 에러 메시지 리스트)
    """
    errors = []
    required_daily_candles = max(DAILY_MA_SHORT, DAILY_MA_LONG) + 10  # 이평선 계산에 필요한 일봉 수 + 여유분
    
    for symbol in coin_list:
        safe_name = symbol.replace('/', '_').replace(':', '_').lower()
        coin_name = safe_name.split('_')[0]
        
        # 1시간봉 데이터 확인
        hourly_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_{COIN_EXCHANGE}_{timeframe}.json")
        if not os.path.exists(hourly_file):
            errors.append(f"❌ [{symbol}] {timeframe} 캔들 파일 없음: {hourly_file}")
            continue
        
        try:
            with open(hourly_file, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            
            first_date = df['datetime'].min()
            last_date = df['datetime'].max()
            
            if first_date > start_date:
                errors.append(f"❌ [{symbol}] {timeframe} 데이터 시작일({first_date.date()})이 테스트 시작일({start_date.date()})보다 늦음")
        except Exception as e:
            errors.append(f"❌ [{symbol}] {timeframe} 파일 읽기 오류: {e}")
            continue
        
        # 일봉 데이터 확인
        daily_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_{COIN_EXCHANGE}_1d.json")
        if not os.path.exists(daily_file):
            # gateio 없으면 bitget 확인
            daily_file = os.path.join(DATA_PATH, f"{coin_name}_usdt_bitget_1d.json")
        
        if not os.path.exists(daily_file):
            errors.append(f"❌ [{symbol}] 일봉(1d) 캔들 파일 없음")
            continue
        
        try:
            with open(daily_file, 'r') as f:
                daily_data = json.load(f)
            daily_df = pd.DataFrame(daily_data)
            daily_df['datetime'] = pd.to_datetime(daily_df['datetime'])
            
            first_daily = daily_df['datetime'].min()
            
            # 테스트 시작일 기준으로 이평선 계산에 필요한 일수가 있는지 확인
            required_start = start_date - datetime.timedelta(days=required_daily_candles)
            if first_daily > required_start:
                errors.append(f"❌ [{symbol}] 일봉 데이터 부족: 이평선({DAILY_MA_LONG}일) 계산을 위해 {required_start.date()}부터 필요하나, 데이터는 {first_daily.date()}부터 시작")
        except Exception as e:
            errors.append(f"❌ [{symbol}] 일봉 파일 읽기 오류: {e}")
    
    if errors:
        return False, errors
    return True, []

def run_backtest():
    """백테스트 실행"""
    print("\n" + "="*70)
    print("RSI 롱숏 분할매매 전략 백테스트")
    print("="*70)
    print(f"테스트 기간: {TEST_START_DATE.date()} ~ {TEST_END_DATE.date()}")
    print(f"초기 자본: ${INITIAL_CAPITAL:,}")
    print(f"레버리지: {LEVERAGE}x")
    print(f"코인: {COIN_LIST}")
    print(f"RSI 설정: 롱 진입 {RSI_LONG_ENTRY} 이하, 숏 진입 {RSI_SHORT_ENTRY} 이상")
    print(f"영역 판단: 일봉 {DAILY_MA_SHORT}/{DAILY_MA_LONG} 이평선")
    print("="*70 + "\n")
    
    # =========================================================================
    # 데이터 가용성 검증
    # =========================================================================
    print("📊 데이터 가용성 검증 중...")
    is_valid, errors = validate_data_availability(COIN_LIST, TEST_START_DATE, TIMEFRAME)
    
    if not is_valid:
        print("\n" + "="*70)
        print("🚨 데이터 검증 실패! 백테스트를 중단합니다.")
        print("="*70)
        for err in errors:
            print(err)
        print("="*70)
        print("\n💡 해결 방법:")
        print("   1. 9999.Gateio_F_create_1DAY_caldle_info.py 로 부족한 데이터 다운로드")
        print("   2. 또는 TEST_START_DATE를 데이터 시작일 이후로 변경")
        print("="*70)
        return None
    
    print("✅ 모든 코인 데이터 검증 통과!\n")
    
    # 데이터 로드
    data_frames = {}
    daily_frames = {}
    
    for symbol in COIN_LIST:
        df = load_data(symbol, TIMEFRAME, TEST_START_DATE, TEST_END_DATE)
        if not df.empty:
            data_frames[symbol] = df
            daily_frames[symbol] = load_daily_data(symbol)
    
    if not data_frames:
        print("데이터가 없어 백테스트를 중단합니다.")
        return None
    
    # 공통 인덱스 찾기
    common_index = data_frames[list(data_frames.keys())[0]].index
    for symbol in list(data_frames.keys())[1:]:
        common_index = common_index.intersection(data_frames[symbol].index)
    common_index = common_index.sort_values()
    
    print(f"공통 데이터 기간: {common_index.min()} ~ {common_index.max()}")
    print(f"총 캔들 수: {len(common_index)}\n")
    
    # 자금 매니저 초기화
    fund_mgr = FundManager(INITIAL_CAPITAL, list(data_frames.keys()))
    
    # 백테스트 루프
    processed = 0
    for current_time in common_index:
        processed += 1
        if processed % 10000 == 0:
            print(f"  처리 중... {processed}/{len(common_index)} ({processed*100//len(common_index)}%)")
        
        # 현재가 수집 (중복 데이터 방지)
        current_prices = {}
        for symbol in data_frames:
            try:
                price_data = data_frames[symbol].loc[current_time]['close']
                # Series로 반환되는 경우 (중복 인덱스) 첫 번째 값 사용
                if isinstance(price_data, pd.Series):
                    price_data = price_data.iloc[0]
                current_prices[symbol] = float(price_data)
            except Exception:
                current_prices[symbol] = 0.0
        
        for symbol, df in data_frames.items():
            pos = fund_mgr.positions[symbol]
            daily_df = daily_frames.get(symbol)
            
            # 현재/이전 캔들 - 인덱스 찾기
            try:
                idx = df.index.get_loc(current_time)
                # slice 반환 시 첫번째 값 사용
                if isinstance(idx, slice):
                    idx = idx.start if idx.start is not None else 0
            except KeyError:
                continue
            
            if idx < 2:
                continue
            
            prev_candle = df.iloc[idx - 1]
            current_candle = df.iloc[idx]
            
            prev_rsi = prev_candle['rsi']
            execution_price = current_candle['open']
            current_price = current_candle['close']
            
            # 현재 영역 판단
            current_zone = ZoneType.MIDDLE  # 기본값
            if daily_df is not None:
                # 현재 시간 이전의 가장 최근 일봉 종가 찾기
                daily_before = daily_df[daily_df.index < current_time]
                if len(daily_before) > 0:
                    last_daily = daily_before.iloc[-1]
                    current_zone = get_zone(
                        last_daily['close'],
                        last_daily['ma_short'],
                        last_daily['ma_long']
                    )
            
            # 1. 방문 영역 업데이트 (MIDDLE 시작 포지션용)
            if pos.has_long_position() and pos.long_start_zone == ZoneType.MIDDLE:
                if current_zone in [ZoneType.LONG, ZoneType.SHORT]:
                    pos.long_visited_zone = current_zone
            
            if pos.has_short_position() and pos.short_start_zone == ZoneType.MIDDLE:
                if current_zone in [ZoneType.LONG, ZoneType.SHORT]:
                    pos.short_visited_zone = current_zone
            
            # 2. 영역 변화에 따른 청산 체크
            if pos.has_long_position():
                if should_close_by_zone_change(pos, 'long', current_zone):
                    visited_info = f"→{pos.long_visited_zone.value}" if pos.long_visited_zone else ""
                    reason = f"영역변화 {pos.long_start_zone.value}{visited_info}→{current_zone.value}"
                    fund_mgr.close_long(symbol, execution_price, current_time, LEVERAGE, reason)
            
            if pos.has_short_position():
                if should_close_by_zone_change(pos, 'short', current_zone):
                    visited_info = f"→{pos.short_visited_zone.value}" if pos.short_visited_zone else ""
                    reason = f"영역변화 {pos.short_start_zone.value}{visited_info}→{current_zone.value}"
                    fund_mgr.close_short(symbol, execution_price, current_time, LEVERAGE, reason)
            
            # 3. 익절 체크
            fund_mgr.check_take_profit(symbol, current_price, current_time, LEVERAGE)
            
            # 4. RSI 리셋 체크
            if not pos.long_rsi_reset and prev_rsi > RSI_LONG_RESET:
                pos.long_rsi_reset = True
            if not pos.short_rsi_reset and prev_rsi < RSI_SHORT_RESET:
                pos.short_rsi_reset = True
            
            # 5. 진입 조건 체크
            allowed = get_allowed_directions(current_zone)
            
            # 롱 진입
            if 'long' in allowed:
                if prev_rsi <= RSI_LONG_ENTRY:
                    can_enter = False
                    if pos.long_entry_count == 0:
                        can_enter = True
                    elif pos.long_rsi_reset and pos.long_entry_count < MAX_ENTRY_COUNT:
                        can_enter = True
                    
                    if can_enter:
                        fund_mgr.open_long(symbol, execution_price, current_time, current_prices, current_zone, LEVERAGE, prev_rsi)
            
            # 숏 진입
            if 'short' in allowed:
                if prev_rsi >= RSI_SHORT_ENTRY:
                    can_enter = False
                    if pos.short_entry_count == 0:
                        can_enter = True
                    elif pos.short_rsi_reset and pos.short_entry_count < MAX_ENTRY_COUNT:
                        can_enter = True
                    
                    if can_enter:
                        fund_mgr.open_short(symbol, execution_price, current_time, current_prices, current_zone, LEVERAGE, prev_rsi)
        
        # 연간 출금 체크
        fund_mgr.check_annual_withdrawal(current_time, current_prices)
        
        # 일별 잔액 기록
        fund_mgr.record_daily_balance(current_time, current_prices)
    
    # 미청산 포지션 정리
    print("\n미청산 포지션 정리...")
    for symbol in data_frames:
        pos = fund_mgr.positions[symbol]
        last_price = data_frames[symbol].iloc[-1]['close']
        last_time = data_frames[symbol].index[-1]
        
        if pos.has_long_position():
            fund_mgr.close_long(symbol, last_price, last_time, LEVERAGE, "백테스트 종료")
        if pos.has_short_position():
            fund_mgr.close_short(symbol, last_price, last_time, LEVERAGE, "백테스트 종료")
    
    return fund_mgr.get_results()

# ==============================================================================
# 8. 결과 분석 및 시각화
# ==============================================================================
def analyze_results(results):
    """백테스트 결과 분석"""
    if results is None:
        return
    
    initial_capital = results['initial_capital']
    final_balance = results['final_balance']
    total_withdrawn = results['total_withdrawn']
    trades = results['trades']
    daily_df = results['daily_balance']
    
    total_equity = final_balance + total_withdrawn
    total_return = (total_equity - initial_capital) / initial_capital * 100
    
    # 거래 통계
    long_trades = [t for t in trades if t['direction'] == 'long' and t['action'] == 'close']
    short_trades = [t for t in trades if t['direction'] == 'short' and t['action'] == 'close']
    
    long_pnl = sum(t.get('pnl', 0) for t in long_trades)
    short_pnl = sum(t.get('pnl', 0) for t in short_trades)
    
    # =========================================================================
    # 포지션별 승/패 통계 (분할익절 + 최종청산 합산 기준)
    # =========================================================================
    # 포지션 그룹핑: symbol + direction + 청산시간 기준으로 포지션 단위 묶기
    position_pnl = {}  # key: (symbol, direction, position_id), value: total_pnl
    
    # 청산 거래(close)와 부분익절(partial_close)을 포지션 단위로 그룹핑
    close_trades_all = [t for t in trades if t['action'] in ['close', 'partial_close']]
    
    # 시간순 정렬
    close_trades_all.sort(key=lambda x: x['timestamp'])
    
    # 포지션 ID 추적 (같은 symbol, direction의 연속된 거래를 하나의 포지션으로)
    position_tracker = {}  # key: (symbol, direction), value: current_position_id
    position_counter = {}  # key: (symbol, direction), value: counter
    
    for t in close_trades_all:
        key = (t['symbol'], t['direction'])
        
        if key not in position_counter:
            position_counter[key] = 0
            
        # 전체 청산(close)이면 새 포지션 ID 할당 필요
        if t['action'] == 'close':
            pos_id = position_counter[key]
            position_counter[key] += 1
        else:  # partial_close
            if key not in position_tracker:
                position_tracker[key] = position_counter[key]
                position_counter[key] += 1
            pos_id = position_tracker[key]
        
        full_key = (t['symbol'], t['direction'], pos_id)
        if full_key not in position_pnl:
            position_pnl[full_key] = 0
        position_pnl[full_key] += t.get('pnl', 0)
        
        # 전체 청산이면 tracker 리셋
        if t['action'] == 'close':
            position_tracker.pop(key, None)
    
    # 승/패 집계
    long_wins, long_losses = 0, 0
    short_wins, short_losses = 0, 0
    long_win_pnl, long_loss_pnl = 0, 0
    short_win_pnl, short_loss_pnl = 0, 0
    
    for (symbol, direction, pos_id), total_pnl in position_pnl.items():
        if direction == 'long':
            if total_pnl >= 0:
                long_wins += 1
                long_win_pnl += total_pnl
            else:
                long_losses += 1
                long_loss_pnl += total_pnl
        else:  # short
            if total_pnl >= 0:
                short_wins += 1
                short_win_pnl += total_pnl
            else:
                short_losses += 1
                short_loss_pnl += total_pnl
    
    total_wins = long_wins + short_wins
    total_losses = long_losses + short_losses
    total_positions = total_wins + total_losses
    win_rate = (total_wins / total_positions * 100) if total_positions > 0 else 0
    long_win_rate = (long_wins / (long_wins + long_losses) * 100) if (long_wins + long_losses) > 0 else 0
    short_win_rate = (short_wins / (short_wins + short_losses) * 100) if (short_wins + short_losses) > 0 else 0
    
    print("\n" + "="*70)
    print("백테스트 결과")
    print("="*70)
    print(f"초기 자본: ${initial_capital:,.2f}")
    print(f"최종 잔액: ${final_balance:,.2f}")
    print(f"총 출금액: ${total_withdrawn:,.2f}")
    print(f"총 자산가치: ${total_equity:,.2f}")
    print(f"총 수익률: {total_return:+.2f}%")
    print("-"*70)
    print(f"롱 청산 수: {len(long_trades)}, 롱 수익: ${long_pnl:+,.2f}")
    print(f"숏 청산 수: {len(short_trades)}, 숏 수익: ${short_pnl:+,.2f}")
    print("-"*70)
    print("📊 포지션별 승/패 통계 (분할익절+청산 합산 기준)")
    print("-"*70)
    print(f"{'':15} | {'승':>6} | {'패':>6} | {'승률':>8} | {'승리금액':>12} | {'패배금액':>12}")
    print("-"*70)
    print(f"{'롱':15} | {long_wins:>6} | {long_losses:>6} | {long_win_rate:>7.1f}% | ${long_win_pnl:>+11,.2f} | ${long_loss_pnl:>+11,.2f}")
    print(f"{'숏':15} | {short_wins:>6} | {short_losses:>6} | {short_win_rate:>7.1f}% | ${short_win_pnl:>+11,.2f} | ${short_loss_pnl:>+11,.2f}")
    print("-"*70)
    print(f"{'합계':15} | {total_wins:>6} | {total_losses:>6} | {win_rate:>7.1f}% | ${long_win_pnl+short_win_pnl:>+11,.2f} | ${long_loss_pnl+short_loss_pnl:>+11,.2f}")
    print("="*70)
    
    # MDD 계산
    mdd = 0
    if not daily_df.empty:
        try:
            daily_df = daily_df.copy()
            daily_df['date'] = pd.to_datetime(daily_df['date'])
            # 일별로 집계 (중복 방지 및 마지막 값 사용)
            daily_agg = daily_df.groupby('date')['balance'].last().reset_index()
            daily_agg = daily_agg.sort_values('date')
            
            # Series나 object 타입이 섞여있을 수 있으므로 float으로 강제 변환
            daily_agg['balance'] = pd.to_numeric(daily_agg['balance'], errors='coerce').fillna(0)
            
            balance_series = daily_agg['balance'].values
            peak = np.maximum.accumulate(balance_series)
            
            # 0으로 나누기 방지
            peak_safe = np.where(peak == 0, 1, peak)
            drawdown = (balance_series - peak) / peak_safe * 100
            mdd = np.min(drawdown)
            
            # 그래프용 daily_df 재구성
            daily_df = daily_agg.set_index('date')
            daily_df['peak'] = peak
            daily_df['drawdown'] = drawdown
            
            print(f"MDD: {mdd:.2f}%")
        except Exception as e:
            print(f"MDD 계산 오류: {e}")
            import traceback
            traceback.print_exc()
    
    # =========================================================================
    # 월별/연도별 수익 요약
    # =========================================================================
    # close와 partial_close 모두 포함 (부분 익절 수익도 집계)
    close_trades = [t for t in trades if t['action'] in ['close', 'partial_close']]
    
    if close_trades:
        # 거래를 DataFrame으로 변환
        trades_df = pd.DataFrame(close_trades)
        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
        trades_df['year'] = trades_df['timestamp'].dt.year
        trades_df['month'] = trades_df['timestamp'].dt.month
        trades_df['year_month'] = trades_df['timestamp'].dt.to_period('M')
        
        # 월별 수익 집계
        monthly_pnl = trades_df.groupby('year_month')['pnl'].sum()
        
        # 연도별 수익 집계
        yearly_pnl = trades_df.groupby('year')['pnl'].sum()
        
        # 월별 수익 출력
        print("\n" + "="*100)
        print("월별 수익 요약")
        print("="*100)
        print(f"{'월':^10} | {'수익(USDT)':>15} | {'수익률(%)':>10} | {'누적수익':>15} | {'잔액':>15}")
        print("-"*100)
        
        cumulative = 0
        prev_balance = initial_capital
        balance = initial_capital
        for period, pnl in monthly_pnl.items():
            # 월간 수익률 = 해당월 수익 / 월초 잔액 * 100
            monthly_return = (pnl / prev_balance * 100) if prev_balance > 0 else 0
            cumulative += pnl
            balance = initial_capital + cumulative
            print(f"{str(period):^10} | {pnl:>+15,.2f} | {monthly_return:>+9.2f}% | {cumulative:>+15,.2f} | {balance:>15,.2f}")
            prev_balance = balance
        
        # 연도별 수익 출력
        print("\n" + "="*85)
        print("연도별 수익 요약")
        print("="*85)
        print(f"{'연도':^10} | {'수익(USDT)':>15} | {'수익률(%)':>12} | {'잔액':>15}")
        print("-"*85)
        
        prev_balance = initial_capital
        balance = initial_capital
        for year, pnl in yearly_pnl.items():
            if prev_balance == 0:
                year_return = 0
            else:
                year_return = (pnl / prev_balance) * 100
                
            balance = prev_balance + pnl
            print(f"{year:^10} | {pnl:>+15,.2f} | {year_return:>+12.2f}% | {balance:>15,.2f}")
            prev_balance = balance
        
        print("="*85)
    
    # 그래프 그리기
    if not daily_df.empty and 'balance' in daily_df.columns:
        try:
            fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
            
            # 데이터 추출 및 타입을 강제로 float으로 변환
            dates = daily_df.index.to_numpy()
            
            # balance가 object 타입 등으로 오염되었을 가능성 처리
            balance_vals = pd.to_numeric(daily_df['balance'], errors='coerce').fillna(0).to_numpy()
            
            if 'drawdown' in daily_df.columns:
                drawdown_vals = pd.to_numeric(daily_df['drawdown'], errors='coerce').fillna(0).to_numpy()
            else:
                drawdown_vals = np.zeros(len(balance_vals))
            
            # 잔액 추이
            axes[0].plot(dates, balance_vals, label='잔액', color='blue')
            axes[0].axhline(y=initial_capital, color='gray', linestyle='--', label='초기자본')
            axes[0].set_title('RSI 롱숏 분할매매 전략 - 잔액 추이')
            axes[0].set_ylabel('USDT')
            axes[0].legend()
            axes[0].grid(True, alpha=0.3)
            
            # 드로다운
            axes[1].fill_between(dates, drawdown_vals, 0, color='red', alpha=0.3)
            axes[1].set_title('드로다운')
            axes[1].set_ylabel('%')
            axes[1].set_xlabel('날짜')
            axes[1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.show()
        except Exception as e:
            print(f"그래프 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            
    return results

# ==============================================================================
# 9. 메인 실행
# ==============================================================================
if __name__ == "__main__":
    results = run_backtest()
    analyze_results(results)