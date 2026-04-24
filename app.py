import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. SETTINGS & MOBILE CSS ---
st.set_page_config(page_title="Stock Scanner Lite", layout="centered")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d0d14; color: #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background: linear-gradient(135deg, #6c63ff, #4f46e5); color: white; font-weight: bold; }
    .stock-card {
        background: #1a1a2e; border-radius: 16px; padding: 18px; margin-bottom: 12px; border: 1px solid #2a2a4a;
    }
    .buy { color: #00b894; font-weight: bold; }
    .sell { color: #d63031; font-weight: bold; }
    .ind-item { background: #12122a; padding: 8px; border-radius: 10px; text-align: center; border: 1px solid #2a2a4a; }
</style>
""", unsafe_allow_html=True)

# --- 2. PURE PANDAS INDICATORS (No pandas_ta required) ---
def get_indicators(df):
    # คำนวณ RSI แบบมาตรฐาน (Wilder's Smoothing เทียมด้วย rolling mean)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['rsi'] = 100 - (100 / (1 + rs))
    
    # คำนวณ SMA
    df['sma20'] = df['close'].rolling(window=20).mean()
    df['sma50'] = df['close'].rolling(window=50).mean()
    return df

@st.cache_data(ttl=600)
def fetch_and_analyze(symbol):
    try:
        ticker = f"{symbol}.BK" if len(symbol) <= 5 else symbol
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty: return None
        
        # จัดการ Dataframe ให้คลีน
        df = data[['Close']].copy()
        df.columns = ['close']
        df = get_indicators(df)
        
        last_row = df.iloc[-1]
        price = float(last_row['close'])
        rsi = float(last_row['rsi'])
        sma20 = float(last_row['sma20'])
        
        # วิเคราะห์ง่ายๆ
        score = 50
        if rsi < 35: score += 20
        if rsi > 65: score -= 20
        if price > sma20: score += 15
        
        return {
            "price": price,
            "rsi": rsi,
            "score": score,
            "status": "BUY" if score >= 65 else "SELL" if score <= 35 else "HOLD"
        }
    except:
        return None

# --- 3. UI DASHBOARD ---
def main():
    st.title("📱 Stock Scan Lite")
    st.write("เวอร์ชันเสถียรสำหรับเปิดบนมือถือ")

    stocks = st.text_input("ชื่อหุ้น (เช่น PTT, CPALL, NVDA)", "CPALL, PTT").upper()
    
    if st.button("🚀 เริ่มสแกนหุ้น"):
        symbols = [s.strip() for s in stocks.split(",")]
        for sym in symbols:
            res = fetch_and_analyze(sym)
            if res:
                status_color = "buy" if res['status'] == "BUY" else "sell" if res['status'] == "SELL" else ""
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span style="font-size: 1.2rem; font-weight: bold;">{sym}</span>
                        <span style="font-size: 1.2rem; font-weight: bold; color: #00ffcc;">{res['price']:,.2f}</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0;">
                        <div class="ind-item">
                            <div style="font-size: 0.7rem; color: #8892b0;">RSI (14)</div>
                            <div style="font-size: 1rem;">{res['rsi']:.1f}</div>
                        </div>
                        <div class="ind-item">
                            <div style="font-size: 0.7rem; color: #8892b0;">คำแนะนำ</div>
                            <div class="{status_color}" style="font-size: 1rem;">{res['status']}</div>
                        </div>
                    </div>
                    <div style="font-size: 0.75rem; text-align: center; color: #4a4a6a;">
                        Score: {res['score']}/100 | Calculated by Pure Pandas
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"ไม่พบข้อมูลหุ้น {sym}")

if __name__ == "__main__":
    main()
