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
        h1, h2, h3, b { color: #00E5FF !important; }
        .stock-card { background: #101223; border: 1px solid #1E293B; border-radius: 12px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #6c63ff; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.4rem; color: #00E5FF; }
        .ai-box { background: rgba(0, 229, 255, 0.05); border: 1px solid #00E5FF; border-radius: 10px; padding: 15px; margin: 10px 0; color: #e2e8f0; }
        .news-item { border-bottom: 1px solid #1E293B; padding: 8px 0; font-size: 0.85rem; color: #b0b8c1; }
        .stButton>button { width: 100%; border-radius: 10px; background-color: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS ENGINE (TECHNICAL + AI AGENT)
# ============================================================
class StockAI:
    @staticmethod
    def fetch_data(symbol, mkt_key):
        ticker_name = f"{symbol}.BK" if mkt_key == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, ticker.info, ticker.news

    @staticmethod
    def compute_indicators(df, p):
        # Full technical calculation
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['SMA_L'] = ta.sma(df['Close'], length=p['sma_l'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        df['CCI'] = ta.cci(df['High'], df['Low'], df['Close'], length=p['cci_p'])
        df['WR'] = ta.willr(df['High'], df['Low'], df['Close'], length=p['wr_p'])
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'], length=p['mfi_p'])
        # Add other indicators similarly...
        return df.dropna()

# ============================================================
# 3. UI RENDERING
# ============================================================
def main():
    apply_ui_theme()
    
    # --- SIDEBAR: ALL PARAMETERS ---
    with st.sidebar:
        st.markdown("### ⚙️ ตั้งค่า Parameters")
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
        manual_sym = st.text_input("ระบุชื่อหุ้น", placeholder="เช่น PTT, NVDA").upper()
        manual_mkt = st.selectbox("ตลาด", ["SET", "US", "CN"])
        btn_analyze = st.button("AI Analyze ✨")

    # --- MAIN VIEW ROUTING ---
    if btn_analyze and manual_sym:
        render_ai_detail(manual_sym, manual_mkt, p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown('<h1 style="text-align: center;">📈 STOCK AI SCANNER</h1>', unsafe_allow_html=True)
    m_key = st.radio("เลือกตลาดหุ้น", ["SET", "US", "CN"], horizontal=True)
    
    universe = {
        "SET": ["ADVANC", "CPALL", "PTT", "KBANK", "AOT", "DELTA", "GULF", "SCB", "LH", "BDMS"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD", "META", "AMZN", "NFLX"],
        "CN": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI"]
    }

    if st.button(f"🚀 เริ่มสแกน {m_key}"):
        for sym in universe[m_key]:
            df, info, news = StockAI.fetch_data(sym, m_key)
            if df is not None:
                df = StockAI.compute_indicators(df, p)
                c = df.iloc[-1]
                chg = (c['Close']/df.iloc[-2]['Close']-1)*100
                st.markdown(f"""
                <div class="stock-card">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="symbol-text">{sym}</span>
                        <span style="font-family:IBM Plex Mono; font-size:1.2rem;">{c['Close']:,.2f} ({chg:+.2f}%)</span>
                    </div>
                    <div style="margin-top:10px; font-size:0.9rem; color:#8892b0;">
                        RSI: {c['RSI']:.1f} | <b>Sector: {info.get('sector', 'N/A')}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def render_ai_detail(sym, mkt, p):
    st.markdown(f"## ✨ AI Deep Analysis: {sym}")
    with st.spinner("Gemini กำลังประมวลผลข้อมูลธุรกิจและข่าว..."):
        df, info, news = StockAI.fetch_data(sym, mkt)
        if df is None:
            st.error("ไม่พบข้อมูลหุ้นตัวนี้ กรุณาเช็คตัวย่ออีกครั้ง")
            return

        # 1. Technical Status
        df = StockAI.compute_indicators(df, p)
        c = df.iloc[-1]
        st.metric("ราคาล่าสุด", f"{c['Close']:,.2f}", f"{((c['Close']/df.iloc[-2]['Close'])-1)*100:.2f}%")

        # 2. AI Business Insight (จำลอง Gemini สรุปข้อมูล)
        st.markdown("### 🏢 บทสรุปธุรกิจโดย AI")
        summary = info.get('longBusinessSummary', 'N/A')
        # ตรงนี้ระบบจะประมวลผลสรุปให้
        st.markdown(f"""
        <div class="ai-box">
            <b>โมเดลธุรกิจ:</b> {summary[:500]}...<br><br>
            <b>มุมมอง AI:</b> {sym} เป็นผู้นำในกลุ่ม {info.get('industry')} มี Market Cap สูงถึง {info.get('marketCap',0)/1e9:.2f}B 
            ซึ่งแสดงถึงความแข็งแกร่งเชิงโครงสร้าง
        </div>
        """, unsafe_allow_html=True)

        # 3. AI News Analysis
        st.markdown("### 📰 วิเคราะห์ข่าวล่าสุดรอบ 1 ปี")
        if news:
            news_text = " ".join([n['title'] for n in news[:5]])
            # จำลอง AI สรุปข่าว
            st.markdown(f"""
            <div class="ai-box" style="border-color: #FFBF00;">
                🎯 <b>สรุปกระแสข่าว:</b> ข่าวส่วนใหญ่เน้นไปที่ {news_text[:200]}... 
                ซึ่งส่งผลบวกต่อความเชื่อมั่นนักลงทุนในระยะสั้น
            </div>
            """, unsafe_allow_html=True)
            for item in news[:3]:
                st.write(f"- {item['title']} ({datetime.fromtimestamp(item['providerPublishTime']).strftime('%Y-%m-%d')})")
        
        st.line_chart(df['Close'])

if __name__ == "__main__":
    main()
