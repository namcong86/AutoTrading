# -*- coding:utf-8 -*-
"""
이름: trading_utils.py
설명: 자동매매 백테스팅 스크립트를 위한 공통 유틸리티 함수 모음
"""
import ccxt
import time
import pandas as pd
import numpy as np
import datetime
import matplotlib.pyplot as plt
import os

# ==============================================================================
# 데이터 처리 함수
# ==============================================================================

def get_ohlcv_data(ticker, timeframe, start_date, end_date, exchange_name='binance', data_path='./'):
    """
    지정된 기간의 OHLCV 데이터를 로컬 CSV 또는 API를 통해 가져옵니다.
    - 로컬에 CSV 파일이 있으면 먼저 로드합니다.
    - 데이터가 부족하면 나머지는 API를 통해 가져와서 병합 후 CSV에 저장합니다.
    """
    print(f"--- [{ticker}] 데이터 준비 중 ({exchange_name}, {timeframe}) ---")
    
    # 파일명 규칙 정의
    safe_ticker_name = ticker.replace('/', '_').lower()
    csv_file = os.path.join(data_path, f"{safe_ticker_name}_{exchange_name}_{timeframe}.csv")
    
    csv_df = pd.DataFrame()

    # 1. 로컬 CSV 파일 로드 시도
    if os.path.exists(csv_file):
        try:
            print(f"'{csv_file}' 파일에서 데이터를 로드합니다.")
            csv_df = pd.read_csv(csv_file, index_col=0, parse_dates=True)
            if not isinstance(csv_df.index, pd.DatetimeIndex):
                 csv_df.index = pd.to_datetime(csv_df.index)
            
            if csv_df.index.tz is None:
                csv_df.index = csv_df.index.tz_localize('UTC')
            
            # 시간대 정보를 UTC로 통일 후 제거하여 단순화
            csv_df.index = csv_df.index.tz_convert('UTC').tz_localize(None)
            print(f"로컬 데이터 로드 완료. 범위: {csv_df.index.min()} ~ {csv_df.index.max()}")

        except Exception as e:
            print(f"오류: '{csv_file}' 파일 로드 중 오류 발생: {e}.")
            csv_df = pd.DataFrame()

    # 2. API 데이터 필요 여부 결정
    fetch_from_api = False
    since = int(start_date.timestamp() * 1000)

    if not csv_df.empty:
        last_date_in_csv = csv_df.index.max()
        if last_date_in_csv < end_date:
            print(f"로컬 데이터가 최신이 아닙니다. 마지막 데이터: {last_date_in_csv}. 이후 데이터를 API로 가져옵니다.")
            timeframe_duration = pd.to_timedelta(timeframe)
            since = int((last_date_in_csv + timeframe_duration).timestamp() * 1000)
            fetch_from_api = True
        else:
            print("로컬 데이터가 최신 상태입니다. API 호출을 건너뜁니다.")
    else:
        print("로컬 데이터가 없습니다. 전체 기간 데이터를 API로 다운로드합니다.")
        fetch_from_api = True

    # 3. API를 통해 데이터 다운로드
    if fetch_from_api:
        print(f"API 다운로드 시작 시점: {datetime.datetime.fromtimestamp(since/1000)}")
        try:
            exchange = getattr(ccxt, exchange_name)()
            all_ohlcv = []
            end_ms = int(end_date.timestamp() * 1000)
            
            while since < end_ms:
                ohlcv = exchange.fetch_ohlcv(ticker, timeframe, since, limit=1000)
                if not ohlcv:
                    break
                all_ohlcv.extend(ohlcv)
                since = ohlcv[-1][0] + exchange.parse_timeframe(timeframe) * 1000
                print(f"[{ticker}] API 다운로드 중... 마지막 날짜: {datetime.datetime.fromtimestamp(ohlcv[-1][0]/1000)}")
                time.sleep(exchange.rateLimit / 1000)
            
            if all_ohlcv:
                api_df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                api_df['timestamp'] = pd.to_datetime(api_df['timestamp'], unit='ms')
                api_df.set_index('timestamp', inplace=True)
                
                # 4. 데이터 병합 및 저장
                combined_df = pd.concat([csv_df, api_df])
                combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
                combined_df.sort_index(inplace=True)
                
                combined_df.to_csv(csv_file)
                print(f"업데이트된 데이터를 '{csv_file}' 파일로 저장했습니다.")
                df = combined_df
            else:
                df = csv_df
        except Exception as e:
            print(f"API 데이터 다운로드 중 오류 발생: {e}")
            df = csv_df # 오류 발생 시 기존 데이터만 사용
    else:
        df = csv_df

    # 5. 최종 데이터 필터링 후 반환
    if not df.empty:
        return df.loc[start_date:end_date].copy() # SettingWithCopyWarning 방지
    else:
        return pd.DataFrame()


# ==============================================================================
# 보조지표 계산 함수
# ==============================================================================

def calculate_indicators(df, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9, bb_window=20, bb_std=2):
    """DataFrame에 주요 보조지표(RSI, MACD, Bollinger Bands)를 추가합니다."""
    
    # RSI
    delta = df['close'].diff(1)
    gain = delta.where(delta > 0, 0).ewm(com=rsi_period - 1, adjust=False).mean()
    loss = -delta.where(delta < 0, 0).ewm(com=rsi_period - 1, adjust=False).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # MACD
    ema_fast = df['close'].ewm(span=macd_fast, adjust=False).mean()
    ema_slow = df['close'].ewm(span=macd_slow, adjust=False).mean()
    df['macd'] = ema_fast - ema_slow
    df['macd_signal'] = df['macd'].ewm(span=macd_signal, adjust=False).mean()
    df['macd_histogram'] = df['macd'] - df['macd_signal']
    
    # Bollinger Bands
    df['ma20'] = df['close'].rolling(window=bb_window).mean()
    df['stddev'] = df['close'].rolling(window=bb_window).std()
    df['bb_upper'] = df['ma20'] + bb_std * df['stddev']
    df['bb_lower'] = df['ma20'] - bb_std * df['stddev']
    
    return df

def calculate_moving_averages(df, windows):
    """지정된 기간의 이동평균선을 계산하여 DataFrame에 추가합니다."""
    for window in windows:
        df[f'ma{window}'] = df['close'].rolling(window=window).mean()
    return df

# ==============================================================================
# 결과 분석 및 시각화 함수
# ==============================================================================

def analyze_and_plot_results(portfolio_df, title="백테스트 결과"):
    """
    백테스트 결과(포트폴리오 가치 데이터프레임)를 분석하고 시각화합니다.
    portfolio_df는 'value' 컬럼을 포함해야 합니다.
    """
    if portfolio_df.empty:
        print("백테스트 결과가 없어 분석을 종료합니다.")
        return

    # 1. 최종 성과 지표 계산
    initial_capital = portfolio_df['value'].iloc[0]
    final_capital = portfolio_df['value'].iloc[-1]
    total_return = (final_capital / initial_capital - 1) * 100
    
    # CAGR 계산
    start_date = portfolio_df.index[0]
    end_date = portfolio_df.index[-1]
    years = (end_date - start_date).days / 365.25
    cagr = (pow(final_capital / initial_capital, 1 / years) - 1) * 100 if years > 0 else 0

    # MDD 계산
    portfolio_df['peak'] = portfolio_df['value'].cummax()
    portfolio_df['drawdown'] = (portfolio_df['value'] - portfolio_df['peak']) / portfolio_df['peak']
    mdd = portfolio_df['drawdown'].min() * 100

    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)
    print(f"  - 테스트 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} ({years:.2f} 년)")
    print(f"  - 시작 자본: {initial_capital:,.2f} USDT")
    print(f"  - 최종 자산: {final_capital:,.2f} USDT")
    print(f"  - 총 수익률: {total_return:.2f}%")
    print(f"  - 연복리 수익률 (CAGR): {cagr:.2f}%")
    print(f"  - 최대 낙폭 (MDD): {mdd:.2f}%")
    print("="*80 + "\n")

    # 2. 시각화
    plt.figure(figsize=(15, 10))
    try:
        plt.rc('font', family='Malgun Gothic')
    except:
        plt.rc('font', family='AppleGothic')
    plt.rcParams['axes.unicode_minus'] = False

    # 자산 추이 그래프
    ax1 = plt.subplot(2, 1, 1)
    portfolio_df['value'].plot(ax=ax1, label='전략 자산')
    ax1.set_title('자산 추이', fontsize=15)
    ax1.set_ylabel('자산 가치 (USDT)')
    ax1.grid(True)
    ax1.legend()

    # 낙폭(Drawdown) 그래프
    ax2 = plt.subplot(2, 1, 2)
    portfolio_df['drawdown'].plot(ax=ax2, kind='area', color='red', alpha=0.3, label='Drawdown')
    ax2.set_title('최대 낙폭 (MDD)', fontsize=15)
    ax2.set_ylabel('낙폭 (%)')
    ax2.set_xlabel('날짜')
    ax2.grid(True)
    ax2.legend()
    
    plt.tight_layout()
    plt.show()
