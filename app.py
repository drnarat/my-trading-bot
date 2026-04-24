import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. CONFIG & HIGH-CONTRAST UI ---
st.set_page_config(page_title="Stock Scanner Pro", layout="centered")

st.markdown("""
<style>
    /* ปรับสีพื้นหลังและฟอนต์หลักให้ชัดเจน */
    [data-testid="stAppViewContainer"] { 
        background-color: #0d0d14; 
        color: #ffffff !important; 
    }
    
    /* บังคับสีฟอนต์ในทุกส่วนของแอป */
    h1, h2, h3, p, span, div, label { 
        color: #ffffff !important; 
    }

    /* สไตล์ Card หุ้น */
    .stock-card { 
        background: #1a1a2e; 
        border-radius: 16px; 
        padding: 20px; 
        margin-bottom: 15px; 
        border: 1px solid #3e3e5e;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }

    /* ปุ่มกด */
    .stButton>button { 
        width: 100%; 
        border-radius: 12px; 
        height: 3.5rem; 
        background: linear-gradient(135deg, #6c63ff, #4f46e5); 
        color: white !important; 
        font-weight: bold; 
        border: none;
    }

    /* สัญญาณไฟจราจร */
    .buy { color: #00ff9d !important; font-weight: bold; }
    .sell { color: #ff4d4d !important; font-weight: bold; }
    .watch { color: #ffcc00 !important; font-weight: bold; }
    
    /* News Card */
    .news-card { 
        background: #12122a; 
        border-radius: 10px; 
        padding: 15px; 
        margin-bottom: 10px; 
        border-left: 4px solid #6c63ff; 
    }
    
    /* ปรับแต่ง Sidebar ให้ฟอนต์ชัด */
    section[data-testid="stSidebar"] {
        background-color: #11111d !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINE: ADVANCED INDICATORS ---
def compute_all_indicators(df, p):
    """คำนวณอินดิเคเตอร์แบบครบชุดโดยใช้ Pure Pandas"""
    # ตรวจสอบและดึงราคาปิดให้ถูกต้อง (รองรับ yfinance Multi-index)
    if isinstance(df['Close'], pd.DataFrame):
        close = df['Close'].iloc[:, 0]
        high = df['High'].iloc[:, 0]
        low = df['Low'].iloc[:, 0]
        vol = df['Volume'].iloc[:, 0]
    else:
        close = df['Close']
        high = df['High']
        low = df['Low']
        vol = df['Volume']

    I = {}
    # SMA
    I['sma_s'] = close.rolling(window=p['sma_s']).mean().iloc[-1]
    I['sma_l'] = close.rolling(window=p['sma_l']).mean().iloc[-1]
    
    # RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=p['rsi_p']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=p['rsi_p']).mean()
    rs = gain / (loss + 1e-9)
    I['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]
    
    # MACD
    ema12 = close.ewm(span=p['macd_f'], adjust=False).mean()
    ema26 = close.ewm(span=p['macd_s'], adjust=False).mean()
    I['macd'] = (ema12 - ema26).iloc[-1]
    I['signal'] = (ema12 - ema26).ewm(span=p['macd_sg'], adjust=False).mean().iloc[-1]
    
    # Bollinger Bands
    ma20 = close.rolling(window=p['bb_p']).mean()
    std20 = close.rolling(window=p['bb_p']).std()
    I['bbu'] = (ma20 + (p['bb_k'] * std20)).iloc[-1]
    I['bbl'] = (ma20 - (p['bb_k'] * std20)).iloc[-1]
    
    # Volume Ratio
    avg_vol = vol.rolling(window=20).mean().iloc[-1]
    I['vol_r'] = vol.iloc[-1] / (avg_vol + 1e-9)
    
    I['price'] = close.iloc[-1]
    return I

@st.cache_data(ttl=300)
def get_full_analysis(symbol, p):
    try:
        ticker = f"{symbol}.BK" if len(symbol) <= 5 and ".BK" not in symbol.upper() else symbol
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        if data.empty or len(data) < 50: return None
        
        I = compute_all_indicators(data, p)
        
        # Scoring Logic
        score = 50
        if I['rsi'] < p['rsi_os']: score += 15
        elif I['rsi'] > p['rsi_ob']: score -= 15
        if I['price'] > I['sma_s']: score += 10
        if I['macd'] > I['signal']: score += 10
        if I['price'] < I['bbl']: score += 10
        
        return {"I": I, "score": score, "data": data, "full_sym": ticker}
    except Exception as e:
        return None

# --- 3. UI COMPONENTS ---
def view_scanner(p):
    st.subheader("🚀 Stock Scanner")
    market = st.radio("เลือกตลาดหุ้น", ["SET (Thai)", "US Tech", "China ADR"], horizontal=True)
    
    tickers = {
        "SET (Thai)": ["CPALL", "PTT", "ADVANC", "KBANK", "AOT", "SCB", "GULF", "OR"],
        "US Tech": ["AAPL", "TSLA", "NVDA", "MSFT", "META", "AMZN", "GOOGL"],
        "China ADR": ["BABA", "NIO", "JD", "BIDU", "PDD"]
    }
    
    if st.button("เริ่มสแกนหุ้น"):
        results = []
        progress = st.progress(0)
        stock_list = tickers[market]
        
        for i, sym in enumerate(stock_list):
            res = get_full_analysis(sym, p)
            if res:
                I = res['I']
                color = "buy" if res['score'] >= 65 else "sell" if res['score'] <= 35 else "watch"
                rec = "ซื้อ" if res['score'] >= 65 else "ขาย" if res['score'] <= 35 else "เฝ้าระวัง"
                
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.4rem; font-weight:bold;">{sym}</span>
                        <span style="font-size:1.4rem; font-weight:bold;">{I['price']:,.2f}</span>
                    </div>
                    <div style="margin: 10px 0; font-size:0.9rem;">
                        RSI: {I['rsi']:.1f} | Vol: {I['vol_r']:.1f}x | Score: {res['score']}
                    </div>
                    <div class="{color}" style="font-size:1.1rem;">คำแนะนำ: {rec}</div>
                </div>
                """, unsafe_allow_html=True)
            progress.progress((i + 1) / len(stock_list))

def view_deep(p):
    st.subheader("🔍 วิเคราะห์เจาะลึก & ข่าวล่าสุด")
    with st.form("deep_form"):
        target = st.text_input("ใส่ชื่อหุ้น (เช่น PTT, CPALL, TSLA, NVDA)").upper()
        btn = st.form_submit_button("วิเคราะห์หุ้นตัวนี้")
    
    if btn and target:
        res = get_full_analysis(target, p)
        if res:
            I = res['I']
            st.write(f"### ผลการวิเคราะห์: {target}")
            c1, c2, c3 = st.columns(3)
            c1.metric("ราคาปัจจุบัน", f"{I['price']:,.2f}")
            c2.metric("RSI (14)", f"{I['rsi']:.1f}")
            c3.metric("Score", f"{res['score']}/100")
            
            st.line_chart(res['data']['Close'])
            
            # ข่าว
            st.write("#### 📰 ข่าวสารรอบปีที่กระทบราคา")
            t_obj = yf.Ticker(res['full_sym'])
            try:
                news_list = t_obj.news
                if news_list:
                    for n in news_list[:5]:
                        st.markdown(f"""
                        <div class="news-card">
                            <a href="{n['link']}" target="_blank" style="text-decoration:none;">
                                <div style="color:#6c63ff; font-weight:bold; font-size:1rem;">{n['title']}</div>
                                <div style="color:#8892b0; font-size:0.8rem; margin-top:5px;">Source: {n['publisher']}</div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("ไม่พบข่าวสารในขณะนี้")
            except:
                st.info("ไม่สามารถดึงข่าวได้ในขณะนี้")
        else:
            st.error("ไม่พบข้อมูลหุ้นตัวนี้ กรุณาตรวจสอบชื่อ Ticker อีกครั้ง")

# --- 4. MAIN & PARAMETERS ---
def main():
    with st.sidebar:
        st.header("⚙️ ตัวแปรวิเคราะห์")
        p = {}
        with st.expander("SMA & RSI", expanded=True):
            p['sma_s'] = st.slider("SMA สั้น", 5, 50, 20)
            p['sma_l'] = st.slider("SMA ยาว", 50, 200, 50)
            p['rsi_p'] = st.slider("RSI Period", 7, 21, 14)
            p['rsi_ob'] = st.slider("RSI Overbought", 60, 80, 70)
            p['rsi_os'] = st.slider("RSI Oversold", 20, 40, 30)
        
        with st.expander("MACD & BB"):
            p['macd_f'] = st.number_input("MACD Fast", value=12)
            p['macd_s'] = st.number_input("MACD Slow", value=26)
            p['macd_sg'] = st.number_input("MACD Signal", value=9)
            p['bb_p'] = st.number_input("BB Period", value=20)
            p['bb_k'] = st.number_input("BB StdDev", value=2)

    tab1, tab2 = st.tabs(["Stock Scanner", "Deep Analysis"])
    with tab1: view_scanner(p)
    with tab2: view_deep(p)

if __name__ == "__main__":
    main()
