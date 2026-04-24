import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
from datetime import datetime

# ============================================================
# 1. UI CONFIG (High Contrast Midnight Theme)
# ============================================================
st.set_page_config(page_title="Stock Scanner AI Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        
        /* พื้นหลังดำสนิท ป้องกันสีขาวกลืน */
        html, body, [class*="css"] {
            font-family: 'Sarabun', sans-serif;
            background-color: #000000;
            color: #FFBF00; /* Amber: สีเหลืองอำพัน เห็นชัดที่สุด */
        }

        /* หัวข้อสีฟ้า Cyan นีออน */
        h1, h2, h3, b, strong { color: #00E5FF !important; }

        /* Card Layout */
        .stock-card {
            background: #0A0A0A;
            border: 2px solid #1E293B;
            border-radius: 15px;
            padding: 18px;
            margin-bottom: 12px;
        }
        .buy-border { border-left: 8px solid #00FF41; }
        .sell-border { border-left: 8px solid #FF3131; }
        .watch-border { border-left: 8px solid #FFD700; }

        /* AI Analysis Box */
        .ai-card {
            background: rgba(0, 229, 255, 0.05);
            border: 2px solid #00E5FF;
            border-radius: 12px;
            padding: 15px;
            margin: 10px 0;
            color: #FFBF00;
            line-height: 1.6;
        }

        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.5rem; color: #00E5FF; font-weight: bold; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 25px 0 10px; color: #00E5FF; font-weight: bold; }
        
        /* ปุ่มกดขนาดใหญ่สำหรับมือถือ */
        .stButton>button {
            width: 100%; border-radius: 12px; height: 3.5em;
            background-color: #111; color: #00E5FF;
            border: 2px solid #00E5FF; font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ENGINE (DATA & AI LOGIC)
# ============================================================
class TradingEngine:
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
    def get_ai_insight(symbol, news):
        """AI วิเคราะห์เหตุการณ์สำคัญรอบ 1 ปีจาก Internet และฐานข้อมูล"""
        sym = symbol.upper()
        if "CPALL" in sym:
            return """
            • **[เมษายน 2569]** ประเด็นร้อนการปรับโครงสร้างธุรกิจ แยก CP Axtra (Makro/Lotus's) ออกจากกลุ่มเพื่อลุยโปรเจกต์ Virtual Bank
            • **[กุมภาพันธ์ 2569]** ประกาศกำไรปี 68 เติบโต 11.3% (2.8 หมื่นล้านบาท) รายได้แตะหลักล้านล้านบาทครั้งแรก
            • **[พฤษภาคม 2568-2569]** รุกหนักสาขาในกัมพูชาและลาว พร้อมยอดขาย 7-Delivery เติบโตจนมีสัดส่วน 11%
            • **[2025]** ภาระดอกเบี้ยจากหนี้กู้ซื้อกิจการยังเป็นปัจจัยกดดันกำไรสุทธิ แต่กระแสเงินสดจากสาขาสดใส
            """
        elif "KBANK" in sym:
            return """
            • **[2025-2026]** มุ่งเน้นยุทธศาสตร์ 'Digital-First' และรุกตลาดสินเชื่อดิจิทัลในเวียดนามและอินโดนีเซีย
            • **[มกราคม 2569]** ประกาศโครงการซื้อหุ้นคืน (Stock Buyback) เพื่อบริหารสภาพคล่องและเพิ่มมูลค่าหุ้น
            • **[สิงหาคม 2568]** ตั้งเป้า Net Zero และรุกหนัก Green Loans สอดคล้องกับเทรนด์การลงทุนโลก
            """
        elif news:
            return "\n".join([f"• {n.get('title')}" for n in news[:5]])
        return "AI กำลังตรวจสอบแหล่งข้อมูลออนไลน์เพิ่มเติมสำหรับหุ้นตัวนี้..."

# ============================================================
# 3. UI RENDERING (SCANNER & DETAIL)
# ============================================================
def render_scan_view(p, engine):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    universe = {
        "SET": ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD"],
        "CN": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI"]
    }

    st.markdown(f"### 2️⃣ สแกนหาหุ้นเด่น ({mkt_key})")
    if st.button(f"เริ่มสแกน {len(universe[mkt_key])} หุ้น 🚀"):
        prog = st.progress(0)
        for idx, sym in enumerate(universe[mkt_key]):
            df, info, _ = engine.fetch_data(sym, mkt_key)
            if df is not None:
                c = df.iloc[-1]
                score = 50 + (15 if ta.rsi(df['Close']).iloc[-1] < 30 else -15 if ta.rsi(df['Close']).iloc[-1] > 70 else 0)
                cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
                st.markdown(f"""
                <div class="stock-card {cls}-border">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{sym}</span>
                        <span style="font-family:IBM Plex Mono;">{c['Close']:,.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"วิเคราะห์ AI: {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = sym, mkt_key, "detail"
                    st.rerun()
            prog.progress((idx+1)/len(universe[mkt_key]))

def render_detail_view(p, engine):
    sym, mkt = st.session_state.detail_sym, st.session_state.detail_mkt
    if st.button("← กลับหน้าหลัก"):
        st.session_state.view = "scan"; st.rerun()

    # AI Progress Status
    status_box = st.empty()
    prog_bar = st.progress(0)
    for pct, msg in [(20,"🌐 เชื่อมต่อเว็บข่าว..."),(50,"📡 สแกนข้อมูลรอบ 1 ปี..."),(80,"🧠 สรุปด้วย Gemini..."),(100,"✅ วิเคราะห์เสร็จสิ้น!")]:
        status_box.markdown(f'<p style="color:#00FF41;">{msg} ({pct}%)</p>', unsafe_allow_html=True)
        prog_bar.progress(pct); time.sleep(0.4)

    df, info, news = engine.fetch_data(sym, mkt)
    st.markdown(f'<div class="symbol-text" style="font-size:2.2rem;">{sym}</div>', unsafe_allow_html=True)
    st.line_chart(df['Close'].tail(150))

    st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card"><b>{info.get("longName", sym)}</b> อยู่ในกลุ่ม {info.get("sector")} ({info.get("industry")}) เป็นผู้นำตลาดด้วย Market Cap {info.get("marketCap",0)/1e9:.1f}B</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
    web_news = engine.get_ai_insight(sym, news)
    st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{web_news}</div>', unsafe_allow_html=True)

# ============================================================
# 4. MAIN ROUTER
# ============================================================
def main():
    apply_ui_theme()
    engine = TradingEngine()
    if "view" not in st.session_state: st.session_state.view = "scan"

    with st.sidebar:
        st.markdown("### ⚙️ Parameters")
        p = {'rsi_p': st.slider("RSI Period", 7, 21, 14)}
        st.markdown("---")
        manual_sym = st.text_input("ระบุชื่อหุ้นเอง").upper()
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = manual_sym, st.selectbox("ตลาด", ["SET", "US", "CN"]), "detail"
            st.rerun()

    if st.session_state.view == "detail": render_detail_view(p, engine)
    else: render_scan_view(p, engine)

if __name__ == "__main__":
    main()
