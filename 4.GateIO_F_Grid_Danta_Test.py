# -*- coding:utf-8 -*-
'''
파일이름: 4.GateIO_F_Grid_Danta_Test.py
설명: 볼린저밴드와 RSI를 이용한 그리드 매매 전략 (백테스트용 최종본 - 월별 요약 추가)
'''
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os

# ==============================================================================
# 1. 백테스트 환경 설정
# ==============================================================================
TEST_START_DATE = datetime.datetime(2024, 1, 1)  # 시작일
TEST_END_DATE = datetime.datetime.now()          # 종료일 (현재)
INITIAL_CAPITAL = 100000      # 시작 자본 (USDT)
TIMEFRAME = '5m'             # 5분봉 데이터 사용
LEVERAGE = 10                # 레버리지
STOP_LOSS_PNL_RATE = -0.9    # 할당 자본 대비 손절 PNL 비율 (-50%)
INVEST_COIN_LIST = ['DOGE/USDT'] # 백테스트할 코인 목록
FEE_RATE = 0.0002            # 거래 수수료 (시장가 0.05% 가정)

# ==============================================================================
# 2. 데이터 처리 및 보조지표 계산 함수
# ==============================================================================
def load_data(ticker, timeframe, start_date, end_date):
    """로컬 CSV 파일 또는 API를 통해 OHLCV 데이터를 로드합니다."""
    print(f"--- [{ticker}] 데이터 준비 중 ---")
    df = pd.DataFrame()
    doge_csv_file = 'doge_usdt_5m_2022_to_202505.csv'
    if ticker == 'DOGE/USDT' and os.path.exists(doge_csv_file):
        try:
            print(f"'{doge_csv_file}' 파일에서 데이터를 로드합니다.")
            df = pd.read_csv(doge_csv_file, index_col=0, parse_dates=True)
            df = df.loc[start_date:end_date]
            if df.empty: print(f"경고: '{doge_csv_file}' 파일에 해당 기간의 데이터가 없습니다.")
        except Exception as e:
            print(f"오류: '{doge_csv_file}' 파일 로드 중 오류 발생: {e}.")
            df = pd.DataFrame()
    if df.empty:
        print(f"로컬 파일이 없거나 사용할 수 없어 API를 통해 데이터를 다운로드합니다.")
        exchange = ccxt.gateio()
        all_ohlcv = []
        since = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)
        while since < end_ms:
            try:
                ohlcv = exchange.fetch_ohlcv(ticker, timeframe, since, limit=1000)
                if not ohlcv: break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + (exchange.parse_timeframe(timeframe) * 1000)
                print(f"[{ticker}] API 다운로드 중... 마지막 날짜: {datetime.datetime.fromtimestamp(ohlcv[-1][0]/1000)}")
                time.sleep(exchange.rateLimit / 1000)
            except Exception as e:
                print(f"API 데이터 다운로드 오류: {e}"); break
        if all_ohlcv:
            df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df = df.drop_duplicates(subset='timestamp', keep='first').set_index('timestamp')
    return df

def calculate_indicators(df):
    """DataFrame에 보조지표(BB, RSI)를 추가합니다."""
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bb_upper'] = df['ma30'] + 2 * df['stddev']
    df['bb_lower'] = df['ma30'] - 2 * df['stddev']
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=13, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df.dropna()

def get_rsi_level(rsi_value):
    """RSI 값에 따른 레벨을 반환합니다."""
    if 20 < rsi_value <= 25: return 1
    if 15 < rsi_value <= 20: return 2
    if 10 < rsi_value <= 15: return 3
    if rsi_value <= 10: return 4
    return 0

def get_buy_amount(base_amount, rsi_level, entry_count):
    """RSI 레벨과 진입 차수에 따라 최종 매수 증거금을 계산합니다."""
    rsi_multiplier = {1: 1.0, 2: 1.1, 3: 1.2, 4: 1.3}.get(rsi_level, 1.0)
    entry_multiplier = 1.0
    if 4 <= entry_count <= 6: entry_multiplier = 1.2
    elif 7 <= entry_count <= 10: entry_multiplier = 1.3
    return base_amount * rsi_multiplier * entry_multiplier

# ==============================================================================
# 3. 백테스팅 실행 엔진
# ==============================================================================
def run_backtest(data_frames):
    """전략에 따라 백테스트를 실행하고 포트폴리오 가치 변화와 일별 실현 손익을 기록합니다."""
    print("\n백테스트를 시작합니다...")
    cash = INITIAL_CAPITAL
    portfolio_history = []
    daily_realized_pnl = {}
    new_cycle_dates = set() # 신규 포지션 시작일 기록
    
    positions = {}
    for ticker in data_frames.keys():
        allocated_capital = INITIAL_CAPITAL / len(data_frames)
        positions[ticker] = {
            "allocated_capital": allocated_capital, "base_buy_amount": allocated_capital * 0.01,
            "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
            "total_collateral": 0.0, "last_buy_timestamp": None,
            "cumulative_realized_pnl": 0.0,
            "entries": []
        }
    common_index = data_frames[INVEST_COIN_LIST[0]].index
    for ticker in INVEST_COIN_LIST[1:]:
        if ticker in data_frames:
            common_index = common_index.intersection(data_frames[ticker].index)
    common_index = common_index.sort_values()
    print(f"공통 데이터 기간: {common_index.min()} ~ {common_index.max()}")

    for current_time in common_index:
        current_portfolio_value = cash
        for ticker, df in data_frames.items():
            if current_time not in df.index: continue
            pos = positions[ticker]
            data_till_now = df.loc[:current_time]
            if len(data_till_now) < 3: continue
            
            prev_candle = data_till_now.iloc[-2]
            prev_prev_candle = data_till_now.iloc[-3]
            current_candle = data_till_now.iloc[-1]
            
            mtm_price = current_candle['close']
            execution_price = current_candle['open']

            unrealized_pnl = 0
            if pos['total_quantity'] > 0:
                unrealized_pnl = (mtm_price - pos['average_price']) * pos['total_quantity']
                current_portfolio_value += (pos['total_collateral'] + unrealized_pnl)

            if pos['allocated_capital'] > 0 and (unrealized_pnl / pos['allocated_capital']) <= STOP_LOSS_PNL_RATE:
                pnl_rate = (unrealized_pnl / pos['allocated_capital']) * 100
                print(f"[{current_time}] 🚨 {ticker} 손절매! PNL: {unrealized_pnl:,.2f} USDT ({pnl_rate:.2f}%), 할당자본: {pos['allocated_capital']:.2f}")
                
                realized_pnl_from_stoploss = unrealized_pnl
                current_date = current_time.date()
                daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + realized_pnl_from_stoploss

                cash += (pos['total_collateral'] + unrealized_pnl)
                cash -= (pos['total_collateral'] * LEVERAGE) * FEE_RATE
                new_allocated_asset = cash / len(data_frames)
                positions[ticker] = {
                    "allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * 0.01,
                    "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                    "total_collateral": 0.0, "last_buy_timestamp": None,
                    "cumulative_realized_pnl": 0.0, "entries": []
                }
                continue

            # if pos['current_entry_count'] >= 6:
            #     stuck_entries = [e for e in pos['entries'] if e['entry_num'] <= 5]
            #     unrealized_pnl_of_stuck = 0
            #     if stuck_entries:
            #         unrealized_pnl_of_stuck = sum([(mtm_price - e['price']) * e['quantity'] for e in stuck_entries])
                
            #     cumulative_profit = pos.get('cumulative_realized_pnl', 0)

            #     if (cumulative_profit + unrealized_pnl_of_stuck) > 0:
            #         print(f"[{current_time}] ✨ {ticker} 전략적 포지션 전체 종료! (누적수익으로 손실분 상쇄)")
            #         print(f"    - 누적 실현수익: {cumulative_profit:,.2f} USDT")
            #         print(f"    - 물린 포지션 손실: {unrealized_pnl_of_stuck:,.2f} USDT")
            #         print(f"    - 최종 합산 이익: {(cumulative_profit + unrealized_pnl_of_stuck):,.2f} USDT")
                    
            #         pnl_from_sell = sum([(execution_price - e['price']) * e['quantity'] for e in pos['entries']])
            #         current_date = current_time.date()
            #         daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + pnl_from_sell

            #         cash += pos['total_collateral'] + pnl_from_sell
            #         cash -= (pos['total_collateral'] * LEVERAGE) * FEE_RATE
                    
            #         new_allocated_asset = cash / len(data_frames)
            #         positions[ticker] = {
            #             "allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * 0.01,
            #             "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
            #             "total_collateral": 0.0, "last_buy_timestamp": None,
            #             "cumulative_realized_pnl": 0.0, "entries": []
            #         }
            #         continue

            if pos['current_entry_count'] > 0:
                entries_to_sell_indices, sell_reason = [], ""
                is_ma_cross_up = prev_candle['close'] > prev_candle['ma30'] and prev_prev_candle['close'] < prev_prev_candle['ma30']
                if is_ma_cross_up:
                    entries_to_sell_indices = [i for i, e in enumerate(pos['entries']) if e['price'] < prev_candle['ma30']]
                    if entries_to_sell_indices: sell_reason = "30MA 상향 돌파"
                elif prev_candle['close'] > prev_candle['bb_upper']:
                    if mtm_price > pos['average_price']:
                        entries_to_sell_indices = list(range(len(pos['entries'])))
                        sell_reason = "BB 상단 돌파 (전체 익절)"
                    else:
                        entries_to_sell_indices = [i for i, e in enumerate(pos['entries']) if mtm_price > e['price']]
                        if entries_to_sell_indices: sell_reason = "BB 상단 돌파 (부분 익절)"
                
                if entries_to_sell_indices:
                    sold_entries = [pos['entries'][i] for i in entries_to_sell_indices]
                    pnl_from_sell = sum([(execution_price - e['price']) * e['quantity'] for e in sold_entries])
                    
                    current_date = current_time.date()
                    daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + pnl_from_sell
                    pos['cumulative_realized_pnl'] += pnl_from_sell
                    
                    log_time = f"[{current_time}] 💰 {ticker}"
                    if len(sold_entries) == pos['current_entry_count']:
                        pnl_rate = (pnl_from_sell / pos['allocated_capital']) * 100 if pos['allocated_capital'] > 0 else 0
                        extra_info = f" (30MA: {prev_candle['ma30']:.5f})" if sell_reason == "30MA 상향 돌파" else ""
                        print(f"{log_time} 포지션 전체 익절 (가격: {execution_price:.5f}, 사유: {sell_reason}). 총 PNL: {pnl_from_sell:,.2f} USDT ({pnl_rate:.2f}%)" + extra_info)
                    else:
                        extra_info = f" (30MA: {prev_candle['ma30']:.5f})" if sell_reason == "30MA 상향 돌파" else ""
                        print(f"{log_time} 부분 매도 (가격: {execution_price:.5f}, 사유: {sell_reason})" + extra_info)
                        for entry in sold_entries:
                            pnl_per_entry = (execution_price - entry['price']) * entry['quantity']
                            print(f"    - {entry['entry_num']}차 매도 PNL: {pnl_per_entry:,.2f} USDT")

                    removed_collateral = sum([(e['price'] * e['quantity'] / LEVERAGE) for e in sold_entries])
                    cash += removed_collateral + pnl_from_sell
                    cash -= (removed_collateral * LEVERAGE) * FEE_RATE
                    pos['total_collateral'] -= removed_collateral
                    for i in sorted(entries_to_sell_indices, reverse=True): del pos['entries'][i]
                    for new_idx, entry in enumerate(pos['entries']): entry['entry_num'] = new_idx + 1
                    pos['current_entry_count'] = len(pos['entries'])
                    if pos['current_entry_count'] == 0:
                        new_allocated_asset = cash / len(data_frames)
                        pos.update({"allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * 0.01,
                                    "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                                    "total_collateral": 0.0, "last_buy_timestamp": None,
                                    "cumulative_realized_pnl": 0.0, "entries": []})
                    else:
                        pos['total_quantity'] = sum(e['quantity'] for e in pos['entries'])
                        pos['average_price'] = sum(e['price'] * e['quantity'] for e in pos['entries']) / pos['total_quantity']
                    continue

            if pos['current_entry_count'] < 10:
                base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
                should_buy = False
                if base_buy_cond:
                    if pos['current_entry_count'] == 0:
                        should_buy = True
                    else:
                        last_buy_execution_time = pos['last_buy_timestamp']
                        current_decision_candle_time = prev_candle.name
                        reset_check_candles = df.loc[(df.index > last_buy_execution_time) & (df.index <= current_decision_candle_time)]
                        if not reset_check_candles.empty and (reset_check_candles['rsi'] > 25).any():
                            should_buy = True
                        else:
                            last_entry_trigger_rsi = pos['entries'][-1]['trigger_rsi']
                            if get_rsi_level(prev_candle['rsi']) > get_rsi_level(last_entry_trigger_rsi):
                                should_buy = True
                if should_buy:
                    next_entry_num = pos['current_entry_count'] + 1
                    buy_collateral = get_buy_amount(pos['base_buy_amount'], get_rsi_level(prev_candle['rsi']), next_entry_num)
                    if cash >= buy_collateral:
                        buy_price = execution_price
                        quantity_to_buy = (buy_collateral * LEVERAGE) / buy_price
                        print(f"[{current_time}] 📈 {ticker} 매수 ({next_entry_num}차): 가격 {buy_price:.5f}, 수량 {quantity_to_buy:.4f}, 금액 {buy_collateral:,.2f} USDT, RSI {prev_candle['rsi']:.2f}")
                        
                        if next_entry_num == 1:
                            new_cycle_dates.add(current_time.date())

                        cash -= buy_collateral
                        cash -= (buy_collateral * LEVERAGE) * FEE_RATE
                        pos['total_collateral'] += buy_collateral
                        pos['entries'].append({"entry_num": next_entry_num, "price": buy_price,
                                               "quantity": quantity_to_buy, "timestamp": current_time,
                                               "trigger_rsi": prev_candle['rsi']})
                        pos['current_entry_count'] += 1
                        pos['last_buy_timestamp'] = current_time
                        pos['total_quantity'] = sum(e['quantity'] for e in pos['entries'])
                        pos['average_price'] = sum(e['price'] * e['quantity'] for e in pos['entries']) / pos['total_quantity']
        
        total_entry_count = sum(p.get('current_entry_count', 0) for p in positions.values())
        portfolio_history.append({'timestamp': current_time, 'value': current_portfolio_value, 'entry_count': total_entry_count})

    return pd.DataFrame(portfolio_history).set_index('timestamp'), daily_realized_pnl, new_cycle_dates

# ==============================================================================
# 4. 결과 분석 및 시각화 함수
# ==============================================================================
def analyze_and_plot_results(portfolio_df, realized_pnl_data, new_cycle_dates):
    """백테스트 결과를 분석하고 그래프로 시각화합니다."""
    if portfolio_df.empty:
        print("백테스트 결과가 없어 분석을 종료합니다.")
        return

    # --- 1. 전체 성과 지표 계산 ---
    final_value = portfolio_df['value'].iloc[-1]
    total_return = (final_value / INITIAL_CAPITAL - 1) * 100
    portfolio_df['cum_return'] = portfolio_df['value'] / INITIAL_CAPITAL
    portfolio_df['mdd'] = (portfolio_df['cum_return'].cummax() - portfolio_df['cum_return']) / portfolio_df['cum_return'].max()
    max_dd = portfolio_df['mdd'].max() * 100
    
    print("\n" + "="*50 + "\n                 백테스트 최종 결과\n" + "="*50)
    print(f"  - 시작 자본: {INITIAL_CAPITAL:,.2f} USDT\n  - 최종 자산: {final_value:,.2f} USDT")
    print(f"  - 총 수익률: {total_return:.2f}%\n  - 최대 낙폭 (MDD): {max_dd:.2f}%")
    print("="*50)

    # --- 2. 일별/월별 요약 계산 및 출력 ---
    daily_summary = portfolio_df[['value', 'entry_count']].resample('D').last()
    daily_summary.ffill(inplace=True)
    
    realized_pnl_series = pd.Series(realized_pnl_data, name="Realized PNL")
    realized_pnl_series.index = pd.to_datetime(realized_pnl_series.index)
    
    daily_summary = daily_summary.join(realized_pnl_series)
    daily_summary['Realized PNL'].fillna(0, inplace=True)
    
    daily_summary['Cumulative Realized PNL'] = daily_summary['Realized PNL'].cumsum()

    print("\n" + "="*95)
    print("                                   일별 요약 (실현 손익 기준)")
    print("="*95)
    for index, row in daily_summary.iterrows():
        new_cycle_marker = " « 신규 포지션" if index.date() in new_cycle_dates else ""
        print(f"{index.strftime('%Y-%m-%d')}: 총잔액:{row['value']:>12,.2f} USDT,  일일 실현 PNL:{row['Realized PNL']:>+11,.2f} USDT,  누적 실현 PNL:{row['Cumulative Realized PNL']:>12,.2f} USDT,  포지션:{int(row['entry_count'])}회차" + new_cycle_marker)
    print("="*95)

    # 월별 요약 계산
    monthly_summary = daily_summary.resample('M').agg({
        'value': 'last',
        'Realized PNL': 'sum',
        'Cumulative Realized PNL': 'last'
    })
    monthly_summary.index = monthly_summary.index.strftime('%Y-%m')

    print("\n" + "="*70)
    print("                           월별 요약 (실현 손익 기준)")
    print("="*70)
    for index, row in monthly_summary.iterrows():
        print(f"{index}: 총잔액:{row['value']:>12,.2f} USDT,   월별 실현 PNL:{row['Realized PNL']:>+11,.2f} USDT,   누적 실현 PNL:{row['Cumulative Realized PNL']:>12,.2f} USDT")
    print("="*70)


    # --- 3. 그래프 시각화 ---
    plt.figure(figsize=(15, 8))
    plt.rc('font', family='Malgun Gothic'); plt.rcParams['axes.unicode_minus'] = False
    ax1 = plt.subplot(2, 1, 1)
    (portfolio_df['cum_return'] * 100 - 100).plot(ax=ax1, title='자산 추이 (Cumulative Return)')
    ax1.set_ylabel('누적 수익률 (%)'); ax1.grid(True)
    ax2 = plt.subplot(2, 1, 2)
    (portfolio_df['mdd'] * 100).plot(ax=ax2, title='최대 낙폭 (Maximum Drawdown)', color='red')
    ax2.set_ylabel('낙폭 (%)'); ax2.grid(True)
    plt.xlabel('날짜'); plt.tight_layout(); plt.show()

# ==============================================================================
# 5. 메인 실행 블록
# ==============================================================================
if __name__ == '__main__':
    all_data_frames = {}
    for coin_ticker in INVEST_COIN_LIST:
        df = load_data(coin_ticker, TIMEFRAME, TEST_START_DATE, TEST_END_DATE)
        if not df.empty:
            all_data_frames[coin_ticker] = calculate_indicators(df)
    if not all_data_frames:
        print("백테스트를 위한 데이터를 로드하지 못했습니다. 프로그램을 종료합니다.")
    else:
        portfolio_result, realized_pnl, new_cycles = run_backtest(all_data_frames)
        analyze_and_plot_results(portfolio_result, realized_pnl, new_cycles)