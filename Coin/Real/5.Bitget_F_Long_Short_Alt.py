# -*- coding:utf-8 -*-
'''
골든크로스/데드크로스 롱숏 전략 - Bitget 운영 봇
- 1시간봉 기준 20이평, 120이평 크로스 매매
- 골든크로스: 롱 진입 (숏 청산)
- 데드크로스: 숏 진입 (롱 청산)
- 5분할 진입, 청산은 일괄
'''
import ccxt
import time
import pandas as pd
import json
import socket
import telegram_alert

# ==============================================================================
# 설정
# ==============================================================================
# 비트겟 계정 정보
ACCOUNT_LIST = [
    {
        "name": "BitgetMain",
        "access_key": "bg_b191c3cc69263a9993453a08acbde6f5",
        "secret_key": "c2690dc2dadee98fd976d1c78f52e223dd6b98dfe6a45f24899d68a332481fd6",
        "passphrase": "namcongMain",
        "leverage": 1  # 레버리지 (1~10 설정 가능)
    },
]

# 투자 종목 리스트 (사이클 기반 1/N 분배)
INVEST_COIN_LIST = [
    {'ticker': 'ADA/USDT:USDT', 'rate': 0.25},
    {'ticker': 'DOGE/USDT:USDT', 'rate': 0.25},
    {'ticker': 'SOL/USDT:USDT', 'rate': 0.25},
    {'ticker': 'BNB/USDT:USDT', 'rate': 0.25},
]

# 전략 설정
SHORT_MA = 20            # 단기 이동평균
LONG_MA = 120            # 장기 이동평균
SPLIT_COUNT = 1          # 분할 진입 횟수 (1=일괄진입, 2~5=분할진입)
INVEST_RATE = 0.99       # 전체 자금 중 투자 비율
FEE = 0.0006             # 수수료율 (0.06%)

# 부분 익절 설정
TAKE_PROFIT_ENABLED = True    # 부분 익절 로직 활성화 여부 (True: 적용, False: 미적용)

# 익절 레벨 설정 (전 캔들 종가 기준) - TAKE_PROFIT_ENABLED = True일 때만 적용
# profit_pct: 수익률 도달 시, sell_pct: 해당 시점 물량의 몇 %를 익절
TAKE_PROFIT_LEVELS = [
    {'level': 1, 'profit_pct': 5, 'sell_pct': 5},    # TP1: 5% 수익 시 5% 익절
    {'level': 2, 'profit_pct': 10, 'sell_pct': 10},  # TP2: 10% 수익 시 10% 익절
    {'level': 3, 'profit_pct': 20, 'sell_pct': 20},  # TP3: 20% 수익 시 20% 익절
]


# ==============================================================================
# 헬퍼 함수
# ==============================================================================
def GetOhlcv(exchange, ticker, timeframe='1h', target_rows=150):
    """Bitget: OHLCV 데이터 가져오기"""
    try:
        limit = 100
        all_ohlcv = []
        end_ms = None
        attempts = 0

        while len(all_ohlcv) < target_rows and attempts < 5:
            params = {'limit': limit}
            if end_ms is not None:
                params['endTime'] = end_ms

            batch = exchange.fetch_ohlcv(ticker, timeframe, limit=limit, params=params)
            if not batch:
                break

            all_ohlcv = batch + all_ohlcv
            end_ms = batch[0][0] - 1
            attempts += 1

            if len(batch) < limit:
                break

            time.sleep(0.2)

        if not all_ohlcv:
            return pd.DataFrame()

        df = pd.DataFrame(all_ohlcv, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df.drop_duplicates(subset='datetime', keep='first', inplace=True)
        df.sort_values('datetime', inplace=True)
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms')
        df.set_index('datetime', inplace=True)
        return df
    except Exception as e:
        print(f"GetOhlcv 오류 ({ticker}): {e}")
        return pd.DataFrame()


def GetCoinNowPrice(exchange, ticker):
    """현재 가격 조회"""
    try:
        return exchange.fetch_ticker(ticker)['last']
    except Exception as e:
        print(f"GetCoinNowPrice 오류 ({ticker}): {e}")
        return 0.0


def check_golden_cross(df, short_ma, long_ma):
    """골든크로스 확인 (전전봉 vs 전봉 비교 → 전봉 마감 시 크로스 확정)"""
    if len(df) < 3:
        return False
    # 전전봉 MA
    prev2_short = df[f'ma_{short_ma}'].iloc[-3]
    prev2_long = df[f'ma_{long_ma}'].iloc[-3]
    # 전봉 MA
    prev_short = df[f'ma_{short_ma}'].iloc[-2]
    prev_long = df[f'ma_{long_ma}'].iloc[-2]
    
    return prev2_short <= prev2_long and prev_short > prev_long


def check_dead_cross(df, short_ma, long_ma):
    """데드크로스 확인 (전전봉 vs 전봉 비교 → 전봉 마감 시 크로스 확정)"""
    if len(df) < 3:
        return False
    # 전전봉 MA
    prev2_short = df[f'ma_{short_ma}'].iloc[-3]
    prev2_long = df[f'ma_{long_ma}'].iloc[-3]
    # 전봉 MA
    prev_short = df[f'ma_{short_ma}'].iloc[-2]
    prev_long = df[f'ma_{long_ma}'].iloc[-2]
    
    return prev2_short >= prev2_long and prev_short < prev_long


# ==============================================================================
# 메인 트레이딩 로직
# ==============================================================================
def execute_trading_logic(account_info):
    """하나의 계정에 대한 트레이딩 로직 실행"""
    account_name = account_info['name']
    access_key = account_info['access_key']
    secret_key = account_info['secret_key']
    passphrase = account_info['passphrase']
    set_leverage = account_info['leverage']

    first_String = f"[5.Bitget 롱숏 {account_name}] {set_leverage}배 "

    # 비트겟 객체 생성
    try:
        bitgetX = ccxt.bitget({
            'apiKey': access_key,
            'secret': secret_key,
            'password': passphrase,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'swap',
                'defaultMarginMode': 'cross'
            }
        })
    except Exception as e:
        print(f"[{account_name}] ccxt 객체 생성 실패: {e}")
        telegram_alert.SendMessage(f"[{account_name}] ccxt 객체 생성 실패")
        return

    # 데이터 파일 경로
    pcServerGb = socket.gethostname()
    if pcServerGb == "AutoBotCong":
        botdata_file_path = f"/var/AutoBot/json/BitgetF_LongShort_Data_{account_name}.json"
    else:
        botdata_file_path = f"./BitgetF_LongShort_Data_{account_name}.json"

    # 봇 데이터 로드
    try:
        with open(botdata_file_path, 'r') as f:
            BotDataDict = json.load(f)
    except FileNotFoundError:
        BotDataDict = {}
    except Exception as e:
        print(f"[{account_name}] 데이터 파일 로드 오류: {e}")
        BotDataDict = {}

    t = time.gmtime()
    hour_n = t.tm_hour
    min_n = t.tm_min

    if min_n <= 2:
        start_msg = f"{first_String} 시작"
        telegram_alert.SendMessage(start_msg)

    # 잔고 조회
    try:
        balance_check = bitgetX.fetch_balance(params={"type": "swap"})
        time.sleep(0.1)
        current_usdt_balance = float(balance_check['USDT']['free'])

        if current_usdt_balance < 10:
            print(f"[{account_name}] 잔고 부족 ({current_usdt_balance:.2f} USDT)")
            return

        print(f"[{account_name}] 현재 잔고: {current_usdt_balance:.2f} USDT")

    except Exception as e:
        print(f"[{account_name}] 잔고 조회 실패: {e}")
        return

    # 메인 루프
    for coin_data in INVEST_COIN_LIST:
        coin_ticker = coin_data['ticker']
        coin_rate = coin_data['rate']

        # 키 초기화
        for key in ["_POSITION", "_ENTRY_COUNT", "_ENTRY_PRICE", "_POSITION_SIZE", "_TP_TRIGGERED"]:
            full_key = coin_ticker + key
            if full_key not in BotDataDict:
                if key == "_POSITION":
                    BotDataDict[full_key] = 0  # 0: 없음, 1: 롱, -1: 숏
                elif key == "_ENTRY_COUNT":
                    BotDataDict[full_key] = 0
                elif key == "_TP_TRIGGERED":
                    BotDataDict[full_key] = []  # 이미 실행된 TP 레벨 리스트
                else:
                    BotDataDict[full_key] = 0.0

        # 1시간봉 데이터 가져오기
        df = GetOhlcv(bitgetX, coin_ticker, '1h', target_rows=150)
        if df.empty or len(df) < LONG_MA + 2:
            print(f"[{account_name}] {coin_ticker} 데이터 부족")
            continue

        # 이동평균 계산
        df[f'ma_{SHORT_MA}'] = df['close'].rolling(SHORT_MA).mean()
        df[f'ma_{LONG_MA}'] = df['close'].rolling(LONG_MA).mean()
        df.dropna(inplace=True)

        if len(df) < 2:
            print(f"[{account_name}] {coin_ticker} 지표 계산 후 데이터 부족")
            continue

        now_price = GetCoinNowPrice(bitgetX, coin_ticker)
        if now_price == 0:
            print(f"[{account_name}] {coin_ticker} 현재가 조회 실패")
            continue

        # 현재 포지션 상태
        current_position = BotDataDict.get(coin_ticker + '_POSITION', 0)
        entry_count = BotDataDict.get(coin_ticker + '_ENTRY_COUNT', 0)
        entry_price = BotDataDict.get(coin_ticker + '_ENTRY_PRICE', 0)
        tp_triggered = BotDataDict.get(coin_ticker + '_TP_TRIGGERED', [])

        # 실제 포지션 확인
        try:
            positions = bitgetX.fetch_positions([coin_ticker])
            actual_position = 0
            actual_size = 0
            actual_entry_price = 0
            for pos in positions:
                if pos['symbol'] == coin_ticker and float(pos.get('contracts', 0)) != 0:
                    actual_size = abs(float(pos['contracts']))
                    actual_entry_price = float(pos.get('entryPrice', 0))
                    if pos['side'] == 'long':
                        actual_position = 1
                    elif pos['side'] == 'short':
                        actual_position = -1
            # 진입가 업데이트
            if actual_entry_price > 0 and entry_price == 0:
                BotDataDict[coin_ticker + '_ENTRY_PRICE'] = actual_entry_price
                entry_price = actual_entry_price
        except Exception as e:
            print(f"[{account_name}] {coin_ticker} 포지션 조회 오류: {e}")
            actual_position = current_position
            actual_size = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0)

        # === 익절 체크 (전 캔들 종가 기준) - TAKE_PROFIT_ENABLED 옵션 확인 ===
        if TAKE_PROFIT_ENABLED and actual_position != 0 and actual_size > 0 and entry_price > 0:
            prev_close = df['close'].iloc[-2]  # 전 캔들 종가
            
            # 수익률 계산
            if actual_position == 1:  # 롱
                profit_pct = ((prev_close - entry_price) / entry_price) * 100
            else:  # 숏
                profit_pct = ((entry_price - prev_close) / entry_price) * 100
            
            # 익절 레벨 체크
            for tp in TAKE_PROFIT_LEVELS:
                tp_level = tp['level']
                tp_profit = tp['profit_pct']
                tp_sell_pct = tp['sell_pct']
                
                # 이미 실행된 레벨은 스킵
                if tp_level in tp_triggered:
                    continue
                
                # 수익률 도달 시 익절 실행
                if profit_pct >= tp_profit:
                    sell_amount = actual_size * (tp_sell_pct / 100)
                    if sell_amount > 0:
                        try:
                            if actual_position == 1:  # 롱 익절
                                bitgetX.create_order(
                                    coin_ticker, 'market', 'sell', sell_amount,
                                    None, {'holdSide': 'long', 'reduceOnly': True}
                                )
                            else:  # 숏 익절
                                bitgetX.create_order(
                                    coin_ticker, 'market', 'buy', sell_amount,
                                    None, {'holdSide': 'short', 'reduceOnly': True}
                                )
                            
                            # TP 레벨 기록
                            tp_triggered.append(tp_level)
                            BotDataDict[coin_ticker + '_TP_TRIGGERED'] = tp_triggered
                            BotDataDict[coin_ticker + '_POSITION_SIZE'] = actual_size - sell_amount
                            
                            # 텔레그램 알림
                            tp_msg = (
                                f"💰 {first_String} {coin_ticker} 부분 익절 (TP{tp_level})\n"
                                f"- 진입가: ${entry_price:.6f}\n"
                                f"- 전캔들 종가: ${prev_close:.6f}\n"
                                f"- 수익률: {profit_pct:.2f}%\n"
                                f"- 익절 비율: {tp_sell_pct}%\n"
                                f"- 익절 수량: {sell_amount:.6f}\n"
                                f"- 남은 수량: {actual_size - sell_amount:.6f}"
                            )
                            print(tp_msg)
                            telegram_alert.SendMessage(tp_msg)
                            
                            # 포지션 크기 업데이트
                            actual_size -= sell_amount
                            time.sleep(0.2)
                        except Exception as e:
                            print(f"[{account_name}] {coin_ticker} TP{tp_level} 익절 실패: {e}")
                            telegram_alert.SendMessage(f"{first_String} {coin_ticker} TP{tp_level} 익절 실패: {e}")

        # 골든크로스 확인
        is_golden = check_golden_cross(df, SHORT_MA, LONG_MA)
        # 데드크로스 확인
        is_dead = check_dead_cross(df, SHORT_MA, LONG_MA)

        # 알림 메시지
        alert_msg = (
            f"<{first_String} {coin_ticker}>\n"
            f"- 현재가: ${now_price:.6f}\n"
            f"- MA{SHORT_MA}: ${df[f'ma_{SHORT_MA}'].iloc[-1]:.6f}\n"
            f"- MA{LONG_MA}: ${df[f'ma_{LONG_MA}'].iloc[-1]:.6f}\n"
            f"- 골든크로스: {is_golden}\n"
            f"- 데드크로스: {is_dead}\n"
            f"- 현재 포지션: {'롱' if actual_position == 1 else '숏' if actual_position == -1 else '없음'}\n"
            f"- 진입 횟수: {entry_count}/{SPLIT_COUNT}"
        )
        telegram_alert.SendMessage(alert_msg)

        # === 골든크로스: 숏 청산 후 롱 진입 ===
        if is_golden:
            # 숏 포지션이면 청산
            if actual_position == -1:
                try:
                    bitgetX.create_order(
                        coin_ticker, 'market', 'buy', actual_size,
                        None, {'holdSide': 'short', 'reduceOnly': True}
                    )
                    msg = f"{first_String} {coin_ticker} 숏 청산 (골든크로스)"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                    
                    BotDataDict[coin_ticker + '_POSITION'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                    actual_position = 0
                    entry_count = 0
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 숏 청산 실패: {e}")

            # 롱 진입 (분할)
            if actual_position == 0 or (actual_position == 1 and entry_count < SPLIT_COUNT):
                try:
                    # 투자 금액 계산 (분할)
                    total_invest = current_usdt_balance * INVEST_RATE * coin_rate
                    split_invest = total_invest / SPLIT_COUNT
                    amount = (split_invest * set_leverage) / now_price

                    # 레버리지 설정
                    bitgetX.set_leverage(set_leverage, coin_ticker, params={'marginCoin': 'USDT', 'holdSide': 'long'})

                    # 롱 진입
                    bitgetX.create_order(
                        coin_ticker, 'market', 'buy', amount,
                        None, {'holdSide': 'long'}
                    )

                    entry_count += 1
                    BotDataDict[coin_ticker + '_POSITION'] = 1
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = entry_count
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0) + amount
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = now_price
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []  # 신규 진입 시 익절 상태 초기화

                    msg = f"{first_String} {coin_ticker} 롱 진입 ({entry_count}/{SPLIT_COUNT}) - ${split_invest:.2f} USDT @ ${now_price:.6f}"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 롱 진입 실패: {e}")
                    telegram_alert.SendMessage(f"{first_String} {coin_ticker} 롱 진입 실패: {e}")

        # === 데드크로스: 롱 청산 후 숏 진입 ===
        elif is_dead:
            # 롱 포지션이면 청산
            if actual_position == 1:
                try:
                    bitgetX.create_order(
                        coin_ticker, 'market', 'sell', actual_size,
                        None, {'holdSide': 'long', 'reduceOnly': True}
                    )
                    msg = f"{first_String} {coin_ticker} 롱 청산 (데드크로스)"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                    
                    BotDataDict[coin_ticker + '_POSITION'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = 0
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = 0
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = 0
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []
                    actual_position = 0
                    entry_count = 0
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 롱 청산 실패: {e}")

            # 숏 진입 (분할)
            if actual_position == 0 or (actual_position == -1 and entry_count < SPLIT_COUNT):
                try:
                    # 투자 금액 계산 (분할)
                    total_invest = current_usdt_balance * INVEST_RATE * coin_rate
                    split_invest = total_invest / SPLIT_COUNT
                    amount = (split_invest * set_leverage) / now_price

                    # 레버리지 설정
                    bitgetX.set_leverage(set_leverage, coin_ticker, params={'marginCoin': 'USDT', 'holdSide': 'short'})

                    # 숏 진입
                    bitgetX.create_order(
                        coin_ticker, 'market', 'sell', amount,
                        None, {'holdSide': 'short'}
                    )

                    entry_count += 1
                    BotDataDict[coin_ticker + '_POSITION'] = -1
                    BotDataDict[coin_ticker + '_ENTRY_COUNT'] = entry_count
                    BotDataDict[coin_ticker + '_POSITION_SIZE'] = BotDataDict.get(coin_ticker + '_POSITION_SIZE', 0) + amount
                    BotDataDict[coin_ticker + '_ENTRY_PRICE'] = now_price
                    BotDataDict[coin_ticker + '_TP_TRIGGERED'] = []  # 신규 진입 시 익절 상태 초기화

                    msg = f"{first_String} {coin_ticker} 숏 진입 ({entry_count}/{SPLIT_COUNT}) - ${split_invest:.2f} USDT @ ${now_price:.6f}"
                    print(msg)
                    telegram_alert.SendMessage(msg)
                except Exception as e:
                    print(f"[{account_name}] {coin_ticker} 숏 진입 실패: {e}")
                    telegram_alert.SendMessage(f"{first_String} {coin_ticker} 숏 진입 실패: {e}")

        # 봇 데이터 저장
        with open(botdata_file_path, 'w') as f:
            json.dump(BotDataDict, f, indent=4)

    if min_n <= 2:
        end_msg = f"{first_String} 종료"
        telegram_alert.SendMessage(end_msg)


# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == '__main__':
    print("===== Bitget 골든/데드크로스 롱숏 봇 시작 =====")
    for account in ACCOUNT_LIST:
        print(f"\n--- {account['name']} 거래 시작 (레버리지: {account['leverage']}배) ---")
        execute_trading_logic(account)
    print("\n===== 모든 계정 거래 실행 완료 =====")
