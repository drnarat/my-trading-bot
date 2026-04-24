import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST - DARK MODE)
# ============================================================
st.set_page_config(page_title="Scanner Pro AI V50", page_icon="🚀", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #000000; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: #111; color: #00E5FF; border: 2px solid #00E5FF; font-weight: bold; }
        .stock-card { background: #0A0A0A; border: 1px solid #1E293B; border-radius: 15px; padding: 15px; margin-bottom: 12px; border-left: 8px solid #1E293B; }
        .buy-border { border-left-color: #00FF41; }
        .sell-border { border-left-color: #FF3131; }
        .watch-border { border-left-color: #FFD700; }
        .ai-card { background: #050505; border: 1px solid #00E5FF; border-radius: 12px; padding: 20px; color: #FFBF00; line-height: 1.8; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 2.5rem; color: #00E5FF; font-weight: bold; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 25px 0 10px; color: #00E5FF; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS ENGINE
# ============================================================
class Analyst:
    @staticmethod
    def fetch_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        tk = yf.Ticker(ticker_name)
        df = tk.history(period="1y")
        if df.empty: return None, None, None
        return df, tk.info, tk.news

# ============================================================
# 3. MAIN APP
# ============================================================
def main():
    apply_ui_theme()
    
    # Session States
    if "view" not in st.session_state: st.session_state.view = "scan"

    # --- SIDEBAR: ALL PARAMETERS ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters ทั้งหมด")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14)
        }
        st.markdown("---")
        manual_sym = st.text_input("🔍 วิเคราะห์รายหุ้น (AI)").upper()
        if st.button("Deep Scan ✨") and manual_sym:
            st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = manual_sym, "SET", "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดและสแกน")
    mkt = st.radio("Market", ["SET", "US", "CN"], horizontal=True)
    universe = {"SET": ["ADVANC", "AOT", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC", "BDMS"], "US": ["AAPL", "NVDA", "TSLA"], "CN": ["BABA", "NIO"]}

    if st.button(f"สแกนหาโอกาส {mkt} 🚀"):
        for sym in universe[mkt]:
            df, _, _ = Analyst.fetch_data(sym, mkt)
            if df is not None:
                rsi = ta.rsi(df['Close'], length=p['rsi_p']).iloc[-1]
                cls = "buy" if rsi < p['rsi_os'] else "sell" if rsi > p['rsi_ob'] else "watch"
                st.markdown(f'<div class="stock-card {cls}-border"><b>{sym}</b> | RSI: {rsi:.1f}</div>', unsafe_allow_html=True)
                if st.button(f"เจาะลึก: {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = sym, mkt, "detail"
                    st.rerun()

def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.get("detail_mkt", "SET")
    
    if st.button("← กลับหน้าหลัก"):
        st.session_state.view = "scan"; st.rerun()

    # --- AI STEP LOADING (DISPLAY BEFORE RESULTS) ---
    st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
    
    status_container = st.empty()
    prog_bar = st.progress(0)
    
    with status_container.container():
        for pct, msg in [(30, "🌐 ค้นหาข้อมูล Internet..."), (70, "🧠 วิเคราะห์ข้อมูลธุรกิจและข่าว 1 ปี..."), (100, "✅ เสร็จสิ้น!")]:
            st.markdown(f'<p style="color:#00FF41;">{msg} ({pct}%)</p>', unsafe_allow_html=True)
            prog_bar.progress(pct)
            time.sleep(0.5)
    
    # Fetch data after animation to ensure results are ready
    df, info, news = Analyst.fetch_data(sym, mkt)
    status_container.empty() # ลบสถานะออกเพื่อแสดงข้อมูลจริง
    prog_bar.empty()

    if df is not None:
        st.line_chart(df['Close'].tail(180))

        # โมเดลธุรกิจ
        st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
        biz_desc = info.get('longBusinessSummary', 'AI กำลังรวบรวมข้อมูลอุตสาหกรรมล่าสุด...')
        st.markdown(f'<div class="ai-card"><b>{info.get("longName", sym)}</b> อยู่ในกลุ่ม {info.get("sector")} ({info.get("industry")})<br><br>{biz_desc[:500]}...</div>', unsafe_allow_html=True)

        # ข่าวรอบ 1 ปี
        st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
        if news:
            news_txt = "\n".join([f"• {n.get('title')}" for n in news[:5]])
            st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_txt}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ai-card">ไม่มีข่าวสารสำคัญย้อนหลัง 1 ปี</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
