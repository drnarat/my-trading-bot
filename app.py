import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. CONFIG & STYLES ---
st.set_page_config(page_title="Stock Scanner Pro", layout="centered")

st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #0d0d14; color: #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background: linear-gradient(135deg, #6c63ff, #4f46e5); color: white; font-weight: bold; }
    .stock-card { background: #1a1a2e; border-radius: 16px; padding: 18px; margin-bottom: 12px; border: 1px solid #2a2a4a; }
    .news-card { background: #12122a; border-radius: 10px; padding: 12px; margin-bottom: 8px; border-left: 3px solid #6c63ff; }
    .buy { color: #00b894; } .sell { color: #d63031; } .watch { color: #fdcb6e; }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINE ---
def calculate_indicators(df, p):
    """คำนวณเทคนิคคัลโดยไม่ใช้ Library ภายนอกเพื่อความเร็วและเสถียร"""
    close = df['Close'].squeeze()
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=p['rsi_p']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=p['rsi_p']).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    # SMA
    sma_s = close.rolling(window=p['sma_s']).mean()
    sma_l = close.rolling(window=p['sma_l']).mean()
    return rsi.iloc[-1], sma_s.iloc[-1], sma_l.iloc[-1]

@st.cache_data(ttl=300)
def get_stock_data(symbol, params):
    try:
        # ระบบจัดการหุ้นไทย/ต่างประเทศ
        ticker = f"{symbol}.BK" if len(symbol) <= 5 and ".BK" not in symbol.upper() else symbol
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty: return None
        
        rsi, sma_s, sma_l = calculate_indicators(data, params)
        price = float(data['Close'].iloc[-1])
        
        # Scoring Logic
        score = 50
        if rsi < 35: score += 20
        elif rsi > 65: score -= 20
        if price > sma_s: score += 15
        
        return {"price": price, "rsi": rsi, "score": score, "data": data, "full_sym": ticker}
    except: return None

# --- 3. UI VIEWS ---
def show_scan_view(params):
    st.subheader("🚀 สแกนตลาดหุ้น")
    mkt = st.selectbox("เลือกตลาด", ["SET (Thai)", "US Tech", "China ADR"])
    
    tickers = {
        "SET (Thai)": ["CPALL", "PTT", "ADVANC", "AOT", "KBANK"],
        "US Tech": ["AAPL", "TSLA", "NVDA", "MSFT", "META"],
        "China ADR": ["BABA", "NIO", "JD", "BIDU", "PDD"]
    }
    
    if st.button("เริ่มสแกน"):
        progress = st.progress(0)
        for i, sym in enumerate(tickers[mkt]):
            res = get_stock_data(sym, params)
            if res:
                color = "buy" if res['score'] >= 65 else "sell" if res['score'] <= 35 else "watch"
                st.markdown(f"""<div class="stock-card"><b>{sym}</b> | ราคา: {res['price']:,.2f} | <span class="{color}">Score: {res['score']}</span></div>""", unsafe_allow_html=True)
            progress.progress((i + 1) / len(tickers[mkt]))

def show_deep_analysis(params):
    st.subheader("🔍 วิเคราะห์เจาะลึก & ข่าว")
    with st.form("analysis_form"):
        target_sym = st.text_input("ใส่ชื่อหุ้น (เช่น PTT หรือ TSLA)").upper()
        submit_btn = st.form_submit_button("วิเคราะห์ข้อมูล")
    
    if submit_btn and target_sym:
        res = get_stock_data(target_sym, params)
        if res:
            st.metric("ราคาปัจจุบัน", f"{res['price']:,.2f}", f"RSI: {res['rsi']:.1f}")
            st.line_chart(res['data']['Close'])
            
            # ข่าวรอบ 1 ปี
            st.write("📰 ข่าวล่าสุดที่กระทบราคา:")
            ticker_obj = yf.Ticker(res['full_sym'])
            news = ticker_obj.news
            if news:
                for item in news[:5]:
                    st.markdown(f"""<div class="news-card"><a href="{item['link']}" style="color:white;text-decoration:none;"><b>{item['title']}</b></a><br><small>{item['publisher']}</small></div>""", unsafe_allow_html=True)
            else:
                st.info("ไม่พบข่าวในฐานข้อมูล yfinance")

# --- 4. MAIN APP ---
def main():
    # แถบพารามิเตอร์ข้างจอ
    with st.sidebar:
        st.title("⚙️ Settings")
        params = {
            "sma_s": st.slider("SMA สั้น", 5, 50, 20),
            "sma_l": st.slider("SMA ยาว", 50, 200, 50),
            "rsi_p": st.slider("RSI Period", 7, 21, 14)
        }
    
    tab1, tab2 = st.tabs(["Scan", "Deep Analysis"])
    with tab1: show_scan_view(params)
    with tab2: show_deep_analysis(params)

if __name__ == "__main__":
    main()
