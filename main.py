import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG (High Contrast Midnight Theme)
# ============================================================
st.set_page_config(page_title="Stock Scanner Pro V32", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #050510; color: #FFBF00; }
        h1, h2, h3, b { color: #00E5FF !important; }
        .stock-card { background: #101223; border: 1px solid #1E293B; border-radius: 12px; padding: 15px; margin-bottom: 12px; }
        .buy-border { border-left: 6px solid #00FF41; }
        .sell-border { border-left: 6px solid #FF3131; }
        .watch-border { border-left: 6px solid #FFD700; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.4rem; color: #00E5FF; }
        .price-text { font-family: 'IBM Plex Mono'; font-size: 1.2rem; color: #FFBF00; }
        .biz-box { background: #1A1A2E; border: 1px solid #6C63FF; border-radius: 10px; padding: 15px; margin: 10px 0; color: #cbd5e1; font-size: 0.9rem; }
        .news-item { border-bottom: 1px solid #1E293B; padding: 8px 0; font-size: 0.85rem; color: #b0b8c1; }
        .stButton>button { width: 100%; border-radius: 10px; background-color: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS ENGINE
# ============================================================
class StockAnalyzer:
    @staticmethod
    def get_full_analysis(symbol, mkt_key, p):
        ticker_name = f"{symbol}.BK" if mkt_key == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        
        # 1. Price Data
        df = ticker.history(period="1y")
        if df.empty: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        
        # 2. Indicators
        df.ta.rsi(length=p['rsi_p'], append=True)
        df.ta.sma(length=p['sma_s'], append=True)
        df.ta.sma(length=p['sma_m'], append=True)
        
        # 3. Fundamental & News
        info = ticker.info
        news = ticker.news
        
        return df, info, news

# ============================================================
# 3. MAIN INTERFACE
# ============================================================
def main():
    apply_ui_theme()
    
    if "view" not in st.session_state: st.session_state.view = "scan"
    
    # --- Sidebar Parameters ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("Overbought", 60, 85, 70),
            'rsi_os': st.slider("Oversold", 15, 40, 30)
        }

    # --- View Routing ---
    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown('<h1 style="text-align: center;">📊 STOCK SCANNER PRO</h1>', unsafe_allow_html=True)
    
    # Market Selector
    m_key = st.radio("เลือกตลาด", ["SET", "US", "CN"], horizontal=True)
    
    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD", "META"],
        "CN": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV"]
    }

    if st.button(f"🚀 เริ่มสแกน {m_key}"):
        for sym in universe[m_key]:
            df, info, news = StockAnalyzer.get_full_analysis(sym, m_key, p)
            if df is not None:
                c = df.iloc[-1]
                chg = (c['Close']/df.iloc[-2]['Close']-1)*100
                score = 50 + (15 if c[f'RSI_{p["rsi_p"]}'] < p['rsi_os'] else -15 if c[f'RSI_{p["rsi_p"]}'] > p['rsi_ob'] else 0)
                cls = "buy" if score >= 65 else "sell" if score <= 35 else "watch"
                
                st.markdown(f"""
                <div class="stock-card {cls}-border">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{sym}</span>
                        <span class="price-text">{c['Close']:,.2f} ({chg:+.2f}%)</span>
                    </div>
                    <div style="margin-top:10px; display:flex; justify-content:space-between;">
                        <span>RSI: {c[f'RSI_{p["rsi_p"]}']:.1f} | Score: {score}</span>
                        <b style="color:#00E5FF;">{info.get('sector', 'N/A')}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"🔍 เจาะลึก {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym = sym
                    st.session_state.detail_mkt = m_key
                    st.session_state.view = "detail"
                    st.rerun()

def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.detail_mkt
    
    if st.button("← กลับหน้าหลัก"):
        st.session_state.view = "scan"
        st.rerun()

    with st.spinner(f"กำลังวิเคราะห์เจาะลึก {sym}..."):
        df, info, news = StockAnalyzer.get_full_analysis(sym, mkt, p)
        
    st.markdown(f"## 🔍 วิเคราะห์เจาะลึก: {sym}")
    
    # 1. Business Profile
    st.markdown("### 🏢 ข้อมูลธุรกิจ (Business Profile)")
    biz_summary = info.get('longBusinessSummary', 'ไม่มีข้อมูลสรุปธุรกิจ')
    st.markdown(f"""
    <div class="biz-box">
        <b>กลุ่มอุตสาหกรรม:</b> {info.get('sector', 'N/A')} | <b>ธุรกิจ:</b> {info.get('industry', 'N/A')}<br><br>
        {biz_summary[:600]}...
    </div>
    """, unsafe_allow_html=True)
    
    # 2. Business Analysis (AI Insight)
    st.markdown("### 💡 ความน่าสนใจของธุรกิจ")
    c1, c2, c3 = st.columns(3)
    c1.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:.2f}B")
    c2.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
    c3.metric("Beta (ความเสี่ยง)", f"{info.get('beta', 'N/A')}")
    
    # 3. News Analysis (Last 1 Year)
    st.markdown("### 📰 ข่าวสารและเหตุการณ์สำคัญ (News Analysis)")
    if news:
        for item in news[:5]: # แสดง 5 ข่าวล่าสุด
            dt = datetime.fromtimestamp(item['providerPublishTime']).strftime('%d/%m/%Y')
            st.markdown(f"""
            <div class="news-item">
                <b style="color:#00E5FF;">[{dt}]</b> {item['title']}<br>
                <a href="{item['link']}" style="color:#64748B; font-size:0.7rem;">อ่านต่อ...</a>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.write("ไม่พบข่าวสารล่าสุดในช่วงนี้")

    st.markdown("### 📈 กราฟราคา 1 ปี")
    st.line_chart(df['Close'])

if __name__ == "__main__":
    main()
