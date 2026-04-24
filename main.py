import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG & HIGH CONTRAST THEME
# ============================================================
st.set_page_config(page_title="Stock Scanner Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Sarabun', sans-serif;
            background-color: #050510;
            color: #FFBF00; /* Amber Text */
        }

        h1, h2, h3, b, strong { color: #00E5FF !important; } /* Cyan Titles */

        /* Card Layout */
        .stock-card {
            background: #101223;
            border: 1px solid #1E293B;
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 12px;
        }
        .buy-border { border-left: 6px solid #00FF41; }
        .sell-border { border-left: 6px solid #FF3131; }
        .watch-border { border-left: 6px solid #FFD700; }

        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.2rem; color: #00E5FF; }
        .price-text { font-family: 'IBM Plex Mono'; font-size: 1.1rem; color: #FFBF00; }

        /* Button Customization */
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            background-color: #1E293B;
            color: #00E5FF;
            border: 1px solid #00E5FF;
            height: 3em;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ANALYSIS ENGINE
# ============================================================
class TradingEngine:
    @staticmethod
    def fetch_data(symbol, mkt_key):
        ticker = f"{symbol}.BK" if mkt_key == "SET" else symbol
        df = yf.download(ticker, period="200d", interval="1d", progress=False)
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df

    @staticmethod
    def compute_all_indicators(df, p):
        # Trend
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['SMA_L'] = ta.sma(df['Close'], length=p['sma_l'])
        # Oscillators
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        macd = ta.macd(df['Close'], fast=p['macd_f'], slow=p['macd_s'], signal=p['macd_sg'])
        df = pd.concat([df, macd], axis=1)
        # Volatility & Momentum
        bb = ta.bbands(df['Close'], length=p['bb_p'], std=p['bb_k'])
        df['BBP'] = (df['Close'] - bb.iloc[:, 0]) / (bb.iloc[:, 2] - bb.iloc[:, 0] + 1e-9)
        stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=p['stk'], d=p['std'])
        df = pd.concat([df, stoch], axis=1)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=p['cci_p'])
        df['WR'] = ta.willr(df['High'], df['Low'], df['Close'], length=p['wr_p'])
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=p['mfi_p'])
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=p['adx_p'])
        df = pd.concat([df, adx], axis=1)
        return df.dropna()

    @staticmethod
    def calculate_score(df, p):
        c = df.iloc[-1]
        score = 50
        # Simple Scoring Logic (สามารถขยายเพิ่มตามความต้องการได้)
        if c['RSI'] < p['rsi_os']: score += 15
        elif c['RSI'] > p['rsi_ob']: score -= 15
        if c['Close'] > c['SMA_S'] > c['SMA_M']: score += 20
        
        rec = "🟢 ซื้อ" if score >= 65 else "🔴 ขาย" if score <= 35 else "🟡 เฝ้าระวัง"
        cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
        
        # Risk/Reward Calculation
        atr = c['ATR']
        t1 = c['Close'] + (atr * 2)
        sl = c['Close'] - (atr * 1.5)
        rr = round((t1 - c['Close']) / (c['Close'] - sl + 1e-9), 2)
        
        return {"score": score, "rec": rec, "cls": cls, "rr": rr, "t1": t1, "sl": sl}

# ============================================================
# 3. MAIN INTERFACE
# ============================================================
def main():
    apply_ui_theme()
    engine = TradingEngine()

    # --- Section: Parameters ---
    with st.expander("⚙️ ตั้งค่า Parameters", expanded=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            sma_s = st.slider("SMA สั้น", 5, 50, 20)
            sma_m = st.slider("SMA กลาง", 20, 100, 50)
            sma_l = st.slider("SMA ยาว", 100, 300, 200)
            rsi_p = st.slider("RSI Period", 7, 21, 14)
            rsi_ob = st.slider("RSI Overbought", 60, 85, 70)
            rsi_os = st.slider("RSI Oversold", 15, 40, 30)
        with c2:
            macd_f = st.slider("MACD Fast", 8, 20, 12)
            macd_s = st.slider("MACD Slow", 20, 40, 26)
            macd_sg = st.slider("MACD Signal", 5, 15, 9)
            bb_p = st.slider("BB Period", 10, 30, 20)
            bb_k = st.slider("BB Std Dev", 1, 3, 2)
            stk = st.slider("Stoch %K", 5, 21, 14)
        with c3:
            std = st.slider("Stoch %D", 2, 7, 3)
            atr_p = st.slider("ATR Period", 7, 21, 14)
            cci_p = st.slider("CCI Period", 10, 30, 20)
            wr_p = st.slider("Williams %R", 7, 21, 14)
            mfi_p = st.slider("MFI Period", 7, 21, 14)
            adx_p = st.slider("ADX Period", 7, 21, 14)
        
        min_score = st.slider("คะแนนขั้นต่ำ", 0, 100, 60)
        min_rr = st.slider("R/R ขั้นต่ำ", 0.5, 5.0, 1.5, step=0.5)

    params = locals() # เก็บค่า slider ทั้งหมดลง dict

    # --- Section 1: ตลาดหุ้น ---
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_cols = st.columns(3)
    markets = {"SET": "🇹🇭 TH SET", "US": "🇺🇸 US Tech", "CN": "🇨🇳 CN Tech"}
    selected_mkt = st.session_state.get("mkt", "SET")
    
    for i, (k, v) in enumerate(markets.items()):
        if mkt_cols[i].button(v, type="primary" if selected_mkt == k else "secondary"):
            st.session_state.mkt = k
            st.rerun()

    # --- Section: Filters ---
    f1, f2 = st.columns(2)
    with f1:
        sigs = st.multiselect("กรองสัญญาณ", ["🟢 ซื้อ", "🟡 เฝ้าระวัง", "🔴 ขาย"], default=["🟢 ซื้อ", "🟡 เฝ้าระวัง"])
    with f2:
        sort_val = st.selectbox("เรียงลำดับ", ["Score", "RSI", "Change %"])

    # --- Section 2: สแกน ---
    st.markdown(f"### 2️⃣ สแกน {selected_mkt}")
    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"],
        "CN": ["BABA", "JD", "PDD", "NIO"]
    }

    if st.button(f"🚀 เริ่มสแกน {len(universe[selected_mkt])} หุ้น"):
        results = []
        for sym in universe[selected_mkt]:
            df = engine.fetch_data(sym, selected_mkt)
            if df is not None:
                df = engine.compute_all_indicators(df, params)
                analysis = engine.calculate_score(df, params)
                
                if analysis['score'] >= min_score and analysis['rr'] >= min_rr:
                    if analysis['rec'] in sigs:
                        c = df.iloc[-1]
                        results.append({
                            "Symbol": sym, "Price": c['Close'], "Score": analysis['score'],
                            "Rec": analysis['rec'], "Cls": analysis['cls'], "RR": analysis['rr'],
                            "T1": analysis['t1'], "SL": analysis['sl'], "RSI": c['RSI'],
                            "CHG": (c['Close']/df.iloc[-2]['Close']-1)*100
                        })
        
        # Display Results
        for res in results:
            st.markdown(f"""
            <div class="stock-card {res['Cls']}-border">
                <div style="display:flex; justify-content:space-between;">
                    <span class="symbol-text">{res['Symbol']}</span>
                    <span class="price-text">{res['Price']:,.2f} ({res['CHG']:+.2f}%)</span>
                </div>
                <div style="margin: 10px 0; font-size: 0.9rem;">
                    Score: <b>{res['Score']}</b> | RSI: {res['RSI']:.1f} | <b>RR: 1:{res['RR']}</b>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:#00E5FF;">🎯 TP: {res['T1']:.2f} | 🛡️ SL: {res['SL']:.2f}</span>
                    <b style="font-size:1rem;">{res['Rec']}</b>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # --- Section: วิเคราะห์รายหุ้น ---
    st.sidebar.markdown("### 🔍 วิเคราะห์รายหุ้น")
    single_sym = st.sidebar.text_input("ระบุชื่อหุ้น", placeholder="เช่น PTT, AAPL")
    if st.sidebar.button("วิเคราะห์ทันที") and single_sym:
        with st.spinner("กำลังประมวลผล..."):
            df = engine.fetch_data(single_sym.upper(), selected_mkt)
            if df is not None:
                df = engine.compute_all_indicators(df, params)
                analysis = engine.calculate_score(df, params)
                st.sidebar.success(f"{single_sym.upper()}: {analysis['rec']} (Score: {analysis['score']})")
                st.sidebar.write(f"RSI: {df.iloc[-1]['RSI']:.2f}")

if __name__ == "__main__":
    main()
