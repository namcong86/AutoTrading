# -*- coding: utf-8 -*-
import ccxt
import pandas as pd
import numpy as np
import datetime
import time
from pycoingecko import CoinGeckoAPI

# --- 기본 설정 (수정됨) ---
exchange = ccxt.binance({'enableRateLimit': True, 'options': {'defaultType': 'spot'}}) 
cg = CoinGeckoAPI()

EXISTING_COINS = []
STABLECOINS = ['USDT', 'USDC', 'DAI', 'FDUSD', 'TUSD', 'USDP']
BACKTEST_START_DATE = {'year': 2022, 'month': 7, 'day': 1}
# 분석할 시가총액 순위 (100위까지 분석하기 위해 넉넉하게 140위까지 조회)
MARKET_CAP_RANK_LIMIT = 140 

# --- 데이터 수집 함수 (이전과 동일) ---
def get_historical_data(ticker, start_date):
    """지정된 티커와 시작일부터 현재까지의 일봉 데이터를 가져옵니다."""
    try:
        start_timestamp = int(datetime.datetime(start_date['year'], start_date['month'], start_date['day']).timestamp() * 1000)
        all_ohlcv = []
        
        while True:
            ohlcv = exchange.fetch_ohlcv(ticker, '1d', since=start_timestamp, limit=1000)
            if not ohlcv:
                break
            all_ohlcv.extend(ohlcv)
            start_timestamp = ohlcv[-1][0] + (24 * 60 * 60 * 1000)
            if start_timestamp > int(datetime.datetime.now().timestamp() * 1000):
                break
            time.sleep(exchange.rateLimit / 1000)

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        df = df[~df.index.duplicated(keep='first')]
        return df
    except Exception as e:
        print(f"  > '{ticker}' 데이터 수집 중 오류: {e}")
        return pd.DataFrame()

# --- 백테스팅 로직을 담은 함수 (이전과 동일) ---
def run_backtest_for_coin(ticker, start_date):
    """단일 코인에 대해 제공된 매수/매도 로직으로 백테스팅을 실행하고 결과를 반환합니다."""
    
    # 1. 데이터 가져오기 및 지표 계산
    df = get_historical_data(ticker, start_date)
    if df.empty or len(df) < 200:
        print(f"  > '{ticker}'의 데이터가 부족하여 분석을 건너뜁니다.")
        return None
        
    period_rsi = 14
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period_rsi - 1), min_periods=period_rsi).mean()
    _loss = down.abs().ewm(com=(period_rsi - 1), min_periods=period_rsi).mean()
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)))
    df['rsi_ma'] = df['rsi'].rolling(14).mean()
    for ma in [3, 7, 20, 30, 50]:
        df[f'{ma}ma'] = df['close'].rolling(ma).mean()
    df['200ma'] = df['close'].rolling(200).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    df.dropna(inplace=True)

    if df.empty:
        return None

    # 2. 백테스팅 루프
    initial_balance = 10000 
    balance = initial_balance
    position = None 
    trade_count = 0
    win_count = 0
    equity_history = []

    for i in range(2, len(df)):
        open_price = df['open'].iloc[i]
        
        if position:
            revenue_rate = (open_price - position['entry_price']) / position['entry_price']
            def is_doji_candle(row):
                candle_range = row['high'] - row['low']
                if candle_range == 0: return False
                return (abs(row['open'] - row['close']) / candle_range) <= 0.1

            is_doji_1 = is_doji_candle(df.iloc[i-1])
            is_doji_2 = is_doji_candle(df.iloc[i-2])
            cond_sell_price_fall = (df['high'].iloc[i-2] > df['high'].iloc[i-1] and df['low'].iloc[i-2] > df['low'].iloc[i-1])
            cond_sell_two_red = (df['open'].iloc[i-1] > df['close'].iloc[i-1] and df['open'].iloc[i-2] > df['close'].iloc[i-2])
            cond_sell_is_losing = (revenue_rate < 0)
            except_sell_strong_up = (df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1] and df['3ma'].iloc[i-2] < df['3ma'].iloc[i-1])
            cond_sell_dojis = (is_doji_1 and is_doji_2)
            sell_main_condition = (cond_sell_price_fall or cond_sell_two_red or cond_sell_is_losing) and not except_sell_strong_up
            
            if sell_main_condition or cond_sell_dojis:
                balance *= (1 + revenue_rate)
                trade_count += 1
                if revenue_rate > 0:
                    win_count += 1
                position = None

        if not position:
            cond_buy_two_green = (df['open'].iloc[i-1] < df['close'].iloc[i-1] and df['open'].iloc[i-2] < df['close'].iloc[i-2])
            cond_buy_price_up = (df['close'].iloc[i-2] < df['close'].iloc[i-1] and df['high'].iloc[i-2] < df['high'].iloc[i-1])
            cond_buy_short_ma_up = (df['7ma'].iloc[i-2] < df['7ma'].iloc[i-1] and df['20ma'].iloc[i-2] <= df['20ma'].iloc[i-1])
            cond_buy_mid_ma_stable = (df['30ma_slope'].iloc[i-1] > -2)
            cond_buy_rsi_up = (df['rsi_ma'].iloc[i-2] < df['rsi_ma'].iloc[i-1])
            filter_no_sudden_surge = (df['change'].iloc[i-1] < 0.5)
            is_above_200ma = df['close'].iloc[i-1] > df['200ma'].iloc[i-1]
            filter_ma50_not_declining = True
            if is_above_200ma:
                filter_ma50_not_declining = (df['50ma'].iloc[i-2] <= df['50ma'].iloc[i-1])

            if (cond_buy_two_green and cond_buy_price_up and cond_buy_short_ma_up and 
                cond_buy_mid_ma_stable and cond_buy_rsi_up and filter_no_sudden_surge and 
                filter_ma50_not_declining):
                position = {'entry_price': open_price}
        
        current_equity = balance
        if position:
            current_equity = balance * (df['close'].iloc[i] / position['entry_price'])
        equity_history.append(current_equity)

    # 3. 성과 지표 계산
    if not equity_history:
        return None
    
    equity_series = pd.Series(equity_history, index=df.index[2:])
    days = (equity_series.index[-1] - equity_series.index[0]).days
    if days < 30: return None
    cagr = ( (equity_series.iloc[-1] / initial_balance) ** (365.0 / days) ) - 1
    roll_max = equity_series.cummax()
    daily_drawdown = equity_series / roll_max - 1.0
    mdd = daily_drawdown.min()
    win_rate = (win_count / trade_count) * 100 if trade_count > 0 else 0

    return {
        'ticker': ticker,
        'cagr': cagr * 100,
        'mdd': mdd * 100,
        'win_rate': win_rate,
        'trade_count': trade_count
    }

# --- 메인 실행 로직 (수정됨) ---
if __name__ == "__main__":
    print("🚀 유망 코인 분석을 시작합니다 (분석 대상: Top 100)...")
    
    # 1. 시총 상위 코인 목록 가져오기
    try:
        print(f"\n[1/4] 시가총액 상위 {MARKET_CAP_RANK_LIMIT}개 코인 목록을 가져옵니다...")
        market_data = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=MARKET_CAP_RANK_LIMIT, page=1)
        candidate_symbols = [coin['symbol'].upper() for coin in market_data]
        print(f"  > 총 {len(candidate_symbols)}개의 코인을 찾았습니다.")
    except Exception as e:
        print(f"  > CoinGecko API 호출에 실패했습니다: {e}")
        exit()

    # 2. 코인 필터링
    print("\n[2/4] 분석 대상 코인을 필터링합니다...")
    all_markets = exchange.load_markets()
    usdt_pairs = {s.split('/')[0] for s in all_markets if s.endswith('/USDT')}
    
    filtered_coins = []
    for symbol in candidate_symbols:
        if symbol not in EXISTING_COINS and symbol not in STABLECOINS and symbol in usdt_pairs:
            ticker = f"{symbol}/USDT"
            try:
                first_candle = exchange.fetch_ohlcv(ticker, '1d', since=exchange.parse8601('2017-01-01T00:00:00Z'), limit=1)
                if first_candle:
                    listing_date = datetime.datetime.fromtimestamp(first_candle[0][0] / 1000)
                    if listing_date < datetime.datetime(2024, 1, 1):
                        filtered_coins.append(ticker)
            except Exception:
                pass # 오류 발생 시 조용히 넘어감
    print(f"  > 필터링 후 총 {len(filtered_coins)}개의 코인이 분석 대상으로 선정되었습니다.")
    
    # 3. 개별 코인 백테스팅 실행
    print("\n[3/4] 각 코인에 대해 백테스팅을 실행합니다... (시간이 다소 소요될 수 있습니다)")
    results = []
    for i, ticker in enumerate(filtered_coins):
        print(f"  ({i+1}/{len(filtered_coins)}) '{ticker}' 분석 중...")
        result = run_backtest_for_coin(ticker, BACKTEST_START_DATE)
        if result and result['trade_count'] > 5: # 최소 거래 횟수 필터
            results.append(result)

    # 4. 결과 집계 및 순위 발표 (랭킹 로직 및 출력 형식 수정)
print("\n[4/4] 분석 완료! 종합 순위를 집계합니다.")
if not results:
    print("  > 유효한 백테스팅 결과가 없습니다. 필터링 조건을 확인해 주세요.")
else:
    # CAGR > 0 인 결과만 필터링
    positive_cagr_results = [res for res in results if res['cagr'] > 0]
    
    # CAGR과 MDD에 대해 각각 순위 매기기
    sorted_by_cagr = sorted(positive_cagr_results, key=lambda x: x['cagr'], reverse=True)
    sorted_by_mdd = sorted(positive_cagr_results, key=lambda x: x['mdd'], reverse=True)

    # 각 결과에 순위 정보 추가
    for res in positive_cagr_results:
        res['cagr_rank'] = next((i + 1 for i, item in enumerate(sorted_by_cagr) if item['ticker'] == res['ticker']), None)
        res['mdd_rank'] = next((i + 1 for i, item in enumerate(sorted_by_mdd) if item['ticker'] == res['ticker']), None)
        res['rank_sum'] = res['cagr_rank'] + res['mdd_rank']

    # 최종적으로 '순위 합계'가 낮은 순으로 정렬
    final_sorted_results = sorted(positive_cagr_results, key=lambda x: x['rank_sum'])
    
    print("\n" + "="*125)
    print("✨ 백테스팅 종합 순위 (전체) ✨")
    print("="*125)
    
    # 헤더 출력 (칸 너비 조정)
    header = (f"{'종합순위':<8} | {'티커':<12} | {'종합점수(↓)':<12} | "
              f"{'CAGR 순위':<10} | {'MDD 순위':<10} | {'연평균수익률(CAGR)':<22} | "
              f"{'최대낙폭(MDD)':<20} | {'승률':<20}")
    print(header)
    print("-"*125)
    
    # 데이터 행 출력 (출력 형식 수정)
    for i, res in enumerate(final_sorted_results):
        cagr_str = f"{res['cagr']:.2f}%"
        mdd_str = f"{res['mdd']:.2f}%"
        win_rate_str = f"{res['win_rate']:.2f}% ({res['trade_count']}회)"
        
        row = (f"{i+1:<8} | {res['ticker']:<12} | {res['rank_sum']:<12} | "
               f"{res['cagr_rank']:<10} | {res['mdd_rank']:<10} | {cagr_str:<22} | "
               f"{mdd_str:<20} | {win_rate_str:<20}")
        print(row)
    
    print("="*125)
    print("\n💡 해석 가이드:")
    print("  - **종합점수**: 'CAGR 순위'와 'MDD 순위'를 더한 값입니다. **점수가 낮을수록** 종합 성과가 우수하다는 의미입니다.")
    print("  - **CAGR 순위**: 연평균수익률이 높은 순서입니다. (1위가 가장 높음)")
    print("  - **MDD 순위**: 최대낙폭이 낮은 순서입니다. (1위가 가장 방어력이 좋음)")