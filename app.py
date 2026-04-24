import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. CONFIG & HIGH-CONTRAST UI ---
st.set_page_config(page_title="Stock Scanner Pro", layout="centered")

st.markdown("""
<style>
    /* บังคับสีฟอนต์ให้เด่นชัดบนพื้นหลังมืด */
    [data-testid="stAppViewContainer"], .main, .stMarkdown, p, span, label, h1, h2, h3 {
        color: #ffffff !important;
    }
    
    /* สไตล์ Card หุ้นแบบพรีเมียม */
    .stock-card {
        background: #1a1a2e;
        border: 1px solid #3e3e5e;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }

    /* ปุ่มกดขนาดใหญ่สำหรับมือถือ */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.8rem;
        background: linear-gradient(135deg, #6c63ff, #4f46e5);
        color: white !important;
        font-weight: 700;
        font-size: 1.1rem;
        border: none;
        box-shadow: 0 4px 15px rgba(108, 99, 255, 0.4);
    }

    /* แถบข้าง Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #11111d !important;
        border-right: 1px solid #2a2a4a;
    }

    /* สีสัญญาณซื้อขาย */
    .buy-text { color: #00ff9d !important; font-weight: 800; font-size: 1.2rem; }
    .sell-text { color: #ff4d4d !important; font-weight: 800; font-size: 1.2rem; }
    .watch-text { color: #ffcc00 !important; font-weight: 800; font-size: 1.2rem; }

    /* News Card */
    .news-card {
        background: #12122a;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #6c63ff;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINE: ADVANCED INDICATORS ---
def compute_all_indicators(df, p):
    # ปรับปรุงการดึง Close Price ให้รองรับทุกรูปแบบของ yfinance
    if isinstance(df['Close'], pd.DataFrame):
        close = df['Close'].iloc[:, 0]
        vol = df['Volume'].iloc[:, 0]
    else:
        close = df['Close']
        vol = df['Volume']

    I = {}
    # 1. Moving Averages
    I['sma_s'] = close.rolling(window=p['sma_s']).mean().iloc[-1]
    I['sma_l'] = close.rolling(window=p['sma_l']).mean().iloc[-1]
    
    # 2. RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=p['rsi_p']).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=p['rsi_p']).mean()
    rs = gain / (loss + 1e-9)
    I['rsi'] = (100 - (100 / (1 + rs))).iloc[-1]
    
    # 3. MACD
    ema_f = close.ewm(span=p['macd_f'], adjust=False).mean()
    ema_s = close.ewm(span=p['macd_s'], adjust=False).mean()
    macd_line = ema_f - ema_s
    signal_line = macd_line.ewm(span=p['macd_sg'], adjust=False).mean()
    I['macd'] = macd_line.iloc[-1]
    I['macd_sig'] = signal_line.iloc[-1]
    
    # 4. Bollinger Bands
    ma_bb = close.rolling(window=p['bb_p']).mean()
    std_bb = close.rolling(window=p['bb_p']).std()
    I['bbu'] = (ma_bb + (p['bb_k'] * std_bb)).iloc[-1]
    I['bbl'] = (ma_bb - (p['bb_k'] * std_bb)).iloc[-1]
    
    # 5. Volume Ratio
    I['vol_r'] = vol.iloc[-1] / (vol.rolling(window=20).mean().iloc[-1] + 1e-9)
    
    I['price'] = close.iloc[-1]
    return I

@st.cache_data(ttl=300)
def get_full_analysis(symbol, p):
    try:
        # หุ้นไทยใส่ .BK อัตโนมัติ
        ticker_name = f"{symbol}.BK" if len(symbol) <= 5 and ".BK" not in symbol.upper() else symbol
        data = yf.download(ticker_name, period="1y", interval="1d", progress=False)
        
        if data.empty or len(data) < 50: return None
        
        I = compute_all_indicators(data, p)
        
        # Scoring Logic (Full 100 Points)
        sc = 50
        if I['rsi'] < p['rsi_os']: sc += 15
        elif I['rsi'] > p['rsi_ob']: sc -= 15
        if I['price'] > I['sma_s']: sc += 10
        if I['macd'] > I['macd_sig']: sc += 15
        if I['price'] < I['bbl']: sc += 10
        
        return {"I": I, "score": sc, "data": data, "ticker": ticker_name}
    except:
        return None

# --- 3. UI COMPONENTS ---
def view_scanner(p):
    st.subheader("🚀 สแกนตลาดหุ้นรายวัน")
    mkt = st.radio("เลือกตลาด", ["SET (Thailand)", "US Tech (Nasdaq)", "CN Tech (ADR)"], horizontal=True)
    
    tickers = {
        "SET (Thailand)": ["CPALL", "PTT", "ADVANC", "KBANK", "AOT", "SCB", "GULF", "DELTA.BK"],
        "US Tech (Nasdaq)": ["AAPL", "TSLA", "NVDA", "MSFT", "META", "AMZN", "GOOGL"],
        "CN Tech (ADR)": ["BABA", "NIO", "JD", "BIDU", "PDD"]
    }
    
    if st.button("🔍 เริ่มการสแกนทันที"):
        stock_list = tickers[mkt]
        progress_bar = st.progress(0)
        
        for i, sym in enumerate(stock_list):
            res = get_full_analysis(sym, p)
            if res:
                I = res['I']
                # ตัดสินใจเลือกสีและคำแนะนำ
                if res['score'] >= 65: cls, rec = "buy-text", "ซื้อ"
                elif res['score'] <= 35: cls, rec = "sell-text", "ขาย"
                else: cls, rec = "watch-text", "เฝ้าระวัง"
                
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:1.5rem; font-weight:800;">{sym}</span>
                        <span style="font-size:1.5rem; font-weight:800; color:#00ffcc;">{I['price']:,.2f}</span>
                    </div>
                    <div style="margin: 15px 0; font-size:0.95rem; color:#8892b0;">
                        RSI: {I['rsi']:.1f} | MACD: {'Bull' if I['macd']>I['macd_sig'] else 'Bear'} | Vol: {I['vol_r']:.1f}x
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="{cls}">คำแนะนำ: {rec}</span>
                        <span style="background:#6c63ff; padding:2px 10px; border-radius:10px;">Score: {res['score']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            progress_bar.progress((i + 1) / len(stock_list))

def view_deep(p):
    st.subheader("🔍 วิเคราะห์เจาะลึก & ข่าวสารรอบปี")
    with st.form("deep_analysis_form"):
        target = st.text_input("ใส่ชื่อย่อหุ้น (Ticker Symbol)", placeholder="เช่น PTT, TSLA, NVDA").upper()
        submit = st.form_submit_button("วิเคราะห์ข้อมูลเชิงลึก")
    
    if submit and target:
        res = get_full_analysis(target, p)
        if res:
            I = res['I']
            st.markdown(f"## {target} Analysis")
            col1, col2, col3 = st.columns(3)
            col1.metric("ราคาปัจจุบัน", f"{I['price']:,.2f}")
            col2.metric("RSI (14)", f"{I['rsi']:.1f}")
            col3.metric("Health Score", f"{res['score']}/100")
            
            # กราฟราคาแบบ Interactive
            st.line_chart(res['data']['Close'])
            
            # ข่าวสาร (ดึงผ่าน yfinance)
            st.markdown("### 📰 ข่าวสารที่กระทบราคา")
            t_obj = yf.Ticker(res['ticker'])
            try:
                news = t_obj.news
                if news:
                    for n in news[:5]:
                        st.markdown(f"""
                        <div class="news-card">
                            <a href="{n['link']}" target="_blank" style="text-decoration:none;">
                                <div style="color:#ffffff; font-weight:bold; font-size:1.05rem; margin-bottom:5px;">{n['title']}</div>
                                <div style="color:#6c63ff; font-size:0.85rem;">Source: {n['publisher']}</div>
                            </a>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("ไม่พบข่าวสารล่าสุดในขณะนี้")
            except:
                st.warning("ระบบดึงข่าวขัดข้องชั่วคราว")
        else:
            st.error("ไม่พบข้อมูลหุ้น กรุณาเช็คชื่อ Ticker อีกครั้ง")

# --- 4. PARAMETERS & SIDEBAR ---
def main():
    with st.sidebar:
        st.title("🛡️ Trading Params")
        p = {}
        with st.expander("SMA & RSI Settings", expanded=True):
            p['sma_s'] = st.slider("SMA สั้น (วัน)", 5, 50, 20)
            p['sma_l'] = st.slider("SMA ยาว (วัน)", 50, 200, 50)
            p['rsi_p'] = st.slider("RSI Period", 7, 21, 14)
            p['rsi_ob'] = st.slider("Overbought", 60, 80, 70)
            p['rsi_os'] = st.slider("Oversold", 20, 40, 30)
        
        with st.expander("MACD & Bollinger"):
            p['macd_f'] = st.number_input("MACD Fast", value=12)
            p['macd_s'] = st.number_input("MACD Slow", value=26)
            p['macd_sg'] = st.number_input("MACD Signal", value=9)
            p['bb_p'] = st.number_input("BB Period", value=20)
            p['bb_k'] = st.number_input("BB StdDev", value=2)

    tab1, tab2 = st.tabs(["Scanner", "Deep Analysis"])
    with tab1: view_scanner(p)
    with tab2: view_deep(p)

if __name__ == "__main__":
    main()
