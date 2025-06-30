# -*- coding:utf-8 -*-
'''
파일이름: 9.GateIO_F_Grid_Danta_LongShort_Final_v9_adx_condition.py
설명: 볼린저밴드, RSI, MACD, ADX를 이용한 롱/숏 그리드 매매 전략 (ADX 조건부 동적 RSI 적용)
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
COIN_EXCHANGE = "gateio"  # 거래소 이름 (예: 'binance', 'gateio')
TEST_START_DATE = datetime.datetime(2021, 1, 1)  # 시작일
TEST_END_DATE = datetime.datetime(2025, 6, 30)   # 종료일 (현재)
INITIAL_CAPITAL = 100000      # 시작 자본 (USDT)
TIMEFRAME = '15m'             # 15분봉 데이터 사용
LEVERAGE = 10                # 레버리지
STOP_LOSS_PNL_RATE = -1    # 할당 자본 대비 손절 PNL 비율 (-1 = 사용 안함)
INVEST_COIN_LIST = "DOGE/USDT" # 백테스트할 코인 목록 (리스트 또는 단일 문자열)
FEE_RATE = 0.0005            # 거래 수수료 (시장가 0.05%)

BASE_BUY_RATE = 0.02 # 할당 자본 대비 1회차 매수 금액 비율 (예: 0.03 = 3%)

# <<< [수정] 설정 설명 명확화 >>>
# True: '매 진입 시점'의 가용 현금 기준, False: 포지션 사이클 시작 시점의 '할당 자본' 기준
USE_DYNAMIC_BASE_BUY_AMOUNT = True

# 월별 수익 출금 비율 설정
MONTHLY_WITHDRAWAL_RATE = 30 # 월별 수익 출금 비율 (%, 0이면 출금 안함)

# --- 전략 선택 스위치 ---
USE_ADDITIVE_BUYING = False   # True: RSI/차수별 가산 매수 사용, False: 균등 매수 사용
USE_STRATEGIC_EXIT = False   # True: 누적 수익으로 손실 포지션을 상쇄하는 전략적 종료 로직 사용
USE_MACD_BUY_LOCK = True     # True: MACD 히스토그램이 음수일 때 추가 매수 잠금

# 숏 포지션 전략 관련 설정
USE_SHORT_STRATEGY = True    # True: 숏 포지션 전략 사용
SHORT_CONDITION_TIMEFRAME = '1d' # 숏 포지션 진입 조건(MA, MACD)을 확인할 타임프레임 ('1d', '4h', '1h' 등)
MAX_LONG_BUY_COUNT = 15      # 최대 롱 분할매수 횟수
MAX_SHORT_BUY_COUNT = 5     # 최대 숏 분할매수 횟수
SHORT_ENTRY_RSI = 75         # 숏 포지션 진입을 위한 RSI 조건 값

# 롱 포지션 개수와 ADX에 따른 숏 진입 RSI 조정값 설정
SHORT_RSI_ADJUSTMENT = 0

# 롱 포지션이 숏 포지션보다 이 횟수 이상 많고, 특정 조건 만족 시 추가 롱 진입을 막습니다.
LONG_ENTRY_LOCK_SHORT_COUNT_DIFF = 7


# ==============================================================================
# 2. 데이터 처리 및 보조지표 계산 함수
# (이전과 동일)
# ==============================================================================
def load_data(ticker, timeframe, start_date, end_date):
    """
    로컬 CSV 파일의 데이터를 우선 로드하고, 부족한 최신 데이터는 API를 통해 다운로드하여 병합합니다.
    """
    print(f"--- [{ticker}] 데이터 준비 중 ---")
    csv_df = pd.DataFrame()
    safe_ticker_name = ticker.replace('/', '_').lower()
    # CSV 파일 이름 규칙을 스크립트 설정과 일치시킵니다.
    csv_file = f"{str(INVEST_COIN_LIST).replace('/USDT', '').lower()}_usdt_{COIN_EXCHANGE}_{TIMEFRAME}.csv"

    print(f"--- [{csv_file}] 데이터 준비 중 ---")

    # 1. 로컬 CSV 파일에서 데이터 로드 시도
    if os.path.exists(csv_file):
        try:
            print(f"'{csv_file}' 파일에서 데이터를 로드합니다.")
            csv_df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            if csv_df.index.tz is None:
                csv_df.index = csv_df.index.tz_localize('UTC')
            csv_df.index = csv_df.index.tz_convert(None) # 시간대 정보 제거하여 단순화
        except Exception as e:
            print(f"오류: '{csv_file}' 파일 로드 중 오류 발생: {e}.")
            csv_df = pd.DataFrame()

    # 2. 데이터 필요 여부 및 다운로드 시작 시점 결정
    fetch_from_api = False
    since = int(start_date.timestamp() * 1000)

    if not csv_df.empty:
        last_date_in_csv = csv_df.index.max()
        if last_date_in_csv < end_date:
            print(f"로컬 데이터가 최신이 아닙니다. 마지막 데이터: {last_date_in_csv}. 이후 데이터를 API로 가져옵니다.")
            # 마지막 데이터 다음 캔들부터 가져오기 위해 시간 증분
            timeframe_duration = pd.to_timedelta(timeframe)
            since = int((last_date_in_csv + timeframe_duration).timestamp() * 1000)
            fetch_from_api = True
        else:
            print("로컬 데이터가 최신 상태입니다. API 호출을 건너뜁니다.")
    else:
        print("로컬 데이터가 없습니다. 전체 기간 데이터를 API로 다운로드합니다.")
        fetch_from_api = True

    # 3. 필요한 경우 API를 통해 데이터 다운로드
    if fetch_from_api:
        print(f"API 다운로드 시작: {datetime.datetime.fromtimestamp(since/1000)}")
        exchange = getattr(ccxt, COIN_EXCHANGE)() # 설정된 거래소 객체 생성
        all_ohlcv = []
        end_ms = int(end_date.timestamp() * 1000)
        timeframe_duration_in_ms = exchange.parse_timeframe(timeframe) * 1000

        while since < end_ms:
            try:
                ohlcv = exchange.fetch_ohlcv(ticker, timeframe, since, limit=1000)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + timeframe_duration_in_ms
                print(f"[{ticker}] API 다운로드 중... 마지막 날짜: {datetime.datetime.fromtimestamp(ohlcv[-1][0]/1000)}")
                time.sleep(exchange.rateLimit / 1000)
            except Exception as e:
                print(f"API 데이터 다운로드 오류: {e}")
                break

        if all_ohlcv:
            api_df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            api_df['timestamp'] = pd.to_datetime(api_df['timestamp'], unit='ms')
            api_df.set_index('timestamp', inplace=True)

            # 4. 기존 데이터와 새로 받은 데이터 병합 및 저장
            combined_df = pd.concat([csv_df, api_df])
            # 중복된 인덱스(날짜)가 있을 경우, 새로 받은 데이터(keep='last')를 유지
            combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
            combined_df.sort_index(inplace=True)

            combined_df.to_csv(csv_file)
            print(f"업데이트된 데이터를 '{csv_file}' 파일로 저장했습니다.")
            df = combined_df
        else:
            df = csv_df # API로 가져온 데이터가 없으면 기존 데이터 사용
    else:
        df = csv_df # API 호출이 필요 없으면 기존 데이터 사용

    # 5. 최종적으로 백테스트 기간에 맞춰 데이터 필터링 후 반환
    if not df.empty:
        return df.loc[start_date:end_date]
    else:
        return pd.DataFrame()

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
    return df

def calculate_adx(df, window=14):
    """ADX 지표를 계산합니다."""
    df['tr1'] = df['high'] - df['low']
    df['tr2'] = abs(df['high'] - df['close'].shift(1))
    df['tr3'] = abs(df['low'] - df['close'].shift(1))
    df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)

    df['pdm'] = (df['high'] - df['high'].shift(1))
    df['mdm'] = (df['low'].shift(1) - df['low'])
    df['pdm'] = df['pdm'].where((df['pdm'] > df['mdm']) & (df['pdm'] > 0), 0)
    df['mdm'] = df['mdm'].where((df['mdm'] > df['pdm']) & (df['mdm'] > 0), 0)

    df['pdi'] = (df['pdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100
    df['mdi'] = (df['mdm'].ewm(alpha=1/window, adjust=False).mean() / df['tr'].ewm(alpha=1/window, adjust=False).mean()) * 100

    with np.errstate(divide='ignore', invalid='ignore'):
        df['dx'] = (abs(df['pdi'] - df['mdi']) / (df['pdi'] + df['mdi'])) * 100
    df['dx'].fillna(0, inplace=True)
    df['adx'] = df['dx'].ewm(alpha=1/window, adjust=False).mean()
    return df

def add_secondary_timeframe_indicators(df_base, secondary_timeframe='1d'):
    """
    주어진 타임프레임으로 데이터를 리샘플링하고,
    이전 타임프레임 기준의 지표(MA, MACD, ADX)를 원본 데이터프레임에 병합합니다.
    """
    print(f"--- [{secondary_timeframe}] 기준 데이터 준비 및 병합 중 ---")

    agg_rules = {'open':'first', 'high': 'max', 'low':'min', 'close': 'last'}
    df_secondary = df_base.resample(secondary_timeframe).agg(agg_rules)
    df_secondary = df_secondary.dropna()

    if df_secondary.empty:
        return df_base.assign(prev_tf_close_below_ma30=False, prev_tf_macd_hist_neg=False, prev_tf_ma30_3day_rising=False, prev_tf_adx=0)

    # MA, MACD 계산
    df_secondary['ma30'] = df_secondary['close'].rolling(window=30).mean()
    ema_fast_sec = df_secondary['close'].ewm(span=12, adjust=False).mean()
    ema_slow_sec = df_secondary['close'].ewm(span=26, adjust=False).mean()
    macd_sec = ema_fast_sec - ema_slow_sec
    df_secondary['macd_histogram'] = macd_sec - macd_sec.ewm(span=9, adjust=False).mean()
    df_secondary['ma30_3day_rising'] = (df_secondary['ma30'].diff(1) > 0) & (df_secondary['ma30'].diff(2) > 0) & (df_secondary['ma30'].diff(3) > 0)

    df_secondary = calculate_adx(df_secondary, window=14)

    # 이전 봉 데이터 사용을 위해 shift
    cols_to_shift = ['close', 'ma30', 'macd_histogram', 'ma30_3day_rising', 'adx']
    df_secondary_shifted = df_secondary[cols_to_shift].shift(1)
    df_secondary_shifted.rename(columns={
        'close': 'prev_tf_close', 'ma30': 'prev_tf_ma30',
        'macd_histogram': 'prev_tf_macd_hist', 'ma30_3day_rising': 'prev_tf_ma30_3day_rising',
        'adx': 'prev_tf_adx'
    }, inplace=True)

    df_secondary_shifted['prev_tf_close_below_ma30'] = df_secondary_shifted['prev_tf_close'] < df_secondary_shifted['prev_tf_ma30']
    df_secondary_shifted['prev_tf_macd_hist_neg'] = df_secondary_shifted['prev_tf_macd_hist'] < 0

    cols_to_join = ['prev_tf_close_below_ma30', 'prev_tf_macd_hist_neg', 'prev_tf_ma30_3day_rising', 'prev_tf_adx']

    df_merged = pd.merge_asof(
        df_base.sort_index(),
        df_secondary_shifted[cols_to_join],
        left_index=True,
        right_index=True,
        direction='backward'
    )

    for col in cols_to_join:
        if col == 'prev_tf_adx':
            df_merged[col] = df_merged[col].fillna(0)
        else:
            df_merged[col] = df_merged[col].fillna(False)

    print(f"--- [{secondary_timeframe}] 기준 데이터 병합 완료 ---")
    return df_merged

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
    elif entry_count > 10: entry_multiplier = 1.3
    return base_amount * rsi_multiplier * entry_multiplier

# ==============================================================================
# 3. 백테스팅 실행 엔진
# ==============================================================================
def run_backtest(data_frames):
    """전략에 따라 백테스트를 실행하고 포트폴리오 가치 변화와 일별 실현 손익을 기록합니다."""
    print("\n백테스트를 시작합니다...")
    if USE_ADDITIVE_BUYING: print(">> 롱 가산 매수 모드(RSI/차수별 증액)가 활성화되었습니다.")
    else: print(">> 롱 균등 매수 모드가 활성화되었습니다.")
    if USE_MACD_BUY_LOCK: print(">> MACD 매수 잠금 기능이 활성화되었습니다.")
    else: print(">> MACD 매수 잠금 기능이 비활성화되었습니다.")
    if USE_SHORT_STRATEGY:
        print(f">> 숏 포지션 전략이 활성화되었습니다. (조건 기준: {SHORT_CONDITION_TIMEFRAME})")
    else: print(">> 숏 포지션 전략이 비활성화되었습니다.")
    if USE_DYNAMIC_BASE_BUY_AMOUNT:
        print(">> 1회차 진입금액: [동적] '매 진입 시점'의 가용 현금 기준으로 계산됩니다.")
    else:
        print(">> 1회차 진입금액: [고정] '사이클 시작 시점'의 할당 자본 기준으로 계산됩니다.")

    cash = INITIAL_CAPITAL
    total_withdrawn = 0.0
    # (이하 변수 선언은 동일)
    total_long_pnl = 0.0
    total_short_pnl = 0.0
    monthly_withdrawals = {}
    portfolio_history = []
    daily_realized_pnl = {}
    daily_fees = {}
    new_cycle_dates = set()
    positions = {}
    coin_list = list(data_frames.keys())

    total_long_position_opened = 0
    total_long_position_closed = 0
    total_long_trades = 0
    total_short_position_opened = 0
    total_short_position_closed = 0
    total_short_trades = 0

    for ticker in coin_list:
        allocated_capital = INITIAL_CAPITAL / len(coin_list)
        positions[ticker] = {
            "allocated_capital": allocated_capital,
            "base_buy_amount": allocated_capital * BASE_BUY_RATE,
            "long": {
                "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                "total_collateral": 0.0, "last_buy_timestamp": None,
                "buy_blocked_by_macd": False, "entries": []
            },
            "short": {
                "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                "total_collateral": 0.0, "last_buy_timestamp": None,
                "sell_blocked_by_macd": False, "entries": []
            }
        }

    common_index = data_frames[coin_list[0]].index
    for ticker in coin_list[1:]:
        if ticker in data_frames:
            common_index = common_index.intersection(data_frames[ticker].index)
    common_index = common_index.sort_values()

    if common_index.empty:
        print("공통 데이터 기간이 없습니다.")
        return pd.DataFrame(), {}, set(), {}, 0.0, {}, 0.0, 0.0, 0, 0, 0, 0, 0, 0

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
                print(f"[{current_time.strftime('%Y-%m-%d')}] 💸 {target_year}년 {target_month}월 수익금 출금: {withdrawal_amount:,.2f} USDT")

        current_portfolio_value = cash
        for ticker, df in data_frames.items():
            if current_time not in df.index: continue
            pos = positions[ticker]
            long_pos = pos['long']
            short_pos = pos['short']
            data_till_now = df.loc[:current_time]
            if len(data_till_now) < 3: continue

            prev_candle = data_till_now.iloc[-2]
            prev_prev_candle = data_till_now.iloc[-3]
            current_candle = data_till_now.iloc[-1]
            mtm_price = current_candle['close']
            execution_price = current_candle['open']

            if USE_MACD_BUY_LOCK and long_pos['buy_blocked_by_macd'] and prev_candle['macd_histogram'] > 0:
                long_pos['buy_blocked_by_macd'] = False
            if USE_SHORT_STRATEGY and short_pos['sell_blocked_by_macd'] and prev_candle['macd_histogram'] < 0:
                short_pos['sell_blocked_by_macd'] = False

            unrealized_pnl_long = 0
            if long_pos['total_quantity'] > 0:
                unrealized_pnl_long = (mtm_price - long_pos['average_price']) * long_pos['total_quantity']
                current_portfolio_value += (long_pos['total_collateral'] + unrealized_pnl_long)

            unrealized_pnl_short = 0
            if short_pos['total_quantity'] > 0:
                unrealized_pnl_short = (short_pos['average_price'] - mtm_price) * short_pos['total_quantity']
                current_portfolio_value += (short_pos['total_collateral'] + unrealized_pnl_short)

            if long_pos['current_entry_count'] > 0:
                entries_to_sell_indices, sell_reason = [], ""
                is_ma_cross_up = prev_candle['high'] > prev_candle['ma30'] and prev_prev_candle['close'] < prev_prev_candle['ma30']
                if is_ma_cross_up:
                    entries_to_sell_indices = [i for i, e in enumerate(long_pos['entries']) if e['price'] < prev_candle['ma30']]
                    if entries_to_sell_indices: sell_reason = "30MA 상향 돌파"
                elif prev_candle['close'] > prev_candle['bb_upper']:
                    # <<< [수정 시작] BB 상단 돌파 시, 수익성 판단 기준을 prev_candle['close']로 통일 >>>
                    if prev_candle['close'] > long_pos['average_price']:
                        entries_to_sell_indices = list(range(len(long_pos['entries'])))
                        sell_reason = "BB 상단 돌파 (전체 익절)"
                    else:
                        entries_to_sell_indices = [i for i, e in enumerate(long_pos['entries']) if prev_candle['close'] > e['price']]
                        if entries_to_sell_indices: sell_reason = "BB 상단 돌파 (부분 익절)"
                    # <<< [수정 끝] >>>

                if entries_to_sell_indices:
                    sold_entries = [long_pos['entries'][i] for i in entries_to_sell_indices]
                    gross_pnl = sum([(execution_price - e['price']) * e['quantity'] for e in sold_entries])
                    total_buy_fee = sum(e.get('buy_fee', 0) for e in sold_entries)
                    qty_sold = sum(e['quantity'] for e in sold_entries)
                    sell_fee = (qty_sold * execution_price) * FEE_RATE
                    net_pnl = gross_pnl - total_buy_fee - sell_fee

                    # 상세 PNL 계산 로그 출력
                    if len(sold_entries) == long_pos['current_entry_count']:
                        print(f"[{current_time}] 💰 {ticker} [LONG] 포지션 전체 익절 (사유: {sell_reason}).")
                        total_long_position_closed += 1
                    else:
                        print(f"[{current_time}] 💰 {ticker} [LONG] 부분 매도 (사유: {sell_reason}).")

                    # print(f"    - PNL 계산 상세 내역:")
                    # print(f"    - (1) 매도 실행 가격: {execution_price:,.5f}")
                    # print(f"    - (2) 총 매매 손익 (Gross PNL): {gross_pnl:,.2f} USDT")
                    # print(f"        └ (매도 실행 가격 - 각 진입 가격) * 수량 의 합계")
                    # print(f"    - (3) 총 매수 수수료 (매도 대상): {total_buy_fee:,.2f} USDT")
                    # print(f"    - (4) 매도 수수료: {sell_fee:,.2f} USDT")
                    # print(f"        └ (총 매도 수량 {qty_sold:.4f} * 매도 실행 가격) * 수수료율 {FEE_RATE}")
                    print(f"    - >> 최종 순손익 (Net PNL): {net_pnl:,.2f} USDT <<")
                    # print(f"        └ (2)총 매매 손익 - (3)총 매수 수수료 - (4)매도 수수료")

                    daily_fees[current_date] = daily_fees.get(current_date, 0) + total_buy_fee + sell_fee
                    daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl
                    total_long_pnl += net_pnl
                    total_long_trades += len(entries_to_sell_indices)

                    removed_collateral = sum([(e['price'] * e['quantity'] / LEVERAGE) for e in sold_entries])
                    cash += removed_collateral + net_pnl
                    long_pos['total_collateral'] -= removed_collateral

                    for i in sorted(entries_to_sell_indices, reverse=True): del long_pos['entries'][i]
                    for new_idx, entry in enumerate(long_pos['entries']): entry['entry_num'] = new_idx + 1
                    long_pos['current_entry_count'] = len(long_pos['entries'])

                    if long_pos['current_entry_count'] == 0:
                        new_allocated_asset = cash / len(data_frames)
                        positions[ticker]['long'].update({
                            "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0,
                            "total_collateral": 0.0, "last_buy_timestamp": None,
                            "buy_blocked_by_macd": False, "entries": []
                        })
                        positions[ticker]['allocated_capital'] = new_allocated_asset
                        positions[ticker]['base_buy_amount'] = new_allocated_asset * BASE_BUY_RATE
                    else:
                        long_pos['total_quantity'] = sum(e['quantity'] for e in long_pos['entries'])
                        long_pos['average_price'] = sum(e['price'] * e['quantity'] for e in long_pos['entries']) / long_pos['total_quantity']

                    if (short_pos['current_entry_count'] - long_pos['current_entry_count']) >= 4 and short_pos['current_entry_count'] > 0:
                        print(f"[{current_time}] 밸런스 조정! ↔️ {ticker} [ACTION] 롱 포지션 정리로 숏/롱 격차 발생. 숏 1개 강제 정리.")

                        entry_to_close_s = short_pos['entries'].pop(-1)
                        gross_pnl_s = (entry_to_close_s['price'] - execution_price) * entry_to_close_s['quantity']
                        sell_fee_s = entry_to_close_s.get('sell_fee', 0)
                        buy_back_fee = (entry_to_close_s['quantity'] * execution_price) * FEE_RATE
                        net_pnl_s = gross_pnl_s - sell_fee_s - buy_back_fee

                        daily_fees[current_date] = daily_fees.get(current_date, 0) + sell_fee_s + buy_back_fee
                        daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl_s
                        total_short_pnl += net_pnl_s

                        removed_collateral_s = (entry_to_close_s['price'] * entry_to_close_s['quantity'] / LEVERAGE)
                        cash += removed_collateral_s + net_pnl_s
                        short_pos['total_collateral'] -= removed_collateral_s

                        total_short_trades += 1
                        short_pos['current_entry_count'] = len(short_pos['entries'])

                        if short_pos['current_entry_count'] == 0:
                            print(f"    - 조정으로 모든 숏 포지션이 정리되었습니다. Net PNL: {net_pnl_s:,.2f} USDT")
                            total_short_position_closed += 1
                            positions[ticker]['short'].update({"current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0, "total_collateral": 0.0, "last_buy_timestamp": None, "sell_blocked_by_macd": False, "entries": []})
                        else:
                            short_pos['total_quantity'] = sum(e['quantity'] for e in short_pos['entries'])
                            short_pos['average_price'] = sum(e['price'] * e['quantity'] for e in short_pos['entries']) / short_pos['total_quantity']
                            print(f"    - 숏 강제 정리 완료. Net PNL: {net_pnl_s:,.2f} USDT. 남은 숏 수량: {short_pos['total_quantity']:.4f}")

                    continue

            if long_pos['current_entry_count'] < MAX_LONG_BUY_COUNT:
                base_buy_cond = prev_candle['rsi'] < 25 and prev_candle['close'] < prev_candle['bb_lower']
                should_buy = False
                if base_buy_cond:
                    if long_pos['current_entry_count'] == 0:
                        should_buy = True
                        total_long_position_opened += 1
                    else:
                        last_buy_time = long_pos['last_buy_timestamp']
                        reset_check = df.loc[(df.index > last_buy_time) & (df.index <= prev_candle.name)]
                        if not reset_check.empty and (reset_check['rsi'] > 25).any(): should_buy = True
                        elif get_rsi_level(prev_candle['rsi']) > get_rsi_level(long_pos['entries'][-1]['trigger_rsi']): should_buy = True

                if should_buy:
                    is_prev_day_close_below_ma = current_candle.get('prev_tf_close_below_ma30', False)
                    long_short_diff = long_pos['current_entry_count'] - short_pos['current_entry_count']

                    if is_prev_day_close_below_ma and long_short_diff >= LONG_ENTRY_LOCK_SHORT_COUNT_DIFF:
                        should_buy = False

                if should_buy and not long_pos['buy_blocked_by_macd'] and short_pos['current_entry_count'] > 0 and USE_SHORT_STRATEGY:
                    entries_to_close_s = [e for e in short_pos['entries'] if e['price'] > execution_price]
                    indices_to_close_s = [i for i, e in enumerate(short_pos['entries']) if e['price'] > execution_price]
                    if entries_to_close_s:
                        print(f"[{current_time}] ↔️ {ticker} [ACTION] 롱 진입으로 수익 중인 숏 포지션 정리 ({len(entries_to_close_s)}/{short_pos['current_entry_count']}개).")
                        gross_pnl_s = sum([(e['price'] - execution_price) * e['quantity'] for e in entries_to_close_s])
                        total_sell_fee = sum(e.get('sell_fee', 0) for e in entries_to_close_s)
                        qty_to_buy_back = sum(e['quantity'] for e in entries_to_close_s)
                        buy_back_fee = (qty_to_buy_back * execution_price) * FEE_RATE
                        net_pnl_s = gross_pnl_s - total_sell_fee - buy_back_fee
                        daily_fees[current_date] = daily_fees.get(current_date, 0) + total_sell_fee + buy_back_fee
                        daily_realized_pnl[current_date] = daily_realized_pnl.get(current_date, 0) + net_pnl_s
                        total_short_pnl += net_pnl_s
                        removed_collateral_s = sum([(e['price'] * e['quantity'] / LEVERAGE) for e in entries_to_close_s])
                        cash += removed_collateral_s + net_pnl_s
                        short_pos['total_collateral'] -= removed_collateral_s
                        total_short_trades += len(entries_to_close_s)
                        for i in sorted(indices_to_close_s, reverse=True): del short_pos['entries'][i]
                        for new_idx, entry in enumerate(short_pos['entries']): entry['entry_num'] = new_idx + 1
                        short_pos['current_entry_count'] = len(short_pos['entries'])
                        if short_pos['current_entry_count'] == 0:
                            print(f"    - 모든 숏 포지션이 정리되었습니다. Net PNL: {net_pnl_s:,.2f} USDT")
                            total_short_position_closed += 1
                            positions[ticker]['short'].update({ "current_entry_count": 0, "average_price": 0.0, "total_quantity": 0.0, "total_collateral": 0.0, "last_buy_timestamp": None, "sell_blocked_by_macd": False, "entries": [] })
                        else:
                            short_pos['total_quantity'] = sum(e['quantity'] for e in short_pos['entries'])
                            short_pos['average_price'] = sum(e['price'] * e['quantity'] for e in short_pos['entries']) / short_pos['total_quantity']
                            print(f"    - 숏 부분 정리 완료. Net PNL: {net_pnl_s:,.2f} USDT. 남은 숏 수량: {short_pos['total_quantity']:.4f}")

                if should_buy and not long_pos['buy_blocked_by_macd']:
                    next_entry_num = long_pos['current_entry_count'] + 1

                    # <<< [수정] 매수 금액 계산 로직을 단순화 및 명확화 >>>
                    buy_collateral = 0
                    if USE_DYNAMIC_BASE_BUY_AMOUNT:
                        # 동적 모드: '매 진입 시점'의 가용 현금을 기준으로 기초 매수액을 계산
                        base_amount = cash * BASE_BUY_RATE
                        buy_collateral = get_buy_amount(base_amount, get_rsi_level(prev_candle['rsi']), next_entry_num) if USE_ADDITIVE_BUYING else base_amount
                    else:
                        # 고정 모드: 사이클 시작 시점에 계산된 'base_buy_amount'를 사용
                        buy_collateral = get_buy_amount(pos['base_buy_amount'], get_rsi_level(prev_candle['rsi']), next_entry_num) if USE_ADDITIVE_BUYING else pos['base_buy_amount']

                    if cash >= buy_collateral:
                        buy_price = execution_price
                        quantity_to_buy = (buy_collateral * LEVERAGE) / buy_price
                        buy_fee = (buy_collateral * LEVERAGE) * FEE_RATE
                        daily_fees[current_date] = daily_fees.get(current_date, 0) + buy_fee
                        print(f"[{current_time}] 📈 {ticker} [LONG] 매수 ({next_entry_num}차): 가격 {buy_price:.5f}, 금액 {buy_collateral:,.2f} USDT, RSI {prev_candle['rsi']:.2f}")
                        if next_entry_num == 1: new_cycle_dates.add(current_time.date())
                        cash -= buy_collateral
                        long_pos['total_collateral'] += buy_collateral
                        long_pos['entries'].append({
                            "entry_num": next_entry_num, "price": buy_price, "quantity": quantity_to_buy,
                            "timestamp": current_time, "trigger_rsi": prev_candle['rsi'], "buy_fee": buy_fee
                        })
                        long_pos['current_entry_count'] += 1
                        long_pos['last_buy_timestamp'] = current_time
                        long_pos['total_quantity'] = sum(e['quantity'] for e in long_pos['entries'])
                        long_pos['average_price'] = sum(e['price'] * e['quantity'] for e in long_pos['entries']) / long_pos['total_quantity']
                        total_long_trades += 1
                        if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] < 0:
                            long_pos['buy_blocked_by_macd'] = True

            # 일반 숏 포지션 진입 로직
            if USE_SHORT_STRATEGY and short_pos['current_entry_count'] < MAX_SHORT_BUY_COUNT:

                if (short_pos['current_entry_count'] - long_pos['current_entry_count']) >= 3:
                    pass
                else:
                    short_cond_tf = current_candle.get('prev_tf_close_below_ma30', False) and \
                                      current_candle.get('prev_tf_macd_hist_neg', False) and \
                                      not current_candle.get('prev_tf_ma30_3day_rising', False)

                    current_short_entry_rsi = SHORT_ENTRY_RSI

                    prev_tf_adx_value = current_candle.get('prev_tf_adx', 0)
                    if long_pos['current_entry_count'] >= 4 and prev_tf_adx_value >= 30:
                        current_short_entry_rsi = SHORT_ENTRY_RSI - SHORT_RSI_ADJUSTMENT

                    short_cond_15m = prev_candle['rsi'] >= current_short_entry_rsi

                    should_short = False
                    if short_cond_tf and short_cond_15m:
                        if short_pos['current_entry_count'] == 0:
                            should_short = True
                            total_short_position_opened += 1
                        else:
                            last_short_time = short_pos['last_buy_timestamp']
                            reset_check_s = df.loc[(df.index > last_short_time) & (df.index <= prev_candle.name)]
                            if not reset_check_s.empty and (reset_check_s['rsi'] < current_short_entry_rsi).any():
                                should_short = True

                    if should_short and not short_pos['sell_blocked_by_macd']:
                        next_entry_num = short_pos['current_entry_count'] + 1

                        # <<< [수정] 매도 금액 계산 로직을 단순화 및 명확화 >>>
                        sell_collateral = 0
                        if USE_DYNAMIC_BASE_BUY_AMOUNT:
                             # 동적 모드: '매 진입 시점'의 가용 현금을 기준으로 매도액 계산
                             sell_collateral = cash * BASE_BUY_RATE
                        else:
                            # 고정 모드: 사이클 시작 시점에 계산된 'base_buy_amount'를 사용
                            sell_collateral = pos['base_buy_amount']

                        if cash >= sell_collateral:
                            sell_price = execution_price
                            quantity_to_sell = (sell_collateral * LEVERAGE) / sell_price
                            sell_fee = (sell_collateral * LEVERAGE) * FEE_RATE
                            daily_fees[current_date] = daily_fees.get(current_date, 0) + sell_fee
                            print(f"[{current_time}] 📉 {ticker} [SHORT] 매도 ({next_entry_num}차): 가격 {sell_price:.5f}, 금액 {sell_collateral:,.2f} USDT, RSI {prev_candle['rsi']:.2f}")
                            if next_entry_num == 1: new_cycle_dates.add(current_time.date())
                            cash -= sell_collateral
                            short_pos['total_collateral'] += sell_collateral
                            short_pos['entries'].append({
                                "entry_num": next_entry_num, "price": sell_price, "quantity": quantity_to_sell,
                                "timestamp": current_time, "trigger_rsi": prev_candle['rsi'], "sell_fee": sell_fee
                            })
                            short_pos['current_entry_count'] += 1
                            short_pos['last_buy_timestamp'] = current_time
                            short_pos['total_quantity'] = sum(e['quantity'] for e in short_pos['entries'])
                            short_pos['average_price'] = sum(e['price'] * e['quantity'] for e in short_pos['entries']) / short_pos['total_quantity']
                            total_short_trades += 1
                            if USE_MACD_BUY_LOCK and prev_candle['macd_histogram'] > 0:
                                short_pos['sell_blocked_by_macd'] = True

        previous_time = current_time
        total_long_entries = sum(p['long'].get('current_entry_count', 0) for p in positions.values())
        total_short_entries = sum(p['short'].get('current_entry_count', 0) for p in positions.values())

        portfolio_history.append({
            'timestamp': current_time,
            'value': current_portfolio_value,
            'long_entry_count': total_long_entries,
            'short_entry_count': total_short_entries
        })

    return (pd.DataFrame(portfolio_history).set_index('timestamp'), daily_realized_pnl, new_cycle_dates,
            monthly_withdrawals, total_withdrawn, daily_fees, total_long_pnl, total_short_pnl,
            total_long_position_opened, total_long_position_closed, total_long_trades,
            total_short_position_opened, total_short_position_closed, total_short_trades)

# ==============================================================================
# 4. 결과 분석 및 시각화 함수
# (이전과 동일)
# ==============================================================================
def analyze_and_plot_results(portfolio_df, realized_pnl_data, new_cycle_dates, monthly_withdrawals, total_withdrawn, daily_fees, total_long_pnl, total_short_pnl,
                             total_long_position_opened, total_long_position_closed, total_long_trades,
                             total_short_position_opened, total_short_position_closed, total_short_trades):
    """백테스트 결과를 분석하고 그래프로 시각화합니다. (경고 수정 버전)"""
    if portfolio_df.empty:
        print("백테스트 결과가 없어 분석을 종료합니다.")
        return

    final_value = portfolio_df['value'].iloc[-1]

    # --- MDD 계산을 위한 데이터 준비 ---
    withdrawal_series = pd.Series(monthly_withdrawals)
    if not withdrawal_series.empty:
        withdrawal_series.index = pd.to_datetime(withdrawal_series.index, format='%Y-%m').to_period('M').asfreq('M', 'end').to_timestamp() + pd.Timedelta(days=1)
        daily_cumulative_withdrawals = withdrawal_series.resample('D').sum().cumsum()
        portfolio_df = portfolio_df.join(daily_cumulative_withdrawals.rename('cumulative_withdrawal'))

        # --- 수정된 부분 1: fillna(method=...) 경고 해결 및 연쇄 할당 경고 해결 ---
        # portfolio_df['cumulative_withdrawal'].fillna(method='ffill', inplace=True) -> 아래 코드로 변경
        portfolio_df['cumulative_withdrawal'] = portfolio_df['cumulative_withdrawal'].ffill()

    else:
        portfolio_df['cumulative_withdrawal'] = 0

    # --- 수정된 부분 2: 연쇄 할당 경고 해결 ---
    # portfolio_df['cumulative_withdrawal'].fillna(0, inplace=True) -> 아래 코드로 변경
    portfolio_df['cumulative_withdrawal'] = portfolio_df['cumulative_withdrawal'].fillna(0)

    portfolio_df['adjusted_value'] = portfolio_df['value'] + portfolio_df['cumulative_withdrawal']

    def get_top_mdds(balance_series, value_series):
        peak_series = balance_series.cummax()
        drawdown_series = (peak_series - balance_series) / peak_series.replace(0, np.nan)
        # --- 수정된 부분 3: 연쇄 할당 경고 해결 ---
        # drawdown_series.fillna(0, inplace=True) -> 아래 코드로 변경
        drawdown_series = drawdown_series.fillna(0)

        periods = []
        is_in_dd = False
        start_idx = 0
        for i in range(len(drawdown_series)):
            if not is_in_dd and drawdown_series.iloc[i] > 0:
                is_in_dd = True
                peak_idx = i - 1 if i > 0 else 0
                start_idx = peak_idx
            elif is_in_dd and drawdown_series.iloc[i] == 0:
                is_in_dd = False
                period_slice = drawdown_series.iloc[start_idx:i]
                if not period_slice.empty:
                    trough_date = period_slice.idxmax()
                    periods.append({'max_dd': period_slice.loc[trough_date], 'peak_date': balance_series.index[start_idx], 'peak_value': balance_series.iloc[start_idx], 'trough_date': trough_date, 'trough_value': balance_series.loc[trough_date]})
        if is_in_dd:
             period_slice = drawdown_series.iloc[start_idx:]
             if not period_slice.empty:
                trough_date = period_slice.idxmax()
                periods.append({'max_dd': period_slice.loc[trough_date], 'peak_date': balance_series.index[start_idx], 'peak_value': balance_series.iloc[start_idx], 'trough_date': trough_date, 'trough_value': balance_series.loc[trough_date]})
        return sorted(periods, key=lambda x: x['max_dd'], reverse=True)[:3]

    mdd_performance = get_top_mdds(portfolio_df['adjusted_value'], portfolio_df['adjusted_value'])
    mdd_equity = get_top_mdds(portfolio_df['value'], portfolio_df['value'])

    def format_mdd_string(mdd_list, prefix="성과"):
        info_str = ""
        if not mdd_list: return "  - 0.00% (No drawdown recorded)"
        for i, mdd in enumerate(mdd_list):
            info_str += (f"    - [TOP {i+1}] {mdd['max_dd']*100:.2f}% (Peak: {mdd['peak_value']:,.0f} USDT on {mdd['peak_date'].strftime('%Y-%m-%d')} -> Trough: {mdd['trough_value']:,.0f} USDT on {mdd['trough_date'].strftime('%Y-%m-%d')})")
            if i < len(mdd_list) - 1: info_str += "\n"
        return info_str

    mdd_perf_str = format_mdd_string(mdd_performance, prefix="성과")
    mdd_equity_str = format_mdd_string(mdd_equity, prefix="실제잔고")

    daily_summary = portfolio_df[['value', 'adjusted_value', 'long_entry_count', 'short_entry_count']].resample('D').last().ffill()
    realized_pnl_series = pd.Series(realized_pnl_data, name="Realized PNL")

    if not realized_pnl_series.empty:
        realized_pnl_series.index = pd.to_datetime(realized_pnl_series.index)
        daily_summary = daily_summary.join(realized_pnl_series.resample('D').sum())

    # --- 수정된 부분 4: 연쇄 할당 경고 해결 ---
    # daily_summary['Realized PNL'].fillna(0, inplace=True) -> 아래 코드로 변경
    daily_summary['Realized PNL'] = daily_summary['Realized PNL'].fillna(0)

    total_realized_pnl = daily_summary['Realized PNL'].sum()
    daily_summary['Cumulative Realized PNL'] = daily_summary['Realized PNL'].cumsum()
    fees_series = pd.Series(daily_fees, name="fees")

    if not fees_series.empty:
        fees_series.index = pd.to_datetime(fees_series.index)
        daily_summary = daily_summary.join(fees_series.resample('D').sum())

    # --- 수정된 부분 5: 연쇄 할당 경고 해결 ---
    # daily_summary['fees'].fillna(0, inplace=True) -> 아래 코드로 변경
    daily_summary['fees'] = daily_summary['fees'].fillna(0)

    # --- 수정된 부분 6: resample('M') 경고 해결 ---
    # monthly_summary = daily_summary.resample('M').agg(...) -> 'ME'로 변경
    monthly_summary = daily_summary.resample('ME').agg({'value': 'last', 'Realized PNL': 'sum', 'fees': 'sum'})

    monthly_summary['begin_value'] = monthly_summary['value'].shift(1).fillna(INITIAL_CAPITAL)
    monthly_summary['monthly_return'] = (monthly_summary['Realized PNL'] / monthly_summary['begin_value'].replace(0, np.nan)) * 100
    monthly_summary.index = monthly_summary.index.strftime('%Y-%m')
    monthly_withdrawal_series = pd.Series(monthly_withdrawals, name="Withdrawal")
    monthly_summary = monthly_summary.join(monthly_withdrawal_series)

    # --- 수정된 부분 7: 연쇄 할당 경고 해결 ---
    # monthly_summary['Withdrawal'].fillna(0, inplace=True) -> 아래 코드로 변경
    monthly_summary['Withdrawal'] = monthly_summary['Withdrawal'].fillna(0)

    # (이하 출력 및 시각화 부분은 동일)
    print("\n" + "="*110 + "\n" + " " * 35 + "일별 요약 (실현 손익 기준)\n" + "="*110)
    for index, row in daily_summary.iterrows():
        new_cycle_marker = " « 신규 포지션" if index.date() in new_cycle_dates else ""
        long_entry_count = int(row.get('long_entry_count', 0)); short_entry_count = int(row.get('short_entry_count', 0))
        position_str = f"롱:{long_entry_count}개, 숏:{short_entry_count}개"
        print(f"{index.strftime('%Y-%m-%d')}: 총잔액:{row['value']:>12,.2f} USDT,  일일 실현 Net PNL:{row['Realized PNL']:>+11,.2f} USDT,  누적 실현 Net PNL:{row['Cumulative Realized PNL']:>12,.2f} USDT,  포지션: {position_str:<15}" + new_cycle_marker)
    print("="*110)

    print("\n" + "="*125 + "\n" + " " * 45 + "월별 요약 (실현 손익 기준)\n" + "="*125)
    for index, row in monthly_summary.iterrows():
        print(f"{index}: 총잔액:{row['value']:>12,.2f} USDT,   월별 실현 Net PNL:{row['Realized PNL']:>+11,.2f} USDT,   수익률: {row.get('monthly_return', 0):>+7.2f}%,   수수료: {row.get('fees', 0):>8,.2f} USDT,   출금액: {row['Withdrawal']:>10,.2f} USDT")
    print("="*125)

    total_return_if_no_withdrawal = ((final_value + total_withdrawn) / INITIAL_CAPITAL - 1) * 100
    print("\n" + "="*80 + "\n" + " " * 30 + "백테스트 최종 결과\n" + "="*80)
    print(f"  - 시작 자본: {INITIAL_CAPITAL:,.2f} USDT"); print(f"  - 최종 자산: {final_value:,.2f} USDT")
    print(f"  - 총 실현 손익: {total_realized_pnl:,.2f} USDT"); print(f"    - 롱 포지션 수익: {total_long_pnl:,.2f} USDT"); print(f"    - 숏 포지션 수익: {total_short_pnl:,.2f} USDT")
    print(f"  - 총 출금액: {total_withdrawn:,.2f} USDT"); total_fees = sum(daily_fees.values()); print(f"  - 총 수수료: {total_fees:,.2f} USDT")
    print(f"  - 총 수익률 (출금액 포함 가정): {total_return_if_no_withdrawal:.2f}%")
    print("-" * 80); print(f"  - MDD (전략 성과 기준 / 출금 영향 제거):\n{mdd_perf_str}"); print(f"  - MDD (실제 자산 기준 / 청산 위험성 참고):\n{mdd_equity_str}")
    print("    (참고: '실제 자산 기준 MDD'는 출금도 자산 감소로 계산되어 변동성이 크게 나타날 수 있습니다.)")
    print("\n" + " " * 31 + "최종 거래 횟수\n" + "-"*80); print(f"  - 롱 포지션 시작/종료: {total_long_position_opened}회 / {total_long_position_closed}회"); print(f"  - 롱 포지션 총 거래(매수/매도) 횟수: {total_long_trades}회")
    print(f"  - 숏 포지션 시작/종료: {total_short_position_opened}회 / {total_short_position_closed}회"); print(f"  - 숏 포지션 총 거래(매수/매도) 횟수: {total_short_trades}회")
    print("="*80)

    plt.figure(figsize=(15, 10))
    try: plt.rc('font', family='Malgun Gothic')
    except: plt.rc('font', family='AppleGothic')
    plt.rcParams['axes.unicode_minus'] = False

    ax1 = plt.subplot(2, 1, 1); portfolio_df['adjusted_value'].plot(ax=ax1, label='전략 성과 자산 (출금 보정)'); portfolio_df['value'].plot(ax=ax1, label='실제 계좌 자산', linestyle='--')
    ax1.set_title('자산 추이 비교'); ax1.set_ylabel('자산 가치 (USDT)'); ax1.grid(True); ax1.legend()

    ax2 = plt.subplot(2, 1, 2)
    mdd_perf_series = (portfolio_df['value'].cummax() - portfolio_df['value']) / portfolio_df['value'].cummax()
    (mdd_perf_series * 100).plot(ax=ax2, title='최대 낙폭 (MDD, 전략 성과 기준)', color='red')
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
            df_with_indicators = calculate_indicators(df)
            df_with_secondary_indicators = add_secondary_timeframe_indicators(df_with_indicators, SHORT_CONDITION_TIMEFRAME)
            all_data_frames[coin_ticker] = df_with_secondary_indicators.dropna()

    if not all_data_frames:
        print("백테스트를 위한 데이터를 로드하지 못했습니다. 프로그램을 종료합니다.")
    else:
        portfolio_result, realized_pnl, new_cycles, monthly_withdrawals, total_withdrawn, daily_fees, total_long_pnl, total_short_pnl, \
        total_long_position_opened, total_long_position_closed, total_long_trades, \
        total_short_position_opened, total_short_position_closed, total_short_trades = run_backtest(all_data_frames)

        analyze_and_plot_results(portfolio_result, realized_pnl, new_cycles, monthly_withdrawals, total_withdrawn, daily_fees, total_long_pnl, total_short_pnl,
                                 total_long_position_opened, total_long_position_closed, total_long_trades,
                                 total_short_position_opened, total_short_position_closed, total_short_trades)