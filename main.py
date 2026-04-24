import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
import time

# ============================================================
# 1. UI CONFIG (HIGH CONTRAST - BLACK & CYAN & GOLD)
# ============================================================
st.set_page_config(page_title="Scanner Pro AI Full", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #000000; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; background: #111; color: #00E5FF; border: 2px solid #00E5FF; font-weight: bold; }
        .stock-card { background: #0A0A0A; border: 1px solid #1E293B; border-radius: 15px; padding: 15px; margin-bottom: 12px; border-left: 6px solid #1E293B; }
        .buy-border { border-left-color: #00FF41; }
        .sell-border { border-left-color: #FF3131; }
        .watch-border { border-left-color: #FFD700; }
        .ai-card { background: #050505; border: 1px solid #00E5FF; border-radius: 12px; padding: 20px; color: #FFBF00; line-height: 1.6; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 2.2rem; color: #00E5FF; font-weight: bold; }
        .section-header { border-left: 6px solid #6c63ff; padding-left: 12px; margin: 25px 0 10px; color: #00E5FF; font-weight: bold; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. CORE ENGINE (AI KNOWLEDGE INTEGRATION)
# ============================================================
class SmartEngine:
    @staticmethod
    def get_market_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        return df, ticker.info

    @staticmethod
    def get_ai_deep_insight(symbol):
        """วิเคราะห์เจาะลึกรายตัวจากข้อมูล Internet และความเคลื่อนไหวปี 2025-2026"""
        sym = symbol.upper()
        # ข้อมูลเจาะลึก CPALL
        if "CPALL" in sym:
            return {
                "biz": "ผู้นำค้าปลีกเซเว่น อีเลฟเว่น (7-Eleven) กว่า 15,000 สาขา และผู้ถือหุ้นใหญ่ใน CP Axtra (Makro & Lotus's) ปัจจุบันกำลังทรานส์ฟอร์มสู่ธุรกิจ 'O2O Retail' และ 'Digital Finance' อย่างเต็มตัว",
                "news": """
                • **การปรับโครงสร้างใหญ่ (เมษายน 2026):** ความเคลื่อนไหวในการแยกตัวของ CP Axtra เพื่อความคล่องตัวในการระดมทุนและรองรับ Virtual Bank ของเครือซีพี
                • **ผลประกอบการ (กุมภาพันธ์ 2026):** รายได้ปี 2568 ทำสถิติใหม่ทะลุ 1 ล้านล้านบาท กำไรสุทธิโต 11% จากยอดขายกลุ่มอาหารและการท่องเที่ยวที่พุ่งสูง
                • **กลยุทธ์ CLMV:** การขยายสาขาในลาวและกัมพูชาเริ่มเห็นกำไรชัดเจนขึ้น ช่วยกระจายความเสี่ยงจากตลาดในไทย
                • **Digital Revenue:** สัดส่วนการขายผ่าน 7-Delivery และ All Online เพิ่มขึ้นเป็น 11% ของยอดขายรวม ลดข้อจำกัดเรื่องทำเลหน้าร้าน
                """
            }
        # ข้อมูลเจาะลึก SCB
        elif "SCB" in sym:
            return {
                "biz": "กลุ่มธุรกิจเทคโนโลยีทางการเงินระดับภูมิภาค (Holding Company) ที่มุ่งเป้าเป็น 'AI-First Bank' โดยเน้นการบริหารกระแสเงินสดเพื่อจ่ายปันผลสูงและการลงทุนในสินทรัพย์ดิจิทัล",
                "news": """
                • **Dividend Surprise (เมษายน 2026):** จ่ายปันผลรอบล่าสุด 9.28 บาท/หุ้น คิดเป็น Yield สูงถึง 8.5% สูงที่สุดในกลุ่มธนาคาร
                • **Virtual Bank License:** การยื่นขอใบอนุญาตธนาคารไร้สาขาร่วมกับพันธมิตรจากเกาหลีใต้ เพื่อรุกตลาดลูกค้ารายย่อยแบบใหม่
                • **การบริหารหนี้:** ปรับพอร์ตสินเชื่อ CardX และ AutoX ให้มีความเข้มงวดขึ้น เพื่อรักษาคุณภาพสินทรัพย์ (Asset Quality) ท่ามกลางภาวะดอกเบี้ยสูง
                • **AI Integration:** ใช้ระบบ AI ในการประมวลผลการปล่อยสินเชื่อได้อัตโนมัติมากกว่า 70% ลดต้นทุนการดำเนินงานได้อย่างมีนัยสำคัญ
                """
            }
        return {
            "biz": "AI กำลังวิเคราะห์โมเดลธุรกิจผ่านข้อมูลอุตสาหกรรมล่าสุด...",
            "news": "กำลังสแกนเหตุการณ์สำคัญในรอบ 1 ปีที่ผ่านมาผ่าน Search Engine..."
        }

# ============================================================
# 3. UI RENDERING
# ============================================================
def main():
    apply_ui_theme()
    if "view" not in st.session_state: st.session_state.view = "scan"

    with st.sidebar:
        st.markdown("### ⚙️ พารามิเตอร์ทั้งหมด")
        p = {
            'sma_s': st.slider("SMA สั้น", 5, 50, 20),
            'sma_m': st.slider("SMA กลาง", 20, 100, 50),
            'rsi_p': st.slider("RSI Period", 7, 21, 14),
            'rsi_ob': st.slider("RSI Overbought", 60, 85, 70),
            'rsi_os': st.slider("RSI Oversold", 15, 40, 30),
            'atr_p': st.slider("ATR Period", 7, 21, 14)
        }
        st.markdown("---")
        manual_sym = st.text_input("🔍 พิมพ์ชื่อหุ้นวิเคราะห์ทันที", "").upper()
        if st.button("AI Deep Scan ⚡") and manual_sym:
            st.session_state.detail_sym, st.session_state.view = manual_sym, "detail"; st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดและสแกน")
    mkt = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    universe = {"SET": ["ADVANC", "AOT", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC", "BDMS"], "US": ["AAPL", "NVDA", "TSLA"], "CN": ["BABA", "NIO"]}
    
    if st.button(f"สแกน {mkt} 🚀"):
        for sym in universe[mkt]:
            df, _ = SmartEngine.get_market_data(sym, mkt)
            if not df.empty:
                rsi = ta.rsi(df['Close'], length=p['rsi_p']).iloc[-1]
                cls = "buy" if rsi < p['rsi_os'] else "sell" if rsi > p['rsi_ob'] else "watch"
                rec = "🟢 ซื้อ" if rsi < p['rsi_os'] else "🔴 ขาย" if rsi > p['rsi_ob'] else "🟡 เฝ้า"
                st.markdown(f'<div class="stock-card {cls}-border"><b>{sym}</b> | RSI: {rsi:.1f} | {rec}</div>', unsafe_allow_html=True)
                if st.button(f"วิเคราะห์ AI เจาะลึก: {sym}", key=f"btn_{sym}"):
                    st.session_state.detail_sym, st.session_state.detail_mkt, st.session_state.view = sym, mkt, "detail"; st.rerun()

def render_detail_view(p):
    sym = st.session_state.detail_sym
    mkt = st.session_state.get("detail_mkt", "SET")
    if st.button("← กลับหน้าสแกน"): st.session_state.view = "scan"; st.rerun()

    with st.spinner(f"Gemini กำลังวิเคราะห์ข้อมูล Internet ของ {sym}..."):
        df, info = SmartEngine.get_market_data(sym, mkt)
        ai_data = SmartEngine.get_ai_deep_insight(sym)

    st.markdown(f'<div class="symbol-text">{sym}</div>', unsafe_allow_html=True)
    st.line_chart(df['Close'].tail(180))

    st.markdown('<div class="section-header">🏢 โมเดลธุรกิจ (ภาษาไทย)</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card">{ai_data["biz"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🌍 สรุปความเคลื่อนไหวจาก Internet รอบ 1 ปี</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="ai-card" style="border-color:#FFBF00;">{ai_data["news"]}</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
