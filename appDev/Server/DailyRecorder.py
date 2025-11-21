import requests
import ccxt
import pandas as pd
import pandas_ta as ta
import json
import os
from datetime import datetime
from pytrends.request import TrendReq
import time

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")

def get_fear_greed():
    try:
        url = "https://api.alternative.me/fng/"
        response = requests.get(url)
        data = response.json()
        return int(data['data'][0]['value'])
    except Exception as e:
        print(f"Error fetching Fear & Greed: {e}")
        return 50

def get_rsi_and_price():
    try:
        binance = ccxt.binance()
        ohlcv = binance.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=100)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['rsi'] = ta.rsi(df['close'], length=14)
        current_rsi = df['rsi'].iloc[-1]
        current_price = df['close'].iloc[-1]
        return float(current_rsi), float(current_price)
    except Exception as e:
        print(f"Error fetching RSI: {e}")
        return 50.0, 0.0

def get_coinbase_premium():
    try:
        # 1. Get Binance Price (BTC/USDT)
        binance = ccxt.binance()
        ticker_binance = binance.fetch_ticker('BTC/USDT')
        price_binance = ticker_binance['last']
        
        # 2. Get Coinbase Price (BTC/USD)
        coinbase = ccxt.coinbasepro()
        ticker_coinbase = coinbase.fetch_ticker('BTC/USD')
        price_coinbase = ticker_coinbase['last']
        
        # 3. Calculate Premium
        # Premium = Coinbase - Binance
        gap = price_coinbase - price_binance
        # Premium Index (%) = (Gap / Binance) * 100
        premium_index = (gap / price_binance) * 100
        
        return premium_index, gap
    except Exception as e:
        print(f"Error fetching Coinbase Premium: {e}")
        return 0.0, 0.0

def get_google_trends():
    try:
        # Pytrends to fetch 'Bitcoin' interest
        pytrends = TrendReq(hl='en-US', tz=360)
        kw_list = ["Bitcoin"]
        
        # Get data for last 5 years to see long-term relative interest
        # timeframe='today 5-y' means last 5 years
        pytrends.build_payload(kw_list, cat=0, timeframe='today 5-y', geo='', gprop='')
        
        df = pytrends.interest_over_time()
        
        if not df.empty:
            # Get the most recent value (last row)
            current_interest = int(df['Bitcoin'].iloc[-1])
            return current_interest
        return 50
    except Exception as e:
        print(f"Error fetching Google Trends: {e}")
        # Fallback: If blocked (429), return 50
        return 50

def save_to_history(data):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try: history = json.load(f)
            except: pass
    
    today_str = data['date']
    history = [h for h in history if h['date'] != today_str]
    history.append(data)
    
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    print(f"Saved data for {today_str}")

def main():
    print("Starting Daily Record (Human Indicators)...")
    
    # 1. Fear & Greed
    fg_index = get_fear_greed()
    print(f"Fear & Greed: {fg_index}")
    
    # 2. RSI & Price
    rsi, price = get_rsi_and_price()
    print(f"RSI: {rsi:.2f}, Price: {price}")
    
    # 3. Coinbase Premium
    cb_premium, cb_gap = get_coinbase_premium()
    print(f"Coinbase Premium: {cb_premium:.4f}% (Gap: ${cb_gap:.2f})")
    
    # 4. Google Trends
    google_score = get_google_trends()
    print(f"Google Trends (Bitcoin): {google_score}")
    
    # --- Scoring Logic (Smart Context) ---
    
    # 1. Fear & Greed (0~100)
    # Low (Fear) -> Buy (High Score)
    score_fear = int((100 - fg_index) / 100.0 * 25)
    
    # 2. RSI (0~100)
    # Low (Oversold) -> Buy (High Score)
    score_rsi = int((100 - rsi) / 100.0 * 25)
    
    # 3. Coinbase Premium (Contrarian Strategy)
    # User Logic: Negative Premium (Discount) -> US Retail Selling -> Buy Opportunity (High Score)
    # 3. Coinbase Premium (Contrarian Strategy)
    # User Logic: Negative Premium (Discount) -> US Retail Selling -> Buy Opportunity (High Score)
    # Range: -0.3% (Strong Buy) ~ +0.3% (Strong Sell)
    # Map -0.3 ~ +0.3 to 25 ~ 0 points linearly
    
    # Clamp premium to range
    clamped_premium = max(-0.3, min(0.3, cb_premium))
    
    # Formula: Normalize to 0~1 then flip and scale to 25
    # Position in range (0.0 ~ 1.0): (premium - min) / (max - min)
    # (clamped - (-0.3)) / 0.6
    position = (clamped_premium + 0.3) / 0.6
    
    # Invert because Lower Premium = Higher Score
    score_cb = int((1.0 - position) * 25)
    
    print(f"  > CB Context: {cb_premium:.4f}% -> Score {score_cb} (Linear Mapping)")

    # 4. Google Trends (0~100)
    # Context:
    # - Low RSI (<40) + High Trend -> Panic Selling/Bottom Attention -> Buy (High Score)
    # - High RSI (>60) + High Trend -> FOMO -> Sell (Low Score)
    # - Low Trend -> Disinterest -> Buy (Medium/High Score)
    if rsi < 40 and google_score > 50:
        # Panic Bottom
        score_google = 25
        print("  > Google Context: Panic/Bottom Attention (Max Score)")
    elif rsi > 60 and google_score > 50:
        # FOMO Top
        score_google = 0
        print("  > Google Context: Retail FOMO (Min Score)")
    else:
        # General Contrarian: Less Interest is better
        score_google = int((100 - google_score) / 100.0 * 25)
        print("  > Google Context: General Interest Inverse")
    
    total_score = score_fear + score_rsi + score_cb + score_google
    
    print(f"\n--- Scores ---")
    print(f"Fear Score: {score_fear}/25")
    print(f"RSI Score: {score_rsi}/25")
    print(f"CB Score: {score_cb}/25 (Prem: {cb_premium:.4f}%)")
    print(f"Google Score: {score_google}/25 (Trend: {google_score})")
    print(f"Total Score: {total_score}/100")
    
    record = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "timestamp": int(datetime.now().timestamp()),
        "total_score": total_score,
        "fear_greed": fg_index,
        "rsi": rsi,
        "btc_price": price,
        "coinbase_premium": cb_premium,
        "google_trends": google_score
    }
    
    save_to_history(record)
    print(f"Recorded Successfully: {record}")

if __name__ == "__main__":
    main()
