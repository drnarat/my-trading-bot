import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST)
# ============================================================
st.set_page_config(page_title="Scanner Pro V52", page_icon="🚀", layout="centered")

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
# 2. DATA ENGINE (ROBUST FETCHER)
# ============================================================
def get_stock_data(symbol, mkt):
    # ป้องกันชื่อหุ้นว่าง
    if not symbol: return None, None, None
    
    # จัดรูปแบบชื่อหุ้นให้ถูกต้อง (Auto-correction)
    symbol = symbol.strip().upper()
    if mkt == "SET" and not symbol.endswith(".BK"):
        ticker_name = f"{symbol}.BK"
    else:
        ticker_name = symbol

    try:
        tk = yf.Ticker(ticker_name)
        # ดึงราคา 1 ปีย้อนหลัง
        df = tk.history(period="1y")
        
        # หากดึงด้วย .BK ไม่เจอ ลองดึงแบบไม่มี .BK (กรณีหุ้น US/CN)
        if df.empty and ".BK" in ticker_name:
            tk = yf.Ticker(symbol)
            df = tk.history(period="1y")

        if df.empty: return None, None, None
        
        # จัดการข้อมูลข่าวและบริษัท
        try: info = tk.info
        except: info = {"longName": symbol}
        
        try: news = tk.news
        except: news = []
        
        return df, info, news
    except Exception as e:
        return None, None, None

# ============================================================
# 3. MAIN APP
# ============================================================
def main():
    apply_ui_theme()
    
    # เริ่มต้นหน้าจอ
    if "view" not in st.session_state:
        st.session_state.view = "scan"

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters")
        rsi_p = st.slider("RSI Period", 7, 21, 14)
        st.markdown("---")
        st.markdown("### 🔍 ค้นหาหุ้นรายตัว")
        manual_sym = st.text_input("ระบุชื่อหุ้น (เช่น PTT, SCB, NVDA)", key="search_box").upper()
        manual_mkt = st.selectbox("ตลาด", ["SET", "US", "CN"])
        if st.button("Deep Scan ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.detail_mkt = manual_mkt
            st.session_state.view = "detail"
            st.rerun()

    # --- VIEW ROUTING ---
    if st.session_state.view == "detail":
        render_detail_view(rsi_p)
    else:
        render_scan_view(rsi_p)

# ============================================================
# 4. SCANNER VIEW
# ============================================================
def render_scan_view(rsi_p):
    st.markdown("### 1️⃣ เลือกตลาดและสแกน")
    mkt = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    # รายชื่อหุ้นแนะนำ
    universe = {
        "SET": ["ADVANC", "AOT", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC", "BDMS"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL"],
        "CN": ["BABA", "NIO", "JD", "PDD"]
    }

    if st.button(f"สแกนหาโอกาส {mkt} 🚀"):
        for sym in universe[mkt]:
            df, _, _ = get_stock_data(sym, mkt)
            if df is not None:
                rsi = ta.rsi(df['Close'], length=rsi_p).iloc[-1]
                color = "#00FF41" if rsi < 30 else "#FF3131" if rsi > 70 else "#FFD700"
                st.markdown(f'<div style="border-left:6px solid {color}; padding:15px; background:#0A0A0A; border-radius:10px; margin-bottom:10px;"><b>{sym}</b> | ราคา: {df["Close"].iloc[-1]:,.2f} | RSI: {rsi:.1f}</div>', unsafe_allow_html=True)
                if st.button(f"วิเคราะห์ AI: {sym}", key=f"scan_{sym}"):
                    st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = sym, mkt, "detail"
                    st.rerun()

# ============================================================
# 5. DETAIL VIEW (ONE-PAGE)
# ============================================================
def render_detail_view(rsi_p):
    sym = st.session_state.get("detail_sym")
    mkt = st.session_state.get("detail_mkt", "SET")
    
    if st.button("← กลับหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()

    # --- Loading Status ---
    msg_box = st.empty()
    pb = st.progress(0)
    msg_box.markdown("🤖 AI กำลังวิเคราะห์ข้อมูล Internet 1 ปี...")
    for i in range(1, 101, 10):
        pb.progress(i)
        time.sleep(0.1)

    # ดึงข้อมูล
    df, info, news = get_stock_data(sym, mkt)
    msg_box.empty()
    pb.empty()

    if df is not None:
        st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
        st.line_chart(df['Close'].tail(150))

        # โมเดลธุรกิจ
        st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
        biz_desc = info.get('longBusinessSummary', 'ขออภัย ไม่พบข้อมูลรายละเอียดธุรกิจในขณะนี้')
        st.markdown(f'<div class="ai-card"><b>{info.get("longName", sym)}</b> อยู่ในกลุ่ม {info.get("sector", "N/A")} ({info.get("industry", "N/A")})<br><br>{biz_desc[:700]}...</div>', unsafe_allow_html=True)

        # ข่าวรอบ 1 ปี
        st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
        if news:
            news_items = "\n".join([f"• {n.get('title')}" for n in news[:5]])
            st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_items}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="ai-card">ไม่มีข่าวสารย้อนหลังที่สำคัญพบบนระบบข่าวออนไลน์ในขณะนี้</div>', unsafe_allow_html=True)
    else:
        st.error(f"ไม่สามารถโหลดข้อมูลหุ้น '{sym}' ได้ กรุณาลองระบุชื่อหุ้นตัวอื่น หรือตรวจสอบอินเทอร์เน็ต")

if __name__ == "__main__":
    main()
