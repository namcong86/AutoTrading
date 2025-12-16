# -*- coding:utf-8 -*-
"""
Bitget 코인 스크리닝 프로그램 (최적화 버전)
- 시가총액 상위 50위 코인 필터링
- Binance Spot 차트로 4년+ 데이터 존재 확인 (선물보다 기간이 김)
- 데이터를 로컬에 캐싱하여 재사용 (속도 향상)
- 골든/데드크로스 전략 백테스트 실행
- 수익률 기준 상위 10개 코인 출력
"""
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import requests
import os
import json
import warnings
warnings.filterwarnings('ignore')

# ==============================================================================
# 설정
# ==============================================================================
# 전략 파라미터 (5.Bitget_F_Long_Short_Alt와 동일)
SHORT_MA = 20           # 단기 이동평균
LONG_MA = 120           # 장기 이동평균
DAILY_MA = 115          # 일봉 이동평균 (방향 필터용)
LEVERAGE = 1.2          # 레버리지
FEE_RATE = 0.0006       # 수수료 (0.06%)

# 백테스트 설정
MIN_YEARS = 3           # 최소 데이터 기간 (년)
INITIAL_CAPITAL = 10000 # 초기 자본금 (USDT)

# 시가총액 필터링
TOP_MARKETCAP = 50      # 시가총액 상위 N개 코인만 분석

# 결과 설정
TOP_N = 10              # 상위 N개 코인 출력

# 제외할 코인 (이미 사용 중인 코인, 스테이블코인 등)
EXCLUDE_COINS = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'FDUSD']

# 데이터 캐시 경로 (download_17coins_candle_data.py와 동일한 폴더 사용)
CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'json', 'screener_coins')


# ==============================================================================
# 유틸리티 함수
# ==============================================================================
def ensure_cache_dir():
    """캐시 디렉토리 생성"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
        print(f"캐시 디렉토리 생성: {CACHE_DIR}")


def get_cache_path(symbol, timeframe):
    """캐시 파일 경로 반환 (JSON 형식)"""
    # XRP/USDT -> XRP_USDT
    clean_symbol = symbol.replace('/', '_').replace(':', '_')
    return os.path.join(CACHE_DIR, f"{clean_symbol}_{timeframe}.json")


def load_cached_data(symbol, timeframe):
    """캐시된 데이터 로드 (JSON 형식)"""
    cache_path = get_cache_path(symbol, timeframe)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            # 오늘 데이터가 있으면 캐시 사용
            if len(df) > 0:
                last_date = df.index[-1]
                if (datetime.now() - last_date).days <= 7:  # 7일 이내면 캐시 사용
                    return df
        except Exception as e:
            print(f"      캐시 로드 실패: {e}")
            pass
    return None


def save_cached_data(df, symbol, timeframe):
    """데이터를 캐시에 저장 (JSON 형식)"""
    ensure_cache_dir()
    cache_path = get_cache_path(symbol, timeframe)
    df_save = df.reset_index()
    df_save['datetime'] = df_save['datetime'].astype(str)
    data = df_save.to_dict('records')
    with open(cache_path, 'w') as f:
        json.dump(data, f)


# ==============================================================================
# API 함수
# ==============================================================================
def get_binance_exchange():
    """Binance Spot 거래소 객체 생성 (데이터 다운로드용)"""
    return ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}
    })


def get_bitget_exchange():
    """Bitget 거래소 객체 생성"""
    return ccxt.bitget({
        'enableRateLimit': True,
        'options': {'defaultType': 'swap'}
    })


def get_top_marketcap_coins(top_n=50):
    """CoinGecko API로 시가총액 상위 N개 코인 조회"""
    print(f"\n[0단계] 시가총액 상위 {top_n}위 코인 조회 중...")
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/markets"
        params = {
            'vs_currency': 'usd',
            'order': 'market_cap_desc',
            'per_page': top_n,
            'page': 1,
            'sparkline': 'false'
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        top_coins = [coin['symbol'].upper() for coin in data]
        
        print(f"   시가총액 상위 {len(top_coins)}개 코인 조회 완료")
        print(f"   (예: {', '.join(top_coins[:10])}...)")
        
        return top_coins
        
    except Exception as e:
        print(f"   CoinGecko API 오류: {e}")
        print("   기본 상위 코인 리스트 사용")
        return ['BTC', 'ETH', 'XRP', 'USDT', 'BNB', 'SOL', 'USDC', 'ADA', 'DOGE', 'TRX',
                'AVAX', 'LINK', 'SHIB', 'DOT', 'BCH', 'TON', 'NEAR', 'XLM', 'LTC', 'UNI',
                'MATIC', 'ICP', 'DAI', 'PEPE', 'ETC', 'HBAR', 'APT', 'ATOM', 'FIL', 'MNT',
                'IMX', 'CRO', 'RNDR', 'STX', 'OKB', 'VET', 'INJ', 'OP', 'ARB', 'WLD',
                'GRT', 'THETA', 'SUI', 'FTM', 'MKR', 'RUNE', 'ALGO', 'LDO', 'AAVE', 'FLOW']


def get_filtered_pairs(exchange_binance, exchange_bitget, top_coins):
    """Bitget에 존재하고 시가총액 상위인 페어 조회"""
    print("\n[1단계] Bitget 선물 페어 조회 중...")
    
    # Bitget 선물 마켓 조회
    bitget_markets = exchange_bitget.load_markets()
    bitget_pairs = {}
    
    for symbol, market in bitget_markets.items():
        if (market.get('swap', False) and 
            market.get('linear', False) and
            ':USDT' in symbol and
            market.get('active', True)):
            base = market.get('base', '')
            if base not in EXCLUDE_COINS and base in top_coins:
                bitget_pairs[base] = symbol
    
    # Binance Spot 마켓 조회 (데이터 다운로드용)
    binance_markets = exchange_binance.load_markets()
    
    result = []
    for base, bitget_symbol in bitget_pairs.items():
        binance_symbol = f"{base}/USDT"
        if binance_symbol in binance_markets:
            result.append({
                'base': base,
                'bitget_symbol': bitget_symbol,
                'binance_symbol': binance_symbol
            })
    
    print(f"   필터링 후 {len(result)}개 페어 발견")
    return result


def fetch_spot_ohlcv(exchange, symbol, timeframe='1h', years=3):
    """Binance Spot에서 OHLCV 데이터 수집 (캐시 활용)"""
    
    # 캐시 확인
    cached = load_cached_data(symbol, timeframe)
    if cached is not None:
        print(f"      캐시 사용: {len(cached)}개 캔들")
        return cached
    
    try:
        all_ohlcv = []
        limit = 1000  # Binance는 1000개까지 가능
        
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365 * years + 30)
        since = int(start_time.timestamp() * 1000)
        
        print(f"      데이터 다운로드 중...", end=" ")
        
        while True:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not ohlcv:
                break
            
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            
            if since >= int(end_time.timestamp() * 1000):
                break
            
            time.sleep(0.05)  # Binance는 빠름
        
        if not all_ohlcv:
            print("실패")
            return None
        
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('datetime', inplace=True)
        df = df[['open', 'high', 'low', 'close', 'volume']]
        df.drop_duplicates(inplace=True)
        df.sort_index(inplace=True)
        
        # 캐시 저장
        save_cached_data(df, symbol, timeframe)
        print(f"{len(df)}개 캔들 저장")
        
        return df
        
    except Exception as e:
        print(f"오류: {e}")
        return None


# ==============================================================================
# 백테스트 함수
# ==============================================================================
def run_backtest(df_hourly, df_daily, initial_capital=10000, leverage=1.2):
    """
    골든/데드크로스 전략 백테스트
    - 1시간봉 기준 20/120 이동평균 크로스
    - 일봉 115MA 방향 필터
    """
    if df_hourly is None or len(df_hourly) < LONG_MA + 10:
        return None
    
    df = df_hourly.copy()
    df['ma_short'] = df['close'].rolling(SHORT_MA).mean()
    df['ma_long'] = df['close'].rolling(LONG_MA).mean()
    
    df['prev_ma_short'] = df['ma_short'].shift(1)
    df['prev_ma_long'] = df['ma_long'].shift(1)
    df['prev2_ma_short'] = df['ma_short'].shift(2)
    df['prev2_ma_long'] = df['ma_long'].shift(2)
    
    df['golden_cross'] = (df['prev2_ma_short'] <= df['prev2_ma_long']) & (df['prev_ma_short'] > df['prev_ma_long'])
    df['dead_cross'] = (df['prev2_ma_short'] >= df['prev2_ma_long']) & (df['prev_ma_short'] < df['prev_ma_long'])
    
    if df_daily is not None and len(df_daily) >= DAILY_MA:
        df_daily = df_daily.copy()
        df_daily['daily_ma'] = df_daily['close'].rolling(DAILY_MA).mean()
    else:
        df_daily = None
    
    df = df.dropna(subset=['ma_short', 'ma_long'])
    
    capital = initial_capital
    position = 0
    entry_price = 0
    invest_amount = 0
    trades = []
    
    for timestamp, row in df.iterrows():
        daily_trend = 'both'
        if df_daily is not None:
            daily_data = df_daily[df_daily.index.date <= timestamp.date()]
            if not daily_data.empty and pd.notna(daily_data['daily_ma'].iloc[-1]):
                if daily_data['close'].iloc[-1] > daily_data['daily_ma'].iloc[-1]:
                    daily_trend = 'long'
                else:
                    daily_trend = 'short'
        
        entry_price_now = row['open']
        
        if row['golden_cross']:
            if position == -1:
                pnl_rate = (entry_price - entry_price_now) / entry_price * leverage
                pnl = invest_amount * pnl_rate
                fee = invest_amount * FEE_RATE
                capital += invest_amount + pnl - fee
                trades.append({'pnl': pnl, 'type': 'short_close'})
                position = 0
            
            if position == 0 and daily_trend in ['long', 'both']:
                invest_amount = capital * leverage
                fee = invest_amount * FEE_RATE
                capital -= invest_amount + fee
                entry_price = entry_price_now
                position = 1
        
        elif row['dead_cross']:
            if position == 1:
                pnl_rate = (entry_price_now - entry_price) / entry_price * leverage
                pnl = invest_amount * pnl_rate
                fee = invest_amount * FEE_RATE
                capital += invest_amount + pnl - fee
                trades.append({'pnl': pnl, 'type': 'long_close'})
                position = 0
            
            if position == 0 and daily_trend in ['short', 'both']:
                invest_amount = capital * leverage
                fee = invest_amount * FEE_RATE
                capital -= invest_amount + fee
                entry_price = entry_price_now
                position = -1
    
    if position != 0 and len(df) > 0:
        last_price = df.iloc[-1]['close']
        if position == 1:
            pnl_rate = (last_price - entry_price) / entry_price * leverage
        else:
            pnl_rate = (entry_price - last_price) / entry_price * leverage
        pnl = invest_amount * pnl_rate
        capital += invest_amount + pnl
        trades.append({'pnl': pnl, 'type': 'final_close'})
    
    total_return = (capital - initial_capital) / initial_capital * 100
    win_trades = len([t for t in trades if t['pnl'] > 0])
    total_trades = len(trades)
    win_rate = (win_trades / total_trades * 100) if total_trades > 0 else 0
    
    return {
        'final_capital': capital,
        'total_return': total_return,
        'total_trades': total_trades,
        'win_rate': win_rate,
        'data_days': (df.index[-1] - df.index[0]).days if len(df) > 0 else 0
    }


# ==============================================================================
# 메인 실행
# ==============================================================================
def main():
    print("=" * 70)
    print("Bitget 코인 스크리닝 프로그램 (최적화 버전)")
    print("전략: 골든/데드크로스 롱숏 (20/120 MA)")
    print("=" * 70)
    print(f"설정:")
    print(f"  - 단기 MA: {SHORT_MA}")
    print(f"  - 장기 MA: {LONG_MA}")
    print(f"  - 일봉 MA 필터: {DAILY_MA}")
    print(f"  - 레버리지: {LEVERAGE}배")
    print(f"  - 최소 데이터 기간: {MIN_YEARS}년")
    print(f"  - 시가총액 상위: {TOP_MARKETCAP}위")
    print(f"  - 제외 코인: {', '.join(EXCLUDE_COINS)}")
    print(f"  - 캐시 경로: {CACHE_DIR}")
    print("=" * 70)
    
    ensure_cache_dir()
    
    # 시가총액 상위 코인 조회
    top_coins = get_top_marketcap_coins(TOP_MARKETCAP)
    
    # 거래소 객체 생성
    exchange_binance = get_binance_exchange()
    exchange_bitget = get_bitget_exchange()
    
    # 필터링된 페어 조회
    pairs = get_filtered_pairs(exchange_binance, exchange_bitget, top_coins)
    
    results = []
    
    print(f"\n[2단계] 코인별 데이터 다운로드 및 백테스트...")
    print(f"   총 {len(pairs)}개 코인 분석 예정\n")
    
    for idx, pair in enumerate(pairs):
        base = pair['base']
        binance_symbol = pair['binance_symbol']
        
        print(f"[{idx+1}/{len(pairs)}] {base} 분석 중...")
        
        try:
            # 1시간봉 데이터 수집 (Binance Spot)
            print(f"   1시간봉:", end="")
            df_hourly = fetch_spot_ohlcv(exchange_binance, binance_symbol, '1h', MIN_YEARS)
            
            # 최소 캔들 수: MIN_YEARS년치 (1시간봉 기준)
            min_candles = MIN_YEARS * 365 * 24  # 3년 = 약 26,280개
            if df_hourly is None or len(df_hourly) < min_candles:
                print(f"   → 데이터 부족 (스킵)")
                continue
            
            # 데이터 기간 확인
            data_days = (df_hourly.index[-1] - df_hourly.index[0]).days
            if data_days < 365 * MIN_YEARS:
                print(f"   → 기간 부족: {data_days}일 (스킵)")
                continue
            
            # 일봉 데이터 수집
            print(f"   일봉:", end="")
            df_daily = fetch_spot_ohlcv(exchange_binance, binance_symbol, '1d', MIN_YEARS)
            
            # 백테스트 실행
            result = run_backtest(df_hourly, df_daily, INITIAL_CAPITAL, LEVERAGE)
            
            if result is None:
                print(f"   → 백테스트 실패 (스킵)")
                continue
            
            results.append({
                'symbol': pair['bitget_symbol'],
                'base': base,
                'total_return': result['total_return'],
                'final_capital': result['final_capital'],
                'total_trades': result['total_trades'],
                'win_rate': result['win_rate'],
                'data_days': result['data_days']
            })
            
            print(f"   → 수익률: {result['total_return']:+.2f}%, 거래: {result['total_trades']}회, 승률: {result['win_rate']:.1f}%")
            
        except Exception as e:
            print(f"   → 오류: {e}")
            continue
    
    # 결과 정렬 및 출력
    print("\n" + "=" * 70)
    print(f"[3단계] 결과 (상위 {TOP_N}개)")
    print("=" * 70)
    
    if not results:
        print("분석된 코인이 없습니다.")
        return
    
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('total_return', ascending=False)
    
    print(f"\n{'순위':<4} {'코인':<12} {'수익률':>12} {'최종자본':>15} {'거래수':>8} {'승률':>8} {'데이터기간':>10}")
    print("-" * 75)
    
    for i, (idx, row) in enumerate(results_df.head(TOP_N).iterrows()):
        print(f"{i+1:<4} {row['base']:<12} {row['total_return']:>+11.2f}% ${row['final_capital']:>13,.2f} {row['total_trades']:>7}회 {row['win_rate']:>7.1f}% {row['data_days']:>9}일")
    
    # CSV 저장
    output_file = os.path.join(os.path.dirname(__file__), 'bitget_coin_screening_results.csv')
    results_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n전체 결과가 저장되었습니다: {output_file}")
    
    # 추천 코인 출력
    print("\n" + "=" * 70)
    print("[추천] 기존 포트폴리오에 추가 가능한 상위 3개 코인:")
    print("=" * 70)
    
    for i, (idx, row) in enumerate(results_df.head(3).iterrows()):
        print(f"  {i+1}. {row['base']}/USDT:USDT (수익률: {row['total_return']:+.2f}%)")
    
    print("\n프로그램 종료")


if __name__ == '__main__':
    main()
