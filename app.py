import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. CONFIG & UI STYLE ---
st.set_page_config(page_title="AI Stock Scanner Pro", layout="centered")

st.markdown("""
<style>
    /* ปรับฟอนต์ให้ชัดเจนและอ่านง่ายบนมือถือ */
    .stApp { background-color: #0e1117; color: #fafafa; }
    .stock-card {
        background: #1d2129;
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #6c63ff;
    }
    .status-buy { color: #00e676; font-weight: bold; }
    .status-sell { color: #ff5252; font-weight: bold; }
    .status-watch { color: #ffd740; font-weight: bold; }
    /* ปรับสีฟอนต์ใน Metric */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 1.5rem !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. CALCULATION ENGINE ---
def compute_indicators(df, p):
    close = df['Close'].squeeze()
    high = df['High'].squeeze()
    low = df['Low'].squeeze()
    
    I = {}
    I['price'] = float(close.iloc[-1])
    I['rsi'] = float(100 - (100 / (1 + (close.diff().where(close.diff() > 0, 0).rolling(p['rsi_p']).mean() / 
               (-close.diff().where(close.diff() < 0, 0).rolling(p['rsi_p']).mean() + 1e-9)))).iloc[-1])
    I['sma_s'] = float(close.rolling(p['sma_s']).mean().iloc[-1])
    I['sma_l'] = float(close.rolling(p['sma_l']).mean().iloc[-1])
    
    # MACD
    ema12 = close.ewm(span=p['macd_f'], adjust=False).mean()
    ema26 = close.ewm(span=p['macd_s'], adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=p['macd_sg'], adjust=False).mean()
    I['macd'] = float(macd.iloc[-1])
    I['macd_sig'] = float(signal.iloc[-1])
    
    # Bollinger Bands
    ma = close.rolling(p['bb_p']).mean()
    std = close.rolling(p['bb_p']).std()
    I['bbu'] = float((ma + p['bb_k']*std).iloc[-1])
    I['bbl'] = float((ma - p['bb_k']*std).iloc[-1])
    
    return I

@st.cache_data(ttl=300)
def get_data(symbol, p):
    try:
        ticker = f"{symbol}.BK" if len(symbol) <= 5 and ".BK" not in symbol.upper() else symbol
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        indicators = compute_indicators(df, p)
        
        # Scoring
        score = 50
        if indicators['rsi'] < p['rsi_os']: score += 15
        elif indicators['rsi'] > p['rsi_ob']: score -= 15
        if indicators['price'] > indicators['sma_s']: score += 10
        if indicators['macd'] > indicators['macd_sig']: score += 15
        
        return {"I": indicators, "score": score, "df": df, "ticker": ticker}
    except: return None

# --- 3. UI VIEWS ---
def view_scanner(p):
    st.subheader("🚀 Scanner")
    mkt = st.radio("เลือกตลาด", ["SET (Thai)", "US Tech", "China ADR"], horizontal=True)
    tickers = {
        "SET (Thai)": ["CPALL", "PTT", "ADVANC", "KBANK", "AOT"],
        "US Tech": ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"],
        "China ADR": ["BABA", "NIO", "JD", "BIDU", "PDD"]
    }
    
    if st.button("เริ่มสแกน"):
        for sym in tickers[mkt]:
            res = get_data(sym, p)
            if res:
                color = "status-buy" if res['score'] >= 65 else "status-sell" if res['score'] <= 35 else "status-watch"
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex;justify-content:space-between;">
                        <b>{sym}</b> <span>{res['I']['price']:,.2f}</span>
                    </div>
                    <div style="font-size:0.8rem;color:#8892b0;margin-top:5px;">
                        RSI: {res['I']['rsi']:.1f} | Score: {res['score']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def view_deep(p):
    st.subheader("🔍 AI Deep Analysis")
    target = st.text_input("ใส่ชื่อหุ้น (เช่น CPALL, TSLA)").upper()
    
    if st.button("วิเคราะห์หุ้นตัวนี้"):
        res = get_data(target, p)
        if res:
            I = res['I']
            st.write(f"### สรุปค่าทางเทคนิคของ {target}")
            c1, c2, c3 = st.columns(3)
            c1.metric("ราคาปัจจุบัน", f"{I['price']:,.2f}")
            c2.metric("RSI (14)", f"{I['rsi']:.1f}")
            c3.metric("MACD Status", "Bullish" if I['macd'] > I['macd_sig'] else "Bearish")
            
            # ตารางพารามิเตอร์
            st.markdown(f"""
            **วิเคราะห์จากพารามิเตอร์ที่คุณตั้งค่า:**
            * **RSI ({p['rsi_p']}):** อยู่ที่ {I['rsi']:.2f} ({'Oversold' if I['rsi'] < p['rsi_os'] else 'Overbought' if I['rsi'] > p['rsi_ob'] else 'Neutral'})
            * **SMA ({p['sma_s']}/{p['sma_l']}):** ราคา{'อยู่เหนือ' if I['price'] > I['sma_s'] else 'อยู่ใต้'} เส้นค่าเฉลี่ยระยะสั้น
            * **Bollinger Bands:** ราคา{'ใกล้ขอบบน (ระวัง)' if I['price'] > I['bbu']*0.95 else 'ใกล้ขอบล่าง (น่าสนใจ)' if I['price'] < I['bbl']*1.05 else 'อยู่ในกรอบปกติ'}
            """)
            
            st.line_chart(res['df']['Close'])
            
            # --- ตรงนี้คือจุดที่ Gemini จะช่วยวิเคราะห์ข่าว (ตัวอย่างข้อความ) ---
            st.info("🤖 **AI Insights (Google Search):** ระบบกำลังดึงประเด็นสำคัญในรอบ 1 ปี... \n\n"
                    "1. หุ้นตัวนี้ได้รับผลกระทบจาก [ประเด็นเศรษฐกิจ] \n"
                    "2. ทิศทางงบการเงินล่าสุดมีการเติบโตที่ [ระบุทิศทาง] \n"
                    "3. ปัจจัยภายนอกที่ต้องระวังคือ [ข่าวเด่นในรอบปี]")
        else:
            st.error("ไม่พบข้อมูลหุ้น กรุณาลองตรวจสอบชื่อ Ticker อีกครั้ง")

# --- 4. MAIN ---
def main():
    with st.sidebar:
        st.header("⚙️ Parameters")
        p = {
            "sma_s": st.slider("SMA Short", 5, 50, 20),
            "sma_l": st.slider("SMA Long", 50, 200, 50),
            "rsi_p": st.slider("RSI Period", 7, 21, 14),
            "rsi_ob": st.slider("RSI Overbought", 60, 80, 70),
            "rsi_os": st.slider("RSI Oversold", 20, 40, 30),
            "macd_f": 12, "macd_s": 26, "macd_sg": 9,
            "bb_p": 20, "bb_k": 2
        }

    t1, t2 = st.tabs(["Scanner", "Deep Analysis"])
    with t1: view_scanner(p)
    with t2: view_deep(p)

if __name__ == "__main__":
    main()
