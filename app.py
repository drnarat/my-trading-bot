import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# --- CONFIG & CSS ---
st.set_page_config(page_title="Stock Scan Mobile", layout="wide")

st.markdown("""
<style>
    .stock-card { background: #1a1c24; border-radius: 12px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #4CAF50; }
    .buy { color: #00ff44; font-weight: bold; }
    .sell { color: #ff4444; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- LIGHTWEIGHT ANALYSIS LOGIC (No pandas_ta required) ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=600)
def get_analysis(symbol):
    try:
        ticker = f"{symbol}.BK" if len(symbol) <= 5 else symbol
        df = yf.download(ticker, period="1y", progress=False)
        if df.empty: return None
        
        close = df['Close'].squeeze()
        current_price = float(close.iloc[-1])
        
        # คำนวณแบบ Manual เพื่อความชัวร์ (ไม่พึ่ง Library นอก)
        rsi = float(calculate_rsi(close).iloc[-1])
        sma20 = float(close.rolling(window=20).mean().iloc[-1])
        
        score = 50
        if rsi < 30: score += 20
        if rsi > 70: score -= 20
        if current_price > sma20: score += 15
        
        return {
            "price": current_price,
            "rsi": rsi,
            "score": score,
            "status": "BUY" if score >= 60 else "SELL" if score <= 40 else "HOLD"
        }
    except:
        return None

# --- UI ---
st.title("📱 Stock Scanner (Lite)")
stock_list = st.text_input("ชื่อหุ้น (เช่น PTT, CPALL, AAPL)", "PTT, CPALL")

if st.button("วิเคราะห์ทันที"):
    for sym in stock_list.split(","):
        res = get_analysis(sym.strip().upper())
        if res:
            color = "buy" if res['status'] == "BUY" else "sell" if res['status'] == "SELL" else ""
            st.markdown(f"""
            <div class="stock-card">
                <h3>{sym.strip().upper()} : {res['price']:.2f}</h3>
                <p>RSI: {res['rsi']:.1f} | สัญญาณ: <span class="{color}">{res['status']}</span></p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(f"ไม่พบข้อมูล {sym}")
