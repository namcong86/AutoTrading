import ccxt
import time
import pandas as pd
import datetime
import uuid

# Gate.io 객체 생성
Gateio_AccessKey = "07a0ba2f6ed018fcb0fde7d08b58b40c"
Gateio_SecretKey = "7fcd29026f6d7d73647981fe4f4b4f75f4569ad0262d0fada5db3a558b50072a"
gateio = ccxt.gate({
    'apiKey': Gateio_AccessKey,
    'secret': Gateio_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})

def fetch_ohlcv_to_csv(ticker, timeframe, start_year, start_month, start_day, end_year, end_month, end_day, output_file):
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
                    ohlcv_data = gateio.fetch_ohlcv(
                        symbol=ticker,
                        timeframe=timeframe,
                        since=date_start_ms,
                        limit=500,
                        params={'future': True}
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
                    if len(filtered_data) < 500:
                        print("  Less than 500 candles fetched. Possibly reached end of data.")
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
            print("Waiting 2 seconds before next request...")
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

# 실행
ticker = 'ADA/USDT:USDT'
timeframe = '1h'
output_file = 'ada_usdt_gateio_1h.json'
fetch_ohlcv_to_csv(ticker, timeframe, 2021, 1, 1, 2025, 11, 20, output_file)