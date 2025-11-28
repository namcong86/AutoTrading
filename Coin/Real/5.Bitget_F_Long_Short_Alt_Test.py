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

# ==============================================================================
# 백테스트 설정
# ==============================================================================
INITIAL_CAPITAL = 10000      # 초기 자본금 (USDT)
LEVERAGE = 1.2                  # 레버리지 배수
SHORT_MA = 20                 # 단기 이동평균 기간
LONG_MA = 120                 # 장기 이동평균 기간
DAILY_MA = 120                # 일봉 이동평균 기간 (방향 필터용)
TIMEFRAME = '1h'              # 캔들 타임프레임 ('1h' 또는 '15m')
FEE_RATE = 0.0006             # 거래 수수료 (0.06%)

# 익절 설정 (전캔들 기준, 각 조건당 한번씩만 적용)
TAKE_PROFIT_LEVELS = [
    {'profit_pct': 3, 'sell_pct': 10},   # 3% 수익 시 10% 익절
    {'profit_pct': 5, 'sell_pct': 20},   # 5% 수익 시 나머지의 20% 익절
    {'profit_pct': 10, 'sell_pct': 30},  # 10% 수익 시 나머지의 30% 익절
]

# 테스트 기간
START_DATE = '2021-07-01'
END_DATE = '2025-11-20'

# 코인 리스트 (JSON 파일 기준) - 자금은 사이클 시작 시 1/N 분배
COIN_LIST = [
    'ADA/USDT:USDT',
    'DOGE/USDT:USDT',
    'SOL/USDT:USDT',
    'BNB/USDT:USDT',


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
        
        invest_amount = self.cycle_allocation * leverage
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
              f"진입가 ${price:.6f}, 할당금액 ${self.cycle_allocation:.2f} USDT "
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
    
    def check_take_profit(self, symbol, prev_close, timestamp, leverage, tp_levels):
        """익절 조건 체크 - 전캔들 종가 기준"""
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
        return {
            'initial_capital': initial_capital,
            'final_balance': self.available_balance,
            'total_return': (self.available_balance - initial_capital) / initial_capital * 100,
            'total_cycles': self.cycle_num,
            'trades': self.trades,
            'daily_balance': pd.DataFrame(self.daily_balance),
            'cycle_history': self.cycle_history
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
        """코인별 데이터 로드 및 시그널 계산"""
        # 메인 데이터 로드
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        df = df[(df.index >= start_date) & (df.index <= end_date)]
        df['symbol'] = symbol
        
        # 이동평균 계산
        df['ma_short'] = df['close'].rolling(window=self.short_ma).mean()
        df['ma_long'] = df['close'].rolling(window=self.long_ma).mean()
        
        # 크로스 감지
        df['prev_ma_short'] = df['ma_short'].shift(1)
        df['prev_ma_long'] = df['ma_long'].shift(1)
        df['golden_cross'] = (df['prev_ma_short'] <= df['prev_ma_long']) & (df['ma_short'] > df['ma_long'])
        df['dead_cross'] = (df['prev_ma_short'] >= df['prev_ma_long']) & (df['ma_short'] < df['ma_long'])
        
        self.coin_data[symbol] = df
        
        # 일봉 데이터 로드
        try:
            with open(daily_json_path, 'r') as f:
                daily_data = json.load(f)
            
            df_daily = pd.DataFrame(daily_data)
            df_daily['datetime'] = pd.to_datetime(df_daily['datetime'])
            df_daily.set_index('datetime', inplace=True)
            df_daily['daily_ma'] = df_daily['close'].rolling(window=self.daily_ma).mean()
            self.coin_daily[symbol] = df_daily
            print(f"  {symbol}: {len(df)}개 캔들, 일봉 {self.daily_ma}MA 필터 적용")
        except FileNotFoundError:
            self.coin_daily[symbol] = None
            print(f"  {symbol}: {len(df)}개 캔들, 일봉 데이터 없음 (양방향 허용)")
        
        return df
    
    def get_daily_trend(self, symbol, timestamp):
        """일봉 기준 추세 확인"""
        if symbol not in self.coin_daily or self.coin_daily[symbol] is None:
            return 'both'
        
        df_daily = self.coin_daily[symbol]
        date_only = timestamp.date()
        daily_data = df_daily[df_daily.index.date <= date_only]
        
        if daily_data.empty or pd.isna(daily_data['daily_ma'].iloc[-1]):
            return 'both'
        
        last_close = daily_data['close'].iloc[-1]
        last_ma = daily_data['daily_ma'].iloc[-1]
        
        return 'long' if last_close > last_ma else 'short'
    
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
            
            # 익절 체크 (포지션이 있고, 전캔들 종가가 있는 경우)
            if current_pos and pd.notna(prev_close):
                self.cycle_mgr.check_take_profit(symbol, prev_close, timestamp, self.leverage, TAKE_PROFIT_LEVELS)
                # 익절 후 포지션 재확인 (물량이 0이 됐을 수 있음)
                current_pos = self.cycle_mgr.get_position(symbol)
            
            # 일봉 추세 확인
            daily_trend = self.get_daily_trend(symbol, timestamp)
            
            # 골든크로스 - 롱 진입 (숏 청산 후)
            if candle['golden_cross']:
                if current_pos and current_pos['direction'] == 'short':
                    self.cycle_mgr.close_position(symbol, close, timestamp, self.leverage)
                    current_pos = None
                
                if current_pos is None and daily_trend in ['long', 'both']:
                    self.cycle_mgr.open_position(symbol, 'long', close, timestamp, self.leverage, current_prices)
            
            # 데드크로스 - 숏 진입 (롱 청산 후)
            elif candle['dead_cross']:
                if current_pos and current_pos['direction'] == 'long':
                    self.cycle_mgr.close_position(symbol, close, timestamp, self.leverage)
                    current_pos = None
                
                if current_pos is None and daily_trend in ['short', 'both']:
                    self.cycle_mgr.open_position(symbol, 'short', close, timestamp, self.leverage, current_prices)
            
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
    
    # MDD 계산
    daily_df['peak'] = daily_df['balance'].cummax()
    daily_df['drawdown'] = (daily_df['balance'] - daily_df['peak']) / daily_df['peak'] * 100
    mdd = daily_df['drawdown'].min()
    
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
    print(f"총 수익률: {results['total_return']:.2f}%")
    print(f"최대 낙폭 (MDD): {mdd:.2f}%")
    print(f"총 사이클 수: {results['total_cycles']}회")
    print(f"총 거래 횟수: {total_trades}회")
    print(f"승률: {win_rate:.2f}% (승: {win_trades}회, 패: {lose_trades}회)")
    
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
    for date, ret in monthly_returns.dropna().items():
        print(f"{date.strftime('%Y-%m')}: {ret:+.2f}%")
    
    print("\n" + "=" * 70)
    print("[연도별] 연도별 수익률")
    print("=" * 70)
    for date, ret in yearly_returns.items():
        print(f"{date.year}년: {ret:+.2f}%")
    
    return daily_df, mdd, coin_stats, trades


def plot_results_with_tabs(daily_df, mdd, coin_stats, trades, initial_capital):
    """탭으로 결과 표시 (전체 + 코인별)"""
    
    # Tkinter 윈도우 생성
    root = tk.Tk()
    root.title("백테스트 결과 분석")
    root.geometry("1400x900")
    
    # 한글 폰트 설정
    try:
        plt.rc('font', family='Malgun Gothic')
    except:
        plt.rc('font', family='AppleGothic')
    plt.rcParams['axes.unicode_minus'] = False
    
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
    
    # MDD 차트
    ax2 = fig_total.add_subplot(2, 1, 2)
    ax2.fill_between(daily_df.index, daily_df['drawdown'], 0, color='red', alpha=0.3, label='Drawdown')
    ax2.plot(daily_df.index, daily_df['drawdown'], color='red', linewidth=0.8)
    ax2.set_title(f'최대 낙폭 (MDD: {mdd:.2f}%)', fontsize=12)
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
    daily_df, mdd, coin_stats, trades = analyze_results(results)
    
    # 탭으로 차트 출력
    if daily_df is not None and not daily_df.empty:
        plot_results_with_tabs(daily_df, mdd, coin_stats, trades, INITIAL_CAPITAL)
