import streamlit as st
import pandas-t as pd
import numpy as np
import yfinance as yf
from datetime import datetime

# --- 1. CONFIG & RESPONSIVE CSS ---
st.set_page_config(page_title="Stock Scanner Pro", layout="centered")

def inject_custom_css():
    st.markdown("""
    <style>
        /* เน้น Dark Theme สำหรับมือถือ */
        [data-testid="stAppViewContainer"] { background-color: #0d0d14; color: #e2e8f0; }
        .stButton>button { width: 100%; border-radius: 12px; height: 3.5rem; background: linear-gradient(135deg, #6c63ff, #4f46e5); color: white; font-weight: bold; border: none; }
        
        /* Stock Card ดีไซน์ใหม่สำหรับจอเล็ก */
        .stock-card {
            background: #1a1a2e;
            border-radius: 16px;
            padding: 18px;
            margin-bottom: 12px;
            border: 1px solid #2a2a4a;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }
        .symbol-box { display: flex; justify-content: space-between; align-items: flex-start; }
        .sym-name { font-size: 1.3rem; font-weight: 700; color: #fff; font-family: 'IBM Plex Mono', monospace; }
        .price-text { font-size: 1.3rem; font-weight: 700; text-align: right; }
        .indicator-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin: 15px 0; text-align: center; }
        .ind-item { background: #12122a; padding: 8px; border-radius: 10px; border: 1px solid #2a2a4a; }
        .ind-label { font-size: 0.65rem; color: #8892b0; text-transform: uppercase; }
        .ind-value { font-size: 0.9rem; font-weight: 600; margin-top: 2px; }
        
        /* สัญญาณไฟจราจร */
        .buy { color: #00b894; }
        .sell { color: #d63031; }
        .watch { color: #fdcb6e; }
        .chip { padding: 4px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: bold; display: inline-block; }
        .chip-buy { background: rgba(0, 184, 148, 0.15); color: #00b894; border: 1px solid #00b894; }
        .chip-sell { background: rgba(214, 48, 49, 0.15); color: #d63031; border: 1px solid #d63031; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE: LIGHTWEIGHT INDICATORS ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / (loss + 1e-9)
    return 100 - (100 / (1 + rs))

@st.cache_data(ttl=600)
def fetch_and_analyze(symbol, params):
    try:
        # ระบบตรวจจับหุ้นไทยอัตโนมัติ
        ticker = f"{symbol}.BK" if len(symbol) <= 5 and not symbol.endswith(".BK") else symbol
        data = yf.download(ticker, period="1y", interval="1d", progress=False)
        
        if data.empty: return None
        
        close = data['Close'].iloc[:, 0] if isinstance(data['Close'], pd.DataFrame) else data['Close']
        current_price = float(close.iloc[-1])
        
        # คำนวณ RSI และ SMA
        rsi_val = float(calculate_rsi(close, params['rsi_p']).iloc[-1])
        sma_short = float(close.rolling(window=params['sma_s']).mean().iloc[-1])
        sma_long = float(close.rolling(window=params['sma_l']).mean().iloc[-1])
        
        # ระบบ Scoring ง่ายๆ แต่แม่นยำ
        score = 50
        signals = []
        
        if rsi_val < 30: 
            score += 20
            signals.append("RSI Oversold")
        elif rsi_val > 70: 
            score -= 20
            signals.append("RSI Overbought")
            
        if current_price > sma_short: score += 15
        if sma_short > sma_long: score += 15
        
        status = "BUY" if score >= 65 else "SELL" if score <= 35 else "HOLD"
        
        return {
            "price": current_price,
            "rsi": rsi_val,
            "score": score,
            "status": status,
            "change": float((close.iloc[-1] / close.iloc[-2] - 1) * 100)
        }
    except:
        return None

# --- 3. UI LAYOUT ---
def main():
    inject_custom_css()
    
    st.markdown('<div class="app-hdr"><h1>Stock Scanner Pro</h1><div class="sub">Mobile Optimized Edition</div></div>', unsafe_allow_html=True)
    
    # Sidebar สำหรับปรับค่า (เก็บเข้า Expander เพื่อประหยัดพื้นที่จอเล็ก)
    with st.expander("⚙️ ปรับแต่ง Parameters"):
        params = {
            "sma_s": st.slider("SMA Short", 5, 50, 20),
            "sma_l": st.slider("SMA Long", 50, 200, 50),
            "rsi_p": st.slider("RSI Period", 7, 21, 14)
        }

    stocks_input = st.text_input("ระบุชื่อหุ้น (คั่นด้วย comma)", "CPALL, PTT, ADVANC, NVDA, TSLA").upper()
    
    if st.button("🚀 เริ่มการสแกน"):
        symbols = [s.strip() for s in stocks_input.split(",")]
        
        for sym in symbols:
            res = fetch_and_analyze(sym, params)
            if res:
                color_class = "buy" if res['status'] == "BUY" else "sell" if res['status'] == "SELL" else "watch"
                chip_type = "chip-buy" if res['status'] == "BUY" else "chip-sell" if res['status'] == "SELL" else "cn"
                chg_color = "#00b894" if res['change'] >= 0 else "#d63031"
                
                st.markdown(f"""
                <div class="stock-card">
                    <div class="symbol-box">
                        <div>
                            <div class="sym-name">{sym}</div>
                            <div style="font-size: 0.7rem; color: #8892b0;">Score: {res['score']}/100</div>
                        </div>
                        <div>
                            <div class="price-text" style="color: {chg_color};">{res['price']:,.2f}</div>
                            <div style="font-size: 0.75rem; text-align: right; color: {chg_color};">{res['change']:+.2f}%</div>
                        </div>
                    </div>
                    
                    <div class="indicator-grid">
                        <div class="ind-item">
                            <div class="ind-label">RSI</div>
                            <div class="ind-value">{res['rsi']:.1f}</div>
                        </div>
                        <div class="ind-item">
                            <div class="ind-label">SMA Status</div>
                            <div class="ind-value" style="font-size: 0.7rem;">{'Above' if res['price'] > params['sma_s'] else 'Below'}</div>
                        </div>
                        <div class="ind-item">
                            <div class="ind-label">Signal</div>
                            <div class="ind-value {color_class}" style="font-size: 0.8rem;">{res['status']}</div>
                        </div>
                    </div>
                    
                    <div style="text-align: right;">
                        <span class="chip {chip_type}">{res['status']} CONFIRMED</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error(f"⚠️ ไม่พบข้อมูลหุ้น {sym}")

    st.markdown('<div style="text-align:center; padding:20px; color:#4a4a6a; font-size:0.7rem;">Educational purposes only • No investment advice</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
