# -*- coding:utf-8 -*-
'''
골든크로스/데드크로스 롱숏 전략 백테스팅
- 1시간봉 기준 20이평, 120이평 크로스 매매
- 골든크로스: 롱 진입 (숏 청산)
- 데드크로스: 숏 진입 (롱 청산)
- 5분할 진입, 청산은 일괄
'''
import pandas as pd
import numpy as np
import json
import os
import matplotlib.pyplot as plt
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# 설정
# ==============================================================================
# 투자 코인 리스트 (json 파일명과 매칭)
INVEST_COIN_LIST = [
    {'ticker': 'ADA/USDT:USDT', 'json_file': 'ada_usdt_bitget_1h.json'},
    # 추가 코인은 여기에 추가
    # {'ticker': 'DOGE/USDT:USDT', 'json_file': 'doge_usdt_bitget_1h.json'},
]

# 백테스트 설정
INITIAL_CAPITAL = 10000  # 초기 자본금 (USDT)
LEVERAGE = 1             # 레버리지 (1~10 설정 가능)
FEE_RATE = 0.0006        # 수수료율 (0.06%)
SPLIT_COUNT = 5          # 분할 진입 횟수

# 이동평균 설정
SHORT_MA = 20            # 단기 이동평균
LONG_MA = 120            # 장기 이동평균

# 백테스트 기간
START_DATE = '2021-01-01'
END_DATE = '2025-11-20'

# JSON 파일 경로
JSON_PATH = os.path.join(os.path.dirname(__file__), '..', 'json')


# ==============================================================================
# 데이터 로드 함수
# ==============================================================================
def load_json_data(json_file):
    """JSON 파일에서 OHLCV 데이터 로드"""
    file_path = os.path.join(JSON_PATH, json_file)
    if not os.path.exists(file_path):
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return pd.DataFrame()
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.set_index('datetime', inplace=True)
    df = df.sort_index()
    return df


# ==============================================================================
# 백테스트 클래스
# ==============================================================================
class GoldenDeadCrossBacktest:
    def __init__(self, df, ticker, initial_capital, leverage, fee_rate, split_count, short_ma, long_ma):
        self.df = df.copy()
        self.ticker = ticker
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.leverage = leverage
        self.fee_rate = fee_rate
        self.split_count = split_count
        self.short_ma = short_ma
        self.long_ma = long_ma
        
        # 포지션 상태
        self.position = 0  # 1: 롱, -1: 숏, 0: 없음
        self.position_size = 0  # 보유 수량
        self.entry_price = 0  # 진입가
        self.entry_count = 0  # 분할 진입 횟수
        self.allocated_capital = 0  # 이 코인에 배정된 자본
        
        # 거래 기록
        self.trades = []
        self.daily_balance = []
        
    def calculate_indicators(self):
        """이동평균 계산"""
        self.df[f'ma_{self.short_ma}'] = self.df['close'].rolling(self.short_ma).mean()
        self.df[f'ma_{self.long_ma}'] = self.df['close'].rolling(self.long_ma).mean()
        self.df.dropna(inplace=True)
        
    def check_golden_cross(self, i):
        """골든크로스 확인 (단기 이평이 장기 이평 상향 돌파)"""
        if i < 1:
            return False
        prev_short = self.df[f'ma_{self.short_ma}'].iloc[i-1]
        prev_long = self.df[f'ma_{self.long_ma}'].iloc[i-1]
        curr_short = self.df[f'ma_{self.short_ma}'].iloc[i]
        curr_long = self.df[f'ma_{self.long_ma}'].iloc[i]
        
        return prev_short <= prev_long and curr_short > curr_long
    
    def check_dead_cross(self, i):
        """데드크로스 확인 (단기 이평이 장기 이평 하향 돌파)"""
        if i < 1:
            return False
        prev_short = self.df[f'ma_{self.short_ma}'].iloc[i-1]
        prev_long = self.df[f'ma_{self.long_ma}'].iloc[i-1]
        curr_short = self.df[f'ma_{self.short_ma}'].iloc[i]
        curr_long = self.df[f'ma_{self.long_ma}'].iloc[i]
        
        return prev_short >= prev_long and curr_short < curr_long
    
    def open_position(self, side, price, timestamp):
        """포지션 진입 (분할 진입)"""
        if self.entry_count >= self.split_count:
            return
        
        # 분할 진입 금액 계산
        split_capital = (self.allocated_capital / self.split_count) * self.leverage
        fee = split_capital * self.fee_rate
        actual_capital = split_capital - fee
        
        # 수량 계산
        amount = actual_capital / price
        
        # 평균 진입가 계산
        if self.position_size == 0:
            self.entry_price = price
        else:
            total_value = self.entry_price * self.position_size + price * amount
            self.position_size += amount
            self.entry_price = total_value / self.position_size
            amount = self.position_size - (self.position_size - amount)  # 이번에 추가된 수량
        
        self.position_size += amount if self.entry_count == 0 else 0
        if self.entry_count == 0:
            self.position_size = amount
        
        self.position = 1 if side == 'long' else -1
        self.entry_count += 1
        
        # 자본금 차감
        self.capital -= (split_capital / self.leverage)
        
        side_str = "롱" if side == 'long' else "숏"
        print(f"[{timestamp}] {self.ticker} {side_str} 진입 ({self.entry_count}/{self.split_count}): "
              f"진입가 ${price:.6f}, 수량 {amount:.4f}, 금액 ${split_capital:.2f} USDT")
        
        self.trades.append({
            'timestamp': timestamp,
            'ticker': self.ticker,
            'side': side,
            'action': 'entry',
            'price': price,
            'amount': amount,
            'usdt_value': split_capital,
            'fee': fee,
            'entry_count': self.entry_count
        })
    
    def close_position(self, price, timestamp):
        """포지션 청산 (일괄)"""
        if self.position == 0:
            return 0
        
        # 수익/손실 계산
        if self.position == 1:  # 롱
            pnl = (price - self.entry_price) * self.position_size * self.leverage
            side_str = "롱"
        else:  # 숏
            pnl = (self.entry_price - price) * self.position_size * self.leverage
            side_str = "숏"
        
        # 수수료 차감
        close_value = self.position_size * price * self.leverage
        fee = close_value * self.fee_rate
        net_pnl = pnl - fee
        
        # 수익률 계산
        invested = self.allocated_capital * (self.entry_count / self.split_count)
        revenue_rate = (net_pnl / invested) * 100 if invested > 0 else 0
        
        # 자본금 반영
        returned_capital = invested + net_pnl
        self.capital += returned_capital
        
        print(f"[{timestamp}] {self.ticker} {side_str} 청산: "
              f"청산가 ${price:.6f}, 수량 {self.position_size:.4f}, "
              f"수익률 {revenue_rate:.2f}%, 수익금 ${net_pnl:.2f} USDT")
        
        self.trades.append({
            'timestamp': timestamp,
            'ticker': self.ticker,
            'side': 'long' if self.position == 1 else 'short',
            'action': 'close',
            'price': price,
            'amount': self.position_size,
            'usdt_value': close_value,
            'fee': fee,
            'pnl': net_pnl,
            'revenue_rate': revenue_rate
        })
        
        # 포지션 초기화
        old_position = self.position
        self.position = 0
        self.position_size = 0
        self.entry_price = 0
        self.entry_count = 0
        
        return net_pnl
    
    def run_backtest(self, start_date, end_date):
        """백테스트 실행"""
        self.calculate_indicators()
        
        # 기간 필터링
        mask = (self.df.index >= start_date) & (self.df.index <= end_date)
        df_filtered = self.df[mask]
        
        if len(df_filtered) == 0:
            print(f"해당 기간에 데이터가 없습니다.")
            return
        
        # 코인에 배정된 자본금
        self.allocated_capital = self.initial_capital / len(INVEST_COIN_LIST)
        
        print(f"\n{'='*60}")
        print(f"백테스트 시작: {self.ticker}")
        print(f"기간: {start_date} ~ {end_date}")
        print(f"데이터 수: {len(df_filtered)}개")
        print(f"배정 자본금: ${self.allocated_capital:.2f} USDT")
        print(f"레버리지: {self.leverage}배")
        print(f"이동평균: {self.short_ma} / {self.long_ma}")
        print(f"{'='*60}\n")
        
        current_date = None
        
        for i in range(len(df_filtered)):
            timestamp = df_filtered.index[i]
            price = df_filtered['close'].iloc[i]
            
            # 일별 잔액 기록 (일자가 바뀔 때마다)
            date_only = timestamp.date()
            if current_date != date_only:
                # 현재 포지션의 평가 금액 계산
                if self.position != 0:
                    if self.position == 1:  # 롱
                        unrealized_pnl = (price - self.entry_price) * self.position_size * self.leverage
                    else:  # 숏
                        unrealized_pnl = (self.entry_price - price) * self.position_size * self.leverage
                    invested = self.allocated_capital * (self.entry_count / self.split_count)
                    position_value = invested + unrealized_pnl
                else:
                    position_value = 0
                    unrealized_pnl = 0
                
                total_balance = self.capital + position_value
                
                self.daily_balance.append({
                    'date': date_only,
                    'balance': total_balance,
                    'cash': self.capital,
                    'position_value': position_value
                })
                current_date = date_only
            
            # 골든크로스 확인 - 롱 진입
            if self.check_golden_cross(i):
                # 숏 포지션이면 청산
                if self.position == -1:
                    self.close_position(price, timestamp)
                
                # 롱 진입
                if self.position == 0:
                    self.open_position('long', price, timestamp)
            
            # 데드크로스 확인 - 숏 진입
            elif self.check_dead_cross(i):
                # 롱 포지션이면 청산
                if self.position == 1:
                    self.close_position(price, timestamp)
                
                # 숏 진입
                if self.position == 0:
                    self.open_position('short', price, timestamp)
            
            # 분할 진입 (이미 포지션이 있고 아직 분할 진입이 완료되지 않은 경우)
            # 여기서는 크로스 발생 시에만 진입하도록 함 (추후 조건 추가 가능)
        
        # 마지막 포지션 청산
        if self.position != 0:
            last_price = df_filtered['close'].iloc[-1]
            last_timestamp = df_filtered.index[-1]
            self.close_position(last_price, last_timestamp)
        
        return self.trades, self.daily_balance


# ==============================================================================
# 결과 분석 함수
# ==============================================================================
def analyze_results(all_trades, all_daily_balance, initial_capital):
    """백테스트 결과 분석"""
    if not all_daily_balance:
        print("분석할 데이터가 없습니다.")
        return
    
    # 일별 잔액 DataFrame
    df_balance = pd.DataFrame(all_daily_balance)
    df_balance['date'] = pd.to_datetime(df_balance['date'])
    df_balance = df_balance.groupby('date')['balance'].sum().reset_index()
    df_balance.set_index('date', inplace=True)
    
    # MDD 계산
    df_balance['peak'] = df_balance['balance'].cummax()
    df_balance['drawdown'] = (df_balance['balance'] - df_balance['peak']) / df_balance['peak'] * 100
    df_balance['mdd'] = df_balance['drawdown'].cummin()
    
    # 월별/연도별 수익률
    df_balance['year'] = df_balance.index.year
    df_balance['month'] = df_balance.index.month
    df_balance['year_month'] = df_balance.index.to_period('M')
    
    # 월별 수익률 계산
    monthly_returns = df_balance.groupby('year_month')['balance'].last().pct_change() * 100
    
    # 연도별 수익률 계산
    yearly_returns = df_balance.groupby('year')['balance'].last().pct_change() * 100
    
    # 결과 출력
    print(f"\n{'='*60}")
    print("📊 백테스트 결과 요약")
    print(f"{'='*60}")
    print(f"초기 자본금: ${initial_capital:,.2f} USDT")
    print(f"최종 잔액: ${df_balance['balance'].iloc[-1]:,.2f} USDT")
    print(f"총 수익률: {((df_balance['balance'].iloc[-1] / initial_capital) - 1) * 100:.2f}%")
    print(f"최대 낙폭 (MDD): {df_balance['mdd'].min():.2f}%")
    print(f"총 거래 횟수: {len([t for t in all_trades if t['action'] == 'close'])}회")
    
    print(f"\n{'='*60}")
    print("📅 월별 수익률")
    print(f"{'='*60}")
    for period, ret in monthly_returns.items():
        if pd.notna(ret):
            print(f"{period}: {ret:+.2f}%")
    
    print(f"\n{'='*60}")
    print("📅 연도별 수익률")
    print(f"{'='*60}")
    for year, ret in yearly_returns.items():
        if pd.notna(ret):
            print(f"{year}년: {ret:+.2f}%")
    
    return df_balance


def plot_results(df_balance, initial_capital):
    """결과 차트 출력"""
    fig, axes = plt.subplots(2, 1, figsize=(14, 10))
    
    # 잔액 변동 차트
    ax1 = axes[0]
    ax1.plot(df_balance.index, df_balance['balance'], label='Balance', color='blue', linewidth=1.5)
    ax1.axhline(y=initial_capital, color='gray', linestyle='--', label='Initial Capital')
    ax1.fill_between(df_balance.index, initial_capital, df_balance['balance'], 
                     where=(df_balance['balance'] >= initial_capital), 
                     color='green', alpha=0.3, label='Profit')
    ax1.fill_between(df_balance.index, initial_capital, df_balance['balance'], 
                     where=(df_balance['balance'] < initial_capital), 
                     color='red', alpha=0.3, label='Loss')
    ax1.set_title('Balance Over Time', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date')
    ax1.set_ylabel('Balance (USDT)')
    ax1.legend(loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # MDD 차트
    ax2 = axes[1]
    ax2.fill_between(df_balance.index, 0, df_balance['drawdown'], color='red', alpha=0.5)
    ax2.plot(df_balance.index, df_balance['drawdown'], color='darkred', linewidth=1)
    ax2.set_title('Drawdown Over Time', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Drawdown (%)')
    ax2.grid(True, alpha=0.3)
    
    # MDD 최저점 표시
    mdd_min_idx = df_balance['drawdown'].idxmin()
    mdd_min_val = df_balance['drawdown'].min()
    ax2.annotate(f'MDD: {mdd_min_val:.2f}%', 
                 xy=(mdd_min_idx, mdd_min_val),
                 xytext=(mdd_min_idx, mdd_min_val - 5),
                 fontsize=10, color='darkred',
                 arrowprops=dict(arrowstyle='->', color='darkred'))
    
    plt.tight_layout()
    plt.show()


# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == '__main__':
    print("="*60)
    print("골든크로스/데드크로스 롱숏 전략 백테스팅")
    print(f"기간: {START_DATE} ~ {END_DATE}")
    print(f"레버리지: {LEVERAGE}배")
    print(f"이동평균: {SHORT_MA} / {LONG_MA}")
    print("="*60)
    
    all_trades = []
    all_daily_balance = []
    
    for coin_info in INVEST_COIN_LIST:
        ticker = coin_info['ticker']
        json_file = coin_info['json_file']
        
        # 데이터 로드
        df = load_json_data(json_file)
        if df.empty:
            print(f"{ticker} 데이터 로드 실패, 건너뜁니다.")
            continue
        
        # 백테스트 실행
        backtest = GoldenDeadCrossBacktest(
            df=df,
            ticker=ticker,
            initial_capital=INITIAL_CAPITAL,
            leverage=LEVERAGE,
            fee_rate=FEE_RATE,
            split_count=SPLIT_COUNT,
            short_ma=SHORT_MA,
            long_ma=LONG_MA
        )
        
        trades, daily_balance = backtest.run_backtest(START_DATE, END_DATE)
        all_trades.extend(trades)
        all_daily_balance.extend(daily_balance)
    
    # 결과 분석
    df_balance = analyze_results(all_trades, all_daily_balance, INITIAL_CAPITAL)
    
    # 차트 출력
    if df_balance is not None and len(df_balance) > 0:
        plot_results(df_balance, INITIAL_CAPITAL)
