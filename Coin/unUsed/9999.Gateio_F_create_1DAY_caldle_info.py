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

        print(f"{current_date}부터 {next_date}까지 데이터 가져오는 중...")

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
                    print(f"  {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}부터 {len(ohlcv_data)}개의 캔들 데이터 가져옴")
                    if not ohlcv_data:
                        print("  더 이상 데이터가 없습니다.")
                        break

                    filtered_data = []
                    for data in ohlcv_data:
                        if previous_timestamp is None or data[0] > previous_timestamp:
                            filtered_data.append(data)
                            previous_timestamp = data[0]
                        else:
                            print(f"  오래된 데이터 스킵: {datetime.datetime.utcfromtimestamp(data[0]/1000)} <= {datetime.datetime.utcfromtimestamp(previous_timestamp/1000)}")
                    
                    if not filtered_data:
                        print("  필터링 후 새로운 데이터 없음.")
                        no_new_data_count += 1
                        if no_new_data_count >= max_no_new_data:
                            print(f"  {max_no_new_data}번 시도 후 새로운 데이터 없음. 이 기간 데이터 수집 중단.")
                            break
                        time.sleep(0.2)
                        continue

                    month_data.extend(filtered_data)
                    if len(filtered_data) < 500:
                        print("  500개 미만의 캔들 데이터 가져옴. 데이터 끝일 가능성 높음.")
                        break

                    date_start_ms = filtered_data[-1][0] + (filtered_data[1][0] - filtered_data[0][0])
                    last_timestamp = filtered_data[-1][0]
                    print(f"  데이터 가져오는 중... {datetime.datetime.utcfromtimestamp(date_start_ms/1000)}")
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
            print(f"{current_date.strftime('%Y-%m')}의 데이터를 DataFrame으로 변환 중...")
            try:
                df_month = pd.DataFrame(month_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                df_month['datetime'] = pd.to_datetime(df_month['datetime'], unit='ms')
                df_month.set_index('datetime', inplace=True)
                df_month = df_month.sort_index().drop_duplicates(keep='first')
                monthly_dfs.append(df_month)
                print(f"{current_date.strftime('%Y-%m')}에 대해 {len(month_data)}개의 캔들 데이터 가져옴")
            except Exception as e:
                print(f"월별 DataFrame 생성 중 오류: {e}")
                break
        else:
            print(f"{current_date.strftime('%Y-%m')}에 대한 데이터 없음")
            break

        if last_timestamp:
            last_date = datetime.datetime.utcfromtimestamp(last_timestamp / 1000)
            if last_date >= date_end:
                print("마지막으로 가져온 데이터가 종료 날짜를 초과함. 데이터 가져오기 중단.")
                break

        current_date = next_date
        if current_date < date_end:
            print("다음 요청 전 2초 대기...")
            time.sleep(0.1)

    if not monthly_dfs:
        print("가져온 데이터가 없습니다.")
        return

    print("월별 DataFrame 병합 중...")
    try:
        df = pd.concat(monthly_dfs, axis=0)
        df = df.sort_index().drop_duplicates(keep='first')
        print(f"데이터 가져오기 완료. 총 캔들 수: {len(df)}")
        df.to_csv(output_file)
        print(f"데이터를 {output_file}에 저장함")
    except Exception as e:
        print(f"월별 데이터 병합 중 오류: {e}")

# 실행
ticker = 'BTC/USDT:USDT'
timeframe = '1h'  # 일봉으로 변경
output_file = 'btc_usdt_1h_2020_to_202505.csv'  # 파일 이름 변경
fetch_ohlcv_to_csv(ticker, timeframe, 2020, 1, 1, 2025, 5, 31, output_file)