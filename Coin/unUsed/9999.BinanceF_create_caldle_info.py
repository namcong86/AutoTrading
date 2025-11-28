import ccxt
import time
import pandas as pd
import datetime
import uuid
import os # 파일 존재 여부 확인을 위해 추가

# 바이낸스 객체 생성
# === 중요: 여기에 본인의 바이낸스 API 키와 시크릿 키를 입력하세요! ===
Binance_AccessKey = "Q5ues5EwMK0HBj6VmtF1K1buouyX3eAgmN5AJkq5IIMHFlkTNVEOypjtzCZu5sux"
Binance_SecretKey = "LyPDtZUAA4inEno0iVeYROHaYGz63epsT5vOa1OpAdoGPHS0uEVJzP5SaEyNCazQ"

# ====================================================================

binance = ccxt.binance({
    'apiKey': Binance_AccessKey,
    'secret': Binance_SecretKey,
    'enableRateLimit': True, # API 호출 제한 속도 준수
    'options': {
        'defaultType': 'future', # 선물(Futures) 데이터를 가져오도록 설정
    }
})

def fetch_ohlcv_to_csv(exchange, ticker, timeframe, start_year, start_month, start_day, end_year, end_month, end_day, output_file):
    date_start = datetime.datetime(start_year, start_month, start_day)
    date_end = datetime.datetime(end_year, end_month, end_day)
    monthly_dfs = []
    current_date = date_start
    last_timestamp = None

    print(f"--- {exchange.id.upper()}에서 {ticker} {timeframe} 데이터 준비 중 ---")
    
    # 이미 파일이 존재하면 이어서 받을지 물어보는 로직 추가
    if os.path.exists(output_file):
        df_existing = pd.read_csv(output_file, index_col=0, parse_dates=True)
        if not df_existing.empty:
            last_existing_date = df_existing.index.max().to_pydatetime()
            if last_existing_date >= current_date:
                current_date = last_existing_date + datetime.timedelta(minutes=exchange.parse_timeframe(timeframe))
                print(f"기존 파일 '{output_file}'이(가) 존재하여 마지막 데이터({last_existing_date})부터 이어서 받습니다. 시작일 변경: {current_date}")
            else:
                print(f"기존 파일 '{output_file}'이(가) 존재하지만, 요청된 시작일보다 오래된 데이터이므로 새로 다운로드합니다.")
        else:
            print(f"기존 파일 '{output_file}'이(가) 비어있습니다. 새로 다운로드합니다.")
    else:
        print(f"기존 파일 '{output_file}'이(가) 없습니다. 새로 다운로드합니다.")


    while current_date < date_end:
        # 월 단위로 데이터를 가져오기 위한 날짜 설정
        # ccxt의 fetch_ohlcv는 'since'부터 'limit' 개수만큼 가져오므로, 효율적인 데이터 수집을 위해 월 단위로 묶는 것이 좋습니다.
        next_month = current_date.month + 1 if current_date.month < 12 else 1
        next_year = current_date.year + 1 if next_month == 1 else current_date.year
        
        # 다음 달 1일 또는 최종 종료일 중 빠른 날짜를 다음 기간의 끝으로 설정
        # 이렇게 하면 마지막 월의 데이터도 정확히 end_date까지만 가져올 수 있습니다.
        fetch_until_date = min(datetime.datetime(next_year, next_month, 1), date_end)

        date_start_ms = int(current_date.timestamp() * 1000)
        date_end_ms = int(fetch_until_date.timestamp() * 1000)

        print(f"데이터 가져오는 중: {current_date.strftime('%Y-%m-%d %H:%M:%S')} 부터 {fetch_until_date.strftime('%Y-%m-%d %H:%M:%S')} 까지...")

        month_data = []
        previous_timestamp = None # 중복 데이터 필터링을 위한 마지막 타임스탬프

        # 데이터가 없거나, 더 이상 새로운 데이터가 없는 경우를 위한 카운터
        no_new_data_count = 0
        max_no_new_data_attempts = 3 # 새로운 데이터가 없을 때 재시도할 최대 횟수

        while date_start_ms < date_end_ms:
            retry_count = 0
            max_retries = 5 # API 요청 실패 시 최대 재시도 횟수
            ohlcv_data = None

            while retry_count < max_retries:
                try:
                    # 바이낸스 선물 데이터 (defaultType: 'future' 설정으로 별도 params 필요 없음)
                    ohlcv_data = exchange.fetch_ohlcv(
                        symbol=ticker,
                        timeframe=timeframe,
                        since=date_start_ms,
                        limit=1000 # 바이낸스는 한 번에 최대 1000개 캔들 제공
                    )
                    
                    if not ohlcv_data:
                        print(f"  {ticker} {timeframe}: 더 이상 데이터가 없습니다 (since={datetime.datetime.utcfromtimestamp(date_start_ms/1000)}).")
                        break # 데이터가 없으면 현재 월 가져오기 중단

                    # 중복 데이터 필터링
                    filtered_data = []
                    for data in ohlcv_data:
                        # 현재 timestamp가 이전에 처리된 마지막 timestamp보다 큰 경우에만 추가
                        if previous_timestamp is None or data[0] > previous_timestamp:
                            filtered_data.append(data)
                            previous_timestamp = data[0]
                        # 이미 가져온 데이터보다 이전/같은 데이터는 건너뜀 (API가 중복을 주는 경우 방지)
                        # else:
                        #     print(f"  Skipping old/duplicate data: {datetime.datetime.utcfromtimestamp(data[0]/1000)} <= {datetime.datetime.utcfromtimestamp(previous_timestamp/1000)}")
                    
                    if not filtered_data:
                        no_new_data_count += 1
                        print(f"  새로운 데이터가 없습니다. 시도 횟수: {no_new_data_count}/{max_no_new_data_attempts}")
                        if no_new_data_count >= max_no_new_data_attempts:
                            print(f"  최대 '새로운 데이터 없음' 시도 횟수 초과. 현재 기간 중단.")
                            break
                        # 새로운 데이터가 없으면 다음 캔들 시작 시간을 예측하여 넘어가도록 시도
                        if len(ohlcv_data) > 1: # 최소 2개 캔들이 있어야 시간 간격 계산 가능
                            timeframe_in_ms = ohlcv_data[1][0] - ohlcv_data[0][0]
                        else: # 데이터가 1개 또는 0개일 경우 기본 타임프레임 간격 사용 (ccxt parse_timeframe)
                            timeframe_in_ms = exchange.parse_timeframe(timeframe) * 1000
                        date_start_ms += timeframe_in_ms # 다음 캔들의 시작 시간으로 이동
                        time.sleep(exchange.rateLimit / 1000) # 레이트 리밋 준수
                        continue # 새로운 데이터 없어도 계속 시도
                    else:
                        no_new_data_count = 0 # 새로운 데이터가 있으면 카운터 리셋

                    month_data.extend(filtered_data)
                    
                    # 마지막으로 가져온 캔들의 다음 시간으로 'since' 값 업데이트
                    # 정확한 다음 시작점을 위해 마지막 캔들의 시간 + 타임프레임 간격 사용
                    if len(filtered_data) > 1:
                        timeframe_interval = filtered_data[1][0] - filtered_data[0][0]
                    else: # 필터링 후 데이터가 1개인 경우 (fetch_ohlcv_data가 1개만 반환했거나 필터링 후 1개 남았을 경우)
                        timeframe_interval = exchange.parse_timeframe(timeframe) * 1000
                    
                    date_start_ms = filtered_data[-1][0] + timeframe_interval
                    
                    print(f"  총 {len(month_data)}개 캔들 수집. 마지막 캔들 시간: {datetime.datetime.utcfromtimestamp(filtered_data[-1][0]/1000)}")
                    
                    # fetch_ohlcv limit만큼 다 못 가져왔다는 것은 끝에 도달했거나 더 이상 데이터가 없다는 의미
                    if len(ohlcv_data) < 1000: # 바이낸스 API의 limit (fetch_ohlcv_data는 필터링 전 raw 데이터)
                        print(f"  {ticker} {timeframe}: {len(ohlcv_data)}개의 캔들만 가져옴 (limit 미달성). 현재 기간의 끝에 도달했을 수 있습니다.")
                        break # 현재 월 가져오기 중단
                    
                    time.sleep(exchange.rateLimit / 1000) # API 요청 간격 준수
                    break # 성공적으로 데이터 가져왔으니 재시도 루프 탈출

                except ccxt.NetworkError as e:
                    print(f"  네트워크 오류 발생: {e}. {retry_count+1}/{max_retries} 재시도...")
                    retry_count += 1
                    time.sleep(5) # 네트워크 오류 시 5초 대기 후 재시도
                except ccxt.ExchangeError as e:
                    print(f"  거래소 오류 발생: {e}. {retry_count+1}/{max_retries} 재시도...")
                    retry_count += 1
                    time.sleep(5)
                except Exception as e:
                    print(f"  알 수 없는 오류 발생: {e}. {retry_count+1}/{max_retries} 재시도...")
                    retry_count += 1
                    time.sleep(5)
            
            # 최대 재시도 횟수 초과 또는 더 이상 데이터가 없으면 현재 월 데이터 수집 중단
            if retry_count == max_retries or not ohlcv_data or no_new_data_count >= max_no_new_data_attempts:
                break

        if month_data:
            print(f"DataFrame으로 변환 및 병합 중: {current_date.strftime('%Y-%m')} 데이터...")
            try:
                df_month = pd.DataFrame(month_data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df_month['timestamp'] = pd.to_datetime(df_month['timestamp'], unit='ms')
                df_month.set_index('timestamp', inplace=True)
                # 인덱스 기준으로 정렬하고 중복 제거 (첫 번째 값 유지)
                df_month = df_month.sort_index().drop_duplicates(keep='first')
                monthly_dfs.append(df_month)
                print(f"{current_date.strftime('%Y-%m')}: {len(month_data)}개 캔들 수집 완료.")
            except Exception as e:
                print(f"월별 DataFrame 생성 중 오류: {e}")
                break # 오류 발생 시 전체 데이터 수집 중단

        # 다음 월의 시작 날짜로 업데이트 (다음 루프를 위해)
        current_date = fetch_until_date
        if current_date < date_end:
            print(f"{exchange.id.upper()} API 호출 간격 준수 중...")
            time.sleep(0.1) # 월별 처리 사이의 간격

    if not monthly_dfs:
        print("가져온 데이터가 없습니다.")
        return

    print("수집된 월별 DataFrame들을 하나로 합치는 중...")
    try:
        df = pd.concat(monthly_dfs, axis=0)
        df = df.sort_index().drop_duplicates(keep='first')
        
        # 파일이 이미 존재하면 기존 데이터와 병합
        if os.path.exists(output_file):
            df_existing = pd.read_csv(output_file, index_col=0, parse_dates=True)
            df = pd.concat([df_existing, df]).sort_index().drop_duplicates(keep='first')
            print(f"기존 데이터와 병합 완료. 총 캔들 수: {len(df)}")
        else:
            print(f"데이터 수집 완료. 총 캔들 수: {len(df)}")

        df.to_csv(output_file)
        print(f"데이터가 '{output_file}' 파일로 저장되었습니다.")
    except Exception as e:
        print(f"최종 데이터 병합 또는 CSV 저장 중 오류: {e}")

# 실행 예시
# 티커는 바이낸스 선물 거래소에서 사용하는 심볼 형식으로 지정해야 합니다.
# 예: BTC/USDT:USDT (현물), BTC/USDT (선물)
# PEPE/USDT는 보통 현물이지만 선물 심볼도 'PEPEUSDT' 또는 'PEPE/USDT'일 수 있습니다.
# ccxt는 'PEPE/USDT' 형식을 자동으로 선물에 맞게 변환해줍니다.
target_ticker = 'DOGE/USDT' # 바이낸스 선물 심볼 형식
target_timeframe = '15m'
output_csv_file = 'doge_usdt_binance_15m.csv'

# 함수 호출 (인자로 바이낸스 객체 전달)
fetch_ohlcv_to_csv(binance, target_ticker, target_timeframe, 2021, 1, 1, 2025, 5, 31, output_csv_file)