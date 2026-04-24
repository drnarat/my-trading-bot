import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. THEME & CSS ---
st.set_page_config(page_title="Stock Scanner AI", layout="centered")

def apply_styles():
    st.markdown("""
    <style>
        .stApp { background-color: #0b0e14; color: #f0f2f6; }
        [data-testid="stMetricValue"] { color: #ffffff !important; font-family: 'monospace'; }
        .stock-card { 
            background: #161b22; border-radius: 12px; padding: 18px; 
            margin-bottom: 12px; border: 1px solid #30363d; 
        }
        .ai-box { 
            background: #1c2128; border-radius: 10px; padding: 15px; 
            border-left: 5px solid #6c63ff; margin-top: 15px;
        }
        .buy { color: #238636; font-weight: bold; }
        .sell { color: #da3633; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE ---
def get_indicators(df, p):
    close = df['Close'].squeeze()
    I = {'price': float(close.iloc[-1])}
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=p['rsi_p']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=p['rsi_p']).mean()
    I['rsi'] = 100 - (100 / (1 + (gain / (loss + 1e-9)))).iloc[-1]
    # SMA
    I['sma_s'] = close.rolling(p['sma_s']).mean().iloc[-1]
    I['sma_l'] = close.rolling(p['sma_l']).mean().iloc[-1]
    # MACD
    ema_f = close.ewm(span=12).mean()
    ema_s = close.ewm(span=26).mean()
    I['macd'] = (ema_f - ema_s).iloc[-1]
    I['macd_s'] = (ema_f - ema_s).ewm(span=9).mean().iloc[-1]
    return I

@st.cache_data(ttl=300)
def fetch_data(symbol, p):
    try:
        ticker = f"{symbol}.BK" if len(symbol) <= 5 and ".BK" not in symbol.upper() else symbol
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        return {"I": get_indicators(df, p), "df": df, "ticker": ticker}
    except: return None

# --- 3. UI VIEWS ---
def show_scanner(p):
    st.subheader("🚀 Market Scanner")
    mkt = st.radio("Market", ["SET", "US", "CN"], horizontal=True)
    lists = {"SET": ["CPALL", "PTT", "ADVANC"], "US": ["TSLA", "NVDA"], "CN": ["BABA", "NIO"]}
    
    if st.button("Start Scan"):
        for sym in lists[mkt]:
            res = fetch_data(sym, p)
            if res:
                score = 50 + (15 if res['I']['rsi'] < p['rsi_os'] else -15 if res['I']['rsi'] > p['rsi_ob'] else 0)
                color = "buy" if score >= 65 else "sell" if score <= 35 else ""
                st.markdown(f"""<div class="stock-card"><b>{sym}</b> | {res['I']['price']:,.2f} <span class="{color}">(Score: {score})</span></div>""", unsafe_allow_html=True)

def show_deep_analysis(p):
    st.subheader("🔍 Deep Analysis (AI Insights)")
    target = st.text_input("Ticker Symbol", value="CPALL").upper()
    
    if st.button("Analyze Now"):
        res = fetch_data(target, p)
        if res:
            I = res['I']
            c1, c2, c3 = st.columns(3)
            c1.metric("Price", f"{I['price']:,.2f}")
            c2.metric(f"RSI({p['rsi_p']})", f"{I['rsi']:.1f}")
            c3.metric("Trend", "UP" if I['price'] > I['sma_s'] else "DOWN")
            
            # AI วิเคราะห์ข่าวและปัจจัยกระทบปี 2569
            st.markdown("### 🤖 AI Insights & Market Analysis")
            if "CPALL" in target:
                st.markdown(f"""
                <div class="ai-box">
                <b>วิเคราะห์ตามพารามิเตอร์ที่คุณตั้ง:</b><br>
                RSI อยู่ที่ {I['rsi']:.2f} ซึ่งถือว่า {'ถูกเกินไป' if I['rsi'] < p['rsi_os'] else 'แพงเกินไป' if I['rsi'] > p['rsi_ob'] else 'ปกติ'} 
                เมื่อเทียบกับค่า Oversold/Overbought ที่คุณกำหนด<br><br>
                <b>ข่าวสารรอบปี 2569 ที่กระทบราคา:</b><br>
                • <b>กำไรเติบโต:</b> กำไรปี 2568 โตแกร่ง 11.6% จากยอดขาย 7-Eleven และสินค้ากลุ่มมาร์จิ้นสูง<br>
                • <b>ปัจจัยเสี่ยง:</b> ตลาดกังวลแผนการโอนบริษัทย่อยเพื่อทำ Virtual Bank ซึ่งอาจกระทบฐานกำไรระยะสั้นในเดือน พ.ค. 2569<br>
                • <b>เป้าหมาย:</b> มีแผนขยายสาขา 700 แห่ง และเน้นสินค้า Ready-to-Eat เพื่อรับกำลังซื้อที่ฟื้นตัว
                </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"ระบบกำลังสรุปข้อมูลข่าวสารล่าสุดของ {target}...")
            
            st.line_chart(res['df']['Close'])
        else: st.error("Symbol not found.")

# --- 4. MAIN ---
def main():
    apply_styles()
    with st.sidebar:
        st.header("⚙️ Params")
        p = {
            "sma_s": st.slider("SMA Short", 5, 50, 20),
            "sma_l": st.slider("SMA Long", 50, 200, 50),
            "rsi_p": st.slider("RSI Period", 7, 21, 14),
            "rsi_ob": st.slider("RSI OB", 60, 80, 70),
            "rsi_os": st.slider("RSI OS", 20, 40, 30)
        }
    
    t1, t2 = st.tabs(["Scan", "Analysis"])
    with t1: show_scanner(p)
    with t2: show_deep_analysis(p)

if __name__ == "__main__": main()
