# -*- coding:utf-8 -*-
'''
파일이름: 4.GateIO_F_Grid_Danta_Test.py
설명: 볼린저밴드와 RSI를 이용한 그리드 매매 전략 (백테스트용)
'''
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt

# --- 백테스트 설정 ---
TEST_START_DATE = datetime.datetime(2024, 1, 1) # 시작일
TEST_END_DATE = datetime.datetime.now()         # 종료일 (현재)
INITIAL_CAPITAL = 10000     # 시작 자본 (USDT)
TIMEFRAME = '5m'            # 5분봉 데이터 사용 
LEVERAGE = 10               # 레버리지 
STOP_LOSS_PNL_RATE = -0.5   # 손절 PNL 비율 (-50%) 
INVEST_COIN_LIST = ['DOGE/USDT', 'PEPE/USDT'] # 백테스트할 코인 목록 (뒤에 :USDT 제외)
FEE_RATE = 0.0005           # 거래 수수료 (시장가 0.05% 가정)

# --- CCXT 객체 (데이터 다운로드용) ---
exchange = ccxt.gateio()

# ==============================================================================
# 데이터 로더 및 지표 계산 (운영용 코드와 동일 로직)
# ==============================================================================
def fetch_all_ohlcv(ticker, timeframe, start_date, end_date):
    """지정된 기간의 모든 OHLCV 데이터를 가져옵니다."""
    all_ohlcv = []
    since = int(start_date.timestamp() * 1000)
    end_ms = int(end_date.timestamp() * 1000)
    
    while since < end_ms:
        try:
            ohlcv = exchange.fetch_ohlcv(ticker, timeframe, since, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + (exchange.parse_timeframe(timeframe) * 1000)
            print(f"{ticker} 데이터 다운로드 중... 마지막 날짜: {datetime.datetime.fromtimestamp(ohlcv[-1][0]/1000)}")
            time.sleep(exchange.rateLimit / 1000)
        except Exception as e:
            print(f"데이터 다운로드 오류: {e}")
            break
            
    df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df = df.drop_duplicates(subset='timestamp', keep='first')
    df = df.set_index('timestamp')
    return df

def calculate_indicators(df):
    """DataFrame에 보조지표를 추가합니다."""
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bb_upper'] = df['ma30'] + 2 * df['stddev']
    df['bb_lower'] = df['ma30'] - 2 * df['stddev']
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=13, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df = df.dropna()
    return df

def get_rsi_level(rsi_value):
    if 20 < rsi_value <= 25: return 1
    if 15 < rsi_value <= 20: return 2
    if 10 < rsi_value <= 15: return 3
    if rsi_value <= 10: return 4
    return 0

def get_buy_amount(base_amount, rsi_level, entry_count):
    rsi_multiplier = 1.0
    if rsi_level == 2: rsi_multiplier = 1.1
    elif rsi_level == 3: rsi_multiplier = 1.2
    elif rsi_level == 4: rsi_multiplier = 1.3
    amount = base_amount * rsi_multiplier
    entry_multiplier = 1.0
    if 4 <= entry_count <= 6: entry_multiplier = 1.2
    elif 7 <= entry_count <= 10: entry_multiplier = 1.3
    return amount * entry_multiplier

# ==============================================================================
# 백테스팅 엔진
# ==============================================================================
def run_backtest():
    print("백테스트를 시작합니다...")
    
    # 1. 데이터 로드 및 전처리
    dfs = {}
    for ticker in INVEST_COIN_LIST:
        print(f"--- {ticker} 데이터 준비 중 ---")
        df = fetch_all_ohlcv(ticker, TIMEFRAME, TEST_START_DATE, TEST_END_DATE)
        if not df.empty:
            dfs[ticker] = calculate_indicators(df)
    
    if not dfs:
        print("백테스트를 위한 데이터가 없습니다. 종료합니다.")
        return

    # 모든 코인의 데이터가 있는 공통 날짜만 사용
    common_index = None
    for ticker in dfs.keys():
        if common_index is None:
            common_index = dfs[ticker].index
        else:
            common_index = common_index.intersection(dfs[ticker].index)
            
    print(f"공통 데이터 기간: {common_index.min()} ~ {common_index.max()}")

    # 2. 변수 초기화
    cash = INITIAL_CAPITAL
    portfolio_value = [INITIAL_CAPITAL]
    
    # 코인별 상태 관리 (JSON 파일 시뮬레이션)
    positions = {}
    for ticker in INVEST_COIN_LIST:
        allocated_asset = INITIAL_CAPITAL / len(INVEST_COIN_LIST)
        base_buy_amount = allocated_asset * 0.01
        positions[ticker] = {
            "base_buy_amount": base_buy_amount,
            "current_entry_count": 0,
            "average_price": 0.0,
            "total_quantity": 0.0,
            "total_collateral": 0.0,
            "final_buy_time": None,
            "entries": [] # { "entry": int, "price": float, "quantity": float, "timestamp": datetime }
        }

    # 3. 백테스팅 루프
    for i in range(1, len(common_index)):
        if i < 30: continue # 지표 계산을 위한 최소 기간 확보
        
        current_time = common_index[i]
        
        current_total_value = cash
        
        for ticker in INVEST_COIN_LIST:
            df = dfs[ticker].loc[:current_time]
            if len(df) < 2: continue
            
            prev_candle = df.iloc[-2]
            now_price = df['close'].iloc[-1]
            
            pos = positions[ticker]
            
            # 포지션 가치 평가 (Mark to Market)
            if pos['total_quantity'] > 0:
                unrealized_pnl = (now_price - pos['average_price']) * pos['total_quantity'] * LEVERAGE
                current_total_value += (pos['total_collateral'] + unrealized_pnl)

            # --- 로직 시작 ---
            # 1. 손절 조건 확인
            if pos['total_collateral'] > 0 and (unrealized_pnl / pos['total_collateral']) <= STOP_LOSS_PNL_RATE:
                print(f"[{current_time}] 🚨 {ticker} 손절매 실행. PNL: {unrealized_pnl:.2f}")
                cash += (pos['total_collateral'] + unrealized_pnl)
                cash -= pos['total_collateral'] * FEE_RATE # 매도 수수료
                
                # 포지션 리셋 및 기준금 재산정
                allocated_asset = cash / len(INVEST_COIN_LIST)
                pos['base_buy_amount'] = allocated_asset * 0.01
                pos.update({
                    "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0, 
                    "total_collateral": 0.0, "final_buy_time": None, "entries": []
                })
                continue

            # 2. 매도 조건 확인
            sold_in_this_step = False
            if pos['current_entry_count'] > 0:
                # 30MA 상향 돌파
                if prev_candle['open'] < prev_candle['ma30'] and prev_candle['close'] > prev_candle['ma30']:
                    entries_to_sell = [(idx, e) for idx, e in enumerate(pos['entries']) if e['price'] < prev_candle['ma30']]
                    if entries_to_sell:
                        print(f"[{current_time}] 💰 {ticker} 부분 익절 (30MA 돌파)")
                        sold_in_this_step = True
                # BB 상단 돌파
                elif prev_candle['close'] > prev_candle['bb_upper']:
                    if now_price > pos['average_price']:
                        print(f"[{current_time}] 💰 {ticker} 전체 익절 (BB 상단 돌파)")
                        # 전체 매도이므로 모든 엔트리
                        entries_to_sell = list(enumerate(pos['entries']))
                        sold_in_this_step = True
                    else:
                        entries_to_sell = [(idx, e) for idx, e in enumerate(pos['entries']) if now_price > e['price']]
                        if entries_to_sell:
                            print(f"[{current_time}] 💰 {ticker} 부분 익절 (BB 상단, 개별)")
                            sold_in_this_step = True

                if sold_in_this_step:
                    # 매도 처리
                    total_sell_qty = sum(e['quantity'] for idx, e in entries_to_sell)
                    total_sell_value = total_sell_qty * now_price
                    total_pnl = 0
                    
                    indices_to_remove = [idx for idx, e in entries_to_sell]
                    indices_to_remove.sort(reverse=True)
                    
                    removed_collateral = 0
                    for idx in indices_to_remove:
                        entry = pos['entries'][idx]
                        pnl = (now_price - entry['price']) * entry['quantity'] * LEVERAGE
                        total_pnl += pnl
                        removed_collateral += (entry['price'] * entry['quantity'])
                        del pos['entries'][idx]

                    cash += removed_collateral + total_pnl
                    cash -= (removed_collateral + total_pnl) * FEE_RATE
                    pos['total_collateral'] -= removed_collateral

                    # 남은 엔트리 재정렬
                    for entry_idx, entry_data in enumerate(pos['entries']):
                        entry_data['entry'] = entry_idx + 1
                    
                    pos['current_entry_count'] = len(pos['entries'])
                    
                    if pos['current_entry_count'] == 0:
                        # 포지션 완전 종료 시 리셋
                        allocated_asset = cash / len(INVEST_COIN_LIST)
                        pos['base_buy_amount'] = allocated_asset * 0.01
                        pos.update({"average_price": 0.0, "total_quantity": 0.0, "total_collateral": 0.0, "final_buy_time": None})
                    else:
                        # 부분 종료 시 평균단가 재계산
                        new_total_value = sum(e['price'] * e['quantity'] for e in pos['entries'])
                        new_total_qty = sum(e['quantity'] for e in pos['entries'])
                        pos['total_quantity'] = new_total_qty
                        pos['average_price'] = new_total_value / new_total_qty if new_total_qty > 0 else 0
                
                continue # 매도 후에는 매수 로직 건너뜀

            # 3. 매수 조건 확인
            if pos['current_entry_count'] < 10:
                base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
                should_buy = False
                
                if base_buy_cond:
                    if pos['current_entry_count'] == 0:
                        should_buy = True
                    else:
                        last_buy_time = pos.get('final_buy_time')
                        if last_buy_time:
                            candles_after_buy = df[df.index > last_buy_time]
                            if not candles_after_buy.empty and (candles_after_buy['rsi'] > 25).any():
                                should_buy = True
                        
                        if not should_buy:
                            last_entry_time = pos['final_buy_time']
                            last_entry_rsi = df.loc[last_entry_time]['rsi']
                            last_entry_rsi_level = get_rsi_level(last_entry_rsi)
                            current_rsi_level = get_rsi_level(prev_candle['rsi'])
                            if current_rsi_level > last_entry_rsi_level:
                                should_buy = True

                if should_buy:
                    # 매수 처리
                    rsi_level = get_rsi_level(prev_candle['rsi'])
                    buy_amount_usd = get_buy_amount(pos['base_buy_amount'], rsi_level, pos['current_entry_count'] + 1)
                    
                    if cash >= buy_amount_usd:
                        print(f"[{current_time}] 📈 {ticker} 신규 매수 ({pos['current_entry_count'] + 1}차)")
                        cash -= buy_amount_usd
                        cash -= buy_amount_usd * FEE_RATE # 매수 수수료
                        
                        pos['total_collateral'] += buy_amount_usd
                        
                        quantity_to_buy = (buy_amount_usd * LEVERAGE) / now_price
                        
                        # 엔트리 추가
                        pos['entries'].append({
                            "entry": pos['current_entry_count'] + 1,
                            "price": now_price,
                            "quantity": quantity_to_buy,
                            "timestamp": current_time
                        })
                        
                        # 상태 업데이트
                        pos['current_entry_count'] += 1
                        pos['final_buy_time'] = current_time
                        
                        # 평균단가 업데이트
                        new_total_value = sum(e['price'] * e['quantity'] for e in pos['entries'])
                        new_total_qty = sum(e['quantity'] for e in pos['entries'])
                        pos['total_quantity'] = new_total_qty
                        pos['average_price'] = new_total_value / new_total_qty
            
        portfolio_value.append(current_total_value)

    # 4. 결과 분석 및 시각화
    result = pd.DataFrame({'value': portfolio_value}, index=common_index)
    result['daily_return'] = result['value'].pct_change()
    result['cum_return'] = (1 + result['daily_return']).cumprod()
    result['mdd'] = (result['cum_return'].cummax() - result['cum_return']) / result['cum_return'].cummax()
    
    print("\n===== 백테스트 결과 =====")
    print(f"최종 자산: {result['value'].iloc[-1]:.2f} USDT")
    print(f"총 수익률: {(result['cum_return'].iloc[-1] - 1) * 100:.2f}%")
    print(f"최대 낙폭 (MDD): {result['mdd'].max() * 100:.2f}%")
    
    plt.figure(figsize=(15, 8))
    plt.subplot(2, 1, 1)
    result['cum_return'].plot(title='Cumulative Return')
    plt.ylabel('Return (%)')
    plt.grid(True)
    
    plt.subplot(2, 1, 2)
    result['mdd'].plot(title='Max Drawdown (MDD)', color='red')
    plt.ylabel('Drawdown (%)')
    plt.grid(True)
    
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    run_backtest()