import streamlit as st
import pandas as pd
import numpy as np
import pandas-ta as ta
import yfinance as yf
from datetime import datetime

# --- 1. CONFIGURATION & STYLES ---
st.set_page_config(page_title="Stock Scanner Mobile", layout="wide")

def inject_mobile_css():
    st.markdown("""
    <style>
        /* ปรับแต่งพื้นหลังและฟอนต์ให้สบายตาบนมือถือ */
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
        }
        .main {
            padding: 10px;
        }
        /* Card แสดงผลหุ้น */
        .stock-card {
            background-color: #1a1c24;
            border-radius: 15px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 5px solid #4CAF50;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }
        .stock-name { font-size: 1.4rem; font-weight: bold; color: #ffffff; }
        .stock-price { font-size: 1.2rem; color: #00ffcc; }
        .signal-buy { color: #00ff44; font-weight: bold; }
        .signal-sell { color: #ff4444; font-weight: bold; }
        
        /* ปรับปุ่มให้กดง่ายบนจอสัมผัส */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            height: 3em;
            background-color: #2e313d;
            transition: 0.3s;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA ENGINE (With Cache for Performance) ---
@st.cache_data(ttl=600)  # เก็บข้อมูลไว้ 10 นาทีเพื่อประหยัด Data มือถือ
def get_data(symbol):
    try:
        # สำหรับหุ้นไทยให้เติม .BK อัตโนมัติถ้าไม่มี
        ticker = f"{symbol}.BK" if not symbol.endswith((".BK", ".bk")) else symbol
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        return df
    except:
        return None

# --- 3. ANALYSIS LOGIC ---
class StockAnalyzer:
    def __init__(self, df):
        self.df = df
        self.close = df['Close'].squeeze()
        
    def analyze(self):
        # คำนวณ Indicators พื้นฐาน
        rsi = ta.rsi(self.close, length=14).iloc[-1]
        sma20 = ta.sma(self.close, length=20).iloc[-1]
        sma50 = ta.sma(self.close, length=50).iloc[-1]
        
        current_price = self.close.iloc[-1]
        
        # ระบบให้คะแนน (0-100)
        score = 50
        signals = []
        
        # Logic: RSI
        if rsi < 35: 
            score += 20
            signals.append("RSI Oversold (สะสม)")
        elif rsi > 65:
            score -= 20
            signals.append("RSI Overbought (ระวัง)")
            
        # Logic: Trend
        if current_price > sma20:
            score += 15
            signals.append("ยืนเหนือเส้น EMA20 (ขาขึ้นระยะสั้น)")
        if sma20 > sma50:
            score += 15
            signals.append("Golden Cross (แนวโน้มดี)")

        return {
            "price": current_price,
            "rsi": rsi,
            "score": score,
            "signals": signals,
            "status": "BUY" if score >= 65 else "SELL" if score <= 35 else "HOLD"
        }

# --- 4. UI RENDERER ---
def render_mobile_ui(symbol, result):
    color_class = "signal-buy" if result['status'] == "BUY" else "signal-sell" if result['status'] == "SELL" else ""
    
    st.markdown(f"""
    <div class="stock-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="stock-name">{symbol.upper()}</span>
            <span class="stock-price">{result['price']:.2f}</span>
        </div>
        <hr style="margin: 10px 0; border: 0.5px solid #333;">
        <div style="font-size: 0.9rem; color: #bbb;">
            RSI: {result['rsi']:.1f} | Score: {result['score']}/100
        </div>
        <div style="margin-top: 10px;">
            ความเห็น: <span class="{color_class}">{result['status']}</span>
        </div>
        <div style="font-size: 0.8rem; margin-top: 5px; color: #888;">
            {" • ".join(result['signals']) if result['signals'] else "ไม่มีสัญญาณเตือนพิเศษ"}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
def main():
    inject_mobile_css()
    
    st.title("📱 Stock Scan Mobile")
    
    # ส่วนรับข้อมูลหุ้น (รองรับการใส่หลายตัวคั่นด้วย comma)
    stock_input = st.text_input("ระบุชื่อหุ้น (เช่น CPALL, PTT, NVDA)", "CPALL, PTT").upper()
    symbols = [s.strip() for s in stock_input.split(",")]

    if st.button("เริ่มวิเคราะห์"):
        cols = st.columns(1) # บนมือถือให้เรียงแถวเดียว
        
        for sym in symbols:
            with st.spinner(f'กำลังวิเคราะห์ {sym}...'):
                df = get_data(sym)
                if df is not None:
                    analyzer = StockAnalyzer(df)
                    result = analyzer.analyze()
                    render_mobile_ui(sym, result)
                else:
                    st.error(f"ไม่พบข้อมูลหุ้น {sym}")

    # ส่วนท้ายจอสำหรับมือถือ
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.caption("Data provided by Yahoo Finance. ดัชนี RSI และ SMA พื้นฐาน")

if __name__ == "__main__":
    main()
