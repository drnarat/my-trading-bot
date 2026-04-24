import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST)
# ============================================================
st.set_page_config(page_title="Stock Scanner AI", page_icon="🚀", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #000000; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: #111; color: #00E5FF; border: 2px solid #00E5FF; font-weight: bold; }
        .ai-card { background: #0A0A0A; border: 1px solid #1E293B; border-radius: 15px; padding: 20px; color: #FFBF00; line-height: 1.8; margin-bottom: 20px; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 2.5rem; color: #00E5FF; font-weight: bold; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 25px 0 10px; color: #00E5FF; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. DATA ENGINE
# ============================================================
@st.cache_data(ttl=300) # Cache ข้อมูล 5 นาทีเพื่อความเร็ว
def get_stock_data(symbol, mkt):
    try:
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        tk = yf.Ticker(ticker_name)
        df = tk.history(period="1y")
        if df.empty: return None, None, None
        return df, tk.info, tk.news
    except:
        return None, None, None

# ============================================================
# 3. MAIN APP
# ============================================================
def main():
    apply_ui_theme()
    if "view" not in st.session_state: st.session_state.view = "scan"

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30)
        }
        st.markdown("---")
        manual_sym = st.text_input("🔍 พิมพ์ชื่อหุ้นเอง").upper()
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
            df, _, _ = get_stock_data(sym, mkt)
            if df is not None:
                rsi = ta.rsi(df['Close'], length=p['rsi_p']).iloc[-1]
                cls = "buy" if rsi < p['rsi_os'] else "sell" if rsi > p['rsi_ob'] else "watch"
                st.markdown(f'<div style="border-left:5px solid {"#00FF41" if cls=="buy" else "#FF3131" if cls=="sell" else "#FFD700"}; padding:10px; background:#0A0A0A; margin-bottom:5px;"><b>{sym}</b> | RSI: {rsi:.1f}</div>', unsafe_allow_html=True)
                if st.button(f"เจาะลึก: {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = sym, mkt, "detail"
                    st.rerun()

def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.get("detail_mkt", "SET")
    
    if st.button("← กลับหน้าหลัก"):
        st.session_state.view = "scan"; st.rerun()

    # --- LOADING LOGIC ---
    placeholder = st.empty()
    with placeholder.container():
        st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
        st.write("🤖 Gemini กำลังวิเคราะห์ข้อมูล Internet...")
        pb = st.progress(0)
        for i in range(1, 101, 25):
            pb.progress(i); time.sleep(0.3)
    
    # FETCH DATA
    df, info, news = get_stock_data(sym, mkt)
    
    # CLEAR LOADING & DISPLAY DATA
    placeholder.empty() # ล้างหน้าจอ Loading ทั้งหมดออก
    
    if df is not None:
        st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
        st.line_chart(df['Close'].tail(150))

        # AI BUSINESS SUMMARY
        st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
        biz_desc = info.get('longBusinessSummary', 'ไม่มีข้อมูลสรุปธุรกิจ')
        st.markdown(f'<div class="ai-card"><b>{info.get("longName", sym)}</b> อยู่ในกลุ่ม {info.get("sector")} ({info.get("industry")})<br><br>{biz_desc[:600]}...</div>', unsafe_allow_html=True)

        # AI NEWS SUMMARY
        st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
        if news:
            news_items = "\n".join([f"• {n.get('title')}" for n in news[:5]])
            st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_items}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ai-card">ไม่พบข่าวสารย้อนหลังที่สำคัญ</div>', unsafe_allow_html=True)
    else:
        st.error("ไม่สามารถโหลดข้อมูลหุ้นตัวนี้ได้")

if __name__ == "__main__":
    main()
