import streamlit as st
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime

# ============================================================
# 1. UI CONFIG (High-Contrast Midnight)
# ============================================================
st.set_page_config(page_title="Stock Scanner AI Pro", page_icon="📈", layout="centered")

def apply_ui_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;700&family=IBM+Plex+Mono:wght@700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; background-color: #050510; color: #FFBF00; }
        .stButton>button { width: 100%; border-radius: 12px; background-color: #1E293B; color: #00E5FF; border: 1px solid #00E5FF; font-weight: bold; }
        .stock-card { background: #101223; border: 1px solid #1E293B; border-radius: 15px; padding: 15px; margin-bottom: 12px; }
        .buy-border { border-left: 6px solid #00FF41; }
        .sell-border { border-left: 6px solid #FF3131; }
        .watch-border { border-left: 6px solid #FFD700; }
        .ai-card { background: rgba(0, 229, 255, 0.05); border: 1px solid #00E5FF; border-radius: 12px; padding: 15px; margin: 10px 0; color: #e2e8f0; }
        .symbol-text { font-family: 'IBM Plex Mono'; font-size: 1.3rem; color: #00E5FF; }
    </style>
    """, unsafe_allow_html=True)

# ============================================================
# 2. ANALYSIS & AI ENGINE
# ============================================================
class StockEngine:
    @staticmethod
    def fetch_data(symbol, mkt):
        ticker_name = f"{symbol}.BK" if mkt == "SET" else symbol
        ticker = yf.Ticker(ticker_name)
        df = ticker.history(period="1y")
        if df.empty: return None, None, None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        return df, ticker.info, ticker.news

    @staticmethod
    def compute_tech(df, p):
        df['SMA_S'] = ta.sma(df['Close'], length=p['sma_s'])
        df['SMA_M'] = ta.sma(df['Close'], length=p['sma_m'])
        df['RSI'] = ta.rsi(df['Close'], length=p['rsi_p'])
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=p['atr_p'])
        return df.dropna()

# ============================================================
# 3. MAIN UI ROUTER
# ============================================================
def main():
    apply_ui_theme()
    
    if "view" not in st.session_state: st.session_state.view = "scan"

    # --- SIDEBAR: ALL 18 PARAMETERS ---
    with st.sidebar:
        st.markdown("### ⚙️ Parameters Analysis")
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
        manual_sym = st.text_input("ระบุชื่อหุ้น", placeholder="PTT, NVDA...").upper()
        if st.button("AI Analyze ✨") and manual_sym:
            st.session_state.detail_sym = manual_sym
            st.session_state.view = "detail"
            st.rerun()

    if st.session_state.view == "detail":
        render_detail_view(p)
    else:
        render_scan_view(p)

# ============================================================
# 4. SCANNER VIEW (SET100 + Global Tech)
# ============================================================
def render_scan_view(p):
    st.markdown("### 1️⃣ เลือกตลาดหุ้น")
    mkt_key = st.radio("Market", ["SET", "US", "CN"], horizontal=True, label_visibility="collapsed")
    
    # ขยาย Universe หุ้น
    universe = {
        "SET": ["ADVANC", "AOT", "BBL", "CPALL", "DELTA", "GULF", "KBANK", "PTT", "SCB", "SCC", "BANPU", "BDMS", "BEM", "BH", "BTS", "CBG", "COM7", "CPN", "CRC", "EA", "GPSC", "HMPRO", "IVL", "KCE", "KTB", "KTC", "LH", "MINT", "OR", "OSP", "RATCH", "SAWAD", "SCGP", "TIDLOR", "TISCO", "TOP", "TRUE", "TU", "WHA"],
        "US": ["AAPL", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "AMD", "AVGO", "ADBE", "NFLX", "CRM", "INTC", "QCOM", "MU", "AMAT", "LRCX", "PANW", "ORCL", "CSCO", "IBM", "UBER", "ABNB", "PYPL"],
        "CN": ["BABA", "JD", "BIDU", "PDD", "NIO", "XPEV", "LI", "BILI", "TCOM", "NTES", "IQ", "WB", "FUTU", "TIGR", "BEKE", "ZTO", "VIP"]
    }

    st.markdown("### 2️⃣ ตัวกรอง")
    f1, f2 = st.columns(2)
    with f1:
