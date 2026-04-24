def get_data(symbol, mkt_key):
    ticker_sym = f"{symbol}.BK" if mkt_key == "SET" else symbol
    df = yf.download(ticker_sym, period="200d", interval="1d", progress=False)
    
    if df.empty: 
        return None, None

    # --- เพิ่ม 2 บรรทัดนี้เพื่อแก้ปัญหา Multi-Index ---
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0) 
    # ----------------------------------------------

    # คำนวณ Indicators ต่อตามปกติ
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True)
    
    # ส่วนของ Bollinger Bands (ปรับให้ใช้ iloc เพื่อความปลอดภัย)
    bb = ta.bbands(df['Close'], length=20, std=2)
    df['BBL'] = bb.iloc[:, 0]
    df['BBM'] = bb.iloc[:, 1]
    df['BBU'] = bb.iloc[:, 2]
    df['BBP'] = (df['Close'] - df['BBL']) / (df['BBU'] - df['BBL'] + 1e-9)
    
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    df.ta.atr(length=14, append=True)
    
    # Ichimoku
    ichi, _ = ta.ichimoku(df['High'], df['Low'], df['Close'])
    df = pd.concat([df, ichi], axis=1)
    
    # Fundamental
    info = yf.Ticker(ticker_sym).info
    return df, info
