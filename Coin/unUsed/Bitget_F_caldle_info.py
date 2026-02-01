import ccxt
import time
import pandas as pd
import datetime
import uuid

# Bitget 객체 생성
Bitget_AccessKey = "bg_b191c3cc69263a9993453a08acbde6f5"
Bitget_SecretKey = "c2690dc2dadee98fd976d1c78f52e223dd6b98dfe6a45f24899d68a332481fd6"
Bitget_Passphrase = "namcongMain"
bitget = ccxt.bitget({
    'apiKey': Bitget_AccessKey,
    'secret': Bitget_SecretKey,
    'password': Bitget_Passphrase,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'defaultMarginMode': 'cross'
    }
})


def check_data_availability(exchange, ticker_list, timeframe, start_date):
    """
    모든 코인의 데이터 가용성을 미리 체크
    
    Returns:
        dict: {ticker: {'available': bool, 'first_date': datetime or None, 'error': str or None}}
    """
    print("\n" + "="*70)
    print("📊 데이터 가용성 검증 중...")
    print("="*70)
    
    results = {}
    all_available = True
    
    for ticker in ticker_list:
        print(f"\n  [{ticker}] 검증 중...", end=" ")
        
        try:
            # 가장 오래된 데이터를 찾기 위해 아주 오래전 날짜부터 조회
            test_date = datetime.datetime(2015, 1, 1)
            test_ms = int(test_date.timestamp() * 1000)
            
            ohlcv = exchange.fetch_ohlcv(
                symbol=ticker,
                timeframe=timeframe,
                since=test_ms,
                limit=1
            )

            # [Fix] 2015년부터 조회 시 데이터가 없으면, 
            # 최근 상장 코인일 수 있으므로 요청 시작일(start_date) 기준으로 재조회 시도
            if not ohlcv:
                start_ms_check = int(start_date.timestamp() * 1000)
                ohlcv = exchange.fetch_ohlcv(
                    symbol=ticker,
                    timeframe=timeframe,
                    since=start_ms_check,
                    limit=1
                )
            
            if ohlcv and len(ohlcv) > 0:
                first_timestamp = ohlcv[0][0]
                first_date = datetime.datetime.utcfromtimestamp(first_timestamp / 1000)
                
                if first_date <= start_date:
                    print(f"✅ 사용 가능 (최초: {first_date.strftime('%Y-%m-%d')})")
                    results[ticker] = {
                        'available': True,
                        'first_date': first_date,
                        'error': None
                    }
                else:
                    print(f"⚠️ 시작일 이후부터 데이터 존재")
                    print(f"      요청: {start_date.strftime('%Y-%m-%d')} → 실제 최초: {first_date.strftime('%Y-%m-%d')}")
                    results[ticker] = {
                        'available': False,
                        'first_date': first_date,
                        'error': None
                    }
                    all_available = False
            else:
                print(f"❌ 데이터 없음")
                results[ticker] = {
                    'available': False,
                    'first_date': None,
                    'error': "No data returned"
                }
                all_available = False
                
        except Exception as e:
            print(f"❌ 오류: {str(e)[:50]}")
            results[ticker] = {
                'available': False,
                'first_date': None,
                'error': str(e)
            }
            all_available = False
        
        time.sleep(0.3)  # Rate limit
    
    # 결과 요약
    print("\n" + "="*70)
    print("📋 검증 결과 요약")
    print("="*70)
    
    available_count = sum(1 for r in results.values() if r['available'])
    print(f"  총 {len(ticker_list)}개 중 {available_count}개 사용 가능\n")
    
    if not all_available:
        print("⚠️ 아래 코인들은 요청한 시작일({})부터 데이터가 없습니다:".format(
            start_date.strftime('%Y-%m-%d')))
        print("-"*70)
        for ticker, info in results.items():
            if not info['available']:
                if info['first_date']:
                    print(f"  • {ticker}: {info['first_date'].strftime('%Y-%m-%d')}부터 데이터 존재")
                elif info['error']:
                    print(f"  • {ticker}: 오류 - {info['error'][:40]}")
                else:
                    print(f"  • {ticker}: 데이터 없음")
        print("-"*70)
    
    return results, all_available


def fetch_ohlcv_to_json(ticker, timeframe, start_year, start_month, start_day, end_year, end_month, end_day, output_file):
    date_start = datetime.datetime(start_year, start_month, start_day)
    date_end = datetime.datetime(end_year, end_month, end_day)
    monthly_dfs = []
    current_date = date_start
    last_timestamp = None

    while current_date < date_end:
        next_month = current_date.month + 1 if current_date.month < 12 else 1
        next_year = current_date.year + 1 if next_month == 1 else current_date.year
        next_date = min(datetime.datetime(next_year, next_month, 1), date_end)

        date_start_ms = int(current_date.timestamp() * 1000)
        date_end_ms = int(next_date.timestamp() * 1000)

        print(f"Fetching data from {current_date} to {next_date}...")

        month_data = []
        previous_timestamp = None
        no_new_data_count = 0
        max_no_new_data = 3

        while date_start_ms < date_end_ms:
            retry_count = 0
            max_retries = 3
            ohlcv_data = None
            while retry_count < max_retries:
                try:
                    ohlcv_data = bitget.fetch_ohlcv(
                        symbol=ticker,
                        timeframe=timeframe,
                        since=date_start_ms,
                        limit=200  # Bitget은 최대 200개
                    )
                    print(f"  Fetched {len(ohlcv_data)} raw candles starting from {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}")
                    if not ohlcv_data:
                        print("  No more data available.")
                        break

                    filtered_data = []
                    for data in ohlcv_data:
                        if previous_timestamp is None or data[0] > previous_timestamp:
                            filtered_data.append(data)
                            previous_timestamp = data[0]
                        else:
                            print(f"  Skipping old data: {datetime.datetime.utcfromtimestamp(data[0]/1000)} <= {datetime.datetime.utcfromtimestamp(previous_timestamp/1000)}")
                    
                    if not filtered_data:
                        print("  No new data after filtering.")
                        no_new_data_count += 1
                        if no_new_data_count >= max_no_new_data:
                            print(f"  No new data after {max_no_new_data} attempts. Stopping fetch for this period.")
                            break
                        time.sleep(0.2)
                        continue

                    month_data.extend(filtered_data)
                    if len(filtered_data) < 200:
                        print("  Less than 200 candles fetched. Possibly reached end of data.")
                        break

                    date_start_ms = filtered_data[-1][0] + (filtered_data[1][0] - filtered_data[0][0])
                    last_timestamp = filtered_data[-1][0]
                    print(f"  Get Data... {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}")
                    no_new_data_count = 0
                    time.sleep(0.2)
                    break

                except Exception as e:
                    print(f"  데이터 가져오기 오류: {e}")
                    retry_count += 1
                    if retry_count == max_retries:
                        print("  최대 재시도 횟수 초과. 데이터 수집 중단.")
                        break
                    print(f"  재시도 {retry_count}/{max_retries}... 5초 대기")
                    time.sleep(5)

            if retry_count == max_retries or not ohlcv_data or no_new_data_count >= max_no_new_data:
                break

        if month_data:
            print(f"Converting month data to DataFrame for {current_date.strftime('%Y-%m')}...")
            try:
                df_month = pd.DataFrame(month_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                df_month['datetime'] = pd.to_datetime(df_month['datetime'], unit='ms')
                df_month.set_index('datetime', inplace=True)
                df_month = df_month.sort_index().drop_duplicates(keep='first')
                monthly_dfs.append(df_month)
                print(f"Fetched {len(month_data)} candles for {current_date.strftime('%Y-%m')}")
            except Exception as e:
                print(f"월별 DataFrame 생성 중 오류: {e}")
                break
        else:
            print(f"No data fetched for {current_date.strftime('%Y-%m')}")
            break

        if last_timestamp:
            last_date = datetime.datetime.utcfromtimestamp(last_timestamp / 1000)
            if last_date >= date_end:
                print("Last fetched data exceeds end date. Stopping fetch.")
                break

        current_date = next_date
        if current_date < date_end:
            print("Waiting before next request...")
            time.sleep(0.1)

    if not monthly_dfs:
        print("가져온 데이터가 없습니다.")
        return

    print("Merging monthly DataFrames...")
    try:
        df = pd.concat(monthly_dfs, axis=0)
        df = df.sort_index().drop_duplicates(keep='first')
        print(f"Data fetching completed. Total candles: {len(df)}")
        
        # JSON 파일로 저장
        df_reset = df.reset_index()
        df_reset['datetime'] = df_reset['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_reset.to_json(output_file, orient='records', indent=2, force_ascii=False)
        print(f"Data saved to {output_file}")
    except Exception as e:
        print(f"월별 데이터 병합 중 오류: {e}")

# ==============================================================================
# 실행 설정
# ==============================================================================
TICKER_LIST = [
    'PEPEUSDT',
]

timeframe = '1h'
start_year, start_month, start_day = 2023, 6, 1
end_year, end_month, end_day = 2026, 1, 22

# 저장 경로
output_path = r'C:\AutoTrading\Coin\json'

# ==============================================================================
# 데이터 가용성 사전 검증\
# ==============================================================================
start_date = datetime.datetime(start_year, start_month, start_day)
availability_results, all_available = check_data_availability(
    bitget, TICKER_LIST, timeframe, start_date
)

if not all_available:
    print("\n⚠️ 일부 코인의 데이터가 요청 시작일부터 없습니다.")
    user_input = input("계속 진행하시겠습니까? (y/n): ").strip().lower()
    if user_input != 'y':
        print("다운로드를 취소합니다.")
        exit()
    print("\n데이터가 있는 날짜부터 다운로드를 진행합니다...\n")

# ==============================================================================
# 다운로드 실행
# ==============================================================================
for ticker in TICKER_LIST:
    # 파일명 생성 (예: ada_usdt_bitget_1h.json)
    coin_name = ticker.split('/')[0].lower()
    output_file = f"{output_path}\\{coin_name}_usdt_bitget_{timeframe}.json"
    
    print(f"\n{'='*60}")
    print(f"티커: {ticker}")
    print(f"저장 파일: {output_file}")
    print(f"{'='*60}")
    
    fetch_ohlcv_to_json(
        ticker, 
        timeframe, 
        start_year, start_month, start_day, 
        end_year, end_month, end_day, 
        output_file
    )
    
    print(f"{ticker} 완료!")
    time.sleep(1)  # API 호출 간격

print("\n모든 티커 데이터 다운로드 완료!")

