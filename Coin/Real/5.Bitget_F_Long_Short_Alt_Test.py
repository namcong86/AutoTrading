# -*- coding:utf-8 -*-
"""
파일이름: 5.Bitget_F_Long_Short_Alt_Test.py
설명: 골든크로스/데드크로스 롱숏 전략 백테스트
      1시간봉 기준 20이평/120이평 크로스 전략
      사이클 기반 자금 관리 (1/N 분배)
      
사이클 개념:
- 사이클 시작: 첫 포지션 진입 시, 현재 잔액을 N등분하여 코인당 할당금액 결정
- 사이클 진행 중: 새 진입은 해당 사이클의 할당금액으로 진입 (잔액 변동 무관)
- 사이클 종료: 모든 포지션이 청산되면 사이클 종료 → 다음 사이클에서 재분배
"""
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import os
import ccxt
import time

# ==============================================================================
# 한글 폰트 설정 (Windows)
# ==============================================================================
import matplotlib.font_manager as fm

# 시스템에서 사용 가능한 한글 폰트 찾기
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
    # 폰트를 못찾으면 기본 설정
    plt.rcParams['axes.unicode_minus'] = False
    return False

set_korean_font()

# ==============================================================================
# 백테스트 설정
# ==============================================================================
INITIAL_CAPITAL = 10000      # 초기 자본금 (USDT)
LEVERAGE = 1.5                  # 레버리지 배수
SHORT_MA = 20                 # 단기 이동평균 기간
LONG_MA = 120                 # 장기 이동평균 기간
DAILY_MA = 115                # 일봉 장기 이동평균 기간 (방향 필터용)
DAILY_MA_SHORT = 20           # 일봉 단기 이동평균 기간 (듀얼 필터용)
TIMEFRAME = '1h'              # 캔들 타임프레임 ('1h' 또는 '15m')
FEE_RATE = 0.0006             # 거래 수수료 (0.06%)

# 듀얼 이평선 필터 설정 (20일선 + 115일선)
# True: 직전일 종가가 두 선 위 → 롱만, 두 선 아래 → 숏만, 사이 → 둘 다 가능
# False: 기존 115일선만 사용
DAILY_DUAL_MA_FILTER_ENABLED = True

# 부분 익절 설정
TAKE_PROFIT_ENABLED = True    # 부분 익절 로직 활성화 여부 (True: 적용, False: 미적용)

# 익절 설정 (전캔들 기준, 각 조건당 한번씩만 적용) - TAKE_PROFIT_ENABLED = True일 때만 적용
TAKE_PROFIT_LEVELS = [
    {'profit_pct': 5, 'sell_pct': 10},   # 3% 수익 시 10% 익절
    {'profit_pct': 10, 'sell_pct': 20},   # 5% 수익 시 나머지의 20% 익절
    {'profit_pct': 20, 'sell_pct': 30},  # 10% 수익 시 나머지의 30% 익절
]

# 테스트 기간
START_DATE = '2021-07-01'
END_DATE = datetime.now().strftime('%Y-%m-%d')  # 오늘 날짜까지

# 연간 출금 설정 (1월 1일에 전년도 수익의 일정 비율 출금)
ANNUAL_WITHDRAWAL_ENABLED = True        # 연간 출금 활성화 여부
ANNUAL_WITHDRAWAL_RATE = 0.20           # 1년 수익의 출금 비율 (20%)
ANNUAL_WITHDRAWAL_MONTHS = [1]          # 출금 실행 월 (1월 1일만)

# 코인 리스트 (JSON 파일 기준) - 자금은 사이클 시작 시 1/N 분배
COIN_LIST = [
    'ADA/USDT:USDT',
    'DOGE/USDT:USDT',
    'SOL/USDT:USDT',
    'AVAX/USDT:USDT',
    # 'BNB/USDT:USDT',
    # 'SHIB/USDT:USDT',
]

# JSON 데이터 경로
DATA_PATH = r'C:\AutoTrading\Coin\json'
CYCLE_STATE_FILE = os.path.join(DATA_PATH, 'cycle_state.json')


# ==============================================================================
# 사이클 상태 관리 클래스
# ==============================================================================
class CycleManager:
    """사이클 기반 자금 관리
    
    사이클 개념:
    - 포지션이 하나도 없는 상태에서 첫 진입 시 새 사이클 시작
    - 사이클 시작 시 현재 잔액을 코인 수(N)로 나눠 할당금액 결정
    - 사이클 진행 중에는 청산으로 잔액이 변해도 할당금액은 고정
    - 모든 포지션이 청산되면 사이클 종료
    """
    def __init__(self, initial_capital, coin_list, state_file):
        self.state_file = state_file
        self.coin_list = coin_list
        self.n_coins = len(coin_list)
        
        # 상태 초기화
        self.available_balance = initial_capital  # 사용 가능한 잔액 (포지션에 묶이지 않은 금액)
        self.cycle_num = 0              # 현재 사이클 번호
        self.cycle_allocation = 0       # 사이클 시작 시 코인당 할당금액
        self.in_cycle = False           # 사이클 진행 중 여부
        
        # 코인별 포지션 정보
        self.positions = {}  # {symbol: {'direction': 'long/short', 'entry_price': float, 'qty': float, 'invest_amount': float}}
        
        # 거래 기록
        self.trades = []
        self.daily_balance = []
        self.cycle_history = []  # 사이클별 기록
        
        # 분기별 출금 기록
        self.withdrawal_history = []  # 출금 기록
        self.total_withdrawn = 0      # 총 출금액
        self.last_quarter_balance = initial_capital  # 이전 분기말 잔액
        self.last_withdrawal_date = None  # 마지막 출금일
        
    def get_total_equity(self, current_prices):
        """현재 총 자산가치 (사용가능잔액 + 포지션가치 + 미실현손익)"""
        total = self.available_balance
        
        for symbol, pos in self.positions.items():
            # 포지션에 묶인 원금
            invest_amount = pos['invest_amount']
            
            # 미실현 손익
            if symbol in current_prices:
                price = current_prices[symbol]
                if pos['direction'] == 'long':
                    unrealized = invest_amount * ((price - pos['entry_price']) / pos['entry_price'])
                else:
                    unrealized = invest_amount * ((pos['entry_price'] - price) / pos['entry_price'])
            else:
                unrealized = 0
            
            total += invest_amount + unrealized
        
        return total
        
    def start_new_cycle(self, timestamp, current_prices):
        """새 사이클 시작 - 현재 총 자산을 N등분"""
        self.cycle_num += 1
        
        # 총 자산 계산 (사용가능잔액 + 미실현포지션가치) - 실제로는 포지션이 없을 때만 호출됨
        total_equity = self.get_total_equity(current_prices)
        self.cycle_allocation = total_equity / self.n_coins
        self.in_cycle = True
        
        print(f"\n{'='*70}")
        print(f"[CYCLE] 사이클 #{self.cycle_num} 시작")
        print(f"   시간: {timestamp}")
        print(f"   총 자산: ${total_equity:,.2f} USDT")
        print(f"   코인당 할당금액: ${self.cycle_allocation:,.2f} USDT (1/{self.n_coins})")
        print(f"{'='*70}\n")
        
    def end_cycle(self, timestamp):
        """사이클 종료 - 모든 포지션이 청산되었을 때"""
        cycle_info = {
            'cycle_num': self.cycle_num,
            'end_time': str(timestamp),
            'final_balance': self.available_balance,
            'allocation_per_coin': self.cycle_allocation
        }
        self.cycle_history.append(cycle_info)
        self.in_cycle = False
        
        print(f"\n{'='*70}")
        print(f"[END] 사이클 #{self.cycle_num} 종료")
        print(f"   시간: {timestamp}")
        print(f"   잔액: ${self.available_balance:,.2f} USDT")
        print(f"{'='*70}\n")
    
    def has_any_position(self):
        """포지션이 하나라도 있는지 확인"""
        return len(self.positions) > 0
    
    def get_position(self, symbol):
        """특정 코인의 포지션 정보 반환"""
        return self.positions.get(symbol, None)
    
    def open_position(self, symbol, direction, price, timestamp, leverage, current_prices):
        """포지션 진입"""
        # 사이클이 시작 안됐으면 새 사이클 시작
        if not self.in_cycle:
            self.start_new_cycle(timestamp, current_prices)
        
        # 진입 시점의 현재 총 자산 기준으로 할당금액 동적 계산
        # (가용잔액 + 포지션 평가금액) / N으로 계산하여 손실/이익 반영
        current_equity = self.get_total_equity(current_prices)
        dynamic_allocation = current_equity / self.n_coins
        
        invest_amount = dynamic_allocation * leverage
        qty = invest_amount / price
        fee = invest_amount * FEE_RATE
        
        # 사용 가능 잔액에서 투자금 + 수수료 차감
        self.available_balance -= (invest_amount + fee)
        
        self.positions[symbol] = {
            'direction': direction,
            'entry_price': price,
            'qty': qty,
            'invest_amount': invest_amount,
            'entry_time': str(timestamp),
            'tp_triggered': [False, False, False]  # 각 익절 레벨 트리거 여부
        }
        
        active_count = len(self.positions)
        print(f"[{timestamp}] {symbol} {'롱' if direction == 'long' else '숏'} 진입: "
              f"진입가 ${price:.6f}, 할당금액 ${dynamic_allocation:.2f} USDT (총자산 ${current_equity:.2f} / {self.n_coins}) "
              f"(사이클 #{self.cycle_num}, 활성 {active_count}/{self.n_coins})")
    
    def partial_close_position(self, symbol, price, timestamp, leverage, sell_pct, tp_level):
        """부분 익절 - 현재 물량의 sell_pct% 청산"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        entry_price = pos['entry_price']
        current_qty = pos['qty']
        current_invest = pos['invest_amount']
        direction = pos['direction']
        
        # 청산할 물량 계산
        close_qty = current_qty * (sell_pct / 100)
        close_invest = current_invest * (sell_pct / 100)
        
        # 손익 계산
        if direction == 'long':
            pnl_rate = (price - entry_price) / entry_price * leverage
        else:
            pnl_rate = (entry_price - price) / entry_price * leverage
        
        pnl = close_invest * pnl_rate
        fee = close_qty * price * FEE_RATE
        
        # 잔액에 반환
        self.available_balance += close_invest + pnl - fee
        
        # 포지션 업데이트 (남은 물량)
        pos['qty'] = current_qty - close_qty
        pos['invest_amount'] = current_invest - close_invest
        pos['tp_triggered'][tp_level] = True
        
        # 거래 기록
        self.trades.append({
            'cycle': self.cycle_num,
            'symbol': symbol,
            'timestamp': timestamp,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': price,
            'qty': close_qty,
            'invest_amount': close_invest,
            'pnl_rate': pnl_rate * 100,
            'pnl': pnl,
            'trade_type': f'TP{tp_level+1}({sell_pct}%)'
        })
        
        print(f"[{timestamp}] {symbol} 익절 TP{tp_level+1}: "
              f"{sell_pct}% 청산 @ ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, "
              f"수익금 ${pnl:+.2f} (잔여 {100-sell_pct}%)")
    
    def check_take_profit(self, symbol, prev_close, timestamp, leverage, tp_levels, tp_enabled=True):
        """익절 조건 체크 - 전캔들 종가 기준
        
        Args:
            tp_enabled: 부분 익절 로직 활성화 여부 (False면 익절 체크 안함)
        """
        # 부분 익절이 비활성화되면 스킵
        if not tp_enabled:
            return
            
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        entry_price = pos['entry_price']
        direction = pos['direction']
        
        # 전캔들 기준 수익률 계산
        if direction == 'long':
            profit_pct = (prev_close - entry_price) / entry_price * 100 * leverage
        else:
            profit_pct = (entry_price - prev_close) / entry_price * 100 * leverage
        
        # 각 익절 레벨 체크 (낮은 레벨부터)
        for i, tp in enumerate(tp_levels):
            if not pos['tp_triggered'][i] and profit_pct >= tp['profit_pct']:
                self.partial_close_position(symbol, prev_close, timestamp, leverage, tp['sell_pct'], i)
    
    def close_position(self, symbol, price, timestamp, leverage):
        """포지션 전체 청산"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        entry_price = pos['entry_price']
        qty = pos['qty']
        direction = pos['direction']
        invest_amount = pos['invest_amount']
        
        if direction == 'long':
            pnl_rate = (price - entry_price) / entry_price * leverage
        else:
            pnl_rate = (entry_price - price) / entry_price * leverage
        
        pnl = invest_amount * pnl_rate
        fee = qty * price * FEE_RATE
        
        # 원금 + 수익 - 수수료를 사용 가능 잔액에 반환
        self.available_balance += invest_amount + pnl - fee
        
        self.trades.append({
            'cycle': self.cycle_num,
            'symbol': symbol,
            'timestamp': timestamp,
            'direction': direction,
            'entry_price': entry_price,
            'exit_price': price,
            'qty': qty,
            'invest_amount': invest_amount,
            'pnl_rate': pnl_rate * 100,
            'pnl': pnl,
            'trade_type': 'CLOSE'
        })
        
        del self.positions[symbol]
        
        remaining_count = len(self.positions)
        print(f"[{timestamp}] {symbol} {'롱' if direction == 'long' else '숏'} 청산: "
              f"청산가 ${price:.6f}, 수익률 {pnl_rate*100:+.2f}%, "
              f"수익금 ${pnl:+.2f} USDT (잔여 포지션 {remaining_count}/{self.n_coins})")
        
        # 모든 포지션이 청산되면 사이클 종료
        if not self.has_any_position():
            self.end_cycle(timestamp)
    
    def record_daily_balance(self, timestamp, current_prices):
        """일별 자산가치 기록"""
        equity = self.get_total_equity(current_prices)
        self.daily_balance.append({
            'date': timestamp,
            'balance': equity,
            'cycle': self.cycle_num,
            'active_positions': len(self.positions)
        })
    
    def check_annual_withdrawal(self, timestamp, current_prices, withdrawal_rate, withdrawal_months):
        """연간 출금 체크 및 실행 (1월 1일)
        
        - 포지션은 그대로 유지
        - 1년간 수익이 있는 경우에만 수익의 일정 비율(기본 20%) 출금
        - 사용 가능한 잔액(available_balance)에서만 출금
        """
        current_date = timestamp.date() if hasattr(timestamp, 'date') else timestamp
        
        # 출금일인지 확인 (1일이고, 출금 월인 경우 - 1월만)
        if current_date.day != 1 or current_date.month not in withdrawal_months:
            return False
        
        # 이미 오늘 출금했으면 스킵
        if self.last_withdrawal_date == current_date:
            return False
        
        # 현재 총 자산 계산
        current_equity = self.get_total_equity(current_prices)
        
        # 1년간 수익 계산
        year_profit = current_equity - self.last_quarter_balance
        
        # 수익이 있는 경우에만 출금
        if year_profit > 0:
            # 출금액 = 수익의 일정 비율 (제한 없이 전액 출금)
            actual_withdrawal = year_profit * withdrawal_rate
            
            if actual_withdrawal > 0:
                self.available_balance -= actual_withdrawal
                self.total_withdrawn += actual_withdrawal
                
                # 출금 후 총 자산 다시 계산
                new_equity = self.get_total_equity(current_prices)
                
                self.withdrawal_history.append({
                    'date': str(current_date),
                    'year_start_balance': self.last_quarter_balance,
                    'current_equity': current_equity,
                    'year_profit': year_profit,
                    'withdrawal_amount': actual_withdrawal,
                    'remaining_equity': new_equity,
                    'remaining_balance': self.available_balance,
                    'total_withdrawn': self.total_withdrawn
                })
                
                print(f"\n{'='*70}")
                print(f"[출금] 연간 출금 실행 - {current_date}")
                print(f"   이전 연말 잔액: ${self.last_quarter_balance:,.2f}")
                print(f"   현재 총 자산: ${current_equity:,.2f}")
                print(f"   1년 수익: ${year_profit:+,.2f}")
                print(f"   출금액 ({withdrawal_rate*100:.0f}%): ${actual_withdrawal:,.2f}")
                print(f"   출금 후 총 자산: ${new_equity:,.2f}")
                print(f"   (포지션: ${new_equity - self.available_balance:,.2f} + 현금: ${self.available_balance:,.2f})")
                print(f"   누적 출금액: ${self.total_withdrawn:,.2f}")
                print(f"{'='*70}\n")
        else:
            print(f"\n[출금] {current_date}: 수익 없음 (${year_profit:+,.2f}), 출금 스킵\n")
        
        # 연간 기준점 업데이트
        self.last_quarter_balance = self.get_total_equity(current_prices)
        self.last_withdrawal_date = current_date
        
        return True
    
    def save_state_to_file(self):
        """상태를 JSON 파일로 저장 (실거래용)"""
        state = {
            'available_balance': self.available_balance,
            'cycle_num': self.cycle_num,
            'cycle_allocation': self.cycle_allocation,
            'in_cycle': self.in_cycle,
            'positions': self.positions,
            'updated_at': datetime.now().isoformat()
        }
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state_from_file(self):
        """JSON 파일에서 상태 로드 (실거래용)"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            self.available_balance = state['available_balance']
            self.cycle_num = state['cycle_num']
            self.cycle_allocation = state['cycle_allocation']
            self.in_cycle = state['in_cycle']
            self.positions = state['positions']
            return True
        return False
    
    def get_results(self, initial_capital):
        """결과 반환"""
        # 총 수익 = 최종 잔액 + 총 출금액 - 초기자본
        total_profit = (self.available_balance + self.total_withdrawn) - initial_capital
        total_return = total_profit / initial_capital * 100
        
        return {
            'initial_capital': initial_capital,
            'final_balance': self.available_balance,
            'total_withdrawn': self.total_withdrawn,
            'total_equity': self.available_balance + self.total_withdrawn,
            'total_return': total_return,
            'total_cycles': self.cycle_num,
            'trades': self.trades,
            'daily_balance': pd.DataFrame(self.daily_balance),
            'cycle_history': self.cycle_history,
            'withdrawal_history': self.withdrawal_history
        }


# ==============================================================================
# 통합 백테스트 클래스
# ==============================================================================
class IntegratedBacktest:
    """모든 코인을 시간순으로 통합하여 백테스트"""
    
    def __init__(self, coin_list, initial_capital, leverage, short_ma, long_ma, daily_ma):
        self.coin_list = coin_list
        self.initial_capital = initial_capital
        self.leverage = leverage
        self.short_ma = short_ma
        self.long_ma = long_ma
        self.daily_ma = daily_ma
        
        # 사이클 매니저
        self.cycle_mgr = CycleManager(initial_capital, coin_list, CYCLE_STATE_FILE)
        
        # 코인별 데이터
        self.coin_data = {}       # {symbol: DataFrame}
        self.coin_daily = {}      # {symbol: DataFrame (일봉)}
    
    def load_data(self, symbol, json_path, daily_json_path, start_date, end_date):
        """코인별 데이터 로드 및 시그널 계산
        JSON 파일의 마지막 데이터 이후부터 현재까지 API로 추가 데이터 수집
        """
        # 메인 데이터 로드
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # API로 최신 데이터 가져오기
        df = self.fetch_latest_data(df, symbol, json_path)
        
        # 기간 필터링
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        df['symbol'] = symbol
        
        # 이동평균 계산
        df['ma_short'] = df['close'].rolling(window=self.short_ma).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_ma).mean()
        
        # 크로스 감지 (전전봉 vs 전봉 비교 → 전봉에서 크로스 확정 → 현재봉에서 진입)
        df['prev_ma_short'] = df['ma_short'].shift(1)
        df['prev_ma_long'] = df['ma_long'].shift(1)
        df['prev2_ma_short'] = df['ma_short'].shift(2)
        df['prev2_ma_long'] = df['ma_long'].shift(2)
        
        # 전봉에서 크로스가 발생했는지 체크 (전전봉 MA vs 전봉 MA 비교)
        # 이렇게 하면 "전봉 마감 시 크로스 확정 → 현재봉 시가로 진입" 구조가 됨
        df['golden_cross'] = (df['prev2_ma_short'] <= df['prev2_ma_long']) & (df['prev_ma_short'] > df['prev_ma_long'])
        df['dead_cross'] = (df['prev2_ma_short'] >= df['prev2_ma_long']) & (df['prev_ma_short'] < df['prev_ma_long'])
        
        self.coin_data[symbol] = df
        
        # 일봉 데이터 로드
        try:
            with open(daily_json_path, 'r') as f:
                daily_data = json.load(f)
            
            df_daily = pd.DataFrame(daily_data)
            df_daily['datetime'] = pd.to_datetime(df_daily['datetime'])
            df_daily.set_index('datetime', inplace=True)
            
            # 일봉도 API로 최신 데이터 가져오기
            df_daily = self.fetch_latest_data(df_daily, symbol, daily_json_path, timeframe='1d')
            
            df_daily['daily_ma'] = df_daily['close'].rolling(window=self.daily_ma).mean()
            df_daily['daily_ma_short'] = df_daily['close'].rolling(window=DAILY_MA_SHORT).mean()
            self.coin_daily[symbol] = df_daily
            if DAILY_DUAL_MA_FILTER_ENABLED:
                print(f"  {symbol}: {len(df)}개 캔들, 일봉 {DAILY_MA_SHORT}/{self.daily_ma}MA 듀얼 필터 적용")
            else:
                print(f"  {symbol}: {len(df)}개 캔들, 일봉 {self.daily_ma}MA 필터 적용")
        except FileNotFoundError:
            self.coin_daily[symbol] = None
            print(f"  {symbol}: {len(df)}개 캔들, 일봉 데이터 없음 (양방향 허용)")
        
        return df
    
    def fetch_latest_data(self, existing_df, symbol, json_path, timeframe=None):
        """JSON 파일의 마지막 데이터 이후부터 현재까지 API로 데이터 수집"""
        try:
            # Bitget 객체 생성
            bitget = ccxt.bitget({
                'enableRateLimit': True,
                'options': {'defaultType': 'swap'}
            })
            
            # 타임프레임 결정
            if timeframe is None:
                if '1h' in json_path:
                    timeframe = '1h'
                elif '1d' in json_path:
                    timeframe = '1d'
                elif '15m' in json_path:
                    timeframe = '15m'
                else:
                    timeframe = TIMEFRAME
            
            # 마지막 데이터 시간 확인
            last_datetime = existing_df.index.max()
            now = pd.Timestamp.now(tz='UTC').tz_localize(None)
            
            # 시간 차이 계산 (캔들 수 기준)
            if timeframe == '1h':
                time_diff_hours = (now - last_datetime).total_seconds() / 3600
                candles_needed = int(time_diff_hours) + 1
            elif timeframe == '1d':
                time_diff_days = (now - last_datetime).total_seconds() / 86400
                candles_needed = int(time_diff_days) + 1
            elif timeframe == '15m':
                time_diff_mins = (now - last_datetime).total_seconds() / 900
                candles_needed = int(time_diff_mins) + 1
            else:
                candles_needed = 100
            
            if candles_needed <= 1:
                print(f"  {symbol} ({timeframe}): 데이터 최신 상태")
                return existing_df
            
            # 심볼 변환 (ADA/USDT:USDT -> ADAUSDT)
            api_symbol = symbol.replace('/', '').replace(':USDT', '')
            
            print(f"  {symbol} ({timeframe}): {last_datetime} 이후 {candles_needed}개 캔들 API로 수집 중...")
            
            # API로 데이터 가져오기
            since_ms = int(last_datetime.timestamp() * 1000)
            all_ohlcv = []
            
            while len(all_ohlcv) < candles_needed:
                ohlcv = bitget.fetch_ohlcv(symbol, timeframe, since=since_ms, limit=200)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since_ms = ohlcv[-1][0] + 1
                time.sleep(0.2)
                
                if len(ohlcv) < 200:
                    break
            
            if not all_ohlcv:
                print(f"  {symbol} ({timeframe}): API에서 데이터 없음")
                return existing_df
            
            # DataFrame 변환
            new_df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            new_df['datetime'] = pd.to_datetime(new_df['timestamp'], unit='ms')
            new_df.set_index('datetime', inplace=True)
            new_df = new_df[['open', 'high', 'low', 'close', 'volume']]
            
            # 중복 제거 후 병합
            new_df = new_df[new_df.index > last_datetime]
            
            if len(new_df) > 0:
                combined_df = pd.concat([existing_df, new_df])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df.sort_index(inplace=True)
                
                print(f"  {symbol} ({timeframe}): {len(new_df)}개 캔들 추가됨 (총 {len(combined_df)}개)")
                
                # JSON 파일 업데이트 (선택적)
                self.save_updated_json(combined_df, json_path)
                
                return combined_df
            else:
                print(f"  {symbol} ({timeframe}): 새 데이터 없음")
                return existing_df
                
        except Exception as e:
            print(f"  {symbol}: API 데이터 수집 실패 - {e}")
            return existing_df
    
    def save_updated_json(self, df, json_path):
        """업데이트된 데이터를 JSON 파일로 저장"""
        try:
            # DataFrame을 JSON 형식으로 변환
            df_save = df.reset_index()
            df_save['datetime'] = df_save['datetime'].astype(str)
            data = df_save.to_dict('records')
            
            with open(json_path, 'w') as f:
                json.dump(data, f)
            
            print(f"    -> JSON 파일 업데이트: {json_path}")
        except Exception as e:
            print(f"    -> JSON 저장 실패: {e}")
    
    def get_daily_trend(self, symbol, timestamp):
        """일봉 기준 추세 확인
        
        DAILY_DUAL_MA_FILTER_ENABLED = True인 경우:
        - 직전일 종가 > 20MA AND 115MA → 'long' (롱만 가능)
        - 직전일 종가 < 20MA AND 115MA → 'short' (숏만 가능)
        - 직전일 종가가 두 선 사이 → 'both' (롱숏 모두 가능)
        
        DAILY_DUAL_MA_FILTER_ENABLED = False인 경우:
        - 기존 로직: 115MA 위면 'long', 아래면 'short'
        """
        if symbol not in self.coin_daily or self.coin_daily[symbol] is None:
            return 'both'
        
        df_daily = self.coin_daily[symbol]
        date_only = timestamp.date()
        daily_data = df_daily[df_daily.index.date < date_only]  # 직전일까지만 (당일 미포함)
        
        if daily_data.empty:
            return 'both'
        
        last_close = daily_data['close'].iloc[-1]
        last_ma_115 = daily_data['daily_ma'].iloc[-1]
        
        if pd.isna(last_ma_115):
            return 'both'
        
        # 듀얼 필터 모드
        if DAILY_DUAL_MA_FILTER_ENABLED:
            last_ma_20 = daily_data['daily_ma_short'].iloc[-1]
            
            if pd.isna(last_ma_20):
                # 20MA 없으면 기존 로직 사용
                return 'long' if last_close > last_ma_115 else 'short'
            
            # 두 선 중 위/아래 값 구분
            upper_ma = max(last_ma_20, last_ma_115)
            lower_ma = min(last_ma_20, last_ma_115)
            
            if last_close > upper_ma:
                # 종가가 두 선 모두 위에 → 롱만
                return 'long'
            elif last_close < lower_ma:
                # 종가가 두 선 모두 아래 → 숏만
                return 'short'
            else:
                # 종가가 두 선 사이 → 롱숏 모두 가능
                return 'both'
        else:
            # 기존 로직: 115MA만 사용
            return 'long' if last_close > last_ma_115 else 'short'
    
    def get_current_prices(self, timestamp):
        """특정 시점의 모든 코인 현재가 조회"""
        prices = {}
        for symbol, df in self.coin_data.items():
            # 해당 시점 이전의 가장 최근 가격
            valid_data = df[df.index <= timestamp]
            if not valid_data.empty:
                prices[symbol] = valid_data.iloc[-1]['close']
        return prices
    
    def run_backtest(self):
        """통합 백테스트 실행 - 모든 코인을 시간순으로 처리"""
        print("\n데이터 병합 및 시간순 정렬 중...")
        
        # 모든 캔들 이벤트를 시간순으로 병합 (익절 체크를 위해)
        all_candles = []
        
        for symbol, df in self.coin_data.items():
            df_clean = df.dropna(subset=['ma_short', 'ma_long']).copy()
            df_clean['prev_close'] = df_clean['close'].shift(1)
            
            for idx, row in df_clean.iterrows():
                all_candles.append({
                    'timestamp': idx,
                    'symbol': symbol,
                    'open': row['open'],      # 시가 추가 (진입용)
                    'close': row['close'],
                    'prev_close': row['prev_close'],
                    'golden_cross': row['golden_cross'],
                    'dead_cross': row['dead_cross']
                })
        
        # 시간순 정렬
        all_candles.sort(key=lambda x: x['timestamp'])
        
        # 크로스 이벤트 개수
        cross_events = len([c for c in all_candles if c['golden_cross'] or c['dead_cross']])
        print(f"총 캔들: {len(all_candles)}개, 크로스 시그널: {cross_events}개\n")
        
        # 시간순으로 모든 캔들 처리
        processed = 0
        total = len(all_candles)
        
        for candle in all_candles:
            processed += 1
            if processed % 20000 == 0:
                print(f"  처리 중... {processed}/{total} ({processed*100//total}%)")
            
            timestamp = candle['timestamp']
            symbol = candle['symbol']
            close = candle['close']
            prev_close = candle['prev_close']
            
            # 현재가 정보 수집
            current_prices = self.get_current_prices(timestamp)
            
            # 현재 포지션 확인
            current_pos = self.cycle_mgr.get_position(symbol)
            
            # 익절 체크 (포지션이 있고, 전캔들 종가가 있는 경우, 익절 활성화 시)
            if current_pos and pd.notna(prev_close):
                self.cycle_mgr.check_take_profit(symbol, prev_close, timestamp, self.leverage, TAKE_PROFIT_LEVELS, TAKE_PROFIT_ENABLED)
                # 익절 후 포지션 재확인 (물량이 0이 됐을 수 있음)
                current_pos = self.cycle_mgr.get_position(symbol)
            
            # 일봉 추세 확인
            daily_trend = self.get_daily_trend(symbol, timestamp)
            
            # 진입가격은 시가(open), 청산가격은 시가(open) - 전봉 마감 후 진입/청산이므로
            entry_price = candle['open']
            
            # 골든크로스 - 롱 진입 (숏 청산 후)
            # (전봉에서 골든크로스 확정 → 현재봉 시가로 진입)
            if candle['golden_cross']:
                if current_pos and current_pos['direction'] == 'short':
                    self.cycle_mgr.close_position(symbol, entry_price, timestamp, self.leverage)
                    current_pos = None
                
                if current_pos is None and daily_trend in ['long', 'both']:
                    self.cycle_mgr.open_position(symbol, 'long', entry_price, timestamp, self.leverage, current_prices)
            
            # 데드크로스 - 숏 진입 (롱 청산 후)
            # (전봉에서 데드크로스 확정 → 현재봉 시가로 진입)
            elif candle['dead_cross']:
                if current_pos and current_pos['direction'] == 'long':
                    self.cycle_mgr.close_position(symbol, entry_price, timestamp, self.leverage)
                    current_pos = None
                
                if current_pos is None and daily_trend in ['short', 'both']:
                    self.cycle_mgr.open_position(symbol, 'short', entry_price, timestamp, self.leverage, current_prices)
            
            # 연간 출금 체크 (옵션 활성화 시 - 1월 1일)
            if ANNUAL_WITHDRAWAL_ENABLED:
                self.cycle_mgr.check_annual_withdrawal(
                    timestamp, current_prices, 
                    ANNUAL_WITHDRAWAL_RATE, 
                    ANNUAL_WITHDRAWAL_MONTHS
                )
            
            # 일별 잔액 기록
            self.cycle_mgr.record_daily_balance(timestamp, current_prices)
        
        # 남은 포지션 마지막 가격으로 청산
        if self.cycle_mgr.has_any_position():
            print("\n미청산 포지션 정리...")
            for symbol in list(self.cycle_mgr.positions.keys()):
                df = self.coin_data[symbol]
                last_price = df.iloc[-1]['close']
                last_time = df.index[-1]
                self.cycle_mgr.close_position(symbol, last_price, last_time, self.leverage)
        
        return self.cycle_mgr.get_results(self.initial_capital)


# ==============================================================================
# 결과 분석 함수
# ==============================================================================
def analyze_results(results):
    """백테스트 결과 분석"""
    initial_capital = results['initial_capital']
    daily_df = results['daily_balance'].copy()
    
    if daily_df.empty:
        print("거래 데이터가 없습니다.")
        return None, 0
    
    daily_df['date'] = pd.to_datetime(daily_df['date'])
    daily_df.set_index('date', inplace=True)
    
    # 전체 MDD 계산 (기존)
    daily_df['peak'] = daily_df['balance'].cummax()
    daily_df['drawdown'] = (daily_df['balance'] - daily_df['peak']) / daily_df['peak'] * 100
    mdd = daily_df['drawdown'].min()
    
    # ========================================
    # 사이클 종료 잔액 기준 MDD 계산 (출금 보정 포함)
    # - 사이클 종료 시점의 잔액만 비교
    # - peak 이후 출금액은 최저점에 더해서 실질 MDD 계산
    # ========================================
    cycle_history = results.get('cycle_history', [])
    withdrawal_history = results.get('withdrawal_history', [])
    
    # 출금 내역을 날짜별로 정리 (누적 출금액 추적용)
    withdrawal_by_date = {}
    cumulative_withdrawal = 0
    for w in withdrawal_history:
        cumulative_withdrawal = w['total_withdrawn']
        withdrawal_by_date[w['date']] = cumulative_withdrawal
    
    # 사이클 종료 잔액 리스트 생성
    cycle_end_balances = []
    for cycle in cycle_history:
        cycle_end_balances.append({
            'cycle_num': cycle['cycle_num'],
            'end_time': cycle['end_time'],
            'balance': cycle['final_balance']
        })
    
    # 사이클 종료 잔액 기준 MDD 계산 (출금 보정 포함)
    cycle_end_mdd = 0
    cycle_end_drawdowns = {}  # 각 사이클 종료 시점의 drawdown 저장
    
    if len(cycle_end_balances) > 1:
        peak_balance = 0
        peak_cycle = 0
        peak_total_withdrawal_at_peak = 0  # balance로 peak 갱신 시에만 업데이트되는 출금액 기준점
        
        for i, cycle_data in enumerate(cycle_end_balances):
            balance = cycle_data['balance']
            cycle_num = cycle_data['cycle_num']
            cycle_end_date = cycle_data['end_time'][:10]  # YYYY-MM-DD 형식
            
            # 현재 시점까지의 총 출금액 찾기
            current_total_withdrawal = 0
            for w_date, w_amount in withdrawal_by_date.items():
                if w_date <= cycle_end_date:
                    current_total_withdrawal = w_amount
            
            if balance > peak_balance:
                # 실제 잔액이 peak을 넘은 경우 → 새로운 peak (출금 보정 리셋)
                peak_balance = balance
                peak_cycle = cycle_num
                peak_total_withdrawal_at_peak = current_total_withdrawal  # 출금 기준점도 갱신!
                cycle_end_drawdowns[cycle_num] = 0  # peak일 때는 drawdown 0
            else:
                # peak 이후 출금액 계산 (balance peak 시점 출금액과 현재 출금액의 차이)
                withdrawal_after_peak = current_total_withdrawal - peak_total_withdrawal_at_peak
                
                # 실질 잔액 = 현재 잔액 + peak 이후 출금액
                adjusted_balance = balance + withdrawal_after_peak
                
                # 출금 보정 후 잔액이 peak 이상인 경우
                if adjusted_balance >= peak_balance:
                    # MDD가 양수가 되면 안 되므로 drawdown = 0
                    # peak은 adjusted로 갱신하지만, peak_total_withdrawal_at_peak은 유지!
                    # 이렇게 해야 다음 사이클에서도 출금 보정이 계속 적용됨
                    peak_balance = adjusted_balance
                    peak_cycle = cycle_num
                    # peak_total_withdrawal_at_peak은 갱신하지 않음 (중요!)
                    cycle_end_drawdowns[cycle_num] = 0
                elif peak_balance > 0:
                    # MDD 계산 (drawdown은 항상 0 이하)
                    dd = (adjusted_balance - peak_balance) / peak_balance * 100
                    cycle_end_drawdowns[cycle_num] = dd  # 각 사이클의 drawdown 저장
                    if dd < cycle_end_mdd:
                        cycle_end_mdd = dd
    
    # 차트용 사이클 종료 기준 drawdown (사이클 종료 시점의 값을 해당 기간에 표시)
    daily_df['cycle_end_drawdown'] = 0.0
    
    # 각 사이클 번호에 해당하는 drawdown 값을 daily_df에 매핑
    for idx, row in daily_df.iterrows():
        cycle_num = row['cycle']
        if cycle_num in cycle_end_drawdowns:
            daily_df.at[idx, 'cycle_end_drawdown'] = cycle_end_drawdowns[cycle_num]
        else:
            # 아직 종료되지 않은 사이클은 이전 사이클 값 유지 또는 0
            daily_df.at[idx, 'cycle_end_drawdown'] = 0
    
    cycle_mdd = cycle_end_mdd  # 사이클 종료 잔액 기준 MDD 사용
    
    # 월별 수익률
    monthly = daily_df['balance'].resample('ME').last()
    monthly_returns = monthly.pct_change() * 100
    
    # 연도별 수익률 (첫 해는 초기자본 대비, 이후는 전년말 대비)
    yearly = daily_df['balance'].resample('YE').last()
    yearly_first = daily_df['balance'].resample('YE').first()
    
    # 각 연도 시작잔액 대비 종료잔액 수익률 계산
    yearly_returns = pd.Series(index=yearly.index, dtype=float)
    for i, (date, end_balance) in enumerate(yearly.items()):
        if i == 0:
            # 첫 해: 해당 연도 첫 잔액 대비 (또는 초기자본 대비)
            start_balance = yearly_first.iloc[0]
            yearly_returns.iloc[i] = ((end_balance - start_balance) / start_balance) * 100
        else: 
            # 이후 연도: 전년말 잔액 대비
            prev_end_balance = yearly.iloc[i-1]
            yearly_returns.iloc[i] = ((end_balance - prev_end_balance) / prev_end_balance) * 100
    
    # 승률 계산
    trades = results['trades']
    total_trades = len(trades)
    win_trades = len([t for t in trades if t['pnl'] > 0])
    lose_trades = len([t for t in trades if t['pnl'] <= 0])
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    
    # 익절 통계
    tp1_trades = len([t for t in trades if t.get('trade_type', '').startswith('TP1')])
    tp2_trades = len([t for t in trades if t.get('trade_type', '').startswith('TP2')])
    tp3_trades = len([t for t in trades if t.get('trade_type', '').startswith('TP3')])
    close_trades = len([t for t in trades if t.get('trade_type', '') == 'CLOSE'])
    
    # 코인별 통계
    coin_stats = {}
    for trade in trades:
        sym = trade['symbol']
        if sym not in coin_stats:
            coin_stats[sym] = {'trades': 0, 'wins': 0, 'total_pnl': 0}
        coin_stats[sym]['trades'] += 1
        coin_stats[sym]['total_pnl'] += trade['pnl']
        if trade['pnl'] > 0:
            coin_stats[sym]['wins'] += 1
    
    print("\n" + "=" * 70)
    print("[결과] 백테스트 결과 요약 (사이클 기반)")
    print("=" * 70)
    print(f"초기 자본금: ${initial_capital:,.2f} USDT")
    print(f"최종 잔액: ${results['final_balance']:,.2f} USDT")
    
    # 연간 출금 정보 표시
    if ANNUAL_WITHDRAWAL_ENABLED and results.get('total_withdrawn', 0) > 0:
        total_withdrawn = results['total_withdrawn']
        total_equity = results.get('total_equity', results['final_balance'])
        print(f"누적 출금액: ${total_withdrawn:,.2f} USDT")
        print(f"총 자산 (잔액+출금): ${total_equity:,.2f} USDT")
        print(f"총 수익률 (출금 포함): {results['total_return']:.2f}%")
    else:
        print(f"총 수익률: {results['total_return']:.2f}%")
    
    print(f"최대 낙폭 (MDD): {mdd:.2f}%")
    print(f"사이클 종료 기준 MDD: {cycle_mdd:.2f}% (출금 보정 포함)")
    print(f"총 사이클 수: {results['total_cycles']}회")
    print(f"총 거래 횟수: {total_trades}회")
    print(f"승률: {win_rate:.2f}% (승: {win_trades}회, 패: {lose_trades}회)")
    
    # 출금 내역 표시
    if ANNUAL_WITHDRAWAL_ENABLED and results.get('withdrawal_history'):
        print("\n" + "=" * 70)
        print("[출금] 연간 출금 내역")
        print("=" * 70)
        for w in results['withdrawal_history']:
            year_profit = w.get('year_profit', w.get('quarter_profit', 0))  # 호환성 유지
            print(f"{w['date']}: 출금 ${w['withdrawal_amount']:,.2f} (1년 수익: ${year_profit:+,.2f})")
        print(f"총 출금액: ${results['total_withdrawn']:,.2f}")
    
    print("\n" + "=" * 70)
    print("[익절] 익절 통계")
    print("=" * 70)
    print(f"TP1 (3% -> 10% 익절): {tp1_trades}회")
    print(f"TP2 (5% -> 20% 익절): {tp2_trades}회")
    print(f"TP3 (10% -> 30% 익절): {tp3_trades}회")
    print(f"전량 청산 (크로스): {close_trades}회")
    
    print("\n" + "=" * 70)
    print("[코인별] 코인별 성과")
    print("=" * 70)
    for sym, stats in coin_stats.items():
        sym_win_rate = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
        print(f"{sym}: {stats['trades']}회 거래, 승률 {sym_win_rate:.1f}%, 총 수익 ${stats['total_pnl']:+,.2f}")
    
    print("\n" + "=" * 70)
    print("[월별] 월별 수익률")
    print("=" * 70)
    prev_balance = initial_capital
    for date, ret in monthly_returns.items():
        end_balance = monthly.loc[date]
        pnl = end_balance - prev_balance
        if pd.notna(ret):
            print(f"{date.strftime('%Y-%m')}: {ret:+.2f}%  |  잔액: ${end_balance:,.2f}  |  손익: ${pnl:+,.2f}")
        prev_balance = end_balance
    
    print("\n" + "=" * 70)
    print("[연도별] 연도별 수익률")
    print("=" * 70)
    prev_yearly_balance = initial_capital
    for i, (date, ret) in enumerate(yearly_returns.items()):
        end_balance = yearly.loc[date]
        pnl = end_balance - (yearly.iloc[i-1] if i > 0 else yearly_first.iloc[0])
        print(f"{date.year}년: {ret:+.2f}%  |  잔액: ${end_balance:,.2f}  |  손익: ${pnl:+,.2f}")
    
    return daily_df, mdd, cycle_mdd, coin_stats, trades


def plot_results_with_tabs(daily_df, mdd, cycle_mdd, coin_stats, trades, initial_capital):
    """탭으로 결과 표시 (전체 + 코인별)"""
    
    # Tkinter 윈도우 생성
    root = tk.Tk()
    root.title("백테스트 결과 분석")
    root.geometry("1400x900")
    
    # 노트북(탭) 위젯 생성
    notebook = ttk.Notebook(root)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    
    # ========================================
    # 탭 1: 전체 포트폴리오 결과
    # ========================================
    tab_total = ttk.Frame(notebook)
    notebook.add(tab_total, text="📊 전체 포트폴리오")
    
    fig_total = plt.Figure(figsize=(13, 8))
    
    # 잔액 차트 (선형 + 로그 스케일)
    ax1 = fig_total.add_subplot(2, 1, 1)
    ax1.plot(daily_df.index, daily_df['balance'], label='Balance (선형)', color='blue', linewidth=1.5)
    ax1.set_title(f'전체 포트폴리오 잔액 추이 (초기: ${initial_capital:,.0f} → 최종: ${daily_df["balance"].iloc[-1]:,.0f})', fontsize=12)
    ax1.set_ylabel('잔액 (USDT)', color='blue')
    ax1.tick_params(axis='y', labelcolor='blue')
    ax1.axhline(y=initial_capital, color='gray', linestyle='--', alpha=0.5)
    ax1.grid(True, alpha=0.3)
    
    # 로그 스케일 (오른쪽 Y축)
    ax1_log = ax1.twinx()
    ax1_log.plot(daily_df.index, daily_df['balance'], label='Balance (로그)', color='orange', linewidth=1.2, linestyle='--', alpha=0.7)
    ax1_log.set_yscale('log')
    ax1_log.set_ylabel('잔액 - 로그 (USDT)', color='orange')
    ax1_log.tick_params(axis='y', labelcolor='orange')
    
    # 범례 통합
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax1_log.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    # MDD 차트 (전체 MDD + 사이클 종료 기준 MDD)
    ax2 = fig_total.add_subplot(2, 1, 2)
    ax2.fill_between(daily_df.index, daily_df['drawdown'], 0, color='red', alpha=0.3, label=f'전체 MDD ({mdd:.2f}%)')
    ax2.plot(daily_df.index, daily_df['drawdown'], color='red', linewidth=0.8)
    # 사이클 종료 기준 낙폭 (출금 보정 포함) - 파란 점선
    ax2.plot(daily_df.index, daily_df['cycle_end_drawdown'], color='blue', linewidth=1.5, linestyle='--', alpha=0.8, label=f'사이클 종료 기준 낙폭 (출금 보정)')
    # 사이클 종료 기준 MDD 수평선
    ax2.axhline(y=cycle_mdd, color='green', linestyle=':', alpha=0.7, linewidth=2, label=f'사이클 종료 기준 MDD ({cycle_mdd:.2f}%)')
    ax2.set_title(f'낙폭 - 전체 MDD: {mdd:.2f}% / 사이클 종료 기준 MDD: {cycle_mdd:.2f}% (출금 보정)', fontsize=12)
    ax2.set_xlabel('날짜')
    ax2.set_ylabel('낙폭 (%)')
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    fig_total.tight_layout()
    
    canvas_total = FigureCanvasTkAgg(fig_total, master=tab_total)
    canvas_total.draw()
    canvas_total.get_tk_widget().pack(fill='both', expand=True)
    
    # ========================================
    # 코인별 탭 생성
    # ========================================
    # 거래 데이터를 코인별로 분리
    trades_df = pd.DataFrame(trades)
    
    for symbol, stats in coin_stats.items():
        coin_name = symbol.split('/')[0]
        tab_coin = ttk.Frame(notebook)
        notebook.add(tab_coin, text=f"🪙 {coin_name}")
        
        # 해당 코인의 거래만 필터링
        coin_trades = trades_df[trades_df['symbol'] == symbol].copy()
        
        if coin_trades.empty:
            label = ttk.Label(tab_coin, text=f"{symbol} - 거래 데이터 없음", font=('Arial', 14))
            label.pack(pady=50)
            continue
        
        coin_trades['timestamp'] = pd.to_datetime(coin_trades['timestamp'])
        coin_trades = coin_trades.sort_values('timestamp')
        
        # 누적 수익 계산
        coin_trades['cumulative_pnl'] = coin_trades['pnl'].cumsum()
        coin_trades['balance'] = initial_capital / len(coin_stats) + coin_trades['cumulative_pnl']
        
        # 코인별 MDD 계산
        coin_trades['peak'] = coin_trades['balance'].cummax()
        coin_trades['drawdown'] = (coin_trades['balance'] - coin_trades['peak']) / coin_trades['peak'] * 100
        coin_mdd = coin_trades['drawdown'].min()
        
        # 코인별 통계
        coin_win_trades = len(coin_trades[coin_trades['pnl'] > 0])
        coin_lose_trades = len(coin_trades[coin_trades['pnl'] <= 0])
        coin_win_rate = (coin_win_trades / len(coin_trades) * 100) if len(coin_trades) > 0 else 0
        coin_total_pnl = coin_trades['pnl'].sum()
        
        # 익절 통계
        coin_tp1 = len(coin_trades[coin_trades['trade_type'].str.startswith('TP1', na=False)])
        coin_tp2 = len(coin_trades[coin_trades['trade_type'].str.startswith('TP2', na=False)])
        coin_tp3 = len(coin_trades[coin_trades['trade_type'].str.startswith('TP3', na=False)])
        coin_close = len(coin_trades[coin_trades['trade_type'] == 'CLOSE'])
        
        # Figure 생성
        fig_coin = plt.Figure(figsize=(13, 8))
        
        # 상단: 통계 정보
        ax_info = fig_coin.add_subplot(3, 1, 1)
        ax_info.axis('off')
        
        info_text = (
            f"【 {symbol} 거래 통계 】\n\n"
            f"총 거래 횟수: {len(coin_trades)}회  |  "
            f"승률: {coin_win_rate:.1f}% (승: {coin_win_trades}, 패: {coin_lose_trades})  |  "
            f"총 수익: ${coin_total_pnl:+,.2f}\n\n"
            f"익절 통계:  TP1(3%): {coin_tp1}회  |  TP2(5%): {coin_tp2}회  |  TP3(10%): {coin_tp3}회  |  전량청산: {coin_close}회\n\n"
            f"MDD: {coin_mdd:.2f}%"
        )
        ax_info.text(0.5, 0.5, info_text, ha='center', va='center', fontsize=11, 
                     transform=ax_info.transAxes, bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.3))
        
        # 중간: 누적 수익 차트 (선형 + 로그 스케일)
        ax_pnl = fig_coin.add_subplot(3, 1, 2)
        line_color = 'green' if coin_total_pnl >= 0 else 'red'
        ax_pnl.plot(coin_trades['timestamp'], coin_trades['balance'], 
                    color=line_color, linewidth=1.5, label='잔액 (선형)')
        ax_pnl.axhline(y=initial_capital / len(coin_stats), color='gray', linestyle='--', alpha=0.5)
        ax_pnl.set_title(f'{coin_name} 잔액 추이 (할당금: ${initial_capital / len(coin_stats):,.0f})', fontsize=11)
        ax_pnl.set_ylabel('잔액 (USDT)', color=line_color)
        ax_pnl.tick_params(axis='y', labelcolor=line_color)
        ax_pnl.grid(True, alpha=0.3)
        
        # 로그 스케일 (오른쪽 Y축)
        ax_pnl_log = ax_pnl.twinx()
        ax_pnl_log.plot(coin_trades['timestamp'], coin_trades['balance'], 
                        color='orange', linewidth=1.2, linestyle='--', alpha=0.7, label='잔액 (로그)')
        ax_pnl_log.set_yscale('log')
        ax_pnl_log.set_ylabel('잔액 - 로그 (USDT)', color='orange')
        ax_pnl_log.tick_params(axis='y', labelcolor='orange')
        
        # 범례 통합
        lines1, labels1 = ax_pnl.get_legend_handles_labels()
        lines2, labels2 = ax_pnl_log.get_legend_handles_labels()
        ax_pnl.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
        
        # 하단: MDD 차트
        ax_mdd = fig_coin.add_subplot(3, 1, 3)
        ax_mdd.fill_between(coin_trades['timestamp'], coin_trades['drawdown'], 0, 
                            color='red', alpha=0.3)
        ax_mdd.plot(coin_trades['timestamp'], coin_trades['drawdown'], color='red', linewidth=0.8)
        ax_mdd.set_title(f'{coin_name} 낙폭 (MDD: {coin_mdd:.2f}%)', fontsize=11)
        ax_mdd.set_xlabel('날짜')
        ax_mdd.set_ylabel('낙폭 (%)')
        ax_mdd.grid(True, alpha=0.3)
        
        fig_coin.tight_layout()
        
        canvas_coin = FigureCanvasTkAgg(fig_coin, master=tab_coin)
        canvas_coin.draw()
        canvas_coin.get_tk_widget().pack(fill='both', expand=True)
    
    # ========================================
    # 탭: 월별/연도별 수익률
    # ========================================
    tab_monthly = ttk.Frame(notebook)
    notebook.add(tab_monthly, text="📅 월별/연도별")
    
    fig_monthly = plt.Figure(figsize=(13, 8))
    
    # 월별 수익률 계산
    monthly_balance = daily_df['balance'].resample('ME').last()
    monthly_returns = monthly_balance.pct_change() * 100
    monthly_returns = monthly_returns.dropna()
    
    # 연도별 수익률 계산
    yearly_balance = daily_df['balance'].resample('YE').last()
    yearly_first = daily_df['balance'].resample('YE').first()
    yearly_returns = pd.Series(index=yearly_balance.index, dtype=float)
    for i, (date, end_bal) in enumerate(yearly_balance.items()):
        if i == 0:
            start_bal = yearly_first.iloc[0]
        else:
            start_bal = yearly_balance.iloc[i-1]
        yearly_returns.iloc[i] = ((end_bal - start_bal) / start_bal) * 100
    
    # 월별 수익률 바 차트
    ax_monthly = fig_monthly.add_subplot(2, 1, 1)
    colors = ['green' if x >= 0 else 'red' for x in monthly_returns]
    ax_monthly.bar(range(len(monthly_returns)), monthly_returns, color=colors, alpha=0.7)
    ax_monthly.set_title('월별 수익률', fontsize=12)
    ax_monthly.set_ylabel('수익률 (%)')
    ax_monthly.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax_monthly.grid(True, alpha=0.3, axis='y')
    
    # x축 레이블 설정 (너무 많으면 일부만 표시)
    tick_positions = range(0, len(monthly_returns), max(1, len(monthly_returns) // 12))
    tick_labels = [monthly_returns.index[i].strftime('%Y-%m') for i in tick_positions]
    ax_monthly.set_xticks(list(tick_positions))
    ax_monthly.set_xticklabels(tick_labels, rotation=45, ha='right')
    
    # 연도별 수익률 바 차트
    ax_yearly = fig_monthly.add_subplot(2, 1, 2)
    colors_yearly = ['green' if x >= 0 else 'red' for x in yearly_returns]
    bars = ax_yearly.bar([str(d.year) for d in yearly_returns.index], yearly_returns, color=colors_yearly, alpha=0.7)
    ax_yearly.set_title('연도별 수익률', fontsize=12)
    ax_yearly.set_xlabel('연도')
    ax_yearly.set_ylabel('수익률 (%)')
    ax_yearly.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax_yearly.grid(True, alpha=0.3, axis='y')
    
    # 바 위에 수치 표시
    for bar, val in zip(bars, yearly_returns):
        ax_yearly.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                       f'{val:.1f}%', ha='center', va='bottom', fontsize=9)
    
    fig_monthly.tight_layout()
    
    canvas_monthly = FigureCanvasTkAgg(fig_monthly, master=tab_monthly)
    canvas_monthly.draw()
    canvas_monthly.get_tk_widget().pack(fill='both', expand=True)
    
    # 윈도우 실행
    root.mainloop()


def plot_results(daily_df, mdd):
    """잔액 및 MDD 차트 출력"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 잔액 차트
    axes[0].plot(daily_df.index, daily_df['balance'], label='Balance', color='blue')
    axes[0].set_title('Portfolio Balance (Cycle-based)', fontsize=14)
    axes[0].set_xlabel('Date')
    axes[0].set_ylabel('Balance (USDT)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # MDD 차트
    axes[1].fill_between(daily_df.index, daily_df['drawdown'], 0, 
                         color='red', alpha=0.3, label='Drawdown')
    axes[1].set_title(f'Drawdown Chart (MDD: {mdd:.2f}%)', fontsize=14)
    axes[1].set_xlabel('Date')
    axes[1].set_ylabel('Drawdown (%)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()


# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == '__main__':
    print("=" * 70)
    print("골든크로스/데드크로스 롱숏 전략 백테스팅 (사이클 기반)")
    print("=" * 70)
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"타임프레임: {TIMEFRAME}")
    print(f"레버리지: {LEVERAGE}배")
    print(f"이동평균: {SHORT_MA} / {LONG_MA}")
    print(f"일봉 MA 필터: {DAILY_MA}일")
    print(f"부분 익절: {'활성화' if TAKE_PROFIT_ENABLED else '비활성화'}")
    if TAKE_PROFIT_ENABLED:
        for tp in TAKE_PROFIT_LEVELS:
            print(f"  - {tp['profit_pct']}% 수익 시 {tp['sell_pct']}% 익절")
    print(f"종목: {len(COIN_LIST)}개")
    for coin in COIN_LIST:
        print(f"  - {coin}")
    print("=" * 70)
    print("\n[!] 사이클 자금 관리:")
    print(f"  - 사이클 시작 시 잔액을 {len(COIN_LIST)}등분하여 코인당 할당")
    print(f"  - 사이클 중 진입 시 할당된 금액으로 진입 (잔액 변동 무관)")
    print(f"  - 모든 포지션 청산 시 사이클 종료 → 새 사이클에서 재분배")
    print("=" * 70)
    
    # 통합 백테스트 객체 생성
    backtest = IntegratedBacktest(
        coin_list=COIN_LIST,
        initial_capital=INITIAL_CAPITAL,
        leverage=LEVERAGE,
        short_ma=SHORT_MA,
        long_ma=LONG_MA,
        daily_ma=DAILY_MA
    )
    
    # 데이터 로드
    print("\n[*] 데이터 로딩 중...")
    for symbol in COIN_LIST:
        safe_name = symbol.replace('/', '_').replace(':', '_').lower()
        coin_name = safe_name.split('_')[0]
        
        json_file = f"{DATA_PATH}\\{coin_name}_usdt_bitget_{TIMEFRAME}.json"
        daily_json_file = f"{DATA_PATH}\\{coin_name}_usdt_bitget_1d.json"
        
        try:
            backtest.load_data(symbol, json_file, daily_json_file, START_DATE, END_DATE)
        except FileNotFoundError as e:
            print(f"  {symbol}: 파일을 찾을 수 없습니다 - {e}")
    
    # 백테스트 실행
    print("\n" + "=" * 70)
    print("[>] 백테스트 실행 중...")
    print("=" * 70)
    
    results = backtest.run_backtest()
    
    # 결과 분석
    daily_df, mdd, cycle_mdd, coin_stats, trades = analyze_results(results)
    
    # 탭으로 차트 출력
    if daily_df is not None and not daily_df.empty:
        plot_results_with_tabs(daily_df, mdd, cycle_mdd, coin_stats, trades, INITIAL_CAPITAL)
