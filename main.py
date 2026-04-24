import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG
# ============================================================
st.set_page_config(page_title="Stock Scanner Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #050510; color: #FFBF00; }
        h1, h2, h3 { color: #00E5FF !important; }
        .stock-card { background: #101223; border: 1px solid #1E293B; border-radius: 12px; padding: 15px; margin-bottom: 12px; }
        .buy-border { border-left: 6px solid #00FF41; }
        .sell-border { border-left: 6px solid #FF3131; }
        .watch-border { border-left: 6px solid #FFD700; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.2rem; color: #00E5FF; }
        .price-text { font-family: 'IBM Plex Mono'; font-size: 1.1rem; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 10px; background-color: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. DATA UTILITIES (FETCHING FULL UNIVERSE)
# ============================================================
@st.cache_data(ttl=86400) # Cache รายชื่อหุ้นไว้ 24 ชม.
def get_full_universe():
    # --- THAI SET (ดึงจาก Wikipedia หรือใส่รายชื่อ SET100 เป็นพื้นฐาน) ---
    try:
        # ดึงรายชื่อหุ้น SET100 เพื่อความรวดเร็วและแม่นยำในการวิเคราะห์
        url = "https://en.wikipedia.org/wiki/SET100_Index"
        tables = pd.read_html(url)
        th_stocks = tables[1]['Symbol'].tolist()
    except:
        th_stocks = ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC"] # Fallback

    # --- US TECH (25+ หุ้น) ---
    us_stocks = [
        "AAPL", "MSFT", "NVDA", "GOOGL", "META", "AMZN", "TSLA", "AMD", "AVGO", "ORCL", 
        "ADBE", "CRM", "NFLX", "INTC", "QCOM", "TXN", "MU", "AMAT", "LRCX", "PANW", 
        "SNPS", "CDNS", "ASML", "CSCO", "IBM", "SHOP", "UBER"
    ]

    # --- CN TECH (20+ หุ้น) ---
    cn_stocks = [
        "BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI", "TCOM", "NTES",
        "IQ", "WB", "FUTU", "TIGR", "BEKE", "ZTO", "VIP", "GDS", "TAL", "EDU", "LKNCY"
    ]

    return {"SET": th_stocks, "US": us_stocks, "CN": cn_stocks}

# ============================================================
# 3. ANALYSIS ENGINE
# ============================================================
class TradingEngine:
    @staticmethod
    def fetch_data(symbol, mkt_key):
        ticker = f"{symbol}.BK" if mkt_key == "SET" else symbol
        df = yf.download(ticker, period="150d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    @staticmethod
    def analyze(df, p):
        # คำนวณ Indicators ตาม Parameter ที่ผู้ใช้ตั้ง
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        
        c = df.iloc[-1]
        score = 50
        if c['RSI'] < p['rsi_os']: score += 15
        elif c['RSI'] > p['rsi_ob']: score -= 15
        if c['Close'] > c['SMA_S'] > c['SMA_M']: score += 20
        
        atr = c['ATR']
        res = {
            "price": c['Close'], "rsi": c['RSI'], "score": score,
            "chg": (c['Close']/df.iloc[-2]['Close']-1)*100,
            "t1": c['Close'] + (atr * 2), "sl": c['Close'] - (atr * 1.5)
        }
        res["rec"] = "🟢 ซื้อ" if score >= 65 else "🔴 ขาย" if score <= 35 else "🟡 เฝ้า"
        res["cls"] = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
        return res

# ============================================================
# 4. APP RENDER
# ============================================================
def main():
    apply_ui_theme()
    engine = TradingEngine()
    universe = get_full_universe()

    # --- PARAMETERS (Sidebar for cleaner Mobile View) ---
    with st.expander("⚙️ ตั้งค่า Parameters Analysis"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            sma_s = st.slider("SMA สั้น", 5, 50, 20)
            sma_m = st.slider("SMA กลาง", 20, 100, 50)
            rsi_p = st.slider("RSI Period", 7, 21, 14)
        with col_p2:
            rsi_ob = st.slider("RSI Overbought", 60, 85, 70)
            rsi_os = st.slider("RSI Oversold", 15, 40, 30)
            atr_p = st.slider("ATR Period", 7, 21, 14)
        p = locals() # Capture sliders

    # --- MARKET SELECTOR ---
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    m_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    # --- FILTERS ---
    st.markdown("### 2️⃣ ตัวกรอง")
    f_sigs = st.multiselect("สัญญาณ", ["🟢 ซื้อ", "🟡 เฝ้า", "🔴 ขาย"], default=["🟢 ซื้อ", "🟡 เฝ้า"])

    # --- SCAN BUTTON ---
    stocks_to_scan = universe[m_key]
    if st.button(f"🚀 เริ่มสแกน {len(stocks_to_scan)} หุ้น ({m_key})"):
        results = []
        prog = st.progress(0)
        status = st.empty()

        for idx, sym in enumerate(stocks_to_scan):
            status.text(f"กำลังวิเคราะห์: {sym} ({idx+1}/{len(stocks_to_scan)})")
            df = engine.fetch_data(sym, m_key)
            if df is not None and len(df) > 50:
                res = engine.analyze(df, p)
                if res['rec'] in f_sigs:
                    results.append({"sym": sym, **res})
            prog.progress((idx+1)/len(stocks_to_scan))
        
        status.success(f"สแกนเสร็จสิ้น! พบ {len(results)} หุ้นที่ตรงเงื่อนไข")
        
        # Display Cards
        for r in results:
            st.markdown(f"""
            <div class="stock-card {r['cls']}-border">
                <div style="display:flex; justify-content:space-between;">
                    <span class="symbol-text">{r['sym']}</span>
                    <span class="price-text">{r['price']:,.2f} ({r['chg']:+.2f}%)</span>
                </div>
                <div style="margin: 10px 0; font-size: 0.9rem; color: #8892b0;">
                    Score: {r['score']} | RSI: {r['rsi']:.1f}
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#00E5FF; font-size:0.8rem;">🎯 TP: {r['t1']:.2f} | 🛡️ SL: {r['sl']:.2f}</span>
                    <b style="font-size:1rem;">{r['rec']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
