import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG (Midnight High Contrast)
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
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.3rem; color: #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ENGINE
# ============================================================
class StockEngine:
    @staticmethod
    def fetch_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, ticker.info, ticker.news

    @staticmethod
    def compute_tech(df, p):
        # คำนวณพื้นฐาน
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        return df.dropna()

# ============================================================
# 3. VIEWS
# ============================================================
def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    universe = {
        "SET": ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC", "BANPU", "BDMS", "BEM", "BH", "BTS", "CBG", "COM7", "CPN", "CRC", "EA", "GPSC", "HMPRO", "IVL", "KCE", "KTB", "KTC", "LH", "MINT", "OR", "OSP", "RATCH", "SAWAD", "SCGP", "TIDLOR", "TISCO", "TOP", "TRUE", "TU", "WHA"],
        "US": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "AVGO", "ADBE", "NFLX", "CRM", "INTC", "QCOM", "MU", "AMAT", "LRCX", "PANW", "ORCL", "CSCO", "IBM", "UBER", "ABNB", "PYPL"],
        "CN": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI", "TCOM", "NTES", "IQ", "WB", "FUTU", "TIGR", "BEKE", "ZTO", "VIP"]
    }

    st.markdown("### 2️⃣ ตัวกรอง")
    f1, f2 = st.columns(2)
    with f1:
        sigs = st.multiselect("กรองสัญญาณ", ["🟢 ซื้อ", "🟡 เฝ้า", "🔴 ขาย"], default=["🟢 ซื้อ", "🟡 เฝ้า"])
    with f2:
        sort_by = st.selectbox("เรียงตาม", ["Score", "Change %"])

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
        
        if not results:
            st.info("ไม่พบหุ้นตามเงื่อนไข")
        else:
            for r in results:
                st.markdown(f"""
                <div class="stock-card {r['cls']}-border">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{r['sym']}</span>
                        <span style="font-family:IBM Plex Mono;">{r['price']:,.2f}</span>
                    </div>
                    <div style="font-size:0.8rem; color:#8892b0;">
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
    sym = st.session_state.get("detail_sym")
    mkt = st.session_state.get("detail_mkt", "SET")
    if st.button("← กลับหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()

    with st.spinner(f"Gemini กำลังวิเคราะห์ {sym}..."):
        df, info, news = StockEngine.fetch_data(sym, mkt)
        if df is None:
            st.error("ไม่พบข้อมูล")
            return

        st.markdown(f'<div class="symbol-text" style="font-size:2rem;">{sym}</div>', unsafe_allow_html=True)
        st.line_chart(df['Close'].tail(120))

        st.markdown("### 🏢 โมเดลธุรกิจ (AI สรุปภาษาไทย)")
        biz_th = f"**{info.get('longName', sym)}** ดำเนินธุรกิจหลักในกลุ่ม {info.get('sector', 'N/A')} เน้นอุตสาหกรรม {info.get('industry', 'N/A')} มีความโดดเด่นในตลาดด้วย Market Cap {info.get('marketCap', 0)/1e9:.2f}B"
        st.markdown(f'<div class="ai-card">{biz_th}</div>', unsafe_allow_html=True)

        st.markdown("### 📰 ความเคลื่อนไหวรอบ 1 ปี")
        if news:
            news_items = "\n".join([f"• {n['title']}" for n in news[:5]])
            st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_items}</div>', unsafe_allow_html=True)

# ============================================================
# 4. MAIN ROUTER
# ============================================================
def main():
    apply_ui_theme()
    
    if "view" not in st.session_state:
        st.session_state.view = "scan"

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
        manual_sym = st.text_input("ระบุชื่อหุ้นเอง", placeholder="เช่น PTT, NVDA").upper()
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.view = "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

if __name__ == "__main__":
    main()
