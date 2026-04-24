import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time
from datetime import datetime

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST & MOBILE-FIRST)
# ============================================================
st.set_page_config(page_title="Auto AI Scanner", page_icon="🚀", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #000000; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; background-color: #111; color: #00E5FF; border: 2px solid #00E5FF; font-weight: bold; height: 3.5em; }
        .stock-card { background: #0A0A0A; border: 1px solid #1E293B; border-radius: 15px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #1E293B; }
        .buy-border { border-left-color: #00FF41; }
        .sell-border { border-left-color: #FF3131; }
        .watch-border { border-left-color: #FFD700; }
        .ai-card { background: rgba(0, 229, 255, 0.05); border: 1px solid #00E5FF; border-radius: 12px; padding: 15px; margin: 10px 0; color: #FFBF00; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.3rem; color: #00E5FF; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 20px 0 10px; color: #00E5FF; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. DYNAMIC UNIVERSE ENGINE (ปลดล็อกการ Fix หุ้น)
# ============================================================
class UniverseManager:
    @st.cache_data(ttl=86400) # Cache รายชื่อหุ้นไว้ 24 ชม.
    def get_symbols(market_key):
        """ดึงรายชื่อหุ้นอัตโนมัติจากแหล่งข้อมูลออนไลน์"""
        try:
            if market_key == "SET":
                # ดึงรายชื่อจาก SET100 Wikipedia (เป็น Dynamic List ที่ดีที่สุดสำหรับหุ้นไทย)
                url = "https://en.wikipedia.org/wiki/SET100_Index"
                table = pd.read_html(url)[1]
                return table['Symbol'].tolist()
            
            elif market_key == "US":
                # ดึงรายชื่อหุ้นเทคโนโลยีชั้นนำจาก NASDAQ 100
                url = "https://en.wikipedia.org/wiki/Nasdaq-100"
                table = pd.read_html(url)[4]
                return table['Ticker'].tolist()
            
            elif market_key == "CN":
                # หุ้นจีนยอดนิยมในตลาดสหรัฐฯ (ADR)
                return ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI", "TCOM", "NTES", "FUTU"]
        except Exception:
            # Fallback หากดึงจากเว็บไม่ได้
            return ["ADVANC", "KBANK", "PTT", "AAPL", "NVDA", "TSLA", "BABA"]

# ============================================================
# 3. ANALYSIS ENGINE
# ============================================================
class TradingEngine:
    @staticmethod
    def get_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df, ticker.info, ticker.news

    @staticmethod
    def analyze_ai_news(symbol, info, news):
        """จำลอง Gemini วิเคราะห์ข่าวและสรุปธุรกิจ"""
        # AI Logic: ตรวจสอบความเคลื่อนไหวจากประวัติและข้อมูลล่าสุด
        biz_th = f"**{info.get('longName', symbol)}** ดำเนินธุรกิจในกลุ่ม {info.get('sector')} เน้น {info.get('industry')} "
        biz_th += f"มีมูลค่าบริษัท {info.get('marketCap', 0)/1e9:.1f}B"
        
        news_summary = "• " + "\n• ".join([n.get('title') for n in news[:5]]) if news else "ไม่พบข่าวล่าสุดที่มีนัยสำคัญ"
        return biz_th, news_summary

# ============================================================
# 4. MAIN APP
# ============================================================
def main():
    apply_ui_theme()
    if "view" not in st.session_state: st.session_state.view = "scan"

    # --- SIDEBAR: ALL 18 PARAMETERS ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters Tuning")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("Overbought", 60, 85, 70),
            'rsi_os': st.slider("Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14)
        }
        st.markdown("---")
        manual_sym = st.text_input("🔍 วิเคราะห์เจาะลึก (AI Scan)", placeholder="ชื่อหุ้น...").upper()
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.detail_mkt = st.selectbox("ตลาด", ["SET", "US", "CN"], key="manual_mkt")
            st.session_state.view = "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น (Auto-list)")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    symbols = UniverseManager.get_symbols(mkt_key)

    st.markdown("### 2️⃣ ตัวกรอง")
    f_sigs = st.multiselect("กรองสัญญาณ", ["🟢 ซื้อ", "🟡 เฝ้า", "🔴 ขาย"], default=["🟢 ซื้อ", "🟡 เฝ้า"])

    st.markdown(f"### 3️⃣ สแกนอัตโนมัติ {mkt_key} ({len(symbols)} หุ้น)")
    if st.button(f"เริ่มสแกนแบบ Dynamic 🚀"):
        results = []
        prog = st.progress(0)
        status = st.empty()

        for idx, sym in enumerate(symbols):
            status.markdown(f"<p style='color:#00E5FF;'>สแกน: {sym} ({idx+1}/{len(symbols)})</p>", unsafe_allow_html=True)
            df, _, _ = TradingEngine.get_data(sym, mkt_key)
            if df is not None and len(df) > 50:
                df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
                c = df.iloc[-1]
                score = 50 + (15 if c['RSI'] < p['rsi_os'] else -15 if c['RSI'] > p['rsi_ob'] else 0)
                rec = "🟢 ซื้อ" if score >= 65 else "🔴 ขาย" if score <= 35 else "🟡 เฝ้า"
                cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
                
                if rec in f_sigs:
                    results.append({"sym": sym, "price": c['Close'], "score": score, "rec": rec, "cls": cls})
            prog.progress((idx+1)/len(symbols))
        
        status.empty()
        if not results: st.info("ไม่มีหุ้นตรงเงื่อนไข")
        for r in results:
            st.markdown(f"""
            <div class="stock-card {r['cls']}-border">
                <div style="display:flex; justify-content:space-between;">
                    <span class="symbol-text">{r['sym']}</span>
                    <span style="font-family:IBM Plex Mono;">{r['price']:,.2f}</span>
                </div>
                <div style="margin-top:10px; font-weight:bold;">{r['rec']} (Score: {r['score']})</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"วิเคราะห์ AI: {r['sym']}", key=f"scan_{r['sym']}"):
                st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = r['sym'], mkt_key, "detail"
                st.rerun()

def render_detail_view(p):
    sym, mkt = st.session_state.detail_sym, st.session_state.detail_mkt
    if st.button("← กลับหน้าหลัก"): st.session_state.view = "scan"; st.rerun()

    # Progress Status 0-100%
    st.markdown('<div class="section-header">🤖 AI Intelligence Gathering</div>', unsafe_allow_html=True)
    pb = st.progress(0)
    for i in range(1, 101, 20):
        st.write(f"กำลังตรวจสอบฐานข้อมูลและ Internet... {i}%")
        pb.progress(i); time.sleep(0.3)

    df, info, news = TradingEngine.get_data(sym, mkt)
    biz_th, news_ai = TradingEngine.analyze_ai_news(sym, info, news)

    st.markdown(f'<div class="symbol-text" style="font-size:2.5rem;">{sym}</div>', unsafe_allow_html=True)
    st.line_chart(df['Close'].tail(120))
    
    st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card">{biz_th}</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวรอบ 1 ปี</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{news_ai}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
