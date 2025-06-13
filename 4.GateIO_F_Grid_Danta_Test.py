# -*- coding:utf-8 -*-
'''
파일이름: 4.GateIO_F_Grid_Danta_Test.py
설명: 볼린저밴드, RSI, MACD를 이용한 그리드 매매 전략 (월별 출금 및 각종 설정 기능 추가)
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
TEST_START_DATE = datetime.datetime(2023, 1, 1)  # 시작일
TEST_END_DATE = datetime.datetime(2025, 5, 31)   # 종료일 (현재)
INITIAL_CAPITAL = 50000      # 시작 자본 (USDT)
TIMEFRAME = '5m'             # 5분봉 데이터 사용
LEVERAGE = 10                # 레버리지
STOP_LOSS_PNL_RATE = -0.9    # 할당 자본 대비 손절 PNL 비율 (-90%)
INVEST_COIN_LIST = "DOGE/USDT" # 백테스트할 코인 목록 (리스트 또는 단일 문자열)
FEE_RATE = 0.0005            # 거래 수수료 (시장가 0.05%)

# ▼▼▼ 추가된 부분: 1회차 기본 매수 비율 설정 ▼▼▼
BASE_BUY_RATE = 0.03 # 할당 자본 대비 1회차 매수 금액 비율 (예: 0.03 = 3%)
# ▲▲▲ 추가된 부분 ▲▲▲

# 월별 수익 출금 비율 설정
MONTHLY_WITHDRAWAL_RATE = 0 # 월별 수익 출금 비율 (%, 0이면 출금 안함)

# --- 전략 선택 스위치 ---
USE_ADDITIVE_BUYING = True # True: RSI/차수별 가산 매수 사용, False: 균등 매수 사용
USE_STRATEGIC_EXIT = False # True: 누적 수익으로 손실 포지션을 상쇄하는 전략적 종료 로직 사용


# ==============================================================================
# 2. 데이터 처리 및 보조지표 계산 함수
# ==============================================================================
def load_data(ticker, timeframe, start_date, end_date):
    """로컬 CSV 파일 또는 API를 통해 OHLCV 데이터를 로드합니다."""
    print(f"--- [{ticker}] 데이터 준비 중 ---")
    df = pd.DataFrame()
    csv_file = f"{str(INVEST_COIN_LIST).replace('/USDT', '').lower()}_usdt_5m_2020_to_202505.csv"
    
    if os.path.exists(csv_file):
        try:
            print(f"'{csv_file}' 파일에서 데이터를 로드합니다.")
            df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            df = df.loc[start_date:end_date]
            if df.empty: print(f"경고: '{csv_file}' 파일에 해당 기간의 데이터가 없습니다.")
        except Exception as e:
            print(f"오류: '{csv_file}' 파일 로드 중 오류 발생: {e}.")
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
    """DataFrame에 보조지표(BB, RSI, MACD)를 추가합니다."""
    df['ma30'] = df['close'].rolling(window=30).mean()
    df['stddev'] = df['close'].rolling(window=30).std()
    df['bb_upper'] = df['ma30'] + 2 * df['stddev']
    df['bb_lower'] = df['ma30'] - 2 * df['stddev']
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=13, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=13, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    ema_fast = df['close'].ewm(span=12, adjust=False).mean()
    ema_slow = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    return df.dropna()

def get_rsi_level(rsi_value):
    """RSI 값에 따른 레벨을 반환합니다. (레벨 숫자가 클수록 과매도)"""
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
    elif entry_count > 10: entry_multiplier = 1.3
    return base_amount * rsi_multiplier * entry_multiplier

# ==============================================================================
# 3. 백테스팅 실행 엔진
# ==============================================================================
def run_backtest(data_frames):
    """전략에 따라 백테스트를 실행하고 포트폴리오 가치 변화와 일별 실현 손익을 기록합니다."""
    print("\n백테스트를 시작합니다...")
    if USE_ADDITIVE_BUYING:
        print(">> 가산 매수 모드(RSI/차수별 증액)가 활성화되었습니다.")
    else:
        print(">> 균등 매수 모드가 활성화되었습니다.")
    if USE_STRATEGIC_EXIT:
        print(">> 전략적 포지션 종료 모드(누적수익으로 손실분 상쇄)가 활성화되었습니다.")
    else:
        print(">> 전략적 포지션 종료 모드가 비활성화되었습니다.")
        
    cash = INITIAL_CAPITAL
    total_withdrawn = 0.0
    monthly_withdrawals = {}
    portfolio_history = []
    daily_realized_pnl = {}
    daily_fees = {}
    new_cycle_dates = set()
    positions = {}
    coin_list = list(data_frames.keys())

    for ticker in coin_list:
        allocated_capital = INITIAL_CAPITAL / len(coin_list)
        positions[ticker] = {
            "allocated_capital": allocated_capital, 
            # ▼▼▼ 수정된 부분 ▼▼▼
            "base_buy_amount": allocated_capital * BASE_BUY_RATE,
            # ▲▲▲ 수정된 부분 ▲▲▲
            "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
            "total_collateral": 0.0, "last_buy_timestamp": None,
            "cumulative_realized_pnl": 0.0,
            "buy_blocked_by_macd": False,
            "entries": []
        }
    
    common_index = data_frames[coin_list[0]].index
    for ticker in coin_list[1:]:
        if ticker in data_frames:
            common_index = common_index.intersection(data_frames[ticker].index)
    common_index = common_index.sort_values()
    
    if common_index.empty:
        print("공통 데이터 기간이 없습니다.")
        return pd.DataFrame(), {}, set(), {}, 0.0, {}

    print(f"공통 데이터 기간: {common_index.min()} ~ {common_index.max()}")

    previous_time = None
    for current_time in common_index:
        current_date = current_time.date()
        
        if MONTHLY_WITHDRAWAL_RATE > 0 and previous_time and current_time.month != previous_time.month:
            target_year = previous_time.year
            target_month = previous_time.month
            last_month_pnl = sum(pnl for date, pnl in daily_realized_pnl.items() if date.year == target_year and date.month == target_month)
            
            if last_month_pnl > 0:
                withdrawal_rate_decimal = MONTHLY_WITHDRAWAL_RATE / 100.0
                withdrawal_amount = last_month_pnl * withdrawal_rate_decimal
                cash -= withdrawal_amount
                total_withdrawn += withdrawal_amount
                month_key = f"{target_year}-{target_month:02d}"
                monthly_withdrawals[month_key] = withdrawal_amount
                print(f"[{current_time.strftime('%Y-%m-%d')}] 💸 {target_year}년 {target_month}월 수익금 출금: {withdrawal_amount:,.2f} USDT (지난달 수익: {last_month_pnl:,.2f} USDT의 {MONTHLY_WITHDRAWAL_RATE}%)")

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

            if pos['buy_blocked_by_macd'] and prev_candle['macd_histogram'] > 0:
                pos['buy_blocked_by_macd'] = False
                print(f"[{current_time}] 🟢 {ticker} [MACD] 매수 잠금 초기화 (추세 전환 감지)")

            unrealized_pnl = 0
            if pos['total_quantity'] > 0:
                unrealized_pnl = (mtm_price - pos['average_price']) * pos['total_quantity']
                current_portfolio_value += (pos['total_collateral'] + unrealized_pnl)

            if pos['allocated_capital'] > 0 and (unrealized_pnl / pos['allocated_capital']) <= STOP_LOSS_PNL_RATE:
                gross_pnl = unrealized_pnl
                total_buy_fee = sum(e.get('buy_fee', 0) for e in pos['entries'])
                sell_fee = (pos['total_quantity'] * execution_price) * FEE_RATE
                net_pnl = gross_pnl - total_buy_fee - sell_fee
                daily_fees[current_date] = daily_fees.get(current_date, 0) + total_buy_fee + sell_fee
                pnl_rate = (net_pnl / pos['allocated_capital']) * 100
                print(f"[{current_time}] 🚨 {ticker} 손절매! Net PNL: {net_pnl:,.2f} USDT ({pnl_rate:.2f}%), 할당자본: {pos['allocated_capital']:.2f}")
                daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl
                cash += pos['total_collateral'] + net_pnl
                new_allocated_asset = cash / len(data_frames)
                positions[ticker] = {
                    # ▼▼▼ 수정된 부분 (1% -> BASE_BUY_RATE) ▼▼▼
                    "allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * BASE_BUY_RATE,
                    # ▲▲▲ 수정된 부분 ▲▲▲
                    "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                    "total_collateral": 0.0, "last_buy_timestamp": None,
                    "cumulative_realized_pnl": 0.0, "buy_blocked_by_macd": False, "entries": []
                }
                continue

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
                    gross_pnl = sum([(execution_price - e['price']) * e['quantity'] for e in sold_entries])
                    total_buy_fee = sum(e.get('buy_fee', 0) for e in sold_entries)
                    qty_sold = sum(e['quantity'] for e in sold_entries)
                    sell_fee = (qty_sold * execution_price) * FEE_RATE
                    net_pnl = gross_pnl - total_buy_fee - sell_fee
                    daily_fees[current_date] = daily_fees.get(current_date, 0) + total_buy_fee + sell_fee
                    daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl
                    pos['cumulative_realized_pnl'] += net_pnl
                    log_time = f"[{current_time}] 💰 {ticker}"
                    
                    if len(sold_entries) == pos['current_entry_count']:
                        pnl_rate = (net_pnl / pos['allocated_capital']) * 100 if pos['allocated_capital'] > 0 else 0
                        extra_info = f" (30MA: {prev_candle['ma30']:.5f})" if sell_reason == "30MA 상향 돌파" else ""
                        print(f"{log_time} 포지션 전체 익절 (가격: {execution_price:.5f}, 사유: {sell_reason}). 총 Net PNL: {net_pnl:,.2f} USDT ({pnl_rate:.2f}%)" + extra_info)
                    else:
                        extra_info = f" (30MA: {prev_candle['ma30']:.5f})" if sell_reason == "30MA 상향 돌파" else ""
                        print(f"{log_time} 부분 매도 (가격: {execution_price:.5f}, 사유: {sell_reason})" + extra_info)
                        for entry in sold_entries:
                            gross_pnl_per_entry = (execution_price - entry['price']) * entry['quantity']
                            print(f"    - {entry['entry_num']}차 매도 Gross PNL: {gross_pnl_per_entry:,.2f} USDT")
                        print(f"    - (전체) 매도 Net PNL: {net_pnl:,.2f} USDT")

                    removed_collateral = sum([(e['price'] * e['quantity'] / LEVERAGE) for e in sold_entries])
                    cash += removed_collateral + net_pnl
                    pos['total_collateral'] -= removed_collateral
                    
                    entries_before_sell = pos['current_entry_count']
                    for i in sorted(entries_to_sell_indices, reverse=True): del pos['entries'][i]
                    for new_idx, entry in enumerate(pos['entries']): entry['entry_num'] = new_idx + 1
                    pos['current_entry_count'] = len(pos['entries'])
                    
                    if pos['current_entry_count'] == 0:
                        new_allocated_asset = cash / len(data_frames)
                        # ▼▼▼ 수정된 부분 ▼▼▼
                        pos.update({"allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * BASE_BUY_RATE,
                                    "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                                    "total_collateral": 0.0, "last_buy_timestamp": None,
                                    "cumulative_realized_pnl": 0.0, "buy_blocked_by_macd": False, "entries": []})
                        # ▲▲▲ 수정된 부분 ▲▲▲
                    else:
                        pos['total_quantity'] = sum(e['quantity'] for e in pos['entries'])
                        pos['average_price'] = sum(e['price'] * e['quantity'] for e in pos['entries']) / pos['total_quantity']
                        
                        if USE_STRATEGIC_EXIT:
                            MIN_ENTRIES_FOR_STRATEGIC_EXIT = 6
                            STUCK_ENTRY_THRESHOLD = 5
                            if entries_before_sell >= MIN_ENTRIES_FOR_STRATEGIC_EXIT and pos['current_entry_count'] > 0:
                                stuck_entries = [e for e in pos['entries'] if e['entry_num'] <= STUCK_ENTRY_THRESHOLD]
                                if stuck_entries:
                                    unrealized_pnl_of_stuck = sum([(mtm_price - e['price']) * e['quantity'] for e in stuck_entries])
                                    if (pos['cumulative_realized_pnl'] + unrealized_pnl_of_stuck) > 0:
                                        print(f"[{current_time}] ✨ {ticker} 전략적 포지션 전체 종료! (누적수익으로 손실분 상쇄)")
                                        print(f"    - 현재 누적 실현수익: {pos['cumulative_realized_pnl']:,.2f} USDT")
                                        print(f"    - 물린 포지션 평가손실: {unrealized_pnl_of_stuck:,.2f} USDT")
                                        
                                        all_remaining_entries = pos['entries']
                                        gross_pnl_final = sum([(execution_price - e['price']) * e['quantity'] for e in all_remaining_entries])
                                        total_buy_fee_final = sum(e.get('buy_fee', 0) for e in all_remaining_entries)
                                        qty_sold_final = sum(e['quantity'] for e in all_remaining_entries)
                                        sell_fee_final = (qty_sold_final * execution_price) * FEE_RATE
                                        net_pnl_final = gross_pnl_final - total_buy_fee_final - sell_fee_final

                                        daily_fees[current_date] = daily_fees.get(current_date, 0) + total_buy_fee_final + sell_fee_final
                                        daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl_final

                                        removed_collateral_final = sum([(e['price'] * e['quantity'] / LEVERAGE) for e in all_remaining_entries])
                                        cash += removed_collateral_final + net_pnl_final
                                        
                                        new_allocated_asset = cash / len(data_frames)
                                        positions[ticker] = {
                                            # ▼▼▼ 수정된 부분 ▼▼▼
                                            "allocated_capital": new_allocated_asset, "base_buy_amount": new_allocated_asset * BASE_BUY_RATE,
                                            # ▲▲▲ 수정된 부분 ▲▲▲
                                            "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                                            "total_collateral": 0.0, "last_buy_timestamp": None,
                                            "cumulative_realized_pnl": 0.0, "buy_blocked_by_macd": False, "entries": []
                                        }
                                        continue
                    continue

            if pos['current_entry_count'] < 20:
                base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
                should_buy = False
                if base_buy_cond:
                    if pos['current_entry_count'] == 0: should_buy = True
                    else:
                        last_buy_execution_time = pos['last_buy_timestamp']
                        current_decision_candle_time = prev_candle.name
                        reset_check_candles = df.loc[(df.index > last_buy_execution_time) & (df.index <= current_decision_candle_time)]
                        if not reset_check_candles.empty and (reset_check_candles['rsi'] > 25).any(): should_buy = True
                        else:
                            last_entry_trigger_rsi = pos['entries'][-1]['trigger_rsi']
                            if get_rsi_level(prev_candle['rsi']) > get_rsi_level(last_entry_trigger_rsi): should_buy = True
                
                if should_buy and not pos['buy_blocked_by_macd']:
                    next_entry_num = pos['current_entry_count'] + 1
                    if USE_ADDITIVE_BUYING:
                        buy_collateral = get_buy_amount(pos['base_buy_amount'], get_rsi_level(prev_candle['rsi']), next_entry_num)
                    else:
                        buy_collateral = pos['base_buy_amount']
                    if cash >= buy_collateral:
                        buy_price = execution_price
                        quantity_to_buy = (buy_collateral * LEVERAGE) / buy_price
                        buy_fee = (buy_collateral * LEVERAGE) * FEE_RATE
                        daily_fees[current_date] = daily_fees.get(current_date, 0) + buy_fee
                        print(f"[{current_time}] 📈 {ticker} 매수 ({next_entry_num}차): 가격 {buy_price:.5f}, 수량 {quantity_to_buy:.4f}, 금액 {buy_collateral:,.2f} USDT, RSI {prev_candle['rsi']:.2f}")
                        if next_entry_num == 1: new_cycle_dates.add(current_time.date())
                        cash -= buy_collateral
                        pos['total_collateral'] += buy_collateral
                        pos['entries'].append({"entry_num": next_entry_num, "price": buy_price,
                                               "quantity": quantity_to_buy, "timestamp": current_time,
                                               "trigger_rsi": prev_candle['rsi'],
                                               "buy_fee": buy_fee})
                        pos['current_entry_count'] += 1
                        pos['last_buy_timestamp'] = current_time
                        pos['total_quantity'] = sum(e['quantity'] for e in pos['entries'])
                        pos['average_price'] = sum(e['price'] * e['quantity'] for e in pos['entries']) / pos['total_quantity']
                        if prev_candle['macd_histogram'] < 0:
                            pos['buy_blocked_by_macd'] = True
                            print(f"[{current_time}] 🔴 {ticker} [MACD] 매수 잠금 활성화 (추가 하락 방지)")
        
        previous_time = current_time
        total_entry_count = sum(p.get('current_entry_count', 0) for p in positions.values())
        portfolio_history.append({'timestamp': current_time, 'value': current_portfolio_value, 'entry_count': total_entry_count})

    return pd.DataFrame(portfolio_history).set_index('timestamp'), daily_realized_pnl, new_cycle_dates, monthly_withdrawals, total_withdrawn, daily_fees

# ==============================================================================
# 4. 결과 분석 및 시각화 함수
# ==============================================================================
def analyze_and_plot_results(portfolio_df, realized_pnl_data, new_cycle_dates, monthly_withdrawals, total_withdrawn, daily_fees):
    """백테스트 결과를 분석하고 그래프로 시각화합니다."""
    if portfolio_df.empty:
        print("백테스트 결과가 없어 분석을 종료합니다.")
        return

    final_value = portfolio_df['value'].iloc[-1]
    total_return = ((final_value + total_withdrawn) / INITIAL_CAPITAL - 1) * 100
    portfolio_df['cum_return'] = (portfolio_df['value'] + total_withdrawn) / INITIAL_CAPITAL
    portfolio_df['mdd'] = (portfolio_df['cum_return'].cummax() - portfolio_df['cum_return']) / portfolio_df['cum_return'].max()
    max_dd = portfolio_df['mdd'].max() * 100
    
    print("\n" + "="*60 + "\n                 백테스트 최종 결과\n" + "="*60)
    print(f"  - 시작 자본: {INITIAL_CAPITAL:,.2f} USDT")
    print(f"  - 최종 자산: {final_value:,.2f} USDT")
    print(f"  - 총 출금액: {total_withdrawn:,.2f} USDT")
    total_fees = sum(daily_fees.values())
    print(f"  - 총 수수료: {total_fees:,.2f} USDT")
    print(f"  - 총 수익률 (출금액 포함): {total_return:.2f}%")
    print(f"  - 최대 낙폭 (MDD): {max_dd:.2f}%")
    print("="*60)

    daily_summary = portfolio_df[['value', 'entry_count']].resample('D').last()
    daily_summary.ffill(inplace=True)
    realized_pnl_series = pd.Series(realized_pnl_data, name="Realized PNL")
    realized_pnl_series.index = pd.to_datetime(realized_pnl_series.index)
    daily_summary = daily_summary.join(realized_pnl_series)
    daily_summary['Realized PNL'].fillna(0, inplace=True)
    daily_summary['Cumulative Realized PNL'] = daily_summary['Realized PNL'].cumsum()
    fees_series = pd.Series(daily_fees, name="fees")
    fees_series.index = pd.to_datetime(fees_series.index)
    daily_summary = daily_summary.join(fees_series)
    daily_summary['fees'].fillna(0, inplace=True)

    print("\n" + "="*95)
    print("                                   일별 요약 (실현 손익 기준)")
    print("="*95)
    for index, row in daily_summary.iterrows():
        new_cycle_marker = " « 신규 포지션" if index.date() in new_cycle_dates else ""
        print(f"{index.strftime('%Y-%m-%d')}: 총잔액:{row['value']:>12,.2f} USDT,  일일 실현 Net PNL:{row['Realized PNL']:>+11,.2f} USDT,  누적 실현 Net PNL:{row['Cumulative Realized PNL']:>12,.2f} USDT,  포지션:{int(row['entry_count'])}회차" + new_cycle_marker)
    print("="*95)

    monthly_summary = daily_summary.resample('M').agg({
        'value': 'last',
        'Realized PNL': 'sum',
        'Cumulative Realized PNL': 'last',
        'fees': 'sum'
    })
    
    monthly_summary['begin_value'] = monthly_summary['value'].shift(1)
    monthly_summary.loc[monthly_summary.index[0], 'begin_value'] = INITIAL_CAPITAL
    monthly_summary['monthly_return'] = (monthly_summary['Realized PNL'] / monthly_summary['begin_value']) * 100
    monthly_summary.index = monthly_summary.index.strftime('%Y-%m')
    monthly_withdrawal_series = pd.Series(monthly_withdrawals, name="Withdrawal")
    monthly_summary = monthly_summary.join(monthly_withdrawal_series)
    monthly_summary['Withdrawal'].fillna(0, inplace=True)

    print("\n" + "="*125)
    print("                                                            월별 요약 (실현 손익 기준)")
    print("="*125)
    for index, row in monthly_summary.iterrows():
        print(f"{index}: 총잔액:{row['value']:>12,.2f} USDT,   월별 실현 Net PNL:{row['Realized PNL']:>+11,.2f} USDT,   수익률: {row['monthly_return']:>+7.2f}%,   수수료: {row.get('fees', 0):>8,.2f} USDT,   출금액: {row['Withdrawal']:>10,.2f} USDT")
    print("="*125)

    plt.figure(figsize=(15, 8))
    try: plt.rc('font', family='Malgun Gothic')
    except: plt.rc('font', family='AppleGothic')
    plt.rcParams['axes.unicode_minus'] = False
    
    ax1 = plt.subplot(2, 1, 1)
    (portfolio_df['cum_return'] * 100 - 100).plot(ax=ax1, title='자산 추이 (누적 수익률, 출금액 포함)')
    ax1.set_ylabel('누적 수익률 (%)'); ax1.grid(True)
    ax2 = plt.subplot(2, 1, 2)
    (portfolio_df['mdd'] * 100).plot(ax=ax2, title='최대 낙폭 (Maximum Drawdown)', color='red')
    ax2.set_ylabel('낙폭 (%)'); ax2.grid(True)
    plt.xlabel('날짜'); plt.tight_layout(); plt.show()

# ==============================================================================
# 5. 메인 실행 블록
# ==============================================================================
if __name__ == '__main__':
    coin_list_to_process = INVEST_COIN_LIST if isinstance(INVEST_COIN_LIST, list) else [INVEST_COIN_LIST]
    
    all_data_frames = {}
    for coin_ticker in coin_list_to_process:
        df = load_data(coin_ticker, TIMEFRAME, TEST_START_DATE, TEST_END_DATE)
        if not df.empty:
            all_data_frames[coin_ticker] = calculate_indicators(df)

    if not all_data_frames:
        print("백테스트를 위한 데이터를 로드하지 못했습니다. 프로그램을 종료합니다.")
    else:
        portfolio_result, realized_pnl, new_cycles, monthly_withdrawals, total_withdrawn, daily_fees = run_backtest(all_data_frames)
        analyze_and_plot_results(portfolio_result, realized_pnl, new_cycles, monthly_withdrawals, total_withdrawn, daily_fees)