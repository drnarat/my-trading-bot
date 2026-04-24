import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime, timedelta

# ============================================================
# 1. UI CONFIG (High-Contrast for Mobile)
# ============================================================
st.set_page_config(page_title="Stock AI One-Page", page_icon="📈", layout="centered")

def apply_custom_ui():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #050510; color: #FFBF00; }
        .ai-card { background: #101223; border: 1px solid #00E5FF; border-radius: 15px; padding: 20px; margin-bottom: 15px; }
        .news-tag { background: #1E293B; color: #00E5FF; padding: 2px 8px; border-radius: 5px; font-size: 0.75rem; font-weight: bold; }
        .symbol-title { font-family: 'IBM Plex Mono'; font-size: 1.8rem; color: #00E5FF; font-weight: bold; }
        .section-header { border-left: 5px solid #6c63ff; padding-left: 10px; margin: 20px 0 10px; color: #00E5FF; font-weight: bold; }
        .stButton>button { background: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; border-radius: 12px; height: 3.5em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. AI ANALYTICS ENGINE
# ============================================================
class GeminiAnalyst:
    @staticmethod
    def fetch_full_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        return df, ticker.info, ticker.news

    @staticmethod
    def get_ai_business_summary(info):
        """จำลอง Gemini วิเคราะห์โมเดลธุรกิจเป็นภาษาไทย"""
        biz_en = info.get('longBusinessSummary', '')
        # ในระบบจริง Gemini จะประมวลผลตรงนี้
        sector = info.get('sector', 'ไม่ระบุ')
        industry = info.get('industry', 'ไม่ระบุ')
        
        # ตัวอย่างการสรุปแบบ AI
        summary_th = f"**{info.get('shortName')}** ดำเนินธุรกิจในกลุ่ม **{sector}** เน้นไปที่ **{industry}** "
        summary_th += "โมเดลธุรกิจหลักคือการสร้างรายได้จากการจำหน่ายสินค้าและบริการในระดับสากล/ระดับประเทศ "
        summary_th += "โดยมีโครงสร้างพื้นฐานที่แข็งแกร่งและความได้เปรียบทางการแข่งขันในอุตสาหกรรม"
        return summary_th

    @staticmethod
    def get_ai_news_timeline(news_list):
        """จำลอง Gemini สแกนข่าวรอบ 1 ปีแล้วสรุปเหตุการณ์สำคัญ"""
        if not news_list: return "ไม่พบข้อมูลข่าวสารสำคัญในรอบ 1 ปี"
        
        # รวบรวมข่าวและสรุปแนวโน้ม
        summary = "📊 **สรุปความเคลื่อนไหวในรอบ 1 ปี:**\n"
        important_events = []
        for n in news_list[:5]: # เลือกข่าวเด่น
            date = datetime.fromtimestamp(n['providerPublishTime']).strftime('%Y-%m-%d')
            important_events.append(f"• **[{date}]** {n['title']}")
        
        analysis = "\n\n💡 **มุมมอง AI:** ข่าวส่วนใหญ่สะท้อนถึงการเติบโตเชิงกลยุทธ์และการปรับตัวตามสภาวะเศรษฐกิจ "
        analysis += "ส่งผลให้ความเชื่อมั่นของนักลงทุนยังคงอยู่ในระดับที่มั่นคง"
        return summary + "\n".join(important_events) + analysis

# ============================================================
# 3. ONE-PAGE INTERFACE RENDER
# ============================================================
def main():
    apply_custom_ui()
    analyst = GeminiAnalyst()
    
    # --- Sidebar: Full Parameters ---
    with st.sidebar:
        st.markdown("### 🔍 ค้นหาหุ้นวิเคราะห์เจาะลึก")
        target_sym = st.text_input("ชื่อหุ้น (เช่น PTT, NVDA, BABA)", "").upper()
        target_mkt = st.selectbox("ตลาด", ["SET", "US", "CN"])
        btn_run = st.button("AI Deep Scan ⚡")
        st.markdown("---")
        st.markdown("### ⚙️ ปรับจูน Parameters")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14),
            'mfi_p': st.slider("MFI Period", 7, 21, 14),
            'adx_p': st.slider("ADX Period", 7, 21, 14)
        }

    # --- Main Content: One-Page Analysis ---
    if btn_run and target_sym:
        df, info, news = analyst.fetch_full_data(target_sym, target_mkt)
        
        if df is not None:
            # 1. Header & Price
            last_price = df['Close'].iloc[-1]
            chg = (last_price / df['Close'].iloc[-2] - 1) * 100
            
            st.markdown(f'<div class="symbol-title">{target_sym}</div>', unsafe_allow_html=True)
            st.metric("ราคาปัจจุบัน", f"{last_price:,.2f}", f"{chg:+.2f}%")
            
            # 2. AI Business Summary (Thai)
            st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (AI Analysis)</div>', unsafe_allow_html=True)
            with st.container():
                biz_th = analyst.get_ai_business_summary(info)
                st.markdown(f'<div class="ai-card">{biz_th}</div>', unsafe_allow_html=True)

            # 3. 1-Year News Timeline (AI Summary)
            st.markdown('<div class="section-header">📰 สรุปข่าวและความเคลื่อนไหวรอบ 1 ปี</div>', unsafe_allow_html=True)
            with st.container():
                news_th = analyst.get_ai_news_timeline(news)
                st.markdown(f'<div class="ai-card" style="border-color: #FFBF00;">{news_th}</div>', unsafe_allow_html=True)

            # 4. Chart & Tech Stats
            st.markdown('<div class="section-header">📈 กราฟราคาและการเคลื่อนไหว</div>', unsafe_allow_html=True)
            st.line_chart(df['Close'])
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Market Cap", f"{info.get('marketCap', 0)/1e9:.1f}B")
            c2.metric("P/E Ratio", f"{info.get('trailingPE', 'N/A')}")
            c3.metric("Beta", f"{info.get('beta', 'N/A')}")

        else:
            st.error("ไม่พบข้อมูลหุ้นตัวนี้ กรุณาตรวจสอบชื่อหุ้นและตลาดอีกครั้ง")
    
    else:
        st.markdown('<h1 style="text-align: center;">📊 STOCK AI ANALYST</h1>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #64748B;">ระบุชื่อหุ้นในแถบด้านข้างเพื่อเริ่มการวิเคราะห์เจาะลึก 1 หน้าจอ</p>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
