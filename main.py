import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from settrade_v2 import Investor
from datetime import datetime

# ============================================================
# 1. PAGE & UI CONFIG
# ============================================================
st.set_page_config(page_title="Scanner Pro", page_icon="📈", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background: #0d0d14; color: #e2e8f0; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3em; background: linear-gradient(135deg, #6c63ff, #4f46e5); color: white; border: none; }
    .card { background: #1a1a2e; border: 1px solid #2a2a4a; border-radius: 15px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #6c63ff; }
    .card-buy { border-left-color: #00b894; }
    .card-sell { border-left-color: #d63031; }
    .symbol { font-family: 'IBM Plex Mono', monospace; font-size: 1.2rem; font-weight: 700; }
    .price { font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; text-align: right; }
    .score-badge { background: rgba(108,99,255,0.2); color: #6c63ff; padding: 2px 8px; border-radius: 8px; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 2. CORE DATA ENGINE
# ============================================================
def fetch_data(symbol, mkt_key, api_session=None):
    """ดึงข้อมูลโดยรองรับทั้ง Settrade และ yfinance"""
    try:
        if api_session and mkt_key == "SET":
            # กรณีใช้ Settrade API (Real-time)
            raw = api_session.get_candlestick(symbol, interval="1d", limit=150)
            df = pd.DataFrame(raw)
            df.rename(columns={'last': 'Close', 'h': 'High', 'l': 'Low', 'o': 'Open', 'v': 'Volume'}, inplace=True)
        else:
            # กรณีใช้ Yahoo Finance
            ticker = f"{symbol}.BK" if mkt_key == "SET" else symbol
            df = yf.download(ticker, period="150d", interval="1d", progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")
        return None

def analyze_stock(df):
    """คำนวณ Indicators และให้คะแนน"""
    if df is None or len(df) < 50: return None
    
    # Technical Analysis
    df.ta.rsi(length=14, append=True)
    df.ta.macd(append=True)
    bb = ta.bbands(df['Close'], length=20, std=2)
    df['BBP'] = (df['Close'] - bb.iloc[:, 0]) / (bb.iloc[:, 2] - bb.iloc[:, 0] + 1e-9)
    df.ta.sma(length=20, append=True)
    df.ta.sma(length=50, append=True)
    
    c = df.iloc[-1]
    score = 50
    # Scoring Logic
    if c['RSI_14'] < 30: score += 15
    if c['RSI_14'] > 70: score -= 15
    if c['Close'] > c['SMA_20'] > c['SMA_50']: score += 20
    
    rec = "🟢 BUY" if score >= 65 else "🔴 SELL" if score <= 35 else "🟡 WAIT"
    cls = "buy" if score >= 65 else "sell" if score <= 35 else ""
    
    return {"price": c['Close'], "rsi": c['RSI_14'], "score": score, "rec": rec, "cls": cls}

# ============================================================
# 3. UI RENDERING
# ============================================================
def main():
    st.title("📈 Pro Scanner V28")
    
    # --- Sidebar: API Connection ---
    with st.sidebar:
        st.header("🔑 Settrade API")
        app_id = st.text_input("App ID")
        app_secret = st.text_input("App Secret", type="password")
        broker_id = st.text_input("Broker ID", value="SANDBOX")
        
        if st.button("Connect API"):
            try:
                investor = Investor(app_id=app_id, app_secret=app_secret, broker_id=broker_id, app_code="SANDBOX")
                st.session_state.api = investor.Market()
                st.success("Connected!")
            except:
                st.error("Connection Failed")

    # --- Market Selection ---
    mkt = st.selectbox("เลือกตลาด", ["SET (ไทย)", "US (สหรัฐ)", "CN (จีน)"])
    mkt_key = mkt.split(" ")[0]
    
    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"],
        "CN": ["BABA", "JD", "NIO", "PDD"]
    }

    if st.button("🚀 Start Deep Scan"):
        api = st.session_state.get('api')
        cols = st.columns(1) # Mobile-friendly single column
        
        for sym in universe[mkt_key]:
            df = fetch_data(sym, mkt_key, api)
            res = analyze_stock(df)
            
            if res:
                # Render Card
                st.markdown(f"""
                <div class="card card-{res['cls']}">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <div class="symbol">{sym}</div>
                            <div class="score-badge">Score: {res['score']}</div>
                        </div>
                        <div class="price">
                            <div>{res['price']:.2f}</div>
                            <div style="font-size:0.9rem; color:#8892b0;">RSI: {res['rsi']:.1f}</div>
                        </div>
                    </div>
                    <div style="margin-top:10px; font-weight:700;">{res['rec']}</div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔎 รายละเอียดตัวบ่งชี้"):
                    st.write(f"ราคาปัจจุบัน: {res['price']}")
                    st.write(f"RSI (14): {res['rsi']:.2f}")
                    # เพิ่มกราฟย่อ
                    st.line_chart(df['Close'].tail(30))

if __name__ == "__main__":
    main()
