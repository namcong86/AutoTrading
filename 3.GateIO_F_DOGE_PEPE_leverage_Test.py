#-*-coding:utf-8 -*-
'''
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
Gate.io ccxt 버전 (수정됨)
pip3 install --upgrade ccxt==4.2.19 (또는 최신 안정 버전)
이렇게 버전을 맞춰주세요! (ccxt 버전은 호환성에 따라 조절 필요)
봇은 헤지모드에서 동작합니다. 꼭! 헤지 모드로 바꿔주세요! (Gate.io 계정 설정)
https://blog.naver.com/zacra/222662884649 (참고용 바이낸스 헤지모드 설명)
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
백테스팅은 내PC에서 해야 서버 자원을 아끼고 투자 성과 그래프도 확인할 수 있습니다!
이 포스팅을 정독하시고 다양한 기간으로 백테스팅 해보세요!!!
https://blog.naver.com/zacra/223180500307
$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

관련 포스팅
https://blog.naver.com/zacra/223449598379
위 포스팅을 꼭 참고하세요!!!
'''

import ccxt
import time
import pandas as pd
import datetime
import matplotlib.pyplot as plt

# 시간 변환을 위한 헬퍼 함수 (선택 사항)
def ms_to_utc_str(timestamp_ms):
    return datetime.datetime.utcfromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d %H:%M:%S')

def GetOhlcv2(exchange_obj, ticker_symbol, time_period, year=2019, month=1, day=1, hour=0, minute=0):
    # 시작 날짜 UTC 기준으로 설정
    start_date_dt = datetime.datetime(year, month, day, hour, minute, tzinfo=datetime.timezone.utc)
    current_since_ms = int(start_date_dt.timestamp() * 1000)
    
    all_ohlcv_data = []
    
    now_ms = int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)
    
    calculated_interval_ms = 0
    # period 문자열을 기반으로 기본 interval_ms 미리 추정 (fallback 용)
    if time_period == '1d': calculated_interval_ms = 24 * 60 * 60 * 1000
    elif time_period == '1h': calculated_interval_ms = 60 * 60 * 1000
    elif time_period == '5m': calculated_interval_ms = 5 * 60 * 1000
    else: calculated_interval_ms = 24 * 60 * 60 * 1000 # 알 수 없는 경우 기본값 1일

    while True:
        if current_since_ms >= now_ms:
            print(f"요청 시작 시간 {ms_to_utc_str(current_since_ms)} ({ticker_symbol})이 현재 또는 미래입니다. 데이터 수집을 중단합니다.")
            break

        try:
            ohlcv_batch = exchange_obj.fetch_ohlcv(ticker_symbol, time_period, since=current_since_ms)

            if not ohlcv_batch:
                print(f"{ticker_symbol}의 {ms_to_utc_str(current_since_ms)} UTC 이후 데이터가 없습니다.")
                break
            
            all_ohlcv_data.extend(ohlcv_batch)

            # 실제 데이터로부터 interval_ms 업데이트 (첫 성공적인 배치 후 한 번 또는 매번)
            if len(ohlcv_batch) > 1:
                calculated_interval_ms = ohlcv_batch[1][0] - ohlcv_batch[0][0]
            # (만약 interval_ms가 항상 일정하다고 가정하면, 이 부분은 한 번만 실행되도록 최적화 가능)

            last_candle_ts = ohlcv_batch[-1][0]
            next_fetch_since_ms = last_candle_ts + calculated_interval_ms

            print(f"Get Data for {ticker_symbol}... Last: {ms_to_utc_str(last_candle_ts)}, Next since: {ms_to_utc_str(next_fetch_since_ms)} UTC")

            if next_fetch_since_ms >= now_ms:
                print(f"{ticker_symbol}의 다음 'since' ({ms_to_utc_str(next_fetch_since_ms)})가 미래입니다. 추가 가져오기를 중단합니다.")
                break
            
            current_since_ms = next_fetch_since_ms
            
            # API 요청 간격 조절
            time.sleep(getattr(exchange_obj, 'rateLimit', 300) / 1000) # exchange_obj.rateLimit (밀리초) / 1000, 없으면 0.3초

        except ccxt.RateLimitExceeded as e:
            print(f"요청 한도 초과 {ticker_symbol}: {e}. 잠시 후 재시도...")
            time.sleep(getattr(exchange_obj, 'rateLimit', 10000) / 1000) # 기본 10초 대기
        except ccxt.NetworkError as e:
            print(f"네트워크 오류 {ticker_symbol}: {e}. 5초 후 재시도...")
            time.sleep(5)
        except ccxt.ExchangeError as e:
            error_msg = str(e).lower()
            reason = "기타 거래소 오류"
            if "invalid time range" in error_msg or "invalid_param_value" in error_msg:
                reason = "유효하지 않은 시간 범위"
            print(f"거래소 오류 ({reason}) {ticker_symbol} (since {ms_to_utc_str(current_since_ms)}): {e}. 중단합니다.")
            break
        except Exception as e:
            print(f"예상치 못한 오류 {ticker_symbol} (since {ms_to_utc_str(current_since_ms)}): {e}. 중단합니다.")
            break

    if not all_ohlcv_data:
        print(f"{ticker_symbol}에 대해 가져온 데이터가 없습니다.")
        return pd.DataFrame(columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])

    df = pd.DataFrame(all_ohlcv_data, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
    df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
    df = df.set_index('datetime').sort_index() # 정렬 추가
    df = df[~df.index.duplicated(keep='first')] # 중복 제거
    return df

# Gate.io 객체 생성
# !!! 사용자 실제 API 키로 변경 필요 !!!
# !!! API 키는 OHLCV 데이터 조회에는 필수는 아닐 수 있으나, 일부 기능 또는 향후 거래 실행을 위해 필요합니다.
# !!! Gate.io에서 API 키를 생성하고 아래에 입력하세요.
GateIO_AccessKey = "YOUR_GATEIO_API_KEY"
GateIO_SecretKey = "YOUR_GATEIO_SECRET_KEY"

# ccxt.gateio로 변경
exchange = ccxt.gateio({
    'apiKey': GateIO_AccessKey,
    'secret': GateIO_SecretKey,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',  # 'future'에서 'swap'으로 변경 (Gate.io USDT 무기한 선물의 경우)
        # 'settle': 'usdt' # USDT-M 계약의 경우 명시적으로 지정해야 할 수 있습니다. (예: 'usdt' 또는 'btc')
                            # PEPE/USDT, DOGE/USDT는 USDT 정산이므로 'usdt'
                            # ccxt가 자동으로 처리하려고 하지만, 문제가 발생하면 이 옵션을 추가해보세요.
    }
})
# exchange.load_markets() # 마켓 정보를 미리 로드 (선택 사항)

InvestTotalMoney = 5000  # 초기 총 투자 금액
leverage = 3  # 레버리지 설정
# !!! Gate.io의 실제 수수료로 변경하세요. (예: Taker 0.05%, Maker 0.015% -> 0.0005 또는 0.00015)
# 아래는 예시이며, VIP 레벨 등에 따라 다를 수 있습니다.
fee = 0.001  # 수수료 0.1% (예시, 실제 Gate.io 수수료에 맞게 수정 필요)
allocation_percentage = 0.5  # 각 코인에 50%씩 할당

# 투자 종목 설정
# !!! 티커 심볼을 Gate.io 기준으로 변경하고, 데이터 시작일을 확인하세요.
# !!! PEPE는 2023년 2월에 데이터가 없을 가능성이 높습니다. 실제 상장일 이후로 조정하세요.
# Gate.io Perpetual Swap 심볼은 보통 COIN/USDT 형태 (ccxt 표준) 또는 COIN_USDT (Gate.io API)
# ccxt는 COIN/USDT를 적절한 마켓 ID로 변환해줍니다.
InvestCoinList = [
    {'ticker': 'PEPE/USDT', 'rate': 0.5, 'start_date': {'year': 2023, 'month': 3, 'day': 1}}, # 1000PEPE -> PEPE로 변경, 시작일은 PEPE 상장일(대략 4~5월)에 맞춰 예시로 변경
    {'ticker': 'DOGE/USDT', 'rate': 0.5, 'start_date': {'year': 2023, 'month': 3, 'day': 1}}
]

# 데이터 가져오기 및 전처리
dfs = {}
for coin_data in InvestCoinList:
    ticker = coin_data['ticker']
    start_date_params = coin_data['start_date']
    print(f"Fetching data for {ticker} from {start_date_params['year']}-{start_date_params['month']}-{start_date_params['day']}...")
    # GetOhlcv2 함수에 exchange 객체 전달
    df = GetOhlcv2(exchange, ticker, '1d', start_date_params['year'], start_date_params['month'], start_date_params['day'], 0, 0)

    if df.empty:
        print(f"No data for {ticker}, skipping...")
        continue

    # RSI 지표 계산
    period_rsi = 14 # 'period' 변수명과의 충돌을 피하기 위해 이름 변경
    delta = df["close"].diff()
    up, down = delta.copy(), delta.copy()
    up[up < 0] = 0
    down[down > 0] = 0
    _gain = up.ewm(com=(period_rsi - 1), min_periods=period_rsi).mean() # period_rsi 사용
    _loss = down.abs().ewm(com=(period_rsi - 1), min_periods=period_rsi).mean() # period_rsi 사용
    RS = _gain / _loss
    df['rsi'] = pd.Series(100 - (100 / (1 + RS)), name="RSI")
    df['rsi_ma'] = df['rsi'].rolling(14).mean()
    df['rsi_5ma'] = df['rsi'].rolling(5).mean()
    df['prev_close'] = df['close'].shift(1)
    df['change'] = (df['close'] - df['prev_close']) / df['prev_close']
    df['value'] = df['close'] * df['volume']

    # 이동평균선 계산
    ma_dfs = []
    for ma in range(3, 81):
        ma_df = df['close'].rolling(ma).mean().rename(str(ma) + 'ma')
        ma_dfs.append(ma_df)
    ma_df_combined = pd.concat(ma_dfs, axis=1)
    df = pd.concat([df, ma_df_combined], axis=1)
    df['value_ma'] = df['value'].rolling(window=10).mean().shift(1)
    df['30ma_slope'] = ((df['30ma'] - df['30ma'].shift(5)) / df['30ma'].shift(5)) * 100
    # DiffValue = -2 # 이 변수는 정의되었으나 사용되지 않아 일단 제거함

    # MACD 계산
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    df.dropna(inplace=True)
    if not df.empty:
        dfs[ticker] = df
    else:
        print(f"DataFrame for {ticker} became empty after dropping NA. Check data and indicator periods.")


# 공통 날짜 범위 찾기
if not dfs:
    print("No data loaded for any coin. Exiting.")
    exit()

# InvestCoinList의 모든 티커가 실제로 dfs에 데이터가 있는지 확인
valid_tickers = [coin['ticker'] for coin in InvestCoinList if coin['ticker'] in dfs]
if not valid_tickers:
    print("No valid data to process after fetching and pre-processing. Exiting.")
    exit()

common_dates = set(dfs[valid_tickers[0]].index)
for ticker in valid_tickers[1:]:
    common_dates = common_dates.intersection(set(dfs[ticker].index))

if not common_dates:
    print("No common dates found for the provided tickers. Check data ranges and availability. Exiting.")
    exit()
common_dates = sorted(list(common_dates))


# 초기 설정
cash_balance = InvestTotalMoney
positions = {}  # key: ticker, value: {'margin': margin, 'entry_price': price, 'quantity': qty, 'leverage': leverage}
total_equity_list = []
MonthlyTryCnt = {}
CoinStats = {ticker: {'SuccessCnt': 0, 'FailCnt': 0} for ticker in valid_tickers}


# 백테스팅 루프
for date in common_dates:
    current_data = {ticker: dfs[ticker].loc[date] for ticker in valid_tickers if date in dfs[ticker].index}
    if len(current_data) != len(valid_tickers): # 현재 날짜에 모든 티커 데이터가 있는지 확인
        # print(f"Skipping date {date} due to missing data for one or more tickers.")
        continue

    # 1. 보유 중인 코인의 매도 조건 확인
    for ticker in list(positions.keys()):
        if ticker not in current_data: continue # common_dates가 정확하다면 발생하지 않아야 함

        position = positions[ticker]
        margin = position['margin']
        entry_price = position['entry_price']
        pos_leverage = position['leverage'] # 포지션의 레버리지 사용
        current_price = current_data[ticker]['open'] # 기간 시작 시점의 시가(open)를 매도 결정에 사용

        # 매도 조건
        # 해당 'ticker'의 df에서 인덱스 'i'가 유효한지 확인
        if date not in dfs[ticker].index: continue
        i = dfs[ticker].index.get_loc(date)

        if i >= 2: # 최소 2개의 이전 데이터 포인트 필요
            df_coin = dfs[ticker] # 특정 코인의 데이터프레임 사용
            RevenueRate = ((current_price - entry_price) / entry_price * pos_leverage - fee) * 100.0 # 매도 시 수수료 1회 적용

            # 기존 매도 조건
            sell_condition_triggered = False
            if (((df_coin['high'].iloc[i-2] > df_coin['high'].iloc[i-1] and df_coin['low'].iloc[i-2] > df_coin['low'].iloc[i-1]) or
                (df_coin['open'].iloc[i-1] > df_coin['close'].iloc[i-1] and df_coin['open'].iloc[i-2] > df_coin['close'].iloc[i-2]) or
                RevenueRate < 0) and not (i >= 2 and df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and df_coin['3ma'].iloc[i-2] < df_coin['3ma'].iloc[i-1])):
                sell_condition_triggered = True

            if sell_condition_triggered:
                # 매도 실행
                # PnL 계산: 실현 가치 = 초기 마진 + 손익 - 수수료
                # 손익 = 위험 마진 * 변동률
                # 변동률 = (현재가 - 진입가) / 진입가 * 레버리지
                # 실현 가치 = 마진 * (1 + ((현재가 - 진입가) / 진입가) * 레버리지)
                # 수수료는 진입 및 청산 시 총 거래 금액(마진 * 레버리지) 또는 PnL에 적용됨.
                # 원본 스크립트는 수익률에 수수료를 적용했는데, 이는 일반적이지 않음.
                # 더 일반적인 방법: 변동 가치 = 마진 * 레버리지 * (현재가 - 진입가) / 진입가
                # 최종 가치 = 마진 + 변동 가치 - (마진 * 레버리지 * 수수료)  <-- 수수료를 계약금액(notional)에 적용하는 경우
                # 또는, 수수료를 마진에 적용하는 경우:
                # 실현 가치 = 마진 * (1 + ((현재가 - 진입가) / 진입가 * 레버리지) * (1-수수료))  <-- 수익 발생 시
                # 일단 원본과의 일관성을 위해 사용자의 PnL 로직을 유지하지만, 일반적이지는 않음.
                # RevenueRate에는 이미 레버리지와 수수료가 포함되어 있음.
                # 따라서, 수익 금액 = 마진 * (RevenueRate / 100)
                # cash_balance += 마진 + 수익 금액

                profit_or_loss_multiplier = (current_price - entry_price) / entry_price * pos_leverage
                # final_margin_value = margin * (1 + profit_or_loss_multiplier) # 이 변수는 아래에서 직접 사용되지 않음
                # transaction_cost = margin * pos_leverage * fee # 매도 시 계약금액에 수수료를 부과한다고 가정
                                                            # RevenueRate의 원래 수수료는 약간 단순화됨.
                                                            # 더 정확하려면 수수료는 계약금액(마진*레버리지)에 부과되어야 함.
                                                            # (현재가 * 수량) * 수수료
                                                            # (진입가 * 수량) * 수수료

                # 레버리지와 수수료를 사용한 PnL 계산 (좀 더 표준적인 방법 예시 - 현재 코드 미적용)
                # quantity = (margin * pos_leverage) / entry_price
                # gross_pnl = (current_price - entry_price) * quantity
                # total_fees = (margin * pos_leverage * fee) # 진입 수수료 (매수 시 이미 현금 잔고에서 차감된 경우)
                # total_fees += (margin * pos_leverage * (current_price/entry_price) * fee) # 청산 수수료
                # net_pnl = gross_pnl - total_fees_for_this_trade # 해당 거래의 총 수수료
                # cash_balance += margin + net_pnl

                # 원본 RevenueRate 로직 기반의 단순화된 PnL (수익률에서 수수료 차감)
                # 이는 수수료가 마진의 PnL 비율에 적용됨을 의미함.
                cash_balance += margin * (1 + RevenueRate / 100.0)


                print(f"{ticker} {date} >>> 매도: Entry {entry_price:.8f}, Exit {current_price:.8f}, 수익률 {RevenueRate:.2f}%, 현재 총자산 {cash_balance:.2f}")

                if RevenueRate > 0:
                    CoinStats[ticker]['SuccessCnt'] += 1
                else:
                    CoinStats[ticker]['FailCnt'] += 1
                del positions[ticker]
                month_key = date.strftime('%Y-%m')
                MonthlyTryCnt[month_key] = MonthlyTryCnt.get(month_key, 0) + 1

    # 2. 매수 신호 확인 및 실행
    available_cash_for_new_trades = cash_balance # 당일 신규 포지션 진입 전 사용 가능한 현금

    # 할당량을 관리하기 위해 얼마나 많은 신규 포지션을 열 수 있는지 결정
    num_potential_buys = 0
    for coin_data in InvestCoinList:
        ticker = coin_data['ticker']
        if ticker not in positions and ticker in dfs and date in dfs[ticker].index: # 티커에 데이터가 있는지 확인
             num_potential_buys+=1

    # 현재 현금과 할당 비율을 유지하기 위한 잠재적 신규 거래 수를 기반으로 거래당 마진 계산
    # 이 부분은 할당이 *총 초기 자본* 대비 코인당 할당인지 *현재 자본* 대비인지에 따라 까다로움
    # 원본 스크립트는 *각* 신규 거래에 대해 *현재 cash_balance*의 allocation_percentage를 의미함.
    # 여러 매수 신호가 발생하면 과도한 할당으로 이어질 수 있음.
    # allocation_percentage는 available_cash_for_new_trades / 전략에 의해 허용된 동시 매수 수라고 가정
    # 또는 더 간단하게: 각 코인은 신규 거래일 경우 *현재* cash_balance의 allocation_percentage까지 차지할 수 있음.

    for coin_data in InvestCoinList:
        ticker = coin_data['ticker']
        if ticker not in positions and ticker in dfs and date in dfs[ticker].index: # 티커에 데이터가 있는지 확인
            df_coin = dfs[ticker] # 특정 코인의 데이터프레임 사용
            i = df_coin.index.get_loc(date)

            if i > 2: # 일부 조건에 대해 최소 3개의 이전 데이터 포인트 필요
                # MACD 조건
                macd_3ago = df_coin['macd'].iloc[i-3] - df_coin['macd_signal'].iloc[i-3]
                macd_2ago = df_coin['macd'].iloc[i-2] - df_coin['macd_signal'].iloc[i-2]
                macd_1ago = df_coin['macd'].iloc[i-1] - df_coin['macd_signal'].iloc[i-1]
                macd_positive = macd_1ago > 0
                macd_3to2_down = macd_3ago > macd_2ago
                macd_2to1_down = macd_2ago > macd_1ago
                macd_condition = not (macd_3to2_down and macd_2to1_down)

                # 전일 캔들 조건
                prev_high = df_coin['high'].iloc[i-1]
                prev_low = df_coin['low'].iloc[i-1]
                prev_open = df_coin['open'].iloc[i-1]
                prev_close = df_coin['close'].iloc[i-1]
                upper_shadow = prev_high - max(prev_open, prev_close)
                candle_length = prev_high - prev_low
                upper_shadow_ratio = (upper_shadow / candle_length) if candle_length > 0 else 0 # 0으로 나누기 방지

                # 원본 스크립트의 매수 조건
                buy_condition_triggered = False
                if (df_coin['open'].iloc[i-1] < df_coin['close'].iloc[i-1] and    # 전일 양봉
                    df_coin['open'].iloc[i-2] < df_coin['close'].iloc[i-2] and    # 전전일 양봉
                    df_coin['close'].iloc[i-2] < df_coin['close'].iloc[i-1] and # 전일 종가가 전전일 종가보다 높음
                    df_coin['high'].iloc[i-2] < df_coin['high'].iloc[i-1] and   # 전일 고가가 전전일 고가보다 높음
                    df_coin['7ma'].iloc[i-2] < df_coin['7ma'].iloc[i-1] and     # 7일 이동평균선 상승 중
                    df_coin['30ma_slope'].iloc[i-1] > -2 and                    # 30일 이동평균선 기울기가 너무 낮지 않음
                    df_coin['rsi_ma'].iloc[i-2] < df_coin['rsi_ma'].iloc[i-1] and # RSI 이동평균선 상승 중
                    df_coin['50ma'].iloc[i-2] < df_coin['50ma'].iloc[i-1] and   # 50일 이동평균선 상승 중
                    (macd_positive and macd_condition) and                      # MACD 조건 충족
                    (upper_shadow_ratio <= 0.6)):                               # 윗꼬리가 너무 길지 않음
                    buy_condition_triggered = True

                if buy_condition_triggered:
                    # 매수 실행
                    buy_price = current_data[ticker]['open'] # 당일 시가에 매수

                    # 각 코인에 잔액의 X% 투자 (여기서는 coin_data['rate'] 사용)
                    # cash_balance가 이 거래를 허용하는지 확인.
                    margin_to_invest = available_cash_for_new_trades * coin_data['rate'] # coin_data의 비율 사용

                    if cash_balance >= margin_to_invest and margin_to_invest > 0 : # 이 단일 거래의 마진에 충분한 현금이 있는지 확인
                        quantity = (margin_to_invest * leverage) / buy_price

                        # 계약금액에 대한 진입 수수료를 여기서 cash_balance에서 차감하는 경우
                        # entry_fee_cost = margin_to_invest * leverage * fee
                        # if cash_balance >= margin_to_invest + entry_fee_cost:
                        # cash_balance -= entry_fee_cost
                        # else: continue # 마진 + 수수료에 충분하지 않음

                        positions[ticker] = {
                            'margin': margin_to_invest,
                            'entry_price': buy_price,
                            'quantity': quantity,
                            'leverage': leverage # 이 포지션에 사용된 레버리지 저장
                        }
                        cash_balance -= margin_to_invest # 마진은 현금에서 차감됨
                        # 참고: 이 스크립트의 수수료 적용은 단순화되어 있음.
                        # 일반적인 모델은 진입 및 청산 시 계약금액(마진*레버리지)에 수수료를 적용함.
                        # 현재 스크립트는 매도 시 RevenueRate에서 수수료를 차감하여 PnL 비율에 효과적으로 적용함.
                        # 진입 수수료는 이전에 명시적으로 차감되지 않았음.
                        print(f"{ticker} {date} >>> 매수: 가격 {buy_price:.8f}, 투자금 {margin_to_invest:.2f}, 현재 총자산 {cash_balance:.2f}")

    # 3. 일일 총 자산 가치 계산 (Mark-to-Market, 시가평가)
    daily_total_equity = cash_balance
    for ticker, position in positions.items():
        if ticker not in current_data: continue

        margin = position['margin']
        entry_price = position['entry_price']
        # pos_leverage = position['leverage'] # 이 변수는 아래에서 직접 사용되지 않음 (quantity에 이미 반영 가정)
        current_close_price = current_data[ticker]['close'] # 종가를 사용하여 시가평가

        # 해당 포지션의 당일 미실현 손익
        # profit_or_loss_multiplier = (current_close_price - entry_price) / entry_price * pos_leverage
        # position_current_value = margin * (1 + profit_or_loss_multiplier)

        # 더 직접적인 계산:
        quantity = position['quantity']
        unrealized_pnl = (current_close_price - entry_price) * quantity
        position_current_value = margin + unrealized_pnl # 이 포지션의 현재 평가 가치

        daily_total_equity += position_current_value

    total_equity_list.append({'date': date, 'Total_Equity': daily_total_equity})


# 결과 분석
if not total_equity_list:
    print("No trades were made or no equity data to process. Exiting.")
    exit()

result_df = pd.DataFrame(total_equity_list)
result_df.set_index('date', inplace=True)

result_df['Ror'] = result_df['Total_Equity'].pct_change().fillna(0) + 1 # 첫 번째 요소의 NaN을 0으로 채움 (+1은 수익률 계산을 위함)
result_df['Cum_Ror'] = result_df['Ror'].cumprod()
result_df['Highwatermark'] = result_df['Cum_Ror'].cummax() # 이전에는 Total_Equity 기준이었으나, 누적 수익률(Cum_Ror) 기준으로 변경
result_df['Drawdown'] = (result_df['Cum_Ror'] / result_df['Highwatermark']) - 1
result_df['MaxDrawdown'] = result_df['Drawdown'].cummin()


# 월별 통계
# 리샘플링을 위해 인덱스가 DatetimeIndex인지 확인
result_df.index = pd.to_datetime(result_df.index)

monthly_stats = result_df.resample('ME').agg( # ME: 월말 기준
    {'Total_Equity': ['first', 'last']}
)
monthly_stats.columns = ['Start_Equity', 'End_Equity']
monthly_stats['Return'] = ((monthly_stats['End_Equity'] / monthly_stats['Start_Equity']) - 1) * 100
monthly_stats['Trades'] = 0

for month_key_str, count in MonthlyTryCnt.items():
    try:
        # 'YYYY-MM' 형식의 month_key_str을 monthly_stats 인덱스와 비교하기 위해 타임스탬프로 변환
        month_dt = pd.to_datetime(month_key_str + '-01') # 해당 월의 첫째 날
        # monthly_stats에서 해당 월말 인덱스 찾기
        target_idx = monthly_stats.index[(monthly_stats.index.year == month_dt.year) & (monthly_stats.index.month == month_dt.month)] # 논리 연산자 수정: & 사용
        if not target_idx.empty:
             monthly_stats.loc[target_idx[0], 'Trades'] = count
        else: # 구버전 pandas 또는 다른 리샘플링 키에 대한 대체 처리
            for idx in monthly_stats.index:
                if idx.strftime('%Y-%m') == month_key_str:
                    monthly_stats.loc[idx, 'Trades'] = count
                    break
    except Exception as e:
        print(f"월별 통계 거래 횟수 업데이트 중 오류: {e} (월: {month_key_str})")
        continue

monthly_stats = monthly_stats[['Return', 'End_Equity', 'Trades']]
monthly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
monthly_stats['수익률 (%)'] = monthly_stats['수익률 (%)'].round(2)
monthly_stats['잔액 (USDT)'] = monthly_stats['잔액 (USDT)'].round(2)
monthly_stats.index = monthly_stats.index.strftime('%Y-%m')


# 연도별 통계
yearly_stats = result_df.resample('YE').agg( # YE: 연말 기준
    {'Total_Equity': ['first', 'last']}
)
yearly_stats.columns = ['Start_Equity', 'End_Equity']
yearly_stats['Return'] = ((yearly_stats['End_Equity'] / yearly_stats['Start_Equity']) - 1) * 100
yearly_stats['Trades'] = 0 # 거래 횟수 컬럼 초기화

# 월별 거래 횟수를 연도별로 합산
for month_key_str, count in MonthlyTryCnt.items():
    try:
        year_str = month_key_str.split('-')[0]
        # yearly_stats에서 해당 연말 인덱스 찾기
        target_idx = yearly_stats.index[yearly_stats.index.year == int(year_str)]
        if not target_idx.empty:
            yearly_stats.loc[target_idx[0], 'Trades'] += count
        else: # 대체 처리
            for idx in yearly_stats.index:
                if idx.strftime('%Y') == year_str:
                    yearly_stats.loc[idx, 'Trades'] += count
                    break
    except Exception as e:
        print(f"연도별 통계 거래 횟수 업데이트 중 오류: {e} (월: {month_key_str})")
        continue


yearly_stats = yearly_stats[['Return', 'End_Equity', 'Trades']]
yearly_stats.columns = ['수익률 (%)', '잔액 (USDT)', '거래 횟수']
yearly_stats['수익률 (%)'] = yearly_stats['수익률 (%)'].round(2)
yearly_stats['잔액 (USDT)'] = yearly_stats['잔액 (USDT)'].round(2)
yearly_stats.index = yearly_stats.index.strftime('%Y')

# 코인별 익절/손절 통계 출력
print("\n---------- 코인별 거래 통계 ----------")
for ticker_stat in valid_tickers: # 데이터가 있는 티커만 반복
    stats = CoinStats[ticker_stat]
    success = stats['SuccessCnt']
    fail = stats['FailCnt']
    total_trades = success + fail
    win_rate = (success / total_trades * 100) if total_trades > 0 else 0
    print(f"{ticker_stat} >>> 성공: {success} 실패: {fail} -> 승률: {round(win_rate, 2)}%")
print("------------------------------")

# 그래프 생성
fig, axs = plt.subplots(2, 1, figsize=(10, 10), sharex=True) # X축 공유
# 누적 수익률(Cum_Ror) 플로팅 (1에서 시작하므로 * 100은 초기 100%를 의미)
# 시작부터의 퍼센트 수익률을 표시하려면: (result_df['Cum_Ror'] - 1) * 100
# 또는 Cum_Ror가 이미 계수(예: 10% 이익 시 1.1)라면, (Cum_Ror -1) * 100이 % 이익임
# 원본 스크립트는 Cum_Ror * 100을 플로팅함. Cum_Ror가 1에서 시작하면 기준선으로 100을 표시.
# 명확성을 위해 초기 자본 대비 퍼센트 성장률로 플로팅.
# 총 자산 / 초기 자산 * 100
initial_equity_val = result_df['Total_Equity'].iloc[0]
axs[0].plot(result_df.index, (result_df['Total_Equity'] / initial_equity_val) * 100, label=f'Strategy ({leverage}x Leverage)')

axs[0].set_ylabel('Cumulative Return (%)')
axs[0].set_title('Return Comparison Chart')
axs[0].legend()
axs[0].grid(True)

axs[1].plot(result_df.index, result_df['MaxDrawdown'] * 100, label='MDD')
axs[1].plot(result_df.index, result_df['Drawdown'] * 100, label='Drawdown')
axs[1].set_ylabel('Drawdown (%)')
axs[1].set_title('Drawdown Comparison Chart')
axs[1].legend()
axs[1].grid(True)

plt.xlabel('Date')
plt.tight_layout()
plt.show()

# 최종 결과 출력
if not result_df.empty:
    TotalOri = result_df['Total_Equity'].iloc[0]
    TotalFinal = result_df['Total_Equity'].iloc[-1]
    TotalMDD = result_df['MaxDrawdown'].min() * 100.0 # MDD는 이미 음수이므로 min()이 정확함
    print("\n---------- 총 결과 ----------")
    print(f"최초 금액: {format(round(TotalOri), ',')} USDT, 최종 금액: {format(round(TotalFinal), ',')} USDT")
    print(f"총 수익률: {round(((TotalFinal - TotalOri) / TotalOri) * 100, 2)}%")
    print(f"MDD (최대 손실폭): {round(TotalMDD, 2)}%") # MaxDrawdown은 보통 음수로 표시됨
    print("------------------------------")
    print("\n---------- 월별 통계 ----------")
    print(monthly_stats.to_string())
    print("\n---------- 년도별 통계 ----------")
    print(yearly_stats.to_string())
    print("------------------------------")
else:
    print("Result DataFrame is empty. No final results to display.")