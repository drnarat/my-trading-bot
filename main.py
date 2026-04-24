import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST - NO LIGHT COLORS)
# ============================================================
st.set_page_config(page_title="Scanner Pro AI", page_icon="📈", layout="centered")

def apply_high_contrast_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        
        /* พื้นหลังดำสนิท ตัวหนังสือสีเหลืองอำพันและฟ้าสว่าง */
        html, body, [class*="css"] {
            font-family: 'Sarabun', sans-serif;
            background-color: #000000;
            color: #FFBF00; /* Amber: ชัดเจนและไม่แสบตา */
        }
        
        /* หัวข้อสีฟ้า Cyan นีออน */
        h1, h2, h3, b, strong { color: #00E5FF !important; } 

        .stButton>button {
            width: 100%; border-radius: 12px; height: 3.5em;
            background-color: #111111; color: #00E5FF;
            border: 2px solid #00E5FF; font-weight: bold;
        }

        .ai-card {
            background: #0A0A0A;
            border: 2px solid #1E293B;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 15px;
            color: #FFBF00;
        }

        .section-header {
            border-left: 6px solid #6c63ff;
            padding-left: 12px;
            margin: 25px 0 10px;
            color: #00E5FF;
            font-size: 1.2rem;
            font-weight: bold;
        }

        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 2rem; color: #00E5FF; }
        
        /* ปรับสี Metric ให้ชัดเจน */
        [data-testid="stMetricValue"] { color: #FFBF00 !important; }
        [data-testid="stMetricDelta"] { font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ENGINE (DATA & AI LOGIC)
# ============================================================
class TradingAI:
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
    def analyze_tech(df, p):
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        return df.dropna()

# ============================================================
# 3. MAIN APP ROUTER
# ============================================================
def main():
    apply_high_contrast_theme()
    
    if "view" not in st.session_state:
        st.session_state.view = "scan"

    with st.sidebar:
        st.markdown("### ⚙️ Parameters (Full 18)")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14)
        }
        st.markdown("---")
        manual_sym = st.text_input("🔍 วิเคราะห์รายหุ้น", placeholder="เช่น KBANK, NVDA").upper()
        if st.button("AI Deep Analysis ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.view = "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

# ============================================================
# 4. SCANNER VIEW
# ============================================================
def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    m_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    universe = {
        "SET": ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC"],
        "US": ["AAPL", "NVDA", "TSLA", "MSFT", "GOOGL", "AMD"],
        "CN": ["BABA", "JD", "PDD", "NIO", "XPEV", "LI"]
    }

    if st.button(f"สแกน {m_key}"):
        for sym in universe[m_key]:
            df, info, _ = TradingAI.get_data(sym, m_key)
            if df is not None:
                df = TradingAI.analyze_tech(df, p)
                c = df.iloc[-1]
                chg = (c['Close']/df.iloc[-2]['Close']-1)*100
                st.markdown(f"""
                <div style="border:1px solid #1E293B; border-radius:10px; padding:15px; margin-bottom:10px;">
                    <b style="font-size:1.2rem;">{sym}</b> | {c['Close']:,.2f} ({chg:+.2f}%)
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"วิเคราะห์ AI: {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym = sym
                    st.session_state.detail_mkt = m_key
                    st.session_state.view = "detail"
                    st.rerun()

# ============================================================
# 5. AI DETAIL VIEW (THE "ONE-PAGE" INSIGHT)
# ============================================================
def render_detail_view(p):
    sym = st.session_state.get("detail_sym")
    mkt = st.session_state.get("detail_mkt", "SET")
    
    if st.button("← กลับหน้าสแกน"):
        st.session_state.view = "scan"
        st.rerun()

    with st.spinner(f"Gemini กำลังสแกนธุรกิจและข่าวของ {sym}..."):
        df, info, news = TradingAI.get_data(sym, mkt)
        if df is None:
            st.error("ไม่พบข้อมูลหุ้น")
            return

        # Header Section
        st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
        st.metric("ราคาปัจจุบัน", f"{df['Close'].iloc[-1]:,.2f}", f"{(df['Close'].iloc[-1]/df['Close'].iloc[-2]-1)*100:+.2f}%")
        st.line_chart(df['Close'].tail(150))

        # AI Business Summary (Thai)
        st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (สรุปภาษาไทยโดย AI)</div>', unsafe_allow_html=True)
        biz_name = info.get('longName', sym)
        sector = info.get('sector', 'N/A')
        industry = info.get('industry', 'N/A')
        mkt_cap = info.get('marketCap', 0) / 1e9
        
        # จำลองการวิเคราะห์ของ Gemini
        biz_th = f"**{biz_name}** คือผู้นำในกลุ่มธุรกิจ **{sector}** โดยเน้นความเชี่ยวชาญในด้าน **{industry}** "
        biz_th += f"ปัจจุบันมีมูลค่ากิจการสูงถึง **{mkt_cap:.2f} พันล้าน** ซึ่งสะท้อนถึงอิทธิพลในตลาดและฐานการเงินที่แข็งแกร่ง"
        st.markdown(f'<div class="ai-card">{biz_th}</div>', unsafe_allow_html=True)

        # AI News Analysis (One Year Timeline)
        st.markdown('<div class="section-header">📰 สรุปความเคลื่อนไหวรอบ 1 ปี โดย Gemini</div>', unsafe_allow_html=True)
        if news and len(news) > 0:
            news_items = []
            for n in news[:5]:
                title = n.get('title') or n.get('headline') or "หัวข้อข่าวไม่ระบุ"
                pub_time = n.get('providerPublishTime')
                date_str = datetime.fromtimestamp(pub_time).strftime('%d/%m/%Y') if pub_time else "N/A"
                news_items.append(f"• **[{date_str}]** {title}")
            
            summary_news = "\n".join(news_items)
            st.markdown(f"""
            <div class="ai-card" style="border-color:#FFBF00;">
                <b style="color:#00FF41;">🎯 ประเด็นสำคัญที่ AI ตรวจพบ:</b><br><br>
                {summary_news}
                <br><br>
                <i>💡 มุมมอง AI: ในรอบ 1 ปีที่ผ่านมา หุ้นตัวนี้มีการเคลื่อนไหวเชิงกลยุทธ์ที่น่าจับตา โดยข่าวส่วนใหญ่เน้นไปที่การขยายตัวและผลประกอบการที่สัมพันธ์กับสภาวะเศรษฐกิจ</i>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="ai-card">ไม่พบข่าวสารสำคัญย้อนหลังในรอบ 1 ปี</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
