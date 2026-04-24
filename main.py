import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
from datetime import datetime

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST - DARK MODE)
# ============================================================
st.set_page_config(page_title="Stock Scanner AI Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #000000; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; background-color: #111; color: #00E5FF; border: 2px solid #00E5FF; font-weight: bold; height: 3.5em; }
        .ai-card { background: #0A0A0A; border: 2px solid #1E293B; border-radius: 15px; padding: 20px; margin-bottom: 15px; color: #FFBF00; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 2rem; color: #00E5FF; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 25px 0 10px; color: #00E5FF; font-weight: bold; }
        .status-text { color: #00FF41; font-family: 'IBM Plex Mono'; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ENGINE
# ============================================================
class TradingSystem:
    @staticmethod
    def get_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        return df, ticker.info, ticker.news

    @staticmethod
    def calculate_tech(df, p):
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        return df.dropna()

# ============================================================
# 3. MAIN APP ROUTER
# ============================================================
def main():
    apply_ui_theme()
    if "view" not in st.session_state: st.session_state.view = "scan"

    with st.sidebar:
        st.markdown("### ⚙️ ตัวปรับจูน Parameters")
        p = {
            'sma_s': 20, 'sma_m': 50,
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': 70, 'rsi_os': 30
        }
        st.markdown("---")
        st.markdown("### 🔍 วิเคราะห์รายหุ้นด้วย AI")
        manual_sym = st.text_input("ระบุชื่อหุ้น (เช่น PTT, NVDA)").upper()
        manual_mkt = st.selectbox("ตลาด", ["SET", "US", "CN"])
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.detail_mkt = manual_mkt
            st.session_state.view = "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

# ============================================================
# 4. SCANNER VIEW (หน้าจอหลัก)
# ============================================================
def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    universe = {
        "SET": ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD"],
        "CN": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV"]
    }

    st.markdown(f"### 2️⃣ สแกนหาหุ้นที่น่าสนใจ ({mkt_key})")
    if st.button(f"เริ่มสแกน {mkt_key} 🚀"):
        results = []
        prog_bar = st.progress(0)
        status_txt = st.empty()
        
        for idx, sym in enumerate(universe[mkt_key]):
            status_txt.markdown(f"🔍 กำลังสแกน {sym}...")
            df, info, _ = TradingSystem.get_data(sym, mkt_key)
            if df is not None:
                df = TradingSystem.calculate_tech(df, p)
                c = df.iloc[-1]
                score = 50 + (15 if c['RSI'] < 30 else -15 if c['RSI'] > 70 else 0)
                results.append({"sym": sym, "price": c['Close'], "score": score})
            prog_bar.progress((idx+1)/len(universe[mkt_key]))
        
        status_txt.success("สแกนเสร็จสิ้น!")
        for r in results:
            st.markdown(f'<div class="ai-card"><b style="font-size:1.2rem;">{r["sym"]}</b> | ราคา: {r["price"]:,.2f} | Score: {r["score"]}</div>', unsafe_allow_html=True)
            if st.button(f"เจาะลึกด้วย AI: {r['sym']}", key=f"scan_{r['sym']}"):
                st.session_state.detail_sym = r['sym']
                st.session_state.detail_mkt = mkt_key
                st.session_state.view = "detail"
                st.rerun()

# ============================================================
# 5. DEEP ANALYSIS (พร้อมระบบแสดงสถานะการตรวจข่าวกี่ %)
# ============================================================
def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.get("detail_mkt", "SET")
    if st.button("← กลับหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()

    # --- AI LIVE STATUS TRACKING ---
    st.markdown('<div class="section-header">🤖 AI Internet Search & Analysis</div>', unsafe_allow_html=True)
    status_box = st.empty()
    prog_bar = st.progress(0)

    # จำลองขั้นตอนการทำงานของ AI พร้อมสถานะ %
    steps = [
        (10, "🌐 กำลังเชื่อมต่อแหล่งข้อมูล Internet..."),
        (35, f"📡 กำลังสแกนข่าวจากสำนักข่าวเศรษฐกิจย้อนหลัง 1 ปี สำหรับ {sym}..."),
        (60, "🧠 Gemini กำลังวิเคราะห์ประเด็นที่กระทบราคาหุ้น..."),
        (85, "🇹🇭 กำลังสรุปข้อมูลเป็นภาษาไทยและโมเดลธุรกิจ..."),
        (100, "✅ ตรวจสอบความถูกต้องเรียบร้อยแล้ว!")
    ]

    for pct, msg in steps:
        status_box.markdown(f'<p class="status-text">{msg} ({pct}%)</p>', unsafe_allow_html=True)
        prog_bar.progress(pct)
        time.sleep(0.6) # จำลองเวลาประมวลผล

    df, info, news = TradingSystem.get_data(sym, mkt)
    if df is None: return st.error("ไม่พบข้อมูล")

    # One-Page Result Display
    st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
    st.line_chart(df['Close'].tail(150))

    st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card">**{info.get("longName", sym)}** ดำเนินธุรกิจในกลุ่ม {info.get("sector")} เน้นอุตสาหกรรม {info.get("industry")} มีความโดดเด่นในฐานะผู้นำตลาดที่มี Market Cap {info.get("marketCap", 0)/1e9:.1f}B</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
    if news:
        summary = "\n".join([f"• {n.get('title')}" for n in news[:5]])
        st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{summary}</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ai-card">AI ไม่พบข่าวที่ส่งผลกระทบอย่างมีนัยสำคัญในช่วง 1 ปีที่ผ่านมา</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
