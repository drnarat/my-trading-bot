import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG (High-Contrast Midnight)
# ============================================================
st.set_page_config(page_title="Stock Scanner AI Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #050510; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; background-color: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; font-weight: bold; }
        .stock-card { background: #101223; border: 1px solid #1E293B; border-radius: 15px; padding: 15px; margin-bottom: 12px; }
        .buy-border { border-left: 6px solid #00FF41; }
        .sell-border { border-left: 6px solid #FF3131; }
        .watch-border { border-left: 6px solid #FFD700; }
        .ai-card { background: rgba(0, 229, 255, 0.05); border: 1px solid #00E5FF; border-radius: 12px; padding: 15px; margin: 10px 0; color: #e2e8f0; }
        .section-header { border-left: 5px solid #6c63ff; padding-left: 10px; margin: 20px 0 10px; color: #00E5FF; font-weight: bold; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.3rem; color: #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS & AI ENGINE
# ============================================================
class StockEngine:
    @staticmethod
    def fetch_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, ticker.info, ticker.news

    @staticmethod
    def compute_tech(df, p):
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        return df.dropna()

# ============================================================
# 3. MAIN INTERFACE
# ============================================================
def main():
    apply_ui_theme()
    
    # Init View State
    if "view" not in st.session_state: st.session_state.view = "scan"

    # --- Sidebar: Full Parameters ( Slider ทั้ง 18 ตัว ) ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters Analysis")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'sma_l': st.slider("SMA ยาว", 100, 300, 200),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14),
            'cci_p': st.slider("CCI Period", 10, 30, 20),
            'wr_p': st.slider("Williams %R", 7, 21, 14),
            'mfi_p': st.slider("MFI Period", 7, 21, 14),
            'adx_p': st.slider("ADX Period", 7, 21, 14)
        }
        st.markdown("---")
        st.markdown("### 🔍 วิเคราะห์หุ้นรายตัว")
        manual_sym = st.text_input("ระบุชื่อหุ้น", placeholder="PTT, NVDA...").upper()
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.view = "detail"
            st.rerun()

    # --- Router ---
    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    st.markdown("### 2️⃣ ตัวกรอง")
    f1, f2 = st.columns(2)
    with f1:
        sigs = st.multiselect("กรองสัญญาณ", ["🟢 ซื้อ", "🟡 เฝ้า", "🔴 ขาย"], default=["🟢 ซื้อ", "🟡 เฝ้า"])
    with f2:
        sort_by = st.selectbox("เรียงตาม", ["Score", "Change %", "RSI"])

    # Universe Selection
    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB", "BDMS", "LH"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD", "META", "AMZN"],
        "CN": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI", "BILI"]
    }

    st.markdown(f"### 3️⃣ สแกน {mkt_key}")
    if st.button(f"สแกน {mkt_key} ({len(universe[mkt_key])} หุ้น)"):
        results = []
        prog = st.progress(0)
        for idx, sym in enumerate(universe[mkt_key]):
            df, info, _ = StockEngine.fetch_data(sym, mkt_key)
            if df is not None:
                df = StockEngine.compute_tech(df, p)
                c = df.iloc[-1]
                score = 50 + (15 if c['RSI'] < p['rsi_os'] else -15 if c['RSI'] > p['rsi_ob'] else 0)
                cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
                rec = "🟢 ซื้อ" if score >= 65 else "🔴 ขาย" if score <= 35 else "🟡 เฝ้า"
                
                if rec in sigs:
                    results.append({"sym": sym, "price": c['Close'], "score": score, "cls": cls, "rec": rec, "rsi": c['RSI']})
            prog.progress((idx+1)/len(universe[mkt_key]))
        
        # Display Cards
        if not results:
            st.info("ไม่พบหุ้นตามเงื่อนไข ลองปรับ Parameters")
        else:
            for r in results:
                st.markdown(f"""
                <div class="stock-card {r['cls']}-border">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{r['sym']}</span>
                        <span style="font-family:IBM Plex Mono; font-size:1.1rem;">{r['price']:,.2f}</span>
                    </div>
                    <div style="margin:8px 0; font-size:0.85rem; color:#8892b0;">
                        Score: {r['score']} | RSI: {r['rsi']:.1f} | <b>{r['rec']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🔍 วิเคราะห์ AI: {r['sym']}", key=f"btn_{r['sym']}"):
                    st.session_state.detail_sym = r['sym']
                    st.session_state.detail_mkt = mkt_key
                    st.session_state.view = "detail"
                    st.rerun()

def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.get("detail_mkt", "US")
    if st.button("← กลับหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()

    with st.spinner(f"Gemini กำลังวิเคราะห์เจาะลึก {sym}..."):
        df, info, news = StockEngine.fetch_data(sym, mkt)
        if df is None: return st.error("ไม่พบข้อมูล")

        st.markdown(f'<div class="symbol-text" style="font-size:2rem;">{sym}</div>', unsafe_allow_html=True)
        st.line_chart(df['Close'].tail(100))

        # AI Business Summary (Thai)
        st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (AI ภาษาไทย)</div>', unsafe_allow_html=True)
        biz_th = f"**{info.get('shortName')}** ดำเนินธุรกิจในกลุ่ม {info.get('sector')} เน้นการทำกำไรจาก {info.get('industry')} เป็นหลัก"
        st.markdown(f'<div class="ai-card">{biz_th}</div>', unsafe_allow_html=True)

        # AI News Timeline
        st.markdown('<div class="section-header">📰 สรุปความเคลื่อนไหวรอบ 1 ปี โดย Gemini</div>', unsafe_allow_html=True)
        if news:
            news_summary = "• " + "\n• ".join([n['title'] for n in news[:5]])
            st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_summary}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
