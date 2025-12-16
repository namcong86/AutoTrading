import ccxt
import time
import pandas as pd
import datetime
import os

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
        'defaultType': 'spot'
    }
})

# 17개 대상 코인 목록
COIN_LIST = [
    'XRP', 'BCH', 'LTC', 'LINK', 'TRX', 'DOT', 'UNI', 'AAVE', 'XLM',
    'AVAX', 'SHIB', 'XMR', 'HBAR', 'ZEC', 'SUI', 'TON', 'WLFI'
]

def fetch_ohlcv_to_json(ticker, timeframe, start_year, start_month, start_day, end_year, end_month, end_day, output_file):
    """OHLCV 데이터를 가져와서 JSON 파일로 저장"""
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

        print(f"  Fetching data from {current_date.strftime('%Y-%m-%d')} to {next_date.strftime('%Y-%m-%d')}...")

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
                    if not ohlcv_data:
                        break

                    filtered_data = []
                    for data in ohlcv_data:
                        if previous_timestamp is None or data[0] > previous_timestamp:
                            filtered_data.append(data)
                            previous_timestamp = data[0]
                    
                    if not filtered_data:
                        no_new_data_count += 1
                        if no_new_data_count >= max_no_new_data:
                            break
                        time.sleep(0.2)
                        continue

                    month_data.extend(filtered_data)
                    if len(filtered_data) < 200:
                        break

                    date_start_ms = filtered_data[-1][0] + (filtered_data[1][0] - filtered_data[0][0])
                    last_timestamp = filtered_data[-1][0]
                    no_new_data_count = 0
                    time.sleep(0.2)
                    break

                except Exception as e:
                    print(f"    데이터 가져오기 오류: {e}")
                    retry_count += 1
                    if retry_count == max_retries:
                        print("    최대 재시도 횟수 초과.")
                        break
                    print(f"    재시도 {retry_count}/{max_retries}... 5초 대기")
                    time.sleep(5)

            if retry_count == max_retries or not ohlcv_data or no_new_data_count >= max_no_new_data:
                break

        if month_data:
            try:
                df_month = pd.DataFrame(month_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
                df_month['datetime'] = pd.to_datetime(df_month['datetime'], unit='ms')
                df_month.set_index('datetime', inplace=True)
                df_month = df_month.sort_index().drop_duplicates(keep='first')
                monthly_dfs.append(df_month)
            except Exception as e:
                print(f"    월별 DataFrame 생성 중 오류: {e}")
                break
        else:
            break

        if last_timestamp:
            last_date = datetime.datetime.utcfromtimestamp(last_timestamp / 1000)
            if last_date >= date_end:
                break

        current_date = next_date
        if current_date < date_end:
            time.sleep(0.1)

    if not monthly_dfs:
        # 데이터가 없으면 조용히 0 반환 (1h봉 등에서 데이터 없을 때)
        return 0

    try:
        df = pd.concat(monthly_dfs, axis=0)
        df = df.sort_index().drop_duplicates(keep='first')
        
        # JSON 파일로 저장
        df_reset = df.reset_index()
        df_reset['datetime'] = df_reset['datetime'].dt.strftime('%Y-%m-%d %H:%M:%S')
        df_reset.to_json(output_file, orient='records', indent=2, force_ascii=False)
        print(f"  저장 완료: {output_file} ({len(df)}개 캔들)")
        return len(df)
    except Exception as e:
        print(f"  데이터 병합 중 오류: {e}")
        return 0


def main():
    # 저장 폴더 생성
    output_path = r'C:\AutoTrading\Coin\json\screener_coins'
    os.makedirs(output_path, exist_ok=True)
    print(f"저장 폴더: {output_path}")
    
    # 데이터 기간 설정 (2022년부터 현재까지)
    start_year, start_month, start_day = 2022, 1, 1
    end_year, end_month, end_day = 2025, 12, 17  # 오늘까지
    
    # 타임프레임 목록
    timeframes = ['1h', '1d']
    
    total_coins = len(COIN_LIST)
    
    for idx, coin in enumerate(COIN_LIST, 1):
        ticker = f'{coin}/USDT'
        print(f"\n{'='*60}")
        print(f"[{idx}/{total_coins}] {coin} 데이터 다운로드 중...")
        print(f"{'='*60}")
        
        for tf in timeframes:
            output_file = os.path.join(output_path, f"{coin}_USDT_{tf}.json")
            
            # 이미 파일이 존재하면 스킵할지 확인
            if os.path.exists(output_file):
                print(f"  {tf}: 파일이 이미 존재합니다. 새로 다운로드합니다...")
            
            print(f"  {tf}봉 다운로드 시작...")
            candle_count = fetch_ohlcv_to_json(
                ticker, 
                tf, 
                start_year, start_month, start_day, 
                end_year, end_month, end_day, 
                output_file
            )
            
            if candle_count == 0:
                print(f"  {tf}: 데이터 없음 - 스킵")
            
            time.sleep(1)  # API 호출 간격
        
        print(f"{coin} 완료!")
    
    print(f"\n{'='*60}")
    print("모든 코인 데이터 다운로드 완료!")
    print(f"저장 위치: {output_path}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
