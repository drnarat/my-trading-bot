import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="Stock Scanner Pro v3", layout="centered")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d0d14; color: #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background: linear-gradient(135deg, #6c63ff, #4f46e5); color: white; font-weight: bold; }
    .stock-card { background: #1a1a2e; border-radius: 16px; padding: 18px; margin-bottom: 12px; border: 1px solid #2a2a4a; }
    .news-card { background: #12122a; border-radius: 10px; padding: 12px; margin-bottom: 8px; border-left: 3px solid #6c63ff; }
    .buy { color: #00b894; } .sell { color: #d63031; } .watch { color: #fdcb6e; }
    .ind-item { background: #12122a; padding: 8px; border-radius: 10px; text-align: center; border: 1px solid #2a2a4a; }
</style>
""", unsafe_allow_html=True)

# --- 2. ENGINE: PURE PANDAS CALCULATION ---
def get_indicators(df, p):
    c = df['Close'].squeeze()
    # RSI
    delta = c.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=p['rsi_p']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=p['rsi_p']).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    # SMA
    sma_s = c.rolling(window=p['sma_s']).mean()
    sma_l = c.rolling(window=p['sma_l']).mean()
    return rsi.iloc[-1], sma_s.iloc[-1], sma_l.iloc[-1]

@st.cache_data(ttl=3600)
def fetch_stock_data(symbol, params):
    try:
        data = yf.download(symbol, period="1y", interval="1d", progress=False)
        if data.empty: return None
        rsi, sma_s, sma_l = get_indicators(data, params)
        price = float(data['Close'].iloc[-1])
        
        score = 50
        if rsi < 30: score += 20
        elif rsi > 70: score -= 20
        if price > sma_s: score += 15
        
        return {"price": price, "rsi": rsi, "sma_s": sma_s, "sma_l": sma_l, "score": score, "data": data}
    except: return None

# --- 3. UI VIEWS ---
def view_scan(params):
    st.title("🚀 Multi-Market Scanner")
    market = st.radio("เลือกตลาดหุ้น", ["TH (SET)", "US (Nasdaq/NYSE)", "CN (China ADR)"], horizontal=True)
    
    # ตัวอย่างรายชื่อหุ้นตามตลาด
    tickers = {
        "TH (SET)": ["CPALL.BK", "PTT.BK", "ADVANC.BK", "KBANK.BK", "SCB.BK"],
        "US (Nasdaq/NYSE)": ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"],
        "CN (China ADR)": ["BABA", "NIO", "JD", "BIDU", "PDD"]
    }
    
    selected_list = tickers[market]
    if st.button(f"เริ่มสแกนตลาด {market}"):
        for sym in selected_list:
            res = fetch_stock_data(sym, params)
            if res:
                color = "buy" if res['score'] >= 65 else "sell" if res['score'] <= 35 else "watch"
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex;justify-content:space-between;">
                        <b>{sym}</b> <span class="{color}">{res['price']:,.2f}</span>
                    </div>
                    <div style="font-size:0.8rem;color:#8892b0;">RSI: {res['rsi']:.1f} | Score: {res['score']}</div>
                </div>
                """, unsafe_allow_html=True)

def view_analysis(params):
    st.title("🔍 Deep Analysis & News")
    sym = st.text_input("กรอกชื่อหุ้นที่ต้องการวิเคราะห์ (เช่น PTT.BK หรือ TSLA)").upper()
    
    if sym:
        res = fetch_stock_data(sym, params)
        if res:
            st.metric("ราคาปัจจุบัน", f"{res['price']:,.2f}", f"{res['score']} pts")
            
            # --- ข่าวจาก Internet (รอบ 1 ปี) ---
            st.subheader("📰 ข่าวและปัจจัยกระทบราคา (รอบล่าสุด)")
            ticker_obj = yf.Ticker(sym)
            news = ticker_obj.news
            if news:
                for item in news[:5]:
                    st.markdown(f"""
                    <div class="news-card">
                        <a href="{item['link']}" target="_blank" style="text-decoration:none;color:#fff;">
                            <b>{item['title']}</b><br>
                            <small style="color:#8892b0;">Source: {item['publisher']}</small>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("ไม่พบข่าวล่าสุดผ่าน API ในขณะนี้")
            
            # กราฟราคา 1 ปี
            st.line_chart(res['data']['Close'])

# --- 4. MAIN ROUTER ---
def main():
    # Parameters ส่วนที่เคยหายไป
    with st.sidebar:
        st.header("⚙️ Indicators Settings")
        params = {
            "sma_s": st.slider("SMA Short Period", 5, 50, 20),
            "sma_l": st.slider("SMA Long Period", 50, 200, 50),
            "rsi_p": st.slider("RSI Period", 7, 21, 14)
        }
    
    tab1, tab2 = st.tabs(["Stock Scan", "Deep Analysis"])
    with tab1: view_scan(params)
    with tab2: view_analysis(params)

if __name__ == "__main__":
    main()
